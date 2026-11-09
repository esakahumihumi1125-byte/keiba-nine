"""Private /tpd synthetic tests: only body-observation presence, no odds."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from jrdb_prestart_body import audit_prestart_body
from jrdb_program_preview import normalize_program_rows
from jrdb_coverage import CoverageError
from test_private_single_readiness_endpoint import source
from test_private_service import SETTINGS, call
from private_service import create_app


def fixture():
    raw,e,t,z,h=source()
    p=normalize_program_rows(raw,'20261101')
    before=[
        {'racedate':'20261101','racekey':'05264b01',
         'horse_id':'2328aaa95a05','horse_number':None,'horse_weight':480,
         'weight_cycling':-4,'paddock_index':'72','this_horse_body_state':'A',
         'withdrawn_flag':'0','win_odds':'9999','odds_index':'SECRET_ODDS'},
        {'racedate':'20261101','racekey':'05264b01',
         'horse_id':None,'horse_number':'02','horse_weight':0,
         'weight_cycling':0,'paddock_index':None,'this_horse_body_state':None,
         'withdrawn_flag':'1'},
    ]
    return p,e,before


class PrestartBodyAuditTests(unittest.TestCase):
    def test_optional_identity_matching_and_zero_weight_is_missing(self):
        p,e,rows=fixture()
        saved=copy.deepcopy((p,e,rows))
        report=audit_prestart_body(p,e,rows,'20261101')
        self.assertEqual(report['version'],'private-prestart-body-1')
        self.assertEqual(report['raceCount'],2)
        self.assertFalse(report['rawHorseRecordsIncluded'])
        self.assertFalse(report['oddsUsed'])
        self.assertFalse(report['officialBodyWeightVerified'])
        self.assertFalse(report['realPredictionReady'])
        self.assertFalse(report['purchaseReady'])
        self.assertEqual(report['summary']['matchedRows'],2)
        self.assertEqual(report['summary']['weightRecords'],1)
        self.assertEqual(report['summary']['paddockRecords'],1)
        self.assertEqual(report['summary']['missingRows'],1)
        tokyo=next(r for r in report['races'] if r['track']=='東京')
        self.assertEqual(tokyo['bodyWeightRecords'],1)
        self.assertEqual(tokyo['weightChangeRecords'],1)
        self.assertEqual(tokyo['providerWithdrawnReports'],1)
        self.assertEqual(tokyo['prestartRowsMissing'],0)
        kyoto=next(r for r in report['races'] if r['track']=='京都')
        self.assertEqual(kyoto['prestartRowsMissing'],1)
        self.assertEqual((p,e,rows),saved)
        # Horse-number presence only; raw weight/delta remain private.
        self.assertEqual([h['number'] for h in tokyo['runners']], [1, 2])
        one, two = tokyo['runners']
        self.assertTrue(one['prestartRowMatched'])
        self.assertTrue(one['bodyWeightRecorded'])
        self.assertTrue(one['weightChangeRecorded'])
        self.assertTrue(two['prestartRowMatched'])
        self.assertFalse(two['bodyWeightRecorded'])  # zero kg is missing
        self.assertFalse(two['weightChangeRecorded'])
        self.assertEqual(len(kyoto['runners']), 1)
        self.assertFalse(kyoto['runners'][0]['prestartRowMatched'])
        for race in report['races']:
            self.assertEqual(len(race['runners']), race['registered'])
            self.assertEqual(sum(h['bodyWeightRecorded'] for h in race['runners']),
                             race['bodyWeightRecords'])
            self.assertEqual(sum(h['weightChangeRecorded'] for h in race['runners']),
                             race['weightChangeRecords'])
            self.assertEqual(sum(h['prestartRowMatched'] for h in race['runners']),
                             race['prestartRowsMatched'])
            for horse in race['runners']:
                self.assertEqual(horse['bodyConditionGrade'], '未評価')
                self.assertIsNone(horse['bodyConditionScore1'])
                self.assertFalse(horse['jraOfficialWeightVerified'])
                self.assertFalse(horse['bettingReady'])
                self.assertEqual(set(horse), {
                    'number', 'prestartRowMatched', 'bodyWeightRecorded',
                    'weightChangeRecorded', 'jraOfficialWeightVerified',
                    'bodyConditionGrade', 'bodyConditionScore1', 'bettingReady',
                })
        output=repr(report)
        for sensitive in ('2328aaa95a05','horse_id','horse_number',
                          'NONPUBLIC','SECRET_ODDS','win_odds','9999',
                          "'horse_weight'", "'weight_cycling'"):
            self.assertNotIn(sensitive,output)

    def test_invalid_duplicates_and_cross_day_identity_fail_closed(self):
        p,e,rows=fixture()
        forged=[
            rows+[dict(rows[0])],
            [dict(rows[0],horse_number='02')],
            [dict(rows[0],racekey='08264b01')],
            [dict(rows[0],racedate='20261102')],
            [dict(rows[0],horse_id='not-known-id')],
            [dict(rows[0],horse_weight=True)],
            [dict(rows[0],horse_weight=1001)],
            [dict(rows[0],weight_cycling=300)],
            [dict(rows[0],withdrawn_flag='3')],
            [dict(rows[0],paddock_index=object())],
        ]
        for bad in forged:
            with self.subTest(label=str(type(bad[0].get('paddock_index')))),self.assertRaises(CoverageError):
                audit_prestart_body(p,e,bad,'20261101')
        with self.assertRaises(CoverageError):
            audit_prestart_body(p,e,rows,'20261132')


class PrestartBodyPrivateEndpointTests(unittest.TestCase):
    def enabled(self):
        return create_app({**SETTINGS,'JRDB_PRIVATE_ENABLED':'1',
                           'KEIBA_PRESTART_BODY_ENABLED':'1',
                           'JRDB_API_KEY':'synthetic-private-key',
                           'JRDB_AUTH_KEY':'synthetic-private-auth'})

    def test_disabled_by_default_and_zero_network(self):
        app=create_app(SETTINGS)
        with patch('private_service.fetch_prestart_body') as call_tpd:
            res=call(app,'/api/jrdb/prestart-body',QUERY_STRING='date=20261101')
        self.assertEqual(res['status'],'503 Service Unavailable')
        call_tpd.assert_not_called()

    def test_auth_header_same_day_and_no_wrong_date_paid_requests(self):
        app=self.enabled()
        with (patch('private_service._now_in_jst',
                    return_value='2026-11-01T09:40:00+09:00'),
              patch('private_service.fetch_race_program') as provider):
            self.assertEqual(call(app,'/api/jrdb/prestart-body',auth='',
                                  QUERY_STRING='date=20261101')['status'],
                             '401 Unauthorized')
            self.assertEqual(call(app,'/api/jrdb/prestart-body',
                                  HTTP_X_KEIBA_REQUEST='',
                                  QUERY_STRING='date=20261101')['status'],
                             '403 Forbidden')
            for q in ('', 'date=20261102', 'date=20261131',
                      'date=20261101&date=20261101', 'date=20261101&token=x'):
                with self.subTest(q=q):
                    self.assertEqual(call(app,'/api/jrdb/prestart-body',
                                          QUERY_STRING=q)['status'],'400 Bad Request')
            provider.assert_not_called()

    def test_three_calls_redacted_and_only_on_explicit_request(self):
        p,e,rows=fixture()
        raw,_,_,_,_=source()
        app=self.enabled()
        with (patch('private_service._now_in_jst',
                    return_value='2026-11-01T09:40:00+09:00'),
              patch('private_service.fetch_race_program',return_value=raw) as a,
              patch('private_service.fetch_horse_entries',return_value=e) as b,
              patch('private_service.fetch_prestart_body',return_value=rows) as c):
            result=call(app,'/api/jrdb/prestart-body',QUERY_STRING='date=20261101')
        self.assertEqual(result['status'],'200 OK')
        self.assertIn('no-store',result['headers']['Cache-Control'])
        report=json.loads(result['body'])
        self.assertEqual(report['summary']['weightRecords'],1)
        self.assertFalse(report['realPredictionReady'])
        self.assertFalse(report['oddsUsed'])
        for mock in (a,b,c):
            mock.assert_called_once_with('20261101')
        for private in ('2328aaa95a05','horse_name','SECRET_ODDS','9999'):
            self.assertNotIn(private,repr(report))

    def test_bad_source_is_502_not_partial(self):
        p,e,rows=fixture()
        raw,_,_,_,_=source()
        rows[0]['horse_weight']=True
        app=self.enabled()
        with (patch('private_service._now_in_jst',
                    return_value='2026-11-01T09:40:00+09:00'),
              patch('private_service.fetch_race_program',return_value=raw),
              patch('private_service.fetch_horse_entries',return_value=e),
              patch('private_service.fetch_prestart_body',return_value=rows)):
            result=call(app,'/api/jrdb/prestart-body',QUERY_STRING='date=20261101')
        self.assertEqual(result['status'],'502 Bad Gateway')
        self.assertNotIn('2328aaa95a05',str(result['body']))


if __name__=='__main__':
    unittest.main()
