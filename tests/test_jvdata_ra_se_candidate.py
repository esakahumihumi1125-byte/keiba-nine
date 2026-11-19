"""Synthetic fixed-layout RA/SE tests. No JV-Link, JRA data or paid calls."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jvdata_ra_se_candidate import (
    RA_LENGTH, SE_LENGTH, parse_jvdata_prestart_racecard,
    compare_jvdata_candidate_to_jrdb,
)

DAY = "20261121"


def put(row, start, end, text):
    value = text.encode("ascii")
    assert len(value) == end - start
    row[start:end] = value


def make(kind, *, horse=1, frame=1, horse_id=None):
    n = RA_LENGTH if kind == "RA" else SE_LENGTH
    row = bytearray(b" " * (n - 2) + b"\r\n")
    put(row, 0, 2, kind)
    put(row, 2, 3, "2")  # Only numbered prestart racecards.
    put(row, 3, 11, "20261120")
    put(row, 11, 15, "2026")
    put(row, 15, 19, "1121")
    put(row, 19, 21, "05")
    put(row, 21, 23, "05")
    put(row, 23, 25, "05")
    put(row, 25, 27, "01")
    if kind == "RA":
        put(row, 873, 877, "1000")
        put(row, 881, 883, "04")
    else:
        put(row, 27, 28, str(frame))
        put(row, 28, 30, f"{horse:02d}")
        put(row, 30, 40, horse_id or f"{1000000000 + horse:010d}")
    return bytes(row)


def sample():
    return make("RA"), [make("SE", horse=i) for i in range(1, 5)]


def replace(row, start, end, text):
    changed = bytearray(row)
    put(changed, start, end, text)
    return bytes(changed)


def candidate():
    return parse_jvdata_prestart_racecard(*sample(), DAY)


def jrdb():
    programme = {
        "racekey": "05265501", "racedate": DAY, "track": "東京",
        "race": 1, "post_time": "10:00", "headcount": 4,
        "programmeOnly": True, "horsesVerified": False,
    }
    entries = [{
        "racekey": programme["racekey"], "racedate": DAY,
        "horse_number": f"{number:02d}", "withdrawn_flag": "0",
    } for number in range(1, 5)]
    return programme, entries


class JvDataRaSeCandidateTests(unittest.TestCase):
    def test_private_ra_and_se_create_race_bound_numbered_candidate(self):
        ra, se = sample()
        unchanged = (ra, se[:])
        parsed = parse_jvdata_prestart_racecard(ra, se, DAY)
        self.assertEqual((ra, se), unchanged)
        self.assertEqual(parsed["track"], "東京")
        self.assertEqual(parsed["race"], 1)
        self.assertEqual(parsed["postTimeCandidate"], "10:00")
        self.assertEqual(parsed["registeredRunnerCount"], 4)
        self.assertEqual(parsed["horseNumbersCandidate"], [1, 2, 3, 4])
        self.assertFalse(parsed["independentlyAuthenticated"])
        self.assertFalse(parsed["finalStarterListVerified"])
        self.assertFalse(parsed["scratchStatusVerified"])
        self.assertFalse(parsed["latestGoingVerified"])
        self.assertFalse(parsed["officialFinalPostTimeVerified"])
        self.assertFalse(parsed["bettingReady"])
        self.assertEqual(parsed["newProviderRequests"], 0)
        for secret in ("1000000001", "horse_id", "racekey", "05" * 6):
            self.assertNotIn(secret, repr(parsed))

    def test_genuine_shape_only_still_cannot_be_official(self):
        record = candidate()
        p, e = jrdb()
        before = copy.deepcopy((record, p, e))
        comparison = compare_jvdata_candidate_to_jrdb(record, p, e)
        self.assertEqual((record, p, e), before)
        self.assertEqual(comparison["status"], "candidate_matched_not_final")
        self.assertTrue(comparison["raceAndNumbersCandidateMatch"])
        self.assertTrue(comparison["scheduledPostCandidateMatch"])
        self.assertTrue(comparison["withdrawalStatusUnresolved"])
        self.assertFalse(comparison["independentOfficialJraVerified"])
        self.assertFalse(comparison["productionPredictionReady"])
        self.assertFalse(comparison["bettingReady"])
        self.assertEqual(comparison["newJrdbProviderRequests"], 0)
        e[-1]["withdrawn_flag"] = "1"
        result = compare_jvdata_candidate_to_jrdb(record, p, e)
        self.assertTrue(result["possibleWithdrawnInJrdb"])
        self.assertTrue(result["withdrawalStatusUnresolved"])
        self.assertFalse(result["currentScratchesVerified"])

    def test_differing_time_roster_or_headcount_holds(self):
        record = candidate()
        for kind in ("time", "horse", "count"):
            p, e = jrdb()
            if kind == "time":
                p["post_time"] = "10:05"
            elif kind == "horse":
                e[0]["horse_number"] = "09"
            else:
                p["headcount"] = 5
            out = compare_jvdata_candidate_to_jrdb(record, p, e)
            self.assertEqual(out["status"], "hold_source_mismatch")
            self.assertFalse(out["productionPredictionReady"])

    def test_source_type_length_record_category_and_dates_rejected(self):
        ra, se = sample()
        for wrong_ra, wrong_se, day in (
            (ra[:-1], se, DAY),
            (replace(ra, 2, 3, "1"), se, DAY),
            (replace(ra, 2, 3, "7"), se, DAY),
            (replace(ra, 19, 21, "99"), se, DAY),
            (replace(ra, 873, 877, "2560"), se, DAY),
            (replace(ra, 3, 11, "20261122"), se, DAY),
            (replace(ra, 15, 19, "1122"), se, DAY),
            (ra, [replace(se[0], 2, 3, "3"), *se[1:]], DAY),
            (ra, [replace(se[0], 25, 27, "02"), *se[1:]], DAY),
            (ra, [replace(se[0], 28, 30, "00"), *se[1:]], DAY),
            (ra, [replace(se[0], 27, 28, "0"), *se[1:]], DAY),
            (ra, [replace(se[0], 30, 40, "0000000000"), *se[1:]], DAY),
            (ra, [se[0], se[0], se[2], se[3]], DAY),
            (ra, se[:3], DAY),
            (ra, se, "20261120"),
        ):
            with self.subTest(wrong_ra=wrong_ra[:3], day=day), self.assertRaises(
                    CoverageError):
                parse_jvdata_prestart_racecard(wrong_ra, wrong_se, day)

    def test_foreign_jrdb_runner_and_promoted_flags_rejected(self):
        jv = candidate()
        p, e = jrdb()
        e[0]["racekey"] = "08265501"
        with self.assertRaises(CoverageError):
            compare_jvdata_candidate_to_jrdb(jv, p, e)
        p, e = jrdb()
        jv["finalStarterListVerified"] = True
        with self.assertRaises(CoverageError):
            compare_jvdata_candidate_to_jrdb(jv, p, e)


if __name__ == "__main__":
    unittest.main()
