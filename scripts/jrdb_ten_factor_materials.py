"""Join private race-level evidence counts into a ten-factor MATERIALS checklist.

This is NOT a grade, AI assessment, model confidence, live tip or purchase
signal. The caller must provide snapshots from the SAME date/private request.
Only fixed labels and coarse counts are exported; never return horse-level JRDB
data, credentials, racekeys, assessed scores or other source strings.
"""
from evaluation_policy import FACTORS, CORE
from jrdb_factor_preflight import audit_assessment_preflight, FACTOR_LABELS
from jrdb_program_preview import TRACKS

VERSION = "ten-factor-materials-1"
HISTORY_CATEGORIES = ("none", "oneOrTwo", "threePlus")
UNMAPPED = "not_mapped_from_provider"


def _count(value, upper):
    if type(value) is not int or not 0 <= value <= upper:
        raise ValueError("Invalid aggregated runner count")
    return value


def _samples(value, runner_count):
    if not isinstance(value, dict) or set(value) != set(HISTORY_CATEGORIES):
        raise ValueError("Invalid historic sample categories")
    counts = {k: _count(value[k], runner_count) for k in HISTORY_CATEGORIES}
    if sum(counts.values()) != runner_count:
        raise ValueError("Historical sample bucket total differs from entries")
    return counts["oneOrTwo"] + counts["threePlus"]


def combine_ten_factor_materials(evidence_audit, historical_quality, *,
                                 bounded_history_complete):
    """Produce a fully redacted, non-predictive checklist for each race.

    Both inputs must originate from the same private validated source snapshot.
    Historical *lookup* completeness never means suitability or win probability.
    """
    if type(bounded_history_complete) is not bool:
        raise ValueError("Invalid bounded history flag")
    preflight = audit_assessment_preflight(evidence_audit)
    if (not isinstance(historical_quality, dict)
            or historical_quality.get("predictionReady") is not False
            or historical_quality.get("suitabilityAssessed") is not False
            or historical_quality.get("predictionConfidenceAssessed") is not False
            or not isinstance(historical_quality.get("races"), list)
            or len(historical_quality["races"]) > 120
            or historical_quality.get("raceCount") != len(historical_quality["races"])):
        raise ValueError("Invalid historical research status")
    past_index = {}
    for item in historical_quality["races"]:
        if not isinstance(item, dict):
            raise ValueError("Invalid historical race")
        key = (item.get("track"), item.get("race"))
        if (key[0] not in TRACKS.values() or type(key[1]) is not int
                or not 1 <= key[1] <= 12 or key in past_index
                or item.get("predictionReady") is not False
                or item.get("suitabilityAssessed") is not False
                or item.get("predictionConfidenceAssessed") is not False):
            raise ValueError("Duplicate or unverified historical race")
        past_index[key] = item
    seen = set()
    result = []
    for race in preflight["races"]:
        key = (race["track"], race["race"])
        if key in seen or key not in past_index:
            raise ValueError("Missing or duplicate historic race")
        seen.add(key)
        past = past_index[key]
        runners = _count(race["observedEntries"], 18)
        if type(past.get("runnerCount")) is not int or past["runnerCount"] != runners:
            raise ValueError("Runner identities / counts do not agree")
        if type(past.get("currentGoingRecorded")) is not bool:
            raise ValueError("Unknown current going presence flag")
        past_unlinked = _count(past.get("unlinkedPastRuns"), 5 * runners)
        distance_count = _samples(past.get("courseComparableSamples"), runners)
        going_count = _samples(past.get("knownGoingComparableSamples"), runners)
        # Both numbers are observable subsets, never predictive grades.
        if going_count > distance_count:
            raise ValueError("Known going comparables cannot exceed course comparables")
        raw = next((r for r in evidence_audit["races"]
                    if r["track"] == key[0] and r["race"] == key[1]), None)
        if not isinstance(raw, dict):
            raise ValueError("Missing source race")
        counts = {
            "training": _count(raw.get("trainingRecords"), runners),
            "recent": _count(raw.get("pastRunRecords"), runners),
            "course_distance": distance_count,
            "ground": going_count,
        }
        factors = {}
        observed_factors = 0
        for factor in FACTORS:
            observed = counts.get(factor)
            if factor == "ground" and not past["currentGoingRecorded"]:
                status = "current_going_unverified"
            elif factor in ("course_distance", "ground") and not bounded_history_complete:
                status = "historical_lookup_incomplete"
            elif observed is None:
                status = UNMAPPED
            elif observed == 0:
                status = "no_comparable_records_observed"
            elif observed < runners:
                status = "partial_observed_records"
            else:
                status = "observed_record_count_matches"
            if observed is not None and observed > 0:
                observed_factors += 1
            factors[factor] = {
                "label": FACTOR_LABELS[factor],
                "sourceStatus": status,
                "observedRunnerCount": observed,
                "grade": "未評価",
                "assessmentComplete": False,
                "requiredForCore": factor in CORE,
            }
        result.append({
            "track": key[0], "race": key[1],
            "runnerCount": runners, "observedFactorCount": observed_factors,
            "unlinkedPastRuns": past_unlinked,
            "pastLookupIncomplete": not bounded_history_complete or past_unlinked > 0,
            "factors": factors,
            "gradedFactors": 0,
            "independentEntriesVerified": False,
            "scratchesVerified": False,
            "oddsUsed": False,
            "predictionConfidenceAssessed": False,
            "predictionReady": False,
            "bettingReady": False,
        })
    if set(past_index) != seen or len(result) != preflight["raceCount"]:
        raise ValueError("Research snapshots refer to different race sets")
    return {
        "version": VERSION,
        "raceCount": len(result),
        "factorCount": len(FACTORS),
        "gradedFactors": 0,
        "predictionReady": False,
        "bettingReady": False,
        "predictionConfidenceAssessed": False,
        "races": result,
        "note": ("調教・近走の資料件数と過去距離・馬場の比較履歴頭数を"
                 "10項目の資料表に統合。後半6項目は未接続、全10項目が未評価。"
                 "件数一致・過去走の存在は能力や勝率の証明ではなく、"
                 "出馬表・取消・馬場の最終確認や実戦の3連単は未実施。"),
    }
