import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evaluation_policy import evaluate_race, FACTORS


def assessment(grade='A', win=False):
    return {'grade': grade, 'reason': '架空検証の根拠', 'winSupport': win,
            'evidence': [{'sourceId': 'synthetic', 'reference': 'fixture',
                          'availableAt': '2026-10-26T12:00:00+09:00'}]}


def horse(n, grade='A'):
    return {'number': n, 'assessments': {k: assessment(grade) for k in FACTORS}}


def race(horses=None):
    return {'recordType': 'test', 'asOf': '2026-10-26T20:00:00+09:00',
            'offAt': '2026-10-27T10:00:00+09:00', 'horses': horses or [horse(1), horse(2)]}


class EvaluationTests(unittest.TestCase):
    def test_deterministic_no_mutation(self):
        data = race(); before = copy.deepcopy(data)
        self.assertEqual(evaluate_race(data), evaluate_race(data))
        self.assertEqual(data, before)

    def test_same_grade_same_rank(self):
        result = evaluate_race(race([horse(8), horse(2)]))
        self.assertEqual([h['rank'] for h in result['horses']], [1, 1])
        self.assertTrue(all(h['overall'] == 'A' for h in result['horses']))

    def test_each_missing_core_blocks_overall(self):
        for key in ['training', 'recent', 'course_distance', 'pace', 'ground']:
            with self.subTest(key=key):
                h = horse(1, 'S'); del h['assessments'][key]
                r = evaluate_race(race([h, horse(2)]))
                row = next(x for x in r['horses'] if x['number'] == 1)
                self.assertEqual(row['overall'], '未評価')
                self.assertIsNone(row['score'])
                self.assertEqual(r['reviewState'], 'data_incomplete')

    def test_missing_body_does_not_inflate_score(self):
        h = horse(1, 'S'); del h['assessments']['body_condition']
        r = evaluate_race(race([h, horse(2)]))['horses'][0]
        self.assertEqual(r['coverage'], 98)
        self.assertEqual(r['score'], 2.94)

    def test_future_evidence_unused(self):
        h = horse(1); h['assessments']['training']['evidence'][0]['availableAt'] = '2026-10-27T11:00:00+09:00'
        r = evaluate_race(race([h, horse(2)]))
        self.assertEqual(next(x for x in r['horses'] if x['number'] == 1)['grades']['training'], '未評価')

    def test_no_reason_or_source_is_unknown(self):
        for field in ['reason', 'evidence']:
            h = horse(1); del h['assessments']['recent'][field]
            self.assertEqual(evaluate_race(race([h, horse(2)]))['reviewState'], 'data_incomplete')

    def test_lower_ranked_winner_reconsidered(self):
        horses = [horse(n, 'S') for n in range(1, 5)] + [horse(5)]
        for key in ['course_distance', 'pace']:
            horses[-1]['assessments'][key]['winSupport'] = True
        out = evaluate_race(race(horses))
        self.assertEqual(out['horses'][-1]['rank'], 5)
        self.assertEqual(out['winCandidatesToReview'], [5])
        self.assertEqual(out['first'], [])

    def test_four_candidates_not_silently_cut(self):
        hs = [horse(n) for n in range(1, 5)]
        for h in hs:
            for key in ['recent', 'training']:
                h['assessments'][key]['winSupport'] = True
        out = evaluate_race(race(hs))
        self.assertEqual(out['winCandidatesToReview'], [1, 2, 3, 4])
        self.assertEqual(out['reviewState'], 'too_many_candidates')

    def test_blocking_or_unverified_concern_prevents_candidate(self):
        for concern in [assessment(), {'reason': '根拠未確認'}]:
            h = horse(1)
            for key in ['recent', 'training']:
                h['assessments'][key]['winSupport'] = True
            h['blockingConcerns'] = [concern]
            self.assertNotIn(1, evaluate_race(race([h, horse(2)]))['winCandidatesToReview'])

    def test_no_auto_s_or_candidate_from_absent_data(self):
        out = evaluate_race(race([{'number': 1}, {'number': 2}]))
        self.assertTrue(all(h['overall'] == '未評価' for h in out['horses']))
        self.assertEqual(out['winCandidatesToReview'], [])

    def test_invalid_inputs_rejected(self):
        for change in [{'recordType': 'live'}, {'asOf': '2026-10-27T10:00:00+09:00'},
                       {'asOf': '2026-10-26T12:00:00'}, {'horses': [horse(1), horse(1)]},
                       {'horses': [horse(True), horse(2)]}]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                evaluate_race({**race(), **change})
        for invalid in ['D', 4]:
            h = horse(1); h['assessments']['training']['grade'] = invalid
            with self.assertRaises(ValueError): evaluate_race(race([h, horse(2)]))

    def test_unknown_factor_rejected(self):
        h = horse(1); h['assessments']['odds'] = assessment()
        with self.assertRaises(ValueError): evaluate_race(race([h, horse(2)]))

    def test_always_draft_and_hold(self):
        out = evaluate_race(race([horse(1, 'S'), horse(2, 'C')]))
        self.assertFalse(out['validated']); self.assertFalse(out['publishable'])
        self.assertEqual(out['status'], 'draft'); self.assertEqual(out['bettingDecision'], '保留')


if __name__ == '__main__': unittest.main()
