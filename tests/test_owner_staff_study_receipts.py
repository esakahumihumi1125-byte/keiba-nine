"""Synthetic-only multi-date signed staff study receipts and private verifier."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_staff_study_receipts import (
    issue_staff_study_receipt, verify_staff_study_receipts,
    StaffStudyReceiptError, VERSION
)
from test_owner_past_staff_batch import source, study
from test_private_service import SETTINGS, call
from private_service import create_app

SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]
NOW = datetime(2026, 11, 10, 11, 0, tzinfo=timezone(timedelta(hours=9)))


def sample(day="20261101"):
    p, entries, previous, _, selected, pairs = source()
    dky=Mock(side_effect=lambda k:copy.deepcopy(pairs[k][0]))
    dse=Mock(side_effect=lambda k:copy.deepcopy(pairs[k][1]))
    summary=study(p,entries,previous,dky,dse)
    return issue_staff_study_receipt(summary,SECRET,day,now=NOW)


class StaffStudyReceiptTests(unittest.TestCase):
    def test_valid_seal_does_not_contain_personnel_and_verifies_across_days(self):
        first=sample()
        again=sample("20261102")
        self.assertEqual(first["snapshot"]["version"],VERSION)
        self.assertEqual(first["snapshot"]["sourceKind"],
                         "private-server-three-race-aggregate-unverified")
        self.assertFalse(first["snapshot"]["formalTenPointReady"])
        self.assertFalse(first["snapshot"]["independentHistoricRaceDedupVerified"])
        self.assertFalse(first["snapshot"]["officialJraVerified"])
        self.assertEqual(first["snapshot"]["summary"]["providerReadCount"],6)
        self.assertNotIn("note",first["snapshot"]["summary"])
        self.assertEqual(first["snapshot"]["summary"]["pairsSeenInTwoOrMoreRaces"],2)
        self.assertEqual(len(verify_staff_study_receipts(
            [first,again],SECRET)),2)
        self.assertEqual(len(verify_staff_study_receipts(
            [first],SECRET,"20261101")),1)
        for field in ("70298","10485","horseRef","racekey","horse_id",
                      "LICENSED_NAME","SECRET_ODDS","privateSelected"):
            self.assertNotIn(field,repr([first,again]))
        # The same historic sample can be re-run under two study dates:
        # cryptographically valid does NOT imply independent historic races.
        self.assertEqual(first["snapshot"]["summary"],
                         again["snapshot"]["summary"])
        self.assertFalse(first["snapshot"]["independentHistoricRaceDedupVerified"])

    def test_changes_to_signed_counts_and_claims_never_verify(self):
        orig=sample()
        mutations=(
            lambda x:x["snapshot"]["summary"].update(providerReadCount=7),
            lambda x:x["snapshot"]["summary"].update(
                formalTenPointScore=10),
            lambda x:x["snapshot"]["summary"].update(
                formalTenPointGrade="S"),
            lambda x:x["snapshot"].update(
                independentHistoricRaceDedupVerified=True),
            lambda x:x["snapshot"].update(officialJraVerified=True),
            lambda x:x["snapshot"].update(actualPurchase=True),
            lambda x:x["snapshot"].update(date="20261102"),
            lambda x:x["snapshot"].update(sourceKind="official"),
            lambda x:x.update(signature="0"*64),
        )
        for mutation in mutations:
            candidate=copy.deepcopy(orig);mutation(candidate)
            with self.subTest(mutation=repr(mutation)), self.assertRaises(
                    StaffStudyReceiptError):
                verify_staff_study_receipts([candidate],SECRET)
        for bad in ([orig,orig], {"receipt":orig}, [orig]*121):
            with self.assertRaises(StaffStudyReceiptError):
                verify_staff_study_receipts(bad,SECRET)

    def test_signer_rejects_forged_source_or_no_prior_reads(self):
        p,entries,previous,_,selected,pairs=source()
        summary=study(p,entries,previous,
                      lambda k:copy.deepcopy(pairs[k][0]),
                      lambda k:copy.deepcopy(pairs[k][1]))
        for change in (
            lambda x:x.update(formalTenPointScore=10),
            lambda x:x.update(independentJraVerified=True),
            lambda x:x.update(providerReadCount=7),
            lambda x:x.update(selectedPastRaceCount=0),
            lambda x:x.update(secretStaff="abc"),
            lambda x:x.update(pairsSeenInTwoOrMoreRaces=99),
        ):
            modified=copy.deepcopy(summary);change(modified)
            with self.subTest(change=repr(change)), self.assertRaises(
                    StaffStudyReceiptError):
                issue_staff_study_receipt(modified,SECRET,"20261101",now=NOW)

    def test_private_readonly_verify_does_not_query_paid_provider(self):
        first=sample()
        private=create_app({
            **SETTINGS,"KEIBA_RENDER_PRIVATE_ONLY":"1",
            "KEIBA_RENDER_PREVIEW_ONLY":"0",
        })
        with patch("private_service.fetch_historical_runner_staff") as paid1, \
             patch("private_service.fetch_historical_finished_runners") as paid2:
            ok=call(private,"/api/owner-staff-study-verify",method="POST",
                    data={"receipts":[first]})
            paid1.assert_not_called()
            paid2.assert_not_called()
        self.assertEqual(ok["status"],"200 OK")
        body=json.loads(ok["body"])
        self.assertEqual(body["version"],"owner-staff-study-verify-1")
        self.assertEqual(body["verifiedDateCount"],1)
        self.assertEqual(body["sourceProviderReadCount"],0)
        self.assertFalse(body["formalTenPointReady"])
        self.assertFalse(body["independentHistoricRaceDedupVerified"])
        self.assertNotIn("summary",body)
        self.assertEqual(call(private,"/api/owner-staff-study-verify",
                              method="POST",auth="",
                              data={"receipts":[first]})["status"],
                         "401 Unauthorized")
        self.assertEqual(call(create_app(SETTINGS),
                    "/api/owner-staff-study-verify",method="POST",
                    data={"receipts":[first]})["status"],"404 Not Found")
        for invalid in (
            {"date":"20261101","receipts":[first]},
            {"receipts":[{**first,"signature":"0"*64}]},
            {"receipts":[first,first]},
        ):
            self.assertEqual(call(private,"/api/owner-staff-study-verify",
                          method="POST",data=invalid)["status"],"400 Bad Request")


if __name__ == "__main__":
    unittest.main()
