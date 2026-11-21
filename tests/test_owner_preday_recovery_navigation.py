"""UI regression: JRDB API errors must leave the separate private pre-day path visible.

No paid provider requests, credentials, live tickets, or browser navigation.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML, JS, CSS


class PredayRecoveryNavigationTests(unittest.TestCase):
    def test_owner_can_open_separate_preday_reference_from_auto_screen(self):
        self.assertIn('id="autoPredayRecovery"', HTML)
        self.assertIn('href="/owner-preday-forecast"', HTML)
        self.assertIn("JRDB APIが403で停止するとき", HTML)
        self.assertIn("JRA公式未照合", HTML)
        self.assertIn("owner-preday-recovery", CSS)

    def test_auto_provider_failure_never_reclassifies_reference_as_formal(self):
        self.assertIn("登録済みの前日参考予想を見る（JRDB APIへの追加照会なし）", JS)
        self.assertIn("正式100点予想は未完成", JS)
        self.assertNotIn("window.location='/owner-preday-forecast'", JS)


if __name__ == "__main__":
    unittest.main()
