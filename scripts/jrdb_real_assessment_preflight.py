"""Fail-closed preflight for future real-race grading (observation only).

All inputs are previously redacted, same-snapshot race-level summaries. This
module never reads JRDB credentials, official JRA data, horse identities,
grades, odds, or results and never makes network requests or writes files.
It cannot authorize predictions; its purpose is to identify blockers.
"""
from jrdb_coverage import CoverageError
from jrdb_program_preview import TRACKS

VERSION = "real-assessment-preflight-1"
ALWAYS_BLOCKED = (
    "source_use_rights_not_verified",
    "independent_jra_final_not_verified",
    "real_factor_assessments_not_validated",
    "race_day_body_condition_not_verified",
)
OPTIONAL_GAPS = (
    "history_lookup_incomplete", "course_comparables_missing",
    "going_comparables_missing", "personnel_records_partial",
    "conformation_codes_partial", "past_run_records_absent",
    "empty_runner_list",
)
BLOCKERS = frozenset(ALWAYS_BLOCKED + OPTIONAL_GAPS)


def _count(value, maximum, name):
    if type(value) is not int or not 0 <= value <= maximum:
        raise CoverageError("Invalid private aggregate " + name)
    return value


def _summary_rows(summary, version, status_fields):
    if (not isinstance(summary, dict) or summary.get("version") != version
            or not isinstance(summary.get("races"), list)
            or len(summary["races"]) > 120
            or type(summary.get("raceCount")) is not int
            or summary["raceCount"] != len(summary["races"])
            or any(summary.get(field) is not False for field in status_fields)):
        raise CoverageError("Unverified summary contract changed")
    indexed = {}
    for row in summary["races"]:
        if not isinstance(row, dict):
            raise CoverageError("Invalid source race")
        track, race = row.get("track"), row.get("race")
        if track not in TRACKS.values() or type(race) is not int or not 1 <= race <= 12:
            raise CoverageError("Invalid source coordinates")
        key = track, race
        if key in indexed:
            raise CoverageError("Duplicate race in source preflight")
        indexed[key] = row
    return indexed


def audit_real_evaluation_preflight(combined, quality, *, history_complete):
    """Explain missing verification without ever marking actual grading ready.

    Observed record counts and provisional grade counts do not establish
    suitability or performance. License, JRA, timestamps and reliability
    must be independently established before designing a real model.
    """
    if type(history_complete) is not bool:
        raise CoverageError("Historical completeness must be explicit")
    joined = _summary_rows(
        combined, "combined-ten-factor-observations-1",
        ("predictionReady", "bettingReady"),
    )
    history = _summary_rows(
        quality, "history-evidence-coverage-1",
        ("predictionReady", "predictionConfidenceAssessed", "suitabilityAssessed"),
    )
    if set(joined) != set(history):
        raise CoverageError("History and source race sets differ")
    output = []
    for key in sorted(joined):
        r, q = joined[key], history[key]
        n = _count(r.get("runnerCount"), 18, "entries")
        if (q.get("runnerCount") != n
                or r.get("sourceMaterialSlots") != 10
                or r.get("provisionalFactorSlots") != 2
                or r.get("observationOnlySlots") != 8
                or r.get("unmappedFactorCount") != 0
                or r.get("verifiedFactorCount") != 0
                or any(r.get(k) is not False for k in (
                    "historySuitabilityAssessed", "jockeyTrainerPerformanceAssessed",
                    "bodyConditionAssessed", "raceDayBodyWeightFetched",
                    "officialJraFinalVerification", "overallRankReady",
                    "predictionReady", "bettingReady"))
                or any(q.get(k) is not False for k in (
                    "predictionReady", "predictionConfidenceAssessed",
                    "suitabilityAssessed"))):
            raise CoverageError("Unverified race cannot be promoted to grading")
        course = _count(r.get("runnersWithComparableCourse"), n, "course")
        going = _count(r.get("runnersWithKnownGoingComparable"), n, "going")
        missing = _count(r.get("runnersWithIncompleteHistory"), n, "history")
        personnel = _count(r.get("runnersWithBothPersonnelNames"), n, "personnel")
        body = _count(r.get("runnersWithConformationCodes"), n, "body")
        no_past = _count(q.get("runnersNoRecordedPast"), n, "past")
        unlinked = _count(q.get("unlinkedPastRuns"), 5 * n, "unlinked runs")
        buckets = (
            ("courseComparableSamples", course),
            ("knownGoingComparableSamples", going),
        )
        for field, at_least_one in buckets:
            group = q.get(field)
            if (not isinstance(group, dict)
                    or set(group) != {"none", "oneOrTwo", "threePlus"}
                    or any(type(value) is not int or not 0 <= value <= n
                           for value in group.values())
                    or sum(group.values()) != n
                    or group["oneOrTwo"] + group["threePlus"] != at_least_one):
                raise CoverageError("Unverified historical comparable sample counts")
        if going > course:
            raise CoverageError("Going comparables exceed course comparables")
        blockers = list(ALWAYS_BLOCKED)
        if not history_complete or missing or unlinked:
            blockers.append("history_lookup_incomplete")
        if course < n:
            blockers.append("course_comparables_missing")
        if going < n:
            blockers.append("going_comparables_missing")
        if personnel < n:
            blockers.append("personnel_records_partial")
        if body < n:
            blockers.append("conformation_codes_partial")
        if no_past:
            blockers.append("past_run_records_absent")
        if not n:
            blockers.append("empty_runner_list")
        if len(set(blockers)) != len(blockers) or not set(blockers) <= BLOCKERS:
            raise CoverageError("Unexpected preflight blocker")
        output.append({
            "track": key[0], "race": key[1], "runnerCount": n,
            "observedTenSlotStructure": True,
            "verifiedFactorCount": 0,
            "unverifiedRunnerHistory": missing,
            "runnersWithoutCourseComparables": n - course,
            "runnersWithoutGoingComparables": n - going,
            "runnersWithoutPersonnelNames": n - personnel,
            "runnersWithoutConformationCodes": n - body,
            "runnersWithoutRecordedPast": no_past,
            "blockerCodes": blockers,
            "realGradeReady": False,
            "realPredictionReady": False,
            "purchaseReady": False,
        })
    return {
        "version": VERSION, "raceCount": len(output),
        "races": output, "realGradeReady": False,
        "realPredictionReady": False, "purchaseReady": False,
        "note": ("10項目の資料枠と実戦S/A/B/Cの妥当性は別。"
                 "出所の利用権限・独立JRA照合・能力評価は未検証。"
                 "未取得や新馬の履歴欠如は能力不足と判断しない。"
                 "予想・馬券は一切生成しない。"),
    }
