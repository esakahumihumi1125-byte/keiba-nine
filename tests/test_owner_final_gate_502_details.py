"""Closed, source-safe diagnosis for the 15 Nov final-prestart 502.

The private endpoint was observed returning 502 after successfully reading
four JRDB feeds. These tests do NOT claim to reproduce that unknown source
error: they ensure the next failure tells us the failing invariant, without
returning source data, race IDs, HMACs, keys or timestamps.
"""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from jrdb_coverage import CoverageError
from owner_last_prestart_gate import (
    expire_undelivered_drafts, final_gate_failure_detail,
)
from test_owner_final_prestart_alignment import fixture, MORNING
from test_owner_jrdb_docs_shaped_36r_acceptance import (
    provider_shaped_day, run_private_pipeline,
)


class FinalGateDiagnosticsTests(unittest.TestCase):
    def test_each_known_source_contract_fail_maps_to_bounded_code(self):
        mutations = (
            ('ticket_integrity', lambda r: r['races'][0]['tickets'].append(
                [1, 2, 3])),
            ('race_identity', lambda r: r['races'][1].__setitem__('race', 1)),
            ('receipt_set_mismatch', lambda r: r['researchReceipts'][0][
                'snapshot'].__setitem__('track', '京都')),
            ('receipt_count_mismatch', lambda r: r.__setitem__(
                'researchReceiptCount', 1)),
            ('receipt_draft_mismatch', lambda r: r['researchReceipts'][0][
                'snapshot'].__setitem__('scheduledOffAt',
                                       '2099-01-01T10:01:00+09:00')),
        )
        for code, edit in mutations:
            with self.subTest(expected=code):
                report = fixture()
                edit(report)
                original = copy.deepcopy(report)
                with self.assertRaises(CoverageError) as ctx:
                    expire_undelivered_drafts(report, MORNING)
                self.assertEqual(final_gate_failure_detail(ctx.exception),
                                 code)
                self.assertEqual(report, original)
        self.assertEqual(final_gate_failure_detail(
            CoverageError('untrusted paid API details XXXXX')), 'other')
        self.assertEqual(final_gate_failure_detail(ValueError('secret')), 'other')

    def test_private_endpoint_returns_known_code_no_raw_source_details(self):
        # Patch only the final gate: all genuine local 36R normalizers,
        # JRDB-shaped roster joins, provisional draft and HMAC signatures
        # must still complete. Every paid HTTP adapter is synthetic.
        with patch('private_service.expire_undelivered_drafts',
                   side_effect=CoverageError(
                       'Final prestart receipt does not match draft')):
            response, reads = run_private_pipeline(provider_shaped_day())
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        self.assertEqual(response['status'], '502 Bad Gateway')
        data = json.loads(response['body'])
        self.assertEqual(data['failureStage'], 'final_prestart_gate')
        self.assertEqual(data['failureKind'], 'source_validation')
        self.assertEqual(data['failureDetail'], 'receipt_draft_mismatch')
        for private in ('horse_id', 'racekey', '2099-01-01T09:00',
                        'TEST-ONLY', 'signature', 'trifectaTickets'):
            self.assertNotIn(private, response['body'].decode())

    def test_unknown_failure_fails_closed_without_echoing_exception(self):
        with patch('private_service.expire_undelivered_drafts',
                   side_effect=CoverageError(
                       'SECRET_TEST_EXCEPTION_JRDB_PRIVATE')):
            response, reads = run_private_pipeline(provider_shaped_day())
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        self.assertEqual(response['status'], '502 Bad Gateway')
        data = json.loads(response['body'])
        self.assertEqual(data['failureStage'], 'final_prestart_gate')
        self.assertEqual(data['failureKind'], 'source_validation')
        self.assertEqual(data['failureDetail'], 'other')
        self.assertNotIn('SECRET_TEST_EXCEPTION', response['body'].decode())


if __name__ == '__main__':
    unittest.main()
