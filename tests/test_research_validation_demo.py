"""Synthetic-only validation-demo regression tests; no account/provider IO."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from research_validation_demo import (
    build_validation_review, render_validation_html, _fixture, _invented_outcome,
    DAYS, SPLIT, TOTAL_RACES,
)
from research_planner import plan_race
from research_winner_diagnostics import audit_synthetic_winners
from private_service import create_app
from test_private_service import SETTINGS, call
from research_batch_demo import DEMO_VENUES


class SyntheticValidationDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_validation_review()

    def test_two_chronological_days_and_frozen_test_results(self):
        report = self.report
        self.assertEqual(report["version"], "synthetic-validation-review-1")
        self.assertEqual(report["fixtureRaces"], TOTAL_RACES)
        self.assertEqual(report["recordType"], "test")
        self.assertEqual(report["splitAt"], SPLIT)
        self.assertEqual(report["fictitiousSettledRaces"], 60)
        self.assertEqual(report["development"]["finalRaces"], 30)
        self.assertEqual(report["validation"]["finalRaces"], 30)
        self.assertEqual(len(report["validationDetails"]), 30)
        for flag in ("officialResultsUsed", "fittedWinProbability", "realPredictionReady",
                     "purchaseReady", "publishable"):
            self.assertIs(report[flag], False)
        self.assertEqual(len({r["raceId"] for r in report["validationDetails"]}), 30)
        self.assertEqual(report, build_validation_review())

    def test_no_results_in_prediction_input_or_postcutoff_evidence(self):
        for day in DAYS:
            for venue in DEMO_VENUES:
                for race_no in (1, 2, 7, 11, 12):
                    race = _fixture(day, venue, race_no)
                    before = copy.deepcopy(race)
                    predicted = plan_race(race)
                    first_hash = predicted["snapshotGate"]["snapshotSha256"]
                    result = _invented_outcome(race)
                    self.assertEqual(race, before)
                    self.assertEqual(predicted["snapshotGate"]["snapshotSha256"], first_hash)
                    self.assertFalse(predicted["publishable"])
                    self.assertFalse(predicted["validated"])
                    self.assertTrue(all(
                        e["availableAt"] < race["asOf"]
                        for h in race["horses"]
                        for factor in h["assessments"].values()
                        for e in factor["evidence"]
                    ))
                    if race_no == 7:
                        self.assertIsNone(result)
                    else:
                        self.assertTrue(result["recordType"] == "test")
                        self.assertGreater(result["availableAt"], race["offAt"])

    def test_validation_metrics_do_not_create_real_performance_claim(self):
        report = self.report
        for part in ("development", "validation"):
            s = report[part]
            self.assertLessEqual(s["trifectaHit"], s["finalRaces"])
            self.assertLessEqual(s["winnerRankTop3"], s["finalRaces"])
            self.assertLessEqual(s["winnerInTicketFirst"], s["finalRaces"])
            self.assertLessEqual(s["reviewedButUnticketed"], s["finalRaces"])
            self.assertLessEqual(s["winnerRankBelow3"], s["finalRaces"])
            self.assertGreaterEqual(s["syntheticStake"], 0)
            self.assertGreaterEqual(s["syntheticReturned"], 0)
        html = render_validation_html(report)
        self.assertIn("架空72R", html)
        self.assertIn("総合4位以下", html)
        self.assertIn("1着候補", html)
        self.assertIn("検証用（架空）", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("JRDB_API_KEY", html)
        self.assertNotIn("実際の的中率", html)
        self.assertIn("実際の競馬成績", html)

    def test_cannot_render_as_live_or_real_performance(self):
        for altered in (
            {"recordType": "live"}, {"basis": "real"}, {"realPredictionReady": True},
            {"publishable": True}, {"officialResultsUsed": True},
            {"purchaseReady": True}, {"fixtureRaces": 2},
            {"validationDetails": []},
        ):
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                render_validation_html({**self.report, **altered})

    def test_result_changes_do_not_change_frozen_pre_race_predicted_hashes(self):
        r1 = _fixture(DAYS[0], DEMO_VENUES[0], 2)
        r2 = _fixture(DAYS[1], DEMO_VENUES[0], 2)
        yes = {
            r1["raceId"]: _invented_outcome(r1),
            r2["raceId"]: _invented_outcome(r2),
        }
        no = {
            r1["raceId"]: {**yes[r1["raceId"]], "finish": [8, 7, 6]},
            r2["raceId"]: {**yes[r2["raceId"]], "finish": [8, 7, 6]},
        }
        a = audit_synthetic_winners([r1,r2], yes, SPLIT, min_validation_races=1)
        b = audit_synthetic_winners([r1,r2], no, SPLIT, min_validation_races=1)
        self.assertEqual([x["predictionHash"] for x in a["rows"]],
                         [x["predictionHash"] for x in b["rows"]])

    def test_only_owner_can_open_and_uses_no_provider(self):
        app = create_app(SETTINGS)
        anonymous = call(app, "/research-validation-demo", auth="")
        self.assertEqual(anonymous["status"], "303 See Other")
        self.assertEqual(anonymous["headers"]["Location"], "/login")
        with (patch("private_service.fetch_race_program") as programme,
              patch("private_service.fetch_horse_entries") as entries,
              patch("private_service.fetch_recent_runs") as past):
            response = call(app, "/research-validation-demo")
        self.assertEqual(response["status"], "200 OK")
        self.assertIn("text/html", response["headers"]["Content-Type"])
        self.assertIn("no-store", response["headers"]["Cache-Control"])
        self.assertIn("架空".encode(), response["body"])
        programme.assert_not_called()
        entries.assert_not_called()
        past.assert_not_called()
        home = call(app, "/")
        self.assertIn(b"/research-validation-demo", home["body"])


if __name__ == "__main__":
    unittest.main()
