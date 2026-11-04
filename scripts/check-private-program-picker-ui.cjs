/* Owner-only track/race picker: fully synthetic, no paid provider calls. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const nodes=new Map(),requests=[];
function el(id){
 if(!nodes.has(id))nodes.set(id,{
  id,value:'',disabled:(id==='programmeTrack'||id==='programmeRace'),textContent:'',children:[],files:[],
  replaceChildren(...c){this.children=[...c];},append(...c){this.children.push(...c)},
  onclick:null,onchange:null,
 });
 return nodes.get(id);
}
const document={getElementById:el,createElement:tag=>({
 tag,value:'',textContent:'',className:'',children:[],
 replaceChildren(...c){this.children=[...c]},append(...c){this.children.push(...c)}
})};
let failDuplicate=false,failDate=false;
const programme=[
 {track:'東京',race:1,racedate:'20261107',race_name:'架空の東京1',
  programmeOnly:true,horsesVerified:false,post_time:'10:05',
  surface:'芝',distance_m:1600,headcount:8},
 {track:'東京',race:2,racedate:'20261107',race_name:'架空の東京2',
  programmeOnly:true,horsesVerified:false,post_time:'10:35',
  surface:'ダート',distance_m:1400,headcount:9},
 {track:'京都',race:1,racedate:'20261107',race_name:'架空の京都1',
  programmeOnly:true,horsesVerified:false,post_time:'10:00',
  surface:'芝',distance_m:1200,headcount:10},
];
async function mockFetch(url,opts={}){
 requests.push({url,opts});
 if(url==='/api/status')return {ok:true,json:async()=>({jrdbConfigured:true})};
 if(url==='/api/jrdb/program?date=20261107')return {ok:true,json:async()=>({
  programmeOnly:true,
  rows:failDuplicate?[programme[0],programme[0]]:failDate?
   [{...programme[0],racedate:'20261108'}]:programme
 })};
 throw Error('Unexpected request '+url);
}
vm.runInNewContext(js,{document,fetch:mockFetch,Date,JSON,console,encodeURIComponent});
async function tick(){await new Promise(r=>setImmediate(r));await new Promise(r=>setImmediate(r))}
(async()=>{
 await tick();
 assert.equal(requests.length,1,'no JRDB calls without owner click');
 assert.equal(el('load').disabled,false);
 assert.equal(el('programmeTrack').disabled,true);
 assert.equal(el('programmeRace').disabled,true);
 el('date').value='2026-11-07';
 await el('load').onclick();
 assert.equal(requests.length,2);
 assert.equal(requests[1].url,'/api/jrdb/program?date=20261107');
 assert.equal(requests[1].opts.credentials,'same-origin');
 assert.equal(requests[1].opts.headers['X-Keiba-Request'],'private');
 assert.equal(el('programmeTrack').disabled,false);
 assert.deepEqual(el('programmeTrack').children.map(x=>x.value),['','東京','京都']);
 assert.equal(el('programmeRace').disabled,true);
 assert.equal(el('races').children.length,0);
 assert.match(el('message').textContent,/3Rを取得/);
 el('programmeTrack').value='東京';
 el('programmeTrack').onchange();
 assert.deepEqual(el('programmeRace').children.map(x=>x.value),['','1','2']);
 assert.equal(el('programmeRace').disabled,false);
 el('programmeRace').value='2';
 el('programmeRace').onchange();
 assert.match(el('programmeSelected').textContent,/東京2R/);
 assert.match(el('programmeSelected').textContent,/10:35/);
 assert.match(el('programmeSelected').textContent,/取消・近走・調教・JRA公式/);
 assert.match(el('races').children[0].textContent,/3連単：未作成/);
 assert.equal(el('races').children.length,1,'show selected race only, not list of old races');
 el('programmeTrack').value='京都';el('programmeTrack').onchange();
 assert.deepEqual(el('programmeRace').children.map(x=>x.value),['','1']);
 assert.equal(el('races').children.length,0,'old track selection must clear');
 el('programmeRace').value='1';el('programmeRace').onchange();
 assert.match(el('programmeSelected').textContent,/京都1R/);
 el('date').value='2026-11-08';el('date').onchange();
 assert.equal(el('programmeTrack').disabled,true);
 assert.equal(el('programmeRace').disabled,true);
 assert.equal(el('races').children.length,0);
 assert.match(el('message').textContent,/再取得/);
 // Stale dates cannot resurrect the previous selection:
 el('programmeTrack').value='東京';el('programmeRace').value='1';
 el('programmeRace').onchange();
 assert.equal(el('races').children.length,0);
 el('date').value='2026-11-07';
 failDuplicate=true;
 await el('load').onclick();
 assert.equal(el('programmeTrack').disabled,true,'duplicate programme fails closed');
 assert.match(el('message').textContent,/重複したレース情報/);
 failDuplicate=false;failDate=true;
 await el('load').onclick();
 assert.equal(el('programmeTrack').disabled,true,'wrong date fails closed');
 assert.match(el('message').textContent,/正しく照合できません/);
 assert.ok(!requests.some(r=>r.url.includes('api_key=')));
 assert.equal(js.includes('innerHTML'),false,'all race names use textContent');
 console.log('Private date-track-race picker: 30+ safety and selection checks passed');
})().catch(e=>{console.error(e);process.exitCode=1});
