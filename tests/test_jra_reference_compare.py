"""No external JRA connection: independent snapshots below are all fictional."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jra_reference_compare import (
    compare_independent_race_snapshot, ReferenceCompareError
)
from jrdb_coverage import CoverageError
from test_jrdb_race_day_gates import fixture


def source():
    programme, entries, conditions = fixture()
    entries[0]["jockey_code"] = "A001"
    entries[1]["jockey_code"] = "B002"
    return programme, entries, conditions


def independent():
    return {
        "date": "20261101",
        "source": "operator_transcription",
        "races": [
            {
                "track": "東京", "race": 1, "completeRoster": True,
                "surface": "芝", "going": "重", "postTime": "10:00",
                "entries": [
                    {"horseNumber": "01", "status": "active", "jockeyCode": "A001"},
                    {"horseNumber": "02", "status": "withdrawn", "jockeyCode": None},
                ],
            },
            {
                "track": "京都", "race": 1, "completeRoster": True,
                "surface": "ダート", "going": None, "postTime": "10:05",
                "entries": [
                    {"horseNumber": "01", "status": "unknown", "jockeyCode": None},
                ],
            },
        ],
    }


def compare(reference=None, bundle=None):
    p, e, c = bundle if bundle is not None else source()
    return compare_independent_race_snapshot(p, e, c, "20261101", reference)


class IndependentReferenceCompareTests(unittest.TestCase):
    def test_no_reference_default_is_pending_and_not_verified(self):
        out = compare()
        self.assertEqual(out["racesMissingReference"], 2)
        self.assertEqual(out["racesCompared"], 0)
        self.assertEqual(out["racesWithDifferences"], 0)
        self.assertEqual({r["comparisonStatus"] for r in out["races"]},
                         {"missing_reference"})
        self.assertTrue(all(r["differenceCount"] == 0 for r in out["races"]))
        self.assertFalse(out["officialJraFinalVerification"])
        self.assertFalse(out["predictionReady"])
        self.assertFalse(out["bettingReady"])

    def test_exact_available_fields_match_but_never_prove_official_origin(self):
        out = compare(independent())
        tokyo = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["differenceCount"], 0)
        self.assertTrue(tokyo["independentReferenceProvided"])
        self.assertGreater(tokyo["comparableFields"], 0)
        self.assertFalse(tokyo["independentSnapshotAuthenticated"])
        self.assertFalse(tokyo["officialJraFinalVerification"])
        self.assertFalse(tokyo["predictionReady"])
        self.assertFalse(tokyo["bettingReady"])
        self.assertEqual(out["racesCompared"], 2)
        self.assertEqual(out["racesWithDifferences"], 0)

    def test_categories_count_without_exposing_horse_numbers(self):
        snap = independent()
        tokyo = snap["races"][0]
        tokyo["postTime"] = "10:15"
        tokyo["going"] = "稍重"
        tokyo["surface"] = "ダート"
        tokyo["entries"][0]["status"] = "withdrawn"
        tokyo["entries"][0]["jockeyCode"] = "Z999"
        tokyo["entries"][1]["horseNumber"] = "03"
        out = compare(snap)
        race = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(race["differenceCategories"]["postTime"], 1)
        self.assertEqual(race["differenceCategories"]["going"], 1)
        self.assertEqual(race["differenceCategories"]["surface"], 1)
        self.assertEqual(race["differenceCategories"]["withdrawal"], 1)
        self.assertEqual(race["differenceCategories"]["roster"], 2)
        self.assertEqual(race["differenceCount"], 6)
        self.assertEqual(race["comparisonStatus"], "differences_found")
        self.assertEqual(out["racesWithDifferences"], 1)
        for private in ("A001", "B002", "Z999", "horseNumber",
                        "jockey_code", "racekey", "LICENSED-HORSE-PRIVATE"):
            self.assertNotIn(private, repr(out))

    def test_only_jockey_change_is_visible_as_count(self):
        snap = independent()
        snap["races"][0]["entries"][0]["jockeyCode"] = "Z999"
        tokyo = next(r for r in compare(snap)["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["differenceCategories"]["jockey"], 1)
        self.assertEqual(tokyo["differenceCount"], 1)
        self.assertFalse(tokyo["officialStarterListVerified"])

    def test_partial_reference_missing_horse_does_not_equal_cancelled(self):
        snap = independent()
        snap["races"][0]["entries"].pop()
        snap["races"][0]["completeRoster"] = False
        tokyo = next(r for r in compare(snap)["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["differenceCategories"]["roster"], 0)
        self.assertGreater(tokyo["unknownComparisons"], 0)
        self.assertFalse(tokyo["officialJraFinalVerification"])

    def test_complete_reference_missing_horse_is_roster_difference(self):
        snap = independent()
        snap["races"][0]["entries"].pop()
        tokyo = next(r for r in compare(snap)["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["differenceCategories"]["roster"], 1)

    def test_date_race_roster_and_duplicate_validation(self):
        cases = ("date", "source", "other_track", "same_race", "duplicate_horse",
                 "unknown_status", "bad_jockey", "extra_field", "bool_race",
                 "unknown_surface", "bad_time", "bad_going")
        for case in cases:
            snap = independent()
            if case == "date":
                snap["date"] = "20261102"
            elif case == "source":
                snap["source"] = "JRA_100pct_verified"
            elif case == "other_track":
                snap["races"][0]["track"] = "札幌"
            elif case == "same_race":
                snap["races"][1]["track"] = "東京"
            elif case == "duplicate_horse":
                snap["races"][0]["entries"][1]["horseNumber"] = "01"
            elif case == "unknown_status":
                snap["races"][0]["entries"][0]["status"] = "excluded"
            elif case == "bad_jockey":
                snap["races"][0]["entries"][0]["jockeyCode"] = "A***"
            elif case == "extra_field":
                snap["races"][0]["horseSecret"] = "DO-NOT-LEAK"
            elif case == "bool_race":
                snap["races"][0]["race"] = True
            elif case == "unknown_surface":
                snap["races"][0]["surface"] = "謎"
            elif case == "bad_time":
                snap["races"][0]["postTime"] = "25:70"
            elif case == "bad_going":
                snap["races"][0]["going"] = "超不良"
            with self.subTest(case=case), self.assertRaises(ReferenceCompareError) as cm:
                compare(snap)
            self.assertNotIn("DO-NOT-LEAK", str(cm.exception))

    def test_unverified_source_flags_cannot_be_silently_corrected(self):
        p, entries, c = source()
        entries[0]["withdrawn_flag"] = "bad"
        with self.assertRaises((ReferenceCompareError, CoverageError)):
            compare(independent(), (p, entries, c))

    def test_missing_snapshot_only_does_not_mutate_inputs(self):
        p, e, c = source()
        snap = independent()
        initial = copy.deepcopy((p, e, c, snap))
        compare(snap, (p, e, c))
        self.assertEqual((p, e, c, snap), initial)


if __name__ == "__main__":
    unittest.main()
