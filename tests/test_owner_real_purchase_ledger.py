"""Private manual 3連単 owner real-purchase ledger: no public data or paid API."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from manual_purchase_book import HTML, CSS, JS
from test_private_service import SETTINGS, call


class OwnerRealPurchaseLedgerTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SETTINGS)

    def test_owner_auth_for_both_page_and_new_script(self):
        with patch("private_service.fetch_race_program") as provider:
            page = call(self.app, "/my-tickets")
            self.assertEqual(page["status"], "200 OK")
            self.assertIn("text/html", page["headers"]["Content-Type"])
            self.assertIn("no-store", page["headers"]["Cache-Control"])
            self.assertIn("id=\"actualPurchasePanel\"", page["body"].decode())
            self.assertIn("/my-purchases.js?v=ledger-v1", page["body"].decode())
            script = call(self.app, "/my-purchases.js")
            self.assertEqual(script["status"], "200 OK")
            self.assertIn("text/javascript", script["headers"]["Content-Type"])
            self.assertIn("no-store", script["headers"]["Cache-Control"])
            self.assertIn("keiba-nine-owner-real-purchases-v1", script["body"].decode())
            self.assertIn("ledger-stats", call(self.app, "/my-tickets.css")["body"].decode())
            for route in ("/my-tickets", "/my-purchases.js"):
                rejected = call(self.app, route, auth="")
                if route == "/my-tickets":
                    self.assertEqual(rejected["status"], "303 See Other")
                    self.assertEqual(rejected["headers"]["Location"], "/login")
                else:
                    self.assertTrue(rejected["status"].startswith("401"))
                self.assertNotIn(b"keiba-nine-owner-real-purchases-v1", rejected["body"])
        provider.assert_not_called()

    def test_ledger_is_explicit_owner_entry_only_and_not_live_prediction(self):
        for element in ("realUnit", "realAdd", "realInvest", "realReturn",
                        "realROI", "realProfit", "realPending", "realList",
                        "realMessage", "realExport"):
            self.assertIn('id="' + element + '"', HTML)
        self.assertIn("実際に購入した分だけ", HTML)
        self.assertIn("払戻未確定", HTML)
        self.assertIn("回収率", HTML)
        self.assertIn("payout!==null", JS)
        self.assertIn("localStorage.setItem", JS)
        self.assertIn("real.length>=500", JS)
        self.assertIn("if(!confirm(explain))return", JS)
        self.assertIn("payout:null", JS)
        self.assertNotIn("fetch(", JS)
        self.assertNotIn("innerHTML", JS)
        self.assertNotIn("JRDB_API_KEY", JS + HTML + CSS)
        self.assertNotIn("KEIBA_OWNER_PASSWORD", JS + HTML + CSS)
        self.assertNotIn("myKeibaPurchase", JS)
        self.assertNotIn("localStorage", HTML)
        self.assertIn("Content-Security-Policy",
                      call(self.app, "/my-tickets")["headers"])


if __name__ == "__main__":
    unittest.main()
