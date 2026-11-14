"""No-source-call signed prestart workout index ordering research tests."""
import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_workout_order_receipts import (
    VERSION, WorkoutLockError, issue_workout_locks, verify_workout_locks
)
from owner_workout_index_order import workout_index_order
from test_owner_workout_index_order import data, BEFORE, AFTER, DAY

SECRET = "synthetic-study-signer-not-a-real-password"


def source():
    p, e, t, report = data()
    report["workoutIndexOrder"] = workout_index_order(p, e, t, report, DAY, now=BEFORE)
    return report


class WorkoutOrderLockTests(unittest.TestCase):
    def test_single_hmac_preserves_equal_s_and_distinct_s_before_off(self):
        draft = source()
        original = copy.deepcopy(draft)
        receipts = issue_workout_locks(draft, SECRET, BEFORE)
        self.assertEqual(original, draft)
        self.assertEqual(len(receipts), 1)
        item = receipts[0]
        self.assertEqual(item["snapshot"]["version"], VERSION)
        self.assertEqual(item["snapshot"]["raceRunnerCount"], 5)
        self.assertEqual(item["snapshot"]["horses"][:2], [
            {"number": 1, "trainingBand": "S", "withinBandRank": 1},
            {"number": 2, "trainingBand": "S", "withinBandRank": 2},
        ])
        originals = verify_workout_locks(receipts, SECRET, DAY)
        self.assertEqual(originals, [item["snapshot"]])
        for secret in ("racekey", "horse_id", "oikirisisu", "siagarisisu",
                       "PAID-NAME", "78.0", "PRIVATE"):
            self.assertNotIn(secret, repr(receipts))
        self.assertFalse(item["snapshot"]["officialJraVerified"])
        self.assertFalse(item["snapshot"]["modelCalibrated"])
        self.assertFalse(item["snapshot"]["actualPurchase"])

    def test_after_off_signature_is_not_issued(self):
        result = issue_workout_locks(source(), SECRET, AFTER)
        self.assertEqual(result, [])

    def test_client_modified_rank_or_offtime_fails_verification(self):
        receipt = issue_workout_locks(source(), SECRET, BEFORE)
        for change in ("rank", "number", "off", "grade", "signature"):
            mutated = copy.deepcopy(receipt)
            row = mutated[0]
            if change == "rank":
                row["snapshot"]["horses"][0]["withinBandRank"] = 2
            elif change == "number":
                row["snapshot"]["horses"][0]["number"] = 9
            elif change == "off":
                row["snapshot"]["scheduledOffAt"] = "2099-01-01T15:00:00+00:00"
            elif change == "grade":
                row["snapshot"]["horses"][0]["trainingBand"] = "B"
            else:
                row["signature"] = "0"*64
            with self.subTest(change=change), self.assertRaises(WorkoutLockError):
                verify_workout_locks(mutated, SECRET, DAY)

    def test_existing_or_wrong_date_receipts_do_not_verify(self):
        receipts=issue_workout_locks(source(), SECRET, BEFORE)
        for rows in ([], receipts*2):
            with self.assertRaises(WorkoutLockError):
                verify_workout_locks(rows, SECRET, DAY)
        with self.assertRaises(WorkoutLockError):
            verify_workout_locks(receipts, SECRET, "20990102")
        with self.assertRaises(WorkoutLockError):
            verify_workout_locks(receipts, "different-secret-different-secret", DAY)

    def test_invalid_draft_or_unrelated_source_stops_without_leaking(self):
        cases = []
        changed=source();changed["races"][0]["runners"][0]["training"]="A";cases.append(changed)
        changed=source();changed["races"][0]["status"]="invalid";cases.append(changed)
        changed=source();changed["races"][0]["reason"]="provider_withdrawal";cases.append(changed)
        changed=source();changed["workoutIndexOrder"]["races"].append(
            copy.deepcopy(changed["workoutIndexOrder"]["races"][0]));cases.append(changed)
        for obj in cases:
            with self.subTest(case=repr(obj)[:40]), self.assertRaises(WorkoutLockError):
                issue_workout_locks(obj,SECRET,BEFORE)

    def test_rank_competition_tie_1_1_3_accepts_not_1_1_2(self):
        receipt=issue_workout_locks(source(), SECRET, BEFORE)
        snap=copy.deepcopy(receipt[0]["snapshot"])
        # Change 2 to rank 1, and first A pair to their normal tie.
        snap["horses"][1]["withinBandRank"]=1
        from owner_workout_order_receipts import _validate
        self.assertEqual(_validate(snap),(DAY,"東京",1))
        snap["horses"][2]["withinBandRank"]=2
        with self.assertRaises(WorkoutLockError):
            _validate(snap)


if __name__=="__main__":
    unittest.main()
