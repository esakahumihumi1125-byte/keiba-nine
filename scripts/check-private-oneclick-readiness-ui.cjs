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
const selected=()=>({version:'selected-race-readiness-5',
 date:'20261107',track:'東京',race:1,
 observedEntries:8,expectedRunners:8,entryCountMatchesSource:true,
 trainingUnaccounted:2,lastWeekUnaccounted:8,pastRunUnaccounted:3,
 providerWithdrawnCount:1,withdrawalFlagUnknownCount:0,
 sourceGoing:'重',sourceGoingAgeStatus:'recent_reported',prestartWindow:'within_two_hours',
 factorResearch:{bothGraded:3,trainingOnly:2,recentOnly:1,neither:2,
  sameGrade:1,trainingHigher:1,recentHigher:1,largeDisagreement:1,bothHigh:1,
  remainingFactors:8,experimental:true,predictionReady:false},
 factorMaterials:{pastFourthCorner:{frontObserved:3,backObserved:1,
  mixedObserved:2,insufficient:2},trainingProvisional:5,recentProvisional:4,
  observedFactors:3,verifiedFactorCount:0,unmappedFactors:7,
  paceForecastAvailable:false,overallRankReady:false,predictionReady:false},
 entryMaterials:{
  entryObservations:{sireRecorded:6,maternalSireRecorded:5,
    bothPedigreeRecorded:4,bracketRecorded:8,weightRecorded:8,
    drawAndWeightRecorded:8},
  rotationIntervals:{under14Days:2,days14to55:3,days56plus:1,unknown:2},
  observedFactorSlots:6,unmappedFactors:4,verifiedFactorCount:0,
  pedigreeAptitudeAssessed:false,drawWeightEffectAssessed:false,
  rotationEffectAssessed:false,overallRankReady:false,predictionReady:false
 },
 personnelBodyMaterials:{
  recorded:{jockeyNameRecorded:7,jockeyCodeRecorded:6,trainerNameRecorded:8,
    trainerCodeRecorded:7,bothPersonnelNamesRecorded:7,bodyTypeRecorded:4,
    integrationCodeRecorded:3,anyConformationRecorded:5},
  observedFactorSlots:8,unmappedFactors:2,verifiedFactorCount:0,
  jockeyTrainerPerformanceAssessed:false,bodyConditionAssessed:false,
  raceDayBodyWeightFetched:false,overallRankReady:false,predictionReady:false
 },
 sourceSnapshotNotOfficial:true,independentJraConnected:false,
 officialJraFinalVerification:badSource,gradedFactors:0,predictionReady:false,
 bettingReady:false
});
async function mockFetch(url,opts){
 calls.push({url,opts});
 if(url==='/api/status')return {ok:true,json:async()=>({jrdbConfigured:true})};
 if(url==='/api/jrdb/program?date=20261107')
  return {ok:true,json:async()=>({programmeOnly:true,rows:programme})};
 if(url==='/api/jrdb/selected-readiness?date=20261107&track=%E6%9D%B1%E4%BA%AC&race=1')
  return {ok:true,json:async()=>{
   if(slow)await new Promise(resolve=>{release=resolve});
   return selected();
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
 assert.equal(calls.length,3,'one click makes only one authenticated read');
 assert.deepEqual(calls.slice(2).map(x=>x.url),[
  '/api/jrdb/selected-readiness?date=20261107&track=%E6%9D%B1%E4%BA%AC&race=1'
 ]);
 assert.ok(calls.slice(2).every(x=>x.opts.credentials==='same-origin'));
 assert.ok(calls.slice(2).every(x=>x.opts.headers['X-Keiba-Request']==='private'));
 assert.match(el('programmeReadinessResult').textContent,/実戦予想はまだ作成できません/);
 assert.match(el('programmeReadinessResult').textContent,/調教不足・未対応 2頭／1週前 8頭／近走 3頭/);
 assert.match(el('programmeReadinessResult').textContent,/調教と近走の暫定評価：両方あり 3頭/);
 assert.match(el('programmeReadinessResult').textContent,/評価差が大きい馬 1頭/);
 assert.match(el('programmeReadinessResult').textContent,/勝ち馬候補ではありません/);
 assert.match(el('programmeReadinessResult').textContent,/過去4角位置（展開の材料のみ）：前方観測 3頭/);
 assert.match(el('programmeReadinessResult').textContent,/血統資料：父 6頭／母父 5頭／両方 4頭/);
 assert.match(el('programmeReadinessResult').textContent,/枠・斤量：枠 8頭／斤量 8頭／両方 8頭/);
 assert.match(el('programmeReadinessResult').textContent,/前走間隔：14日未満 2頭／14〜55日 3頭／56日以上 1頭／不明 2頭/);
 assert.match(el('programmeReadinessResult').textContent,/騎手・厩舎資料：騎手名 7頭／騎手コード 6頭／調教師名 8頭/);
 assert.match(el('programmeReadinessResult').textContent,/馬体形状資料：体型コード 4頭／総合コード 3頭／どちらか 5頭/);
 assert.match(el('programmeReadinessResult').textContent,/当日の馬体重・増減は未取得/);
 assert.match(el('programmeReadinessResult').textContent,/残り2項目/);
 assert.match(el('programmeReadinessResult').textContent,/10項目評価：未実施/);
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
