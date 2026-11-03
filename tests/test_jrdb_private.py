import io
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from jrdb_private import (fetch_race_program, fetch_horse_entries,
                          fetch_training_analysis, fetch_recent_runs, fetch_venue_conditions, JRDBError, _NoRedirect)


class PrivateClientTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'JRDB_PRIVATE_ENABLED': '1', 'JRDB_API_KEY': 'synthetic-app', 'JRDB_AUTH_KEY': 'synthetic-user'}, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.factory = patch('urllib.request.build_opener')
        self.mock = self.factory.start()
        self.addCleanup(self.factory.stop)
        self.response = self.mock.return_value.open.return_value.__enter__.return_value
        self.response.read.return_value = json.dumps({'success': True, 'result': {'data': [{'racekey': 'synthetic'}]}}).encode()

    def test_disabled_without_opt_in(self):
        del os.environ['JRDB_PRIVATE_ENABLED']
        with self.assertRaises(JRDBError): fetch_race_program('20261026')
        self.mock.assert_not_called()

    def test_actions_blocked(self):
        os.environ['GITHUB_ACTIONS'] = 'true'
        with self.assertRaises(JRDBError): fetch_race_program('20261026')
        self.mock.assert_not_called()

    def test_invalid_dates(self):
        for date in ['20260230', '20261301', '../data', 20261026, '２０２６１０２６']:
            with self.subTest(date=date), self.assertRaises(JRDBError): fetch_race_program(date)
        self.mock.assert_not_called()

    def test_missing_key(self):
        del os.environ['JRDB_AUTH_KEY']
        with self.assertRaises(JRDBError): fetch_race_program('20261026')
        self.mock.assert_not_called()

    def test_request_and_rows(self):
        self.assertEqual(fetch_race_program('20261026'), [{'racekey': 'synthetic'}])
        request = self.mock.return_value.open.call_args.args[0]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(json.loads(request.data), {'racedate': '20261026'})
        self.assertEqual(request.get_header('X-user-key'), 'synthetic-user')
        self.assertTrue(request.full_url.startswith('https://dev.api.bigtime.world/v1/tra?'))

    def test_horse_entry_endpoint_is_private_and_allowlisted(self):
        self.assertEqual(fetch_horse_entries('20261026'), [{'racekey': 'synthetic'}])
        request = self.mock.return_value.open.call_args.args[0]
        self.assertEqual(request.method, 'POST')
        self.assertEqual(json.loads(request.data), {'racedate': '20261026'})
        self.assertIn('/v1/tky?', request.full_url)
        del os.environ['JRDB_PRIVATE_ENABLED']
        with self.assertRaises(JRDBError):
            fetch_horse_entries('20261026')

    def test_training_and_recent_requests_private_only(self):
        for fn, endpoint in [(fetch_training_analysis, 'tcy'),
                             (fetch_recent_runs, 'tze')]:
            with self.subTest(endpoint=endpoint):
                self.assertEqual(fn('20261026'), [{'racekey': 'synthetic'}])
                req = self.mock.return_value.open.call_args.args[0]
                self.assertEqual(req.method, 'POST')
                self.assertIn('/v1/' + endpoint + '?', req.full_url)
                self.assertEqual(json.loads(req.data), {'racedate': '20261026'})
        os.environ['GITHUB_ACTIONS'] = 'true'
        for fn in (fetch_training_analysis, fetch_recent_runs):
            with self.assertRaises(JRDBError):
                fn('20261026')

    def test_venue_going_request_is_owner_only_and_no_credentials_in_response(self):
        self.assertEqual(fetch_venue_conditions('20261026'), [{'racekey': 'synthetic'}])
        req = self.mock.return_value.open.call_args.args[0]
        self.assertEqual(req.method, 'POST')
        self.assertEqual(json.loads(req.data), {'racedate': '20261026'})
        self.assertIn('/v1/tka?', req.full_url)
        self.assertEqual(req.get_header('X-user-key'), 'synthetic-user')
        os.environ['GITHUB_ACTIONS'] = 'true'
        with self.assertRaises(JRDBError):
            fetch_venue_conditions('20261026')

    def test_error_omits_secret_url_and_body(self):
        self.mock.return_value.open.side_effect = urllib.error.HTTPError('https://example/?secret', 403, 'private-data', {}, io.BytesIO(b'private-data'))
        with self.assertRaises(JRDBError) as result: fetch_race_program('20261026')
        self.assertEqual(str(result.exception), 'JRDB request failed (HTTP 403)')
        self.assertTrue(result.exception.__suppress_context__)

    def test_bad_responses(self):
        for value in [b'private text', b'[]', b'{"success":false}', b'{"result":{"data":[null]}}', b'x' * 10_000_001]:
            self.response.read.return_value = value
            with self.assertRaises(JRDBError): fetch_race_program('20261026')

    def test_no_redirect(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com'))


if __name__ == '__main__': unittest.main()
