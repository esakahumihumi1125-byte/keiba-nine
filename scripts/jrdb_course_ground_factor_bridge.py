"""Join bounded private course/going history to the 10-factor research matrix.

All rows remain in owner-only memory. Never treat observed past runs as
suitability, confidence, race ranking, or purchase advice. This module
performs no JRDB requests; it only consumes already checked source snapshots.
"""
from copy import deepcopy

from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import KEY, NUMBER
from jrdb_private_factor_bridge import summarize_factor_materials
from jrdb_program_preview import TRACKS

VERSION = "private-course-ground-materials-1"
COURSE_BASIS = "historical_surface_distance_counts"
GOING_BASIS = "historical_going_counts"
UNMAPPED = {"grade": "未評価", "basis": "not_mapped"}
COUNTS = (
    "datedRuns", "linkedPastProgrammes", "missingPastProgrammes",
    "sameSurfaceNearDistanceRuns", "topThreeComparableRuns",
    "knownGoingComparableRuns", "unknownGoingComparableRuns",
    "heavyComparableRuns", "poorComparableRuns", "sameCurrentGoingComparableRuns",
    "heavyTopThreeRuns", "poorTopThreeRuns",
)


def _count(value, upper=5):
    if type(value) is not int or not 0 <= value <= upper:
        raise CoverageError("Invalid historical observation count")
    return value


def _check_race(row):
    if (not isinstance(row, dict) or not isinstance(row.get("racekey"), str)
            or not KEY.fullmatch(row["racekey"])
            or row.get("track") not in TRACKS.values()
            or type(row.get("race")) is not int or not 1 <= row["race"] <= 12
            or row.get("predictionReady") is not False
            or row.get("goingSuitabilityAssessed") is not False
            or type(row.get("currentGoingRecorded")) is not bool
            or not isinstance(row.get("byNumber"), dict)
            or len(row["byNumber"]) > 18):
        raise CoverageError("Invalid historical race or missing safeguards")


def _check_stats(row, known_current):
    stats = {k: _count(row.get(k)) for k in COUNTS}
    if (stats["datedRuns"] != stats["linkedPastProgrammes"]
            + stats["missingPastProgrammes"]
            or stats["sameSurfaceNearDistanceRuns"] > stats["linkedPastProgrammes"]
            or stats["topThreeComparableRuns"] > stats["sameSurfaceNearDistanceRuns"]
            or stats["knownGoingComparableRuns"]
            + stats["unknownGoingComparableRuns"] != stats["sameSurfaceNearDistanceRuns"]
            or stats["heavyComparableRuns"] + stats["poorComparableRuns"]
            > stats["knownGoingComparableRuns"]
            or stats["heavyTopThreeRuns"] > stats["heavyComparableRuns"]
            or stats["poorTopThreeRuns"] > stats["poorComparableRuns"]
            or stats["sameCurrentGoingComparableRuns"] > stats["knownGoingComparableRuns"]
            or (not known_current and stats["sameCurrentGoingComparableRuns"])):
        raise CoverageError("Course/going observation counts disagree")
    return stats


def enrich_course_ground_matrix(matrix, historical, *, history_complete):
    """Attach historical evidence by exact racekey AND runner number.

    No grade is assigned. A full provider lookup is not equivalent to
    verified JRA conditions or aptitude; missing history stays unknown.
    """
    if type(history_complete) is not bool:
        raise CoverageError("History completeness must be explicit")
    # Validate all existing factor slots before touching the protected matrix.
    summarize_factor_materials(matrix)
    if not isinstance(historical, list) or len(historical) > 120:
        raise CoverageError("Invalid historical factor collection")
    reference = {}
    coords = set()
    for row in historical:
        _check_race(row)
        key = row["racekey"]
        coordinate = (row["track"], row["race"])
        if key in reference or coordinate in coords:
            raise CoverageError("Duplicate historical race identity")
        reference[key] = row
        coords.add(coordinate)
    if len(matrix) != len(reference):
        raise CoverageError("Incomplete historical race set")
    enriched = []
    for race in matrix:
        old = reference.get(race["racekey"])
        if old is None or (race["track"], race["race"]) != (old["track"], old["race"]):
            raise CoverageError("Historical factor race mismatch")
        raw = old["byNumber"]
        if set(race["byNumber"]) != set(raw):
            raise CoverageError("Historical runner identities disagree")
        updated = deepcopy(race)
        for number, stats in raw.items():
            if not isinstance(number, str) or not NUMBER.fullmatch(number):
                raise CoverageError("Invalid historical runner number")
            if not isinstance(stats, dict):
                raise CoverageError("Invalid historical runner observations")
            values = _check_stats(stats, old["currentGoingRecorded"])
            slots = updated["byNumber"][number]
            if (set(slots) != set(FACTORS)
                    or slots["course_distance"] != UNMAPPED
                    or slots["ground"] != UNMAPPED):
                raise CoverageError("Course and going factor slots are not empty")
            course = values["sameSurfaceNearDistanceRuns"]
            known = values["knownGoingComparableRuns"]
            unknown = values["unknownGoingComparableRuns"]
            full = history_complete and values["missingPastProgrammes"] == 0
            slots["course_distance"] = {
                "grade": "未評価", "basis": COURSE_BASIS,
                "comparableRuns": course,
                "unlinkedRuns": values["missingPastProgrammes"],
                "historyLookupComplete": full,
            }
            slots["ground"] = {
                "grade": "未評価", "basis": GOING_BASIS,
                "knownComparableRuns": known,
                "unknownComparableRuns": unknown,
                "wetComparableRuns": values["heavyComparableRuns"]
                                      + values["poorComparableRuns"],
                "matchingCurrentGoingRuns": values["sameCurrentGoingComparableRuns"],
                "currentGoingRecorded": old["currentGoingRecorded"],
                "historyLookupComplete": full and unknown == 0,
            }
        enriched.append(updated)
    return enriched


