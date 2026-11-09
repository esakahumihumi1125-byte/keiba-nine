"""Five-factor 85/100 research overlay, not real model score or prediction."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation_policy import FACTORS, POINTS
from jrdb_coverage import CoverageError
from owner_three_core_research import three_core_research
from owner_four_core_research import four_core_research
from owner_five_core_research import five_core_research, CORE, WEIGHTS
from test_owner_three_core_research import sample


def sources():
    five, inventory = sample()
    three = three_core_research(five, inventory)
    four = four_core_research(five, inventory, three)
    return five, inventory, three, four


class FiveCoreResearchTests(unittest.TestCase):
    def test_same_races_85_exact_int_and_read_only(self):
        five, inventory, three, four = sources()
        before = copy.deepcopy((five, inventory, three, four))
        out = five_core_research(five, inventory, three, four)
        self.assertEqual((five, inventory, three, four), before)
        self.assertEqual(out["version"], "owner-five-core-research-1")
        self.assertEqual(out["factorWeights"], {
            "training": 30, "course_distance": 20,
            "pace": 20, "ground": 12, "recent": 3,
        })
        self.assertEqual(out["observedWeightTotal"], 85)
        self.assertEqual(out["factorGradesVerified"], 0)
        self.assertEqual(out["raceCount"], 2)
        self.assertEqual(out["raceCount"], len(out["races"]))
        for flag in ("overallPredictionReady", "formalScoreReady",
                     "officialJraVerified", "bettingReady", "autoPurchase",
                     "changesExistingTickets", "changesExistingCoreReceipts"):
            self.assertFalse(out[flag])
        self.assertTrue(out["historicalBandsNotCalibrated"])
        self.assertTrue(out["recentResultRankNotPrediction"])
        for race in out["races"]:
            self.assertFalse(race["formalGradeReady"])
            self.assertFalse(race["trifectaReady"])
            self.assertEqual(race["runnerCount"], len(race["horses"]))
            self.assertEqual(race["completeObserved"], sum(
                horse["evidenceScore85"] is not None
                for horse in race["horses"]))
            for horse in race["horses"]:
                self.assertFalse(horse["scoreIsCalibrated"])
                self.assertIsNone(horse["formalScore100"])
                self.assertEqual(horse["formalGrade"], "未評価")
                self.assertIsNone(horse["formalRank"])
                self.assertFalse(horse["bettingReady"])
                self.assertEqual(horse["observedFactorCount"],
                                 5 - len(horse["missing"]))
                if horse["missing"]:
                    self.assertIsNone(horse["rawThirdPoints"])
                    self.assertIsNone(horse["evidenceScore85"])
                else:
                    exact = sum(
                        FACTORS[key] * POINTS[horse["bands"][key]]
                        for key in CORE
                    )
                    self.assertEqual(horse["rawThirdPoints"], exact)
                    self.assertEqual(horse["evidenceScore85"],
                                     round(exact / 3, 2))
                    self.assertLessEqual(horse["evidenceScore85"], 85)
        for secret in ("racekey", "horse_name", "trifectaTickets",
                       "api_key", "auth_key", "resultPayout"):
            self.assertNotIn(secret, repr(out))

    def test_recent_only_three_points_and_low_recent_can_still_score_82(self):
        five, inventory, _, _ = sources()
        f = five["races"][0]["runners"][0]
        i = next(row for row in inventory["races"][0]["runners"]
                 if row["number"] == f["number"])
        for factor in CORE:
            f["bands"][factor] = "S"
            i["provisionalBands"][factor] = "S"
        three = three_core_research(five, inventory)
        four = four_core_research(five, inventory, three)
        full = five_core_research(five, inventory, three, four)
        first = full["races"][0]["horses"][0]
        self.assertEqual(first["evidenceScore85"], 85.0)
        self.assertEqual(first["rawThirdPoints"], 255)
        self.assertFalse(full["bettingReady"])
        self.assertIsNone(first["formalScore100"])
        f["bands"]["recent"] = "C"
        i["provisionalBands"]["recent"] = "C"
        worse = five_core_research(
            five, inventory,
            three_core_research(five, inventory),
            four_core_research(five, inventory,
                               three_core_research(five, inventory)))
        self.assertEqual(worse["races"][0]["horses"][0]["evidenceScore85"], 82.0)
        self.assertEqual(first["evidenceScore85"] -
                         worse["races"][0]["horses"][0]["evidenceScore85"], 3.0)
        self.assertFalse(worse["changesExistingCoreReceipts"])

    def test_missing_recent_never_cast_to_c_or_reweight_other_four(self):
        five, inventory, _, _ = sources()
        f = five["races"][0]["runners"][0]
        i = next(row for row in inventory["races"][0]["runners"]
                 if row["number"] == f["number"])
        for key in CORE:
            f["bands"][key] = "S"
            i["provisionalBands"][key] = "S"
        f["bands"]["recent"] = "未評価"
        i["provisionalBands"]["recent"] = "未評価"
        three = three_core_research(five, inventory)
        four = four_core_research(five, inventory, three)
        self.assertEqual(four["races"][0]["horses"][0]["evidenceScore82"], 82)
        five_result = five_core_research(five, inventory, three, four)
        horse = five_result["races"][0]["horses"][0]
        self.assertEqual(horse["missing"], ["recent"])
        self.assertEqual(horse["observedFactorCount"], 4)
        self.assertIsNone(horse["evidenceScore85"])
        self.assertIsNone(horse["rawThirdPoints"])
        self.assertEqual(horse["formalGrade"], "未評価")

    def test_promotion_tamper_previous_study_or_recent_roster_mismatch(self):
        mutators = (
            lambda f, i, t, q: i["races"][0]["runners"][0][
                "provisionalBands"].update(recent="UNTRUSTED"),
            lambda f, i, t, q: q["races"][0]["horses"][0].update(
                rawThirdPoints=255),
            lambda f, i, t, q: q.update(officialJraVerified=True),
            lambda f, i, t, q: t.update(changesExistingTickets=True),
            lambda f, i, t, q: f.update(verifiedFactorCount=1),
            lambda f, i, t, q: i["factorWeights"].update(recent=99),
            lambda f, i, t, q: f["races"][0]["runners"][0].update(
                actualGradesVerified=1),
        )
        for index, mutate in enumerate(mutators):
            with self.subTest(case=index):
                five, inventory, three, four = sources()
                mutate(five, inventory, three, four)
                with self.assertRaises(CoverageError):
                    five_core_research(five, inventory, three, four)


if __name__ == "__main__":
    unittest.main()
