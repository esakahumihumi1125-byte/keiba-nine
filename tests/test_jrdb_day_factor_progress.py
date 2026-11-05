"""Day-wide provisional factor research stays private and never becomes a bet."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

from test_private_single_readiness_endpoint import source
from test_private_service import call
from test_jrdb_day_pipeline import enabled_app
from jrdb_day_pipeline import inspect_day
from jrdb_day_factor_progress import summarize_day_factor_progress
from jrdb_program_preview import normalize_program_rows
from jrdb_coverage import CoverageError


def fixture():
    p,e,t,z,h=source()
    # Invent experimental information for one runner only.
    t[0].update(oikirisisu=82,siagarisisu=80)
    t[1].update(oikirisisu=66,siagarisisu=62)
    z[0].update(race_back_1_order_of_finish=2,
                race_back_1_idm=74,
                race_back_2_racedate='20260920',
                race_back_2_order_of_finish=3,
                race_back_2_idm=72)
    return p,e,t,z,h


class DayFactorProgressTests(unittest.TestCase):
    def test_mixed_training_recent_counts_not_overall_prediction(self):
        raw,e,t,z,h=fixture()
        p=normalize_program_rows(raw,'20261101')
        day=inspect_day(p,e,t,z,h,'20261101')
        inputs=copy.deepcopy((p,e,t,z,h,day))
        out=summarize_day_factor_progress(p,e,t,z,'20261101',day)
        self.assertEqual(out['version'],'day-factor-progress-1')
        self.assertEqual(out['raceCount'],2)
        self.assertEqual(out['summary']['runnersWithTrainingProvisional'],2)
        self.assertEqual(out['summary']['runnersWithRecentProvisional'],1)
        self.assertEqual(out['summary']['runnersWithBothProvisional'],1)
        self.assertEqual(out['summary']['actualPredictions'],0)
        self.assertFalse(out['realPredictionReady'])
        self.assertFalse(out['realOverallGradeReady'])
        self.assertFalse(out['purchaseReady'])
        tokyo=next(r for r in out['races'] if r['track']=='東京')
        self.assertEqual(tokyo['registered'],2)
        self.assertEqual(tokyo['trainingExperimentalGraded'],2)
        self.assertEqual(tokyo['recentExperimentalGraded'],1)
        self.assertEqual(tokyo['bothExperimentalGraded'],1)
        self.assertEqual(tokyo['remainingFactorsUnassessed'],8)
        self.assertEqual(tokyo['fullTenFactorsGraded'],0)
        self.assertFalse(tokyo['realOverallGradeReady'])
        self.assertEqual((p,e,t,z,h,day),inputs)
        serialized=json.dumps(out,ensure_ascii=False)
        for private in ('racekey','horse_number','horse_id','2328aaa95a05',
                        'NONPUBLIC','oikirisisu','siagarisisu','IDM',
                        'PRIVATE','win_odds'):
            self.assertNotIn(private,serialized)

    def test_source_mismatch_and_promotion_never_succeeds(self):
        raw,e,t,z,h=fixture()
        p=normalize_program_rows(raw,'20261101')
        day=inspect_day(p,e,t,z,h,'20261101')
        bad=copy.deepcopy(day)
        bad['realPredictionReady']=True
        with self.assertRaises(CoverageError):
            summarize_day_factor_progress(p,e,t,z,'20261101',bad)
        bad=copy.deepcopy(day)
        bad['races'].pop()
        with self.assertRaises(CoverageError):
            summarize_day_factor_progress(p,e,t,z,'20261101',bad)
        bad=copy.deepcopy(day)
        bad['races'][1]['track']='東京'
        with self.assertRaises(CoverageError):
            summarize_day_factor_progress(p,e,t,z,'20261101',bad)
        bad=copy.deepcopy(day)
        bad['date']='20261102'
        with self.assertRaises(CoverageError):
            summarize_day_factor_progress(p,e,t,z,'20261101',bad)
        with self.assertRaises(CoverageError):
            summarize_day_factor_progress(p,e,t,z,'20261102',day)

    def test_duplicate_identity_and_invalid_provider_index_fail_closed(self):
        raw,e,t,z,h=fixture()
        p=normalize_program_rows(raw,'20261101')
        day=inspect_day(p,e,t,z,h,'20261101')
        bad=copy.deepcopy(t)
        bad[0]['siagarisisu']='not-number'
        with self.assertRaises(CoverageError):
            summarize_day_factor_progress(p,e,bad,z,'20261101',day)
        duplicate=copy.deepcopy(t)+[copy.deepcopy(t[0])]
        with self.assertRaises(CoverageError):
            summarize_day_factor_progress(p,e,duplicate,z,'20261101',day)

    def test_endpoint_uses_existing_five_sources_once(self):
        raw,e,t,z,h=fixture()
        app=enabled_app()
        with (patch('private_service.fetch_race_program',return_value=raw) as a,
              patch('private_service.fetch_horse_entries',return_value=e) as b,
              patch('private_service.fetch_training_analysis',return_value=t) as c,
              patch('private_service.fetch_recent_runs',return_value=z) as d,
              patch('private_service.fetch_venue_conditions',return_value=h) as f,
              patch('private_service._now_in_jst',return_value='2026-11-01T09:40:00+09:00')):
            res=call(app,'/api/jrdb/day-pipeline',QUERY_STRING='date=20261101')
        self.assertEqual(res['status'],'200 OK')
        data=json.loads(res['body'])
        self.assertEqual(data['factorProgress']['summary']['runnersWithBothProvisional'],1)
        self.assertFalse(data['factorProgress']['realPredictionReady'])
        self.assertFalse(data['purchaseReady'])
        for called in (a,b,c,d,f):
            called.assert_called_once_with('20261101')
        for word in ('horse_id','horse_number','racekey','oikirisisu',
                     '2328aaa95a05','PRIVATE-SIRE'):
            self.assertNotIn(word,repr(data))


if __name__ == '__main__':
    unittest.main()