def summarize_owner_runner_course_going(enriched, historical):
    """Private per-horse-number *observations*, never grades or raw licensed rows.

    Existing internal identity joins and count validation must pass first.
    Only bounded small integer counts are returned; horse_id, racekey, names,
    detailed form, source records and historical race identifiers stay private.
    """
    summarize_course_ground_matrix(enriched)
    if not isinstance(historical, list) or len(historical) != len(enriched):
        raise CoverageError("Per-horse historical race set mismatch")
    by_coord = {}
    for row in historical:
        _check_race(row)
        key = row["track"], row["race"]
        if key in by_coord:
            raise CoverageError("Repeated per-horse historical race")
        by_coord[key] = row
    output = []
    for r in enriched:
        coord = r["track"], r["race"]
        history = by_coord.get(coord)
        if history is None or history.get("racekey") != r["racekey"]:
            raise CoverageError("Per-horse historical race identity mismatch")
        if set(history["byNumber"]) != set(r["byNumber"]):
            raise CoverageError("Per-horse history roster mismatch")
        runners = []
        for number in sorted(history["byNumber"]):
            stats = _check_stats(history["byNumber"][number],
                                 history["currentGoingRecorded"])
            slots = r["byNumber"][number]
            course, ground = slots["course_distance"], slots["ground"]
            wet = stats["heavyComparableRuns"] + stats["poorComparableRuns"]
            wet_top_three = stats["heavyTopThreeRuns"] + stats["poorTopThreeRuns"]
            if (course["grade"] != "未評価"
                    or ground["grade"] != "未評価"
                    or slots["pace"]["grade"] != "未評価"
                    or course["comparableRuns"] != stats["sameSurfaceNearDistanceRuns"]
                    or course["unlinkedRuns"] != stats["missingPastProgrammes"]
                    or ground["knownComparableRuns"] != stats["knownGoingComparableRuns"]
                    or ground["matchingCurrentGoingRuns"] != stats["sameCurrentGoingComparableRuns"]
                    or ground["wetComparableRuns"] != wet
                    or ground["currentGoingRecorded"] != history["currentGoingRecorded"]
                    or stats["topThreeComparableRuns"] > course["comparableRuns"]
                    or wet_top_three > wet):
                raise CoverageError("Per-horse historical counts disagree")
            runners.append({
                "number": int(number),
                "comparableRuns": course["comparableRuns"],
                "comparableTopThreeRuns": stats["topThreeComparableRuns"],
                "knownGoingRuns": ground["knownComparableRuns"],
                "matchingCurrentGoingRuns": ground["matchingCurrentGoingRuns"],
                "wetGoingRuns": wet,
                "wetTopThreeRuns": wet_top_three,
                "missingPastProgrammes": course["unlinkedRuns"],
                "historyLookupComplete": course["historyLookupComplete"],
                "currentGoingRecorded": ground["currentGoingRecorded"],
            })
        output.append({
            "track": coord[0], "race": coord[1],
            "runnerCount": len(runners), "runners": runners,
            "gradeReady": False, "courseSuitabilityAssessed": False,
            "goingSuitabilityAssessed": False, "paceForecastReady": False,
        })
    if len(output) != len(by_coord):
        raise CoverageError("Per-horse historical race count mismatch")
    return {
        "version": "owner-runner-course-going-observation-1",
        "raceCount": len(output), "races": output,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "gradeReady": False,
        "predictionReady": False, "bettingReady": False,
    }


