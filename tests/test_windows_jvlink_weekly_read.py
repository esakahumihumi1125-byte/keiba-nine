"""Synthetic-only JV-Link weekly collection tests; no real COM or JRA-VAN calls."""
import contextlib
import copy
import io
import json
import os
from datetime import date
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from test_jvdata_ra_se_candidate import make, replace, DAY
from windows_jvlink_weekly_read import (
    JvLocalCheckError, collect_weekly_candidate_records,
    run_one_weekly_read, main, next_saturday, MAX_RECORDS,
)


class FakeJv:
    def __init__(self, raws, *, fail_open=False, fail_read=False):
        self.raws = list(raws)
        self.open_calls = []
        self.closed = 0
        self.fail_open = fail_open
        self.fail_read = fail_read
        self.init_args = []

    def JVInit(self, sid):
        self.init_args.append(sid)
        return 0

    def JVOpen(self, *args):
        self.open_calls.append(args)
        if self.fail_open:
            return (-413, 0, 0, "")
        return (0, len(self.raws), 0, "20261120090000")

    def JVGets(self, *_args):
        if self.fail_read:
            raise RuntimeError("PROVIDER_PRIVATE_ERROR:DO_NOT_PRINT")
        if not self.raws:
            return 0, b"", bytearray()
        item = self.raws.pop(0)
        if item == -1:
            return -1, b"", bytearray()
        return len(item), memoryview(item), bytearray(b"PRIVATE_FILE_NAME")

    def JVClose(self):
        self.closed += 1
        return 0


def weekly_records():
    return [make("RA"), *[make("SE", horse=i) for i in range(1, 5)]]


