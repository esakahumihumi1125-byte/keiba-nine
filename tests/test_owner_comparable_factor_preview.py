import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from owner_comparable_factor_preview import preview_comparable_factor_holds
from jrdb_coverage import CoverageError

DAY = '20261121'
NOW = datetime.fromisoformat('2026-11-21T09:00:00+09:00')
BASE_WEIGHTS = {'course_distance': 17, 'pace': 17, 'ground': 12,
                'jockey_stable': 10, 'rotation': 1}


def fixture():
    grades = ('S', 'S', 'A', 'A', 'B', 'B', 'C', 'C')
    runners = [{'number': n, 'training': grades[n - 1], 'recent': '未評価'}
               for n in range(1, 9)]
    def slot(weight, points):
        if points is None:
            return {'weight': weight, 'points': None, 'score': None,
                    'grade': '未評価', 'reason': 'missing'}
        score = round(points * 100 / weight, 4)
        return {'weight': weight, 'points': round(score * weight / 100, 4),
                'score': score, 'grade': ('S' if score >= 85 else 'A' if score >= 70
                                         else 'B' if score >= 55 else 'C'),
                'reason': 'research'}
    horses = []
    for n in range(1, 9):
        horses.append({'number': n, 'factors': {
            'course_distance': slot(17, 17 - n),
            'pace': slot(17, 17 - n),
            'ground': slot(12, None),
            'jockey_stable': slot(10, 10 - n / 2),
            'rotation': slot(1, .8),
        }})
    report = {
        'version': 'jrdb-owner-auto-draft-1', 'date': DAY, 'raceCount': 1,
        'researchOnly': True, 'privateOwnerOnly': True,
        'officialJraVerified': False, 'overallPredictionReady': False,
        'bettingReady': False, 'autoPurchase': False,
        'draftCount': 0, 'holdCount': 1,
        'races': [{
            'track': '東京', 'race': 1, 'postTime': '11:00',
            'horseCount': 8, 'status': 'hold', 'reason': 'missing_factors',
            'runners': runners, 'first': [], 'second': [], 'third': [],
            'tickets': [], 'points': 0,
        }]
    }
    auto = {
        'version': 'owner-automatic-factor-scores-3',
        'date': DAY, 'factorKeys': ['pace', 'jockey_stable', 'rotation',
                                   'course_distance', 'ground'],
        'maximumPoints': 57, 'modelCalibrated': False,
        'officialJraVerified': False, 'overallPredictionReady': False,
        'newProviderRequests': 0,
        'races': [{'track': '東京', 'race': 1, 'postTime': '11:00',
                   'status': 'scored', 'reason': None, 'horses': horses}]
    }
    return report, auto


class ComparableResearchTests(unittest.TestCase):
    def run_model(self, report=None, automatic=None, now=NOW):
        if report is None or automatic is None:
            p, a = fixture()
            report = p if report is None else report
            automatic = a if automatic is None else automatic
        return preview_comparable_factor_holds(report, automatic, DAY, now=now)

    def test_missing_recent_excluded_globally_with_stable_formation(self):
        original, automatic = fixture()
        untouched = copy.deepcopy((original, automatic))
        result = self.run_model(original, automatic)
        self.assertEqual(result['unsignedReferenceCount'], 1)
        item = result['races'][0]
        self.assertEqual(item['comparedWeight'], 75)
        self.assertEqual(item['excludedKeys'], ['recent', 'ground'])
        self.assertEqual(item['comparedKeys'],
                         ['training', 'course_distance', 'pace', 'jockey_stable', 'rotation'])
        self.assertEqual(item['first'], [1, 2])
        self.assertTrue(30 <= item['points'] <= 40)
        self.assertEqual(item['points'],
                         len(item['first']) * (len(item['second'])-1) *
                         (len(item['third'])-2))
        self.assertFalse(item['bettingReady'])
        self.assertFalse(result['officialJraVerified'])
        self.assertEqual(result['newProviderRequests'], 0)
        self.assertEqual(result['ticketsIssued'], 0)
        self.assertEqual((original, automatic), untouched)

    def test_incomplete_core_sources_never_imputed(self):
        for adjustment in ('missing_training', 'missing_pace', 'missing_staff',
                           'unknown_score', 'conflict_roster'):
            report, automatic = fixture()
            if adjustment == 'missing_training':
                report['races'][0]['runners'][0]['training'] = '未評価'
            elif adjustment == 'missing_pace':
                automatic['races'][0]['horses'][0]['factors']['pace'].update(
                    points=None, score=None, grade='未評価')
            elif adjustment == 'missing_staff':
                automatic['races'][0]['horses'][0]['factors']['jockey_stable'].update(
                    points=None, score=None, grade='未評価')
            elif adjustment == 'unknown_score':
                automatic['races'][0]['horses'][0]['factors']['pace']['points'] = float('nan')
            elif adjustment == 'conflict_roster':
                automatic['races'][0]['horses'][0]['number'] = 13
            self.assertEqual(self.run_model(report, automatic)['unsignedReferenceCount'], 0,
                             adjustment)

    def test_gate_prestart_held_and_unverified(self):
        for change in ('late', 'signed', 'withdrawal', 'already_draft',
                       'report_date', 'auto_date'):
            report, automatic = fixture()
            now = NOW
            if change == 'late': now = datetime.fromisoformat('2026-11-21T11:00:00+09:00')
            if change == 'signed': report['officialJraVerified'] = True
            if change == 'withdrawal': report['races'][0]['reason'] = 'provider_withdrawal'
            if change == 'already_draft': report['races'][0]['status'] = 'provisional_draft'
            if change == 'report_date': report['date'] = '20261122'
            if change == 'auto_date': automatic['date'] = '20261122'
            if change in ('signed', 'report_date', 'auto_date'):
                with self.assertRaises(CoverageError):
                    self.run_model(report, automatic, now)
            else:
                self.assertEqual(self.run_model(report, automatic, now)['unsignedReferenceCount'], 0)

    def test_no_number_based_tie_break_and_low_coverage(self):
        report, automatic = fixture()
        # Equal total scores across the whole field cannot be split merely
        # by the lower horse number.
        for horse in report['races'][0]['runners']:
            horse['training'] = 'A'
        for horse in automatic['races'][0]['horses']:
            for key, point in [('course_distance', 10), ('pace', 10), ('jockey_stable', 6)]:
                v = horse['factors'][key]
                v['points'] = point
                v['score'] = round(point * 100 / v['weight'], 4)
        self.assertEqual(self.run_model(report, automatic)['unsignedReferenceCount'], 0)

    def test_recent_when_all_known_changes_comparison_weight_but_not_existing_draft(self):
        report, automatic = fixture()
        for horse in report['races'][0]['runners']:
            horse['recent'] = 'A'
        result = self.run_model(report, automatic)
        self.assertEqual(result['races'][0]['comparedWeight'], 78)
        self.assertEqual(report['races'][0]['tickets'], [])


if __name__ == '__main__':
    unittest.main()
