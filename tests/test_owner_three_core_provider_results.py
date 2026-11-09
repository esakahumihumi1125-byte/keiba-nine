"""Provider placement is an observation, not verified JRA outcomes/accuracy."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_three_core_provider_results import compare_three_core_provider_results
from owner_three_core_receipts import (
    issue_three_core_receipts, verify_three_core_receipts, CoreReceiptError
)
from test_owner_three_core_receipts import source, DAY
from test_private_service import call, SETTINGS
from private_service import create_app

SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]


def snapshots():
    history, programme, before = source()
    payload = issue_three_core_receipts(
        history, programme, SECRET, DAY, before)
    return verify_three_core_receipts(payload["receipts"], SECRET, DAY)


def row(track="05", race="01", horse="01", finish="1", **extra):
    return {"racekey": track+"99ab"+race, "racedate": DAY,
            "horse_number": horse, "order_of_finish": finish, **extra}


def complete():
    return [row(horse="01", finish="01"),
            row(horse="02", finish="02"),
            row(horse="03", finish="03")]


def after():
    return datetime(2099, 4, 12, 3, 0, tzinfo=timezone.utc)


class CoreProviderResultsTests(unittest.TestCase):
    def test_provisional_podium_matched_to_frozen_research_not_predictions(self):
        saved = snapshots()
        original = copy.deepcopy(saved)
        output = compare_three_core_provider_results(
            saved, complete(), DAY, now=after())
        self.assertEqual(saved, original)
        self.assertEqual(output["raceCount"], 2)
        self.assertEqual(output["observedRaceCount"], 1)
        self.assertEqual(output["observedStudiedWinnerCount"], 1)
        first, second = output["races"]
        self.assertEqual(first["providerStatus"], "podium_observed")
        self.assertEqual(first["observedPodiumNumbers"], [1, 2, 3])
        self.assertEqual(first["scoredRunnerCount"], 2)
        self.assertEqual(first["winnerStudyScore70"], 50.0)
        self.assertEqual(first["winnerStudyBands"], {
            "training": "S", "course_distance": "A", "pace": "B"})
        self.assertTrue(first["studiedWinnerObserved"])
        self.assertFalse(first["officialVerified"])
        self.assertEqual(second["providerStatus"], "pending")
        self.assertIsNone(second["observedPodiumNumbers"])
        self.assertIsNone(second["studiedWinnerObserved"])
        self.assertEqual(output["winnerBandCounts"]["training"]["S"], 1)
        self.assertEqual(sum(output["winnerBandCounts"]["pace"].values()), 1)
        for flag in ("officialJraVerified","officialFeedConnected",
                     "jraIndependentConfirmation","outcomeCalibrationReady",
                     "bettingReady","actualPurchase","payoutVerified"):
            self.assertFalse(output[flag])
        self.assertEqual(output["verifiedRaceCount"], 0)
        self.assertIsNone(output["confirmedHitCount"])
        self.assertIsNone(output["modelAccuracyPercent"])
        self.assertIsNone(output["roiPercent"])
        self.assertNotIn("racekey", repr(output))
        self.assertNotIn("horse_id", repr(output))
        self.assertNotIn("trifectaTickets", repr(output))

    def test_unscored_winner_stays_unknown_not_zero_or_miss(self):
        out = compare_three_core_provider_results(snapshots(), [
            row(horse="03",finish="1"),
            row(horse="02",finish="2"),
            row(horse="01",finish="3")
        ], DAY, now=after())
        self.assertEqual(out["observedRaceCount"], 1)
        self.assertEqual(out["observedStudiedWinnerCount"], 0)
        first = out["races"][0]
        self.assertFalse(first["studiedWinnerObserved"])
        self.assertIsNone(first["winnerStudyScore70"])
        self.assertIsNone(first["winnerStudyBands"])
        self.assertEqual(sum(out["winnerBandCounts"]["training"].values()), 0)

    def test_no_outcome_before_start_or_incomplete_conflicting_result(self):
        base = snapshots()
        early = datetime(2099,4,12,0,40,tzinfo=timezone.utc)
        out = compare_three_core_provider_results(
            base, complete(), DAY, now=early)
        self.assertEqual(out["observedRaceCount"], 0)
        self.assertEqual(out["races"][0]["providerStatus"], "pending")
        self.assertEqual(out["winnerBandCounts"]["training"]["S"], 0)
        for bad in (
            [], [row()],
            [row(horse="01",finish="1"),row(horse="02",finish="2")],
            [row(horse="01",finish="1"),row(horse="02",finish="1"),
             row(horse="03",finish="3")],
            [row(horse="01",finish="1"),row(horse="01",finish="2"),
             row(horse="03",finish="3")],
            [row(horse="01",finish="1"),row(horse="02",finish="2"),
             row(horse="03",finish="3",trouble_classification="1")],
            [row(horse="01",finish="1"),row(horse="02",finish="2"),
             row(horse="03",finish="withdrawn")],
            [*complete(),row(horse="04",finish="4",track="05",race="01",
                             racekey="0599cc01")],
        ):
            with self.subTest(bad=bad):
                result=compare_three_core_provider_results(
                    base, bad, DAY, now=after())
                self.assertEqual(result["observedRaceCount"], 0)
                self.assertIsNone(result["races"][0]["winnerStudyScore70"])
        with self.assertRaises(CoreReceiptError):
            compare_three_core_provider_results(base, [], DAY,
                                                now=after(),source_read_count=2)
        with self.assertRaises(CoreReceiptError):
            compare_three_core_provider_results(base,[row()],DAY,
                                                now=after(),source_read_count=0)
        safe = compare_three_core_provider_results(
            base, [], DAY, now=early, source_read_count=0)
        self.assertEqual(safe["providerSourceReadCount"], 0)

    def test_provisional_three_place_rows_cannot_override_sealed_runner_count(self):
        # Synthetic 2-runner Kyoto slot cannot legitimately contain a
        # 1st/2nd/3rd podium. Treat the whole conflicting race as pending.
        rows = complete() + [
            row(track="08",race="02",horse="04",finish="1"),
            row(track="08",race="02",horse="05",finish="2"),
            row(track="08",race="02",horse="07",finish="3"),
        ]
        output = compare_three_core_provider_results(
            snapshots(), rows, DAY, now=after())
        self.assertEqual(output["observedRaceCount"], 1)
        self.assertEqual(output["races"][1]["providerStatus"], "pending")
        self.assertIsNone(output["races"][1]["observedPodiumNumbers"])
        self.assertEqual(output["observedStudiedWinnerCount"], 1)

    def test_bad_source_identity_rejected_not_assimilated(self):
        for bad in (
            {**row(),"horse_number":"1"},
            {**row(),"horse_number":"19"},
            {**row(),"racedate":"20990413"},
            {**row(),"racekey":"0526ab01"},
            {**row(),"racekey":"05BADS00"},
            {**row(),"racekey":"05000013"},
            {**row(),"order_of_finish":1},
            {**row(),"racekey":"NOT_REAL"},
        ):
            with self.subTest(bad=bad),self.assertRaises(CoreReceiptError):
                compare_three_core_provider_results(snapshots(),[bad],
                                                    DAY,now=after())

    def test_private_endpoint_one_tse_call_and_no_result_injection(self):
        history,programme,before=source()
        signed=issue_three_core_receipts(
            history,programme,SECRET,DAY,before)["receipts"]
        opts={**SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
              "KEIBA_RENDER_PREVIEW_ONLY":"0",
              "JRDB_PRIVATE_ENABLED":"1",
              "JRDB_API_KEY":"synthetic", "JRDB_AUTH_KEY":"synthetic"}
        app=create_app(opts)
        with (patch("private_service.fetch_finished_race_results",
                    return_value=complete()) as fetch,
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T12:00:00+09:00")):
            response=call(app,"/api/owner-three-core-provider-check",
                          method="POST",data={"date":DAY,"receipts":signed})
            fetch.assert_called_once_with(DAY)
        self.assertEqual(response["status"],"200 OK")
        body=json.loads(response["body"])
        self.assertEqual(body["observedRaceCount"],1)
        self.assertFalse(body["officialJraVerified"])
        self.assertIsNone(body["modelAccuracyPercent"])
        self.assertNotIn("racekey",response["body"].decode())
        self.assertNotIn("horse_id",response["body"].decode())
        with patch("private_service.fetch_finished_race_results") as fetch:
            for bad in (
                {"date":DAY,"receipts":signed,"winner":1},
                {"date":DAY,"receipts":signed,"results":complete()},
                {"date":DAY,"receipts":[]},
                {"date":DAY,"receipts":[{**signed[0],"signature":"f"*64}]},
            ):
                self.assertEqual(
                    call(app,"/api/owner-three-core-provider-check",
                         method="POST",data=bad)["status"],"400 Bad Request")
            fetch.assert_not_called()
        self.assertEqual(
            call(app,"/api/owner-three-core-provider-check",
                 method="POST",auth="",data={"date":DAY,"receipts":signed})["status"],
            "401 Unauthorized")
        no_api=create_app({**opts,"JRDB_PRIVATE_ENABLED":"0"})
        self.assertEqual(
            call(no_api,"/api/owner-three-core-provider-check",
                 method="POST",data={"date":DAY,"receipts":signed})["status"],
            "503 Service Unavailable")
        self.assertEqual(
            call(create_app(SETTINGS),"/api/owner-three-core-provider-check",
                 method="POST",data={"date":DAY,"receipts":signed})["status"],
            "404 Not Found")

    def test_no_provider_read_before_any_original_off(self):
        history,programme,before=source()
        signed=issue_three_core_receipts(
            history,programme,SECRET,DAY,before)["receipts"]
        app=create_app({**SETTINGS,
             "KEIBA_RENDER_PRIVATE_ONLY":"1",
             "KEIBA_RENDER_PREVIEW_ONLY":"0",
             "JRDB_PRIVATE_ENABLED":"1",
             "JRDB_API_KEY":"synthetic","JRDB_AUTH_KEY":"synthetic"})
        with (patch("private_service.fetch_finished_race_results") as fetch,
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T09:40:00+09:00")):
            response=call(app,"/api/owner-three-core-provider-check",
                          method="POST",data={"date":DAY,"receipts":signed})
            fetch.assert_not_called()
        self.assertEqual(response["status"],"200 OK")
        data=json.loads(response["body"])
        self.assertEqual(data["providerSourceReadCount"],0)
        self.assertEqual(data["observedRaceCount"],0)
        self.assertTrue(all(r["providerStatus"]=="pending" for r in data["races"]))

if __name__ == "__main__":
    unittest.main()
