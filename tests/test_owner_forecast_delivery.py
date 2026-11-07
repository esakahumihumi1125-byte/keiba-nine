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

    def test_compact_36r_nonlicensed_server_configuration(self):
        source = forecast()
        fields = []
        for race in source["races"]:
            fields.append([race["time"], race["course"], race["field"],
                           race["rank"], len(race["first"]), len(race["second"]),
                           len(race["third"]), race["confidence"], race["headNames"]])
        packed = {"format": "owner-compact-36r-v1",
                  "date": "2026-11-07", "races": fields}
        response = call(create_app({**SETTINGS, ENV_KEY: pack(packed)}),
                        "/api/owner-preday-forecast")
        self.assertEqual(response["status"], "200 OK")
        result = json.loads(response["body"])["forecast"]
        self.assertEqual(result["raceCount"], 36)
        self.assertEqual(result["races"][0]["track"], "東京")
        self.assertEqual(result["races"][0]["race"], 1)
        self.assertEqual(result["races"][12]["track"], "京都")
        self.assertEqual(result["races"][24]["track"], "福島")
        self.assertEqual(result["races"][35]["race"], 12)
        self.assertEqual(result["races"][0]["points"], 30)
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["purchased"])
        malformed = dict(packed)
        malformed["races"] = [*fields[:-1]]
        bad = call(create_app({**SETTINGS, ENV_KEY: pack(malformed)}),
                   "/api/owner-preday-forecast")
        self.assertEqual(bad["status"], "503 Service Unavailable")

    def test_tomorrow_six_horses_and_three_win_candidates(self):
        raw = forecast()
        raw["date"] = "2026-11-08"
        six = raw["races"][14]  # Kyoto 3R
        self.assertEqual((six["track"], six["race"]), ("京都", 3))
        six.update(field=6, rank=[4, 6, 1, 3, 2, 5],
                   first=[4], second=[4, 6, 1, 3], third=[4, 6, 1, 3, 2, 5],
                   points=12, headNames=["架空堅実軸"])
        crowded = raw["races"][13]
        crowded.update(rank=[7, 4, 2, 1, 9, 6, 3], first=[7, 4, 2],
                       second=[7, 4, 2, 1], third=[7, 4, 2, 1, 9, 6, 3],
                       points=45, headNames=["架空先行", "架空差し", "架空大穴"])
        validated = validate_owner_forecast(raw)
        self.assertEqual(validated["races"][14]["points"],12)
        self.assertEqual(len(validated["races"][13]["headNames"]),3)
        fields=[]
        for r in raw["races"]:
            fields.append([r["time"],r["course"],r["field"],r["rank"],len(r["first"]),
                           len(r["second"]),len(r["third"]),r["confidence"],r["headNames"],
                           "堅いレースは点数を減らす。混戦は3〜5番手の勝ち切りを再点検。"])
        snapshot={"format":"owner-compact-36r-v2","date":"2026-11-08","races":fields}
        result=decode_forecast(pack(snapshot))
        self.assertEqual(result["date"],"2026-11-08")
        self.assertEqual(result["races"][14]["field"],6)
        self.assertEqual(result["races"][13]["points"],45)
        self.assertIn("点数を減らす",result["races"][14]["note"])
        self.assertFalse(result["officialJraVerified"])

    def test_private_plain_json_preferred_and_same_origin_protected(self):
        source=forecast()
        source["date"]="2026-11-08"
        packed={"format":"owner-compact-36r-v2","date":source["date"],
            "races":[[r["time"],r["course"],r["field"],r["rank"],
                      len(r["first"]),len(r["second"]),len(r["third"]),
                      r["confidence"],r["headNames"],"勝負度と買い目を調整する暫定案。"]
                     for r in source["races"]]}
        settings={**SETTINGS,"KEIBA_OWNER_FORECAST_JSON":json.dumps(packed,ensure_ascii=False),
                  ENV_KEY:pack(forecast())}
        app=create_app(settings)
        r=call(app,"/api/owner-preday-forecast")
        self.assertEqual(r["status"],"200 OK")
        self.assertEqual(json.loads(r["body"])["forecast"]["date"],"2026-11-08")
        self.assertEqual(call(app,"/api/owner-preday-forecast",auth="")["status"],"401 Unauthorized")
        self.assertEqual(call(app,"/api/owner-preday-forecast",
                              HTTP_X_KEIBA_REQUEST="")["status"],"403 Forbidden")
        settings["KEIBA_OWNER_FORECAST_JSON"]="bad-json"
        self.assertEqual(call(create_app(settings),"/api/owner-preday-forecast")["status"],
                         "503 Service Unavailable")

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
