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
        self.assertEqual(sum(f["weight"] for f in policy),100)
        self.assertEqual({f["key"]:f["weight"] for f in policy},{
            "training":30,"recent":3,"course_distance":17,"pace":17,
            "ground":12,"pedigree":6,"draw_weight":3,
            "jockey_stable":10,"rotation":1,"body_condition":1,
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
        self.assertEqual(converted["totalWeight"],100)
        self.assertEqual(converted["normalization"],"weighted_mean_over_100")
        self.assertEqual(converted["gradeThresholds"],{"S":85,"A":70,"B":55})
        self.assertEqual(converted["scoreUnit"],"0_to_100")
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
        self.assertEqual(h["provisionalWeightCapacity"],33)
        self.assertEqual(h["unassessedWeightCapacity"],67)
        self.assertEqual(h["verifiedWeightCapacity"],0)
        self.assertEqual(h["priorityMissingFactors"],[
            "course_distance", "pace", "ground", "jockey_stable",
            "pedigree", "draw_weight", "rotation", "body_condition"
        ])
        self.assertEqual(h["verifiedFactorCount"],0)
        self.assertTrue(h["provisionalScoreReady"])
        self.assertEqual(h["provisionalBreakdown"],{"training":30,"recent":3})
        self.assertEqual(h["provisionalPoints33"],33)
        self.assertEqual(h["provisionalMaxPoints"],33)
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
        self.assertEqual(last["provisionalWeightCapacity"],30)
        self.assertEqual(last["unassessedWeightCapacity"],70)
        self.assertEqual(last["verifiedWeightCapacity"],0)
        self.assertFalse(last["provisionalScoreReady"])
        self.assertEqual(last["provisionalBreakdown"],{"training":None,"recent":None})
        self.assertIsNone(last["provisionalPoints33"])
        self.assertEqual(last["priorityMissingFactors"][:3],
                         ["course_distance","pace","ground"])
        self.assertIn("recent",last["priorityMissingFactors"])
        self.assertEqual(len(last["missing"]),9)
        self.assertEqual(converted["fullPredictionRaceCount"],0)

    def test_four_grade_combinations_produce_weighted_provisional_points(self):
        cases=[("S","S",33,30,3),("A","B",21,20,1),
               ("B","A",12,10,2),("C","C",0,0,0)]
        report=generate(r=research([(a,b) for a,b,*_ in cases]+[
            ("B","C"),("B","B"),("C","A")]))
        rows=ten_factor_contract(report)["races"][0]["horses"]
        keyed={h["number"]:h for h in rows}
        for number,(a,b,total,t,r) in enumerate(cases,1):
            h=keyed[number]
            self.assertEqual((h["grades"]["training"],h["grades"]["recent"]),(a,b))
            self.assertEqual(h["provisionalBreakdown"],{"training":t,"recent":r})
            self.assertEqual(h["provisionalPoints33"],total)
            self.assertTrue(h["provisionalScoreReady"])
            self.assertIsNone(h["score"])
            self.assertEqual(h["overallGrade"],"未評価")

    def test_tampered_two_factor_raw_points_fail_closed(self):
        report=generate()
        report["races"][0]["runners"][0]["weightedResearchPoints"]=0
        with self.assertRaises(CoverageError):
            ten_factor_contract(report)

    def test_high_training_low_recent_is_flagged_for_more_evidence_not_bet(self):
        report=generate(r=research([
            ("S","C"),("S","A"),("A","B"),("A","C"),
            ("B","S"),("B","C"),("C","C")]))
        preview=ten_factor_contract(report)
        row=preview["races"][0]
        self.assertEqual(row["trainingLedRecheckNumbers"],[1,3,4])
        self.assertFalse(row["trainingLedRecheckIsWinPick"])
        self.assertEqual(row["trainingLedRecheckNeeds"],
                         ["course_distance","pace","ground"])
        self.assertFalse(row["overallReady"])
        self.assertTrue(all(h["overallRank"] is None for h in row["horses"]))
        self.assertTrue(all(h["score"] is None for h in row["horses"]))

    def test_poststart_holds_have_no_retrospective_horse_ranks(self):
        data=generate(now=datetime(2099,1,1,12,10,tzinfo=JST))
        self.assertEqual(data["races"][0]["reason"],"after_provisional_off")
        converted=ten_factor_contract(data)
        self.assertEqual(converted["races"][0]["horses"],[])
        self.assertEqual(converted["races"][0]["trainingLedRecheckNumbers"],[])
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
