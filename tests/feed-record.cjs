// Run with node tests/feed-record.cjs. Executes production functions in an isolated storage harness.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8');
const section=(a,b)=>{let start=html.indexOf(a);assert(start>=0,a);let end=html.indexOf(b,start);assert(end>start,b);return html.slice(start,end)};
let checks=0;const ok=(v)=>{assert(v);checks++};
function context(initial={}){
 const storage=new Map(Object.entries(initial));let failKey=null;
 const c={console,Date,Intl,Set,Map,JSON,Number,Math,crypto:require('node:crypto').webcrypto,alert:()=>{},localStorage:{getItem:k=>storage.get(k)??null,setItem:(k,v)=>{if(k===failKey)throw Error('quota');storage.set(k,v)}},document:{getElementById:()=>({value:'',textContent:''})}};c.window=c;
 vm.createContext(c);
 vm.runInContext(`const STORE='keiba_nine_beta23_local_v1';`+section('const R23={forecasts:[],results:[]};','const el=id=>document.getElementById(id);')+section('const id23=','function updateTrio29()')+section('function persist23(){','const getAllRaces=')+section('function adjudicate(f,r){','/* BETA 2.4:')+section('window.saveFeedForecast51=function(r){','window.KEIBA_NINE_23_TEST=')+`\nconst el=()=>({});const render23=()=>{};const getToken25=()=>false;const queueCloud25=()=>{};window.getRaces=()=>R23.forecasts;`,c);
 vm.runInContext(`const K='batch';const TRACKS=new Set(['京都','東京']);const render40=()=>{};`+section('const id40=','function json40(')+section('window.receiveFeed51=function(feed){','window.openFeed51='),c);
 return {c,storage,fail:k=>failKey=k};
}
const tomorrow=new Date(Date.now()+86400000).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
const row={date:tomorrow,track:'京都',race:1,off:'23:59',recordType:'live',status:'final',intent:'購入推奨',first:[1],second:[2],third:[3],trioMode:'ボックス',trioPool:[1,2,3],evidence:{references:['isolated test fixture']}};
const feed={schema:1,generatedAt:new Date(Date.now()-60000).toISOString(),forecasts:[row]};
const {c,storage,fail}=context();
ok(c.receiveFeed51(feed)===1);ok(c.getRaces().length===1);ok(c.receiveFeed51(feed)===0);
ok(c.receiveFeed51({...feed,generatedAt:new Date(Date.now()-30000).toISOString()})===0);ok(c.getRaces().length===1);
for(const change of [{recordType:'test'},{status:'draft'},{date:'2020-01-01'}])ok(c.receiveFeed51({...feed,forecasts:[{...row,...change}]})===0);
for(const forecasts of [[row,row],[{...row,race:2},{...row,race:3,first:[99]}],[{...row,evidence:{references:[]}}]]){assert.throws(()=>c.receiveFeed51({...feed,forecasts}));checks++;ok(c.getRaces().length===1)}
const result={one:1,two:2,three:3,triDividend:1000,trioDividend:500},o=c.adjudicate(c.getRaces()[0],result);ok(o.stake===200&&o.returned===1500&&o.net===1300);
for(const change of [{triDividend:-100},{triDividend:''},{triDividend:null},{triDividend:1.5},{two:1}])ok(c.adjudicate(c.getRaces()[0],{...result,...change})===null);
const changed={...feed,generatedAt:new Date(Date.now()-10000).toISOString(),forecasts:[{...row,third:[4]}]};
fail('keiba_nine_beta23_local_v1');assert.throws(()=>c.receiveFeed51(changed));checks++;ok(c.getRaces().length===1);fail(null);ok(c.receiveFeed51(changed)===1);ok(c.getRaces().length===2);ok(c.receiveFeed51(feed)===0);
for(const broken of ['broken-original',JSON.stringify({schema:9,forecasts:[],results:[]})]){
 const q=context({'keiba_nine_beta23_local_v1':broken});assert.throws(()=>q.c.receiveFeed51(feed));checks++;ok(q.storage.get('keiba_nine_beta23_local_v1')===broken);
}
const q=context({batch:'broken-batch'});assert.throws(()=>q.c.receiveFeed51(feed));checks++;ok(q.storage.get('batch')==='broken-batch');
const old=Array.from({length:3001},(_,i)=>({id:'old'+i,date:'2020-01-01',track:'京都',race:1,recordType:'test',version:i}));const large=context({batch:JSON.stringify({schema:1,forecasts:old})});large.c.receiveFeed51(feed);ok(JSON.parse(large.storage.get('batch')).forecasts.length===3002);
for(const m of html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g))new vm.Script(m[1]);checks++;
ok(fs.readFileSync('index.html','utf8').includes('keiba-nine-beta51-feed-record.html'));ok(html.includes('BETA · 5.5'));
console.log(`${checks} checks passed: feed validation, deduplication, history, storage failures, result calculation, script syntax and entry point.`);
module.exports={context,section};
