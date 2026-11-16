"""Read-only 7-factor research subtotal from the SAME protected day snapshot.

The standard owner pipeline already has provisional 30+3 training/recent
grades and five separately generated uncalibrated hypotheses (up to 57 more
weight points). This assembler makes the observed subtotal explicit without
extrapolating unknown bloodline/draw/body evidence or asserting a formal 100
point score. No JRDB/JRA fetch, ranking, tickets, saving or publishing.
"""
from datetime import datetime, timedelta, timezone
import re

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
SOURCE_FIELDS = ("pedigree", "draw_weight", "jockey_stable", "rotation", "past_corner")
BODY_STATUS = "raceday_bodyweight_not_available"
JST = timezone(timedelta(hours=9))
HELD_REASONS = frozenset(("missing_factors", "ambiguous_equal_grade_boundary"))
GRADES = {"S": 3, "A": 2, "B": 1, "C": 0}
MIN_HELD_WEIGHT = 30


def _source_materials(report):
    """Only same-snapshot, redacted /tky presence flags; never infer a grade.

    A missing or broken optional source audit yields NOT_CHECKED, not MISSING.
    No material values, provider IDs or unsupported score percentages escape.
    """
    evidence = report.get("runnerSourceEvidence")
    if (not isinstance(evidence, dict)
            or evidence.get("version") != "owner-runner-source-hints-1"
            or evidence.get("researchOnly") is not True
            or evidence.get("privateOwnerOnly") is not True
            or evidence.get("officialJraVerified") is not False
            or evidence.get("overallPredictionReady") is not False
            or evidence.get("bettingReady") is not False
            or evidence.get("verifiedNewFactorCount") != 0
            or evidence.get("newProviderRequests") != 0
            or evidence.get("rawSourceRowsIncluded") is not False
            or evidence.get("factorFields") != list(SOURCE_FIELDS)
            or not isinstance(evidence.get("races"), list)
            or evidence.get("raceCount") != len(evidence["races"])
            or evidence["raceCount"] != len(report.get("races", []))):
        return {}
    try:
        rows = _index(evidence["races"], "optional material")
        if set(rows) != set(_index(report["races"], "draft")):
            return {}
        materials = {}
        for key, race in rows.items():
            if race.get("status") != "observed":
                continue
            numbers = _horses(race.get("runners"))
            for value in numbers.values():
                flags = value.get("observed")
                if (value.get("verifiedFactorCount") != 0
                        or not isinstance(flags, dict)
                        or set(flags) != set(SOURCE_FIELDS)
                        or any(type(v) is not bool for v in flags.values())):
                    raise CoverageError("Malformed optional source flags")
            materials[key] = numbers
        return materials
    except (CoverageError, ValueError, TypeError, KeyError):
        return {}


def _remaining_material(flags):
    pedigree = "not_checked"
    draw = "not_checked"
    if isinstance(flags, dict):
        presence = flags.get("observed")
        if isinstance(presence, dict):
            pedigree = ("fields_observed" if presence.get("pedigree") is True
                        else "fields_missing")
            draw = ("fields_observed" if presence.get("draw_weight") is True
                    else "fields_missing")
    return {
        "pedigree": pedigree, "draw_weight": draw,
        "body_condition": BODY_STATUS,
    }


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


