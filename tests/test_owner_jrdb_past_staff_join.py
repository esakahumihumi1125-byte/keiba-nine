"""Fully synthetic /dky × /dse contracts, no paid API calls or IDs in UI."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_jrdb_past_staff_join import (
    join_jrdb_past_jockey_trainer, PastStaffJoinError,
)

DAY = "20261018"
RACEKEY = "08264b07"


def sample():
    dky, dse = [], []
    for number in range(1, 8):
        horse = f"2328aaa95a{number:02d}"
        result = f"{10000000+number:08d}{DAY}"
        ids = {
            "racedate": DAY, "racekey": RACEKEY,
            "horse_number": f"{number:02d}",
            "horse_id": horse, "resultkey": result,
        }
        dky.append({
            **ids, "bracket_number": str(number),
            "weight_to_carry": "55.0" if number < 4 else "58.0",
            "jockey_cd": "70298" if number < 4 else "12345",
            "trainer_cd": "10485" if number < 4 else "54321",
            "withdrawn_flag": "0",
            "horse_name": "LICENSED-NAME-MUST-NOT-BE-PUBLIC",
        })
        dse.append({
            **ids, "order_of_finish": str(number),
            "trouble_classification": None,
            "confirmed_win_odds": "PRIVATE-ODDS-IGNORE",
        })
    return dky, dse


class JRDBPastStaffJoinTests(unittest.TestCase):
    def test_complete_join_private_without_trusting_publication_or_grades(self):
        dky, dse = sample()
        before = copy.deepcopy((dky, dse))
        joined = join_jrdb_past_jockey_trainer(
            dky, dse, racekey=RACEKEY, racedate=DAY)
        self.assertEqual((dky, dse), before)
        self.assertEqual(joined["racekey"], RACEKEY)
        self.assertEqual(len(joined["horseRows"]), 7)
        self.assertEqual([r["finish"] for r in joined["horseRows"]],
                         list(range(1, 8)))
        first = joined["horseRows"][0]
        self.assertEqual(first["number"], 1)
        self.assertEqual(first["jockeyRef"], "70298")
        self.assertEqual(first["trainerRef"], "10485")
        self.assertEqual(first["carriedKg"], 55.0)
        self.assertFalse(joined["officialJraVerified"])
        self.assertFalse(joined["resultPublicationTimeVerified"])
        self.assertFalse(joined["eligibleForTimeCutScoring"])
        self.assertIsNone(joined["formalJockeyStableGrade"])
        self.assertTrue(joined["includesPrivateProviderIdentifiers"])
        self.assertEqual(joined["sourceReadCount"], 0)
        for forbidden in ("LICENSED-NAME", "PRIVATE-ODDS",
                          "horse_name", "confirmed_win_odds", "API_KEY"):
            self.assertNotIn(forbidden, repr(joined))

    def test_wrong_horse_id_same_number_and_changed_resultkey_fail(self):
        for mutate in (
            lambda a,b: b[0].update(horse_id="aaaaaaaaaaaa"),
            lambda a,b: b[0].update(resultkey="8888888820261018"),
            lambda a,b: b[0].update(horse_number="02"),
            lambda a,b: b[0].update(racekey="05264b07"),
            lambda a,b: a[0].update(racedate="20261019"),
            lambda a,b: a[0].update(jockey_cd="??"),
            lambda a,b: a[0].update(trainer_cd=None),
            lambda a,b: a[0].update(bracket_number="9"),
            lambda a,b: a[0].update(weight_to_carry="not_weight"),
            lambda a,b: a[0].update(withdrawn_flag="1"),
            lambda a,b: b[0].update(trouble_classification="1"),
            lambda a,b: b[0].update(order_of_finish=None),
            lambda a,b: b[0].update(order_of_finish="abc"),
            lambda a,b: b[0].update(order_of_finish="02"),
            lambda a,b: b[0].update(officialVerified=True, horse_id="DIFFERENT123"),
        ):
            a,b=sample();mutate(a,b)
            with self.subTest(mutate=repr(mutate)), self.assertRaises(
                    PastStaffJoinError):
                join_jrdb_past_jockey_trainer(a,b,racekey=RACEKEY,racedate=DAY)

    def test_incomplete_or_duplicated_historical_ensemble_fails(self):
        for mutate in (
            lambda a,b:b.pop(),
            lambda a,b:a.pop(),
            lambda a,b:b.append(copy.deepcopy(b[0])),
            lambda a,b:a.append(copy.deepcopy(a[0])),
            lambda a,b:b[1].update(order_of_finish="1"),
            lambda a,b:b[6].update(order_of_finish="8"),
            lambda a,b:a[1].update(horse_id=a[0]["horse_id"]),
        ):
            a,b=sample();mutate(a,b)
            with self.subTest(mutate=repr(mutate)), self.assertRaises(
                    PastStaffJoinError):
                join_jrdb_past_jockey_trainer(a,b,racekey=RACEKEY,racedate=DAY)

    def test_changed_date_year_invalid_key_and_unknown_race(self):
        dky,dse=sample()
        for key,day in (
            ("05264b07", DAY), ("08254b07", DAY),
            ("08264b00", DAY), ("08264b13", DAY),
            ("08264b07", "20261019"), ("08264b07", "20261318"),
            ("08264b07", "20161018"), ("08264b07", None),
            ("xxxxxxxx", DAY),
        ):
            with self.subTest(key=key,day=day), self.assertRaises(
                    PastStaffJoinError):
                join_jrdb_past_jockey_trainer(
                    dky,dse,racekey=key,racedate=day)

    def test_extra_provider_fields_do_not_become_prediction_features(self):
        dky,dse=sample()
        dky[0].update(jockey_index="999", stable_index="999",
                      jockey_expect_placerate="95", odd=1)
        dse[0].update(confirmed_win_odds="0.1",idm="999")
        report=join_jrdb_past_jockey_trainer(
            dky,dse,racekey=RACEKEY,racedate=DAY)
        self.assertNotIn("jockey_index",repr(report))
        self.assertNotIn("stable_index",repr(report))
        self.assertNotIn("confirmed_win_odds",repr(report))
        self.assertFalse(report["eligibleForTimeCutScoring"])


if __name__ == "__main__":
    unittest.main()
