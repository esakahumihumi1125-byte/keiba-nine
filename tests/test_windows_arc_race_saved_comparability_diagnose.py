"""Synthetic tests for an owner-PC-only, no-network 3連単 HOLD diagnosis."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from windows_arc_race_saved_comparability_diagnose import diagnose
from test_owner_jvdata_offline_trifecta_trial import LocalTrifectaTrialTests


class SavedComparabilityDiagnoseTests(unittest.TestCase):
    def source(self):
        return LocalTrifectaTrialTests().filled()

    def test_same_eligible_conditions_as_research_trifecta(self):
        source = self.source()
        result = diagnose(source)
        self.assertEqual(result["status"], "RESEARCH_ONLY")
        self.assertEqual(result["runnerCount"], 7)
        self.assertEqual(result["comparableRunners"], 7)
        self.assertEqual(result["missing"], [])

    def test_each_first_unmet_requirement_has_a_precise_label(self):
        cases = {
            "no_visible_recent_runs": lambda horse, race: (
                horse.update(observedRecordCount=0, recentObservedRuns=[]),
                race.update(observedHorseHistory=6)),
            "no_historical_ra7_context": lambda horse, race:
                horse["recentObservedRuns"][0].update(
                    historicalRaceContextMatched=False),
            "no_matching_surface_distance": lambda horse, race:
                horse["recentObservedRuns"][0].update(surface="ダート"),
            "no_valid_finish": lambda horse, race:
                horse["recentObservedRuns"][0].update(finishPosition=None),
            "no_valid_last_corner": lambda horse, race:
                horse["recentObservedRuns"][0]["cornerPositions"].__setitem__(3, None),
            "abnormal_or_incomplete_run": lambda horse, race:
                horse["recentObservedRuns"][0].update(hasAbnormalCode=True),
        }
        for expected, mutate in cases.items():
            with self.subTest(reason=expected):
                source = self.source()
                race = source["races"][0]
                mutate(race["byNumber"][6], race)
                result = diagnose(source)
                self.assertEqual(result["comparableRunners"], 6)
                self.assertEqual(result["missing"], [{"number": 7, "reason": expected}])
                self.assertEqual(result["reasonCounts"], {expected: 1})

    def test_course_unknown_does_not_invent_per_horse_diagnoses(self):
        source = self.source()
        source["races"][0]["distanceMetersCandidate"] = None
        result = diagnose(source)
        self.assertEqual(result["status"], "CURRENT_COURSE_NOT_VERIFIED")
        self.assertIsNone(result["comparableRunners"])
        self.assertEqual(result["missing"], [])

    def test_does_not_copy_paid_ids_or_arbitrary_source_fields(self):
        source = self.source()
        source["privateToken"] = "SENSITIVE_TEST_TOKEN"
        source["races"][0]["byNumber"][0]["horseId"] = "PRIVATE_STUDY_HORSE"
        result = diagnose(source)
        self.assertNotIn("SENSITIVE_TEST_TOKEN", repr(result))
        self.assertNotIn("PRIVATE_STUDY_HORSE", repr(result))


if __name__ == "__main__":
    unittest.main()
