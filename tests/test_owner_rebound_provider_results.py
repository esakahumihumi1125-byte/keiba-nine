"""No posthoc claims of verified wins from JRDB /tse alone."""
import copy
import sys
import unittest
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_rebound_receipts import issue_rebound_watch_receipts,verify_rebound_watch_receipts,WatchReceiptError
from owner_rebound_provider_results import summarize_provider_watch_results
from test_owner_rebound_receipts import sample,DAY,SECRET
from unittest.mock import patch
from private_service import create_app
from test_private_service import call,SETTINGS


def signed_watches():
    h,p,t=sample()
    return verify_rebound_watch_receipts(
        issue_rebound_watch_receipts(h,p,SECRET,DAY,t)["receipts"],SECRET,DAY)

def row(track="05",race="01",horse="04",finish="1"):
    return {"racedate":DAY,"racekey":track+"99ab"+race,
            "horse_number":horse,"order_of_finish":finish}


class TestPrivateReboundProviderCheck(unittest.TestCase):
    def test_private_endpoint_reads_tse_once_and_never_accepts_claimed_result(self):
        history,programme,now=sample()
        receipts=issue_rebound_watch_receipts(
            history,programme,SETTINGS["KEIBA_OWNER_PASSWORD"],DAY,now)["receipts"]
        settings={**SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
                  "KEIBA_RENDER_PREVIEW_ONLY":"0","JRDB_PRIVATE_ENABLED":"1",
                  "JRDB_API_KEY":"fake-fixture-only","JRDB_AUTH_KEY":"fake-fixture-only"}
        app=create_app(settings)
        observations=[
            row(horse="04",finish="1"),row(horse="05",finish="2"),
            row(horse="09",finish="3"),
            row(track="08",race="02",horse="05",finish="1"),
            row(track="08",race="02",horse="06",finish="2"),
            row(track="08",race="02",horse="07",finish="3")
        ]
        with patch("private_service.fetch_finished_race_results",
                   return_value=observations) as fetch:
            with patch("private_service._now_in_jst",
                       return_value="2099-04-12T12:00:00+09:00"):
                r=call(app,"/api/owner-rebound-provider-check",
                       method="POST",data={"date":DAY,"receipts":receipts})
            fetch.assert_called_once_with(DAY)
        self.assertEqual(r["status"],"200 OK")
        import json
        out=json.loads(r["body"])
        self.assertEqual(out["observedRaceCount"],2)
        self.assertEqual(out["verifiedRaceCount"],0)
        self.assertFalse(out["officialJraVerified"])
        self.assertFalse(out["officialFeedConnected"])
        self.assertIsNone(out["roiPercent"])
        self.assertNotIn("horse_id",r["body"].decode())
        self.assertNotIn("racekey",r["body"].decode())
        self.assertEqual(call(app,"/api/owner-rebound-provider-check",
                              method="POST",auth="",
                              data={"date":DAY,"receipts":receipts}
                             )["status"],"401 Unauthorized")
        with patch("private_service.fetch_finished_race_results") as fetch:
            attempts=[
                {"date":DAY,"receipts":receipts,"results":[{"officialVerified":True}]},
                {"date":DAY,"receipts":receipts,"winner":4},
                {"date":DAY,"receipts":[]},
            ]
            for data in attempts:
                self.assertEqual(call(app,"/api/owner-rebound-provider-check",
                                 method="POST",data=data)["status"],
                                 "400 Bad Request")
            fetch.assert_not_called()
        app_without_provider=create_app({**settings,
                                         "JRDB_PRIVATE_ENABLED":"0"})
        self.assertEqual(call(app_without_provider,
                         "/api/owner-rebound-provider-check",
                         method="POST",data={"date":DAY,"receipts":receipts}
                         )["status"],"503 Service Unavailable")
        app_public=create_app(SETTINGS)
        self.assertEqual(call(app_public,"/api/owner-rebound-provider-check",
                         method="POST",data={"date":DAY,"receipts":receipts}
                         )["status"],"404 Not Found")

    def test_no_tse_fetch_before_any_sealed_race_has_started(self):
        history,programme,now=sample()
        receipts=issue_rebound_watch_receipts(
            history,programme,SETTINGS["KEIBA_OWNER_PASSWORD"],DAY,now)["receipts"]
        app=create_app({**SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
                        "KEIBA_RENDER_PREVIEW_ONLY":"0",
                        "JRDB_PRIVATE_ENABLED":"1",
                        "JRDB_API_KEY":"synthetic","JRDB_AUTH_KEY":"synthetic"})
        with patch("private_service.fetch_finished_race_results") as fetch:
            with patch("private_service._now_in_jst",
                       return_value="2099-04-12T09:40:00+09:00"):
                r=call(app,"/api/owner-rebound-provider-check",
                       method="POST",data={"date":DAY,"receipts":receipts})
            fetch.assert_not_called()
        self.assertEqual(r["status"],"200 OK")
        import json
        report=json.loads(r["body"])
        self.assertEqual(report["observedRaceCount"],0)
        self.assertFalse(report["officialJraVerified"])

    def test_observed_first_in_watch_is_not_official_hit(self):
        snaps=signed_watches()
        initial=copy.deepcopy(snaps)
        results=[row(horse="04",finish="01"),row(horse="05",finish="02"),
                 row(horse="09",finish="03"),row(track="08",race="02",
                                             horse="05",finish="1")]
        out=summarize_provider_watch_results(
            snaps,results,DAY,datetime(2099,4,12,3,0,tzinfo=timezone.utc))
        self.assertEqual(out["raceCount"],2)
        self.assertEqual(out["observedRaceCount"],2)
        self.assertEqual(out["observedFirstInWatchCount"],1)
        self.assertEqual(out["observedFirstInPriorityCount"],1)
        self.assertFalse(out["officialJraVerified"])
        self.assertEqual(out["verifiedRaceCount"],0)
        self.assertIsNone(out["verifiedWatchHitCount"])
        self.assertIsNone(out["roiPercent"])
        self.assertTrue(out["sourceIncompleteCouldChange"])
        self.assertEqual(initial,snaps)
        for protected in ("racekey","horse_id","horse_name",
                          "API_KEY","confirmed_win_odds","resultkey"):
            self.assertNotIn(protected,repr(out))

    def test_missing_partial_ambiguous_and_prestart_remain_pending(self):
        snaps=signed_watches()
        now=datetime(2099,4,12,0,45,tzinfo=timezone.utc)
        out=summarize_provider_watch_results(
            snaps,[row()],DAY,now)
        self.assertIsNone(out["races"][0]["observedFirstNumber"])
        self.assertEqual(out["observedRaceCount"],0)
        later=datetime(2099,4,12,3,0,tzinfo=timezone.utc)
        for rows in (
            [],
            [row(finish=None)],
            [row(horse="04",finish="1"),row(horse="05",finish="1")],
            [row(horse="04",finish="1"),row(horse="04",finish="1")],
            [row(horse="04",finish="1"),row(horse="05",finish="z")],
            [row(horse="04",finish="1"),row(horse="05",finish="2"),
             row(horse="09",finish="3"),
             row(horse="05",finish="1",track="05",race="02")],
            # unrelated race must not fabricate matching watch
        ):
            with self.subTest(rows=rows):
                out=summarize_provider_watch_results(snaps,rows,DAY,later)
                # unrelated row doesn't change 東京1R first-place observation
                if len(rows)==4 and rows[0].get("order_of_finish")=="1":
                    self.assertEqual(out["observedRaceCount"],1)
                else:
                    self.assertEqual(out["observedRaceCount"],0)

    def test_identity_and_fabricated_result_fail_closed(self):
        snaps=signed_watches()
        later=datetime(2099,4,12,3,0,tzinfo=timezone.utc)
        for bad in (
            {"racedate":DAY,"racekey":"05BADbad","horse_number":"01","order_of_finish":"1"},
            row(horse="19"),row(horse="1"),
            {**row(),"racedate":"20990413"},
            {**row(),"racekey":"05000013"},
            {**row(),"order_of_finish":1},
            {**row(),"racekey":"050000xx"},
        ):
            with self.subTest(bad=bad),self.assertRaises(WatchReceiptError):
                summarize_provider_watch_results(snaps,[bad],DAY,later)
        # A single result row, or an incomplete podium, must stay pending.
        partial=summarize_provider_watch_results(
            snaps,[row(horse="04",finish="1"),
                   row(horse="05",finish="2")],DAY,later)
        self.assertEqual(partial["observedRaceCount"],0)
        # A different-year race key cannot silently be joined to today's
        # watch merely because it shares venue and race number.
        with self.assertRaises(WatchReceiptError):
            summarize_provider_watch_results(snaps,[{
                **row(),"racekey":"05260101"}],DAY,later)
        r=row()
        r["trouble_classification"]="1"
        out=summarize_provider_watch_results(snaps,[r],DAY,later)
        self.assertEqual(out["observedRaceCount"],0)
        with self.assertRaises(WatchReceiptError):
            summarize_provider_watch_results(snaps,[], "20990413",later)


if __name__=="__main__":
    unittest.main()
