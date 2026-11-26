import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from windows_jvlink_workout_pair_study import evaluate


def obs(day="20261120",center="0",speed=120,gain=10):
    return {"date":day,"center":center,"surface":"SLOP","course":None,
            "direction":None,"lastFurlongTenths":speed,
            "lastFurlongGainTenths":gain}


class PairStudyTests(unittest.TestCase):
    def test_condition_match_and_latest_shared_day(self):
        horses=[("a",1),("b",2),("c",3),("d",4)]
        source=[("2026112805010101",("20261129","05","芝",1800,horses),None)]
        records={"a":[obs(speed=120),obs(speed=122,gain=12),obs(day="20261121",speed=150)],
                 "b":[obs(speed=130,gain=5)],"c":[obs(center="1")],"d":[]}
        with patch("windows_jvlink_workout_pair_study.completed_races",return_value=source), \
             patch("windows_jvlink_workout_pair_study.observations_before",
                   return_value={"byPrivateHorseId":records,"heldWorkoutKeys":1}) as check:
            result=evaluate(None,{"SLOP":None},as_of_day="20261130")
        check.assert_called_once_with(None,"SLOP","20261128",set(records))
        s=result["bySpec"]["SLOP"]
        self.assertEqual(s["runnersObserved"],3)
        self.assertEqual(s["totalRunners"],4)
        self.assertEqual(s["racesWithComparablePairs"],1)
        for metric in s["metrics"].values():
            self.assertEqual(metric["comparablePairs"],1)
            self.assertEqual(metric["concordant"],1)
        self.assertFalse(result["formalTrainingGradeReady"])
        self.assertFalse(result["modelSaved"])

    def test_ties_and_disagreement_not_hidden(self):
        source=[("2026112805010101",("20261129","05","芝",1800,[("a",1),("b",2),("c",3),("d",4)]),None)]
        records={"a":[obs(speed=130,gain=8)],"b":[obs(speed=120,gain=8)],
                 "c":[],"d":[]}
        with patch("windows_jvlink_workout_pair_study.completed_races",return_value=source), \
             patch("windows_jvlink_workout_pair_study.observations_before",
                   return_value={"byPrivateHorseId":records,"heldWorkoutKeys":0}):
            s=evaluate(None,{"SLOP":None},as_of_day="20261130")["bySpec"]["SLOP"]
        self.assertEqual(s["metrics"]["lastFurlongTenths"]["discordant"],1)
        self.assertEqual(s["metrics"]["lastFurlongGainTenths"]["tied"],1)
        self.assertIsNone(s["metrics"]["lastFurlongGainTenths"]["directionalAgreementPercent"])

if __name__=="__main__":
    unittest.main()
