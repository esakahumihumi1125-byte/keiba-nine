"""Private WSGI operator intake: own choices only, zero provider calls."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import SETTINGS, call


def selection():
    return {
        "recordType": "operator_factor_note", "date": "20261107",
        "track": "京都", "race": 1, "horseNumber": "03",
        "factor": "recent", "state": "noted",
        "source": "operator_observation",
    }


class OperatorFactorEndpointTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SETTINGS)

    def test_note_works_without_jrdb_and_does_not_save(self):
        with (patch("private_service.fetch_race_program") as programme,
              patch("private_service.fetch_horse_entries") as entries,
              patch("private_service.fetch_venue_conditions") as holding):
            out = call(self.app, "/api/operator/factor-note", "POST",
                       data=selection())
        self.assertEqual(out["status"], "200 OK")
        data = json.loads(out["body"])
        self.assertEqual(data["factor"], "recent")
        self.assertFalse(data["saved"])
        self.assertEqual(data["grade"], "未評価")
        self.assertEqual(data["gradedFactorCount"], 0)
        self.assertFalse(data["predictionReady"])
        self.assertFalse(data["bettingReady"])
        self.assertNotIn(b"horseNumber", out["body"])
        for mocked in (programme, entries, holding):
            mocked.assert_not_called()
        self.assertIn("no-store", out["headers"]["Cache-Control"])

    def test_owner_and_same_origin_requirements(self):
        for env in (
            {"HTTP_AUTHORIZATION": ""},
            {"HTTP_X_KEIBA_REQUEST": ""},
            {"HTTP_SEC_FETCH_SITE": "cross-site"},
            {"wsgi.url_scheme": "http"},
        ):
            with self.subTest(env=env):
                response = call(self.app, "/api/operator/factor-note", "POST",
                                data=selection(), **env)
                self.assertNotEqual(response["status"], "200 OK")

    def test_bad_payload_rejected_without_paid_lookups(self):
        with patch("private_service.fetch_race_program") as paid:
            for item in (
                {**selection(), "race": True},
                {**selection(), "source": "paid_jrdb_api"},
                {**selection(), "state": "S"},
                {**selection(), "additionalHorseName": "PAID-HORSE"},
                {**selection(), "factor": "odds"},
            ):
                response = call(self.app, "/api/operator/factor-note", "POST",
                                data=item)
                self.assertTrue(response["status"].startswith("400"))
                self.assertNotIn(b"PAID-HORSE", response["body"])
            for changes in (
                {"QUERY_STRING": "debug=1"},
                {"CONTENT_TYPE": "text/plain"},
                {"CONTENT_LENGTH": "1000"},
            ):
                response = call(self.app, "/api/operator/factor-note", "POST",
                                data=selection(), **changes)
                self.assertTrue(response["status"].startswith("400"))
        paid.assert_not_called()

    def test_form_is_owner_only_and_does_not_post_automatically(self):
        html = call(self.app, "/")["body"].decode()
        js = call(self.app, "/app.js")["body"].decode()
        for item in ('id="operatorFactorPanel"', 'id="noteTrack"',
                     'id="noteRace"', 'id="noteHorse"', 'id="noteFactor"',
                     'id="noteState"', 'id="noteSource"', 'id="noteRun"',
                     'id="noteResult"'):
            self.assertIn(item, html)
        self.assertIn("el('noteRun').onclick=async()=>", js)
        self.assertNotIn("innerHTML", js)
        self.assertIn("operatorNotes", js)


if __name__ == "__main__":
    unittest.main()
