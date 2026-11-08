"""Private factor-preflight coverage: synthetic source counts, never actual grades."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_evidence_readiness import audit_evidence_coverage
from jrdb_factor_preflight import audit_assessment_preflight
from evaluation_policy import FACTORS, CORE, POLICY_VERSION
from test_jrdb_evidence_readiness import sample


def fixture():
    p, e, t, z = sample()
    return audit_evidence_coverage(p, e, t, z, "20261101")


class AssessmentPreflightTests(unittest.TestCase):
    def test_ten_factors_are_ungraded_even_when_some_records_exist(self):
        result = audit_assessment_preflight(fixture())
        self.assertEqual(result["factorCount"], 10)
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["readyForPrediction"], 0)
        self.assertEqual(result["gradedFactors"], 0)
        self.assertEqual(set(result["coreFactors"]), CORE)
        self.assertEqual(result["policyVersion"], POLICY_VERSION)
        for race in result["races"]:
            self.assertEqual(set(race["factors"]), set(FACTORS))
            self.assertEqual(len(race["pendingAssessments"]), 10)
            self.assertFalse(race["readyForPrediction"])
            self.assertTrue(all(x["grade"] == "未評価" and not x["assessmentComplete"]
                                for x in race["factors"].values()))

    def test_source_presence_not_source_truth(self):
        tokyo, kyoto = audit_assessment_preflight(fixture())["races"]
        self.assertEqual(tokyo["factors"]["training"]["sourceStatus"],
                         "source_record_count_matches")
        self.assertEqual(tokyo["factors"]["recent"]["sourceStatus"],
                         "partial_source_records")
        self.assertEqual(kyoto["factors"]["training"]["sourceStatus"],
                         "unknown_or_not_applicable")
        self.assertEqual(kyoto["factors"]["recent"]["sourceStatus"],
                         "unknown_or_not_applicable")
        for row in (tokyo, kyoto):
            self.assertEqual(row["factors"]["ground"]["sourceStatus"],
                             "not_mapped_from_provider")
            self.assertEqual(row["factors"]["course_distance"]["sourceStatus"],
                             "not_mapped_from_provider")

    def test_no_paid_horse_content_is_exposed(self):
        audit = fixture()
        audit["races"][0]["horse_name"] = "PRIVATE-HORSE"
        audit["races"][0]["horse_id"] = "secret123"
        report = repr(audit_assessment_preflight(audit))
        for raw in ("NONPUBLIC", "PRIVATE-HORSE", "secret123", "2328aaa95a05"):
            self.assertNotIn(raw, report)

    def test_invalid_or_conflicting_counts_rejected(self):
        for key, value in (("observedEntries", 19), ("observedEntries", -1),
                           ("observedEntries", True), ("trainingRecords", 5),
                           ("pastRunRecords", 3), ("trainingRecords", None),
                           ("expectedRunners", 19)):
            with self.subTest(key=key, value=value):
                audit = fixture()
                audit["races"][0][key] = value
                with self.assertRaises(ValueError):
                    audit_assessment_preflight(audit)

    def test_duplicate_race_rejected(self):
        audit = fixture()
        audit["races"][1]["track"] = "東京"
        with self.assertRaises(ValueError):
            audit_assessment_preflight(audit)

    def test_no_provider_records_never_creates_scores(self):
        p, e, t, z = sample()
        audit = audit_evidence_coverage(p, e, [], [], "20261101")
        result = audit_assessment_preflight(audit)
        self.assertEqual(result["readyForPrediction"], 0)
        self.assertTrue(all(r["gradedCount"] == 0 for r in result["races"]))
        self.assertNotIn("S/A/B/Cを算出", result["note"])

    def test_empty_race_day_is_not_full_program_confirmation(self):
        result = audit_assessment_preflight({"races": []})
        self.assertEqual(result["raceCount"], 0)
        self.assertEqual(result["readyForPrediction"], 0)

    def test_input_immutability(self):
        inp = fixture()
        before = copy.deepcopy(inp)
        audit_assessment_preflight(inp)
        self.assertEqual(inp, before)


if __name__ == "__main__":
    unittest.main()
