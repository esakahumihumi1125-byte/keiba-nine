"""Synthetic source and authenticated owner HTTP tests for /tch workout audit."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from jrdb_main_workout_evidence import audit_main_workouts
from jrdb_coverage import CoverageError
from jrdb_program_preview import normalize_program_rows
from test_private_single_readiness_endpoint import source
from private_service import create_app
from test_private_service import SETTINGS, call


DAY = "20261101"


def fixture():
    raw, entries, _, _, _ = source()
    programme = normalize_program_rows(raw, DAY)
    workouts = [
        {
            "racedate": DAY, "racekey": "05264b01", "horse_number": None,
            "horse_id": "2328aaa95a05", "exercise_date": "20261029",
            "oikirisisu": 25.5, "shimai": "12.1",
            "work_kind": "3", "abreast_result": "sample-private",
            "win_odds": 999, "horse_name": "SECRET-HORSE",
        },
        {
            "racedate": DAY, "racekey": "05264b01", "horse_number": "02",
            "horse_id": None, "exercise_date": "20261026",
            "oikirisisu": 0, "shimai": None,
        },
    ]
    return raw, programme, entries, workouts


class MainWorkoutEvidenceTests(unittest.TestCase):
    def test_join_multiple_workouts_without_leaking_raw_times_or_indices(self):
        _, programme, entries, workouts = fixture()
        saved = copy.deepcopy((programme, entries, workouts))
        report = audit_main_workouts(programme, entries, workouts, DAY)
        self.assertEqual((programme, entries, workouts), saved)
        self.assertEqual(report["version"], "owner-main-workout-tch-evidence-1")
        self.assertEqual(report["raceCount"], 2)
        self.assertEqual(report["summary"]["workoutRows"], 2)
        self.assertEqual(report["summary"]["runnersWithWorkout"], 2)
        self.assertEqual(report["summary"]["runnersWithRecentWorkout"], 2)
        self.assertEqual(report["summary"]["runnersWithIndex"], 1)
        self.assertEqual(report["summary"]["runnersWithDatedIndexTime"], 1)
        tokyo = next(x for x in report["races"] if x["track"] == "東京")
        self.assertEqual(tokyo["registered"], 2)
        self.assertEqual(tokyo["sourceWorkoutRows"], 2)
        self.assertEqual(tokyo["runnersWithIndex"], 1)
        self.assertTrue(tokyo["runners"][0]["mainIndexRecorded"])
        self.assertFalse(tokyo["runners"][1]["mainIndexRecorded"])
        self.assertEqual(tokyo["runners"][0]["trainingGrade"], "未評価")
        self.assertIsNone(tokyo["runners"][0]["trainingScore30"])
        kyoto = next(x for x in report["races"] if x["track"] == "京都")
        self.assertEqual(kyoto["sourceWorkoutRows"], 0)
        self.assertEqual(kyoto["runnersWithWorkout"], 0)
        for claim in ("modelCalibrated", "trainingGradeReady",
                      "overallPredictionReady", "officialJraVerified",
                      "bettingReady", "actualPurchase", "oddsUsed"):
            self.assertFalse(report[claim])
        for forbidden in ("2328aaa95a05", "SECRET-HORSE", "sample-private",
                          "25.5", "12.1", "win_odds", "horse_id", "racekey"):
            self.assertNotIn(forbidden, repr(report))

    def test_same_horse_multiple_workouts_is_one_runner(self):
        _, programme, entries, workouts = fixture()
        more = copy.deepcopy(workouts[0])
        more.update(exercise_date="20261024", oikirisisu=11,
                    shimai="11.9")
        report = audit_main_workouts(programme, entries, workouts + [more], DAY)
        self.assertEqual(report["summary"]["workoutRows"], 3)
        self.assertEqual(report["summary"]["runnersWithWorkout"], 2)
        self.assertEqual(report["summary"]["runnersWithIndex"], 1)

    def test_identity_errors_future_dates_and_invalid_indexes_fail_closed(self):
        _, programme, entries, workouts = fixture()
        invalid = [
            [dict(workouts[0], horse_number="02")],
            [dict(workouts[0], racekey="08264b01")],
            [dict(workouts[0], racedate="20261102")],
            [dict(workouts[0], horse_id="not-an-id")],
            [dict(workouts[0], exercise_date="20261102")],
            [dict(workouts[0], exercise_date="20261199")],
            [dict(workouts[0], oikirisisu=True)],
            [dict(workouts[0], oikirisisu=float("nan"))],
            [dict(workouts[0], oikirisisu=2500)],
            [dict(workouts[0], shimai=object())],
            [dict(workouts[0], horse_number="18", horse_id=None)],
        ]
        for rows in invalid:
            with self.subTest(i=invalid.index(rows)), self.assertRaises(CoverageError):
                audit_main_workouts(programme, entries, rows, DAY)
        with self.assertRaises(CoverageError):
            audit_main_workouts(programme, entries, workouts, "20261132")


class MainWorkoutEndpointTests(unittest.TestCase):
    def app(self):
        return create_app({**SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
                           "JRDB_API_KEY": "fake-test-only-key",
                           "JRDB_AUTH_KEY": "fake-test-only-auth"})

    def test_unauthorized_or_wrong_day_causes_zero_paid_reads(self):
        app = self.app()
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:30:00+09:00"),
              patch("private_service.fetch_race_program") as reader):
            cases = [
                ("date=20261102", {}), ("date=20261199", {}),
                ("date=20261101&date=20261101", {}),
                ("date=20261101&token=abc", {}),
                ("date=20261101", {"auth": ""}),
                ("date=20261101", {"HTTP_X_KEIBA_REQUEST": ""}),
            ]
            for query, kw in cases:
                self.assertNotEqual(call(app,
                    "/api/jrdb/main-workout-evidence",
                    QUERY_STRING=query, **kw)["status"], "200 OK")
            reader.assert_not_called()
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T19:00:00+09:00"),
              patch("private_service.fetch_race_program") as reader):
            result=call(app, "/api/jrdb/main-workout-evidence",
                        QUERY_STRING="date=20261101")
            self.assertEqual(result["status"], "409 Conflict")
            reader.assert_not_called()

    def test_opt_in_triplet_is_redacted_and_no_background_fetch(self):
        raw, _, entries, workouts = fixture()
        app = self.app()
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:30:00+09:00"),
              patch("private_service.fetch_race_program", return_value=raw) as a,
              patch("private_service.fetch_horse_entries", return_value=entries) as b,
              patch("private_service.fetch_main_workout_detail",
                    return_value=workouts) as c):
            result = call(app,"/api/jrdb/main-workout-evidence",
                          QUERY_STRING="date=20261101")
        self.assertEqual(result["status"], "200 OK")
        self.assertEqual(json.loads(result["body"])["summary"]["workoutRows"], 2)
        for fetch in (a, b, c):
            fetch.assert_called_once_with(DAY)
        for protected in ("2328aaa95a05", "SECRET-HORSE", "25.5", "12.1",
                          "win_odds", "horse_id", "racekey"):
            self.assertNotIn(protected, result["body"].decode())

    def test_provider_format_error_is_502_without_partial_data(self):
        raw, _, entries, workouts = fixture()
        bad = [dict(workouts[0], exercise_date="20261199")]
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:30:00+09:00"),
              patch("private_service.fetch_race_program",return_value=raw),
              patch("private_service.fetch_horse_entries",return_value=entries),
              patch("private_service.fetch_main_workout_detail",return_value=bad)):
            result=call(self.app(), "/api/jrdb/main-workout-evidence",
                        QUERY_STRING="date=20261101")
        self.assertEqual(result["status"], "502 Bad Gateway")
        self.assertNotIn("20261199", str(result["body"]))


if __name__=="__main__":
    unittest.main()
