"""Offline diagnosis of why an existing one-race JV-Link study holds at 0 points.

Only read the owner's already-sanitized local one-race JSON. No provider,
network, authentication, betting or production-record operations. Count the
same prerequisites as owner_jvdata_offline_trifecta_trial, but never rank horses.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
import sys

from jrdb_coverage import CoverageError
from owner_jvdata_offline_evidence import summarize_one_race
from windows_arc_race_saved_history_review import (
    JvLocalCheckError, private_source,
)

JST = timezone(timedelta(hours=9))
REASONS = {
    "no_visible_recent_runs": "観測できた直近5走の記録なし",
    "no_historical_ra7_context": "過去RA7のコース条件との結合なし",
    "no_matching_surface_distance": "同じ芝ダート・距離差200m以内の過去走なし",
    "no_valid_finish": "同条件の有効な着順なし",
    "no_valid_last_corner": "同条件の有効な4角位置なし",
    "abnormal_or_incomplete_run": "同条件の記録が異常・不完全",
}
COURSES = {"芝", "ダート"}


def reason_for_runner(runs, surface, distance):
    """Return one first unmet condition; never infer that a horse is weak."""
    if not runs:
        return "no_visible_recent_runs"
    joined = [
        r for r in runs
        if r.get("historicalRaceContextMatched") is True
        and r.get("surface") in COURSES
        and type(r.get("distanceMeters")) is int
        and 400 <= r["distanceMeters"] <= 10000
    ]
    if not joined:
        return "no_historical_ra7_context"
    matching = [
        r for r in joined
        if r["surface"] == surface
        and abs(r["distanceMeters"] - distance) <= 200
    ]
    if not matching:
        return "no_matching_surface_distance"
    finished = [
        r for r in matching
        if type(r.get("finishPosition")) is int
        and 1 <= r["finishPosition"] <= 18
    ]
    if not finished:
        return "no_valid_finish"
    cornered = [
        r for r in finished
        if isinstance(r.get("cornerPositions"), list)
        and len(r["cornerPositions"]) == 4
        and type(r["cornerPositions"][-1]) is int
        and 1 <= r["cornerPositions"][-1] <= 18
    ]
    if not cornered:
        return "no_valid_last_corner"
    if not any(r.get("hasAbnormalCode") is False for r in cornered):
        return "abnormal_or_incomplete_run"
    return "comparable"


def diagnose(report):
    """Return safe count/horse-number summary from a strict private report."""
    evidence = summarize_one_race(report)
    race = report["races"][0]
    surface = race.get("surfaceCandidate")
    distance = race.get("distanceMetersCandidate")
    if (race.get("status") != "historical_observations_not_graded"
            or surface not in COURSES or type(distance) is not int
            or not 400 <= distance <= 10000):
        return {
            "status": "CURRENT_COURSE_NOT_VERIFIED",
            "runnerCount": evidence["runnerCount"],
            "comparableRunners": None,
            "missing": [], "reasonCounts": {},
        }
    missing = []
    for horse in race["byNumber"]:
        reason = reason_for_runner(horse["recentObservedRuns"], surface, distance)
        if reason != "comparable":
            missing.append({"number": horse["number"], "reason": reason})
    missing.sort(key=lambda item: item["number"])
    reasons = Counter(item["reason"] for item in missing)
    return {
        "status": "RESEARCH_ONLY",
        "runnerCount": evidence["runnerCount"],
        "comparableRunners": evidence["runnerCount"] - len(missing),
        "missing": missing,
        "reasonCounts": {key: reasons[key] for key in REASONS if reasons[key]},
    }


def main():
    day = datetime.now(JST).strftime("%Y%m%d")
    try:
        source = private_source(day)
        with source.open("r", encoding="utf-8") as infile:
            report = json.load(infile)
        result = diagnose(report)
    except (OSError, ValueError, KeyError, TypeError, CoverageError,
            JvLocalCheckError):
        print("ARC_RACE_COMPARABILITY=SOURCE_NOT_VALID")
        return 1
    print("ARC_RACE_COMPARABILITY=" + result["status"])
    print("RUNNERS=" + str(result["runnerCount"]))
    if result["comparableRunners"] is not None:
        print("COMPARABLE=" + str(result["comparableRunners"]))
        print("NOT_COMPARABLE=" + str(len(result["missing"])))
        for item in result["missing"]:
            print("NUMBER=" + str(item["number"]) + " REASON="
                  + item["reason"] + " (" + REASONS[item["reason"]] + ")")
        for reason, count in result["reasonCounts"].items():
            print("REASON_COUNT=" + reason + ":" + str(count))
    print("OFFICIAL_JRA_VERIFIED=NO")
    print("FORMAL_TEN_FACTOR_GRADED=NO")
    print("BETTING_READY=NO")
    print("NETWORK_REQUESTS=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
