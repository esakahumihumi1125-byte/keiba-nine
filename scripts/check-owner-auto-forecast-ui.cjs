/* Owner-only auto-draft mobile UI: synthetic DOM and local receipt preservation. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-auto-forecast.js','utf8');
const STORAGE='keiba-nine-owner-server-receipts-v1';
const day='20990101', date='2099-01-01';
const pairs=[['S','S',8,'S'],['S','A',7,'A'],['A','A',6,'A'],
 ['A','B',5,'B'],['B','B',4,'B'],['B','C',3,'C'],['C','C',2,'C']];
const runners=pairs.map(([training,recent,twoFactorPoints,twoFactorGrade],i)=>({
 number:i+1,training,recent,twoFactorPoints,twoFactorGrade,
 weightedResearchPoints:30*({S:3,A:2,B:1,C:0}[training])+
                         3*({S:3,A:2,B:1,C:0}[recent]),
 pastFourthCorner:'insufficient',comparisonRank:i+1
}));
const first=[1,2],second=[1,2,3,4,5],third=[1,2,3,4,5,6,7];
const tickets=[];
for(const a of first)for(const b of second)for(const c of third)
 if(a!==b&&a!==c&&b!==c)tickets.push([a,b,c]);
const sortedTickets=tickets.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
const POLICY=[
 ['training','調教',30,true],['recent','近走',3,true],
 ['course_distance','コース・距離',20,true],['pace','展開・脚質',20,true],
 ['ground','馬場',12,true],['pedigree','血統',8,false],
 ['draw_weight','枠・斤量',3,false],['jockey_stable','騎手・厩舎',2,false],
 ['rotation','ローテ',1,false],['body_condition','馬体重',1,false]
];
function withTenPreview(r){
 r.tenFactorPreview={
  version:'owner-ten-factor-contract-1',policyVersion:'research-5',
  factorCount:10,totalWeight:100,normalization:'weighted_mean_over_100',
  scoreUnit:'0_to_100',gradeThresholds:{S:85,A:70,B:55},
  researchOnly:true,overallPredictionReady:false,officialJraVerified:false,
  autoPurchase:false,fullPredictionRaceCount:0,
  requiredForOverall:'all_ten_verified_before_start',
  factors:POLICY.map(([key,label,weight,core])=>({key,label,weight,core})),
  raceCount:r.races.length,
  races:r.races.map(row=>({
   track:row.track,race:row.race,runnerCount:row.runners.length,
   overallReady:false,fullTenFactorCount:0,
   sourceGradeMode:'two_factor_provisional_only',
   horses:row.runners.map(h=>{
    const grades=Object.fromEntries(POLICY.map(([key])=>
     [key,key==='training'?h.training:key==='recent'?h.recent:'未評価']));
    return {number:h.number,grades,score:null,overallGrade:'未評価',
     overallRank:null,verifiedFactorCount:0,
     provisionalFactorCount:['training','recent'].filter(k=>grades[k]!=='未評価').length,
     missing:POLICY.map(([k])=>k).filter(k=>grades[k]==='未評価')};
   })
  }))
 };
 return r;
}
const research=()=>({
 version:'jrdb-owner-auto-draft-1',date:day,researchOnly:true,
 privateOwnerOnly:true,officialJraVerified:false,
 overallPredictionReady:false,bettingReady:false,autoPurchase:false,
 sourceReadCount:4,unitYen:100,raceCount:1,draftCount:1,holdCount:0,holdReasons:{},
 weightedResearchOrder:'training30_recent3',weightedResearchMax:99,
 weightedResearchPolicy:'research-5',
 serverStamped:true,captureAuditVerified:false,researchReceiptCount:1,
 archiveEnabled:false,archiveRecordCount:0,archiveConflictCount:0,
 raceContext:{
  version:'race-context-1',raceCount:1,courseInfoPresentCount:1,
  goingAvailableCount:1,raceConditionsVerified:false,predictionReady:false,
  conditionProviderReadCount:1,conditionProviderFetchStatus:'received',
  races:[{
   track:'東京',race:1,surface:'芝',distance_m:2000,turn:'左',
   going:'重',goingAvailable:true,conditionSnapshotPresent:true,
   conditionUpdateRecorded:true,courseInfoPresent:true,
   horseCourseSuitabilityAssessed:false,
   horseGoingSuitabilityAssessed:false,predictionReady:false
  }]
 },
 sourceMaterials:{version:'owner-draft-material-coverage-1',status:'unavailable',
  observedFactorSlots:0,gradedNewFactors:0,officialJraVerified:false,races:[]},
 races:[{
  track:'東京',race:1,status:'provisional_draft',reason:'two_factor_only',
  postTime:'12:00',researchOnly:true,officialJraVerified:false,
  overallPredictionReady:false,bettingReady:false,autoPurchase:false,
  runners,first,second,third,tickets,points:40,amountYen:4000
 }]
});
function resultWith(signature){
 const result=research();
 result.researchReceipts=[{
  signature, snapshot:{
   date,track:'東京',race:1,sourceKind:'prestart-locked',
   actualPurchase:false,lockedAt:'2099-01-01T09:00:00+09:00',
   scheduledOffAt:'2099-01-01T12:00:00+09:00',
   trifectaTickets:sortedTickets,trioTickets:[],
   scheduleVerified:false,predictionVerified:false
  }
 }];
 return withTenPreview(result);
}
function boot(){
 const storage=new Map(),elements=new Map(),requests=[];
 let next=resultWith('a'.repeat(64)),holdFetch=null;
 let now='2099-01-01T00:00:00Z',onVisibility=null;
 function node(tag){
  return {
   tag,children:[],textContent:'',className:'',value:'',disabled:false,
   dataset:{},onclick:null,role:null,
   append(...children){this.children.push(...children)},
   replaceChildren(...children){this.children=children},
   setAttribute(k,v){this[k]=v},
   querySelectorAll(name){return this.children.filter(x=>x.tag===name)},
  };
 }
 function get(id){if(!elements.has(id))elements.set(id,node('div'));return elements.get(id)}
 const document={
  visibilityState:'visible',
  getElementById:get,createElement:node,createDocumentFragment:()=>node('fragment'),
  addEventListener:(name,fn)=>{if(name==='visibilitychange')onVisibility=fn}
 };
 const localStorage={
  getItem:k=>storage.get(k)||null,
  setItem(k,v){storage.set(k,v)},
 };
 const fetch=async(url,options)=>{
  requests.push({url,options});
  const pause=holdFetch;holdFetch=null;
  if(pause)await pause;
  return {ok:true,json:async()=>structuredClone(next)};
 };
 class FakeDate extends Date{
  constructor(...args){super(...(args.length?args:[now]))}
 }
 const context={document,localStorage,fetch,Intl,Date:FakeDate,JSON,Set,Map,Number,
  String,Array,Error,Promise,Object};
 vm.runInNewContext(js,context);
 get('autoDay').value=date;
 return {get,storage,requests,setServer:x=>next=withTenPreview(x),
  setServerRaw:x=>next=x,
  waitNextFetch:promise=>{holdFetch=promise},
  advanceClock:iso=>{now=iso},resume:()=>{if(onVisibility)onVisibility()}};
}
(async()=>{
 const a=boot();
 // Visiting the owner-only page triggers the first read automatically.
 await new Promise(r=>setImmediate(r));
 assert.equal(a.requests.length,1);
 assert.equal(a.get('autoRun').disabled,false);
 assert.match(a.requests[0].url,/\/api\/jrdb\/owner-auto-draft\?date=20990101$/);
 assert.equal(a.requests[0].options.headers['X-Keiba-Request'],'private');
 assert.equal(a.get('autoSummary').textContent.includes('1R中、研究用自動案 1R'),true);
 assert.equal(a.get('autoTenWeights').children.length,10);
 assert.match(a.get('autoRaces').children[0].children[0].children[3].textContent,
  /調教30：近走3での仮順位/);
 assert.match(a.get('autoTenStatus').textContent,/残り8項目は未評価/);
 assert.match(a.get('autoSummary').textContent,/馬場資料の存在 1R/);
 assert.match(a.get('autoRaces').children[0].children[0].children[1].textContent,
  /芝／2000m／左／重（JRDB資料）/);
 assert.match(a.get('autoRaces').children[0].children[0].children[2].textContent,
  /過去4角の位置取り観測/);
 const firstDetail=a.get('autoRaces').children[0].children[0];
 assert.equal(firstDetail.children.filter(x=>x.className==='ten-horse').length,7);
 const firstTen=firstDetail.children.find(x=>x.className==='ten-horse');
 assert.match(firstTen.children[0].textContent,/総合 未評価/);
 assert.equal(firstTen.children[1].children.length,10);
 assert.match(firstTen.children[1].children[0].children[1].textContent,/S（仮）/);
 assert.match(firstTen.children[1].children[2].children[1].textContent,/未評価/);
 assert.match(a.get('autoSavedStatus').textContent,/新規 1R/);
 const firstSave=JSON.parse(a.storage.get(STORAGE));
 assert.equal(firstSave.length,1);
 assert.match(a.get('autoHistoryStatus').textContent,/固定 1R/);
 assert.equal(a.get('autoHistory').children.length,1);
 const history=a.get('autoHistory').children[0];
 assert.match(history.children[0].textContent,/3連単 40点/);
 assert.match(history.children[2].textContent,/1着候補：1・2番/);
 assert.match(history.children[5].textContent,/1→2→3/);
 assert.equal(firstSave[0].signature,'a'.repeat(64));
 assert.equal(firstSave[0].snapshot.trifectaTickets.length,40);
 // A later forecast is NOT allowed to overwrite the earlier frozen receipt.
 a.setServer(resultWith('b'.repeat(64)));
 await a.get('autoRun').onclick();
 assert.equal(JSON.parse(a.storage.get(STORAGE))[0].signature,'a'.repeat(64));
 assert.match(a.get('autoSavedStatus').textContent,/新規 0R/);
 assert.equal(a.get('autoHistory').children.length,1);
 // Invalid graded/threshold payloads must never be rendered as 10-factor
 // finished predictions or be saved as new signed receipts.
 const beforeInvalidTen=a.storage.get(STORAGE);
 const badTen=resultWith('a'.repeat(64));
 badTen.tenFactorPreview.factors[0].weight=99;
 a.setServerRaw(badTen);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoTenStatus').textContent,/確認できません/);
 assert.equal(a.get('autoTenWeights').children.length,0);
 assert.equal(a.storage.get(STORAGE),beforeInvalidTen);
 // A corrupt current-going source must not be displayed as a trusted
 // racing condition or cause any new receipt write.
 const badCondition=resultWith('a'.repeat(64));
 badCondition.raceContext.races[0].going='unsupported';
 a.setServerRaw(badCondition);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoTenStatus').textContent,/確認できません/);
 assert.equal(a.storage.get(STORAGE),beforeInvalidTen);
 // A bad response signature must not mutate frozen picks or purchases.
 const corrupted=resultWith('not-an-authentic-signature');
 a.setServer(corrupted);
 const before=a.storage.get(STORAGE);
 await a.get('autoRun').onclick();
 assert.equal(a.storage.get(STORAGE),before);
 assert.match(a.get('autoSavedStatus').textContent,/保存はできませんでした/);
 assert.equal(a.storage.has('keiba-nine-owner-real-purchases-v1'),false);
 // A malformed runner source holds only that race and never saves tickets.
 const bad=research();
 bad.races=[{...bad.races[0],status:'hold',reason:'invalid_two_factor',
  validationIssue:'runner_shape',runners:[],first:[],second:[],third:[],
  tickets:[],points:0,amountYen:0}];
 bad.draftCount=0;bad.holdCount=1;bad.holdReasons={invalid_two_factor:1};
 bad.researchReceipts=[];bad.researchReceiptCount=0;
 a.setServer(bad);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoRaces').children[0].children[0].children[2].textContent,/馬番別資料の形式/);
 assert.equal(a.storage.get(STORAGE),before);
 // An older archived formation wins over a changed reanalysis. No newer
 // selection is exposed as a draft or written to this device.
 const conflict=research();
 conflict.races=[{...conflict.races[0],status:'hold',
   reason:'archived_earlier_draft',runners:[],first:[],second:[],
   third:[],tickets:[],points:0,amountYen:0}];
 conflict.draftCount=0;conflict.holdCount=1;
 conflict.holdReasons={archived_earlier_draft:1};
 conflict.archiveEnabled=true;conflict.archiveRecordCount=1;
 conflict.archiveConflictCount=1;
 conflict.researchReceipts=[];conflict.researchReceiptCount=0;
 a.setServer(conflict);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoSummary').textContent,/既存の固定買い目を優先 1R/);
 assert.match(a.get('autoRaces').children[0].children[0].children[2].textContent,/先にサーバーへ固定済み/);
 assert.equal(a.storage.get(STORAGE),before);
 // No new prestart forecast means no new record, not a fabricated loss.
 const empty=research();
 empty.races=[{...empty.races[0],status:'hold',reason:'after_provisional_off',
  first:[],second:[],third:[],tickets:[],points:0,amountYen:0}];
 empty.draftCount=0;empty.holdCount=1;empty.holdReasons={after_provisional_off:1};
 empty.researchReceipts=[];empty.researchReceiptCount=0;
 a.setServer(empty);
 await a.get('autoRun').onclick();
 assert.equal(a.storage.get(STORAGE),before);
 assert.match(a.get('autoSavedStatus').textContent,/ありません/);
 // A date switch while a slow fetch is in flight must remain operable,
 // and older data must not silently overwrite the selected day's status.
 const b=boot();
 await new Promise(r=>setImmediate(r));
 let release;
 const pause=new Promise(resolve=>{release=resolve});
 b.waitNextFetch(pause);
 const stale=b.get('autoRun').onclick();
 assert.equal(b.get('autoRun').disabled,true);
 b.get('autoDay').value='2099-01-02';
 b.get('autoDay').onchange();
 assert.equal(b.get('autoRun').disabled,false);
 assert.match(b.get('autoSavedStatus').textContent,/ありません/);
 assert.equal(b.get('autoHistory').children.length,0);
 release();
 await stale;
 assert.equal(b.get('autoSummary').textContent,'未取得');
 b.get('autoDay').value='2099-01-01';
 b.get('autoDay').onchange();
 assert.match(b.get('autoSavedStatus').textContent,/固定済み研究記録 1R/);
 assert.equal(b.get('autoHistory').children.length,1);
 assert.equal(b.get('autoRun').disabled,false);
 // A long-running PWA that crosses midnight should select the new JST day
 // exactly once when visible, without background polling.
 const c=boot();
 await new Promise(r=>setImmediate(r));
 const nextDay=resultWith('d'.repeat(64));
 nextDay.date='20990102';
 nextDay.researchReceipts[0].snapshot.date='2099-01-02';
 nextDay.researchReceipts[0].snapshot.lockedAt='2099-01-02T09:00:00+09:00';
 nextDay.researchReceipts[0].snapshot.scheduledOffAt='2099-01-02T12:00:00+09:00';
 c.setServer(nextDay);
 c.advanceClock('2099-01-01T16:00:00Z');
 c.resume();
 await new Promise(r=>setImmediate(r));
 assert.equal(c.get('autoDay').value,'2099-01-02');
 assert.equal(c.requests.length,2);
 assert.equal(c.get('autoHistory').children.length,1);
 c.resume();
 assert.equal(c.requests.length,2);
 // A deliberately chosen old date cannot be replaced by resume events.
 c.get('autoDay').value='2099-01-01';c.get('autoDay').onchange();
 c.advanceClock('2099-01-02T16:00:00Z');
 c.resume();
 assert.equal(c.get('autoDay').value,'2099-01-01');
 assert.equal(c.requests.length,2);
 assert.ok(!js.includes('innerHTML'),'no DOM HTML injection');
 assert.ok(!js.includes('owner-real-purchases-v1'),'do not write actual purchases');
 console.log('Owner auto forecast: 40-point signed save, idempotency, tamper block, no purchased writes PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
