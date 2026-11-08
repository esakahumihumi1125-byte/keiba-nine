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
                          fetch_training_analysis, fetch_recent_runs, fetch_venue_conditions,
                          fetch_prestart_body,fetch_finished_race_results,
                          fetch_historical_race_program, fetch_historical_venue_conditions,
                          JRDBError, _NoRedirect)


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

    def test_prestart_body_endpoint_is_not_public_or_automatic(self):
        self.assertEqual(fetch_prestart_body('20261026'),
                         [{'racekey': 'synthetic'}])
        req = self.mock.return_value.open.call_args.args[0]
        self.assertEqual(req.method, 'POST')
        self.assertEqual(json.loads(req.data), {'racedate': '20261026'})
        self.assertIn('/v1/tpd?', req.full_url)
        self.assertEqual(req.get_header('X-user-key'), 'synthetic-user')
        self.assertNotIn('start_racedate', req.data.decode())
        os.environ['GITHUB_ACTIONS'] = 'true'
        with self.assertRaises(JRDBError):
            fetch_prestart_body('20261026')
        del os.environ['GITHUB_ACTIONS']
        del os.environ['JRDB_PRIVATE_ENABLED']
        with self.assertRaises(JRDBError):
            fetch_prestart_body('20261026')

    def test_provider_postrace_read_is_single_private_day_and_not_jra(self):
        self.assertEqual(fetch_finished_race_results('20261026'),
                         [{'racekey':'synthetic'}])
        req=self.mock.return_value.open.call_args.args[0]
        self.assertIn('/v1/tse?',req.full_url)
        self.assertEqual(json.loads(req.data),{'racedate':'20261026'})
        os.environ['GITHUB_ACTIONS']='true'
        with self.assertRaises(JRDBError):
            fetch_finished_race_results('20261026')
        del os.environ['GITHUB_ACTIONS']
        del os.environ['JRDB_PRIVATE_ENABLED']
        with self.assertRaises(JRDBError):
            fetch_finished_race_results('20261026')
        with self.assertRaises(JRDBError):
            fetch_finished_race_results('20261099')

    def test_single_historical_racekey_is_only_allowed_dra_query(self):
        rows = fetch_historical_race_program('05264b01')
        self.assertEqual(rows, [{'racekey': 'synthetic'}])
        req = self.mock.return_value.open.call_args.args[0]
        self.assertEqual(req.method, 'POST')
        self.assertIn('/v1/dra?', req.full_url)
        self.assertEqual(json.loads(req.data), {'racekey': '05264b01'})
        self.assertNotIn('start_racedate', req.data.decode())
        self.assertNotIn('end_racedate', req.data.decode())

    def test_historical_lookup_invalid_key_never_contacts_provider(self):
        for bad in ('', '05264B01', 'garbage', '05264a01;DROP',
                    '05264b0Z', '../api', '０５２６４ｂ０１', 123,
                    None, {'start_racedate': '20000101'}):
            with self.subTest(bad=bad):
                with self.assertRaises(JRDBError):
                    fetch_historical_race_program(bad)
        self.mock.assert_not_called()

    def test_historical_lookup_is_disabled_in_actions(self):
        os.environ['GITHUB_ACTIONS'] = 'true'
        with self.assertRaises(JRDBError):
            fetch_historical_race_program('05264b01')
        self.mock.assert_not_called()

    def test_historical_lookup_requires_explicit_private_activation(self):
        del os.environ['JRDB_PRIVATE_ENABLED']
        with self.assertRaises(JRDBError):
            fetch_historical_race_program('05264b01')
        self.mock.assert_not_called()

    def test_single_historical_going_query_has_no_date_range(self):
        self.assertEqual(fetch_historical_venue_conditions('05264a01'),
                         [{'racekey': 'synthetic'}])
        req = self.mock.return_value.open.call_args.args[0]
        self.assertIn('/v1/dka?', req.full_url)
        self.assertEqual(json.loads(req.data), {'racekey': '05264a01'})
        self.assertNotIn('start_racedate', req.data.decode())
        self.assertNotIn('end_racedate', req.data.decode())

    def test_historical_going_rejects_invalid_keys_before_network(self):
        for key in ('05264A01', '000', '05264a01&date=20261101',
                    {'start_racedate': '20260101'}, 123, None):
            with self.subTest(key=key), self.assertRaises(JRDBError):
                fetch_historical_venue_conditions(key)
        self.mock.assert_not_called()

    def test_historical_going_is_disabled_for_actions_and_public_mode(self):
        os.environ['GITHUB_ACTIONS'] = 'true'
        with self.assertRaises(JRDBError):
            fetch_historical_venue_conditions('05264a01')
        del os.environ['GITHUB_ACTIONS']
        del os.environ['JRDB_PRIVATE_ENABLED']
        with self.assertRaises(JRDBError):
            fetch_historical_venue_conditions('05264a01')
        self.mock.assert_not_called()

    def test_error_omits_secret_url_and_body(self):
        self.mock.return_value.open.side_effect = urllib.error.HTTPError('https://example/?secret', 403, 'private-data', {}, io.BytesIO(b'private-data'))
        with self.assertRaises(JRDBError) as result: fetch_race_program('20261026')
        self.assertEqual(str(result.exception), 'JRDB request failed (HTTP 403)')
        self.assertTrue(result.exception.__suppress_context__)

    def test_bad_responses(self):
        for value in [b'private text', b'[]', b'{"success":false}', b'{"result":{"data":[null]}}', b'x' * 10_000_001]:
            self.response.read.return_value = value
            with self.assertRaises(JRDBError): fetch_race_program('20261026')

    def test_published_beta_response_schema_and_echo(self):
        self.response.read.return_value = json.dumps({
            'request': {'racedate': '20261026'},
            'result': {'status': 'success', 'data': [{'racekey': '05260101'}]}
        }).encode()
        self.assertEqual(fetch_race_program('20261026'), [{'racekey': '05260101'}])

    def test_endpoint_beta_200_schema_nested_request_echo(self):
        # /docs/endpoints/today/tra publishes this variant, even though the
        # generic response page documents status="success".
        payload = {
            'request': {'parameters': {'racedate': '20261026'}},
            'result': {'status': 200, 'endpoint_uri': '/v1/tra',
                       'result_count': 1,
                       'data': [{'racekey': '05264b01'}]},
        }
        self.response.read.return_value = json.dumps(payload).encode()
        self.assertEqual(fetch_race_program('20261026'), [{'racekey': '05264b01'}])
        payload['request']['parameters']['racedate'] = '20261027'
        self.response.read.return_value = json.dumps(payload).encode()
        with self.assertRaisesRegex(JRDBError, 'different race request'):
            fetch_race_program('20261026')

    def test_published_beta_response_metadata_never_silently_mismatched(self):
        good = {'request': {'parameters': {'racedate': '20261026'}},
                'result': {'status': 200, 'endpoint_uri': '/v1/tra',
                           'result_count': 1, 'data': [{'racekey': 'test'}]}}
        bad = [
            {**good, 'result': {**good['result'], 'status': 201}},
            {**good, 'result': {**good['result'], 'status': '200'}},
            {**good, 'result': {**good['result'], 'status': True}},
            {**good, 'result': {**good['result'], 'endpoint_uri': '/v1/tky'}},
            {**good, 'result': {**good['result'], 'result_count': 2}},
            {**good, 'result': {**good['result'], 'result_count': '1'}},
            {**good, 'request': {'parameters': {'racekey': '05264b01'}}},
            {**good, 'request': {'parameters': 'garbled'}},
            {**good, 'error': {'code': 'LIMIT_EXCEEDED'}},
            {'result': {'data': [{'racekey': 'test'}]}},
        ]
        for payload in bad:
            with self.subTest(payload=str(payload)[:75]):
                self.response.read.return_value = json.dumps(payload).encode()
                with self.assertRaises(JRDBError):
                    fetch_race_program('20261026')

    def test_documented_api_host_may_be_selected_without_leaking_keys(self):
        os.environ['JRDB_API_BASE_URL'] = 'https://api.bigtime.world/v1'
        self.assertEqual(fetch_race_program('20261026'), [{'racekey': 'synthetic'}])
        request = self.mock.return_value.open.call_args.args[0]
        self.assertTrue(request.full_url.startswith('https://api.bigtime.world/v1/tra?'))
        self.assertEqual(request.get_header('X-user-key'), 'synthetic-user')

    def test_unapproved_base_is_blocked_before_any_network(self):
        for base in ['http://api.bigtime.world/v1', 'https://evil.example/v1',
                     'https://api.bigtime.world/v1/', 'https://api.bigtime.world/v1@evil.example',
                     'https://dev.api.bigtime.world/v1?redirect=https://evil.example',
                     'https://127.0.0.1/v1']:
            with self.subTest(base=base):
                os.environ['JRDB_API_BASE_URL'] = base
                with self.assertRaisesRegex(JRDBError, 'Unapproved'):
                    fetch_race_program('20261026')
        self.mock.assert_not_called()

    def test_api_key_control_characters_never_hit_provider(self):
        for key in ['abc' + chr(10) + 'value', 'abc value', 'abc' + chr(13) + 'value']:
            with self.subTest(key=key):
                os.environ['JRDB_API_KEY'] = key
                with self.assertRaisesRegex(JRDBError, 'Invalid credential format'):
                    fetch_race_program('20261026')
        self.mock.assert_not_called()

    def test_provider_errors_and_mismatched_echo_fail_closed(self):
        bad = [
            {'result': {'status': 'error', 'data': [{'racekey': 'synthetic'}]}},
            {'success': False, 'result': {'status': 'success', 'data': []}},
            {'success': True, 'result': {'status': 'error', 'data': []}},
            {'success': 'yes', 'result': {'data': []}},
            {'result': {'status': 'unknown', 'data': []}},
            {'request': {'racedate': '20261027'}, 'result': {'status': 'success', 'data': []}},
            {'request': ['20261026'], 'result': {'status': 'success', 'data': []}},
            {'result': {'status': 'success', 'data': [None]}},
            {'result': {'status': 'success', 'data': [{}] * 50001}},
        ]
        for payload in bad:
            self.response.read.return_value = json.dumps(payload).encode()
            with self.subTest(case=str(payload)[:60]), self.assertRaises(JRDBError):
                fetch_race_program('20261026')

    def test_no_redirect(self):
        self.assertIsNone(_NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com'))


if __name__ == '__main__': unittest.main()
