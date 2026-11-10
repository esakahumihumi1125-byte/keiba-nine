"""Owner one-previous-race staff source trial; every byte is synthetic."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_history_pipeline import plan_bounded_history
from owner_past_staff_sample import (
    inspect_one_past_staff_sample, VERSION
)
from test_jrdb_history_pipeline import context
from test_private_service import SETTINGS, call
from private_service import create_app


def synthetic_pair(key, date):
    dky, dse = [], []
    for n in range(1, 8):
        base = {
            "racedate": date, "racekey": key, "horse_number": f"{n:02d}",
            "horse_id": f"2328aaa95a{n:02d}",
            "resultkey": f"{10000000+n:08d}{date}",
        }
        dky.append({
            **base, "bracket_number": str(n),
            "weight_to_carry": "55.0" if n < 4 else "58.0",
            "jockey_cd": "70298" if n < 4 else "12345",
            "trainer_cd": "10485" if n < 4 else "54321",
            "withdrawn_flag": "0",
            "horse_name": "LICENSED_NAME_DO_NOT_DISPLAY"
        })
        dse.append({
            **base, "order_of_finish": str(n),
            "trouble_classification": None,
            "confirmed_win_odds": "SECRET_ODDS"
        })
    return dky, dse


def source_context():
    programme, entries, previous, current, dra, dka = context()
    plan = plan_bounded_history(programme, entries, previous, "20261101", 8)
    key, date = plan["privateSelected"][0]
    dky, dse = synthetic_pair(key, date)
    return (programme, entries, previous, current), key, dky, dse


class OwnerPastStaffTrialTests(unittest.TestCase):
    def test_uses_exactly_two_provider_reads_and_returns_no_raw_staff(self):
        (p, entries, previous, _), key, dky, dse = source_context()
        original = copy.deepcopy((p, entries, previous, dky, dse))
        a, b = Mock(return_value=dky), Mock(return_value=dse)
        report = inspect_one_past_staff_sample(
            p, entries, previous, "20261101", fetch_dky=a, fetch_dse=b)
        self.assertEqual((p, entries, previous, dky, dse), original)
        a.assert_called_once_with(key)
        b.assert_called_once_with(key)
        self.assertEqual(report["version"], VERSION)
        self.assertEqual(report["status"], "joined_private_sample")
        self.assertEqual(report["providerReadCount"], 2)
        self.assertEqual(report["pastRacesSelected"], 1)
        self.assertEqual(report["runnerCount"], 7)
        self.assertEqual(report["distinctJockeyCount"], 2)
        self.assertEqual(report["distinctTrainerCount"], 2)
        self.assertEqual(report["distinctPairCount"], 2)
        self.assertEqual(report["observedFirstPlaceCount"], 1)
        self.assertEqual(report["observedTop3Count"], 3)
        self.assertEqual(report["formalTenPointGrade"], "未評価")
        self.assertIsNone(report["formalTenPointScore"])
        for false in ("pastResultPublicationVerified","independentJraVerified",
                      "jockeyTrainerPerformanceAssessed","holdoutValidated",
                      "predictionReady","bettingReady","autoPurchase",
                      "actualPurchase","changesExistingReceipts",
                      "changesExistingTickets","changesExistingRoi"):
            self.assertFalse(report[false])
        for private in ("2328aaa95a","70298","10485",
                        "LICENSED_NAME", "SECRET_ODDS","racekey","horseRef"):
            self.assertNotIn(private,repr(report))

    def test_disqualified_provider_results_hold_without_extra_races(self):
        (p, entries, previous, _), key, dky, dse = source_context()
        for modifier in (
            lambda a,b: b[0].update(horse_id="aaaaaaaaaaaa"),
            lambda a,b: b[0].update(order_of_finish="2"),
            lambda a,b: a[0].update(withdrawn_flag="1"),
            lambda a,b: b.pop(),
        ):
            x, y = copy.deepcopy((dky, dse))
            modifier(x,y)
            a,b = Mock(return_value=x),Mock(return_value=y)
            result=inspect_one_past_staff_sample(
                p,entries,previous,"20261101",fetch_dky=a,fetch_dse=b)
            self.assertEqual(result["status"],
                             "incomplete_or_ambiguous_historical_result")
            self.assertEqual(result["runnerCount"],0)
            self.assertIsNone(result["formalTenPointScore"])
            a.assert_called_once_with(key)
            b.assert_called_once_with(key)
        b = Mock(side_effect=RuntimeError("provider secret"))
        result=inspect_one_past_staff_sample(
            p,entries,previous,"20261101",
            fetch_dky=Mock(return_value=dky), fetch_dse=b)
        self.assertEqual(result["status"],"provider_unavailable")
        self.assertNotIn("provider secret",repr(result))

    def test_no_past_reference_makes_zero_additional_requests(self):
        p, entries, previous, _ = source_context()[0]
        a,b = Mock(),Mock()
        result=inspect_one_past_staff_sample(
            p,entries,[],"20261101",fetch_dky=a,fetch_dse=b)
        self.assertEqual(result["status"],"no_referenced_past_race")
        self.assertEqual(result["providerReadCount"],0)
        a.assert_not_called()
        b.assert_not_called()

    def test_authenticated_service_requires_explicit_staff_option(self):
        (p, entries, previous, current), key, dky, dse = source_context()
        raw_prog=[{
            "racedate":r["racedate"], "racekey":r["racekey"],
            "post_time":"1010", "headcount":r["headcount"],
            "track_type":"1" if r["surface"]=="芝" else "2",
            "distance":str(r["distance_m"]),
            "turn_cd":"2" if r["turn"]=="左" else "1",
        } for r in p]
        config={**SETTINGS,"JRDB_PRIVATE_ENABLED":"1",
                "JRDB_API_KEY":"synthetic","JRDB_AUTH_KEY":"synthetic",
                "KEIBA_HISTORY_ENABLED":"1",
                "KEIBA_RENDER_PRIVATE_ONLY":"1"}
        app=create_app(config)
        with (patch("private_service.fetch_race_program",return_value=raw_prog),
              patch("private_service.fetch_horse_entries",return_value=entries),
              patch("private_service.fetch_recent_runs",return_value=previous),
              patch("private_service.fetch_training_analysis",return_value=[]),
              patch("private_service.fetch_venue_conditions",return_value=current),
              patch("private_service.run_bounded_history_audit",
                    return_value={"date":"20261101","predictionReady":False}),
              patch("private_service.issue_rebound_watch_receipts",
                    return_value={"receiptCount":0}),
              patch("private_service.fetch_historical_runner_staff",
                    return_value=dky) as staff,
              patch("private_service.fetch_historical_finished_runners",
                    return_value=dse) as results):
            raw=call(app,"/api/jrdb/history","POST",
                     data={"date":"20261101","limit":8})
            self.assertEqual(raw["status"],"200 OK")
            self.assertNotIn("pastStaffSample",json.loads(raw["body"]))
            staff.assert_not_called()
            results.assert_not_called()
            check=call(app,"/api/jrdb/history","POST",
                      data={"date":"20261101","limit":8,"staffSample":True})
            self.assertEqual(check["status"],"200 OK")
            report=json.loads(check["body"])["pastStaffSample"]
            self.assertEqual(report["status"],"joined_private_sample")
            self.assertEqual(report["distinctPairCount"],2)
            staff.assert_called_once_with(key)
            results.assert_called_once_with(key)
            for private in (b"LICENSED_NAME",b"SECRET_ODDS",b"70298",
                            b"10485", key.encode(), b"horse_id"):
                self.assertNotIn(private,check["body"])
            for malformed in (
                {"date":"20261101","staffSample":"true"},
                {"date":"20261101","staffSample":1},
                {"date":"20261101","staffSample":None},
                {"date":"20261101","staffSample":True,"racekey":key},
            ):
                bad=call(app,"/api/jrdb/history","POST",data=malformed)
                self.assertEqual(bad["status"],"400 Bad Request")
            not_private=create_app({**config,"KEIBA_RENDER_PRIVATE_ONLY":"0"})
            refused=call(not_private,"/api/jrdb/history","POST",
                         data={"date":"20261101","staffSample":True})
            self.assertEqual(refused["status"],"403 Forbidden")
            staff.assert_called_once_with(key)
            results.assert_called_once_with(key)
            denied=call(app,"/api/jrdb/history","POST",auth="",
                        data={"date":"20261101","staffSample":True})
            self.assertEqual(denied["status"],"401 Unauthorized")
        self.assertNotIn(b"2328aaa95a",check["body"])


if __name__=="__main__":
    unittest.main()
