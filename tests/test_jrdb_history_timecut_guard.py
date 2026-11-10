"""Synthetic regression: reject leaky/duplicate past race references before reads."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_history_pipeline import plan_bounded_history, run_bounded_history_audit
from owner_past_staff_batch import inspect_three_past_staff_samples
from test_jrdb_history_pipeline import context

TARGET_DAY = "20261101"


class HistoryTimecutGuardTests(unittest.TestCase):
    def _reject_before_reads(self, mutate):
        bundle = context()
        programme, entries, previous, current, dra, dka = bundle
        original = copy.deepcopy((programme, entries, previous, current))
        mutate(previous[0])
        altered = copy.deepcopy((programme, entries, previous, current))

        with self.assertRaises(CoverageError):
            plan_bounded_history(programme, entries, previous, TARGET_DAY)
        with self.assertRaises(CoverageError):
            run_bounded_history_audit(
                programme, entries, previous, current, TARGET_DAY,
                fetch_dra=dra, fetch_dka=dka,
            )
        dky, dse = Mock(), Mock()
        with self.assertRaises(CoverageError):
            inspect_three_past_staff_samples(
                programme, entries, previous, TARGET_DAY,
                fetch_dky=dky, fetch_dse=dse,
            )
        for paid in (dra, dka, dky, dse):
            paid.assert_not_called()
        self.assertEqual((programme, entries, previous, current), altered)
        self.assertNotEqual(original, altered)

    def test_previous_race_key_year_must_match_historical_date(self):
        self._reject_before_reads(
            lambda row: row.update(race_back_1_racekey="05254a01"))

    def test_same_runner_cannot_reuse_one_race_in_two_back_slots(self):
        def duplicate(row):
            row["race_back_2_racedate"] = row["race_back_1_racedate"]
            row["race_back_2_racekey"] = row["race_back_1_racekey"]
        self._reject_before_reads(duplicate)

    def test_older_numbered_back_slot_cannot_be_more_recent(self):
        def reverse(row):
            row["race_back_2_racedate"] = "20261020"
            row["race_back_2_racekey"] = "05264a03"
        self._reject_before_reads(reverse)

    def test_duplicate_previous_rows_for_same_current_runner_are_rejected(self):
        programme, entries, previous, current, dra, dka = context()
        previous.append(copy.deepcopy(previous[0]))
        original = copy.deepcopy(previous)
        with self.assertRaises(CoverageError):
            plan_bounded_history(
                programme, entries, previous, TARGET_DAY)
        with self.assertRaises(CoverageError):
            run_bounded_history_audit(
                programme, entries, previous, current, TARGET_DAY,
                fetch_dra=dra, fetch_dka=dka,
            )
        dky, dse = Mock(), Mock()
        with self.assertRaises(CoverageError):
            inspect_three_past_staff_samples(
                programme, entries, previous, TARGET_DAY,
                fetch_dky=dky, fetch_dse=dse,
            )
        for paid in (dra, dka, dky, dse):
            paid.assert_not_called()
        self.assertEqual(previous, original)

    def test_valid_cross_runner_references_are_still_deduplicated(self):
        programme, entries, previous, current, dra, dka = context()
        original = copy.deepcopy(previous)
        plan = plan_bounded_history(
            programme, entries, previous, TARGET_DAY)
        self.assertEqual(plan["referencedCount"], 3)
        self.assertEqual(len(plan["privateSelected"]), 3)
        self.assertEqual(
            len({key for key, day in plan["privateSelected"]}), 3)
        self.assertEqual(previous, original)
        dra.assert_not_called()
        dka.assert_not_called()


if __name__ == "__main__":
    unittest.main()
