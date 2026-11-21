"""Owner-only buy-vs-hold audit; user-entered outcomes never claim JRA authority."""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_decision_audit_ui import HTML, CSS, JS
from private_service import create_app
from test_private_service import SETTINGS, call


class OwnerDecisionAuditTests(unittest.TestCase):
    def test_private_owner_pages_and_assets_require_authentication(self):
        app = create_app({**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1"})
        for route, mime in [
            ("/owner-decision-audit", "text/html"),
            ("/owner-decision-audit.js", "text/javascript"),
            ("/owner-decision-audit.css", "text/css"),
        ]:
            with self.subTest(route=route):
                response = call(app, route)
                self.assertEqual(response["status"], "200 OK")
                self.assertIn(mime, response["headers"]["Content-Type"])
                self.assertIn("no-store", response["headers"]["Cache-Control"])
                anonymous = call(app, route, auth="")
                self.assertIn(anonymous["status"],
                              ("303 See Other", "401 Unauthorized"))
                self.assertNotIn("予想を読み込み中", anonymous["body"].decode("utf8"))
        preview = create_app({**SETTINGS, "KEIBA_RENDER_PREVIEW_ONLY": "1"})
        self.assertEqual(call(preview, "/owner-decision-audit")["status"],
                         "404 Not Found")
        self.assertIn('href="/owner-decision-audit"',
                      call(app, "/owner-preday-forecast")["body"].decode())
        self.assertIn('href="/owner-decision-audit"',
                      call(app, "/")["body"].decode())

    def test_no_provider_results_or_forecast_mutation(self):
        self.assertIn("/api/owner-preday-forecast", JS)
        self.assertIn("X-Keiba-Request", JS)
        self.assertIn("自己入力", HTML)
        self.assertIn("返還", HTML)
        self.assertIn("買い候補", HTML)
        self.assertIn("見送り", HTML)
        self.assertIn("localStorage", JS)
        self.assertIn("owner-decision-freeze", JS)
        self.assertIn("owner-decision-verify", JS)
        self.assertIn("stored(day)", JS)
        self.assertNotIn("sessionStorage", JS)
        self.assertNotIn("JRDB_API", JS)
        self.assertNotIn("GmailApp", JS)
        self.assertIn(".panel", CSS)

    @unittest.skipUnless(shutil.which("node"), "node unavailable")
    def test_offline_javascript_counts_buy_and_hold_and_rejects_bad_data(self):
        script = r"""
const vm=require('node:vm'),assert=require('node:assert/strict');
const source=require('node:fs').readFileSync(0,'utf8');
const module={exports:{}};
vm.runInNewContext(source,{module},{timeout:2000});
const {parseLine,auditForecast,capturedToSource}=module.exports;
assert.equal(parseLine('京都３Ｒ 13→15→4 701850').finish.join(','),'13,15,4');
const race=(track,race,status,a)=>({
  track,race,status,first:[a,a+1],second:[a,a+1,a+2],
  third:[a,a+1,a+2,a+3],points:8
});
const original={date:'2026-11-21',races:[
  race('京都',3,'買い候補',1),
  race('福島',7,'見送り',4),
  race('京都',5,'見送り',9)
]};
const before=JSON.stringify(original);
const result=auditForecast(original,
 '京都3 1-3-4 3500\n福島7 4-6-7 42510\n京都5 18-2-3');
assert.equal(result.buckets.buy.races,1);
assert.equal(result.buckets.buy.hits,1);
assert.equal(result.buckets.buy.stake,800);
assert.equal(result.buckets.hold.races,2);
assert.equal(result.buckets.hold.hits,1);
assert.equal(result.buckets.hold.knownReturn,42510);
assert.equal(result.items[2].reason,'1着候補漏れ');
assert.equal(result.unreviewed,0);
const sealed=capturedToSource({
  schema:'keiba-nine-owner-decision-receipt-v1',verified:true,
  officialScheduleVerified:false,officialResultsVerified:false,
  actualPurchase:false,date:'2026-11-21',
  captures:[{track:'福島',race:7,decision:'見送り',first:[4,5],
    second:[4,5,6],third:[4,5,6,7],points:8,
    sourceKind:'owner-private-prestart-reference'}]
});
assert.equal(sealed.races[0].status,'見送り');
assert.equal(auditForecast(sealed,'福島7 4-6-7').buckets.hold.hits,1);
assert.throws(()=>capturedToSource({...sealed,verified:false}),/./);
assert.equal(JSON.stringify(original),before,'never modify the source forecast');
assert.equal(result.anyUnknownPayoff,false);
assert.equal(auditForecast(original,'福島7 4-6-7').anyUnknownPayoff,true);
assert.equal(auditForecast(original,'京都3 18-3-4').buckets.buy.hits,0);
for(const bad of [
 '京都3 1-1-2', '京都3 19-2-3', '東京8 1-2-3',
 '京都3 1-3-4\n京都3 2-3-4',
 '京都3 1-3-4 999999999', 'bad input']){
  assert.throws(()=>auditForecast(original,bad),/./,bad);
}
console.log('owner buy-vs-hold pure audit synthetic cases PASS');
"""
        result = subprocess.run(["node", "-e", script], input=JS, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=5, check=False)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
