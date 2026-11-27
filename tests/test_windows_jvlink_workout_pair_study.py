import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from windows_jvlink_workout_pair_study import evaluate, composite_direction


def obs(day="20261120",center="0",speed=120,gain=10, *, surface="SLOP", four=None, six=None):
    return {"date":day,"center":center,"surface":surface,"course":None,
            "direction":None,"lastFurlongTenths":speed,
            "lastFurlongGainTenths":gain,"totalTenths":{4:four,6:six}}


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
        for name in ("lastFurlongTenths", "lastFurlongGainTenths"):
            metric = s["metrics"][name]
            self.assertEqual(metric["comparablePairs"],1)
            self.assertEqual(metric["concordant"],1)
        self.assertFalse(result["formalTrainingGradeReady"])
        self.assertFalse(result["modelSaved"])

    def test_total_clocks_match_same_distance_and_skip_missing_values(self):
        horses = [("a",1),("b",2),("c",3),("d",4)]
        source = [("2026112805010101",("20261129","05","芝",1800,horses),None)]
        records = {
            "a":[obs(surface="WOOD", four=480, six=760)],
            "b":[obs(surface="WOOD", four=500, six=740)],
            "c":[obs(surface="WOOD", four=None, six=800, center="1")],
            "d":[obs(surface="WOOD", four=None, six=None)],
        }
        with patch("windows_jvlink_workout_pair_study.completed_races",return_value=source), \
             patch("windows_jvlink_workout_pair_study.observations_before",
                   return_value={"byPrivateHorseId":records,"heldWorkoutKeys":0}):
            result = evaluate(None,{"WOOD":None},as_of_day="20261130")
        metrics = result["bySpec"]["WOOD"]["metrics"]
        self.assertEqual(metrics["fourFurlongTenths"]["comparablePairs"],1)
        self.assertEqual(metrics["fourFurlongTenths"]["concordant"],1)
        self.assertEqual(metrics["sixFurlongTenths"]["comparablePairs"],1)
        self.assertEqual(metrics["sixFurlongTenths"]["discordant"],1)
        self.assertFalse(result["formalTrainingGradeReady"])

    def test_fixed_composite_distinguishes_missing_ties_and_surface_weight(self):
        self.assertIsNone(composite_direction({"SLOP":{"lastFurlongTenths":1}}))
        self.assertIsNone(composite_direction({"SLOP":{"lastFurlongTenths":1},
                                               "WOOD":{"lastFurlongTenths":1}}))
        self.assertEqual(composite_direction({"SLOP":{"lastFurlongTenths":1,
                                                      "fourFurlongTenths":-1}}),0)
        self.assertEqual(composite_direction({"SLOP":{"lastFurlongTenths":1},
                                               "WOOD":{"lastFurlongTenths":-1,
                                                       "fourFurlongTenths":-1}}),0)
        self.assertEqual(composite_direction({"SLOP":{"lastFurlongTenths":1,
                                                      "fourFurlongTenths":0}}),1)

    def test_composite_reports_separate_periods_and_unobserved_pairs(self):
        horses=[("a",1),("b",2),("c",3),("d",4)]
        source=[(day+"05010101",(day,"05","芝",1800,horses),None)
                for day in ("20260630","20260701")]
        def observations(conn,spec,day,ids):
            return {"byPrivateHorseId":{
                "a":[obs(speed=120,gain=10)],"b":[obs(speed=130,gain=5)],
                "c":[],"d":[]}, "heldWorkoutKeys":0}
        with patch("windows_jvlink_workout_pair_study.completed_races",return_value=source), \
             patch("windows_jvlink_workout_pair_study.observations_before",
                   side_effect=observations):
            result=evaluate(None,{"SLOP":None},as_of_day="20261130")
        self.assertEqual(result["holdoutStart"],"20260701")
        for period in ("earlier","holdout"):
            s=result["compositeStudy"][period]
            self.assertEqual(s["totalPairs"],6)
            self.assertEqual(s["comparablePairs"],1)
            self.assertEqual(s["insufficient"],5)
            self.assertEqual(s["concordant"],1)
        self.assertFalse(result["weightsFitted"])
        self.assertFalse(result["formalTrainingGradeReady"])

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
