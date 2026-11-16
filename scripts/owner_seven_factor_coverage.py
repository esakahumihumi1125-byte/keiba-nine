"""Read-only 7-factor research subtotal from the SAME protected day snapshot.

The standard owner pipeline already has provisional 30+3 training/recent
grades and five separately generated uncalibrated hypotheses (up to 57 more
weight points). This assembler makes the observed subtotal explicit without
extrapolating unknown bloodline/draw/body evidence or asserting a formal 100
point score. No JRDB/JRA fetch, ranking, tickets, saving or publishing.
"""
from evaluation_policy import (OWNER_FORMAL_FACTORS as WEIGHTS,
                               OWNER_FORMAL_POLICY_VERSION)
from jrdb_coverage import CoverageError
from jrdb_owner_runner_research import VALUES

VERSION = "owner-seven-factor-coverage-1"
OPTIONAL = ("course_distance", "ground", "pace", "jockey_stable", "rotation")
CORE = ("training", "recent")
MISSING_MODEL = ("pedigree", "draw_weight", "body_condition")
SUPPORTED = set(VALUES)
MAX_RACES = 120


def _index(rows, label):
    if not isinstance(rows, list) or len(rows) > MAX_RACES:
        raise CoverageError("Invalid " + label + " races")
    found = {}
    for row in rows:
        if not isinstance(row, dict):
            raise CoverageError("Invalid " + label + " race")
        key = row.get("track"), row.get("race")
        if (type(key[0]) is not str or type(key[1]) is not int
                or key[1] < 1 or key[1] > 12 or key in found):
            raise CoverageError("Duplicate " + label + " race")
        found[key] = row
    return found


def _horses(rows):
    if not isinstance(rows, list) or len(rows) > 18:
        raise CoverageError("Invalid horse list")
    index = {}
    for item in rows:
        if not isinstance(item, dict):
            raise CoverageError("Invalid horse")
        number = item.get("number")
        if type(number) is not int or number < 1 or number > 18 or number in index:
            raise CoverageError("Duplicate or invalid horse number")
        index[number] = item
    return index


