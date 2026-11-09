"""Synthetic source passport tests. No JRDB calls, keys, odds or real picks."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_day_source_passport import (
    owner_day_source_passport, safe_owner_day_source_passport, VERSION,
)
from owner_ten_factor_contract import ten_factor_contract
from jrdb_owner_draft_materials import unavailable
from jrdb_race_context import audit_race_context
from test_jrdb_owner_auto_draft import generate, programme, DAY


def synthetic_report():
    draft = generate()
    draft["tenFactorPreview"] = ten_factor_contract(draft)
    draft["sourceMaterials"] = unavailable()
    draft["raceContext"] = audit_race_context(programme(), [], DAY)
    return draft


class OwnerDaySourcePassportTests(unittest.TestCase):
    def test_all_ten_factors_remain_unverified_with_four_source_reads(self):
        report = synthetic_report()
        untouched = copy.deepcopy(report)
        out = owner_day_source_passport(report)
        self.assertEqual(report, untouched)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(out["raceCount"], 1)
        self.assertTrue(out["sourceAuditAvailable"])
        self.assertEqual(out["newProviderRequests"], 0)
        self.assertFalse(out["independentJraVerified"])
        self.assertFalse(out["purchaseReady"])
        self.assertEqual(out["gradedFactors"], 0)
        row = out["races"][0]
        self.assertEqual(row["provisionalTrainingCount"], 7)
        self.assertEqual(row["provisionalRecentCount"], 7)
        self.assertEqual(row["programmeRunnerCount"], 7)
        self.assertFalse(row["sourceMaterialsObserved"])
        self.assertIsNone(row["additionalFieldCounts"])
        self.assertEqual(row["raceDayBodyweightVerifiedCount"], 0)
        self.assertEqual(len(row["unassessedFactorKeys"]), 8)
        self.assertFalse(row["completeTenFactorReady"])
        self.assertNotIn("horse_name", str(out))
        self.assertNotIn("racekey", str(out))
        self.assertNotIn("trainingGrade", str(out))

    def test_observed_fields_do_not_become_grades_or_weight(self):
        report = synthetic_report()
        report["sourceMaterials"] = {
            "version": "owner-draft-material-coverage-1",
            "status": "observed", "observedFactorSlots": 8,
            "gradedNewFactors": 0, "officialJraVerified": False,
            "races": [{
                "track": "東京", "race": 1, "runnerCount": 7,
                "counts": {
                    "pedigree": 7, "drawWeight": 7,
                    "rotation": 4, "personnel": 6,
                    "body": 7, "pastCorner": 6,
                },
            }],
        }
        report["raceContext"]["races"][0]["goingAvailable"] = False
        out = owner_day_source_passport(report)
        row = out["races"][0]
        self.assertTrue(row["sourceMaterialsObserved"])
        self.assertEqual(row["additionalFieldCounts"]["pedigree"], 7)
        self.assertEqual(row["additionalFieldCounts"]["body"], 7)
        self.assertEqual(row["raceDayBodyweightVerifiedCount"], 0)
        self.assertEqual(row["verifiedFactorCount"], 0)
        self.assertEqual(out["gradedFactors"], 0)
        self.assertFalse(row["goingContextPresent"])

    def test_duplicate_or_wrong_roster_fails_closed(self):
        report = synthetic_report()
        report["sourceMaterials"] = {
            "version": "owner-draft-material-coverage-1",
            "status": "observed", "observedFactorSlots": 8,
            "gradedNewFactors": 0, "officialJraVerified": False,
            "races": [{
                "track": "東京", "race": 1, "runnerCount": 8,
                "counts": {k: 0 for k in (
                    "pedigree", "drawWeight", "rotation",
                    "personnel", "body", "pastCorner")},
            }],
        }
        with self.assertRaises(CoverageError):
            owner_day_source_passport(report)
        safe = safe_owner_day_source_passport(report)
        self.assertFalse(safe["sourceAuditAvailable"])
        self.assertEqual(safe["newProviderRequests"], 0)

    def test_injected_grade_or_extra_race_rejected(self):
        report = synthetic_report()
        report["tenFactorPreview"]["races"][0]["horses"][0]["grades"]["pace"] = "S"
        with self.assertRaises(CoverageError):
            owner_day_source_passport(report)
        self.assertFalse(safe_owner_day_source_passport(report)["sourceAuditAvailable"])
        report = synthetic_report()
        report["raceContext"]["races"][0]["race"] = 11
        with self.assertRaises(CoverageError):
            owner_day_source_passport(report)

    def test_held_race_has_no_reconstructed_postoff_horse_grade(self):
        from datetime import datetime
        from test_jrdb_owner_auto_draft import JST
        draft = generate(now=datetime(2099, 1, 1, 12, 10, tzinfo=JST))
        draft["tenFactorPreview"] = ten_factor_contract(draft)
        draft["sourceMaterials"] = unavailable()
        draft["raceContext"] = audit_race_context(programme(), [], DAY)
        out = owner_day_source_passport(draft)
        row = out["races"][0]
        self.assertEqual(row["draftStatus"], "hold")
        self.assertEqual(row["provisionalTrainingCount"], 0)
        self.assertEqual(row["provisionalRecentCount"], 0)
        self.assertEqual(row["verifiedFactorCount"], 0)
        self.assertFalse(row["completeTenFactorReady"])


if __name__ == "__main__":
    unittest.main()
