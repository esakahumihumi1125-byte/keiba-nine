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
 pastFourthCorner:'insufficient',comparisonRank:i+1
}));
const first=[1,2],second=[1,2,3,4,5],third=[1,2,3,4,5,6,7];
const tickets=[];
for(const a of first)for(const b of second)for(const c of third)
 if(a!==b&&a!==c&&b!==c)tickets.push([a,b,c]);
const sortedTickets=tickets.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
const research=()=>({
 version:'jrdb-owner-auto-draft-1',date:day,researchOnly:true,
 privateOwnerOnly:true,officialJraVerified:false,
 overallPredictionReady:false,bettingReady:false,autoPurchase:false,
 sourceReadCount:4,unitYen:100,raceCount:1,draftCount:1,holdCount:0,holdReasons:{},
 serverStamped:true,captureAuditVerified:false,researchReceiptCount:1,
 archiveEnabled:false,archiveRecordCount:0,archiveConflictCount:0,
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
 return result;
}
function boot(){
 const storage=new Map(),elements=new Map(),requests=[];
 let next=resultWith('a'.repeat(64)),holdFetch=null;
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
  getElementById:get,createElement:node,createDocumentFragment:()=>node('fragment')
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
  constructor(...args){super(...(args.length?args:['2099-01-01T00:00:00Z']))}
 }
 const context={document,localStorage,fetch,Intl,Date:FakeDate,JSON,Set,Map,Number,
  String,Array,Error,Promise,Object};
 vm.runInNewContext(js,context);
 get('autoDay').value=date;
 return {get,storage,requests,setServer:x=>next=x,
  waitNextFetch:promise=>{holdFetch=promise}};
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
 assert.match(a.get('autoSavedStatus').textContent,/新規 1R/);
 const firstSave=JSON.parse(a.storage.get(STORAGE));
 assert.equal(firstSave.length,1);
 assert.equal(firstSave[0].signature,'a'.repeat(64));
 assert.equal(firstSave[0].snapshot.trifectaTickets.length,40);
 // A later forecast is NOT allowed to overwrite the earlier frozen receipt.
 a.setServer(resultWith('b'.repeat(64)));
 await a.get('autoRun').onclick();
 assert.equal(JSON.parse(a.storage.get(STORAGE))[0].signature,'a'.repeat(64));
 assert.match(a.get('autoSavedStatus').textContent,/新規 0R/);
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
 assert.match(a.get('autoRaces').children[0].children[0].children[1].textContent,/馬番別資料の形式/);
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
 assert.match(a.get('autoRaces').children[0].children[0].children[1].textContent,/先にサーバーへ固定済み/);
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
 release();
 await stale;
 assert.equal(b.get('autoSummary').textContent,'未取得');
 b.get('autoDay').value='2099-01-01';
 b.get('autoDay').onchange();
 assert.match(b.get('autoSavedStatus').textContent,/固定済み研究記録 1R/);
 assert.equal(b.get('autoRun').disabled,false);
 assert.ok(!js.includes('innerHTML'),'no DOM HTML injection');
 assert.ok(!js.includes('owner-real-purchases-v1'),'do not write actual purchases');
 console.log('Owner auto forecast: 40-point signed save, idempotency, tamper block, no purchased writes PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
