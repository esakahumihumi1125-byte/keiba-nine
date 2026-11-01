import unittest

from scripts.jrdb_program_preview import (
    ProgrammeFormatError, normalize_program_rows,
)


def sample(**overrides):
    row = {
        "racekey": "05264b11", "racedate": "20261101",
        "racecourse_cd": "05", "post_time": "1555",
        "distance": "2000", "track_type": "1", "headcount": 15,
        "race_name": "架空テストレース",
    }
    row.update(overrides)
    return row


class PrivateProgramPreviewTests(unittest.TestCase):
    def test_only_schedule_information_is_exposed(self):
        raw = sample(api_key="SHOULD-NOT-APPEAR", auth_key="PRIVATE",
                     horse_data="UNLICENSED", runners=[{"name": "Private"}])
        rows = normalize_program_rows([raw], "20261101")
        self.assertEqual(rows, [{
            "racekey": "05264b11", "racedate": "20261101",
            "track": "東京", "race": 11, "race_name": "架空テストレース",
            "post_time": "15:55", "surface": "芝",
            "distance_m": 2000, "headcount": 15,
            "programmeOnly": True, "horsesVerified": False,
            "predictionStatus": "未作成",
        }])
        self.assertNotIn("SHOULD-NOT-APPEAR", repr(rows))
        self.assertNotIn("UNLICENSED", repr(rows))
        self.assertNotIn("Private", repr(rows))

    def test_hexadecimal_holding_day_in_race_key(self):
        rows = normalize_program_rows([sample()], "20261101")
        self.assertEqual(rows[0]["race"], 11)

    def test_missing_optional_values_are_unknown(self):
        rows = normalize_program_rows([sample(
            post_time=None, distance=None, headcount="16",
            track_type=None, race_name=None,
        )], "20261101")
        row = rows[0]
        self.assertIsNone(row["post_time"])
        self.assertIsNone(row["distance_m"])
        self.assertIsNone(row["headcount"])
        self.assertIsNone(row["surface"])
        self.assertIsNone(row["race_name"])

    def test_date_mismatch_fails_closed(self):
        with self.assertRaises(ProgrammeFormatError):
            normalize_program_rows([sample(racedate="20261102")], "20261101")

    def test_bad_race_key_fails_closed(self):
        for key in ["05264B11", "garbage", "05264b00", "05264b13",
                    "11264b11", "05264b0z"]:
            with self.subTest(key=key), self.assertRaises(ProgrammeFormatError):
                normalize_program_rows([sample(racekey=key)], "20261101")

    def test_duplicate_race_is_rejected(self):
        with self.assertRaises(ProgrammeFormatError):
            normalize_program_rows([sample(), sample()], "20261101")

    def test_empty_day_is_valid(self):
        self.assertEqual(normalize_program_rows([], "20261101"), [])

    def test_invalid_dates(self):
        for date in ["20260230", "2026-11-01", "２０２６１１０１"]:
            with self.subTest(date=date), self.assertRaises(ProgrammeFormatError):
                normalize_program_rows([], date)

    def test_response_never_infers_horses_or_predictions(self):
        row = normalize_program_rows([sample()], "20261101")[0]
        self.assertEqual(row["predictionStatus"], "未作成")
        self.assertFalse(row["horsesVerified"])


if __name__ == "__main__":
    unittest.main()
