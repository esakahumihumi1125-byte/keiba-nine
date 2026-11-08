"""Owner-only frozen hypothetical review tests; all data synthetic."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_100yen_snapshot import decode_frozen_snapshots, FrozenSnapshotError, SCHEMA
from private_service import create_app
from test_private_service import call, SETTINGS


def race(track="東京", number=1):
    return {
        "date": "2026-11-08",
        "track": track,
        "race": number,
        "sourceKind": "prestart-locked",
        "actualPurchase": False,
        "lockedAt": "2026-11-07T18:00:00+09:00",
        "scheduledOffAt": "2026-11-08T10:00:00+09:00",
        "trifectaTickets": [[1, 2, 3], [2, 1, 3]],
        "trioTickets": [[3, 2, 1]],
    }


def settings_for(*rows):
    return {
        **SETTINGS,
        "KEIBA_RENDER_PRIVATE_ONLY": "1",
        "KEIBA_RENDER_PREVIEW_ONLY": "0",
        "KEIBA_OWNER_FROZEN_PREDICTIONS_JSON":
            json.dumps({"schema": SCHEMA, "snapshots": list(rows)},
                       ensure_ascii=False),
        # Pretending to verify results in configuration MUST have no effect.
        "KEIBA_OWNER_OFFICIAL_RESULTS_JSON":
            json.dumps([{"date":"2026-11-08", "track":"東京",
                         "race":1, "officialVerified":True,
                         "finish":[1,2,3],
                         "trifectaPer100Yen":999999999,
                         "trioPer100Yen":888888888}])
    }


def get_day(app, day="2026-11-08", **changes):
    return call(app, "/api/owner-100yen-review",
                QUERY_STRING="date="+day, **changes)


class Owner100YenPageTests(unittest.TestCase):
    def test_private_navigation_and_assets_only(self):
        preview = create_app(SETTINGS)
        private = create_app(settings_for())
        self.assertNotIn("/owner-100yen-review", call(preview, "/")["body"].decode())
        for path in ("/owner-100yen-review",
                     "/owner-100yen-review.js", "/owner-100yen-review.css"):
            self.assertEqual(call(preview, path)["status"], "404 Not Found")
            self.assertEqual(call(private, path)["status"], "200 OK")
            self.assertIn(call(private, path, auth="")["status"].split()[0],
                          ("303", "401"))
        home = call(private, "/")["body"].decode()
        self.assertIn('href="/owner-100yen-review"', home)
        page = call(private, "/owner-100yen-review")["body"].decode()
        js = call(private, "/owner-100yen-review.js")["body"].decode()
        self.assertIn("実購入・実際の払戻ではありません", page)
        self.assertIn("未確定", js)
        self.assertNotIn("innerHTML", js)
        self.assertIn("keiba-nine-owner-server-receipts-v1", js)
        self.assertIn("/api/owner-100yen-verify-receipts", js)
        # Read-only dashboard may inspect signed receipts on this device,
        # but must never edit, replace or remove the saved forecast receipts.
        self.assertNotIn("localStorage.setItem", js)
        self.assertNotIn("localStorage.removeItem", js)
        self.assertIn("fromForecast", js)
        self.assertIn("if(document.visibilityState!=='hidden')$('load').onclick();", js)
        forecast_js=call(private, "/owner-auto-forecast.js")["body"].decode()
        self.assertIn("autoReviewLink", forecast_js)
        self.assertIn("updateReviewLink", forecast_js)

    def test_unconfigured_returns_empty_not_fake_losses(self):
        private = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY":"1",
                              "KEIBA_RENDER_PREVIEW_ONLY":"0"})
        resp = get_day(private)
        self.assertEqual(resp["status"], "200 OK")
        obj = json.loads(resp["body"])
        self.assertFalse(obj["available"])
        self.assertIsNone(obj["review"])
        self.assertFalse(obj["officialFeedConnected"])
        self.assertFalse(obj["captureAuditVerified"])

    def test_snapshots_are_pending_without_an_independent_result_feed(self):
        private = create_app(settings_for(race(), race("京都", 2)))
        resp = get_day(private)
        self.assertEqual(resp["status"], "200 OK")
        data = json.loads(resp["body"])
        self.assertTrue(data["available"])
        self.assertFalse(data["captureAuditVerified"])
        self.assertFalse(data["officialFeedConnected"])
        view = data["review"]
        self.assertEqual(view["reviewedRaces"], 0)
        self.assertEqual(view["pendingRaces"], 2)
        self.assertIsNone(view["roiPercent"])
        self.assertEqual(view["pendingStakeYen"], 600)
        self.assertEqual(view["totalInvestedYen"], 0)
        self.assertFalse(view["actualPurchase"])
        self.assertEqual(len(view["venueBreakdown"]), 2)
        self.assertNotIn(b"999999999", resp["body"])
        self.assertNotIn(b"888888888", resp["body"])
        self.assertNotIn(b"lockedAt", resp["body"])

    def test_mismatch_date_shows_no_races(self):
        private = create_app(settings_for(race()))
        out = get_day(private, day="2026-11-07")
        self.assertEqual(out["status"], "200 OK")
        self.assertFalse(json.loads(out["body"])["available"])

    def test_access_controls_and_query_rejection(self):
        private = create_app(settings_for(race()))
        self.assertEqual(get_day(private, auth="")["status"], "401 Unauthorized")
        self.assertEqual(get_day(private, HTTP_X_KEIBA_REQUEST="")["status"],
                         "403 Forbidden")
        self.assertEqual(get_day(private, HTTP_SEC_FETCH_SITE="cross-site")["status"],
                         "403 Forbidden")
        for query in ("", "date=2026-11-08&date=2026-11-07",
                      "date=2026-11-31", "date=../../secret",
                      "date=2026-11-08&foo=1"):
            with self.subTest(query=query):
                out=call(private, "/api/owner-100yen-review", QUERY_STRING=query)
                self.assertEqual(out["status"], "400 Bad Request")

    def test_invalid_source_or_postrace_lock_fails_closed(self):
        late = race()
        late["lockedAt"] = late["scheduledOffAt"]
        data = settings_for(late)
        for bad in (
            data["KEIBA_OWNER_FROZEN_PREDICTIONS_JSON"],
            "{invalid",
            json.dumps({"schema":SCHEMA, "snapshots":[{
                **race(), "privateSecret": "must_not_leak"}]}),
        ):
            with self.subTest(payload=bad[:20]):
                config = {**data,"KEIBA_OWNER_FROZEN_PREDICTIONS_JSON":bad}
                out=get_day(create_app(config))
                self.assertEqual(out["status"], "503 Service Unavailable")
                self.assertNotIn(b"privateSecret", out["body"])
                self.assertNotIn(b"must_not_leak", out["body"])

    def test_snapshot_strict_shape_and_day_validation(self):
        s = json.dumps({"schema":SCHEMA,"snapshots":[race()]})
        self.assertEqual(len(decode_frozen_snapshots(s,"2026-11-08")),1)
        with self.assertRaises(FrozenSnapshotError):
            decode_frozen_snapshots(s,"2026-99-88")
        with self.assertRaises(FrozenSnapshotError):
            decode_frozen_snapshots(json.dumps({
                "schema":SCHEMA,"snapshots":[race()],
                "officialResults":[]}),"2026-11-08")


if __name__ == "__main__":
    unittest.main()
