"""Synthetic-only test of the bloodline eight-point evidence gate."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_ten_factor_source_inventory import ten_factor_source_inventory
from owner_pedigree_evidence_preflight import (
    pedigree_evidence_preflight, COHORT_MISSING, HOLDOUT_MISSING,
    PARENTAGE_INCOMPLETE,
)
from test_jrdb_ten_factor_source_inventory import fixture
from test_jrdb_history_pipeline import run_case, context


class PedigreeEvidencePreflightTests(unittest.TestCase):
    def setUp(self):
        self.inventory = ten_factor_source_inventory(*fixture())

    def test_parentage_presence_never_scores_even_with_both_parents(self):
        original = copy.deepcopy(self.inventory)
        out = pedigree_evidence_preflight(self.inventory)
        self.assertEqual(self.inventory, original)
        self.assertEqual(out["version"], "owner-pedigree-evidence-preflight-1")
        self.assertEqual(out["weight"], 8)
        self.assertEqual(out["raceCount"], 2)
        self.assertEqual(out["pedigreeGradesVerified"], 0)
        for flag in ("independentCohortAvailable", "temporalValidationComplete",
                     "officialJraVerified", "overallPredictionReady",
                     "bettingReady", "autoPurchase", "changesExistingTickets",
                     "changesExistingReceipts"):
            self.assertFalse(out[flag])
        first = next(row for row in out["races"] if row["track"] == "東京")
        self.assertEqual(first["parentageCompleteCount"], 1)
        one, two = first["horses"]
        self.assertTrue(one["parentageComplete"])
        self.assertEqual(one["missingEvidence"], [COHORT_MISSING, HOLDOUT_MISSING])
        self.assertFalse(two["parentageComplete"])
        self.assertEqual(two["missingEvidence"],
                         [PARENTAGE_INCOMPLETE, COHORT_MISSING, HOLDOUT_MISSING])
        for race in out["races"]:
            self.assertEqual(race["verifiedPedigreeGrades"], 0)
            for horse in race["horses"]:
                self.assertEqual(horse["grade"], "未評価")
                self.assertIsNone(horse["score8"])
                self.assertFalse(horse["bettingReady"])
        for sensitive in ("racekey", "horse_id", "sire_name", "mare_sire_name",
                          "架空父馬A", "auth_key", "raw"):
            self.assertNotIn(sensitive, repr(out))

    def test_invalid_roster_source_promotion_and_coverage_rejected(self):
        mutations = (
            lambda d: d.update(overallPredictionReady=True),
            lambda d: d.update(verifiedGrades=1),
            lambda d: d["races"][-1]["runners"][0].update(number=19),
            lambda d: d["races"][-1]["runners"][1].update(number=1),
            lambda d: d["races"][0]["runners"][0].update(overallScore=99),
            lambda d: d["races"][0]["runners"][0]["sourceStates"].update(
                pedigree="S"),
            lambda d: d["races"][0]["remainingFieldCoverage"].update(
                pedigree=999),
            lambda d: d["races"][0].update(track=""),
        )
        for i, modify in enumerate(mutations):
            with self.subTest(i=i):
                case = copy.deepcopy(self.inventory)
                modify(case)
                with self.assertRaises(CoverageError):
                    pedigree_evidence_preflight(case)

    def test_history_pipeline_readiness_is_unverified_and_has_no_calls(self):
        report = run_case(context())
        out = report["pedigreeEvidencePreflight"]
        inventory = report["tenFactorSourceInventory"]
        self.assertEqual(out, pedigree_evidence_preflight(inventory))
        self.assertEqual(out["raceCount"], report["fiveCoreResearch"]["raceCount"])
        self.assertFalse(out["independentCohortAvailable"])
        self.assertFalse(out["overallPredictionReady"])
        self.assertEqual(report["maxTotalCalls"], 16)


if __name__ == "__main__":
    unittest.main()
