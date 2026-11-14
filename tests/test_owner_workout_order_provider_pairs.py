"""Synthetic result-only evaluation of frozen workout index rank pairs."""
import copy
import sys
import unittest
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_workout_order_provider_pairs import compare_workout_order_with_provider
from owner_workout_order_receipts import (
    issue_workout_locks, verify_workout_locks, WorkoutLockError
)
from test_owner_workout_order_receipts import source, SECRET, DAY, BEFORE, AFTER


def receipts():
    issued=issue_workout_locks(source(),SECRET,BEFORE)
    return verify_workout_locks(issued,SECRET,DAY)


def rows():
    return [{
        "racekey":"05994b01","racedate":DAY,
        "horse_number":f"{n:02d}",
        "order_of_finish":f"{finish:02d}",
        "trouble_classification":"0",
    } for n,finish in [(1,2),(2,1),(3,3),(4,4),(5,5)]]


class WorkoutOrderProviderPairTests(unittest.TestCase):
    def test_compares_actual_paired_order_without_index_or_runner_leaks(self):
        original=receipts()
        frozen=copy.deepcopy(original)
        result=compare_workout_order_with_provider(original,rows(),DAY,now=AFTER)
        self.assertEqual(original,frozen)
        self.assertEqual(result["studiedRaceCount"],1)
        self.assertEqual(result["observedPairsByTrainingBand"]["S"],{
            "concordant":0,"discordant":1,"equalIndexExcluded":0
        })
        self.assertEqual(result["observedPairsByTrainingBand"]["A"],{
            "concordant":0,"discordant":0,"equalIndexExcluded":1
        })
        self.assertFalse(result["accuracyVerified"])
        self.assertFalse(result["calibrationReady"])
        self.assertFalse(result["scoreReady"])
        self.assertIsNone(result["roiPercent"])
        for private in ("racekey","horse_number","order_of_finish",
                        "withinBandRank","2328aaa95a","0.01"):
            self.assertNotIn(private,repr(result))

    def test_same_study_can_be_concordant_but_is_not_a_model_score(self):
        source_rows=rows()
        source_rows[0]["order_of_finish"]="01"
        source_rows[1]["order_of_finish"]="02"
        r=compare_workout_order_with_provider(
            receipts(),source_rows,DAY,now=AFTER)
        self.assertEqual(r["observedPairsByTrainingBand"]["S"]["concordant"],1)
        self.assertEqual(r["observedPairsByTrainingBand"]["S"]["discordant"],0)
        self.assertFalse(r["newScoringRubric"])

    def test_incomplete_dead_heat_or_flagged_provider_results_are_pending(self):
        for invalid in (
            rows()[:4],
            rows()[:-1]+[dict(rows()[-1],order_of_finish="03")],
            rows()[:-1]+[dict(rows()[-1],trouble_classification="1")],
            rows()[:-1]+[dict(rows()[-1],order_of_finish="")],
            rows()[:-1]+[dict(rows()[-1],horse_number="04")],
        ):
            with self.subTest(invalid=repr(invalid)[:40]):
                x=compare_workout_order_with_provider(
                    receipts(),invalid,DAY,now=AFTER)
                self.assertEqual(x["studiedRaceCount"],0)
                self.assertEqual(x["races"][0]["providerStatus"],"pending")
                self.assertIsNone(x["races"][0]["pairCounts"])
                self.assertEqual(x["observedPairsByTrainingBand"]["S"]["discordant"],0)

    def test_before_race_no_comparison_and_zero_result_reads(self):
        x=compare_workout_order_with_provider(
            receipts(),[],DAY,now=BEFORE,source_read_count=0)
        self.assertEqual(x["studiedRaceCount"],0)
        self.assertEqual(x["sourceReadCount"],0)
        self.assertIsNone(x["races"][0]["pairCounts"])

    def test_bad_provider_identity_never_substitutes_a_horse(self):
        for field,value in (
            ("racekey","99994b01"),
            ("racedate","20990102"),
            ("horse_number","19"),
            ("order_of_finish","withdrawn"),
        ):
            damaged=rows()
            damaged[0][field]=value
            if field=="order_of_finish":
                # Nonfinish is explicitly not comparable, not an exception.
                p=compare_workout_order_with_provider(
                    receipts(),damaged,DAY,now=AFTER)
                self.assertEqual(p["studiedRaceCount"],0)
            else:
                with self.subTest(field=field),self.assertRaises(WorkoutLockError):
                    compare_workout_order_with_provider(
                        receipts(),damaged,DAY,now=AFTER)


if __name__=="__main__":
    unittest.main()
