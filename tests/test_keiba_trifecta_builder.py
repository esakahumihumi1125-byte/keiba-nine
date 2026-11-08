"""Pure formation tests: synthetic numbers and no real races or tickets."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from keiba_trifecta_builder import (
    build_trifecta, FormationError, REQUIRED_EVIDENCE, MAX_POINTS,
)

CHECKED = {key: True for key in REQUIRED_EVIDENCE}


class TrifectaBuilderTests(unittest.TestCase):
    def test_no_verified_evidence_means_zero_tickets(self):
        for evidence in (None, {}, {"verified": True},
                         {"jra_starters_verified": True}):
            with self.subTest(evidence=evidence):
                result = build_trifecta(list(range(1, 11)),
                                        evidence=evidence)
                self.assertEqual(result["status"], "not_ready")
                self.assertEqual(result["points"], 0)
                self.assertEqual(result["totalStakeYen"], 0)
                self.assertEqual(result["tickets"], [])
                self.assertFalse(result["bettingReady"])

    def test_normal_2_5_7_formation_is_exactly_40_points(self):
        result = build_trifecta(list(range(1, 19)), evidence=CHECKED)
        self.assertEqual(result["status"], "review_only")
        self.assertEqual(result["first"], [1, 2])
        self.assertEqual(result["second"], [1, 2, 3, 4, 5])
        self.assertEqual(result["third"], [1, 2, 3, 4, 5, 6, 7])
        self.assertEqual(result["points"], 40)
        self.assertEqual(result["totalStakeYen"], 4000)
        self.assertEqual(len(set(map(tuple, result["tickets"]))), 40)
        self.assertTrue(all(len(set(ticket)) == 3 for ticket in result["tickets"]))
        self.assertFalse(result["bettingReady"])

    def test_small_field_and_one_horse_fixed_reduce_points(self):
        self.assertEqual(build_trifecta(list(range(1, 7)),
                                        evidence=CHECKED)["points"], 32)
        self.assertEqual(build_trifecta(list(range(1, 6)),
                                        evidence=CHECKED)["points"], 24)
        one = build_trifecta(list(range(1, 13)), evidence=CHECKED, first=[1])
        self.assertEqual(one["points"], 20)
        self.assertTrue(all(ticket[0] == 1 for ticket in one["tickets"]))

    def test_extra_discrete_trifecta_is_deduped(self):
        result = build_trifecta(list(range(1, 10)), evidence=CHECKED,
                                extra_tickets=[(8, 3, 4), (1, 2, 3), (8, 3, 4)])
        self.assertEqual(result["points"], 41)
        self.assertEqual(result["individual"], [[8, 3, 4]])
        self.assertEqual(result["totalStakeYen"], 4100)

    def test_48_is_cap_not_target(self):
        with self.assertRaises(FormationError):
            build_trifecta(list(range(1, 19)), evidence=CHECKED,
                           third=list(range(1, 11)))
        with self.assertRaises(FormationError):
            build_trifecta(list(range(1, 19)), evidence=CHECKED,
                           extra_tickets=[(8, x, y)
                                          for x in range(1, 7)
                                          for y in range(9, 12)])

    def test_candidate_integrity_and_verified_runner_list(self):
        for ranked in ([1, 1, 2], [1, "2", 3], [0, 1, 2], list(range(1, 20))):
            with self.subTest(ranked=ranked), self.assertRaises(FormationError):
                build_trifecta(ranked, evidence=CHECKED)
        for bad in ([1, 19], [1, 1], [2.0], [], [True]):
            with self.subTest(first=bad), self.assertRaises(FormationError):
                build_trifecta(list(range(1, 10)), evidence=CHECKED, first=bad)

    def test_invalid_discrete_ticket_is_not_accepted(self):
        for extra in ([(1, 1, 2)], [(1, 2, 99)], [(1, "2", 3)],
                      [(1, 2)], ["1-2-3"]):
            with self.subTest(extra=extra), self.assertRaises(FormationError):
                build_trifecta(list(range(1, 11)), evidence=CHECKED,
                               extra_tickets=extra)


if __name__ == "__main__":
    unittest.main()
