"""One RACE+RCVN stream yields multiple strictly private prestart racecards."""
import json
import os
import sqlite3
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_jvdata_ra_se_candidate import replace, DAY
from test_windows_jvlink_day_history_preview import FakeJv, sources, PRESTART, JST
from windows_jvlink_day_history_preview import (
    read_local_day_history, save_private_day_local, JvLocalCheckError,
    local_workout_connections, local_html,
)


def first_card():
    return [replace(replace(row, 697, 701, "1800"), 705, 707, "17")
            if row[:3] == b"RA2" else row for row in sources()["RACE"]]


def second_card():
    result = []
    for row in sources()["RACE"]:
        if row[:3] == b"RA2":
            result.append(replace(replace(replace(replace(
                row, 25, 27, "02"), 873, 877, "1040"),
                697, 701, "1800"), 705, 707, "17"))
        else:
            result.append(replace(row, 25, 27, "02"))
    return result


def read(jv, **kwargs):
    with patch("windows_jvlink_day_history_preview.validate_day",
               return_value=DAY):
        return read_local_day_history(
            DAY, jv_factory=lambda: jv, captured_at=PRESTART,
            flat_only=True, all_flat_races=True, **kwargs,
        )


class AllFlatHistoryTests(unittest.TestCase):
    def test_all_flat_contains_two_races_from_two_provider_reads(self):
        jv = FakeJv({
            "RACE": [*first_card(), *second_card()],
            "RCVN": sources()["RCVN"],
        })
        diagnostic = {}
        output = read(jv, diagnostics=diagnostic)
        self.assertEqual(output["raceCount"], 2)
        self.assertEqual([(r["track"], r["race"]) for r in output["races"]],
                         [("東京", 1), ("東京", 2)])
        self.assertEqual([args[0] for args in jv.opens], ["RACE", "RCVN"])
        self.assertEqual(jv.closes, 2)
        self.assertEqual(diagnostic["prestartFlatRaceCount"], 2)
        self.assertEqual(diagnostic["racesWithObservedPriorRows"], 2)
        for flag in ("formalTenFactorReady", "productionPredictionReady",
                     "officialStarterListVerified", "bettingReady"):
            self.assertIs(output[flag], False)
        self.assertNotIn("1000000001", repr(output))
        self.assertNotIn("PRIVATE_FILENAME", repr(output))

    def test_saved_workout_archives_read_only_and_no_additional_provider_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/"ARC-RACE-private"/"licensed-history"
            folder.mkdir(parents=True)
            with patch.dict(os.environ, {"LOCALAPPDATA":tmp}):
                with self.assertRaisesRegex(JvLocalCheckError, "DAY_WORKOUT_ARCHIVE_MISSING_SLOP"):
                    with local_workout_connections():
                        self.fail("missing archive accepted")
                for spec in ("SLOP","WOOD"):
                    path = folder/("jvdata-2026-"+spec.lower()+".sqlite3")
                    conn = sqlite3.connect(path)
                    conn.execute("CREATE TABLE manifest(key,value)")
                    conn.executemany("INSERT INTO manifest VALUES (?,?)", [
                        ("schema","arc-race-workout-1"),("dataspec",spec),
                        ("stream_completed","yes")])
                    conn.execute("CREATE TABLE records(digest,workout_day,workout_key,created_day,category,raw)")
                    conn.commit()
                    conn.close()
                jv = FakeJv({"RACE":first_card(),"RCVN":sources()["RCVN"]})
                with local_workout_connections() as connections:
                    with self.assertRaises(sqlite3.OperationalError):
                        connections["SLOP"].execute("DELETE FROM manifest")
                    result = read(jv, workout_connections=connections)
                self.assertEqual([args[0] for args in jv.opens],["RACE","RCVN"])
                coverage = result["races"][0]["workoutCoverage"]
                self.assertEqual(len(coverage["byNumber"]),4)
                self.assertEqual(coverage["byNumber"][0]["bySpec"]["SLOP"]["observedWorkouts"],0)
                self.assertFalse(coverage["formalTrainingGradeReady"])
                self.assertIn("調教資料の照合件数",local_html(result))
                self.assertNotIn("1000000001",repr(result))
                self.assertFalse(result["formalTenFactorReady"])

    def test_integrated_evidence_table_uses_ungraded_observations(self):
        report = read(FakeJv({"RACE":first_card(),"RCVN":sources()["RCVN"]}))
        race = report["races"][0]
        self.assertIn("重点3項目の資料一覧",local_html(report))
        self.assertIn("坂路 未照合",local_html(report))
        self.assertIn("過去4角の位置傾向",local_html(report))
        race["workoutCoverage"] = {
            "formalTrainingGradeReady":False,"researchOnly":True,
            "byNumber":[{"number":n,"bySpec":{"SLOP":{"observedWorkouts":2},
                                              "WOOD":{"observedWorkouts":0}}}
                        for n in range(1,5)],
        }
        rendered = local_html(report)
        self.assertIn("坂路 2件 / ウッド 0件",rendered)
        self.assertIn("資料不足",rendered)
        self.assertFalse(report["formalTenFactorReady"])
        race["workoutCoverage"]["byNumber"].pop()
        from jrdb_coverage import CoverageError
        with self.assertRaises(CoverageError):
            local_html(report)

    def test_one_unmatched_race_remains_unassessed_not_excluded(self):
        initial = []
        for row in first_card():
            if row[:3] == b"SE2":
                initial.append(replace(
                    row, 30, 40, f"{2000000000 + int(row[28:30]):010d}"))
            else:
                initial.append(row)
        jv = FakeJv({
            "RACE": [*initial, *second_card()],
            "RCVN": sources()["RCVN"],
        })
        output = read(jv)
        self.assertEqual(output["raceCount"], 2)
        self.assertEqual(output["races"][0]["observedHorseHistory"], 0)
        self.assertGreater(output["races"][1]["observedHorseHistory"], 0)
        self.assertIs(output["historyCompletenessVerified"], False)
        self.assertEqual(len(jv.opens), 2)

    def test_never_reintroduces_started_race_after_provider_scan(self):
        jv = FakeJv({
            "RACE": [*first_card(), *second_card()],
            "RCVN": sources()["RCVN"],
        })
        with patch("windows_jvlink_day_history_preview.validate_day",
                   return_value=DAY):
            result = read_local_day_history(
                DAY, jv_factory=lambda: jv,
                captured_at=datetime(2026, 11, 21, 10, 10, tzinfo=JST),
                flat_only=True, all_flat_races=True,
            )
        self.assertEqual(result["raceCount"], 1)
        self.assertEqual(result["races"][0]["race"], 2)

    def test_explicit_batch_mode_and_create_only_local_save(self):
        with patch("windows_jvlink_day_history_preview.validate_day",
                   return_value=DAY):
            with self.assertRaisesRegex(
                    JvLocalCheckError, "^DAY_HISTORY_BATCH_MODE_INVALID$"):
                read_local_day_history(DAY, flat_only=False,
                                       all_flat_races=True)
        jv = FakeJv({
            "RACE": [*first_card(), *second_card()],
            "RCVN": sources()["RCVN"],
        })
        result = read(jv)
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LOCALAPPDATA": folder}):
                target = save_private_day_local(result)
                self.assertEqual(target.name,
                                 "jvdata-all-flat-races-" + DAY + ".html")
                self.assertTrue(target.is_file())
                self.assertIn("東京 1R", target.read_text("utf-8"))
                self.assertIn("東京 2R", target.read_text("utf-8"))
                raw = target.with_suffix(".json").read_text("utf-8")
                self.assertEqual(json.loads(raw)["raceCount"], 2)
                self.assertNotIn("1000000001", raw)
                self.assertFalse(list(target.parent.glob(".arc-race-all-*.tmp")))
                with self.assertRaisesRegex(
                        JvLocalCheckError, "^DAY_HISTORY_ALREADY_SAVED$"):
                    save_private_day_local(result)
                self.assertEqual(len(list(target.parent.glob("jvdata-all-*"))), 2)


if __name__ == "__main__":
    unittest.main()
