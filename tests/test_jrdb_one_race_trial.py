"""Synthetic-only JRDB 2-factor pilot and owner-authenticated route tests."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_one_race_trial import build_one_race_trial
from jrdb_coverage import CoverageError
from private_service import create_app
from test_private_service import SETTINGS, call
from test_jrdb_evidence_readiness import sample
from test_private_single_readiness_endpoint import source


def sample_input():
    p, e, t, z = sample()
    t[0].update(oikirisisu=78, siagarisisu=80)
    t[1].update(oikirisisu=65, siagarisisu=63)
    z[0].update(
        race_back_1_idm=71,
        race_back_2_racedate="20260920",
        race_back_2_order_of_finish=2,
        race_back_2_idm=62,
    )
    return p, e, t, z


class JRDBOneRaceTrialTests(unittest.TestCase):
    def test_two_factor_sorted_and_no_bets_or_raw_source(self):
        p, e, t, z = sample_input()
        result = build_one_race_trial(p, e, t, z, "20261101", "東京", 1)
        self.assertEqual(result["version"], "owner-single-race-two-factor-trial-1")
        self.assertEqual(result["runnersObserved"], 2)
        self.assertEqual(result["twoFactorComparable"], 1)
        self.assertEqual(result["ungraded"], 1)
        self.assertEqual(result["runners"][0], {
            "horseNumber": 1, "trainingGrade": "S", "recentGrade": "A",
            "twoFactorPoints": 7, "provisionalOnly": True, "comparisonRank": 1,
            "missingReasons": [],
        })
        self.assertIsNone(result["runners"][1]["comparisonRank"])
        self.assertIsNone(result["runners"][1]["twoFactorPoints"])
        for key in ("predictionReady", "bettingReady", "autoTicketReady",
                    "overallRankReady", "officialJraVerified"):
            self.assertIs(result[key], False)
        self.assertIs(result["researchOnly"], True)
        for forbidden in ("horse_id", "racekey", "private_metric",
                          "SECRET-NOT-FOR-API", "2328aaa95a05", "NONPUBLIC",
                          "siagarisisu", "oikirisisu", "confirmed_win_odds"):
            self.assertNotIn(forbidden, repr(result))

    def test_refuses_to_infer_missing_histories(self):
        p, e, t, z = sample_input()
        z.clear()
        result = build_one_race_trial(p, e, t, z, "20261101", "東京", 1)
        self.assertEqual(result["twoFactorComparable"], 0)
        self.assertTrue(all(row["twoFactorPoints"] is None
                            for row in result["runners"]))
        self.assertFalse(result["predictionReady"])

    def test_rejects_bad_coordinates_and_conflicting_identity(self):
        p, e, t, z = sample_input()
        for args in (("20261101", "東京", 0), ("20261101", "東京", 13),
                     ("20261101", "大阪", 1), ("20260230", "東京", 1),
                     ("20261101", "中山", 1)):
            with self.subTest(args=args), self.assertRaises(CoverageError):
                build_one_race_trial(p, e, t, z, *args)
        broken = copy.deepcopy(t)
        broken[0]["horse_number"] = "02"
        with self.assertRaises(CoverageError):
            build_one_race_trial(p, e, broken, z, "20261101", "東京", 1)
        p[0]["headcount"] = 3
        with self.assertRaises(CoverageError):
            build_one_race_trial(p, e, t, z, "20261101", "東京", 1)

    def test_no_mutations_and_odds_ignored(self):
        p, e, t, z = sample_input()
        before = copy.deepcopy((p, e, t, z))
        result = build_one_race_trial(p, e, t, z, "20261101", "東京", 1)
        self.assertEqual((p, e, t, z), before)
        z[0]["race_back_1_confirmed_win_odds"] = 900
        self.assertEqual(build_one_race_trial(p, e, t, z, "20261101", "東京", 1),
                         result)


PATH = "/api/jrdb/one-race-trial"
QUERY = "date=20261101&track=%E6%9D%B1%E4%BA%AC&race=1"


class JRDBTrialRouteTests(unittest.TestCase):
    def test_beta_key_missing_disables_network(self):
        app = create_app(SETTINGS)
        with patch("private_service.fetch_race_program") as spy:
            self.assertEqual(call(app, PATH, QUERY_STRING=QUERY)["status"],
                             "503 Service Unavailable")
            spy.assert_not_called()
        root = call(app, "/")["body"].decode("utf-8")
        self.assertIn('href="/owner-auto-trial"', root)

    def test_authorization_and_bad_input_rejected_before_provider(self):
        app = create_app({**SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
                          "JRDB_API_KEY": "synthetic-api", "JRDB_AUTH_KEY": "synthetic-auth"})
        with patch("private_service.fetch_race_program") as spy:
            self.assertEqual(call(app, PATH, auth="", QUERY_STRING=QUERY)["status"],
                             "401 Unauthorized")
            self.assertEqual(call(app, PATH, QUERY_STRING=QUERY,
                                  HTTP_X_KEIBA_REQUEST="")["status"], "403 Forbidden")
            for query in ("", "date=20261101&track=東京", "date=20260230&track=東京&race=1",
                          "date=20261101&track=京都&race=02",
                          "date=20261101&track=東京&race=1&token=x",
                          "date=20261101&track=東京&race=1&race=2"):
                self.assertEqual(call(app, PATH, QUERY_STRING=query)["status"],
                                 "400 Bad Request")
            spy.assert_not_called()

    def test_single_race_four_source_reads_and_no_provider_payload(self):
        raw, entries, t, z, _ = source()
        app = create_app({**SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
                          "JRDB_API_KEY": "synthetic-api", "JRDB_AUTH_KEY": "synthetic-auth"})
        with (patch("private_service.fetch_race_program", return_value=raw) as program,
              patch("private_service.fetch_horse_entries", return_value=entries) as horse,
              patch("private_service.fetch_training_analysis", return_value=t) as training,
              patch("private_service.fetch_recent_runs", return_value=z) as recent):
            result = call(app, PATH, QUERY_STRING=QUERY)
        self.assertEqual(result["status"], "200 OK")
        data = json.loads(result["body"])
        self.assertEqual(data["version"], "owner-single-race-two-factor-trial-1")
        self.assertFalse(data["predictionReady"])
        self.assertFalse(data["bettingReady"])
        self.assertEqual(data["track"], "東京")
        self.assertEqual(data["race"], 1)
        self.assertEqual(data["runnersObserved"], 2)
        self.assertIn("no-store", result["headers"]["Cache-Control"])
        for fetch in (program, horse, training, recent):
            fetch.assert_called_once_with("20261101")
        self.assertNotIn("horse_id", repr(data))
        self.assertNotIn("racekey", repr(data))
        self.assertNotIn("NONPUBLIC", repr(data))

    def test_authenticated_html_and_scripts(self):
        app = create_app(SETTINGS)
        for path, term in (
            ("/owner-auto-trial", "開催日・全Rの自動試算"),
            ("/owner-auto-trial.js", "owner-single-race-two-factor-trial-1"),
            ("/owner-auto-trial.css", ".trial-horse"),
        ):
            with self.subTest(path=path):
                reply = call(app, path)
                self.assertEqual(reply["status"], "200 OK")
                self.assertIn(term, reply["body"].decode("utf-8"))
                self.assertIn("no-store", reply["headers"]["Cache-Control"])
                denied = call(app, path, auth="")
                self.assertIn(denied["status"], ("303 See Other", "401 Unauthorized"))


if __name__ == "__main__":
    unittest.main()
