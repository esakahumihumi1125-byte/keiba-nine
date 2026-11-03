"""Pre-start freshness is a diagnostic, never a live prediction or official proof."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_prestart_freshness import audit_prestart_freshness, FreshnessError
from jrdb_race_context import RaceContextError
from test_jrdb_race_context import fake


class PrestartFreshnessTests(unittest.TestCase):
    NOW = "2026-11-01T09:30:00+09:00"

    def test_recent_timestamp_and_upcoming_race_are_only_review_candidates(self):
        p, holding = fake()
        holding[0]["updated_at"] = "2026-11-01T09:05:00+09:00"
        out = audit_prestart_freshness(p, holding, "20261101", self.NOW)
        rows = {(r["track"], r["race"]): r for r in out["races"]}
        tokyo = rows["東京", 1]
        self.assertEqual(tokyo["minutesUntilListedPost"], 30)
        self.assertEqual(tokyo["prestartWindow"], "within_two_hours")
        self.assertEqual(tokyo["sourceGoingAgeStatus"], "recent_reported")
        self.assertEqual(tokyo["sourceGoingUpdateAgeMinutes"], 25)
        self.assertTrue(tokyo["candidateForManualJraReview"])
        self.assertEqual(out["manualJraReviewCandidates"], 2)
        self.assertEqual(out["officiallyVerifiedRaces"], 0)
        self.assertFalse(out["predictionReady"])
        self.assertFalse(tokyo["finalRaceReady"])
        self.assertFalse(tokyo["bettingReady"])
        self.assertFalse(tokyo["jraOfficialDataFetched"])
        self.assertFalse(tokyo["jraPostTimeVerified"])
        self.assertEqual(rows["京都", 1]["sourceGoingAgeStatus"], "no_going_report")

    def test_stale_day_before_timestamp_not_promoted(self):
        p, holding = fake()
        out = audit_prestart_freshness(p, holding, "20261101", self.NOW)
        row = next(r for r in out["races"] if r["track"] == "東京" and r["race"] == 1)
        self.assertEqual(row["sourceGoingAgeStatus"], "old_or_other_date_reported")
        self.assertEqual(row["sourceGoingUpdateAgeMinutes"], 17 * 60)
        self.assertEqual(out["manualJraReviewCandidates"], 0)
        self.assertEqual(out["racesWithRecentlyReportedGoing"], 0)

    def test_other_calendar_day_is_not_prestart_ready(self):
        p, holding = fake()
        holding[0]["updated_at"] = "2026-11-01T09:05:00+09:00"
        out = audit_prestart_freshness(
            p, holding, "20261101", "2026-10-31T23:30:00+09:00"
        )
        tokyo = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["prestartWindow"], "other_date")
        self.assertEqual(tokyo["sourceGoingAgeStatus"], "timestamp_in_future")
        self.assertFalse(tokyo["candidateForManualJraReview"])
        self.assertEqual(out["racesWithinTwoHours"], 0)

    def test_past_post_time_never_reopens_race_for_betting(self):
        p, holding = fake()
        holding[0]["updated_at"] = "2026-11-01T10:05:00+09:00"
        out = audit_prestart_freshness(
            p, holding, "20261101", "2026-11-01T10:35:00+09:00"
        )
        tokyo = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["prestartWindow"], "post_time_passed")
        self.assertLess(tokyo["minutesUntilListedPost"], 0)
        self.assertFalse(tokyo["candidateForManualJraReview"])

    def test_unknown_post_time_keeps_unverified(self):
        p, holding = fake()
        p[0]["post_time"] = None
        out = audit_prestart_freshness(p, holding, "20261101", self.NOW)
        self.assertEqual(out["races"][0]["prestartWindow"], "post_time_unknown")
        self.assertIsNone(out["races"][0]["minutesUntilListedPost"])
        self.assertFalse(out["races"][0]["bettingReady"])

    def test_future_update_not_silent_recent(self):
        p, holding = fake()
        holding[0]["updated_at"] = "2026-11-01T10:30:00+09:00"
        out = audit_prestart_freshness(p, holding, "20261101", self.NOW)
        row = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(row["sourceGoingAgeStatus"], "timestamp_in_future")
        self.assertIsNone(row["sourceGoingUpdateAgeMinutes"])
        self.assertFalse(row["candidateForManualJraReview"])

    def test_missing_timestamp_never_becomes_fresh(self):
        p, holding = fake()
        holding[0].pop("updated_at")
        out = audit_prestart_freshness(p, holding, "20261101", self.NOW)
        tokyo = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["sourceGoingAgeStatus"], "no_update_timestamp")
        self.assertIsNone(tokyo["sourceGoingUpdateAgeMinutes"])

    def test_timezone_offsets_are_normalized_to_japan(self):
        p, holding = fake()
        holding[0]["updated_at"] = "2026-11-01T00:05:00Z"
        out = audit_prestart_freshness(
            p, holding, "20261101", "2026-11-01T00:30:00Z"
        )
        tokyo = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["sourceGoingUpdateAgeMinutes"], 25)
        self.assertEqual(out["checkedAtJapan"], "2026-11-01 09:30 JST")

    def test_aware_clock_required(self):
        for invalid in ("2026-11-01", "2026-11-01T09:30:00", "bad",
                        "", None, 123, [], "2026-11-01T25:30:00+09:00"):
            p, holding = fake()
            with self.subTest(invalid=invalid), self.assertRaises(FreshnessError):
                audit_prestart_freshness(p, holding, "20261101", invalid)

    def test_malformed_post_time_rejected(self):
        for bad in ("24:01", "12:60", "1030", "ab:cd", 1200, True):
            p, holding = fake()
            p[0]["post_time"] = bad
            with self.subTest(value=bad), self.assertRaises(FreshnessError):
                audit_prestart_freshness(p, holding, "20261101", self.NOW)

    def test_invalid_provider_timestamp_rejected_without_exposing_raw_data(self):
        p, holding = fake()
        holding[0]["updated_at"] = "PAID_SECRET_TIMESTAMP"
        with self.assertRaises((RaceContextError, FreshnessError)) as ctx:
            audit_prestart_freshness(p, holding, "20261101", self.NOW)
        self.assertNotIn("PAID_SECRET_TIMESTAMP", str(ctx.exception))

    def test_no_raw_licensed_data_in_report_and_inputs_preserved(self):
        p, holding = fake()
        before = copy.deepcopy((p, holding))
        out = audit_prestart_freshness(p, holding, "20261101", self.NOW)
        self.assertEqual(before, (p, holding))
        for secret in ("horse_name", "holdingkey", "racekey", "SECRET-HORSE",
                       "LICENSED-SOURCE", "source_url", "api_key"):
            self.assertNotIn(secret, repr(out))


if __name__ == "__main__":
    unittest.main()
