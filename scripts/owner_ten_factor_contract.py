"""Owner-private 10-factor automatic prediction CONTRACT, phase 1.

Ten evaluated factors are required to publish an overall score; source field
presence is never a grade. The current JRDB /tra-/tze four-call pipeline only
supports experimental training + recent grades. This helper makes the eight
missing factor slots visible while preserving separate two-factor research
tickets and the strict no-retroactive-ranking rule.

No extra provider calls, source rows, prediction claims, or purchases.
"""
from evaluation_policy import FACTORS, CORE, POLICY_VERSION, TOTAL_WEIGHT, SCORE_THRESHOLDS
from jrdb_coverage import CoverageError
from jrdb_factor_preflight import FACTOR_LABELS
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION
from jrdb_owner_runner_research import VALUES

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
        numbers, horses = set(), []
        for raw in race["runners"]:
            if (not isinstance(raw, dict)
                    or type(raw.get("number")) is not int
                    or not 1 <= raw["number"] <= 18
                    or raw["number"] in numbers
                    or any(raw.get(key) not in GRADE | {UNASSESSED}
                           for key in PROVISIONAL)):
                raise CoverageError("Invalid ten-factor runner")
            numbers.add(raw["number"])
            slots = {key: (raw[key] if key in PROVISIONAL else UNASSESSED)
                     for key in FACTORS}
            n_provisional = sum(slots[k] in GRADE for k in PROVISIONAL)
            horses.append({
                "number": raw["number"], "grades": slots,
                "provisionalFactorCount": n_provisional,
                "verifiedFactorCount": 0, "score": None,
                "overallGrade": UNASSESSED, "overallRank": None,
                "missing": [key for key in FACTORS if slots[key] == UNASSESSED],
            })
        output.append({
            "track": race["track"], "race": race["race"],
            "runnerCount": len(horses), "horses": horses,
            "fullTenFactorCount": 0, "overallReady": False,
            "sourceGradeMode": "two_factor_provisional_only",
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
