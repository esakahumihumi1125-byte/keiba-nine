"""Race-day priority is an observation-only, fail-closed private queue."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from test_private_single_readiness_endpoint import source
from test_jrdb_day_pipeline import enabled_app
from test_private_service import call
from jrdb_program_preview import normalize_program_rows
from jrdb_day_pipeline import inspect_day
from jrdb_prestart_freshness import audit_prestart_freshness
from jrdb_day_review_gate import build_day_review_queue
from jrdb_coverage import CoverageError


def fixture(checked_at='2026-11-01T09:40:00+09:00'):
    p,e,t,z,h=source()
    program=normalize_program_rows(p,'20261101')
    day=inspect_day(program,e,t,z,h,'20261101')
    freshness=audit_prestart_freshness(program,h,'20261101',checked_at)
    return day,freshness


class DayReviewTests(unittest.TestCase):
    def test_future_start_priority_uses_server_clock_and_private_status(self):
        day,freshness=fixture()
        out=build_day_review_queue(day,freshness)
        self.assertEqual(out['version'],'private-day-review-1')
        self.assertEqual(out['raceCount'],2)
        self.assertEqual(out['racesWithinTwoHours'],2)
        self.assertEqual(out['racesNeedingManualPriorityCheck'],2)
        self.assertEqual(out['racesWithRecentSourceGoing'],1)
        self.assertEqual(out['racesPassedPost'],0)
        by_track={r['track']:r for r in out['races']}
        self.assertTrue(by_track['東京']['candidateForManualJraReview'])
        self.assertFalse(by_track['京都']['candidateForManualJraReview'])
        self.assertTrue(by_track['東京']['sourceGoingAgeStatus']=='recent_reported')
        self.assertFalse(by_track['東京']['realPredictionReady'])
        self.assertFalse(out['officialFinalVerified'])
        self.assertFalse(out['purchaseReady'])
        self.assertIn('公式',repr(out))
        for private in ('racekey','horse_id','horse_number','LICENSED-HORSE-PRIVATE',
                        'LICENSED-GOING-PRIVATE','holdingkey','2026-11-01T00:30:00Z'):
            self.assertNotIn(private,repr(out))

    def test_post_passed_is_not_a_betting_candidate(self):
        day,freshness=fixture('2026-11-01T11:00:00+09:00')
        out=build_day_review_queue(day,freshness)
        self.assertEqual(out['racesPassedPost'],2)
        for row in out['races']:
            self.assertEqual(row['reviewPriority'],'post_time_passed')
            self.assertFalse(row['candidateForManualJraReview'])
            self.assertIn('発走時刻経過・馬券対象外',row['blockers'])
            self.assertFalse(row['ticketReady'])

    def test_clocks_and_missing_updates_dont_create_verified_races(self):
        for clock in ('2026-11-01T09:20:00+09:00',
                      '2026-11-02T09:40:00+09:00'):
            day, freshness=fixture(clock)
            result=build_day_review_queue(day,freshness)
            self.assertEqual(result['raceCount'],2)
            self.assertFalse(result['realPredictionReady'])
            self.assertTrue(all(r['blockers'] for r in result['races']))
            self.assertTrue(all(not r['independentJraVerified'] for r in result['races']))

    def test_duplicate_missing_or_promoted_races_fail_closed(self):
        day, fresh=fixture()
        damaged=[]
        bad=copy.deepcopy(fresh);bad['races'][1]['track']=bad['races'][0]['track'];bad['races'][1]['race']=bad['races'][0]['race'];damaged.append((day,bad))
        bad=copy.deepcopy(fresh);bad['races'].pop();damaged.append((day,bad))
        bad=copy.deepcopy(fresh);bad['races'][0]['predictionReady']=True;damaged.append((day,bad))
        bad=copy.deepcopy(fresh);bad['races'][0]['candidateForManualJraReview']=False;damaged.append((day,bad))
        bad=copy.deepcopy(fresh);bad['races'][0]['listedPostTime']='17:10';damaged.append((day,bad))
        bad=copy.deepcopy(day);bad['races'][0]['ticketReady']=True;damaged.append((bad,fresh))
        bad=copy.deepcopy(day);bad['realPredictionReady']=True;damaged.append((bad,fresh))
        for main,timing in damaged:
            with self.subTest(main=main['version'],timing=timing['version']),self.assertRaises(CoverageError):
                build_day_review_queue(main,timing)

    def test_pure_and_deterministic_for_same_snapshot(self):
        day, fresh=fixture()
        a,b=copy.deepcopy(day),copy.deepcopy(fresh)
        first=build_day_review_queue(day,fresh)
        self.assertEqual(first,build_day_review_queue(day,fresh))
        self.assertEqual(day,a)
        self.assertEqual(fresh,b)


class DayReviewRouteTests(unittest.TestCase):
    def test_owner_only_result_joins_without_another_paid_fetch(self):
        p,e,t,z,h=source()
        app=enabled_app()
        with (patch('private_service.fetch_race_program',return_value=p) as a,
              patch('private_service.fetch_horse_entries',return_value=e) as b,
              patch('private_service.fetch_training_analysis',return_value=t) as c,
              patch('private_service.fetch_recent_runs',return_value=z) as d,
              patch('private_service.fetch_venue_conditions',return_value=h) as f,
              patch('private_service._now_in_jst',return_value='2026-11-01T09:40:00+09:00')):
            response=call(app,'/api/jrdb/day-pipeline',QUERY_STRING='date=20261101')
        self.assertEqual(response['status'],'200 OK')
        payload=json.loads(response['body'])
        self.assertEqual(payload['reviewQueue']['racesNeedingManualPriorityCheck'],2)
        self.assertEqual(payload['reviewQueue']['racesWithRecentSourceGoing'],1)
        self.assertFalse(payload['reviewQueue']['realPredictionReady'])
        self.assertFalse(payload['reviewQueue']['purchaseReady'])
        for call_mock in (a,b,c,d,f):
            call_mock.assert_called_once_with('20261101')
        for raw in ('racekey','horse_id','horse_number','LICENSED-HORSE-PRIVATE'):
            self.assertNotIn(raw,repr(payload))

    def test_bad_timing_snapshot_blocks_no_partial_readiness_response(self):
        p,e,t,z,h=source()
        app=enabled_app()
        h[0]['updated_at']='2099-01-01T09:00:00+09:00'
        with (patch('private_service.fetch_race_program',return_value=p),
              patch('private_service.fetch_horse_entries',return_value=e),
              patch('private_service.fetch_training_analysis',return_value=t),
              patch('private_service.fetch_recent_runs',return_value=z),
              patch('private_service.fetch_venue_conditions',return_value=h),
              patch('private_service._now_in_jst',return_value='2026-11-01T09:40:00+09:00')):
            response=call(app,'/api/jrdb/day-pipeline',QUERY_STRING='date=20261101')
        self.assertEqual(response['status'],'200 OK')
        report=json.loads(response['body'])
        self.assertEqual(report['reviewQueue']['racesWithRecentSourceGoing'],0)
        self.assertFalse(report['reviewQueue']['officialFinalVerified'])


if __name__=='__main__':
    unittest.main()
