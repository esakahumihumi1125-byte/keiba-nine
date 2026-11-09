"""Five-factor 85-point *uncalibrated* JRDB history research overlay.

Adds recent runs (only 3 weight) to 30/20/20/12 observations. This is
NOT a graded real-race prediction, an independently confirmed JRA result,
or a new betting strategy. No data fetch, receipt signature or writes.
"""
from evaluation_policy import FACTORS, POINTS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_five_factor_hypotheses import GRADE
from owner_four_core_research import four_core_research, CORE as FOUR, UNKNOWN

VERSION = "owner-five-core-research-1"
CORE = (*FOUR, "recent")
WEIGHTS = {key: FACTORS[key] for key in CORE}
assert sum(WEIGHTS.values()) == 85 and WEIGHTS["recent"] == 3


def five_core_research(five, inventory, three, four):
    """Same-snapshot five-factor experimental comparison; fail closed.

    Unobserved recent is not a C/0 grade. No scaled partial total when any
    factor is missing. A poor recent grade changes score by at most 3 points.
    """
    expected = four_core_research(five, inventory, three)
    if not isinstance(four, dict) or four != expected:
        raise CoverageError("Four-factor study is not matched to source")
    by_five = {(r["track"], r["race"]): r for r in five["races"]}
    by_inventory = {(r["track"], r["race"]): r for r in inventory["races"]}
    result = []
    for four_race in four["races"]:
        key = four_race["track"], four_race["race"]
        f = {h["number"]: h for h in by_five[key]["runners"]}
        i = {h["number"]: h for h in by_inventory[key]["runners"]}
        missing_counts = dict.fromkeys(CORE, 0)
        horses = []
        for previous in four_race["horses"]:
            number = previous["number"]
            source, inventory_horse = f[number], i[number]
            recent = source["bands"].get("recent")
            if (recent not in GRADE
                    or recent != inventory_horse["provisionalBands"].get("recent")
                    or source.get("actualGradesVerified") != 0
                    or inventory_horse.get("verifiedGrades") != 0
                    or source.get("overallScore") is not None
                    or inventory_horse.get("overallScore") is not None):
                raise CoverageError("Invalid or promoted recent-runs hypothesis")
            bands = {**previous["bands"], "recent": recent}
            missing = [k for k in CORE if bands[k] == UNKNOWN]
            for key_name in missing:
                missing_counts[key_name] += 1
            raw = None if missing else sum(
                WEIGHTS[key_name] * POINTS[bands[key_name]]
                for key_name in CORE
            )
            if not missing and (
                previous["rawThirdPoints"] is None
                or raw != previous["rawThirdPoints"] + 3 * POINTS[recent]
            ):
                raise CoverageError("Five-factor study arithmetic mismatch")
            horses.append({
                "number": number, "bands": bands, "missing": missing,
                "observedFactorCount": len(CORE) - len(missing),
                "rawThirdPoints": raw,
                "evidenceScore85": None if raw is None else round(raw / 3, 2),
                "scoreIsCalibrated": False,
                "formalScore100": None, "formalGrade": UNKNOWN,
                "formalRank": None, "bettingReady": False,
            })
        # Stable evidence groups by exact third-points, never rank tied
        # horses by their number or assign an untested formal position.
        buckets = {}
        unassessed = []
        for horse in horses:
            if horse["rawThirdPoints"] is None:
                unassessed.append(horse["number"])
            else:
                buckets.setdefault(horse["rawThirdPoints"], []).append(horse["number"])
        order_groups = [
            {"rawThirdPoints": raw, "numbers": sorted(buckets[raw])}
            for raw in sorted(buckets, reverse=True)
        ]
        result.append({
            "track": four_race["track"], "race": four_race["race"],
            "runnerCount": len(horses), "horses": horses,
            "comparisonGroups": order_groups,
            "unassessedNumbers": sorted(unassessed),
            "comparisonIsFormalRank": False,
            "completeObserved": sum(h["rawThirdPoints"] is not None
                                    for h in horses),
            "missingByFactor": missing_counts,
            "researchOnly": True, "formalGradeReady": False,
            "trifectaReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": len(result), "races": result,
        "factorWeights": dict(WEIGHTS), "observedWeightTotal": 85,
        "factorGradesVerified": 0, "overallPredictionReady": False,
        "formalScoreReady": False, "officialJraVerified": False,
        "bettingReady": False, "autoPurchase": False,
        "changesExistingTickets": False,
        "changesExistingCoreReceipts": False,
        "historicalBandsNotCalibrated": True,
        "recentResultRankNotPrediction": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": ("調教30・近走3・過去同条件20・過去位置取り20・"
                 "過去馬場12の研究用85点。近走の比重は最大3点。"
                 "同点馬は同一グループとし未評価は並べない。"
                  "比較の順序は未検証で正式S/A/B/C・3連単に反映しない。"
                 "項目未評価なら85点研究値も未評価。"),
    }
