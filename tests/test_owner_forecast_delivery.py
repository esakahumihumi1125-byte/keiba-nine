"""Synthetic tests for Render env -> authenticated private 36R forecast viewer."""
import base64
import json
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_forecast_delivery import decode_forecast, validate_owner_forecast, OwnerForecastError, ENV_KEY
from private_service import create_app
from test_private_service import SETTINGS, call


def forecast():
    races = []
    for track in ("東京", "京都", "福島"):
        for race in range(1, 13):
            races.append({
                "track": track, "race": race, "time": "12:00",
                "course": "芝1400", "field": 12,
                "rank": [1, 2, 3, 4, 5, 6, 7],
                "first": [1, 2], "second": [1, 2, 3, 4],
                "third": [1, 2, 3, 4, 5, 6, 7],
                "points": 30, "confidence": 3, "status": "買い候補",
                "headNames": ["架空A", "架空B"],
                "note": "合成レース・研究用の暫定比較。",
                "provisional": True,
                "jraOfficialConfirmed": False,
                "fullFactorVerified": False,
                "rawPrivateIndex": 99,
            })
    return {"schema": "keiba-nine-private-preday-review-v1",
            "date": "2026-11-07", "races": races,
            "providerSecret": "NOT_TO_EXPOSE"}


def pack(data):
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(zlib.compress(text, level=9)).decode().rstrip("=")


class PrivateForecastDeliveryTests(unittest.TestCase):
    def test_owner_only_36r_auto_read_and_no_raw_source(self):
        settings = {**SETTINGS, ENV_KEY: pack(forecast())}
        app = create_app(settings)
        without = call(app, "/api/owner-preday-forecast", auth="")
        self.assertEqual(without["status"], "401 Unauthorized")
        missing_header = call(app, "/api/owner-preday-forecast",
                              HTTP_X_KEIBA_REQUEST="")
        self.assertEqual(missing_header["status"], "403 Forbidden")
        self.assertEqual(call(app, "/api/owner-preday-forecast",
                              method="POST")["status"], "404 Not Found")
        response = call(app, "/api/owner-preday-forecast")
        self.assertEqual(response["status"], "200 OK")
        self.assertIn("no-store", response["headers"]["Cache-Control"])
        d = json.loads(response["body"])
        self.assertTrue(d["available"])
        view = d["forecast"]
        self.assertEqual(view["raceCount"], 36)
        self.assertFalse(view["predictionReady"])
        self.assertFalse(view["officialJraVerified"])
        self.assertFalse(view["purchased"])
        self.assertEqual(view["races"][0]["points"], 30)
        self.assertEqual(view["races"][0]["headNames"], ["架空A", "架空B"])
        self.assertNotIn("providerSecret", str(d))
        self.assertNotIn("rawPrivateIndex", str(d))
        self.assertNotIn("NOT_TO_EXPOSE", str(d))
        self.assertNotIn("JRDB", str(d))

    def test_missing_env_safe_and_invalid_env_closed(self):
        app = create_app(SETTINGS)
        response = call(app, "/api/owner-preday-forecast")
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(json.loads(response["body"]),
                         {"available": False, "forecast": None})
        for value in ("invalid", "a"*20001, pack({
                **forecast(), "races": [{**r, "jraOfficialConfirmed": True}
                                         for r in forecast()["races"]]})):
            broken = create_app({**SETTINGS, ENV_KEY: value})
            response = call(broken, "/api/owner-preday-forecast")
            self.assertEqual(response["status"], "503 Service Unavailable")
            self.assertNotIn("providerSecret", response["body"].decode())

    def test_bad_race_and_formations_rejected(self):
        source = forecast()
        changes = (
            ("repeated race", lambda d: d["races"][1].update(race=1)),
            ("bad rank", lambda d: d["races"][0]["rank"].__setitem__(4, 4)),
            ("wrong counts", lambda d: d["races"][0].update(points=29)),
            ("fake JRA", lambda d: d["races"][0].update(jraOfficialConfirmed=True)),
            ("fake analysis", lambda d: d["races"][0].update(fullFactorVerified=True)),
            ("purchase status", lambda d: d["races"][0].update(status="購入済")),
        )
        for label, change in changes:
            with self.subTest(label=label):
                data = json.loads(json.dumps(source))
                change(data)
                with self.assertRaises(OwnerForecastError):
                    validate_owner_forecast(data)
        allowed = decode_forecast(pack(source))
        self.assertEqual(allowed["date"], source["date"])
        self.assertEqual(len(allowed["races"]), 36)
        self.assertNotIn("rawPrivateIndex", allowed["races"][0])


if __name__ == "__main__":
    unittest.main()
