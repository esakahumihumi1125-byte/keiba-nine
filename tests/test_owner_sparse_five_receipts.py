"""Synthetic HMAC-only sparse reference research archive tests (no provider)."""
import copy
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_owner_research6_five_drafts import materials, calculate, DAY, JST
from test_owner_sparse_five_preview import SPARSE, add_original_subtotals
from owner_sparse_five_preview import preview_sparse_five_holds
from owner_sparse_five_receipts import (
    issue_sparse_reference_receipts, verify_sparse_reference_receipts,
    SparseReferenceReceiptError,
)

NOW = datetime(2099, 1, 1, 9, 0, tzinfo=JST)
AFTER = datetime(2099, 1, 1, 12, 0, tzinfo=JST)
SECRET = "private-owner-hmac-secret-only-for-test-xxxxxxxxxxxx"


def trusted():
    programme, research = materials(SPARSE)
    add_original_subtotals(research)
    held = calculate(programme, research, now=NOW)
    source = preview_sparse_five_holds(programme, research, held, DAY, now=NOW)
    report = {
        "date": DAY, "predictionReady": False,
        "newWeightFiveResearch": research,
        "research6FiveDrafts": held,
        "sparseFiveRecentReferences": source,
    }
    return programme, report


class SparseReferenceSigningTests(unittest.TestCase):
    def test_exact_reference_record_is_hmac_signed_and_immutable(self):
        p, source = trusted()
        original = copy.deepcopy((p, source))
        cap = issue_sparse_reference_receipts(source, p, SECRET, DAY, now=NOW)
        self.assertEqual((p, source), original)
        self.assertEqual(cap["receiptCount"], 1)
        self.assertEqual(cap["expiredBeforeSigning"], 0)
        entry = cap["receipts"][0]
        snap = entry["snapshot"]
        self.assertEqual((snap["first"], snap["second"], snap["third"]),
                         ([1, 2], [1, 2, 3, 4, 5], list(range(1, 8))))
        self.assertEqual(snap["points"], 40)
        self.assertEqual(snap["amountYen"], 4000)
        self.assertEqual(len(snap["tickets"]), 40)
        self.assertEqual(snap["missingRecentCount"], 7)
        self.assertFalse(snap["predictionReady"])
        self.assertFalse(snap["bettingReady"])
        self.assertFalse(snap["actualPurchase"])
        self.assertFalse(snap["scoreCalibrated"])
        self.assertFalse(cap["changesExistingRoi"])
        self.assertEqual(verify_sparse_reference_receipts(
            cap["receipts"], SECRET, DAY), [snap])
        self.assertEqual(source["sparseFiveRecentReferences"]["races"][0]
                         ["receiptIssued"], False)

    def test_delayed_server_generation_after_off_cannot_backfill(self):
        p, source = trusted()
        result = issue_sparse_reference_receipts(
            source, p, SECRET, DAY, now=AFTER)
        self.assertEqual(result["receiptCount"], 0)
        self.assertEqual(result["expiredBeforeSigning"], 1)
        self.assertEqual(result["receipts"], [])

    def test_hmac_and_domains_block_modification_and_duplicate_claims(self):
        p, source = trusted()
        signed = issue_sparse_reference_receipts(
            source, p, SECRET, DAY, now=NOW)["receipts"]
        for patch in (
            lambda x: x["snapshot"].update(points=39),
            lambda x: x["snapshot"].update(missingRecentCount=1),
            lambda x: x["snapshot"].update(actualPurchase=True),
            lambda x: x["snapshot"].update(
                capturedAt="2099-01-01T12:30:00+09:00"),
            lambda x: x["snapshot"]["first"].reverse(),
            lambda x: x.update(signature="a" * 64),
        ):
            forged = copy.deepcopy(signed)
            patch(forged[0])
            with self.subTest(patch=str(patch)), self.assertRaises(
                    SparseReferenceReceiptError):
                verify_sparse_reference_receipts(forged, SECRET, DAY)
        with self.assertRaises(SparseReferenceReceiptError):
            verify_sparse_reference_receipts(signed + signed, SECRET, DAY)
        with self.assertRaises(SparseReferenceReceiptError):
            verify_sparse_reference_receipts(signed, SECRET, "20990102")
        with self.assertRaises(SparseReferenceReceiptError):
            verify_sparse_reference_receipts(
                signed, "unrelated-secret-this-is-long-enough-xxxxxxxxxx", DAY)

    def test_forged_server_preview_must_not_be_signed(self):
        p, source = trusted()
        for patch in (
            lambda x: x["sparseFiveRecentReferences"]["races"][0]
             ["first"].reverse(),
            lambda x: x["sparseFiveRecentReferences"]["races"][0]
             .update(points=39),
            lambda x: x["newWeightFiveResearch"]["races"][0]
             ["horses"][0]["bands"].update(pace="C"),
        ):
            attempt = copy.deepcopy(source)
            patch(attempt)
            with self.subTest(patch=str(patch)), self.assertRaises(
                    SparseReferenceReceiptError):
                issue_sparse_reference_receipts(
                    attempt, p, SECRET, DAY, now=NOW)
        original = copy.deepcopy(source)
        original["date"] = "20990102"
        with self.assertRaises(SparseReferenceReceiptError):
            issue_sparse_reference_receipts(original, p, SECRET, DAY, now=NOW)

    def test_cannot_sign_when_receipts_are_unavailable_or_secret_is_short(self):
        p, source = trusted()
        del source["newWeightFiveResearch"]
        with self.assertRaises(SparseReferenceReceiptError):
            issue_sparse_reference_receipts(source, p, SECRET, DAY, now=NOW)
        p, source = trusted()
        with self.assertRaises(SparseReferenceReceiptError):
            issue_sparse_reference_receipts(source, p, "short", DAY, now=NOW)


if __name__ == "__main__":
    unittest.main()
