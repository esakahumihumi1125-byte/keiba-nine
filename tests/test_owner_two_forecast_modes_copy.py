"""The 24R preday reference and two-factor draft are distinct owner views."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_auto_forecast_ui import HTML, JS


class SeparateOwnerForecastModesTests(unittest.TestCase):
    def test_available_preday_reference_has_primary_safe_navigation(self):
        self.assertIn('id="autoPredayRecovery"', HTML)
        self.assertIn('href="/owner-preday-forecast"', HTML)
        self.assertIn("全レースの前日参考予想", HTML)
        self.assertIn("別画面・追加の有料取得なし", HTML)
        self.assertIn("正式10項目採点・購入推奨ではありません", HTML)

    def test_two_factor_count_never_claims_to_be_the_24r_preday_count(self):
        self.assertIn("JRDB2項目の研究用下書き", JS)
        self.assertIn("JRDB2項目の見送り", JS)
        self.assertIn("前日参考予想の件数ではありません", JS)
        self.assertIn("直下のリンクから見られます", JS)
        self.assertNotIn("24Rすべて正式予想", HTML + JS)

    def test_no_extra_fetch_or_betting_side_effects_in_copy_change(self):
        self.assertIn('href="/owner-preday-forecast"', HTML)
        self.assertIn("前日参考予想の件数ではありません", JS)
        self.assertNotIn("前日参考予想24Rが消えた意味ではありません。\n", HTML)


if __name__ == "__main__":
    unittest.main()
