"""Private pre-race going/track context from fictional /tra and /tka rows."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_program_preview import normalize_program_rows
from jrdb_race_context import audit_race_context, RaceContextError


def fake():
    program = normalize_program_rows([
        {"racekey": "05264b01", "racedate": "20261101",
         "post_time": "1000", "track_type": "1", "turn_cd": "2",
         "distance": "2000", "headcount": 12, "race_name": "架空1R"},
        {"racekey": "05264b02", "racedate": "20261101",
         "post_time": "1030", "track_type": "2", "turn_cd": "2",
         "distance": "1400", "headcount": 14, "race_name": "架空2R"},
        {"racekey": "08264b01", "racedate": "20261101",
         "post_time": "1010", "track_type": "3", "turn_cd": "1",
         "distance": "3000", "headcount": 8, "race_name": "架空障害"},
    ], "20261101")
    going = [
        {"holdingkey": "05264b".replace("b", "8"), "racedate": "20261101",
         "course_cd": "1", "turf_condition_cd": "02",
         "dirt_condition_cd": "4", "updated_at": "2026-10-31T16:30:00+09:00",
         "horse_name": "SECRET-HORSE", "raw_data": "LICENSED-SOURCE"},
        {"holdingkey": "082648", "racedate": "20261101",
         "course_cd": "1", "turf_condition_cd": "1", "dirt_condition_cd": "1"}
    ]
    return program, going


class RaceContextTests(unittest.TestCase):
    def test_separate_surface_and_track_going(self):
        races, holding = fake()
        output = audit_race_context(races, holding, "20261101")
        self.assertEqual(output["raceCount"], 3)
        by_key = {(r["track"], r["race"]): r for r in output["races"]}
        turf = by_key["東京", 1]
        dirt = by_key["東京", 2]
        jump = by_key["京都", 1]
        self.assertEqual((turf["surface"], turf["distance_m"], turf["turn"]),
                         ("芝", 2000, "左"))
        self.assertEqual(turf["going"], "稍重")
        self.assertEqual(dirt["going"], "不良")
        self.assertEqual(jump["going"], "未確認")
        self.assertEqual(output["goingAvailableCount"], 2)
        self.assertEqual(output["courseInfoPresentCount"], 3)
        self.assertFalse(output["predictionReady"])
        self.assertFalse(output["raceConditionsVerified"])

    def test_no_horse_suitability_grade_without_historical_data(self):
        report = audit_race_context(*fake(), "20261101")
        for row in report["races"]:
            self.assertFalse(row["horseCourseSuitabilityAssessed"])
            self.assertFalse(row["horseGoingSuitabilityAssessed"])
            self.assertFalse(row["predictionReady"])
            self.assertNotIn("grades", row)
        for secret in ("SECRET-HORSE", "LICENSED-SOURCE", "holdingkey", "racekey"):
            self.assertNotIn(secret, repr(report))

    def test_missing_current_going_is_unknown_not_good(self):
        programme, going = fake()
        going = []
        result = audit_race_context(programme, going, "20261101")
        self.assertEqual(result["goingAvailableCount"], 0)
        self.assertTrue(all(x["going"] == "未確認" for x in result["races"]))
        self.assertTrue(all(not x["conditionSnapshotPresent"] for x in result["races"]))

    def test_unverified_course_direction_keeps_context_incomplete(self):
        programme, going = fake()
        programme[0]["turn"] = None
        result = audit_race_context(programme, going, "20261101")
        self.assertFalse(result["races"][0]["courseInfoPresent"])

    def test_wrong_date_and_unknown_venue_are_rejected(self):
        for key, value in (("racedate", "20261102"),
                           ("holdingkey", "112648"),
                           ("holdingkey", "unknown")):
            programme, holding = fake()
            holding[0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(RaceContextError):
                audit_race_context(programme, holding, "20261101")

    def test_unrecognized_going_never_assumed_good(self):
        for value in ("5", "30", -1, True, "良", "NaN"):
            programme, holding = fake()
            holding[0]["turf_condition_cd"] = value
            with self.subTest(value=value), self.assertRaises(RaceContextError):
                audit_race_context(programme, holding, "20261101")

    def test_duplicate_snapshot_for_venue_rejected(self):
        programme, holding = fake()
        holding.append(copy.deepcopy(holding[0]))
        with self.assertRaises(RaceContextError):
            audit_race_context(programme, holding, "20261101")

    def test_bad_timestamp_fails_closed(self):
        for value in ("2026-11-01", "garbage", [], 123):
            programme, holding = fake()
            holding[0]["updated_at"] = value
            with self.subTest(value=value), self.assertRaises(RaceContextError):
                audit_race_context(programme, holding, "20261101")

    def test_duplicate_or_bad_programme_fails_closed(self):
        programme, holding = fake()
        programme.append(copy.deepcopy(programme[0]))
        with self.assertRaises(RaceContextError):
            audit_race_context(programme, holding, "20261101")
        programme, holding = fake()
        programme[0]["distance_m"] = "2000"
        with self.assertRaises(RaceContextError):
            audit_race_context(programme, holding, "20261101")

    def test_input_unchanged(self):
        original = fake()
        frozen = copy.deepcopy(original)
        audit_race_context(*original, "20261101")
        self.assertEqual(original, frozen)

    def test_empty_race_day_never_means_prediction_ready(self):
        empty = audit_race_context([], [], "20261101")
        self.assertEqual(empty["raceCount"], 0)
        self.assertFalse(empty["predictionReady"])


if __name__ == "__main__":
    unittest.main()
