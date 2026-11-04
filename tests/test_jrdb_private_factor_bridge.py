"""Synthetic-only tests for the private 10-factor evidence bridge."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_private_factor_bridge import (
    build_private_factor_matrix, summarize_factor_materials,
)
from test_jrdb_training_hypothesis import setup as workout_sample
from test_jrdb_recent_hypothesis import fixture as recent_sample


def inputs():
    p, entries, training = workout_sample()
    _, _, previous = recent_sample()
    return (build_training_hints(p, entries, training, "20261101"),
            build_recent_hints(p, entries, previous, "20261101"))


class PrivateFactorBridgeTests(unittest.TestCase):
    def test_ten_factor_slots_maintain_unmapped_factors(self):
        matrix = build_private_factor_matrix(*inputs())
        tokyo = matrix[0]
        self.assertEqual(len(tokyo["byNumber"]), 2)
        first = tokyo["byNumber"]["01"]
        self.assertEqual(set(first), set(FACTORS))
        self.assertEqual(first["training"], {
            "grade": "S", "basis": "experimental_workout_index"
        })
        self.assertEqual(first["recent"], {
            "grade": "S", "basis": "experimental_recent_idm"
        })
        self.assertEqual(first["pace"]["grade"], "未評価")
        self.assertEqual(first["pace"]["basis"], "historical_fourth_corner_only")
        self.assertEqual(first["pace"]["positionObservation"], "frontObserved")
        for factor in set(FACTORS) - {"training", "recent", "pace"}:
            self.assertEqual(first[factor], {
                "grade": "未評価", "basis": "not_mapped"
            })
        self.assertFalse(tokyo["predictionReady"])
        self.assertFalse(tokyo["bettingReady"])
        self.assertFalse(tokyo["independentJraVerified"])

    def test_only_aggregate_position_and_factor_counts_leave_private_matrix(self):
        data = summarize_factor_materials(build_private_factor_matrix(*inputs()))
        tokyo, kyoto = data["races"]
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["provisionalGradeCounts"], {
            "trainingProvisional": 2, "recentProvisional": 2,
        })
        self.assertEqual(tokyo["pastFourthCorner"], {
            "frontObserved": 1, "backObserved": 0,
            "mixedObserved": 0, "insufficient": 1,
        })
        self.assertEqual(kyoto["pastFourthCorner"]["insufficient"], 1)
        self.assertEqual(kyoto["provisionalGradeCounts"]["recentProvisional"], 0)
        self.assertEqual(tokyo["mappedFactors"], ["training", "recent"])
        self.assertEqual(tokyo["observationOnlyFactors"], ["pace"])
        self.assertEqual(tokyo["unmappedFactorCount"], 7)
        self.assertFalse(tokyo["paceForecastAvailable"])
        self.assertFalse(tokyo["overallRankReady"])
        self.assertFalse(data["predictionReady"])
        self.assertFalse(data["bettingReady"])
        for private in ("horse_number", "horse_id", "racekey", "byNumber",
                        "SECRET-PAID-HORSE", "2328aaa95a05", "01",
                        "oikirisisu", "race_back_"):
            self.assertNotIn(private, repr(data))

    def test_changed_position_label_stays_observation_not_grade(self):
        a, b = inputs()
        b[0]["byNumber"]["01"]["fourthObserved"] = 2
        b[0]["byNumber"]["01"]["frontAtFourth"] = 0
        matrix = build_private_factor_matrix(a, b)
        first = matrix[0]["byNumber"]["01"]["pace"]
        self.assertEqual(first["positionObservation"], "backObserved")
        self.assertEqual(first["grade"], "未評価")
        grouped = summarize_factor_materials(matrix)
        self.assertEqual(grouped["races"][0]["pastFourthCorner"]["backObserved"], 1)

    def test_conflicting_runner_sets_fail_without_guessing(self):
        for field in ("training", "recent"):
            a, b = inputs()
            if field == "training": del a[0]["gradesByNumber"]["02"]
            else: del b[0]["byNumber"]["02"]
            with self.subTest(field=field), self.assertRaises(CoverageError):
                build_private_factor_matrix(a, b)

    def test_conflicting_race_date_or_identity_rejected(self):
        for change in ("racekey", "track", "duplicate"):
            a, b = inputs()
            if change == "racekey": b[0]["racekey"] = "05264b02"
            elif change == "track": b[0]["track"] = "京都"
            else: a.append(copy.deepcopy(a[0]))
            with self.subTest(change=change), self.assertRaises(CoverageError):
                build_private_factor_matrix(a, b)

    def test_bad_grade_and_position_rejected(self):
        for grade in (None, "X", True, 3):
            a, b = inputs()
            a[0]["gradesByNumber"]["01"] = grade
            with self.subTest(grade=grade), self.assertRaises(CoverageError):
                build_private_factor_matrix(a, b)
        for observed, front in ((4, 2), (2, 3), (True, 1),
                                (2, False), ("2", 1), (1, -1)):
            a, b = inputs()
            b[0]["byNumber"]["01"].update(
                fourthObserved=observed, frontAtFourth=front
            )
            with self.subTest(position=(observed, front)), self.assertRaises(CoverageError):
                build_private_factor_matrix(a, b)

    def test_aggregate_cannot_promote_an_unmapped_or_pace_factor(self):
        matrix = build_private_factor_matrix(*inputs())
        row = matrix[0]["byNumber"]["01"]
        for factor, grade in (("pace", "S"), ("ground", "A")):
            invalid = copy.deepcopy(matrix)
            invalid[0]["byNumber"]["01"][factor]["grade"] = grade
            with self.subTest(factor=factor), self.assertRaises(CoverageError):
                summarize_factor_materials(invalid)

    def test_aggregate_cannot_claim_betting_or_verified_jra(self):
        matrix = build_private_factor_matrix(*inputs())
        for key, value in (("bettingReady", True), ("predictionReady", True),
                           ("independentJraVerified", True)):
            invalid = copy.deepcopy(matrix)
            invalid[0][key] = value
            with self.subTest(key=key), self.assertRaises(CoverageError):
                summarize_factor_materials(invalid)

    def test_source_inputs_are_never_mutated(self):
        a, b = inputs()
        before = copy.deepcopy((a, b))
        summarize_factor_materials(build_private_factor_matrix(a, b))
        self.assertEqual((a, b), before)


if __name__ == "__main__":
    unittest.main()