def _race_coverage(draft, ten, optional):
    """Either emit same-runner experimental coverage or hold that whole race."""
    held = {
        "track": draft["track"], "race": draft["race"],
        "status": "held", "horses": [],
        "researchOnly": True, "overallScoreReady": False,
    }
    if draft.get("status") != "provisional_draft":
        return held
    if (optional.get("status") != "scored"
            or optional.get("reason") is not None
            or optional.get("postTime") != draft.get("postTime")
            or (ten.get("track"), ten.get("race"))
               != (draft["track"], draft["race"])):
        return held

    try:
        primary = _horses(draft.get("runners"))
        factors = _horses(optional.get("horses"))
        previews = _horses(ten.get("horses"))
        if (len(primary) < 4 or set(primary) != set(factors)
                or set(primary) != set(previews)
                or len(primary) != ten.get("runnerCount")):
            return held
        results = []
        for number in primary:
            prior = previews[number]
            current = factors[number]
            raw = primary[number]
            breakdown = prior.get("provisionalBreakdown")
            grades = prior.get("grades")
            if (not isinstance(breakdown, dict)
                    or not isinstance(grades, dict)
                    or prior.get("provisionalScoreReady") is not True
                    or type(prior.get("provisionalPoints33")) is not int
                    or raw.get("number") != number):
                return held
            # The current partial 33-point snapshot is a grade heuristic
            # already created before off-time. Never construct an alternate
            # training or recent grade here.
            core_points = 0
            for key in CORE:
                grade = grades.get(key)
                points = breakdown.get(key)
                expected = {"S": 3, "A": 2, "B": 1, "C": 0}
                if (grade not in SUPPORTED or raw.get(key) != grade
                        or type(points) is not int
                        or points != expected[grade] * WEIGHTS[key] // 3):
                    return held
                core_points += points
            if core_points != prior["provisionalPoints33"]:
                return held
            slots = current.get("factors")
            if not isinstance(slots, dict) or set(slots) != set(OPTIONAL):
                return held
            covered = sum(WEIGHTS[key] for key in CORE)
            subtotal = float(core_points)
            unscored = list(MISSING_MODEL)
            for key in OPTIONAL:
                item = slots[key]
                if (not isinstance(item, dict)
                        or item.get("weight") != WEIGHTS[key]
                        or item.get("grade") not in (*SUPPORTED, "未評価")):
                    return held
                value, points = item.get("score"), item.get("points")
                if value is None:
                    if points is not None or item["grade"] != "未評価":
                        return held
                    unscored.append(key)
                else:
                    if (type(value) not in (int, float)
                            or type(points) not in (int, float)
                            or not 0 <= value <= 100
                            or not 0 <= points <= WEIGHTS[key]
                            or abs(points - WEIGHTS[key] * value / 100) > .000051
                            or item["grade"] != (
                                "S" if value >= 85 else "A" if value >= 70
                                else "B" if value >= 55 else "C")):
                        return held
                    covered += WEIGHTS[key]
                    subtotal += points
            if covered > 90 or covered < 33 or subtotal < 0 or subtotal > covered + .0001:
                return held
            unknown = 100 - covered
            if unknown < 10 or unknown != sum(WEIGHTS[k] for k in unscored):
                return held
            results.append({
                "number": number,
                "researchSubtotal": round(subtotal, 2),
                "assessedWeight": covered,
                "unassessedWeight": unknown,
                "unassessedFactors": sorted(unscored, key=lambda k: (
                    -WEIGHTS[k], list(WEIGHTS).index(k))),
                "finalScore100": None,
                "overallGrade": "未評価",
                "overallRank": None,
            })
        return {
            **held, "status": "partial", "horses": results,
        }
    except (CoverageError, ValueError, TypeError, KeyError, ArithmeticError):
        return held


def seven_factor_research_coverage(report):
    """No user inputs, no network and no promotion of 7/10 to 10/10."""
    if (not isinstance(report, dict)
            or report.get("version") != "jrdb-owner-auto-draft-1"
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("overallPredictionReady") is not False
            or report.get("officialJraVerified") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False):
        raise CoverageError("Untrusted owner research snapshot")
    ten, optional = report.get("tenFactorPreview"), report.get("automaticFactorScores")
    if (not isinstance(ten, dict) or ten.get("version") != "owner-ten-factor-contract-1"
            or ten.get("policyVersion") != OWNER_FORMAL_POLICY_VERSION
            or ten.get("overallPredictionReady") is not False
            or ten.get("fullPredictionRaceCount") != 0
            or not isinstance(optional, dict)
            or optional.get("version") != "owner-automatic-factor-scores-3"
            or optional.get("policyVersion") != OWNER_FORMAL_POLICY_VERSION
            or optional.get("date") != report.get("date")
            or optional.get("modelCalibrated") is not False
            or optional.get("officialJraVerified") is not False
            or optional.get("overallPredictionReady") is not False
            or optional.get("newProviderRequests") != 0):
        raise CoverageError("Unverified 7-factor source status")
    main = _index(report.get("races"), "draft")
    ten_by = _index(ten.get("races"), "contract")
    factor_by = _index(optional.get("races"), "optional")
    if set(main) != set(ten_by) or set(main) != set(factor_by):
        raise CoverageError("Seven-factor race coordinate mismatch")
    result = [
        _race_coverage(r, ten_by[key], factor_by[key])
        for key, r in main.items()
    ]
    return {
        "version": VERSION,
        "policyVersion": OWNER_FORMAL_POLICY_VERSION,
        "date": report["date"], "raceCount": len(result),
        "races": result,
        "partialRaceCount": sum(r["status"] == "partial" for r in result),
        "maximumPossibleAssessedWeight": 90,
        "remainingUnmappedWeight": sum(WEIGHTS[k] for k in MISSING_MODEL),
        "modelCalibrated": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "publishable": False, "bettingReady": False, "autoPurchase": False,
        "ticketsIssued": 0, "changesExistingDrafts": False,
        "changesExistingReceipts": False, "newProviderRequests": 0,
    }
