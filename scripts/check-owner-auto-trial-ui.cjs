/* Local-only iPhone one-race JRDB research pilot UI tests. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('/tmp/keiba-owner-auto-trial.js','utf8');
const date='2026-11-07';
const payload={
 version:'owner-single-race-two-factor-trial-1',date:'20261107',track:'東京',race:1,
 runnersObserved:2,twoFactorComparable:1,ungraded:1,researchOnly:true,
 officialJraVerified:false,overallRankReady:false,predictionReady:false,
 bettingReady:false,autoTicketReady:false,unverifiedFactors:8,
 runners:[
  {horseNumber:2,trainingGrade:'S',recentGrade:'A',twoFactorPoints:7,comparisonRank:1,provisionalOnly:true},
  {horseNumber:3,trainingGrade:'A',recentGrade:'未評価',twoFactorPoints:null,comparisonRank:null,provisionalOnly:true},
 ],warning:'2項目だけの試算、買い目未生成'
};
function mock(connected=true,result=payload){
 const nodes=new Map(),fetches=[];
 function element(){
  return {value:'',textContent:'',disabled:false,children:[],onchange:null,onclick:null,
    className:'',append(...nodes){this.children.push(...nodes)},
    replaceChildren(...nodes){this.children=[...nodes]}};
 }
 function el(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);}
 const respond=(data,ok=true)=>({ok,json:async()=>data});
 const fetch=async(url,opts)=>{
  fetches.push([url,opts]);
  return url==='/api/status'?respond({jrdbConfigured:connected}):respond(result);
 };
 vm.runInNewContext(src,{document:{getElementById:el,createElement:element},
  window:{},Date,JSON,Set,Number,String,Error,URLSearchParams,fetch});
 return {el,fetches};
}
async function tick(){await new Promise(resolve=>setImmediate(resolve));}
(async()=>{
 const demo=mock(),$=demo.el;
 await tick();
 assert.equal(demo.fetches.length,1,'loading the page only checks status, no provider fetch');
 assert.equal(demo.fetches[0][0],'/api/status');
 assert.equal($('trialRace').children.length,12);
 assert.equal($('trialRun').disabled,true,'no track selected');
 $('trialDate').value=date;$('trialDate').onchange();
 $('trialTrack').value='東京';$('trialTrack').onchange();
 $('trialRace').value='1';$('trialRace').onchange();
 assert.equal($('trialRun').disabled,false);
 await $('trialRun').onclick();await tick();
 assert.equal(demo.fetches.length,2,'only a user click fetches the private trial');
 assert.match(demo.fetches[1][0],/^\/api\/jrdb\/one-race-trial\?/);
 const selected=new URLSearchParams(demo.fetches[1][0].split('?')[1]);
 assert.equal(selected.get('date'),'20261107');
 assert.equal(selected.get('track'),'東京');
 assert.equal(selected.get('race'),'1');
 assert.equal(selected.size,3,'horse IDs, credentials and raw source are never in query');
 assert.equal(demo.fetches[1][1].headers['X-Keiba-Request'],'private');
 assert.equal($('trialRows').children.length,2);
 assert.match($('trialRows').children[0].children[0].textContent,/暫定1位｜2番/);
 assert.match($('trialRows').children[1].children[1].textContent,/比較不可/);
 assert.match($('trialSummary').textContent,/買い目は未作成/);
 assert.match($('trialStatus').textContent,/買い目未生成/);
 assert.equal($('trialRun').disabled,false,'safe re-run possible');
 const absent=mock(false),b=absent.el;
 await tick();
 b('trialDate').value=date;b('trialDate').onchange();
 b('trialTrack').value='東京';b('trialTrack').onchange();
 b('trialRace').value='1';b('trialRace').onchange();
 assert.equal(b('trialRun').disabled,true,'beta API missing remains disabled');
 assert.equal(absent.fetches.length,1);
 assert.match(b('trialConnect').textContent,/未設定/);
 const tampered=mock(true,{...payload,predictionReady:true}),c=tampered.el;
 await tick();
 c('trialDate').value=date;c('trialDate').onchange();
 c('trialTrack').value='東京';c('trialTrack').onchange();
 c('trialRace').value='1';c('trialRace').onchange();
 await c('trialRun').onclick();await tick();
 assert.match(c('trialStatus').textContent,/検証できません/);
 assert.equal(c('trialRows').children.length,0,'unsafe data not displayed');
 assert.ok(!src.includes('localStorage'),'never persist provider-derived per-horse data');
 assert.ok(!src.includes('innerHTML'),'no untrusted HTML');
 console.log('JRDB one-race research iPhone pilot: auth readiness, explicit-click, no predictions and no storage PASS');
})().catch(err=>{console.error(err);process.exitCode=1;});
