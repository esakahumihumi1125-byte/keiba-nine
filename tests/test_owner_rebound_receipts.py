"""Prestart watch receipts are not official outcomes, tickets or purchase proof."""
import copy
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))

from owner_rebound_receipts import (
    issue_rebound_watch_receipts,verify_rebound_watch_receipts,
    compare_watched_winners,WatchReceiptError
)
from unittest.mock import patch
from private_service import create_app
from test_private_service import call, SETTINGS

DAY="20990412"
SECRET="sample signing secret 1234567890 !"*3


def sample():
    review={
        "version":"owner-rebound-context-review-1",
        "researchOnly":True,"officialJraVerified":False,
        "overallScoreReady":False,"winPickReady":False,
        "bettingReady":False,"autoPurchase":False,
        "modifiesFrozenPicks":False,"raceCount":2,
        "races":[
            {"track":"東京","race":1,"winPickReady":False,
             "watchCount":2,"watch":[
               {"number":4,"reviewState":"cross_source_review"},
               {"number":9,"reviewState":"overlapping_history_only"}
             ]},
            {"track":"京都","race":2,"winPickReady":False,
             "watchCount":1,"watch":[
               {"number":3,"reviewState":"need_more_evidence"}
             ]},
        ]
    }
    history={"date":DAY,"predictionReady":False,
             "reboundContextReview":review}
    programme=[
        {"racedate":DAY,"track":"東京","race":1,"post_time":"11:00"},
        {"racedate":DAY,"track":"京都","race":2,"post_time":"10:00"},
    ]
    now=datetime(2099,4,12,0,30,tzinfo=timezone.utc) # 09:30 JST
    return history,programme,now


