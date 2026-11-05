/* Safe iPhone day-pipeline flow: mock-only integration, no JRDB or account data. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'), vm=require('node:vm');
const script=fs.readFileSync('/tmp/keiba-jrdb-day-pipeline.js','utf8');
function instance(configured){
 const nodes=new Map(), calls=[];
 const el=id=>{
  if(!nodes.has(id))nodes.set(id,{id,value:'',disabled:id==='run',hidden:id==='report'||id==='review',
   textContent:'',children:[],events:{},
   addEventListener(type,fn){this.events[type]=fn},
   replaceChildren(...children){this.children=children},
   append(...children){this.children.push(...children)},
  });
  return nodes.get(id);
 };
 const document={getElementById:el,createElement(tag){
  return {tag,textContent:'',children:[],className:'',
   append(...children){this.children.push(...children)}};
 }};
 let malformed=false;
 const demo={
  realPredictionReady:false,purchaseReady:false,rawHorseRecordsIncluded:false,
  sourceRequestCount:5,raceCount:2,recordType:'test',
  summary:{matchedEntryCountRaces:2,missingTrainingRecords:0,
   missingLastWeekRecords:0,missingRecentRecords:1},
  races:[
   {track:'東京',race:1,postTimeFromProvider:'10:00',registered:2,expected:2,
    trainingUnaccounted:0,lastWeekUnaccounted:0,recentUnaccounted:1,
    sourceGoingRecorded:true},
   {track:'京都',race:1,postTimeFromProvider:'10:05',registered:1,expected:1,
    trainingUnaccounted:0,lastWeekUnaccounted:0,recentUnaccounted:0,
    sourceGoingRecorded:false}
  ],
  reviewQueue:{version:'private-day-review-1',raceCount:2,
   officialFinalVerified:false,realPredictionReady:false,purchaseReady:false,
   racesWithinTwoHours:2,racesNeedingManualPriorityCheck:2,
   racesPassedPost:0,races:[
    {track:'東京',race:1,reviewPriority:'urgent_manual_check',
     minutesUntilListedPost:20,sourceGoingAgeStatus:'recent_reported',
     realPredictionReady:false,ticketReady:false,independentJraVerified:false,
     blockers:['JRA公式照合待ち']},
    {track:'京都',race:1,reviewPriority:'urgent_manual_check',
     minutesUntilListedPost:25,sourceGoingAgeStatus:'no_going_report',
     realPredictionReady:false,ticketReady:false,independentJraVerified:false,
     blockers:['馬場資料なし']},
   ]}
 };
 async function fetchMock(url,opts){
  calls.push({url,opts});
  if(url==='/api/setup')return {ok:true,json:async()=>({jrdbConfigured:configured})};
  if(url==='/api/jrdb/day-pipeline?date=20261101')
   return {ok:true,json:async()=>malformed?
    {...demo,reviewQueue:{...demo.reviewQueue,realPredictionReady:true}}:demo};
  throw Error('Unexpected network URL '+url);
 }
 const context={document,fetch:fetchMock,Intl,Date,Object,Math,JSON,Array,
                encodeURIComponent,console};
 vm.runInNewContext(script,context);
 return {el,calls,setMalformed:value=>{malformed=value}};
}
async function tick(){
 await new Promise(resolve=>setImmediate(resolve));
 await new Promise(resolve=>setImmediate(resolve));
}
(async()=>{
 const offline=instance(false);
 await tick();
 assert.equal(offline.calls.length,1,'Only local setup checks on initial load');
 assert.equal(offline.calls[0].url,'/api/setup');
 assert.equal(offline.el('run').disabled,true,'Paid fetch cannot start without credentials');
 assert.match(offline.el('state').textContent,/認証情報待ち/);
 assert.equal(offline.el('report').hidden,true);
 const ready=instance(true);
 await tick();
 assert.equal(ready.calls.length,1,'Never fetch JRDB during page load');
 assert.equal(ready.el('run').disabled,false);
 assert.equal(typeof ready.el('run').events.click,'function');
 ready.el('date').value='2026-11-01';
 await ready.el('run').events.click();
 assert.equal(ready.calls.length,2,'One owner click causes one protected API request');
 assert.equal(ready.calls[1].url,'/api/jrdb/day-pipeline?date=20261101');
 assert.equal(ready.calls[1].opts.credentials,'same-origin');
 assert.equal(ready.calls[1].opts.headers['X-Keiba-Request'],'private');
 assert.equal(ready.el('report').hidden,false);
 assert.equal(ready.el('review').hidden,false);
 assert.equal(ready.el('rows').children.length,2);
 assert.equal(ready.el('reviewRows').children.length,2);
 assert.match(ready.el('reviewSummary').textContent,/優先確認 2R/);
 assert.match(ready.el('reviewRows').children[0].children[1].textContent,/直近60分以内の報告/);
 assert.ok(!ready.el('reviewRows').children.some(c=>String(c.textContent).includes('実購入')));
 ready.el('date').value='2026-11-02';
 ready.el('date').events.change();
 assert.equal(ready.el('report').hidden,true,'Previous day must not remain on screen');
 assert.equal(ready.el('reviewRows').children.length,0);
 assert.equal(ready.el('rows').children.length,0);
 ready.el('date').value='2026-11-01';
 ready.setMalformed(true);
 await ready.el('run').events.click();
 assert.equal(ready.el('report').hidden,true,'Forged prediction-ready flags rejected');
 assert.match(ready.el('message').textContent,/安全に表示できません/);
 assert.equal(ready.el('run').disabled,false,'Recover from invalid response');
 assert.ok(!script.includes('localStorage'));
 assert.ok(!script.includes('innerHTML'));
 assert.ok(!script.includes('setInterval'));
 assert.ok(!ready.calls.some(x=>x.url.includes('api_key')));
 console.log('iPhone day pipeline: no automatic JRDB fetch, protected one-click, timing UI, date clearing and forged-response blocking OK');
})().catch(e=>{console.error(e);process.exitCode=1});
