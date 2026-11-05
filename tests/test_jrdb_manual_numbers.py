"""Private manual JRA-number correspondence is browser-only, not official verification."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from private_service import create_app
from jrdb_final_numbers_manual import HTML, CSS, JS
from test_private_service import SETTINGS, call

class ManualNumberMappingTests(unittest.TestCase):
    def setUp(self):
        self.app=create_app(SETTINGS)

    def test_private_access_and_no_external_calls(self):
        with patch("private_service.fetch_race_program") as programme:
            page=call(self.app,"/jrdb-mail-local")
            js=call(self.app,"/jrdb-manual-numbers.js")
            css=call(self.app,"/jrdb-mail-local.css")
        self.assertEqual(page["status"],"200 OK")
        self.assertEqual(js["status"],"200 OK")
        self.assertEqual(css["status"],"200 OK")
        self.assertIn("no-store",page["headers"]["Cache-Control"])
        self.assertIn("no-store",js["headers"]["Cache-Control"])
        self.assertIn("text/javascript",js["headers"]["Content-Type"])
        self.assertIn(b'id="manualNumberSection"',page["body"])
        self.assertIn(b'id="numberPaste"',page["body"])
        self.assertIn(b'id="compareNumbers"',page["body"])
        self.assertIn(b'id="saveNumbers"',page["body"])
        self.assertIn(b'/jrdb-manual-numbers.js',page["body"])
        self.assertIn(b'number-match',css["body"])
        programme.assert_not_called()
        for route in ("/jrdb-mail-local","/jrdb-manual-numbers.js"):
            anonymous=call(self.app,route,auth="")
            self.assertEqual(anonymous["status"],
                             "303 See Other" if route.endswith("local")
                             else "401 Unauthorized")
            self.assertNotIn(b"keiba-nine-owner-manual-numbers-v1",anonymous["body"])
            post=call(self.app,route,method="POST")
            self.assertEqual(post["status"],"404 Not Found")

    def test_local_storage_separation_and_unverified_status(self):
        self.assertIn("keiba-nine-jrdb-personal-mail-v1", JS)
        self.assertIn("keiba-nine-owner-manual-numbers-v1",JS)
        self.assertIn("sourceMark",JS)
        self.assertIn("manual", JS.lower())
        self.assertIn("再照合が必要",JS)
        self.assertIn("JRA公式照合をアプリが保証するものではありません",JS)
        self.assertIn("馬番", HTML)
        self.assertIn("手入力",HTML)
        self.assertIn("想定",HTML)
        self.assertNotIn("keiba-nine-owner-real-purchases-v1",JS)
        self.assertNotIn("keiba-nine-owner-ticket-drafts-v1",JS)
        self.assertNotIn("fetch(", JS)
        self.assertNotIn("XMLHttpRequest",JS)
        self.assertNotIn("innerHTML",JS)
        self.assertNotIn("My KEIBA",JS)
        self.assertNotIn("supabase",JS.lower())

if __name__=="__main__":
    unittest.main()
