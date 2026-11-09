"""Research-6 signed pick capture: synthetic clocks, no paid /tra reads."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_research6_draft_receipts import (
    issue_research6_draft_receipts, verify_research6_draft_receipts,
    DraftReceiptError, VERSION,
)
from test_owner_research6_five_drafts import (
    DAY, JST, materials, calculate,
)
from jrdb_program_preview import normalize_program_rows
from private_service import create_app
from test_private_service import SETTINGS, call

SECRET=SETTINGS["KEIBA_OWNER_PASSWORD"]
NOW=datetime(2099,1,1,9,0,tzinfo=JST)


def setup():
    raw, study = materials()
    programme = normalize_program_rows(raw, DAY)
    report = calculate(programme, study, now=NOW)
    return programme, {
        "date": DAY, "predictionReady": False,
        "newWeightFiveResearch": study,
        "research6FiveDrafts": report,
    }


class Draft79CaptureTests(unittest.TestCase):
    def test_normalized_race_40_tickets_first_write_fingerprint(self):
        programme, hist = setup()
        before = copy.deepcopy((programme, hist))
        report = issue_research6_draft_receipts(hist, programme, SECRET, DAY, now=NOW)
        self.assertEqual((programme, hist), before)
        self.assertEqual(report["receiptCount"],1)
        self.assertEqual(report["version"],VERSION)
        self.assertTrue(report["serverSigned"])
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["bettingReady"])
        self.assertFalse(report["actualPurchase"])
        self.assertFalse(report["changesExistingReceipts"])
        receipt = report["receipts"][0]
        snap = verify_research6_draft_receipts([receipt],SECRET,DAY)[0]
        self.assertEqual((snap["points"], snap["amountYen"]), (40,4000))
        self.assertEqual((snap["first"],snap["second"],snap["third"]),
                         ([1,2],[1,2,3,4,5],[1,2,3,4,5,6,7]))
        self.assertEqual(snap["sourceKind"],"prestart-unverified-research6-79-draft")
        self.assertEqual(snap["policyVersion"],"research-6")
        self.assertEqual(snap["researchWeight"],79)
        self.assertEqual(snap["remainingUnassessedWeight"],21)
        self.assertEqual(len(snap["tickets"]),len({tuple(x) for x in snap["tickets"]}))
        for forbidden in ("racekey","horse_id","sire_name","JRA_API_KEY",
                          "password","realPurchase","payout"):
            self.assertNotIn(forbidden,repr(report))

    def test_old_source_cannot_be_edited_and_signed_again(self):
        p, h = setup()
        tampered=copy.deepcopy(h)
        tampered["research6FiveDrafts"]["races"][0]["tickets"][0]=[7,6,5]
        with self.assertRaises(DraftReceiptError):
            issue_research6_draft_receipts(tampered,p,SECRET,DAY,now=NOW)
        tampered=copy.deepcopy(h)
        tampered["research6FiveDrafts"]["races"][0]["first"]=[7,2]
        with self.assertRaises(DraftReceiptError):
            issue_research6_draft_receipts(tampered,p,SECRET,DAY,now=NOW)
        tampered=copy.deepcopy(h)
        tampered["newWeightFiveResearch"]["factorWeights"]["pace"]=20
        with self.assertRaises(DraftReceiptError):
            issue_research6_draft_receipts(tampered,p,SECRET,DAY,now=NOW)

    def test_over_provisional_off_cannot_sign_but_old_signature_verifies(self):
        p, h = setup()
        fixed=issue_research6_draft_receipts(h,p,SECRET,DAY,now=NOW)["receipts"]
        after=NOW+timedelta(hours=4)
        late=issue_research6_draft_receipts(h,p,SECRET,DAY,now=after)
        self.assertEqual(late["receiptCount"],0)
        self.assertEqual(late["expiredBeforeSigning"],1)
        self.assertEqual(len(verify_research6_draft_receipts(fixed,SECRET,DAY)),1)

    def test_hold_never_signs_and_suspicious_future_clock_fails(self):
        p, h = setup()
        h["newWeightFiveResearch"]["races"][0]["horses"][0]["bands"]["training"]="未評価"
        with self.assertRaises(DraftReceiptError):
            issue_research6_draft_receipts(h,p,SECRET,DAY,now=NOW)
        p,h=setup()
        h["research6FiveDrafts"]["races"][0]["status"]="hold"
        with self.assertRaises(DraftReceiptError):
            issue_research6_draft_receipts(h,p,SECRET,DAY,now=NOW)

    def test_receipt_forgery_duplicate_and_wrong_day_fail_closed(self):
        p,h=setup()
        signed=issue_research6_draft_receipts(h,p,SECRET,DAY,now=NOW)["receipts"]
        mutations=(
            lambda x:x[0]["snapshot"]["tickets"][0].__setitem__(2,7),
            lambda x:x[0]["snapshot"]["amountYen"].__class__,
            lambda x:x[0]["snapshot"].update(amountYen=9999),
            lambda x:x[0]["snapshot"].update(officialJraVerified=True),
            lambda x:x[0]["snapshot"].update(predictionReady=True),
            lambda x:x[0]["snapshot"].update(capturedAt="2099-01-01T14:00:00+09:00"),
            lambda x:x[0]["snapshot"].update(sourceKind="prestart-locked"),
            lambda x:x[0].update(signature="0"*64),
        )
        for mutate in mutations:
            fixed=copy.deepcopy(signed);mutate(fixed)
            if fixed==signed: continue
            with self.subTest(mutation=repr(mutate)),self.assertRaises(DraftReceiptError):
                verify_research6_draft_receipts(fixed,SECRET,DAY)
        for candidate,credential,date in (
            (signed*2,SECRET,DAY),
            (signed,"not-the-key-12345678901234567890",DAY),
            (signed,SECRET,"20990102"),
        ):
            with self.assertRaises(DraftReceiptError):
                verify_research6_draft_receipts(candidate,credential,date)

    def test_authenticated_private_verify_route_is_read_only(self):
        p,h=setup()
        signed=issue_research6_draft_receipts(
            h,p,SECRET,DAY,now=NOW)["receipts"]
        app=create_app({**SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
                        "KEIBA_RENDER_PREVIEW_ONLY":"0"})
        with patch("private_service.fetch_historical_race_program") as paid:
            result=call(app,"/api/owner-research6-draft-verify",method="POST",
                        data={"date":DAY,"receipts":signed})
            paid.assert_not_called()
        self.assertEqual(result["status"],"200 OK")
        body=json.loads(result["body"])
        self.assertEqual(body["recordCount"],1)
        self.assertTrue(body["serverSigned"])
        self.assertFalse(body["officialJraVerified"])
        self.assertFalse(body["formalPredictionReady"])
        self.assertFalse(body["resultComparisonReady"])
        self.assertFalse(body["actualPurchase"])
        self.assertNotIn("tickets",repr(body))
        self.assertEqual(call(app,"/api/owner-research6-draft-verify",
                              auth="",method="POST",
                              data={"date":DAY,"receipts":signed})["status"],
                         "401 Unauthorized")
        self.assertEqual(call(create_app(SETTINGS),"/api/owner-research6-draft-verify",
                              method="POST",data={"date":DAY,"receipts":signed})["status"],
                         "404 Not Found")
        for bad in (
            {"date":DAY,"receipts":signed,"payout":10000},
            {"date":DAY,"receipts":[{**signed[0],"signature":"0"*64}]},
            {"date":"20990102","receipts":signed},
        ):
            self.assertEqual(call(app,"/api/owner-research6-draft-verify",
                         method="POST",data=bad)["status"],"400 Bad Request")


if __name__=="__main__":
    unittest.main()
