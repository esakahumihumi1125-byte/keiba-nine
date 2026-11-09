"""Synthetic, read-only 85-point provider outcome review tests (no paid data)."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_five_core_provider_results import compare_five_core_provider_results
from owner_five_core_receipts import (
    issue_five_core_receipts, verify_five_core_receipts, FiveCoreReceiptError
)
from test_owner_five_core_receipts import sample
from test_owner_three_core_provider_results import row, complete
from test_owner_three_core_receipts import DAY
from test_private_service import call, SETTINGS
from private_service import create_app

SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]
AFTER = datetime(2099, 4, 12, 14, 0, tzinfo=timezone.utc)


def signed():
    history, programme, before = sample()
    issued = issue_five_core_receipts(history, programme, SECRET, DAY, before)
    return verify_five_core_receipts(issued["receipts"], SECRET, DAY), issued["receipts"]


class FiveCoreProviderReviewTests(unittest.TestCase):
    def test_frozen_85_winner_observation_is_not_an_accuracy_claim(self):
        originals, _ = signed()
        saved = copy.deepcopy(originals)
        result = compare_five_core_provider_results(
            originals, complete(), DAY, now=AFTER)
        self.assertEqual(originals, saved)
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["observedRaceCount"], 1)
        self.assertEqual(result["observedStudiedWinnerCount"], 1)
        self.assertEqual(result["observedStudiedRunnerCount"], 2)
        self.assertEqual(result["observedResearchBandExposureCounts"]["training"],
                         {"S": 1, "A": 0, "B": 0, "C": 1})
        self.assertEqual(result["winnerBandCounts"]["training"],
                         {"S": 1, "A": 0, "B": 0, "C": 0})
        self.assertEqual(result["observedResearchBandExposureCounts"]["ground"]["A"],2)
        self.assertEqual(result["winnerBandCounts"]["ground"]["A"],1)
        for factor, exposures in result["observedResearchBandExposureCounts"].items():
            self.assertEqual(sum(exposures.values()), 2, factor)
            for band, count in exposures.items():
                self.assertLessEqual(result["winnerBandCounts"][factor][band], count)
        first = result["races"][0]
        self.assertEqual(first["observedPodiumNumbers"], [1, 2, 3])
        self.assertEqual(first["winnerStudyScore85"], 58.0)
        self.assertEqual(first["winnerStudyBands"]["recent"], "C")
        self.assertTrue(first["studiedWinnerObserved"])
        self.assertEqual(result["races"][1]["providerStatus"], "pending")
        self.assertFalse(result["officialJraVerified"])
        self.assertFalse(result["outcomeCalibrationReady"])
        self.assertIsNone(result["modelAccuracyPercent"])
        self.assertIsNone(result["roiPercent"])
        self.assertFalse(result["actualPurchase"])
        self.assertNotIn("racekey", repr(result))
        self.assertNotIn("horse_id", repr(result))

    def test_unstudied_winner_is_unknown_not_a_loss_or_zero(self):
        originals, _ = signed()
        observed = [row(horse="03", finish="01"),
                    row(horse="02", finish="02"),
                    row(horse="01", finish="03")]
        result = compare_five_core_provider_results(
            originals, observed, DAY, now=AFTER)
        first = result["races"][0]
        self.assertEqual(first["providerStatus"], "podium_observed")
        self.assertIs(first["studiedWinnerObserved"], False)
        self.assertIsNone(first["winnerStudyScore85"])
        self.assertIsNone(first["winnerStudyBands"])
        self.assertEqual(result["observedStudiedWinnerCount"], 0)
        # A winner without five bands does NOT make the signed runners vanish.
        self.assertEqual(result["observedStudiedRunnerCount"], 2)
        self.assertEqual(result["observedResearchBandExposureCounts"]["recent"]["C"], 2)
        self.assertEqual(result["winnerBandCounts"]["recent"]["C"], 0)

    def test_before_off_or_ambiguous_provider_rows_stay_pending(self):
        originals, _ = signed()
        before = datetime(2099, 4, 12, 0, 0, tzinfo=timezone.utc)
        result = compare_five_core_provider_results(
            originals, [], DAY, now=before, source_read_count=0)
        self.assertEqual(result["observedRaceCount"], 0)
        self.assertTrue(all(r["providerStatus"] == "pending"
                            for r in result["races"]))
        self.assertEqual(result["observedStudiedRunnerCount"], 0)
        self.assertTrue(all(not any(counts.values())
                            for counts in result["observedResearchBandExposureCounts"].values()))
        for broken in (
            complete()[:2],
            [row(horse="01", finish="withdrawn")],
            complete() + [row(horse="01", finish="04")],
            [row(horse="01", finish="01"),
             row(horse="02", finish="01"),
             row(horse="03", finish="03")],
            [row(horse="01", finish="01", trouble_classification="1"),
             *complete()[1:]],
        ):
            result = compare_five_core_provider_results(
                originals, broken, DAY, now=AFTER)
            self.assertEqual(result["races"][0]["providerStatus"], "pending")
            self.assertIsNone(result["races"][0]["winnerStudyScore85"])
            self.assertEqual(result["observedStudiedRunnerCount"], 0)
            self.assertTrue(all(not any(counts.values())
                                for counts in result["observedResearchBandExposureCounts"].values()))

    def test_invalid_identity_and_unsigned_schema_are_rejected(self):
        originals, _ = signed()
        for bad in (
            [row(track="ZZ")],
            [row(horse="19")],
            [row(race="13")],
            [row(racedate="20990413")],
        ):
            with self.subTest(bad=bad), self.assertRaises(FiveCoreReceiptError):
                compare_five_core_provider_results(
                    originals, bad, DAY, now=AFTER)
        with self.assertRaises(FiveCoreReceiptError):
            compare_five_core_provider_results(
                originals + originals[:1], complete(), DAY, now=AFTER)
        with self.assertRaises(FiveCoreReceiptError):
            compare_five_core_provider_results(
                originals, complete(), DAY, now=AFTER, source_read_count=0)
        changed = copy.deepcopy(originals)
        changed[0]["horses"][0]["rawThirdPoints"] = 255
        with self.assertRaises(FiveCoreReceiptError):
            compare_five_core_provider_results(
                changed, complete(), DAY, now=AFTER)

    def test_private_route_one_result_request_only_and_no_user_supplied_results(self):
        originals, receipts = signed()
        app = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                          "KEIBA_RENDER_PREVIEW_ONLY": "0",
                          "JRDB_PRIVATE_ENABLED": "1",
                          "JRDB_API_KEY": "synthetic",
                          "JRDB_AUTH_KEY": "synthetic"})
        with patch("private_service._now_in_jst",
                   return_value="2099-04-12T23:00:00+09:00"), patch(
                    "private_service.fetch_finished_race_results",
                    return_value=complete()) as fetched:
            resp = call(app, "/api/owner-five-core-provider-check", method="POST",
                        data={"date": DAY, "receipts": receipts})
            fetched.assert_called_once_with(DAY)
        self.assertEqual(resp["status"], "200 OK")
        body=json.loads(resp["body"])
        self.assertEqual(body["observedRaceCount"], 1)
        self.assertEqual(body["observedStudiedRunnerCount"], 2)
        self.assertFalse(body["outcomeCalibrationReady"])
        self.assertNotIn("horse_number", repr(body))
        with patch("private_service.fetch_finished_race_results") as fetched:
            early = call(app, "/api/owner-five-core-provider-check", method="POST",
                         data={"date": DAY, "receipts": receipts})
            fetched.assert_not_called()
        self.assertEqual(early["status"], "200 OK")
        self.assertEqual(json.loads(early["body"])["observedRaceCount"], 0)
        for payload in (
            {"date": DAY, "receipts": receipts, "result": [1, 2, 3]},
            {"date": DAY, "receipts": receipts, "payout": 200000},
            {"date": DAY, "receipts": [{**receipts[0], "signature": "f"*64}]},
        ):
            resp = call(app, "/api/owner-five-core-provider-check",
                        method="POST", data=payload)
            self.assertEqual(resp["status"], "400 Bad Request")
        self.assertEqual(call(app, "/api/owner-five-core-provider-check",
                              method="POST", auth="",
                              data={"date": DAY, "receipts": receipts})["status"],
                         "401 Unauthorized")
        self.assertEqual(call(create_app(SETTINGS),
                              "/api/owner-five-core-provider-check",
                              method="POST",
                              data={"date": DAY, "receipts": receipts})["status"],
                         "404 Not Found")


if __name__ == "__main__":
    unittest.main()
