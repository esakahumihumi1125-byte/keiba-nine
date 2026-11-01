import unittest
from scripts.jrdb_coverage import CoverageError, audit_race_coverage


def race(key, track, number, count):
    return {
        "racekey": key, "racedate": "20261101", "track": track,
        "race": number, "headcount": count, "post_time": "10:00",
    }


def horse(key, number, **extras):
    return {
        "racekey": key, "racedate": "20261101",
        "horse_number": number, "horse_name": "SECRET-DO-NOT-EXPORT",
        "training_index": "88.8", **extras,
    }


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.programme = [race("05264b01", "東京", 1, 2),
                          race("08264b01", "京都", 1, 3)]
        self.entries = [horse("05264b01", "01"), horse("05264b01", "02"),
                        horse("08264b01", "03")]

    def check(self, programme=None, entries=None):
        return audit_race_coverage(
            self.programme if programme is None else programme,
            self.entries if entries is None else entries, "20261101")

    def test_all_tracks_are_counted_independently(self):
        result = self.check()
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["matchingEntryCounts"], 1)
        self.assertEqual(result["fullyVerifiedRaces"], 0)
        self.assertEqual(result["predictionsReady"], 0)
        self.assertEqual(result["races"][0]["status"], "出走馬データ不足")
        self.assertEqual(result["races"][1]["status"], "件数一致（取消等未照合）")

    def test_private_horse_information_never_leaves_audit(self):
        result = repr(self.check())
        self.assertNotIn("SECRET-DO-NOT-EXPORT", result)
        self.assertNotIn("training_index", result)
        self.assertNotIn("88.8", result)

    def test_all_race_numbers_can_be_represented(self):
        cards = [race("05264b" + str(n).zfill(2), "東京", n, 1)
                 for n in range(1, 13)]
        entries = [horse(r["racekey"], "01") for r in cards]
        result = self.check(cards, entries)
        self.assertEqual(result["raceCount"], 12)
        self.assertEqual(result["matchingEntryCounts"], 12)

    def test_duplicate_entry_is_rejected(self):
        with self.assertRaises(CoverageError):
            self.check(entries=self.entries + [horse("05264b01", "02")])

    def test_another_race_is_rejected(self):
        with self.assertRaises(CoverageError):
            self.check(entries=self.entries + [horse("06264b01", "01")])

    def test_unexpected_horse_number_fails_closed(self):
        for number in ["1", "19", 1, "00", "０１"]:
            with self.subTest(number=number), self.assertRaises(CoverageError):
                self.check(entries=[horse("05264b01", number)])

    def test_missing_expected_count_is_unknown(self):
        programme = [race("05264b01", "東京", 1, None)]
        result = self.check(programme, [horse("05264b01", "01")])
        self.assertEqual(result["races"][0]["status"], "頭数未確認")

    def test_excess_horses_detected(self):
        cards = [race("05264b01", "東京", 1, 1)]
        result = self.check(cards, [horse("05264b01", "01"),
                                    horse("05264b01", "02")])
        self.assertEqual(result["races"][0]["status"], "出走馬データ過多")

    def test_empty_race_day_safe(self):
        result = self.check([], [])
        self.assertEqual(result["raceCount"], 0)

    def test_source_identifiers_must_be_strings(self):
        for key in [None, 22, ["05264b01"], "05264bzz"]:
            with self.subTest(key=key), self.assertRaises(CoverageError):
                self.check(entries=[horse(key, "01")])


if __name__ == "__main__":
    unittest.main()
