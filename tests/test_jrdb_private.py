import io
import json
import os
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from jrdb_private import fetch_race_program, JRDBError, _NoRedirect


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
