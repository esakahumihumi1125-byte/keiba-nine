"""Synthetic no-network regression for explicit JRDB /tcy + /tch overlap."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from owner_training_source_crosscheck import crosscheck_training_sources
from jrdb_coverage import CoverageError
from test_jrdb_main_workout_evidence import fixture, DAY
from test_private_service import SETTINGS, call
from private_service import create_app


def sources():
    raw, programme, entries, main = fixture()
    training = [
        {"racekey": "05264b01", "racedate": DAY,
         "horse_number": None, "horse_id": "2328aaa95a05",
         "oikirisisu": 52, "siagarisisu": 48,
         "horse_name": "SECRET-HORSE", "win_odds": 9999},
        {"racekey": "05264b01", "racedate": DAY,
         "horse_number": "02", "horse_id": None,
         "oikirisisu": 49, "siagarisisu": 39},
    ]
    return raw, programme, entries, training, main


class TrainingCrosscheckTests(unittest.TestCase):
    def test_race_level_overlap_and_source_gap_is_read_only(self):
        _, p, e, tcy, tch = sources()
        before = copy.deepcopy((p, e, tcy, tch))
        out = crosscheck_training_sources(p, e, tcy, tch, DAY)
        self.assertEqual((p, e, tcy, tch), before)
        self.assertEqual(out["version"], "owner-training-tcy-tch-crosscheck-1")
        self.assertEqual(out["raceCount"], 2)
        self.assertEqual(out["sourceRequestsRequired"], ["tra", "tky", "tcy", "tch"])
        self.assertEqual(out["summary"]["registered"], 3)
        self.assertEqual(out["summary"]["tcyComplete"], 2)
        self.assertEqual(out["summary"]["tchComplete"], 1)
        self.assertEqual(out["summary"]["bothComplete"], 1)
        self.assertEqual(out["summary"]["tcyOnly"], 1)
        self.assertEqual(out["summary"]["tchOnly"], 0)
        self.assertEqual(out["summary"]["neither"], 1)
        tokyo = next(row for row in out["races"] if row["track"] == "東京")
        self.assertEqual(tokyo["registered"], 2)
        self.assertEqual((tokyo["bothComplete"], tokyo["tcyOnly"],
                          tokyo["tchOnly"], tokyo["neither"]), (1, 1, 0, 0))
        self.assertFalse(tokyo["formalTrainingScore30Ready"])
        for flag in ("rawWorkoutValuesIncluded", "horseIdentifiersIncluded",
                     "oddsUsed", "indexValuesCompared", "jraOfficialVerified",
                     "trainingGradeCalibrated", "formalTrainingScore30Ready",
                     "overallPredictionReady", "bettingReady", "actualPurchase",
                     "changesExistingTickets", "changesExistingReceipts",
                     "changesExistingRoi"):
            self.assertFalse(out[flag])
        for confidential in ("SECRET-HORSE", "2328aaa95a05", "horse_name",
                             "horse_id", "racekey", "win_odds", "52", "48",
                             "12.1", "25.5", "oikirisisu"):
            self.assertNotIn(confidential, repr(out))

    def test_tch_only_when_tcy_finishing_index_is_missing(self):
        _, p, e, tcy, tch = sources()
        del tcy[0]["siagarisisu"]
        out = crosscheck_training_sources(p, e, tcy, tch, DAY)
        self.assertEqual(out["summary"]["bothComplete"], 0)
        self.assertEqual(out["summary"]["tchOnly"], 1)
        self.assertEqual(out["summary"]["tcyOnly"], 1)

    def test_wrong_roster_duplicate_training_and_workout_conflict_rejected(self):
        _, p, e, tcy, tch = sources()
        for corrupt in (
            lambda t, w: t.append(dict(t[0])),
            lambda t, w: t[0].update(horse_number="02"),
            lambda t, w: t[0].update(siagarisisu=float("nan")),
            lambda t, w: w[0].update(horse_number="02"),
            lambda t, w: w[0].update(exercise_date="20261102"),
            lambda t, w: w[0].update(oikirisisu=True),
        ):
            a, b = copy.deepcopy((tcy, tch))
            corrupt(a, b)
            with self.subTest(corrupt=repr(corrupt)), self.assertRaises(CoverageError):
                crosscheck_training_sources(p, e, a, b, DAY)
        with self.assertRaises(CoverageError):
            crosscheck_training_sources(p, e, tcy, tch, "20261130")


class TrainingCrosscheckOwnerEndpointTests(unittest.TestCase):
    def app(self):
        return create_app({**SETTINGS,
                           "JRDB_PRIVATE_ENABLED": "1",
                           "JRDB_API_KEY": "synthetic-jrdb-test",
                           "JRDB_AUTH_KEY": "synthetic-jrdb-user-test"})

    def test_bad_auth_date_and_after_off_do_not_read_provider(self):
        app = self.app()
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:30:00+09:00"),
              patch("private_service.fetch_race_program") as first):
            for query, extra in (
                ("date=20261102", {}),
                ("date=20261101&date=20261101", {}),
                ("date=20261101&token=unknown", {}),
                ("date=20261132", {}),
                ("date=20261101", {"auth": ""}),
                ("date=20261101", {"HTTP_X_KEIBA_REQUEST": ""}),
            ):
                with self.subTest(query=query):
                    result=call(app, "/api/jrdb/training-source-crosscheck",
                                QUERY_STRING=query, **extra)
                    self.assertNotEqual(result["status"], "200 OK")
            first.assert_not_called()
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T19:10:00+09:00"),
              patch("private_service.fetch_race_program") as reader):
            res=call(app, "/api/jrdb/training-source-crosscheck",
                     QUERY_STRING="date=20261101")
            self.assertEqual(res["status"], "409 Conflict")
            reader.assert_not_called()

    def test_exact_four_reads_redacted_and_not_prediction(self):
        raw, _, e, tcy, tch = sources()
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:30:00+09:00"),
              patch("private_service.fetch_race_program", return_value=raw) as tra,
              patch("private_service.fetch_horse_entries", return_value=e) as tky,
              patch("private_service.fetch_training_analysis", return_value=tcy) as a,
              patch("private_service.fetch_main_workout_detail", return_value=tch) as b):
            result=call(self.app(), "/api/jrdb/training-source-crosscheck",
                        QUERY_STRING="date=20261101")
        self.assertEqual(result["status"], "200 OK")
        self.assertIn("no-store",result["headers"]["Cache-Control"])
        data=json.loads(result["body"])
        self.assertEqual((data["raceCount"],data["summary"]["bothComplete"]),(2,1))
        self.assertFalse(data["formalTrainingScore30Ready"])
        for item in (tra,tky,a,b):
            item.assert_called_once_with(DAY)
        for secret in ("2328aaa95a05", "SECRET-HORSE", "synthetic-jrdb-",
                       "win_odds", "oikirisisu", "racekey", "horse_id"):
            self.assertNotIn(secret, result["body"].decode())

    def test_bad_provider_row_aborts_without_sensitive_partial_response(self):
        raw, _, e, tcy, tch = sources()
        tch[0]["horse_number"] = "02"
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:30:00+09:00"),
              patch("private_service.fetch_race_program", return_value=raw),
              patch("private_service.fetch_horse_entries", return_value=e),
              patch("private_service.fetch_training_analysis", return_value=tcy),
              patch("private_service.fetch_main_workout_detail", return_value=tch)):
            res=call(self.app(), "/api/jrdb/training-source-crosscheck",
                     QUERY_STRING="date=20261101")
        self.assertEqual(res["status"], "502 Bad Gateway")
        self.assertNotIn("2328aaa95a05", repr(res))


if __name__ == "__main__":
    unittest.main()
