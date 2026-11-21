"""Owner-only buy-vs-hold audit; user-entered outcomes never claim JRA authority."""
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_decision_audit_ui import HTML, CSS, JS
from owner_backup import HTML as GLOBAL_BACKUP_HTML
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

    def test_global_legacy_backup_discloses_new_decision_capture_scope(self):
        self.assertIn('href="/owner-decision-audit"', GLOBAL_BACKUP_HTML)
        self.assertIn('この16種類の一括バックアップには', GLOBAL_BACKUP_HTML)
        self.assertIn('含まれません', GLOBAL_BACKUP_HTML)
        self.assertIn('専用の検証画面から別ファイル', GLOBAL_BACKUP_HTML)

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
        self.assertIn("/api/jra/result-candidate?", JS)
        self.assertIn("jraAuditFetch", HTML)
        self.assertIn("同着", HTML)
        self.assertIn("公式", HTML)
        self.assertIn("stored(day)", JS)
        self.assertIn("auditBackupDownload", HTML)
        self.assertIn("auditBackupFile", HTML)
        self.assertIn("auditBackupRestore", HTML)
        self.assertIn("RESULT_PREFIX", JS)
        self.assertIn("mergeSignedCaptures", JS)
        self.assertIn("auditBackupStatus", JS)
        self.assertIn("localStorage.setItem(RESULT_PREFIX+report.date", JS)
        self.assertNotIn("method:'POST',credentials:'include'", JS)
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
const {parseLine,auditForecast,capturedToSource,candidateToInputLine,appendCandidateRow,reviewLines,mergeResults,mergeSignedCaptures,portableBackup,ensureReviewFitsCaptures,preferredAuditDate}=module.exports;
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

const candidate={
 version:'owner-jra-public-result-probe-1',date:'2026-11-21',
 track:'京都',race:3,sourceHostAllowlisted:true,
 visibleRaceIdentityMatched:true,payoutLayoutParsed:true,
 podiumChecked:true,payoutMatchesDisplayedPodium:true,
 officialJraVerified:false,sourceAuthenticityAttested:false,
 finalityVerified:false,refundsVerified:false,settlementReady:false,
 officialRoiPercent:null,actualPurchase:false,researchOnly:true,
 sourceReadCount:1,changesExistingReceipts:false,changesExistingRoi:false,
 podiumShape:'single_third_place',matchingTrifectaCount:1,matchingTrioCount:1,
 trifectaCandidates:[{ticket:[13,15,4],payoutYen:701850}],
 trioCandidates:[{ticket:[4,13,15],payoutYen:15000}]
};
const c=candidateToInputLine(candidate,'2026-11-21','京都',3);
assert.equal(c.line,'京都3 13-15-4 701850');
const added=appendCandidateRow('福島7 7-3-1 42510',c.line);
assert.equal(added.split('\n').length,2);
assert.throws(()=>appendCandidateRow(added,c.line),/入力済み/);
assert.throws(()=>appendCandidateRow('broken',c.line),/書式/);
assert.deepEqual([...parseLine(c.line).finish],[13,15,4]);
// A dead heat can yield two distinct trifecta payouts. Never choose one
// or silently drop the second winner in a single-result input field.
const tie={...candidate,podiumShape:'third_place_dead_heat',
 matchingTrifectaCount:2,matchingTrioCount:2,
 trifectaCandidates:[{ticket:[13,15,4],payoutYen:701850},
                      {ticket:[13,15,2],payoutYen:905000}],
 trioCandidates:[{ticket:[4,13,15],payoutYen:15000},
                 {ticket:[2,13,15],payoutYen:10000}]};
assert.equal(candidateToInputLine(tie,'2026-11-21','京都',3).line,null);
for(const changed of [
 {...candidate,officialJraVerified:true},
 {...candidate,finalityVerified:true},
 {...candidate,refundsVerified:true},
 {...candidate,sourceReadCount:0},
 {...candidate,payoutMatchesDisplayedPodium:false},
 {...candidate,date:'2026-11-20'},
 {...candidate,trifectaCandidates:[{ticket:[13,13,4],payoutYen:701850}]},
 {...candidate,trifectaCandidates:[{ticket:[13,15,4],payoutYen:0}]},
 ]){
 assert.throws(()=>candidateToInputLine(changed,'2026-11-21','京都',3),/./);
}
assert.throws(()=>candidateToInputLine(candidate,'2026-11-21','福島',3),/./);
assert.equal(candidateToInputLine(
 {...candidate,trifectaCandidates:[{ticket:[13,15,4],payoutYen:100000000}]},
 '2026-11-21','京都',3).line,null);


