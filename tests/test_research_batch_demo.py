"""Owner-only, deterministic full-card sandbox (all inputs are fictitious)."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from research_batch_demo import (
    build_demo_batch, demo_race, render_batch_html, CSS, DEMO_VENUES,
    MAX_RACES, DEMO_DATE,
)
from private_service import create_app
from test_private_service import SETTINGS, call


class SyntheticBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_demo_batch()

    def test_full_card_and_all_three_decisions(self):
        report = self.report
        self.assertEqual(report['version'], 'synthetic-batch-1')
        self.assertEqual(report['recordType'], 'test')
        self.assertTrue(report['sample'])
        self.assertFalse(report['livePredictionEnabled'])
        self.assertFalse(report['publishable'])
        self.assertFalse(report['purchaseEnabled'])
        self.assertEqual(report['date'], '2099-01-01')
        self.assertEqual(report['raceCount'], MAX_RACES)
        self.assertEqual(report['raceCount'], 36)
        counts = report['summary']
        self.assertEqual((counts['simulate'], counts['hold'], counts['skip']),
                         (9, 18, 9))
        for venue in DEMO_VENUES:
            races = [r for r in report['rows'] if r['track'] == venue]
            self.assertEqual([r['race'] for r in races], list(range(1, 13)))

    def test_point_cap_ranking_and_no_duplicate_combos(self):
        hashes = []
        for row in self.report['rows']:
            with self.subTest(track=row['track'],race=row['race']):
                self.assertFalse(row['publishable'])
                self.assertEqual(row['recordType'], 'test')
                self.assertEqual(len(row['ranks']), 8)
                self.assertEqual({r['number'] for r in row['ranks']}, set(range(1, 9)))
                self.assertTrue({r['overall'] for r in row['ranks']} <= {'S','A','B','C','未評価'})
                self.assertEqual(len(row['tickets']), row['points'])
                self.assertLessEqual(row['points'],40)
                self.assertEqual(row['stake'],row['points']*100)
                self.assertEqual(len(set(row['tickets'])), row['points'])
                self.assertTrue(all(len(set(ticket))==3 for ticket in row['tickets']))
                if row['decision'] == 'simulate':
                    self.assertGreater(row['points'],0)
                    self.assertEqual({t[0] for t in row['tickets']},{1,2})
                else:
                    self.assertEqual(row['tickets'], [])
                    self.assertEqual(row['stake'],0)
                hashes.append(row['snapshotSha256'])
        self.assertEqual(len(set(hashes)),MAX_RACES)
        self.assertEqual(sum(r['stake'] for r in self.report['rows']),
                         self.report['summary']['sampleStake'])

    def test_batch_determinism_no_mutation_and_independent_dates(self):
        source = [demo_race(DEMO_VENUES[0],n) for n in range(1,13)]
        prior = copy.deepcopy(source)
        first = build_demo_batch(source)
        second = build_demo_batch(source)
        self.assertEqual(first,second)
        self.assertEqual(source,prior)
        self.assertEqual(first['raceCount'],12)
        self.assertEqual(build_demo_batch(),self.report)

    def test_reject_real_duplicate_malformed_and_post_race_leaks(self):
        base = demo_race(DEMO_VENUES[0], 1)
        invalids = [
            [{**base, 'recordType':'live'}],
            [{**base, 'track':'東京'}],
            [{**base, 'date':'2026-11-07'}],
            [{**base, 'race':13}],
            [{**base, 'race':True}],
            [base,copy.deepcopy(base)],
            [{**base,'outcome':{'finish':[1,2,3]}}],
            [{**base,'horses':base['horses'][:1]}],
            [{**base,'offAt':base['asOf']}],
        ]
        for data in invalids:
            with self.subTest(data=str(data)[:90]), self.assertRaises(ValueError):
                build_demo_batch(data)
        with self.assertRaises(ValueError):
            build_demo_batch([])
        with self.assertRaises(ValueError):
            build_demo_batch([base] * 37)

    def test_no_silent_promotion_or_paid_io(self):
        with patch("research_batch_demo.plan_race", side_effect=ValueError("invalid")):
            with self.assertRaises(ValueError):
                build_demo_batch([demo_race(DEMO_VENUES[0],1)])
        with self.assertRaises(ValueError):
            render_batch_html({**self.report, 'publishable': True})
        html = render_batch_html(self.report)
        self.assertIn('架空の3競馬場×12R＝36R',html)
        self.assertIn('AIの実データ分析',html)
        self.assertIn('組み合わせ一覧',html)
        self.assertIn('架空A競馬場',html)
        self.assertNotIn('<script',html)
        self.assertNotIn('JRDB_API_KEY',html)
        self.assertIn('.rank .S',CSS)
        self.assertIn('.rank .A',CSS)


class PrivateSyntheticBatchRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SETTINGS)

    def test_owner_only_html_and_css_with_no_provider_io(self):
        with patch('private_service.fetch_race_program') as paid, \
             patch('private_service.fetch_horse_entries') as entries:
            page = call(self.app, '/research-batch-demo')
            self.assertEqual(page['status'], '200 OK')
            self.assertIn('text/html',page['headers']['Content-Type'])
            self.assertIn('no-store',page['headers']['Cache-Control'])
            self.assertIn(b'2099',page['body'])
            self.assertIn(b'/research-batch-demo.css',page['body'])
            style = call(self.app, '/research-batch-demo.css')
            self.assertEqual(style['status'], '200 OK')
            self.assertIn('text/css',style['headers']['Content-Type'])
        paid.assert_not_called()
        entries.assert_not_called()

    def test_unauthenticated_page_redirects_and_css_rejected(self):
        page=call(self.app,'/research-batch-demo',auth='')
        self.assertEqual(page['status'],'303 See Other')
        self.assertEqual(page['headers']['Location'],'/login')
        css=call(self.app,'/research-batch-demo.css',auth='')
        self.assertEqual(css['status'],'401 Unauthorized')
        self.assertNotIn(b'synthetic-batch-1',css['body'])

    def test_preview_home_has_discoverable_link(self):
        home = call(self.app,'/')
        self.assertIn(b'/research-batch-demo',home['body'])


if __name__=='__main__':
    unittest.main()
