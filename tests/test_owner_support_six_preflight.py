"""Synthetic checks for ungraded draw/personnel/rotation readiness."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_ten_factor_source_inventory import ten_factor_source_inventory
from owner_support_six_preflight import support_six_preflight, KEYS, GAPS
from test_jrdb_ten_factor_source_inventory import fixture
from test_jrdb_history_pipeline import context, run_case


class SupportSixPreflightTests(unittest.TestCase):
    def setUp(self):
        self.source = ten_factor_source_inventory(*fixture())

    def test_source_counts_without_any_six_points_or_mutation(self):
        original = copy.deepcopy(self.source)
        out = support_six_preflight(self.source)
        self.assertEqual(original, self.source)
        self.assertEqual(out["factors"], {
            "draw_weight": 3, "jockey_stable": 2, "rotation": 1
        })
        self.assertEqual(out["weightTotal"], 6)
        self.assertEqual(out["raceCount"], 2)
        self.assertEqual(out["verifiedFactorCount"], 0)
        for field in ("conditionMatchedEffectValidated", "temporalValidationComplete",
                      "officialJraVerified", "overallPredictionReady",
                      "bettingReady", "autoPurchase", "changesExistingTickets",
                      "changesExistingReceipts"):
            self.assertFalse(out[field])
        tokyo = next(r for r in out["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["fieldCompleteCounts"], {
            "draw_weight": 2, "jockey_stable": 2, "rotation": 2
        })
        self.assertEqual(tokyo["allThreeFieldCompleteCount"], 2)
        for race in out["races"]:
            for horse in race["horses"]:
                self.assertEqual(set(horse["grades"]), set(KEYS))
                self.assertTrue(all(horse["grades"][k] == "未評価" for k in KEYS))
                self.assertTrue(all(horse["scores"][k] is None for k in KEYS))
                self.assertFalse(horse["bettingReady"])
                self.assertFalse(horse["conditionalEffectVerified"])
                self.assertFalse(horse["outOfTimeValidated"])
                for k in KEYS:
                    self.assertEqual(
                        horse["missingEvidence"][k],
                        ([] if horse["fieldPresent"][k] else [GAPS[k][0]])
                        + list(GAPS[k][1:])
                    )
        kyoto = next(r for r in out["races"] if r["track"] == "京都")
        self.assertEqual(kyoto["horses"][0]["sourceStates"]["rotation"], "unknown")
        self.assertEqual(kyoto["horses"][0]["fieldPresenceWeight"], 0)
        for secret in ("racekey", "byNumber", "sire_name", "jockey_name",
                       "weight_to_carry", "horse_id", "auth_key"):
            self.assertNotIn(secret, repr(out))

    def test_tampered_roster_or_results_are_rejected(self):
        edits = (
            lambda v: v.update(verifiedGrades=1),
            lambda v: v.update(overallPredictionReady=True),
            lambda v: v["races"][-1]["runners"][0].update(number=19),
            lambda v: v["races"][-1]["runners"][1].update(number=1),
            lambda v: v["races"][0]["runners"][0].update(overallScore=100),
            lambda v: v["races"][-1]["runners"][0]["sourceStates"].update(rotation="S"),
            lambda v: v["races"][-1]["remainingFieldCoverage"].update(draw_weight=0),
            lambda v: v["races"][-1].update(track=""),
        )
        for index, edit in enumerate(edits):
            with self.subTest(index=index):
                sample = copy.deepcopy(self.source)
                edit(sample)
                with self.assertRaises(CoverageError):
                    support_six_preflight(sample)

    def test_no_added_paid_history_calls(self):
        old = run_case(context())
        six = old["supportSixPreflight"]
        self.assertEqual(six, support_six_preflight(old["tenFactorSourceInventory"]))
        self.assertEqual(six["raceCount"], old["fiveCoreResearch"]["raceCount"])
        self.assertEqual(old["maxTotalCalls"], 16)
        self.assertFalse(old["predictionReady"])


if __name__ == "__main__":
    unittest.main()
