"""Read-only per-race source passport from an already fetched owner draft.

No additional JRDB calls, raw provider rows, results, odds, runner identities,
credentials or scores. An observed input field never becomes a graded factor.
This is only a source coverage/status audit for the owner iPhone screen.
"""
from evaluation_policy import (OWNER_FORMAL_FACTORS as FACTORS,
    OWNER_FORMAL_POLICY_VERSION as POLICY_VERSION)
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION
from owner_ten_factor_contract import VERSION as TEN_VERSION
from jrdb_owner_draft_materials import VERSION as MATERIAL_VERSION

VERSION = "owner-day-source-passport-1"
SOURCES = ("pedigree", "drawWeight", "rotation",
           "personnel", "body", "pastCorner")
EIGHT = tuple(k for k in FACTORS if k not in ("training", "recent"))
assert len(EIGHT) == 8 and len(FACTORS) == 10 and sum(FACTORS.values()) == 100


def _index(rows, field):
    if not isinstance(rows, list) or len(rows) > 120:
        raise CoverageError("Invalid " + field + " race count")
    indexed = {}
    for row in rows:
        if (not isinstance(row, dict)
                or not isinstance(row.get("track"), str)
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoverageError("Invalid " + field + " coordinate")
        key = row["track"], row["race"]
        if key in indexed:
            raise CoverageError("Duplicate " + field + " coordinate")
        indexed[key] = row
    return indexed


def _source_count(value, total):
    if type(value) is not int or not 0 <= value <= total:
        raise CoverageError("Invalid material coverage count")
    return value


def _unavailable():
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": 0, "races": [], "sourceAuditAvailable": False,
        "gradedFactors": 0, "verifiedPredictions": 0,
        "independentJraVerified": False, "purchaseReady": False,
        "newProviderRequests": 0, "reason": "source_audit_unavailable",
    }


