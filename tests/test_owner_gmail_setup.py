"""Private iPhone Gmail setup is read-only and never exports credentials."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import SETTINGS, call


class SetupTests(unittest.TestCase):
    def test_private_setup_page_and_assets(self):
        app = create_app(SETTINGS)
        for path, marker in (
            ("/owner-gmail-setup", "Gmail直前メール連携"),
            ("/owner-gmail-setup.js", "setupCodeFallback"),
            ("/owner-gmail-setup.css", "color-scheme:dark"),
        ):
            with self.subTest(path=path):
                ok = call(app, path)
                self.assertEqual(ok["status"], "200 OK")
                self.assertIn(marker, ok["body"].decode())
                self.assertIn("no-store", ok["headers"]["Cache-Control"])
                denied = call(app, path, auth="")
                self.assertIn(denied["status"][:3], ("303", "401"))
        self.assertIn(
            'href="/owner-gmail-setup"',
            call(app, "/owner-preday-forecast")["body"].decode(),
        )
        js = call(app, "/owner-gmail-setup.js")["body"].decode()
        self.assertNotIn("innerHTML", js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("KEIBA_MAIL_BRIDGE_TOKEN", js)
        self.assertIn("X-Keiba-Request", js)

    def test_script_copy_is_private_read_only(self):
        app = create_app(SETTINGS)
        path = "/api/owner-gmail-script-code"
        self.assertEqual(call(app, path, auth="")["status"], "401 Unauthorized")
        self.assertEqual(call(app, path, HTTP_X_KEIBA_REQUEST="")["status"], "403 Forbidden")
        self.assertEqual(
            call(app, path, HTTP_SEC_FETCH_SITE="cross-site")["status"],
            "403 Forbidden",
        )
        self.assertEqual(call(app, path, method="POST")["status"], "404 Not Found")
        good = call(app, path)
        self.assertEqual(good["status"], "200 OK")
        self.assertIn("text/plain", good["headers"]["Content-Type"])
        self.assertIn("no-store", good["headers"]["Cache-Control"])
        code = good["body"].decode()
        self.assertIn("function installKeibaMailTrigger()", code)
        self.assertIn("function syncKeibaMail()", code)
        self.assertNotIn(SETTINGS["KEIBA_OWNER_PASSWORD"], code)


if __name__ == "__main__":
    unittest.main()
