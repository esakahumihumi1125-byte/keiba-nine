"""Synthetic tests for the completely offline owner-only coverage page."""
import sys
import copy
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_jvdata_local_report import render_weekly_candidate_summary
from test_windows_jvlink_weekly_read import FakeJv, weekly_records, DAY
from windows_jvlink_weekly_read import collect_weekly_candidate_records


def sample():
    return collect_weekly_candidate_records(FakeJv(weekly_records()), DAY)


class OwnerLocalCandidateSummaryTests(unittest.TestCase):
    def test_renders_static_mobile_friendly_private_view(self):
        data = sample()
        original = copy.deepcopy(data)
        html = render_weekly_candidate_summary(data)
        self.assertEqual(data, original)
        self.assertIn("2026年11月21日", html)
        self.assertIn("東京", html)
        self.assertIn("1R", html)
        self.assertIn("10:00", html)
        self.assertIn("4頭候補", html)
        self.assertIn("未取得のRあり", html)
        self.assertIn("まだJRA公式最終確認ではありません", html)
        self.assertIn("default-src", html)
        for unsafe in ("<script", "https://", "http://", "fetch(", "form",
                       "horse_id", "racekey", "1000000001", "20261120090000",
                       "jockey_index", "PRIVATE_FILE_NAME"):
            self.assertNotIn(unsafe, html)

    def test_missing_or_promoted_official_status_is_rejected(self):
        changes = (
            lambda d: d.update(independentJraVerified=True),
            lambda d: d.update(productionPredictionReady=True),
            lambda d: d.update(date="20261122"),
            lambda d: d.update(raceCount=2),
            lambda d: d["races"][0].update(finalStarterListVerified=True),
            lambda d: d["races"][0].update(sourceDataUseRightsVerified=True),
            lambda d: d["races"][0].update(track="<script>alert(1)</script>"),
            lambda d: d["races"][0].update(horseNumbersCandidate=[1, 2, 3, 3]),
            lambda d: d["races"].append(copy.deepcopy(d["races"][0])),
        )
        for change in changes:
            report = sample()
            change(report)
            with self.subTest(change=change), self.assertRaises(CoverageError):
                render_weekly_candidate_summary(report)

    def test_unknown_optional_fields_are_never_placed_in_html(self):
        data = sample()
        data["privateKey"] = "SECRET-TOP-DO-NOT-LEAK"
        data["races"][0]["privateRecord"] = "SECRET-ROW-DO-NOT-LEAK"
        html = render_weekly_candidate_summary(data)
        self.assertNotIn("SECRET-TOP-DO-NOT-LEAK", html)
        self.assertNotIn("SECRET-ROW-DO-NOT-LEAK", html)

    def test_no_data_does_not_claim_full_racecard(self):
        data = sample()
        data["races"] = []
        data["raceCount"] = 0
        with self.assertRaises(CoverageError):
            render_weekly_candidate_summary(data)


if __name__ == "__main__":
    unittest.main()
