"""Synthetic-only SE7 past-performance preview tests; no real paid records."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_jvdata_horse_history_preview import (
    parse_historical_se7_observation, preview_jvdata_horse_history,
    MAX_VISIBLE_PRIOR_RUNS,
)
from test_jvdata_ra_se_candidate import make, replace, DAY
from test_owner_jvdata_horse_history_coverage import racecard, old_result

JST = timezone(timedelta(hours=9))
PRESTART = datetime(2026, 11, 20, 18, 0, tzinfo=JST)
POSTOFF = datetime(2026, 11, 21, 10, 0, tzinfo=JST)


def sample(horse=1, *, day="20251012", race="01", finish="08"):
    row = old_result(horse, day=day, race=race)
    for start, end, value in (
        (331, 332, "0"), (334, 336, finish),
        (338, 342, "1387"), (351, 353, "05"),
        (353, 355, "03"), (355, 357, "06"),
        (357, 359, "02"), (390, 393, "356"),
        (552, 553, "3"),
        # Popularity and odds may exist but must NEVER be read.
        (359, 363, "9999"), (363, 365, "01"),
    ):
        row = replace(row, start, end, value)
    return row



def old_ra(*, day="20251012", race="01", created="20251101",
           distance="1800", track="11", turf="2", dirt="0"):
    record = make("RA")
    for start, end, value in (
        (2, 3, "7"),
        (3, 11, created),
        (11, 15, day[:4]),
        (15, 19, day[4:]),
        (25, 27, race),
        (697, 701, distance),
        (705, 707, track),
        (888, 889, turf),
        (889, 890, dirt),
    ):
        record = replace(record, start, end, value)
    return record


def preview(records, *, captured_at=PRESTART, historical_ra=None):
    ra, se = racecard()
    return preview_jvdata_horse_history(
        ra, se, records, DAY, captured_at=captured_at,
        historical_ra=historical_ra,
    )


class HorseHistoryPreviewTests(unittest.TestCase):
    def test_result_fields_are_an_observation_not_a_score(self):
        row = sample()
        observed = parse_historical_se7_observation(row, DAY)
        self.assertEqual(observed["date"], "20251012")
        self.assertEqual(observed["trackCode"], "05")
        self.assertEqual(observed["race"], 1)
        self.assertEqual(observed["finishPosition"], 8)
        self.assertEqual(observed["runTimeTenths"], 987)
        self.assertEqual(observed["cornerPositions"], [5, 3, 6, 2])
        self.assertEqual(observed["last3fTenths"], 356)
        self.assertEqual(observed["historicalRunningStyleCode"], 3)
        self.assertFalse(observed["hasAbnormalCode"])
        self.assertIsNone(observed["distanceMeters"])
        self.assertIsNone(observed["going"])
        self.assertNotIn("odds", repr(observed).lower())
        self.assertNotIn("popularity", repr(observed).lower())
        self.assertNotIn("1000000001", repr(observed))

    def test_recent_five_runs_sorted_newest_first_and_private(self):
        days = ["20251012", "20250802", "20250703",
                "20250504", "20250301", "20250102"]
        rows = [sample(1, day=day) for day in days]
        rows += [sample(3, day="20251015"), sample(7)]
        result = preview(rows)
        self.assertEqual(result["status"], "historical_observations_not_graded")
        self.assertEqual(result["maxRunsPerHorse"], MAX_VISIBLE_PRIOR_RUNS)
        self.assertEqual(len(result["byNumber"]), 4)
        by_number = {r["number"]: r for r in result["byNumber"]}
        self.assertEqual(by_number[1]["observedRecordCount"], 6)
        self.assertEqual(
            [r["date"] for r in by_number[1]["recentObservedRuns"]],
            days[:5],
        )
        self.assertEqual(by_number[2]["observedRecordCount"], 0)
        self.assertEqual(by_number[2]["recentObservedRuns"], [])
        self.assertEqual(by_number[3]["observedRecordCount"], 1)
        self.assertFalse(result["historyComplete"])
        self.assertFalse(result["outcomeStatisticsVerified"])
        self.assertFalse(result["formalTenFactorReady"])
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["newProviderRequests"], 0)
        for secret in ("1000000001", "1000000003",
                       "horse_id", "registrationId", "PRIVATE_FILE_NAME"):
            self.assertNotIn(secret, repr(result))

    def test_debut_or_missing_rows_remain_unknown(self):
        result = preview([])
        self.assertEqual(result["status"], "no_matched_history_observed")
        self.assertTrue(all(row["missingHistoryUnproven"]
                            for row in result["byNumber"]))
        self.assertEqual(sum(row["observedRecordCount"]
                             for row in result["byNumber"]), 0)
        self.assertFalse(result["formalTenFactorReady"])

    def test_no_results_and_special_sentinels_become_null_not_fast(self):
        row = sample()
        for start, end, value in (
            (334, 336, "00"), (338, 342, "9999"),
            (351, 353, "00"), (353, 355, "00"),
            (355, 357, "00"), (357, 359, "00"),
            (390, 393, "999"), (552, 553, "0"),
        ):
            row = replace(row, start, end, value)
        x = parse_historical_se7_observation(row, DAY)
        self.assertIsNone(x["finishPosition"])
        self.assertIsNone(x["runTimeTenths"])
        self.assertEqual(x["cornerPositions"], [None] * 4)
        self.assertIsNone(x["last3fTenths"])
        self.assertIsNone(x["historicalRunningStyleCode"])

    def test_conflicts_and_future_data_rejected_before_analysis(self):
        row = sample(1)
        self.assertEqual(preview([row, row])["byNumber"][0]["observedRecordCount"], 1)
        with self.assertRaises(CoverageError):
            preview([row, replace(row, 334, 336, "01")])
        for bad in (
            sample(1, day=DAY),
            sample(1, day="20261122"),
            replace(row, 3, 11, "20261122"),  # future update
            replace(row, 3, 11, "20261121"),  # created after capture day
            replace(row, 2, 3, "2"),          # current card is not a result
            replace(row, 334, 336, "XX"),     # malformed finish
            replace(row, 338, 342, "Z123"),   # malformed time
        ):
            with self.subTest(bad=bad[:14]), self.assertRaises(CoverageError):
                preview([bad])

    def test_post_off_cannot_create_retroactive_prior_run_preview(self):
        result = preview([sample(1)], captured_at=POSTOFF)
        self.assertEqual(result["status"], "post_off_capture_hold")
        self.assertTrue(all(not row["recentObservedRuns"] and
                            row["observedRecordCount"] == 0
                            for row in result["byNumber"]))
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["formalTenFactorReady"])

    def test_matching_historical_ra_supplies_course_context(self):
        row = sample(1)
        matched = old_ra(distance="1800", track="11", turf="2")
        report = preview([row], historical_ra=[matched, matched])
        first = report["byNumber"][0]["recentObservedRuns"][0]
        self.assertTrue(report["historicalRaContextJoined"])
        self.assertTrue(first["historicalRaceContextMatched"])
        self.assertEqual(first["distanceMeters"], 1800)
        self.assertEqual(first["surface"], "芝")
        self.assertEqual(first["goingCode"], 2)
        self.assertEqual(first["going"], "稍重")
        self.assertFalse(report["formalTenFactorReady"])
        self.assertFalse(report["predictionReady"])

    def test_dirt_going_and_foreign_historical_ra_are_not_crossed(self):
        row = sample(1)
        foreign = old_ra(race="02", distance="2400")
        report = preview([row], historical_ra=[foreign])
        prior = report["byNumber"][0]["recentObservedRuns"][0]
        self.assertFalse(report["historicalRaContextJoined"])
        self.assertIsNone(prior["distanceMeters"])
        self.assertFalse(prior["historicalRaceContextMatched"])
        report = preview([row], historical_ra=[
            old_ra(track="24", distance="1600", dirt="3")
        ])
        prior = report["byNumber"][0]["recentObservedRuns"][0]
        self.assertEqual(prior["distanceMeters"], 1600)
        self.assertEqual(prior["surface"], "ダート")
        self.assertEqual(prior["going"], "重")

    def test_bad_or_future_ra_context_cannot_influence_a_horse(self):
        good = old_ra()
        cases = (
            replace(good, 2, 3, "2"),
            replace(good, 3, 11, "20261121"),  # later than local capture
            replace(good, 11, 15, "2026"),     # wrong past race date
            good[:-1],
        )
        for value in cases:
            with self.subTest(value=value[:30]), self.assertRaises(CoverageError):
                preview([sample()], historical_ra=[value])
        unknown = replace(good, 705, 707, "00")
        out = preview([sample()], historical_ra=[unknown])
        run = out["byNumber"][0]["recentObservedRuns"][0]
        self.assertIsNone(run["surface"])
        self.assertIsNone(run["going"])

    def test_conflicting_ra_revisions_are_not_silently_preferred(self):
        a = old_ra(distance="1200")
        b = old_ra(distance="1800")
        with self.assertRaises(CoverageError):
            preview([sample()], historical_ra=[a, b])

    def test_post_off_ra_join_cannot_fabricate_prestart_evidence(self):
        result = preview([sample()], historical_ra=[old_ra()],
                         captured_at=POSTOFF)
        self.assertEqual(result["status"], "post_off_capture_hold")
        self.assertFalse(result["historicalRaContextJoined"])
        self.assertTrue(all(not x["recentObservedRuns"]
                            for x in result["byNumber"]))

    def test_current_race_number_mismatch_is_blocked(self):
        ra, se = racecard()
        se[-1] = replace(se[-1], 25, 27, "02")
        with self.assertRaises(CoverageError):
            preview_jvdata_horse_history(
                ra, se, [sample()], DAY, captured_at=PRESTART,
            )


if __name__ == "__main__":
    unittest.main()
