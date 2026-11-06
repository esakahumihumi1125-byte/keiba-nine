/* Synthetic iPhone whole-day research trial: strict read-only, on-click only. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('/tmp/keiba-owner-auto-trial.js','utf8');
const one={
 version:'owner-single-race-two-factor-trial-1',date:'20261107',track:'東京',race:1,
 runnersObserved:2,twoFactorComparable:1,ungraded:1,researchOnly:true,
 officialJraVerified:false,overallRankReady:false,predictionReady:false,
 bettingReady:false,autoTicketReady:false,unverifiedFactors:8,
 runners:[
  {horseNumber:1,trainingGrade:'S',recentGrade:'A',twoFactorPoints:7,comparisonRank:1,provisionalOnly:true},
  {horseNumber:2,trainingGrade:'未評価',recentGrade:'B',twoFactorPoints:null,comparisonRank:null,provisionalOnly:true}
 ],warning:'研究用2項目のみ'
};
const two={...one,track:'京都',race:12,runners:[
 {horseNumber:3,trainingGrade:'A',recentGrade:'S',twoFactorPoints:7,comparisonRank:1,provisionalOnly:true},
 {horseNumber:4,trainingGrade:'A',recentGrade:'未評価',twoFactorPoints:null,comparisonRank:null,provisionalOnly:true}
]};
const coverage=(runners)=>({
 observedRunnerCount:runners.length,verifiedAbilityFactors:0,notOverallGrades:true,
 materialCountByFactor:{
  training:runners.filter(h=>h.trainingGrade!=='未評価').length,
  recent:runners.filter(h=>h.recentGrade!=='未評価').length,
  pace:0,pedigree:0,draw_weight:0,rotation:0,jockey_stable:0,
  body_condition:0,course_distance:0,ground:0
 },
 experimentalFactors:['training','recent'],
 observationOnlyFactors:['pace','pedigree','draw_weight','rotation','jockey_stable','body_condition'],
 uncheckedFactors:['course_distance','ground']
});
one.factorCoverage=coverage(one.runners);
two.factorCoverage=coverage(two.runners);
one.runners[0].pastFourthCornerObservation='frontObserved';
one.runners[1].pastFourthCornerObservation='insufficient';
two.runners[0].pastFourthCornerObservation='backObserved';
two.runners[1].pastFourthCornerObservation='insufficient';
one.factorCoverage.materialCountByFactor.pace=1;
two.factorCoverage.materialCountByFactor.pace=1;
const positionSummary=runners=>({
 categoryCounts:{
  frontObserved:runners.filter(h=>h.pastFourthCornerObservation==='frontObserved').length,
  backObserved:runners.filter(h=>h.pastFourthCornerObservation==='backObserved').length,
  mixedObserved:runners.filter(h=>h.pastFourthCornerObservation==='mixedObserved').length,
  insufficient:runners.filter(h=>h.pastFourthCornerObservation==='insufficient').length,
 },
 researchOnly:true,racePaceForecastAvailable:false,
 minObservedRacesForCategory:2,notRunnerAbilityGrade:true,
});
one.pastFourthCornerSummary=positionSummary(one.runners);
two.pastFourthCornerSummary=positionSummary(two.runners);
one.raceContext={
 surface:'芝',distance_m:1600,turn:'左',going:'重',
 courseInfoPresent:true,goingAvailable:true,
 conditionSnapshotPresent:true,conditionUpdateRecorded:true,
 officialJraVerified:false,horseCourseSuitabilityAssessed:false,
 horseGoingSuitabilityAssessed:false,raceConditionsVerified:false
};
two.raceContext={
 ...one.raceContext,surface:'ダート',distance_m:1800,turn:'右',
 going:'未確認',goingAvailable:false,
 conditionSnapshotPresent:false,conditionUpdateRecorded:false
};
const day={
 version:'owner-day-two-factor-trial-4',date:'20261107',raceCount:2,
 runnerCount:4,twoFactorComparable:2,ungraded:2,
 courseInfoPresentCount:2,goingAvailableCount:1,
 officialJraVerified:false,overallRankReady:false,predictionReady:false,
 bettingReady:false,autoTicketReady:false,researchOnly:true,
 races:[one,two],warning:'実戦予想・買い目未作成'
};
function start(isConfigured=true,reply=day){
 const elements=new Map(),calls=[];
 function element(){
  return {value:'',textContent:'',disabled:false,children:[],className:'',
   append(...r){this.children.push(...r)},replaceChildren(...r){this.children=[...r]},
   onclick:null,onchange:null};
 }
 const el=id=>{if(!elements.has(id))elements.set(id,element());return elements.get(id);};
 const fetch=async(url,options)=>{
  calls.push({url,options});
  if(url==='/api/status')return {ok:true,json:async()=>({jrdbConfigured:isConfigured})};
  if(url.startsWith('/api/jrdb/one-day-trial?'))
   return {ok:true,json:async()=>reply};
  throw Error('Unexpected HTTP request '+url);
 };
 vm.runInNewContext(source,{
  document:{getElementById:el,createElement:element},
  window:{location:{hash:''}},Date,JSON,Set,Number,String,Error,URLSearchParams,fetch,
 });
 return {el,calls};
}
const tick=async()=>new Promise(r=>setImmediate(r));
(async()=>{
 const app=start(),$=app.el;
 await tick();
 assert.equal(app.calls.length,1);
 assert.equal(app.calls[0].url,'/api/status');
 assert.equal($('trialDayRun').disabled,false,'default valid JST day permits date-scoped research when configured');
 $('trialDate').value='2026-11-07';
 $('trialDate').onchange();
 await $('trialDayRun').onclick();await tick();
 assert.equal(app.calls.length,2,'only one explicit click should invoke the full-day service');
 assert.equal(app.calls[1].url,'/api/jrdb/one-day-trial?date=20261107');
 assert.equal(app.calls[1].options.headers['X-Keiba-Request'],'private');
 assert.equal(app.calls[1].options.cache,'no-store');
 assert.match($('trialDaySummary').textContent,/2R・4頭.*比較可能 2頭/);
 assert.match($('trialDaySummary').textContent,/コース資料 2\/2R・提供元馬場 1\/2R/);
 assert.match($('trialDayStatus').textContent,/買い目未作成/);
 assert.equal($('trialDayRaces').children.length,2);
 assert.match($('trialDayRaces').children[0].children[0].textContent,/東京1R/);
 assert.match($('trialDayRaces').children[0].children[0].textContent,/前方複数回 1頭/);
 assert.match($('trialDayRaces').children[1].children[0].textContent,/京都12R/);
 assert.match($('trialDayRaces').children[0].children[2].textContent,/コース 芝 1600m 左/);
 assert.match($('trialDayRaces').children[0].children[2].textContent,/提供元の馬場 重/);
 assert.match($('trialDayRaces').children[0].children[2].textContent,/JRA公式未照合/);
 assert.match($('trialDayRaces').children[1].children[2].textContent,/提供元の馬場 未確認/);
 assert.match($('trialDayRaces').children[0].children[3].children[0].textContent,/10項目の資料記録/);
 assert.equal($('trialDayRaces').children[0].children[3].children.length,11);
 assert.match($('trialDayRaces').children[0].children[4].textContent,/暫定1位/);
 assert.match($('trialDayRaces').children[0].children[4].textContent,/前方での通過を複数回観測/);
 assert.match($('trialDayRaces').children[0].children[4].className,/trial-front/);
 assert.doesNotMatch($('trialDayRaces').children[1].children[4].className,/trial-front/);
 assert.match($('trialDayRaces').children[0].children[5].textContent,/比較順位なし/);
 assert.match($('trialDayRaces').children[0].children[5].textContent,/4角位置の観測不足/);
 assert.match($('trialDayRaces').children[1].children[4].textContent,/後方寄りの通過を観測/);
 assert.equal($('trialDayRun').disabled,false);
 $('trialTrack').value='東京';$('trialTrack').onchange();
 assert.equal($('trialDayRaces').children.length,2,'changing one-race picker does not erase the day snapshot');
 $('trialDate').value='2026-11-08';$('trialDate').onchange();
 assert.equal($('trialDayRaces').children.length,0,'different day clears old results');
 assert.equal($('trialDaySummary').textContent,'');
 assert.equal(app.calls.length,2,'changing date cannot auto-trigger a paid call');
 const missing=start(false),m=missing.el;
 await tick();
 assert.equal(m('trialDayRun').disabled,true,'unissued API keys fail closed');
 m('trialDate').value='2026-11-07';m('trialDate').onchange();
 assert.equal(m('trialDayRun').disabled,true);
 assert.equal(missing.calls.length,1);
 const bad=start(true,{...day,races:[one,{...one}]});
 const b=bad.el;await tick();
 b('trialDate').value='2026-11-07';b('trialDate').onchange();
 await b('trialDayRun').onclick();await tick();
 assert.match(b('trialDayStatus').textContent,/試算できません/);
 assert.equal(b('trialDayRaces').children.length,0,'duplicate race is not partially shown');
 const forged=start(true,{...day,races:[one,{...two,factorCoverage:{
 ...two.factorCoverage,materialCountByFactor:{
 ...two.factorCoverage.materialCountByFactor,
 course_distance:2
 }} }]});
 const fx=forged.el;await tick();
 fx('trialDate').value='2026-11-07';fx('trialDate').onchange();
 await fx('trialDayRun').onclick();await tick();
 assert.equal(fx('trialDayRaces').children.length,0,'unverified course claims rejected');
 const fakePace=start(true,{...day,races:[one,{
  ...two,pastFourthCornerSummary:{...two.pastFourthCornerSummary,
   racePaceForecastAvailable:true}
 }]});
 const fp=fakePace.el;await tick();
 fp('trialDate').value='2026-11-07';fp('trialDate').onchange();
 await fp('trialDayRun').onclick();await tick();
 assert.equal(fp('trialDayRaces').children.length,0,'position data cannot turn into forecast');
 const contradictoryPosition=start(true,{...day,races:[one,{
  ...two,runners:two.runners.map((h,i)=>i?{...h,pastFourthCornerObservation:'frontObserved'}:h)
 }]});
 const cp=contradictoryPosition.el;await tick();
 cp('trialDate').value='2026-11-07';cp('trialDate').onchange();
 await cp('trialDayRun').onclick();await tick();
 assert.equal(cp('trialDayRaces').children.length,0,'per-runner position must match aggregate');
 const fakeGoing=start(true,{...day,races:[one,{...two,raceContext:{...two.raceContext,going:'良'}}]});
 const fg=fakeGoing.el;await tick();
 fg('trialDate').value='2026-11-07';fg('trialDate').onchange();
 await fg('trialDayRun').onclick();await tick();
 assert.equal(fg('trialDayRaces').children.length,0,'missing venue cannot claim good going');
 const fakeJra=start(true,{...day,races:[one,{...two,raceContext:{...two.raceContext,officialJraVerified:true}}]});
 const fj=fakeJra.el;await tick();
 fj('trialDate').value='2026-11-07';fj('trialDate').onchange();
 await fj('trialDayRun').onclick();await tick();
 assert.equal(fj('trialDayRaces').children.length,0,'provider source cannot claim official verification');
 const mixed=start(true,{...day,races:[one,{...two,predictionReady:true}]});
 const x=mixed.el;await tick();
 x('trialDate').value='2026-11-07';x('trialDate').onchange();
 await x('trialDayRun').onclick();await tick();
 assert.equal(x('trialDayRaces').children.length,0,'malformed later R invalidates whole day');
 const empty=start(true,{...day,raceCount:0,races:[],runnerCount:0,twoFactorComparable:0,ungraded:0,courseInfoPresentCount:0,goingAvailableCount:0});
 const e=empty.el;await tick();
 e('trialDate').value='2026-11-07';e('trialDate').onchange();
 await e('trialDayRun').onclick();await tick();
 assert.match(e('trialDaySummary').textContent,/0R・0頭/);
 assert.equal(e('trialDayRaces').children.length,0);
 assert.ok(!source.includes('localStorage'),'no provider derived data persisted to browser');
 assert.ok(!source.includes('innerHTML'),'never inject provider text as HTML');
 console.log('Owner all-day JRDB trial: per-horse historical position, 5-source API, validation, privacy PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
