"""Synthetic HMAC cross-grade research, no paid provider reads."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_workout_cross_band_receipts import (
    issue_cross_band_observations,verify_cross_band_observations,
)
from owner_workout_order_provider_pairs import compare_workout_order_with_provider
from owner_workout_order_receipts import WorkoutLockError
from test_owner_workout_order_provider_pairs import receipts, rows
from test_owner_workout_order_receipts import SECRET, DAY, BEFORE, AFTER


class WorkoutCrossGradeSignedTests(unittest.TestCase):
    def model(self,observations=None):
        original=receipts()
        report=compare_workout_order_with_provider(
            original,rows() if observations is None else observations,
            DAY,now=AFTER)
        return original,report

    def test_signs_only_original_postrace_hypothesis_and_zero_new_reads(self):
        original,report=self.model()
        before=copy.deepcopy((original,report))
        rows_signed=issue_cross_band_observations(
            report,original,SECRET,now=AFTER)
        self.assertEqual((original,report),before)
        self.assertEqual(len(rows_signed),1)
        p=rows_signed[0]["snapshot"]
        self.assertEqual(p["crossBandPairs"]["S>A"],
                         {"concordant":4,"discordant":0})
        self.assertEqual(p["runnerCount"],5)
        self.assertEqual(p["prestartSignature"].__len__(),64)
        self.assertFalse(p["officialJraVerified"])
        self.assertFalse(p["modelCalibrated"])
        self.assertFalse(p["actualPurchase"])
        self.assertEqual(
            verify_cross_band_observations(rows_signed,original,SECRET,DAY),
            [p])
        self.assertNotIn("racekey",repr(rows_signed))
        self.assertNotIn("horse_number",repr(rows_signed))
        self.assertNotIn("oikirisisu",repr(rows_signed))

    def test_bad_signature_changed_count_or_late_timestamp_rejected(self):
        original,report=self.model()
        signed=issue_cross_band_observations(report,original,SECRET,now=AFTER)
        changes=[
            lambda r:r[0].update(signature="0"*64),
            lambda r:r[0]["snapshot"]["crossBandPairs"]["S>A"].update(
                concordant=0),
            lambda r:r[0]["snapshot"].update(actualPurchase=True),
            lambda r:r[0]["snapshot"].update(
                observedAt="2099-01-01T08:00:00+09:00"),
            lambda r:r[0]["snapshot"].update(prestartSignature="0"*64),
        ]
        for change in changes:
            forged=copy.deepcopy(signed)
            change(forged)
            with self.subTest(change=str(change)), self.assertRaises(WorkoutLockError):
                verify_cross_band_observations(forged,original,SECRET,DAY)
        for forged in (signed+signed,[]):
            with self.assertRaises(WorkoutLockError):
                verify_cross_band_observations(forged,original,SECRET,DAY)
        with self.assertRaises(WorkoutLockError):
            verify_cross_band_observations(signed,original,
                                           "unrelated-secret-unrelated",DAY)

    def test_incomplete_result_cannot_be_retroactively_signed(self):
        original,report=self.model(rows()[:4])
        self.assertEqual(report["studiedRaceCount"],0)
        self.assertEqual(issue_cross_band_observations(
            report,original,SECRET,now=AFTER),[])
        report["races"][0]["crossBandPairs"]={"S>A":{"concordant":2,
              "discordant":2}}
        with self.assertRaises(WorkoutLockError):
            issue_cross_band_observations(report,original,SECRET,now=AFTER)

    def test_provider_tampering_and_changed_roster_rejected(self):
        original,report=self.model()
        changed=copy.deepcopy(report)
        changed["races"][0]["crossBandPairs"]["S>A"]["concordant"]+=1
        with self.assertRaises(WorkoutLockError):
            issue_cross_band_observations(changed,original,SECRET,now=AFTER)
        changed=copy.deepcopy(report)
        changed["observedCrossBandPairs"]["A>B"]["discordant"]+=1
        with self.assertRaises(WorkoutLockError):
            issue_cross_band_observations(changed,original,SECRET,now=AFTER)
        changed=copy.deepcopy(report)
        changed["crossBandResultsSigned"]=True
        with self.assertRaises(WorkoutLockError):
            issue_cross_band_observations(changed,original,SECRET,now=AFTER)

if __name__=="__main__":
    unittest.main()
