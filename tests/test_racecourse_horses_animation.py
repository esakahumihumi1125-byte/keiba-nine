"""ARC RACE public homepage has a quiet, motion-free premium banner.

The historical file name is retained so existing test discovery and CI paths
remain stable. The private owner's 18-horse scene is intentionally unaffected.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")

class StaticArcRaceBannerTests(unittest.TestCase):
    def setUp(self):
        self.hero = HTML.split('<div class="arc-race-static-hero"', 1)[1].split('</div>', 1)[0]
        self.css = HTML.split('<style id="arc-race-static-hero-style">', 1)[1].split('</style>', 1)[0]

    def test_static_gold_blue_brand_and_forecast_copy(self):
        self.assertEqual(HTML.count('id="arc-race-static-hero"'), 1)
        self.assertIn('ARC RACE · NIGHT TRACK', self.hero)
        self.assertIn('勝負を描く、予想のアーク。', self.hero)
        self.assertIn('AI競馬予想・データ分析', self.hero)
        self.assertIn('<b>3連単</b><b>WIN5</b><b>実戦記録</b>', self.hero)
        self.assertIn('border:2px solid #d8ab59a3', self.css)
        self.assertIn('border:2px solid #4898c5a1', self.css)
        self.assertIn('linear-gradient(116deg,#081827', self.css)
        self.assertIn('min-height:142px', self.css)

    def test_no_motion_or_provider_access(self):
        for forbidden in ('<script', '<animateMotion', '@keyframes', 'animation:',
                          'fetch(', 'localStorage', 'sessionStorage', 'setInterval(',
                          'requestAnimationFrame', 'JRDB_API_KEY'):
            self.assertNotIn(forbidden, self.hero + self.css)
        self.assertNotIn('RACECOURSE58_MINI_HORSES_START', HTML)
        self.assertNotIn('kn-thoroughbred-gallop', HTML)
        self.assertNotIn('const numHorses=18;', HTML)
        self.assertNotIn('racecourse58.svg', self.css)

    def test_app_navigation_and_stored_data_contract(self):
        self.assertIn("keiba_nine_race_flow_demo_v1_8", HTML)
        self.assertIn('id="knOwnerForecastLaunch"', HTML)
        self.assertIn('data-screen="win5"', HTML)
        self.assertIn('data-screen="live" onclick="show(\'results\')"', HTML)
        self.assertIn('<title>ARC RACE｜アークレース</title>', HTML)

if __name__ == '__main__':
    unittest.main()
