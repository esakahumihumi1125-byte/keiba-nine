"""18 miniature thoroughbreds follow the turf rail, purely decorative.

No provider data, purchases, betting tickets, timers or cross-origin writes.
Visual motion is suppressed by OS settings, inactive tab and hidden page.
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

    def test_eighteen_numbered_reusable_horses_beyond_foreground_fence(self):
        self.assertIn("const numHorses=18;",self.scene)
        self.assertIn("for(let i=0;i<numHorses;i++)",self.scene)
        self.assertIn("horse.setAttribute('data-horse',String(i+1))",self.scene)
        self.assertIn("number.textContent=String(i+1)",self.scene)
        self.assertIn("vector.setAttribute('href','#kn-thoroughbred')",self.scene)
        self.assertIn("class=\\\"kn-far-side-fence\\\"",self.scene)
        self.assertIn("id=\\\"kn-racecourse-horse-field\\\"",self.scene)
        self.assertLess(self.scene.index("id=\\\"kn-racecourse-horse-field\\\""),
                        self.scene.index("class=\\\"kn-far-side-fence\\\""))
        self.assertIn("pointer-events:none",self.scene)
        self.assertIn("aria-hidden=\\\"true\\\"",self.scene)
        self.assertIn("preserveAspectRatio=\\\"xMidYMid slice\\\"",self.scene)
        self.assertIn("stroke=\\\"var(--coat",self.scene)
        self.assertIn("class=\\\"kn-tail\\\"",self.scene)

    def test_curved_motion_and_horse_gallop_instead_of_straight_translation(self):
        self.assertRegex(self.scene,r'id=\\\"kn-racecourse-arc\\\" d=\\\"M .*? C .*? C .*?\\\"')
        self.assertIn("const ROUTE=arc.getAttribute('d');",self.scene)
        self.assertIn("const motion=newNode('animateMotion');",self.scene)
        self.assertIn("motion.setAttribute('path',ROUTE)",self.scene)
        self.assertIn("motion.setAttribute('rotate','auto')",self.scene)
        self.assertIn("motion.setAttribute('dur','28s')",self.scene)
        self.assertIn("motion.setAttribute('repeatCount','indefinite')",self.scene)
        self.assertIn("motion.setAttribute('begin','-'+(1+i*1.25).toFixed(2)+'s')",self.scene)
        self.assertIn("kn-thoroughbred-gallop .43s",self.scene)
        self.assertNotIn("kn-turf-pass",self.scene)
        self.assertNotIn("@keyframes kn-turf-pass",self.scene)
        self.assertIn("getPointAtLength(positions*(i+.5)/numHorses)",self.scene)

    def test_low_power_hidden_and_reduced_motion_can_freeze_scene(self):
        self.assertIn("window.matchMedia('(prefers-reduced-motion: reduce)')",self.scene)
        self.assertIn("@media(prefers-reduced-motion:reduce)",self.scene)
        self.assertIn("if(anim)anim.remove()",self.scene)
        self.assertIn("document.hidden||!home.classList.contains('active')",self.scene)
        self.assertIn("svg.pauseAnimations()",self.scene)
        self.assertIn("svg.unpauseAnimations()",self.scene)
        self.assertIn("observer.observe(home,{attributes:true,attributeFilter:['class']})",self.scene)
        self.assertIn("document.addEventListener('visibilitychange',syncPlayback)",self.scene)
        self.assertIn("reduced.addEventListener('change',updateMotion)",self.scene)
        self.assertIn("height:125px",self.scene)
        self.assertIn("overflow:hidden",self.scene)

    def test_no_extra_provider_requests_and_no_record_mutations(self):
        for forbidden in ("fetch(", "localStorage","sessionStorage","setInterval(",
                          "onClick","JRDB_API_KEY","KEIBA_OWNER_PASSWORD"):
            self.assertNotIn(forbidden,self.scene)
        self.assertIn("home.prepend(banner);",self.scene)
        self.assertIn("url('./assets/racecourse58.svg')",self.scene)
        self.assertEqual(HTML.count("const banner=document.createElement('div');"),1)
        self.assertIn('id="knOwnerForecastLaunch"',HTML)
        self.assertIn('data-screen="win5"',HTML)
        self.assertIn('data-screen="live" onclick="show(\'results\')"',HTML)


if __name__=="__main__":
    unittest.main()
