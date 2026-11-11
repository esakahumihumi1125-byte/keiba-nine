"""Owner forecast must not show old races as if they were current."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_preday_forecast_ui import HTML, JS
from private_service import HTML as HOME


class OwnerForecastFreshnessTests(unittest.TestCase):
    def test_stale_races_hidden_before_any_cards_are_rendered(self):
        self.assertIn("function todayJst()", JS)
        self.assertIn("timeZone:'Asia/Tokyo'", JS)
        self.assertIn("if(current.date<todayJst())", JS)
        self.assertIn("古い暫定予想は非表示", JS)
        self.assertLess(JS.index("if(current.date<todayJst())"),
                        JS.index("for(const r of rows)"))
        self.assertIn("host.replaceChildren();", JS)
        self.assertIn("if(current&&current.date>safe.date)", JS)

    def test_refreshes_after_ios_webapp_resumes(self):
        self.assertIn("document.addEventListener('visibilitychange',refreshOnReturn)", JS)
        self.assertIn("window.addEventListener('pageshow'", JS)
        self.assertIn("nextAutoCheck=Date.now()+60000", JS)
        self.assertIn("credentials:'same-origin',cache:'no-store'", JS)

    def test_home_opens_private_forecast_first_without_hardcoded_day(self):
        self.assertLess(HOME.index('href="/owner-preday-forecast"'),
                        HOME.index('href="/my-scorecard"'))
        self.assertIn("登録済みなら自動表示", HOME)
        self.assertIn("正式10項目とJRA公式照合は未完成", HOME)
        self.assertNotIn("④ 11月7日・前日予想36R", HOME)
        self.assertIn("過去の開催日の予想は自動的に非表示", HTML)


if __name__ == "__main__":
    unittest.main()
