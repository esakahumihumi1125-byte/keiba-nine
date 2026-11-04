"""WSGI-level tests for owner-only single-request selected-race readiness."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import SETTINGS, call
from test_jrdb_evidence_readiness import sample
from test_jrdb_race_day_gates import fixture


def source():
    raw_programme = [
        {"racekey":"05264b01","racedate":"20261101","post_time":"1000",
         "track_type":"1","distance":"1600","turn_cd":"2","headcount":2},
        {"racekey":"08264b01","racedate":"20261101","post_time":"1005",
         "track_type":"2","distance":"1800","turn_cd":"1","headcount":1},
    ]
    _, entries, holding = fixture()
    _, _, training, recent = sample()
    return raw_programme, entries, training, recent, holding


def authorized():
    return create_app({**SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
                       "JRDB_API_KEY":"fake-private-test-key",
                       "JRDB_AUTH_KEY":"fake-private-test-auth"})


PATH = "/api/jrdb/selected-readiness"
QUERY = "date=20261101&track=%E6%9D%B1%E4%BA%AC&race=1"


class PrivateSingleReadinessServiceTests(unittest.TestCase):
    def test_off_by_default_and_does_not_call_any_provider(self):
        app=create_app(SETTINGS)
        with patch("private_service.fetch_race_program") as fetch:
            result=call(app,PATH,QUERY_STRING=QUERY)
            self.assertEqual(result["status"],"503 Service Unavailable")
            fetch.assert_not_called()

    def test_user_header_and_basic_auth_required(self):
        app=authorized()
        with patch("private_service.fetch_race_program") as fetch:
            self.assertEqual(call(app,PATH,auth="",QUERY_STRING=QUERY)["status"],
                             "401 Unauthorized")
            self.assertEqual(call(app,PATH,QUERY_STRING=QUERY,
                                  HTTP_X_KEIBA_REQUEST="")["status"],
                             "403 Forbidden")
            fetch.assert_not_called()

    def test_bad_coordinates_rejected_before_any_source_request(self):
        app=authorized()
        invalid=[
            "", "date=20261101&track=東京",
            "date=20261101&track=東京&race=1&race=2",
            "date=20261101&track=東京&race=01",
            "date=20261101&track=東京&race=13",
            "date=20261101&track=大阪&race=1",
            "date=20260230&track=東京&race=1",
            "date=20261101&track=東京&race=1&token=extra",
        ]
        with patch("private_service.fetch_race_program") as fetch:
            for query in invalid:
                with self.subTest(query=query):
                    reply=call(app,PATH,QUERY_STRING=query)
                    self.assertEqual(reply["status"],"400 Bad Request")
            fetch.assert_not_called()

    def test_one_click_retrieves_five_sources_once_and_redacts(self):
        p,e,t,z,h=source()
        app=authorized()
        with (patch("private_service.fetch_race_program",return_value=p) as program,
              patch("private_service.fetch_horse_entries",return_value=e) as entries,
              patch("private_service.fetch_training_analysis",return_value=t) as training,
              patch("private_service.fetch_recent_runs",return_value=z) as previous,
              patch("private_service.fetch_venue_conditions",return_value=h) as holding,
              patch("private_service._now_in_jst",return_value="2026-11-01T09:30:00+09:00")):
            reply=call(app,PATH,QUERY_STRING=QUERY)
            self.assertEqual(reply["status"],"200 OK")
            payload=json.loads(reply["body"])
            self.assertEqual((payload["track"],payload["race"]),("東京",1))
            self.assertEqual(payload["observedEntries"],2)
            self.assertEqual(payload["trainingUnaccounted"],0)
            self.assertEqual(payload["providerWithdrawnCount"],1)
            self.assertFalse(payload["predictionReady"])
            self.assertFalse(payload["bettingReady"])
            self.assertFalse(payload["officialJraFinalVerification"])
            self.assertEqual(payload["version"],"selected-race-readiness-2")
            pair = payload["factorResearch"]
            self.assertTrue(pair["experimental"])
            self.assertEqual(pair["remainingFactors"],8)
            self.assertEqual(pair["bothGraded"] + pair["trainingOnly"] +
                             pair["recentOnly"] + pair["neither"],2)
            self.assertFalse(pair["predictionReady"])
            self.assertNotIn("races",payload)
            self.assertIn("no-store",reply["headers"]["Cache-Control"])
            for item in (program,entries,training,previous,holding):
                item.assert_called_once_with("20261101")
            for word in ("racekey","horse_id","horse_number","NONPUBLIC",
                         "LICENSED-HORSE-PRIVATE","2328aaa95a05",
                         "fake-private-test-key","fake-private-test-auth"):
                self.assertNotIn(word,repr(payload))

    def test_wrong_race_is_error_not_another_races_data(self):
        p,e,t,z,h=source()
        app=authorized()
        with (patch("private_service.fetch_race_program",return_value=p),
              patch("private_service.fetch_horse_entries",return_value=e),
              patch("private_service.fetch_training_analysis",return_value=t),
              patch("private_service.fetch_recent_runs",return_value=z),
              patch("private_service.fetch_venue_conditions",return_value=h)):
            reply=call(app,PATH,
                QUERY_STRING="date=20261101&track=%E6%9D%B1%E4%BA%AC&race=2")
            self.assertEqual(reply["status"],"502 Bad Gateway")
            self.assertNotIn(b"NONPUBLIC",reply["body"])

    def test_github_actions_cannot_enable_provider_access(self):
        app=create_app({**SETTINGS,"JRDB_PRIVATE_ENABLED":"1",
                        "JRDB_API_KEY":"test-key","JRDB_AUTH_KEY":"test-auth",
                        "GITHUB_ACTIONS":"true"})
        with patch("private_service.fetch_race_program") as fetch:
            self.assertEqual(call(app,PATH,QUERY_STRING=QUERY)["status"],
                             "503 Service Unavailable")
            fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
