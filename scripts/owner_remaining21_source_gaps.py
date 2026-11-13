"""Research-6 source-gap map for the remaining 21/100 points.

This checks the *already-produced* private 79-weight hypothesis and old-policy
ten-factor source inventory, with no additional provider request. Source-field
presence is never a skill grade, a formal score or an invitation to bet.
"""
from evaluation_policy import (
    FACTORS as OLD, POLICY_VERSION as OLD_POLICY,
    OWNER_FORMAL_FACTORS as NEW, OWNER_FORMAL_POLICY_VERSION as NEW_POLICY,
    POINTS,
)
from jrdb_coverage import CoverageError
from jrdb_ten_factor_source_inventory import VERSION as INVENTORY_VERSION
from owner_new_weight_five_research import VERSION as STUDY_VERSION, KEYS as CORE

VERSION = "owner-remaining21-source-gaps-1"
KEYS = ("pedigree", "draw_weight", "jockey_stable", "rotation",
        "body_condition")
WEIGHTS = {key: NEW[key] for key in KEYS}
RESEARCH_WEIGHTS = {key: NEW[key] for key in CORE}
SOURCE_STATES = {"complete_fields_observed", "partial_fields_observed",
                 "no_fields_observed"}
INTERVALS = {"under14Days", "days14to55", "days56plus", "unknown"}
assert sum(WEIGHTS.values()) == 21 and sum(RESEARCH_WEIGHTS.values()) == 79

STEPS = {
    "pedigree": "父・母父の独立した同条件実績と時系列検証",
    "draw_weight": "枠と相対斤量の同条件成績と時系列検証",
    "jockey_stable": "騎手・厩舎の条件別成績と馬の能力差調整",
    "rotation": "前走間隔に応じた条件別成績と時系列検証",
    "body_condition": "発走前の当日馬体重と前走比・JRA独立確認",
}


