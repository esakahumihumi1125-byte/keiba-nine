/* Owner one-click race readiness: synthetic, private, no paid provider calls. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const nodes=new Map(), calls=[];
function el(id){
 if(!nodes.has(id))nodes.set(id,{
  id,value:'',disabled:['programmeTrack','programmeRace','programmeReadiness'].includes(id),
  textContent:'',children:[],files:[],
  replaceChildren(...xs){this.children=[...xs]},append(...xs){this.children.push(...xs)},
  onclick:null,onchange:null
 });
 return nodes.get(id);
}
const document={getElementById:el,createElement:tag=>({
 tag,value:'',textContent:'',className:'',children:[],
 replaceChildren(...xs){this.children=[...xs]},append(...xs){this.children.push(...xs)}
})};
const programme=[{racedate:'20261107',track:'東京',race:1,race_name:'架空の検証1R',
 post_time:'10:00',surface:'芝',distance_m:1600,headcount:8,
 programmeOnly:true,horsesVerified:false}];
let badSource=false,slow=false,release=null;
const evidence=()=>({date:'20261107',raceCount:1,predictionReady:false,
 races:[{track:'東京',race:1,observedEntries:8,
  trainingUnaccounted:2,lastWeekUnaccounted:8,pastRunUnaccounted:3}],
 assessmentPreflight:{gradedFactors:0,readyForPrediction:0,races:[
  {track:'東京',race:1,observedEntries:8,gradedFactors:0,readyForPrediction:false}
 ]}
});
const meeting=()=>({date:'20261107',raceCount:1,predictionReady:false,bettingReady:false,
 racesWithOfficialFinalCheck:0,
 races:[{track:'東京',race:1,finalRaceReady:false,predictionReady:false,
  officialScratchesVerified:false,officialGoingVerified:false}],
 independentComparison:{officialJraFinalVerification:false,racesCompared:0,
  races:[{track:'東京',race:1,independentReferenceProvided:false,
   officialJraFinalVerification:badSource,comparisonStatus:'missing_reference'}]},
 prestartFreshness:{officiallyVerifiedRaces:0,
  races:[{track:'東京',race:1,jraOfficialDataFetched:false,
   jraScratchesVerified:false,jraGoingVerified:false,jraPostTimeVerified:false}]}
});
async function mockFetch(url,opts){
 calls.push({url,opts});
 if(url==='/api/status')return {ok:true,json:async()=>({jrdbConfigured:true})};
 if(url==='/api/jrdb/program?date=20261107')
  return {ok:true,json:async()=>({programmeOnly:true,rows:programme})};
 if(url==='/api/jrdb/evidence?date=20261107')
  return {ok:true,json:async()=>evidence()};
 if(url==='/api/jrdb/race-day?date=20261107')
  return {ok:true,json:async()=>{
   if(slow)await new Promise(resolve=>{release=resolve});
   return meeting();
  }};
 throw Error('Unexpected URL '+url);
}
vm.runInNewContext(js,{document,fetch:mockFetch,Date,JSON,console,encodeURIComponent});
async function tick(){await new Promise(r=>setImmediate(r));await new Promise(r=>setImmediate(r))}
(async()=>{
 await tick();
 assert.deepEqual(calls.map(x=>x.url),['/api/status'],'no auto paid reads');
 assert.equal(el('programmeReadiness').disabled,true);
 el('programmeDemo').onclick();
 el('programmeTrack').value='東京';el('programmeTrack').onchange();
 el('programmeRace').value='1';el('programmeRace').onchange();
 assert.equal(el('programmeReadiness').disabled,true,'demo cannot trigger paid checks');
 assert.equal(calls.length,1);
 el('date').value='2026-11-07';el('date').onchange();
 await el('load').onclick();
 el('programmeTrack').value='東京';el('programmeTrack').onchange();
 assert.equal(el('programmeReadiness').disabled,true,'needs a selected race');
 el('programmeRace').value='1';el('programmeRace').onchange();
 assert.equal(el('programmeReadiness').disabled,false);
 await el('programmeReadiness').onclick();
 assert.equal(calls.length,4);
 assert.deepEqual(calls.slice(2).map(x=>x.url),[
  '/api/jrdb/evidence?date=20261107','/api/jrdb/race-day?date=20261107'
 ]);
 assert.ok(calls.slice(2).every(x=>x.opts.credentials==='same-origin'));
 assert.ok(calls.slice(2).every(x=>x.opts.headers['X-Keiba-Request']==='private'));
 assert.match(el('programmeReadinessResult').textContent,/実戦予想はまだ作成できません/);
 assert.match(el('programmeReadinessResult').textContent,/調教不足・未対応 2頭／1週前 8頭／近走 3頭/);
 assert.match(el('programmeReadinessResult').textContent,/10項目評価：全項目未評価/);
 assert.match(el('programmeReadinessResult').textContent,/独立したJRAデータ取得：未接続/);
 assert.equal(el('programmeReadiness').disabled,false,'re-enabled for manual retry');
 el('programmeRace').value='';el('programmeRace').onchange();
 assert.equal(el('programmeReadiness').disabled,true);
 assert.doesNotMatch(el('programmeReadinessResult').textContent,/調教不足・未対応 2頭/);
 // Untrusted source must never upgrade readiness to confirmed.
 el('programmeRace').value='1';el('programmeRace').onchange();
 badSource=true;
 await el('programmeReadiness').onclick();
 assert.match(el('programmeReadinessResult').textContent,/資料を照合できません/);
 assert.doesNotMatch(el('programmeReadinessResult').textContent,/10項目評価：全項目未評価/);
 badSource=false;
 // A request racing with day selection is discarded, not displayed to wrong race.
 slow=true;
 const pending=el('programmeReadiness').onclick();
 await tick();
 assert.equal(el('programmeReadiness').disabled,true);
 assert.equal(typeof release,'function');
 el('date').value='2026-11-08';el('date').onchange();
 release();
 await pending;
 assert.equal(el('programmeReadiness').disabled,true);
 assert.doesNotMatch(el('programmeReadinessResult').textContent,/調教不足・未対応 2頭/);
 assert.equal(el('races').children.length,0);
 assert.equal(js.includes('innerHTML'),false,'source text cannot be HTML');
 assert.ok(!calls.some(x=>x.url.includes('api_key')||x.url.includes('history')));
 console.log('One-click source readiness: manual-only, fail-closed, stale-result-safe checks passed');
})().catch(err=>{console.error(err);process.exitCode=1});
