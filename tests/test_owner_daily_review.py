"""Checks that a private review remains provisional and internally consistent."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from owner_daily_review_snapshot import decode_review, ReviewError, SCHEMA
from owner_daily_review_ui import HTML, JS


class DailyReviewTests(unittest.TestCase):
    def sample(self):
        return {'schema': SCHEMA, 'sourceKind': 'owner-retrospective-provisional',
                'actualPurchase': False, 'jraAllVerified': False, 'complete': False,
                'date': '2026-11-07', 'racesReviewed': 3,
                'unit': 100, 'pointsPerRace': 30,
                'scopeNote': '3レースの仮想収支、正式照合は未完了。',
                'venues': [
                    dict(name='東京',racesReviewed=1,firstCandidateHits=1,
                         secondCandidateHits=1,trifectaHits=1,payout=1500),
                    dict(name='京都',racesReviewed=1,firstCandidateHits=0,
                         secondCandidateHits=0,trifectaHits=0,payout=0),
                    dict(name='福島',racesReviewed=1,firstCandidateHits=0,
                         secondCandidateHits=0,trifectaHits=0,payout=0)],
                'hits': [dict(track='東京',race=1,combination=[5,10,7],payout=1500)],
                'strong': dict(races=1,hits=1,payout=1500),
                'findings': ['1着候補を再評価する。', '2着の適性を見直す。']}

    def test_valid_data(self):
        result=decode_review(json.dumps(self.sample(),ensure_ascii=False))
        self.assertEqual(len(result['hits']),1)
        self.assertFalse(result['actualPurchase'])
        self.assertFalse(result['complete'])

    def test_rejects_unfounded_claims_and_inconsistent_totals(self):
        for key,value in [('actualPurchase',True),('complete',True),
                          ('jraAllVerified',True),('racesReviewed',4)]:
            with self.subTest(key=key):
                bad=self.sample()
                bad[key]=value
                with self.assertRaises(ReviewError):
                    decode_review(json.dumps(bad,ensure_ascii=False))

    def test_generic_page_keeps_real_records_separate(self):
        self.assertIn('/api/owner-daily-review',JS)
        self.assertNotIn('localStorage',JS)
        self.assertIn('実際の購入履歴',HTML)

if __name__ == '__main__':
    unittest.main()