def summarize_course_ground_matrix(enriched):
    """Only coarse per-race totals may leave the private backend."""
    if not isinstance(enriched, list) or len(enriched) > 120:
        raise CoverageError("Invalid enriched factor matrix")
    results, seen = [], set()
    for row in enriched:
        if (not isinstance(row, dict)
                or row.get("track") not in TRACKS.values()
                or type(row.get("race")) is not int or not 1 <= row["race"] <= 12
                or row.get("researchOnly") is not True
                or row.get("independentJraVerified") is not False
                or row.get("predictionReady") is not False
                or row.get("bettingReady") is not False
                or not isinstance(row.get("byNumber"), dict)
                or len(row["byNumber"]) > 18):
            raise CoverageError("Invalid enriched factor state")
        coord = row["track"], row["race"]
        if coord in seen:
            raise CoverageError("Repeated historical factor race")
        seen.add(coord)
        count = 0
        course = known = wet = matching = missing = unknown = 0
        missing_current = 0
        for number, slots in row["byNumber"].items():
            if (not isinstance(number, str) or not NUMBER.fullmatch(number)
                    or not isinstance(slots, dict) or set(slots) != set(FACTORS)):
                raise CoverageError("Invalid enriched runner factors")
            # The previously graded experimental factors and pace observation
            # must retain their safe shape, even when the history is appended.
            if (slots.get("training", {}).get("basis") != "experimental_workout_index"
                    or slots.get("recent", {}).get("basis") != "experimental_recent_idm"
                    or slots.get("training", {}).get("grade") not in ("S", "A", "B", "C", "未評価")
                    or slots.get("recent", {}).get("grade") not in ("S", "A", "B", "C", "未評価")
                    or slots.get("pace", {}).get("basis") != "historical_fourth_corner_only"
                    or slots.get("pace", {}).get("grade") != "未評価"
                    or slots.get("pace", {}).get("positionObservation") not in (
                        "frontObserved", "backObserved", "mixedObserved", "insufficient")
                    or any(slots[f] != UNMAPPED
                           for f in set(FACTORS) - {
                               "training", "recent", "pace", "course_distance", "ground"})):
                raise CoverageError("Incomplete or promoted nonhistorical factors")
            a, b = slots["course_distance"], slots["ground"]
            if (not isinstance(a, dict) or not isinstance(b, dict)
                    or set(a) != {"grade", "basis", "comparableRuns", "unlinkedRuns",
                                  "historyLookupComplete"}
                    or set(b) != {"grade", "basis", "knownComparableRuns",
                                  "unknownComparableRuns", "wetComparableRuns",
                                  "matchingCurrentGoingRuns", "currentGoingRecorded",
                                  "historyLookupComplete"}
                    or a["grade"] != "未評価" or a["basis"] != COURSE_BASIS
                    or b["grade"] != "未評価" or b["basis"] != GOING_BASIS
                    or type(a["historyLookupComplete"]) is not bool
                    or type(b["historyLookupComplete"]) is not bool
                    or type(b["currentGoingRecorded"]) is not bool):
                raise CoverageError("Historical factors cannot imply aptitude")
            c = _count(a["comparableRuns"])
            u = _count(a["unlinkedRuns"])
            k = _count(b["knownComparableRuns"])
            x = _count(b["unknownComparableRuns"])
            w = _count(b["wetComparableRuns"])
            m = _count(b["matchingCurrentGoingRuns"])
            if (k + x != c or w > k or m > k
                    or (not b["currentGoingRecorded"] and m > 0)
                    or b["historyLookupComplete"] and (
                        not a["historyLookupComplete"] or x > 0)):
                raise CoverageError("Contradictory historical factor slots")
            count += 1
            course += c > 0
            known += k > 0
            wet += w > 0
            matching += m > 0
            missing += u > 0 or not a["historyLookupComplete"]
            unknown += x
            missing_current += not b["currentGoingRecorded"]
        results.append({
            "track": coord[0], "race": coord[1], "runnerCount": count,
            "runnersWithComparableCourse": course,
            "runnersWithKnownGoingComparable": known,
            "runnersWithWetComparable": wet,
            "runnersMatchingCurrentGoing": matching,
            "runnersWithIncompleteHistory": missing,
            "unknownComparableGoingRuns": unknown,
            "runnersWithCurrentGoingUnknown": missing_current,
            "observationOnlyFactors": ["pace", "course_distance", "ground"],
            "unmappedFactorCount": 5,
            "verifiedFactorCount": 0,
            "suitabilityAssessed": False,
            "overallRankReady": False,
            "predictionReady": False, "bettingReady": False,
        })
    return {"version": VERSION, "raceCount": len(results), "races": results,
            "predictionReady": False, "bettingReady": False,
            "note": ("過去番組と馬場の照合済み部分を10項目の内部資料に接続。"
                     "コース・距離と馬場は観測数のみで適性ランクは未評価。"
                     "近走・調教は未検証、展開と他5項目も未評価。"
                     "JRA公式確認・総合順位・買い目は作成していません。")}
