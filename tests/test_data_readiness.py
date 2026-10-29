import copy
import unittest
from scripts.data_readiness import inventory, valid_record


class InventoryTests(unittest.TestCase):
    def race(self):
        return dict(recordType='live', date='2030-01-02', track='京都', race=1,
                    raceCard=dict(date='2030-01-02', track='京都', race=1, complete=True,
                                  runners=[dict(number=1, name='架空馬', status='active')]), horses=[])

    def test_missing_does_not_disappear(self):
        race = self.race()
        before = copy.deepcopy(race)
        self.assertIn('近走', inventory(race)['horses'][0]['missing'])
        self.assertIn('調教', inventory(race)['horses'][0]['missing'])
        self.assertEqual(before, race)

    def test_real_records_only(self):
        record = dict(date='2030-01-01', source='架空資料', detail='試験用記録')
        self.assertTrue(valid_record(record, '2030-01-02'))
        for change in [dict(date='2030-01-02'), dict(date='2030-02-30'), dict(source=''), dict(detail='')]:
            self.assertFalse(valid_record(record | change, '2030-01-02'))

    def test_duplicate_and_cancelled(self):
        race = self.race()
        race['raceCard']['runners'] *= 2
        self.assertTrue(inventory(race)['issues'])
        race['raceCard']['runners'] = [dict(number=1, status='scratched')]
        self.assertEqual(inventory(race)['horses'], [])

    def test_missing_roster_and_test_data(self):
        report = inventory(dict(recordType='test'))
        self.assertIn('全頭出走表がありません', report['issues'])
        self.assertIn('実データの区分ではありません', report['issues'])

    def test_duplicate_horse_not_counted(self):
        race = self.race()
        race['horses'] = [dict(number=1, name='架空馬')] * 2
        self.assertIn('馬別資料（未登録または重複）', inventory(race)['horses'][0]['missing'])
