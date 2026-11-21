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
const {compareLocalJvWithJrdb}=module.exports;
const date='2026-11-22';
const jrdb={schema:'keiba-nine-private-preday-review-v1',date,
 sourceKind:'owner-private-authored-preday',predictionReady:false,
 officialJraVerified:false,purchased:false,races:[
  {track:'東京',race:1,time:'09:50',course:'ダ・左1300M',
   field:3,rank:[3,2,1]}]};
const file={version:'owner-jvdata-local-day-history-bridge-1',date,
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
 {...file,date:'2026-11-21'},
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
console.log('private local dual-source observation tests PASS');
"""
        result = subprocess.run(["node", "-e", node], input=JS, text=True,
                                capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr[-1500:])
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
