"""Synthetic checks: no guessed missing form, no signed/off-time tickets."""
import copy
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import build_owner_auto_drafts
from owner_uncertain_recent_preview import preview_missing_recent_holds, VERSION
from test_jrdb_owner_auto_draft import programme, research, JST, DAY

PRESTART = datetime(2099, 1, 1, 9, tzinfo=JST)
# 2 S; 2 A; 3 B; 1 C. Missing past form never changes groups.
PAIRS = [
    ("S", "未評価"), ("S", "C"),
    ("A", "未評価"), ("A", "S"),
    ("B", "未評価"), ("B", "A"),
    ("B", "C"), ("C", "未評価"),
]


def build(pairs=PAIRS, now=PRESTART):
    return build_owner_auto_drafts(
        programme(headcount=len(pairs)),
        research(pairs), DAY, now=now,
    )


class UncertainRecentResearchTests(unittest.TestCase):
    def test_safe_candidate_when_training_dominates_missing_recent(self):
        original = build()
        self.assertEqual(original["draftCount"], 0)
        self.assertEqual(original["races"][0]["reason"], "missing_factors")
        untouched = copy.deepcopy(original)
        preview = preview_missing_recent_holds(original, DAY, now=PRESTART)
        self.assertEqual(preview["version"], VERSION)
        self.assertEqual(preview["safeResearchPreviewCount"], 1)
        self.assertEqual(preview["reviewedPrestartMissingFactorRaces"], 1)
        race = preview["races"][0]
        self.assertEqual(race["first"], [1, 2])
        self.assertEqual(race["second"], [1, 2, 4, 3])
        self.assertEqual(set(race["third"]), set(range(1, 9)))
        self.assertEqual(race["points"], 36)
        self.assertEqual(race["missingRecentCount"], 4)
        self.assertTrue(race["eachCutoffProvenForAllRecentGrades"])
        self.assertFalse(race["officialJraVerified"])
        self.assertFalse(race["receiptIssued"])
        self.assertFalse(preview["formalTenFactorReady"])
        self.assertEqual(preview["ticketsIssued"], 0)
        self.assertEqual(preview["newProviderRequests"], 0)
        self.assertEqual(original, untouched)
        self.assertNotIn("racekey", repr(preview))
        self.assertNotIn("horse_id", repr(preview))

    def test_overlapping_uncertainty_never_splits_top_group(self):
        pairs = [("A", "未評価")] * 8
        output = preview_missing_recent_holds(build(pairs), DAY, now=PRESTART)
        self.assertEqual(output["safeResearchPreviewCount"], 0)
        self.assertEqual(output["reviewedPrestartMissingFactorRaces"], 1)
        self.assertEqual(output["races"], [])

    def test_missing_training_blocks_high_weight_guess(self):
        pairs = list(PAIRS)
        pairs[0] = ("未評価", "S")
        output = preview_missing_recent_holds(build(pairs), DAY, now=PRESTART)
        self.assertEqual(output["safeResearchPreviewCount"], 0)

    def test_poststart_never_reconstructs_held_horse_ranks(self):
        past = datetime(2099, 1, 1, 12, 1, tzinfo=JST)
        # Even if a stored *prestart* report still has runner details,
        # a late renderer must not derive or issue new candidate groups.
        old_report = build()
        result = preview_missing_recent_holds(old_report, DAY, now=past)
        self.assertEqual(result["races"], [])
        self.assertEqual(result["safeResearchPreviewCount"], 0)
        new_report = build(now=past)
        self.assertEqual(new_report["races"][0]["reason"], "after_provisional_off")
        new_result = preview_missing_recent_holds(new_report, DAY, now=past)
        self.assertEqual(new_result["races"], [])

    def test_no_preview_for_complete_strict_draft(self):
        report = build([("S", "S"), ("S", "A"), ("A", "A"),
                        ("A", "B"), ("B", "B"), ("B", "C"),
                        ("C", "C")])
        self.assertEqual(report["draftCount"], 1)
        output = preview_missing_recent_holds(report, DAY, now=PRESTART)
        self.assertEqual(output["safeResearchPreviewCount"], 0)
        self.assertEqual(output["races"], [])

    def test_invalid_snapshot_or_clock_fail_closed(self):
        orig = build()
        broken = copy.deepcopy(orig)
        broken["officialJraVerified"] = True
        with self.assertRaises(CoverageError):
            preview_missing_recent_holds(broken, DAY, now=PRESTART)
        with self.assertRaises(CoverageError):
            preview_missing_recent_holds(orig, DAY,
                                         now=datetime(2099, 1, 1, 9))
        with self.assertRaises(CoverageError):
            preview_missing_recent_holds(orig, "20990102", now=PRESTART)

if __name__ == "__main__":
    unittest.main()
