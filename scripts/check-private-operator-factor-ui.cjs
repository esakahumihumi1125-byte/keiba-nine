/* Owner-only manual factor intake UI, all data synthetic and private. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const nodes=new Map(), requests=[];
function el(id){
 if(!nodes.has(id))nodes.set(id,{
   value:'',disabled:false,textContent:'',children:[],files:[],
   append(child){this.children.push(child)},
   replaceChildren(){this.children=[]},onclick:null,onchange:null
 });
 return nodes.get(id);
}
const document={getElementById:el,createElement:()=>({
  className:'',textContent:'',children:[],append(x){this.children.push(x)}
})};
async function mockFetch(url,opts={}){
 requests.push({url,opts});
 if(url==='/api/status')return {ok:true,json:async()=>({
  jrdbConfigured:false,historyConfigured:false,manualComparisonConfigured:false
 })};
 if(url==='/api/operator/factor-note'){
  const data=JSON.parse(opts.body);
  return {ok:true,json:async()=>({
    version:'operator-factor-intake-1',recordType:'operator_factor_note',
    track:data.track,date:data.date,race:data.race,factor:data.factor,
    state:data.state,sourceKind:data.source,submittedByOperator:true,
    saved:false,sourceAuthenticated:false,verifiedBeforePostTime:false,
    jraOfficialFinalVerification:false,grade:'未評価',gradedFactorCount:0,
    predictionReady:false,bettingReady:false
  })};
 }
 throw new Error('Unexpected request: '+url);
}
vm.runInNewContext(js,{document,fetch:mockFetch,Date,JSON,Map,console,encodeURIComponent});
async function tick(){await new Promise(r=>setImmediate(r));await new Promise(r=>setImmediate(r));}
(async()=>{
 await tick();
 assert.deepEqual(requests.map(x=>x.url),['/api/status'],'no automatic paid or operator notes');
 assert.equal(el('load').disabled,true,'JRDB remains disabled');
 assert.equal(el('noteRun').disabled,false,'operator form works without JRDB');
 el('date').value='2026-11-07';
 el('noteTrack').value='東京';
 el('noteRace').value='1';
 el('noteHorse').value='03';
 el('noteFactor').value='training';
 el('noteState').value='noted';
 el('noteSource').value='none';
 await el('noteRun').onclick();
 assert.equal(requests.length,1,'must choose a source when marked noted');
 assert.match(el('noteResult').textContent,/資料の種類を選んでください/);
 el('noteSource').value='operator_observation';
 await el('noteRun').onclick();
 assert.equal(requests.length,2);
 assert.equal(requests[1].url,'/api/operator/factor-note');
 assert.equal(requests[1].opts.method,'POST');
 assert.equal(requests[1].opts.credentials,'same-origin');
 assert.equal(requests[1].opts.headers['X-Keiba-Request'],'private');
 assert.deepEqual(JSON.parse(requests[1].opts.body),{
   recordType:'operator_factor_note',date:'20261107',track:'東京',race:1,
   horseNumber:'03',factor:'training',state:'noted',source:'operator_observation'
 });
 assert.match(el('noteResult').textContent,/入力した項目 1\/10/);
 assert.match(el('noteResult').textContent,/保存なし／能力ランク未評価／公式照合未実施/);
 await el('noteRun').onclick();
 assert.match(el('noteResult').textContent,/入力した項目 1\/10/,'same factor overwrites');
 el('noteFactor').value='recent';
 el('noteState').value='unknown';
 el('noteSource').value='none';
 await el('noteRun').onclick();
 assert.match(el('noteResult').textContent,/入力した項目 2\/10/);
 assert.match(el('noteResult').textContent,/資料を見た 1／未確認 1/);
 el('noteHorse').value='04';
 await el('noteRun').onclick();
 assert.match(el('noteResult').textContent,/入力した項目 1\/10/,'horse scoped');
 assert.equal(el('noteRun').disabled,false);
 assert.ok(!requests.some(x=>x.url.startsWith('/api/jrdb')));
 assert.ok(!js.includes('innerHTML'));
 console.log('Owner manual factor intake: session-only, credential-free, format checks passed');
})().catch(err=>{console.error(err);process.exitCode=1});
