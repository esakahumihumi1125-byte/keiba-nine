"""Synthetic-only tests: no credentials, no JRDB network, no user records."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_going_history import (
    build_going_history_observations, summarize_going_history_observations
)
from test_jrdb_course_history import fixture


def sample_going():
    programme, entries, previous, historic_programmes = fixture()
    past_conditions = [
        {"holdingkey": "05264a", "racedate": "20261004",
         "turf_condition_cd": "03", "dirt_condition_cd": "01",
         "private_field": "PAID-SECRET"},
        {"holdingkey": "052649", "racedate": "20260920",
         "turf_condition_cd": "04", "dirt_condition_cd": "01"},
    ]
    current_conditions = [
        {"holdingkey": "05264b", "racedate": "20261101",
         "turf_condition_cd": "03", "dirt_condition_cd": "01"},
    ]
    return (programme, entries, previous, historic_programmes,
            past_conditions, current_conditions)


class GoingHistoryTests(unittest.TestCase):
    def audit(self, data=None):
        return build_going_history_observations(
            *(data or sample_going()), "20261101"
        )

    def test_comparable_heavy_and_poor_runs_are_not_aptitude(self):
        races = self.audit()
        first = races[0]["byNumber"]["01"]
        self.assertEqual(first["sameSurfaceKnownGoingRuns"], 2)
        self.assertEqual(first["sameSurfaceUnknownGoingRuns"], 0)
        self.assertEqual(first["knownGoingComparableRuns"], 2)
        self.assertEqual(first["unknownGoingComparableRuns"], 0)
        self.assertEqual(first["heavyComparableRuns"], 1)
        self.assertEqual(first["poorComparableRuns"], 1)
        self.assertEqual(first["heavyTopThreeRuns"], 1)
        self.assertEqual(first["poorTopThreeRuns"], 0)
        self.assertEqual(first["sameCurrentGoingComparableRuns"], 1)
        self.assertEqual(races[0]["byNumber"]["02"]["knownGoingComparableRuns"], 0)
        self.assertFalse(races[0]["goingSuitabilityAssessed"])
        self.assertFalse(races[0]["predictionReady"])

    def test_redacted_aggregate_does_not_emit_paid_records(self):
        report = summarize_going_history_observations(self.audit())
        row = report["races"][0]
        self.assertEqual(row["runnerCount"], 2)
        self.assertTrue(row["currentGoingRecorded"])
        self.assertEqual(row["knownComparableRuns"], 2)
        self.assertEqual(row["heavyTopThreeRuns"], 1)
        self.assertEqual(row["poorComparableRuns"], 1)
        self.assertEqual(row["matchingCurrentGoingRuns"], 1)
        self.assertFalse(report["predictionReady"])
        for forbidden in ("horse_id", "horse_number", "racekey", "byNumber",
                          "05264a01", "PAID-SECRET", "PRIVATE-HORSE",
                          "LICENSED-PAST"):
            self.assertNotIn(forbidden, repr(report))

    def test_missing_historical_going_stays_unknown_not_failure(self):
        data = list(sample_going())
        data[4].clear()
        first = self.audit(data)[0]["byNumber"]["01"]
        self.assertEqual(first["unknownGoingComparableRuns"], 2)
        self.assertEqual(first["knownGoingComparableRuns"], 0)
        self.assertEqual(first["heavyTopThreeRuns"], 0)
        report = summarize_going_history_observations(self.audit(data))
        self.assertEqual(report["races"][0]["unknownComparableRuns"], 2)

    def test_missing_current_going_cannot_claim_same_going(self):
        data = list(sample_going())
        data[5].clear()
        output = self.audit(data)
        self.assertFalse(output[0]["currentGoingRecorded"])
        self.assertEqual(output[0]["byNumber"]["01"]["sameCurrentGoingComparableRuns"], 0)
        self.assertEqual(output[0]["byNumber"]["01"]["heavyComparableRuns"], 1)

    def test_invalid_condition_codes_are_rejected(self):
        for value in ("5", "00", "2 ", 2, True):
            with self.subTest(value=value):
                data = list(sample_going())
                data[4][0]["turf_condition_cd"] = value
                with self.assertRaises(CoverageError):
                    self.audit(data)

    def test_wrong_date_or_unreferenced_holding_is_rejected(self):
        for field, value in (("racedate", "20261005"),
                             ("racedate", "20261101"),
                             ("holdingkey", "08264a"),
                             ("holdingkey", "0526zz")):
            with self.subTest(field=field, value=value):
                data = list(sample_going())
                data[4][0][field] = value
                with self.assertRaises(CoverageError):
                    self.audit(data)

    def test_duplicate_conditions_are_rejected(self):
        data = list(sample_going())
        data[4].append(copy.deepcopy(data[4][0]))
        with self.assertRaises(CoverageError):
            self.audit(data)

    def test_wrong_current_day_cannot_create_match(self):
        data = list(sample_going())
        data[5][0]["racedate"] = "20261004"
        with self.assertRaises(CoverageError):
            self.audit(data)

    def test_current_unknown_code_does_not_create_match(self):
        data = list(sample_going())
        data[5][0]["turf_condition_cd"] = None
        rows = self.audit(data)
        self.assertFalse(rows[0]["currentGoingRecorded"])
        self.assertEqual(rows[0]["byNumber"]["01"]["sameCurrentGoingComparableRuns"], 0)

    def test_missing_historical_programme_does_not_fabricate_evidence(self):
        data = list(sample_going())
        data[3].pop(1)
        data[4].pop(1)
        first = self.audit(data)[0]["byNumber"]["01"]
        self.assertEqual(first["knownGoingComparableRuns"], 1)
        self.assertEqual(first["unknownGoingComparableRuns"], 0)
        self.assertEqual(first["poorComparableRuns"], 0)

    def test_original_inputs_are_not_modified(self):
        data = sample_going()
        before = copy.deepcopy(data)
        self.audit(data)
        self.assertEqual(before, data)

    def test_summary_rejects_contradictory_aggregates(self):
        result = self.audit()
        result[0]["byNumber"]["01"]["poorComparableRuns"] = 10
        with self.assertRaises(ValueError):
            summarize_going_history_observations(result)


if __name__ == "__main__":
    unittest.main()
