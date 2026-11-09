"""Synthetic out-of-time pedigree evidence tests: no provider credentials or races."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_pedigree_cohort_study import (
    PedigreeCohortError, study_pedigree_cohorts
)

TARGET = {
    "raceDate": "2026-11-14", "track": "京都", "race": 7,
    "capturedAt": "2026-11-13T20:00:00+09:00",
    "scheduledOffAt": "2026-11-14T13:25:00+09:00",
    "surface": "芝", "distanceM": 2000, "going": "重",
    "runners": [
        {"number": 5, "sireRef": "SIRE0001", "damsireRef": "DAM00001"},
        {"number": 2, "sireRef": "SIRE0002", "damsireRef": "DAM00002"},
        {"number": 7, "sireRef": "SIRE0003", "damsireRef": "DAM00003"},
    ],
}


def finished_race(n, *, day=None, track="京都", distance=2000,
                  going="重", surface="芝", available=None):
    day = day or f"2026-10-{n:02d}"
    return {
        "raceDate": day, "track": track, "race": 1,
        "scheduledOffAt": day + "T12:00:00+09:00",
        "resultAvailableAt": available or day + "T12:20:00+09:00",
        "surface": surface, "distanceM": distance, "going": going,
        "runners": [
            {
                "number": i, "horseRef": f"HORSE{n:02d}{i:02d}",
                "sireRef": "SIRE0001" if i < 4 else "SIRE0002",
                "damsireRef": "DAM00001" if i < 4 else "DAM00002",
                "finish": i,
            } for i in range(1, 5)
        ],
    }


class PedigreeCohortStudyTests(unittest.TestCase):
    def test_research_counts_from_complete_past_races_not_grades(self):
        old = [finished_race(i) for i in range(1, 13)]
        before = copy.deepcopy((TARGET, old))
        out = study_pedigree_cohorts(TARGET, old)
        self.assertEqual((TARGET, old), before)
        self.assertEqual(out["providedHistoricalRaces"], 12)
        self.assertEqual(out["historicalRacesAvailableBeforeCapture"], 12)
        self.assertEqual(out["excludedLaterOrUnpublishedRaces"], 0)
        self.assertEqual(out["otherConditionRaces"], 0)
        self.assertEqual(out["conditionMatchedBaseline"]["observedRunners"], 48)
        self.assertEqual(out["conditionMatchedBaseline"]["observedWins"], 12)
        self.assertEqual(out["conditionMatchedBaseline"]["observedTop3"], 36)
        self.assertEqual([x["number"] for x in out["horses"]], [2, 5, 7])
        strong = out["horses"][1]
        self.assertTrue(strong["sireHistory"]["minimumCoverageMet"])
        self.assertEqual(strong["sireHistory"]["observedRunners"], 36)
        self.assertEqual(strong["sireHistory"]["distinctHorses"], 36)
        self.assertEqual(strong["sireHistory"]["distinctHistoricalRaces"], 12)
        self.assertEqual(strong["sireHistory"]["observedWinRatePercent"], 33.33)
        self.assertEqual(strong["sireHistory"]["observedTop3RatePercent"], 100.0)
        self.assertTrue(strong["damsireHistory"]["minimumCoverageMet"])
        self.assertFalse(out["horses"][0]["sireHistory"]["minimumCoverageMet"])
        self.assertIsNone(out["horses"][0]["sireHistory"]["observedWinRatePercent"])
        self.assertEqual(out["horses"][2]["sireHistory"]["observedRunners"], 0)
        for horse in out["horses"]:
            self.assertEqual(horse["grade"], "未評価")
            self.assertIsNone(horse["score8"])
            self.assertFalse(horse["outOfTimeValidated"])
        for flag in ("allPastResultsHaveIndependentProvenance",
                     "independentJraOfficialVerification",
                     "prospectiveHoldoutValidated", "overallPredictionReady",
                     "bettingReady", "autoPurchase", "actualPurchase",
                     "changesExistingReceipts", "changesExistingTickets"):
            self.assertFalse(out[flag])
        self.assertEqual(out["formalPedigreeGradesVerified"], 0)
        self.assertEqual(out["sourceReadCount"], 0)
        for forbidden in ("SIRE0001", "DAM00001", "HORSE", "horseRef",
                          "payout", "predictedWinProbability"):
            self.assertNotIn(forbidden, repr(out))

    def test_future_published_after_snapshot_or_same_day_are_excluded(self):
        races = [finished_race(i) for i in range(1, 13)]
        races.append(finished_race(
            13, day="2026-11-13",
            available="2026-11-13T22:00:00+09:00"))
        races.append(finished_race(14, day="2026-11-14",
                                  available="2026-11-14T12:30:00+09:00"))
        races.append(finished_race(15, day="2026-10-15", track="東京"))
        races.append(finished_race(16, day="2026-10-16", distance=1200))
        races.append(finished_race(17, day="2026-10-17", going="良"))
        report = study_pedigree_cohorts(TARGET, races)
        self.assertEqual(report["providedHistoricalRaces"], 17)
        self.assertEqual(report["excludedLaterOrUnpublishedRaces"], 2)
        self.assertEqual(report["historicalRacesAvailableBeforeCapture"], 15)
        self.assertEqual(report["otherConditionRaces"], 3)
        self.assertEqual(report["conditionMatchedBaseline"]["observedRunners"], 48)

    def test_small_sample_can_never_become_grade(self):
        out = study_pedigree_cohorts(TARGET, [finished_race(1)])
        row = next(x for x in out["horses"] if x["number"] == 5)
        self.assertEqual(row["sireHistory"]["observedRunners"], 3)
        self.assertFalse(row["sireHistory"]["minimumCoverageMet"])
        self.assertIsNone(row["sireHistory"]["observedWinRatePercent"])
        self.assertIsNone(row["sireHistory"]["observedTop3RatePercent"])
        self.assertEqual(row["grade"], "未評価")

    def test_wrong_dates_finish_ties_duplicate_horses_and_unverified_markers_fail(self):
        base = finished_race(1)
        changes = (
            lambda x: x["runners"][0].update(finish=2),
            lambda x: x["runners"][0].update(number=2),
            lambda x: x["runners"][0].update(horseRef="HORSE0102"),
            lambda x: x["runners"][0].update(sireRef="a b"),
            lambda x: x.update(resultAvailableAt="2026-10-01T11:00:00+09:00"),
            lambda x: x.update(scheduledOffAt="2026-10-02T12:00:00+09:00"),
            lambda x: x.update(resultAvailableAt="2026-10-01T12:20:00"),
            lambda x: x.update(officialJraVerified=True),
            lambda x: x.update(going="unknown"),
        )
        for change in changes:
            row = copy.deepcopy(base)
            change(row)
            with self.subTest(change=repr(change)), self.assertRaises(PedigreeCohortError):
                study_pedigree_cohorts(TARGET, [row])
        with self.assertRaises(PedigreeCohortError):
            study_pedigree_cohorts(TARGET, [base, copy.deepcopy(base)])
        for change in (
            lambda x: x["runners"][0].update(number=True),
            lambda x: x["runners"][0].update(damsireRef="父"),
            lambda x: x.update(capturedAt="2026-11-14T13:26:00+09:00"),
            lambda x: x.update(scheduledOffAt="2026-11-13T13:25:00+09:00"),
            lambda x: x.update(raceDate="2026-11-31"),
            lambda x: x.update(officialVerified=True),
        ):
            row = copy.deepcopy(TARGET)
            change(row)
            with self.subTest(change=repr(change)), self.assertRaises(PedigreeCohortError):
                study_pedigree_cohorts(row, [base])

    def test_latest_future_race_cannot_be_used_to_raise_an_old_2026_grade(self):
        earlier = copy.deepcopy(TARGET)
        earlier["raceDate"] = "2026-10-20"
        earlier["capturedAt"] = "2026-10-19T20:00:00+09:00"
        earlier["scheduledOffAt"] = "2026-10-20T13:25:00+09:00"
        histories = [finished_race(i) for i in range(1, 13)]
        later = finished_race(15, day="2026-11-01")
        report = study_pedigree_cohorts(earlier, histories + [later])
        self.assertEqual(report["excludedLaterOrUnpublishedRaces"], 1)
        self.assertFalse(report["prospectiveHoldoutValidated"])
        self.assertEqual(report["formalPedigreeGradesVerified"], 0)


if __name__ == "__main__":
    unittest.main()
