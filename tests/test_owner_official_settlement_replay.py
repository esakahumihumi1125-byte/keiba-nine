"""Synthetic settlements: signed early tickets, multiple 3連単 and refunds.

All source URLs in this test use a fictitious 2099 date. These tests never
fetch JRA, connect JRDB, persist data or claim official verification.
"""
import copy
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_official_settlement_replay import (
    SCHEMA, SettlementReplayError, replay_attested_settlements,
    sign_authenticated_source_record,
)
from owner_prestart_receipt import issue_preview_receipts
from test_owner_prestart_receipt import DAY, forecast, sample_race
from test_private_service import SETTINGS

RESULT_SECRET = "abcdefghijklmNOPQRSTUVWXYZ0123456789!@#$%^&*()_+=-K9"
PASS = SETTINGS["KEIBA_OWNER_PASSWORD"]
NOW = datetime(2099, 4, 12, 4, 0, tzinfo=timezone.utc)


def receipts():
    original = forecast(sample_race(), sample_race("京都", 2))
    return issue_preview_receipts(
        original, PASS, DAY,
        now=datetime(2099, 4, 11, 9, 0, tzinfo=timezone.utc)
    )["receipts"]


def payload(track="東京", race=1, status="settled"):
    return {
        "schema": SCHEMA,
        "date": DAY, "track": track, "race": race,
        "sourceUrl": "https://www.jra.go.jp/JRADB/accessS.html?"
                     "CNAME=pw01sde0105209901010120990412%2FAB",
        "sourceCollectedAt": "2099-04-12T11:25:00+09:00",
        "finalizedAt": "2099-04-12T11:00:00+09:00",
        "status": status,
        "trifectaPayouts": [
            {"ticket": [1, 2, 3], "payoutYen": 26050},
            {"ticket": [1, 2, 4], "payoutYen": 48920},
        ] if status == "settled" else [],
        "trioPayouts": [] ,
        "trifectaRefunds": [
            {"ticket": [2, 1, 3]}
        ] if status == "settled" else [],
        "trioRefunds": [],
        "sourceVerificationMethod": "server_authenticated_jra_page",
    }


def attest(item):
    return sign_authenticated_source_record(item, RESULT_SECRET)


