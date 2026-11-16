"""Connect the REAL owner day/runner coordinates to the formal 10-factor gate.

This is an intentionally fail-closed SHADOW run using the same 4 already
fetched JRDB sources. The live 2-factor S/A/B/C and optional 5-factor rule
outputs have NOT been historically calibrated or JRA-independently verified.
For that reason NONE of those observations may be promoted into formal
grades. Only date, venue, race, scheduled post and horse numbers are handed
to the existing formal day gate; all ten assessments are UNASSESSED.

This is the integration seam for a future trusted evidence adapter. It makes
the existing formal evaluator run against real day coordinates and exposes
anonymized missing-evidence counts without changing tickets, signed receipts,
ROI, JRA claims, purchases or paid API calls.
"""
import re
from datetime import datetime, timedelta, timezone

from evaluation_policy import OWNER_FORMAL_FACTORS as FACTORS
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION
from jrdb_program_preview import TRACKS
from owner_ten_factor_contract import VERSION as TEN_VERSION
from owner_full_ten_day_gate import full_ten_day_research

VERSION = "owner-live-formal-shadow-1"
JST = timezone(timedelta(hours=9))
TIME = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z", re.ASCII)
MAX_RACES = 36
EXPERIMENTAL = {"training", "recent"}
RACE_STATES = frozenset(("blocked_missing_verified_evidence",
                         "past_off_no_retroactive_gate",
                         "roster_or_schedule_unavailable"))
assert len(FACTORS) == 10 and sum(FACTORS.values()) == 100


