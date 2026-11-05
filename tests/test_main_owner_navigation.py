"""Main app navigation to authenticated owner notebook: static and offline checks."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from manual_ticket_book import HTML as OWNER_HTML

class MainAppOwnerNavigationTests(unittest.TestCase):
    def test_main_menu_has_owner_ticket_entry_without_altering_saved_data(self):
        main = (ROOT / "keiba-nine-beta51-feed-record.html").read_text(encoding="utf-8")
        self.assertIn('data-screen="ticket" onclick="show(\'ticket\')"', main)
        self.assertIn('id="ownerTicketOpen"', main)
        self.assertIn('id="ownerLedgerOpen"', main)
        self.assertEqual(main.count('https://keiba-nine-owner-preview.onrender.com/my-tickets'), 2)
        self.assertIn('name===\'published\'?\'home\':name', main)
        self.assertIn("保存記録はRender側に別管理", main)
        self.assertNotIn('KEIBA_OWNER_PASSWORD=', main)
        self.assertNotIn('KEIBA_OWNER_PUBLIC_ORIGIN=', main)

    def test_owner_notebook_has_return_link_and_is_still_private(self):
        self.assertIn("https://esakahumihumi1125-byte.github.io/keiba-nine/", OWNER_HTML)
        self.assertIn("いつもの競馬ナインへ", OWNER_HTML)
        self.assertIn('href=\"/\"', OWNER_HTML)
        self.assertNotIn("window.parent", OWNER_HTML)

if __name__ == "__main__":
    unittest.main()
