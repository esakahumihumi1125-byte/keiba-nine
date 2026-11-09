"""New-policy 79 research overlay synthetic checks: historical 85 immutable."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluation_policy import POINTS, OWNER_FORMAL_FACTORS
from jrdb_coverage import CoverageError
from owner_new_weight_five_research import (
    new_weight_five_research, KEYS, WEIGHTS,
)
from owner_five_core_research import five_core_research
from test_owner_five_core_research import sources


def old_source():
    return five_core_research(*sources())


class New79FiveResearchTests(unittest.TestCase):
    def test_read_only_projection_with_new_exact_weights(self):
        legacy = old_source()
        unchanged = copy.deepcopy(legacy)
        report = new_weight_five_research(legacy)
        self.assertEqual(legacy, unchanged)
        self.assertEqual(report["policyVersion"], "research-6")
        self.assertEqual(report["sourcePolicyVersion"], "research-5")
        self.assertEqual(report["factorWeights"], {
            "training": 30, "course_distance": 17,
            "pace": 17, "ground": 12, "recent": 3})
        self.assertEqual(report["observedWeightTotal"], 79)
        self.assertEqual(report["raceCount"], len(legacy["races"]))
        for race in report["races"]:
            self.assertEqual(race["runnerCount"], len(race["horses"]))
            self.assertFalse(race["comparisonIsFormalRank"])
            self.assertFalse(race["formalGradeReady"])
            for horse in race["horses"]:
                self.assertEqual(horse["formalGrade"], "未評価")
                self.assertIsNone(horse["formalScore100"])
                self.assertIsNone(horse["formalRank"])
                self.assertFalse(horse["bettingReady"])
                self.assertEqual(horse["missing"],
                                 [k for k in KEYS if horse["bands"][k] == "未評価"])
                if horse["missing"]:
                    self.assertIsNone(horse["rawThirdPoints"])
                    self.assertIsNone(horse["evidenceScore79"])
                else:
                    raw = sum(WEIGHTS[k]*POINTS[horse["bands"][k]] for k in KEYS)
                    self.assertEqual(horse["rawThirdPoints"], raw)
                    self.assertEqual(horse["evidenceScore79"], round(raw/3,2))
        for flag in ("overallPredictionReady", "formalScoreReady",
                     "officialJraVerified", "bettingReady", "autoPurchase",
                     "resultVerified", "changesExistingTickets",
                     "changesExistingCoreReceipts", "changesExistingFiveReceipts"):
            self.assertFalse(report[flag])
        self.assertEqual(report["extraProviderCalls"], 0)
        for forbidden in ("racekey", "horse_id", "horseRef", "payout",
                          "trifectaTickets", "apiKey", "sourceId"):
            self.assertNotIn(forbidden, repr(report))

    def test_every_factor_all_s_is_79_and_recent_c_only_reduces_three(self):
        old = old_source()
        original = old["races"][0]
        for h in original["horses"]:
            h["bands"] = dict.fromkeys(KEYS, "S")
            h["rawThirdPoints"] = 255
            h["evidenceScore85"] = 85.0
            h["missing"] = []
            h["observedFactorCount"] = 5
        original["missingByFactor"] = dict.fromkeys(KEYS, 0)
        original["completeObserved"] = original["runnerCount"]
        original["comparisonGroups"] = [{
            "rawThirdPoints": 255,
            "numbers": sorted(h["number"] for h in original["horses"]),
        }]
        original["unassessedNumbers"] = []
        all_s = new_weight_five_research(old)
        h = all_s["races"][0]["horses"][0]
        self.assertEqual(h["evidenceScore79"], 79)
        self.assertEqual(h["rawThirdPoints"], 237)
        old["races"][0]["horses"][0]["bands"]["recent"] = "C"
        old["races"][0]["horses"][0]["rawThirdPoints"] = 246
        old["races"][0]["horses"][0]["evidenceScore85"] = 82.0
        other = sorted(h["number"] for h in original["horses"]
                       if h["number"] != original["horses"][0]["number"])
        original["comparisonGroups"] = (
            ([{"rawThirdPoints": 255, "numbers": other}] if other else [])
            + [{"rawThirdPoints": 246,
                "numbers": [original["horses"][0]["number"]]}]
        )
        output = new_weight_five_research(old)
        self.assertEqual(output["races"][0]["horses"][0]["evidenceScore79"], 76)
        self.assertEqual(all_s["races"][0]["horses"][0]["evidenceScore79"] -
                         output["races"][0]["horses"][0]["evidenceScore79"], 3)

    def test_missing_never_gets_default_grade_or_false_zero(self):
        old = old_source()
        report = new_weight_five_research(old)
        for race in report["races"]:
            for h in race["horses"]:
                if h["missing"]:
                    self.assertIsNone(h["evidenceScore79"])
                    self.assertNotIn(h["number"], [
                        n for g in race["comparisonGroups"] for n in g["numbers"]])
        self.assertFalse(report["resultVerified"])

    def test_invalid_legacy_values_cannot_create_new_79_research(self):
        edits = [
            lambda x: x.update(policyVersion="research-6"),
            lambda x: x["factorWeights"].update(pace=17),
            lambda x: x.update(observedWeightTotal=79),
            lambda x: x.update(officialJraVerified=True),
            lambda x: x["races"][0].update(comparisonIsFormalRank=True),
            lambda x: x["races"][0]["horses"][0].update(evidenceScore85="tampered"),
            lambda x: x["races"][0]["horses"][0].update(formalScore100=79),
            lambda x: x["races"][0]["horses"][0].update(rawThirdPoints=123),
            lambda x: x["races"][0]["horses"][0]["bands"].update(pace="INVALID"),
            lambda x: x["races"][0]["horses"][0].update(number=21),
            lambda x: x["races"][0]["horses"][0].update(missing=["injected"]),
            lambda x: x["races"][0].update(unassessedNumbers=[21]),
            lambda x: x["races"][0].update(comparisonGroups=[{"rawThirdPoints":255,"numbers":[21]}]),
            lambda x: x["races"][0].update(completeObserved=17),
            lambda x: x["races"][0]["missingByFactor"].update(recent=17),
            lambda x: x["races"][0]["horses"][0].update(
                bands={"training":"S", "recent":"S"}),
        ]
        for edit in edits:
            source = old_source()
            edit(source)
            with self.subTest(edit=repr(edit)), self.assertRaises(CoverageError):
                new_weight_five_research(source)


if __name__ == "__main__":
    unittest.main()
