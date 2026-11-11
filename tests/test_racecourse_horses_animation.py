"""Decorative racing horses in the home-banner, not bets or external media.

Validation is static and offline: no live JRDB, no generated forecasts,
no changes to existing race cards, local storage, or browser sessions.
"""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")


class MiniTurfHorsesTests(unittest.TestCase):
    def setUp(self):
        self.scene=HTML.split("<!-- RACECOURSE58_MINI_HORSES_START:",1)[1].split(
            "<!-- RACECOURSE58_MINI_HORSES_END -->",1)[0]

    def test_three_small_horses_2_3_8_behind_foreground_fence(self):
        self.assertEqual(re.findall(r'data-horse="(\d+)" transform=',self.scene),
                         ["2","3","8"])
        self.assertIn('<text x="70" y="50">2</text>',self.scene)
        self.assertIn('<text x="70" y="50">3</text>',self.scene)
        self.assertIn('<text x="70" y="50">8</text>',self.scene)
        self.assertLess(self.scene.index('class="kn-horse-pack"'),
                        self.scene.index('class="kn-far-side-fence"'))
        self.assertIn('pointer-events:none',self.scene)
        self.assertIn('aria-hidden="true" focusable="false"',self.scene)
        self.assertEqual(self.scene.count('class="kn-racecourse-horses"'),1)
        self.assertIn('preserveAspectRatio="xMidYMid slice"',self.scene)

    def test_iphone_animation_is_bounded_reduced_motion_still_shows_scene(self):
        self.assertIn('animation:kn-turf-pass 24s linear infinite',self.scene)
        self.assertIn('@keyframes kn-turf-gallop',self.scene)
        self.assertIn('animation-delay:-9s',self.scene)
        self.assertIn('@media(prefers-reduced-motion:reduce)',self.scene)
        self.assertIn('.kn-horse-pack,.kn-horse-bob{animation:none!important}',self.scene)
        self.assertIn('.kn-horse-pack{transform:translateX(300px)}',self.scene)
        self.assertIn('height:125px',self.scene)
        self.assertIn('overflow:hidden',self.scene)

    def test_no_extra_provider_requests_and_no_record_mutations(self):
        self.assertNotIn('fetch(',self.scene)
        self.assertNotIn('localStorage',self.scene)
        self.assertNotIn('sessionStorage',self.scene)
        self.assertNotIn('setInterval(',self.scene)
        self.assertNotIn('onClick',self.scene)
        self.assertIn("home.prepend(banner);",self.scene)
        self.assertIn("url('./assets/racecourse58.svg')",self.scene)
        self.assertEqual(HTML.count("const banner=document.createElement('div');"),1)
        self.assertIn('id="knOwnerForecastLaunch"',HTML)
        self.assertIn('data-screen="win5"',HTML)
        self.assertIn('data-screen="live" onclick="show(\'results\')"',HTML)


if __name__=="__main__":
    unittest.main()
