/* Synthetic browser test: date-aware read-only 100-yen review. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-100yen-review.js','utf8');
function boot(query,reviewFixture=null,provisionalFixture=null){
 const elements=new Map(),requests=[],storage=new Map();
 let pending=null;
 function node(tag){
  return {tag,children:[],value:'',textContent:'',disabled:false,
    append(...items){this.children.push(...items)},
    replaceChildren(...items){this.children=items},
  };
 }
 function get(id){
  if(!elements.has(id))elements.set(id,node('div'));
  return elements.get(id);
 }
 const document={visibilityState:'visible',getElementById:get,createElement:node};
 const localStorage={getItem:key=>storage.get(key)||null,
   setItem(){throw Error('Read-only dashboard wrote storage')},
   removeItem(){throw Error('Read-only dashboard deleted storage')}};
 const fetch=async(url,opts)=>{
  requests.push({url,opts});
  const wait=pending;pending=null;
  if(wait)await wait;
  if(url.startsWith('/api/owner-100yen-archived'))return {
    ok:true,json:async()=>({archiveEnabled:false,available:false})
  };
  if(url.startsWith('/api/owner-100yen-review'))return {
    ok:true,json:async()=>({available:!!reviewFixture,review:reviewFixture})
  };
  if(url.startsWith('/api/owner-archive-read'))return {
    ok:true,json:async()=>({archiveEnabled:false,persistentStorageReady:false,available:false,receipts:[]})
  };
  if(url==='/api/owner-prestart-tse-review')return {
    ok:true,json:async()=>provisionalFixture
  };
  throw Error('Unexpected backend request');
 };
 const context={document,localStorage,location:{search:query},fetch,
   Date,Intl,JSON,Number,Object,Array,String,RegExp,Set,Map,Error,Promise};
 vm.runInNewContext(js,context);
 return {get,requests,storage,delay:p=>{pending=p}};
}
(async()=>{
 const a=boot('?date=2099-01-02');
 await new Promise(r=>setImmediate(r));
 assert.equal(a.get('day').value,'2099-01-02');
 assert.equal(a.requests.length,2);
 assert.match(a.requests[0].url,/date=2099-01-02$/);
 assert.match(a.requests[1].url,/date=2099-01-02$/);
 assert.match(a.get('status').textContent,/未登録/);
 assert.equal(a.get('load').disabled,false);
 assert.equal(a.storage.size,0);
 const b=boot('?date=2099-02-31');
 await new Promise(r=>setImmediate(r));
 assert.notEqual(b.get('day').value,'2099-02-31');
 assert.equal(b.requests.length,2);
 const c=boot('?date=2099-03-01');
 await new Promise(r=>setImmediate(r));
 let release;
 const pause=new Promise(resolve=>{release=resolve});
 c.delay(pause);
 const stale=c.get('load').onclick();
 assert.equal(c.get('load').disabled,true);
 c.get('day').value='2099-03-02';
 c.get('day').onchange();
 assert.equal(c.get('load').disabled,false);
 release();
 await stale;
 assert.match(c.get('status').textContent,/選んで確認/);
 assert.equal(c.get('summary').children.length,0);
 assert.equal(c.storage.size,0);
 // Read-only official-result fixture tests the newly added slot-miss
 // column without connecting a real results feed or altering local tickets.
 const fake={
  version:'keiba-100yen-review-1',unitYen:100,actualPurchase:false,
  races:[
   {date:'2099-01-02',track:'東京',race:1,status:'verified_result',
    trifectaPoints:40,trioPoints:0,investedYen:4000,returnedYen:0,
    trifectaMissReason:'winner_wrong_slot'},
   {date:'2099-01-02',track:'東京',race:2,status:'pending',
    trifectaPoints:30,trioPoints:0,investedYen:null,returnedYen:null,
    trifectaMissReason:null}
  ],venueBreakdown:[],reviewedRaces:1,pendingRaces:1,
  totalInvestedYen:4000,totalReturnedYen:0,totalProfitYen:-4000,
  roiPercent:0,firstCandidateHits:0,firstCandidateEligibleRaces:1,
  pendingStakeYen:3000,note:'架空の検証'
 };
 const d=boot('?date=2099-01-02',fake);
 await new Promise(r=>setImmediate(r));
 assert.equal(d.get('races').children.length,1);
 const t=d.get('races').children[0].children[0];
 const head=t.children[0].children[0];
 assert.ok(head.children.some(x=>x.textContent==='3連単の検証'));
 const body=t.children[1];
 assert.match(body.children[0].children[4].textContent,/1着馬を2・3着に評価/);
 assert.equal(body.children[1].children[4].textContent,'結果待ち');
 assert.equal(d.storage.size,0);

 // The optional postrace comparison must NOT run on page open.
 const sample={
  version:'owner-prestart-tse-comparison-1',date:'2099-01-02',
  researchOnly:true,privateOwnerOnly:true,officialJraVerified:false,
  independentJraVerified:false,payoutVerified:false,roiPercent:null,
  officialHitCount:null,realPredictionReady:false,actualPurchase:false,
  bettingReady:false,changesExistingReceipts:false,providerReadCount:1,
  raceCount:2,observedRaceCount:1,pendingRaceCount:1,
  provisionalExactCombinationCount:0,provisionalFirstCandidateCount:0,
  races:[
   {track:'東京',race:1,providerStatus:'provider_podium_observed',
    trifectaPoints:40,firstCandidateObserved:false,secondCandidateObserved:true,
    thirdCandidateObserved:true,exactCombinationObserved:false,
    firstMissType:'wrong_slot',officialVerified:false},
   {track:'京都',race:2,providerStatus:'pending',trifectaPoints:30,
    firstCandidateObserved:null,secondCandidateObserved:null,
    thirdCandidateObserved:null,exactCombinationObserved:null,
    firstMissType:null,officialVerified:false}
  ]
 };
 const e=boot('?date=2099-01-02',fake,sample);
 await new Promise(r=>setImmediate(r));
 assert.equal(e.requests.length,2);
 const signed=[{snapshot:{date:'2099-01-02',track:'東京',race:1},
  signature:'a'.repeat(64)}];
 e.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
 await e.get('provisionalCheck').onclick();
 assert.equal(e.requests.length,4);
 assert.match(e.requests[2].url,/owner-archive-read/);
 assert.equal(e.requests[3].url,'/api/owner-prestart-tse-review');
 assert.equal(e.requests[3].opts.method,'POST');
 assert.equal(e.requests[3].opts.headers['X-Keiba-Request'],'private');
 assert.equal(JSON.parse(e.requests[3].opts.body).receipts.length,1);
 assert.match(e.get('provisionalStatus').textContent,/公式の結果・的中・払戻・回収率に加算していません/);
 assert.equal(e.get('provisionalRaces').children.length,3);
 assert.match(e.get('provisionalRaces').children[1].textContent,/勝ち馬を2・3着候補に配置/);
 assert.match(e.get('provisionalRaces').children[2].textContent,/保留/);
 assert.equal(e.storage.size,1);
 e.get('day').value='2099-01-03';e.get('day').onchange();
 assert.equal(e.get('provisionalRaces').children.length,0);

 const forged=boot('?date=2099-01-02',fake,
  {...sample,officialJraVerified:true});
 await new Promise(r=>setImmediate(r));
 forged.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
 await forged.get('provisionalCheck').onclick();
 assert.equal(forged.get('provisionalRaces').children.length,0);
 assert.match(forged.get('provisionalStatus').textContent,/暫定照合ができませんでした/);
 const missing=boot('?date=2099-01-02',fake,sample);
 await new Promise(r=>setImmediate(r));
 await missing.get('provisionalCheck').onclick();
 assert.equal(missing.requests.length,3);
 assert.equal(missing.storage.size,0);
 const staleProvisional=boot('?date=2099-01-02',fake,sample);
 await new Promise(r=>setImmediate(r));
 staleProvisional.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
 let releaseProvisional;
 const holdProvisional=new Promise(resolve=>{releaseProvisional=resolve});
 staleProvisional.delay(holdProvisional);
 const waiting=staleProvisional.get('provisionalCheck').onclick();
 staleProvisional.get('day').value='2099-01-03';
 staleProvisional.get('day').onchange();
 releaseProvisional();await waiting;
 assert.equal(staleProvisional.get('provisionalRaces').children.length,0);
 assert.equal(staleProvisional.storage.size,1);
 console.log('Owner 100-yen review: provisional comparison opt-in/read-only PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
