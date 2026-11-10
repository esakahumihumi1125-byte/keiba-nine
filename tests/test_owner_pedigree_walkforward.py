"""Synthetic, no-provider pedigree holdout checks. Nothing is bet or persisted."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_pedigree_walkforward import pedigree_walkforward_preflight
from owner_pedigree_cohort_study import PedigreeCohortError
from test_owner_pedigree_cohort_study import TARGET


def finished_day(i):
    date = f"2026-10-{i:02d}"
    return {
        "raceDate": date, "track": "京都", "race": 1,
        "scheduledOffAt": date + "T12:00:00+09:00",
        "resultAvailableAt": date + "T12:30:00+09:00",
        "surface": "芝", "distanceM": 2000, "going": "重",
        "runners": [{
            "number": n,
            "horseRef": f"HORSE{i:02d}{n:02d}",
            "sireRef": "SIRE0001" if n <= 3 else "SIRE0002",
            "damsireRef": "DAM00001" if n <= 3 else "DAM00002",
            "finish": n,
        } for n in range(1, 7)]
    }


def history():
    return [finished_day(i) for i in range(1, 31)]


class PedigreeWalkforwardTests(unittest.TestCase):
    def test_fixed_chronological_holdout_without_any_source_lookups(self):
        past = history()
        before = copy.deepcopy((TARGET, past))
        result = pedigree_walkforward_preflight(TARGET, past)
        self.assertEqual((TARGET, past), before)
        self.assertEqual(result["policyVersion"], "research-6")
        self.assertEqual(result["factor"], "pedigree")
        self.assertEqual(result["weight"], 6)
        self.assertEqual(result["trainingRaceCount"], 21)
        self.assertEqual(result["holdoutRaceCount"], 9)
        self.assertEqual(result["holdoutComparisonRaces"], 9)
        self.assertEqual(result["holdoutComparisonRunners"], 54)
        self.assertEqual(result["comparedBySire"], 54)
        self.assertEqual(result["comparedByDamsire"], 0)
        self.assertTrue(result["descriptiveComparisonCoverageMet"])
        self.assertLess(result["pedigreeTopThreeBrier"],
                        result["naiveTopThreeBrier"])
        self.assertFalse(result["independentJraVerified"])
        self.assertFalse(result["prospectiveResultCalibrationVerified"])
        self.assertFalse(result["horseQualityAndConfoundingAdjusted"])
        self.assertEqual(result["formalPedigreeGrade"], "未評価")
        self.assertIsNone(result["formalPedigreeScore6"])
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["providerReads"], 0)
        for banned in ("HORSE", "SIRE0001", "DAM00001",
                       "horseRef", "sireRef", "damsireRef", "racekey"):
            self.assertNotIn(banned, repr(result))

    def test_holdout_never_updates_training_and_no_pair_borrowing(self):
        past = history()
        for row in past[21:]:
            for horse in row["runners"]:
                horse["sireRef"] = "NOVELSIRE"
                horse["damsireRef"] = "NOVELDAM"
        out = pedigree_walkforward_preflight(TARGET, past)
        self.assertFalse(out["descriptiveComparisonCoverageMet"])
        self.assertEqual(out["holdoutComparisonRunners"], 0)
        self.assertEqual(out["holdoutNoQualifiedLineageRunners"], 54)
        self.assertIsNone(out["pedigreeTopThreeBrier"])
        self.assertIsNone(out["naiveTopThreeBrier"])

    def test_repeated_horse_identity_not_used_for_own_validation(self):
        past = history()
        past[21]["runners"][0]["horseRef"] = past[0]["runners"][0]["horseRef"]
        out = pedigree_walkforward_preflight(TARGET, past)
        self.assertEqual(out["heldOutPreviouslySeenHorseRunnersExcluded"], 1)
        self.assertEqual(out["holdoutComparisonRunners"], 53)
        self.assertTrue(out["descriptiveComparisonCoverageMet"])

    def test_train_race_results_published_after_holdout_off_excluded(self):
        original = pedigree_walkforward_preflight(TARGET, history())
        delayed = history()
        delayed[0]["resultAvailableAt"] = "2026-11-13T18:00:00+09:00"
        changed = pedigree_walkforward_preflight(TARGET, delayed)
        self.assertEqual(changed["trainingRaceCount"], 21)
        self.assertEqual(changed["holdoutRaceCount"], 9)
        self.assertEqual(changed["holdoutComparisonRunners"], 54)
        self.assertNotEqual(changed["pedigreeTopThreeBrier"],
                            original["pedigreeTopThreeBrier"])

    def test_no_metric_when_training_or_holdout_insufficient(self):
        small = pedigree_walkforward_preflight(TARGET, history()[:12])
        self.assertFalse(small["descriptiveComparisonCoverageMet"])
        self.assertIsNone(small["pedigreeTopThreeBrier"])
        self.assertIsNone(small["naiveTopThreeBrier"])

    def test_noncomparable_or_future_races_are_excluded(self):
        past = history()
        other = finished_day(31)
        other["raceDate"] = "2026-11-01"
        other["scheduledOffAt"] = "2026-11-01T12:00:00+09:00"
        other["resultAvailableAt"] = "2026-11-01T12:30:00+09:00"
        other["track"] = "東京"
        later = finished_day(32)
        later["raceDate"] = "2026-11-14"
        later["scheduledOffAt"] = "2026-11-14T12:00:00+09:00"
        later["resultAvailableAt"] = "2026-11-14T12:30:00+09:00"
        out = pedigree_walkforward_preflight(TARGET, past + [other, later])
        self.assertEqual(out["differentConditionsExcluded"], 1)
        self.assertEqual(out["futureOrUnpublishedExcluded"], 1)
        self.assertEqual(out["holdoutComparisonRunners"], 54)

    def test_duplicate_and_invalid_source_rejected(self):
        past = history()
        with self.assertRaises(PedigreeCohortError):
            pedigree_walkforward_preflight(TARGET, past + [copy.deepcopy(past[0])])
        invalid = history()
        invalid[2]["runners"][0]["finish"] = 2
        with self.assertRaises(PedigreeCohortError):
            pedigree_walkforward_preflight(TARGET, invalid)
        invalid = history()
        invalid[0]["resultAvailableAt"] = "2026-10-01T11:00:00+09:00"
        with self.assertRaises(PedigreeCohortError):
            pedigree_walkforward_preflight(TARGET, invalid)
        invalid = copy.deepcopy(TARGET)
        invalid["capturedAt"] = "2026-11-14T14:00:00+09:00"
        with self.assertRaises(PedigreeCohortError):
            pedigree_walkforward_preflight(invalid, history())


if __name__ == "__main__":
    unittest.main()
