"""Private-side JV-Link/JRDB one-race candidate comparison, synthetic only."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_jvlink_compare_ui import HTML, CSS, JS
from owner_preday_forecast_ui import HTML as PREDAY_HTML
from private_service import create_app
from test_private_service import SETTINGS, call


class OwnerJvlinkCompareTests(unittest.TestCase):
    def test_routes_authenticated_and_private_only(self):
        settings = {**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1"}
        app = create_app(settings)
        for path, mime in (
            ("/owner-jvlink-compare", "text/html"),
            ("/owner-jvlink-compare.js", "text/javascript"),
            ("/owner-jvlink-compare.css", "text/css"),
        ):
            with self.subTest(path=path):
                ready = call(app, path)
                self.assertEqual(ready["status"], "200 OK")
                self.assertIn(mime, ready["headers"]["Content-Type"])
                self.assertIn("no-store", ready["headers"]["Cache-Control"])
                unauth = call(app, path, auth="")
                self.assertIn(unauth["status"],
                              ("303 See Other", "401 Unauthorized"))
        preview = create_app({**settings, "KEIBA_RENDER_PREVIEW_ONLY": "1"})
        self.assertEqual(call(preview, "/owner-jvlink-compare")["status"],
                         "404 Not Found")
        self.assertIn('href="/owner-jvlink-compare"', PREDAY_HTML)
        self.assertIn("JRA-VAN", HTML)
        self.assertIn("vanJrdbProbe", HTML)
        self.assertIn("/api/jrdb/connection-test?date=", JS)
        self.assertIn("button.disabled=true", JS)
        self.assertIn("jvdata-candidate-YYYYMMDD.json", HTML)
        self.assertIn("JRDB", HTML)
        self.assertIn("JRA", HTML)
        self.assertIn("2資料", HTML)
        self.assertIn("input", CSS)
        self.assertNotIn("localStorage", JS)
        self.assertNotIn("sessionStorage", JS)
        self.assertNotIn("method:'POST'", JS)
        self.assertNotIn("API_KEY", JS)
        self.assertNotIn("rawJvData", JS)
        self.assertNotIn("fetch('/api/jra", JS)

    @unittest.skipUnless(shutil.which("node"), "Node is unavailable")
    def test_one_race_can_compare_only_candidates_without_formal_status(self):
        node = r"""
const vm=require('node:vm'),assert=require('node:assert/strict');
const source=require('node:fs').readFileSync(0,'utf8'),module={exports:{}};
vm.runInNewContext(source,{module},{timeout:2000});
const {compareLocalJvWithJrdb,compareWeeklyJvCandidate,normalizeJrdbProbeResult,sameRaceDay}=module.exports;
const date='2026-11-22',pcDate='20261122';
const jrdb={schema:'keiba-nine-private-preday-review-v1',date,
 sourceKind:'owner-private-authored-preday',predictionReady:false,
 officialJraVerified:false,purchased:false,races:[
  {track:'東京',race:1,time:'09:50',course:'ダ・左1300M',
   field:3,rank:[3,2,1],status:'買い候補'}]};
const file={version:'owner-jvdata-local-day-history-bridge-1',date:pcDate,
 raceCount:1,privateOwnerOnly:true,researchOnly:true,
 historySource:'private_jvlink_rcvn_partial_observations',
 historyCompletenessVerified:false,captureTimeIndependentlyVerified:false,
 officialStarterListVerified:false,officialScratchStateVerified:false,
 officialGoingVerified:false,formalTenFactorReady:false,
 productionPredictionReady:false,bettingReady:false,autoPurchase:false,
 newProviderRequests:0,races:[{
  track:'東京',race:1,postTimeCandidate:'09:50',
  distanceMetersCandidate:1300,surfaceCandidate:'ダート',
  byNumber:[1,2,3].map(number=>({
   number,observedRecordCount:number===2?0:1,
   missingHistoryUnproven:true,graded:false,recentObservedRuns:[]})),
  historyComplete:false,graded:false,bettingReady:false}]};
