"""Offline and synthetic six-point cohort tests; no credentials, no paid data."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_support_six_cohort_study import (
    support_six_cohort_study, SupportCohortError
)

TARGET = {
    "raceDate": "2026-11-14", "track": "京都", "race": 7,
    "capturedAt": "2026-11-13T20:00:00+09:00",
    "scheduledOffAt": "2026-11-14T13:25:00+09:00",
    "surface": "芝", "distanceM": 2000, "going": "重", "classCode": "C2",
    "runners": [
        {"number": i, "frame": i, "carriedKg": 55.0 if i <= 3 else 58.0,
         "jockeyRef": "JOCKEY001" if i <= 3 else "JOCKEY002",
         "trainerRef": "STABLE001" if i <= 3 else "STABLE002",
         "lastRunDate": "2026-10-21" if i != 6 else None}
        for i in range(1, 7)
    ],
}


def past(n, *, day=None, track="京都", going="重", klass="C2",
         surface="芝", distance=2000, availability=None):
    day = day or f"2026-10-{n:02d}"
    return {
        "raceDate": day, "track": track, "race": 1,
        "scheduledOffAt": day + "T12:00:00+09:00",
        "resultAvailableAt": availability or day + "T12:20:00+09:00",
        "surface": surface, "distanceM": distance, "going": going,
        "classCode": klass,
        "runners": [
            {"number": i, "frame": i, "carriedKg": 55.0 if i <= 3 else 58.0,
             "jockeyRef": "JOCKEY001" if i <= 3 else "JOCKEY002",
             "trainerRef": "STABLE001" if i <= 3 else "STABLE002",
             "lastRunDate": "2026-09-10",
             "horseRef": f"HORSE{n:02d}{i:02d}", "finish": i}
            for i in range(1, 7)
        ],
    }


class SupportSixCohortTests(unittest.TestCase):
    def test_full_cohort_descriptive_only_and_inputs_unchanged(self):
        history = [past(n) for n in range(1, 13)]
        original = copy.deepcopy((TARGET, history))
        report = support_six_cohort_study(TARGET, history)
        self.assertEqual((TARGET, history), original)
        self.assertEqual(report["weightTotal"], 14)
        self.assertEqual(report["factorWeights"], {
            "draw_weight": 3, "jockey_stable": 10, "rotation": 1})
        self.assertEqual(report["pastRacesEligible"], 12)
        self.assertEqual(report["matchingBaseline"]["observedRunners"], 72)
        self.assertEqual(report["matchingBaseline"]["observedWins"], 12)
        self.assertEqual(report["matchingBaseline"]["observedTop3"], 36)
        self.assertEqual([r["number"] for r in report["horses"]],
                         [1, 2, 3, 4, 5, 6])
        inner = report["horses"][0]["cohortEvidence"]
        self.assertEqual(inner["frame"]["observedRunners"], 24)
        self.assertIsNone(inner["frame"]["observedWinRatePercent"])
        self.assertEqual(inner["relativeWeight"]["observedRunners"], 36)
        self.assertEqual(inner["relativeWeight"]["observedWins"], 12)
        self.assertEqual(inner["relativeWeight"]["observedWinRatePercent"], 33.33)
        self.assertEqual(inner["jockey"]["observedWins"], 12)
        self.assertEqual(inner["trainer"]["observedTop3"], 36)
        self.assertEqual(inner["jockeyTrainerPair"]["observedRunners"], 36)
        self.assertEqual(inner["jockeyTrainerPair"]["observedWins"], 12)
        self.assertEqual(inner["jockeyTrainerPair"]["observedTop3"], 36)
        self.assertEqual(inner["jockeyTrainerPair"]["distinctHistoricalRaces"], 12)
        self.assertTrue(inner["jockeyTrainerPair"]["minimumCoverageMet"])
        self.assertTrue(report["horses"][0]["jockeyTrainerPairCoverageMet"])
        self.assertTrue(report["horses"][0]["jockeyAndTrainerIndividualCoverageMet"])
        self.assertFalse(report["horses"][0]["pairEffectIndependentlyValidated"])
        self.assertEqual(inner["rotation"]["observedRunners"], 72)
        self.assertTrue(inner["rotation"]["minimumCoverageMet"])
        self.assertEqual(report["horses"][-1]["cohortEvidence"]["rotation"]
                         ["observedRunners"], 0)
        self.assertFalse(report["horses"][-1]["rotationSourceAvailable"])
        for row in report["horses"]:
            self.assertEqual(row["grades"], {
                "draw_weight": "未評価", "jockey_stable": "未評価", "rotation": "未評価"})
            self.assertEqual(row["scores"], {
                "draw_weight": None, "jockey_stable": None, "rotation": None})
            self.assertFalse(row["independentSourcesVerified"])
        self.assertEqual(report["verifiedFactorCount"], 0)
        self.assertFalse(report["independentJraVerified"])
        self.assertFalse(report["holdoutValidationComplete"])
        self.assertFalse(report["overallPredictionReady"])
        self.assertFalse(report["bettingReady"])
        self.assertFalse(report["changesExistingRoi"])
        self.assertEqual(report["sourceReadCount"], 0)
        for private in ("JOCKEY001", "STABLE001", "HORSE",
                        "horseRef", "resultAvailableAt", "trifectaTickets",
                        "payout"):
            self.assertNotIn(private, repr(report))

    def test_separate_adequate_jockey_and_trainer_not_equivalent_to_same_pair(self):
        # JOCKEY001 has 36 past starts, and STABLE001 independently has
        # 36 past starts, but the rider NEVER rode for that particular stable.
        history = [past(n) for n in range(1, 13)]
        for race in history:
            for row in race["runners"]:
                row["trainerRef"] = ("STABLE002" if row["number"] <= 3
                                     else "STABLE001")
        before = copy.deepcopy(history)
        report = support_six_cohort_study(TARGET, history)
        self.assertEqual(history, before)
        row = report["horses"][0]
        self.assertTrue(row["cohortEvidence"]["jockey"]["minimumCoverageMet"])
        self.assertTrue(row["cohortEvidence"]["trainer"]["minimumCoverageMet"])
        self.assertEqual(
            row["cohortEvidence"]["jockeyTrainerPair"]["observedRunners"], 0)
        self.assertFalse(
            row["cohortEvidence"]["jockeyTrainerPair"]["minimumCoverageMet"])
        self.assertTrue(row["jockeyAndTrainerIndividualCoverageMet"])
        self.assertFalse(row["jockeyTrainerPairCoverageMet"])
        self.assertFalse(row["pairEffectIndependentlyValidated"])
        self.assertEqual(row["grades"]["jockey_stable"], "未評価")
        self.assertIsNone(row["scores"]["jockey_stable"])
        for private in ("JOCKEY001", "STABLE001", "STABLE002"):
            self.assertNotIn(private, repr(report))

    def test_rider_trainer_pair_never_uses_unpublished_or_other_race_cohort(self):
        history = [past(n) for n in range(1, 13)]
        later = past(13, day="2026-11-13",
                     availability="2026-11-13T23:30:00+09:00")
        for h in later["runners"]:
            h["jockeyRef"] = "JOCKEY001"
            h["trainerRef"] = "STABLE001"
        history.append(later)
        report = support_six_cohort_study(TARGET, history)
        self.assertEqual(report["futureOrUnpublishedRacesExcluded"], 1)
        self.assertEqual(
            report["horses"][0]["cohortEvidence"]["jockeyTrainerPair"]
                  ["observedRunners"], 36)
        self.assertFalse(report["holdoutValidationComplete"])

    def test_future_unpublished_and_mismatched_classes_excluded(self):
        history = [past(n) for n in range(1, 13)]
        history.append(past(13, day="2026-11-13",
                            availability="2026-11-13T21:00:00+09:00"))
        history.append(past(14, day="2026-11-14"))
        history.append(past(15, day="2026-10-15", klass="C3"))
        history.append(past(16, day="2026-10-16", track="東京"))
        history.append(past(17, day="2026-10-17", going="良"))
        out = support_six_cohort_study(TARGET, history)
        self.assertEqual(out["futureOrUnpublishedRacesExcluded"], 2)
        self.assertEqual(out["otherConditionRacesExcluded"], 3)
        self.assertEqual(out["pastRacesEligible"], 15)
        self.assertEqual(out["matchingBaseline"]["observedRunners"], 72)

    def test_few_historic_races_are_not_treated_as_bad_grades(self):
        report = support_six_cohort_study(TARGET, [past(1)])
        study = report["horses"][0]["cohortEvidence"]
        self.assertEqual(study["jockey"]["observedRunners"], 3)
        self.assertFalse(study["jockey"]["minimumCoverageMet"])
        self.assertIsNone(study["jockey"]["observedWinRatePercent"])
        self.assertEqual(report["horses"][0]["grades"]["jockey_stable"], "未評価")

    def test_race_and_runner_quality_invalid_values_fail_closed(self):
        base = past(1)
        mutations = (
            lambda x: x["runners"][0].update(finish=2),
            lambda x: x["runners"][0].update(number=2),
            lambda x: x["runners"][0].update(horseRef="HORSE0102"),
            lambda x: x["runners"][0].update(carriedKg=55.25),
            lambda x: x["runners"][0].update(frame=0),
            lambda x: x["runners"][0].update(jockeyRef="not valid"),
            lambda x: x["runners"][0].update(lastRunDate="2026-12-01"),
            lambda x: x.update(resultAvailableAt="2026-10-01T11:30:00+09:00"),
            lambda x: x.update(resultAvailableAt="2026-10-01T12:30:00"),
            lambda x: x.update(officialVerified=True),
            lambda x: x.update(classCode=""),
            lambda x: x.update(race=13),
        )
        for change in mutations:
            sample = copy.deepcopy(base); change(sample)
            with self.subTest(change=repr(change)), self.assertRaises(SupportCohortError):
                support_six_cohort_study(TARGET, [sample])
        with self.assertRaises(SupportCohortError):
            support_six_cohort_study(TARGET, [base, copy.deepcopy(base)])
        for change in (
            lambda x: x.update(capturedAt="2026-11-14T13:26:00+09:00"),
            lambda x: x.update(scheduledOffAt="2026-11-13T13:25:00+09:00"),
            lambda x: x.update(classCode="💰"),
            lambda x: x.update(officialVerified=True),
            lambda x: x["runners"][0].update(carriedKg=True),
            lambda x: x["runners"][0].update(lastRunDate="2026-11-20"),
            lambda x: x["runners"][0].update(trainerRef=""),
        ):
            altered = copy.deepcopy(TARGET);change(altered)
            with self.subTest(change=repr(change)), self.assertRaises(SupportCohortError):
                support_six_cohort_study(altered, [base])

    def test_unknown_rotation_is_unknown_without_imputed_zero(self):
        target = copy.deepcopy(TARGET)
        target["runners"][0]["lastRunDate"] = None
        result = support_six_cohort_study(target, [past(n) for n in range(1, 13)])
        a = result["horses"][0]
        self.assertFalse(a["rotationSourceAvailable"])
        self.assertEqual(a["cohortEvidence"]["rotation"]["observedRunners"], 0)
        self.assertIsNone(a["scores"]["rotation"])
        self.assertEqual(a["grades"]["rotation"], "未評価")


if __name__ == "__main__":
    unittest.main()
