"""Synthetic 85-weight prestart attestation tests; no licensed provider data."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_five_core_receipts import (
    issue_five_core_receipts, verify_five_core_receipts, FiveCoreReceiptError
)
from evaluation_policy import POINTS
from test_owner_three_core_receipts import source as three_fixture, SECRET, DAY
from test_private_service import call, SETTINGS
from private_service import create_app

WEIGHTS = {"training":30, "course_distance":20, "pace":20,
           "ground":12, "recent":3}
FACTOR_KEYS = set(WEIGHTS)


def sample():
    history, programme, now = three_fixture()
    races = []
    for three in history["threeCoreResearch"]["races"]:
        runners = []
        for old in three["horses"]:
            bands = {**old["bands"], "ground":"A", "recent":"C"}
            missing = [key for key in WEIGHTS if bands[key] == "未評価"]
            raw = None if missing else sum(WEIGHTS[key]*POINTS[bands[key]]
                                          for key in WEIGHTS)
            runners.append({
                "number":old["number"],"bands":bands,"missing":missing,
                "rawThirdPoints":raw,
                "evidenceScore85":None if raw is None else round(raw/3,2),
                "scoreIsCalibrated":False,"formalScore100":None,
                "formalGrade":"未評価","formalRank":None,"bettingReady":False,
            })
        races.append({
            "track":three["track"],"race":three["race"],
            "runnerCount":len(runners),"horses":runners,
            "completeObserved":sum(h["rawThirdPoints"] is not None
                                   for h in runners),
            "formalGradeReady":False,"trifectaReady":False,
            "comparisonIsFormalRank":False,
        })
    history["fiveCoreResearch"] = {
        "version":"owner-five-core-research-1","policyVersion":"research-5",
        "factorWeights":dict(WEIGHTS),"observedWeightTotal":85,
        "factorGradesVerified":0,"overallPredictionReady":False,
        "formalScoreReady":False,"officialJraVerified":False,
        "bettingReady":False,"autoPurchase":False,
        "changesExistingTickets":False,
        "changesExistingCoreReceipts":False,
        "historicalBandsNotCalibrated":True,"researchOnly":True,
        "privateOwnerOnly":True,
        "races":races,"raceCount":len(races),
    }
    return history, programme, now


class FiveCoreAttestationTests(unittest.TestCase):
    def test_all_five_hypotheses_are_frozen_before_off_and_reverified(self):
        history, programme, now = sample()
        original = copy.deepcopy((history, programme))
        output = issue_five_core_receipts(history,programme,SECRET,DAY,now)
        self.assertEqual((history,programme),original)
        self.assertEqual(output["receiptCount"],2)
        self.assertFalse(output["calibrationReady"])
        self.assertFalse(output["jraScheduleVerified"])
        self.assertFalse(output["officialResultsVerified"])
        self.assertFalse(output["bettingReady"])
        verified = verify_five_core_receipts(output["receipts"],SECRET,DAY)
        self.assertEqual([s["track"] for s in verified],["東京","京都"])
        self.assertEqual(verified[0]["raceRunnerCount"],3)
        self.assertEqual(verified[0]["observedRunnerCount"],2)
        self.assertEqual([h["number"] for h in verified[0]["horses"]],[1,2])
        for snap in verified:
            self.assertEqual(snap["sourceKind"],"prestart-uncalibrated-85-research")
            for runner in snap["horses"]:
                self.assertEqual(set(runner["bands"]),FACTOR_KEYS)
                self.assertEqual(runner["rawThirdPoints"],sum(
                    WEIGHTS[k]*POINTS[v] for k,v in runner["bands"].items()))
        for private in ("horse_id","racekey","paid_","odds","trifectaTickets",
                        "realPredictionReady","result","payout"):
            self.assertNotIn(private,repr(output))
        self.assertNotEqual(output["receipts"][0]["signature"],
                            __import__("owner_three_core_receipts")._seal(
                                verified[0],SECRET))

    def test_started_or_unknown_off_races_can_never_get_retroactive_signatures(self):
        history, programme, now = sample()
        after = datetime(2099,4,12,2,1,tzinfo=timezone.utc)
        response = issue_five_core_receipts(history,programme,SECRET,DAY,after)
        self.assertEqual(response["receiptCount"],0)
        self.assertEqual(response["postOffOrMissingTimeRaces"],2)
        programme[0]["post_time"]=None
        one=issue_five_core_receipts(history,programme,SECRET,DAY,now)
        self.assertEqual(one["receiptCount"],1)
        programme.append(copy.deepcopy(programme[0]))
        with self.assertRaises(FiveCoreReceiptError):
            issue_five_core_receipts(history,programme,SECRET,DAY,now)

    def test_invalid_grade_missing_runner_and_forgery_fail_closed(self):
        history, programme, now = sample()
        original=issue_five_core_receipts(history,programme,SECRET,DAY,now)["receipts"]
        edits = (
            lambda x: x[0]["snapshot"]["horses"][0].update(rawThirdPoints=255),
            lambda x: x[0]["snapshot"]["horses"][0]["bands"].update(recent="S"),
            lambda x: x[0]["snapshot"].update(predictionReady=True),
            lambda x: x[0]["snapshot"].update(sourceKind="official"),
            lambda x: x[0]["snapshot"].update(capturedAt="2099-04-13T00:00:00Z"),
            lambda x: x[0].update(signature="f"*64),
            lambda x: x[0]["snapshot"]["horses"].append(
                copy.deepcopy(x[0]["snapshot"]["horses"][0])),
        )
        for mutation in edits:
            v=copy.deepcopy(original)
            mutation(v)
            with self.subTest(mutation=repr(mutation)),self.assertRaises(
                    FiveCoreReceiptError):
                verify_five_core_receipts(v,SECRET,DAY)
        with self.assertRaises(FiveCoreReceiptError):
            verify_five_core_receipts(original+original[:1],SECRET,DAY)
        with self.assertRaises(FiveCoreReceiptError):
            verify_five_core_receipts(original,"some-other-secret-123456789012345",DAY)
        for mutation in (
            lambda d:d["fiveCoreResearch"].update(formalScoreReady=True),
            lambda d:d["fiveCoreResearch"]["races"][0]["horses"][0].update(
                evidenceScore85=100.0),
            lambda d:d["fiveCoreResearch"]["races"][0]["horses"][0].update(
                rawThirdPoints=255),
            lambda d:d["fiveCoreResearch"]["races"][0].update(
                completeObserved=0),
        ):
            v=copy.deepcopy(history);mutation(v)
            with self.subTest(mutation=repr(mutation)),self.assertRaises(
                    FiveCoreReceiptError):
                issue_five_core_receipts(v,programme,SECRET,DAY,now)

    def test_private_verify_route_no_external_fetches_or_payouts(self):
        history,programme,now=sample()
        receipts=issue_five_core_receipts(
            history,programme,SETTINGS["KEIBA_OWNER_PASSWORD"],DAY,now)["receipts"]
        private=create_app({
            **SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
            "KEIBA_RENDER_PREVIEW_ONLY":"0"
        })
        with patch("private_service.fetch_finished_race_results") as results,patch(
                "private_service.fetch_historical_race_programme") as paid:
            response=call(private,"/api/owner-five-core-verify",method="POST",
                          data={"date":DAY,"receipts":receipts})
            results.assert_not_called()
            paid.assert_not_called()
        self.assertEqual(response["status"],"200 OK")
        body=json.loads(response["body"])
        self.assertTrue(body["serverSigned"])
        self.assertEqual(body["recordCount"],2)
        self.assertFalse(body["calibrationReady"])
        self.assertFalse(body["officialJraVerified"])
        self.assertFalse(body["resultComparisonReady"])
        self.assertNotIn("horses",body)
        self.assertEqual(call(private,"/api/owner-five-core-verify",auth="",
                              method="POST",data={"date":DAY,"receipts":receipts})["status"],
                         "401 Unauthorized")
        self.assertEqual(call(create_app(SETTINGS),"/api/owner-five-core-verify",
                              method="POST",data={"date":DAY,"receipts":receipts})["status"],
                         "404 Not Found")
        for altered in (
            {"date":DAY,"receipts":receipts,"result":[1,2,3]},
            {"date":DAY,"receipts":receipts,"payout":100000},
            {"date":DAY,"receipts":[{**receipts[0],"signature":"f"*64}]},
            {"date":"20990413","receipts":receipts},
        ):
            self.assertEqual(call(private,"/api/owner-five-core-verify",
                             method="POST",data=altered)["status"],"400 Bad Request")


if __name__=="__main__":
    unittest.main()