def _index(rows):
    if not isinstance(rows, list) or len(rows) > MAX_RACES:
        raise CoverageError("Formal shadow day race list invalid")
    found = {}
    for row in rows:
        if (not isinstance(row, dict) or row.get("track") not in TRACKS.values()
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoverageError("Formal shadow race identity invalid")
        key = row["track"], row["race"]
        if key in found:
            raise CoverageError("Formal shadow duplicate race")
        found[key] = row
    return found


def live_formal_gate_shadow(report, day, *, now):
    """Use only same-day coordinates, NEVER the unverified factor grades.

    A malformed one-R roster is held locally. A missing/repeated/foreign
    race or changed day/contract blocks the entire optional audit.
    """
    if (not _valid_date(day) or not isinstance(now, datetime)
            or now.tzinfo is None or now.utcoffset() is None
            or not isinstance(report, dict)
            or report.get("version") != DRAFT_VERSION
            or report.get("date") != day
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("officialJraVerified") is not False
            or report.get("overallPredictionReady") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False
            or type(report.get("raceCount")) is not int
            or not 0 <= report["raceCount"] <= MAX_RACES):
        raise CoverageError("Formal shadow untrusted research contract")
    ten = report.get("tenFactorPreview")
    if (not isinstance(ten, dict)
            or ten.get("version") != TEN_VERSION
            or ten.get("policyVersion") != "research-6"
            or ten.get("fullPredictionRaceCount") != 0
            or ten.get("overallPredictionReady") is not False
            or ten.get("officialJraVerified") is not False
            or ten.get("autoPurchase") is not False):
        raise CoverageError("Formal shadow unverified ten-factor contract")
    original = _index(report.get("races"))
    mapped = _index(ten.get("races"))
    if (set(original) != set(mapped)
            or len(original) != report["raceCount"]
            or ten.get("raceCount") != len(mapped)):
        raise CoverageError("Formal shadow day/venue/race sets differ")
    now_jst = now.astimezone(JST)
    candidates, outside, unavailable = [], [], []
    for key in sorted(original):
        draft, ten_race = original[key], mapped[key]
        if (draft.get("status") not in ("hold", "provisional_draft")
                or ten_race.get("fullTenFactorCount") != 0
                or ten_race.get("overallReady") is not False
                or ten_race.get("sourceGradeMode") != "two_factor_provisional_only"
                or ten_race.get("trainingLedRecheckIsWinPick") is not False):
            raise CoverageError("Formal shadow cannot accept promoted evidence")
        post = draft.get("postTime")
        if type(post) is not str or not TIME.fullmatch(post):
            unavailable.append(key)
            continue
        off = datetime.strptime(day + post, "%Y%m%d%H:%M").replace(tzinfo=JST)
        # A completed race may intentionally have its runner list removed
        # by the upstream safe expiry gate. Check the off-time FIRST,
        # never reconstruct a roster from an expired signed research draft.
        if now_jst >= off:
            outside.append(key)
            continue
        raw, shadows = draft.get("runners"), ten_race.get("horses")
        if not isinstance(raw, list) or not isinstance(shadows, list):
            raise CoverageError("Formal shadow expected redacted runner lists")
        if (len(raw) != len(shadows)
                or ten_race.get("runnerCount") != len(raw)
                or len(raw) > 18):
            unavailable.append(key)
            continue
        ids, verified = set(), {}
        safe = True
        for horse in raw:
            n = horse.get("number") if isinstance(horse, dict) else None
            if (type(n) is not int or not 1 <= n <= 18 or n in ids
                    or horse.get("training") not in ("S", "A", "B", "C", "未評価")
                    or horse.get("recent") not in ("S", "A", "B", "C", "未評価")):
                safe = False
                break
            ids.add(n)
        if safe:
            for horse in shadows:
                n = horse.get("number") if isinstance(horse, dict) else None
                grades = horse.get("grades") if isinstance(horse, dict) else None
                if (type(n) is not int or n in verified
                        or not isinstance(grades, dict)
                        or set(grades) != set(FACTORS)
                        or horse.get("verifiedFactorCount") != 0
                        or horse.get("verifiedWeightCapacity") != 0
                        or horse.get("overallGrade") != "未評価"
                        or horse.get("overallRank") is not None
                        or horse.get("score") is not None
                        or any(grades.get(k) != "未評価"
                               for k in FACTORS if k not in EXPERIMENTAL)):
                    safe = False
                    break
                verified[n] = grades
        if not safe or set(verified) != ids:
            unavailable.append(key)
            continue
        by_number = {h["number"]: h for h in raw}
        if any(verified[n]["training"] != by_number[n]["training"]
               or verified[n]["recent"] != by_number[n]["recent"]
               for n in ids):
            unavailable.append(key)
            continue
        if len(ids) < 4:
            unavailable.append(key)
            continue
        # Important: 'owner_verified_prestart_v1' is an INTERNAL input
        # shape, NOT proof of origin. Approval flags stay explicitly FALSE
        # and *every* factor stays 未評価 even if JRDB supplied an S.
        snapshot = {
            "mode": "owner_verified_prestart_v1",
            "track": key[0], "race": key[1],
            "asOf": now_jst.isoformat(), "offAt": off.isoformat(),
            "independentJra": {
                "jra_starters_verified": False,
                "jra_scratches_verified": False,
                "jra_going_verified": False,
                "jra_posttime_verified": False,
            },
            "assessmentValidated": False, "predictionValidated": False,
            "horses": [{
                "number": n,
                "assessments": {factor: {"grade": "未評価"} for factor in FACTORS},
            } for n in sorted(ids)],
        }
        candidates.append({"track": key[0], "race": key[1],
                           "snapshot": snapshot})
    checked = full_ten_day_research(day, candidates, now=now)
    if (checked["raceCount"] != len(candidates)
            or checked["fullTenResearchRankRaces"] != 0
            or checked["researchFormationRaces"] != 0
            or checked["newProviderRequests"] != 0
            or checked["productionPredictionReady"] is not False
            or checked["independentJraFeedConnected"] is not False
            or any(r["status"] != "missing_evidence"
                   or r["reviewOnlyTicketCount"] != 0
                   or r["preview"]["ranking"]
                   or r["preview"]["trifecta"]["tickets"]
                   for r in checked["races"])):
        raise CoverageError("Formal shadow unexpectedly generated predictions")
    # Return only aggregate race statuses, not a 10-factor assessment or
    # the internal source/provisional grades. No horse identities or keys.
    statuses = {key: "blocked_missing_verified_evidence"
                for key in ((x["track"], x["race"]) for x in candidates)}
    statuses.update({key: "past_off_no_retroactive_gate" for key in outside})
    statuses.update({key: "roster_or_schedule_unavailable" for key in unavailable})
    if set(statuses) != set(original) or not set(statuses.values()) <= RACE_STATES:
        raise CoverageError("Formal shadow lost a day race")
    return {
        "version": VERSION, "date": day, "raceCount": len(original),
        "prestartFormalGateRuns": len(candidates),
        "blockedMissingEvidenceRaces": len(candidates),
        "pastOffRaces": len(outside),
        "rosterOrTimeUnavailableRaces": len(unavailable),
        "verifiedFormalFactorCount": 0, "verifiedTotalScoreCount": 0,
        "formalTrifectaCount": 0, "officialJraVerified": False,
        "overallPredictionReady": False, "bettingReady": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "newProviderRequests": 0, "ticketsIssued": 0,
        "changesExistingDrafts": False, "changesExistingReceipts": False,
        "races": [
            {"track": key[0], "race": key[1], "status": statuses[key],
             "formalScoreReady": False, "officialJraVerified": False,
             "bettingReady": False}
            for key in sorted(original)
        ],
        "note": ("当日の実開催日・競馬場・馬番と発走時刻だけを正式10項目ゲート"
                 "へ試験接続。JRDBの7項目研究値や調教・近走の仮評価を"
                 "正式採点へ昇格させず、10項目全て未評価・正式3連単0点。"
                 "今後の独立JRA照合・時系列検証済み採点の接続先。"),
    }
