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

    def test_equal_two_factor_totals_are_tied(self):
        a, b = self.selected()
        a[0]["gradesByNumber"]["01"] = "S"
        b[0]["byNumber"]["01"]["grade"] = "B"
        a[0]["gradesByNumber"]["02"] = "A"
        b[0]["byNumber"]["02"]["grade"] = "A"
        doc = owner_runner_research(a, b, "東京", 1)
        self.assertEqual([r["researchOrder"] for r in doc["runners"]], [1, 1])

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
