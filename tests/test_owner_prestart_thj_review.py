"""Synthetic-only tests: signed-prestart JRDB 100-yen return observations."""
import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_prestart_thj_review import compare_verified_prestart_thj

JST = timezone(timedelta(hours=9))
DATE = "2026-11-15"
NOW = datetime(2026, 11, 15, 18, 0, tzinfo=JST)


def receipt(track="東京", race=1, tickets=None):
    return {
        "date": DATE, "track": track, "race": race,
        "sourceKind": "prestart-locked", "actualPurchase": False,
        "lockedAt": "2026-11-15T09:00:00+09:00",
        "scheduledOffAt": "2026-11-15T12:00:00+09:00",
        "trifectaTickets": tickets or [[1, 2, 3], [1, 3, 2]],
        "trioTickets": [],
    }


def payoff(first="01-02-03", amount=26050, racekey="05264b01"):
    return {
        "racedate": "20261115", "racekey": racekey,
        "trifecta_number_1": first, "trifecta_payoff_1": amount,
        "trifecta_number_2": None, "trifecta_payoff_2": 0,
    }


class ThjReturnReferenceTests(unittest.TestCase):
    def test_signed_picks_match_provider_payoff_without_writing(self):
        saved = [receipt()]
        raw = [payoff()]
        original = copy.deepcopy((saved, raw))
        out = compare_verified_prestart_thj(saved, raw, DATE, now=NOW)
        self.assertEqual(out["providerReadCount"], 1)
        self.assertEqual((out["observedRaces"], out["pendingRaces"]), (1, 0))
        self.assertEqual(out["reviewedInvestedYen"], 200)
        self.assertEqual(out["reviewedReturnedYen"], 26050)
        self.assertEqual(out["reviewedProfitYen"], 25850)
        self.assertEqual(out["reviewedRoiPercent"], 13025.0)
        self.assertEqual(out["providerMatchedRaces"], 1)
        self.assertEqual(out["races"][0]["providerMatchedTickets"], 1)
        self.assertEqual((saved, raw), original)
        self.assertFalse(out["officialJraVerified"])
        self.assertFalse(out["payoutOfficiallyVerified"])
        self.assertFalse(out["actualPurchase"])
        self.assertFalse(out["writesPersistentResults"])
        self.assertNotIn("racekey", repr(out))

    def test_legacy_compact_and_multiple_dead_heat_combinations(self):
        row = payoff("010203", 26050)
        row.update(trifecta_number_2="01-03-02", trifecta_payoff_2=48920)
        out = compare_verified_prestart_thj(
            [receipt()], [row], DATE, now=NOW)
        self.assertEqual(out["races"][0]["providerMatchedTickets"], 2)
        self.assertEqual(out["reviewedReturnedYen"], 74970)

    def test_valid_miss_is_zero_but_unknown_result_is_pending(self):
        saved = [receipt()]
        no_hit = compare_verified_prestart_thj(
            saved, [payoff("02-03-01", 1200)], DATE, now=NOW)
        self.assertEqual(no_hit["reviewedReturnedYen"], 0)
        self.assertEqual(no_hit["reviewedProfitYen"], -200)
        self.assertEqual(no_hit["reviewedRoiPercent"], 0)
        no_rows = compare_verified_prestart_thj(saved, [], DATE, now=NOW)
        self.assertEqual(no_rows["observedRaces"], 0)
        self.assertIsNone(no_rows["reviewedRoiPercent"])
        self.assertEqual(no_rows["pendingStakeYen"], 200)
        blank = compare_verified_prestart_thj(
            saved, [payoff(first=None, amount=0)], DATE, now=NOW)
        self.assertEqual(blank["races"][0]["status"], "pending")

    def test_refund_and_unknown_format_do_not_fabricate_losses(self):
        ref = payoff()
        ref["refund_number_1"] = "05"
        result = compare_verified_prestart_thj(
            [receipt()], [ref], DATE, now=NOW)
        self.assertEqual(result["races"][0]["status"], "refund_review")
        self.assertIsNone(result["races"][0]["returnedYen"])
        self.assertEqual(result["reviewedInvestedYen"], 0)
        strange = payoff("1>2>3")
        result = compare_verified_prestart_thj(
            [receipt()], [strange], DATE, now=NOW)
        self.assertEqual(result["races"][0]["status"], "format_review")
        self.assertEqual(result["pendingStakeYen"], 200)
        mismatch = payoff()
        mismatch["trifecta_payoff_1"] = None
        self.assertEqual(compare_verified_prestart_thj(
            [receipt()], [mismatch], DATE, now=NOW)["pendingRaces"], 1)

    def test_prestart_never_exposes_provider_results_or_roi(self):
        before = datetime(2026, 11, 15, 11, 0, tzinfo=JST)
        data = compare_verified_prestart_thj(
            [receipt()], [], DATE, now=before, provider_read_count=0)
        self.assertEqual(data["races"][0]["status"], "pending")
        self.assertIsNone(data["reviewedRoiPercent"])
        with self.assertRaises(CoverageError):
            compare_verified_prestart_thj(
                [receipt()], [payoff()], DATE, now=before,
                provider_read_count=0)
        # Even if caller erroneously supplied after-race provider rows,
        # the race must still remain pending before the signed off time.
        hold = compare_verified_prestart_thj(
            [receipt()], [payoff()], DATE, now=before)
        self.assertEqual(hold["observedRaces"], 0)

    def test_wrong_year_date_duplicate_or_malformed_source_is_rejected(self):
        for data in (
            [payoff(racekey="05254b01")],
            [payoff(racekey="05264b00")],
            [payoff(racekey="11264b01")],
            [payoff(), payoff()],
            [dict(payoff(), racedate="20261114")],
        ):
            with self.subTest(data=data):
                with self.assertRaises(CoverageError):
                    compare_verified_prestart_thj([receipt()], data, DATE, now=NOW)

    def test_broken_or_retroactive_receipts_are_rejected(self):
        bad = receipt()
        bad["trifectaTickets"] = [[1, 2, 3], [1, 2, 3]]
        with self.assertRaises(CoverageError):
            compare_verified_prestart_thj([bad], [payoff()], DATE, now=NOW)
        bad2 = receipt()
        bad2["lockedAt"] = "2026-11-15T13:00:00+09:00"
        with self.assertRaises(CoverageError):
            compare_verified_prestart_thj([bad2], [payoff()], DATE, now=NOW)
        with self.assertRaises(CoverageError):
            compare_verified_prestart_thj(
                [receipt(), receipt()], [payoff()], DATE, now=NOW)


if __name__ == "__main__":
    unittest.main()
