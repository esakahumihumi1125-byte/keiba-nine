"""Synthetic-only tests for real-race grading blockers.

No real JRDB access, outcomes, HTTP calls, or licensed records.
"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_real_assessment_preflight import (
    audit_real_evaluation_preflight, ALWAYS_BLOCKED,
)
from test_jrdb_history_pipeline import context, run_case


def fixtures():
    snapshot = run_case(context())
    return snapshot["allTenFactorSources"], snapshot["evidenceQuality"], snapshot["historyComplete"]


class RealAssessmentPreflightTests(unittest.TestCase):
    def test_explicit_history_materials_are_not_validated_grades(self):
        material, quality, complete = fixtures()
        report = audit_real_evaluation_preflight(
            material, quality, history_complete=complete,
        )
        self.assertEqual(report["version"], "real-assessment-preflight-1")
        self.assertEqual(report["raceCount"], 2)
        self.assertFalse(report["realGradeReady"])
        self.assertFalse(report["realPredictionReady"])
        self.assertFalse(report["purchaseReady"])
        for race in report["races"]:
            self.assertEqual(race["verifiedFactorCount"], 0)
            self.assertEqual(race["blockerCodes"][:4], list(ALWAYS_BLOCKED))
            self.assertFalse(race["realGradeReady"])
            self.assertFalse(race["realPredictionReady"])
            self.assertFalse(race["purchaseReady"])

    def test_missing_history_is_not_treated_as_a_bad_grade(self):
        material, quality, _ = fixtures()
        report = audit_real_evaluation_preflight(
            material, quality, history_complete=False,
        )
        for race in report["races"]:
            self.assertIn("history_lookup_incomplete", race["blockerCodes"])
        self.assertFalse(report["realGradeReady"])
        self.assertNotIn("C", str(report["races"]))

    def test_aggregates_are_redacted(self):
        material, quality, complete = fixtures()
        result = audit_real_evaluation_preflight(
            material, quality, history_complete=complete,
        )
        for secret in ("racekey", "horse_id", "horse_number", "byNumber",
                       "PRIVATE-HORSE", "PAID-SECRET", "LICENSED-PAST",
                       "05264a01", "x-user-key", "api_key"):
            self.assertNotIn(secret, repr(result))

    def test_promoted_status_is_rejected(self):
        for field, value in (
            ("verifiedFactorCount", 10),
            ("realGradeReady", True),
            ("officialJraFinalVerification", True),
            ("raceDayBodyWeightFetched", True),
            ("sourceMaterialSlots", 9),
            ("observationOnlySlots", 7),
            ("runnersWithComparableCourse", 99),
            ("runnersWithKnownGoingComparable", True),
            ("runnersWithIncompleteHistory", -1),
        ):
            material, quality, complete = fixtures()
            material["races"][0][field] = value
            with self.subTest(field=field), self.assertRaises(CoverageError):
                audit_real_evaluation_preflight(
                    material, quality, history_complete=complete,
                )

    def test_cross_source_mismatch_and_bad_buckets_rejected(self):
        for what in ("race", "runner", "bucket", "going"):
            material, quality, complete = fixtures()
            if what == "race":
                quality["races"][0]["track"] = "福島"
            elif what == "runner":
                quality["races"][0]["runnerCount"] = 18
            elif what == "bucket":
                quality["races"][0]["courseComparableSamples"]["threePlus"] = 10
            else:
                material["races"][0]["runnersWithKnownGoingComparable"] = 18
            with self.subTest(what=what), self.assertRaises(CoverageError):
                audit_real_evaluation_preflight(
                    material, quality, history_complete=complete,
                )

    def test_incorrect_history_flag_and_input_mutation_rejected(self):
        material, quality, complete = fixtures()
        old = copy.deepcopy((material, quality))
        audit_real_evaluation_preflight(material, quality, history_complete=complete)
        self.assertEqual((material, quality), old)
        for flag in (None, 1, "true", []):
            with self.subTest(flag=flag), self.assertRaises(CoverageError):
                audit_real_evaluation_preflight(
                    material, quality, history_complete=flag,
                )

    def test_no_races_is_blocked_not_ready(self):
        material, quality, _ = fixtures()
        material["races"] = []
        material["raceCount"] = 0
        quality["races"] = []
        quality["raceCount"] = 0
        out = audit_real_evaluation_preflight(
            material, quality, history_complete=False,
        )
        self.assertEqual(out["raceCount"], 0)
        self.assertFalse(out["realGradeReady"])


if __name__ == "__main__":
    unittest.main()
