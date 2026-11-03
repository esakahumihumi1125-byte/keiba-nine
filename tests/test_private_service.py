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

    def test_setup_diagnostic_requires_owner_and_custom_header(self):
        for auth in ('', 'Basic malformed'):
            self.assertTrue(call(self.app, '/api/setup', auth=auth)['status'].startswith('401'))
        self.assertTrue(call(self.app, '/api/setup', HTTP_X_KEIBA_REQUEST='')['status'].startswith('403'))

    def test_setup_diagnostic_discloses_no_secrets_or_false_readiness(self):
        out = call(self.app, '/api/setup')
        self.assertEqual(out['status'], '200 OK')
        data = json.loads(out['body'])
        self.assertEqual(data['transport'], 'https')
        self.assertFalse(data['jrdbConfigured'])
        self.assertFalse(data['liveConnectionVerified'])
        self.assertFalse(data['realPredictionEnabled'])
        self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), out['body'])
        self.assertEqual(set(data), {'transport', 'jrdbConfigured',
                                   'liveConnectionVerified', 'realPredictionEnabled',
                                   'nextStep'})
        self.assertIn('no-store', out['headers']['Cache-Control'])

    def test_configured_setup_diagnostic_never_claims_live_api_success(self):
        cfg = {**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1',
               'JRDB_API_KEY': 'synthetic-api-key-not-real',
               'JRDB_AUTH_KEY': 'synthetic-auth-key-not-real'}
        with patch('private_service.fetch_race_program') as fetch:
            out = call(create_app(cfg), '/api/setup')
        self.assertEqual(out['status'], '200 OK')
        body = json.loads(out['body'])
        self.assertTrue(body['jrdbConfigured'])
        self.assertFalse(body['liveConnectionVerified'])
        self.assertFalse(body['realPredictionEnabled'])
        self.assertNotIn(cfg['JRDB_API_KEY'].encode(), out['body'])
        self.assertNotIn(cfg['JRDB_AUTH_KEY'].encode(), out['body'])
        fetch.assert_not_called()

    def test_http_preview_cannot_enable_paid_jrdb_credentials(self):
        with self.assertRaisesRegex(ValueError, 'HTTPS-only'):
            create_app({**SETTINGS, 'KEIBA_ALLOW_LOCAL_HTTP': '1',
                        'JRDB_PRIVATE_ENABLED': '1', 'JRDB_API_KEY': 'fake',
                        'JRDB_AUTH_KEY': 'fake'})
        local = create_app({**SETTINGS, 'KEIBA_ALLOW_LOCAL_HTTP': '1'})
        info = json.loads(call(local, '/api/setup', **{'wsgi.url_scheme':'http'})['body'])
        self.assertEqual(info['transport'], 'local-dev')
        self.assertFalse(info['jrdbConfigured'])

    def test_private_page_exposes_diagnostic_without_credentials(self):
        html = call(self.app, '/')['body']
        script = call(self.app, '/app.js')['body']
        self.assertIn(b'id="diagnose"', html)
        self.assertIn(b'/api/setup', script)
        self.assertNotIn(SETTINGS['KEIBA_OWNER_PASSWORD'].encode(), html + script)

    def test_live_connection_disabled_by_default(self):
        with patch('private_service.fetch_race_program') as fetch:
            self.assertTrue(call(self.app, '/api/jrdb/program', QUERY_STRING='date=20261027')['status'].startswith('503'))
            fetch.assert_not_called()

    def test_authorized_connection_uses_fixed_client(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        incoming = [{'racekey': '05264b11', 'racedate': '20261027',
                     'post_time': '1555', 'racecourse_cd': '05',
                     'track_type': '1', 'distance': '2000',
                     'race_name': '架空テスト', 'headcount': 15,
                     'privateNotes': 'never-display-secret'}]
        with patch('private_service.fetch_race_program', return_value=incoming) as fetch:
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('200'))
            fetch.assert_called_once_with('20261027')
            payload = json.loads(result['body'])
            self.assertTrue(payload['programmeOnly'])
            self.assertEqual(payload['rows'][0]['track'], '東京')
            self.assertEqual(payload['rows'][0]['race'], 11)
            self.assertEqual(payload['rows'][0]['post_time'], '15:55')
            self.assertNotIn(b'never-display-secret', result['body'])

    def test_invalid_upstream_programme_is_not_exposed(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_race_program',
                   return_value=[{'racekey': 'invalid', 'secret': 'hidden-value'}]):
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('502'))
            self.assertNotIn(b'hidden-value', result['body'])

    def test_private_coverage_counts_without_leaking_horse_data(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        programme = [{'racekey': '05264b11', 'racedate': '20261027',
                      'racecourse_cd': '05', 'post_time': '1555',
                      'headcount': 2}]
        entries = [
            {'racekey': '05264b11', 'racedate': '20261027',
             'horse_number': n, 'horse_name': 'TOP-SECRET-HORSE'}
            for n in ('01', '02')
        ]
        with patch('private_service.fetch_race_program', return_value=programme), \
             patch('private_service.fetch_horse_entries', return_value=entries):
            result = call(app, '/api/jrdb/coverage', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('200'))
        payload = json.loads(result['body'])
        self.assertEqual(payload['raceCount'], 1)
        self.assertEqual(payload['matchingEntryCounts'], 1)
        self.assertEqual(payload['predictionsReady'], 0)
        self.assertNotIn(b'TOP-SECRET-HORSE', result['body'])

    def test_private_coverage_is_denied_without_connection(self):
        app = create_app(SETTINGS)
        with patch('private_service.fetch_race_program') as programme, \
             patch('private_service.fetch_horse_entries') as entries:
            result = call(app, '/api/jrdb/coverage', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('503'))
        programme.assert_not_called()
        entries.assert_not_called()

    def test_training_and_recent_evidence_are_private_counts_only(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [{'racekey': '05264b01', 'racedate': '20261027',
                 'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        horse = [{'racekey': '05264b01', 'racedate': '20261027',
                  'horse_number': '01', 'horse_id': '2328aaa95a05',
                  'horse_name': 'SECRET-HORSE'}]
        training = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': None, 'horse_id': '2328aaa95a05',
                     'oikirisisu': 40, 'oikirisisu_lastweek': 30,
                     'internal_field': 'HIDDEN-DATA'}]
        previous = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'race_back_1_racedate': '20260926'}]
        with patch('private_service.fetch_race_program', return_value=race), \
             patch('private_service.fetch_horse_entries', return_value=horse), \
             patch('private_service.fetch_training_analysis', return_value=training), \
             patch('private_service.fetch_recent_runs', return_value=previous):
            result = call(app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('200'))
        data = json.loads(result['body'])
        self.assertEqual(data['raceCount'], 1)
        self.assertEqual(data['races'][0]['trainingRecords'], 1)
        self.assertEqual(data['races'][0]['lastWeekRecords'], 1)
        self.assertEqual(data['races'][0]['pastRunRecords'], 1)
        self.assertEqual(data['races'][0]['trainingUnaccounted'], 0)
        self.assertEqual(data['races'][0]['lastWeekUnaccounted'], 0)
        self.assertEqual(data['races'][0]['pastRunUnaccounted'], 0)
        self.assertEqual(data['gapRaceCount'], 0)
        self.assertEqual(data['unaccountedTotals'],
                         {'training': 0, 'lastWeek': 0, 'pastRuns': 0})
        self.assertEqual(data['predictionsReady'], 0)
        preflight = data['assessmentPreflight']
        self.assertEqual(preflight['factorCount'], 10)
        self.assertEqual(preflight['gradedFactors'], 0)
        self.assertEqual(preflight['readyForPrediction'], 0)
        self.assertEqual(preflight['raceCount'], 1)
        self.assertEqual(preflight['races'][0]['factors']['training']['grade'], '未評価')
        self.assertEqual(preflight['races'][0]['factors']['recent']['grade'], '未評価')
        self.assertNotIn(b'SECRET-HORSE', result['body'])
        self.assertNotIn(b'HIDDEN-DATA', result['body'])

    def test_evidence_gap_summary_is_owner_only_and_not_live_prediction(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [{'racekey': '05264b01', 'racedate': '20261027',
                 'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        entries = [{'racekey': '05264b01', 'racedate': '20261027',
                    'horse_number': '01', 'horse_id': '2328aaa95a05',
                    'horse_name': 'NONPUBLIC-TEST-HORSE'}]
        with (
            patch('private_service.fetch_race_program', return_value=race),
            patch('private_service.fetch_horse_entries', return_value=entries),
            patch('private_service.fetch_training_analysis', return_value=[]),
            patch('private_service.fetch_recent_runs', return_value=[]),
        ):
            denied = call(private, '/api/jrdb/evidence', auth='',
                          QUERY_STRING='date=20261027')
            result = call(private, '/api/jrdb/evidence',
                          QUERY_STRING='date=20261027')
        self.assertTrue(denied['status'].startswith('401'))
        self.assertTrue(result['status'].startswith('200'))
        report = json.loads(result['body'])
        self.assertEqual(report['gapRaceCount'], 1)
        self.assertEqual(report['unaccountedTotals'],
                         {'training': 1, 'lastWeek': 1, 'pastRuns': 1})
        self.assertFalse(report['races'][0]['predictionsReady'])
        self.assertEqual(report['races'][0]['trainingUnaccounted'], 1)
        self.assertNotIn(b'NONPUBLIC-TEST-HORSE', result['body'])
        self.assertNotIn(b'2328aaa95a05', result['body'])
        self.assertNotIn(b'API_KEY', result['body'])

    def test_private_client_script_displays_missing_evidence_counts(self):
        script = call(self.app, '/app.js')['body']
        for label in (b'trainingUnaccounted', b'lastWeekUnaccounted',
                      b'pastRunUnaccounted', b'gapRaceCount',
                      b'assessmentPreflight', b'sourceStatus',
                      b'trainingHypothesis', b'gradeCounts'):
            self.assertIn(label, script)
        self.assertNotIn(b'innerHTML', script)

    def test_preflight_does_not_promote_raw_horse_data_to_grades(self):
        private = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        race = [{'racekey': '05264b01', 'racedate': '20261027',
                 'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        entries = [{'racekey': '05264b01', 'racedate': '20261027',
                    'horse_number': '01', 'horse_id': '2328aaa95a05',
                    'horse_name': 'SECRET-PROVIDER-HORSE'}]
        training = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'oikirisisu': 99, 'oikirisisu_lastweek': 90,
                     'grade': 'S', 'private_notes': 'SECRET-PAID-REPORT'}]
        previous = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'race_back_1_racedate': '20261001'}]
        with (
            patch('private_service.fetch_race_program', return_value=race),
            patch('private_service.fetch_horse_entries', return_value=entries),
            patch('private_service.fetch_training_analysis', return_value=training),
            patch('private_service.fetch_recent_runs', return_value=previous),
        ):
            result = call(private, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertEqual(result['status'], '200 OK')
        data = json.loads(result['body'])
        self.assertEqual(data['assessmentPreflight']['gradedFactors'], 0)
        row = data['assessmentPreflight']['races'][0]
        self.assertTrue(all(item['grade'] == '未評価'
                            for item in row['factors'].values()))
        self.assertEqual(row['factors']['training']['sourceStatus'],
                         'source_record_count_matches')
        for private_value in (b'SECRET-PROVIDER-HORSE', b'SECRET-PAID-REPORT',
                              b'2328aaa95a05', b'oikirisisu'):
            self.assertNotIn(private_value, result['body'])

    def test_private_workout_hypothesis_returns_only_aggregate_provisional_grades(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        program = [{'racekey': '05264b01', 'racedate': '20261027',
                    'racecourse_cd': '05', 'post_time': '1010', 'headcount': 2}]
        horses = [
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '01', 'horse_id': '2328aaa95a05',
             'horse_name': 'PRIVATE-HORSE-A'},
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '02', 'horse_id': '2328aaa95a06',
             'horse_name': 'PRIVATE-HORSE-B'},
        ]
        training = [
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '01', 'horse_id': '2328aaa95a05',
             'oikirisisu': 78, 'siagarisisu': 80},
            {'racekey': '05264b01', 'racedate': '20261027',
             'horse_number': '02', 'horse_id': '2328aaa95a06',
             'oikirisisu': 62, 'siagarisisu': 60},
        ]
        with (
            patch('private_service.fetch_race_program', return_value=program),
            patch('private_service.fetch_horse_entries', return_value=horses),
            patch('private_service.fetch_training_analysis', return_value=training),
            patch('private_service.fetch_recent_runs', return_value=[]),
        ):
            result = call(app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertEqual(result['status'], '200 OK')
        payload = json.loads(result['body'])
        counts = payload['trainingHypothesis']['races'][0]['gradeCounts']
        self.assertEqual(counts, {'S': 1, 'A': 1, 'B': 0, 'C': 0, '未評価': 0})
        self.assertFalse(payload['trainingHypothesis']['predictionReady'])
        self.assertEqual(payload['assessmentPreflight']['gradedFactors'], 0)
        self.assertEqual(payload['predictionsReady'], 0)
        for secret in (b'PRIVATE-HORSE-', b'2328aaa95a05',
                       b'oikirisisu', b'siagarisisu'):
            self.assertNotIn(secret, result['body'])

    def test_out_of_range_workout_index_cannot_produce_a_race_report(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        program = [{'racekey': '05264b01', 'racedate': '20261027',
                    'racecourse_cd': '05', 'post_time': '1010', 'headcount': 1}]
        horses = [{'racekey': '05264b01', 'racedate': '20261027',
                   'horse_number': '01', 'horse_id': '2328aaa95a05'}]
        training = [{'racekey': '05264b01', 'racedate': '20261027',
                     'horse_number': '01', 'horse_id': '2328aaa95a05',
                     'oikirisisu': 999, 'siagarisisu': 70,
                     'private': 'SECRET-PROVIDER-SCORE'}]
        with (
            patch('private_service.fetch_race_program', return_value=program),
            patch('private_service.fetch_horse_entries', return_value=horses),
            patch('private_service.fetch_training_analysis', return_value=training),
            patch('private_service.fetch_recent_runs', return_value=[]),
        ):
            result = call(app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('502'))
        self.assertNotIn(b'SECRET-PROVIDER-SCORE', result['body'])

    def test_evidence_endpoint_disabled_without_private_activation(self):
        with patch('private_service.fetch_race_program') as fetch:
            result = call(self.app, '/api/jrdb/evidence', QUERY_STRING='date=20261027')
        self.assertTrue(result['status'].startswith('503'))
        fetch.assert_not_called()

    def test_evidence_endpoint_is_owner_only(self):
        for auth in ('', 'Basic malformed'):
            result = call(self.app, '/api/jrdb/evidence', auth=auth,
                          QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('401'))

    def test_invalid_query_is_rejected(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        for query in ['', 'date=20261027&date=20261028', 'url=https://example.com']:
            self.assertTrue(call(app, '/api/jrdb/program', QUERY_STRING=query)['status'].startswith('400'))

    def test_upstream_error_is_redacted(self):
        app = create_app({**SETTINGS, 'JRDB_PRIVATE_ENABLED': '1'})
        with patch('private_service.fetch_race_program', side_effect=JRDBError('secret-data')):
            result = call(app, '/api/jrdb/program', QUERY_STRING='date=20261027')
            self.assertTrue(result['status'].startswith('502')); self.assertNotIn(b'secret-data', result['body'])

    def test_research_preview_available_only_to_owner(self):
        for path in ('/', '/app.js'):
            blocked = call(self.app, path, auth='')
            self.assertTrue(blocked['status'].startswith('401'))
        html = call(self.app, '/')['body']
        script = call(self.app, '/app.js')['body']
        for label in (b'id="researchDemo"', b'id="researchInput"',
                      b'id="researchRun"', b'id="researchFile"'):
            self.assertIn(label, html)
        for label in (b'function syntheticSample', b'async function runResearch',
                      b"'/api/research'", b"recordType:'test'"):
            self.assertIn(label, script)
        self.assertIn(b'textContent', script)
        self.assertNotIn(b'innerHTML', script)

    def test_research_sandbox_rejects_real_provider_sources(self):
        race = sample()
        race['horses'][0]['assessments']['training']['evidence'][0]['sourceId'] = 'jrdb-tcy'
        with patch('private_service.fetch_race_program') as fetch:
            response = call(self.app, '/api/research', 'POST', data=race)
        self.assertTrue(response['status'].startswith('400'))
        self.assertNotIn(b'jrdb-tcy', response['body'])
        fetch.assert_not_called()

    def test_research_sandbox_rejects_bad_evidence_shapes(self):
        for evidence in ('not-an-array', [{'sourceId': 'unknown'}],
                         [{'sourceId': 'synthetic'}, None], {}):
            with self.subTest(evidence=evidence):
                race = sample()
                race['horses'][0]['assessments']['recent']['evidence'] = evidence
                result = call(self.app, '/api/research', 'POST', data=race)
                self.assertTrue(result['status'].startswith('400'))

    def test_synthetic_research_response_contains_rank_and_tickets_only_as_test(self):
        result = call(self.app, '/api/research', 'POST', data=sample())
        self.assertEqual(result['status'], '200 OK')
        payload = json.loads(result['body'])
        self.assertEqual(payload['recordType'], 'test')
        self.assertFalse(payload['publishable'])
        self.assertFalse(payload['validated'])
        self.assertEqual(payload['researchDecision'], 'simulate')
        self.assertTrue(len(payload['evaluation']['horses']) >= 2)
        self.assertEqual(payload['points'], len(payload['tri']))
        self.assertLessEqual(payload['points'], 40)
        self.assertEqual(payload['stake'], payload['points'] * 100)

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
