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


def signed_watches():
    h,p,t=sample()
    return verify_rebound_watch_receipts(
        issue_rebound_watch_receipts(h,p,SECRET,DAY,t)["receipts"],SECRET,DAY)

def row(track="05",race="01",horse="04",finish="1"):
    return {"racedate":DAY,"racekey":track+"99ab"+race,
            "horse_number":horse,"order_of_finish":finish}


class TestPrivateReboundProviderCheck(unittest.TestCase):
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
            [row(horse="04",finish="1"),row(horse="05",finish="1",
                 track="05",race="02")],  # unrelated race must not fabricate matching watch
        ):
            with self.subTest(rows=rows):
                out=summarize_provider_watch_results(snaps,rows,DAY,later)
                # unrelated row doesn't change 東京1R first-place observation
                if rows==[row(horse="04",finish="1"),row(horse="05",finish="1",
                              track="05",race="02")]:
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
        r=row()
        r["trouble_classification"]="1"
        out=summarize_provider_watch_results(snaps,[r],DAY,later)
        self.assertEqual(out["observedRaceCount"],0)
        with self.assertRaises(WatchReceiptError):
            summarize_provider_watch_results(snaps,[], "20990413",later)


if __name__=="__main__":
    unittest.main()
