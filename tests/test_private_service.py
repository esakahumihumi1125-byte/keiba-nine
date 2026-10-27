import base64
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from private_service import create_app, MAX_BODY
from jrdb_private import JRDBError
from test_research_pipeline import sample

# Synthetic fixture, not a deployed password.
SETTINGS = {'KEIBA_OWNER_PASSWORD': 'synthetic-test-fixture-1234567890-ABCDE'}
AUTH = 'Basic ' + base64.b64encode(('owner:' + SETTINGS['KEIBA_OWNER_PASSWORD']).encode()).decode()


def call(app, path='/', method='GET', auth=AUTH, data=None, **changes):
    raw = json.dumps(data).encode() if data is not None else b''
    env = {'wsgi.url_scheme': 'https', 'REMOTE_ADDR': '127.0.0.1', 'PATH_INFO': path,
           'REQUEST_METHOD': method, 'HTTP_AUTHORIZATION': auth, 'HTTP_X_KEIBA_REQUEST': 'private',
           'CONTENT_LENGTH': str(len(raw)), 'CONTENT_TYPE': 'application/json', 'wsgi.input': io.BytesIO(raw)}
    env.update(changes)
    result = {}
    def start(status, headers):
        result.update(status=status, headers=dict(headers))
    result['body'] = b''.join(app(env, start))
    return result


class PrivateServiceTests(unittest.TestCase):
    def setUp(self): self.app = create_app(SETTINGS)

    def test_no_or_weak_password_fails_closed(self):
        for config in [{}, {'KEIBA_OWNER_PASSWORD': 'short'}, {'KEIBA_OWNER_PASSWORD': 'x' * 40}]:
            with self.assertRaises(ValueError): create_app(config)

    def test_all_pages_require_owner(self):
        with patch('private_service.fetch_race_program') as fetch:
            for path in ['/', '/app.js', '/app.css', '/api/status', '/api/jrdb/program', '/api/research']:
                for auth in ['', 'Basic invalid', 'Basic ' + base64.b64encode(b'other:password').decode()]:
                    self.assertTrue(call(self.app, path=path, auth=auth)['status'].startswith('401'))
            fetch.assert_not_called()

    def test_http_and_spoofed_forwarded_header_rejected(self):
        result = call(self.app, **{'wsgi.url_scheme': 'http', 'HTTP_X_FORWARDED_PROTO': 'https'})
        self.assertTrue(result['status'].startswith('426'))
        self.assertNotIn('WWW-Authenticate', result['headers'])

    def test_local_http_requires_explicit_opt_in(self):
        local = create_app({**SETTINGS, 'KEIBA_ALLOW_LOCAL_HTTP': '1'})
        self.assertTrue(call(local, **{'wsgi.url_scheme': 'http'})['status'].startswith('200'))
        self.assertTrue(call(local, **{'wsgi.url_scheme': 'http', 'REMOTE_ADDR': '203.0.113.1'})['status'].startswith('426'))

    def test_status_has_no_credentials(self):
        result = call(self.app, '/api/status')
        self.assertEqual(json.loads(result['body']), {'jrdbConfigured': False, 'livePredictionEnabled': False})
        self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), result['body'])
        self.assertIn('no-store', result['headers']['Cache-Control'])
        self.assertNotIn('Access-Control-Allow-Origin', result['headers'])

    def test_no_directory_or_repo_file_serving(self):
        for path in ['/../.env', '/scripts/jrdb_private.py', '/keiba-nine-auto-feed.json']:
            self.assertTrue(call(self.app, path)['status'].startswith('404'))

    def test_cross_site_or_simple_request_denied(self):
        for extra in [{'HTTP_SEC_FETCH_SITE': 'cross-site'}, {'HTTP_X_KEIBA_REQUEST': ''}]:
            self.assertTrue(call(self.app, '/api/research', 'POST', data=sample(), **extra)['status'].startswith('403'))

    def test_live_connection_disabled_by_default(self):
        with patch('private_service.fetch_race_program') as fetch:
            self.assertTrue(call(self.app, '/api/jrdb/program', QUERY_STRING='date=20261027')['status'].startswith('503'))
            fetch.assert_not_called()

    def test_authorized_connection_uses_fixed_client(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_race_program', return_value=[{'racekey': 'synthetic'}]) as fetch:
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('200')); fetch.assert_called_once_with('20261027')

    def test_invalid_query_is_rejected(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        for query in ['', 'date=20261027&date=20261028', 'url=https://example.com']:
            self.assertTrue(call(app, '/api/jrdb/program', QUERY_STRING=query)['status'].startswith('400'))

    def test_upstream_error_is_redacted(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_race_program', side_effect=JRDBError('secret-data')):
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('502')); self.assertNotIn(b'secret-data', result['body'])

    def test_research_pipeline_end_to_end(self):
        result = call(self.app, '/api/research', 'POST', data=sample())
        self.assertTrue(result['status'].startswith('200'))
        plan = json.loads(result['body']); self.assertFalse(plan['publishable'])
        self.assertEqual(plan['researchDecision'], 'simulate'); self.assertLessEqual(plan['points'], 40)

    def test_live_and_bad_inputs_are_rejected(self):
        for data in [{**sample(), 'recordType': 'live'}, {}, None, []]:
            self.assertNotEqual(call(self.app, '/api/research', 'POST', data=data)['status'], '200 OK')
        result = call(self.app, '/api/research', 'POST', data=sample(), CONTENT_LENGTH=str(MAX_BODY + 1))
        self.assertTrue(result['status'].startswith('413'))
        self.assertTrue(call(self.app, '/api/research', 'POST', data=sample(), CONTENT_TYPE='text/plain')['status'].startswith('415'))

    def test_html_and_script_do_not_embed_secrets(self):
        for path in ['/', '/app.js', '/app.css']:
            result = call(self.app, path)
            self.assertTrue(result['status'].startswith('200'))
            self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), result['body'])
            self.assertEqual(result['headers']['X-Frame-Options'], 'DENY')


if __name__ == '__main__': unittest.main()
