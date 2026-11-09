"""Research-only interval arithmetic, strict roster joins, immutable inputs."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_research6_uncertainty import research6_uncertainty_intervals
from test_jrdb_history_pipeline import run_case, context


def original():
    report = run_case(context())
    return report["newWeightFiveResearch"], report["remaining21SourceGaps"]


class Research6UncertaintyTests(unittest.TestCase):
    def test_real_pipeline_synthetic_source_stays_immutable(self):
        five, remaining = original()
        untouched = copy.deepcopy((five, remaining))
        report = research6_uncertainty_intervals(five, remaining)
        self.assertEqual((five, remaining), untouched)
        self.assertEqual(report["policyVersion"], "research-6")
        self.assertEqual(sum(report["factorWeights"].values()), 100)
        self.assertEqual(report["observedFactorWeightCeiling"], 79)
        self.assertEqual(report["alwaysUnassessedWeight"], 21)
        self.assertEqual(report["jockeyStableUnassessedWeight"], 10)
        self.assertEqual(report["raceCount"], len(five["races"]))
        for race in report["races"]:
            self.assertFalse(race["formalRankReady"])
            for h in race["horses"]:
                self.assertEqual(h["jockeyStableStillUnassessedWeight"], 10)
                self.assertEqual(h["unassessedTotalWeight"],
                                 h["otherUnassessedWeight"] + 10)
                self.assertLessEqual(h["lowerResearchBound"], h["upperResearchBound"])
                self.assertLessEqual(h["upperResearchBound"], 100)
                self.assertEqual(
                    h["upperResearchRawThirdPoints"] - h["lowerResearchRawThirdPoints"],
                    3 * h["unassessedTotalWeight"])
                self.assertEqual(h["formalGrade"], "未評価")
                self.assertIsNone(h["formalScore100"])
                self.assertIsNone(h["formalRank"])
                self.assertFalse(h["scoreIsCalibrated"])
                self.assertFalse(h["bettingReady"])
                self.assertTrue(1 <= h["researchPossibleBestRank"]
                                <= h["researchPossibleWorstRank"] <= race["runnerCount"])
        for key in ("verifiedFactorCount", "extraProviderCalls"):
            self.assertEqual(report[key], 0)
        for key in ("formalScoreReady", "officialJraVerified", "bettingReady",
                    "autoPurchase", "changesExistingReceipts",
                    "changesExistingTickets", "changesExistingRoi"):
            self.assertFalse(report[key])
        for secret in ("racekey", "horseRef", "trainerRef",
                       "apiKey", "trifectaTickets", "payoutYen"):
            self.assertNotIn(secret, repr(report))

    def test_all_s_five_has_79_to_100_interval_recent_c_has_3_point_cost(self):
        five, remaining = original()
        h = five["races"][0]["horses"][0]
        g = remaining["races"][0]["horses"][0]
        h["bands"] = dict.fromkeys(h["bands"], "S")
        h["missing"] = []
        h["observedFactorCount"] = 5
        h["rawThirdPoints"] = 237
        h["evidenceScore79"] = 79
        g["research79Observed"] = True
        g["research79"] = 79
        report = research6_uncertainty_intervals(five, remaining)
        sample = report["races"][0]["horses"][0]
        self.assertEqual((sample["lowerResearchBound"], sample["upperResearchBound"]),
                         (79, 100))
        self.assertEqual(sample["unassessedTotalWeight"], 21)
        self.assertEqual(sample["otherUnassessedWeight"], 11)
        h["bands"]["recent"] = "C"
        h["rawThirdPoints"] = 228
        h["evidenceScore79"] = 76
        g["research79"] = 76
        new = research6_uncertainty_intervals(five, remaining)["races"][0]["horses"][0]
        self.assertEqual((new["lowerResearchBound"], new["upperResearchBound"]),
                         (76, 97))
        self.assertEqual(sample["lowerResearchBound"] - new["lowerResearchBound"], 3)

    def test_missing_is_interval_not_zero_and_can_reverse_comparisons(self):
        five, remaining = original()
        first, gap = five["races"][0]["horses"][0], remaining["races"][0]["horses"][0]
        first["bands"] = dict.fromkeys(first["bands"], "C")
        first["bands"]["training"] = "未評価"
        first["missing"] = ["training"]
        first["observedFactorCount"] = 4
        first["rawThirdPoints"] = None
        first["evidenceScore79"] = None
        gap["research79Observed"] = False
        gap["research79"] = None
        first_input_copy = copy.deepcopy(first)
        result = research6_uncertainty_intervals(five, remaining)
        row = result["races"][0]["horses"][0]
        self.assertEqual(row["lowerResearchBound"], 0)
        self.assertEqual(row["upperResearchBound"], 51)
        self.assertEqual(row["unassessedTotalWeight"], 51)
        self.assertEqual(first, first_input_copy)
        self.assertEqual(row["formalGrade"], "未評価")

    def test_rejects_merged_race_wrong_personnel_or_forged_grade(self):
        changes = (
            lambda f, g: f.update(policyVersion="research-5"),
            lambda f, g: f["factorWeights"].update(jockey_stable=10),
            lambda f, g: g["factorWeights"].update(jockey_stable=2),
            lambda f, g: g["races"][0]["horses"][0].update(research79=99),
            lambda f, g: f["races"][0]["horses"][0].update(formalScore100=95),
            lambda f, g: g["races"][0]["horses"][0].update(formalGrade="S"),
            lambda f, g: g["races"][0]["horses"][0]
                        ["sourceFieldsPresent"].update(body_condition=True),
            lambda f, g: g["races"][0]["horses"][0]
                        .update(sourceFieldCoverageEquivalent21=21),
            lambda f, g: f["races"][0]["horses"][0]["bands"].update(pace="WRONG"),
            lambda f, g: f["races"][0]["horses"][0].update(rawThirdPoints=241),
            lambda f, g: g["races"][0].update(gradeReady=True),
            lambda f, g: g.update(officialJraVerified=True),
        )
        for change in changes:
            five, gaps = original()
            change(five, gaps)
            with self.subTest(change=repr(change)), self.assertRaises(CoverageError):
                research6_uncertainty_intervals(five, gaps)


if __name__ == "__main__":
    unittest.main()
