"""Synthetic-only regression tests of winner selection diagnosis."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from research_winner_diagnostics import audit_synthetic_winners
from test_research_pipeline import sample, outcome

SPLIT = "2026-10-21T00:00:00+09:00"


class WinnerDiagnosticsTests(unittest.TestCase):
    def test_rank_and_first_candidate_misses_are_separate(self):
        first = sample()
        second = sample("fixture-next", "2026-10-22")
        report = audit_synthetic_winners(
            [second, first], {
                first["raceId"]: outcome(first),
                second["raceId"]: outcome(second, [8, 7, 6]),
            }, SPLIT)
        self.assertEqual(report["version"], "synthetic-winner-review-1")
        self.assertEqual(report["development"]["finalRaces"], 1)
        self.assertEqual(report["validation"]["finalRaces"], 1)
        self.assertEqual(report["summary"]["winnerRank1"], 1)
        self.assertEqual(report["summary"]["winnerRankBelow3"], 1)
        self.assertEqual(report["summary"]["winnerInWinReview"], 1)
        self.assertEqual(report["summary"]["winnerInTicketFirst"], 1)
        self.assertEqual(report["summary"]["trifectaHit"], 1)
        self.assertEqual(report["validation"]["winnerGrades"]["B"], 1)
        self.assertEqual(report["rows"][1]["winnerRank"], 5)
        self.assertFalse(report["rows"][1]["winnerInWinReview"])
        self.assertFalse(report["approvedForLive"])

    def test_reviewed_winner_not_ticketed_when_another_runner_incomplete(self):
        race = sample()
        race["horses"][-1]["assessments"].pop("recent")
        result = audit_synthetic_winners(
            [race], {race["raceId"]: outcome(race, [1, 3, 4])}, SPLIT)
        self.assertEqual(result["summary"]["reviewedButUnticketed"], 1)
        self.assertEqual(result["summary"]["winnerInWinReview"], 1)
        self.assertEqual(result["summary"]["winnerInTicketFirst"], 0)
        self.assertEqual(result["summary"]["syntheticStake"], 0)
        self.assertIsNone(result["summary"]["syntheticRoi"])

    def test_unranked_winner_is_unknown_not_rank_below_three(self):
        race = sample()
        race["horses"][0]["assessments"].pop("ground")
        result = audit_synthetic_winners(
            [race], {race["raceId"]: outcome(race, [1, 3, 4])}, SPLIT)
        self.assertEqual(result["summary"]["winnerUnranked"], 1)
        self.assertEqual(result["summary"]["winnerRankBelow3"], 0)
        self.assertEqual(result["summary"]["winnerGrades"]["未評価"], 1)

    def test_unsettled_excluded_from_win_rate_denominator(self):
        first = sample()
        second = sample("fixture-next", "2026-10-22")
        cancelled = {**outcome(first), "status": "cancelled"}
        result = audit_synthetic_winners(
            [first, second], {first["raceId"]: cancelled}, SPLIT)
        self.assertEqual(result["summary"]["finalRaces"], 0)
        self.assertEqual(result["summary"]["winnerInWinReview"], 0)
        self.assertFalse(result["validationSampleMeetsMinimum"])

    def test_sample_threshold_does_not_make_synthetic_data_live(self):
        race = sample("fixture-next", "2026-10-22")
        result = audit_synthetic_winners(
            [race], {race["raceId"]: outcome(race)}, SPLIT,
            min_validation_races=1)
        self.assertTrue(result["validationSampleMeetsMinimum"])
        self.assertFalse(result["calibrated"])
        self.assertFalse(result["approvedForPublication"])
        self.assertFalse(result["approvedForBetting"])

    def test_invalid_result_on_held_race_is_not_ignored(self):
        race = sample()
        race["horses"][0]["assessments"].pop("recent")
        original = outcome(race, [1, 3, 4])
        for altered in (
            {"recordType": "live"},
            {"availableAt": race["asOf"]},
            {"finish": [1, 1, 2]},
            {"trifectaPayout": True},
            {"deadHeat": True},
        ):
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                audit_synthetic_winners(
                    [race], {race["raceId"]: {**original, **altered}}, SPLIT)

    def test_result_does_not_change_precomputed_prediction_or_inputs(self):
        race = sample()
        frozen = copy.deepcopy(race)
        a = audit_synthetic_winners(
            [race], {race["raceId"]: outcome(race)}, SPLIT)
        b = audit_synthetic_winners(
            [race], {race["raceId"]: outcome(race, [8, 7, 6])}, SPLIT)
        self.assertEqual(race, frozen)
        self.assertEqual(a["rows"][0]["predictionHash"],
                         b["rows"][0]["predictionHash"])

    def test_real_races_and_bad_threshold_are_rejected(self):
        race = sample()
        for n in (0, -1, 1.5, True, "20", 10001):
            with self.subTest(n=n), self.assertRaises(ValueError):
                audit_synthetic_winners([race], {}, SPLIT,
                                        min_validation_races=n)
        with self.assertRaises(ValueError):
            audit_synthetic_winners(
                [{**race, "recordType": "live"}], {}, SPLIT)


if __name__ == "__main__":
    unittest.main()
