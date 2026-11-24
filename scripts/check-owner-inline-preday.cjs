/* Standalone DOM checks for the owner's no-cost in-page preday reference. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const whole=fs.readFileSync('/tmp/keiba-owner-auto-forecast.js','utf8');
const marker=";(()=>{'use strict';\nconst load=document.getElementById('autoPredayInlineLoad');";
const offset=whole.lastIndexOf(marker);
assert(offset>=0,'isolated script found');
const code=whole.slice(offset);
class El{
 constructor(tag){this.tag=tag;this.children=[];this.textContent='';this.disabled=false;this.value='';this.onclick=null;this.ariaPressed='';}
 append(...children){this.children.push(...children);}
 replaceChildren(...children){this.children=children;}
 setAttribute(key,value){this[key]=value;}
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
function setup(fetchImpl,initialDay='2099-01-01'){
 const elements=new Map(['autoPredayInlineLoad','autoPredayInlineStatus','autoPredayInlineRaces','autoDay'].map(id=>[id,new El(id)]));
 const input=elements.get('autoDay');
 input.value=initialDay;
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
async function tick(){await new Promise(resolve=>setImmediate(resolve));}
(async()=>{
 const ok=setup(async()=>({ok:true,json:async()=>forecast()}));
 await tick(); // The free private snapshot loads without pressing a button.
 assert.match(ok.get('autoPredayInlineStatus').textContent,/前日参考 24R/);
 assert.match(ok.get('autoPredayInlineStatus').textContent,/追加のJRDB照会0回/);
 assert.equal(ok.get('autoPredayInlineLoad').disabled,false);
 assert.equal(ok.calls.length,1,'one free snapshot request on page open');
 assert.equal(ok.calls[0][0],'/api/owner-preday-forecast');
 assert.equal(ok.calls[0][1].credentials,'same-origin');
 const shown=descendantText(ok.get('autoPredayInlineRaces'));
 assert.match(shown,/(京都|東京) 12R/,'one venue presents all 12R');
 assert.match(shown,/1着 1/);
 assert.match(shown,/2着 1・2/);
 assert.match(shown,/3着 1・2・3/);
 const [tabs,kinds,chooser,cards]=ok.get('autoPredayInlineRaces').children;
 assert.equal(tabs.children.length,2,'separate venue tabs');
 assert(new Set(tabs.children.map(x=>x.textContent)).has('東京'));
 assert(new Set(tabs.children.map(x=>x.textContent)).has('京都'));
 assert.equal(cards.children.length,12,'all 12R in selected venue by default');
 assert.equal(kinds.children.length,3,'free preday can filter candidate/held races');
 assert.deepEqual(kinds.children.map(x=>x.textContent),[
  '全R 12R','買い候補 8R','見送り等 4R']);
 kinds.children[1].onclick();
 assert.equal(cards.children.filter(c=>!c.hidden).length,8,
  'only authored buy-candidate status, not all unsigned references');
 assert.equal(kinds.children[1]['aria-pressed'],'true');
 assert.equal(cards.children[2].hidden,true,'3R is an authored hold');
 kinds.children[2].onclick();
 assert.equal(cards.children.filter(c=>!c.hidden).length,4);
 assert.equal(cards.children[2].hidden,false,'held rows remain discoverable');
 assert.equal(cards.children[0].hidden,true);
 assert.equal(chooser.children.length,13,'all 12R + all-races control');
 chooser.children[7].onclick();
 assert.equal(kinds.children[0]['aria-pressed'],'true','number tap resets filters');
 assert.equal(cards.children.filter(el=>!el.hidden).length,1);
 assert.equal(cards.children[6].hidden,false,'7R one-tap filter');
 assert.equal(chooser.children[7]['aria-pressed'],'true');
 chooser.children[0].onclick();
 assert.equal(cards.children.filter(el=>!el.hidden).length,12);
 tabs.children[1].onclick();
 assert.equal(cards.children.length,12,'all 12R after venue switch');
 assert.equal(cards.children.filter(el=>!el.hidden).length,12,'venue resets to allR');
 assert.deepEqual(kinds.children.map(x=>x.textContent),[
  '全R 12R','買い候補 8R','見送り等 4R']);
 assert.match(descendantText(cards),/(京都|東京) 12R/);
 assert.match(shown,/正式10項目・JRA最終出走/);
 assert(!shown.includes('馬名を勝手に生成'));
 // Same-day current race is historical after the provisional post time:
 // no new formation should appear.
 const expired=setup(async()=>({ok:true,json:async()=>forecast('2026-11-21')}),'2026-11-21');
 // The runtime current date might be beyond this fixture; past days
 // must be rejected before any API request or new betting display.
 await tick();
 assert.equal(expired.calls.length,0);
 assert.match(expired.get('autoPredayInlineStatus').textContent,/過去日の新規参考買い目/);
 const bad=forecast();bad.forecast.races[0].points=48;
 const fail=setup(async()=>({ok:true,json:async()=>bad}));
 await tick();
 assert.match(fail.get('autoPredayInlineStatus').textContent,/安全に表示できません/);
 assert.equal(fail.get('autoPredayInlineRaces').children.length,0);
 const mismatch=setup(async()=>({ok:true,json:async()=>forecast('2099-01-02')}));
 await tick();
 assert.equal(mismatch.get('autoPredayInlineRaces').children.length,0);
 const replies=[];
 const delayed=setup(()=>new Promise(resolve=>{replies.push(resolve);}));
 assert.equal(delayed.calls.length,1,'initial request is in flight');
 delayed.input.value='2099-01-02';delayed.input.onchange();
 assert.equal(delayed.existingChanges,1,'preserve original day change');
 assert.equal(delayed.calls.length,2,'new day causes one free read');
 replies[0]({ok:true,json:async()=>forecast()});
 await tick();
 assert.equal(delayed.get('autoPredayInlineRaces').children.length,0,
  'stale response must not populate changed date');
 replies[1]({ok:true,json:async()=>forecast('2099-01-02')});
 await tick();
 assert.match(delayed.get('autoPredayInlineStatus').textContent,/前日参考 24R/,
  'new selected day renders only its own reference');
 assert.equal(delayed.get('autoPredayInlineRaces').children[3].children.length,12);
 console.log('Owner in-page preday 24R: automatic free load, 12R venue tabs, stale-safe PASS');
})().catch(e=>{console.error(e);process.exitCode=1});