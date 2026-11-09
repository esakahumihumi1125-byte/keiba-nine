"""Frozen-before-off, 100-yen hypothetical accounting regression tests."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from keiba_100yen_review import review_100yen, ReviewInputError


def snapshot(race=1):
    return {
        "date": "2026-11-08", "track": "東京", "race": race,
        "sourceKind": "prestart-locked", "actualPurchase": False,
        "lockedAt": "2026-11-07T20:00:00+09:00",
        "scheduledOffAt": "2026-11-08T10:00:00+09:00",
        "trifectaTickets": [[1, 2, 3], [2, 1, 3], [1, 2, 3]],
        "trioTickets": [[3, 1, 2]],
    }


def outcome(race=1, verified=True):
    return {
        "date": "2026-11-08", "track": "東京", "race": race,
        "officialVerified": verified,
        "finish": [1, 2, 3],
        "trifectaPer100Yen": 474290,
        "trioPer100Yen": 5300,
    }


class HypotheticalReviewTests(unittest.TestCase):
    def test_exact_payout_includes_one_100yen_stake_per_unique_point(self):
        prediction, result = snapshot(), outcome()
        frozen = copy.deepcopy((prediction, result))
        review = review_100yen([prediction], [result])
        self.assertEqual(review["reviewedRaces"], 1)
        self.assertEqual(review["totalInvestedYen"], 300)
        self.assertEqual(review["totalReturnedYen"], 479590)
        self.assertEqual(review["totalProfitYen"], 479290)
        self.assertEqual(review["trifectaHits"], 1)
        self.assertEqual(review["trioHits"], 1)
        self.assertTrue(review["races"][0]["firstCandidateHit"])
        self.assertFalse(review["actualPurchase"])
        self.assertEqual((prediction, result), frozen)

    def test_wrong_order_loses_trifecta_but_can_hit_trio(self):
        prediction, result = snapshot(), outcome()
        result["finish"] = [3, 1, 2]
        out = review_100yen([prediction], [result])
        self.assertEqual(out["trifectaHits"], 0)
        self.assertEqual(out["trioHits"], 1)
        self.assertEqual(out["totalReturnedYen"], 5300)
        self.assertFalse(out["races"][0]["firstCandidateHit"])

    def test_unverified_or_missing_result_remains_pending(self):
        data = [snapshot(1), snapshot(2)]
        for results in ([outcome(1, False)], []):
            with self.subTest(results=results):
                result = review_100yen(data, results)
                self.assertEqual(result["reviewedRaces"], 0)
                self.assertEqual(result["pendingRaces"], 2)
                self.assertEqual(result["totalInvestedYen"], 0)
                self.assertEqual(result["totalReturnedYen"], 0)
                self.assertIsNone(result["roiPercent"])
                self.assertIsNone(result["races"][0]["hitTrifecta"])

    def test_verified_loss_is_counted_only_when_official(self):
        p, r = snapshot(), outcome()
        r["finish"] = [4, 5, 6]
        out = review_100yen([p], [r])
        self.assertEqual(out["totalInvestedYen"], 300)
        self.assertEqual(out["totalReturnedYen"], 0)
        self.assertEqual(out["roiPercent"], 0)
        self.assertEqual(out["trifectaHits"], 0)
        self.assertEqual(out["trioHits"], 0)

    def test_venue_breakdown_excludes_unverified_stakes_and_tracks_first_choices(self):
        tokyo = snapshot(1)
        kyoto = snapshot(2)
        kyoto["track"] = "京都"
        fukushima = snapshot(3)
        fukushima["track"] = "福島"
        hit = outcome(1)
        loss = outcome(2)
        loss["track"] = "京都"
        loss["finish"] = [5, 6, 7]
        report = review_100yen([tokyo, kyoto, fukushima], [hit, loss])
        self.assertEqual(report["reviewedRaces"], 2)
        self.assertEqual(report["pendingRaces"], 1)
        self.assertEqual(report["totalInvestedYen"], 600)
        self.assertEqual(report["totalReturnedYen"], 479590)
        self.assertEqual(report["pendingStakeYen"], 300)
        self.assertEqual(report["firstCandidateHits"], 1)
        self.assertEqual(report["firstCandidateEligibleRaces"], 2)
        self.assertEqual([x["track"] for x in report["venueBreakdown"]],
                         ["東京", "京都", "福島"])
        by_track = {x["track"]: x for x in report["venueBreakdown"]}
        self.assertEqual(by_track["東京"]["investedYen"], 300)
        self.assertEqual(by_track["東京"]["returnedYen"], 479590)
        self.assertEqual(by_track["京都"]["roiPercent"], 0)
        self.assertEqual(by_track["福島"]["pendingStakeYen"], 300)
        self.assertIsNone(by_track["福島"]["roiPercent"])
        self.assertEqual(by_track["福島"]["reviewedRaces"], 0)

    def test_trio_only_does_not_claim_first_place_candidate(self):
        prediction = snapshot()
        prediction["trifectaTickets"] = []
        report = review_100yen([prediction], [outcome()])
        self.assertEqual(report["firstCandidateEligibleRaces"], 0)
        self.assertEqual(report["firstCandidateHits"], 0)
        self.assertIsNone(report["races"][0]["firstCandidateHit"])
        self.assertEqual(report["totalInvestedYen"], 100)

    def test_dead_heat_refund_or_abandoned_race_wait_for_full_settlement(self):
        for flag in ("deadHeat", "refundRequired", "raceAbandoned"):
            with self.subTest(flag=flag):
                o = outcome()
                o[flag] = True
                report = review_100yen([snapshot()], [o])
                self.assertEqual(report["reviewedRaces"], 0)
                self.assertEqual(report["pendingRaces"], 1)
                self.assertEqual(report["totalInvestedYen"], 0)
                self.assertIsNone(report["roiPercent"])
                self.assertEqual(report["pendingStakeYen"], 300)

    def test_postoff_forecast_never_backtests_as_prerace(self):
        p=snapshot()
        p["lockedAt"] = p["scheduledOffAt"]
        with self.assertRaises(ReviewInputError):
            review_100yen([p], [outcome()])
        p["lockedAt"] = "2026-11-08T23:00:00+09:00"
        with self.assertRaises(ReviewInputError):
            review_100yen([p], [outcome()])

    def test_altered_results_or_false_purchase_claim_rejected(self):
        p, r = snapshot(), outcome()
        p["actualPurchase"] = True
        with self.assertRaises(ReviewInputError):
            review_100yen([p], [r])
        p["actualPurchase"] = False
        for bad in (-1, None, "5300", 10**10):
            r["trioPer100Yen"] = bad
            with self.subTest(bad=bad), self.assertRaises(ReviewInputError):
                review_100yen([p], [r])

    def test_miss_reason_identifies_uncovered_finishing_slot(self):
        scenarios = (
            ([1, 2, 3], "trifecta_hit"),
            ([3, 1, 2], "winner_wrong_slot"),
            ([4, 2, 3], "winner_not_selected"),
            ([1, 3, 2], "second_wrong_slot"),
            ([1, 4, 3], "second_not_selected"),
            ([1, 2, 4], "third_not_selected"),
        )
        for finish, expected in scenarios:
            with self.subTest(finish=finish):
                outcome_row = outcome()
                outcome_row["finish"] = finish
                result = review_100yen([snapshot()], [outcome_row])
                self.assertEqual(result["races"][0]["trifectaMissReason"], expected)
                self.assertEqual(result["trifectaMissReasons"][expected], 1)
                self.assertEqual(
                    result["venueBreakdown"][0]["trifectaMissReasons"][expected], 1
                )
                self.assertEqual(sum(result["trifectaMissReasons"].values()), 1)

    def test_no_exact_combination_despite_each_place_covered(self):
        prediction = snapshot()
        prediction["trifectaTickets"] = [[1, 2, 4], [2, 3, 5]]
        prediction["trioTickets"] = []
        result_row = outcome()
        result_row["finish"] = [1, 3, 5]
        result = review_100yen([prediction], [result_row])
        self.assertEqual(result["races"][0]["trifectaMissReason"],
                         "combination_missing")
        self.assertFalse(result["races"][0]["hitTrifecta"])

    def test_pending_and_trio_only_have_no_false_miss_reason(self):
        prediction = snapshot()
        pending = review_100yen([prediction], [])
        self.assertIsNone(pending["races"][0]["trifectaMissReason"])
        self.assertEqual(sum(pending["trifectaMissReasons"].values()), 0)
        trio = snapshot()
        trio["trifectaTickets"] = []
        report = review_100yen([trio], [outcome()])
        self.assertIsNone(report["races"][0]["trifectaMissReason"])
        self.assertEqual(sum(report["trifectaMissReasons"].values()), 0)
        self.assertTrue(report["races"][0]["hitTrio"])

    def test_duplicate_race_or_invalid_tickets_fail_closed(self):
        p = snapshot()
        with self.assertRaises(ReviewInputError):
            review_100yen([p,p], [outcome()])
        with self.assertRaises(ReviewInputError):
            review_100yen([p], [outcome(),outcome()])
        for bad in ([[1,1,2]], [[1,2,"3"]], [[0,1,2]], [[19,1,2]]):
            q = snapshot()
            q["trifectaTickets"] = bad
            with self.subTest(bad=bad), self.assertRaises(ReviewInputError):
                review_100yen([q], [outcome()])


if __name__ == "__main__":
    unittest.main()
