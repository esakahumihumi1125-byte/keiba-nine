"""Private, offline first-stage horse-history join for JRA-VAN RCVN records.

RCVN (the successor to RCOV) may supply prior horse-result SE records.
This module does NOT call JV-Link, consume a subscription, parse result
performance statistics, or assign formal ARC RACE grades. It verifies that
a historical SE result belongs to a currently numbered SE racecard horse,
using the internal 10-digit registered horse ID, then discards that ID.

Never send original RCVN rows, horse IDs or this private horse-by-number
coverage to a public endpoint. The caller must supply a bounded, licensed
prestart snapshot and independently establish collection rights.
"""
from datetime import datetime, timedelta, timezone

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from jvdata_ra_se_candidate import (
    SE_LENGTH, _ascii, parse_jvdata_prestart_racecard,
)

VERSION = "owner-jvdata-horse-history-coverage-1"
HISTORY_DATA_SPEC = "RCVN"  # Deprecated RCOV must never be used.
MAX_HISTORY_RECORDS = 10000
JST = timezone(timedelta(hours=9))


def _past_result_identity(record, target_day):
    """Strictly parse only completed historical SE category 7 (555 bytes)."""
    if (type(record) is not bytes or len(record) != SE_LENGTH
            or record[:3] != b"SE7" or record[-2:] != b"\r\n"):
        raise CoverageError("Unsupported historical horse result record")
    created = _ascii(record, 3, 11)
    year, month_day = _ascii(record, 11, 15), _ascii(record, 15, 19)
    venue = _ascii(record, 19, 21)
    meeting = _ascii(record, 21, 23)
    meeting_day = _ascii(record, 23, 25)
    race = _ascii(record, 25, 27)
    horse_id = _ascii(record, 30, 40)
    racedate = year + month_day
    # Record creation can follow the historical race. But a later correction
    # cannot be used in a historical as-of replay before it existed.
    if (not _valid_date(created) or not _valid_date(racedate)
            or racedate >= target_day or created > target_day
            or venue not in TRACKS
            or not 1 <= int(meeting) <= 12
            or not 1 <= int(meeting_day) <= 12
            or not 1 <= int(race) <= 12
            or horse_id == "0000000000"):
        raise CoverageError("Historical race identity or cutoff mismatch")
    return horse_id, (racedate, venue, meeting, meeting_day, race)


def audit_jvdata_horse_history(current_ra, current_se, historical_se, day,
                               *, captured_at):
    """Return sanitized prestart history-coverage diagnostics, never grades.

    Current SE category-2 rows identify today's horse numbers. Historical SE
    category-7 rows are matched via internal registration ID and deduplicated
    by their original race identity. Other horses' history is not promoted.
    Even if locally captured before scheduled off, source availability,
    final starters, grades, and the user's data rights remain unverified.

    NOTE: A missing RCVN row is NOT proof that a horse has never raced.
    """
    racecard = parse_jvdata_prestart_racecard(current_ra, current_se, day)
    if (not isinstance(historical_se, (list, tuple))
            or len(historical_se) > MAX_HISTORY_RECORDS):
        raise CoverageError("Invalid historical record batch")
    if (not isinstance(captured_at, datetime)
            or captured_at.tzinfo is None or captured_at.utcoffset() is None):
        raise CoverageError("Untrusted local history capture clock")

    off_at = datetime.strptime(
        day + racecard["postTimeCandidate"], "%Y%m%d%H:%M"
    ).replace(tzinfo=JST)
    before_off = captured_at.astimezone(JST) < off_at

    # The existing racecard parser has already rejected duplicate IDs,
    # foreign races, duplicate horse numbers, invalid dates and counts.
    ids = {
        _ascii(record, 30, 40): int(_ascii(record, 28, 30))
        for record in current_se
    }
    histories = {number: {} for number in ids.values()}
    for raw in historical_se:
        horse_id, prior_race = _past_result_identity(raw, day)
        number = ids.get(horse_id)
        if number is None:
            continue
        old = histories[number].get(prior_race)
        if old is not None and old != raw:
            raise CoverageError("Conflicting historical SE result updates")
        histories[number][prior_race] = raw

    by_number = [{
        "number": number,
        "observedPriorResultRecords": len(histories[number]) if before_off else 0,
        "historyCoverageComplete": False,
        "historyResultGrade": None,
        "formalFactorAssessment": None,
    } for number in sorted(histories)]
    return {
        "version": VERSION,
        "sourceDataSpec": HISTORY_DATA_SPEC,
        "date": day,
        "track": racecard["track"], "race": racecard["race"],
        "status": (
            "post_off_capture_hold" if not before_off
            else "linked_history_observed_not_graded" if any(histories.values())
            else "no_matched_history_observed"
        ),
        "runnerCount": len(by_number),
        "runnersWithObservedHistory": (
            sum(bool(histories[number]) for number in histories)
            if before_off else 0
        ),
        "byNumber": by_number,
        "historyCoverageComplete": False,
        "prestartDeliveryIndependentlyVerified": False,
        "finalJraStartersVerified": False,
        "historyOutcomeFieldsInterpreted": False,
        "trainingDataImported": False,
        "pedigreeDataImported": False,
        "formalTenFactorReady": False,
        "predictionReady": False,
        "bettingReady": False,
        "autoPurchase": False,
        "extraProviderRequests": 0,
        "privateOwnerOnly": True,
        "researchOnly": True,
        "note": (
            "RCVNの過去SE結果レコードを当日の馬番候補へ内部照合した件数のみ。"
            "未観測は未出走の証明ではない。成績・調教・血統の採点と公式最終照合は未実装。"
        ),
    }
