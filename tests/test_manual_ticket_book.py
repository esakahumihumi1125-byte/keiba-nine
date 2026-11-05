"""Owner notebook is protected, no data reads or server storage."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from manual_ticket_book import HTML, JS, CSS
from test_private_service import SETTINGS, call


class PrivateManualNotebookTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SETTINGS)

    def test_auth_boundary_and_private_asset_types(self):
        with patch("private_service.fetch_race_program") as paid:
            for path, mime in (
                ("/my-tickets", "text/html"),
                ("/my-tickets.js", "text/javascript"),
                ("/my-tickets.css", "text/css"),
            ):
                approved = call(self.app, path)
                self.assertEqual(approved["status"], "200 OK")
                self.assertIn(mime, approved["headers"]["Content-Type"])
                self.assertIn("no-store", approved["headers"]["Cache-Control"])
                denied = call(self.app, path, auth="")
                if path == "/my-tickets":
                    self.assertEqual(denied["status"], "303 See Other")
                    self.assertEqual(denied["headers"]["Location"], "/login")
                else:
                    self.assertTrue(denied["status"].startswith("401"))
            self.assertIn(b'3', call(self.app, "/my-tickets")["body"])
        paid.assert_not_called()

    def test_manual_notebook_only_no_prediction_or_purchase_claims(self):
        self.assertIn('id="mDate"', HTML)
        self.assertIn('id="mTrack"', HTML)
        self.assertIn('id="mRace"', HTML)
        for id_ in ("mFirst", "mSecond", "mThird", "mCount",
                    "mCost", "mSave", "mSaved", "mExport", "mImport",
                    "mAxisSingle", "mAxisPair", "mCopyThird",
                    "mPrevRace", "mNextRace"):
            self.assertIn('id="' + id_ + '"', HTML)
        self.assertIn("AI予想・JRAの出走確定・購入履歴ではありません", HTML)
        self.assertIn("localStorage.setItem", JS)
        self.assertIn("keiba-nine-owner-ticket-drafts-v1", JS)
        self.assertIn("ticketsFor(first,second,third)", JS)
        self.assertIn("MAX_SAVED=300", JS)
        self.assertIn("keiba-nine-owner-drafts-1", JS)
        self.assertIn("picker.files", JS)
        self.assertIn("raw.every(validRecord)", JS)
        self.assertIn("LIMIT=48", JS)
        self.assertIn("function applyQuick(mode)", JS)
        self.assertIn("function changeRace(delta)", JS)
        self.assertIn("1頭軸ながし", HTML)
        self.assertIn("2頭軸ながし", HTML)
        self.assertIn('class="back app-home-link"', HTML)
        self.assertIn('https://esakahumihumi1125-byte.github.io/keiba-nine/', HTML)
        self.assertNotIn("fetch(", JS)
        self.assertNotIn("innerHTML", JS)
        self.assertNotIn("JRDB_API_KEY", JS + HTML + CSS)
        self.assertNotIn("KEIBA_OWNER_PASSWORD", JS + HTML + CSS)
        self.assertNotIn("myKeibaPurchase", JS)
        self.assertIn("Content-Security-Policy",
                      call(self.app, "/my-tickets")["headers"])

    def test_post_disabled_and_no_public_source_disclosure(self):
        posted = call(self.app, "/my-tickets", method="POST")
        self.assertEqual(posted["status"], "404 Not Found")
        for route in ("/my-tickets", "/my-tickets.js", "/my-tickets.css"):
            out = call(self.app, route, auth="")
            self.assertNotIn(b"keiba-nine-owner-ticket-drafts-v1", out["body"])


if __name__ == "__main__":
    unittest.main()
