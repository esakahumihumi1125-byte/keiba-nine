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
    for i,val in enumerate(("16.0","12.0","12.0",None,"-5.5"),1):
        entries.append({
            "racekey":race["racekey"],"racedate":DAY,
            "horse_number":f"{i:02d}",
            "horse_id":f"2328aaa95a{i:02d}",
            "training_index":val,
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
        self.assertEqual(row["runners"],[
            {"number":1,"observedRank":1},
            {"number":2,"observedRank":2},
            {"number":3,"observedRank":2},
            {"number":5,"observedRank":4},
        ])
        self.assertTrue(result["trainingSourceDistinctFromTcy"])
        self.assertFalse(result["training30Ready"])
        self.assertFalse(result["predictionReady"])
        self.assertEqual(result["ticketsIssued"],0)
        self.assertEqual(result["newProviderRequests"],0)
        for private in ("PAID-TEST-HORSE","horse_id","racekey",
                        "training_index':","16.0","12.0","-5.5"):
            self.assertNotIn(private,repr(result))

    def test_no_assessment_when_less_than_two_observed(self):
        p,e,r=fixture()
        for item in e[1:]:item["training_index"]=None
        result=tky_training_index_study(p,e,r,DAY,now=NOW)
        self.assertEqual(result["races"],[])
        self.assertEqual(result["studiedRaceCount"],0)

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
