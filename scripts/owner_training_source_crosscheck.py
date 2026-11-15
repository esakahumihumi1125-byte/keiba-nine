"""Owner-private /tcy x /tch training SOURCE overlap, not a fitness grade.

One explicitly requested day, four total /tra /tky /tcy /tch provider
reads, all held in trusted memory only. A workout /tcy grade is used ONLY
as a marker that both numeric source indices passed the existing
research-level validity check; the provisional S/A/B/C is never emitted.
A /tch complete row has dated, nonzero index and final-time evidence.
Workouts can have more than one row per runner. These distinct provider
sources do NOT promise numerically equal index values.
"""
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_main_workout_evidence import (
    audit_main_workouts, VERSION as TCH_VERSION,
)

VERSION = "owner-training-tcy-tch-crosscheck-1"
SOURCE_IDS = ["tra", "tky", "tcy", "tch"]
MAX_RACES = 120


def crosscheck_training_sources(programme, entries, training, workouts, day):
    """Returns only redacted race-level source availability, never scores."""
    main = audit_main_workouts(programme, entries, workouts, day)
    hints = build_training_hints(programme, entries, training, day)
    if (main.get("version") != TCH_VERSION
            or main.get("raceCount") != len(programme)
            or len(hints) != len(programme)
            or len(programme) > MAX_RACES):
        raise CoverageError("Training source race set mismatch")
    by_coord = {}
    for row in hints:
        coord = row.get("track"), row.get("race")
        if (coord in by_coord
                or not isinstance(row.get("gradesByNumber"), dict)
                or row.get("researchOnly") is not True
                or row.get("predictionReady") is not False):
            raise CoverageError("Invalid training analysis evidence")
        by_coord[coord] = row
    result = []
    totals = dict.fromkeys((
        "registered", "tcyComplete", "tchComplete", "bothComplete",
        "tcyOnly", "tchOnly", "neither", "tchWorkoutPresent",
        "tchRecentWorkoutPresent",
    ), 0)
    seen = set()
    for row in main["races"]:
        coord = row["track"], row["race"]
        if coord in seen or coord not in by_coord:
            raise CoverageError("Training main workout race identity mismatch")
        seen.add(coord)
        hint = by_coord[coord]["gradesByNumber"]
        observed = row["runners"]
        if (row["registered"] != len(observed)
                or len(hint) != len(observed)
                or set(hint) != {str(x["number"]).zfill(2) for x in observed}
                or any(label not in ("S", "A", "B", "C", "未評価")
                       for label in hint.values())):
            raise CoverageError("Training source horse roster differs")
        counts = dict.fromkeys((
            "tcyComplete", "tchComplete", "bothComplete", "tcyOnly",
            "tchOnly", "neither", "tchWorkoutPresent",
            "tchRecentWorkoutPresent",
        ), 0)
        for horse in observed:
            number = str(horse["number"]).zfill(2)
            tcy_complete = hint[number] != "未評価"
            tch_complete = horse["datedIndexTimePairRecorded"]
            if (type(tch_complete) is not bool
                    or type(horse["mainWorkoutsRecorded"]) is not bool
                    or type(horse["withinSevenDaysRecorded"]) is not bool):
                raise CoverageError("Invalid main-workout source flags")
            counts["tcyComplete"] += int(tcy_complete)
            counts["tchComplete"] += int(tch_complete)
            counts["bothComplete"] += int(tcy_complete and tch_complete)
            counts["tcyOnly"] += int(tcy_complete and not tch_complete)
            counts["tchOnly"] += int(tch_complete and not tcy_complete)
            counts["neither"] += int(not tcy_complete and not tch_complete)
            counts["tchWorkoutPresent"] += int(horse["mainWorkoutsRecorded"])
            counts["tchRecentWorkoutPresent"] += int(
                horse["withinSevenDaysRecorded"])
        n = row["registered"]
        if (sum(counts[k] for k in ("bothComplete", "tcyOnly", "tchOnly",
                                   "neither")) != n
                or counts["tcyComplete"] != (
                    counts["bothComplete"] + counts["tcyOnly"])
                or counts["tchComplete"] != (
                    counts["bothComplete"] + counts["tchOnly"])
                or counts["tchComplete"] != row["runnersWithDatedIndexTime"]
                or counts["tchWorkoutPresent"] != row["runnersWithWorkout"]
                or counts["tchRecentWorkoutPresent"] != row["runnersWithRecentWorkout"]):
            raise CoverageError("Inconsistent training completeness counts")
        item = {
            "track": coord[0], "race": coord[1],
            "registered": n, **counts,
            "bothSourcesForEveryRunner": counts["bothComplete"] == n and n > 0,
            "trainingGradeCalibrated": False,
            "formalTrainingScore30Ready": False,
            "jraOfficialVerified": False, "trifectaReady": False,
        }
        result.append(item)
        totals["registered"] += n
        for key in counts:
            totals[key] += counts[key]
    if seen != set(by_coord):
        raise CoverageError("Training comparison incomplete")
    return {
        "version": VERSION, "date": day, "raceCount": len(result),
        "races": result, "summary": totals,
        "sourceRequestsRequired": SOURCE_IDS,
        "researchOnly": True, "privateOwnerOnly": True,
        "rawWorkoutValuesIncluded": False, "horseIdentifiersIncluded": False,
        "oddsUsed": False, "indexValuesCompared": False,
        "jraOfficialVerified": False, "trainingGradeCalibrated": False,
        "formalTrainingScore30Ready": False,
        "overallPredictionReady": False, "bettingReady": False,
        "actualPurchase": False, "changesExistingTickets": False,
        "changesExistingReceipts": False, "changesExistingRoi": False,
        "additionalProviderRequestsAfterFour": 0,
        "note": (
            "調教分析(/tcy)の追切・仕上指数と本追切(/tch)の"
            "日付・追切指数・終いタイムの資料が同一出走馬に"
            "揃うかだけを照合。指数値そのものの一致、"
            "S/A/B/Cの精度、JRA公式結果は未検証。"
            "正式調教30点、3連単、保存済み馬券には反映しない。"
        ),
    }
