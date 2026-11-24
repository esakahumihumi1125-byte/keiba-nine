"""Owner-day JRDB and local JV-Link history availability join: zero uploads/calls."""
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML, JS


class LocalJvlinkJrdbCoverageTests(unittest.TestCase):
    def test_affordance_and_no_silent_promotion(self):
        self.assertIn('id="autoJvHistoryJoinPanel"', HTML)
        self.assertIn('id="autoJvHistoryFile"', HTML)
        self.assertIn('id="autoJvHistoryCompare"', HTML)
        self.assertIn('id="autoJvHistoryRows"', HTML)
        self.assertIn("jvdata-all-flat-races-YYYYMMDD.json", HTML)
        self.assertIn("同じ馬の本人確認", HTML)
        self.assertIn("ファイル送信0回", JS)
        self.assertIn("officialHorseIdentityVerified:false", JS)
        self.assertIn("formalTenFactorReady:false", JS)
        # The separate 24R read-only export may create a local Blob URL;
        # the JV-Link source-file importer itself must never do so.
        local_join = JS.rsplit("const dateInput=document.getElementById('autoDay');", 1)[-1]
        self.assertNotIn("URL.createObjectURL", local_join)

    @unittest.skipUnless(shutil.which("node"), "Node unavailable")
    def test_same_day_merge_and_stale_file_guards_without_network(self):
        js = r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
