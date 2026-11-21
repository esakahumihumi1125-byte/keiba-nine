"""Synthetic owner-PC JV-Link 3連単 study: no providers, credentials or wagers."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_jvdata_offline_trifecta_trial import (
    build_local_trifecta_study, render_local_trifecta_html,
)
from windows_arc_race_saved_trifecta_trial import (
    save_offline_trifecta_trial, JvLocalCheckError,
)
from windows_jvlink_day_history_preview import (
    read_local_day_history, save_private_local,
)
from test_windows_jvlink_day_history_preview import (
    FakeJv, sources, PRESTART, JST,
)
from test_jvdata_ra_se_candidate import DAY, replace
from jvdata_ra_se_candidate import parse_jvdata_prestart_racecard


NOW = datetime(2026, 11, 21, 9, 20, tzinfo=JST)


class LocalTrifectaTrialTests(unittest.TestCase):
    def source(self):
        with patch("windows_jvlink_day_history_preview.validate_day", return_value=DAY):
            return read_local_day_history(
                DAY, jv_factory=lambda: FakeJv(sources()),
                captured_at=PRESTART,
            )

    def filled(self):
        report = self.source()
        race = report["races"][0]
        old = copy.deepcopy(race["byNumber"][0]["recentObservedRuns"][0])
        self.assertTrue(old["historicalRaceContextMatched"])
        self.assertEqual(old["surface"], "芝")
        self.assertEqual(old["distanceMeters"], 1800)
        horses = []
        for n in range(1, 8):
            horse = copy.deepcopy(race["byNumber"][0])
            horse["number"] = n
            horse["observedRecordCount"] = 1
            run = copy.deepcopy(old)
            run["finishPosition"] = n
            run["cornerPositions"] = [n + 1, n + 1, n + 1, min(n + 3, 18)]
            run["hasAbnormalCode"] = False
            horse["recentObservedRuns"] = [run]
            horses.append(horse)
        race["byNumber"] = horses
        race["observedHorseHistory"] = len(horses)
        race["status"] = "historical_observations_not_graded"
        race["surfaceCandidate"] = "芝"
        race["distanceMetersCandidate"] = 1800
        race["postTimeCandidate"] = "10:00"
        return report

    def test_raw_ra2_course_is_only_a_scheduled_candidate(self):
        original = sources()["RACE"]
        ra = replace(replace(original[0], 697, 701, "1800"),
                     705, 707, "10")
        parsed = parse_jvdata_prestart_racecard(ra, original[1:], DAY)
        self.assertEqual(parsed["surfaceCandidate"], "芝")
        self.assertEqual(parsed["distanceMetersCandidate"], 1800)
        self.assertFalse(parsed["finalStarterListVerified"])
        self.assertFalse(parsed["latestGoingVerified"])
        # Unknown course is not guessed from the meeting or venue.
        unknown = parse_jvdata_prestart_racecard(*(
            original[0], original[1:], DAY))
        self.assertIsNone(unknown["surfaceCandidate"])
        self.assertIsNone(unknown["distanceMetersCandidate"])

    def test_bridge_keeps_current_race_metadata_and_private_prestart_clock(self):
        src = sources()
        src["RACE"][0] = replace(replace(src["RACE"][0], 697, 701, "1800"),
                                705, 707, "10")
        with patch("windows_jvlink_day_history_preview.validate_day",
                   return_value=DAY):
            report = read_local_day_history(
                DAY, jv_factory=lambda: FakeJv(src), captured_at=PRESTART,
            )
        race = report["races"][0]
        self.assertEqual(race["surfaceCandidate"], "芝")
        self.assertEqual(race["distanceMetersCandidate"], 1800)
        self.assertEqual(race["postTimeCandidate"], "10:00")
        self.assertEqual(report["capturedAtLocalJst"], PRESTART.isoformat(timespec="seconds"))
        self.assertFalse(report["captureTimeIndependentlyVerified"])
        self.assertNotIn("1000000001", repr(report))

    def test_complete_comparable_history_yields_only_40_point_study(self):
        report = self.filled()
        result = build_local_trifecta_study(report, as_of=NOW)
        self.assertEqual(result["status"], "local_history_research_only")
        self.assertEqual(result["researchOrder"], [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(result["first"], [1, 2])
        self.assertEqual(result["second"], [1, 2, 3, 4, 5])
        self.assertEqual(result["third"], [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(result["points"], 40)
        self.assertEqual(len({tuple(t) for t in result["tickets"]}), 40)
        self.assertEqual(result["referenceYenAt100"], 4000)
        self.assertFalse(result["bettingReady"])
        self.assertFalse(result["formalTenFactorReady"])
        self.assertFalse(result["officialJraVerified"])
        self.assertFalse(result["predictionValidated"])
        self.assertEqual(result["newProviderCalls"], 0)
        html = render_local_trifecta_html(result)
        self.assertIn("過去走限定", html)
        self.assertIn("1着候補", html)
        self.assertIn("40点", html)
        self.assertIn("正式予想・購入用ではありません", html)
        self.assertNotIn("<script", html.lower())
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)

    def test_missing_current_course_or_incomplete_history_holds_without_ranking(self):
        source = self.source()  # only 2/4 have history, current course unknown
        self.assertEqual(build_local_trifecta_study(source, as_of=NOW)["points"], 0)
        complete = self.filled()
        complete["races"][0]["byNumber"][6]["recentObservedRuns"] = []
        complete["races"][0]["byNumber"][6]["observedRecordCount"] = 0
        complete["races"][0]["observedHorseHistory"] = 6
        output = build_local_trifecta_study(complete, as_of=NOW)
        self.assertEqual(output["status"], "hold")
        self.assertEqual(output["holdReason"], "incomplete_comparable_prior_runs")
        self.assertEqual(output["comparableRunners"], 6)
        self.assertEqual(output["tickets"], [])
        self.assertEqual(output["researchOrder"], [])

    def test_after_off_and_tied_boundary_cannot_forge_tickets(self):
        full = self.filled()
        after = NOW.replace(hour=10, minute=0)
        result = build_local_trifecta_study(full, as_of=after)
        self.assertEqual(result["holdReason"], "not_before_scheduled_off")
        self.assertEqual(result["points"], 0)
        full["races"][0]["byNumber"][2]["recentObservedRuns"][0][
            "finishPosition"] = 2
        full["races"][0]["byNumber"][2]["recentObservedRuns"][0][
            "cornerPositions"] = [3, 3, 3, 5]
        tie = build_local_trifecta_study(full, as_of=NOW)
        self.assertEqual(tie["holdReason"], "ambiguous_formation_boundary")
        self.assertEqual(tie["first"], [])

    def test_late_or_tampered_source_and_secret_keys_are_not_promoted(self):
        full = self.filled()
        full["secret_api_token"] = "SUPER_SECRET_FOR_TEST"
        full["races"][0]["byNumber"][0]["horse_id"] = "SECRET-HORSE-ID"
        result = build_local_trifecta_study(full, as_of=NOW)
        self.assertNotIn("SUPER_SECRET_FOR_TEST", repr(result))
        self.assertNotIn("SECRET-HORSE-ID", repr(result))
        full["bettingReady"] = True
        with self.assertRaises(CoverageError):
            build_local_trifecta_study(full, as_of=NOW)

    def test_local_create_only_output_preserves_earlier_history(self):
        full = self.filled()
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, {"LOCALAPPDATA": folder}):
                source = save_private_local(full).with_suffix(".json")
                target, report = save_offline_trifecta_trial(source, as_of=NOW)
                self.assertEqual(report["points"], 40)
                self.assertTrue(target.is_file())
                self.assertTrue(target.with_suffix(".json").is_file())
                self.assertTrue(source.is_file())
                self.assertEqual(save_offline_trifecta_trial(source, as_of=NOW)[0], target)
                payload = json.loads(target.with_suffix(".json").read_text("utf-8"))
                self.assertFalse(payload["formalTenFactorReady"])
                self.assertNotIn("1000000001", repr(payload))
                self.assertEqual(list(target.parent.glob(
                    ".arc-race-trifecta-*.tmp")), [])
                target.write_text("<script>tampered</script>", encoding="utf-8")
                with self.assertRaisesRegex(
                    JvLocalCheckError, "LOCAL_TRIFECTA_RESEARCH_CONFLICT"):
                    save_offline_trifecta_trial(source, as_of=NOW)


if __name__ == "__main__":
    unittest.main()
