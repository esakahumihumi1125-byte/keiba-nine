"""Synthetic-only review of rebound contexts. Zero actual bets."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_private_factor_bridge import build_private_factor_matrix
from jrdb_experimental_condition_grades import hypothesis_from_owner_history
from jrdb_experimental_pace_scenarios import hypothesize_owner_pace
from jrdb_experimental_rebound_review import build_rebound_context_review
from test_jrdb_private_factor_bridge import inputs


def fixtures():
    matrix = build_private_factor_matrix(*inputs())
    race = matrix[0]
    template = copy.deepcopy(race["byNumber"]["01"])
    race["byNumber"] = {}
    settings = [
        ("S","C","frontObserved"),
        ("A","C","backObserved"),
        ("S","B","backObserved"),
        ("B","C","mixedObserved"),
        ("A","A","insufficient")
    ]
    rows = []
    for i,(train,recent,style) in enumerate(settings,1):
        n = f"{i:02d}"
        slots = copy.deepcopy(template)
        slots["training"]["grade"] = train
        slots["recent"]["grade"] = recent
        slots["pace"]["positionObservation"] = style
        race["byNumber"][n] = slots
        if i==1:
            c,ct,k,m,mt = 3,2,3,3,2
        elif i==2:
            c,ct,k,m,mt = 3,2,3,3,2
        elif i==3:
            c,ct,k,m,mt = 3,1,3,1,0
        else:
            c,ct,k,m,mt = 0,0,0,0,0
        rows.append({
            "number":i,"comparableRuns":c,"comparableTopThreeRuns":ct,
            "knownGoingRuns":k,"matchingCurrentGoingRuns":m,
            "matchingCurrentGoingTopThreeRuns":mt,
            "wetGoingRuns":0,"wetTopThreeRuns":0,
            "missingPastProgrammes":0,"historyLookupComplete":True,
            "currentGoingRecorded":True
        })
    history = {
        "version":"owner-runner-course-going-observation-2",
        "raceCount":len(matrix),"researchOnly":True,"privateOwnerOnly":True,
        "officialJraVerified":False,"gradeReady":False,
        "predictionReady":False,"bettingReady":False,
        "races":[{
            "track":race["track"],"race":race["race"],"runnerCount":5,
            "runners":rows,"gradeReady":False,
            "courseSuitabilityAssessed":False,
            "goingSuitabilityAssessed":False,"paceForecastReady":False
        }]
    }
    # The existing private factor matrix includes a second (Kyoto) race.
    other = matrix[1]
    history["races"].append({
        "track":other["track"],"race":other["race"],
        "runnerCount":len(other["byNumber"]),
        "runners":[{
            "number":int(n),"comparableRuns":0,"comparableTopThreeRuns":0,
            "knownGoingRuns":0,"matchingCurrentGoingRuns":0,
            "matchingCurrentGoingTopThreeRuns":0,"wetGoingRuns":0,
            "wetTopThreeRuns":0,"missingPastProgrammes":0,
            "historyLookupComplete":False,"currentGoingRecorded":False
        } for n in other["byNumber"]],
        "gradeReady":False,"courseSuitabilityAssessed":False,
        "goingSuitabilityAssessed":False,"paceForecastReady":False
    })
    bands=hypothesis_from_owner_history(history)
    pace=hypothesize_owner_pace(matrix)
    return matrix,history,bands,pace


class ReboundContextReviewTests(unittest.TestCase):
    def test_multi_source_vs_correlated_histories_and_no_auto_tickets(self):
        args=fixtures()
        before=copy.deepcopy(args)
        result=build_rebound_context_review(*args)
        self.assertEqual(args,before)
        self.assertEqual(result["factorWeights"],{
            "training":30,"recent":3,"course_distance":20,
            "pace":20,"ground":12
        })
        self.assertTrue(result["contextRequiresPaceAndHistory"])
        self.assertTrue(result["historyOnlySignalsMayOverlap"])
        self.assertFalse(result["winPickReady"])
        self.assertFalse(result["bettingReady"])
        self.assertFalse(result["modifiesFrozenPicks"])
        self.assertEqual(result["watchCount"],3)
        self.assertEqual(result["crossSourceReviewCount"],1)
        tokyo=next(r for r in result["races"] if r["track"]=="東京")
        watch={r["number"]:r for r in tokyo["watch"]}
        self.assertEqual(set(watch),{1,2,3})
        self.assertEqual(watch[1]["reviewState"],"cross_source_review")
        self.assertEqual(watch[1]["contextSignalCount"],3)
        self.assertEqual(watch[2]["reviewState"],"overlapping_history_only")
        self.assertEqual(watch[2]["contextSignalCount"],2)
        self.assertEqual(watch[3]["reviewState"],"need_more_evidence")
        self.assertEqual(watch[3]["contextSignalCount"],1)
        self.assertEqual(watch[1]["trainingProvisional"],"S")
        self.assertEqual(watch[1]["recentProvisional"],"C")
        self.assertTrue(all(not x["winPickReady"] for x in watch.values()))
        for forbidden in ("racekey","horse_id","byNumber","PAID-SECRET"):
            self.assertNotIn(forbidden,repr(result))

    def test_no_review_when_training_is_not_high_or_recent_is_not_low(self):
        m,h,_,_=fixtures()
        for race in m:
            for slots in race["byNumber"].values():
                slots["recent"]["grade"]="S"
        r=build_rebound_context_review(
            m,h,hypothesis_from_owner_history(h),
            hypothesize_owner_pace(m))
        self.assertEqual(r["watchCount"],0)
        self.assertEqual(r["crossSourceReviewCount"],0)

    def test_missing_pace_does_not_promote_two_correlated_history_signals(self):
        m,h,_,_=fixtures()
        m[0]["byNumber"]["01"]["pace"]["positionObservation"]="insufficient"
        b=hypothesis_from_owner_history(h)
        p=hypothesize_owner_pace(m)
        r=build_rebound_context_review(m,h,b,p)
        one=next(x for x in r["races"] if x["track"]=="東京")["watch"][0]
        self.assertEqual(one["reviewState"],"overlapping_history_only")
        self.assertFalse(one["winPickReady"])

    def test_untrusted_source_or_identity_mismatch_fails_closed(self):
        def reject(update):
            args=list(fixtures())
            update(args)
            with self.assertRaises(CoverageError):
                build_rebound_context_review(*args)
        reject(lambda a:a[2]["races"][0]["runners"][0].update(
            courseEvidenceBand="C"))
        reject(lambda a:a[3]["races"][0]["runners"][0].update(
            scenarioFitBand="B"))
        reject(lambda a:a[1]["races"][0]["runners"][0].update(number=18))
        reject(lambda a:a[0][0]["byNumber"]["01"]["training"].update(
            grade="X"))
        reject(lambda a:a[0][0]["byNumber"]["01"]["ground"].update(
            grade="S"))


if __name__=="__main__":
    unittest.main()
