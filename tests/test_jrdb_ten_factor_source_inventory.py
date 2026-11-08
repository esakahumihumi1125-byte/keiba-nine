"""Offline ten-factor source inventory tests: no credentials or real races."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from jrdb_ten_factor_source_inventory import ten_factor_source_inventory
from test_jrdb_personnel_body_materials import run_case
from test_jrdb_history_pipeline import context, run_case as history_run


FIVE = ("training", "recent", "course_distance", "pace", "ground")


def fixture():
    person = run_case()
    races = []
    for item in person:
        horses = []
        for number, slots in item["byNumber"].items():
            horses.append({
                "number": int(number),
                "bands": {k: (
                    slots[k]["grade"] if k in ("training", "recent") else "未評価"
                ) for k in FIVE},
                "actualGradesVerified": 0,
                "overallScore": None, "overallRank": None,
            })
        races.append({
            "track": item["track"], "race": item["race"],
            "runnerCount": len(horses), "runners": horses,
            "verifiedFactorCount": 0, "overallReady": False,
            "bettingReady": False,
        })
    five = {
        "version": "owner-five-factor-hypotheses-1",
        "policyVersion": "research-5", "raceCount": len(races),
        "races": races,
        "factors": [{"key": k, "weight": FACTORS[k]} for k in FIVE],
        "hypothesisBandsNotVerifiedGrades": True,
        "materialCoverageDoesNotMeanPrediction": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "verifiedFactorCount": 0, "bettingReady": False,
        "autoPurchase": False,
    }
    return five, person


class TenFactorSourceInventoryTests(unittest.TestCase):
    def test_remaining_five_source_fields_never_become_ten_grades(self):
        five, personnel = fixture()
        originals = copy.deepcopy((five, personnel))
        report = ten_factor_source_inventory(five, personnel)
        self.assertEqual((five, personnel), originals)
        self.assertEqual(report["factorCount"], 10)
        self.assertEqual(report["totalWeight"], 100)
        self.assertEqual(report["factorWeights"], FACTORS)
        self.assertEqual(report["raceCount"], 2)
        self.assertFalse(report["overallPredictionReady"])
        self.assertFalse(report["independentJraVerified"])
        self.assertFalse(report["bettingReady"])
        first_race = next(x for x in report["races"] if x["track"] == "東京")
        self.assertEqual(first_race["runnerCount"], 2)
        self.assertEqual(first_race["remainingFieldCoverage"], {
            "pedigree": 1, "draw_weight": 2,
            "jockey_stable": 2, "rotation": 2, "body_condition": 0
        })
        one, two = first_race["runners"]
        self.assertEqual(one["number"], 1)
        self.assertEqual(one["sourceStates"]["pedigree"], "complete_fields_observed")
        self.assertEqual(two["sourceStates"]["pedigree"], "partial_fields_observed")
        self.assertEqual(one["sourceStates"]["rotation"], "under14Days")
        self.assertEqual(two["sourceStates"]["rotation"], "days14to55")
        self.assertTrue(one["bodyShapeCodePresent"])
        self.assertEqual(one["sourceStates"]["body_condition"], 
                         "race_day_bodyweight_unavailable")
        self.assertIsNone(one["overallScore"])
        self.assertIsNone(one["overallRank"])
        self.assertEqual(one["verifiedGrades"], 0)
        other = next(x for x in report["races"] if x["track"] == "京都")
        self.assertEqual(other["runners"][0]["sourceStates"]["rotation"], "unknown")

    def test_output_does_not_copy_paid_provider_fields(self):
        report = ten_factor_source_inventory(*fixture())
        for secret in ("racekey", "byNumber", "horse_id", "jockeyNameRecorded",
                       "sire_name", "mare_sire_name", "weight_to_carry",
                       "架空父馬A", "架空騎手A", "22222222",
                       "horse_bodytype_integration_cd"):
            self.assertNotIn(secret, repr(report))

    def test_reject_source_promotions_and_mismatched_rosters(self):
        modifications = (
            lambda f,p: f["races"][0]["runners"][0].update(number=18),
            lambda f,p: f["races"][0]["runners"][1].update(number=1),
            lambda f,p: f["races"][0].update(track="札幌"),
            lambda f,p: f["races"][0]["runners"][0]["bands"].update(training="A"),
            lambda f,p: f.update(overallPredictionReady=True),
            lambda f,p: p[0]["byNumber"]["01"]["pedigree"].update(grade="S"),
            lambda f,p: p[0]["byNumber"]["01"]["body_condition"].update(grade="A"),
            lambda f,p: f["races"][0]["runners"][0].update(overallScore=85),
        )
        for change in modifications:
            with self.subTest(change=str(change)):
                sources = fixture()
                change(*sources)
                with self.assertRaises(CoverageError):
                    ten_factor_source_inventory(*sources)

    def test_existing_bounded_history_build_includes_inventory(self):
        report = history_run(context())
        inv = report["tenFactorSourceInventory"]
        self.assertEqual(inv["version"], "owner-ten-factor-source-inventory-1")
        self.assertEqual(inv["raceCount"], report["fiveFactorHypotheses"]["raceCount"])
        self.assertEqual(inv["raceCount"], report["allTenFactorSources"]["raceCount"])
        self.assertTrue(all(r["verifiedGrades"] == 0 for r in inv["races"]))
        self.assertFalse(inv["overallPredictionReady"])
        self.assertFalse(inv["bettingReady"])


if __name__ == "__main__":
    unittest.main()
