"""All ordinary ARC RACE public controls share a safe blue family."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")

class PublicBlueControlTests(unittest.TestCase):
    def setUp(self):
        self.css=HTML.split('<style id="arc-race-blue-controls">',1)[1].split('</style>',1)[0]

    def test_primary_matches_existing_owner_launch(self):
        self.assertEqual(HTML.count('id="arc-race-blue-controls"'),1)
        self.assertIn('--arc-action-top:#2b78b4',self.css)
        self.assertIn('--arc-action-bottom:#1c5486',self.css)
        self.assertIn('--arc-action-border:#70aee0',self.css)
        self.assertIn('#app .btn:not(.secondary):not(.ghost):not(.danger)',self.css)
        self.assertIn('background:linear-gradient(180deg,var(--arc-action-top),var(--arc-action-bottom))',self.css)
        old=HTML.split('<style id="knForecastHubStyle">',1)[1].split('</style>',1)[0]
        self.assertIn('background:linear-gradient(180deg,#2b78b4 0%,#1c5486 100%)',old)

    def test_secondary_navigation_and_safety_states(self):
        self.assertIn('#app .btn.secondary,#app .btn.ghost',self.css)
        self.assertIn('var(--arc-action-secondary-bottom)',self.css)
        self.assertIn('#app .tabs button.active{background:#1c4668',self.css)
        self.assertIn('#app .record66-states button[aria-pressed="true"]',self.css)
        self.assertIn('#app .btn.danger{background:#8d3443',self.css)
        self.assertIn('#app .btn:disabled,#app button:disabled',self.css)
        self.assertIn('outline:3px solid #f2ca72',self.css)

    def test_shortcuts_and_data_logic_unchanged(self):
        self.assertIn('#knTicketShortcut,#knPurchaseLink,#knPersonalRecord',self.css)
        for forbidden in ('localStorage','sessionStorage','fetch(','setInterval(',
                          '<script','JRDB_API_KEY','autoPurchase'):
            self.assertNotIn(forbidden,self.css)
        for preserved in ('id="knOwnerForecastLaunch"', 'data-screen="win5"',
                          'id="reset"', 'class="btn danger"',
                          'id="arc-race-static-hero"',
                          "show('results')","keiba_nine_race_flow_demo_v1_8"):
            self.assertIn(preserved,HTML)

if __name__=='__main__':
    unittest.main()
