"""Synthetic formal-ten formation regression: 30-40 preferred, <=48 max."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_formal_formation import formal_formation_sizes
from owner_full_ten_factor import full_ten_factor_preview
from jrdb_coverage import CoverageError
from test_owner_full_ten_factor import fixture, horse, NOW, OFFICIAL


def ranking(scores):
    return [{"weightedPoints": score} for score in scores]


class FormalFormationTests(unittest.TestCase):
    def test_ten_factor_default_still_forty_points(self):
        before = fixture()
        original = copy.deepcopy(before)
        r = full_ten_factor_preview(before, now=NOW)
        self.assertEqual(before, original)
        self.assertEqual(r["trifecta"]["points"], 40)
        self.assertEqual(r["trifecta"]["first"], [1, 2])
        self.assertEqual(len({tuple(t) for t in r["trifecta"]["tickets"]}), 40)
        self.assertFalse(r["bettingReady"])

    def test_exactly_forty_eight_when_thirty_to_forty_splits_a_tie(self):
        # 1: 300, 2: 297, 3/4: 294, 5..10: 288 (third group tied).
        # Candidate 2x4x10 => 48 exact distinct 3連単. Arbitrarily taking
        # just seven/eight of the six equally scored tail horses is wrong.
        source = fixture()
        source["horses"] = [
            horse(1), horse(2, {"recent": "A"}),
            horse(3, {"pedigree": "A"}), horse(4, {"pedigree": "A"}),
            *[horse(n, {"ground": "A"}) for n in range(5, 11)],
        ]
        source["independentJra"]["confirmedStarterNumbers"] = list(range(1, 11))
        original = copy.deepcopy(source)
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, original)
        self.assertEqual(result["status"], "review_only")
        draft = result["trifecta"]
        self.assertEqual((draft["first"], draft["second"], draft["third"]),
                         ([1, 2], [1, 2, 3, 4], list(range(1, 11))))
        self.assertEqual(draft["points"], 48)
        self.assertEqual(draft["totalStakeYen"], 4800)
        self.assertEqual(len({tuple(t) for t in draft["tickets"]}), 48)
        self.assertTrue(all(len(set(t)) == 3 for t in draft["tickets"]))
        self.assertFalse(draft["bettingReady"])

        source["independentJra"]["jra_posttime_verified"] = False
        blocked = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(blocked["trifecta"]["points"], 0)
        self.assertFalse(blocked["bettingReady"])
        del source["horses"][0]["assessments"]["pace"]
        missing = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(missing["status"], "missing_evidence")
        self.assertEqual(missing["trifecta"]["points"], 0)

    def test_fourteen_runners_retain_the_full_c_tier_for_preferred_36(self):
        # 1S / 3A / 6B / 4C. The old <=12 third cutoff stopped
        # at the complete 10-runner B tier and returned only 24 points.
        scores = [300] + [270] * 3 + [240] * 6 + [210] * 4
        self.assertEqual(formal_formation_sizes(ranking(scores)), (1, 4, 14))
        source = fixture()
        source["horses"] = (
            [horse(1)] +
            [horse(n, {"training": "A"}) for n in range(2, 5)] +
            [horse(n, {"training": "B"}) for n in range(5, 11)] +
            [horse(n, {"training": "C"}) for n in range(11, 15)]
        )
        source["independentJra"]["confirmedStarterNumbers"] = list(range(1, 15))
        pristine = copy.deepcopy(source)
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, pristine)
        self.assertEqual(result["status"], "review_only")
        formation = result["trifecta"]
        self.assertEqual(formation["first"], [1])
        self.assertEqual(formation["second"], [1, 2, 3, 4])
        self.assertEqual(formation["third"], list(range(1, 15)))
        self.assertEqual(formation["points"], 36)
        self.assertEqual(formation["totalStakeYen"], 3600)
        self.assertEqual(len({tuple(t) for t in formation["tickets"]}), 36)
        self.assertFalse(formation["bettingReady"])
        self.assertFalse(result["autoPurchase"])
        self.assertFalse(result["publishable"])

    def test_eighteen_runners_keep_full_b_tier_without_exceeding_48(self):
        # When only full tied tiers are allowed, 1S / 3A / 14B admits
        # a 48-point 1x4x18 reference; stopping at 12 loses 42 points.
        sample = ranking([300] + [270] * 3 + [240] * 14)
        self.assertEqual(formal_formation_sizes(sample), (1, 4, 18))
        source = fixture()
        source["horses"] = (
            [horse(1)] +
            [horse(n, {"training": "A"}) for n in range(2, 5)] +
            [horse(n, {"training": "B"}) for n in range(5, 19)]
        )
        source["independentJra"]["confirmedStarterNumbers"] = list(range(1, 19))
        before = copy.deepcopy(source)
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, before)
        self.assertEqual(result["status"], "review_only")
        form = result["trifecta"]
        self.assertEqual(form["first"], [1])
        self.assertEqual(form["second"], [1, 2, 3, 4])
        self.assertEqual(form["third"], list(range(1, 19)))
        self.assertEqual(form["points"], 48)
        self.assertEqual(len({tuple(t) for t in form["tickets"]}), 48)
        self.assertEqual(form["totalStakeYen"], 4800)
        self.assertTrue(all(len(set(t)) == 3 for t in form["tickets"]))
        self.assertFalse(form["bettingReady"])
        self.assertFalse(result["autoPurchase"])
        # No extra / false independent JRA approval can create a ticket.
        source["independentJra"]["jra_scratches_verified"] = False
        withheld = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(withheld["trifecta"]["points"], 0)
        source["independentJra"]["jra_scratches_verified"] = True
        del source["horses"][0]["assessments"]["ground"]
        incomplete = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(incomplete["status"], "missing_evidence")
        self.assertEqual(incomplete["trifecta"]["points"], 0)

    def test_strong_single_uses_36_instead_of_two_winner_48(self):
        # Full evidence: 1S at 100pt, runner-up A at 80pt.
        # 2 x 3 x 14 permits 48, but the strong-leader 1 x 4 x 14
        # can safely stay within the owner's 30-40 point target.
        expected = [300, 240, 237, 231] + [159] * 10
        self.assertEqual(formal_formation_sizes(ranking(expected)), (1, 4, 14))
        source = fixture()
        source["horses"] = (
            [horse(1),
             horse(2, {"training": "B"}),
             horse(3, {"training": "B", "recent": "A"}),
             horse(4, {"training": "B", "recent": "C"})]
            + [horse(n, {"training": "C", "pace": "C"})
               for n in range(5, 15)]
        )
        source["independentJra"]["confirmedStarterNumbers"] = list(range(1, 15))
        original = copy.deepcopy(source)
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, original)
        self.assertEqual([r["weightedPoints"] for r in result["ranking"]], expected)
        self.assertEqual(result["status"], "review_only")
        tickets = result["trifecta"]
        self.assertEqual(tickets["first"], [1])
        self.assertEqual(tickets["second"], [1, 2, 3, 4])
        self.assertEqual(tickets["third"], list(range(1, 15)))
        self.assertEqual(tickets["points"], 36)
        self.assertEqual(len({tuple(t) for t in tickets["tickets"]}), 36)
        self.assertEqual(tickets["totalStakeYen"], 3600)
        self.assertFalse(tickets["bettingReady"])
        self.assertFalse(result["publishable"])
        self.assertFalse(result["autoPurchase"])
        source["independentJra"]["jra_scratches_verified"] = False
        blocked = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(blocked["trifecta"]["points"], 0)
        source["independentJra"]["jra_scratches_verified"] = True
        del source["horses"][0]["assessments"]["recent"]
        missing = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(missing["status"], "missing_evidence")
        self.assertEqual(missing["trifecta"]["points"], 0)

    def test_no_weak_or_tied_singleton_promoted_for_lower_stake(self):
        # A small 1-point leader is NOT a trusted single, even if a
        # 36-point single would be cheaper than the legal 48-point pair.
        self.assertEqual(formal_formation_sizes(
            ranking([300, 297, 294, 270] + [159] * 10)),
            (2, 3, 14))
        # Ten-point threshold alone is not enough when second still S.
        self.assertEqual(formal_formation_sizes(
            ranking([300, 270, 267, 261] + [159] * 10)),
            (2, 3, 14))
        # A clear S/A split with only a 9-point lead is not fixed first.
        self.assertEqual(formal_formation_sizes(
            ranking([270, 243, 240, 237] + [159] * 10)),
            (2, 3, 14))
        self.assertEqual(formal_formation_sizes(
            ranking([255, 254, 251, 248] + [159] * 10)),
            (2, 3, 14))

    def test_one_clear_leader_can_rescue_an_entire_equal_second_group(self):
        # Old strict 2/3-first boundary splits the second-place tier;
        # first=[clear 1], second=[1..5], third=[1..10] gives 32.
        sample = ranking([300] + [260] * 4 + [220] * 5)
        self.assertEqual(formal_formation_sizes(sample), (1, 5, 10))

    def test_normal_two_first_prefers_thirty_to_forty_over_forty_eight(self):
        # A 40 point option exists, so a legal 48-point expansion is
        # not automatically preferred merely because it is larger.
        sample = ranking([300, 297, 294, 291, 288, 285, 282, 279, 276, 273])
        sizes = formal_formation_sizes(sample)
        points = sizes[0] * (sizes[1] - 1) * (sizes[2] - 2)
        self.assertTrue(30 <= points <= 40)
        self.assertEqual(sizes[0], 2)

    def test_equal_scores_stay_equal_and_missing_inputs_fail_closed(self):
        self.assertIsNone(formal_formation_sizes(ranking([300] * 8)))
        self.assertIsNone(formal_formation_sizes(ranking([300] * 4 + [200] * 4)))
        for invalid in ([300, 297, None, 200], [300, 100, 200, 0],
                        [300, True, 100, 0], [400, 300, 200, 100]):
            with self.subTest(value=invalid), self.assertRaises(CoverageError):
                formal_formation_sizes(ranking(invalid))
        for invalid in ([], ranking([300] * 3), ranking([300] * 19), "bad"):
            with self.subTest(value=repr(invalid)), self.assertRaises(CoverageError):
                formal_formation_sizes(invalid)

    def test_no_trifecta_auto_purchase_or_snapshot_mutation(self):
        source = fixture()
        before = copy.deepcopy(source)
        r = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, before)
        self.assertEqual(r["autoPurchase"], False)
        self.assertEqual(r["publishable"], False)
        self.assertEqual(r["researchOnly"], True)
        self.assertLessEqual(r["trifecta"]["points"], 48)
        self.assertFalse(r["trifecta"]["bettingReady"])


if __name__ == "__main__":
    unittest.main()