class WeeklyJvLinkLocalTests(unittest.TestCase):
    def test_default_next_saturday_is_one_click(self):
        self.assertEqual(next_saturday(date(2026, 11, 18)), "20261121")
        self.assertEqual(next_saturday(date(2026, 11, 21)), "20261121")
        self.assertEqual(next_saturday(date(2026, 11, 22)), "20261128")

    def test_one_opt_in_weekly_open_and_matched_private_candidates(self):
        jv = FakeJv([-1, *weekly_records()])
        report = collect_weekly_candidate_records(jv, DAY)
        self.assertEqual(jv.open_calls,
                         [("RACE", "00000000000000", 2, 0, 0, "")])
        self.assertEqual(jv.closed, 1)
        self.assertEqual(report["raceCount"], 1)
        self.assertEqual(report["races"][0]["horseNumbersCandidate"], [1, 2, 3, 4])
        self.assertEqual(report["races"][0]["postTimeCandidate"], "10:00")
        self.assertFalse(report["independentJraVerified"])
        self.assertFalse(report["officialGoingVerified"])
        self.assertFalse(report["productionPredictionReady"])
        self.assertFalse(report["bettingReady"])
        self.assertFalse(report["autoPurchase"])
        self.assertTrue(report["privateOwnerOnly"])
        for secret in ("PRIVATE_FILE_NAME", "PROVIDER_PRIVATE_ERROR",
                       "1000000001", "horse_id", "racekey"):
            self.assertNotIn(secret, repr(report))

    def test_irrelevant_data_and_different_day_are_not_promoted(self):
        existing = weekly_records()
        ignored = replace(existing[0], 2, 3, "3")
        other_day = replace(existing[0], 11, 15, "2025")
        jv = FakeJv([ignored, other_day, *existing])
        report = collect_weekly_candidate_records(jv, DAY)
        self.assertEqual(report["raceCount"], 1)
        self.assertEqual(report["weekReadRecordCount"], 7)
        self.assertEqual(jv.closed, 1)

    def test_duplication_conflict_and_incomplete_race_are_held(self):
        ra, se = weekly_records()[0], weekly_records()[1:]
        cases = [
            [ra, ra, *se],  # byte-for-byte replay okay
            [ra, *se, se[0]],  # exact replay okay
        ]
        for records in cases:
            with self.subTest(records=len(records)):
                self.assertEqual(collect_weekly_candidate_records(
                    FakeJv(records), DAY)["raceCount"], 1)
        bad = [
            [ra, replace(ra, 873, 877, "1005"), *se],
            [ra, *se, replace(se[0], 30, 40, "1000000015")],
            [ra, *se[:3]],
            [*se],
            [ra],
        ]
        for records in bad:
            jv = FakeJv(records)
            with self.subTest(records=len(records)), self.assertRaises(
                    JvLocalCheckError):
                collect_weekly_candidate_records(jv, DAY)
            self.assertEqual(jv.closed, 1)

    def test_extra_nul_or_com_buffer_padding_is_not_a_record_corruption(self):
        class PaddedJv(FakeJv):
            def JVGets(self, *_args):
                value = super().JVGets(*_args)
                code, raw, filename = value
                if code > 0:
                    return code, bytes(raw) + b"\\x00", filename
                return value
        sample = collect_weekly_candidate_records(PaddedJv(weekly_records()), DAY)
        self.assertEqual(sample["races"][0]["horseNumbersCandidate"], [1, 2, 3, 4])

        class ShortJv(FakeJv):
            def JVGets(self, *_args):
                value = super().JVGets(*_args)
                code, raw, filename = value
                if code > 0:
                    return code, bytes(raw)[:-1], filename
                return value
        with self.assertRaisesRegex(JvLocalCheckError, "^JVGETS_DATA_INVALID$"):
            collect_weekly_candidate_records(ShortJv(weekly_records()), DAY)

    def test_close_always_runs_after_read_failure(self):
        jv = FakeJv(weekly_records(), fail_read=True)
        with self.assertRaises(RuntimeError):
            collect_weekly_candidate_records(jv, DAY)
        self.assertEqual(jv.closed, 1)
        self.assertEqual(jv.open_calls[0][2], 2)

    def test_failed_open_does_not_read_or_close_an_unopened_reader(self):
        jv = FakeJv(weekly_records(), fail_open=True)
        with self.assertRaisesRegex(JvLocalCheckError, "^JVOPEN_NOT_READY$"):
            collect_weekly_candidate_records(jv, DAY)
        self.assertEqual(jv.closed, 0)
        self.assertEqual(len(jv.raws), 5)

    def test_budget_limit_never_returns_incomplete_output(self):
        with self.assertRaisesRegex(
                JvLocalCheckError, "^WEEKLY_READ_LIMIT_REACHED$"):
            collect_weekly_candidate_records(FakeJv(weekly_records()), DAY,
                                             max_records=2)
        with self.assertRaisesRegex(JvLocalCheckError, "^READ_BUDGET_INVALID$"):
            collect_weekly_candidate_records(FakeJv([]), DAY,
                                             max_records=MAX_RECORDS + 1)

    def test_real_entry_point_is_fail_closed_and_does_not_reveal_exceptions(self):
        jv = FakeJv(weekly_records())
        with patch("windows_jvlink_weekly_read.validate_day", return_value=DAY):
            report = run_one_weekly_read(DAY, jv_factory=lambda: jv)
        self.assertEqual(report["raceCount"], 1)
        self.assertEqual(jv.init_args, ["UNKNOWN"])
        jv = FakeJv(weekly_records(), fail_read=True)
        with patch("windows_jvlink_weekly_read.validate_day", return_value=DAY):
            with self.assertRaisesRegex(
                    JvLocalCheckError, "^JVLINK_WEEKLY_READ_FAILED$"):
                run_one_weekly_read(DAY, jv_factory=lambda: jv)

    def test_one_time_private_json_saved_and_never_overwritten(self):
        report = collect_weekly_candidate_records(FakeJv(weekly_records()), DAY)
        with tempfile.TemporaryDirectory() as tmp:
            output = io.StringIO()
            with patch.dict(os.environ, {"LOCALAPPDATA": tmp}), \
                 patch("windows_jvlink_weekly_read.run_one_weekly_read", return_value=report), \
                 contextlib.redirect_stdout(output):
                self.assertEqual(main(["--date", DAY]), 0)
                self.assertEqual(main(["--date", DAY]), 1)
            target = Path(tmp) / "ARC-RACE-private" / (
                "jvdata-candidate-" + DAY + ".json")
            saved = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(saved["raceCount"], 1)
            self.assertEqual(saved["races"][0]["horseNumbersCandidate"], [1, 2, 3, 4])
            self.assertNotIn("PRIVATE_FILE_NAME", target.read_text(encoding="utf-8"))
            self.assertEqual(list(target.parent.glob(".arc-race-*.tmp")), [])
            self.assertIn("ARCRACE_WEEKLY_READ=SUCCESS", output.getvalue())
            self.assertIn("ARCRACE_WEEKLY_READ=OUTPUT_EXISTS_NOT_OVERWRITTEN",
                          output.getvalue())


if __name__ == "__main__":
    unittest.main()
