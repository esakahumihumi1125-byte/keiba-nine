"""Navigation-only integration: the owner app stays private and data stays isolated."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "keiba-nine-beta51-feed-record.html"


class OwnerNavigationTests(unittest.TestCase):
    def test_main_app_has_one_owner_notebook_entry_per_workflow(self):
        html = MAIN.read_text(encoding="utf-8")
        owner_url = "https://keiba-nine-owner-preview.onrender.com/my-tickets"
        self.assertEqual(html.count('id="ownerTicketOpen"'), 1)
        self.assertEqual(html.count('id="ownerLedgerOpen"'), 1)
        self.assertEqual(html.count('href="' + owner_url + '"'), 2)
        self.assertIn('data-screen="ticket" onclick="show(\'ticket\')"', html)
        self.assertIn("name==='published'?'home':name", html)
        self.assertNotIn('href="' + owner_url + '?', html,
                         "Never put account data in navigation URL")
        self.assertIn("自動合算しません", html)

    def test_original_app_data_boundary_unchanged(self):
        html = MAIN.read_text(encoding="utf-8")
        self.assertIn("const KEY='keiba_nine_race_flow_demo_v1_8'", html)
        self.assertNotIn("keiba-nine-owner-ticket-drafts-v1", html,
                         "No cross-origin localStorage assumptions")


if __name__ == "__main__":
    unittest.main()
