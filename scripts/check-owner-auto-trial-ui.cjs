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
function mock(connected=true,result=payload,hash='',deferTrial=false){
 const nodes=new Map(),fetches=[],navigations=[],stored=new Map();
 let resumeTrial=null;
 const sessionStorage={getItem:k=>stored.get(k)||null,setItem:(k,v)=>stored.set(k,v),removeItem:k=>stored.delete(k)};
 function element(){
  return {value:'',textContent:'',disabled:false,children:[],onchange:null,onclick:null,
    className:'',append(...nodes){this.children.push(...nodes)},
    replaceChildren(...nodes){this.children=[...nodes]}};
 }
 function el(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);}
 const respond=(data,ok=true)=>({ok,json:async()=>data});
 const fetch=async(url,opts)=>{
  fetches.push([url,opts]);
  if(url==='/api/status')return respond({jrdbConfigured:connected});
  if(deferTrial)return new Promise(resolve=>{resumeTrial=()=>resolve(respond(result));});
  return respond(result);
 };
 vm.runInNewContext(src,{document:{getElementById:el,createElement:element},
  window:{location:{hash,assign:url=>navigations.push(url)}},
  sessionStorage,confirm:()=>true,Date,JSON,Set,Number,String,Error,URLSearchParams,fetch});
 return {el,fetches,navigations,stored,finish:()=>{if(!resumeTrial)throw Error('No pending trial');resumeTrial();}};
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
 const slow=mock(true,payload,'',true),sl=slow.el;
 await tick();
 sl('trialDate').value=date;sl('trialDate').onchange();
 sl('trialTrack').value='東京';sl('trialTrack').onchange();
 sl('trialRace').value='1';sl('trialRace').onchange();
 const pending=sl('trialRun').onclick();
 assert.equal(sl('trialRun').disabled,true);
 await sl('trialRun').onclick();
 assert.equal(slow.fetches.length,2,'one status and one research request');
 slow.finish();await pending;await tick();
 assert.equal(sl('trialRows').children.length,2);
 assert.equal(sl('trialRun').disabled,false);
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
 // Even a provider-shaped result must not be shown with incorrect scoring,
 // skipped tie ranks, reordered ties or inflated provisional totals.
 async function tryReply(result){
  const m=mock(true,result),x=m.el;
  await tick();
  x('trialDate').value=date;x('trialDate').onchange();
  x('trialTrack').value='東京';x('trialTrack').onchange();
  x('trialRace').value='1';x('trialRace').onchange();
  await x('trialRun').onclick();await tick();
  return {m,x};
 }
 const tieFixture={...payload,runnersObserved:3,twoFactorComparable:3,ungraded:0,runners:[
  {horseNumber:1,trainingGrade:'S',recentGrade:'A',twoFactorPoints:7,comparisonRank:1,provisionalOnly:true},
  {horseNumber:2,trainingGrade:'A',recentGrade:'S',twoFactorPoints:7,comparisonRank:1,provisionalOnly:true},
  {horseNumber:3,trainingGrade:'B',recentGrade:'B',twoFactorPoints:4,comparisonRank:3,provisionalOnly:true},
 ]};
 const validTie=await tryReply(tieFixture);
 assert.equal(validTie.x('trialRows').children.length,3,'1,1,3 is a valid documented comparison tie');
 for(const [title,bad] of [
  ['wrong points',{...payload,runners:[{...payload.runners[0],twoFactorPoints:8},payload.runners[1]]}],
  ['inflated rank',{...payload,runners:[{...payload.runners[0],comparisonRank:2},payload.runners[1]]}],
  ['incorrect tie rank',{...tieFixture,runners:[
    tieFixture.runners[0],{...tieFixture.runners[1],comparisonRank:2},tieFixture.runners[2]]}],
  ['gap after tie',{...tieFixture,runners:[
    tieFixture.runners[0],tieFixture.runners[1],{...tieFixture.runners[2],comparisonRank:2}]}],
  ['reordered tied horses',{...tieFixture,runners:[
    tieFixture.runners[1],tieFixture.runners[0],tieFixture.runners[2]]}],
  ['repeated horse number',{...tieFixture,runners:[
    tieFixture.runners[0],tieFixture.runners[1],{...tieFixture.runners[2],horseNumber:2}]}],
 ]){
  const check=await tryReply(bad);
  assert.match(check.x('trialStatus').textContent,/試算できません/,title);
  assert.equal(check.x('trialRows').children.length,0,title+' never renders runners');
  assert.equal(check.x('trialGradeHandoff').disabled,true,title+' never transfers grades');
  assert.equal(check.m.navigations.length,0);
  assert.equal(check.m.stored.size,0);
 }
 const jump=mock(true,payload,'#select=v1&date=2026-11-07&track=%E6%9D%B1%E4%BA%AC&race=8');
 const je=jump.el;await tick();
 assert.equal(je('trialDate').value,'2026-11-07');
 assert.equal(je('trialTrack').value,'東京');
 assert.equal(je('trialRace').value,'8');
 assert.equal(jump.fetches.length,1,'36R navigation must not automatically fetch JRDB data');
 const badJump=mock(true,payload,'#select=v1&date=2026-11-07&track=%E6%9D%B1%E4%BA%AC&race=8&token=secret');
 await tick();
 assert.equal(badJump.el('trialTrack').value,'','fragment with extra data ignored');
 const sample3={...payload,runnersObserved:3,twoFactorComparable:1,ungraded:2,runners:[
  ...payload.runners,
  {horseNumber:4,trainingGrade:'B',recentGrade:'未評価',twoFactorPoints:null,comparisonRank:null,provisionalOnly:true},
 ]};
 const forward=mock(true,sample3),fe=forward.el;
 await tick();
 fe('trialDate').value=date;fe('trialDate').onchange();
 fe('trialTrack').value='東京';fe('trialTrack').onchange();
 fe('trialRace').value='1';fe('trialRace').onchange();
 await fe('trialRun').onclick();await tick();
 assert.equal(fe('trialGradeHandoff').disabled,false,'3 horses with provisional factors allow operator prefill');
 assert.equal(forward.navigations.length,0,'no navigation without the user pressing the transfer button');
 fe('trialGradeHandoff').onclick();
 assert.equal(forward.navigations[0],'/my-scorecard#research=v1');
 const payloadRaw=JSON.parse(forward.stored.get('keiba-nine-owner-research-scorecard-handoff-v1'));
 assert.equal(payloadRaw.version,'jrdb-research-to-scorecard-v1');
 assert.equal(payloadRaw.researchOnly,true);
 assert.equal(payloadRaw.predictionReady,false);
 assert.equal(payloadRaw.officialJraVerified,false);
 assert.equal(payloadRaw.runners.length,3);
 assert.deepEqual(Array.from(payloadRaw.runners,h=>h.number),[2,3,4]);
 assert.deepEqual(Array.from(payloadRaw.runners,h=>h.recent),['A','未評価','未評価']);
 assert.ok(!JSON.stringify(payloadRaw).includes('twoFactorPoints'),'licensed indices must not transfer');
 assert.ok(!JSON.stringify(payloadRaw).includes('comparisonRank'),'research rank must not transfer');
 assert.ok(!forward.navigations[0].includes('runner'),'no grades in URL fragment');
 fe('trialDate').value='2026-11-08';fe('trialDate').onchange();
 assert.equal(fe('trialGradeHandoff').disabled,true,'changing date invalidates previous factor transfer');
 const ungraded=mock(true,{...sample3,runners:sample3.runners.map(h=>({
  ...h,trainingGrade:'未評価',recentGrade:'未評価',twoFactorPoints:null,comparisonRank:null
 })),twoFactorComparable:0,ungraded:3}),ug=ungraded.el;
 await tick();
 ug('trialDate').value=date;ug('trialDate').onchange();
 ug('trialTrack').value='東京';ug('trialTrack').onchange();
 ug('trialRace').value='1';ug('trialRace').onchange();
 await ug('trialRun').onclick();await tick();
 assert.equal(ug('trialGradeHandoff').disabled,true,'no fabricated grades when provider has no data');
 assert.equal(ungraded.navigations.length,0);
 assert.ok(!src.includes('localStorage'),'never persist provider-derived per-horse data');
 assert.ok(!src.includes('innerHTML'),'no untrusted HTML');
 console.log('JRDB one-race research iPhone pilot: auth readiness, explicit-click, no predictions and no storage PASS');
})().catch(err=>{console.error(err);process.exitCode=1;});
