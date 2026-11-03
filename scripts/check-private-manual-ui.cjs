/* Owner-only manual reference UI; synthetic DOM with no official/provider traffic. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const nodes=new Map(), requests=[];
function el(id){
 if(!nodes.has(id)) nodes.set(id,{
  value:'',disabled:false,textContent:'',files:[],children:[],
  replaceChildren(){this.children=[];},
  append(node){this.children.push(node);},onclick:null,onchange:null
 });
 return nodes.get(id);
}
const document={getElementById:el,createElement:()=>({className:'',textContent:''})};
let checks=0;
async function mockFetch(path,opts={}){
 requests.push({path,opts});
 if(path==='/api/status')return {ok:true,json:async()=>({
    jrdbConfigured:true,historyConfigured:false,manualComparisonConfigured:true
  })};
 if(path==='/api/jrdb/compare-manual'){
  checks++;
  return {ok:true,json:async()=>({
   predictionReady:false,bettingReady:false,officialJraFinalVerification:false,
   racesCompared:1,racesMissingReference:1,
   races:[{
    track:'東京',race:1,
    differenceCount:checks===1?2:1,
    differenceCategories:{withdrawal:1,jockey:0,going:checks===1?1:0,
      postTime:0,surface:0,roster:0},
    unknownComparisons:4,independentSnapshotAuthenticated:false,
    referenceCollectionFreshnessVerified:false,officialJraFinalVerification:false,
    predictionReady:false,bettingReady:false,
   }]
  })};
 }
 throw Error('Unexpected live request '+path);
}
vm.runInNewContext(js,{document,fetch:mockFetch,Date,JSON,encodeURIComponent,console});
async function settle(){await new Promise(r=>setImmediate(r));await new Promise(r=>setImmediate(r));}
(async()=>{
 await settle();
 assert.equal(requests.length,1,'must not fetch independent records automatically');
 assert.equal(el('manualCompare').disabled,false);
 assert.equal(el('history').disabled,true,'separate historical integration stays disabled');
 el('date').value='2026-11-07';
 el('manualTrack').value='東京';
 el('manualRace').value='1';
 el('manualTime').value='10:10';
 el('manualSurface').value='芝';
 el('manualGoing').value='重';
 el('manualHorse').value='02';
 el('manualStatus').value='withdrawn';
 await el('manualCompare').onclick();
 assert.equal(requests.length,2,'one click makes one combined request');
 const first=requests[1];
 assert.equal(first.path,'/api/jrdb/compare-manual');
 assert.equal(first.opts.method,'POST');
 assert.equal(first.opts.credentials,'same-origin');
 assert.equal(first.opts.headers['Content-Type'],'application/json');
 assert.equal(first.opts.headers['X-Keiba-Request'],'private');
 const sent=JSON.parse(first.opts.body);
 assert.deepEqual(sent,{
  date:'20261107',source:'operator_transcription',
  races:[{track:'東京',race:1,completeRoster:false,
   postTime:'10:10',going:'重',surface:'芝',
   entries:[{horseNumber:'02',status:'withdrawn',jockeyCode:null}]}]
 });
 assert.match(el('manualMessage').textContent,/差分 2件/);
 assert.match(el('manualMessage').textContent,/取消1件/);
 assert.match(el('manualMessage').textContent,/出所・最新性の独立認証なし/);
 assert.match(el('manualMessage').textContent,/JRA公式の最終確認：未実施/);
 assert.equal(el('manualCompare').disabled,false);
 await el('manualCompare').onclick();
 assert.equal(requests.length,3);
 assert.match(el('manualMessage').textContent,/前回との差分件数 2→1/);
 assert.match(el('manualMessage').textContent,/比較できない項目 4件/);
 assert.ok(!js.includes('innerHTML'));
 console.log('Manual independent-reference iPhone UI: 19 checks passed');
})().catch(err=>{console.error(err);process.exitCode=1});
