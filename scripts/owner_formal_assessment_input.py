"""Validate the private input contract before the formal ten-factor scorer.

This validates shape and consistency only. It does not authenticate JRDB/JRA,
create factor grades, or authorize caller-supplied verification flags. Only a
trusted server-side adapter may call it; never expose it as a client endpoint.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone

from evaluation_policy import (
    OWNER_FORMAL_FACTORS as FACTORS,
    OWNER_FORMAL_POLICY_VERSION,
    POINTS,
    TOTAL_WEIGHT,
    timestamp,
)
from jrdb_coverage import CoverageError
from jrdb_program_preview import TRACKS

VERSION = "owner-formal-assessment-input-1"
UNASSESSED = "未評価"
JST = timezone(timedelta(hours=9))
OFFICIAL_FLAGS = (
    "jra_starters_verified", "jra_scratches_verified",
    "jra_going_verified", "jra_posttime_verified",
)
SNAPSHOT_FIELDS = {
    "mode", "track", "race", "asOf", "offAt", "independentJra",
    "assessmentValidated", "predictionValidated", "horses",
}
EVIDENCE_FIELDS = {"sourceId", "reference", "availableAt", "sourceFamily"}


def _text(value, label, *, maximum=512):
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise CoverageError("Invalid " + label)


def _evidence(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 20:
        raise CoverageError("Invalid formal assessment evidence")
    for row in rows:
        if (not isinstance(row, dict)
                or set(row) - EVIDENCE_FIELDS
                or not {"sourceId", "reference", "availableAt"} <= set(row)):
            raise CoverageError("Invalid formal assessment evidence")
        _text(row["sourceId"], "evidence source")
        _text(row["reference"], "evidence reference")
        # Timestamp syntax and cutoff are checked by the existing scorer,
        # which turns malformed or late evidence into an unassessed factor.
        _text(row["availableAt"], "evidence timestamp")
        if "sourceFamily" in row:
            _text(row["sourceFamily"], "evidence source family", maximum=128)


def validate_formal_assessment_snapshot(snapshot, *, expected_track,
                                        expected_race, day):
    """Return a defensive copy of one normalized, race-bound scorer input.

    The scorer remains responsible for evidence cutoff and official-roster
    decisions. This boundary rejects malformed data but does not promote
    observations into grades or treat flags as authenticated facts.
    """
    if (len(FACTORS) != 10 or sum(FACTORS.values()) != TOTAL_WEIGHT
            or TOTAL_WEIGHT != 100
            or OWNER_FORMAL_POLICY_VERSION != "research-6"):
        raise CoverageError("Formal ten-factor policy contract changed")
    if (type(day) is not str or len(day) != 8 or not day.startswith("20")
            or not day.isascii()
            or not day.isdigit()):
        raise CoverageError("Invalid formal assessment day")
    try:
        parsed_day = datetime.strptime(day, "%Y%m%d")
    except ValueError:
        raise CoverageError("Invalid formal assessment day") from None
    if parsed_day.strftime("%Y%m%d") != day:
        raise CoverageError("Invalid formal assessment day")
    if (type(expected_track) is not str or expected_track not in TRACKS.values()
            or type(expected_race) is not int
            or not 1 <= expected_race <= 12):
        raise CoverageError("Invalid expected formal race")
    if (not isinstance(snapshot, dict)
            or set(snapshot) != SNAPSHOT_FIELDS
            or snapshot.get("mode") != "owner_verified_prestart_v1"
            or snapshot.get("track") != expected_track
            or type(snapshot.get("race")) is not int
            or snapshot["race"] != expected_race):
        raise CoverageError("Formal assessment race identity mismatch")

    try:
        as_of = timestamp(snapshot.get("asOf"))
        off_at = timestamp(snapshot.get("offAt"))
    except (ValueError, TypeError, OverflowError):
        raise CoverageError("Invalid formal assessment time") from None
    if as_of >= off_at or off_at.astimezone(JST).strftime("%Y%m%d") != day:
        raise CoverageError("Formal assessment time does not match race day")

    if type(snapshot.get("assessmentValidated")) is not bool:
        raise CoverageError("Invalid assessment validation flag")
    if type(snapshot.get("predictionValidated")) is not bool:
        raise CoverageError("Invalid prediction validation flag")

    official = snapshot.get("independentJra")
    allowed_official = set(OFFICIAL_FLAGS) | {"confirmedStarterNumbers"}
    if (not isinstance(official, dict)
            or set(OFFICIAL_FLAGS) - set(official)
            or set(official) - allowed_official
            or any(type(official[key]) is not bool for key in OFFICIAL_FLAGS)):
        raise CoverageError("Invalid independent JRA verification shape")
    if "confirmedStarterNumbers" in official:
        confirmed = official["confirmedStarterNumbers"]
        if (not isinstance(confirmed, list) or len(confirmed) > 18
                or any(type(number) is not int or not 1 <= number <= 18
                       for number in confirmed)
                or len(set(confirmed)) != len(confirmed)):
            raise CoverageError("Invalid independently confirmed starter list")

    horses = snapshot.get("horses")
    if not isinstance(horses, list) or not 4 <= len(horses) <= 18:
        raise CoverageError("Invalid formal assessment runner count")
    numbers = set()
    for horse in horses:
        if (not isinstance(horse, dict)
                or set(horse) - {"number", "assessments", "blockingConcerns"}
                or type(horse.get("number")) is not int
                or not 1 <= horse["number"] <= 18
                or horse["number"] in numbers):
            raise CoverageError("Invalid formal assessment runner")
        numbers.add(horse["number"])

        assessments = horse.get("assessments")
        if (not isinstance(assessments, dict)
                or set(assessments) - set(FACTORS)):
            raise CoverageError("Invalid formal assessment factor map")
        for factor, item in assessments.items():
            if item is None:
                continue
            if (not isinstance(item, dict)
                    or set(item) - {"grade", "reason", "evidence", "winSupport"}
                    or item.get("grade") not in (*POINTS, UNASSESSED)):
                raise CoverageError("Invalid formal factor assessment")
            if ("winSupport" in item and type(item["winSupport"]) is not bool):
                raise CoverageError("Invalid formal factor support flag")
            has_reason, has_evidence = "reason" in item, "evidence" in item
            if has_reason != has_evidence:
                raise CoverageError("Incomplete formal factor evidence")
            if item["grade"] != UNASSESSED and not has_reason:
                raise CoverageError("Graded factor lacks supporting evidence")
            if has_reason:
                _text(item["reason"], "formal factor reason")
                _evidence(item["evidence"])

        concerns = horse.get("blockingConcerns", [])
        if not isinstance(concerns, list) or len(concerns) > 12:
            raise CoverageError("Invalid formal assessment blockers")
        for concern in concerns:
            if (not isinstance(concern, dict)
                    or set(concern) != {"reason", "evidence"}):
                raise CoverageError("Invalid formal assessment blocker")
            _text(concern["reason"], "formal assessment blocker")
            _evidence(concern["evidence"])

    return deepcopy(snapshot)
