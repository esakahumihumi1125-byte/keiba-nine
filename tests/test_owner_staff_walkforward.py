"""Synthetic, offline, time-cut pair holdout tests; no paid JRDB reads."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_staff_walkforward import staff_pair_walkforward_preflight
from owner_support_six_cohort_study import SupportCohortError
from test_owner_support_six_cohort_study import TARGET, past


def history(count=25):
    return [past(i) for i in range(1, count + 1)]


class StaffPairWalkforwardTests(unittest.TestCase):
    def test_old_train_new_holdout_pair_is_only_descriptive(self):
        target = copy.deepcopy(TARGET)
        rows = history()
        before = copy.deepcopy((target, rows))
        result = staff_pair_walkforward_preflight(target, rows)
        self.assertEqual((target, rows), before)
        self.assertEqual(result["eligibleConditionMatchedRaces"], 25)
        self.assertEqual(result["trainingRaceCount"], 17)
        self.assertEqual(result["holdoutRaceCount"], 8)
        self.assertEqual(result["holdoutPairComparisonRaces"], 8)
        self.assertEqual(result["holdoutPairComparisonRunners"], 48)
        self.assertTrue(result["descriptiveComparisonCoverageMet"])
        self.assertLess(result["pairTopThreeBrier"], result["naiveTopThreeBrier"])
        self.assertFalse(result["claimedResultPublicationTimesIndependentlyVerified"])
        self.assertFalse(result["independentJraVerified"])
        self.assertFalse(result["causalPairEffectVerified"])
        self.assertFalse(result["outOfTimePerformanceOfficiallyValidated"])
        self.assertEqual(result["formalTenPointGrade"], "未評価")
        self.assertIsNone(result["formalTenPointScore"])
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["sourceReadCount"], 0)
        self.assertFalse(result["changesExistingRoi"])
        for secret in ("JOCKEY001", "STABLE001", "HORSE0101",
                       "horseRef", "resultAvailableAt", "runners"):
            self.assertNotIn(secret, repr(result))

    def test_small_cohort_stays_without_brier_or_grade(self):
        result = staff_pair_walkforward_preflight(TARGET, history(12))
        self.assertEqual(result["trainingRaceCount"], 8)
        self.assertFalse(result["descriptiveComparisonCoverageMet"])
        self.assertIsNone(result["pairTopThreeBrier"])
        self.assertIsNone(result["naiveTopThreeBrier"])
        self.assertIsNone(result["formalTenPointScore"])

    def test_no_exact_pair_never_borrows_individual_rider_and_trainer(self):
        rows = history()
        # Train riders and trainers have plenty of *individual* starts,
        # but only with the opposite partner. Holdout uses new pairs.
        for race in rows[:17]:
            for h in race["runners"]:
                h["trainerRef"] = ("STABLE002" if h["number"] <= 3
                                   else "STABLE001")
        result = staff_pair_walkforward_preflight(TARGET, rows)
        self.assertEqual(result["trainingRaceCount"], 17)
        self.assertEqual(result["holdoutRaceCount"], 8)
        self.assertEqual(result["holdoutPairComparisonRunners"], 0)
        self.assertEqual(result["holdoutWithoutQualifiedPairRunners"], 48)
        self.assertFalse(result["descriptiveComparisonCoverageMet"])
        self.assertIsNone(result["pairTopThreeBrier"])
        self.assertIsNone(result["formalTenPointScore"])

    def test_missing_mismatched_and_future_rows_not_counted_as_training(self):
        rows = history()
        rows.append(past(26, day="2026-11-13",
                         availability="2026-11-13T23:30:00+09:00"))
        rows.append(past(27, day="2026-10-27", klass="C3"))
        report = staff_pair_walkforward_preflight(TARGET, rows)
        self.assertEqual(report["eligibleConditionMatchedRaces"], 25)
        self.assertEqual(report["futureOrUnpublishedRacesExcluded"], 1)
        self.assertEqual(report["otherConditionRacesExcluded"], 1)

    def test_late_result_publication_is_not_usable_in_earlier_holdout(self):
        baseline = staff_pair_walkforward_preflight(TARGET, history())
        rows = history()
        # First training race exists, but its result becomes available only
        # after the first six holdout races start (still before target capture).
        rows[0]["resultAvailableAt"] = "2026-10-24T13:00:00+09:00"
        delayed = staff_pair_walkforward_preflight(TARGET, rows)
        self.assertEqual(delayed["holdoutPairComparisonRunners"], 48)
        self.assertNotEqual(delayed["pairTopThreeBrier"],
                            baseline["pairTopThreeBrier"])

    def test_bad_race_identity_result_clocks_and_duplicates_fail_closed(self):
        scenarios = (
            lambda rows: rows.append(copy.deepcopy(rows[0])),
            lambda rows: rows[0]["runners"][1].update(finish=1),
            lambda rows: rows[0].update(
                resultAvailableAt="2026-10-01T11:59:00+09:00"),
            lambda rows: rows[0]["runners"][0].update(trainerRef="bad id!"),
            lambda rows: rows[0].update(officialVerified=True),
        )
        for mutation in scenarios:
            rows = history()
            mutation(rows)
            with self.subTest(mutation=repr(mutation)), self.assertRaises(
                    SupportCohortError):
                staff_pair_walkforward_preflight(TARGET, rows)

    def test_no_history_remains_unrated(self):
        report = staff_pair_walkforward_preflight(TARGET, [])
        self.assertEqual(report["trainingRaceCount"], 0)
        self.assertEqual(report["holdoutRaceCount"], 0)
        self.assertEqual(report["holdoutPairComparisonRunners"], 0)
        self.assertIsNone(report["pairTopThreeBrier"])
        self.assertIsNone(report["formalTenPointScore"])


if __name__ == "__main__":
    unittest.main()
