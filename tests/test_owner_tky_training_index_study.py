"""Already-fetched /tky training_index gives observed-only order, not scores."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_tky_training_index_study import (
    tky_training_index_study, _index, VERSION
)
from jrdb_coverage import CoverageError

DAY="20990101"
NOW=datetime.fromisoformat("2099-01-01T09:00:00+09:00")
LATE=datetime.fromisoformat("2099-01-01T10:00:00+09:00")


def fixture():
    race={
        "racekey":"05994b01","racedate":DAY,
        "track":"東京","race":1,"post_time":"10:00","headcount":5
    }
    entries=[]
    arrows=("4","2","2","1",None)
    for i,val in enumerate(("16.0","12.0","12.0",None,"-5.5"),1):
        entries.append({
            "racekey":race["racekey"],"racedate":DAY,
            "horse_number":f"{i:02d}",
            "horse_id":f"2328aaa95a{i:02d}",
            "training_index":val,
            "training_arrow":arrows[i-1],
            "horse_name":"PAID-TEST-HORSE",
            "withdrawn_flag":"0"
        })
    report={
        "version":"jrdb-owner-auto-draft-1","date":DAY,
        "raceCount":1,"researchOnly":True,"privateOwnerOnly":True,
        "officialJraVerified":False,"overallPredictionReady":False,
        "bettingReady":False,
        "races":[{
            "track":"東京","race":1,"status":"hold",
            "reason":"missing_factors","horseCount":5,
            "postTime":"10:00",
            "runners":[{"number":i,"training":"未評価","recent":"C"}
                       for i in range(1,6)]
        }]
    }
    return [race],entries,report


class TkyTrainingIndexStudyTests(unittest.TestCase):
    def test_tky_independent_index_recovers_observed_order_without_tcy(self):
        p,e,r=fixture()
        original=copy.deepcopy((p,e,r))
        result=tky_training_index_study(p,e,r,DAY,now=NOW)
        self.assertEqual((p,e,r),original)
        self.assertEqual(result["version"],VERSION)
        self.assertEqual(result["studiedRaceCount"],1)
        row=result["races"][0]
        self.assertEqual(row["rosterCount"],5)
        self.assertEqual(row["observedCount"],4)
        self.assertEqual(row["unassessedCount"],1)
        self.assertEqual(row["arrowObservedCount"],4)
        self.assertEqual(row["arrowUnobservedCount"],1)
        self.assertEqual(row["rankingScope"],"tky_arrow_first_index_descriptive_only")
        self.assertEqual(row["comparableDirectionPairs"],2)
        self.assertEqual(row["disagreeDirectionPairs"],2)
        self.assertEqual(row["arrows"],[
            {"number":4,"condition":"デキ抜群"},
            {"number":2,"condition":"上昇"},
            {"number":3,"condition":"上昇"},
            {"number":1,"condition":"やや下降"},
        ])
        self.assertEqual(row["runners"],[
            {"number":1,"observedRank":1},
            {"number":2,"observedRank":2},
            {"number":3,"observedRank":2},
            {"number":5,"observedRank":4},
        ])
        self.assertTrue(result["trainingSourceDistinctFromTcy"])
        self.assertTrue(result["trainingArrowPriority"])
        self.assertEqual(result["sourceMetric"],
                         "tky_training_index_and_training_arrow")
        self.assertFalse(result["training30Ready"])
        self.assertFalse(result["predictionReady"])
        self.assertEqual(result["ticketsIssued"],0)
        self.assertEqual(result["newProviderRequests"],0)
        for private in ("PAID-TEST-HORSE","horse_id","racekey",
                        "training_index':","16.0","12.0","-5.5"):
            self.assertNotIn(private,repr(result))

    def test_no_assessment_when_less_than_two_observed(self):
        p,e,r=fixture()
        for item in e[1:]:
            item["training_index"]=None
            item["training_arrow"]=None
        e[0]["training_arrow"]=None
        result=tky_training_index_study(p,e,r,DAY,now=NOW)
        self.assertEqual(result["races"],[])
        self.assertEqual(result["studiedRaceCount"],0)

    def test_arrow_only_is_useful_even_if_numeric_index_is_missing(self):
        p,e,r=fixture()
        for entry in e:entry["training_index"]=None
        result=tky_training_index_study(p,e,r,DAY,now=NOW)
        self.assertEqual(result["studiedRaceCount"],1)
        row=result["races"][0]
        self.assertEqual(row["observedCount"],0)
        self.assertEqual(row["unassessedCount"],5)
        self.assertEqual(row["arrowObservedCount"],4)
        self.assertEqual(row["runners"],[])
        self.assertEqual(row["arrows"][0],{
            "number":4,"condition":"デキ抜群"
        })
        self.assertEqual(row["arrows"][-1],{
            "number":1,"condition":"やや下降"
        })
        self.assertFalse(result["predictionReady"])

    def test_invalid_arrow_codes_never_become_expert_evidence(self):
        p,e,r=fixture()
        for i,item in enumerate(e):
            item["training_arrow"]=("9","",None,4,False)[i]
            item["training_index"]=None
        result=tky_training_index_study(p,e,r,DAY,now=NOW)
        self.assertEqual(result["races"],[])
        self.assertEqual(result["studiedRaceCount"],0)

    def test_number_only_and_arrow_are_not_combined_into_fake_score(self):
        p,e,r=fixture()
        # The largest numeric index is horse 1, but the best expert arrow
        # is horse 4. Never promote numeric order to superior condition.
        result=tky_training_index_study(p,e,r,DAY,now=NOW)
        row=result["races"][0]
        self.assertEqual(row["runners"][0]["number"],1)
        self.assertEqual(row["arrows"][0]["number"],4)
        self.assertNotIn("score",repr(result))
        self.assertNotIn("tickets",repr(row))
        self.assertFalse(result["training30Ready"])

    def test_arrow_index_disagreements_are_observation_only(self):
        p,e,r=fixture()
        # Horse 1 has a worse arrow than horses 2 and 3 but a higher
        # numeric index: two genuine opposite-direction comparisons.
        contradictory=tky_training_index_study(p,e,r,DAY,now=NOW)["races"][0]
        self.assertEqual(contradictory["comparableDirectionPairs"],2)
        self.assertEqual(contradictory["disagreeDirectionPairs"],2)
        self.assertNotIn("score",repr(contradictory))
        self.assertNotIn("training_index",repr(contradictory))

        # Reverse numeric ordering to agree with the expert arrows.
        e[0]["training_index"]="4.0"
        agreed=tky_training_index_study(p,e,r,DAY,now=NOW)["races"][0]
        self.assertEqual(agreed["comparableDirectionPairs"],2)
        self.assertEqual(agreed["disagreeDirectionPairs"],0)

        # Equal-arrow pairs do not have a directional verdict.
        e[0]["training_arrow"]="2"
        tied=tky_training_index_study(p,e,r,DAY,now=NOW)["races"][0]
        self.assertEqual(tied["comparableDirectionPairs"],0)
        self.assertEqual(tied["disagreeDirectionPairs"],0)

        # Missing all indexes still allows arrow-only observations,
        # but must not invent a comparison count.
        for entry in e:
            entry["training_index"]=None
        only_arrows=tky_training_index_study(p,e,r,DAY,now=NOW)["races"][0]
        self.assertEqual(only_arrows["comparableDirectionPairs"],0)
        self.assertEqual(only_arrows["disagreeDirectionPairs"],0)

    def test_race_closed_after_provisional_post(self):
        p,e,r=fixture()
        for instant in (LATE,datetime.fromisoformat("2099-01-01T11:00:00+09:00")):
            with self.subTest(instant=instant):
                result=tky_training_index_study(p,e,r,DAY,now=instant)
                self.assertEqual(result["races"],[])
        self.assertEqual(tky_training_index_study(p,e,r,DAY,now=NOW)
                         ["studiedRaceCount"],1)

    def test_not_a_fallback_when_existing_training_grades_complete(self):
        p,e,r=fixture()
        for item in r["races"][0]["runners"]:item["training"]="A"
        self.assertEqual(tky_training_index_study(p,e,r,DAY,now=NOW)["races"],[])

    def test_withdrawals_mismatched_roster_and_ids_are_not_ranked(self):
        for edit in ("withdraw","roster","identifiers","source_date"):
            p,e,r=fixture()
            if edit=="withdraw":e[0]["withdrawn_flag"]="1"
            if edit=="roster":r["races"][0]["runners"][0]["number"]=18
            if edit=="identifiers":e[0]["horse_id"]=e[1]["horse_id"]
            if edit=="source_date":e[0]["racedate"]="20990102"
            with self.subTest(edit=edit):
                if edit=="source_date":
                    with self.assertRaises(CoverageError):
                        tky_training_index_study(p,e,r,DAY,now=NOW)
                else:
                    self.assertEqual(tky_training_index_study(p,e,r,DAY,now=NOW)["races"],[])

    def test_bad_source_index_not_promoted_to_strong_grade(self):
        for raw in ("1,000", "NaN","inf","0e100",[],{},True,10000,-5000):
            with self.subTest(raw=raw):
                self.assertIsNone(_index(raw))
        self.assertEqual(_index("0.0"),0)
        self.assertEqual(_index("-5.5"),-5.5)

    def test_strict_input_contract(self):
        p,e,r=fixture()
        with self.assertRaises(CoverageError):
            tky_training_index_study(p,e,r,DAY,now=datetime(2099,1,1,9))
        with self.assertRaises(CoverageError):
            tky_training_index_study(p,e,r,"not-a-day",now=NOW)
        with self.assertRaises(CoverageError):
            tky_training_index_study(p,e,r,DAY,now=None)
        broken=copy.deepcopy(r)
        broken["officialJraVerified"]=True
        with self.assertRaises(CoverageError):
            tky_training_index_study(p,e,broken,DAY,now=NOW)


if __name__=="__main__":
    unittest.main()
