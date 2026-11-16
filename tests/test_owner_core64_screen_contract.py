"""Keep the visible iPhone explanation aligned with the research gate."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML
from owner_comparable_factor_preview import (
    MIN_COMPARABLE_WEIGHT, CORE_TRIO, LEGACY_MIN_WITHOUT_CORE_TRIO,
)
from evaluation_policy import OWNER_FORMAL_FACTORS


class Core64ScreenContract(unittest.TestCase):
    def test_iPhone_readable_core_rule_matches_actual_research_gate(self):
        self.assertEqual(MIN_COMPARABLE_WEIGHT, 64)
        self.assertEqual(LEGACY_MIN_WITHOUT_CORE_TRIO, 70)
        self.assertEqual(sum(OWNER_FORMAL_FACTORS[k] for k in CORE_TRIO), 64)
        self.assertIn("調教30点・コース距離17点・展開脚質17点", HTML)
        self.assertIn("主要64点分", HTML)
        self.assertIn("共通の評価項目70点分以上", HTML)
        self.assertIn("正式100点予想・JRA公式照合・購入・固定記録・収支には反映しません", HTML)
        self.assertNotIn("同じ評価項目が70点分以上そろう場合だけ", HTML)


if __name__ == "__main__":
    unittest.main()