const day='2026-11-21';
const old={
  snapshot:{date:day,track:'福島',race:7},
  signature:'a'.repeat(64)
}, next={
  snapshot:{date:day,track:'京都',race:4},
  signature:'b'.repeat(64)
};
const oldClone=JSON.parse(JSON.stringify(old));
const mergedCaptures=mergeSignedCaptures([old],[old,next],day);
assert.equal(mergedCaptures.length,2);
assert.equal(mergedCaptures[0],old,'first sealed race stays first');
assert.equal(mergedCaptures[1],next);
assert.deepEqual(JSON.parse(JSON.stringify(old)),oldClone,
  'a backup must never mutate the first capture');
for(const bad of [
 {...old,signature:'c'.repeat(64)},
 {...old,snapshot:{...old.snapshot,date:'2026-11-20'}},
 {...old,signature:'INVALID'},
]){
 assert.throws(()=>mergeSignedCaptures([old],[bad],day),/./);
}
assert.throws(()=>mergeSignedCaptures([old,old],[],day),/./);
assert.throws(()=>mergeSignedCaptures([old],[], '2026-11-20'),/./);
const userResults=mergeResults('福島7 7-3-1 42510',
  '福島7 7-3-1 42510\n京都4 6-9-2 1910');
assert.equal(reviewLines(userResults).length,2);
assert.equal(mergeResults(userResults,'京都4 6-9-2 1910'),userResults);
assert.throws(()=>mergeResults('福島7 7-3-1 42510',
  '福島7 7-3-1 42511'),/上書き/);
assert.throws(()=>mergeResults('福島7 7-3-1 42510',
  '福島7 7-3-2 42510'),/上書き/);
assert.throws(()=>reviewLines('福島7 7-3-1\n福島7 7-3-2'),/重複/);
assert.throws(()=>reviewLines('invalid result'),/書式/);
ensureReviewFitsCaptures('福島7 7-3-1 42510',mergedCaptures);
assert.throws(()=>ensureReviewFitsCaptures(
 '東京11 1-2-3 15000',mergedCaptures),/固定記録のない/);
const packed=portableBackup(day,mergedCaptures,userResults);
assert.equal(packed.schema,'arc-race-private-decision-review-export-v1');
assert.equal(packed.date,day);
assert.equal(packed.captures.length,2);
assert.equal(packed.lines,userResults);
assert.equal(packed.captures[0],old);
assert.throws(()=>portableBackup('2026-02-31',[old],''),/日付/);
assert.throws(()=>portableBackup(day,[],''),/保存対象/);
assert.throws(()=>portableBackup(day,mergedCaptures,'福島7 7-3-3'),/馬番/);
assert.throws(()=>portableBackup(day,mergedCaptures,
 '福島7 7-3-1 42510\n福島7 7-3-2 999'),/重複/);

const todayAudit='2026-11-21', tomorrow='2026-11-22', yesterday='2026-11-20';
assert.equal(preferredAuditDate(todayAudit,todayAudit,tomorrow,false,false),tomorrow,
 'tomorrow reference shown by default when there is no prior local evidence');
assert.equal(preferredAuditDate(todayAudit,todayAudit,tomorrow,false,true),todayAudit,
 'existing signed decisions or reviewed results must keep todays review');
assert.equal(preferredAuditDate(todayAudit,todayAudit,tomorrow,true,false),todayAudit,
 'explicitly selected date stays selected');
assert.equal(preferredAuditDate(todayAudit,yesterday,tomorrow,true,false),yesterday,
 'user can review an earlier date');
assert.equal(preferredAuditDate(todayAudit,todayAudit,'2026-11-23',false,false),todayAudit,
 'day after tomorrow cannot hijack audit selection');
assert.equal(preferredAuditDate(todayAudit,todayAudit,yesterday,false,false),todayAudit,
 'stale server forecast cannot hijack audit selection');
assert.equal(preferredAuditDate(todayAudit,todayAudit,day,false,false),todayAudit);
assert.equal(preferredAuditDate(todayAudit,todayAudit,'invalid',false,false),todayAudit);
console.log('owner buy-vs-hold pure audit synthetic cases PASS');
"""
        result = subprocess.run(["node", "-e", script], input=JS, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=5, check=False)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
