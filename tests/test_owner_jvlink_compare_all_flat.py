"""All-flat JV-Link/JRDB browser-only crosscheck; synthetic files only."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_jvlink_compare_ui import JS, HTML


class OwnerAllFlatBrowserCompareTests(unittest.TestCase):
    def test_owner_ui_accepts_new_sanitized_batch_file(self):
        self.assertIn("jvdata-all-flat-races-YYYYMMDD.json", HTML)
        self.assertIn("2資料を照合（全R対応）", HTML)
        self.assertIn("compareLocalAllFlatHistory", JS)
        self.assertIn("file.size>8000000", JS)
        self.assertNotIn("method:'POST'", JS)
        self.assertNotIn("localStorage", JS)
        self.assertNotIn("sessionStorage", JS)
        self.assertNotIn("rawJvData", JS)

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_24r_consistency_and_strict_fail_closed(self):
        code = r"""
const source=require('node:fs').readFileSync(0,'utf8');
const assert=require('node:assert/strict'),vm=require('node:vm');
const module={exports:{}};
vm.runInNewContext(source,{module},{timeout:2000});
const {compareLocalAllFlatHistory}=module.exports;
const date='2026-11-22',day='20261122';
const tracks=['東京','京都'];
const races=tracks.flatMap(track=>Array.from({length:12},(_,i)=>({
 track,race:i+1,time:'09:50',course:'芝・左1800M',
 field:4,rank:[1,2,3],status:i%3===0?'見送り':'買い候補'
})));
const reference={
 schema:'keiba-nine-private-preday-review-v1',sourceKind:'owner-private-authored-preday',
 date,predictionReady:false,officialJraVerified:false,purchased:false,races
};
const card=(track,race)=>({
 track,race,postTimeCandidate:'09:50',distanceMetersCandidate:1800,
 surfaceCandidate:'芝',historyComplete:false,graded:false,bettingReady:false,
 byNumber:[1,2,3,4].map(number=>({
  number,observedRecordCount:number%2?1:0,
  missingHistoryUnproven:true,graded:false,recentObservedRuns:[]
 }))
});
const file={
 version:'owner-jvdata-local-day-history-bridge-1',date:day,
 raceCount:24,privateOwnerOnly:true,researchOnly:true,
 historySource:'private_jvlink_rcvn_partial_observations',
 historyCompletenessVerified:false,captureTimeIndependentlyVerified:false,
 officialStarterListVerified:false,officialScratchStateVerified:false,
 officialGoingVerified:false,formalTenFactorReady:false,
 productionPredictionReady:false,bettingReady:false,autoPurchase:false,
 newProviderRequests:0,races:races.map(r=>card(r.track,r.race))
};
const output=compareLocalAllFlatHistory(file,reference);
assert.equal(output.observedJvRaceCount,24);
assert.equal(output.editorialRaceCount,24);
assert.equal(output.consistentCandidateRaceCount,24);
assert.equal(output.missingJvRaces,0);
assert.equal(output.mismatchJvRaces,0);
assert.equal(output.unexpectedJvRaceCount,0);
assert.equal(output.observedHorseHistories,48);
assert.equal(output.referenceCardAndJvCandidateFieldsAllConsistent,true);
assert.equal(output.races.length,24);
assert(!JSON.stringify(output).includes('recentObservedRuns'));
for(const key of ['allHorseIdentityMatched','officialStarterListVerified',
 'officialScratchesVerified','officialGoingVerified','formalTenFactorReady','bettingReady']){
 assert.equal(output[key],false,key+' cannot be promoted');
}
const missing=compareLocalAllFlatHistory({...file,
 races:file.races.slice(0,-1),raceCount:23},reference);
assert.equal(missing.missingJvRaces,1);
assert.equal(missing.consistentCandidateRaceCount,23);
assert.equal(missing.referenceCardAndJvCandidateFieldsAllConsistent,false);
const mismatch=compareLocalAllFlatHistory({...file,races:[
 {...file.races[0],distanceMetersCandidate:1600},...file.races.slice(1)
]},reference);
assert.equal(mismatch.mismatchJvRaces,1);
assert.equal(mismatch.consistentCandidateRaceCount,23);
const extra=compareLocalAllFlatHistory({...file,
 races:[...file.races,card('福島',1)],raceCount:25},reference);
assert.equal(extra.unexpectedJvRaceCount,1);
assert.equal(extra.referenceCardAndJvCandidateFieldsAllConsistent,false);
for(const edited of [
 {...file,date:'20261121'},
 {...file,historyCompletenessVerified:true},
 {...file,officialStarterListVerified:true},
 {...file,bettingReady:true},
 {...file,newProviderRequests:1},
 {...file,raceCount:1},
 {...file,races:[...file.races,file.races[0]],raceCount:25},
 {...file,races:[...file.races.slice(0,1),{...file.races[1],
  byNumber:[file.races[1].byNumber[0],file.races[1].byNumber[0],
  ...file.races[1].byNumber.slice(2)]},...file.races.slice(2)]},
]){
 assert.throws(()=>compareLocalAllFlatHistory(edited,reference));
}
assert.throws(()=>compareLocalAllFlatHistory(file,{...reference,races:[
 ...reference.races,reference.races[0]
]}));
assert.throws(()=>compareLocalAllFlatHistory(file,{...reference,date:'2026-11-23'}));
console.log('Owner all-flat JV-Link x JRDB: 24R candidate consistency, hold/missing, privacy and fail-closed PASS');
"""
        run = subprocess.run(
            ["node", "-e", code], input=JS, text=True,
            capture_output=True, timeout=15, check=False,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("24R candidate consistency", run.stdout)


if __name__ == "__main__":
    unittest.main()
