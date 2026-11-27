"""Offline-only synthetic tests: no JRA-VAN, HTTP, private IDs or wagers."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_jvdata_offline_evidence import (
    summarize_runner, summarize_one_race, render_evidence_html,
    FACTORS_JP,
)
from windows_arc_race_saved_history_review import (
    private_source, save_offline_review, JvLocalCheckError,
)
from windows_jvlink_day_history_preview import (
    read_local_day_history, save_private_local,
)
from test_windows_jvlink_day_history_preview import (
    FakeJv, sources, PRESTART,
)
from test_jvdata_ra_se_candidate import DAY


class OfflineEvidenceTests(unittest.TestCase):
    def report(self):
        with patch("windows_jvlink_day_history_preview.validate_day",
                   return_value=DAY):
            return read_local_day_history(
                DAY, jv_factory=lambda: FakeJv(sources()), captured_at=PRESTART
            )

    def test_observed_recent_and_pace_are_never_formal_grades(self):
        report = self.report()
        result = summarize_one_race(report)
        self.assertEqual(result["runnerCount"], 4)
        self.assertEqual(result["runnersWithObservedHistory"], 2)
        self.assertEqual(result["runnersWithRecentFinishObservation"], 2)
        self.assertEqual(result["runnersWithPaceObservation"], 2)
        self.assertEqual(len(result["byNumber"]), 4)
        self.assertEqual(len(FACTORS_JP), 10)
        self.assertFalse(result["tenFactorScoresReady"])
        self.assertFalse(result["formalForecastReady"])
        self.assertFalse(result["trifectaReady"])
        self.assertFalse(result["rankedByAbility"])
        horse1 = result["byNumber"][0]
        self.assertEqual(horse1["number"], 1)
        self.assertEqual(horse1["observedFinishes"], [8])
        self.assertEqual(horse1["observedLast3fTenths"], [356])
        self.assertEqual(horse1["factorsWithObservations"], ["recent", "pace"])
        self.assertIsNone(horse1["totalScore"])
        self.assertIsNone(horse1["overallGrade"])
        self.assertFalse(horse1["eligibleForPrediction"])
        self.assertEqual(horse1["factorEvidence"]["training"]["status"],
                         "unverified")
        self.assertEqual(horse1["factorEvidence"]["course_distance"]["status"],
                         "past_context_only")
        self.assertEqual(horse1["factorEvidence"]["ground"]["status"],
                         "past_context_only")
        self.assertEqual(horse1["historicalCourseContextRowsObserved"], 1)
        self.assertEqual(horse1["historicalGoingContextRowsObserved"], 1)
        self.assertEqual(result["runnersWithPastCourseContext"], 2)
        self.assertEqual(result["runnersWithPastGoingContext"], 2)
        self.assertIsNone(horse1["factorEvidence"]["course_distance"]["score"])
        self.assertIsNone(horse1["factorEvidence"]["ground"]["score"])
        self.assertEqual(horse1["factorEvidence"]["pace"]["status"],
                         "observed_not_scored")
        self.assertTrue(all(
            x["score"] is None and x["grade"] is None
            for x in horse1["factorEvidence"].values()
        ))
        nohistory = result["byNumber"][1]
        self.assertEqual(nohistory["historicalRowsObserved"], 0)
        self.assertTrue(nohistory["missingHistoryUnproven"])
        self.assertEqual(nohistory["factorsWithObservations"], [])
        for forbidden in ("1000000001", "PRIVATE_FILENAME", "horse_id",
                          "source_raw", "SECRET_TOKEN", "privateApi"):
            self.assertNotIn(forbidden, repr(result))

    def test_past_course_without_verified_today_remains_ungraded(self):
        report = self.report()
        horse = report["races"][0]["byNumber"][0]
        run = horse["recentObservedRuns"][0]
        self.assertTrue(run["historicalRaceContextMatched"])
        self.assertEqual(run["surface"], "芝")
        self.assertEqual(run["distanceMeters"], 1800)
        self.assertEqual(run["going"], "稍重")
        result = summarize_one_race(report)
        self.assertEqual(result["byNumber"][0][
            "factorEvidence"]["course_distance"]["status"], "past_context_only")
        self.assertEqual(result["byNumber"][0][
            "factorEvidence"]["ground"]["status"], "past_context_only")
        self.assertFalse(result["tenFactorScoresReady"])
        self.assertFalse(result["trifectaReady"])
        html = render_evidence_html(result)
        self.assertIn("過去の条件のみ", html)
        self.assertIn("今回の適性は未評価", html)

        # A partial old JSON with no RA7 context cannot be upgraded by
        # assuming the missing past race was comparable.
        run["historicalRaceContextMatched"] = False
        run["surface"] = None
        run["distanceMeters"] = None
        run["going"] = None
        partial = summarize_one_race(report)
        self.assertEqual(partial["byNumber"][0][
            "factorEvidence"]["course_distance"]["status"], "unverified")
        self.assertEqual(partial["byNumber"][0][
            "factorEvidence"]["ground"]["status"], "unverified")

    def test_comparable_course_counts_are_not_grades(self):
        report = self.report()
        race = report["races"][0]
        race.update(surfaceCandidate="芝", distanceMetersCandidate=1800)
        run = race["byNumber"][0]["recentObservedRuns"][0]
        from jrdb_program_preview import TRACKS
        venue = next(k for k, v in TRACKS.items() if v == race["track"])
        run.update(trackCode=venue, surface="芝", distanceMeters=1800,
                   historicalRaceContextMatched=True, hasAbnormalCode=False,
                   finishPosition=5, cornerPositions=[4, 5, 6, 6],
                   historicalStarterCount=6, historicalFinishersCount=6)
        for distance, count, exact in ((1800, 1, 1), (2000, 1, 0),
                                        (1600, 1, 0), (2001, 0, 0)):
            run["distanceMeters"] = distance
            horse = summarize_one_race(report)["byNumber"][0]
            self.assertEqual(horse["sameVenueSurfaceWithin200mObserved"], count)
            self.assertEqual(horse["sameVenueSurfaceExactDistanceObserved"], exact)
            self.assertEqual(horse["comparableRunsWithFieldRelativeFinish"], count)
            self.assertIsNone(horse["totalScore"])
            self.assertFalse(horse["eligibleForPrediction"])
        run["distanceMeters"] = 1800
        for changes in ({"trackCode": "99"}, {"surface": "ダート"},
                        {"historicalRaceContextMatched": False},
                        {"hasAbnormalCode": True}):
            bad = copy.deepcopy(report)
            bad["races"][0]["byNumber"][0]["recentObservedRuns"][0].update(changes)
            self.assertEqual(summarize_one_race(bad)["byNumber"][0][
                "sameVenueSurfaceWithin200mObserved"], 0)
        result = summarize_one_race(report)
        self.assertTrue(result["targetCourseCandidateAvailable"])
        self.assertGreaterEqual(result["runnersWithComparableCourseObservations"], 1)
        self.assertFalse(result["formalForecastReady"])
        self.assertIn("同競馬場・同芝/ダート・距離±200m", render_evidence_html(result))
        race["distanceMetersCandidate"] = None
        unknown = summarize_one_race(report)
        self.assertFalse(unknown["targetCourseCandidateAvailable"])
        self.assertIsNone(unknown["runnersWithComparableCourseObservations"])
        self.assertIsNone(unknown["byNumber"][0]["sameVenueSurfaceWithin200mObserved"])

    def test_field_relative_history_never_imputes_old_or_abnormal_rows(self):
        horse = self.report()["races"][0]["byNumber"][0]
        run = horse["recentObservedRuns"][0]
        run.update(finishPosition=5, cornerPositions=[4, 5, 6, 6],
                   historicalStarterCount=6, historicalFinishersCount=6,
                   historicalRaceContextMatched=True, hasAbnormalCode=False)
        first = summarize_runner(horse)
        obs = first["fieldRelativeHistoricalObservations"][0]
        self.assertEqual(obs["finisherPositionPercentile"], 20.0)
        self.assertEqual(obs["finalCornerToFinishGainPerFieldPercent"], 20.0)
        run.update(historicalStarterCount=18, historicalFinishersCount=18)
        obs = summarize_runner(horse)["fieldRelativeHistoricalObservations"][0]
        self.assertEqual(obs["finisherPositionPercentile"], 76.47)
        self.assertEqual(obs["finalCornerToFinishGainPerFieldPercent"], 5.88)
        run["historicalFinishersCount"] = 17
        obs = summarize_runner(horse)["fieldRelativeHistoricalObservations"][0]
        self.assertIsNone(obs["finalCornerToFinishGainPerFieldPercent"])
        for changes in ({"historicalStarterCount": None},
                        {"historicalFinishersCount": 19},
                        {"historicalFinishersCount": 4},
                        {"hasAbnormalCode": True},
                        {"historicalRaceContextMatched": False}):
            bad = copy.deepcopy(horse)
            bad["recentObservedRuns"][0].update(changes)
            summary = summarize_runner(bad)
            self.assertEqual(summary["fieldRelativeHistoricalObservations"], [None])
            self.assertIsNone(summary["totalScore"])
            self.assertFalse(summary["eligibleForPrediction"])
        old = copy.deepcopy(horse)
        for key in ("historicalStarterCount", "historicalFinishersCount"):
            old["recentObservedRuns"][0].pop(key)
        self.assertEqual(summarize_runner(old)["fieldRelativeHistoricalObservations"], [None])

    def test_only_weak_observations_dont_become_strength_or_a_debut(self):
        report = self.report()
        one = report["races"][0]["byNumber"][0]
        one["recentObservedRuns"][0]["finishPosition"] = None
        one["recentObservedRuns"][0]["historicalRunningStyleCode"] = None
        one["recentObservedRuns"][0]["cornerPositions"] = [None] * 4
        one["recentObservedRuns"][0]["last3fTenths"] = None
        summary = summarize_runner(one)
        self.assertEqual(summary["factorsWithObservations"], [])
        self.assertIsNone(summary["overallGrade"])
        self.assertTrue(summary["missingHistoryUnproven"])
        self.assertFalse(summary["eligibleForPrediction"])

    def test_no_production_promotion_even_if_all_history_is_present(self):
        report = self.report()
        report["races"][0]["byNumber"][1]["observedRecordCount"] = 1
        report["races"][0]["byNumber"][1]["recentObservedRuns"] = copy.deepcopy(
            report["races"][0]["byNumber"][0]["recentObservedRuns"]
        )
        report["races"][0]["byNumber"][3]["observedRecordCount"] = 1
        report["races"][0]["byNumber"][3]["recentObservedRuns"] = copy.deepcopy(
            report["races"][0]["byNumber"][0]["recentObservedRuns"]
        )
        report["races"][0]["observedHorseHistory"] = 4
        summary = summarize_one_race(report)
        self.assertEqual(summary["runnersWithObservedHistory"], 4)
        self.assertFalse(summary["formalForecastReady"])
        self.assertFalse(summary["trifectaReady"])

    def test_reject_untrusted_input_and_inconsistent_counts(self):
        report = self.report()
        changes = [
            ("privateOwnerOnly", False),
            ("bettingReady", True),
            ("formalTenFactorReady", True),
            ("officialStarterListVerified", True),
            ("raceCount", 2),
        ]
        for key, value in changes:
            bad = {**report, key: value}
            with self.subTest(key=key), self.assertRaises(CoverageError):
                summarize_one_race(bad)
        bad = copy.deepcopy(report)
        bad["races"][0]["byNumber"][0]["observedRecordCount"] = 0
        with self.assertRaises(CoverageError):
            summarize_one_race(bad)
        bad = copy.deepcopy(report)
        bad["races"][0]["byNumber"][0]["recentObservedRuns"][0][
            "finishPosition"] = -1
        with self.assertRaises(CoverageError):
            summarize_one_race(bad)
        bad = copy.deepcopy(report)
        bad["races"][0]["byNumber"][0]["number"] = 2
        with self.assertRaises(CoverageError):
            summarize_one_race(bad)

    def test_same_day_future_and_duplicate_history_cannot_be_forecast_evidence(self):
        # Even a manually edited local research report cannot smuggle a
        # result from the target race or a later day into pre-off evidence.
        report = self.report()
        target = datetime.strptime(DAY, "%Y%m%d")
        future = (target + timedelta(days=1)).strftime("%Y%m%d")
        for illegal_day in (DAY, future):
            bad = copy.deepcopy(report)
            bad["races"][0]["byNumber"][0]["recentObservedRuns"][0]["date"] = illegal_day
            with self.subTest(illegal_day=illegal_day):
                with self.assertRaises(CoverageError):
                    summarize_one_race(bad)
        duplicate = copy.deepcopy(report)
        runner = duplicate["races"][0]["byNumber"][0]
        runner["recentObservedRuns"].append(copy.deepcopy(
            runner["recentObservedRuns"][0]))
        runner["observedRecordCount"] += 1
        with self.assertRaises(CoverageError):
            summarize_one_race(duplicate)
        # The original older history must remain viewable as research.
        self.assertFalse(summarize_one_race(report)["formalForecastReady"])

    def test_html_is_safe_static_and_doesnt_copy_extra_keys(self):
        report = self.report()
        report["horse_id"] = "SECRET_TOKEN"
        report["races"][0]["byNumber"][0]["password"] = "SECRET_TOKEN"
        result = summarize_one_race(report)
        html = render_evidence_html(result)
        self.assertIn("10項目の資料確認（未採点）", html)
        self.assertIn("近走", html)
        self.assertIn("35.6秒", html)
        self.assertIn("これは予想ではありません", html)
        self.assertNotIn("SECRET_TOKEN", html)
        self.assertNotIn("1000000001", html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("http://", html.lower())
        self.assertNotIn("https://", html.lower())
        self.assertNotIn("3連単の買い目", repr(result))
        result["formalForecastReady"] = True
        with self.assertRaises(CoverageError):
            render_evidence_html(result)

    def test_read_already_saved_local_file_once_without_any_jvlink_calls(self):
        report = self.report()
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LOCALAPPDATA": folder}):
                source_html = save_private_local(report)
                source = source_html.with_suffix(".json")
                chosen = private_source(DAY, appdata=folder)
                self.assertEqual(chosen, source)
                view, summary = save_offline_review(chosen)
                self.assertEqual(view.suffix, ".html")
                self.assertTrue(view.is_file())
                self.assertTrue(view.with_suffix(".json").is_file())
                self.assertTrue(source.is_file())
                self.assertEqual(summary["networkCalls"], 0)
                self.assertFalse(summary["rawJvdataExported"])
                evidence = json.loads(
                    view.with_suffix(".json").read_text("utf-8"))
                self.assertEqual(evidence["byNumber"][0]["observedFinishes"],
                                 [8])
                self.assertNotIn("1000000001", repr(evidence))
                self.assertNotIn("SECRET_TOKEN", repr(evidence))
                self.assertEqual(save_offline_review(chosen)[0], view)
                self.assertEqual(list(view.parent.glob(
                    ".arc-race-evidence-*.tmp")), [])
                # A manually edited HTML should NEVER be silently opened
                # merely because the output filename already exists.
                view.write_text("<script>tampered</script>", encoding="utf-8")
                with self.assertRaisesRegex(
                        JvLocalCheckError, "OFFLINE_EVIDENCE_TARGET_CONFLICT"):
                    save_offline_review(chosen)

    def test_no_saved_file_really_does_not_start_provider_read(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(
                    JvLocalCheckError, "OFFLINE_EVIDENCE_NO_SAVED_RESEARCH"):
                private_source(DAY, appdata=folder)
            with self.assertRaisesRegex(
                    JvLocalCheckError, "OFFLINE_EVIDENCE_DATE_INVALID"):
                private_source("../../foo", appdata=folder)

    def test_private_file_is_ungraded_and_does_not_trust_poisoned_data(self):
        report = self.report()
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LOCALAPPDATA": folder}):
                source = save_private_local(report).with_suffix(".json")
                parsed = json.loads(source.read_text("utf-8"))
                parsed["bettingReady"] = True
                source.write_text(json.dumps(parsed), encoding="utf-8")
                with self.assertRaisesRegex(
                        JvLocalCheckError, "OFFLINE_EVIDENCE_BAD_INPUT"):
                    save_offline_review(source)
                self.assertFalse(
                    source.with_name(source.stem + "-evidence.html").exists()
                )


if __name__ == "__main__":
    unittest.main()
