"""Whole-day eight-slot source-material coverage, synthetic-only and redacted."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_private_single_readiness_endpoint import source
from test_private_service import call
from test_jrdb_day_pipeline import enabled_app
from jrdb_day_pipeline import inspect_day
from jrdb_day_materials_progress import summarize_day_materials
from jrdb_program_preview import normalize_program_rows
from jrdb_coverage import CoverageError


def fixture():
    raw, entries, training, recent, going = source()
    entries[0].update(sire_name="PRIVATE-SIRE", mare_sire_name="PRIVATE-MATERNAL",
                      bracket_number="1", weight_to_carry="56.0",
                      jockey_name="PRIVATE-JOCKEY", trainer_name="PRIVATE-TRAINER",
                      jockey_cd="00001", trainer_cd="00002", bodytype="1")
    return raw, entries, training, recent, going


def analyze():
    raw, entries, training, recent, going = fixture()
    programme = normalize_program_rows(raw, "20261101")
    day = inspect_day(programme, entries, training, recent, going, "20261101")
    return programme, entries, training, recent, going, day


class DayMaterialProgressTests(unittest.TestCase):
    def test_eight_source_slots_and_two_missing_history_slots(self):
        p, entries, training, recent, going, day = analyze()
        original = copy.deepcopy((p, entries, training, recent, going, day))
        result = summarize_day_materials(
            p, entries, training, recent, "20261101", day)
        self.assertEqual(result["version"], "private-eight-materials-1")
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["verifiedOverallFactors"], 0)
        self.assertFalse(result["realPredictionReady"])
        self.assertFalse(result["purchaseReady"])
        self.assertFalse(result["rawHorseRecordsIncluded"])
        self.assertEqual(len(result["mappedSourceSlots"]), 8)
        self.assertEqual(set(result["unmappedHistorySlots"]), {
            "course_distance", "ground"})
        tokyo = next(r for r in result["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["observedSourceSlots"], 8)
        self.assertEqual(tokyo["unmappedHistorySlots"], 2)
        self.assertEqual(tokyo["unverifiedFactorGrades"], 10)
        self.assertEqual(tokyo["provisionalFactorsOnly"], 2)
        self.assertEqual(tokyo["registered"], 2)
        self.assertEqual(tokyo["counts"]["pedigreeParentsRecorded"], 1)
        self.assertEqual(tokyo["counts"]["drawAndAssignedWeightRecorded"], 1)
        self.assertEqual(tokyo["counts"]["jockeyTrainerNamesRecorded"], 1)
        self.assertEqual(tokyo["counts"]["conformationCodeRecorded"], 1)
        self.assertEqual(tokyo["counts"]["lastRaceDateRecorded"], 1)
        self.assertEqual(result["summary"]["totalRegistered"], 3)
        self.assertEqual((p, entries, training, recent, going, day), original)
        text = json.dumps(result, ensure_ascii=False)
        for forbidden in ("racekey", "horse_id", "horse_number", "PRIVATE-SIRE",
                          "PRIVATE-JOCKEY", "oikirisisu", "win_odds",
                          "2328aaa95a05"):
            self.assertNotIn(forbidden, text)

    def test_missing_observation_is_not_bad_grade_or_negative_assessment(self):
        p, entries, training, recent, _, day = analyze()
        result = summarize_day_materials(p, entries, training, recent,
                                         "20261101", day)
        kyoto = next(r for r in result["races"] if r["track"] == "京都")
        self.assertEqual(kyoto["registered"], 1)
        self.assertEqual(kyoto["counts"]["pedigreeParentsRecorded"], 0)
        self.assertEqual(kyoto["counts"]["jockeyTrainerNamesRecorded"], 0)
        self.assertFalse(kyoto["realPredictionReady"])
        self.assertFalse(kyoto["overallRankReady"])
        self.assertEqual(kyoto["unverifiedFactorGrades"], 10)

    def test_reject_wrong_date_unsafe_flags_and_ambiguous_entries(self):
        p, entries, training, recent, _, day = analyze()
        bad = copy.deepcopy(day)
        bad["date"] = "20261102"
        with self.assertRaises(CoverageError):
            summarize_day_materials(p, entries, training, recent, "20261101", bad)
        bad = copy.deepcopy(day)
        bad["races"][0]["ticketReady"] = True
        with self.assertRaises(CoverageError):
            summarize_day_materials(p, entries, training, recent, "20261101", bad)
        bad = copy.deepcopy(day)
        bad["races"].append(copy.deepcopy(bad["races"][0]))
        bad["raceCount"] += 1
        with self.assertRaises(CoverageError):
            summarize_day_materials(p, entries, training, recent, "20261101", bad)
        altered = copy.deepcopy(entries)
        altered[0]["bracket_number"] = "9"
        with self.assertRaises(CoverageError):
            summarize_day_materials(p, altered, training, recent, "20261101", day)

    def test_no_additional_paid_calls_in_full_day_route(self):
        raw, entries, training, recent, going = fixture()
        app = enabled_app()
        with (patch("private_service.fetch_race_program", return_value=raw) as a,
              patch("private_service.fetch_horse_entries", return_value=entries) as b,
              patch("private_service.fetch_training_analysis", return_value=training) as c,
              patch("private_service.fetch_recent_runs", return_value=recent) as d,
              patch("private_service.fetch_venue_conditions", return_value=going) as e,
              patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:40:00+09:00")):
            response = call(app, "/api/jrdb/day-pipeline", QUERY_STRING="date=20261101")
        self.assertEqual(response["status"], "200 OK")
        data = json.loads(response["body"])
        self.assertEqual(data["sourceMaterials"]["raceCount"], 2)
        self.assertEqual(data["sourceMaterials"]["summary"]["pedigreePresent"], 1)
        self.assertFalse(data["sourceMaterials"]["realPredictionReady"])
        self.assertFalse(data["purchaseReady"])
        for provider in (a, b, c, d, e):
            provider.assert_called_once_with("20261101")
        text = json.dumps(data, ensure_ascii=False)
        for forbidden in ("racekey", "horse_id", "horse_number",
                          "PRIVATE-SIRE", "PRIVATE-JOCKEY",
                          "2328aaa95a05"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