class ReboundReceiptTests(unittest.TestCase):
    def test_authenticated_private_capture_and_verified_pending_api(self):
        history,programme,now=sample()
        cfg={**SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
             "KEIBA_RENDER_PREVIEW_ONLY":"0",
             "JRDB_PRIVATE_ENABLED":"1","KEIBA_HISTORY_ENABLED":"1",
             "JRDB_API_KEY":"synthetic-jrdb-api-key",
             "JRDB_AUTH_KEY":"synthetic-jrdb-auth-key"}
        app=create_app(cfg)
        with (patch("private_service.fetch_race_program",return_value=[]),
              patch("private_service.normalize_program_rows",return_value=programme),
              patch("private_service.fetch_horse_entries",return_value=[]),
              patch("private_service.fetch_recent_runs",return_value=[]),
              patch("private_service.fetch_training_analysis",return_value=[]),
              patch("private_service.fetch_venue_conditions",return_value=[]),
              patch("private_service.run_bounded_history_audit",return_value=history),
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T09:30:00+09:00")):
            r=call(app,"/api/jrdb/history",method="POST",
                   data={"date":DAY,"limit":8})
        self.assertEqual(r["status"],"200 OK")
        obj=__import__("json").loads(r["body"])
        captured=obj["watchCapture"]
        self.assertEqual(captured["receiptCount"],2)
        self.assertEqual(obj["reboundContextReview"]["version"],
                         "owner-rebound-context-review-1")
        self.assertNotIn(SECRET,r["body"].decode())
        selected=DAY[:4]+"-"+DAY[4:6]+"-"+DAY[6:]
        ok=call(app,"/api/owner-rebound-verify",method="POST",
                data={"date":DAY,"receipts":captured["receipts"]})
        self.assertEqual(ok["status"],"200 OK")
        verified=__import__("json").loads(ok["body"])
        self.assertEqual(verified["review"]["pendingRaces"],2)
        self.assertEqual(verified["review"]["reviewedRaces"],0)
        self.assertFalse(verified["officialFeedConnected"])
        forged=copy.deepcopy(captured["receipts"])
        forged[0]["snapshot"]["watch"][0]["reviewState"]="need_more_evidence"
        bad=call(app,"/api/owner-rebound-verify",method="POST",
                 data={"date":DAY,"receipts":forged})
        self.assertEqual(bad["status"],"400 Bad Request")
        self.assertEqual(call(app,"/api/owner-rebound-verify",method="POST",
                              data={"date":DAY,"receipts":captured["receipts"],
                                    "results":[{"winner":4,"officialVerified":True}]}
                              )["status"],"400 Bad Request")
        self.assertEqual(call(app,"/api/owner-rebound-verify",method="POST",
                              auth="",data={"date":DAY,"receipts":[]}
                              )["status"],"401 Unauthorized")
        private_only=create_app(SETTINGS)
        self.assertEqual(call(private_only,"/api/owner-rebound-verify",
                              method="POST",data={"date":DAY,"receipts":[]}
                              )["status"],"404 Not Found")

    def test_prestart_capture_and_signature_and_independent_domain(self):
        history,programme,now=sample()
        before=copy.deepcopy((history,programme))
        out=issue_rebound_watch_receipts(history,programme,SECRET,DAY,now)
        self.assertEqual(out["receiptCount"],2)
        self.assertEqual(out["postOffOrMissingTimeRaces"],0)
        self.assertFalse(out["officialResultsVerified"])
        snaps=verify_rebound_watch_receipts(out["receipts"],SECRET,DAY)
        self.assertEqual(snaps[0]["watch"],[
            {"number":4,"reviewState":"cross_source_review"},
            {"number":9,"reviewState":"overlapping_history_only"}])
        self.assertEqual((history,programme),before)
        self.assertFalse(snaps[0]["officialJraVerified"])
        self.assertFalse(snaps[0]["captureAuditVerified"])
        self.assertFalse(snaps[0]["actualPurchase"])
        self.assertNotIn("racekey",repr(out))
        self.assertNotIn("horse_id",repr(out))

    def test_time_gate_rejects_retroactive_and_missing_off(self):
        history,programme,_=sample()
        at_off=datetime(2099,4,12,1,0,tzinfo=timezone.utc)
        out=issue_rebound_watch_receipts(history,programme,SECRET,DAY,at_off)
        self.assertEqual(out["receiptCount"],1)
        self.assertEqual(out["postOffOrMissingTimeRaces"],1)
        self.assertEqual(out["receipts"][0]["snapshot"]["track"],"東京")
        after=datetime(2099,4,12,2,1,tzinfo=timezone.utc)
        out=issue_rebound_watch_receipts(history,programme,SECRET,DAY,after)
        self.assertEqual(out["receiptCount"],0)
        self.assertEqual(out["postOffOrMissingTimeRaces"],2)
        programme[0]["post_time"]=None
        out=issue_rebound_watch_receipts(history,programme,SECRET,DAY,sample()[2])
        self.assertEqual(out["receiptCount"],1)

    def test_signature_invalid_after_any_edit_and_wrong_date(self):
        history,programme,now=sample()
        out=issue_rebound_watch_receipts(history,programme,SECRET,DAY,now)
        original=copy.deepcopy(out["receipts"])
        for mut in (
            lambda x:x[0]["snapshot"]["watch"][0].update(number=5),
            lambda x:x[0]["snapshot"].update(capturedAt="2099-04-12T06:00:00+00:00"),
            lambda x:x[0]["snapshot"].update(officialJraVerified=True),
            lambda x:x[0]["snapshot"].update(actualPurchase=True),
            lambda x:x[0]["snapshot"].update(sourceKind="official-result"),
            lambda x:x[0].update(signature="0"*64),
        ):
            item=copy.deepcopy(original)
            mut(item)
            with self.assertRaises(WatchReceiptError):
                verify_rebound_watch_receipts(item,SECRET,DAY)
        with self.assertRaises(WatchReceiptError):
            verify_rebound_watch_receipts(original,SECRET,"20990413")
        with self.assertRaises(WatchReceiptError):
            verify_rebound_watch_receipts(original+original,SECRET,DAY)
        with self.assertRaises(WatchReceiptError):
            verify_rebound_watch_receipts(original,"wrong owner password"*3,DAY)

    def test_malformed_research_never_signed(self):
        history,programme,now=sample()
        for change in (
            lambda h,p:h["reboundContextReview"].update(officialJraVerified=True),
            lambda h,p:h["reboundContextReview"]["races"][0]["watch"].append(
                {"number":9,"reviewState":"cross_source_review"}),
            lambda h,p:h["reboundContextReview"]["races"][0]["watch"][0].update(
                reviewState="winner"),
            lambda h,p:p[1].update(track="東京"),
            lambda h,p:h.update(date="20990413"),
        ):
            with self.subTest(change=change):
                h,p=copy.deepcopy((history,programme))
                change(h,p)
                with self.assertRaises(WatchReceiptError):
                    issue_rebound_watch_receipts(h,p,SECRET,DAY,now)

    def test_without_server_official_feed_all_wins_are_pending(self):
        h,p,now=sample()
        report=issue_rebound_watch_receipts(h,p,SECRET,DAY,now)
        watches=verify_rebound_watch_receipts(report["receipts"],SECRET,DAY)
        pending=compare_watched_winners(watches,[])
        self.assertEqual(pending["reviewedRaces"],0)
        self.assertEqual(pending["pendingRaces"],2)
        self.assertEqual(pending["winnersInWatch"],0)
        self.assertFalse(pending["outcomeCalibrationReady"])
        # Deliberately unverified/ambiguous results must never be losses.
        self.assertEqual(compare_watched_winners(watches,[{
            "date":DAY,"track":"東京","race":1,"winner":4,
            "officialVerified":False
        }])["pendingRaces"],2)

    def test_future_trusted_adaptor_can_assess_watch_presence_not_retroactively(self):
        h,p,now=sample()
        snaps=verify_rebound_watch_receipts(
            issue_rebound_watch_receipts(h,p,SECRET,DAY,now)["receipts"],SECRET,DAY)
        official=[
           {"date":DAY,"track":"東京","race":1,"winner":4,
            "sourceKind":"independent-official-result",
            "officialVerified":True,"deadHeat":False,
            "refundRequired":False,"raceAbandoned":False},
           {"date":DAY,"track":"京都","race":2,"winner":5,
            "sourceKind":"independent-official-result",
            "officialVerified":True,"deadHeat":False,
            "refundRequired":False,"raceAbandoned":False}
        ]
        out=compare_watched_winners(snaps,official)
        self.assertEqual(out["reviewedRaces"],2)
        self.assertEqual(out["winnersInWatch"],1)
        self.assertEqual(out["winnersInCrossSource"],1)
        self.assertFalse(out["outcomeCalibrationReady"])
        official[0]["deadHeat"]=True
        out=compare_watched_winners(snaps,official)
        self.assertEqual(out["pendingRaces"],1)


if __name__=="__main__":
    unittest.main()
