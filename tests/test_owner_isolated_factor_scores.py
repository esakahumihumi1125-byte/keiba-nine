"""Synthetic no-credentials regressions for per-race optional-factor isolation."""
import copy
import json
import sys
import unittest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from jrdb_coverage import CoverageError
from owner_automatic_factor_scores import automatic_factor_scores
from owner_isolated_factor_scores import isolated_automatic_factor_scores
from test_owner_automatic_factor_scores import fixture, DAY, NOW


def two_races():
    original = fixture()
    p, e, z = copy.deepcopy(original)
    second = dict(p[0], racekey='08265502', track='京都',
                  race=2, post_time='10:30')
    p.append(second)
    for row in original[1]:
        n = int(row['horse_number'])
        e.append({**row, 'racekey': second['racekey'],
                  'horse_id': f'{n+100:012d}',
                  'horse_number': f'{n:02d}'})
    for row in original[2]:
        n = int(row['horse_number'])
        z.append({**row, 'racekey': second['racekey'],
                  'horse_id': f'{n+100:012d}',
                  'horse_number': f'{n:02d}'})
    return p, e, z


class IsolatedFactorTests(unittest.TestCase):
    def model(self, data):
        return isolated_automatic_factor_scores(*data, DAY, now=NOW)

    def test_clean_two_race_outputs_match_original_strict_engine(self):
        data = two_races()
        untouched = copy.deepcopy(data)
        new = self.model(data)
        old = automatic_factor_scores(*data, DAY, now=NOW)
        self.assertEqual(new['races'], old['races'])
        self.assertEqual(new['isolatedHeldRaces'], 0)
        self.assertEqual(new['newProviderRequests'], 0)
        self.assertFalse(new['modelCalibrated'])
        self.assertFalse(new['officialJraVerified'])
        self.assertFalse(new['overallPredictionReady'])
        self.assertEqual(data, untouched)

    def test_corrupted_first_race_preserves_independent_second_race(self):
        data = two_races()
        data[2][0]['race_back_1_racedate'] = '20261121'
        private_row = 'SECRET-PAID-HORSE-NEVER-RETURN'
        data[1][0]['horse_name'] = private_row
        before = copy.deepcopy(data)
        with self.assertRaises(CoverageError):
            automatic_factor_scores(*data, DAY, now=NOW)
        result = self.model(data)
        self.assertEqual(result['isolatedHeldRaces'], 1)
        self.assertEqual(len(result['races']), 2)
        rejected, accepted = result['races']
        self.assertEqual(rejected['status'], 'held')
        self.assertEqual(rejected['reason'], 'source_validation_failed')
        self.assertEqual(rejected['horses'], [])
        self.assertEqual(accepted['status'], 'scored')
        expected = automatic_factor_scores(
            [data[0][1]], data[1][4:], data[2][4:], DAY, now=NOW)
        self.assertEqual(accepted, expected['races'][0])
        self.assertEqual(data, before)
        exported = json.dumps(result, ensure_ascii=False)
        for secret in ('SECRET-PAID-HORSE', 'horse_id',
                       'racekey', '20261121'):
            if secret == '20261121':
                # Race date in public report is intentional, not a paid field.
                continue
            self.assertNotIn(secret, exported)

    def test_bad_optional_row_inside_second_race_keeps_first(self):
        data = two_races()
        data[2][4]['horse_id'] = 'INVALID'
        outcome = self.model(data)
        self.assertEqual(outcome['isolatedHeldRaces'], 1)
        self.assertEqual(outcome['races'][0]['status'], 'scored')
        self.assertEqual(outcome['races'][1]['status'], 'held')
        self.assertEqual(outcome['races'][1]['horses'], [])

    def test_foreign_race_identity_is_never_silently_ignored(self):
        for key in ('99999999', '', None):
            data = two_races()
            data[2][0]['racekey'] = key
            with self.assertRaises(CoverageError):
                self.model(data)
        data = two_races()
        data[0][1]['racekey'] = data[0][0]['racekey']
        with self.assertRaises(CoverageError):
            self.model(data)
        data = two_races()
        data[0][1]['race'] = 1
        data[0][1]['track'] = '東京'
        with self.assertRaises(CoverageError):
            self.model(data)

    def test_post_off_is_held_even_when_source_is_complete(self):
        data = two_races()
        out = isolated_automatic_factor_scores(
            *data, DAY, now=datetime.fromisoformat('2026-11-21T10:00:00+09:00'))
        self.assertEqual(out['races'][0]['status'], 'held')
        self.assertEqual(out['races'][0]['reason'], 'after_start')
        self.assertEqual(out['races'][0]['horses'], [])
        self.assertEqual(out['races'][1]['status'], 'scored')
        self.assertEqual(out['isolatedHeldRaces'], 0)

    def test_bad_clock_does_not_promote_any_race(self):
        with self.assertRaises(CoverageError):
            isolated_automatic_factor_scores(
                *two_races(), DAY, now=datetime(2026, 11, 21, 9))


if __name__ == '__main__':
    unittest.main()
