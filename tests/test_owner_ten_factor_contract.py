"""Ten-factor owner research contract: synthetic, no paid source calls."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from jrdb_coverage import CoverageError
from owner_ten_factor_contract import ten_factor_contract, definition, VERSION
from test_jrdb_owner_auto_draft import generate, programme, research, JST
from datetime import datetime


class TenFactorContractTests(unittest.TestCase):
    def test_ten_labels_weights_and_core_use_existing_policy(self):
        policy=definition()
        self.assertEqual(len(policy),10)
        self.assertEqual(sum(f["weight"] for f in policy),110)
        self.assertEqual({f["key"]:f["weight"] for f in policy},{
            "training":30,"recent":3,"course_distance":20,"pace":20,
            "ground":15,"pedigree":10,"draw_weight":5,
            "jockey_stable":5,"rotation":1,"body_condition":1,
        })
        self.assertEqual({f["key"]:f["label"] for f in policy}["body_condition"],"馬体重")
        self.assertEqual(set(f["key"] for f in policy),{
            "training","recent","course_distance","pace","ground",
            "pedigree","draw_weight","jockey_stable","rotation","body_condition"})
        self.assertEqual([f["key"] for f in policy if f["core"]],[
            "training","recent","course_distance","pace","ground"])

    def test_existing_two_factors_do_not_become_10_factor_score(self):
        report=generate()
        unchanged=copy.deepcopy(report)
        converted=ten_factor_contract(report)
        self.assertEqual(converted["version"],VERSION)
        self.assertEqual(converted["totalWeight"],110)
        self.assertEqual(converted["normalization"],"weighted_mean_over_110")
        self.assertEqual(converted["raceCount"],1)
        self.assertEqual(converted["fullPredictionRaceCount"],0)
        self.assertFalse(converted["overallPredictionReady"])
        self.assertFalse(converted["officialJraVerified"])
        self.assertEqual(report,unchanged)
        race=converted["races"][0]
        self.assertEqual(race["runnerCount"],7)
        self.assertFalse(race["overallReady"])
        self.assertEqual(race["fullTenFactorCount"],0)
        h=race["horses"][0]
        self.assertEqual(h["number"],1)
        self.assertEqual((h["grades"]["training"],h["grades"]["recent"]),("S","S"))
        self.assertTrue(all(h["grades"][f]=="未評価" for f in (
            "course_distance","pace","ground","pedigree",
            "draw_weight","jockey_stable","rotation","body_condition")))
        self.assertEqual(h["provisionalFactorCount"],2)
        self.assertEqual(h["verifiedFactorCount"],0)
        self.assertIsNone(h["score"])
        self.assertIsNone(h["overallRank"])
        self.assertEqual(h["overallGrade"],"未評価")
        self.assertEqual(len(h["missing"]),8)
        self.assertNotIn("racekey",repr(converted))
        self.assertNotIn("idm",repr(converted))

    def test_unassessed_workout_stays_unassessed_without_fill_in(self):
        report=generate(r=research([("S","S"),("S","A"),("A","A"),
                                    ("A","B"),("B","B"),("B","C"),("C","未評価")]))
        converted=ten_factor_contract(report)
        last=converted["races"][0]["horses"][-1]
        self.assertEqual(last["grades"]["recent"],"未評価")
        self.assertEqual(last["provisionalFactorCount"],1)
        self.assertEqual(len(last["missing"]),9)
        self.assertEqual(converted["fullPredictionRaceCount"],0)

    def test_poststart_holds_have_no_retrospective_horse_ranks(self):
        data=generate(now=datetime(2099,1,1,12,10,tzinfo=JST))
        self.assertEqual(data["races"][0]["reason"],"after_provisional_off")
        converted=ten_factor_contract(data)
        self.assertEqual(converted["races"][0]["horses"],[])
        self.assertEqual(converted["fullPredictionRaceCount"],0)

    def test_invalid_or_swapped_temporary_draft_cannot_create_10f(self):
        report=generate()
        report["races"][0]["runners"][0]["training"]="unknown"
        with self.assertRaises(CoverageError):
            ten_factor_contract(report)
        report=generate()
        report["races"][0]["runners"][1]["number"]=1
        with self.assertRaises(CoverageError):
            ten_factor_contract(report)


if __name__=="__main__":
    unittest.main()
