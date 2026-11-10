"""Offline source-gap contract tests. No paid JRDB or JRA requests."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_experimental_pace_scenarios import hypothesize_owner_pace
from jrdb_course_ground_factor_bridge import (
    enrich_course_ground_matrix, summarize_owner_runner_course_going
)
from owner_three_factor_source_gaps import three_factor_source_gaps, VERSION
from test_jrdb_course_ground_factor_bridge import prepare


def sample():
    base, observations = prepare()
    course = enrich_course_ground_matrix(
        base, observations, history_complete=True
    )
    historical = summarize_owner_runner_course_going(course, observations)
    pace = hypothesize_owner_pace(base)
    return historical, pace


class ThreeFactorSourceGapTests(unittest.TestCase):
    def test_real_private_observation_shapes_join_without_grading(self):
        history, pace = sample()
        unchanged = copy.deepcopy((history, pace))
        result = three_factor_source_gaps(history, pace)
        self.assertEqual((history, pace), unchanged)
        self.assertEqual(result["version"], VERSION)
        self.assertEqual(result["factorWeights"], {
            "course_distance": 17, "pace": 17, "ground": 12
        })
        self.assertEqual(result["weightTotal"], 46)
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["extraProviderCalls"], 0)
        self.assertFalse(result["overallPredictionReady"])
        self.assertFalse(result["officialJraVerified"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["formalGradesVerified"], 0)
        tokyo = next(r for r in result["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["observed"]["courseComparableObserved"], 1)
        self.assertEqual(tokyo["observed"]["sameGoingObserved"], 1)
        self.assertEqual(tokyo["gaps"]["noCourseComparableRuns"], 1)
        self.assertEqual(tokyo["formalGradesVerified"], 0)
        for private in ("racekey", "horse_id", "horse_number", "PAID-SECRET"):
            self.assertNotIn(private, repr(result))

    def test_missing_current_going_is_not_graded_or_bad_ability(self):
        history, pace = sample()
        horse = history["races"][0]["runners"][0]
        horse["currentGoingRecorded"] = False
        horse["matchingCurrentGoingRuns"] = 0
        horse["matchingCurrentGoingTopThreeRuns"] = 0
        report = three_factor_source_gaps(history, pace)
        tokyo = next(r for r in report["races"] if r["track"] == "東京")
        self.assertGreater(tokyo["gaps"]["currentGoingUnknown"], 0)
        self.assertEqual(tokyo["formalGradesVerified"], 0)
        self.assertFalse(tokyo["bettingReady"])

    def test_duplicate_horse_or_missing_race_fails_closed(self):
        history, pace = sample()
        pace["races"].pop()
        pace["raceCount"] -= 1
        with self.assertRaises(CoverageError):
            three_factor_source_gaps(history, pace)
        history, pace = sample()
        pace["races"][0]["runners"][1]["number"] = (
            pace["races"][0]["runners"][0]["number"]
        )
        with self.assertRaises(CoverageError):
            three_factor_source_gaps(history, pace)

    def test_no_forged_material_readiness_or_legacy_weight_17(self):
        for kind in ("grade", "ready", "weight", "coverage"):
            history, pace = sample()
            if kind == "grade":
                history["gradeReady"] = True
            elif kind == "ready":
                pace["races"][0]["paceForecastReady"] = True
            elif kind == "weight":
                # 20 is the historical hypothesis weight. New output is 17.
                pace["factorWeight"] = 17
            else:
                pace["races"][0]["coverageAdequate"] = True
            with self.subTest(kind=kind), self.assertRaises(CoverageError):
                three_factor_source_gaps(history, pace)

    def test_inconsistent_history_counts_and_source_rows_fail(self):
        for kind in ("negative", "overlap", "missing"):
            history, pace = sample()
            h = history["races"][0]["runners"][0]
            if kind == "negative":
                h["comparableRuns"] = -1
            elif kind == "overlap":
                h["matchingCurrentGoingRuns"] = 5
            else:
                h.pop("historyLookupComplete")
            with self.subTest(kind=kind), self.assertRaises(CoverageError):
                three_factor_source_gaps(history, pace)


if __name__ == "__main__":
    unittest.main()
