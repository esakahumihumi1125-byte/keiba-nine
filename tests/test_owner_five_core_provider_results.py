"""85-weight sealed JRDB provisional observations: never official scoring or ROI."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_five_core_receipts import (
    issue_five_core_receipts, verify_five_core_receipts, FiveCoreReceiptError
)
from owner_five_core_provider_results import compare_five_core_provider_results
from test_owner_five_core_receipts import sample, DAY
from test_private_service import call, SETTINGS
from private_service import create_app

SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]
AFTER = datetime(2099, 4, 12, 3, 0, tzinfo=timezone.utc)
BEFORE = datetime(2099, 4, 12, 0, 0, tzinfo=timezone.utc)


def signed():
    history, programme, now = sample()
    receipts = issue_five_core_receipts(
        history, programme, SECRET, DAY, now)["receipts"]
    return receipts, verify_five_core_receipts(receipts, SECRET, DAY)


def row(track="05", race="01", horse="01", finish="1", **kw):
    return {
        "racekey": track+"99ab"+race,
        "racedate": DAY,
        "horse_number": horse, "order_of_finish": finish, **kw,
    }


def podium(winner="01", second="02", third="03"):
    return [row(horse=winner, finish="01"),
            row(horse=second, finish="02"),
            row(horse=third, finish="03")]


class FiveCoreObservedResultsTests(unittest.TestCase):
    def test_immutable_five_factor_reference_and_studied_winner(self):
        originals = signed()[1]
        unchanged = copy.deepcopy(originals)
        report = compare_five_core_provider_results(
            originals, podium(), DAY, now=AFTER)
        self.assertEqual(originals, unchanged)
        self.assertEqual(report["raceCount"], 2)
        self.assertEqual(report["observedRaceCount"], 1)
        self.assertEqual(report["observedStudiedWinnerCount"], 1)
        self.assertEqual(report["observedTopGroupWinnerCount"], 1)
        first = report["races"][0]
        self.assertEqual(first["observedPodiumNumbers"], [1, 2, 3])
        self.assertEqual(first["winnerStudyScore85"], 58.0)
        self.assertEqual(first["winnerStudyBands"], {
            "training":"S", "course_distance":"A", "pace":"B",
            "ground":"A", "recent":"C"})
        self.assertEqual(first["winnerStudyGroup"], 1)
        self.assertTrue(first["winnerInTopStudyGroup"])
        self.assertTrue(first["studyGroupNotFormalRank"])
        self.assertEqual(report["races"][1]["providerStatus"], "pending")
        self.assertIsNone(report["races"][1]["winnerStudyGroup"])
        self.assertEqual(report["winnerBandCounts"]["recent"]["C"], 1)
        self.assertEqual(report["winnerBandCounts"]["training"]["S"], 1)
        for k in ("officialJraVerified", "officialFeedConnected",
                  "jraIndependentConfirmation", "outcomeCalibrationReady",
                  "bettingReady", "actualPurchase", "payoutVerified"):
            self.assertFalse(report[k])
        self.assertIsNone(report["confirmedHitCount"])
        self.assertIsNone(report["modelAccuracyPercent"])
        self.assertIsNone(report["roiPercent"])
        for k in ("racekey", "horse_id", "trifectaTickets", "JRDB_API_KEY"):
            self.assertNotIn(k, repr(report))

    def test_unstudied_winner_never_counted_as_bad_grade_or_zero(self):
        report = compare_five_core_provider_results(
            signed()[1], podium("03","01","02"), DAY, now=AFTER)
        self.assertEqual(report["observedRaceCount"], 1)
        self.assertEqual(report["observedStudiedWinnerCount"], 0)
        self.assertEqual(report["observedTopGroupWinnerCount"], 0)
        first = report["races"][0]
        self.assertFalse(first["studiedWinnerObserved"])
        self.assertIsNone(first["winnerStudyScore85"])
        self.assertIsNone(first["winnerStudyGroup"])
        for factor, counts in report["winnerBandCounts"].items():
            self.assertEqual(sum(counts.values()), 0, factor)

    def test_second_studied_winner_is_not_claimed_top(self):
        report = compare_five_core_provider_results(
            signed()[1], podium("02","01","03"), DAY, now=AFTER)
        first = report["races"][0]
        self.assertEqual(first["winnerStudyGroup"], 2)
        self.assertFalse(first["winnerInTopStudyGroup"])
        self.assertEqual(report["observedTopGroupWinnerCount"], 0)

    def test_late_missing_or_contradictory_podium_stays_pending(self):
        originals = signed()[1]
        before = compare_five_core_provider_results(
            originals, podium(), DAY, now=BEFORE)
        self.assertEqual(before["observedRaceCount"], 0)
        self.assertEqual(before["observedStudiedWinnerCount"], 0)
        self.assertEqual(compare_five_core_provider_results(
            originals, [], DAY, now=BEFORE, source_read_count=0
        )["providerSourceReadCount"], 0)
        for bad in (
            [], podium()[:2],
            podium()+[row(horse="01", finish="04")],
            podium()+[row(horse="04", finish="01")],
            podium()+[row(horse="04", finish="04",racekey="0599cc01")],
            [*podium()[:2], row(horse="03",finish="withdrawn")],
            [*podium()[:2],row(horse="03",finish="03",
                               trouble_classification="1")],
        ):
            with self.subTest(bad=bad):
                report = compare_five_core_provider_results(
                    originals, bad, DAY, now=AFTER)
                self.assertEqual(report["observedRaceCount"], 0)
                self.assertEqual(report["races"][0]["providerStatus"], "pending")
                self.assertIsNone(report["races"][0]["winnerStudyScore85"])
        with self.assertRaises(FiveCoreReceiptError):
            compare_five_core_provider_results(originals, podium(), DAY,
                                               now=AFTER,source_read_count=0)

    def test_bad_provider_identity_or_fake_signed_grade_rejected(self):
        originals = signed()[1]
        for bad in (
            {**row(), "horse_number":"1"},
            {**row(), "horse_number":"19"},
            {**row(), "racedate":"20990413"},
            {**row(), "racekey":"0526ab01"},
            {**row(), "racekey":"NOT_REAL"},
            {**row(), "order_of_finish":1},
        ):
            with self.subTest(bad=bad), self.assertRaises(FiveCoreReceiptError):
                compare_five_core_provider_results(
                    originals, [bad], DAY, now=AFTER)
        forged=copy.deepcopy(originals)
        forged[0]["horses"][0]["bands"]["recent"]="S"
        with self.assertRaises(FiveCoreReceiptError):
            compare_five_core_provider_results(forged,podium(),DAY,now=AFTER)

    def test_private_route_one_provider_read_and_no_client_outcome_injection(self):
        signed_receipts = signed()[0]
        opts={**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY":"1",
              "KEIBA_RENDER_PREVIEW_ONLY":"0",
              "JRDB_PRIVATE_ENABLED":"1",
              "JRDB_API_KEY":"synthetic","JRDB_AUTH_KEY":"synthetic"}
        app=create_app(opts)
        with (patch("private_service.fetch_finished_race_results",
                    return_value=podium()) as fetch,
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T12:00:00+09:00")):
            resp=call(app,"/api/owner-five-core-provider-check",
                      method="POST",data={"date":DAY,"receipts":signed_receipts})
            fetch.assert_called_once_with(DAY)
        self.assertEqual(resp["status"],"200 OK")
        payload=json.loads(resp["body"])
        self.assertEqual(payload["observedStudiedWinnerCount"],1)
        self.assertFalse(payload["officialJraVerified"])
        self.assertNotIn("racekey",resp["body"].decode())
        with patch("private_service.fetch_finished_race_results") as fetch:
            for bad in (
                {"date":DAY,"receipts":signed_receipts,"winner":1},
                {"date":DAY,"receipts":signed_receipts,"result":podium()},
                {"date":DAY,"receipts":[]},
                {"date":DAY,"receipts":[{
                    **signed_receipts[0],"signature":"a"*64}]},
            ):
                self.assertEqual(call(app,"/api/owner-five-core-provider-check",
                            method="POST",data=bad)["status"],"400 Bad Request")
            fetch.assert_not_called()
        self.assertEqual(call(app,"/api/owner-five-core-provider-check",
                  auth="",method="POST",
                  data={"date":DAY,"receipts":signed_receipts})["status"],
                  "401 Unauthorized")
        self.assertEqual(call(create_app(SETTINGS),
                  "/api/owner-five-core-provider-check",method="POST",
                  data={"date":DAY,"receipts":signed_receipts})["status"],
                  "404 Not Found")
        disabled=create_app({**opts,"JRDB_PRIVATE_ENABLED":"0"})
        self.assertEqual(call(disabled,"/api/owner-five-core-provider-check",
                   method="POST",data={"date":DAY,"receipts":signed_receipts})["status"],
                   "503 Service Unavailable")

    def test_before_start_makes_zero_provider_calls(self):
        signed_receipts=signed()[0]
        app=create_app({**SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
          "KEIBA_RENDER_PREVIEW_ONLY":"0","JRDB_PRIVATE_ENABLED":"1",
          "JRDB_API_KEY":"synthetic","JRDB_AUTH_KEY":"synthetic"})
        with (patch("private_service.fetch_finished_race_results") as fetch,
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T09:40:00+09:00")):
            res=call(app,"/api/owner-five-core-provider-check",
                     method="POST",data={"date":DAY,"receipts":signed_receipts})
            fetch.assert_not_called()
        self.assertEqual(res["status"],"200 OK")
        report=json.loads(res["body"])
        self.assertEqual(report["providerSourceReadCount"],0)
        self.assertEqual(report["observedRaceCount"],0)


if __name__=="__main__":
    unittest.main()
