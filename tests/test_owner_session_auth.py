"""Strict owner auth and iPhone signed-session regression checks."""
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlencode
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_session_auth import (
    COOKIE_NAME, SESSION_SECONDS, owner_credentials_match, session_cookie,
    session_cookie_valid,
)
from private_service import create_app
from test_private_service import SETTINGS, AUTH, call


def login(app, fields, **changes):
    raw = urlencode(fields).encode()
    environ = {
        "wsgi.url_scheme": "https",
        "REMOTE_ADDR": "127.0.0.1",
        "PATH_INFO": "/login",
        "REQUEST_METHOD": "POST",
        "HTTP_HOST": "keiba-nine-owner-preview.onrender.com",
        "HTTP_ORIGIN": "https://keiba-nine-owner-preview.onrender.com",
        "CONTENT_TYPE": "application/x-www-form-urlencoded",
        "CONTENT_LENGTH": str(len(raw)),
        "HTTP_AUTHORIZATION": "",
        "wsgi.input": io.BytesIO(raw),
    }
    environ.update(changes)
    response = {}
    def start(status, headers):
        response.update(status=status, headers=dict(headers))
    response["body"] = b"".join(app(environ, start))
    return response


class OwnerSessionTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SETTINGS)
        self.expected = hashlib.sha256(
            ("owner:" + SETTINGS["KEIBA_OWNER_PASSWORD"]).encode()
        ).digest()

    def test_exact_password_check_and_cookie_expiry(self):
        self.assertTrue(owner_credentials_match("owner", SETTINGS["KEIBA_OWNER_PASSWORD"],
                                                self.expected, "owner"))
        self.assertFalse(owner_credentials_match("owner", "wrong", self.expected, "owner"))
        self.assertFalse(owner_credentials_match("other", SETTINGS["KEIBA_OWNER_PASSWORD"],
                                                 self.expected, "owner"))
        token = session_cookie(self.expected, now=1800000000)
        self.assertIn("Secure; SameSite=Lax", token)
        self.assertIn("HttpOnly", token)
        self.assertTrue(token.startswith(COOKIE_NAME + "="))
        self.assertIn("Max-Age=604800", token)
        raw = token.split(";", 1)[0]
        self.assertTrue(session_cookie_valid(raw, self.expected, now=1800000000))
        self.assertTrue(session_cookie_valid(raw, self.expected,
                                             now=1800000000 + SESSION_SECONDS - 1))
        self.assertFalse(session_cookie_valid(raw, self.expected,
                                              now=1800000000 + SESSION_SECONDS))
        self.assertFalse(session_cookie_valid(raw, self.expected, now=1799999999))
        self.assertFalse(session_cookie_valid(raw, b"x" * 32, now=1800000000))
        self.assertFalse(session_cookie_valid(raw + "; " + raw, self.expected, now=1800000000))
        self.assertFalse(session_cookie_valid(raw + "other", self.expected, now=1800000000))
        self.assertFalse(session_cookie_valid("a" * 6000, self.expected))

    def test_form_no_basic_popup_and_no_secret_leak(self):
        with patch("private_service.fetch_race_program") as provider:
            root = call(self.app, "/", auth="")
            self.assertEqual(root["status"], "303 See Other")
            self.assertEqual(root["headers"]["Location"], "/login")
            self.assertNotIn("WWW-Authenticate", root["headers"])
            html = call(self.app, "/login", auth="")
            self.assertEqual(html["status"], "200 OK")
            self.assertIn(b'type="password"', html["body"])
            self.assertIn(b'name="username"', html["body"])
            self.assertNotIn(SETTINGS["KEIBA_OWNER_PASSWORD"].encode(), html["body"])
            self.assertEqual(call(self.app, "/login.css", auth="")["status"], "200 OK")
            self.assertTrue(call(self.app, "/api/status", auth="")["status"].startswith("401"))
            self.assertTrue(call(self.app, "/ui-version", auth="")["status"].startswith("401"))
        provider.assert_not_called()

    def test_cookie_allows_owner_pages_and_api_requires_csrf_header(self):
        with (patch("private_service.fetch_race_program") as programme,
              patch("private_service.fetch_horse_entries") as entries):
            result = login(self.app, {
                "username": "owner", "password": SETTINGS["KEIBA_OWNER_PASSWORD"]
            })
            self.assertEqual(result["status"], "303 See Other")
            self.assertEqual(result["headers"]["Location"], "/login?session=check")
            cookie = result["headers"]["Set-Cookie"]
            self.assertIn("HttpOnly; Secure; SameSite=Lax", cookie)
            self.assertNotIn(SETTINGS["KEIBA_OWNER_PASSWORD"], cookie)
            header = cookie.split(";", 1)[0]
            # The intermediate redirect distinguishes a valid password from
            # browsers that block/drop cookies during the same navigation.
            missing = call(self.app, "/login", auth="", QUERY_STRING="session=check")
            self.assertEqual(missing["status"], "200 OK")
            self.assertIn("認証情報がブラウザーに保存されていません", missing["body"].decode())
            self.assertNotIn("Set-Cookie", missing["headers"])
            with_cookie = call(self.app, "/login", auth="", HTTP_COOKIE=header,
                               QUERY_STRING="session=check")
            self.assertEqual(with_cookie["status"], "303 See Other")
            self.assertEqual(with_cookie["headers"]["Location"], "/")
            home = call(self.app, "/", auth="", HTTP_COOKIE=header)
            self.assertEqual(home["status"], "200 OK")
            status = call(self.app, "/api/status", auth="", HTTP_COOKIE=header)
            self.assertEqual(status["status"], "200 OK")
            self.assertFalse(json.loads(status["body"])["jrdbConfigured"])
            blocked = call(self.app, "/api/status", auth="", HTTP_COOKIE=header,
                           HTTP_X_KEIBA_REQUEST="")
            self.assertEqual(blocked["status"], "403 Forbidden")
            blocked = call(self.app, "/api/status", auth="", HTTP_COOKIE=header,
                           HTTP_SEC_FETCH_SITE="cross-site")
            self.assertEqual(blocked["status"], "403 Forbidden")
        programme.assert_not_called()
        entries.assert_not_called()

    def test_same_site_iphone_form_with_verified_origin_and_render_proxy(self):
        # Safari may label the navigation same-site even for the owner form.
        # A verified exact Origin must still be required.
        good = {"username": "owner", "password": SETTINGS["KEIBA_OWNER_PASSWORD"]}
        app = create_app({**SETTINGS, "RENDER": "true",
                          "RENDER_EXTERNAL_HOSTNAME":
                          "keiba-nine-owner-preview.onrender.com"})
        normal = login(app, good, HTTP_SEC_FETCH_SITE="same-site")
        self.assertEqual(normal["status"], "303 See Other")
        proxy = login(app, good, HTTP_HOST="render-internal:10000",
                      HTTP_SEC_FETCH_SITE="same-site")
        self.assertEqual(proxy["status"], "303 See Other")
        rejected = login(app, good, HTTP_SEC_FETCH_SITE="same-site",
                         HTTP_ORIGIN="https://unrelated.example")
        self.assertEqual(rejected["status"], "401 Unauthorized")
        rejected = login(app, good, HTTP_SEC_FETCH_SITE="cross-site")
        self.assertEqual(rejected["status"], "401 Unauthorized")
        rejected = login(app, good, HTTP_SEC_FETCH_SITE="same-site",
                         HTTP_ORIGIN="")
        self.assertEqual(rejected["status"], "401 Unauthorized")

    def test_failed_form_does_not_leak_password_or_issue_cookie(self):
        good = {"username": "owner", "password": SETTINGS["KEIBA_OWNER_PASSWORD"]}
        with patch("private_service.fetch_race_program") as provider:
            cases = [
                ({**good, "password": "wrong"}, {}),
                ({**good, "username": "other"}, {}),
                (good, {"HTTP_ORIGIN": "https://other.example"}),
                (good, {"HTTP_SEC_FETCH_SITE": "cross-site"}),
                (good, {"CONTENT_TYPE": "application/json"}),
                (good, {"QUERY_STRING": "debug=1"}),
                (good, {"CONTENT_LENGTH": "9000"}),
            ]
            for fields, headers in cases:
                result = login(self.app, fields, **headers)
                self.assertEqual(result["status"], "401 Unauthorized")
                self.assertNotIn("Set-Cookie", result["headers"])
                self.assertNotIn("WWW-Authenticate", result["headers"])
                self.assertNotIn(good["password"].encode(), result["body"])
            self.assertEqual(call(self.app, "/", auth=AUTH)["status"], "200 OK")
            self.assertTrue(call(self.app, "/app.js", auth="")["status"].startswith("401"))
            for path in ("/app.js", "/app.css", "/my-tickets.js",
                         "/my-tickets.css", "/my-purchases.js"):
                asset = call(self.app, path, auth="")
                self.assertEqual(asset["status"], "401 Unauthorized")
                self.assertNotIn("WWW-Authenticate", asset["headers"],
                                 "Browser assets must not trigger native login popups")
        provider.assert_not_called()


if __name__ == "__main__":
    unittest.main()
