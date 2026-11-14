"""Synthetic-only tests for evidence-gated 0.01-point research arithmetic."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from evaluation_policy import OWNER_FORMAL_FACTORS as WEIGHTS
from jrdb_coverage import CoverageError
from owner_granular_100_study import (
    MODE, VERSION, factor_grade, research_granular_100,
)

AS_OF = "2099-01-01T09:00:00+09:00"
OFF = "2099-01-01T10:00:00+09:00"


def horse(number, training=None):
    assessments = {}
    for key, weight in WEIGHTS.items():
        points = weight * 100 if key != "training" or training is None else training
        assessments[key] = {
            "pointsCenti": points,
            "reason": "PRESTART SYNTHETIC rubric evidence",
            "evidence": [{
                "sourceId": "PRIVATE-INTERNAL-EVIDENCE",
                "reference": "synthetic-rubric-fixture",
                "availableAt": AS_OF,
            }],
        }
    return {"number": number, "assessments": assessments}


def snapshot(horses=None):
    return {
        "mode": MODE, "recordType": "test", "asOf": AS_OF, "offAt": OFF,
        "horses": horses if horses is not None else [horse(2, 2750),horse(1, 2950)],
    }


class OwnerGranular100Tests(unittest.TestCase):
    def test_same_s_can_have_distinct_supported_internal_scores(self):
        source = snapshot()
        untouched = copy.deepcopy(source)
        result = research_granular_100(source)
        self.assertEqual(source, untouched)
        self.assertEqual(result["version"], VERSION)
        self.assertEqual(result["policyVersion"], "research-6")
        self.assertTrue(result["scoreReady"])
        self.assertEqual([h["number"] for h in result["ranking"]], [1, 2])
        self.assertEqual([h["score100"] for h in result["ranking"]], [99.5,97.5])
        self.assertEqual([h["overallGrade"] for h in result["ranking"]], ["S","S"])
        self.assertEqual([h["factorGrades"]["training"] for h in result["ranking"]], ["S","S"])
        self.assertEqual([h["rank"] for h in result["ranking"]], [1,2])
        self.assertEqual(result["factorCount"], 10)
        self.assertEqual(result["totalWeight"], 100)
        self.assertFalse(result["formalPrediction"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["tickets"], [])
        self.assertEqual(result["purchases"], [])
        self.assertEqual(result["newProviderCalls"], 0)
        self.assertFalse(result["changesExistingReceipts"])
        self.assertFalse(result["changesExistingRoi"])
        self.assertNotIn("PRIVATE-INTERNAL-EVIDENCE", repr(result))
        self.assertNotIn("synthetic-rubric-fixture", repr(result))

    def test_training_display_bands_have_expected_integer_cutoffs(self):
        for points, expected in [
            (3000,"S"), (2700,"S"), (2699,"A"), (2200,"A"),
            (2199,"B"), (1500,"B"), (1499,"C"), (0,"C")
        ]:
            with self.subTest(points=points):
                self.assertEqual(factor_grade(points, 30), expected)
        # One-point factors can still be represented without forced 4-grade
        # integer collisions by using a hundredth of a point internally.
        self.assertEqual(factor_grade(90,1),"S")
        self.assertEqual(factor_grade(80,1),"A")
        self.assertEqual(factor_grade(50,1),"B")
        self.assertEqual(factor_grade(49,1),"C")

    def test_identical_points_stay_exactly_tied(self):
        result = research_granular_100(snapshot([horse(9,2750),horse(3,2750)]))
        self.assertEqual([h["number"] for h in result["ranking"]],[3,9])
        self.assertEqual([h["rank"] for h in result["ranking"]],[1,1])

    def test_missing_or_late_evidence_never_creates_a_partial_rank(self):
        for change in ("missing","late","unverified"):
            with self.subTest(change=change):
                source = snapshot()
                item = source["horses"][0]["assessments"]["pace"]
                if change == "missing":
                    del source["horses"][0]["assessments"]["pace"]
                elif change == "late":
                    item["evidence"][0]["availableAt"] = "2099-01-01T09:10:00+09:00"
                else:
                    item["reason"] = " "
                original = copy.deepcopy(source)
                result = research_granular_100(source)
                self.assertEqual(source, original)
                self.assertEqual(result["status"], "missing_evidence")
                self.assertEqual(result["missingByNumber"], {2:["pace"]})
                self.assertEqual(result["ranking"], [])
                self.assertEqual(result["tickets"], [])
                self.assertFalse(result["scoreReady"])
                self.assertNotIn("PRIVATE-INTERNAL-EVIDENCE", repr(result))

    def test_bogus_points_or_claimed_band_fail_closed(self):
        for points in (-1, 3001, 30.5, True, "2999", None):
            with self.subTest(points=repr(points)):
                source=snapshot()
                source["horses"][0]["assessments"]["training"]["pointsCenti"]=points
                with self.assertRaises(CoverageError):
                    research_granular_100(source)
        contradiction = snapshot()
        contradiction["horses"][0]["assessments"]["training"]["grade"]="B"
        with self.assertRaises(CoverageError):
            research_granular_100(contradiction)

    def test_live_provider_or_late_race_is_not_eligible(self):
        for invalid in (
            {"recordType": "live"},
            {"mode": "owner_verified_prestart_v1"},
        ):
            with self.subTest(value=invalid):
                with self.assertRaises(CoverageError):
                    research_granular_100({**snapshot(), **invalid})
        for off in (AS_OF,"2099-01-01T08:59:59+09:00","not-a-date"):
            with self.subTest(off=off):
                with self.assertRaises(CoverageError):
                    research_granular_100({**snapshot(), "offAt": off})

    def test_unknown_factor_or_duplicate_runner_is_not_a_tiebreaker(self):
        source=snapshot()
        source["horses"][0]["assessments"]["odds"] = {
            "pointsCenti":99,
        }
        with self.assertRaises(CoverageError):
            research_granular_100(source)
        source=snapshot([horse(2),horse(2)])
        with self.assertRaises(CoverageError):
            research_granular_100(source)


if __name__ == "__main__":
    unittest.main()
