"""Single-entry iPhone navigation between public KEIBA NINE and private Render.
This is view integration, not CORS, data merging or owner-credential transfer.
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
from owner_auto_forecast_ui import HTML as OWNER_HTML, CSS as OWNER_CSS

OWNER_URL = "https://keiba-nine-owner-jrdb.onrender.com/owner-auto-forecast"
PAGES_URL = ("https://esakahumihumi1125-byte.github.io/keiba-nine/"
             "keiba-nine-beta51-feed-record.html")


class OwnerForecastHubIntegrationTests(unittest.TestCase):
    def test_main_forecast_first_and_no_cross_origin_secrets(self):
        self.assertEqual(MAIN.count('id="knOwnerForecastLaunch"'), 1)
        self.assertEqual(MAIN.count('id="knOwnerForecastHub"'), 1)
        self.assertIn('href="' + OWNER_URL + '" rel="noopener noreferrer"', MAIN)
        self.assertLess(MAIN.index('id="knOwnerForecastHub"'),
                        MAIN.index('id="simple52"'))
        self.assertIn("正式10項目100点予想とJRA公式照合は未完成", MAIN)
        self.assertIn("通常の土日に当日分を自動照会", MAIN)
        self.assertIn("平日・祝日の変則開催は日付を選んで手動取得", MAIN)
        self.assertIn("契約による利用制限・料金", MAIN)
        self.assertIn("onclick=\"show('win5')\"", MAIN)
        self.assertNotIn("KEIBA_OWNER_PASSWORD=", MAIN)
        self.assertNotIn("JRDB_API_KEY=", MAIN)
        self.assertNotIn("token=", OWNER_URL)
        self.assertNotIn("?", OWNER_URL)

    def test_private_forecast_returns_to_main_without_sharing_records(self):
        self.assertEqual(OWNER_HTML.count('href="' + PAGES_URL + '"'), 1)
        self.assertEqual(OWNER_HTML.count('href="' + PAGES_URL + '#win5"'), 1)
        self.assertIn("← KEIBA NINE本体へ", OWNER_HTML)
        self.assertIn("rel=\"noopener noreferrer\"", OWNER_HTML)
        self.assertIn(".owner-nav{flex-wrap:wrap", OWNER_CSS)
        self.assertIn("id=\"autoSaturdayQuick\"", OWNER_HTML)
        self.assertIn("id=\"fixedHistorySection\"", OWNER_HTML)
        self.assertNotIn("iframe", MAIN[MAIN.index('id="knOwnerForecastHub"'):
                                       MAIN.index('id="simple52"')])
        self.assertNotIn("localStorage", MAIN[MAIN.index('id="knOwnerForecastHub"'):
                                             MAIN.index('id="simple52"')])

    def test_win5_and_old_prediction_storage_kept_separate(self):
        self.assertIn('data-screen="win5" onclick="show(\'win5\')"', MAIN)
        self.assertIn("get('win5').append(panel);", MAIN)
        self.assertIn("keiba_nine_win5_v57", MAIN)
        self.assertIn("keiba_nine_race_flow_demo_v1_8", MAIN)
        self.assertIn("function validateWin57(input,now,existing=[])", MAIN)
        self.assertIn("now>=deadline", MAIN)
        self.assertIn("3連単", OWNER_HTML)

if __name__ == "__main__":
    unittest.main()
