"""Synthetic provider-only entry/pedigree/draw/rotation evidence checks."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_private_factor_bridge import build_private_factor_matrix
from jrdb_entry_rotation_materials import (
    enrich_entry_materials_matrix, summarize_entry_materials_matrix,
)
from test_jrdb_private_factor_bridge import inputs
from test_jrdb_evidence_readiness import sample
from test_jrdb_recent_hypothesis import fixture


def sample_data():
    training, recent = inputs()
    matrix = build_private_factor_matrix(training, recent)
    programme, entries, _, _ = sample()
    _, _, previous = fixture()
    entries[0].update(
        sire_name="架空父馬A", mare_sire_name="架空母父A",
        bracket_number="1", weight_to_carry="56.0")
    entries[1].update(
        sire_name="架空父馬B", bracket_number="2", weight_to_carry="55.5")
    # 16 days from the target day (still more recent than the second run).
    previous[1]["race_back_1_racedate"] = "20261016"
    return matrix, programme, entries, previous


def calculate(source=None):
    matrix, programme, entries, previous = source or sample_data()
    return enrich_entry_materials_matrix(matrix, programme, entries, previous,
                                         "20261101")


class EntryRotationMaterialsTests(unittest.TestCase):
    def test_bloodlines_draw_weight_and_intervals_are_observations_only(self):
        result = calculate()
        first = result[0]["byNumber"]["01"]
        self.assertEqual(first["pedigree"], {
            "grade": "未評価", "basis": "documented_parentage_presence",
            "sireRecorded": True, "maternalSireRecorded": True})
        self.assertEqual(first["draw_weight"], {
            "grade": "未評価", "basis": "documented_draw_weight_presence",
            "bracketRecorded": True, "assignedWeightRecorded": True})
        self.assertEqual(first["rotation"]["intervalBucket"], "under14Days")
        second = result[0]["byNumber"]["02"]
        self.assertFalse(second["pedigree"]["maternalSireRecorded"])
        self.assertEqual(second["rotation"]["intervalBucket"], "days14to55")
        third = result[1]["byNumber"]["01"]
        self.assertEqual(third["rotation"]["intervalBucket"], "unknown")
        self.assertFalse(third["draw_weight"]["assignedWeightRecorded"])
        self.assertEqual(first["training"]["basis"], "experimental_workout_index")
        self.assertEqual(first["pace"]["grade"], "未評価")
        self.assertFalse(result[0]["predictionReady"])

    def test_redacted_per_race_only(self):
        report = summarize_entry_materials_matrix(calculate())
        self.assertEqual(report["version"], "entry-pedigree-draw-rotation-materials-1")
        self.assertFalse(report["predictionReady"])
        first, second = report["races"]
        self.assertEqual(first["runnerCount"], 2)
        self.assertEqual(first["entryObservations"], {
            "sireRecorded": 2, "maternalSireRecorded": 1,
            "bothPedigreeRecorded": 1, "bracketRecorded": 2,
            "weightRecorded": 2, "drawAndWeightRecorded": 2,
        })
        self.assertEqual(first["rotationIntervals"], {
            "under14Days": 1, "days14to55": 1, "days56plus": 0, "unknown": 0,
        })
        self.assertEqual(second["rotationIntervals"]["unknown"], 1)
        self.assertEqual(first["unmappedFactorCount"], 4)
        self.assertEqual(first["verifiedFactorCount"], 0)
        self.assertFalse(first["pedigreeAptitudeAssessed"])
        self.assertFalse(first["rotationEffectAssessed"])
        self.assertFalse(first["drawWeightEffectAssessed"])
        for secret in ("racekey", "byNumber", "horse_id", "horse_number",
                       "2328aaa95a05", "架空父馬A", "架空母父A",
                       "weight_to_carry", "56.0", "PRIVATE-HORSE"):
            self.assertNotIn(secret, repr(report))

    def test_old_race_interval_is_observed_not_negative_fitness(self):
        data = sample_data()
        data[3][0]["race_back_1_racedate"] = "20260820"
        # Make historic dates descend; the latest date remains valid.
        data[3][0]["race_back_2_racedate"] = "20260801"
        data[3][0]["race_back_3_racedate"] = "20260720"
        row = calculate(data)[0]["byNumber"]["01"]["rotation"]
        self.assertEqual(row["intervalBucket"], "days56plus")
        self.assertEqual(row["grade"], "未評価")

    def test_missing_recent_date_is_unknown_not_first_time_starter(self):
        data = sample_data()
        data[3].clear()
        result = summarize_entry_materials_matrix(calculate(data))
        self.assertEqual(result["races"][0]["rotationIntervals"]["unknown"], 2)
        self.assertEqual(result["races"][1]["rotationIntervals"]["unknown"], 1)
        self.assertFalse(result["races"][0]["predictionReady"])

    def test_reject_invalid_optional_provider_formats(self):
        cases = [
            ("bracket_number", "9"), ("bracket_number", "01"),
            ("bracket_number", 1), ("bracket_number", True),
            ("weight_to_carry", -1), ("weight_to_carry", "abc"),
            ("weight_to_carry", "99.0"), ("weight_to_carry", True),
            ("weight_to_carry", "55.555"), ("sire_name", 33),
            ("sire_name", "\nPRIVATE"), ("mare_sire_name", "  "),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                data = sample_data()
                data[2][0][field] = value
                with self.assertRaises(CoverageError):
                    calculate(data)

    def test_missing_mixed_identity_or_future_race_rejected(self):
        for invalid in ("future", "duplicate", "horse_id", "wrong_number",
                        "entry_racedate", "runner"):
            data = sample_data()
            if invalid == "future":
                data[3][0]["race_back_1_racedate"] = "20261102"
            elif invalid == "duplicate":
                data[3].append(copy.deepcopy(data[3][0]))
            elif invalid == "horse_id":
                data[3][0]["horse_id"] = data[2][1]["horse_id"]
            elif invalid == "wrong_number":
                # Number belongs to no entrant, even though the horse ID resolves.
                data[3][0]["horse_number"] = "18"
            elif invalid == "entry_racedate":
                data[2][0]["racedate"] = "20261001"
            else:
                data[0][0]["byNumber"]["03"] = data[0][0]["byNumber"].pop("02")
            with self.subTest(invalid=invalid), self.assertRaises(CoverageError):
                calculate(data)

    def test_corrupt_status_and_promotion_never_accepted(self):
        for slot, field, value in [
            ("pedigree", "grade", "S"),
            ("draw_weight", "grade", "A"),
            ("rotation", "grade", "S"),
            ("pedigree", "sireRecorded", 1),
            ("rotation", "intervalBucket", "restedAndReady"),
        ]:
            result = calculate()
            result[0]["byNumber"]["01"][slot][field] = value
            with self.subTest(slot=slot, field=field), self.assertRaises(CoverageError):
                summarize_entry_materials_matrix(result)
        result = calculate()
        result[0]["predictionReady"] = True
        with self.assertRaises(CoverageError):
            summarize_entry_materials_matrix(result)

    def test_source_inputs_and_existing_factor_matrix_unchanged(self):
        source = sample_data()
        frozen = copy.deepcopy(source)
        output = calculate(source)
        summarize_entry_materials_matrix(output)
        self.assertEqual(source, frozen)
        self.assertEqual(source[0][0]["byNumber"]["01"]["rotation"],
                         {"grade": "未評価", "basis": "not_mapped"})


if __name__ == "__main__":
    unittest.main()
