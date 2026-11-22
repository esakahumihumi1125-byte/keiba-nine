"""Free authenticated storage-proof checks for tomorrow's JRDB research receipts."""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import SETTINGS, call
from owner_auto_forecast_ui import HTML, JS


class OwnerPrestartStorageStatusTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1"})
        self.url = "/api/owner-prestart-storage-status"
        self.query = {"QUERY_STRING": "date=2026-11-23"}

    def test_no_archive_does_not_claim_saved_or_call_paid_provider(self):
        with (
            patch("private_service.fetch_race_program") as programme,
            patch("private_service.fetch_horse_entries") as entries,
            patch("private_service.fetch_training_analysis") as training,
            patch("private_service.fetch_recent_runs") as recent,
            patch("private_service.read_archived_day") as read,
        ):
            response = call(self.app, self.url, **self.query)
            result = json.loads(response["body"])
            self.assertEqual(response["status"], "200 OK")
            self.assertEqual(result, {
                "version": "owner-prestart-storage-status-1",
                "date": "2026-11-23", "archiveEnabled": False,
                "persistentStorageReady": False,
                "serverSavedRaceCount": 0,
                "verifiedServerSignedRaceCount": 0,
                "providerRequests": 0, "officialJraVerified": False,
                "finalResultsConnected": False, "actualPurchase": False,
            })
            self.assertIn("no-store", response["headers"]["Cache-Control"])
            for fetch in (programme, entries, training, recent, read):
                fetch.assert_not_called()

    def test_enabled_archive_counts_only_earliest_verified_receipts(self):
        signed = [{"snapshot": {"track": "東京", "race": 1},
                   "signature": "synthetic_signature_not_returned"}]
        with (
            patch("private_service.archive_enabled", return_value=True),
            patch("private_service.archive_signing_secret",
                  return_value="synthetic-archive-secret"),
            patch("private_service.read_archived_day", return_value=signed) as read,
            patch("private_service.verify_preview_receipts",
                  return_value=[{"date": "2026-11-23"}]) as verify,
        ):
            response = call(self.app, self.url, **self.query)
            payload = json.loads(response["body"])
            self.assertEqual(response["status"], "200 OK")
            self.assertTrue(payload["persistentStorageReady"])
            self.assertTrue(payload["archiveEnabled"])
            self.assertEqual(payload["serverSavedRaceCount"], 1)
            self.assertEqual(payload["verifiedServerSignedRaceCount"], 1)
            self.assertEqual(payload["providerRequests"], 0)
            read.assert_called_once()
            self.assertEqual(read.call_args.args[1:],
                             ("synthetic-archive-secret", "2026-11-23"))
            verify.assert_called_once_with(
                signed, "synthetic-archive-secret", "2026-11-23")
            raw = response["body"].decode()
            for forbidden in ("synthetic_signature_not_returned",
                              "synthetic-archive-secret", "trifectaTickets",
                              SETTINGS["KEIBA_OWNER_PASSWORD"]):
                self.assertNotIn(forbidden, raw)

    def test_mismatch_fails_closed_not_zero(self):
        with (
            patch("private_service.archive_enabled", return_value=True),
            patch("private_service.archive_signing_secret",
                  return_value="synthetic-archive-secret"),
            patch("private_service.read_archived_day",
                  return_value=[{"snapshot": {}, "signature": "dummy"}]),
            patch("private_service.verify_preview_receipts",
                  return_value=[]),
        ):
            response = call(self.app, self.url, **self.query)
            self.assertEqual(response["status"], "503 Service Unavailable")
            self.assertNotIn(b'"serverSavedRaceCount":0', response["body"])

    def test_private_date_header_method_and_preview_gate(self):
        self.assertEqual(call(self.app, self.url, auth="", **self.query)["status"],
                         "401 Unauthorized")
        self.assertEqual(call(self.app, self.url,
                              HTTP_X_KEIBA_REQUEST="", **self.query)["status"],
                         "403 Forbidden")
        self.assertEqual(call(self.app, self.url, method="POST", **self.query)["status"],
                         "404 Not Found")
        for query in ("", "date=2026-02-30", "date=2026-11-23&x=1",
                      "date=2026-11-23&date=2026-11-24"):
            with self.subTest(query=query):
                self.assertEqual(call(self.app, self.url,
                                      QUERY_STRING=query)["status"],
                                 "400 Bad Request")
        preview = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                              "KEIBA_RENDER_PREVIEW_ONLY": "1"})
        self.assertEqual(call(preview, self.url, **self.query)["status"],
                         "404 Not Found")

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_browser_pulse_rejects_stale_and_false_saved_status(self):
        self.assertIn('id="autoStoragePulse"', HTML)
        self.assertIn("/api/owner-prestart-storage-status?date=", JS)
        self.assertIn("serverSavedRaceCount", JS)
        self.assertIn("既存", JS)
        js = r"""
const vm=require('node:vm'),assert=require('node:assert/strict');
const s=require('node:fs').readFileSync(0,'utf8');
const marker=";(()=>{'use strict';\nconst dayInput=document.getElementById('autoDay');";
const k=s.lastIndexOf(marker);assert(k>=0,'status script');
const code=s.slice(k);
const day={value:'2026-11-23',onchange:()=>{}};
const output={textContent:''};
let generateCalls=0;
const run={onclick:async()=>{generateCalls++;}};
let responses=[], fetchCalls=[];
const fetch=(url,options)=>{
 fetchCalls.push({url,options});
 return new Promise(resolve=>responses.push(resolve));
};
vm.runInNewContext(code,{
 document:{getElementById:id=>({
  autoDay:day,autoStoragePulse:output,autoRun:run
 })[id]},
 fetch,Date,Number,Array,Object,Set,Error,encodeURIComponent
},{timeout:500});
const validBody=(n,enabled)=>({
 version:'owner-prestart-storage-status-1',date:'2026-11-23',
 archiveEnabled:enabled,persistentStorageReady:enabled,
 serverSavedRaceCount:n,verifiedServerSignedRaceCount:n,
 providerRequests:0,officialJraVerified:false,
 finalResultsConnected:false,actualPurchase:false
});
const done=async()=>{for(let i=0;i<6;i++)await Promise.resolve();};
(async()=>{
 assert.equal(fetchCalls.length,1);
 assert.equal(fetchCalls[0].options.credentials,'same-origin');
 assert.equal(fetchCalls[0].options.cache,'no-store');
 responses.shift()({ok:true,json:async()=>validBody(0,false)});
 await done();
 assert.match(output.textContent,/永続保存は未設定/);
 const rerun=run.onclick();
 assert.equal(generateCalls,1);
 await done();assert.equal(fetchCalls.length,2);
 responses.shift()({ok:true,json:async()=>validBody(2,true)});
 await rerun;
 assert.match(output.textContent,/研究用3連単 2R/);
 const before=day.onchange;
 const pending=run.onclick();
 await done();
 assert.equal(fetchCalls.length,3);
 const stale=responses.shift();
 day.value='2026-11-24';before();
 await done();
 assert.equal(fetchCalls.length,4);
 stale({ok:true,json:async()=>validBody(3,true)});
 await pending;await done();
 assert.doesNotMatch(output.textContent,/研究用3連単 3R/);
 responses.shift()({ok:true,json:async()=>validBody(3,true)});
 await done();
 assert.match(output.textContent,/安全に確認できません/);
 console.log('Owner prestart storage pulse: no paid call, verified count, stale guard PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
"""
        completed = subprocess.run(["node", "-e", js], input=JS,
                                   text=True, capture_output=True,
                                   check=False, timeout=12)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("stale guard PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
