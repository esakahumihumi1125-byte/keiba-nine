"""Synthetic private Gmail relay contract; no real mailbox or paid content."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_mail_bridge import (
    BRIDGE_SCHEMA, BRIDGE_URL, BRIDGE_TOKEN, BridgeUnavailable,
    bridge_enabled, fetch_mail_brief, validate_bridge_feed, load_owner_live_notes)
from private_service import create_app
from test_private_service import call, SETTINGS

URL = "https://script.google.com/macros/s/" + "AKfycABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmno" + "/exec"
TOKEN = "private-synthetic-only-0123456789_ABCDEFGH"
DATE = "2026-11-08"
TIMES = {("福島", 1): "09:45", ("東京", 1): "09:55"}


def feed():
    return {"schema": BRIDGE_SCHEMA, "date": DATE, "races": [
        {"track": "福島", "race": 1, "time": "09:45",
         "observedAt": "09:27", "ground": "稍重", "paddock": [3, 4, 5],
         "licensedRaw": "NEVER_IN_BROWSER", "forecastOverride": [6, 7, 8]}]}


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, _):
        return self.payload


class BridgeTests(unittest.TestCase):
    def test_reject_invalid_destination_and_token(self):
        self.assertFalse(bridge_enabled(SETTINGS))
        self.assertFalse(bridge_enabled({BRIDGE_URL: "https://example.com/evil", BRIDGE_TOKEN: TOKEN}))
        self.assertFalse(bridge_enabled({BRIDGE_URL: URL, BRIDGE_TOKEN: "short"}))
        self.assertTrue(bridge_enabled({BRIDGE_URL: URL, BRIDGE_TOKEN: TOKEN}))

    def test_mail_digest_has_only_sanitized_brief(self):
        received = validate_bridge_feed(feed(), DATE, TIMES)
        self.assertEqual(received["races"][0]["paddock"], [3, 4, 5])
        self.assertFalse(received["predictionReady"])
        self.assertFalse(received["officialJraVerified"])
        self.assertNotIn("NEVER_IN_BROWSER", str(received))
        self.assertNotIn("forecastOverride", str(received))
        self.assertIn("予想・馬券は変更しません", received["races"][0]["note"])
        settings = {BRIDGE_URL: URL, BRIDGE_TOKEN: TOKEN}
        called = []
        def opener(request, timeout):
            called.append((request, timeout))
            return FakeResponse(feed())
        result = fetch_mail_brief(settings, DATE, TIMES, opener=opener)
        self.assertEqual(result["races"][0]["track"], "福島")
        self.assertEqual(called[0][1], 5)
        self.assertEqual(called[0][0].get_method(), "POST")
        self.assertNotIn(TOKEN, called[0][0].full_url)

    def test_rejected_mail_bridge_response_is_distinguishable(self):
        settings = {BRIDGE_URL: URL, BRIDGE_TOKEN: TOKEN}
        with self.assertRaisesRegex(BridgeUnavailable, "Remote rejected request"):
            fetch_mail_brief(settings, DATE, TIMES,
                             opener=lambda *_args, **_kw: FakeResponse({"ok": False}))

    def test_missing_owner_calendar_shows_safe_issue_code(self):
        settings = {**SETTINGS, BRIDGE_URL: URL, BRIDGE_TOKEN: TOKEN}
        _notes, sync = load_owner_live_notes(settings, today=DATE)
        self.assertEqual(sync["status"], "要確認")
        self.assertEqual(sync["issue"], "calendar")
        self.assertNotIn(TOKEN, str(sync))

    def test_stale_late_wrong_calendar_rejected(self):
        changes = [
            lambda d: d.update(date="2026-11-07"),
            lambda d: d["races"][0].update(observedAt="09:44"),
            lambda d: d["races"][0].update(time="09:50"),
            lambda d: d["races"][0].update(track="阪神"),
            lambda d: d["races"][0].update(paddock=[3, 3]),
            lambda d: d["races"].append(copy.deepcopy(d["races"][0])),
        ]
        for mutate in changes:
            with self.subTest(change=str(mutate)):
                d = copy.deepcopy(feed())
                mutate(d)
                with self.assertRaises(BridgeUnavailable):
                    validate_bridge_feed(d, DATE, TIMES)

    def test_unconfigured_keeps_existing_manual_notes_and_no_network(self):
        store = {"KEIBA_OWNER_LIVE_NOTES_JSON": json.dumps({
            "schema": "keiba-nine-owner-live-notes-v1", "date": "2026-11-07",
            "races": [{"track": "京都", "race": 1, "time": "10:05",
                       "observedAt": "09:47", "ground": "良",
                       "paddock": [2], "note": "架空の前日メモ"}]})}
        def fail(*_):
            raise AssertionError("No remote request expected")
        result, sync = load_owner_live_notes(store, today=DATE, opener=fail)
        self.assertEqual(result["date"], "2026-11-07")
        self.assertFalse(sync["configured"])
        self.assertFalse(sync["autoChangesToPicks"])

    def test_private_endpoint_requires_login_and_preserves_forecasts(self):
        # Intercept the expensive part with an explicit validated digest.
        with patch("private_service.load_owner_live_notes",
                   return_value=(validate_bridge_feed(feed(), DATE, TIMES),
                                 {"configured": True, "status": "接続済み",
                                  "autoChangesToPicks": False})):
            app = create_app({**SETTINGS, BRIDGE_URL: URL, BRIDGE_TOKEN: TOKEN})
            self.assertEqual(call(app, "/api/owner-live-notes", auth="")["status"],
                             "401 Unauthorized")
            self.assertEqual(call(app, "/api/owner-live-notes",
                                  HTTP_X_KEIBA_REQUEST="")["status"],
                             "403 Forbidden")
            self.assertEqual(call(app, "/api/owner-live-notes",
                                  method="POST")["status"], "404 Not Found")
            response = call(app, "/api/owner-live-notes")
            self.assertEqual(response["status"], "200 OK")
            decoded = json.loads(response["body"])
            self.assertEqual(decoded["sync"]["status"], "接続済み")
            self.assertEqual(decoded["notes"]["races"][0]["paddock"], [3, 4, 5])
            self.assertNotIn(TOKEN, response["body"].decode())

    def test_remote_errors_degrade_to_manual_without_guessing(self):
        def opener(_request, _timeout):
            raise TimeoutError("Synthetic network outage")
        from unittest.mock import patch as _patch
        with _patch("owner_mail_bridge.decode_plain_owner_snapshot", create=True):
            pass
        settings = {**SETTINGS, BRIDGE_URL: URL, BRIDGE_TOKEN: TOKEN}
        notes, sync = load_owner_live_notes(settings, today=DATE, opener=opener)
        self.assertIsNone(notes)
        self.assertEqual(sync["status"], "要確認")


if __name__ == "__main__":
    unittest.main()
