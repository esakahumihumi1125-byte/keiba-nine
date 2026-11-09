"""Synthetic JRDB/TSE reference-only inspection of sealed trifecta tickets."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_prestart_receipt import issue_preview_receipts, verify_preview_receipts
from owner_prestart_tse_review import (
    compare_prestart_tickets, ProvisionalResultError
)
from test_owner_prestart_receipt import forecast, sample_race, DAY
from test_private_service import call, SETTINGS
from private_service import create_app

SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]
EARLY = datetime(2099, 4, 12, 0, 0, tzinfo=timezone.utc)
AFTER = datetime(2099, 4, 12, 3, 0, tzinfo=timezone.utc)


def receipts():
    signed = issue_preview_receipts(
        forecast(sample_race(), sample_race("京都", 2, time="14:00")),
        SECRET, DAY, now=EARLY)["receipts"]
    return signed, verify_preview_receipts(signed, SECRET, DAY)


def result(track="05", race="01", horse="01", finish="1", **extra):
    return {
        "racekey": track + "99ab" + race,
        "racedate": DAY.replace("-", ""),
        "horse_number": horse, "order_of_finish": finish, **extra,
    }


def podium(winner="01", second="02", third="03"):
    return [
        result(horse=winner, finish="01"),
        result(horse=second, finish="02"),
        result(horse=third, finish="03"),
    ]


class ProvisionalTicketTests(unittest.TestCase):
    def test_frozen_trifecta_observation_no_roi_or_official_hit(self):
        signed, frozen = receipts()
        before = copy.deepcopy(frozen)
        view = compare_prestart_tickets(frozen, podium(), DAY, now=AFTER)
        self.assertEqual(frozen, before)
        self.assertEqual(view["raceCount"], 2)
        self.assertEqual(view["observedRaceCount"], 1)
        self.assertEqual(view["pendingRaceCount"], 1)
        self.assertEqual(view["provisionalExactCombinationCount"], 1)
        self.assertEqual(view["provisionalFirstCandidateCount"], 1)
        first, second = view["races"]
        self.assertEqual(first["providerStatus"], "provider_podium_observed")
        self.assertTrue(first["exactCombinationObserved"])
        self.assertTrue(first["firstCandidateObserved"])
        self.assertTrue(first["secondCandidateObserved"])
        self.assertTrue(first["thirdCandidateObserved"])
        self.assertEqual(first["firstMissType"], "first_candidate")
        self.assertEqual(second["providerStatus"], "pending")
        self.assertIsNone(second["exactCombinationObserved"])
        for k in ("officialJraVerified", "independentJraVerified",
                  "payoutVerified", "realPredictionReady", "actualPurchase",
                  "bettingReady", "changesExistingReceipts"):
            self.assertFalse(view[k])
        self.assertIsNone(view["officialHitCount"])
        self.assertIsNone(view["roiPercent"])
        for raw_key in ("racekey", "horse_number", "order_of_finish",
                        "trifectaTickets", "scheduledOffAt", "JRDB_API_KEY"):
            self.assertNotIn(raw_key, repr(view))
        self.assertEqual(view["providerReadCount"], 1)
        self.assertFalse(any("Yen" in key for key in view))

    def test_winner_wrong_slot_versus_not_selected(self):
        frozen = receipts()[1]
        wrong = compare_prestart_tickets(
            frozen, podium("03", "01", "02"), DAY, now=AFTER)
        self.assertEqual(wrong["races"][0]["firstMissType"], "wrong_slot")
        self.assertFalse(wrong["races"][0]["firstCandidateObserved"])
        self.assertFalse(wrong["races"][0]["exactCombinationObserved"])
        absent = compare_prestart_tickets(
            frozen, podium("05", "02", "03"), DAY, now=AFTER)
        self.assertEqual(absent["races"][0]["firstMissType"], "not_selected")
        self.assertEqual(absent["provisionalFirstCandidateCount"], 0)
        self.assertEqual(absent["provisionalExactCombinationCount"], 0)

    def test_partial_ambiguous_and_preoff_are_pending(self):
        frozen = receipts()[1]
        first_off = datetime(2099, 4, 12, 0, 30, tzinfo=timezone.utc)
        view = compare_prestart_tickets(
            frozen, podium(), DAY, now=first_off)
        self.assertEqual(view["observedRaceCount"], 0)
        self.assertEqual(view["pendingRaceCount"], 2)
        self.assertEqual(
            compare_prestart_tickets(frozen, [], DAY,
                                     now=first_off, source_read_count=0)["providerReadCount"],
            0)
        for rows in (
            [], podium()[:2],
            podium() + [result(horse="04", finish="1")],
            podium() + [result(horse="01", finish="04")],
            podium() + [result(horse="04", finish="4", racekey="0599cc01")],
            [*podium()[:2], result(horse="03", finish="withdrawn")],
            [*podium()[:2], result(horse="03", finish="03",
                                    trouble_classification="1")],
        ):
            with self.subTest(rows=rows):
                report = compare_prestart_tickets(frozen, rows, DAY, now=AFTER)
                self.assertEqual(report["observedRaceCount"], 0)
                self.assertIsNone(report["races"][0]["firstMissType"])
        with self.assertRaises(ProvisionalResultError):
            compare_prestart_tickets(frozen, podium(), DAY,
                                     now=AFTER, source_read_count=0)
        with self.assertRaises(ProvisionalResultError):
            compare_prestart_tickets(frozen, [], DAY,
                                     now=datetime(2099, 4, 12, 3, 0))

    def test_bad_provider_rows_fail_closed(self):
        frozen = receipts()[1]
        for bad in (
            {**result(), "racedate": "20990413"},
            {**result(), "horse_number": "1"},
            {**result(), "horse_number": "19"},
            {**result(), "order_of_finish": 1},
            {**result(), "racekey": "0599ab13"},
            {**result(), "racekey": "NOTREAL"},
        ):
            with self.subTest(bad=bad), self.assertRaises(ProvisionalResultError):
                compare_prestart_tickets(frozen, [bad], DAY, now=AFTER)

    def test_authenticated_endpoint_one_call_and_no_injected_results(self):
        signed, frozen = receipts()
        opts = {**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                "KEIBA_RENDER_PREVIEW_ONLY": "0", "JRDB_PRIVATE_ENABLED": "1",
                "JRDB_API_KEY": "synthetic", "JRDB_AUTH_KEY": "synthetic"}
        app = create_app(opts)
        with (patch("private_service.fetch_finished_race_results",
                    return_value=podium()) as fetched,
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T12:00:00+09:00")):
            response = call(app, "/api/owner-prestart-tse-review",
                            method="POST", data={"date": DAY, "receipts": signed})
            fetched.assert_called_once_with(DAY.replace("-", ""))
        self.assertEqual(response["status"], "200 OK")
        payload = json.loads(response["body"])
        self.assertEqual(payload["observedRaceCount"], 1)
        self.assertFalse(payload["officialJraVerified"])
        self.assertIsNone(payload["roiPercent"])
        self.assertNotIn("racekey", response["body"].decode())
        self.assertNotIn("trifectaTickets", response["body"].decode())
        with patch("private_service.fetch_finished_race_results") as fetched:
            for injection in (
                {"date": DAY, "receipts": signed, "finish": [1, 2, 3]},
                {"date": DAY, "receipts": signed, "payout": 250000},
                {"date": DAY, "receipts": []},
                {"date": DAY, "receipts": [
                    {**signed[0], "signature": "f" * 64}]},
            ):
                self.assertEqual(
                    call(app, "/api/owner-prestart-tse-review",
                         method="POST", data=injection)["status"],
                    "400 Bad Request")
            fetched.assert_not_called()
        self.assertEqual(
            call(app, "/api/owner-prestart-tse-review", method="POST",
                 auth="", data={"date": DAY, "receipts": signed})["status"],
            "401 Unauthorized")
        self.assertEqual(
            call(create_app(SETTINGS), "/api/owner-prestart-tse-review",
                 method="POST", data={"date": DAY, "receipts": signed})["status"],
            "404 Not Found")

    def test_no_provider_read_before_off_and_no_paid_settings(self):
        signed, _ = receipts()
        app = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                          "KEIBA_RENDER_PREVIEW_ONLY": "0",
                          "JRDB_PRIVATE_ENABLED": "1", "JRDB_API_KEY": "synthetic",
                          "JRDB_AUTH_KEY": "synthetic"})
        with (patch("private_service.fetch_finished_race_results") as fetched,
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T09:00:00+09:00")):
            reply = call(app, "/api/owner-prestart-tse-review",
                         method="POST", data={"date": DAY, "receipts": signed})
            fetched.assert_not_called()
        self.assertEqual(reply["status"], "200 OK")
        self.assertEqual(json.loads(reply["body"])["providerReadCount"], 0)
        no_access = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                                "KEIBA_RENDER_PREVIEW_ONLY": "0",
                                "JRDB_PRIVATE_ENABLED": "0"})
        self.assertEqual(
            call(no_access, "/api/owner-prestart-tse-review",
                 method="POST", data={"date": DAY, "receipts": signed})["status"],
            "503 Service Unavailable")


if __name__ == "__main__":
    unittest.main()
