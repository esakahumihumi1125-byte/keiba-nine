"""Pure, synthetic 10-factor gate regression tests. No provider or bet calls."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from owner_full_ten_factor import full_ten_factor_preview

AS_OF = "2099-01-01T09:00:00+09:00"
NOW = "2099-01-01T09:15:00+09:00"
OFF = "2099-01-01T10:00:00+09:00"
OFFICIAL = {
    "jra_starters_verified": True,
    "jra_scratches_verified": True,
    "jra_going_verified": True,
    "jra_posttime_verified": True,
}
CHANGES = ({}, {"recent": "A"}, {"pedigree": "A"},
           {"ground": "A"}, {"course_distance": "A"},
           {"training": "A"}, {"training": "A", "ground": "A"},
           {"training": "A", "course_distance": "A"})


def horse(number, changes=None):
    grades = {key: "S" for key in FACTORS}
    grades.update(changes or {})
    return {
        "number": number,
        "assessments": {
            key: {
                "grade": grade, "reason": "Prestart independent evidence",
                "evidence": [{
                    "sourceId": "test-original", "reference": "fixture",
                    "availableAt": AS_OF,
                }],
            }
            for key, grade in grades.items()
        },
    }


def fixture():
    return {
        "mode": "owner_verified_prestart_v1",
        "asOf": AS_OF, "offAt": OFF,
        "independentJra": dict(OFFICIAL),
        "assessmentValidated": True, "predictionValidated": True,
        "horses": [horse(i + 1, change) for i, change in enumerate(CHANGES)],
    }


class FullTenFactorGateTests(unittest.TestCase):
    def test_full_evidenced_eight_horse_preview_40_unique_tickets(self):
        source = fixture()
        untouched = copy.deepcopy(source)
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, untouched)
        self.assertEqual(result["status"], "review_only")
        self.assertTrue(result["overallReady"])
        self.assertFalse(result["bettingReady"])
        self.assertFalse(result["publishable"])
        self.assertEqual([r["number"] for r in result["ranking"]], list(range(1, 9)))
        self.assertEqual(result["ranking"][0]["score100"], 100)
        self.assertEqual(result["ranking"][0]["overallGrade"], "S")
        self.assertEqual(result["trifecta"]["points"], 40)
        self.assertEqual(result["trifecta"]["totalStakeYen"], 4000)
        self.assertEqual(len(set(map(tuple, result["trifecta"]["tickets"]))), 40)
        self.assertTrue(all(len(set(t)) == 3 for t in result["trifecta"]["tickets"]))

    def test_missing_eighth_factor_never_normalizes_partial_grade(self):
        source = fixture()
        del source["horses"][0]["assessments"]["ground"]
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["status"], "missing_evidence")
        self.assertFalse(result["overallReady"])
        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["missingByNumber"], {1: ["ground"]})
        self.assertEqual(result["trifecta"]["points"], 0)

    def test_source_available_after_prediction_cutoff_is_unassessed(self):
        source = fixture()
        source["horses"][1]["assessments"]["pace"]["evidence"][0]["availableAt"] = (
            "2099-01-01T09:10:00+09:00")
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["status"], "missing_evidence")
        self.assertEqual(result["missingByNumber"], {2: ["pace"]})

    def test_no_caller_supplied_approval_means_no_trifecta(self):
        for absent in ("predictionValidated", "assessmentValidated"):
            source = fixture()
            source[absent] = False
            result = full_ten_factor_preview(source, now=NOW)
            self.assertEqual(result["status"], "research_only")
            self.assertTrue(result["overallReady"])
            self.assertEqual(result["trifecta"]["points"], 0)
            self.assertEqual(result["trifecta"]["status"], "not_ready")
        source = fixture()
        source["independentJra"]["jra_scratches_verified"] = False
        result = full_ten_factor_preview(source, now=NOW)
        self.assertIn("jra_scratches_verified", result["trifecta"]["blockingEvidence"])
        self.assertEqual(result["trifecta"]["points"], 0)

    def test_cutoff_ties_never_split_using_horse_number(self):
        source = fixture()
        source["horses"] = [horse(i) for i in range(1, 9)]
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["status"], "ambiguous_score_cutoff")
        self.assertEqual(result["trifecta"]["points"], 0)
        self.assertEqual([h["rank"] for h in result["ranking"]], [1] * 8)

    def test_stale_or_poststart_snapshot_cannot_recalculate(self):
        for clock in (OFF, "2099-01-01T11:00:00+09:00",
                      "2099-01-01T08:59:00+09:00"):
            result = full_ten_factor_preview(fixture(), now=clock)
            self.assertEqual(result["status"], "outside_prestart_window")
            self.assertEqual(result["ranking"], [])
            self.assertEqual(result["trifecta"]["points"], 0)

    def test_rebound_horse_is_not_penalized_by_finishing_position(self):
        source = fixture()
        source["horses"][0]["assessments"]["recent"]["grade"] = "C"
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["ranking"][0]["number"], 2)
        self.assertEqual(result["ranking"][1]["number"], 3)
        self.assertEqual(result["ranking"][2]["number"], 1)
        self.assertEqual(result["ranking"][2]["score100"], 97)
        self.assertEqual(result["ranking"][2]["overallGrade"], "S")

    def test_duplicate_numbers_and_unrecognized_factors_are_rejected(self):
        source = fixture()
        source["horses"][1]["number"] = 1
        with self.assertRaises(CoverageError):
            full_ten_factor_preview(source, now=NOW)
        source = fixture()
        source["horses"][0]["assessments"]["odds"] = {
            "grade": "S", "reason": "invalid"}
        with self.assertRaises(CoverageError):
            full_ten_factor_preview(source, now=NOW)


if __name__ == "__main__":
    unittest.main()
