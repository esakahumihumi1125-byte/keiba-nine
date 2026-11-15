"""Owner-private JRDB /tch main-workout evidence availability audit.

Explicit manual request only, one date-bounded /tch read. No odds,
workout times, indices, names, horse IDs, private race keys, source rows or
betting signals are returned. Joining is ONLY by race+number and/or an
unambiguous horse ID from independently fetched /tky. Multiple workouts
per horse are permitted; zero-valued placeholder indices do not count as
usable main-workout evidence. Source presence != validated training grade.
"""
from datetime import datetime
import math
import re

from jrdb_coverage import CoverageError, audit_race_coverage
from jrdb_evidence_readiness import _valid_date

VERSION = "owner-main-workout-tch-evidence-1"
KEY = re.compile(r"[0-9a-f]{8}\Z", re.ASCII)
HORSE_ID = re.compile(r"[0-9a-z]{12}\Z", re.ASCII)
NUMBER = re.compile(r"(?:0[1-9]|1[0-8])\Z", re.ASCII)
MAX_WORKOUTS = 20000
MAX_PER_HORSE = 30


def _usable_text(value, field):
    if value is None or value == "":
        return False
    if (type(value) is not str or len(value) > 32
            or not value.strip() or any(ord(c) < 32 or ord(c) == 127
                                        for c in value)):
        raise CoverageError("Invalid main workout " + field)
    return True


def _index(value):
    if value is None:
        return False
    if type(value) not in (int, float) or not math.isfinite(value):
        raise CoverageError("Invalid main workout index")
    if not -1000 <= value <= 1000:
        raise CoverageError("Out-of-range main workout index")
    return value != 0  # /tch sample uses 0 when no real index is available.


