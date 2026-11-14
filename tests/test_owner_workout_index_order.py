"""Synthetic JRDB /tcy within-band ordering, strict redaction and prestart."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_workout_index_order import workout_index_order, unavailable

DAY = "20990101"
BEFORE = datetime.fromisoformat("2099-01-01T09:00:00+09:00")
AFTER = datetime.fromisoformat("2099-01-01T10:00:00+09:00")
KEY = "05264b01"
GRADE = {"01":"S","02":"S","03":"A","04":"A","05":"B"}
RAW = [(80,78),(77,75),(71,62),(65,62),(52,51)]


def data():
    programme=[{
        "racekey":KEY, "racedate":DAY, "track":"東京",
        "race":1, "post_time":"10:00", "headcount":5,
    }]
    entries=[]
    training=[]
    for i, pair in enumerate(RAW,1):
        num=f"{i:02d}"
        hid=f"2328aaa95a{i:02d}"
        entries.append({
            "racekey":KEY,"racedate":DAY,"horse_number":num,
            "horse_id":hid, "horse_name":"PAID-NAME"
        })
        training.append({
            "racekey":KEY,"racedate":DAY,
            "horse_number":num,"horse_id":hid,
            "oikirisisu":pair[0],"siagarisisu":pair[1],
        })
    report={
        "version":"jrdb-owner-auto-draft-1","date":DAY,"raceCount":1,
        "researchOnly":True,"privateOwnerOnly":True,
        "officialJraVerified":False,"overallPredictionReady":False,
        "races":[{
            "track":"東京","race":1,"status":"hold",
            "reason":"ambiguous_equal_grade_boundary","postTime":"10:00",
            "runners":[{"number":i,"training":GRADE[f"{i:02d}"]}
                       for i in range(1,6)]
        }]
    }
    return programme,entries,training,report


class WorkoutIndexOrderTests(unittest.TestCase):
    def test_same_s_is_separated_by_real_index_order_without_claimed_points(self):
        inputs=data()
        before=copy.deepcopy(inputs)
        output=workout_index_order(*inputs,DAY,now=BEFORE)
        self.assertEqual(inputs,before)
        self.assertEqual((output["raceCount"],output["studiedRaceCount"]),(1,1))
        self.assertEqual(output["races"][0]["runners"],[
            {"number":1,"trainingBand":"S","withinBandRank":1},
            {"number":2,"trainingBand":"S","withinBandRank":2},
            {"number":3,"trainingBand":"A","withinBandRank":1},
            {"number":4,"trainingBand":"A","withinBandRank":1},
            {"number":5,"trainingBand":"B","withinBandRank":1},
        ])
        self.assertEqual(output["races"][0]["differentIndexPairsWithinBand"],1)
        self.assertEqual(output["races"][0]["exactTiePairsWithinBand"],1)
        for forbidden in ("racekey","horse_id","horse_name",
                          "PAID-NAME","2328aaa95a01",
                          "oikirisisu","siagarisisu","78.0"):
            self.assertNotIn(forbidden,repr(output))
        self.assertFalse(output["scoreReady"])
        self.assertFalse(output["predictionReady"])
        self.assertEqual(output["ticketsIssued"],0)
        self.assertEqual(output["newProviderRequests"],0)
        self.assertFalse(output["changesExistingReceipts"])

    def test_post_time_including_boundary_never_creates_new_order(self):
        for date in (AFTER,datetime.fromisoformat("2099-01-01T12:00:00+09:00")):
            result=workout_index_order(*data(),DAY,now=date)
            self.assertEqual(result,unavailable(DAY,1))

    def test_incomplete_unmatched_and_inconsistent_data_is_not_ranked(self):
        for mutator in (
            lambda p,e,t,r: t[0].update(siagarisisu=None),
            lambda p,e,t,r: t.append(copy.deepcopy(t[0])),
            lambda p,e,t,r: r["races"][0]["runners"][0].update(training="A"),
            lambda p,e,t,r: t[0].update(horse_number="02"),
            lambda p,e,t,r: r["races"][0].update(reason="provider_withdrawal"),
        ):
            with self.subTest(mutator=str(mutator)):
                inputs=data()
                mutator(*inputs)
                result=workout_index_order(*inputs,DAY,now=BEFORE)
                self.assertEqual(result["studiedRaceCount"],0)
                self.assertEqual(result["races"],[])

    def test_invalid_source_or_misrepresented_mode_fails(self):
        inputs=data()
        inputs[3]["officialJraVerified"]=True
        with self.assertRaises(Exception):
            workout_index_order(*inputs,DAY,now=BEFORE)
        inputs=data()
        with self.assertRaises(Exception):
            workout_index_order(*inputs,DAY,now=datetime.now())


if __name__=="__main__":
    unittest.main()
