'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-owner-preday-forecast.js','utf8');
const KEY='keiba-nine-owner-preday-analysis-v1';
class TestDate extends Date {constructor(...args){super(...(args.length?args:['2026-11-07T01:00:00Z']));}static now(){return Date.parse('2026-11-07T01:00:00Z');}}
const data=()=>({schema:'keiba-nine-private-preday-review-v1',date:'2026-11-07',
 races:['東京','京都','福島'].flatMap(track=>Array.from({length:12},(_,i)=>({
  track,race:i+1,time:'12:00',course:'芝1400',field:9,
  rank:[1,2,3,4,5,6,7],first:[1,2],second:[1,2,3,4],
  third:[1,2,3,4,5,6,7],points:30,
  confidence:3,status:'買い候補',headNames:['架空A','架空B'],note:'仮',
  provisional:true,jraOfficialConfirmed:false,fullFactorVerified:false
 })))}); 
function boot(serverReady=false){
 const nodes=new Map(),store=new Map([['other','preserved']]),writes=[],calls=[];
 const node=()=>({textContent:'',value:'',files:[],children:[],checked:false,
  onclick:null,onchange:null,setAttribute(k,v){this[k]=v},append(...a){this.children.push(...a)},
  replaceChildren(...a){this.children=[...a]}});
 const $=id=>{if(!nodes.has(id))nodes.set(id,node());return nodes.get(id)};
 vm.runInNewContext(js,{document:{getElementById:$,createElement:node},
  Date:TestDate,JSON,Set,Map,Number,String,Error,URLSearchParams,console,
  navigator:{clipboard:{writeText:async()=>{}}},
  fetch:async(url,options)=>{
   calls.push({url,options});
   const signed=(track,race,decision,signature)=>({
    snapshot:{date:'2026-11-07',track,race,decision,
     lockedAt:'2026-11-07T09:00:00+09:00',
     scheduledOffAt:'2026-11-07T12:00:00+09:00',
     first:[1,2],second:[1,2,3,4],third:[1,2,3,4,5,6,7],
     points:30,sourceKind:'owner-private-prestart-reference',
     actualPurchase:false,officialScheduleVerified:false,
     formalPredictionVerified:false},
    signature:signature.repeat(64)});
   if(url.startsWith('/api/jra/advance-programme?')){
    const races=['東京','京都','福島'].flatMap(track=>
     Array.from({length:12},(_,i)=>({
      track,race:i+1,postTime:'12:00',distanceM:1400,surface:'芝'})));
    return {ok:true,json:async()=>({
     version:'owner-jra-advance-programme-reference-1',
     date:'2026-11-07',
     referenceKind:'advance_schedule_not_final_racecard',
     raceCount:36,venueCount:3,races,
     officialFinalCardVerified:false,officialStartersVerified:false,
     officialScratchesVerified:false,officialGoingVerified:false,
     officialPostTimeVerified:false,predictionReady:false,bettingReady:false,
     newJrdbRequests:0,existingTicketsChanged:false,
     existingReceiptsChanged:false
    })};
   }
   if(url==='/api/owner-decision-freeze'){
    return {ok:true,json:async()=>({
     schema:'keiba-nine-owner-decision-receipt-v1',date:'2026-11-07',
     captures:[signed('東京',1,'買い候補','a'),
               signed('京都',2,'見送り','b')],
     capturedRaces:2,skippedStartedRaces:34,
     actualPurchase:false,officialScheduleVerified:false,
     resultsVerified:false
    })};
   }
   if(url==='/api/owner-decision-verify'){
    const captured=JSON.parse(options.body).captures;
    if(captured.some(x=>!['a'.repeat(64),'b'.repeat(64)].includes(x.signature)))
     return {ok:false,json:async()=>({error:'tampered'})};
    return {ok:true,json:async()=>({
     schema:'keiba-nine-owner-decision-receipt-v1',
     date:'2026-11-07',captures:captured,captureCount:captured.length,
     verified:true,actualPurchase:false,officialScheduleVerified:false,
     officialResultsVerified:false
    })};
   }
   return {ok:true,json:async()=>url==='/api/owner-race-evidence'?(serverReady?{
    available:true,evidence:{schema:'keiba-nine-private-evidence-v1',date:'2026-11-07',
     sourceKind:'owner-editorial-limited-evidence',finalVerified:false,predictionRevised:false,
     races:['東京','京都','福島'].flatMap(track=>Array.from({length:12},(_,i)=>({track,race:i+1,
      lead:[{number:1,name:'架空A',reason:'事前の参考候補。'}],
      pace:'先行の仮説。',secondThird:'相手候補を比較。',singles:'削減の検証。',
      risk:'当日確認が必要。',verifiedFacts:[],coverage:{officialPastRuns:false,
       publicTrainingChecked:false,officialPedigreeChecked:false,officialEntryCompared:false,
       allHorseTrainingChecked:false,dayOfScratchesAndTrackChecked:false}})))}
   }:{available:false,evidence:null}):url==='/api/owner-live-notes'?(serverReady?{
    available:true,notes:{date:'2026-11-07',sourceKind:'owner-edited-live-brief',
     officialJraVerified:false,predictionReady:false,races:[{track:'東京',race:1,
      time:'12:00',observedAt:'11:45',ground:'稍重',paddock:[5,6],note:'試験用の短い観察メモ'}]}
   }:{available:false,notes:null}):(serverReady?{
    available:true,forecast:{...data(),sourceKind:'owner-private-authored-preday',
      predictionReady:false,officialJraVerified:false,purchased:false,raceCount:36}
   }:{available:false,forecast:null})};
  },
  localStorage:{getItem:k=>store.get(k)||null,
   setItem(k,v){writes.push(k);store.set(k,v)},
   removeItem(k){writes.push('remove:'+k);store.delete(k)}},
  confirm:()=>true});
 return {$,store,writes,calls};
}
async function tick(){await new Promise(resolve=>setImmediate(resolve));}
(async()=>{
 const server=boot(true),se=server.$;
 await tick();
 assert.equal(se('fpRaces').children.length,1,'show only one R by default');
 const firstCard=se('fpRaces').children[0];
 const alternative=firstCard.children.find(x=>x.className==='selective');
 assert.ok(alternative,'an alternative selective individual-ticket view appears');
 assert.match(alternative.children[0].textContent,/10点/);
 assert.equal(alternative.children[2].children.length,10,'10 distinct single tickets');
 const tickets=alternative.children[2].children.map(x=>x.textContent);
 assert.equal(new Set(tickets).size,10,'alternative ticket list has no duplicates');
 for(const ticket of tickets){
  const numbers=ticket.split(' → ').map(Number);
  assert.ok([1,2].includes(numbers[0])&&[1,2,3,4].includes(numbers[1])
    &&[1,2,3,4,5,6,7].includes(numbers[2]),'singles are part of formation');
  assert.equal(new Set(numbers).size,3,'three horses are distinct');
 }
 assert.equal(server.writes.length,0,'alternative is read-only');
 assert.equal(se('fpVenueTabs').children.length,3,'three venue tabs appear');
 assert.equal(se('fpRaceTabs').children.length,12,'12 race buttons appear');
 assert.equal(server.writes.length,0,'server auto-read does not overwrite local storage');
 assert.equal(server.calls.length,3,'forecast, private live brief and evidence requests on startup');
 assert.equal(se('fpJraAdvanceStatus').textContent,
  '未実行。最終出走・馬場は未確認。');
 assert.equal(server.calls.some(x=>x.url.startsWith('/api/jra/advance-programme?')),false,
  'never fetch JRA advance programme automatically');
 await se('fpJraAdvance').onclick();await tick();
 assert.match(se('fpJraAdvanceStatus').textContent,/事前番組の候補一致36／36R/);
 assert.match(se('fpJraAdvanceStatus').textContent,/最終出走・取消・馬場は未確認/);
 assert.equal(se('fpJraAdvanceDetails').children.length,36);
 assert.ok(server.calls.some(x=>x.url==='/api/jra/advance-programme?date=2026-11-07'));
 assert.equal(server.writes.length,0,'one public reference read never mutates tickets or frozen records');

 assert.equal(server.calls[2].url,'/api/owner-race-evidence');
 assert.equal(server.calls[2].options.headers['X-Keiba-Request'],'private');
 assert.ok(se('fpRaces').children[0].children.some(x=>x.className==='race-evidence'));
 assert.equal(server.writes.length,0,'evidence is not written to purchase storage');
 assert.equal(server.calls[1].url,'/api/owner-live-notes');
 assert.equal(server.calls[1].options.headers['X-Keiba-Request'],'private');
 assert.equal(se('fpRaces').children[0].children.some(x=>x.className==='live-brief'),true,
  'only matching private prestart note shown on selected race');
 assert.equal(server.calls[0].url,'/api/owner-preday-forecast');
 assert.equal(server.calls[0].options.headers['X-Keiba-Request'],'private');
 assert.match(se('fpCloudStatus').textContent,/自動表示/);
 se('fpVenueTabs').children[2].onclick();
 assert.match(se('fpSummary').textContent,/福島/);
 assert.equal(se('fpRaces').children.length,1,'tab switches venue');
 se('fpRaceTabs').children[5].onclick();
 assert.match(se('fpSummary').textContent,/6R/);
 assert.equal(se('fpRaces').children.length,1,'single 6R selected');
 se('fpShowAll').onclick();
 assert.equal(se('fpRaces').children.length,12,'show full venue on demand');
 se('fpDelete').onclick();await tick();
 assert.equal(se('fpRaces').children.length,12,'deleting local upload leaves server forecast visible');
 const b=boot(),el=b.$;
 assert.equal(b.writes.length,0);
 const source=JSON.stringify(data());
 el('fpFile').files=[{size:source.length,text:async()=>source}];
 await el('fpImport').onclick();
 assert.equal(el('fpRaces').children.length,1);
 assert.equal(el('fpVenueTabs').children.length,3);
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
 el('fpVenueTabs').children[1].onclick();
 assert.match(el('fpSummary').textContent,/京都/);
 assert.equal(el('fpRaces').children.length,1);
 el('fpShowAll').onclick();
 assert.equal(el('fpRaces').children.length,12);
 el('fpDelete').onclick();
 assert.equal(b.store.has(KEY),false);
 assert.equal(b.store.get('other'),'preserved');
 const freeze=boot(true),fz=freeze.$;
 await tick();
 assert.equal(freeze.writes.length,0,'no implicit prestart decision storage');
 assert.equal(freeze.calls.filter(x=>x.url.includes('decision-')).length,0,
  'no automatic signature request on load');
 await fz('fpFreezeAll').onclick();await tick();
 const prefix='arc-race-owner-decision-capture-v1:2026-11-07';
 const sealed=JSON.parse(freeze.store.get(prefix));
 assert.equal(sealed.length,2,'only server-signed eligible 2 races are retained');
 assert.equal(sealed[0].snapshot.decision,'買い候補');
 assert.equal(sealed[1].snapshot.decision,'見送り');
 assert.equal(sealed[1].snapshot.race,2);
 assert.match(fz('fpFreezeAllStatus').textContent,/買い候補1R・見送り1R/);
 assert.equal(freeze.store.get('other'),'preserved');
 assert.equal(freeze.writes.length,1,'single date-scoped local write');
 assert.ok(freeze.calls.some(x=>x.url==='/api/owner-decision-freeze'&&
  x.options.method==='POST'&&
  x.options.headers['X-Keiba-Request']==='private'));
 assert.ok(freeze.calls.some(x=>x.url==='/api/owner-decision-verify'));
 await fz('fpFreezeAll').onclick();await tick();
 assert.equal(freeze.writes.length,2,'repeat does not add or overwrite decisions');
 assert.equal(freeze.store.get(prefix),JSON.stringify(sealed),
  'original signed records must be byte-for-byte unchanged');
 const corrupted=JSON.parse(JSON.stringify(sealed));
 corrupted[0].signature='c'.repeat(64);
 freeze.store.set(prefix,JSON.stringify(corrupted));
 const before=freeze.writes.length;
 await fz('fpFreezeAll').onclick();await tick();
 assert.equal(freeze.writes.length,before,
  'unverified existing record cannot be overwritten');
 assert.equal(freeze.store.get(prefix),JSON.stringify(corrupted),
  'bad existing data preserved for recovery, not overwritten');
 assert.match(fz('fpFreezeAllStatus').textContent,/失敗/);
 assert.equal(fz('fpFreezeAll').disabled,false);
 console.log('Owner provisional 36R private forecast file import and safety PASS');
})().catch(e=>{console.error(e);process.exitCode=1});