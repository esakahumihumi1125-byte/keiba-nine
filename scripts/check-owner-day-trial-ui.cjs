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
const day={
 version:'owner-day-two-factor-trial-1',date:'20261107',raceCount:2,
 runnerCount:4,twoFactorComparable:2,ungraded:2,
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
 assert.match($('trialDayStatus').textContent,/買い目未作成/);
 assert.equal($('trialDayRaces').children.length,2);
 assert.match($('trialDayRaces').children[0].children[0].textContent,/東京1R/);
 assert.match($('trialDayRaces').children[1].children[0].textContent,/京都12R/);
 assert.match($('trialDayRaces').children[0].children[2].textContent,/暫定1位/);
 assert.match($('trialDayRaces').children[0].children[3].textContent,/比較順位なし/);
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
 const mixed=start(true,{...day,races:[one,{...two,predictionReady:true}]});
 const x=mixed.el;await tick();
 x('trialDate').value='2026-11-07';x('trialDate').onchange();
 await x('trialDayRun').onclick();await tick();
 assert.equal(x('trialDayRaces').children.length,0,'malformed later R invalidates whole day');
 const empty=start(true,{...day,raceCount:0,races:[],runnerCount:0,twoFactorComparable:0,ungraded:0});
 const e=empty.el;await tick();
 e('trialDate').value='2026-11-07';e('trialDate').onchange();
 await e('trialDayRun').onclick();await tick();
 assert.match(e('trialDaySummary').textContent,/0R・0頭/);
 assert.equal(e('trialDayRaces').children.length,0);
 assert.ok(!source.includes('localStorage'),'no provider derived data persisted to browser');
 assert.ok(!source.includes('innerHTML'),'never inject provider text as HTML');
 console.log('Owner all-day JRDB trial: one-click 4-source API, full validation, date reset, privacy PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
