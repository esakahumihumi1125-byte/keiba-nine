"""Owner ARC RACE blue theme: presentation-only, with preserved user data."""
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from private_service import CSS as OWNER_CSS, LOGIN_CSS, HTML as OWNER_HTML, LOGIN_HTML
from owner_auto_forecast_ui import CSS as FORECAST_CSS, HTML as FORECAST_HTML
from arc_race_track_motion import SCENE_HTML, SCENE_CSS

class OwnerBluePaletteTests(unittest.TestCase):
    def test_blue_backgrounds_and_components(self):
        self.assertIn('linear-gradient(165deg,#103a61,#0b2745',OWNER_CSS)
        self.assertIn('.owner-quick-start{background:linear-gradient(145deg,#19476a,#11314e',OWNER_CSS)
        self.assertIn('.preview-mode{background:#143855',OWNER_CSS)
        self.assertIn('.owner-release-panel{padding:14px;background:#143b5c',OWNER_CSS)
        self.assertIn('linear-gradient(160deg,#103a61,#0b2745',FORECAST_CSS)
        self.assertIn('section{background:#173b5b',FORECAST_CSS)
        self.assertIn('linear-gradient(165deg,#10355a,#07182c',LOGIN_CSS)
        self.assertIn('theme=arc-blue-20261112',OWNER_HTML)
        self.assertIn('theme=arc-blue-20261112',FORECAST_HTML)
        self.assertIn('theme=arc-blue-20261112',LOGIN_HTML)

    def test_track_is_blue_without_green_gradient(self):
        self.assertIn('arc-scene-blue-track',SCENE_HTML)
        self.assertIn('stop-color="#2b638e"',SCENE_HTML)
        self.assertIn('stop-color="#102b47"',SCENE_HTML)
        self.assertNotIn('stop-color="#314b3b"',SCENE_HTML)
        self.assertNotIn('arc-scene-grass',SCENE_HTML)
        self.assertEqual(SCENE_HTML.count('<animateMotion '),18)
        self.assertIn('.arc-horse-motion{display:none}',SCENE_CSS)

    def test_unmodified_forecast_and_owner_access(self):
        for token in ('name="username"','name="password"','name="login_csrf"'):
            self.assertIn(token,LOGIN_HTML)
        for token in ('href="__OWNER_FORECAST_ROUTE__"', 'href="/my-tickets"',
                      '__OWNER_RELEASE__','__OWNER_FORECAST_TITLE__'):
            self.assertIn(token,OWNER_HTML)
        self.assertIn('id="autoRun"',FORECAST_HTML)
        self.assertIn('.grade-s{background:#D4AF37',OWNER_CSS)
        self.assertIn('.grade-a{background:#c6374c',OWNER_CSS)
        self.assertIn('.S{color:#f3d475}',FORECAST_CSS)
        self.assertIn('.A{color:#ffa6b1}',FORECAST_CSS)

if __name__=='__main__':
    unittest.main()
