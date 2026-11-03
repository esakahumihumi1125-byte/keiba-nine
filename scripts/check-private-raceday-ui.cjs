/* Private source-only race-day inspection; synthetic DOM and no providers. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-private-console.js','utf8');
const elements=new Map(), requests=[];
function el(id){
 if(!elements.has(id)) elements.set(id,{value:'',disabled:false,textContent:'',files:[],children:[],
   replaceChildren(){this.children=[]},append(c){this.children.push(c)},onclick:null});
 return elements.get(id);
}
const document={getElementById:el,createElement:()=>({className:'',textContent:''})};
const data={raceCount:2,racesWithProviderWithdrawal:1,racesWithUnknownFlags:1,
  racesWithOfficialFinalCheck:0,predictionReady:false,bettingReady:false,
  races:[
    {track:'東京',race:1,providerWithdrawnCount:1,withdrawalFlagUnknownCount:0,
      sourceGoing:'重',sourceGoingUpdateTimeRecorded:true,
      finalRaceReady:false,predictionReady:false,
      officialScratchesVerified:false,officialGoingVerified:false},
    {track:'京都',race:1,providerWithdrawnCount:0,withdrawalFlagUnknownCount:1,
      sourceGoing:'未確認',sourceGoingUpdateTimeRecorded:false,
      finalRaceReady:false,predictionReady:false,
      officialScratchesVerified:false,officialGoingVerified:false}
]};
async function mockFetch(path,opts={}){
 requests.push({path,opts});
 if(path==='/api/status') return {ok:true,json:async()=>({
  jrdbConfigured:true,historyConfigured:false})};
 if(path==='/api/jrdb/race-day?date=20261107')
   return {ok:true,json:async()=>data};
 throw Error('Unexpected URL '+path);
}
vm.runInNewContext(js,{document,fetch:mockFetch,Date,JSON,encodeURIComponent,console});
function tick(){return new Promise(resolve=>setImmediate(resolve))}
(async()=>{
 await tick();await tick();
 assert.equal(requests.length,1,'no automatic source queries');
 assert.equal(el('raceday').disabled,false);
 assert.equal(typeof el('raceday').onclick,'function');
 assert.equal(el('history').disabled,true,'paid past lookup remains separately disabled');
 el('date').value='2026-11-07';
 await el('raceday').onclick();
 assert.equal(requests.length,2);
 assert.equal(requests[1].path,'/api/jrdb/race-day?date=20261107');
 assert.equal(requests[1].opts.credentials,'same-origin');
 assert.equal(requests[1].opts.headers['X-Keiba-Request'],'private');
 assert.match(el('message').textContent,/JRA公式での最終確認：全R未完了/);
 assert.equal(el('races').children.length,2);
 assert.match(el('races').children[0].textContent,/取消報告 1頭/);
 assert.match(el('races').children[0].textContent,/馬場 重/);
 assert.match(el('races').children[1].textContent,/フラグ不明 1頭/);
 assert.match(el('races').children[1].textContent,/公式の取消・馬場・発走時刻：未確認/);
 assert.equal(el('raceday').disabled,false);
 assert.ok(!js.includes('innerHTML'));
 console.log('Race-day private source check: 15 assertions passed');
})().catch(e=>{console.error(e);process.exitCode=1});
