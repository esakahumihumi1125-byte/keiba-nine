"""Fail-closed future-only 48-point tie rescue for actual owner 2-factor drafts.

No provider/official feed, fixed purchase record, odds or training calibration.
Legacy <=40-point receipts MUST remain bit-for-bit unchanged.
"""
import copy
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_owner_auto_draft import build_owner_auto_drafts
from owner_auto_draft_receipts import seal_auto_research_drafts
from owner_prestart_receipt import verify_preview_receipts
from test_jrdb_owner_auto_draft import (
    programme, research, JST, DAY, SETTINGS
)

BEFORE = datetime(2099, 1, 1, 9, 0, tzinfo=JST)
AFTER = datetime(2099, 1, 1, 12, 1, tzinfo=JST)
SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]


def generate(pairs, at=BEFORE):
    source = programme(headcount=len(pairs))
    ratings = research(pairs)
    untouched = copy.deepcopy((source, ratings))
    result = build_owner_auto_drafts(source, ratings, DAY, now=at)
    assert (source, ratings) == untouched
    return result


class OwnerTie48DraftTests(unittest.TestCase):
    def test_sole_clear_leader_rescues_32_points_without_splitting_4_a(self):
        pairs = [("S", "C")] + [("A", "C")] * 4 + [("B", "C")] * 5
        result = generate(pairs)
        self.assertEqual((result["draftCount"], result["holdCount"]), (1, 0))
        race = result["races"][0]
        self.assertEqual(race["status"], "provisional_draft")
        self.assertEqual(race["first"], [1])
        self.assertEqual(race["second"], [1, 2, 3, 4, 5])
        self.assertEqual(race["third"], list(range(1, 11)))
        self.assertEqual(race["points"], 32)
        self.assertEqual(race["amountYen"], 3200)
        self.assertEqual(len({tuple(t) for t in race["tickets"]}), 32)
        self.assertTrue(all(len(set(t)) == 3 for t in race["tickets"]))
        self.assertFalse(race["officialJraVerified"])
        self.assertFalse(race["overallPredictionReady"])
        self.assertFalse(race["bettingReady"])
        self.assertFalse(race["autoPurchase"])
        sealed = seal_auto_research_drafts(result, SECRET, now=BEFORE)
        self.assertEqual(len(sealed), 1)
        self.assertEqual(len(sealed[0]["snapshot"]["trifectaTickets"]), 32)
        verified = verify_preview_receipts(sealed, SECRET, f"{DAY[:4]}-{DAY[4:6]}-{DAY[6:]}")
        self.assertEqual(len(verified), 1)

    def test_eight_horse_second_tier_42_points_new_bounded_path(self):
        # 1 S leader, 7 equally-rated A horses, 2 B horses.
        # Picking a favored A horse as first is forbidden by equality.
        # First=[S], second=third=[S+7 A] => 1*7*6 = 42 tickets.
        pairs = [("S", "C")] + [("A", "C")] * 7 + [("B", "C")] * 2
        result = generate(pairs)
        race = result["races"][0]
        self.assertEqual(race["first"], [1])
        self.assertEqual(race["second"], list(range(1, 9)))
        self.assertEqual(race["third"], list(range(1, 9)))
        self.assertEqual(race["points"], 42)
        self.assertEqual(race["amountYen"], 4200)
        self.assertEqual(len({tuple(t) for t in race["tickets"]}), 42)
        self.assertEqual(len(seal_auto_research_drafts(result, SECRET, now=BEFORE)), 1)

    def test_old_forty_point_algorithm_is_unchanged_when_already_safe(self):
        result = generate([("S", "S"), ("S", "A"), ("A", "A"),
                           ("A", "B"), ("B", "B"), ("B", "C"),
                           ("C", "C")])
        race = result["races"][0]
        self.assertEqual(race["points"], 40)
        self.assertEqual(race["first"], [1, 2])
        self.assertEqual(race["second"], [1, 2, 3, 4, 5])
        self.assertEqual(race["third"], list(range(1, 8)))

    def test_four_equal_winners_still_hold_no_receipt(self):
        result = generate([("S", "S")] * 4 + [("A", "S")] * 6)
        self.assertEqual(result["draftCount"], 0)
        self.assertEqual(result["holdReasons"], {"ambiguous_equal_grade_boundary": 1})
        self.assertEqual(seal_auto_research_drafts(result, SECRET, now=BEFORE), [])

    def test_unknown_grade_still_hold_no_fabricated_zero(self):
        result = generate([("S", "未評価")] +
                          [("A", "C")] * 4 + [("B", "C")] * 5)
        self.assertEqual(result["draftCount"], 0)
        self.assertEqual(result["holdReasons"], {"missing_factors": 1})
        self.assertEqual(seal_auto_research_drafts(result, SECRET, now=BEFORE), [])

    def test_past_off_does_not_create_or_sign_retrospective_tickets(self):
        pairs = [("S", "C")] + [("A", "C")] * 4 + [("B", "C")] * 5
        result = generate(pairs, at=AFTER)
        self.assertEqual(result["races"][0]["reason"], "after_provisional_off")
        self.assertEqual(result["races"][0]["tickets"], [])
        self.assertEqual(seal_auto_research_drafts(result, SECRET, now=AFTER), [])


if __name__ == "__main__":
    unittest.main()
