"""Synthetic /tky-only jockey/trainer/conformation checks."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_personnel_body_materials import (
    enrich_personnel_body_matrix, summarize_personnel_body_matrix,
)
from test_jrdb_entry_rotation_materials import sample_data, calculate


def source():
    matrix, programme, entries, previous = sample_data()
    entries[0].update(jockey_name="架空騎手A", jockey_cd="01234",
                      trainer_name="架空厩舎A", trainer_cd="43210",
                      bodytype="22222222 2222", horse_bodytype_integration_cd1="12")
    entries[1].update(jockey_name="架空騎手B", trainer_name="架空厩舎B",
                      bodytype="  ")
    return matrix, programme, entries, previous


def run_case(data=None):
    matrix, programme, entries, previous = data or source()
    prepared = calculate((matrix, programme, entries, previous))
    return enrich_personnel_body_matrix(prepared, programme, entries, "20261101")


class PersonnelBodyMaterialsTests(unittest.TestCase):
    def test_attaches_presence_not_a_condition_or_rank(self):
        result = run_case()
        one = result[0]["byNumber"]["01"]
        self.assertEqual(one["jockey_stable"]["grade"], "未評価")
        self.assertTrue(one["jockey_stable"]["jockeyNameRecorded"])
        self.assertTrue(one["jockey_stable"]["trainerCodeRecorded"])
        self.assertTrue(one["body_condition"]["bodyTypeRecorded"])
        self.assertTrue(one["body_condition"]["integrationCodeRecorded"])
        self.assertFalse(result[0]["predictionReady"])

    def test_redacted_summary_and_missing_body_not_called_weight(self):
        summary = summarize_personnel_body_matrix(run_case())
        tokyo, kyoto = summary["races"]
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["recorded"]["jockeyNameRecorded"], 2)
        self.assertEqual(tokyo["recorded"]["jockeyCodeRecorded"], 1)
        self.assertEqual(tokyo["recorded"]["bothPersonnelNamesRecorded"], 2)
        self.assertEqual(tokyo["recorded"]["anyConformationRecorded"], 1)
        self.assertEqual(kyoto["recorded"]["anyConformationRecorded"], 0)
        self.assertEqual(tokyo["observedFactorSlots"], 8)
        self.assertEqual(tokyo["unmappedFactorCount"], 2)
        self.assertFalse(tokyo["bodyConditionAssessed"])
        self.assertFalse(tokyo["raceDayBodyWeightFetched"])
        self.assertFalse(summary["bettingReady"])
        for private in ("racekey", "horse_id", "horse_number", "架空騎手A",
                        "架空厩舎A", "01234", "43210", "22222222"):
            self.assertNotIn(private, repr(summary))

    def test_missing_optional_fields_are_not_assumed_present(self):
        data = source()
        for entry in data[2]:
            for field in ("jockey_name", "trainer_name", "bodytype"):
                entry.pop(field, None)
        summary = summarize_personnel_body_matrix(run_case(data))
        self.assertEqual(summary["races"][0]["recorded"]["jockeyNameRecorded"], 0)
        self.assertEqual(summary["races"][0]["recorded"]["bodyTypeRecorded"], 0)

    def test_bad_provider_fields_fail_closed(self):
        for field, bad in (("jockey_name", "unsafe\nheader"),
                           ("trainer_cd", 11), ("bodytype", "\x00secret"),
                           ("horse_bodytype_integration_cd1", ["x"])):
            data = source()
            data[2][0][field] = bad
            with self.subTest(field=field), self.assertRaises(CoverageError):
                run_case(data)

    def test_no_promoted_status_or_corrupt_counts(self):
        for factor, field, bad in (
            ("jockey_stable", "grade", "S"),
            ("body_condition", "grade", "A"),
            ("jockey_stable", "jockeyCodeRecorded", 1),
            ("body_condition", "basis", "live_weight_kg"),
        ):
            matrix = run_case()
            matrix[0]["byNumber"]["01"][factor][field] = bad
            with self.subTest(factor=factor, field=field), self.assertRaises(CoverageError):
                summarize_personnel_body_matrix(matrix)

    def test_no_mutation_and_roster_conflicts_fail(self):
        data = source()
        old = copy.deepcopy(data)
        run_case(data)
        self.assertEqual(data, old)
        data[2][0]["horse_number"] = "02"
        with self.assertRaises(CoverageError):
            run_case(data)


if __name__ == "__main__":
    unittest.main()
