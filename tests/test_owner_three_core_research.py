"""Synthetic JRDB history: core research evidence is NOT formal scoring."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation_policy import FACTORS, POINTS
from jrdb_coverage import CoverageError
from owner_three_core_research import three_core_research, CORE, WEIGHTS
from test_jrdb_history_pipeline import run_case, context


def sample():
    report = run_case(context())
    return report["fiveFactorHypotheses"], report["tenFactorSourceInventory"]


class ThreeCoreResearchTests(unittest.TestCase):
    def test_real_pipeline_sources_remain_unverified_and_read_only(self):
        five, inventory = sample()
        original = copy.deepcopy((five, inventory))
        report = three_core_research(five, inventory)
        self.assertEqual((five, inventory), original)
        self.assertEqual(report["version"], "owner-three-core-research-1")
        self.assertEqual(report["coreFactorWeights"], {
            "training": 30, "course_distance": 20, "pace": 20
        })
        self.assertEqual(report["coreWeightTotal"], 70)
        self.assertEqual(report["raceCount"], 2)
        for flag in ("overallPredictionReady", "formalScoreReady",
                     "officialJraVerified", "bettingReady", "autoPurchase",
                     "changesExistingTickets"):
            self.assertFalse(report[flag])
        self.assertEqual(report["factorGradesVerified"], 0)
        self.assertTrue(report["historicalBandsNotCalibrated"])
        mapped = {(r["track"], r["race"]): r for r in report["races"]}
        self.assertEqual(set(mapped), {
            (r["track"], r["race"]) for r in five["races"]
        })
        for race in report["races"]:
            self.assertEqual(race["runnerCount"], len(race["horses"]))
            self.assertFalse(race["formalGradeReady"])
            self.assertFalse(race["trifectaReady"])
            self.assertEqual(race["completeCoreObserved"], sum(
                h["evidenceScore70"] is not None for h in race["horses"]))
            for horse in race["horses"]:
                self.assertIsNone(horse["formalScore100"])
                self.assertEqual(horse["formalGrade"], "未評価")
                self.assertIsNone(horse["formalRank"])
                self.assertFalse(horse["bettingReady"])
                self.assertEqual(horse["observedCoreCount"],
                                 3 - len(horse["missing"]))
                if horse["missing"]:
                    self.assertIsNone(horse["evidenceScore70"])
                    self.assertIsNone(horse["rawThirdPoints"])
                else:
                    raw = sum(POINTS[horse["bands"][key]] * FACTORS[key]
                              for key in CORE)
                    self.assertEqual(horse["rawThirdPoints"], raw)
                    self.assertEqual(horse["evidenceScore70"],
                                     round(raw / 3, 2))
                    self.assertLessEqual(horse["evidenceScore70"], 70)
        for secret in ("racekey", "byNumber", "horse_id", "sourceId",
                       "jockey_name", "trifectaTickets", "auth_key"):
            self.assertNotIn(secret, repr(report))

    def test_all_s_still_never_authorizes_tickets_or_formal_score(self):
        five, inventory = sample()
        horse = five["races"][0]["runners"][0]
        linked = next(h for h in inventory["races"][0]["runners"]
                      if h["number"] == horse["number"])
        for k in CORE:
            horse["bands"][k] = "S"
            linked["provisionalBands"][k] = "S"
        result = three_core_research(five, inventory)
        first = next(x for x in result["races"][0]["horses"]
                     if x["number"] == horse["number"])
        self.assertEqual(first["evidenceScore70"], 70.0)
        self.assertEqual(first["rawThirdPoints"], 210)
        self.assertIsNone(first["formalScore100"])
        self.assertFalse(result["bettingReady"])
        self.assertFalse(result["changesExistingTickets"])

    def test_missing_core_is_never_extrapolated_or_treated_as_c(self):
        five, inventory = sample()
        horse = five["races"][0]["runners"][0]
        link = next(h for h in inventory["races"][0]["runners"]
                    if h["number"] == horse["number"])
        # Explicitly construct a fully observed 3-core baseline,
        # then remove only pace to check no partial extrapolation.
        for k in CORE:
            horse["bands"][k] = "S"
            link["provisionalBands"][k] = "S"
        horse["bands"]["pace"] = "未評価"
        link["provisionalBands"]["pace"] = "未評価"
        result = three_core_research(five, inventory)
        h = next(x for x in result["races"][0]["horses"]
                 if x["number"] == horse["number"])
        self.assertEqual(h["missing"], ["pace"])
        self.assertEqual(h["observedCoreCount"], 2)
        self.assertIsNone(h["evidenceScore70"])
        self.assertIsNone(h["rawThirdPoints"])
        self.assertEqual(h["formalGrade"], "未評価")

    def test_mismatched_source_or_promoted_flag_is_rejected(self):
        changes = (
            lambda f, i: i["races"][0]["runners"][0].update(number=18),
            lambda f, i: f["races"][0].update(track="阪神"),
            lambda f, i: f["races"][0]["runners"][0]["bands"].update(training="A"),
            lambda f, i: f.update(officialJraVerified=True),
            lambda f, i: i.update(bettingReady=True),
            lambda f, i: f.update(verifiedFactorCount=1),
            lambda f, i: i["races"][0]["runners"][0].update(overallScore=85),
            lambda f, i: i["factorWeights"].update(training=29),
        )
        for change in changes:
            with self.subTest(change=repr(change)):
                five, inventory = sample()
                change(five, inventory)
                with self.assertRaises(CoverageError):
                    three_core_research(five, inventory)


if __name__ == "__main__":
    unittest.main()
