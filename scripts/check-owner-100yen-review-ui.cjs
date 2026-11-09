/* Synthetic browser test: date-aware read-only 100-yen review. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-100yen-review.js','utf8');
function boot(query,reviewFixture=null){
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
 console.log('Owner 100-yen review: auto open, day handoff, stale fetch, miss reasons, read-only PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