assert.equal(sameRaceDay('20261122','2026-11-22'),true);
assert.equal(sameRaceDay('20261121','2026-11-22'),false);
assert.equal(sameRaceDay('2026-11-22','2026-11-22'),false);
assert.equal(sameRaceDay('20261122','20261122'),false);
assert.equal(sameRaceDay('20260230','2026-02-30'),false);
assert.equal(sameRaceDay('20260228','2026-02-28'),true);
assert.equal(sameRaceDay('20240229','2024-02-29'),true);
assert.equal(sameRaceDay('20230229','2023-02-29'),false);
const result=compareLocalJvWithJrdb(file,jrdb);
assert.equal(result.candidateFieldsConsistent,true);
assert.equal(result.checkedRaceCount,1);
assert.equal(result.observedHorseHistories,2);
assert.equal(result.totalEditorialRaces,1);
for(const k of ['allHorseIdentityMatched','officialJraVerified',
 'currentGoingVerified','scratchesVerified','formalTenFactorsReady','bettingReady']){
 assert.equal(result[k],false,'must not upgrade '+k);
}
for(const edited of [
 {...file,date:'20261121'},
 {...file,date:'2026-11-22'},
 {...file,date:'2026112X'},
 {...file,privateOwnerOnly:false},
 {...file,officialStarterListVerified:true},
 {...file,races:[{...file.races[0],race:2}]},
 {...file,races:[{...file.races[0],byNumber:[...file.races[0].byNumber.slice(1),file.races[0].byNumber[1]]}]},
 {...file,races:[{...file.races[0],byNumber:file.races[0].byNumber.slice(0,2)}]},
 ]){
 if(edited.races[0].race===2||edited.races[0].byNumber.length===2){
   assert.throws(()=>compareLocalJvWithJrdb(edited,jrdb),/./);
 }else{
   assert.throws(()=>compareLocalJvWithJrdb(edited,jrdb),/./);
 }
}
const mismatch=compareLocalJvWithJrdb({
 ...file,races:[{...file.races[0],distanceMetersCandidate:1400}]},jrdb);
assert.equal(mismatch.candidateFieldsConsistent,false);
assert.equal(mismatch.formalTenFactorsReady,false);
assert.equal(JSON.stringify(file).includes('rawProviderRecord'),false);
const weeklyCard=(track,race,postTime,distance,surface,nums)=>({
 track,race,postTimeCandidate:postTime,distanceMetersCandidate:distance,
 surfaceCandidate:surface,
 registeredRunnerCount:nums.length,horseNumbersCandidate:nums,
 sourceRecordCategory:'numbered_racecard_not_final_changes',
 privateInputOnly:true,collectionTimeIndependentlyVerified:false,
 beforeScheduledOffAtLocalCapture:true,finalStarterListVerified:false,
 scratchStatusVerified:false,latestGoingVerified:false,
 officialFinalPostTimeVerified:false,formalTenFactorReady:false,
 bettingReady:false
});
const dayCard=weeklyCard('東京',1,'09:50',1300,'ダート',[1,2,3]);
const extraCard=weeklyCard('京都',2,'10:35',1200,'ダート',[1,2,3,4]);
const dailyReference={...jrdb,races:[...jrdb.races,
 {track:'京都',race:2,time:'10:35',course:'ダ・右1200M',
  field:4,rank:[1,4,2],status:'見送り'}]};
const weekly={version:'owner-jvlink-weekly-local-candidates-1',date:pcDate,
 source:'private_jvlink_weekly_ra_se_candidate',
 raceCount:2,races:[dayCard,extraCard],
 privateOwnerOnly:true,researchOnly:true,providerDataRawIncluded:false,
 collectionTimeIndependentlyVerified:false,
 capturedAtLocalJst:'2026-11-22T08:00:00+09:00',allCandidatesBeforeScheduledOff:true,
 allScheduledVenuesVerified:false,independentJraVerified:false,
 officialScratchesVerified:false,officialGoingVerified:false,
 officialFinalPostTimeVerified:false,productionPredictionReady:false,
 bettingReady:false,autoPurchase:false};
const report=compareWeeklyJvCandidate(weekly,dailyReference);
assert.equal(report.consistentCandidateRaceCount,2);
assert.equal(report.observedJvRaceCount,2);
assert.equal(report.missingJvRaces,0);
assert.equal(report.mismatchJvRaces,0);
assert.equal(report.referenceCardAndJvCandidateFieldsAllConsistent,true);
for(const field of ['allHorseIdentityMatched','officialStarterListVerified',
 'officialScratchesVerified','officialGoingVerified',
 'formalTenFactorReady','bettingReady']){
 assert.equal(report[field],false,'do not upgrade '+field);
}
const postOff=compareWeeklyJvCandidate({
 ...weekly,capturedAtLocalJst:'2026-11-22T09:50:00+09:00',
 allCandidatesBeforeScheduledOff:false,
 races:[{...dayCard,beforeScheduledOffAtLocalCapture:false},extraCard]
},dailyReference);
assert.equal(postOff.postOffJvRaces,1);
assert.equal(postOff.consistentCandidateRaceCount,1);
assert.equal(postOff.races[0].status,'post_off_local_capture');
assert.equal(postOff.referenceCardAndJvCandidateFieldsAllConsistent,false);
assert.equal(postOff.officialStarterListVerified,false);
assert.equal(report.postOffJvRaces,0);
const incomplete=compareWeeklyJvCandidate(
 {...weekly,raceCount:1,races:[dayCard]},dailyReference);
