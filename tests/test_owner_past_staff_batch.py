"""Three historical staff races: fixed 6-call ceiling and private redaction."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_history_pipeline import plan_bounded_history
from owner_past_staff_batch import inspect_three_past_staff_samples, VERSION
from test_owner_past_staff_sample import synthetic_pair
from test_jrdb_history_pipeline import context
from test_private_service import SETTINGS, call
from private_service import create_app

DAY = "20261101"


def source():
    p, entries, previous, conditions, dra, dka = context()
    plan=plan_bounded_history(p,entries,previous,DAY,8)
    selected=plan["privateSelected"][:3]
    assert len(selected)==3
    pairs={key:synthetic_pair(key,date) for key,date in selected}
    return p,entries,previous,conditions,selected,pairs


def study(p,entries,previous,read1,read2):
    return inspect_three_past_staff_samples(
        p,entries,previous,DAY,fetch_dky=read1,fetch_dse=read2)


class ThreeRaceStaffTests(unittest.TestCase):
    def test_cross_race_pair_reappears_without_rider_codes_in_output(self):
        p,e,old,_,selected,pairs=source()
        sources=copy.deepcopy(pairs)
        dky=Mock(side_effect=lambda k:copy.deepcopy(pairs[k][0]))
        dse=Mock(side_effect=lambda k:copy.deepcopy(pairs[k][1]))
        result=study(p,e,old,dky,dse)
        self.assertEqual(pairs,sources)
        self.assertEqual(dky.call_count,3)
        self.assertEqual(dse.call_count,3)
        self.assertEqual([c.args[0] for c in dky.call_args_list],
                         [key for key,_ in selected])
        self.assertEqual([c.args[0] for c in dse.call_args_list],
                         [key for key,_ in selected])
        self.assertEqual(result["version"],VERSION)
        self.assertEqual(result["requestedRaceLimit"],3)
        self.assertEqual(result["selectedPastRaceCount"],3)
        self.assertEqual(result["providerReadCount"],6)
        self.assertEqual(result["providerReadBudget"],6)
        self.assertEqual(result["completedJoinRaceCount"],3)
        self.assertEqual(result["heldOrIncompleteRaceCount"],0)
        self.assertFalse(result["providerUnavailable"])
        self.assertEqual(result["totalJoinedRunnerObservations"],21)
        self.assertEqual(result["pairRunnerObservations"],21)
        self.assertEqual(result["distinctJockeyCount"],2)
        self.assertEqual(result["distinctTrainerCount"],2)
        self.assertEqual(result["distinctPairCount"],2)
        self.assertEqual(result["pairsSeenInTwoOrMoreRaces"],2)
        self.assertEqual(result["observedFirstPlaceCount"],3)
        self.assertEqual(result["observedTopThreeCount"],9)
        self.assertEqual(result["formalTenPointGrade"],"未評価")
        self.assertIsNone(result["formalTenPointScore"])
        for key in ("pastResultPublicationVerified","independentJraVerified",
                    "fullTenFactorReady","holdoutValidated",
                    "jockeyTrainerPerformanceAssessed","predictionReady",
                    "bettingReady","autoPurchase","actualPurchase",
                    "changesExistingReceipts","changesExistingTickets",
                    "changesExistingRoi"):
            self.assertFalse(result[key])
        self.assertTrue(result["additionalPaidReadsOnlyOnExplicitOptIn"])
        for forbidden in ("2328aaa95a","70298","10485","LICENSED_NAME",
                          "SECRET_ODDS","racekey","horseRef","jockeyRef"):
            self.assertNotIn(forbidden,repr(result))

    def test_invalid_one_of_three_does_not_try_a_fourth(self):
        p,e,old,_,selected,pairs=source()
        middle=selected[1][0]
        bad=copy.deepcopy(pairs)
        bad[middle][1][0]["horse_id"]="wronghorse12"
        dky=Mock(side_effect=lambda k:copy.deepcopy(bad[k][0]))
        dse=Mock(side_effect=lambda k:copy.deepcopy(bad[k][1]))
        out=study(p,e,old,dky,dse)
        self.assertEqual(dky.call_count,3)
        self.assertEqual(dse.call_count,3)
        self.assertEqual(out["completedJoinRaceCount"],2)
        self.assertEqual(out["heldOrIncompleteRaceCount"],1)
        self.assertEqual(out["providerReadCount"],6)
        self.assertEqual(out["observedFirstPlaceCount"],2)
        self.assertEqual(out["observedTopThreeCount"],6)
        self.assertEqual(out["totalJoinedRunnerObservations"],14)

    def test_connection_error_stops_remaining_paid_reads(self):
        p,e,old,_,selected,pairs=source()
        first=selected[0][0]
        dky=Mock(side_effect=lambda k:copy.deepcopy(pairs[k][0]))
        dse=Mock(side_effect=RuntimeError("secret provider error"))
        out=study(p,e,old,dky,dse)
        self.assertEqual((dky.call_count,dse.call_count),(1,1))
        self.assertEqual(out["providerReadCount"],2)
        self.assertTrue(out["providerUnavailable"])
        self.assertEqual((out["heldOrIncompleteRaceCount"],
                          out["selectedPastRaceCount"]),(3,3))
        self.assertNotIn("secret provider",repr(out))
        dky=Mock(side_effect=RuntimeError("do not disclose"))
        dse=Mock()
        out=study(p,e,old,dky,dse)
        self.assertEqual(out["providerReadCount"],1)
        self.assertTrue(out["providerUnavailable"])
        dse.assert_not_called()

    def test_no_source_rows_zero_paid_reads(self):
        p,e,old,_,selected,pairs=source()
        dky,dse=Mock(),Mock()
        out=study(p,e,[],dky,dse)
        self.assertEqual((out["selectedPastRaceCount"],out["providerReadCount"]),(0,0))
        self.assertEqual(out["completedJoinRaceCount"],0)
        self.assertEqual(out["pairsSeenInTwoOrMoreRaces"],0)
        dky.assert_not_called()
        dse.assert_not_called()

    def test_explicit_private_service_batch_flag_with_six_calls(self):
        p,entries,old,current,selected,pairs=source()
        raw=[{
            "racedate":r["racedate"],"racekey":r["racekey"],
            "post_time":"1010","headcount":r["headcount"],
            "track_type":"1" if r["surface"]=="芝" else "2",
            "distance":str(r["distance_m"]),
            "turn_cd":"2" if r["turn"]=="左" else "1",
        } for r in p]
        opts={**SETTINGS,"JRDB_PRIVATE_ENABLED":"1",
              "JRDB_API_KEY":"synthetic","JRDB_AUTH_KEY":"synthetic",
              "KEIBA_HISTORY_ENABLED":"1","KEIBA_RENDER_PRIVATE_ONLY":"1"}
        app=create_app(opts)
        with (patch("private_service.fetch_race_program",return_value=raw),
              patch("private_service.fetch_horse_entries",return_value=entries),
              patch("private_service.fetch_recent_runs",return_value=old),
              patch("private_service.fetch_training_analysis",return_value=[]),
              patch("private_service.fetch_venue_conditions",return_value=current),
              patch("private_service.run_bounded_history_audit",
                    return_value={"date":DAY,"predictionReady":False}),
              patch("private_service.issue_rebound_watch_receipts",
                    return_value={"receiptCount":0}),
              patch("private_service.fetch_historical_runner_staff",
                    side_effect=lambda key:copy.deepcopy(pairs[key][0])) as dky,
              patch("private_service.fetch_historical_finished_runners",
                    side_effect=lambda key:copy.deepcopy(pairs[key][1])) as dse):
            no=call(app,"/api/jrdb/history",method="POST",
                    data={"date":DAY,"limit":8})
            self.assertEqual(no["status"],"200 OK")
            self.assertNotIn("pastStaffBatch",json.loads(no["body"]))
            dky.assert_not_called();dse.assert_not_called()
            yes=call(app,"/api/jrdb/history",method="POST",data={
                "date":DAY,"limit":8,"staffSample":True,"staffBatchRaces":3})
            self.assertEqual(yes["status"],"200 OK")
            payload=json.loads(yes["body"])
            self.assertNotIn("pastStaffSample",payload)
            summary=payload["pastStaffBatch"]
            self.assertEqual(summary["providerReadCount"],6)
            self.assertEqual(summary["pairsSeenInTwoOrMoreRaces"],2)
            dky.assert_has_calls([unittest.mock.call(k) for k,_ in selected])
            self.assertEqual(dky.call_count,3)
            self.assertEqual(dse.call_count,3)
            for secret in (b"LICENSED_NAME",b"SECRET_ODDS",
                           b"70298",b"10485",b"2328aaa95a",
                           b"horse_id",b"racekey"):
                self.assertNotIn(secret,yes["body"])
            for invalid in [
                {"date":DAY,"staffSample":False,"staffBatchRaces":3},
                {"date":DAY,"staffBatchRaces":3},
                {"date":DAY,"staffSample":True,"staffBatchRaces":2},
                {"date":DAY,"staffSample":True,"staffBatchRaces":99},
                {"date":DAY,"staffSample":True,"staffBatchRaces":True},
                {"date":DAY,"staffSample":True,"staffBatchRaces":"3"},
            ]:
                bad=call(app,"/api/jrdb/history",method="POST",data=invalid)
                self.assertEqual(bad["status"],"400 Bad Request")
            unauthorized=call(app,"/api/jrdb/history",method="POST",auth="",
                              data={"date":DAY,"staffSample":True,
                                    "staffBatchRaces":3})
            self.assertEqual(unauthorized["status"],"401 Unauthorized")
            not_private=create_app({**opts,"KEIBA_RENDER_PRIVATE_ONLY":"0"})
            refused=call(not_private,"/api/jrdb/history",method="POST",
                         data={"date":DAY,"staffSample":True,
                               "staffBatchRaces":3})
            self.assertEqual(refused["status"],"403 Forbidden")
            self.assertEqual(dky.call_count,3)
            self.assertEqual(dse.call_count,3)


if __name__=="__main__":
    unittest.main()
