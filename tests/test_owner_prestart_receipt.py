"""Synthetic tests for authenticated server time signing and private review."""
import copy
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_forecast_delivery import validate_owner_forecast, SCHEMA
from owner_prestart_receipt import (
    issue_preview_receipts, verify_preview_receipts, ReceiptError)
from keiba_100yen_review import review_100yen
from private_service import create_app
from test_private_service import call, SETTINGS

DAY = "2099-04-12"


def sample_race(track="東京", race=1, time="10:00", status="買い候補"):
    first = [1, 2]
    second = [1, 2, 3]
    third = [1, 2, 3, 4]
    points = len({(x, y, z) for x in first for y in second for z in third
                  if x != y and x != z and y != z})
    return {
        "track": track, "race": race, "time": time, "course": "芝1600m",
        "field": 8, "rank": [1, 2, 3, 4],
        "first": first, "second": second, "third": third,
        "points": points, "confidence": 4 if status == "買い候補" else 2,
        "status": status, "headNames": [None, None], "note": "synthetic",
        "provisional": True, "jraOfficialConfirmed": False,
        "fullFactorVerified": False
    }


def forecast(*races):
    return validate_owner_forecast({
        "schema": SCHEMA, "date": DAY, "races": list(races)})


def setup(*races):
    return {
        **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
        "KEIBA_RENDER_PREVIEW_ONLY": "0",
        "KEIBA_OWNER_FORECAST_JSON": json.dumps({
            "schema": SCHEMA, "date": DAY, "races": list(races)
        }, ensure_ascii=False)
    }


def post(app, path, body, **changes):
    return call(app, path, method="POST", data=body, **changes)


