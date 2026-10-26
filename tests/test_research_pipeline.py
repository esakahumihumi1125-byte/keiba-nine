import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluation_policy import FACTORS
from research_planner import plan_race
from research_backtest import backtest


def sample(race_id='fixture-1', date='2026-10-20', number=1):
    hs = []
    for n in range(1, 9):
        grade = 'S' if n <= 2 else 'A' if n <= 4 else 'B'
        hs.append({'number': n, 'assessments': {k: {
            'grade': grade, 'winSupport': n <= 2 and k in ('training', 'pace'),
            'reason': '架空検証用', 'evidence': [{'sourceId': 'synthetic', 'reference': 'fixture',
            'availableAt': date+'T08:00:00+09:00'}]} for k in FACTORS}})
    return {'raceId': race_id, 'recordType': 'test', 'date': date, 'track': '架空競馬場', 'race': number,
            'asOf': date+'T09:00:00+09:00', 'offAt': date+'T10:00:00+09:00', 'horses': hs}


def outcome(race, finish=None, payout=8000):
    return {'recordType': 'test', 'status': 'final', 'availableAt': race['date']+'T10:10:00+09:00',
            'finish': finish or plan_race(race)['tri'][0], 'trifectaPayout': payout}


class PlannerTests(unittest.TestCase):
    def test_candidates_and_cap(self):
        p = plan_race(sample())
        self.assertEqual(p['researchDecision'], 'simulate')
        self.assertEqual(p['first'], [1, 2])
        self.assertTrue(0 < p['points'] <= 40)
        self.assertEqual(p['stake'], p['points'] * 100)
        self.assertEqual(len(set(map(tuple, p['tri']))), p['points'])
        self.assertTrue(all(len(set(t)) == 3 for t in p['tri']))
        self.assertEqual(set(t[0] for t in p['tri']), {1, 2})

    def test_no_filling_up_to_target(self):
        r = sample(); r['horses'] = r['horses'][:3]
        self.assertLess(plan_race(r)['points'], 30)

    def test_missing_horse_evaluation_holds_entire_race(self):
        r = sample(); r['horses'][-1]['assessments'].pop('recent')
        self.assertEqual(plan_race(r)['researchDecision'], 'hold')
        self.assertEqual(plan_race(r)['tri'], [])

    def test_four_winners_not_pruned(self):
        r = sample()
        for h in r['horses'][:4]:
            for k in ('recent', 'training'): h['assessments'][k]['winSupport'] = True
        self.assertEqual(plan_race(r)['researchDecision'], 'hold')

    def test_weak_single_not_fixed(self):
        r = sample()
        for a in r['horses'][1]['assessments'].values(): a['winSupport'] = False
        self.assertEqual(plan_race(r)['researchDecision'], 'hold')

    def test_strong_single_requires_support_and_margin(self):
        r = sample()
        for a in r['horses'][1]['assessments'].values():
            a['winSupport'] = False; a['grade'] = 'A'
        r['horses'][0]['assessments']['recent']['winSupport'] = True
        self.assertEqual(plan_race(r)['first'], [1])

    def test_no_supported_winner_skips(self):
        r = sample()
        for h in r['horses']:
            for a in h['assessments'].values(): a['winSupport'] = False
        self.assertEqual(plan_race(r)['researchDecision'], 'skip')

    def test_tie_is_not_broken_by_horse_number(self):
        r = sample()
        for h in r['horses']:
            for a in h['assessments'].values(): a['grade'] = 'A'
        self.assertEqual(plan_race(r)['researchDecision'], 'hold')

    def test_no_mutation_or_live_predictions(self):
        r = sample(); before = copy.deepcopy(r); p = plan_race(r)
        self.assertEqual(r, before); self.assertFalse(p['publishable'])
        self.assertFalse(p['validated']); self.assertEqual(p['status'], 'draft')
        with self.assertRaises(ValueError): plan_race({**r, 'recordType': 'live'})


class BacktestTests(unittest.TestCase):
    split = '2026-10-21T00:00:00+09:00'

    def test_partition_sorted_and_exact_payout(self):
        a, b = sample(), sample('fixture-2', '2026-10-22')
        report = backtest([b, a], {a['raceId']: outcome(a), b['raceId']: outcome(b, [8, 7, 6])}, self.split)
        self.assertEqual([r['raceId'] for r in report['rows']], ['fixture-1', 'fixture-2'])
        self.assertEqual(report['development']['hits'], 1)
        self.assertEqual(report['validation']['hits'], 0)
        self.assertEqual(report['summary']['stake'], plan_race(a)['stake'] * 2)
        self.assertEqual(report['summary']['returned'], 8000)
        self.assertEqual(report['summary']['maxDrawdown'], plan_race(b)['stake'])

    def test_results_do_not_change_predictions(self):
        r = sample()
        hit = backtest([r], {r['raceId']: outcome(r)}, self.split)
        miss = backtest([r], {r['raceId']: outcome(r, [8, 7, 6], 99999)}, self.split)
        self.assertEqual(hit['rows'][0]['predictionHash'], miss['rows'][0]['predictionHash'])
        self.assertEqual(hit['rows'][0]['plan'], miss['rows'][0]['plan'])

    def test_pending_is_not_a_loss(self):
        r = sample(); summary = backtest([r], {}, self.split)['summary']
        self.assertEqual(summary['pendingStake'], plan_race(r)['stake'])
        self.assertEqual(summary['stake'], 0); self.assertEqual(summary['net'], 0)
        self.assertIsNone(summary['roi'])

    def test_cancelled_is_refund_not_hit(self):
        r = sample(); o = {**outcome(r), 'status': 'cancelled'}
        summary = backtest([r], {r['raceId']: o}, self.split)['summary']
        self.assertEqual(summary['refundedStake'], plan_race(r)['stake'])
        self.assertEqual(summary['hits'], 0); self.assertEqual(summary['stake'], 0)

    def test_missing_data_not_counted_as_bet(self):
        r = sample(); r['horses'][0]['assessments'] = {}
        summary = backtest([r], {}, self.split)['summary']
        self.assertEqual(summary['held'], 1); self.assertEqual(summary['pendingStake'], 0)

    def test_duplicate_races_and_unknown_results_rejected(self):
        r = sample()
        for rs, outcomes in [([r, r], {}), ([r, {**r, 'raceId': 'different-id'}], {}), ([r], {'unknown': {}})]:
            with self.assertRaises(ValueError): backtest(rs, outcomes, self.split)

    def test_invalid_results_rejected(self):
        r = sample()
        for change in [{'trifectaPayout': -1}, {'trifectaPayout': True}, {'trifectaPayout': 1.5},
                       {'finish': [1, 1, 2]}, {'finish': [1, 2, 18]}, {'deadHeat': True},
                       {'excludedNumbers': [8]}, {'recordType': 'live'},
                       {'availableAt': r['asOf']}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                backtest([r], {r['raceId']: {**outcome(r), **change}}, self.split)

    def test_crossing_partition_rejected(self):
        r = sample()
        with self.assertRaises(ValueError): backtest([r], {}, r['date']+'T09:30:00+09:00')

    def test_losing_streak(self):
        races = [sample('r'+str(n), number=n) for n in range(1, 4)]
        outcomes = {r['raceId']: outcome(r, [8, 7, 6]) for r in races}
        summary = backtest(races, outcomes, self.split)['summary']
        self.assertEqual(summary['maxConsecutiveLosingRaces'], 3)
        self.assertEqual(summary['maxDrawdown'], summary['stake'])


if __name__ == '__main__': unittest.main()
