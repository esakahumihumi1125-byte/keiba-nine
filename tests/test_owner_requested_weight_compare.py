"""Provenance-gated 100-vs-105 research policy comparison tests."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests"))

from evaluation_policy import OWNER_FORMAL_FACTORS
from owner_full_ten_factor import full_ten_factor_preview
from owner_requested_weight_compare import compare_verified_policies
from test_owner_full_ten_factor import fixture, NOW, OFF, AS_OF


class OwnerRequestedWeightCompareTests(unittest.TestCase):
    def test_exact_reversal_no_ordering_by_rounded_score(self):
        source = fixture()
        for horse in source["horses"]:
            for item in horse["assessments"].values():
                item["grade"] = "C"
        for item in source["horses"][0]["assessments"].values():
            item["grade"] = "S"
        for item in source["horses"][1]["assessments"].values():
            item["grade"] = "S"
        # Under research-6 horse 1 loses 15 points, horse 2 loses 16.
        # Under the requested 105 weights horse 1 loses 20 points and
        # horse 2 loses 16, so the ordered pair reverses.
        source["horses"][0]["assessments"]["ground"]["grade"] = "C"
        source["horses"][0]["assessments"]["draw_weight"]["grade"] = "C"
        source["horses"][1]["assessments"]["training"]["grade"] = "A"
        source["horses"][1]["assessments"]["pedigree"]["grade"] = "C"
        before = copy.deepcopy(source)
        baseline = full_ten_factor_preview(source, now=NOW)
        self.assertTrue(baseline["overallReady"])
        self.assertEqual(baseline["ranking"][0]["number"], 1)
        result = compare_verified_policies(source, now=NOW)
        self.assertEqual(source, before)
        self.assertTrue(result["candidateRankReady"])
        self.assertEqual(result["status"], "read_only_policy_comparison")
        self.assertEqual(result["runners"][0]["number"], 2)
        self.assertEqual(result["runners"][1]["number"], 1)
        self.assertEqual(result["changedPairwiseOrderCount"], 1)
        self.assertEqual(result["runners"][1]["candidateThirdPoints"], 255)
        self.assertEqual(result["runners"][1]["candidateScore100"], 80.95)
        self.assertEqual(result["runners"][0]["candidateThirdPoints"], 267)
        self.assertEqual(result["runners"][0]["candidateScore100"], 84.76)
        self.assertFalse(result["publishable"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["candidateTickets"], [])
        self.assertNotIn("test-original", repr(result))
        self.assertNotIn("fixture", repr(result))

    def test_all_s_ties_share_rank_and_never_turn_into_bets(self):
        source = fixture()
        for horse in source["horses"]:
            for item in horse["assessments"].values():
                item["grade"] = "S"
        result = compare_verified_policies(source, now=NOW)
        self.assertTrue(result["candidateRankReady"])
        self.assertEqual({x["candidateRank"] for x in result["runners"]}, {1})
        self.assertEqual({x["candidateScore100"] for x in result["runners"]},
                         {100.0})
        self.assertEqual(result["changedPairwiseOrderCount"], 0)
        self.assertEqual(result["candidateTickets"], [])
        self.assertEqual(result["sourceGateStatus"], "ambiguous_score_cutoff")

    def test_missing_or_late_evidence_blocks_comparison(self):
        for mode in ("unassessed", "late", "empty_source"):
            source = fixture()
            assessment = source["horses"][0]["assessments"]["ground"]
            if mode == "unassessed":
                assessment["grade"] = "未評価"
            elif mode == "late":
                assessment["evidence"][0]["availableAt"] = OFF
            else:
                assessment["evidence"] = []
            result = compare_verified_policies(source, now=NOW)
            self.assertFalse(result["candidateRankReady"])
            self.assertEqual(result["status"], "held")
            self.assertEqual(result["runners"], [])
            self.assertEqual(result["candidateTickets"], [])

    def test_no_independent_official_or_internal_verification_blocks(self):
        for token in ("jra_starters_verified", "jra_scratches_verified",
                      "jra_going_verified", "jra_posttime_verified"):
            source = fixture()
            source["independentJra"][token] = False
            result = compare_verified_policies(source, now=NOW)
            self.assertEqual(result["status"], "held")
            self.assertFalse(result["candidateRankReady"])
        for key in ("assessmentValidated", "predictionValidated"):
            source = fixture()
            source[key] = False
            self.assertEqual(
                compare_verified_policies(source, now=NOW)["status"], "held"
            )

    def test_off_time_and_roster_changes_are_held(self):
        source = fixture()
        self.assertEqual(compare_verified_policies(source, now=OFF)["runners"], [])
        source["independentJra"]["confirmedStarterNumbers"] = list(range(1, 7))
        result = compare_verified_policies(source, now=NOW)
        self.assertEqual(result["status"], "held")
        self.assertFalse(result["candidateRankReady"])

    def test_original_formal_policy_does_not_change(self):
        self.assertEqual(OWNER_FORMAL_FACTORS["ground"], 12)
        self.assertEqual(OWNER_FORMAL_FACTORS["draw_weight"], 3)
        self.assertEqual(sum(OWNER_FORMAL_FACTORS.values()), 100)
        module = (ROOT/"scripts"/"owner_requested_weight_compare.py").read_text(
            encoding="utf-8")
        for forbidden in ("requests.", "http.client", "localStorage",
                          "sessionStorage", "fetch(", "write_text(",
                          "save_receipt(", "place_bet("):
            self.assertNotIn(forbidden, module)


if __name__ == "__main__":
    unittest.main()