def _indexed(races):
    if not isinstance(races, list) or len(races) > 120:
        raise CoverageError("Source gap races invalid")
    idx = {}
    for row in races:
        if (not isinstance(row, dict)
                or not isinstance(row.get("track"), str)
                or not row["track"] or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoverageError("Source gap race identity invalid")
        key = row["track"], row["race"]
        if key in idx:
            raise CoverageError("Duplicated source gap race")
        idx[key] = row
    return idx


def _horses(rows):
    if not isinstance(rows, list) or len(rows) > 18:
        raise CoverageError("Source gap runner list invalid")
    idx = {}
    for row in rows:
        if (not isinstance(row, dict) or type(row.get("number")) is not int
                or not 1 <= row["number"] <= 18 or row["number"] in idx):
            raise CoverageError("Source gap runner invalid")
        idx[row["number"]] = row
    return idx


def remaining21_source_gaps(study, inventory):
    """Join already-safe five-band and presence views by exact track/race/horse."""
    if (not isinstance(study, dict) or not isinstance(inventory, dict)
            or study.get("version") != STUDY_VERSION
            or study.get("policyVersion") != NEW_POLICY
            or study.get("sourcePolicyVersion") != OLD_POLICY
            or study.get("observedWeightTotal") != 79
            or study.get("factorWeights") != RESEARCH_WEIGHTS
            or study.get("factorGradesVerified") != 0
            or study.get("overallPredictionReady") is not False
            or study.get("formalScoreReady") is not False
            or study.get("officialJraVerified") is not False
            or study.get("bettingReady") is not False
            or study.get("autoPurchase") is not False
            or study.get("researchOnly") is not True
            or study.get("privateOwnerOnly") is not True
            or study.get("historicalBandsNotCalibrated") is not True
            or study.get("resultVerified") is not False
            or study.get("extraProviderCalls") != 0
            or inventory.get("version") != INVENTORY_VERSION
            or inventory.get("policyVersion") != OLD_POLICY
            or inventory.get("factorCount") != 10
            or inventory.get("totalWeight") != 100
            or inventory.get("factorWeights") != OLD
            or inventory.get("verifiedGrades") != 0
            or inventory.get("independentJraVerified") is not False
            or inventory.get("overallPredictionReady") is not False
            or inventory.get("bettingReady") is not False
            or inventory.get("autoPurchase") is not False
            or inventory.get("researchOnly") is not True
            or inventory.get("privateOwnerOnly") is not True):
        raise CoverageError("Study and source inventory policy mismatch")
    left, right = _indexed(study.get("races")), _indexed(inventory.get("races"))
    if (set(left) != set(right) or study.get("raceCount") != len(left)
            or inventory.get("raceCount") != len(right)):
        raise CoverageError("Source gap race set differs")
    result, ready_prior_total, bodies_missing = [], 0, 0
    for key in sorted(left):
        a, b = left[key], right[key]
        old = _horses(a.get("horses"))
        observed = _horses(b.get("runners"))
        if (set(old) != set(observed)
                or a.get("runnerCount") != len(old)
                or b.get("runnerCount") != len(observed)
                or a.get("researchOnly") is not True
                or a.get("formalGradeReady") is not False
                or a.get("trifectaReady") is not False
                or a.get("comparisonIsFormalRank") is not False
                or b.get("verifiedGrades") != 0
                or b.get("overallReady") is not False
                or b.get("independentJraVerified") is not False
                or b.get("bettingReady") is not False):
            raise CoverageError("Source gap rosters differ")
        coverage = dict.fromkeys(KEYS, 0)
        prior_ready = 0
        horses = []
        for n in sorted(old):
            h, source = old[n], observed[n]
            bands = h.get("bands")
            statuses = source.get("sourceStates")
            if (not isinstance(bands, dict) or set(bands) != set(CORE)
                    or not isinstance(statuses, dict) or set(statuses) != set(KEYS)
                    or source.get("verifiedGrades") != 0
                    or source.get("overallScore") is not None
                    or source.get("overallRank") is not None
                    or not isinstance(source.get("provisionalBands"), dict)
                    or set(source["provisionalBands"]) != set(CORE)
                    or source["provisionalBands"] != bands
                    or type(source.get("bodyShapeCodePresent")) is not bool
                    or h.get("scoreIsCalibrated") is not False
                    or h.get("formalGrade") != "未評価"
                    or h.get("formalScore100") is not None
                    or h.get("formalRank") is not None
                    or h.get("bettingReady") is not False
                    or not isinstance(h.get("missing"), list)
                    or type(h.get("observedFactorCount")) is not int):
                raise CoverageError("Source gap runner evidence mismatch")
            if (any(x not in (*POINTS, "未評価") for x in bands.values())
                    or any(statuses[k] not in SOURCE_STATES
                           for k in ("pedigree", "draw_weight", "jockey_stable"))
                    or statuses["rotation"] not in INTERVALS
                    or statuses["body_condition"] != "race_day_bodyweight_unavailable"):
                raise CoverageError("Source gap status unknown")
            missing = [k for k in CORE if bands[k] == "未評価"]
            exact = None if missing else sum(
                RESEARCH_WEIGHTS[k] * POINTS[bands[k]] for k in CORE)
            if (h["missing"] != missing
                    or h["observedFactorCount"] != 5 - len(missing)
                    or h.get("rawThirdPoints") != exact
                    or h.get("evidenceScore79") != (
                        None if exact is None else round(exact / 3, 2))):
                raise CoverageError("Invalid 79-weight observation")
            present = {
                k: (False if k == "body_condition" else
                    statuses[k] != "unknown" if k == "rotation" else
                    statuses[k] == "complete_fields_observed")
                for k in KEYS
            }
            for k in KEYS:
                coverage[k] += int(present[k])
            weight_present = sum(WEIGHTS[k] for k in KEYS if present[k])
            prior_ready += int(all(present[k] for k in KEYS[:-1]))
            bodies_missing += 1
            # Source fields are NOT conditional performance evidence.
            # 6pt pedigree and 10pt jockey/trainer need separate historical
            # cohorts, verified publication cutoffs, and out-of-time tests.
            family_present = present["pedigree"]
            staff_present = present["jockey_stable"]
            sixteen_gaps = {
                "pedigree": (["parentage_fields_incomplete"] if not family_present else [])
                + ["independent_condition_cohort_unavailable",
                   "temporal_holdout_not_validated"],
                "jockey_stable": (["jockey_or_trainer_fields_incomplete"] if not staff_present else [])
                + ["condition_matched_staff_results_unvalidated",
                   "temporal_holdout_not_validated"],
            }
            horses.append({
                "number": n,
                "pedigreeStaffSourceCoverage16": (
                    6 * int(family_present) + 10 * int(staff_present)),
                "pedigreeStaffMissingEvidence": sixteen_gaps,
                "pedigreeStaffGrades": {"pedigree": "未評価", "jockey_stable": "未評価"},
                "pedigreeStaffScores": {"pedigree": None, "jockey_stable": None},
                "pedigreeStaffScoreReady": False,
                "research79Observed": exact is not None,
                "research79": h["evidenceScore79"],
                "sourceStates": dict(statuses),
                "sourceFieldsPresent": present,
                "sourceFieldCoverageEquivalent21": weight_present,
                "missingSourceFields": [k for k in KEYS if not present[k]],
                "missingValidation": dict(STEPS),
                "verifiedFactorCount": 0, "formalScore100": None,
                "formalGrade": "未評価", "bettingReady": False,
            })
        if (not isinstance(b.get("remainingFieldCoverage"), dict)
                or b["remainingFieldCoverage"] != coverage):
            raise CoverageError("Source gap source counts mismatch")
        result.append({
            "track": key[0], "race": key[1], "runnerCount": len(horses),
            "horses": horses,
            "priorSourceFourCompleteCount": sum(
                all(h["sourceFieldsPresent"][k] for k in KEYS[:-1])
                for h in horses),
            "research79ObservedCount": sum(
                h["research79Observed"] for h in horses),
            "sourceCoverageByFactor": coverage,
            "pedigreeParentageCompleteCount": coverage["pedigree"],
            "staffIdentityCompleteCount": coverage["jockey_stable"],
            "bothPedigreeStaffCompleteCount": sum(
                h["pedigreeStaffSourceCoverage16"] == 16 for h in horses),
            "pedigreeStaffVerifiedGrades": 0,
            "gradeReady": False, "trifectaReady": False,
        })
        ready_prior_total += result[-1]["priorSourceFourCompleteCount"]
    return {
        "version": VERSION, "policyVersion": NEW_POLICY,
        "sourcePolicyVersion": OLD_POLICY,
        "raceCount": len(result), "races": result,
        "factorWeights": dict(WEIGHTS),
        "remainingWeight": 21, "initialResearchWeight": 79,
        "totalWeight": 100,
        "pedigreeStaffWeight": 16, "pedigreeStaffGradesVerified": 0,
        "independentPedigreeCohortValidated": False,
        "conditionMatchedStaffResultsValidated": False,
        "outOfTimePerformanceValidated": False,
        "priorSourceFourCompleteCount": ready_prior_total,
        "verifiedFactorCount": 0, "formallyEvaluatedHorseCount": 0,
        "officialJraVerified": False,
        "independentResultsVerified": False,
        "historicalBandsCalibrated": False,
        "overallPredictionReady": False,
        "bettingReady": False, "autoPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "extraProviderCalls": 0, "changesExistingReceipts": False,
        "changesExistingTickets": False, "changesExistingRoi": False,
        "note": (
            "新配点の残り21点に必要な資料の有無だけを馬番別に照合。"
            "血統6と騎手厩舎10は名前の存在を確認しても能力評価は不可。"
            "別の条件一致実績・公表時刻・時系列検証が必要。"
            "資料カバー配点相当は能力点ではなく、馬体重は全頭未確認。"
            "JRA独立照合・条件別効果・時系列検証は未完了。"
        ),
    }
