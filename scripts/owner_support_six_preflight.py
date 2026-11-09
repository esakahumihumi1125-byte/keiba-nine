"""Research-only evidence readiness for draw/weight, jockey/stable and rotation.

The source inventory contains bracket, carried-weight, personnel and
last-run-interval *presence*, but no validated conditional effects or future
performance. Keep all six possible factor points ungraded. No provider calls,
raw JRDB values, market inputs, predictions, receipts, purchases or ROI.
"""
from evaluation_policy import FACTORS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_ten_factor_source_inventory import VERSION as SOURCE_VERSION

VERSION = "owner-support-six-preflight-1"
KEYS = ("draw_weight", "jockey_stable", "rotation")
WEIGHTS = {k: FACTORS[k] for k in KEYS}
WEIGHT_TOTAL = 6
STATES = frozenset((
    "complete_fields_observed", "partial_fields_observed", "no_fields_observed"
))
ROTATION = frozenset(("under14Days", "days14to55", "days56plus", "unknown"))
GAPS = {
    "draw_weight": ("draw_or_carried_weight_missing",
                    "field_and_weight_effects_unvalidated",
                    "temporal_holdout_not_validated"),
    "jockey_stable": ("jockey_or_trainer_missing",
                     "comparable_personnel_performance_unvalidated",
                     "temporal_holdout_not_validated"),
    "rotation": ("last_run_interval_missing",
                 "condition_matched_rotation_effect_unvalidated",
                 "temporal_holdout_not_validated"),
}
assert sum(WEIGHTS.values()) == WEIGHT_TOTAL


def support_six_preflight(inventory):
    """Check same-roster three-source availability, never grade six points."""
    if (not isinstance(inventory, dict)
            or inventory.get("version") != SOURCE_VERSION
            or inventory.get("policyVersion") != POLICY_VERSION
            or inventory.get("factorWeights") != FACTORS
            or inventory.get("factorCount") != 10
            or inventory.get("totalWeight") != 100
            or inventory.get("verifiedGrades") != 0
            or inventory.get("researchOnly") is not True
            or inventory.get("privateOwnerOnly") is not True
            or inventory.get("independentJraVerified") is not False
            or inventory.get("overallPredictionReady") is not False
            or inventory.get("bettingReady") is not False
            or inventory.get("autoPurchase") is not False
            or not isinstance(inventory.get("races"), list)
            or not 0 <= len(inventory["races"]) <= 120
            or inventory.get("raceCount") != len(inventory["races"])):
        raise CoverageError("Invalid six-point source inventory")

    result, seen = [], set()
    for race in inventory["races"]:
        if (not isinstance(race, dict)
                or not isinstance(race.get("track"), str) or not race["track"]
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or type(race.get("runnerCount")) is not int
                or not 0 <= race["runnerCount"] <= 18
                or race.get("verifiedGrades") != 0
                or race.get("overallReady") is not False
                or race.get("independentJraVerified") is not False
                or race.get("bettingReady") is not False
                or not isinstance(race.get("runners"), list)
                or len(race["runners"]) != race["runnerCount"]
                or not isinstance(race.get("remainingFieldCoverage"), dict)
                or set(race["remainingFieldCoverage"]) != {
                    "pedigree", "draw_weight", "jockey_stable",
                    "rotation", "body_condition"}):
            raise CoverageError("Invalid six-point race")
        identity = race["track"], race["race"]
        if identity in seen:
            raise CoverageError("Duplicate six-point race")
        seen.add(identity)
        numbers, horses = set(), []
        field_counts = dict.fromkeys(KEYS, 0)
        all_present = 0
        for raw in race["runners"]:
            if (not isinstance(raw, dict)
                    or type(raw.get("number")) is not int
                    or not 1 <= raw["number"] <= 18
                    or raw["number"] in numbers
                    or raw.get("verifiedGrades") != 0
                    or raw.get("overallScore") is not None
                    or raw.get("overallRank") is not None
                    or not isinstance(raw.get("sourceStates"), dict)
                    or set(raw["sourceStates"]) != {
                        "pedigree", "draw_weight", "jockey_stable",
                        "rotation", "body_condition"}):
                raise CoverageError("Invalid six-point runner")
            numbers.add(raw["number"])
            states = {k: raw["sourceStates"][k] for k in KEYS}
            if (states["draw_weight"] not in STATES
                    or states["jockey_stable"] not in STATES
                    or states["rotation"] not in ROTATION):
                raise CoverageError("Invalid six-point states")
            present = {
                "draw_weight": states["draw_weight"] == "complete_fields_observed",
                "jockey_stable": states["jockey_stable"] == "complete_fields_observed",
                "rotation": states["rotation"] != "unknown",
            }
            gaps = {
                k: ([] if present[k] else [GAPS[k][0]]) + list(GAPS[k][1:])
                for k in KEYS
            }
            for k in KEYS:
                field_counts[k] += int(present[k])
            all_present += all(present.values())
            horses.append({
                "number": raw["number"],
                "sourceStates": states,
                "fieldPresent": present,
                "fieldPresenceWeight": sum(WEIGHTS[k] for k in KEYS if present[k]),
                "missingEvidence": gaps,
                "grades": dict.fromkeys(KEYS, "未評価"),
                "scores": dict.fromkeys(KEYS, None),
                "conditionalEffectVerified": False,
                "outOfTimeValidated": False,
                "bettingReady": False,
            })
        for k in KEYS:
            if (type(race["remainingFieldCoverage"][k]) is not int
                    or race["remainingFieldCoverage"][k] != field_counts[k]):
                raise CoverageError("Six-point source coverage disagrees")
        horses.sort(key=lambda x: x["number"])
        result.append({
            "track": identity[0], "race": identity[1],
            "runnerCount": race["runnerCount"],
            "fieldCompleteCounts": field_counts,
            "allThreeFieldCompleteCount": all_present,
            "verifiedFactorCount": 0,
            "scoreReady": False,
            "horses": horses,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "factors": dict(WEIGHTS), "weightTotal": WEIGHT_TOTAL,
        "raceCount": len(result), "races": result,
        "verifiedFactorCount": 0,
        "conditionMatchedEffectValidated": False,
        "temporalValidationComplete": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "bettingReady": False, "autoPurchase": False,
        "changesExistingTickets": False, "changesExistingReceipts": False,
        "note": ("枠斤量3・騎手厩舎2・ローテ1の資料有無だけを照合。"
                 "同条件の効果と時系列検証が未完成のため実得点は全頭未評価。"
                 "買い目・固定履歴には反映しない。"),
    }
