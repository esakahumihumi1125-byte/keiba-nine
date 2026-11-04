"""Strict synthetic tests for combined redacted private ten-slot materials."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_private_factor_bridge import build_private_factor_matrix
from jrdb_going_history import build_going_history_observations
from jrdb_course_ground_factor_bridge import enrich_course_ground_matrix
from jrdb_entry_rotation_materials import enrich_entry_materials_matrix
from jrdb_personnel_body_materials import enrich_personnel_body_matrix
from jrdb_complete_factor_materials import combine_ten_factor_observations
from test_jrdb_going_history import sample_going


def matrices(*, complete=True):
    programme, entries, previous, past, old, today = sample_going()
    entries[0].update(
        jockey_name="PRIVATE-JOCKEY", trainer_name="PRIVATE-TRAINER",
        sire_name="PRIVATE-SIRE", bracket_number="1",
        weight_to_carry="56.0", bodytype="PRIVATE-BODYCODE",
    )
    training = build_training_hints(programme, entries, [], "20261101")
    recent = build_recent_hints(programme, entries, previous, "20261101")
    base = build_private_factor_matrix(training, recent)
    history = build_going_history_observations(
        programme, entries, previous, past, old, today, "20261101")
    course = enrich_course_ground_matrix(base, history, history_complete=complete)
    entry = enrich_entry_materials_matrix(
        base, programme, entries, previous, "20261101")
    personnel = enrich_personnel_body_matrix(
        entry, programme, entries, "20261101")
    return course, personnel


class CombinedMaterialsTests(unittest.TestCase):
    def test_join_ten_slots_with_zero_verified_grade(self):
        report = combine_ten_factor_observations(*matrices())
        self.assertEqual(report["version"], "combined-ten-factor-observations-1")
        self.assertEqual(report["raceCount"], 2)
        tokyo = next(x for x in report["races"] if x["track"] == "東京")
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["sourceMaterialSlots"], 10)
        self.assertEqual(tokyo["provisionalFactorSlots"], 2)
        self.assertEqual(tokyo["observationOnlySlots"], 8)
        self.assertEqual(tokyo["unmappedFactorCount"], 0)
        self.assertEqual(tokyo["verifiedFactorCount"], 0)
        self.assertEqual(tokyo["runnersWithComparableCourse"], 1)
        self.assertEqual(tokyo["runnersWithKnownGoingComparable"], 1)
        self.assertEqual(tokyo["runnersWithBothPersonnelNames"], 1)
        self.assertEqual(tokyo["runnersWithConformationCodes"], 1)
        self.assertFalse(tokyo["officialJraFinalVerification"])
        self.assertFalse(tokyo["overallRankReady"])
        self.assertFalse(tokyo["predictionReady"])
        self.assertFalse(report["bettingReady"])

    def test_missing_history_is_not_aptitude_or_forecast(self):
        report = combine_ten_factor_observations(*matrices(complete=False))
        self.assertGreater(report["races"][1]["runnersWithIncompleteHistory"], 0)
        self.assertFalse(report["predictionReady"])

    def test_no_raw_runner_or_source_values_in_aggregate(self):
        report = combine_ten_factor_observations(*matrices())
        for secret in ("racekey", "horse_id", "horse_number", "byNumber",
                       "PRIVATE-JOCKEY", "PRIVATE-TRAINER", "PRIVATE-SIRE",
                       "PRIVATE-BODYCODE", "PAID-SECRET", "056.0"):
            self.assertNotIn(secret, repr(report))

    def test_identity_and_base_material_conflicts_rejected(self):
        for mode in ("race", "runner", "training"):
            course, person = matrices()
            if mode == "race":
                person[0]["racekey"] = "05264001"
            elif mode == "runner":
                person[0]["byNumber"]["03"] = person[0]["byNumber"].pop("02")
            else:
                person[0]["byNumber"]["01"]["training"]["grade"] = "S"
            with self.subTest(mode=mode), self.assertRaises(CoverageError):
                combine_ten_factor_observations(course, person)

    def test_promoting_unverified_observation_to_grade_rejected(self):
        for matrix_index, factor in ((0, "ground"), (0, "course_distance"),
                                     (1, "jockey_stable"), (1, "body_condition")):
            source = list(matrices())
            source[matrix_index][0]["byNumber"]["01"][factor]["grade"] = "S"
            with self.subTest(factor=factor), self.assertRaises(CoverageError):
                combine_ten_factor_observations(*source)

    def test_inputs_unchanged(self):
        source = matrices()
        original = copy.deepcopy(source)
        combine_ten_factor_observations(*source)
        self.assertEqual(source, original)


if __name__ == "__main__":
    unittest.main()
