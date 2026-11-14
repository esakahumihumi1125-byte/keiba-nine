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
