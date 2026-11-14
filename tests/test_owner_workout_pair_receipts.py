"""Synthetic-only, no-provider-call checks for signed postrace pair observations."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_workout_pair_receipts import (
    issue_workout_pair_observations, verify_workout_pair_observations,
    WorkoutLockError, VERSION,
)
from owner_workout_order_provider_pairs import compare_workout_order_with_provider
from test_owner_workout_order_provider_pairs import receipts, rows, DAY, AFTER, BEFORE
from test_owner_workout_order_receipts import SECRET


def source():
    originals = receipts()
    report = compare_workout_order_with_provider(
        originals, rows(), DAY, now=AFTER)
    return originals, report


class SignedPairReceiptTests(unittest.TestCase):
    def test_sign_completed_provisional_result_with_independent_domain(self):
        before, report = source()
        saved = copy.deepcopy((before, report))
        result = issue_workout_pair_observations(
            report, before, SECRET, now=AFTER)
        self.assertEqual((before, report), saved)
        self.assertEqual(len(result), 1)
        p = result[0]["snapshot"]
        self.assertEqual(p["version"], VERSION)
        self.assertEqual(p["prestartSignature"].__len__(), 64)
        self.assertEqual(p["pairCounts"]["S"]["discordant"], 1)
        self.assertEqual(p["pairCounts"]["A"]["equalIndexExcluded"], 1)
        self.assertNotEqual(p["prestartSignature"],result[0]["signature"])
        self.assertEqual(verify_workout_pair_observations(
            result, before, SECRET, DAY), [p])
        for value in ("horse_number", "racekey", "order_of_finish",
                      "oikirisisu", "siagarisisu", "2328aaa", "PAID-NAME"):
            self.assertNotIn(value, repr(result))
        self.assertFalse(p["officialJraVerified"])
        self.assertFalse(p["modelCalibrated"])
        self.assertFalse(p["actualPurchase"])

    def test_no_premature_or_incomplete_receipts(self):
        before, report=source()
        with self.assertRaises(WorkoutLockError):
            issue_workout_pair_observations(report,before,SECRET,now=BEFORE)
        pending=compare_workout_order_with_provider(before,[],DAY,
                            now=BEFORE,source_read_count=0)
        self.assertEqual(issue_workout_pair_observations(
            pending,before,SECRET,now=BEFORE),[])
        partial=compare_workout_order_with_provider(before,rows()[:3],DAY,now=AFTER)
        self.assertEqual(issue_workout_pair_observations(
            partial,before,SECRET,now=AFTER),[])

    def test_observation_is_immutable_even_if_provider_returns_later_revision(self):
        before, report=source()
        first=issue_workout_pair_observations(
            report,before,SECRET,now=AFTER)
        modified=rows()
        modified[0]["order_of_finish"]="01"
        modified[1]["order_of_finish"]="02"
        altered=compare_workout_order_with_provider(
            before,modified,DAY,now=AFTER)
        second=issue_workout_pair_observations(
            altered,before,SECRET,now=AFTER)
        self.assertNotEqual(first,second)
        # Data is not edited or merged server-side. First-write ledger tests
        # prevent later provisional revisions from replacing initial receipt.
        self.assertEqual(first[0]["snapshot"]["pairCounts"]["S"]["discordant"],1)
        self.assertEqual(second[0]["snapshot"]["pairCounts"]["S"]["discordant"],0)

    def test_reject_tampering_wrong_prestart_and_aggregate_conflicts(self):
        frozen, report=source()
        good=issue_workout_pair_observations(report,frozen,SECRET,now=AFTER)
        for edit in ("band","paired","time","signature","source","unverified"):
            current=copy.deepcopy(good)
            snap=current[0]["snapshot"]
            if edit=="band": snap["pairCounts"]["S"]["concordant"]=5
            elif edit=="paired": snap["prestartSignature"]="f"*64
            elif edit=="time": snap["observedAt"]="2099-01-01T08:59:00+09:00"
            elif edit=="source": snap["sourceKind"]="JRA official"
            elif edit=="unverified": snap["officialJraVerified"]=True
            else: current[0]["signature"]="a"*64
            with self.subTest(edit=edit),self.assertRaises(WorkoutLockError):
                verify_workout_pair_observations(current,frozen,SECRET,DAY)
        wrong=copy.deepcopy(report)
        wrong["observedPairsByTrainingBand"]["S"]["discordant"]=0
        with self.assertRaises(WorkoutLockError):
            issue_workout_pair_observations(wrong,frozen,SECRET,now=AFTER)
        with self.assertRaises(WorkoutLockError):
            verify_workout_pair_observations(good, frozen, "WRONG-TEST-PASSWORD-012345",DAY)

    def test_duplicate_or_partial_review_is_not_silently_signed(self):
        original, review=source()
        for rows in (review["races"]+review["races"], [], [{"bogus":1}]):
            bad=copy.deepcopy(review)
            bad["races"]=rows
            with self.subTest(count=len(rows)),self.assertRaises(WorkoutLockError):
                issue_workout_pair_observations(bad,original,SECRET,now=AFTER)
        good=issue_workout_pair_observations(review,original,SECRET,now=AFTER)
        with self.assertRaises(WorkoutLockError):
            verify_workout_pair_observations(good*2, original,SECRET,DAY)


if __name__=="__main__":
    unittest.main()
