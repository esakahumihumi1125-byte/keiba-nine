"""Synthetic-only current race / past results linking: no JV-Link or real data."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_jvdata_day_history_bridge import build_local_day_history, MAX_HISTORY_BATCH
from test_jvdata_ra_se_candidate import make, replace, DAY
from test_owner_jvdata_horse_history_preview import sample, old_ra

JST = timezone(timedelta(hours=9))
BEFORE = datetime(2026, 11, 20, 18, tzinfo=JST)
AFTER = datetime(2026, 11, 21, 11, tzinfo=JST)


def current():
    return [make("RA"), *(make("SE", horse=n) for n in range(1, 5))]


def bridge(history, *, sources=None, now=BEFORE):
    return build_local_day_history(
        sources if sources is not None else current(), history, DAY,
        captured_at=now,
    )


class DayJvDataHistoryBridgeTests(unittest.TestCase):
    def test_current_horses_join_correct_past_results_and_ra(self):
        history = [
            sample(1, day="20251012"), sample(1, day="20250802"),
            sample(3, day="20251012"), sample(7, day="20251012"),
            old_ra(day="20251012", track="11", distance="1800"),
            old_ra(day="20250802", track="24", distance="1600", dirt="3"),
        ]
        result = bridge(history)
        self.assertEqual(result["raceCount"], 1)
        self.assertEqual(result["races"][0]["track"], "東京")
        self.assertEqual(result["races"][0]["race"], 1)
        numbers = {row["number"]: row for row in result["races"][0]["byNumber"]}
        self.assertEqual(numbers[1]["observedRecordCount"], 2)
        self.assertEqual(numbers[3]["observedRecordCount"], 1)
        self.assertEqual(numbers[2]["observedRecordCount"], 0)
        self.assertEqual(numbers[4]["observedRecordCount"], 0)
        self.assertEqual(numbers[1]["recentObservedRuns"][0]["distanceMeters"], 1800)
        self.assertEqual(numbers[1]["recentObservedRuns"][0]["surface"], "芝")
        self.assertEqual(numbers[1]["recentObservedRuns"][1]["distanceMeters"], 1600)
        self.assertEqual(numbers[1]["recentObservedRuns"][1]["surface"], "ダート")
        self.assertFalse(result["formalTenFactorReady"])
        self.assertFalse(result["productionPredictionReady"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["newProviderRequests"], 0)
        for forbidden in ("1000000001", "1000000003",
                          "registrationId", "horse_id", "SECRET_FILENAME"):
            self.assertNotIn(forbidden, repr(result))

    def test_empty_history_is_not_debut_claim(self):
        x = bridge([])
        self.assertFalse(x["historyCompletenessVerified"])
        self.assertTrue(all(
            horse["missingHistoryUnproven"] for horse in x["races"][0]["byNumber"]
        ))
        self.assertEqual(x["races"][0]["status"], "no_matched_history_observed")

    def test_post_off_never_creates_prestart_research(self):
        x = bridge([sample(1), old_ra()], now=AFTER)
        self.assertEqual(x["races"][0]["status"], "post_off_capture_hold")
        self.assertEqual(x["races"][0]["observedHorseHistory"], 0)
        self.assertTrue(all(not h["recentObservedRuns"]
                            for h in x["races"][0]["byNumber"]))
        self.assertFalse(x["formalTenFactorReady"])

    def test_missing_se_or_ra_blocks_incomplete_current_card(self):
        cases = (current()[1:], current()[:-1])
        for case in cases:
            with self.subTest(case=len(case)), self.assertRaises(CoverageError):
                bridge([], sources=case)

    def test_duplicate_current_roster_and_conflicts_are_blocked(self):
        rows = current()
        self.assertEqual(bridge([], sources=rows + [rows[-1]])["raceCount"], 1)
        with self.assertRaises(CoverageError):
            bridge([], sources=rows + [replace(rows[-1], 30, 40, "1234567890")])
        with self.assertRaises(CoverageError):
            bridge([], sources=rows + [replace(rows[0], 873, 877, "1100")])

    def test_conflicting_historical_revision_is_not_silently_selected(self):
        one = sample(1)
        with self.assertRaises(CoverageError):
            bridge([one, replace(one, 334, 336, "01")])
        a = old_ra()
        with self.assertRaises(CoverageError):
            bridge([sample(1), a, replace(a, 697, 701, "2400")])

    def test_later_record_and_date_mismatch_are_not_accepted(self):
        for raw in (replace(sample(1), 3, 11, "20261122"),
                    sample(1, day=DAY)):
            with self.subTest(raw=raw[:16]), self.assertRaises(CoverageError):
                bridge([raw])
        row = current()
        with self.assertRaises(CoverageError):
            bridge([], sources=[replace(row[0], 11, 15, "2025"), *row[1:]])

    def test_race_list_cannot_contain_other_category_or_go_unbounded(self):
        with self.assertRaises(CoverageError):
            bridge([], sources=[replace(current()[0], 2, 3, "7"),
                                *current()[1:]])
        with self.assertRaises(CoverageError):
            bridge([], sources=current() * 1001)
        with self.assertRaises(CoverageError):
            bridge([sample(1)] * (MAX_HISTORY_BATCH + 1))

    def test_unrelated_overseas_historical_races_cannot_block_matched_horse(self):
        # Full RCVN streams can include other horses and venues; unrelated
        # records must not distort an active runner's valid historical match.
        unrelated_ra = replace(old_ra(day="20250715"), 19, 21, "90")
        unrelated_se = replace(sample(7, day="20250715"), 19, 21, "90")
        result = bridge([
            sample(1), old_ra(),
            unrelated_ra, unrelated_se,
        ])
        runs = result["races"][0]["byNumber"][0]["recentObservedRuns"]
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["finishPosition"], 8)
        self.assertEqual(runs[0]["distanceMeters"], 1800)
        self.assertFalse(result["formalTenFactorReady"])

    def test_not_all_historical_ra_must_be_present(self):
        result = bridge([sample(1)])
        run = result["races"][0]["byNumber"][0]["recentObservedRuns"][0]
        self.assertIsNone(run["distanceMeters"])
        self.assertIsNone(run["surface"])
        self.assertFalse(run["historicalRaceContextMatched"])


if __name__ == "__main__":
    unittest.main()
