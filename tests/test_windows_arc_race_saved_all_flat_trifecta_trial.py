"""Batch offline JRA-VAN past-course studies use no providers or actual wagers."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from test_owner_jvdata_offline_trifecta_trial import LocalTrifectaTrialTests, NOW
from windows_arc_race_saved_all_flat_trifecta_trial import (
    build_day_studies, render_day_html, save_local_day_trial,
    local_path, JvLocalCheckError,
)


def input_day():
    report = LocalTrifectaTrialTests().filled()
    race2 = copy.deepcopy(report["races"][0])
    race2["race"] = 2
    race2["postTimeCandidate"] = "10:40"
    report["races"].append(race2)
    report["raceCount"] = 2
    return report


class BatchJvHistoryTrifectaTests(unittest.TestCase):
    def test_two_live_comparable_races_produce_research_studies_not_bets(self):
        report = input_day()
        frozen = copy.deepcopy(report)
        study = build_day_studies(report, as_of=NOW)
        self.assertEqual(report, frozen)
        self.assertEqual(study["raceCount"], 2)
        self.assertEqual(study["studyCount"], 2)
        self.assertEqual(study["holdCount"], 0)
        self.assertEqual([r["race"] for r in study["races"]], [1, 2])
        self.assertEqual([r["points"] for r in study["races"]], [40, 40])
        self.assertTrue(all(len({tuple(t) for t in r["tickets"]}) == 40
                            for r in study["races"]))
        for key in ("officialJraVerified", "formalTenFactorReady",
                    "predictionValidated", "bettingReady",
                    "changesExistingRecords"):
            self.assertIs(study[key], False)
        self.assertEqual(study["newProviderCalls"], 0)
        self.assertEqual(study["realPurchases"], 0)
        self.assertEqual(study["signedReceiptsIssued"], 0)
        html = render_day_html(study)
        self.assertIn("東京 1R", html)
        self.assertIn("東京 2R", html)
        self.assertIn("40点", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("https://", html)

    def test_after_off_and_missing_history_keep_zero_points(self):
        report = input_day()
        result = build_day_studies(
            report, as_of=NOW.replace(hour=10, minute=10))
        self.assertEqual(result["studyCount"], 1)
        self.assertEqual(result["holdCount"], 1)
        self.assertEqual(result["races"][0]["points"], 0)
        self.assertEqual(result["races"][0]["holdReason"],
                         "not_before_scheduled_off")
        self.assertEqual(result["races"][1]["points"], 40)
        report["races"][1]["byNumber"][6]["observedRecordCount"] = 0
        report["races"][1]["byNumber"][6]["recentObservedRuns"] = []
        report["races"][1]["observedHorseHistory"] = 6
        partial = build_day_studies(report, as_of=NOW)
        self.assertEqual(partial["holdCount"], 1)
        self.assertEqual(partial["races"][1]["holdReason"],
                         "incomplete_comparable_prior_runs")
        self.assertEqual(partial["races"][1]["tickets"], [])

    def test_wrong_flags_and_duplicates_block_all_studies(self):
        for mutate in (
            lambda r: r.update(bettingReady=True),
            lambda r: r["races"][1].update(race=1),
            lambda r: r["races"][1].update(graded=True),
            lambda r: r.update(officialStarterListVerified=True),
        ):
            with self.subTest(mutate=mutate):
                report = input_day()
                mutate(report)
                with self.assertRaises(CoverageError):
                    build_day_studies(report, as_of=NOW)

    def test_create_only_file_and_existing_source_unchanged(self):
        report = input_day()
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder) / "ARC-RACE-private"
            base.mkdir()
            source = base / ("jvdata-all-flat-races-" + report["date"] + ".json")
            raw = json.dumps(report, ensure_ascii=False)
            source.write_text(raw, "utf-8")
            self.assertEqual(local_path(report["date"], appdata=folder), source)
            html_path, study = save_local_day_trial(source, as_of=NOW)
            self.assertTrue(html_path.is_file())
            self.assertTrue(html_path.with_suffix(".json").is_file())
            self.assertEqual(study["studyCount"], 2)
            self.assertEqual(source.read_text("utf-8"), raw)
            self.assertNotIn("1000000001", html_path.read_text("utf-8"))
            self.assertEqual(list(base.glob(".arc-race-all-study-*.tmp")), [])
            with self.assertRaisesRegex(
                    JvLocalCheckError, "^ALL_FLAT_ALREADY_SAVED$"):
                save_local_day_trial(source, as_of=NOW)
            self.assertEqual(source.read_text("utf-8"), raw)

    def test_wrong_filename_date_cannot_publish_study(self):
        report = input_day()
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "jvdata-all-flat-races-20261122.json"
            source.write_text(json.dumps(report), "utf-8")
            with self.assertRaisesRegex(
                    JvLocalCheckError, "^ALL_FLAT_SOURCE_INVALID$"):
                save_local_day_trial(source, as_of=NOW)


if __name__ == "__main__":
    unittest.main()
