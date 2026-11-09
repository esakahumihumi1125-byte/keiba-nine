"""Four-factor 82-weight experiment never becomes official scoring."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation_policy import FACTORS, POINTS
from jrdb_coverage import CoverageError
from owner_three_core_research import three_core_research
from owner_four_core_research import four_core_research, CORE, WEIGHTS
from test_owner_three_core_research import sample


def sources():
    five, inventory = sample()
    return five, inventory, three_core_research(five, inventory)


class FourCoreResearchTests(unittest.TestCase):
    def test_82_weight_breakdown_and_same_races_are_immutable(self):
        five, inventory, three = sources()
        before = copy.deepcopy((five, inventory, three))
        out = four_core_research(five, inventory, three)
        self.assertEqual((five, inventory, three), before)
        self.assertEqual(out["version"], "owner-four-core-research-1")
        self.assertEqual(out["factorWeights"], {
            "training": 30, "course_distance": 20,
            "pace": 20, "ground": 12,
        })
        self.assertEqual(out["observedWeightTotal"], 82)
        self.assertEqual(out["raceCount"], 2)
        self.assertEqual(out["factorGradesVerified"], 0)
        for key in ("overallPredictionReady", "formalScoreReady",
                    "officialJraVerified", "bettingReady", "autoPurchase",
                    "changesExistingTickets", "changesExistingCoreReceipts",
                    "goingSuitabilityVerified"):
            self.assertFalse(out[key])
        self.assertTrue(out["historicalBandsNotCalibrated"])
        for race in out["races"]:
            self.assertFalse(race["formalGradeReady"])
            self.assertFalse(race["trifectaReady"])
            self.assertEqual(race["runnerCount"], len(race["horses"]))
            self.assertEqual(race["completeObserved"], sum(
                h["evidenceScore82"] is not None for h in race["horses"]))
            for h in race["horses"]:
                self.assertEqual(h["formalGrade"], "未評価")
                self.assertIsNone(h["formalScore100"])
                self.assertIsNone(h["formalRank"])
                self.assertFalse(h["bettingReady"])
                self.assertEqual(h["observedFactorCount"], 4 - len(h["missing"]))
                if h["missing"]:
                    self.assertIsNone(h["evidenceScore82"])
                    self.assertIsNone(h["rawThirdPoints"])
                else:
                    raw = sum(POINTS[h["bands"][k]] * FACTORS[k] for k in CORE)
                    self.assertEqual(h["rawThirdPoints"], raw)
                    self.assertEqual(h["evidenceScore82"], round(raw / 3, 2))
                    self.assertLessEqual(h["evidenceScore82"], 82)
        for forbidden in ("racekey", "horse_name", "trifectaTickets",
                          "api_key", "auth_key", "observedWinner"):
            self.assertNotIn(forbidden, repr(out))

    def test_all_s_only_research_and_ground_max_changes_by_twelve(self):
        five, inventory, _ = sources()
        h = five["races"][0]["runners"][0]
        linked = next(x for x in inventory["races"][0]["runners"]
                      if x["number"] == h["number"])
        for factor in CORE:
            h["bands"][factor] = "S"
            linked["provisionalBands"][factor] = "S"
        three = three_core_research(five, inventory)
        full = four_core_research(five, inventory, three)
        first = next(x for x in full["races"][0]["horses"]
                     if x["number"] == h["number"])
        self.assertEqual(first["evidenceScore82"], 82.0)
        self.assertEqual(first["rawThirdPoints"], 246)
        self.assertEqual(first["formalGrade"], "未評価")
        self.assertFalse(full["bettingReady"])
        self.assertFalse(full["changesExistingCoreReceipts"])
        h["bands"]["ground"] = "C"
        linked["provisionalBands"]["ground"] = "C"
        bottom = four_core_research(
            five, inventory, three_core_research(five, inventory))
        first_bottom = next(x for x in bottom["races"][0]["horses"]
                            if x["number"] == h["number"])
        self.assertEqual(first_bottom["evidenceScore82"], 70.0)
        self.assertEqual(first["evidenceScore82"] -
                         first_bottom["evidenceScore82"], 12.0)

    def test_unknown_going_does_not_create_fake_zero_or_partial_score(self):
        five, inventory, _ = sources()
        h = five["races"][0]["runners"][0]
        linked = next(x for x in inventory["races"][0]["runners"]
                      if x["number"] == h["number"])
        for factor in CORE:
            h["bands"][factor] = "S"
            linked["provisionalBands"][factor] = "S"
        h["bands"]["ground"] = "未評価"
        linked["provisionalBands"]["ground"] = "未評価"
        three = three_core_research(five, inventory)
        self.assertEqual(three["races"][0]["horses"][0]["evidenceScore70"], 70.0)
        four = four_core_research(five, inventory, three)
        first = four["races"][0]["horses"][0]
        self.assertEqual(first["observedFactorCount"], 3)
        self.assertEqual(first["missing"], ["ground"])
        self.assertIsNone(first["evidenceScore82"])
        self.assertIsNone(first["rawThirdPoints"])
        self.assertEqual(first["formalGrade"], "未評価")

    def test_mismatched_going_and_tampered_three_core_refused(self):
        changes = (
            lambda f, i, t: i["races"][0]["runners"][0][
                "provisionalBands"].update(ground="S"),
            lambda f, i, t: t["races"][0]["horses"][0].update(
                rawThirdPoints=210),
            lambda f, i, t: t.update(officialJraVerified=True),
            lambda f, i, t: f.update(verifiedFactorCount=1),
            lambda f, i, t: i["factorWeights"].update(ground=999),
        )
        for action in changes:
            with self.subTest(action=repr(action)):
                five, inventory, three = sources()
                action(five, inventory, three)
                with self.assertRaises(CoverageError):
                    four_core_research(five, inventory, three)


if __name__ == "__main__":
    unittest.main()
