/* Offline mobile race context UI regression, no live JRDB connectivity. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const JS=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const nodes=new Map(), calls=[];
function el(id){
 if(!nodes.has(id))nodes.set(id,{
  id,value:'',disabled:false,textContent:'',files:[],children:[],
  replaceChildren(){this.children=[];},
  append(child){this.children.push(child);},
  onclick:null,onchange:null,
 });
 return nodes.get(id);
}
const doc={getElementById:el,createElement:tag=>({
 tag,className:'',textContent:'',children:[],
 append(child){this.children.push(child)},
 })};
async function fetchMock(url,opts){
 calls.push(url);
 if(url==='/api/status')return {
  ok:true,json:async()=>({jrdbConfigured:true})};
 if(url==='/api/jrdb/context?date=20261107')return {
  ok:true,json:async()=>({
   raceCount:2,courseInfoPresentCount:2,goingAvailableCount:1,
   races:[
    {track:'東京',race:1,surface:'芝',distance_m:1600,turn:'左',going:'不良',
     conditionUpdateRecorded:true,predictionReady:false},
    {track:'京都',race:2,surface:'ダート',distance_m:1800,turn:'右',going:'未確認',
     conditionUpdateRecorded:false,predictionReady:false}
   ]
  })
 };
 throw Error('Unexpected request: '+url);
}
vm.runInNewContext(JS,{document:doc,fetch:fetchMock,Date,console,encodeURIComponent,JSON});
(async()=>{
 await new Promise(resolve=>setImmediate(resolve));
 assert.equal(el('context').disabled,false,'enabled private connection only');
 assert.equal(typeof el('context').onclick,'function');
 el('date').value='2026-11-07';
 await el('context').onclick();
 assert.ok(calls.includes('/api/jrdb/context?date=20261107'));
 assert.match(el('message').textContent,/コース条件取得 2R／馬場状態取得 1R/);
 assert.equal(el('races').children.length,2);
 assert.match(el('races').children[0].textContent,/芝 1600m 左/);
 assert.match(el('races').children[0].textContent,/馬場 不良/);
 assert.match(el('races').children[1].textContent,/馬場 未確認/);
 assert.match(el('races').children[1].textContent,/コース・馬場適性：未評価/);
 assert.equal(el('context').disabled,false);
 assert.ok(!calls.some(url=>url.includes('api_key')));
 console.log('Private race context mobile UI: 10 assertions passed');
})().catch(err=>{console.error(err);process.exitCode=1});