const source=require('node:fs').readFileSync(0,'utf8');
const marker=";(()=>{'use strict';\nconst dateInput=document.getElementById('autoDay');";
const i=source.lastIndexOf(marker);
assert(i>0,'JOIN IIFE present');
const code=source.slice(i);
class Elem{
 constructor(){this.value='';this.children=[];this.textContent='';
  this.onclick=null;this.onchange=null;this.disabled=false;this.files=[];}
 replaceChildren(...c){this.children=c;}
 append(...c){this.children.push(...c);}
}
const makeRace=(track,race,values=[1,2,3])=>({
 track,race,postTimeCandidate:'10:00',historyComplete:false,graded:false,bettingReady:false,
 observedHorseHistory:2,
 byNumber:values.map((number,i)=>({
  number,observedRecordCount:i<2?2:0,
  missingHistoryUnproven:true,graded:false,
  recentObservedRuns:i<2?[{observed:true}]:[],
 }))
});
const day='20261123';
const sourceFile=(races)=>({
 version:'owner-jvdata-local-day-history-bridge-1',date:day,
 capturedAtLocalJst:'2026-11-23T08:00:00+09:00',
 researchOnly:true,privateOwnerOnly:true,
 historySource:'private_jvlink_rcvn_partial_observations',
 historyCompletenessVerified:false,captureTimeIndependentlyVerified:false,
 officialStarterListVerified:false,officialScratchStateVerified:false,
 officialGoingVerified:false,formalTenFactorReady:false,
 productionPredictionReady:false,bettingReady:false,autoPurchase:false,
 newProviderRequests:0,raceCount:races.length,races
});
function env(){
 const controls=new Map([
  'autoDay','autoJvHistoryFile','autoJvHistoryCompare',
  'autoJvHistoryStatus','autoJvHistoryRows','autoRun'
 ].map(k=>[k,new Elem()]));
 const get=id=>controls.get(id);
 get('autoDay').value='2026-11-23';
 let clickCount=0,dateCount=0,networkCount=0;
 get('autoDay').onchange=()=>{dateCount++};
 get('autoRun').onclick=async()=>{clickCount++};
 const rosters=new Map([
  ['東京|1',new Set([1,2,3])],['福島|2',new Set([1,2,3])]
 ]);
 const grades=new Map([
  ['東京|1',new Map([[1,{training:'S',recent:'A'}],
    [2,{training:'A',recent:'未評価'}],
    [3,{training:'未評価',recent:'未評価'}]])],
  ['福島|2',new Map([[1,{training:'S',recent:'B'}],
    [2,{training:'A',recent:'A'}],[3,{training:'B',recent:'C'}]])]
 ]);
 const document={
  getElementById:get,
  createDocumentFragment:()=>new Elem(),
  createElement:()=>new Elem()
 };
 vm.runInNewContext(code,{
  document,historyDay:day,historyRosters:rosters,
  historyGrades:grades,fetch:()=>{networkCount++},
  Set,Map,Date,Object,Array,Number,String,Error,JSON,RegExp,Math
 },{timeout:500});
 return {get,rosters,grades,
  counters:()=>({clickCount,dateCount,networkCount})};
}
const load=(view,doc,name='jvdata-all-flat-races-20261123.json')=>{
 const raw=JSON.stringify(doc);
 view.get('autoJvHistoryFile').files=[{
  name,size:raw.length,text:async()=>raw
 }];
};
const flush=async()=>{for(let j=0;j<8;j++)await Promise.resolve()};
(async()=>{
 const x=env();
 load(x,sourceFile([makeRace('東京',1),makeRace('福島',2)]));
 await x.get('autoJvHistoryCompare').onclick();
 assert.match(x.get('autoJvHistoryStatus').textContent,/馬番集合一致 2R/);
 assert.match(x.get('autoJvHistoryStatus').textContent,/ファイル送信0回/);
 assert.match(x.get('autoJvHistoryStatus').textContent,/同じ馬のID照合/);
 assert.equal(x.get('autoJvHistoryRows').children.length,1); // fragment with two entries
 assert.equal(x.get('autoJvHistoryRows').children[0].children.length,2);
 assert.match(x.get('autoJvHistoryRows').children[0].children[0].textContent,/東京1R/);
 assert.match(x.get('autoJvHistoryRows').children[0].children[0].textContent,/JRA-VAN過去走が観測できた馬番 2/);
 assert.match(x.get('autoJvHistoryRows').children[0].children[0].textContent,/仮評価もある馬番 1/);
 assert.equal(x.counters().networkCount,0);
 assert.equal(x.counters().clickCount,0);
 load(x,sourceFile([makeRace('東京',1,[1,2,4])]));
 await x.get('autoJvHistoryCompare').onclick();
 assert.match(x.get('autoJvHistoryStatus').textContent,/不一致 1R/);
 assert.match(x.get('autoJvHistoryStatus').textContent,/JV側Rなし 1R/);
 const late=sourceFile([makeRace('東京',1),{...makeRace('福島',2),postTimeCandidate:'11:00'}]);
 late.capturedAtLocalJst='2026-11-23T10:00:00+09:00';
 load(x,late);
 await x.get('autoJvHistoryCompare').onclick();
 assert.match(x.get('autoJvHistoryStatus').textContent,/馬番集合一致 1R/);
 assert.match(x.get('autoJvHistoryStatus').textContent,/発走予定後のPC取得 1R/);
 assert.match(x.get('autoJvHistoryRows').children[0].children[0].textContent,/発走予定後のPC取得/);
 assert.match(x.get('autoJvHistoryRows').children[0].children[0].textContent,/観測できた馬番 0/);
 for(const stamp of ['2026-02-30T08:00:00+09:00','2026-11-23T08:00:00','bad']){
  load(x,{...sourceFile([makeRace('東京',1)]),capturedAtLocalJst:stamp});
  await x.get('autoJvHistoryCompare').onclick();
  assert.match(x.get('autoJvHistoryStatus').textContent,/安全に照合できません/);
 }
 const fraud=sourceFile([makeRace('東京',1),makeRace('福島',2)]);
 fraud.officialStarterListVerified=true;
 load(x,fraud);
 await x.get('autoJvHistoryCompare').onclick();
 assert.match(x.get('autoJvHistoryStatus').textContent,/安全に照合できません/);
 assert.equal(x.get('autoJvHistoryRows').children.length,0);
 const dup=sourceFile([makeRace('東京',1),makeRace('東京',1)]);
 load(x,dup);
 await x.get('autoJvHistoryCompare').onclick();
 assert.match(x.get('autoJvHistoryStatus').textContent,/安全に照合できません/);
 const wrongDate=sourceFile([makeRace('東京',1),makeRace('福島',2)]);
 load(x,wrongDate,'jvdata-all-flat-races-20261122.json');
 await x.get('autoJvHistoryCompare').onclick();
 assert.match(x.get('autoJvHistoryStatus').textContent,/同じ開催日の8MB以内/);
 const y=env();
 let resolve;
 y.get('autoJvHistoryFile').files=[{
  name:'jvdata-all-flat-races-20261123.json',size:100,
  text:()=>new Promise(ok=>{resolve=ok})
 }];
 const pending=y.get('autoJvHistoryCompare').onclick();
 y.get('autoDay').value='2026-11-24';
 y.get('autoDay').onchange();
 resolve(JSON.stringify(sourceFile([makeRace('東京',1),makeRace('福島',2)])));
 await pending;await flush();
 assert.equal(y.get('autoJvHistoryRows').children.length,0);
 assert.match(y.get('autoJvHistoryStatus').textContent,/開催日を変更しました/);
 assert.equal(y.counters().dateCount,1);
 assert.equal(y.get('autoJvHistoryCompare').disabled,false);
 await y.get('autoRun').onclick();
 assert.equal(y.counters().clickCount,1);
 assert.equal(y.counters().networkCount,0);
 console.log('Owner JRDB x JV-Link local same-number evidence join: 2R, invalid/stale/date and no network PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
"""
        completed = subprocess.run(["node", "-e", js], input=JS,
                                   capture_output=True, text=True,
                                   check=False, timeout=12)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("no network PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
