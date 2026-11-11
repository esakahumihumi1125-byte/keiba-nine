"""The Results tab opens the actual score/result screen, not old records.

Safe navigation only: do not merge legacy, WIN5 and private Render storage.
"""
import re
import unittest
from pathlib import Path

HTML = (Path(__file__).resolve().parents[1] /
        "keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")


class ResultsTabNavigationTest(unittest.TestCase):
    def test_bottom_tab_shows_results_while_highlighting_current_destination(self):
        menu = re.search(r'<nav class="tabs" aria-label="メインメニュー">(.*?)</nav>',
                         HTML, re.S)
        self.assertIsNotNone(menu)
        self.assertEqual(menu.group(1).count('>結果</button>'),1)
        self.assertIn('data-screen="live" onclick="show(\'results\')"',menu.group(1))
        self.assertIn("name==='results'?'live'", HTML)
        self.assertIn('<section id="results" class="screen"><div class="heading">結果</div>',
                      HTML)
        self.assertIn('id="realResultBlock"',HTML)
        self.assertIn('id="realReview"',HTML)
        self.assertIn('id="raKpi24"',HTML)
        self.assertIn('id="raByKind24"',HTML)

    def test_saved_records_remain_accessible_without_migration(self):
        self.assertIn('onclick="show(\'results\')">結果を見る</button>',HTML)
        self.assertEqual(HTML.count('id="resultsSavedRecordsOpen"'),1)
        self.assertIn('id="resultsSavedRecordsOpen" onclick="show(\'live\')"',
                      HTML)
        self.assertIn('<section id="live" class="screen">',HTML)
        self.assertIn('id="finance54"',HTML)
        self.assertIn("keiba_nine_win5_v57",HTML)
        self.assertIn("keiba_nine_race_flow_demo_v1_8",HTML)
        self.assertIn("この画面は手動の記録用",HTML)
        self.assertIn("JRA公式結果の自動取得は未接続",HTML)


if __name__ == "__main__":
    unittest.main()
