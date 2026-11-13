"""No-money, no-provider test of new-policy remaining 21 source readiness."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_new_weight_five_research import new_weight_five_research
from owner_remaining21_source_gaps import remaining21_source_gaps
from test_jrdb_history_pipeline import run_case, context


def original():
    report = run_case(context())
    return report["newWeightFiveResearch"], report["tenFactorSourceInventory"]


class Remaining21SourceGapsTests(unittest.TestCase):
    def test_source_coverage_not_prediction_or_points(self):
        five, inventory = original()
        before = copy.deepcopy((five, inventory))
        report = remaining21_source_gaps(five, inventory)
        self.assertEqual((five, inventory), before)
        self.assertEqual(report["policyVersion"], "research-6")
        self.assertEqual(report["sourcePolicyVersion"], "research-5")
        self.assertEqual(report["remainingWeight"], 21)
        self.assertEqual(report["initialResearchWeight"], 79)
        self.assertEqual(report["pedigreeStaffWeight"], 16)
        self.assertEqual(report["pedigreeStaffGradesVerified"], 0)
        self.assertFalse(report["independentPedigreeCohortValidated"])
        self.assertFalse(report["conditionMatchedStaffResultsValidated"])
        self.assertFalse(report["outOfTimePerformanceValidated"])
        self.assertEqual(report["factorWeights"], {
            "pedigree": 6, "draw_weight": 3, "jockey_stable": 10,
            "rotation": 1, "body_condition": 1,
        })
        self.assertEqual(report["raceCount"], len(five["races"]))
        self.assertEqual(report["raceCount"], len(inventory["races"]))
        for item in report["races"]:
            self.assertFalse(item["gradeReady"])
            self.assertFalse(item["trifectaReady"])
            self.assertEqual(len(item["horses"]), item["runnerCount"])
            self.assertEqual(item["pedigreeParentageCompleteCount"],
                item["sourceCoverageByFactor"]["pedigree"])
            self.assertEqual(item["staffIdentityCompleteCount"],
                item["sourceCoverageByFactor"]["jockey_stable"])
            self.assertEqual(item["bothPedigreeStaffCompleteCount"],
                sum(h["pedigreeStaffSourceCoverage16"] == 16
                    for h in item["horses"]))
            self.assertEqual(item["pedigreeStaffVerifiedGrades"], 0)
            for horse in item["horses"]:
                self.assertIsNone(horse["formalScore100"])
                self.assertEqual(horse["formalGrade"], "未評価")
                p = horse["sourceFieldsPresent"]
                self.assertEqual(horse["pedigreeStaffSourceCoverage16"],
                                 int(p["pedigree"]) * 6 +
                                 int(p["jockey_stable"]) * 10)
                self.assertFalse(horse["pedigreeStaffScoreReady"])
                self.assertEqual(horse["pedigreeStaffGrades"],
                                 {"pedigree": "未評価",
                                  "jockey_stable": "未評価"})
                self.assertEqual(horse["pedigreeStaffScores"],
                                 {"pedigree": None, "jockey_stable": None})
                for key in ("pedigree", "jockey_stable"):
                    self.assertIn("temporal_holdout_not_validated",
                                  horse["pedigreeStaffMissingEvidence"][key])
                self.assertFalse(horse["bettingReady"])
                self.assertFalse(horse["sourceFieldsPresent"]["body_condition"])
                self.assertIn("body_condition", horse["missingSourceFields"])
                self.assertLessEqual(horse["sourceFieldCoverageEquivalent21"], 20)
                self.assertEqual(horse["sourceFieldCoverageEquivalent21"],
                                 sum(report["factorWeights"][key] for key, val
                                     in horse["sourceFieldsPresent"].items() if val))
                self.assertTrue(all(key in horse["missingValidation"]
                                    for key in report["factorWeights"]))
        self.assertEqual(report["verifiedFactorCount"], 0)
        self.assertEqual(report["formallyEvaluatedHorseCount"], 0)
        for false in ("officialJraVerified", "independentResultsVerified",
                      "historicalBandsCalibrated", "overallPredictionReady",
                      "bettingReady", "autoPurchase", "changesExistingReceipts",
                      "changesExistingTickets", "changesExistingRoi"):
            self.assertFalse(report[false])
        self.assertEqual(report["extraProviderCalls"], 0)
        for private in ("horseRef", "trainerRef", "sireRef", "racekey",
                        "payout", "api_key", "jockeyName", "odds"):
            self.assertNotIn(private, repr(report))

    def test_no_explicit_missing_is_converted_to_zero_or_c(self):
        five, inventory = original()
        for row in inventory["races"]:
            for horse in row["runners"]:
                horse["sourceStates"]["pedigree"] = "no_fields_observed"
            row["remainingFieldCoverage"]["pedigree"] = 0
        report = remaining21_source_gaps(five, inventory)
        for race in report["races"]:
            for horse in race["horses"]:
                self.assertIn("pedigree", horse["missingSourceFields"])
                self.assertEqual(horse["formalGrade"], "未評価")
                self.assertIsNone(horse["formalScore100"])

    def test_missing_staff_and_parentage_remain_unassessed_without_spoofed_points(self):
        five, inventory = original()
        for row in inventory["races"]:
            for horse in row["runners"]:
                horse["sourceStates"]["pedigree"] = "partial_fields_observed"
                horse["sourceStates"]["jockey_stable"] = "no_fields_observed"
            row["remainingFieldCoverage"]["pedigree"] = 0
            row["remainingFieldCoverage"]["jockey_stable"] = 0
        report = remaining21_source_gaps(five, inventory)
        for race in report["races"]:
            self.assertEqual(race["bothPedigreeStaffCompleteCount"], 0)
            for horse in race["horses"]:
                self.assertEqual(horse["pedigreeStaffSourceCoverage16"], 0)
                self.assertIn("parentage_fields_incomplete",
                    horse["pedigreeStaffMissingEvidence"]["pedigree"])
                self.assertIn("jockey_or_trainer_fields_incomplete",
                    horse["pedigreeStaffMissingEvidence"]["jockey_stable"])
                self.assertEqual(horse["pedigreeStaffScores"],
                                 {"pedigree": None, "jockey_stable": None})

    def test_mismatch_and_forged_formal_grade_fail_closed(self):
        edits = [
            lambda f, i: f.update(policyVersion="research-5"),
            lambda f, i: f["factorWeights"].update(pace=20),
            lambda f, i: f.update(officialJraVerified=True),
            lambda f, i: f["races"][0]["horses"][0].update(formalScore100=85),
            lambda f, i: f["races"][0]["horses"][0].update(evidenceScore79=79),
            lambda f, i: i["races"][0]["runners"][0].update(number=18),
            lambda f, i: i["races"][0]["runners"][0]["sourceStates"].update(
                body_condition="body_ready"),
            lambda f, i: i["races"][0]["runners"][0]["sourceStates"].update(
                jockey_stable="unknown"),
            lambda f, i: i["races"][0]["runners"][0].update(overallScore=99),
            lambda f, i: i["races"][0].update(remainingFieldCoverage={}),
            lambda f, i: i.update(verifiedGrades=1),
            lambda f, i: i["races"][0]["runners"][0].update(
                provisionalBands={"training": "S"}),
        ]
        for edit in edits:
            left, right = original()
            edit(left, right)
            with self.subTest(edit=repr(edit)), self.assertRaises(CoverageError):
                remaining21_source_gaps(left, right)


if __name__ == "__main__":
    unittest.main()