class ResearchReceiptTests(unittest.TestCase):
    def test_server_issued_immutable_ticket_selection_and_pending_only(self):
        doc = forecast(sample_race(), sample_race("京都", 2))
        now = datetime(2099, 4, 11, 10, 0, tzinfo=timezone.utc)
        issued = issue_preview_receipts(doc, SETTINGS["KEIBA_OWNER_PASSWORD"],
                                        DAY, now=now)
        self.assertEqual(issued["issuedRaces"], 2)
        self.assertFalse(issued["officialScheduleVerified"])
        self.assertFalse(issued["actualPurchase"])
        self.assertEqual(issued["captureServerTime"], now.isoformat())
        snaps = verify_preview_receipts(
            issued["receipts"], SETTINGS["KEIBA_OWNER_PASSWORD"], DAY)
        self.assertEqual(len(snaps), 2)
        self.assertTrue(all(p["sourceKind"] == "prestart-locked" for p in snaps))
        self.assertTrue(all(p["actualPurchase"] is False for p in snaps))
        self.assertTrue(all(p["trioTickets"] == [] for p in snaps))
        self.assertNotIn("horseNames", json.dumps(issued))
        self.assertNotIn("API_KEY", json.dumps(issued))
        report = review_100yen(snaps, [])
        self.assertEqual(report["reviewedRaces"], 0)
        self.assertEqual(report["pendingRaces"], 2)
        self.assertEqual(report["totalInvestedYen"], 0)
        self.assertIsNone(report["roiPercent"])
        self.assertEqual(report["pendingStakeYen"], 2 * 8 * 100)

    def test_past_and_non_buy_races_excluded(self):
        doc = forecast(sample_race(time="10:00"),
                       sample_race("京都", 2, time="13:00"),
                       sample_race("福島", 3, time="15:00", status="見送り"))
        now = datetime(2099, 4, 12, 3, 0, tzinfo=timezone.utc)  # noon JST
        issued = issue_preview_receipts(doc, SETTINGS["KEIBA_OWNER_PASSWORD"],
                                        DAY, now=now)
        self.assertEqual(issued["issuedRaces"], 1)
        self.assertEqual(issued["skippedStartedRaces"], 1)
        self.assertEqual(issued["skippedNotBuyRaces"], 1)
        self.assertEqual(issued["receipts"][0]["snapshot"]["track"], "京都")

    def test_no_post_off_or_naive_clock(self):
        doc = forecast(sample_race())
        for now in (datetime(2099, 4, 12, 1, 0, tzinfo=timezone.utc),
                    datetime(2099, 4, 12, 2, 0, tzinfo=timezone.utc)):
            out = issue_preview_receipts(doc, SETTINGS["KEIBA_OWNER_PASSWORD"],
                                         DAY, now=now)
            self.assertEqual(out["issuedRaces"], 0)
            self.assertEqual(out["skippedStartedRaces"], 1)
        with self.assertRaises(ReceiptError):
            issue_preview_receipts(doc, SETTINGS["KEIBA_OWNER_PASSWORD"],
                                   DAY, now=datetime(2099, 4, 11, 21))

    def test_any_changed_number_or_timestamp_invalidates_signature(self):
        issued = issue_preview_receipts(forecast(sample_race()),
                                        SETTINGS["KEIBA_OWNER_PASSWORD"], DAY,
                                        now=datetime(2099, 4, 11, tzinfo=timezone.utc))
        receipts = issued["receipts"]
        verify_preview_receipts(receipts, SETTINGS["KEIBA_OWNER_PASSWORD"], DAY)
        for edit in ("number", "time", "paid", "signature"):
            changed = copy.deepcopy(receipts)
            if edit == "number":
                changed[0]["snapshot"]["trifectaTickets"][0][0] = 6
            elif edit == "time":
                changed[0]["snapshot"]["lockedAt"] = "2099-04-12T08:30:00+09:00"
            elif edit == "paid":
                changed[0]["snapshot"]["actualPurchase"] = True
            else:
                changed[0]["signature"] = "0" * 64
            with self.subTest(edit=edit), self.assertRaises(ReceiptError):
                verify_preview_receipts(changed, SETTINGS["KEIBA_OWNER_PASSWORD"], DAY)
        with self.assertRaises(ReceiptError):
            verify_preview_receipts(receipts, "different-random-owner-password-1234", DAY)
        with self.assertRaises(ReceiptError):
            verify_preview_receipts(receipts+receipts, SETTINGS["KEIBA_OWNER_PASSWORD"], DAY)
        with self.assertRaises(ReceiptError):
            verify_preview_receipts(receipts, SETTINGS["KEIBA_OWNER_PASSWORD"], "2099-04-13")

    def test_private_http_freeze_and_review_without_official_results(self):
        app = create_app(setup(sample_race()))
        issue = post(app, "/api/owner-freeze-preday", {"date":DAY})
        self.assertEqual(issue["status"], "200 OK")
        out = json.loads(issue["body"])
        self.assertTrue(out["available"])
        self.assertEqual(out["issuedRaces"], 1)
        self.assertFalse(out["officialScheduleVerified"])
        verified = post(app, "/api/owner-100yen-verify-receipts",
                        {"date":DAY,"receipts":out["receipts"]})
        self.assertEqual(verified["status"], "200 OK")
        summary = json.loads(verified["body"])
        self.assertTrue(summary["serverSigned"])
        self.assertFalse(summary["captureAuditVerified"])
        self.assertFalse(summary["officialFeedConnected"])
        self.assertEqual(summary["review"]["pendingRaces"], 1)
        self.assertEqual(summary["review"]["reviewedRaces"], 0)
        self.assertIsNone(summary["review"]["roiPercent"])
        self.assertNotIn("signature", verified["body"].decode())
        self.assertNotIn("lockedAt", verified["body"].decode())
        self.assertNotIn("synthetic", verified["body"].decode())

    def test_fail_closed_for_preview_unauth_cross_site_or_bad_request(self):
        app = create_app(setup(sample_race()))
        preview = create_app({
            **setup(sample_race()),
            "KEIBA_RENDER_PRIVATE_ONLY":"0", "KEIBA_RENDER_PREVIEW_ONLY":"1"})
        for path, body in (
            ("/api/owner-freeze-preday", {"date":DAY}),
            ("/api/owner-100yen-verify-receipts", {"date":DAY,"receipts":[]})
        ):
            with self.subTest(path=path):
                self.assertEqual(post(preview, path, body)["status"], "404 Not Found")
                self.assertEqual(post(app, path, body, auth="")["status"], "401 Unauthorized")
                self.assertEqual(post(app, path, body, HTTP_X_KEIBA_REQUEST="")["status"],
                                 "403 Forbidden")
                self.assertEqual(post(app, path, body, HTTP_SEC_FETCH_SITE="cross-site")["status"],
                                 "403 Forbidden")
                self.assertEqual(post(app, path, {**body,"other":123})["status"],
                                 "400 Bad Request")
                self.assertEqual(call(app,path,method="GET")["status"],"404 Not Found")

    def test_signed_record_review_rejects_tampering(self):
        app = create_app(setup(sample_race()))
        data = json.loads(post(app,"/api/owner-freeze-preday",
                               {"date":DAY})["body"])
        changed = copy.deepcopy(data["receipts"])
        changed[0]["snapshot"]["trifectaTickets"][0][0] = 17
        bad=post(app, "/api/owner-100yen-verify-receipts",
                 {"date":DAY,"receipts":changed})
        self.assertEqual(bad["status"], "400 Bad Request")
        self.assertNotIn("17",bad["body"].decode())


if __name__ == "__main__":
    unittest.main()
