"""Opt-in 70-weight historical EXPERIMENT, never a verified 100-point grade.

Merge already cross-validated JRDB /tcy workouts, historical course evidence,
and past-corner scenario hypotheses. A past placing rate or past fourth-corner
position is NOT validated current-race suitability or pace. Absolutely no
new source calls, price/odds, official confirmations, receipts, or wagers.
"""
from evaluation_policy import FACTORS, POINTS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_five_factor_hypotheses import VERSION as FIVE_VERSION, GRADE
from jrdb_ten_factor_source_inventory import VERSION as INVENTORY_VERSION

VERSION = "owner-three-core-research-1"
CORE = ("training", "course_distance", "pace")
WEIGHTS = {key: FACTORS[key] for key in CORE}
UNKNOWN = "未評価"
assert sum(WEIGHTS.values()) == 70 and len(CORE) == 3


def _race_index(rows):
    if not isinstance(rows, list) or len(rows) > 120:
        raise CoverageError("Unexpected three-core race list")
    result = {}
    for row in rows:
        if (not isinstance(row, dict)
                or not isinstance(row.get("track"), str)
                or not row["track"]
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoverageError("Invalid three-core race identity")
        key = row["track"], row["race"]
        if key in result:
            raise CoverageError("Duplicate three-core race")
        result[key] = row
    return result


def _horse_index(rows):
    if not isinstance(rows, list) or len(rows) > 18:
        raise CoverageError("Invalid three-core runner roster")
    indexed = {}
    for horse in rows:
        if not isinstance(horse, dict) or type(horse.get("number")) is not int:
            raise CoverageError("Invalid three-core runner")
        num = horse["number"]
        if not 1 <= num <= 18 or num in indexed:
            raise CoverageError("Duplicate/invalid three-core horse number")
        indexed[num] = horse
    return indexed


def three_core_research(five, inventory):
    """Bounded per-horse observation scores, separate from the formal gate.

    Any core band absent => NO 70-point comparison for that horse.
    This is not calibrated against held-out outcomes and cannot authorize
    a winner, a formal ranking or a ticket, even if every band is present.
    """
    if (not isinstance(five, dict)
            or five.get("version") != FIVE_VERSION
            or five.get("policyVersion") != POLICY_VERSION
            or five.get("researchOnly") is not True
            or five.get("privateOwnerOnly") is not True
            or five.get("hypothesisBandsNotVerifiedGrades") is not True
            or five.get("materialCoverageDoesNotMeanPrediction") is not True
            or five.get("officialJraVerified") is not False
            or five.get("overallPredictionReady") is not False
            or five.get("verifiedFactorCount") != 0
            or five.get("bettingReady") is not False
            or five.get("autoPurchase") is not False
            or not isinstance(inventory, dict)
            or inventory.get("version") != INVENTORY_VERSION
            or inventory.get("policyVersion") != POLICY_VERSION
            or inventory.get("factorCount") != 10
            or inventory.get("totalWeight") != 100
            or inventory.get("verifiedGrades") != 0
            or inventory.get("researchOnly") is not True
            or inventory.get("privateOwnerOnly") is not True
            or inventory.get("independentJraVerified") is not False
            or inventory.get("overallPredictionReady") is not False
            or inventory.get("bettingReady") is not False
            or inventory.get("autoPurchase") is not False
            or not isinstance(inventory.get("factorWeights"), dict)
            or inventory["factorWeights"] != FACTORS):
        raise CoverageError("Unverified three-core input promotion")
    first = _race_index(five.get("races"))
    second = _race_index(inventory.get("races"))
    if (first.keys() != second.keys()
            or five.get("raceCount") != len(first)
            or inventory.get("raceCount") != len(second)):
        raise CoverageError("Three-core race set differs")
    out = []
    for coord in sorted(first):
        fa, source = first[coord], second[coord]
        a = _horse_index(fa.get("runners"))
        b = _horse_index(source.get("runners"))
        if (a.keys() != b.keys() or fa.get("runnerCount") != len(a)
                or source.get("runnerCount") != len(b)
                or fa.get("verifiedFactorCount") != 0
                or fa.get("overallReady") is not False
                or fa.get("bettingReady") is not False
                or source.get("verifiedGrades") != 0
                or source.get("overallReady") is not False
                or source.get("independentJraVerified") is not False
                or source.get("bettingReady") is not False):
            raise CoverageError("Three-core runner roster differs")
        horses, missing_tally = [], {key: 0 for key in CORE}
        for n in sorted(a):
            h, evidence = a[n], b[n]
            if (h.get("actualGradesVerified") != 0
                    or h.get("overallScore") is not None
                    or h.get("overallRank") is not None
                    or evidence.get("verifiedGrades") != 0
                    or evidence.get("overallScore") is not None
                    or evidence.get("overallRank") is not None
                    or not isinstance(h.get("bands"), dict)
                    or not isinstance(evidence.get("provisionalBands"), dict)
                    or h["bands"] != evidence["provisionalBands"]):
                raise CoverageError("Three-core band and inventory mismatch")
            bands = {key: h["bands"].get(key) for key in CORE}
            if any(label not in GRADE for label in bands.values()):
                raise CoverageError("Unexpected three-core evidence band")
            missing = [key for key, label in bands.items() if label == UNKNOWN]
            for key in missing:
                missing_tally[key] += 1
            # Never scale 2-of-3 weights to 70 or make a partial rank.
            raw = (None if missing else
                   sum(POINTS[bands[key]] * WEIGHTS[key] for key in CORE))
            horses.append({
                "number": n, "bands": bands, "missing": missing,
                "observedCoreCount": len(CORE) - len(missing),
                "evidenceScore70": None if raw is None else round(raw / 3, 2),
                "rawThirdPoints": raw,
                "scoreIsCalibrated": False,
                "formalScore100": None, "formalGrade": UNKNOWN,
                "formalRank": None, "bettingReady": False,
            })
        complete = [h for h in horses if h["rawThirdPoints"] is not None]
        # No published ordering: an exploratory score is an observation,
        # not an actual win-prediction rank or a tie-breaker.
        out.append({
            "track": coord[0], "race": coord[1], "runnerCount": len(horses),
            "completeCoreObserved": len(complete),
            "missingByFactor": missing_tally,
            "horses": horses, "researchOnly": True,
            "formalGradeReady": False, "trifectaReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": len(out), "races": out,
        "coreFactorWeights": dict(WEIGHTS), "coreWeightTotal": 70,
        "factorGradesVerified": 0, "overallPredictionReady": False,
        "formalScoreReady": False, "officialJraVerified": False,
        "bettingReady": False, "autoPurchase": False,
        "changesExistingTickets": False,
        "historicalBandsNotCalibrated": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": ("調教30・同条件実績20・過去位置取り仮説20の研究用70点。"
                 "過去3着内率と4角位置は今走の能力・展開予測ではなく、"
                 "検証済み10項目S/A/B/C、馬券、回収率には反映しない。"),
    }