def audit_main_workouts(programme, entries, workouts, day):
    """Summarize availability of actual /tch workouts; never grade a horse."""
    if not _valid_date(day):
        raise CoverageError("Invalid main workout date")
    base = audit_race_coverage(programme, entries, day)
    if (not isinstance(workouts, list) or len(workouts) > MAX_WORKOUTS
            or any(not isinstance(x, dict) for x in workouts)):
        raise CoverageError("Invalid main workout source")
    keys = {row["racekey"] for row in programme}
    by_number, by_id = {}, {}
    for entry in entries:
        key, num, hid = (entry["racekey"], entry["horse_number"],
                         entry.get("horse_id"))
        by_number[key, num] = True
        if hid not in (None, ""):
            if type(hid) is not str or not HORSE_ID.fullmatch(hid):
                raise CoverageError("Invalid main workout horse id")
            if (key, hid) in by_id:
                raise CoverageError("Ambiguous main workout horse id")
            by_id[key, hid] = num
    per_horse = {(key, num): {
        "rows": 0, "dated": False, "recent": False,
        "index": False, "finish": False, "paired": False,
    } for key, num in by_number}
    race_rows = {key: 0 for key in keys}
    today = datetime.strptime(day, "%Y%m%d").date()
    for row in workouts:
        key, date = row.get("racekey"), row.get("racedate")
        if (type(key) is not str or not KEY.fullmatch(key) or key not in keys
                or date != day):
            raise CoverageError("Main workout race/date mismatch")
        num, hid = row.get("horse_number"), row.get("horse_id")
        if num not in (None, "") and (type(num) is not str
                                     or not NUMBER.fullmatch(num)):
            raise CoverageError("Invalid main workout number")
        if hid not in (None, "") and (type(hid) is not str
                                     or not HORSE_ID.fullmatch(hid)):
            raise CoverageError("Invalid main workout id")
        number_link = num if (key, num) in by_number else None
        horse_link = by_id.get((key, hid)) if hid not in (None, "") else None
        if number_link and horse_link and number_link != horse_link:
            raise CoverageError("Main workout identity conflict")
        matched = horse_link or number_link
        if matched is None:
            raise CoverageError("Unmatched main workout runner")
        observed = per_horse[key, matched]
        observed["rows"] += 1
        race_rows[key] += 1
        if observed["rows"] > MAX_PER_HORSE:
            raise CoverageError("Too many workouts for one runner")
        raw_date = row.get("exercise_date")
        dated = False
        if raw_date not in (None, ""):
            if not _valid_date(raw_date):
                raise CoverageError("Invalid main workout exercise date")
            workout_day = datetime.strptime(raw_date, "%Y%m%d").date()
            if workout_day > today:
                raise CoverageError("Workout recorded after race date")
            days = (today - workout_day).days
            dated = True
            observed["dated"] = True
            if days <= 7:
                observed["recent"] = True
        finish = _usable_text(row.get("shimai"), "final time")
        _usable_text(row.get("ten"), "opening time")
        _usable_text(row.get("naka"), "middle time")
        _usable_text(row.get("abreast_result"), "paired-work status")
        raw_index = row.get("oikirisisu")
        has_index = _index(raw_index)
        observed["index"] |= has_index
        observed["finish"] |= finish
        if has_index and finish and dated:
            observed["paired"] = True
    by_coord = {(r["track"], r["race"]): r["racekey"] for r in programme}
    result = []
    for race in base["races"]:
        coord = (race["track"], race["race"])
        key = by_coord[coord]
        runners = []
        for num in sorted((number for k, number in by_number if k == key),
                          key=int):
            stats = per_horse[key, num]
            runners.append({
                "number": int(num),
                "mainWorkoutsRecorded": stats["rows"] > 0,
                "datedWorkoutRecorded": stats["dated"],
                "withinSevenDaysRecorded": stats["recent"],
                "mainIndexRecorded": stats["index"],
                "finalTimeRecorded": stats["finish"],
                "datedIndexTimePairRecorded": stats["paired"],
                "trainingGrade": "未評価",
                "trainingScore30": None,
                "modelCalibrated": False,
            })
        if len(runners) != race["observedEntries"]:
            raise CoverageError("Workout entry roster mismatched")
        result.append({
            "track": coord[0], "race": coord[1],
            "registered": len(runners),
            "sourceWorkoutRows": race_rows[key],
            "runnersWithWorkout": sum(r["mainWorkoutsRecorded"] for r in runners),
            "runnersWithRecentWorkout": sum(r["withinSevenDaysRecorded"] for r in runners),
            "runnersWithIndex": sum(r["mainIndexRecorded"] for r in runners),
            "runnersWithFinalTime": sum(r["finalTimeRecorded"] for r in runners),
            "runnersWithDatedIndexTime": sum(
                r["datedIndexTimePairRecorded"] for r in runners),
            "runners": runners,
            "workoutIndexCalibrated": False,
            "officialJraVerified": False,
            "trainingGradeReady": False, "trifectaReady": False,
        })
    if sum(r["sourceWorkoutRows"] for r in result) != len(workouts):
        raise CoverageError("Workout source total mismatch")
    return {
        "version": VERSION, "date": day, "raceCount": len(result),
        "races": result,
        "summary": {
            "workoutRows": len(workouts),
            "runnersWithWorkout": sum(r["runnersWithWorkout"] for r in result),
            "runnersWithRecentWorkout": sum(
                r["runnersWithRecentWorkout"] for r in result),
            "runnersWithIndex": sum(r["runnersWithIndex"] for r in result),
            "runnersWithDatedIndexTime": sum(
                r["runnersWithDatedIndexTime"] for r in result),
        },
        "sourceRequestsRequired": ["tra", "tky", "tch"],
        "sourceFamily": "jrdb_tch_owner_prestart",
        "researchOnly": True, "privateOwnerOnly": True,
        "horseIdsIncluded": False, "rawWorkoutValuesIncluded": False,
        "oddsUsed": False, "officialJraVerified": False,
        "modelCalibrated": False, "trainingGradeReady": False,
        "overallPredictionReady": False, "bettingReady": False,
        "actualPurchase": False, "changesExistingTickets": False,
        "changesExistingReceipts": False, "changesExistingRoi": False,
        "additionalPaidReadsAfterSource": 0,
        "note": ("JRDB本追切の調教日・終い・追切指数の記録有無だけを集計。"
                 "指数0や未発表は観測扱いにしません。未評価を勝手に補完せず、"
                 "正式な調教30点や3連単・購入・回収率には反映しません。"),
    }
