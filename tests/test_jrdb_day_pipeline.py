"""Single-calendar-day JRDB source readiness, no API calls in CI.

All test credentials and horse records are invented and never sent online.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from private_service import create_app
from test_private_service import SETTINGS, call
from test_private_single_readiness_endpoint import source
from jrdb_program_preview import normalize_program_rows
from jrdb_day_pipeline import inspect_day
from jrdb_coverage import CoverageError

ENDPOINT='/api/jrdb/day-pipeline'
QUERY='date=20261101'


def enabled_app():
    return create_app({**SETTINGS,'JRDB_PRIVATE_ENABLED':'1',
                       'JRDB_API_KEY':'fake-nonpublic-test-api',
                       'JRDB_AUTH_KEY':'fake-nonpublic-test-auth'})


class DayPipelineTests(unittest.TestCase):
    def test_multiple_races_and_private_identity_redaction(self):
        p,e,t,z,h=source()
        e[0]['horse_name']='DO-NOT-LEAK-PER-HORSE-NAME'
        e[0]['sire_name']='DO-NOT-LEAK-SIRE'
        report=inspect_day(normalize_program_rows(p,'20261101'),e,t,z,h,'20261101')
        self.assertEqual(report['version'],'private-day-pipeline-1')
        self.assertEqual(report['raceCount'],2)
        self.assertFalse(report['realPredictionReady'])
        self.assertFalse(report['purchaseReady'])
        self.assertFalse(report['rawHorseRecordsIncluded'])
        self.assertEqual(report['summary']['realPredictions'],0)
        self.assertEqual(report['sourceRequestCount'],5)
        self.assertEqual(set(report['sourceRequestsRequired']),{'tra','tky','tcy','tze','tka'})
        self.assertEqual({(r['track'],r['race']) for r in report['races']},{('東京',1),('京都',1)})
        self.assertEqual(report['summary']['matchedEntryCountRaces'],2)
        for r in report['races']:
            self.assertEqual(r['gradedFactors'],0)
            self.assertFalse(r['realPredictionReady'])
            self.assertFalse(r['ticketReady'])
            self.assertFalse(r['independentJraVerified'])
            self.assertTrue(r['blockers'])
        redacted=repr(report)
        for secret in ('DO-NOT-LEAK-PER-HORSE-NAME','DO-NOT-LEAK-SIRE',
                       'racekey','horse_id','horse_number','fake-nonpublic-test-api'):
            self.assertNotIn(secret,redacted)

    def test_wrong_source_snapshot_rejected_before_any_report(self):
        p,e,t,z,h=source()
        normalized=normalize_program_rows(p,'20261101')
        with self.assertRaises(CoverageError):
            inspect_day(normalized,e,t,z,h,'20261102')
        with self.assertRaises(CoverageError):
            inspect_day(normalized,e+[dict(e[0])],t,z,h,'20261101')
        with self.assertRaises(CoverageError):
            inspect_day(normalized,e,t+[{'racekey':'00000000','racedate':'20261101'}],z,h,'20261101')
        with self.assertRaises(CoverageError):
            inspect_day(normalized,e,t,z,h,'20261131')


class DayPipelineRouteTests(unittest.TestCase):
    def test_disabled_before_provider_credentials_no_calls(self):
        app=create_app(SETTINGS)
        with patch('private_service.fetch_race_program') as provider:
            out=call(app,ENDPOINT,QUERY_STRING=QUERY)
            self.assertEqual(out['status'],'503 Service Unavailable')
            provider.assert_not_called()

    def test_both_auth_and_private_header_required(self):
        app=enabled_app()
        with patch('private_service.fetch_race_program') as provider:
            self.assertEqual(call(app,ENDPOINT,auth='',QUERY_STRING=QUERY)['status'],
                             '401 Unauthorized')
            self.assertEqual(call(app,ENDPOINT,QUERY_STRING=QUERY,
                                  HTTP_X_KEIBA_REQUEST='')['status'],
                             '403 Forbidden')
            provider.assert_not_called()

    def test_reject_duplicate_invalid_date_before_provider_calls(self):
        app=enabled_app()
        inputs=('', 'date=20261101&date=20261102', 'date=20261101&key=secret',
                'date=20261131', 'date=2026-11-01', 'date=%EF%BC%92%EF%BC%90%EF%BC%92%EF%BC%96')
        with patch('private_service.fetch_race_program') as provider:
            for bad in inputs:
                with self.subTest(bad=bad):
                    out=call(app,ENDPOINT,QUERY_STRING=bad)
                    self.assertEqual(out['status'],'400 Bad Request')
            provider.assert_not_called()

    def test_five_calls_once_cover_all_races_without_horse_source_export(self):
        p,e,t,z,h=source()
        app=enabled_app()
        with (patch('private_service.fetch_race_program',return_value=p) as program,
              patch('private_service.fetch_horse_entries',return_value=e) as entries,
              patch('private_service.fetch_training_analysis',return_value=t) as training,
              patch('private_service.fetch_recent_runs',return_value=z) as previous,
              patch('private_service.fetch_venue_conditions',return_value=h) as conditions):
            out=call(app,ENDPOINT,QUERY_STRING=QUERY)
        self.assertEqual(out['status'],'200 OK')
        self.assertIn('no-store',out['headers']['Cache-Control'])
        report=json.loads(out['body'])
        self.assertEqual(report['raceCount'],2)
        self.assertEqual(len(report['races']),2)
        self.assertFalse(report['realPredictionReady'])
        self.assertFalse(report['purchaseReady'])
        for mock in (program,entries,training,previous,conditions):
            mock.assert_called_once_with('20261101')
        for secret in ('racekey','horse_id','horse_number','fake-nonpublic-test-api'):
            self.assertNotIn(secret,repr(report))

    def test_invalid_data_returns_no_partial_results(self):
        p,e,t,z,h=source()
        app=enabled_app()
        e[0]['horse_number']='19'
        with (patch('private_service.fetch_race_program',return_value=p),
              patch('private_service.fetch_horse_entries',return_value=e),
              patch('private_service.fetch_training_analysis',return_value=t),
              patch('private_service.fetch_recent_runs',return_value=z),
              patch('private_service.fetch_venue_conditions',return_value=h)):
            out=call(app,ENDPOINT,QUERY_STRING=QUERY)
        self.assertEqual(out['status'],'502 Bad Gateway')
        self.assertNotIn('DO-NOT-LEAK',str(out['body']))


if __name__=='__main__':
    unittest.main()
