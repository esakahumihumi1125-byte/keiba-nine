"""Synthetic-only tests for past-programme comparison by historic race keys."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_course_history import (
    build_course_history_observations, summarize_course_history_observations
)
from jrdb_coverage import CoverageError
from test_jrdb_evidence_readiness import sample


def fixture():
    programme, entries, _, previous = sample()
    programme[0].update(surface="芝", distance_m=1600, turn="左")
    programme[1].update(surface="ダート", distance_m=1800, turn="右")
    previous[0].update(
        race_back_1_racekey="05264a01",
        race_back_1_order_of_finish=2,
        race_back_2_racedate="20260920",
        race_back_2_racekey="05264903",
        race_back_2_order_of_finish=4,
        horse_name="PRIVATE-HORSE-SECRET")
    previous.append({
        "racekey": "05264b01", "racedate": "20261101",
        "horse_number": "02", "horse_id": "2328aaa95a06",
        "race_back_1_racedate": "20261004",
        "race_back_1_racekey": "05264a02",
        "race_back_1_order_of_finish": 1
    })
    historical = [
        {"racekey": "05264a01", "racedate": "20261004",
         "track_type": "1", "distance": "1600", "turn_cd": "2",
         "horse_name": "LICENSED-PAST-SECRET"},
        {"racekey": "05264903", "racedate": "20260920",
         "track_type": "1", "distance": "1400", "turn_cd": "2"},
        {"racekey": "05264a02", "racedate": "20261004",
         "track_type": "2", "distance": "1600", "turn_cd": "2"},
    ]
    return programme, entries, previous, historical


class CourseHistoryTests(unittest.TestCase):
    def run_audit(self, data=None):
        return build_course_history_observations(
            *(data if data is not None else fixture()), "20261101")

    def test_exact_surface_near_distance_and_track(self):
        rows = self.run_audit()
        first = rows[0]["byNumber"]["01"]
        self.assertEqual(first["datedRuns"], 2)
        self.assertEqual(first["linkedPastProgrammes"], 2)
        self.assertEqual(first["sameSurfaceRuns"], 2)
        self.assertEqual(first["nearDistanceRuns"], 2)
        self.assertEqual(first["sameTrackRuns"], 2)
        self.assertEqual(first["sameTurnRuns"], 2)
        self.assertEqual(first["sameSurfaceNearDistanceRuns"], 2)
        self.assertEqual(first["topThreeComparableRuns"], 1)
        second = rows[0]["byNumber"]["02"]
        self.assertEqual(second["nearDistanceRuns"], 1)
        self.assertEqual(second["sameSurfaceNearDistanceRuns"], 0)
        self.assertEqual(rows[1]["byNumber"]["01"]["datedRuns"], 0)
        self.assertFalse(rows[0]["courseSuitabilityAssessed"])

    def test_only_redacted_aggregates_cross_boundary(self):
        report = summarize_course_history_observations(self.run_audit())
        row = report["races"][0]
        self.assertEqual(row["runnerCount"], 2)
        self.assertEqual(row["linkedPastRuns"], 3)
        self.assertEqual(row["unlinkedPastRuns"], 0)
        self.assertEqual(row["runnersWithComparableRun"], 1)
        self.assertEqual(row["runnersWithTwoComparableRuns"], 1)
        self.assertEqual(row["topThreeComparableObservations"], 1)
        self.assertFalse(report["predictionReady"])
        for secret in ("horse_number", "horse_id", "05264a01",
                       "PRIVATE-HORSE", "LICENSED-PAST", "byNumber", "racekey"):
            self.assertNotIn(secret, repr(report))

    def test_missing_programmes_are_not_assumed_mismatches(self):
        p, e, z, h = fixture()
        h.pop(1)
        first = self.run_audit((p, e, z, h))[0]["byNumber"]["01"]
        self.assertEqual(first["datedRuns"], 2)
        self.assertEqual(first["linkedPastProgrammes"], 1)
        self.assertEqual(first["missingPastProgrammes"], 1)
        self.assertEqual(first["sameSurfaceNearDistanceRuns"], 1)

    def test_missing_past_key_is_unknown(self):
        p, e, z, h = fixture()
        z[0].pop("race_back_2_racekey")
        h.pop(1)
        first = self.run_audit((p, e, z, h))[0]["byNumber"]["01"]
        self.assertEqual(first["datedRuns"], 2)
        self.assertEqual(first["missingPastProgrammes"], 1)

    def test_past_key_without_date_is_invalid(self):
        p, e, z, h = fixture()
        z[0]["race_back_3_racekey"] = "05264803"
        with self.assertRaises(CoverageError):
            self.run_audit((p, e, z, h))

    def test_different_dates_with_same_past_key_rejected(self):
        p, e, z, h = fixture()
        z[0]["race_back_2_racekey"] = "05264a01"
        with self.assertRaises(CoverageError):
            self.run_audit((p, e, z, h))

    def test_historical_date_must_match_race_back_date(self):
        p, e, z, h = fixture()
        h[0]["racedate"] = "20261005"
        with self.assertRaises(CoverageError):
            self.run_audit((p, e, z, h))

    def test_duplicate_past_programme_rejected(self):
        p, e, z, h = fixture()
        h.append(copy.deepcopy(h[0]))
        with self.assertRaises(CoverageError):
            self.run_audit((p, e, z, h))

    def test_historic_wrong_track_or_future_date_rejected(self):
        for key, value in (("racekey", "11264a01"),
                           ("racedate", "20261101"),
                           ("distance", "not-a-number")):
            p, e, z, h = fixture()
            h[0][key] = value
            # invalid distance means the distance is unknown, not a fatal
            # historical assertion; no match is inferred.
            if key == "distance":
                match = self.run_audit((p, e, z, h))[0]["byNumber"]["01"]
                self.assertEqual(match["nearDistanceRuns"], 1)
                continue
            with self.subTest(key=key), self.assertRaises(CoverageError):
                self.run_audit((p, e, z, h))

    def test_extra_history_rows_rejected(self):
        p, e, z, h = fixture()
        h.append({"racekey": "05264801", "racedate": "20260801",
                  "track_type": "1", "distance": "1600", "turn_cd": "2"})
        with self.assertRaises(CoverageError):
            self.run_audit((p, e, z, h))

    def test_wrong_horse_id_prevents_broken_join(self):
        p, e, z, h = fixture()
        z[0]["horse_id"] = "2328aaa95a99"
        with self.assertRaises(CoverageError):
            self.run_audit((p, e, z, h))

    def test_no_historical_rows_stays_unknown(self):
        p, e, z, _ = fixture()
        rows = self.run_audit((p, e, z, []))
        report = summarize_course_history_observations(rows)
        self.assertEqual(report["races"][0]["linkedPastRuns"], 0)
        self.assertEqual(report["races"][0]["unlinkedPastRuns"], 3)
        self.assertFalse(report["races"][0]["courseSuitabilityAssessed"])

    def test_input_immutability(self):
        data = fixture()
        before = copy.deepcopy(data)
        self.run_audit(data)
        self.assertEqual(data, before)

    def test_impossible_summary_counts_fail(self):
        rows = self.run_audit()
        rows[0]["byNumber"]["01"]["linkedPastProgrammes"] = 8
        with self.assertRaises(ValueError):
            summarize_course_history_observations(rows)


if __name__ == "__main__":
    unittest.main()
