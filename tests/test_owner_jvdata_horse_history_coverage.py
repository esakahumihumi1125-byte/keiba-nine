"""Synthetic RCVN history identity tests: no provider calls or real horse data."""
import copy
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_jvdata_horse_history_coverage import (
    HISTORY_DATA_SPEC, MAX_HISTORY_RECORDS, audit_jvdata_horse_history,
)
from test_jvdata_ra_se_candidate import make, replace, DAY

JST = timezone(timedelta(hours=9))
PRESTART = datetime(2026, 11, 20, 18, 0, tzinfo=JST)
POST_OFF = datetime(2026, 11, 21, 10, 0, tzinfo=JST)


def racecard():
    return make("RA"), [make("SE", horse=i) for i in range(1, 5)]


def old_result(horse=1, *, day="20251012", race="01", created="20251101"):
    row = make("SE", horse=horse)
    row = replace(row, 2, 3, "7")
    row = replace(row, 3, 11, created)
    row = replace(row, 11, 15, day[:4])
    row = replace(row, 15, 19, day[4:])
    row = replace(row, 25, 27, race)
    return row


def audit(history, *, captured_at=PRESTART):
    ra, se = racecard()
    return audit_jvdata_horse_history(
        ra, se, history, DAY, captured_at=captured_at,
    )


class JvDataHorseHistoryCoverageTests(unittest.TestCase):
    def test_rcvn_history_join_by_private_registration_not_horse_number(self):
        self.assertEqual(HISTORY_DATA_SPEC, "RCVN")
        a = old_result(1)
        b = old_result(1, day="20250915", race="03")
        c = old_result(3, day="20240801", race="12")
        others = old_result(7, day="20250915", race="02")
        original = [a, b, c, others]
        report = audit(original)
        self.assertEqual(original, [a, b, c, others])
        self.assertEqual(report["status"], "linked_history_observed_not_graded")
        self.assertEqual(report["runnerCount"], 4)
        self.assertEqual(report["runnersWithObservedHistory"], 2)
        self.assertEqual(
            [(row["number"], row["observedPriorResultRecords"])
             for row in report["byNumber"]],
            [(1, 2), (2, 0), (3, 1), (4, 0)]
        )
        self.assertEqual(report["extraProviderRequests"], 0)
        self.assertTrue(report["privateOwnerOnly"])
        self.assertFalse(report["finalJraStartersVerified"])
        self.assertFalse(report["formalTenFactorReady"])
        self.assertFalse(report["predictionReady"])
        self.assertFalse(report["bettingReady"])
        self.assertFalse(report["historyOutcomeFieldsInterpreted"])
        self.assertTrue(all(row["historyResultGrade"] is None
                            and row["formalFactorAssessment"] is None
                            and row["historyCoverageComplete"] is False
                            for row in report["byNumber"]))
        for private in ("1000000001", "1000000003",
                        "horse_id", "registrationId", "PRIVATE_FILE_NAME"):
            self.assertNotIn(private, repr(report))

    def test_empty_history_is_unknown_not_unraced(self):
        out = audit([])
        self.assertEqual(out["status"], "no_matched_history_observed")
        self.assertEqual(out["runnersWithObservedHistory"], 0)
        self.assertFalse(out["historyCoverageComplete"])
        self.assertFalse(out["formalTenFactorReady"])
        self.assertTrue(all(row["observedPriorResultRecords"] == 0
                            for row in out["byNumber"]))

    def test_same_exact_history_replay_is_deduplicated(self):
        row = old_result(1)
        out = audit([row, row])
        self.assertEqual(out["byNumber"][0]["observedPriorResultRecords"], 1)

    def test_history_conflict_cannot_be_silently_merged(self):
        row = old_result(1)
        other = replace(row, 41, 42, "X")
        with self.assertRaisesRegex(CoverageError, "Conflicting historical"):
            audit([row, other])

    def test_future_results_and_late_corrections_rejected(self):
        invalid = (
            old_result(1, day=DAY, created="20261120"),
            old_result(1, day="20261122", created="20261122"),
            old_result(1, day="20251012", created="20261122"),
            replace(old_result(1), 2, 3, "2"),
            replace(old_result(1), 19, 21, "99"),
            replace(old_result(1), 30, 40, "0000000000"),
            old_result(1)[:-1],
        )
        for row in invalid:
            with self.subTest(value=row[:30]), self.assertRaises(CoverageError):
                audit([row])

    def test_post_off_snapshot_is_held_even_if_prior_result_exists(self):
        row = old_result(1)
        result = audit([row], captured_at=POST_OFF)
        self.assertEqual(result["status"], "post_off_capture_hold")
        self.assertEqual(result["runnersWithObservedHistory"], 0)
        self.assertTrue(all(row["observedPriorResultRecords"] == 0
                            for row in result["byNumber"]))
        self.assertFalse(result["prestartDeliveryIndependentlyVerified"])
        self.assertFalse(result["predictionReady"])

    def test_no_unbounded_batches_or_naive_capture_times(self):
        with self.assertRaises(CoverageError):
            audit([old_result(1)] * (MAX_HISTORY_RECORDS + 1))
        with self.assertRaises(CoverageError):
            audit([old_result(1)], captured_at=datetime(2026, 11, 20, 18, 0))
        with self.assertRaises(CoverageError):
            audit([old_result(1)], captured_at="2026-11-20T18:00:00+09:00")

    def test_unrelated_current_race_id_is_rejected_before_join(self):
        ra, se = racecard()
        foreign = replace(se[-1], 25, 27, "02")
        with self.assertRaises(CoverageError):
            audit_jvdata_horse_history(
                ra, se[:-1] + [foreign], [old_result(1)], DAY,
                captured_at=PRESTART,
            )


if __name__ == "__main__":
    unittest.main()
