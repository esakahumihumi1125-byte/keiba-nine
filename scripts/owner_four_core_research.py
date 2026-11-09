"""Opt-in 82-weight weather/going extension of the 70-point history experiment.

Same matched JRDB historical snapshot; ground is only a past-going observation,
NOT a proven present-going suitability or JRA-confirmed condition. This module
never signs/rewrites existing 70-point research, 3連単, official results or ROI.
"""
from evaluation_policy import FACTORS, POINTS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_five_factor_hypotheses import GRADE
from owner_three_core_research import (
    three_core_research, CORE as THREE, UNKNOWN,
)

VERSION = "owner-four-core-research-1"
CORE = (*THREE, "ground")
WEIGHTS = {factor: FACTORS[factor] for factor in CORE}
assert sum(WEIGHTS.values()) == 82 and FACTORS["ground"] == 12


def four_core_research(five, inventory, three):
    """Explore 4 uncalibrated factors, with all-or-nothing missingness.

    The previously signed 70-weight study remains immutable. For a missing
    prior core band or a missing current-going observation, the 82-point
    exploratory value is NULL, never a partial normalized number or C/zero.
    """
    expected_three = three_core_research(five, inventory)
    if not isinstance(three, dict) or three != expected_three:
        raise CoverageError("Mismatched three-core historical study")
    races_by_key = {
        (race["track"], race["race"]): race
        for race in five["races"]
    }
    material_by_key = {
        (race["track"], race["race"]): race
        for race in inventory["races"]
    }
    output = []
    for source in three["races"]:
        key = source["track"], source["race"]
        five_race = races_by_key[key]
        ten_race = material_by_key[key]
        f_by_number = {h["number"]: h for h in five_race["runners"]}
        i_by_number = {h["number"]: h for h in ten_race["runners"]}
        missing_count = dict.fromkeys(CORE, 0)
        horses = []
        for h in source["horses"]:
            number = h["number"]
            from_five = f_by_number[number]
            from_inventory = i_by_number[number]
            ground = from_five["bands"].get("ground")
            if (ground not in GRADE
                    or ground != from_inventory["provisionalBands"].get("ground")
                    or from_five.get("actualGradesVerified") != 0
                    or from_inventory.get("verifiedGrades") != 0
                    or from_five.get("overallScore") is not None
                    or from_inventory.get("overallScore") is not None):
                raise CoverageError("Unverified going grade mismatch")
            bands = {**h["bands"], "ground": ground}
            missing = [k for k in CORE if bands[k] == UNKNOWN]
            for k in missing:
                missing_count[k] += 1
            raw = None if missing else sum(
                WEIGHTS[k] * POINTS[bands[k]] for k in CORE
            )
            if not missing and (h["rawThirdPoints"] is None
                                or raw != h["rawThirdPoints"] +
                                WEIGHTS["ground"] * POINTS[ground]):
                raise CoverageError("Four-core arithmetic disagrees")
            horses.append({
                "number": number, "bands": bands, "missing": missing,
                "observedFactorCount": len(CORE) - len(missing),
                "rawThirdPoints": raw,
                "evidenceScore82": None if raw is None else round(raw / 3, 2),
                "scoreIsCalibrated": False,
                "formalScore100": None, "formalGrade": UNKNOWN,
                "formalRank": None, "bettingReady": False,
            })
        output.append({
            "track": key[0], "race": key[1],
            "runnerCount": len(horses), "horses": horses,
            "completeObserved": sum(
                h["rawThirdPoints"] is not None for h in horses
            ),
            "missingByFactor": missing_count,
            "researchOnly": True, "formalGradeReady": False,
            "trifectaReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": len(output), "races": output,
        "factorWeights": dict(WEIGHTS), "observedWeightTotal": 82,
        "factorGradesVerified": 0, "overallPredictionReady": False,
        "formalScoreReady": False, "officialJraVerified": False,
        "bettingReady": False, "autoPurchase": False,
        "changesExistingTickets": False,
        "changesExistingCoreReceipts": False,
        "historicalBandsNotCalibrated": True,
        "goingSuitabilityVerified": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": ("調教30・過去の同条件好走20・過去4角の展開仮説20・"
                 "過去馬場実績12による未検証の82点研究値。"
                 "馬場状態が未確認の馬は研究用点数も未評価。"
                 "正式な10項目ランク、3連単、70点の署名固定値は変更しない。"),
    }
