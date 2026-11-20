"""Fake-COM only: private owner-PC day history preview never touches JRA-VAN."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from test_jvdata_ra_se_candidate import make, replace, DAY
from test_owner_jvdata_horse_history_preview import old_ra, sample
from windows_jvlink_day_history_preview import (
    JvLocalCheckError, read_source_once, read_local_day_history,
    save_private_local, local_html,
)

JST = timezone(timedelta(hours=9))
PRESTART = datetime(2026, 11, 20, 18, tzinfo=JST)


def sources():
    return {
        "RACE": [make("RA"), *[make("SE", horse=i) for i in range(1, 5)]],
        "RCVN": [sample(1), sample(3), old_ra()],
    }


class FakeJv:
    def __init__(self, by_spec, *, result_codes=None, fail_close=False):
        self.sources = {k: list(v) for k, v in by_spec.items()}
        self.result_codes = result_codes or {}
        self.opens = []
        self.closes = 0
        self.active = None
        self.fail_close = fail_close
        self.inits = []

    def JVInit(self, key):
        self.inits.append(key)
        return 0

    def JVOpen(self, *args):
        spec = args[0]
        self.opens.append(args)
        status = self.result_codes.get(spec, 0)
        if status == 0:
            self.active = spec
        return (status, 0, 0, "")

    def JVGets(self, *_args):
        rows = self.sources[self.active]
        if not rows:
            return (0, b"", bytearray())
        row = rows.pop(0)
        if type(row) is int:
            return (row, b"", bytearray())
        return (len(row), memoryview(row), bytearray(b"PRIVATE_FILENAME"))

    def JVClose(self):
        self.closes += 1
        self.active = None
        return -201 if self.fail_close else 0


class WindowsHistoryDayTests(unittest.TestCase):
    def get_report(self, jv):
        with patch("windows_jvlink_day_history_preview.validate_day",
                   return_value=DAY):
            return read_local_day_history(
                DAY, jv_factory=lambda: jv, captured_at=PRESTART,
            )

    def test_two_source_open_and_sanitized_day_report(self):
        jv = FakeJv(sources())
        report = self.get_report(jv)
        self.assertEqual(
            [args[:3] for args in jv.opens],
            [
                ("RACE", "00000000000000", 2),
                ("RCVN", "00000000000000", 2),
            ]
        )
        self.assertEqual(jv.closes, 2)
        self.assertEqual(jv.inits, ["UNKNOWN"])
        self.assertEqual(report["raceCount"], 1)
        self.assertEqual(report["races"][0]["observedHorseHistory"], 2)
        self.assertFalse(report["formalTenFactorReady"])
        self.assertFalse(report["productionPredictionReady"])
        self.assertFalse(report["bettingReady"])
        self.assertFalse(report["officialStarterListVerified"])
        for token in ("1000000001", "PRIVATE_FILENAME", "horse_id",
                      "jvlink_token", "source_raw"):
            self.assertNotIn(token, repr(report).lower())

    def test_two_complete_races_only_earliest_is_sent_to_rcvn_bridge(self):
        race_2 = [
            replace(replace(row, 25, 27, "02"), 873, 877, "1040")
            if row[:3] == b"RA2" else replace(row, 25, 27, "02")
            for row in sources()["RACE"]
        ]
        jv = FakeJv({
            "RACE": [*race_2, *sources()["RACE"]],
            "RCVN": sources()["RCVN"],
        })
        report = self.get_report(jv)
        self.assertEqual(report["raceCount"], 1)
        self.assertEqual(report["races"][0]["track"], "東京")
        self.assertEqual(report["races"][0]["race"], 1)
        self.assertEqual(jv.closes, 2)
        self.assertTrue(report["races"][0]["observedHorseHistory"] > 0)
        self.assertFalse(report["productionPredictionReady"])

    def test_unpublished_first_race_falls_back_to_complete_second(self):
        original = sources()["RACE"]
        race_2 = [
            replace(replace(row, 25, 27, "02"), 873, 877, "1040")
            if row[:3] == b"RA2" else replace(row, 25, 27, "02")
            for row in original
        ]
        jv = FakeJv({
            "RACE": [original[0], original[1], *race_2],
            "RCVN": sources()["RCVN"],
        })
        report = self.get_report(jv)
        self.assertEqual(report["raceCount"], 1)
        self.assertEqual(report["races"][0]["race"], 2)
        self.assertEqual(len(jv.opens), 2)

    def test_started_race_is_skipped_before_rcvn(self):
        original = sources()["RACE"]
        race_2 = [
            replace(replace(row, 25, 27, "02"), 873, 877, "1040")
            if row[:3] == b"RA2" else replace(row, 25, 27, "02")
            for row in original
        ]
        jv = FakeJv({
            "RACE": [*original, *race_2],
            "RCVN": sources()["RCVN"],
        })
        with patch("windows_jvlink_day_history_preview.validate_day",
                   return_value=DAY):
            report = read_local_day_history(
                DAY, jv_factory=lambda: jv,
                captured_at=datetime(2026, 11, 21, 10, 10, tzinfo=JST))
        self.assertEqual(report["races"][0]["race"], 2)
        self.assertEqual(jv.closes, 2)

        past = FakeJv({
            "RACE": original, "RCVN": sources()["RCVN"],
        })
        with patch("windows_jvlink_day_history_preview.validate_day",
                   return_value=DAY):
            with self.assertRaisesRegex(
                    JvLocalCheckError, "^DAY_HISTORY_ALL_RACES_STARTED$"):
                read_local_day_history(
                    DAY, jv_factory=lambda: past,
                    captured_at=datetime(2026, 11, 21, 10, 10, tzinfo=JST))
        self.assertEqual(len(past.opens), 1)
        self.assertEqual(past.closes, 1)

    def test_current_race_replay_conflict_blocks_history_read(self):
        original = sources()["RACE"]
        jv = FakeJv({
            "RACE": [*original, replace(original[0], 873, 877, "1120")],
            "RCVN": sources()["RCVN"],
        })
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_CURRENT_ROSTER_CONFLICT$"):
            self.get_report(jv)
        self.assertEqual(len(jv.opens), 1)
        self.assertEqual(jv.closes, 1)

    def test_empty_or_no_recent_data_cannot_claim_a_debut(self):
        jv = FakeJv({"RACE": sources()["RACE"], "RCVN": []})
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_NO_MATCHED_RCVN_HORSE_ROWS$"):
            self.get_report(jv)
        self.assertEqual(jv.closes, 2)
        jv = FakeJv(sources(), result_codes={"RCVN": -1})
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_RCVN_NO_NEW_DATA$"):
            self.get_report(jv)
        self.assertEqual(jv.closes, 1)

    def test_realistic_ra_prefix_then_current_horse_se_join(self):
        # Live first attempt observed >5000 RA7 records before SE7.
        # They must not exhaust a 5000-row history buffer, and only
        # current runners' SE7 may enter the private downstream bridge.
        rows = {
            "RACE": sources()["RACE"],
            "RCVN": [old_ra()] * 5200
            + [sample(9), sample(1), sample(3)],
        }
        jv = FakeJv(rows)
        report = self.get_report(jv)
        self.assertEqual(jv.closes, 2)
        self.assertEqual(report["races"][0]["observedHorseHistory"], 2)
        self.assertEqual(
            [x["number"] for x in report["races"][0]["byNumber"]
             if x["observedRecordCount"]], [1, 3])
        self.assertFalse(report["historyCompletenessVerified"])
        # RA7 is intentionally omitted in this initial current-horse
        # identity test. Unverified course/going cannot be fabricated.
        for race in report["races"]:
            for horse in race["byNumber"]:
                for run in horse["recentObservedRuns"]:
                    self.assertIsNone(run["distanceMeters"])
                    self.assertIsNone(run["going"])
        self.assertNotIn("1000000001", repr(report))

    def test_no_matching_se_does_not_claim_horse_is_new(self):
        jv = FakeJv({
            "RACE": sources()["RACE"],
            "RCVN": [old_ra(), sample(8)],
        })
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_NO_MATCHED_RCVN_HORSE_ROWS$"):
            self.get_report(jv)
        self.assertEqual(jv.closes, 2)

    def test_rcvn_time_limit_stops_early_and_closes(self):
        rows = [old_ra()] * 12
        jv = FakeJv({"RCVN": rows})
        clock = [0.0]
        def monotonic():
            clock[0] += 1
            return clock[0]
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_RCVN_TIME_LIMIT$"):
            read_source_once(jv, "RCVN", relevant_ids={b"1000000001"},
                             max_rcvn_seconds=3, monotonic=monotonic)
        self.assertEqual(jv.closes, 1)
        self.assertEqual(len(jv.opens), 1)

    def test_rcvn_max_steps_and_memory_are_bounded(self):
        jv = FakeJv({"RCVN": [old_ra()] * 11})
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_RCVN_BUDGET_LIMIT$"):
            read_source_once(jv, "RCVN", relevant_ids={b"1000000001"},
                             max_steps=10)
        self.assertEqual(jv.closes, 1)
        for kwargs in (
            {"max_steps": 80001},
            {"max_rcvn_seconds": 61},
            {"relevant_ids": {b"bad"}},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(
                    JvLocalCheckError, "^DAY_HISTORY_BUDGET_OR_INPUT_INVALID$"):
                read_source_once(FakeJv({"RCVN": []}), "RCVN", **kwargs)

    def test_empty_current_race_never_requests_history(self):
        jv = FakeJv({"RACE": [], "RCVN": sources()["RCVN"]})
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_NO_CURRENT_CARDS$"):
            self.get_report(jv)
        self.assertEqual(len(jv.opens), 1)
        self.assertEqual(jv.closes, 1)

    def test_stream_close_on_conflict_bad_records_and_budget(self):
        for spec, rows in (
            ("RACE", [make("RA"), b"RA2x"]),
            ("RCVN", [sample(1), b"SE7bad"]),
        ):
            jv = FakeJv({spec: rows})
            with self.subTest(spec=spec), self.assertRaises(JvLocalCheckError):
                read_source_once(jv, spec, day=DAY if spec == "RACE" else None)
            self.assertEqual(jv.closes, 1)
        jv = FakeJv({"RCVN": sources()["RCVN"]})
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_RCVN_BUDGET_LIMIT$"):
            read_source_once(jv, "RCVN", max_steps=2)
        self.assertEqual(jv.closes, 1)

    def test_data_download_wait_is_bounded(self):
        rows = [-3, make("RA"), *[make("SE", horse=i) for i in range(1, 5)]]
        clock = [0.0]
        def sleep(seconds):
            clock[0] += seconds
        jv = FakeJv({"RACE": rows})
        output = read_source_once(
            jv, "RACE", day=DAY, max_download_wait=5,
            sleep=sleep, monotonic=lambda: clock[0],
        )
        self.assertEqual(len(output), 5)
        self.assertEqual(len(jv.opens), 1)
        self.assertEqual(jv.closes, 1)

    def test_incomplete_current_race_does_not_trigger_rcvn(self):
        jv = FakeJv({
            "RACE": sources()["RACE"][:-1],
            "RCVN": sources()["RCVN"],
        })
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_NO_COMPLETE_RACE$"):
            self.get_report(jv)
        self.assertEqual(jv.closes, 1)
        self.assertEqual(len(jv.opens), 1)
        self.assertEqual(jv.opens[0][0], "RACE")

    def test_conflicting_history_remains_fail_closed(self):
        jv = FakeJv({
            "RACE": sources()["RACE"],
            "RCVN": [
                sample(1), replace(sample(1), 334, 336, "01"), old_ra(),
            ],
        })
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_INCOMPLETE_OR_MISMATCHED$"):
            self.get_report(jv)
        self.assertEqual(jv.closes, 2)

    def test_local_json_and_html_are_create_only_no_raw_sources(self):
        report = self.get_report(FakeJv(sources()))
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LOCALAPPDATA": folder}):
                target = save_private_local(report)
                self.assertTrue(target.is_file())
                self.assertEqual(target.suffix, ".html")
                text = target.read_text("utf-8")
                self.assertIn("東京 1R", text)
                self.assertIn("過去走観測", text)
                self.assertIn("正式採点", text)
                self.assertNotIn("1000000001", text)
                payload = json.loads(target.with_suffix(".json").read_text("utf-8"))
                self.assertEqual(payload["raceCount"], 1)
                self.assertFalse(payload["productionPredictionReady"])
                self.assertNotIn("1000000001", repr(payload))
                with self.assertRaisesRegex(
                        JvLocalCheckError, "^DAY_HISTORY_ALREADY_SAVED$"):
                    save_private_local(report)
                self.assertEqual(list(target.parent.glob(".arc-race-history-*.tmp")), [])

    def test_html_rejects_unverified_or_client_supplied_report(self):
        report = self.get_report(FakeJv(sources()))
        report["bettingReady"] = True
        with self.assertRaises(CoverageError):
            local_html(report)

    def test_failed_close_never_returns_partial_records(self):
        jv = FakeJv(sources(), fail_close=True)
        with self.assertRaisesRegex(
                JvLocalCheckError, "^DAY_HISTORY_CLOSE_FAILED$"):
            self.get_report(jv)
        self.assertEqual(len(jv.opens), 1)
        self.assertEqual(jv.closes, 1)


if __name__ == "__main__":
    unittest.main()
