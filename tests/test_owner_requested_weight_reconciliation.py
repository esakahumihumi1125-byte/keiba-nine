"""Synthetic arithmetic and backward-compatibility for requested weights."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation_policy import OWNER_FORMAL_FACTORS, OWNER_FORMAL_POLICY_VERSION
from owner_requested_weight_reconciliation import (
    REQUESTED_WEIGHTS, RAW_TOTAL, VERSION, requested_policy_review,
    synthetic_score_preview,
)

ROOT = Path(__file__).resolve().parents[1]
UI = (ROOT / "scripts" / "owner_auto_forecast_ui.py").read_text(encoding="utf-8")


class OwnerRequestedWeightTests(unittest.TestCase):
    def test_exact_owner_requested_weights_and_105_total(self):
        self.assertEqual(REQUESTED_WEIGHTS, {
            "training":30, "recent":3, "course_distance":17, "pace":17,
            "ground":15, "pedigree":6, "draw_weight":5, "jockey_stable":10,
            "rotation":1, "body_condition":1,
        })
        self.assertEqual(RAW_TOTAL, 105)
        report = requested_policy_review()
        self.assertEqual(report["version"], VERSION)
        self.assertEqual(report["rawRequestedWeightTotal"], 105)
        self.assertEqual(report["normalizedScoreMax"], 100)
        self.assertEqual(report["status"], "candidate_not_active")
        self.assertFalse(report["officialPredictionReady"])
        self.assertFalse(report["bettingReady"])
        self.assertFalse(report["publishable"])
        self.assertEqual(report["existingResearchPolicyVersion"], OWNER_FORMAL_POLICY_VERSION)
        self.assertEqual(report["existingResearchWeights"], OWNER_FORMAL_FACTORS)
        self.assertEqual(OWNER_FORMAL_FACTORS["ground"], 12)
        self.assertEqual(OWNER_FORMAL_FACTORS["draw_weight"], 3)
        shares = report["normalizedShares"]
        self.assertEqual(sum(row["numerator"] for row in shares.values()),
                         100 * 105)
        self.assertEqual({row["denominator"] for row in shares.values()}, {105})

    def test_all_s_all_c_and_exact_partial_arithmetic(self):
        grades = {key:"S" for key in REQUESTED_WEIGHTS}
        record = {"recordType":"synthetic_test", "grades":grades}
        unchanged = copy.deepcopy(record)
        result = synthetic_score_preview(record)
        self.assertEqual(record, unchanged)
        self.assertEqual(result["score100"], 100)
        self.assertEqual(result["rawThirdPoints"], 315)
        self.assertIsNone(result["trifecta"])
        self.assertFalse(result["officialPredictionReady"])
        grades = {key:"C" for key in REQUESTED_WEIGHTS}
        self.assertEqual(synthetic_score_preview(
            {"recordType":"synthetic_test","grades":grades})["score100"],0)
        grades = {key:"S" for key in REQUESTED_WEIGHTS}
        grades.update(training="A", recent="C")
        score = synthetic_score_preview(
            {"recordType":"synthetic_test","grades":grades})
        self.assertEqual(score["rawThirdPoints"], 276)
        self.assertEqual(score["score100"], 87.62)

    def test_unassessed_or_omitted_factor_blocks_score(self):
        grades = {key:"S" for key in REQUESTED_WEIGHTS}
        grades["ground"] = "未評価"
        partial = synthetic_score_preview(
            {"recordType":"synthetic_test","grades":grades})
        self.assertEqual(partial["status"], "missing_synthetic_factors")
        self.assertEqual(partial["missingFactors"], ["ground"])
        self.assertIsNone(partial["score100"])
        self.assertIsNone(partial["rawThirdPoints"])
        del grades["ground"]
        self.assertIsNone(synthetic_score_preview(
            {"recordType":"synthetic_test","grades":grades})["score100"])

    def test_real_or_incomplete_inputs_are_not_admitted(self):
        for bad in (
            None, {}, {"recordType":"live","grades":{}},
            {"recordType":"synthetic_test","grades":[]},
            {"recordType":"synthetic_test","grades":{"training":"S","odds":"S"}},
            {"recordType":"synthetic_test","grades":{"training":2}},
            {"recordType":"synthetic_test","grades":{},"horses":[]},
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                synthetic_score_preview(bad)

    def test_owner_screen_explains_review_is_not_active(self):
        self.assertIn('id="autoRequestedWeightReview"',UI)
        self.assertIn('指定の10項目は合計105点',UI)
        self.assertIn('100÷105',UI)
        self.assertIn('現行research-6の100点配点',UI)
        self.assertIn('正式採点には未反映',UI)
        self.assertIn('正式10項目の予想とJRA公式照合は未完成',UI)


if __name__=="__main__":
    unittest.main()
