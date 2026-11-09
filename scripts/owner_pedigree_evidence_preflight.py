"""Owner-only pedigree (8-weight) evidence gates; no inferred bloodline grade.

Existing /tky parent names prove only identity-field presence. Reliable course /
distance / going pedigree comparisons require an independent historical cohort
and out-of-time validation that this bounded JRDB history feed does not supply.
No provider calls, paywalled names, pedigree IDs, probabilities, tickets or ROI.
"""
from evaluation_policy import FACTORS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_ten_factor_source_inventory import VERSION as INVENTORY_VERSION

VERSION = "owner-pedigree-evidence-preflight-1"
STATES = frozenset((
    "complete_fields_observed", "partial_fields_observed", "no_fields_observed"
))
UNASSESSED = "未評価"
PARENTAGE_INCOMPLETE = "parentage_fields_incomplete"
COHORT_MISSING = "independent_condition_matched_cohort_unavailable"
HOLDOUT_MISSING = "temporal_holdout_not_validated"

assert FACTORS["pedigree"] == 8


def pedigree_evidence_preflight(inventory):
    """Validate the same race/horse roster, report *why* pedigree is ungraded.

    This stage never receives or searches a historical sire-performance cohort.
    It must therefore remain ungraded even for horses with both parent names.
    """
    if (not isinstance(inventory, dict)
            or inventory.get("version") != INVENTORY_VERSION
            or inventory.get("policyVersion") != POLICY_VERSION
            or inventory.get("factorCount") != 10
            or inventory.get("totalWeight") != 100
            or inventory.get("factorWeights") != FACTORS
            or inventory.get("researchOnly") is not True
            or inventory.get("privateOwnerOnly") is not True
            or inventory.get("independentJraVerified") is not False
            or inventory.get("overallPredictionReady") is not False
            or inventory.get("verifiedGrades") != 0
            or inventory.get("bettingReady") is not False
            or inventory.get("autoPurchase") is not False
            or not isinstance(inventory.get("races"), list)
            or not 0 <= len(inventory["races"]) <= 120
            or inventory.get("raceCount") != len(inventory["races"])):
        raise CoverageError("Invalid pedigree source inventory")

    output, seen = [], set()
    for race in inventory["races"]:
        if (not isinstance(race, dict)
                or not isinstance(race.get("track"), str)
                or not race["track"]
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
                or not isinstance(race.get("remainingFieldCoverage"), dict)):
            raise CoverageError("Invalid pedigree research race")
        coordinate = race["track"], race["race"]
        if coordinate in seen:
            raise CoverageError("Duplicate pedigree research race")
        seen.add(coordinate)
        horses, seen_numbers, completed = [], set(), 0
        for runner in race["runners"]:
            if (not isinstance(runner, dict)
                    or type(runner.get("number")) is not int
                    or not 1 <= runner["number"] <= 18
                    or runner["number"] in seen_numbers
                    or runner.get("verifiedGrades") != 0
                    or runner.get("overallScore") is not None
                    or runner.get("overallRank") is not None
                    or not isinstance(runner.get("sourceStates"), dict)):
                raise CoverageError("Invalid pedigree research runner")
            seen_numbers.add(runner["number"])
            source_state = runner["sourceStates"].get("pedigree")
            if source_state not in STATES:
                raise CoverageError("Invalid pedigree parentage state")
            complete = source_state == "complete_fields_observed"
            completed += complete
            missing = ([] if complete else [PARENTAGE_INCOMPLETE]) + [
                COHORT_MISSING, HOLDOUT_MISSING
            ]
            horses.append({
                "number": runner["number"],
                "parentageSourceState": source_state,
                "parentageComplete": complete,
                "independentCohortValidated": False,
                "conditionMatched": False,
                "outOfTimeCalibrated": False,
                "missingEvidence": missing,
                "grade": UNASSESSED,
                "score8": None,
                "bettingReady": False,
            })
        if (race["remainingFieldCoverage"].get("pedigree") != completed
                or type(race["remainingFieldCoverage"]["pedigree"]) is not int):
            raise CoverageError("Pedigree parentage count disagrees")
        horses.sort(key=lambda horse: horse["number"])
        output.append({
            "track": coordinate[0], "race": coordinate[1],
            "runnerCount": race["runnerCount"],
            "parentageCompleteCount": completed,
            "independentCohortValidatedCount": 0,
            "verifiedPedigreeGrades": 0,
            "horses": horses,
            "pedigreeScoreReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "factor": "pedigree", "weight": FACTORS["pedigree"],
        "raceCount": len(output), "races": output,
        "pedigreeGradesVerified": 0,
        "independentCohortAvailable": False,
        "temporalValidationComplete": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "bettingReady": False, "autoPurchase": False,
        "changesExistingTickets": False,
        "changesExistingReceipts": False,
        "note": ("血統8点は未評価。父・母父の資料だけでは適性は採点しない。"
                 "芝/ダート・距離・馬場別の独立血統実績母集団、"
                 "レース前時点の利用可能性、時系列の未使用期間検証が必要。"),
    }
