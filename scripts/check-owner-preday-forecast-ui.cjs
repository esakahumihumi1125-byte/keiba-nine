'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-owner-preday-forecast.js','utf8');
const KEY='keiba-nine-owner-preday-analysis-v1';
const data=()=>({schema:'keiba-nine-private-preday-review-v1',date:'2026-11-07',
 races:['東京','京都','福島'].flatMap(track=>Array.from({length:12},(_,i)=>({
  track,race:i+1,time:'12:00',course:'芝1400',field:9,
  rank:[1,2,3,4,5,6,7],first:[1,2],second:[1,2,3,4],
  third:[1,2,3,4,5,6,7],points:30,
  confidence:3,status:'買い候補',headNames:['架空A','架空B'],note:'仮',
  provisional:true,jraOfficialConfirmed:false,fullFactorVerified:false
 })))}); 
function boot(){
 const nodes=new Map(),store=new Map([['other','preserved']]),writes=[];
 const node=()=>({textContent:'',value:'',files:[],children:[],checked:false,
  onclick:null,onchange:null,append(...a){this.children.push(...a)},
  replaceChildren(...a){this.children=[...a]}});
 const $=id=>{if(!nodes.has(id))nodes.set(id,node());return nodes.get(id)};
 vm.runInNewContext(js,{document:{getElementById:$,createElement:node},
  Date,JSON,Set,Map,Number,String,Error,URLSearchParams,console,
  navigator:{clipboard:{writeText:async()=>{}}},
  localStorage:{getItem:k=>store.get(k)||null,
   setItem(k,v){writes.push(k);store.set(k,v)},
   removeItem(k){writes.push('remove:'+k);store.delete(k)}},
  confirm:()=>true});
 return {$,store,writes};
}
(async()=>{
 const b=boot(),el=b.$;
 assert.equal(b.writes.length,0);
 const source=JSON.stringify(data());
 el('fpFile').files=[{size:source.length,text:async()=>source}];
 await el('fpImport').onclick();
 assert.equal(el('fpRaces').children.length,36);
 assert.equal(b.writes.length,1);
 assert.equal(b.writes[0],KEY);
 assert.equal(JSON.parse(b.store.get(KEY)).races.length,36);
 assert.equal(b.store.get('other'),'preserved');
 const bad=data();bad.races[0].points=31;
 const reject=boot(),re=reject.$,raw=JSON.stringify(bad);
 re('fpFile').files=[{size:raw.length,text:async()=>raw}];
 await re('fpImport').onclick();
 assert.equal(reject.writes.length,0);
 assert.match(re('fpStatus').textContent,/取り込めません/);
 const fake=data();fake.races[0].jraOfficialConfirmed=true;
 const unsafe=boot(),un=unsafe.$,wrong=JSON.stringify(fake);
 un('fpFile').files=[{size:wrong.length,text:async()=>wrong}];
 await un('fpImport').onclick();
 assert.equal(unsafe.writes.length,0);
 el('fpTrack').value='京都';el('fpTrack').onchange();
 assert.equal(el('fpRaces').children.length,12);
 el('fpDelete').onclick();
 assert.equal(b.store.has(KEY),false);
 assert.equal(b.store.get('other'),'preserved');
 console.log('Owner provisional 36R private forecast file import and safety PASS');
})().catch(e=>{console.error(e);process.exitCode=1});