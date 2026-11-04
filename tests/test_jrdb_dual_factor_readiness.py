"""Synthetic-only overlap checks for training and near-term form grades."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_dual_factor_readiness import summarize_dual_factor_readiness
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from test_jrdb_evidence_readiness import sample


def data():
    p, entries, training, past = sample()
    training[0].update(oikirisisu=76, siagarisisu=77)
    training[1].update(oikirisisu=61, siagarisisu=64)
    past[0].update(
        race_back_1_idm=70,
        race_back_2_racedate="20260920",
        race_back_2_order_of_finish=2,
        race_back_2_idm=62)
    train = build_training_hints(p, entries, training, "20261101")
    recent = build_recent_hints(p, entries, past, "20261101")
    return train, recent


class DualFactorReadinessTests(unittest.TestCase):
    def test_counts_both_and_training_only(self):
        out = summarize_dual_factor_readiness(*data())
        tokyo, kyoto = out["races"]
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["both"], 1)
        self.assertEqual(tokyo["trainingOnly"], 1)
        self.assertEqual(tokyo["recentOnly"], 0)
        self.assertEqual(tokyo["neither"], 0)
        self.assertEqual(kyoto["runnerCount"], 1)
        self.assertEqual(kyoto["neither"], 1)
        self.assertEqual(out["predictionReady"], False)
        self.assertTrue(tokyo["coreFactorsStillUnverified"])
        self.assertEqual(tokyo["remainingFactors"], 8)

    def test_agreement_and_disagreement_counts_without_horse_picks(self):
        training, recent = data()
        # First runner is S (training) versus A (recent).
        tokyo = summarize_dual_factor_readiness(training, recent)["races"][0]
        self.assertEqual(tokyo["both"], 1)
        self.assertEqual(tokyo["trainingHigher"], 1)
        self.assertEqual(tokyo["largeDisagreement"], 0)
        self.assertEqual(tokyo["bothHigh"], 1)
        self.assertEqual(tokyo["sameGrade"], 0)
        # Deliberate conflict: S vs C is a difference of three grades.
        recent[0]["byNumber"]["01"]["grade"] = "C"
        tokyo = summarize_dual_factor_readiness(training, recent)["races"][0]
        self.assertEqual(tokyo["trainingHigher"], 1)
        self.assertEqual(tokyo["largeDisagreement"], 1)
        self.assertEqual(tokyo["bothHigh"], 0)
        self.assertEqual(tokyo["recentHigher"], 0)
        # Opposite conflict: C vs S.
        training[0]["gradesByNumber"]["01"] = "C"
        recent[0]["byNumber"]["01"]["grade"] = "S"
        tokyo = summarize_dual_factor_readiness(training, recent)["races"][0]
        self.assertEqual(tokyo["recentHigher"], 1)
        self.assertEqual(tokyo["largeDisagreement"], 1)
        self.assertEqual(tokyo["trainingHigher"], 0)
        self.assertFalse(tokyo["predictionReady"])
        self.assertEqual(tokyo["remainingFactors"], 8)
        # Both equal C still does not imply race assessment.
        training[0]["gradesByNumber"]["01"] = "C"
        recent[0]["byNumber"]["01"]["grade"] = "C"
        tokyo = summarize_dual_factor_readiness(training, recent)["races"][0]
        self.assertEqual(tokyo["sameGrade"], 1)
        self.assertEqual(tokyo["largeDisagreement"], 0)

    def test_training_missing_recent_only(self):
        train, past = data()
        train[0]["gradesByNumber"]["01"] = "未評価"
        self.assertEqual(
            summarize_dual_factor_readiness(train, past)["races"][0]["recentOnly"], 1)

    def test_rejects_mismatched_runner_list(self):
        train, recent = data()
        del recent[0]["byNumber"]["02"]
        with self.assertRaises(CoverageError):
            summarize_dual_factor_readiness(train, recent)

    def test_rejects_missing_race_or_duplicate(self):
        train, recent = data()
        with self.assertRaises(CoverageError):
            summarize_dual_factor_readiness(train, recent[:1])
        train, recent = data()
        recent[1] = copy.deepcopy(recent[0])
        with self.assertRaises(CoverageError):
            summarize_dual_factor_readiness(train, recent)

    def test_rejects_unrecognized_grade(self):
        train, recent = data()
        recent[0]["byNumber"]["01"]["grade"] = "X"
        with self.assertRaises(CoverageError):
            summarize_dual_factor_readiness(train, recent)

    def test_output_hides_private_identifiers(self):
        result = repr(summarize_dual_factor_readiness(*data()))
        for secret in ("2328aaa95a05", "NONPUBLIC", "racekey", "byNumber",
                       "gradesByNumber", "oikirisisu", "race_back_1"):
            self.assertNotIn(secret, result)

    def test_source_immutability(self):
        original = data()
        frozen = copy.deepcopy(original)
        summarize_dual_factor_readiness(*original)
        self.assertEqual(original, frozen)


if __name__ == "__main__":
    unittest.main()
