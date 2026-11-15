import copy
import json
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from owner_automatic_factor_scores import automatic_factor_scores
from jrdb_coverage import CoverageError
from test_private_service import call, SETTINGS
from private_service import create_app

DAY = '20261121'
NOW = datetime.fromisoformat('2026-11-21T09:00:00+09:00')


def fixture():
    p = [{'racekey': '05265501', 'racedate': DAY, 'track': '東京', 'race': 1,
          'post_time': '10:00', 'headcount': 4}]
    e = [{'racekey': p[0]['racekey'], 'racedate': DAY, 'horse_number': f'{n:02d}',
          'horse_id': f'{n:012d}', 'withdrawn_flag': '0', 'foottype_cd': str(n),
          'jockey_index': str(n), 'stable_index': str(n * 2)} for n in range(1, 5)]
    z = [{**{k: r[k] for k in ('racekey', 'racedate', 'horse_id', 'horse_number')},
          'race_back_1_racedate': '20261031'} for r in e]
    return p, e, z


class AutomaticFactorTests(unittest.TestCase):
    def score(self, data=None, now=NOW):
        return automatic_factor_scores(*(data or fixture()), DAY, now=now)

    def test_numeric_contributions_and_source_immutability(self):
        data = fixture()
        original = copy.deepcopy(data)
        out = self.score(data)
        horses = out['races'][0]['horses']
        self.assertEqual(horses[0]['factors']['jockey_stable']['points'], 0)
        self.assertEqual(horses[3]['factors']['jockey_stable']['points'], 10)
        self.assertEqual(horses[0]['factors']['rotation']['points'], .8)
        self.assertGreater(horses[2]['factors']['pace']['points'], horses[0]['factors']['pace']['points'])
        self.assertEqual(data, original)
        self.assertFalse(out['modelCalibrated'])
        self.assertFalse(out['overallPredictionReady'])
        for private in ('horse_id', 'racekey', 'jockey_index', 'stable_index', '20261031'):
            self.assertNotIn(private, json.dumps(out))

    def test_distance_research_provisional_no_extra_claims(self):
        data = fixture()
        data[0][0].update(surface='芝', distance_m=1600)
        for row, code in zip(data[1], ('5', '1', '2', '6')):
            row['distance_aptitude_cd1'] = code
        original = copy.deepcopy(data)
        out = self.score(data)
        got = [h['factors']['course_distance'] for h in out['races'][0]['horses']]
        self.assertEqual([x['points'] for x in got], [14.45, 11.05, 11.05, 12.75])
        self.assertEqual([x['grade'] for x in got], ['S', 'B', 'B', 'A'])
        self.assertEqual(out['maximumPoints'], 45)
        self.assertEqual(out['version'], 'owner-automatic-factor-scores-2')
        self.assertFalse(out['officialJraVerified'])
        self.assertFalse(out['overallPredictionReady'])
        self.assertEqual(data, original)
        data[1][0]['distance_aptitude_cd1'] = None
        missing = self.score(data)['races'][0]['horses'][0]['factors']['course_distance']
        self.assertIsNone(missing['points'])
        self.assertEqual(missing['reason'], 'distance_code_missing')
        data[0][0]['surface'] = '障害'
        self.assertTrue(all(h['factors']['course_distance']['points'] is None
                            for h in self.score(data)['races'][0]['horses']))
        data[0][0].update(surface='芝', distance_m=4000)
        self.assertTrue(all(h['factors']['course_distance']['points'] is None
                            for h in self.score(data)['races'][0]['horses']))

    def test_odds_and_popularity_have_no_effect(self):
        data = fixture()
        before = self.score(data)
        for row in data[1]:
            row.update(criteria_win_odds=999, criteria_win_popularity=1, popularity_index=9000,
                       integration_index=9999, odds_mark='1')
        self.assertEqual(before, self.score(data))

    def test_equal_indices_stay_equal_and_missing_is_not_zero(self):
        data = fixture()
        for e in data[1]:
            e.update(jockey_index='2', stable_index='2')
        self.assertEqual({h['factors']['jockey_stable']['points'] for h in
                         self.score(data)['races'][0]['horses']}, {5})
        for invalid in (None, '', 'NaN', float('inf'), True, {}):
            broken = copy.deepcopy(data)
            broken[1][0]['stable_index'] = invalid
            self.assertTrue(all(h['factors']['jockey_stable']['points'] is None
                                for h in self.score(broken)['races'][0]['horses']))
        data[2].pop()
        self.assertIsNone(self.score(data)['races'][0]['horses'][-1]['factors']['rotation']['points'])

    def test_missing_style_withholds_pace_for_whole_race(self):
        data = fixture()
        data[1][0]['foottype_cd'] = None
        self.assertTrue(all(h['factors']['pace']['points'] is None for h in
                            self.score(data)['races'][0]['horses']))
        for style in ('5', '6'):
            data[1][0]['foottype_cd'] = style
            self.assertIsNotNone(self.score(data)['races'][0]['horses'][0]['factors']['pace']['points'])

    def test_start_roster_and_withdrawal_gates(self):
        for change in ('late', 'roster', 'unknown', 'withdrawn'):
            data = fixture()
            now = NOW
            if change == 'late': now = datetime.fromisoformat('2026-11-21T10:00:00+09:00')
            if change == 'roster': data[0][0]['headcount'] = 5
            if change == 'unknown': data[1][0].pop('withdrawn_flag')
            if change == 'withdrawn': data[1][0]['withdrawn_flag'] = '1'
            row = self.score(data, now)['races'][0]
            self.assertEqual(row['status'], 'held')
            self.assertEqual(row['horses'], [])

    def test_duplicate_identity_and_future_history_rejected(self):
        for change in ('duplicate', 'future', 'wrong_horse'):
            data = fixture()
            if change == 'duplicate': data[2].append(copy.deepcopy(data[2][0]))
            if change == 'future': data[2][0]['race_back_1_racedate'] = DAY
            if change == 'wrong_horse': data[2][0]['horse_id'] = '000000000099'
            with self.assertRaises(CoverageError): self.score(data)

    def test_private_http_route_reuses_existing_fetches(self):
        from contextlib import ExitStack
        p, e, z = fixture()
        raw = [{'racekey': '05265501', 'racedate': DAY, 'post_time': '1000',
                'headcount': 4, 'track_type': '1', 'distance': '1600', 'turn_cd': '2'}]
        config = {**SETTINGS, 'KEIBA_RENDER_PRIVATE_ONLY': '1', 'JRDB_PRIVATE_ENABLED': '1',
                  'JRDB_API_KEY': 'synthetic', 'JRDB_AUTH_KEY': 'synthetic',
                  'JRDB_API_BASE_URL': 'https://api.bigtime.world/v1'}
        app = create_app(config)
        with ExitStack() as stack:
            mocks = [stack.enter_context(patch('private_service.' + name, return_value=value))
                     for name, value in [('fetch_race_program', raw), ('fetch_horse_entries', e),
                         ('fetch_training_analysis', []), ('fetch_recent_runs', z),
                         ('fetch_venue_conditions', [])]]
            stack.enter_context(patch('private_service._now_in_jst', return_value=NOW.isoformat()))
            response = call(app, '/api/jrdb/owner-auto-draft', QUERY_STRING='date=' + DAY)
            self.assertEqual(response['status'], '200 OK')
            result = json.loads(response['body'])
            self.assertEqual(len(result['automaticFactorScores']['races'][0]['horses']), 4)
            for mock in mocks: mock.assert_called_once()
            unauth = call(app, '/api/jrdb/owner-auto-draft', QUERY_STRING='date=' + DAY, auth='')
            self.assertEqual(unauth['status'], '401 Unauthorized')
            for mock in mocks: mock.assert_called_once()


if __name__ == '__main__': unittest.main()
