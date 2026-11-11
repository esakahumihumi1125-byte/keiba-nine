"""ARC RACE premium background is visual-only across public app screens."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")
class PublicNightThemeTests(unittest.TestCase):
    def setUp(self):
        self.theme=HTML.split('<style id="arc-race-premium-theme">',1)[1].split('</style>',1)[0]
    def test_dark_palette_surfaces_and_legible_text(self):
        for token in (':root{', 'color-scheme:dark', 'html{background:#071521}',
                      'body{', '.screen{background:#0e2335f5',
                      '.panel,.kpi,.hero', 'input,select,textarea{background:#0a1e2f',
                      '.tabs{background:#071828f7', '#knOwnerForecastHub{',
                      '#backupTools68{', '#knPurchaseLink,#knPersonalRecord',
                      '#win57 .w57-leg', '#financeNet54', 'button:focus-visible'):
            self.assertIn(token,self.theme)
        self.assertNotIn('racecourse58.svg',self.theme)
        self.assertNotIn('#edf4ed',self.theme)
    def test_grades_remain_distinct():
        self.assertIn('.s52-rank-S{--rank-ink:#e8bc5f',self.theme)
        self.assertIn('.s52-rank-A{--rank-ink:#f47881',self.theme)
        self.assertIn('.s52-rank-B{--rank-ink:#83c5d0',self.theme)
    def test_no_data_behavior_changed(self):
        for illegal in ('localStorage', 'sessionStorage', 'fetch(', 'JRDB_API_KEY',
                        'setInterval(', 'window.location', 'document.cookie'):
            self.assertNotIn(illegal,self.theme)
        for saved in ("keiba_nine_race_flow_demo_v1_8", "keiba-nine-auto-feed.json",
                      'const numHorses=18;', 'id="knOwnerForecastLaunch"',
                      'data-screen="win5"', "show('results')"):
            self.assertIn(saved,HTML)
        self.assertIn("勝負を描く、予想のアーク。",HTML)
if __name__=='__main__':
    unittest.main()
