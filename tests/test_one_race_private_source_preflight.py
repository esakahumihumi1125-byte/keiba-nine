"""Single real-data RACE source gate: fake-only HTTP, no billed reads."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from private_service import create_app
from test_private_service import AUTH, SETTINGS, call
from test_jrdb_training_hypothesis import setup as training_fixture
from test_jrdb_recent_hypothesis import fixture as history_fixture


class OneRaceSourceGuardTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            **SETTINGS,
            "JRDB_PRIVATE_ENABLED": "1",
            "JRDB_API_KEY": "DONT_PRINT_SYNTHETIC_TEST_KEY",
            "JRDB_AUTH_KEY": "DONT_PRINT_SYNTHETIC_TEST_AUTH",
            "KEIBA_RENDER_PRIVATE_ONLY": "1",
            "KEIBA_RENDER_PREVIEW_ONLY": "0",
        })

    def test_unpublished_day_makes_one_read_not_four(self):
        with (patch("private_service.fetch_race_program", return_value=[]) as programme,
              patch("private_service.fetch_horse_entries") as entries,
              patch("private_service.fetch_training_analysis") as training,
              patch("private_service.fetch_recent_runs") as recent):
            result = call(
                self.app, "/api/jrdb/one-race-trial",
                QUERY_STRING="date=20261121&track=%E6%9D%B1%E4%BA%AC&race=1",
            )
        self.assertEqual(result["status"], "409 Conflict")
        body = json.loads(result["body"])
        self.assertEqual(body["status"], "one_race_programme_not_observed")
        self.assertEqual(body["sourceReadsMade"], 1)
        self.assertFalse(body["officialJraVerified"])
        self.assertFalse(body["formalTenFactorReady"])
        self.assertFalse(body["bettingReady"])
        self.assertIn("配信前", body["error"])
        programme.assert_called_once_with("20261121")
        entries.assert_not_called()
        training.assert_not_called()
        recent.assert_not_called()

    def test_nonmatching_venue_or_race_does_not_read_more_sources(self):
        programme_rows, _, _ = training_fixture()
        with (patch("private_service.fetch_race_program", return_value=programme_rows)
              as provider,
              patch("private_service.fetch_horse_entries") as entries,
              patch("private_service.fetch_training_analysis") as training,
              patch("private_service.fetch_recent_runs") as recent):
            result = call(
                self.app, "/api/jrdb/one-race-trial",
                QUERY_STRING="date=20261101&track=%E6%9D%B1%E4%BA%AC&race=12",
            )
        self.assertEqual(result["status"], "409 Conflict")
        self.assertEqual(json.loads(result["body"])["sourceReadsMade"], 1)
        provider.assert_called_once()
        entries.assert_not_called()
        training.assert_not_called()
        recent.assert_not_called()

    def test_present_one_race_still_uses_real_four_source_contract(self):
        p, e, t = training_fixture()
        _, _, recent_rows = history_fixture()
        with (patch("private_service.fetch_race_program", return_value=p)
              as programme,
              patch("private_service.fetch_horse_entries", return_value=e)
              as entries,
              patch("private_service.fetch_training_analysis", return_value=t)
              as training,
              patch("private_service.fetch_recent_runs", return_value=recent_rows)
              as recent):
            result = call(
                self.app, "/api/jrdb/one-race-trial",
                QUERY_STRING="date=20261101&track=%E6%9D%B1%E4%BA%AC&race=1",
            )
        self.assertEqual(result["status"], "200 OK")
        body = json.loads(result["body"])
        self.assertEqual(body["track"], "東京")
        self.assertEqual(body["race"], 1)
        self.assertGreater(body["runnersObserved"], 0)
        self.assertFalse(body["predictionReady"])
        self.assertFalse(body["bettingReady"])
        for func in (programme, entries, training, recent):
            func.assert_called_once()
        for secret in ("DONT_PRINT_SYNTHETIC_TEST_KEY",
                       "DONT_PRINT_SYNTHETIC_TEST_AUTH",
                       "SECRET-PAID-HORSE", "horse_id", "racekey"):
            self.assertNotIn(secret, result["body"].decode())

    def test_unauthed_or_invalid_request_does_not_bill_sources(self):
        with (patch("private_service.fetch_race_program") as programme,
              patch("private_service.fetch_horse_entries") as entries):
            unauth = call(
                self.app, "/api/jrdb/one-race-trial",
                QUERY_STRING="date=20261121&track=%E6%9D%B1%E4%BA%AC&race=1",
                auth="",
            )
            malformed = call(
                self.app, "/api/jrdb/one-race-trial",
                QUERY_STRING="date=20261121&track=invalid&race=1",
            )
            self.assertEqual(unauth["status"], "401 Unauthorized")
            self.assertEqual(malformed["status"], "400 Bad Request")
            programme.assert_not_called()
            entries.assert_not_called()


if __name__ == "__main__":
    unittest.main()
