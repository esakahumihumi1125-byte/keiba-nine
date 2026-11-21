"""Synthetic end-to-end prestart decision signing: BUY and HOLD both count."""
import copy
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_decision_receipt import (
    issue_decision_captures, verify_decision_captures,
    DecisionReceiptError, SCHEMA, JST,
)
from test_owner_forecast_delivery import forecast
from private_service import create_app
from test_private_service import SETTINGS, call

KEY = "test-owner-decision-signing-key-1234567890ABCXYZ"
DAY = "2026-11-21"


def private_forecast(day=DAY):
    f = forecast()
    f["date"] = day
    f["sourceKind"] = "owner-private-authored-preday"
    f["predictionReady"] = False
    f["officialJraVerified"] = False
    f["purchased"] = False
    f["races"][0]["status"] = "買い候補"
    f["races"][1]["status"] = "見送り"
    # Validated owner references are reduced to strict presentation fields.
    return f


class DecisionReceiptTests(unittest.TestCase):
    def test_buy_and_hold_are_signed_before_off_and_not_modified(self):
        f = private_forecast()
        before = copy.deepcopy(f)
        now = datetime(2026, 11, 20, 18, tzinfo=JST)
        issued = issue_decision_captures(f, KEY, DAY, now=now)
        self.assertEqual(issued["schema"], SCHEMA)
        self.assertEqual(issued["capturedRaces"], 36)
        self.assertEqual(issued["skippedStartedRaces"], 0)
        self.assertFalse(issued["officialScheduleVerified"])
        self.assertFalse(issued["actualPurchase"])
        self.assertEqual(f, before, "never mutate original decisions")
        verified = verify_decision_captures(issued["captures"], KEY, DAY)
        self.assertTrue(verified["verified"])
        self.assertEqual(verified["captureCount"], 36)
        self.assertEqual(verified["captures"][0]["decision"], "買い候補")
        self.assertEqual(verified["captures"][1]["decision"], "見送り")
        self.assertEqual(verified["captures"][1]["points"], 30)
        self.assertFalse(verified["officialResultsVerified"])
        self.assertNotIn("providerSecret", str(verified))
        self.assertNotIn("rawPrivateIndex", str(verified))

    def test_no_backdating_after_off_even_with_valid_forecast(self):
        f = private_forecast()
        f["races"][0]["time"] = "10:00"
        f["races"][1]["time"] = "16:00"
        now = datetime(2026, 11, 21, 14, tzinfo=JST)
        doc = issue_decision_captures(f, KEY, DAY, now=now)
        self.assertEqual(doc["skippedStartedRaces"], 35)
        self.assertEqual(doc["capturedRaces"], 1)
        self.assertEqual(doc["captures"][0]["snapshot"]["race"], 2)
        later = issue_decision_captures(f, KEY, DAY,
                                        now=datetime(2026,11,21,17,tzinfo=JST))
        self.assertEqual(later["capturedRaces"], 0)
        self.assertEqual(later["skippedStartedRaces"], 36)
        with self.assertRaisesRegex(DecisionReceiptError, "Day is not upcoming"):
            issue_decision_captures(
                f, KEY, DAY, now=datetime(2026,11,22,9,tzinfo=JST))

    def test_changed_status_numbers_timestamp_or_signature_are_rejected(self):
        base = issue_decision_captures(
            private_forecast(), KEY, DAY,
            now=datetime(2026,11,20,18,tzinfo=JST))["captures"]
        for field, value in (
            ("decision", "見送り"),
            ("points", 40),
            ("lockedAt", "2026-11-20T10:00:00+00:00"),
            ("officialScheduleVerified", True),
            ("actualPurchase", True),
        ):
            altered = copy.deepcopy(base[:1])
            altered[0]["snapshot"][field] = value
            with self.subTest(field=field), self.assertRaises(DecisionReceiptError):
                verify_decision_captures(altered, KEY, DAY)
        with self.assertRaises(DecisionReceiptError):
            verify_decision_captures(base[:1] + base[:1], KEY, DAY)
        with self.assertRaises(DecisionReceiptError):
            verify_decision_captures(base[:1], "another-secret-very-long-ABCDEFGH", DAY)
        with self.assertRaises(DecisionReceiptError):
            verify_decision_captures(base[:1], KEY, "2026-11-22")

    def test_authenticated_routes_do_not_report_real_bets(self):
        date = (datetime.now(JST).date() + timedelta(days=1)).isoformat()
        f = private_forecast(date)
        settings = {**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                    "KEIBA_OWNER_FORECAST_JSON": json.dumps(f,ensure_ascii=False)}
        app = create_app(settings)
        frozen = call(app, "/api/owner-decision-freeze", method="POST",
                      data={"date":date})
        self.assertEqual(frozen["status"], "200 OK", frozen["body"])
        d = json.loads(frozen["body"])
        self.assertTrue(d["available"])
        self.assertEqual(d["capturedRaces"], 36)
        self.assertFalse(d["officialScheduleVerified"])
        self.assertFalse(d["actualPurchase"])
        saved = d["captures"]
        view = call(app, "/api/owner-decision-verify", method="POST",
                    data={"date":date,"captures":saved})
        self.assertEqual(view["status"], "200 OK")
        v = json.loads(view["body"])
        self.assertTrue(v["verified"])
        self.assertEqual(v["captureCount"], 36)
        self.assertEqual(v["captures"][1]["decision"], "見送り")
        self.assertFalse(v["officialResultsVerified"])
        for route,payload in (
            ("/api/owner-decision-freeze", {"date":date}),
            ("/api/owner-decision-verify", {"date":date,"captures":saved}),
        ):
            with self.subTest(route=route):
                anonymous = call(app,route,method="POST",auth="",data=payload)
                self.assertEqual(anonymous["status"], "401 Unauthorized")
                csrf = call(app,route,method="POST",data=payload,
                            HTTP_X_KEIBA_REQUEST="")
                self.assertEqual(csrf["status"], "403 Forbidden")
        modified = copy.deepcopy(saved)
        modified[1]["snapshot"]["decision"] = "買い候補"
        invalid = call(app,"/api/owner-decision-verify",method="POST",
                       data={"date":date,"captures":modified})
        self.assertEqual(invalid["status"], "400 Bad Request")
        preview=create_app({**settings, "KEIBA_RENDER_PREVIEW_ONLY":"1"})
        self.assertEqual(call(preview,"/api/owner-decision-freeze",method="POST",
                              data={"date":date})["status"], "404 Not Found")

    def test_past_races_are_not_created_by_capturing_old_reference(self):
        f = private_forecast("2026-11-20")
        app=create_app({**SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
                        "KEIBA_OWNER_FORECAST_JSON":json.dumps(f,ensure_ascii=False)})
        r=call(app,"/api/owner-decision-freeze",method="POST",
               data={"date":"2026-11-20"})
        self.assertEqual(r["status"],"400 Bad Request")


if __name__ == "__main__":
    unittest.main()