def owner_day_source_passport(report):
    """Cross-check the same-snapshot 2-factor, source and course summaries.

    A held race may deliberately have no per-horse draft to avoid recreating
    a post-off ranking. Its material source counts still refer to the original
    programme roster, and are NOT used to restore a horse-level ranking.
    """
    if (not isinstance(report, dict)
            or report.get("version") != DRAFT_VERSION
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("officialJraVerified") is not False
            or report.get("overallPredictionReady") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False
            or report.get("sourceReadCount") != 4
            or type(report.get("raceCount")) is not int
            or not 0 <= report["raceCount"] <= 120):
        raise CoverageError("Invalid source passport input")

    ten = report.get("tenFactorPreview")
    material = report.get("sourceMaterials")
    context = report.get("raceContext")
    if (not isinstance(ten, dict) or ten.get("version") != TEN_VERSION
            or ten.get("policyVersion") != POLICY_VERSION
            or ten.get("fullPredictionRaceCount") != 0
            or ten.get("overallPredictionReady") is not False
            or ten.get("officialJraVerified") is not False
            or not isinstance(material, dict)
            or material.get("version") != MATERIAL_VERSION
            or material.get("status") not in ("observed", "unavailable")
            or material.get("gradedNewFactors") != 0
            or material.get("officialJraVerified") is not False
            or not isinstance(context, dict)
            or context.get("version") != "race-context-1"
            or context.get("raceConditionsVerified") is not False
            or context.get("predictionReady") is not False):
        raise CoverageError("Source passport research contracts mismatch")

    draft = _index(report.get("races"), "draft")
    grades = _index(ten.get("races"), "ten-factor")
    course = _index(context.get("races"), "course")
    materials = _index(material.get("races"), "materials")
    if (len(draft) != report["raceCount"] or set(draft) != set(grades)
            or set(draft) != set(course)
            or ten.get("raceCount") != len(grades)
            or context.get("raceCount") != len(course)
            or (material["status"] == "observed" and set(draft) != set(materials))
            or (material["status"] == "unavailable" and materials)):
        raise CoverageError("Source passport race sets disagree")

    rows = []
    for key in sorted(draft):
        race, ten_row, ctx = draft[key], grades[key], course[key]
        horses = ten_row.get("horses")
        if (race.get("status") not in ("hold", "provisional_draft")
                or not isinstance(race.get("runners"), list)
                or not isinstance(horses, list)
                or len(horses) != len(race["runners"])
                or ten_row.get("runnerCount") != len(horses)
                or ten_row.get("overallReady") is not False
                or ten_row.get("fullTenFactorCount") != 0
                or ten_row.get("trainingLedRecheckIsWinPick") is not False
                or ctx.get("horseCourseSuitabilityAssessed") is not False
                or ctx.get("horseGoingSuitabilityAssessed") is not False
                or ctx.get("predictionReady") is not False
                or type(ctx.get("courseInfoPresent")) is not bool
                or type(ctx.get("goingAvailable")) is not bool):
            raise CoverageError("Invalid race-level grade/readiness status")

        counts = None
        registered = len(horses)
        if material["status"] == "observed":
            source = materials[key]
            registered = source.get("runnerCount")
            if (type(registered) is not int or not 0 <= registered <= 18
                    or not isinstance(source.get("counts"), dict)
                    or set(source["counts"]) != set(SOURCES)):
                raise CoverageError("Invalid source material roster")
            counts = {k: _source_count(source["counts"][k], registered)
                      for k in SOURCES}
            # Valid prestart drafts must have the same roster. Held races may
            # intentionally withhold the post-off horse list entirely.
            if race["status"] == "provisional_draft" and registered != len(horses):
                raise CoverageError("Draft/source roster mismatch")
        provisional = {"training": 0, "recent": 0}
        for horse in horses:
            if (not isinstance(horse, dict)
                    or horse.get("verifiedFactorCount") != 0
                    or horse.get("overallRank") is not None
                    or horse.get("score") is not None
                    or not isinstance(horse.get("grades"), dict)
                    or set(horse["grades"]) != set(FACTORS)
                    or any(horse["grades"][k] != "未評価" for k in EIGHT)):
                raise CoverageError("Unverified factors cannot become grades")
            for factor in provisional:
                if horse["grades"][factor] in ("S", "A", "B", "C"):
                    provisional[factor] += 1
                elif horse["grades"][factor] != "未評価":
                    raise CoverageError("Invalid provisional grade")
        if (not isinstance(race.get("runners"), list)
                or any(type(h.get("number")) is not int for h in race["runners"])
                or {h["number"] for h in horses}
                   != {h["number"] for h in race["runners"]}):
            raise CoverageError("Draft/ten-factor roster differs")

        rows.append({
            "track": key[0], "race": key[1],
            "draftStatus": race["status"],
            "programmeRunnerCount": registered,
            "provisionalTrainingCount": provisional["training"],
            "provisionalRecentCount": provisional["recent"],
            "sourceMaterialsObserved": counts is not None,
            "additionalFieldCounts": counts,
            "courseContextPresent": ctx["courseInfoPresent"],
            "goingContextPresent": ctx["goingAvailable"],
            "raceDayBodyweightVerifiedCount": 0,
            "officialJraVerified": False,
            "verifiedFactorCount": 0,
            "unassessedFactorKeys": list(EIGHT),
            "completeTenFactorReady": False,
            "independentResultsConnected": False,
            "purchaseReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": len(rows), "races": rows,
        "sourceAuditAvailable": True,
        "observedMaterialRaces": len(materials),
        "gradedFactors": 0, "verifiedPredictions": 0,
        "independentJraVerified": False, "purchaseReady": False,
        "newProviderRequests": 0,
        "reason": "unvalidated_source_observations_only",
    }


def safe_owner_day_source_passport(report):
    """Optional audit cannot fail an already signed private research receipt."""
    try:
        return owner_day_source_passport(report)
    except (CoverageError, ValueError, TypeError, KeyError):
        return _unavailable()