class MultiWinnerSettlementReplayTests(unittest.TestCase):
    def test_two_distinct_dead_heat_payouts_refund_and_pending_race(self):
        before = receipts()
        official_shape = payload()
        untouched = copy.deepcopy((before, official_shape))
        out = replay_attested_settlements(
            before, PASS, DAY, [attest(official_shape)], RESULT_SECRET, now=NOW)
        self.assertEqual((before, official_shape), untouched)
        self.assertEqual(out["raceCount"], 2)
        self.assertEqual(out["attestedReplayRaces"], 1)
        self.assertEqual(out["pendingRaces"], 1)
        first = next(r for r in out["races"] if r["track"] == "東京")
        self.assertTrue(first["trifectaHit"])
        self.assertEqual(first["ticketCount"], 8)
        self.assertEqual(first["grossStakeYen"], 800)
        self.assertEqual(first["refundedTicketCount"], 1)
        self.assertEqual(first["returnedYen"], 26050+48920+100)
        self.assertEqual(out["returnedYen"], 75070)
        self.assertEqual(out["grossStakeYen"], 800)
        self.assertEqual(out["netYen"], 74270)
        self.assertEqual(out["pendingRaces"], 1)
        self.assertFalse(out["officialJraVerified"])
        self.assertFalse(out["independentJraFeedConnected"])
        self.assertFalse(out["sourceRecordsIndependentlyValidatedHere"])
        self.assertIsNone(out["officialRoiPercent"])
        self.assertFalse(out["actualPurchase"])
        self.assertFalse(out["changesExistingOfficialRoi"])
        for disallowed in ("trifectaTickets", "sourceUrl", "finalizedAt",
                           "20990412", "signature", "JRA_API_KEY"):
            self.assertNotIn(disallowed, repr(out))

    def test_cancelled_race_refunds_exactly_one_hundred_per_saved_ticket(self):
        saved = receipts()
        cancel = payload("東京", 1, "cancelled")
        out = replay_attested_settlements(
            saved, PASS, DAY, [attest(cancel)], RESULT_SECRET, now=NOW)
        race = out["races"][0]
        self.assertEqual(race["grossStakeYen"], 800)
        self.assertEqual(race["returnedYen"], 800)
        self.assertEqual(race["refundedTicketCount"], 8)
        self.assertFalse(race["trifectaHit"])
        self.assertEqual(out["replayRoiPercent"], 100.0)
        self.assertIsNone(out["officialRoiPercent"])

    def test_no_authoritative_results_means_pending_not_zero_return(self):
        out = replay_attested_settlements(
            receipts(), PASS, DAY, [], RESULT_SECRET, now=NOW)
        self.assertEqual(out["attestedReplayRaces"], 0)
        self.assertEqual(out["pendingRaces"], 2)
        self.assertEqual(out["grossStakeYen"], 0)
        self.assertEqual(out["returnedYen"], 0)
        self.assertIsNone(out["replayRoiPercent"])
        self.assertTrue(all(r["returnedYen"] is None for r in out["races"]))

    def test_signed_source_and_frozen_ticket_tampering_are_rejected(self):
        original = receipts()
        valid = attest(payload())
        changes = (
            lambda p: p["payload"]["trifectaPayouts"][0].update(payoutYen=10**8),
            lambda p: p["payload"].update(date="2099-04-13"),
            lambda p: p.update(signature="0"*64),
            lambda p: p["payload"]["trifectaRefunds"].append(
                {"ticket": [1, 2, 3]}),
        )
        for change in changes:
            modified = copy.deepcopy(valid)
            change(modified)
            with self.subTest(change=repr(change)), self.assertRaises(SettlementReplayError):
                replay_attested_settlements(
                    original, PASS, DAY, [modified], RESULT_SECRET, now=NOW)
        changed_receipts = copy.deepcopy(original)
        changed_receipts[0]["snapshot"]["trifectaTickets"][0] = [1, 5, 6]
        with self.assertRaises(SettlementReplayError):
            replay_attested_settlements(
                changed_receipts, PASS, DAY, [valid], RESULT_SECRET, now=NOW)
        with self.assertRaises(SettlementReplayError):
            replay_attested_settlements(
                original, PASS, DAY, [valid, valid], RESULT_SECRET, now=NOW)
        with self.assertRaises(SettlementReplayError):
            replay_attested_settlements(
                original, PASS, DAY, [valid], "bad-key", now=NOW)

    def test_invalid_source_or_unconfirmed_outcomes_never_become_settled(self):
        transforms = (
            lambda p: p.update(sourceUrl="https://jra.go.jp.evil.net/JRADB/accessS.html"),
            lambda p: p.update(sourceUrl="http://www.jra.go.jp/JRADB/accessS.html"),
            lambda p: p.update(sourceUrl="https://www.jra.go.jp/JRADB/accessS.html?CNAME=pw01sde20990413"),
            lambda p: p.update(sourceVerificationMethod="operator_transcription"),
            lambda p: p.update(sourceCollectedAt="2099-04-12T10:00:00+09:00"),
            lambda p: p["trifectaPayouts"].append({"ticket": [1, 2, 3], "payoutYen": 40000}),
            lambda p: p["trifectaPayouts"][0].update(payoutYen=99),
            lambda p: p["trifectaRefunds"].append({"ticket": [1, 2, 3]}),
            lambda p: p["trifectaPayouts"].append({"ticket": [1, 2, 2], "payoutYen": 1000}),
            lambda p: p.update(officialVerified=True),
        )
        for change in transforms:
            p = payload()
            change(p)
            with self.subTest(change=repr(change)), self.assertRaises(SettlementReplayError):
                attest(p)
        # A result stamped before a race can be sealed syntactically,
        # but the independent replay must reject it against the locked off-time.
        pre_off = payload()
        pre_off["finalizedAt"] = "2099-04-12T09:00:00+09:00"
        with self.assertRaises(SettlementReplayError):
            replay_attested_settlements(
                receipts(), PASS, DAY, [attest(pre_off)], RESULT_SECRET, now=NOW)
        valid = attest(payload())
        with self.assertRaises(SettlementReplayError):
            replay_attested_settlements(
                receipts(), PASS, DAY, [valid], RESULT_SECRET,
                now=datetime(2099, 4, 12, 1, 30, tzinfo=timezone.utc))
        another = attest(payload(track="阪神"))
        with self.assertRaises(SettlementReplayError):
            replay_attested_settlements(
                receipts(), PASS, DAY, [another], RESULT_SECRET, now=NOW)


if __name__ == "__main__":
    unittest.main()
