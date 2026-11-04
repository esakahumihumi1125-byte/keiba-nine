"""Join the private 8-slot entry matrix and 2 historical factor slots.

This function operates ONLY on independently validated, same-snapshot private
matrices. The complete horse-number matrix is never returned or stored.
The output is a coarse per-race audit, NOT ten evaluated/graded factors.
No paid calls, official JRA checks, persistence, or predictions.
"""
from copy import deepcopy

from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from jrdb_private_factor_bridge import summarize_factor_materials
from jrdb_entry_rotation_materials import NO_DATA
from jrdb_personnel_body_materials import summarize_personnel_body_matrix
from jrdb_course_ground_factor_bridge import summarize_course_ground_matrix

VERSION = "combined-ten-factor-observations-1"
ENTRY_FACTORS = (
    "pedigree", "draw_weight", "rotation", "jockey_stable", "body_condition",
)
BASE_FACTORS = ("training", "recent", "pace")
HISTORY_FACTORS = ("course_distance", "ground")
EXPECTED = set(FACTORS)


def _index(matrix):
    if not isinstance(matrix, list) or len(matrix) > 120:
        raise CoverageError("Invalid private factor collection")
    out = {}
    coords = set()
    for race in matrix:
        if not isinstance(race, dict):
            raise CoverageError("Invalid private factor race")
        key = race.get("racekey")
        coord = (race.get("track"), race.get("race"))
        if not isinstance(key, str) or key in out or coord in coords:
            raise CoverageError("Duplicate private race identity")
        out[key] = race
        coords.add(coord)
    return out


def combine_ten_factor_observations(course_matrix, entry_matrix):
    """Redacted per-race totals; no horse-level values ever leave this call.

    Course/going is taken exclusively from explicit, bounded /dra + /dka
    audit. The other eight slots come from the same-day /tky,/tcy,/tze
    research matrix and remain ungraded or provisional.
    """
    # These reject grade promotions, bad source formats, and altered roster states.
    course_summary = summarize_course_ground_matrix(course_matrix)
    entry_summary = summarize_personnel_body_matrix(entry_matrix)
    course_by_key = _index(course_matrix)
    entry_by_key = _index(entry_matrix)
    if set(course_by_key) != set(entry_by_key):
        raise CoverageError("Private history and entry race sets differ")
    course_counts = {(r["track"], r["race"]): r for r in course_summary["races"]}
    entry_counts = {(r["track"], r["race"]): r for r in entry_summary["races"]}
    if (course_summary["predictionReady"] is not False
            or course_summary["bettingReady"] is not False
            or entry_summary["predictionReady"] is not False
            or entry_summary["bettingReady"] is not False
            or set(course_counts) != set(entry_counts)):
        raise CoverageError("Private source status differs")
    result = []
    for key, history in course_by_key.items():
        entry = entry_by_key[key]
        if ((entry.get("track"), entry.get("race"))
                != (history.get("track"), history.get("race"))):
            raise CoverageError("Historical and entry race coordinates differ")
        coord = history["track"], history["race"]
        h, p = course_counts[coord], entry_counts[coord]
        hs, ps = history["byNumber"], entry["byNumber"]
        if (set(hs) != set(ps) or len(hs) != h["runnerCount"]
                or h["runnerCount"] != p["runnerCount"]):
            raise CoverageError("Historical and entry runner rosters differ")
        for number, slots in hs.items():
            other = ps[number]
            if (not isinstance(slots, dict) or not isinstance(other, dict)
                    or set(slots) != EXPECTED or set(other) != EXPECTED
                    or any(slots[factor] != other[factor] for factor in BASE_FACTORS)
                    or any(slots[factor] != NO_DATA for factor in ENTRY_FACTORS)
                    or any(other[factor] != NO_DATA for factor in HISTORY_FACTORS)):
                raise CoverageError("Private factor slot source mismatch")
            # Join all ten slots internally; do not return this merged matrix.
            joined = deepcopy(slots)
            for factor in ENTRY_FACTORS:
                joined[factor] = deepcopy(other[factor])
            if (set(joined) != EXPECTED
                    or any(joined[factor].get("grade") != "未評価"
                           for factor in (*ENTRY_FACTORS, *HISTORY_FACTORS, "pace"))):
                raise CoverageError("Observation source cannot assign grades")
        counts = p["recorded"]
        n = h["runnerCount"]
        if (not 0 <= h["runnersWithKnownGoingComparable"] <=
                h["runnersWithComparableCourse"] <= n
                or not 0 <= counts["bothPersonnelNamesRecorded"] <= n
                or not 0 <= counts["anyConformationRecorded"] <= n
                or h["verifiedFactorCount"] != 0
                or p["verifiedFactorCount"] != 0
                or h["suitabilityAssessed"] is not False
                or p["jockeyTrainerPerformanceAssessed"] is not False
                or p["bodyConditionAssessed"] is not False
                or p["raceDayBodyWeightFetched"] is not False):
            raise CoverageError("Private source aggregates are inconsistent")
        result.append({
            "track": coord[0], "race": coord[1], "runnerCount": n,
            "sourceMaterialSlots": 10,
            "provisionalFactorSlots": 2,  # training/recent heuristics, NOT validated grades
            "observationOnlySlots": 8,
            "unmappedFactorCount": 0,
            "verifiedFactorCount": 0,
            "runnersWithComparableCourse": h["runnersWithComparableCourse"],
            "runnersWithKnownGoingComparable": h["runnersWithKnownGoingComparable"],
            "runnersWithIncompleteHistory": h["runnersWithIncompleteHistory"],
            "runnersWithBothPersonnelNames": counts["bothPersonnelNamesRecorded"],
            "runnersWithConformationCodes": counts["anyConformationRecorded"],
            "historySuitabilityAssessed": False,
            "jockeyTrainerPerformanceAssessed": False,
            "bodyConditionAssessed": False,
            "raceDayBodyWeightFetched": False,
            "officialJraFinalVerification": False,
            "overallRankReady": False,
            "predictionReady": False,
            "bettingReady": False,
        })
    return {
        "version": VERSION, "raceCount": len(result),
        "races": sorted(result, key=lambda row: (row["track"], row["race"])),
        "predictionReady": False, "bettingReady": False,
        "note": ("資料項目10/10を本人用メモリ上で照合。調教と近走は未検証の"
                 "暫定基準、残る8項目は観測資料のみ。"
                 "欠損・履歴不足は不適性を意味しない。"
                 "JRA公式照合、総合S/A/B/C、3連単は未実施。"),
    }
