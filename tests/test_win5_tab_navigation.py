"""WIN5 is a real fifth navigation destination, separate from 3連単.

The existing manual 5-leg planner and strict deadline guard must be reused;
this test must never claim JRA-confirmed targets or paid provider data.
"""
import re
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
from owner_auto_forecast_ui import HTML as OWNER_HTML


class Win5NavigationTest(unittest.TestCase):
    def test_five_destinations_and_distinct_screen(self):
        nav = re.search(r'<nav class="tabs" aria-label="メインメニュー">(.*?)</nav>',
                        HTML, re.S)
        self.assertIsNotNone(nav)
        screens = re.findall(r'data-screen="([^"]+)"', nav.group(1))
        self.assertEqual(screens, ["home", "ticket", "win5", "live", "tools"])
        self.assertEqual(HTML.count('id="win5"'), 1)
        self.assertIn('<section id="win5" class="screen"', HTML)
        self.assertIn('get(\'win5\').append(panel);', HTML)
        self.assertNotIn('get(\'home\').append(panel);', HTML)
        self.assertIn("jump.onclick=()=>show('win5')", HTML)
        self.assertIn("if(location.hash==='#win5')show('win5');", HTML)
        self.assertIn(".tabs button{width:20%;max-width:none", HTML)

    def test_owner_private_app_can_open_win5_without_exposing_credentials(self):
        url = "https://esakahumihumi1125-byte.github.io/keiba-nine/keiba-nine-beta51-feed-record.html#win5"
        self.assertEqual(OWNER_HTML.count('href="' + url + '"'), 1)
        self.assertIn("WIN5（別画面）", OWNER_HTML)
        self.assertIn('rel="noopener noreferrer"', OWNER_HTML)
        self.assertNotIn("KEIBA_OWNER_PASSWORD=", OWNER_HTML)
        self.assertNotIn("token=", url)
        self.assertIn("keiba_nine_win5_v57", HTML)
        self.assertNotIn("fetch(", HTML[HTML.index("/* WIN57_LOGIC_START */"):
                                         HTML.index("</script>", HTML.index("/* WIN57_LOGIC_START */"))])

    def test_existing_win5_not_a_fake_automatic_prediction(self):
        self.assertEqual(HTML.count("function validateWin57(input,now,existing=[])"),1)
        self.assertIn("now>=deadline", HTML)
        self.assertIn("input.legs.length!==5", HTML)
        self.assertIn("合計'+points+'点です。上限48点以内", HTML)
        self.assertIn("source:'manual'", HTML)
        self.assertIn("この画面は手動の記録用", HTML)
        self.assertIn("自動予想・JRA公式照合・購入は未接続", HTML)
        self.assertIn("基本は8点・必要時だけ16点程度", HTML)
        self.assertIn("keiba_nine_win5_v57", HTML)
        self.assertIn("keiba_nine_race_flow_demo_v1_8", HTML)
        self.assertIn("この端末に保存します。購入は行いません。", HTML)


if __name__ == "__main__":
    unittest.main()
