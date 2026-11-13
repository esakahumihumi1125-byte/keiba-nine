"""Guard the public/private owner 100-point contract against false 105-point comparisons."""
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from evaluation_policy import (OWNER_FORMAL_FACTORS, OWNER_FORMAL_POLICY_VERSION,
                               TOTAL_WEIGHT)
from owner_ten_factor_contract import definition
from owner_auto_forecast_ui import HTML as OWNER_HTML, JS as OWNER_JS
from owner_factor_scorecard import HTML as LEGACY_HTML, JS as LEGACY_JS

class Owner100PointContractTests(unittest.TestCase):
    def test_ten_factors_total_exactly_100_without_normalization(self):
        self.assertEqual(OWNER_FORMAL_POLICY_VERSION,"research-6")
        self.assertEqual(len(OWNER_FORMAL_FACTORS),10)
        self.assertEqual(sum(OWNER_FORMAL_FACTORS.values()),100)
        self.assertEqual(TOTAL_WEIGHT,100)
        self.assertEqual({f["key"]:f["weight"] for f in definition()},
                         OWNER_FORMAL_FACTORS)

    def test_owner_ui_displays_100_point_policy_and_correct_breakdown(self):
        self.assertIn('id="autoPolicy100Notice"',OWNER_HTML)
        self.assertIn('10項目・合計100点',OWNER_HTML)
        self.assertIn('正式100点の計算方法・安全確認',OWNER_HTML)
        self.assertIn("p.totalWeight!==100",OWNER_JS)
        self.assertIn("['ground','馬場',12]",OWNER_JS)
        self.assertIn("['draw_weight','枠・斤量',3]",OWNER_JS)
        self.assertNotIn('autoRequestedWeightReview',OWNER_HTML)
        self.assertNotIn('105点',OWNER_HTML)
        self.assertNotIn('100÷105',OWNER_HTML)
        self.assertIn('発走前に固定した買い目',OWNER_HTML)

    def test_legacy_manual_five_factor_is_not_mislabelled_formal_hundred(self):
        self.assertIn("<h1>旧5項目の手動評価</h1>",LEGACY_HTML)
        self.assertIn("正式仕様の<b>10項目・合計100点</b>とは配点が異なり",LEGACY_HTML)
        self.assertIn('href="/owner-auto-forecast"',LEGACY_HTML)
        self.assertIn("正式10項目採点は未完成",LEGACY_HTML)
        self.assertIn("調教30・近走3・コース距離17・展開17・馬場12",LEGACY_HTML)
        # Old manual calculations and local notes deliberately remain untouched.
        self.assertIn("重み：調教25%／近走25%",LEGACY_HTML)
        self.assertIn("const WEIGHTS=Object.freeze([25,25,20,10,20]);",LEGACY_JS)
        self.assertIn("保存済みの手入力メモや買い目を遡って書き換えません",LEGACY_HTML)

    def test_experimental_105_point_comparison_removed(self):
        for path in (
            "scripts/owner_requested_weight_reconciliation.py",
            "scripts/owner_requested_weight_compare.py",
            "tests/test_owner_requested_weight_reconciliation.py",
            "tests/test_owner_requested_weight_compare.py",
        ):
            self.assertFalse((ROOT/path).exists(),path)

if __name__=="__main__":
    unittest.main()
