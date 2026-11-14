"""No-provider, no-secret tests for the personal two-factor draft."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_owner_runner_research import owner_runner_research
from test_jrdb_private_factor_bridge import inputs


class OwnerRunnerResearchTests(unittest.TestCase):
    def selected(self):
        a, b = inputs()
        return [a[0]], [b[0]]

    def test_only_unvalidated_two_factor_order_is_returned(self):
        a, b = self.selected()
        frozen = copy.deepcopy((a, b))
        doc = owner_runner_research(a, b, "東京", 1)
        self.assertEqual(doc["runnerCount"], 2)
        self.assertEqual(doc["completeTwoFactorCount"], 2)
        self.assertEqual([r["number"] for r in doc["runners"]], [1, 2])
        self.assertEqual([r["researchOrder"] for r in doc["runners"]], [1, 2])
        self.assertEqual(doc["runners"][0]["training"], "S")
        self.assertEqual(doc["runners"][0]["recent"], "S")
        self.assertEqual(doc["runners"][0]["pastFourthCorner"], "frontObserved")
        self.assertFalse(doc["officialJraVerified"])
        self.assertFalse(doc["overallRankReady"])
        self.assertFalse(doc["predictionReady"])
        self.assertFalse(doc["bettingReady"])
        self.assertEqual((a, b), frozen)
        for sensitive in ("racekey", "horse_id", "horse_name", "idm",
                          "oikirisisu", "siagarisisu", "_partialScore",
                          "finish", "confirmed_win_odds"):
            self.assertNotIn(sensitive, repr(doc))

    def test_missing_factor_never_receives_a_research_rank(self):
        a, b = self.selected()
        b[0]["byNumber"]["02"]["grade"] = "未評価"
        doc = owner_runner_research(a, b, "東京", 1)
        self.assertEqual(doc["completeTwoFactorCount"], 1)
        self.assertEqual(doc["runners"][0]["researchOrder"], 1)
        self.assertIsNone(doc["runners"][1]["researchOrder"])
        self.assertEqual(doc["runners"][1]["completeFactors"], 1)
        self.assertFalse(doc["bettingReady"])

    def test_training_30_recent_3_matches_draft_priority(self):
        a, b = self.selected()
        # Old equal-weight grades put A/S above S/C (7 vs 5).
        # The user's 30:3 priority requires S/C (90) above A/S (69).
        a[0]["gradesByNumber"]["01"] = "S"
        b[0]["byNumber"]["01"]["grade"] = "C"
        a[0]["gradesByNumber"]["02"] = "A"
        b[0]["byNumber"]["02"]["grade"] = "S"
        original = copy.deepcopy((a, b))
        out = owner_runner_research(a, b, "東京", 1)
        self.assertEqual([h["number"] for h in out["runners"]], [1, 2])
        self.assertEqual([h["researchOrder"] for h in out["runners"]], [1, 2])
        self.assertEqual((a, b), original)
        self.assertNotIn("_partialScore", repr(out))
        self.assertFalse(out["predictionReady"])

    def test_genuinely_equal_weighted_grades_are_tied(self):
        a, b = self.selected()
        a[0]["gradesByNumber"]["01"] = "S"
        b[0]["byNumber"]["01"]["grade"] = "B"
        a[0]["gradesByNumber"]["02"] = "S"
        b[0]["byNumber"]["02"]["grade"] = "B"
        out = owner_runner_research(a, b, "東京", 1)
        self.assertEqual([h["number"] for h in out["runners"]], [1, 2])
        self.assertEqual([h["researchOrder"] for h in out["runners"]], [1, 1])

    def test_missing_training_never_uses_recent_as_full_score(self):
        a, b = self.selected()
        a[0]["gradesByNumber"]["01"] = "未評価"
        b[0]["byNumber"]["01"]["grade"] = "S"
        out = owner_runner_research(a, b, "東京", 1)
        by_number = {h["number"]: h for h in out["runners"]}
        self.assertIsNone(by_number[1]["researchOrder"])
        self.assertEqual(by_number[1]["completeFactors"], 1)
        self.assertEqual(by_number[2]["researchOrder"], 1)

    def test_single_scored_run_is_observed_but_never_invents_recent_grade(self):
        a, b = self.selected()
        record = b[0]["byNumber"]["02"]
        record.update({
            "grade": "未評価", "assessmentStatus": "only_one_usable_run",
            "datedRuns": 1, "completedRuns": 1, "topThree": 1,
            "fourthObserved": 1, "frontAtFourth": 1,
            "late3fObserved": 1,
        })
        source = copy.deepcopy((a, b))
        out = owner_runner_research(a, b, "東京", 1)
        horse = next(h for h in out["runners"] if h["number"] == 2)
        self.assertEqual(horse["recent"], "未評価")
        self.assertIsNone(horse["researchOrder"])
        self.assertEqual(horse["recentObserved"], {
            "datedRuns": 1, "completedRuns": 1,
            "topThreeObserved": 1, "fourthCornerObserved": 1,
            "late3fObserved": 1,
        })
        self.assertFalse(out["bettingReady"])
        self.assertEqual((a, b), source)
        for forbidden in ("race_back_", "order_of_finish", "idm",
                          "horse_id", "horse_name", "racedate"):
            self.assertNotIn(forbidden, repr(out))

    def test_bad_redacted_evidence_fails_one_race_instead_of_guessing(self):
        for key, bad in (("datedRuns", -1), ("completedRuns", 6),
                         ("topThree", 2), ("late3fObserved", 3),
                         ("fourthObserved", True)):
            a, b = self.selected()
            row = b[0]["byNumber"]["02"]
            row.update({"datedRuns": 1, "completedRuns": 1,
                        "topThree": 1, "fourthObserved": 1,
                        "frontAtFourth": 1, "late3fObserved": 1})
            row[key] = bad
            with self.subTest(key=key), self.assertRaises(CoverageError):
                owner_runner_research(a, b, "東京", 1)

    def test_inconsistent_identity_or_values_rejected(self):
        for change in ("race", "runners", "grade", "corner", "number"):
            with self.subTest(change=change):
                a, b = self.selected()
                if change == "race":
                    b[0]["race"] = 12
                elif change == "runners":
                    del b[0]["byNumber"]["02"]
                elif change == "grade":
                    b[0]["byNumber"]["02"]["grade"] = "X"
                elif change == "corner":
                    b[0]["byNumber"]["01"]["fourthObserved"] = 8
                elif change == "number":
                    a[0]["gradesByNumber"]["19"] = "S"
                    b[0]["byNumber"]["19"] = {
                        "grade": "未評価",
                        "frontAtFourth": 0,
                        "fourthObserved": 0,
                    }
                with self.assertRaises(CoverageError):
                    owner_runner_research(a, b, "東京", 1)


if __name__ == "__main__":
    unittest.main()
