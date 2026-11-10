"""Offline JRDB /dse updated_at diagnostics never certify first publication."""
import copy
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_dse_update_diagnostic import audit_dse_update_fields, VERSION

CAPTURE = datetime(2026, 11, 13, 20, 0,
                   tzinfo=timezone(timedelta(hours=9)))


class DseUpdatedAtTests(unittest.TestCase):
    def test_jrdb_date_only_example_never_proves_result_publication(self):
        rows = [{"horse_id": "PRIVATE_ID", "updated_at": "20251129"} for _ in range(7)]
        old = copy.deepcopy(rows)
        out = audit_dse_update_fields([rows], captured_at=CAPTURE)
        self.assertEqual(rows, old)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(out["observedResponseCount"], 1)
        self.assertEqual(out["observedResultRowCount"], 7)
        self.assertEqual(out["dateOnlyCount"], 7)
        self.assertEqual(out["timestampBeforeCaptureCount"], 0)
        self.assertFalse(out["initialPublicationTimeVerified"])
        self.assertFalse(out["historicalResultPublicationTimesVerified"])
        self.assertFalse(out["bettingReady"])
        self.assertEqual(out["extraProviderCalls"], 0)
        self.assertNotIn("PRIVATE_ID", repr(out))
        self.assertNotIn("20251129", repr(out))

    def test_timezone_offset_compared_as_instant_without_treating_as_release(self):
        # 20:00 JST == 11:00 UTC; equality must be held.
        rows = [
            {"updated_at": "2026-11-13T10:59:59Z"},
            {"updated_at": "2026-11-13T11:00:00Z"},
            {"updated_at": "2026-11-13T21:00:00+09:00"},
            {"updated_at": "2026-11-13T10:00:00"},
            {"updated_at": None},
        ]
        out = audit_dse_update_fields([rows], captured_at=CAPTURE)
        self.assertEqual(out["timestampBeforeCaptureCount"], 1)
        self.assertEqual(out["timestampAtOrAfterCaptureCount"], 2)
        self.assertEqual(out["ambiguousUpdateCount"], 1)
        self.assertEqual(out["missingUpdateCount"], 1)
        self.assertFalse(out["sourceTimestampAuthenticityVerified"])
        self.assertFalse(out["initialPublicationTimeVerified"])

    def test_ambiguous_and_dateonly_formats_stay_unknown(self):
        rows = [
            {"updated_at": "2025-11-29"},
            {"updated_at": "20251129"},
            {"updated_at": "2025-11-29T10:00:00"},
            {"updated_at": "invalid"},
            {"updated_at": ["2025-11-29"]},
            {"updated_at": False},
            {},
        ]
        out = audit_dse_update_fields([rows], captured_at=CAPTURE)
        self.assertEqual(out["dateOnlyCount"], 2)
        self.assertEqual(out["ambiguousUpdateCount"], 4)
        self.assertEqual(out["missingUpdateCount"], 1)
        self.assertEqual(out["observedResultRowCount"], 7)

    def test_missing_and_invalid_provider_batch_without_leaking_data(self):
        out = audit_dse_update_fields(
            [[{"updated_at": "2025-01-01T10:00:00+09:00"}] * 2, None, []],
            captured_at=CAPTURE)
        self.assertEqual(out["invalidResponseCount"], 3)
        self.assertEqual(out["observedResultRowCount"], 0)
        for field in ("changesExistingTickets", "changesExistingReceipts",
                      "changesExistingRoi", "officialJraVerified"):
            self.assertFalse(out[field])
        with self.assertRaises(ValueError):
            audit_dse_update_fields([[]] * 4, captured_at=CAPTURE)
        with self.assertRaises(ValueError):
            audit_dse_update_fields([], captured_at=datetime(2026, 11, 13))

    def test_three_bounded_batches_and_no_raw_timestamps_in_output(self):
        batch = [{"horse_id": "PRIVATE_ID", "updated_at": "2025-11-29T10:00:00Z"}
                 for _ in range(18)]
        out = audit_dse_update_fields([batch] * 3, captured_at=CAPTURE)
        self.assertEqual(out["observedResponseCount"], 3)
        self.assertEqual(out["observedResultRowCount"], 54)
        self.assertEqual(out["timestampBeforeCaptureCount"], 54)
        self.assertFalse(out["initialPublicationTimeVerified"])
        self.assertEqual(out["extraProviderCalls"], 0)
        self.assertNotIn("PRIVATE_ID", repr(out))
        self.assertNotIn("2025-11-29T", repr(out))


if __name__ == "__main__":
    unittest.main()
