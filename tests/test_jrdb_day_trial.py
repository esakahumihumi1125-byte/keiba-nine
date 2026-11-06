"""Private day-wide research tests; synthetic source fixtures and no live API."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_day_trial import build_day_trial, VERSION
from jrdb_coverage import CoverageError
from private_service import create_app
from test_private_service import SETTINGS, call
from test_jrdb_one_race_trial import sample_input
from test_private_single_readiness_endpoint import source


PATH = "/api/jrdb/one-day-trial"
QUERY = "date=20261101"


def owner():
    return create_app({**SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
                       "JRDB_API_KEY": "synthetic-api-key",
                       "JRDB_AUTH_KEY": "synthetic-auth-key"})


class DayTrialResearchTests(unittest.TestCase):
    def test_reuses_one_factor_audit_for_all_races(self):
        p, e, t, z = sample_input()
        frozen = copy.deepcopy((p, e, t, z))
        # One-race helper must NOT recompute the expensive factors per race.
        with (patch("jrdb_day_trial.build_training_hints",
                    wraps=__import__("jrdb_day_trial").build_training_hints) as train,
              patch("jrdb_day_trial.build_recent_hints",
                    wraps=__import__("jrdb_day_trial").build_recent_hints) as form,
              patch("jrdb_one_race_trial.build_training_hints") as redundant_a,
              patch("jrdb_one_race_trial.build_recent_hints") as redundant_b):
            result = build_day_trial(p, e, t, z, "20261101")
        train.assert_called_once()
        form.assert_called_once()
        redundant_a.assert_not_called()
        redundant_b.assert_not_called()
        self.assertEqual((p, e, t, z), frozen)
        self.assertEqual(result["version"], VERSION)
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["runnerCount"], 3)
        self.assertEqual(result["twoFactorComparable"], 1)
        self.assertEqual(result["ungraded"], 2)
        self.assertEqual([r["track"] for r in result["races"]], ["東京", "京都"])
        self.assertEqual([r["race"] for r in result["races"]], [1, 1])
        self.assertEqual(result["races"][0]["runners"][0]["horseNumber"], 1)
        self.assertTrue(all(x["researchOnly"] for x in result["races"]))
        for key in ("predictionReady", "overallRankReady", "bettingReady",
                    "officialJraVerified", "autoTicketReady"):
            self.assertIs(result[key], False)
        for raw in ("horse_id", "racekey", "NONPUBLIC", "2328aaa95a05",
                    "oikirisisu", "siagarisisu", "race_back_1",
                    "private_metric", "SECRET-NOT-FOR-API"):
            self.assertNotIn(raw, repr(result))

    def test_missing_histories_not_filled_and_odds_ignored(self):
        p, e, t, z = sample_input()
        z.clear()
        without = build_day_trial(p, e, t, z, "20261101")
        self.assertEqual(without["twoFactorComparable"], 0)
        self.assertEqual(without["ungraded"], 3)
        z.append({"racekey": "05264b01", "racedate": "20261101",
                  "horse_number": "01", "horse_id": "2328aaa95a05",
                  "race_back_1_racedate": "20261004",
                  "race_back_1_order_of_finish": 4,
                  "race_back_1_confirmed_win_odds": 1.01})
        prior = build_day_trial(p, e, t, z, "20261101")
        z[0]["race_back_1_confirmed_win_odds"] = 8000
        self.assertEqual(build_day_trial(p, e, t, z, "20261101"), prior)

    def test_disallows_ambiguity_bad_date_and_extra_venues(self):
        p, e, t, z = sample_input()
        with self.assertRaises(CoverageError):
            build_day_trial(p, e, t, z, "20260230")
        with self.assertRaises(CoverageError):
            build_day_trial(p * 19, e, t, z, "20261101")
        dupe = copy.deepcopy(p)
        dupe[1]["track"] = "東京"
        dupe[1]["race"] = 1
        with self.assertRaises(CoverageError):
            build_day_trial(dupe, e, t, z, "20261101")
        mismatch = copy.deepcopy(p)
        mismatch[1]["racedate"] = "20261102"
        with self.assertRaises(CoverageError):
            build_day_trial(mismatch, e, t, z, "20261101")
        wrong = copy.deepcopy(e)
        wrong[0]["horse_number"] = "02"
        with self.assertRaises(CoverageError):
            build_day_trial(p, wrong, t, z, "20261101")

    def test_empty_programme_does_not_claim_jra_no_races(self):
        result = build_day_trial([], [], [], [], "20261101")
        self.assertEqual(result["raceCount"], 0)
        self.assertIn("断定できません", result["warning"])
        with self.assertRaises(CoverageError):
            build_day_trial([], [{"horse_number": "01"}], [], [], "20261101")


class DayTrialRouteTests(unittest.TestCase):
    def test_not_configured_auth_required_and_no_api_calls(self):
        app = create_app(SETTINGS)
        with patch("private_service.fetch_race_program") as source:
            self.assertEqual(call(app, PATH, QUERY_STRING=QUERY)["status"],
                             "503 Service Unavailable")
            source.assert_not_called()
        app = owner()
        with patch("private_service.fetch_race_program") as source:
            self.assertEqual(call(app, PATH, auth="", QUERY_STRING=QUERY)["status"],
                             "401 Unauthorized")
            self.assertEqual(call(app, PATH, QUERY_STRING=QUERY,
                                  HTTP_X_KEIBA_REQUEST="")["status"], "403 Forbidden")
            for q in ("", "date=20260230", "date=20261101&track=東京",
                      "date=20261101&date=20261102", "date=20990101&extra=1"):
                self.assertEqual(call(app, PATH, QUERY_STRING=q)["status"],
                                 "400 Bad Request")
            source.assert_not_called()

    def test_one_day_uses_four_provider_calls_not_four_per_race(self):
        p, e, t, z, _ = source()
        app = owner()
        with (patch("private_service.fetch_race_program", return_value=p) as p_fetch,
              patch("private_service.fetch_horse_entries", return_value=e) as e_fetch,
              patch("private_service.fetch_training_analysis", return_value=t) as t_fetch,
              patch("private_service.fetch_recent_runs", return_value=z) as z_fetch):
            r = call(app, PATH, QUERY_STRING=QUERY)
        self.assertEqual(r["status"], "200 OK")
        payload = json.loads(r["body"])
        self.assertEqual(payload["raceCount"], 2)
        self.assertEqual(payload["runnerCount"], 3)
        self.assertEqual(payload["version"], VERSION)
        self.assertFalse(payload["predictionReady"])
        self.assertFalse(payload["bettingReady"])
        self.assertIn("no-store", r["headers"]["Cache-Control"])
        for fetch in (p_fetch, e_fetch, t_fetch, z_fetch):
            fetch.assert_called_once_with("20261101")
        for secret in ("horse_id", "racekey", "NONPUBLIC", "synthetic-api-key",
                       "private_metric", "oikirisisu", "race_back_1"):
            self.assertNotIn(secret, repr(payload))

    def test_bad_source_fails_closed_without_publishing(self):
        p, e, t, z, _ = source()
        p[0]["headcount"] = 12
        app = owner()
        with (patch("private_service.fetch_race_program", return_value=p),
              patch("private_service.fetch_horse_entries", return_value=e),
              patch("private_service.fetch_training_analysis", return_value=t),
              patch("private_service.fetch_recent_runs", return_value=z)):
            r = call(app, PATH, QUERY_STRING=QUERY)
        self.assertEqual(r["status"], "502 Bad Gateway")
        self.assertNotIn("races", json.loads(r["body"]))
        self.assertNotIn("horse_number", repr(r["body"]))


if __name__ == "__main__":
    unittest.main()
