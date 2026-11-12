"""Owner-private 10-factor automatic prediction CONTRACT, phase 1.

Ten evaluated factors are required to publish an overall score; source field
presence is never a grade. The current JRDB /tra-/tze four-call pipeline only
supports experimental training + recent grades. This helper makes the eight
missing factor slots visible while preserving separate two-factor research
tickets and the strict no-retroactive-ranking rule.

No extra provider calls, source rows, prediction claims, or purchases.
"""
from evaluation_policy import (OWNER_FORMAL_FACTORS as FACTORS, CORE,
    OWNER_FORMAL_POLICY_VERSION as POLICY_VERSION, TOTAL_WEIGHT, SCORE_THRESHOLDS)
from jrdb_coverage import CoverageError
from jrdb_factor_preflight import FACTOR_LABELS
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION
from jrdb_owner_runner_research import VALUES
from evaluation_policy import POINTS

VERSION = "owner-ten-factor-contract-1"
GRADE = frozenset(VALUES)
UNASSESSED = "未評価"
PROVISIONAL = frozenset(("training", "recent"))
# A full 10-factor score may ONLY become available when every factor has
# separately verified, prestart evidence (a future pipeline, not this one).
FULL_COUNT = 10


def definition():
    if (len(FACTORS) != FULL_COUNT or sum(FACTORS.values()) != TOTAL_WEIGHT
            or TOTAL_WEIGHT != 100
            or set(FACTOR_LABELS) != set(FACTORS)
            or not CORE.issubset(FACTORS)
            or set(PROVISIONAL) - set(FACTORS)):
        raise CoverageError("Ten-factor policy contract changed")
    return [
        {"key": key, "label": FACTOR_LABELS[key],
         "weight": weight, "core": key in CORE}
        for key, weight in FACTORS.items()
    ]


def ten_factor_contract(two_factor_drafts):
    """Convert validated private 2-factor findings to 10 explicit slots.

    This is a display-level specification, NOT a fully graded prediction.
    Neither an off-time race nor an archived-vs-current conflict may get
    a new derived ranking, new ticket, or new score here.
    """
    specs = definition()
    if (not isinstance(two_factor_drafts, dict)
            or two_factor_drafts.get("version") != DRAFT_VERSION
            or two_factor_drafts.get("researchOnly") is not True
            or two_factor_drafts.get("privateOwnerOnly") is not True
            or any(two_factor_drafts.get(k) is not False for k in (
                "officialJraVerified", "overallPredictionReady",
                "bettingReady", "autoPurchase"))
            or not isinstance(two_factor_drafts.get("races"), list)
            or len(two_factor_drafts["races"]) > 120
            or two_factor_drafts.get("raceCount")
            != len(two_factor_drafts["races"])):
        raise CoverageError("Invalid ten-factor input snapshot")
    output = []
    seen = set()
    for race in two_factor_drafts["races"]:
        if (not isinstance(race, dict)
                or race.get("status") not in ("hold", "provisional_draft")
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or not isinstance(race.get("track"), str)
                or not isinstance(race.get("runners"), list)
                or len(race["runners"]) > 18):
            raise CoverageError("Invalid ten-factor race")
        coord = (race["track"], race["race"])
        if coord in seen:
            raise CoverageError("Repeated ten-factor race")
        seen.add(coord)
        numbers, horses, watch = set(), [], []
        for raw in race["runners"]:
            if (not isinstance(raw, dict)
                    or type(raw.get("number")) is not int
                    or not 1 <= raw["number"] <= 18
                    or raw["number"] in numbers
                    or any(raw.get(key) not in GRADE | {UNASSESSED}
                           for key in PROVISIONAL)):
                raise CoverageError("Invalid ten-factor runner")
            numbers.add(raw["number"])
            # Low recent grade is NOT a veto on a well-trained horse.
            # This watch list is NOT a winner selection or new bet, and is
            # limited to races with prestart provisional drafts.
            if (race["status"] == "provisional_draft"
                    and raw["training"] in ("S", "A")
                    and raw["recent"] in ("B", "C")):
                watch.append(raw["number"])
            slots = {key: (raw[key] if key in PROVISIONAL else UNASSESSED)
                     for key in FACTORS}
            n_provisional = sum(slots[k] in GRADE for k in PROVISIONAL)
            # Factor WEIGHT COVERAGE is not an earned ability score.
            # Even a provisional 'S' here cannot count as verified points.
            # Prioritize future evidence by the owner's 100-point policy,
            # never silently fill the other eight factors with grade C.
            provisional_weight = sum(
                weight for key, weight in FACTORS.items()
                if key in PROVISIONAL and slots[key] in GRADE
            )
            missing = [key for key in FACTORS if slots[key] == UNASSESSED]
            priority_missing = sorted(
                missing, key=lambda key: (-FACTORS[key], list(FACTORS).index(key))
            )
            # Already computed provisional S/A/B/C -> integer contribution.
            # Weight/3 converts ordinal thirds to the owner 100-point scale.
            # Missing categories are NULL, not zero. Held/off-time races
            # never receive a new numeric research score.
            breakdown = {
                key: (POINTS[slots[key]] * FACTORS[key] // 3
                      if slots[key] in GRADE and race["status"] == "provisional_draft"
                      else None)
                for key in PROVISIONAL
            }
            partial_ready = all(value is not None for value in breakdown.values())
            provisional_points = sum(breakdown.values()) if partial_ready else None
            if partial_ready and raw.get("weightedResearchPoints") != provisional_points * 3:
                raise CoverageError("Provisional grade and research order mismatch")
            horses.append({
                "number": raw["number"], "grades": slots,
                "provisionalBreakdown": breakdown,
                "provisionalPoints33": provisional_points,
                "provisionalScoreReady": partial_ready,
                "provisionalMaxPoints": 33,
                "provisionalFactorCount": n_provisional,
                "provisionalWeightCapacity": provisional_weight,
                "unassessedWeightCapacity": 100 - provisional_weight,
                "verifiedWeightCapacity": 0,
                "priorityMissingFactors": priority_missing,
                "verifiedFactorCount": 0, "score": None,
                "overallGrade": UNASSESSED, "overallRank": None,
                "missing": missing,
            })
        output.append({
            "track": race["track"], "race": race["race"],
            "runnerCount": len(horses), "horses": horses,
            "fullTenFactorCount": 0, "overallReady": False,
            "sourceGradeMode": "two_factor_provisional_only",
            "trainingLedRecheckNumbers": sorted(watch),
            "trainingLedRecheckNeeds": ["course_distance", "pace", "ground"],
            "trainingLedRecheckIsWinPick": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "factorCount": FULL_COUNT, "totalWeight": TOTAL_WEIGHT,
        "normalization": "weighted_mean_over_100",
        "gradeThresholds": dict(SCORE_THRESHOLDS),
        "scoreUnit": "0_to_100",
        "factors": specs,
        "raceCount": len(output), "fullPredictionRaceCount": 0,
        "researchOnly": True, "overallPredictionReady": False,
        "officialJraVerified": False, "autoPurchase": False,
        "requiredForOverall": "all_ten_verified_before_start",
        "races": output,
    }
