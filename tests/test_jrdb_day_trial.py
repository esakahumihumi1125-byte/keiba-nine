"""Private day-wide research tests; synthetic source fixtures and no live API."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_day_trial import build_day_trial, VERSION
from jrdb_program_preview import normalize_program_rows
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
        row = result["races"][0]["factorCoverage"]
        self.assertEqual(row["observedRunnerCount"], 2)
        self.assertEqual(row["verifiedAbilityFactors"], 0)
        self.assertTrue(row["notOverallGrades"])
        self.assertEqual(len(row["materialCountByFactor"]), 10)
        self.assertEqual(row["materialCountByFactor"]["training"], 2)
        self.assertEqual(row["materialCountByFactor"]["recent"], 1)
        self.assertEqual(row["materialCountByFactor"]["pace"], 0)
        self.assertEqual(row["materialCountByFactor"]["rotation"], 1)
        self.assertEqual(row["materialCountByFactor"]["course_distance"], 0)
        self.assertEqual(row["materialCountByFactor"]["ground"], 0)
        self.assertEqual(row["uncheckedFactors"], ["course_distance", "ground"])
        self.assertTrue(all(v == 0 for v in result["races"][1]["factorCoverage"]["materialCountByFactor"].values()))
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

    def test_existing_provider_fields_enrich_material_presence_not_predictions(self):
        p, e, t, z = sample_input()
        e[0].update(sire_name="SYNTHETIC-SIRE", mare_sire_name="SYNTHETIC-MARESIRE",
                    bracket_number="2", weight_to_carry="55.0",
                    jockey_name="SYNTHETIC-JOCKEY", trainer_name="SYNTHETIC-TRAINER",
                    bodytype="222222")
        z[0].update(race_back_1_corner4_order=2, race_back_2_corner4_order=3)
        report = build_day_trial(p, e, t, z, "20261101")
        coverage = report["races"][0]["factorCoverage"]
        observed = coverage["materialCountByFactor"]
        self.assertEqual(observed["pedigree"], 1)
        self.assertEqual(observed["draw_weight"], 1)
        self.assertEqual(observed["jockey_stable"], 1)
        self.assertEqual(observed["body_condition"], 1)
        self.assertEqual(observed["pace"], 1)
        self.assertEqual(observed["rotation"], 1)
        self.assertEqual(coverage["verifiedAbilityFactors"], 0)
        self.assertFalse(report["predictionReady"])
        self.assertFalse(report["bettingReady"])
        for leaked in ("SYNTHETIC-SIRE", "SYNTHETIC-JOCKEY", "222222",
                       "55.0", "horse_id", "racekey"):
            self.assertNotIn(leaked, repr(report))

    def test_venue_context_is_separate_from_horse_ability(self):
        raw, entries, training, previous, venue = source()
        programme = normalize_program_rows(raw, "20261101")
        before = copy.deepcopy((programme, entries, training, previous, venue))
        day = build_day_trial(programme, entries, training, previous,
                              "20261101", venue)
        self.assertEqual(day["courseInfoPresentCount"], 2)
        self.assertEqual(day["goingAvailableCount"], 1)
        tokyo, kyoto = day["races"]
        self.assertEqual(tokyo["raceContext"]["surface"], "芝")
        self.assertEqual(tokyo["raceContext"]["distance_m"], 1600)
        self.assertEqual(tokyo["raceContext"]["turn"], "左")
        self.assertEqual(tokyo["raceContext"]["going"], "重")
        self.assertTrue(tokyo["raceContext"]["goingAvailable"])
        self.assertEqual(kyoto["raceContext"]["going"], "未確認")
        self.assertFalse(kyoto["raceContext"]["conditionSnapshotPresent"])
        for row in day["races"]:
            self.assertFalse(row["raceContext"]["officialJraVerified"])
            self.assertFalse(row["raceContext"]["horseCourseSuitabilityAssessed"])
            self.assertFalse(row["raceContext"]["horseGoingSuitabilityAssessed"])
            self.assertFalse(row["raceContext"]["raceConditionsVerified"])
            self.assertEqual(row["factorCoverage"]["materialCountByFactor"]["course_distance"], 0)
            self.assertEqual(row["factorCoverage"]["materialCountByFactor"]["ground"], 0)
        self.assertEqual((programme, entries, training, previous, venue), before)
        for secret in ("LICENSED-GOING-PRIVATE", "holdingkey", "racekey",
                       "private_notes", "updated_at"):
            self.assertNotIn(secret, repr(day))

    def test_invalid_venue_conditions_rejected_without_fabricating_going(self):
        raw, entries, training, previous, venue = source()
        programme = normalize_program_rows(raw, "20261101")
        for bad in ({"turf_condition_cd":"5"},
                    {"racedate":"20261102"},
                    {"holdingkey":"invalid"},
                    {"updated_at":"not-a-timestamp"}):
            with self.subTest(bad=bad):
                broken = copy.deepcopy(venue)
                broken[0].update(bad)
                with self.assertRaises(ValueError):
                    build_day_trial(programme, entries, training, previous,
                                    "20261101", broken)
        with self.assertRaises(ValueError):
            build_day_trial(programme, entries, training, previous,
                            "20261101", venue+copy.deepcopy(venue))
        unreported = build_day_trial(programme, entries, training, previous,
                                     "20261101", [])
        self.assertEqual(unreported["goingAvailableCount"], 0)
        self.assertTrue(all(r["raceContext"]["going"] == "未確認"
                            for r in unreported["races"]))

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

    def test_one_day_uses_five_provider_calls_not_five_per_race(self):
        p, e, t, z, holding = source()
        app = owner()
        with (patch("private_service.fetch_race_program", return_value=p) as p_fetch,
              patch("private_service.fetch_horse_entries", return_value=e) as e_fetch,
              patch("private_service.fetch_training_analysis", return_value=t) as t_fetch,
              patch("private_service.fetch_recent_runs", return_value=z) as z_fetch,
              patch("private_service.fetch_venue_conditions", return_value=holding) as going_fetch):
            r = call(app, PATH, QUERY_STRING=QUERY)
        self.assertEqual(r["status"], "200 OK")
        payload = json.loads(r["body"])
        self.assertEqual(payload["raceCount"], 2)
        self.assertEqual(payload["runnerCount"], 3)
        self.assertEqual(payload["version"], VERSION)
        self.assertEqual(payload["courseInfoPresentCount"], 2)
        self.assertEqual(payload["goingAvailableCount"], 1)
        self.assertEqual(payload["races"][0]["raceContext"]["going"], "重")
        self.assertFalse(payload["races"][0]["raceContext"]["raceConditionsVerified"])
        self.assertFalse(payload["predictionReady"])
        self.assertFalse(payload["bettingReady"])
        self.assertIn("no-store", r["headers"]["Cache-Control"])
        for fetch in (p_fetch, e_fetch, t_fetch, z_fetch, going_fetch):
            fetch.assert_called_once_with("20261101")
        for secret in ("horse_id", "racekey", "NONPUBLIC", "synthetic-api-key",
                       "private_metric", "oikirisisu", "race_back_1"):
            self.assertNotIn(secret, repr(payload))

    def test_bad_source_fails_closed_without_publishing(self):
        p, e, t, z, holding = source()
        p[0]["headcount"] = 12
        app = owner()
        with (patch("private_service.fetch_race_program", return_value=p),
              patch("private_service.fetch_horse_entries", return_value=e),
              patch("private_service.fetch_training_analysis", return_value=t),
              patch("private_service.fetch_recent_runs", return_value=z),
              patch("private_service.fetch_venue_conditions", return_value=holding)):
            r = call(app, PATH, QUERY_STRING=QUERY)
        self.assertEqual(r["status"], "502 Bad Gateway")
        self.assertNotIn("races", json.loads(r["body"]))
        self.assertNotIn("horse_number", repr(r["body"]))


if __name__ == "__main__":
    unittest.main()
