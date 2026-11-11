"""Visual-only public ARC RACE branding migration."""
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")

class PublicArcRaceBrandTests(unittest.TestCase):
    def test_brand_and_owner_logo(self):
        self.assertIn("<title>ARC RACE｜アークレース</title>", MAIN)
        self.assertIn('apple-mobile-web-app-title" content="ARC RACE"', MAIN)
        self.assertIn('<header class="brand arc-public-brand"', MAIN)
        self.assertIn('aria-label="円弧と競走馬の横顔"', MAIN)
        self.assertIn('stroke="#3d97ce"', MAIN)
        self.assertIn('stroke="url(#arc-brand-gold)"', MAIN)
        self.assertIn("Powered by <strong>UMETRIC</strong>", MAIN)
        self.assertIn('id="arc-race-public-brand"', MAIN)
        self.assertIn('勝負を描く、予想のアーク。', MAIN)
        self.assertIn('ARC RACE · NIGHT TRACK', MAIN)
        self.assertNotIn('青空のターフへ', MAIN)
        self.assertIn('>ARC RACEを開く</a>', INDEX)

    def test_existing_navigation_and_storage_stay_intact(self):
        self.assertIn('href="./keiba-nine-beta51-feed-record.html"', INDEX)
        self.assertIn("location.replace(document.getElementById('openApp').href)", INDEX)
        for token in ('keiba_nine_race_flow_demo_v1_8',
                      'keiba_nine_mykeiba_url_v30', 'keiba-nine-auto-feed.json',
                      'data-screen="win5"', "show('results')",
                      'id="knOwnerForecastLaunch"',
                      'RACECOURSE58_MINI_HORSES_START',
                      'const numHorses=18;'):
            self.assertIn(token, MAIN)
        self.assertIn('https://keiba-nine-owner-jrdb.onrender.com/owner-auto-forecast', MAIN)

    def test_new_icons(self):
        png = (ROOT / "assets" / "arc-race-icon-v1.png").read_bytes()
        self.assertEqual(png[:8], bytes((137,80,78,71,13,10,26,10)))
        self.assertEqual(struct.unpack(">II", png[16:24]), (180, 180))
        svg = (ROOT / "assets" / "arc-race-icon-v1.svg").read_text(encoding="utf-8")
        self.assertIn("ARC RACE", svg)
        self.assertIn('stroke="#3d97ce"', svg)
        for html in (MAIN, INDEX):
            self.assertIn('href="./assets/arc-race-icon-v1.png"', html)
            self.assertIn('href="./assets/arc-race-icon-v1.svg"', html)

if __name__ == "__main__":
    unittest.main()
