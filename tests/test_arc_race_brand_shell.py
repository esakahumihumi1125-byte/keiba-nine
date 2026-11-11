"""ARC RACE B-design regression: view-only migration, old data flows preserved."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from arc_race_track_motion import SCENE_HTML, SCENE_CSS, ANIMATED_HORSE_COUNT
from owner_auto_forecast_ui import HTML as FORECAST, CSS as FORECAST_CSS, JS as FORECAST_JS
from private_service import HTML as HOME, CSS as HOME_CSS, LOGIN_HTML, LOGIN_CSS


class ArcRaceBrandShellTests(unittest.TestCase):
    def test_three_owner_entrypoints_show_arc_race_horse_and_dual_arc(self):
        for label, page, css in (
            ("forecast", FORECAST, FORECAST_CSS),
            ("home", HOME, HOME_CSS),
            ("login", LOGIN_HTML, LOGIN_CSS),
        ):
            with self.subTest(label=label):
                self.assertIn("ARC RACE", page)
                self.assertIn("Powered by", page)
                self.assertIn("UMETRIC", page)
                self.assertIn("アークレース", page)
                self.assertEqual(page.count('class="arc-brand"'), 1)
                self.assertIn('aria-label="円弧と競走馬の横顔"', page)
                self.assertIn('stroke="#3d97ce"', page)
                self.assertIn('stroke="url(#arc-brand-gold)"', page)
                self.assertIn(".arc-brand-mark{", css)
                self.assertIn(".arc-brand-copy h1{", css)
                self.assertIn("@media(max-width:360px)", css)
                self.assertIn('content="ARC RACE"', page) if label != "forecast" else None

    def test_owner_home_uses_static_blue_gold_arc_without_animation(self):
        self.assertEqual(ANIMATED_HORSE_COUNT, 0)
        self.assertIn('arc-race-scene-static', SCENE_HTML)
        self.assertIn('勝負を描く、予想のアーク。', SCENE_HTML)
        self.assertIn('arc-race-scene', HOME)
        self.assertEqual(HOME.count('class="arc-race-scene arc-race-scene-static"'), 1)
        self.assertLess(HOME.index('arc-race-scene'), HOME.index('owner-quick-start'))
        self.assertIn('border:2px solid #dfb56d9e', SCENE_CSS)
        self.assertIn('border:2px solid #69b8e6a6', SCENE_CSS)
        self.assertIn('linear-gradient(115deg,#0a2238,#15476c', SCENE_CSS)
        for forbidden in ('<svg', '<animate', 'arc-horse-moving', '18頭',
                          'fetch(', 'localStorage', 'sessionStorage', 'JRDB_API_KEY',
                          '/api/jrdb/', 'trifectaTickets'):
            self.assertNotIn(forbidden, SCENE_HTML + SCENE_CSS)
        for forbidden in ('animation:', '@keyframes', 'setInterval(', '<script'):
            self.assertNotIn(forbidden, SCENE_HTML + SCENE_CSS)

    def test_legacy_links_credentials_and_forecast_controls_are_not_renamed(self):
        # Brand is cosmetic. No renaming of private URLs or storage keys.
        # Home route is intentionally an owner-only placeholder resolved by
        # the existing WSGI handler after authentication.
        self.assertIn('href="__OWNER_FORECAST_ROUTE__"', HOME)
        self.assertIn('href="/my-tickets"', HOME)
        self.assertIn('href="/owner-backup"', HOME)
        self.assertIn("__OWNER_RELEASE__", HOME)
        self.assertIn("__OWNER_FORECAST_ROUTE__", HOME)
        self.assertIn('__CSRF__', LOGIN_HTML)
        self.assertIn('name="username"', LOGIN_HTML)
        self.assertIn('name="password"', LOGIN_HTML)
        self.assertIn('name="login_csrf"', LOGIN_HTML)
        self.assertIn('id="autoRun"', FORECAST)
        self.assertIn('id="autoDay"', FORECAST)
        self.assertIn('id="autoRaces"', FORECAST)
        self.assertIn('id="autoReceiptVerify"', FORECAST)
        self.assertIn("keiba-nine-", FORECAST_JS)
        self.assertIn("/api/jrdb/owner-auto-draft", FORECAST_JS)
        self.assertIn("正式10項目の予想とJRA公式照合は未完成", FORECAST)


if __name__ == "__main__":
    unittest.main()
