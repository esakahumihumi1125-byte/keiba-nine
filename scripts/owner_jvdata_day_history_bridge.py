"""Owner-local RACE+RCVN historical observation bridge, strictly ungraded.

Receives ONLY in-memory, locally licensed JV-Data records; no JV-Link or
network calls. Match current RA2/SE2 to SE7 by PRIVATE registration ID, then
attach historical RA7 by the full six-part race identity.

This is not proof of complete history, authorised redistribution, accurate
JRA scratches or official starter list. Never send output to public APIs.
"""
from datetime import datetime

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jvdata_ra_se_candidate import (
    RA_LENGTH, SE_LENGTH, parse_jvdata_prestart_racecard,
)
from owner_jvdata_horse_history_coverage import (
    _past_result_identity, MAX_HISTORY_RECORDS, JST,
)
from owner_jvdata_horse_history_preview import (
    _historical_ra_context, preview_jvdata_horse_history,
)

VERSION = "owner-jvdata-local-day-history-bridge-1"
MAX_CURRENT_RECORDS = 5000
MAX_HISTORY_BATCH = 5000
MAX_RACE_CARDS = 36


def _require_record(raw, kind, category, length):
    if (type(raw) is not bytes or len(raw) != length
            or raw[:3] != kind + category or raw[-2:] != b"\r\n"):
        raise CoverageError("Invalid JV-Data record in local history input")
    return raw


def build_local_day_history(current_records, history_records, day, *,
                            captured_at):
    """Produce no more than 36 local-only, ungraded per-horse observations.

    An RCVN feed without linked SE7 rows does not prove a horse is unraced.
    No result fields are converted into a formal grade or purchase.
    """
    if (type(day) is not str or not _valid_date(day)
            or not isinstance(captured_at, datetime)
            or captured_at.tzinfo is None or captured_at.utcoffset() is None
            or not isinstance(current_records, (list, tuple))
            or not 1 <= len(current_records) <= MAX_CURRENT_RECORDS
            or not isinstance(history_records, (list, tuple))
            or len(history_records) > MAX_HISTORY_BATCH):
        raise CoverageError("Invalid local history input collection")
    capture_day = captured_at.astimezone(JST).strftime("%Y%m%d")

    today_ra, today_se, joined_ids = {}, {}, set()
    for raw in current_records:
        if not isinstance(raw, bytes) or len(raw) < 30:
            raise CoverageError("Invalid local current record")
        kind = raw[:2]
        if kind not in (b"RA", b"SE") or raw[2:3] != b"2":
            raise CoverageError("Unexpected record in current race list")
        _require_record(
            raw, kind, b"2", RA_LENGTH if kind == b"RA" else SE_LENGTH
        )
        if raw[11:19].decode("ascii", errors="replace") != day:
            raise CoverageError("Unmatched current race date")
        identity = raw[11:27]
        if (len(identity) != 16 or not identity.isdigit()
                or raw[3:11].decode("ascii", errors="replace") > capture_day):
            raise CoverageError("Current race key or date invalid")
        if kind == b"RA":
            old = today_ra.get(identity)
            if old is not None and old != raw:
                raise CoverageError("Conflicting current race record")
            today_ra[identity] = raw
        else:
            key = (identity, raw[28:30])
            old = today_se.get(key)
            if old is not None and old != raw:
                raise CoverageError("Conflicting current horse record")
            today_se[key] = raw
            # The past-record parser decodes registration IDs to ASCII str.
            # Compare str to str, not bytes to str (which silently loses runs).
            try:
                joined_ids.add(raw[30:40].decode("ascii"))
            except UnicodeDecodeError:
                raise CoverageError("Invalid current horse registration ID") from None
    if not today_ra or len(today_ra) > MAX_RACE_CARDS:
        raise CoverageError("No bounded day race roster")
    if {key[0] for key in today_se} != set(today_ra):
        raise CoverageError("Incomplete day horse roster")

    related_history, related_keys = [], set()
    for raw in history_records:
        if not isinstance(raw, bytes) or len(raw) < 3:
            raise CoverageError("Invalid local RCVN record")
        if raw[:3] == b"SE7":
            _require_record(raw, b"SE", b"7", SE_LENGTH)
            # RCVN may include history for many other horses and venues.
            # Inspect only the registered IDs on the current racecard.
            if raw[30:40].decode("ascii", errors="replace") not in joined_ids:
                continue
            horse_id, key = _past_result_identity(raw, day)
            if raw[3:11].decode("ascii") > capture_day:
                raise CoverageError("Post-capture historical record")
            if horse_id in joined_ids:
                related_history.append(raw)
                related_keys.add(key)
        elif raw[:3] != b"RA7":
            raise CoverageError("Unexpected local historical record type")

    needed_ra_ids = {
        (key[0] + key[1] + key[2] + key[3] + key[4]).encode("ascii")
        for key in related_keys
    }
    past_race_info = {}
    for raw in history_records:
        if raw[:3] != b"RA7":
            continue
        _require_record(raw, b"RA", b"7", RA_LENGTH)
        if raw[11:27] not in needed_ra_ids:
            # Unrelated historical races should not block another horse.
            continue
        key, _ = _historical_ra_context(raw, day, capture_day)
        existing = past_race_info.get(key)
        if existing is not None and existing != raw:
            raise CoverageError("Conflicting historical race records")
        past_race_info[key] = raw

    prior_ra = [past_race_info[key] for key in sorted(related_keys)
                if key in past_race_info]
    by_key = {}
    for identity in sorted(today_ra):
        se = [row for (key, _), row in today_se.items() if key == identity]
        preview = preview_jvdata_horse_history(
            today_ra[identity], se, related_history, day,
            historical_ra=prior_ra, captured_at=captured_at,
        )
        coord = preview["track"], preview["race"]
        if coord in by_key:
            raise CoverageError("Duplicate current venue/race")
        by_key[coord] = {
            "track": coord[0], "race": coord[1],
            "status": preview["status"],
            "byNumber": preview["byNumber"],
            "observedHorseHistory": sum(
                bool(h["observedRecordCount"]) for h in preview["byNumber"]
            ),
            "historyComplete": False, "graded": False,
            "bettingReady": False,
        }

    return {
        "version": VERSION, "date": day,
        "raceCount": len(by_key),
        "races": [by_key[k] for k in sorted(by_key)],
        "historySource": "private_jvlink_rcvn_partial_observations",
        "historyCompletenessVerified": False,
        "captureTimeIndependentlyVerified": False,
        "officialStarterListVerified": False,
        "officialScratchStateVerified": False,
        "officialGoingVerified": False,
        "formalTenFactorReady": False,
        "productionPredictionReady": False,
        "bettingReady": False,
        "autoPurchase": False,
        "newProviderRequests": 0,
        "privateOwnerOnly": True, "researchOnly": True,
        "note": (
            "RACE候補馬番にRCVN過去SE7/RA7を照合。資料不足は未出走と断定しない。"
            "履歴の完備性・配信時刻・当日取消は未検証。"
            "正式採点や馬券・外部送信は行わない。"
        ),
    }
