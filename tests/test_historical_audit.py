import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from historical_audit import audit, REQUIRED


def sample():
    return {'recordType': 'historical', 'raceId': 'unit-example',
            'offAt': '2025-10-26T15:40:00+09:00', 'asOf': '2025-10-26T15:30:00+09:00',
            'declaredNumbers': [1, 2, 3], 'evidence': []}


def evidence():
    return {'kind': 'workouts', 'horseNumber': 1, 'source': 'unit test',
            'reference': 'fixture', 'detail': 'synthetic test evidence', 'stage': 'pre_race',
            'availableAt': '2025-10-25T09:00:00+09:00', 'retrievedAt': '2026-10-28T09:00:00+09:00'}


class AuditTests(unittest.TestCase):
    def test_missing_does_not_become_a_loss(self):
        r = audit(sample())
        self.assertEqual(len(r['missingByHorse']), 3)
        self.assertIsNone(r['hit']); self.assertIsNone(r['roi'])
        self.assertFalse(r['publishable'])

    def test_result_cannot_supply_prediction_evidence(self):
        r = sample(); e = evidence(); e['kind'] = 'result'; r['evidence'] = [e]
        self.assertEqual(audit(r)['acceptedEvidence'], 0)

    def test_postrace_page_rejected_even_with_backdated_timestamp(self):
        r = sample(); e = evidence(); e['stage'] = 'post_race'; r['evidence'] = [e]
        self.assertEqual(audit(r)['acceptedEvidence'], 0)

    def test_future_and_unknown_availability_rejected(self):
        for value in (None, '2026-10-28T08:00:00+09:00', '2025-10-25T08:00:00'):
            r = sample(); e = evidence(); e['availableAt'] = value; r['evidence'] = [e]
            self.assertEqual(audit(r)['acceptedEvidence'], 0)

    def test_complete_input_still_does_not_claim_prediction(self):
        r = sample(); r['evidence'] = [dict(evidence(), horseNumber=n, kind=k) for n in (1, 2, 3) for k in REQUIRED]
        before = copy.deepcopy(r); out = audit(r)
        self.assertTrue(out['inputComplete']); self.assertEqual(r, before)
        self.assertEqual(out['predictionStatus'], 'not_generated')

    def test_duplicate_evidence_does_not_cover_other_fields(self):
        r = sample(); r['evidence'] = [evidence()] * 20
        self.assertIn('recentRuns', audit(r)['missingByHorse']['1'])

    def test_invalid_field_and_cutoff(self):
        for changes in ({'declaredNumbers': [1, 1, 3]}, {'declaredNumbers': [True, 2, 3]}, {'asOf': '2025-10-26T15:40:00+09:00'}):
            with self.assertRaises(ValueError): audit(dict(sample(), **changes))

    def test_result_identity_payout_and_finish(self):
        r = sample(); r['result'] = {'raceId': 'unit-example', 'finish': [1, 2, 3], 'trifectaPayout': 1000, 'source': 'fixture', 'retrievedAt': '2026-10-28T09:00:00+09:00'}
        self.assertEqual(audit(r)['resultStatus'], 'recorded_not_independently_verified')
        for changes in ({'raceId': 'wrong'}, {'finish': [1, 1, 3]}, {'trifectaPayout': True}, {'deadHeat': True}):
            bad = copy.deepcopy(r); bad['result'].update(changes)
            with self.assertRaises(ValueError): audit(bad)


if __name__ == '__main__': unittest.main()