def _race_coverage(draft, ten, optional, source=None, *, day=None, now=None):
    """Either emit same-runner experimental coverage or hold that whole race."""
    held = {
        "track": draft["track"], "race": draft["race"],
        "status": "held", "horses": [],
        "researchOnly": True, "overallScoreReady": False,
    }
    is_draft = draft.get("status") == "provisional_draft"
    is_held = (draft.get("status") == "hold"
               and draft.get("reason") in HELD_REASONS)
    if not is_draft and not is_held:
        return held
    if is_held:
        # A new observation must never backfill historical, off-time or
        # already-archived research with a fresh after-the-fact score.
        if (not isinstance(now, datetime) or now.tzinfo is None
                or now.utcoffset() is None or type(day) is not str
                or not re.fullmatch(r"20[0-9]{6}", day)):
            return held
        off_text = draft.get("postTime")
        if (not isinstance(off_text, str)
                or not re.fullmatch(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]", off_text)):
            return held
        try:
            off_time = datetime.strptime(day + off_text, "%Y%m%d%H:%M").replace(
                tzinfo=JST)
        except ValueError:
            return held
        if now.astimezone(JST) >= off_time:
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
        # Only the exact same active prestart horse set can supply source
        # availability; a mismatch cannot masquerade as a negative field.
        source_by_number = source if (isinstance(source, dict)
                and set(source) == set(primary)) else {}
        results = []
        for number in primary:
            prior = previews[number]
            current = factors[number]
            raw = primary[number]
            breakdown = prior.get("provisionalBreakdown")
            grades = prior.get("grades")
            if (not isinstance(breakdown, dict)
                    or not isinstance(grades, dict)
                    or raw.get("number") != number):
                return held
            # The signed two-factor candidate keeps its ORIGINAL 33-point
            # integrity checks. A prestart held race does not inherit those
            # points: only independently matching S/A/B/C fields contribute
            # to an UNSIGNED partial observation, never an ordinal rank.
            core_points = 0
            covered_core = 0
            missing_core = []
            for key in CORE:
                grade = grades.get(key)
                points = breakdown.get(key)
                if grade != raw.get(key) or grade not in (*SUPPORTED, "未評価"):
                    return held
                if is_draft:
                    if (grade not in SUPPORTED or type(points) is not int
                            or points != GRADES[grade] * WEIGHTS[key] // 3):
                        return held
                elif (points is not None or
                      prior.get("provisionalScoreReady") is not False):
                    return held
                if grade in SUPPORTED:
                    core_points += GRADES[grade] * WEIGHTS[key] // 3
                    covered_core += WEIGHTS[key]
                else:
                    missing_core.append(key)
            if is_draft:
                if (prior.get("provisionalScoreReady") is not True
                        or type(prior.get("provisionalPoints33")) is not int
                        or core_points != prior["provisionalPoints33"]):
                    return held
            elif prior.get("provisionalPoints33") is not None:
                return held
            slots = current.get("factors")
            if not isinstance(slots, dict) or set(slots) != set(OPTIONAL):
                return held
            covered = covered_core
            subtotal = float(core_points)
            unscored = list(MISSING_MODEL) + missing_core
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
            if (covered > 90 or covered < (33 if is_draft else MIN_HELD_WEIGHT)
                    or subtotal < 0 or subtotal > covered + .0001):
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
                "remainingMaterialReadiness": _remaining_material(
                    source_by_number.get(number)),
                "remainingEvidenceIsNotScore": True,
                "finalScore100": None,
                "overallGrade": "未評価",
                "overallRank": None,
            })
        return {
            **held, "status": "partial" if is_draft else "partial_held",
            "horses": results,
            "heldResearchNeverFormsTickets": True,
        }
    except (CoverageError, ValueError, TypeError, KeyError, ArithmeticError):
        return held


def seven_factor_research_coverage(report, *, now=None):
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
    materials = _source_materials(report)
    result = [
        _race_coverage(
            r, ten_by[key], factor_by[key], materials.get(key),
            day=report.get("date"), now=now)
        for key, r in main.items()
    ]
    return {
        "version": VERSION,
        "policyVersion": OWNER_FORMAL_POLICY_VERSION,
        "date": report["date"], "raceCount": len(result),
        "races": result,
        "partialRaceCount": sum(r["status"] == "partial" for r in result),
        "heldPartialRaceCount": sum(
            r["status"] == "partial_held" for r in result),
        "heldCoverageNeverRanksOrBets": True,
        "maximumPossibleAssessedWeight": 90,
        "remainingUnmappedWeight": sum(WEIGHTS[k] for k in MISSING_MODEL),
        "remainingFactorFieldsOnly": True,
        "racedayBodyWeightFromDayRead": False,
        "modelCalibrated": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "publishable": False, "bettingReady": False, "autoPurchase": False,
        "ticketsIssued": 0, "changesExistingDrafts": False,
        "changesExistingReceipts": False, "newProviderRequests": 0,
    }
