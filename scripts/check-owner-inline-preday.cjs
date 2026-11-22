/* Standalone DOM checks for the owner's no-cost in-page preday reference. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const whole=fs.readFileSync('/tmp/keiba-owner-auto-forecast.js','utf8');
const marker=";(()=>{'use strict';\nconst load=document.getElementById('autoPredayInlineLoad');";
const offset=whole.lastIndexOf(marker);
assert(offset>=0,'isolated script found');
const code=whole.slice(offset);
class El{
 constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.disabled=false;this.value='';}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=children;}
}
function forecast(day='2099-01-01'){
 const races=[];
 for(const track of ['東京','京都'])for(let n=1;n<=12;n++)races.push({
  track,race:n,time:'11:00',field:5,rank:[1,2,3],first:[1],
  second:[1,2],third:[1,2,3],points:1,status:n%3?'買い候補':'見送り',
  provisional:true,jraOfficialConfirmed:false,fullFactorVerified:false
 });
 return {available:true,forecast:{
  schema:'keiba-nine-private-preday-review-v1',
  sourceKind:'owner-private-authored-preday',date:day,
  raceCount:races.length,predictionReady:false,
  officialJraVerified:false,purchased:false,races
 }};
}
function setup(fetchImpl){
 const elements=new Map(['autoPredayInlineLoad','autoPredayInlineStatus','autoPredayInlineRaces','autoDay'].map(id=>[id,new El(id)]));
 const input=elements.get('autoDay');
 input.value='2099-01-01';
 let existingChanges=0;
 input.onchange=()=>{existingChanges++;};
 const calls=[];
 const fetch=async (...args)=>{calls.push(args);return fetchImpl(...args);};
 vm.runInNewContext(code,{
  document:{
   getElementById:id=>elements.get(id),
   createElement:tag=>new El(tag),
   createDocumentFragment:()=>new El('fragment')
  },fetch,Date,Intl,Set,Map,Object,Array,Number,String,RegExp,Error
 },{timeout:500});
 return {elements,input,calls,get:id=>elements.get(id),get existingChanges(){return existingChanges;}};
}
function descendantText(el){
 return (el.textContent||'')+(el.children||[]).map(descendantText).join('\n');
}
(async()=>{
 const ok=setup(async()=>({ok:true,json:async()=>forecast()}));
 await ok.get('autoPredayInlineLoad').onclick();
 assert.match(ok.get('autoPredayInlineStatus').textContent,/前日参考 24R/);
 assert.match(ok.get('autoPredayInlineStatus').textContent,/追加のJRDB照会0回/);
 assert.equal(ok.get('autoPredayInlineLoad').disabled,false);
 assert.equal(ok.calls.length,1);
 assert.equal(ok.calls[0][0],'/api/owner-preday-forecast');
 assert.equal(ok.calls[0][1].credentials,'same-origin');
 const shown=descendantText(ok.get('autoPredayInlineRaces'));
 assert.match(shown,/京都 12R/);
 assert.match(shown,/東京 12R/);
 assert.match(shown,/1着 1 ／ 2着 1・2 ／ 3着 1・2・3/);
 assert.match(shown,/正式10項目・JRA最終出走/);
 assert(!shown.includes('馬名を勝手に生成'));
 // Same-day current race is historical after the provisional post time:
 // no new formation should appear.
 const expired=setup(async()=>({ok:true,json:async()=>forecast('2026-11-21')}));
 expired.input.value='2026-11-21';
 // The runtime current date might be beyond this fixture; past days
 // must be rejected before any API request or new betting display.
 await expired.get('autoPredayInlineLoad').onclick();
 assert.equal(expired.calls.length,0);
 assert.match(expired.get('autoPredayInlineStatus').textContent,/過去日の新規参考買い目/);
 const bad=forecast();bad.forecast.races[0].points=48;
 const fail=setup(async()=>({ok:true,json:async()=>bad}));
 await fail.get('autoPredayInlineLoad').onclick();
 assert.match(fail.get('autoPredayInlineStatus').textContent,/安全に表示できません/);
 assert.equal(fail.get('autoPredayInlineRaces').children.length,0);
 const mismatch=setup(async()=>({ok:true,json:async()=>forecast('2099-01-02')}));
 await mismatch.get('autoPredayInlineLoad').onclick();
 assert.equal(mismatch.get('autoPredayInlineRaces').children.length,0);
 let release;
 const delayed=setup(()=>new Promise(resolve=>{release=resolve;}));
 const pending=delayed.get('autoPredayInlineLoad').onclick();
 delayed.input.value='2099-01-02';delayed.input.onchange();
 assert.equal(delayed.existingChanges,1,'preserve original day change');
 release({ok:true,json:async()=>forecast()});
 await pending;
 assert.equal(delayed.get('autoPredayInlineRaces').children.length,0,
  'stale response must not populate changed date');
 assert.match(delayed.get('autoPredayInlineStatus').textContent,/開催日が変わりました/);
 assert.equal(delayed.get('autoPredayInlineLoad').disabled,false);
 console.log('Owner in-page preday 24R: validated, stale-safe, no paid JRDB/receipt writes PASS');
})().catch(e=>{console.error(e);process.exitCode=1});