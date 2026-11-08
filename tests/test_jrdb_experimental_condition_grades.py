"""Unvalidated course/going evidence bands are never bet recommendations."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_experimental_condition_grades import hypothesis_from_owner_history

def source():
    return {
      "version":"owner-runner-course-going-observation-2",
      "raceCount":1,"researchOnly":True,"privateOwnerOnly":True,
      "officialJraVerified":False,"gradeReady":False,
      "predictionReady":False,"bettingReady":False,
      "races":[{
        "track":"東京","race":1,"runnerCount":2,
        "gradeReady":False,"courseSuitabilityAssessed":False,
        "goingSuitabilityAssessed":False,"paceForecastReady":False,
        "runners":[
          dict(number=1,comparableRuns=3,comparableTopThreeRuns=2,
               knownGoingRuns=3,matchingCurrentGoingRuns=3,
               matchingCurrentGoingTopThreeRuns=2,wetGoingRuns=3,
               wetTopThreeRuns=2,missingPastProgrammes=0,
               historyLookupComplete=True,currentGoingRecorded=True),
          dict(number=2,comparableRuns=5,comparableTopThreeRuns=0,
               knownGoingRuns=5,matchingCurrentGoingRuns=5,
               matchingCurrentGoingTopThreeRuns=0,wetGoingRuns=0,
               wetTopThreeRuns=0,missingPastProgrammes=0,
               historyLookupComplete=True,currentGoingRecorded=True)
        ]
      }]
    }

class ExperimentalConditionGradeTests(unittest.TestCase):
    def test_research_only_and_not_in_final_ten_factor_rank(self):
        original=source()
        frozen=copy.deepcopy(original)
        result=hypothesis_from_owner_history(original)
        self.assertEqual(original,frozen)
        self.assertEqual(result["version"],"owner-condition-evidence-hypothesis-1")
        self.assertEqual(result["minComparableSamples"],3)
        self.assertEqual((result["courseDistanceWeight"],result["goingWeight"]),(20,12))
        a,b=result["races"][0]["runners"]
        self.assertEqual((a["courseEvidenceBand"],a["goingEvidenceBand"]),("S","S"))
        self.assertEqual((b["courseEvidenceBand"],b["goingEvidenceBand"]),("C","C"))
        self.assertTrue(result["negativeBandNeverExcludesRebound"])
        self.assertTrue(result["evidenceBandsNotSuitability"])
        self.assertFalse(result["overallScoreReady"])
        self.assertFalse(result["winnerPickReady"])
        self.assertFalse(result["bettingReady"])
        for forbidden in ("racekey","horse_id","byNumber","horse_name"):
            self.assertNotIn(forbidden,repr(result))

    def test_diverse_boundary_starts_and_placings(self):
        expected={
           (3,2):"S",(3,1):"A",(3,0):"B",
           (4,3):"S",(4,2):"A",(4,1):"B",
           (5,4):"S",(5,2):"A",(5,1):"B",(5,0):"C"
        }
        for (runs,hit),grade in expected.items():
            with self.subTest(runs=runs,hit=hit):
                report=source()
                horse=report["races"][0]["runners"][0]
                horse.update(comparableRuns=runs,comparableTopThreeRuns=hit,
                             knownGoingRuns=runs,matchingCurrentGoingRuns=runs,
                             matchingCurrentGoingTopThreeRuns=hit,wetGoingRuns=0,
                             wetTopThreeRuns=0)
                out=hypothesis_from_owner_history(report)["races"][0]["runners"][0]
                self.assertEqual((out["courseEvidenceBand"],out["goingEvidenceBand"]),
                                 (grade,grade))

    def test_missing_and_new_horses_never_get_artificial_c_grade(self):
        for changes,reason in (
            (dict(comparableRuns=0,comparableTopThreeRuns=0,knownGoingRuns=0,
                  matchingCurrentGoingRuns=0,matchingCurrentGoingTopThreeRuns=0,
                  wetGoingRuns=0,wetTopThreeRuns=0),"sample_below_three"),
            (dict(historyLookupComplete=False),"incomplete_history"),
            (dict(currentGoingRecorded=False,matchingCurrentGoingRuns=0,
                  matchingCurrentGoingTopThreeRuns=0),"current_going_unknown"),
            (dict(knownGoingRuns=1,matchingCurrentGoingRuns=1,
                  matchingCurrentGoingTopThreeRuns=1,wetGoingRuns=0,
                  wetTopThreeRuns=0),"incomplete_history"),
        ):
            with self.subTest(reason=reason,changes=changes):
                report=source()
                h=report["races"][0]["runners"][0]
                h.update(changes)
                out=hypothesis_from_owner_history(report)["races"][0]["runners"][0]
                self.assertEqual(out["goingEvidenceBand"],"未評価")
                self.assertEqual(out["goingReason"],reason)

    def test_bad_numbers_and_promoted_source_fail_closed(self):
        for field,value in (
           ("comparableRuns",True),("comparableTopThreeRuns",6),
           ("matchingCurrentGoingTopThreeRuns",4),
           ("matchingCurrentGoingTopThreeRuns",-1),
           ("wetGoingRuns",5),
           ("missingPastProgrammes",1),
        ):
            report=source()
            report["races"][0]["runners"][0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(CoverageError):
                hypothesis_from_owner_history(report)
        for flag in ("officialJraVerified","bettingReady","gradeReady"):
            report=source()
            report[flag]=True
            with self.subTest(flag=flag),self.assertRaises(CoverageError):
                hypothesis_from_owner_history(report)
        report=source()
        report["races"][0]["runners"][1]["number"]=1
        with self.assertRaises(CoverageError):
            hypothesis_from_owner_history(report)

if __name__=="__main__":
    unittest.main()
