"""Synthetic result rows; no actual provider calls."""
import copy
import json
import unittest
from unittest.mock import patch
from datetime import timedelta
from test_owner_research6_draft_receipts import setup, NOW, DAY, SECRET
from owner_research6_draft_receipts import (
    issue_research6_draft_receipts, verify_research6_draft_receipts,
)
from owner_research6_result_review import compare_research6_results, compare_research6_payoffs
from private_service import create_app
from test_private_service import SETTINGS, call


class Research6ResultTests(unittest.TestCase):
    def setUp(self):
        p, history = setup()
        self.signed = issue_research6_draft_receipts(
            history, p, SECRET, DAY, now=NOW)["receipts"]
        self.snapshots = verify_research6_draft_receipts(self.signed, SECRET, DAY)
        self.rows = [{"racekey": "0599ff01", "racedate": DAY,
                      "horse_number": f"{n:02d}", "order_of_finish": f"{n:02d}"}
                     for n in range(1, 8)]
        self.after = NOW + timedelta(hours=4)

    def test_complete_results_and_originals_unchanged(self):
        before = copy.deepcopy(self.snapshots)
        report = compare_research6_results(
            self.snapshots, self.rows, DAY, now=self.after)
        self.assertEqual(report["observedRaceCount"], 1)
        self.assertEqual(report["provisionalExactCombinationCount"], 1)
        self.assertEqual(report["researchWeight"], 79)
        self.assertFalse(report["officialJraVerified"])
        self.assertIsNone(report["roiPercent"])
        self.assertEqual(before, self.snapshots)

    def test_incomplete_tied_abnormal_and_future_are_pending(self):
        for rows in (self.rows[:3], self.rows[:-1],
                     self.rows[:-1] + [{**self.rows[-1], "order_of_finish": "06"}],
                     self.rows[:-1] + [{**self.rows[-1], "trouble_classification": "1"}]):
            report = compare_research6_results(
                self.snapshots, rows, DAY, now=self.after)
            self.assertEqual(report["pendingRaceCount"], 1)
            self.assertIsNone(report["races"][0]["exactCombinationObserved"])
        report = compare_research6_results(
            self.snapshots, [], DAY, now=NOW, source_read_count=0)
        self.assertEqual(report["observedRaceCount"], 0)
        self.assertEqual(report["providerReadCount"], 0)

    def test_selected_horse_absent_from_full_results_is_pending(self):
        rows = copy.deepcopy(self.rows)
        rows[-1]["horse_number"] = "08"
        report = compare_research6_results(
            self.snapshots, rows, DAY, now=self.after)
        self.assertEqual(report["pendingRaceCount"], 1)

    def test_payoff_is_reference_only_and_refunds_stay_pending(self):
        rows = [{"racekey": "0599ff01", "racedate": DAY,
                 "trifecta_number_1": "010203", "trifecta_payoff_1": 26050}]
        original = copy.deepcopy(self.snapshots)
        report = compare_research6_payoffs(
            self.snapshots, rows, DAY, now=self.after)
        self.assertEqual(report["researchWeight"], 79)
        self.assertEqual(report["reviewedInvestedYen"], 4000)
        self.assertEqual(report["reviewedReturnedYen"], 26050)
        self.assertEqual(report["reviewedProfitYen"], 22050)
        self.assertEqual(report["reviewedRoiPercent"], 651.25)
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["changesExistingRoi"])
        for source in ([], [{**rows[0], "refund_number_1": "07"}],
                       [{**rows[0], "trifecta_payoff_1": None}]):
            pending = compare_research6_payoffs(
                self.snapshots, source, DAY, now=self.after)
            self.assertEqual(pending["pendingStakeYen"], 4000)
            self.assertIsNone(pending["reviewedRoiPercent"])
        self.assertEqual(self.snapshots, original)

    def test_payoff_route_no_read_before_off_or_for_tampered_receipt(self):
        app = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                          "KEIBA_RENDER_PREVIEW_ONLY": "0",
                          "JRDB_PRIVATE_ENABLED": "1",
                          "JRDB_API_KEY": "synthetic", "JRDB_AUTH_KEY": "synthetic"})
        path = "/api/owner-research6-payoff-review"
        args = {"date": DAY, "receipts": self.signed}
        rows = [{"racekey": "0599ff01", "racedate": DAY,
                 "trifecta_number_1": "010203", "trifecta_payoff_1": 26050}]
        with patch("private_service.fetch_finished_race_payoffs", return_value=rows) as read:
            with patch("private_service._now_in_jst", return_value=NOW.isoformat()):
                resp = call(app, path, method="POST", data=args)
                self.assertEqual(resp["status"], "200 OK")
                self.assertEqual(json.loads(resp["body"])["providerReadCount"], 0)
            with patch("private_service._now_in_jst", return_value=self.after.isoformat()):
                bad = call(app, path, method="POST", data={**args, "receipts": [
                    {**self.signed[0], "signature": "0"*64}]})
                self.assertEqual(bad["status"], "400 Bad Request")
                read.assert_not_called()
                resp = call(app, path, method="POST", data=args)
                self.assertEqual(resp["status"], "200 OK")
                self.assertEqual(json.loads(resp["body"])["reviewedProfitYen"], 22050)
                read.assert_called_once_with(DAY)

    def test_route_verified_only_and_no_reads_before_off(self):
        app = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                          "KEIBA_RENDER_PREVIEW_ONLY": "0",
                          "JRDB_PRIVATE_ENABLED": "1",
                          "JRDB_API_KEY": "synthetic", "JRDB_AUTH_KEY": "synthetic"})
        path = "/api/owner-research6-result-review"
        args = {"date": DAY, "receipts": self.signed}
        with patch("private_service.fetch_finished_race_results",
                   return_value=self.rows) as read:
            with patch("private_service._now_in_jst", return_value=NOW.isoformat()):
                resp = call(app, path, method="POST", data=args)
                self.assertEqual(resp["status"], "200 OK")
                self.assertEqual(json.loads(resp["body"])["providerReadCount"], 0)
                read.assert_not_called()
            with patch("private_service._now_in_jst", return_value=self.after.isoformat()):
                bad = call(app, path, method="POST",
                           data={**args, "receipts": [
                               {**self.signed[0], "signature": "0"*64}]})
                self.assertEqual(bad["status"], "400 Bad Request")
                read.assert_not_called()
                resp = call(app, path, method="POST", data=args)
                self.assertEqual(resp["status"], "200 OK")
                self.assertEqual(json.loads(resp["body"])["observedRaceCount"], 1)
                read.assert_called_once_with(DAY)
            self.assertEqual(call(app, path, method="POST", data=args,
                                  auth="")["status"], "401 Unauthorized")
            self.assertEqual(read.call_count, 1)


if __name__ == "__main__":
    unittest.main()
