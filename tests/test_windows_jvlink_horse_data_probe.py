"""No real JV-Link access: validate one-time RCVN read-only diagnostics."""
import contextlib
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from windows_jvlink_horse_data_probe import (
    MAX_PROBE_RECORDS, JvLocalCheckError, probe_rcvn_once, run_once, main,
)
from test_jvdata_ra_se_candidate import make, replace


def history_records():
    ra = replace(make("RA"), 2, 3, "7")
    se = replace(make("SE"), 2, 3, "7")
    return [ra, se]


class FakeJv:
    def __init__(self, rows, *, open_result=0, close_result=0):
        self.rows = list(rows)
        self.open_result = open_result
        self.close_result = close_result
        self.opens = []
        self.closes = 0
        self.inits = []

    def JVInit(self, key):
        self.inits.append(key)
        return 0

    def JVOpen(self, *args):
        self.opens.append(args)
        return (self.open_result, 0, 0, "")

    def JVGets(self, *_args):
        if not self.rows:
            return (0, b"", bytearray())
        item = self.rows.pop(0)
        if type(item) is int:
            return (item, b"", bytearray())
        return (len(item), memoryview(item), bytearray(b"SECRET_FILENAME"))

    def JVClose(self):
        self.closes += 1
        return self.close_result


class HorseDataProbeTests(unittest.TestCase):
    def test_observes_both_past_result_types_without_releasing_records(self):
        sample = history_records()
        jv = FakeJv([-1, *sample])
        result = probe_rcvn_once(jv)
        self.assertEqual(jv.opens,
                         [("RCVN", "00000000000000", 2, 0, 0, "")])
        self.assertEqual(jv.closes, 1)
        self.assertEqual(result["status"], "RCVN_HISTORY_RA_SE_OBSERVED")
        self.assertTrue(result["historicalRaceRecordsObserved"])
        self.assertTrue(result["historicalHorseResultsObserved"])
        self.assertFalse(result["historicalDatasetComplete"])
        self.assertFalse(result["formalTenFactorReady"])
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["bettingReady"])
        self.assertFalse(result["providerRecordStored"])
        self.assertFalse(result["networkUploadPerformed"])
        for forbidden in ("1000000001", "SECRET_FILENAME",
                          "horse_id", "licence", "registration"):
            self.assertNotIn(forbidden, repr(result))

    def test_no_records_and_other_types_are_different(self):
        a = probe_rcvn_once(FakeJv([]))
        self.assertEqual(a["status"], "RCVN_EMPTY_READ")
        b = probe_rcvn_once(FakeJv([make("SE")]))
        self.assertEqual(b["status"], "RCVN_NO_RA_SE_RESULT_OBSERVED")
        self.assertTrue(b["nonHistoricalRecordsObserved"])

    def test_no_new_data_is_not_entitlement_proof(self):
        jv = FakeJv(history_records(), open_result=-1)
        with self.assertRaisesRegex(JvLocalCheckError, "RCVN_NO_NEW_DATA"):
            probe_rcvn_once(jv)
        self.assertEqual(jv.closes, 0)
        self.assertEqual(len(jv.opens), 1)

    def test_one_bounded_wait_can_recover_without_second_open(self):
        clock = [0.0]
        def pause(seconds):
            clock[0] += seconds
        jv = FakeJv([-3, *history_records()])
        result = probe_rcvn_once(
            jv, monotonic=lambda: clock[0], sleep=pause,
            max_download_wait=5,
        )
        self.assertEqual(result["status"], "RCVN_HISTORY_RA_SE_OBSERVED")
        self.assertEqual(clock[0], 2.0)
        self.assertEqual(len(jv.opens), 1)
        self.assertEqual(jv.closes, 1)

    def test_download_timeout_closes_and_keeps_no_partial_output(self):
        clock = [0.0]
        def pause(seconds):
            clock[0] += seconds
        jv = FakeJv([-3] * 10)
        with self.assertRaisesRegex(JvLocalCheckError, "RCVN_DOWNLOAD_PENDING"):
            probe_rcvn_once(
                jv, monotonic=lambda: clock[0], sleep=pause,
                max_download_wait=3,
            )
        self.assertEqual(jv.closes, 1)
        self.assertEqual(len(jv.opens), 1)

    def test_strict_budget_reports_incompleteness_not_full_success(self):
        jv = FakeJv(history_records())
        result = probe_rcvn_once(jv, budget=2)
        self.assertTrue(result["readWasBudgetLimited"])
        self.assertEqual(result["status"], "RCVN_PARTIAL_BUDGET_LIMIT")
        self.assertTrue(result["historicalHorseResultsObserved"])
        self.assertEqual(jv.closes, 1)
        with self.assertRaisesRegex(JvLocalCheckError, "RCVN_READ_BUDGET_INVALID"):
            probe_rcvn_once(FakeJv([]), budget=MAX_PROBE_RECORDS + 1)

    def test_closure_and_shape_failures_do_not_expose_data(self):
        for rows in ([-2], [b"x"], [make("SE")]):
            jv = FakeJv(rows, close_result=-5)
            with self.assertRaises(JvLocalCheckError):
                probe_rcvn_once(jv)
            self.assertEqual(jv.closes, 1)

    def test_actual_5000_ra_prefix_no_longer_hides_first_se(self):
        ra, se = history_records()
        # Simulates the user's first read: 5,000+ RA7 before any SE7.
        # The old cap would always say SE=NO even when present later.
        jv = FakeJv([ra] * 5100 + [se, b"PRIVATE_FOLLOWING_ROW"])
        report = probe_rcvn_once(jv, stop_when_both=True)
        self.assertEqual(report["status"], "RCVN_HISTORY_RA_SE_OBSERVED_PARTIAL")
        self.assertTrue(report["historicalRaceRecordsObserved"])
        self.assertTrue(report["historicalHorseResultsObserved"])
        self.assertFalse(report["readWasBudgetLimited"])
        self.assertTrue(report["stoppedWhenBothObserved"])
        self.assertFalse(report["historicalDatasetComplete"])
        self.assertFalse(report["predictionReady"])
        self.assertEqual(jv.closes, 1)
        # Once both formats are visible, don't touch the remaining bytes.
        self.assertEqual(jv.rows, [b"PRIVATE_FOLLOWING_ROW"])
        self.assertNotIn("PRIVATE_FOLLOWING_ROW", repr(report))

    def test_hard_wall_scan_cap_without_guessing_se_absence(self):
        clock = [0]
        def tick():
            clock[0] += 1
            return clock[0]
        ra, _ = history_records()
        jv = FakeJv([ra] * 50)
        report = probe_rcvn_once(
            jv, monotonic=tick, max_scan_seconds=2,
            stop_when_both=True,
        )
        self.assertEqual(report["status"], "RCVN_PARTIAL_TIME_LIMIT")
        self.assertTrue(report["historicalRaceRecordsObserved"])
        self.assertFalse(report["historicalHorseResultsObserved"])
        self.assertTrue(report["readWasTimeLimited"])
        self.assertFalse(report["readWasBudgetLimited"])
        self.assertEqual(jv.closes, 1)

    def test_real_read_cap_remains_bounded_if_se_never_arrives(self):
        ra, _ = history_records()
        jv = FakeJv([ra] * 4)
        report = probe_rcvn_once(jv, budget=3, stop_when_both=True)
        self.assertEqual(report["status"], "RCVN_PARTIAL_BUDGET_LIMIT")
        self.assertFalse(report["historicalHorseResultsObserved"])
        self.assertEqual(jv.closes, 1)

    def test_scan_seconds_cannot_be_extended_by_caller(self):
        with self.assertRaisesRegex(JvLocalCheckError, "RCVN_READ_BUDGET_INVALID"):
            probe_rcvn_once(FakeJv([]), max_scan_seconds=61)

    def test_run_once_handles_local_com_without_debug_leaks(self):
        jv = FakeJv(history_records())
        self.assertTrue(run_once(jv_factory=lambda: jv)["privateOwnerOnly"])
        self.assertEqual(jv.inits, ["UNKNOWN"])

        class LeakyFake:
            def JVInit(self, _):
                raise RuntimeError("PRIVATE_LICENSE_TOKEN")
        with self.assertRaisesRegex(JvLocalCheckError, "^RCVN_CHECK_FAILED$"):
            run_once(jv_factory=LeakyFake)

    def test_main_only_shows_fixed_status_lines(self):
        out = io.StringIO()
        jv = FakeJv(history_records())
        with patch("windows_jvlink_horse_data_probe.run_once",
                   return_value=probe_rcvn_once(jv)), \
             contextlib.redirect_stdout(out):
            self.assertEqual(main(), 0)
        visible = out.getvalue()
        self.assertIn("ARC_RACE_RCVN_CHECK=RCVN_HISTORY_RA_SE_OBSERVED", visible)
        self.assertIn("RCVN_HISTORICAL_RA_OBSERVED=YES", visible)
        self.assertIn("RCVN_HISTORICAL_SE_OBSERVED=YES", visible)
        self.assertNotIn("SECRET_FILENAME", visible)


if __name__ == "__main__":
    unittest.main()
