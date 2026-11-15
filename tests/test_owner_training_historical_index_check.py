"""No-network historical index vs finish audit, route and source contract tests."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_private import _fetch_endpoint, JRDBError
from owner_training_historical_index_check import compare_one_historical_training_day
from private_service import create_app
from test_private_service import SETTINGS, call

DAY = "20261031"
KEY = "05264b01"
OTHER = "08264b01"


def samples():
    before = [
        {"racedate": DAY, "racekey": KEY, "horse_number": f"{n:02d}",
         "horse_id": f"2328aaa95a{n:02d}",
         "horse_name": "LICENSED-HORSE-DO-NOT-RETURN",
         "training_index": str((5 - n) * 20), "win_odds": "999.9"}
        for n in range(1, 5)]
    before += [
        {"racedate": DAY, "racekey": OTHER, "horse_number": f"{n:02d}",
         "horse_id": f"2328bbbb5a{n:02d}",
         "training_index": str(n)}
        for n in range(1, 4)]
    after = [
        {"racedate": row["racedate"], "racekey": row["racekey"],
         "horse_number": row["horse_number"], "horse_id": row["horse_id"],
         "order_of_finish": str(int(row["horse_number"])),
         "confirmed_win_odds": "SECRET-ODDS", "horse_name": "SECRET-FINISH"}
        for row in before
    ]
    return before, after


class RetrospectiveTrainingStudyTests(unittest.TestCase):
    def test_full_roster_one_day_study_never_returns_horse_data(self):
        a, b = samples()
        unchanged = copy.deepcopy((a, b))
        study = compare_one_historical_training_day(a, b, DAY)
        self.assertEqual((a, b), unchanged)
        self.assertEqual(study["raceCount"], 2)
        self.assertEqual(study["summary"]["registered"], 7)
        self.assertEqual(study["summary"]["eligibleRaces"], 1)
        self.assertEqual(study["summary"]["uniqueIndexTopWon"], 1)
        self.assertEqual(study["summary"]["indexFinishConcordantPairs"], 6)
        self.assertEqual(study["summary"]["indexFinishDiscordantPairs"], 0)
        self.assertEqual(study["ineligibleReasons"], {"too_few_runners": 1})
        tokyo = next(x for x in study["races"] if x["track"] == "東京")
        self.assertTrue(tokyo["topIndexWinnerObserved"])
        self.assertEqual(tokyo["registered"], 4)
        for flag in ("prestartFeatureSnapshotVerified", "independentJraVerified",
                     "outOfTimeValidated", "calibrationReady",
                     "formalTrainingScore30Ready", "overallPredictionReady",
                     "bettingReady", "actualPurchase", "oddsUsed",
                     "rawProviderRowsIncluded", "horseNumbersIncluded",
                     "changesExistingRoi"):
            self.assertFalse(study[flag])
        for bad in ("LICENSED-HORSE", "SECRET-FINISH", "SECRET-ODDS",
                    "999.9", "horse_id", "racekey", "80", "60",
                    "2328aaa95a01", "'order_of_finish':", "'training_index':"):
            self.assertNotIn(bad, repr(study))

    def test_partial_or_nonfinish_is_never_counted_as_defeat(self):
        a, b = samples()
        a[0]["training_index"] = None
        r = compare_one_historical_training_day(a, b, DAY)
        self.assertEqual(r["summary"]["eligibleRaces"], 0)
        self.assertEqual(r["ineligibleReasons"]["training_index_missing"], 1)
        a, b = samples()
        b[0]["order_of_finish"] = "取消"
        r = compare_one_historical_training_day(a, b, DAY)
        self.assertEqual(r["summary"]["eligibleRaces"], 0)
        self.assertEqual(r["ineligibleReasons"]["race_result_incomplete"], 1)
        a, b = samples()
        b[0]["order_of_finish"] = None
        r = compare_one_historical_training_day(a, b, DAY)
        self.assertEqual(r["summary"]["uniqueIndexTopWon"], 0)
        a, b = samples()
        a[1]["training_index"] = a[0]["training_index"]
        r = compare_one_historical_training_day(a, b, DAY)
        self.assertEqual(r["summary"]["eligibleRaces"], 0)
        self.assertEqual(r["ineligibleReasons"]["top_training_index_tied"], 1)
        a, b = samples()
        b[0]["order_of_finish"] = "2"
        r = compare_one_historical_training_day(a, b, DAY)
        self.assertEqual(r["ineligibleReasons"]["single_winner_unconfirmed"], 1)

    def test_mismatched_identity_duplicate_or_future_source_fails(self):
        a, b = samples()
        patches = [
            lambda train, finish: train.append(copy.deepcopy(train[0])),
            lambda train, finish: finish.append(copy.deepcopy(finish[0])),
            lambda train, finish: finish[0].update(horse_id="2328aaa95a04"),
            lambda train, finish: finish[0].update(horse_number="18"),
            lambda train, finish: train[0].update(racedate="20261101"),
            lambda train, finish: train[0].update(racekey="01264b01"),
            lambda train, finish: train[0].update(training_index="NaN"),
            lambda train, finish: train[0].update(training_index=True),
            lambda train, finish: train[0].update(training_index=9999),
            lambda train, finish: finish[0].update(order_of_finish=1),
            lambda train, finish: finish[0].update(order_of_finish="\nBAD"),
        ]
        for mutate in patches:
            x, y = copy.deepcopy((a, b))
            mutate(x, y)
            with self.subTest(mutation=repr(mutate)), self.assertRaises(CoverageError):
                compare_one_historical_training_day(x, y, DAY)
        with self.assertRaises(CoverageError):
            compare_one_historical_training_day(a, b, "20261032")

    def test_empty_day_is_not_faked_prediction(self):
        report = compare_one_historical_training_day([], [], DAY)
        self.assertEqual(report["raceCount"], 0)
        self.assertEqual(report["summary"]["eligibleRaces"], 0)
        self.assertFalse(report["formalTrainingScore30Ready"])


class OneDayHistoricalRequestTests(unittest.TestCase):
    def test_rejects_day_ranges_before_reading_credentials(self):
        with patch.dict("os.environ", {"JRDB_PRIVATE_ENABLED": "1",
                                       "JRDB_API_KEY": "", "JRDB_AUTH_KEY": ""}):
            for args in (
                {"start_racedate": DAY, "end_racedate": "20261101"},
                {"start_racedate": "20261032", "end_racedate": "20261032"},
                {"start_racedate": DAY},
                {"racekey": KEY, "start_racedate": DAY},
            ):
                with self.subTest(args=args), self.assertRaises(JRDBError):
                    _fetch_endpoint("dky", args)
            with self.assertRaises(JRDBError):
                _fetch_endpoint("dka", {"start_racedate": DAY,
                                        "end_racedate": DAY})


class HistoricalTrainingServiceTests(unittest.TestCase):
    def app(self, enabled=True):
        return create_app({**SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
                           "KEIBA_HISTORY_ENABLED": "1" if enabled else "0",
                           "JRDB_API_KEY": "TEST-PRIVATE-KEY-NO-LEAK",
                           "JRDB_AUTH_KEY": "TEST-PRIVATE-SECRET-NO-LEAK"})

    def test_no_source_on_auth_or_invalid_day(self):
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-15T10:00:00+09:00"),
              patch("private_service.fetch_one_historical_day_training") as f):
            for query, extra in (
                ("date=20261115", {}), ("date=20261116", {}),
                ("date=20261032", {}), ("date=20200101", {}),
                ("date=20261031&date=20261031", {}),
                ("date=20261031&race=1", {}),
                ("date=20261031", {"auth": ""}),
                ("date=20261031", {"HTTP_X_KEIBA_REQUEST": ""}),
            ):
                with self.subTest(query=query):
                    res = call(self.app(), "/api/jrdb/historical-training-check",
                               QUERY_STRING=query, **extra)
                    self.assertNotEqual(res["status"], "200 OK")
            f.assert_not_called()
            self.assertEqual(call(self.app(False), "/api/jrdb/historical-training-check",
                                  QUERY_STRING="date=20261031")["status"],
                             "503 Service Unavailable")
            f.assert_not_called()

    def test_two_sources_only_and_redacted_aggregate(self):
        a, b = samples()
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-15T10:00:00+09:00"),
              patch("private_service.fetch_one_historical_day_training",
                    return_value=a) as x,
              patch("private_service.fetch_one_historical_day_finishes",
                    return_value=b) as y):
            reply = call(self.app(), "/api/jrdb/historical-training-check",
                         QUERY_STRING="date=20261031")
        self.assertEqual(reply["status"], "200 OK")
        self.assertIn("no-store", reply["headers"]["Cache-Control"])
        x.assert_called_once_with(DAY)
        y.assert_called_once_with(DAY)
        data = json.loads(reply["body"])
        self.assertEqual(data["summary"]["eligibleRaces"], 1)
        self.assertFalse(data["outOfTimeValidated"])
        for secret in ("TEST-PRIVATE-KEY", "TEST-PRIVATE-SECRET",
                       "LICENSED-HORSE", "2328aaa95a01", "SECRET-ODDS",
                       "\"training_index\":", "\"horse_number\":", "\"racekey\":"):
            self.assertNotIn(secret, reply["body"].decode())

    def test_malformed_source_fails_no_partial_result(self):
        a, b = samples()
        b[0]["horse_id"] = "2328aaa95a04"
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-15T10:00:00+09:00"),
              patch("private_service.fetch_one_historical_day_training",
                    return_value=a),
              patch("private_service.fetch_one_historical_day_finishes",
                    return_value=b)):
            reply = call(self.app(), "/api/jrdb/historical-training-check",
                         QUERY_STRING="date=20261031")
        self.assertEqual(reply["status"], "502 Bad Gateway")
        self.assertNotIn("2328aaa95a04", repr(reply))


if __name__ == "__main__":
    unittest.main()
