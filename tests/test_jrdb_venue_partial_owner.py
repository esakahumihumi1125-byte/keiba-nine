"""Research-only fallback for a temporarily unavailable venue API.

No live JRDB credentials, provider calls, or public source data.
"""
import json
import unittest
from contextlib import ExitStack
from unittest.mock import patch

from test_private_service import SETTINGS, call
from test_jrdb_selected_race_readiness import records, NOW
from private_service import create_app
from jrdb_private import JRDBError


class VenueOnlyFailureTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            **SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
            'JRDB_API_KEY': 'synthetic-app',
            'JRDB_AUTH_KEY': 'synthetic-user',
        })
        self.programme, self.entries, self.training, self.past, self.venue = records()
        self.url = 'date=20261101&track=東京&race=1'

    def request(self, venue_reply):
        with ExitStack() as stack:
            stack.enter_context(patch('private_service.normalize_program_rows',
                                      return_value=self.programme))
            for func, output in (
                ('fetch_race_program', []),
                ('fetch_horse_entries', self.entries),
                ('fetch_training_analysis', self.training),
                ('fetch_recent_runs', self.past),
            ):
                stack.enter_context(patch('private_service.' + func,
                                          return_value=output))
            if isinstance(venue_reply, Exception):
                stack.enter_context(patch('private_service.fetch_venue_conditions',
                                          side_effect=venue_reply))
            else:
                stack.enter_context(patch('private_service.fetch_venue_conditions',
                                          return_value=venue_reply))
            stack.enter_context(patch('private_service._now_in_jst',
                                      return_value=NOW))
            return call(self.app, '/api/jrdb/selected-readiness',
                        QUERY_STRING=self.url)

    def test_transient_venue_failure_is_explicitly_unverified(self):
        for reason in ('JRDB request or response failed',
                       'JRDB returned an unsuccessful response',
                       'JRDB request failed (HTTP 503)'):
            with self.subTest(reason=reason):
                result = self.request(JRDBError(reason))
                self.assertEqual(result['status'], '200 OK')
                payload = json.loads(result['body'])
                self.assertEqual(payload['venueFetchStatus'], 'unavailable')
                self.assertEqual(payload['sourceGoing'], '未確認')
                self.assertEqual(payload['observedEntries'], 2)
                self.assertFalse(payload['predictionReady'])
                self.assertFalse(payload['bettingReady'])
                self.assertFalse(payload['officialJraFinalVerification'])
                self.assertIn('馬場は未確認', payload['venueFetchNotice'])
                self.assertNotIn(reason, repr(payload))
                self.assertNotIn('synthetic-user', repr(payload))

    def test_successful_venue_response_keeps_the_original_going(self):
        result = self.request(self.venue)
        self.assertEqual(result['status'], '200 OK')
        payload = json.loads(result['body'])
        self.assertEqual(payload['venueFetchStatus'], 'ok')
        self.assertIsNone(payload['venueFetchNotice'])
        self.assertEqual(payload['sourceGoing'], '重')
        self.assertFalse(payload['predictionReady'])

    def test_auth_quota_and_mismatch_keep_venue_unknown_only(self):
        cases = (
            ('JRDB request failed (HTTP 401)', 'permission'),
            ('JRDB request failed (HTTP 403)', 'permission'),
            ('JRDB request failed (HTTP 429)', 'rate_limit'),
            ('JRDB request failed (HTTP 404)', 'http'),
            ('JRDB returned a different race request', 'inconsistent'),
            ('JRDB returned a different endpoint', 'inconsistent'),
            ('Unexpected JRDB response format', 'provider_response'),
        )
        for reason, category in cases:
            with self.subTest(reason=reason):
                result = self.request(JRDBError(reason))
                self.assertEqual(result['status'], '200 OK')
                payload = json.loads(result['body'])
                self.assertEqual(payload['venueFetchStatus'], 'unavailable')
                self.assertEqual(payload['venueFailureKind'], category)
                self.assertEqual(payload['sourceGoing'], '未確認')
                self.assertFalse(payload['predictionReady'])
                self.assertFalse(payload['bettingReady'])
                self.assertFalse(payload['officialJraFinalVerification'])
                self.assertNotIn(reason, repr(payload))
                self.assertNotIn('synthetic-app', repr(payload))
                self.assertNotIn('synthetic-user', repr(payload))


if __name__ == '__main__':
    unittest.main()
