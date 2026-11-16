"""Fail-closed roster binding for same-day optional JRDB factor scores.

Synthetic fixtures only: no provider read, no passwords, no official claims,
no new tickets or persisted records.
"""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_isolated_factor_scores import reconcile_factor_rosters_with_drafts


def example():
    factor = {
        "version": "owner-automatic-factor-scores-3",
        "policyVersion": "research-6",
        "date": "20990101",
        "modelCalibrated": False,
        "officialJraVerified": False,
        "overallPredictionReady": False,
        "newProviderRequests": 0,
        "isolatedHeldRaces": 0,
        "races": [
            {"track": "東京", "race": 1, "postTime": "12:00",
             "status": "scored", "reason": None,
             "horses": [{"number": n, "factors": {}} for n in [1, 2, 3, 4]]},
            {"track": "京都", "race": 2, "postTime": "13:00",
             "status": "scored", "reason": None,
             "horses": [{"number": n, "factors": {}} for n in [3, 4, 5, 6]]},
            {"track": "福島", "race": 3, "postTime": "14:00",
             "status": "held", "reason": "after_start", "horses": []},
        ],
    }
    draft = {
        "researchOnly": True, "officialJraVerified": False,
        "races": [
            {"track": "東京", "race": 1, "postTime": "12:00",
             "status": "provisional_draft",
             "runners": [{"number": n} for n in [4, 3, 2, 1]]},
            {"track": "京都", "race": 2, "postTime": "13:00",
             "status": "hold", "runners": [{"number": n} for n in [3, 4, 5, 7]]},
            {"track": "福島", "race": 3, "postTime": "14:00",
             "status": "hold", "runners": []},
        ],
    }
    return factor, draft


class ExactRosterBindingTests(unittest.TestCase):
    def test_one_mismatch_held_and_unrelated_race_preserved(self):
        factors, drafts = example()
        original = deepcopy(factors)
        output = reconcile_factor_rosters_with_drafts(factors, drafts)
        self.assertEqual(factors, original)
        self.assertEqual(output["races"][0], original["races"][0])
        self.assertEqual(output["races"][1]["reason"], "research_roster_mismatch")
        self.assertEqual(output["races"][1]["horses"], [])
        self.assertEqual(output["races"][2], original["races"][2])
        self.assertEqual(output["isolatedHeldRaces"], 1)
        self.assertIs(output["overallPredictionReady"], False)

    def test_all_matching_scores_keep_horse_numbers(self):
        factors, drafts = example()
        drafts["races"][1]["runners"] = [
            {"number": n} for n in [6, 5, 4, 3]
        ]
        output = reconcile_factor_rosters_with_drafts(factors, drafts)
        self.assertEqual(output["races"], factors["races"])
        self.assertEqual(output["isolatedHeldRaces"], 0)

    def test_empty_draft_holds_optional_scores(self):
        factors, drafts = example()
        drafts["races"][0]["runners"] = []
        output = reconcile_factor_rosters_with_drafts(factors, drafts)
        self.assertEqual(output["races"][0]["status"], "held")
        self.assertEqual(output["races"][0]["horses"], [])

    def test_different_start_time_fails_closed(self):
        factors, drafts = example()
        drafts["races"][0]["postTime"] = "11:55"
        with self.assertRaises(CoverageError):
            reconcile_factor_rosters_with_drafts(factors, drafts)

    def test_duplicate_or_foreign_race_is_rejected(self):
        factors, drafts = example()
        drafts["races"][1]["track"] = "東京"
        drafts["races"][1]["race"] = 1
        with self.assertRaises(CoverageError):
            reconcile_factor_rosters_with_drafts(factors, drafts)
        factors, drafts = example()
        factors["races"][0]["track"] = "中山"
        with self.assertRaises(CoverageError):
            reconcile_factor_rosters_with_drafts(factors, drafts)

    def test_duplicate_and_malformed_numbers_fail(self):
        for value in (2, "2", True, 19, None):
            factors, drafts = example()
            factors["races"][0]["horses"][0]["number"] = value
            with self.assertRaises(CoverageError):
                reconcile_factor_rosters_with_drafts(factors, drafts)
        factors, drafts = example()
        drafts["races"][0]["runners"][0]["number"] = 1
        with self.assertRaises(CoverageError):
            reconcile_factor_rosters_with_drafts(factors, drafts)

    def test_research_only_flags_are_mandatory(self):
        factors, drafts = example()
        factors["officialJraVerified"] = True
        with self.assertRaises(CoverageError):
            reconcile_factor_rosters_with_drafts(factors, drafts)


if __name__ == "__main__":
    unittest.main()