assert.equal(incomplete.consistentCandidateRaceCount,1);
assert.equal(incomplete.missingJvRaces,1);
assert.equal(incomplete.referenceCardAndJvCandidateFieldsAllConsistent,false);
const different=compareWeeklyJvCandidate(
 {...weekly,races:[dayCard,{...extraCard,postTimeCandidate:'11:35'}]},
 dailyReference);
assert.equal(different.mismatchJvRaces,1);
assert.equal(different.formalTenFactorReady,false);
const unknown=compareWeeklyJvCandidate(
 {...weekly,raceCount:3,races:[...weekly.races,weeklyCard(
 '新潟',1,'10:00',1200,'芝',[1,2,3])]},dailyReference);
assert.equal(unknown.unexpectedJvRaceCount,1);
assert.equal(unknown.referenceCardAndJvCandidateFieldsAllConsistent,false);
for(const malformed of [
 {...weekly,date:'20261121'},
 {...weekly,date:'2026-11-22'},
 {...weekly,date:'2026112X'},
 {...weekly,providerDataRawIncluded:true},
 {...weekly,officialGoingVerified:true},
 {...weekly,source:'some-other-source'},
 {...weekly,raceCount:3},
 {...weekly,capturedAtLocalJst:'2026-11-22T08:00:00'},
 {...weekly,capturedAtLocalJst:'2026-02-30T08:00:00+09:00'},
 {...weekly,capturedAtLocalJst:'2026-11-22T09:50:00+09:00'},
 {...weekly,allCandidatesBeforeScheduledOff:false},
 {...weekly,races:[{...dayCard,beforeScheduledOffAtLocalCapture:false},extraCard]},
 {...weekly,races:[dayCard,dayCard]},
 {...weekly,races:[dayCard,{...extraCard,horseNumbersCandidate:[1,1,2,3]}]},
 {...weekly,races:[dayCard,{...extraCard,finalStarterListVerified:true}]},
]){
 assert.throws(()=>compareWeeklyJvCandidate(malformed,dailyReference),/./);
}


const goodProbe={
 date:'20261122',connectionVerified:true,programmeCount:24,
 providerDataStored:false,predictionReady:false
};
const checked=normalizeJrdbProbeResult(200,goodProbe,'20261122');
assert.equal(checked.connected,true);
assert.match(checked.label,/接続は成功/);
assert.match(checked.label,/正式10項目予想/);
assert.equal(normalizeJrdbProbeResult(502,{
 error:'JRDB β版アカウントの利用権限・有効期限を確認してください。'
 },'20261122').connected,false);
assert.match(normalizeJrdbProbeResult(502,{
 error:'JRDBの通信回数制限です。再試行の間隔を空けてください。'
 },'20261122').label,/通信回数制限/);
assert.match(normalizeJrdbProbeResult(502,{
 error:'Do not echo secrets'
 },'20261122').label,/接続診断に失敗/);
assert.doesNotMatch(normalizeJrdbProbeResult(502,{
 error:'Do not echo secrets'
 },'20261122').label,/secrets/);
for(const bad of [
 {...goodProbe,date:'20261121'},
 {...goodProbe,connectionVerified:false},
 {...goodProbe,predictionReady:true},
 {...goodProbe,providerDataStored:true},
 {...goodProbe,programmeCount:-1},
 {...goodProbe,programmeCount:'24'},
]){
 assert.throws(()=>normalizeJrdbProbeResult(200,bad,'20261122'),/./);
}
assert.throws(()=>normalizeJrdbProbeResult(200,goodProbe,'2026-11-22'),/./);

console.log('private local dual-source observation tests PASS');
"""
        result = subprocess.run(["node", "-e", node], input=JS, text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
