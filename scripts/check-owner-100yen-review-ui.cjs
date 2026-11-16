/* Synthetic browser test: date-aware read-only 100-yen review. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-100yen-review.js','utf8');
function boot(query,reviewFixture=null,provisionalFixture=null,archiveFixture=null,
 jraResultFixture=null,receiptVerifyFixture=null,thjFixture=null,clockISO=null){
 const elements=new Map(),requests=[],storage=new Map();
 let pending=null;
 function node(tag){
  return {tag,children:[],value:'',textContent:'',disabled:false,
    append(...items){this.children.push(...items)},
    replaceChildren(...items){this.children=items},
  };
 }
 function get(id){
  if(!elements.has(id))elements.set(id,node('div'));
  return elements.get(id);
 }
 const document={visibilityState:'visible',getElementById:get,createElement:node};
 const localStorage={getItem:key=>storage.get(key)||null,
   setItem(){throw Error('Read-only dashboard wrote storage')},
   removeItem(){throw Error('Read-only dashboard deleted storage')}};
 const fetch=async(url,opts)=>{
  requests.push({url,opts});
  const wait=pending;pending=null;
  if(wait)await wait;
  if(url.startsWith('/api/jra/result-candidate?'))return {
    ok:!!jraResultFixture,json:async()=>jraResultFixture||{error:'not found'}
   };
  if(url.startsWith('/api/owner-100yen-archived'))return {
    ok:true,json:async()=>({archiveEnabled:false,available:false})
  };
  if(url==='/api/owner-100yen-verify-receipts')return {
    ok:!!receiptVerifyFixture,
    json:async()=>receiptVerifyFixture||{error:'unverified'}
  };
  if(url.startsWith('/api/owner-100yen-review'))return {
    ok:true,json:async()=>({available:!!reviewFixture,review:reviewFixture})
  };
  if(url.startsWith('/api/owner-archive-read'))return {
    ok:true,json:async()=>archiveFixture||{
     archiveEnabled:false,persistentStorageReady:false,available:false,receipts:[]
    }
  };
  if(url==='/api/owner-prestart-tse-review')return {
    ok:true,json:async()=>provisionalFixture
  };
  if(url==='/api/owner-prestart-thj-review')return {
    ok:!!thjFixture,json:async()=>thjFixture||{error:'not ready'}
  };
  throw Error('Unexpected backend request');
 };
 const TestDate=clockISO?class extends Date {
  constructor(...args){super(...(args.length?args:[clockISO]));}
  static now(){return Date.parse(clockISO);}
 }:Date;
 const context={document,localStorage,location:{search:query},fetch,
   Date:TestDate,Intl,JSON,Number,Object,Array,String,RegExp,Set,Map,Error,Promise};
 vm.runInNewContext(js,context);
 return {get,requests,storage,delay:p=>{pending=p}};
}
(async()=>{
 const a=boot('?date=2099-01-02');
 await new Promise(r=>setImmediate(r));
 assert.equal(a.get('day').value,'2099-01-02');
 assert.equal(a.requests.length,2);
 assert.match(a.requests[0].url,/date=2099-01-02$/);
 assert.match(a.requests[1].url,/date=2099-01-02$/);
 assert.match(a.get('status').textContent,/未登録/);
 assert.equal(a.get('load').disabled,false);
 assert.equal(a.storage.size,0);
 // Monday JST: default to Sunday and select either weekend day in one tap.
 // No JRDB/JRA paid lookup, ticket mutation or new purchase is allowed.
 const monday=boot('',null,null,null,null,null,null,'2026-11-15T23:10:00Z');
 await new Promise(r=>setImmediate(r));
 assert.equal(monday.get('day').value,'2026-11-15');
 const mondayReads=monday.requests.length;
 monday.get('recentSaturday').onclick();
 await new Promise(r=>setImmediate(r));
 assert.equal(monday.get('day').value,'2026-11-14');
 assert.equal(monday.requests.length,mondayReads+2);
 assert.ok(monday.requests.slice(mondayReads).every(x=>
  x.url.startsWith('/api/owner-100yen-')));
 monday.get('recentSunday').onclick();
 await new Promise(r=>setImmediate(r));
 assert.equal(monday.get('day').value,'2026-11-15');
 assert.equal(monday.requests.length,mondayReads+4);
 assert.equal(monday.storage.size,0);
 // Saturday JST defaults to Saturday, never a future Sunday.
 const saturday=boot('',null,null,null,null,null,null,'2026-11-20T23:10:00Z');
 await new Promise(r=>setImmediate(r));
 assert.equal(saturday.get('day').value,'2026-11-21');
 // JRA official result candidates are an explicit read-only ONE-race
 // observation: never run automatically or certify a payout/ROI.
 const officialURL='https://www.jra.go.jp/JRADB/accessS.html?'+
  'CNAME=pw01sde0108202605020820261108%2FA0';
 const candidate={
  version:'owner-jra-public-result-probe-1',
  date:'2026-11-08',track:'京都',race:8,
  trifectaCandidates:[{ticket:[7,8,2],payoutYen:26050}],
  trioCandidates:[{ticket:[2,7,8],payoutYen:2320}],
  payoutMatchesDisplayedPodium:true,podiumShape:'single_third_place',
  matchingTrifectaCount:1,matchingTrioCount:1,
  sourceHostAllowlisted:true,visibleRaceIdentityMatched:true,
  payoutLayoutParsed:true,podiumChecked:true,
  officialJraVerified:false,sourceAuthenticityAttested:false,
  finalityVerified:false,refundsVerified:false,settlementReady:false,
  officialRoiPercent:null,actualPurchase:false,researchOnly:true,
  sourceReadCount:1,changesExistingReceipts:false,
  changesExistingRoi:false,
 };
 const observed=boot('?date=2026-11-08',null,null,null,candidate);
 await new Promise(r=>setImmediate(r));
 assert.equal(observed.requests.length,2,
  'result page never auto-queries JRA on opening');
 observed.get('jraResultTrack').value='京都';
 observed.get('jraResultRace').value='8';
 observed.get('jraResultUrl').value=officialURL;
 const before=observed.requests.length;
 await observed.get('jraResultCheck').onclick();
 assert.equal(observed.requests.length,before+2,
  'one explicit JRA public request and one local archive check, no JRDB query');
 assert.equal(observed.requests.filter(x=>
  x.url.startsWith('/api/jra/result-candidate?')).length,1);
 assert.match(observed.requests[3].url,/^\/api\/owner-archive-read\?/);
 assert.match(observed.requests[2].url,/^\/api\/jra\/result-candidate\?/);
 assert.match(observed.requests[2].url,/track=%E4%BA%AC%E9%83%BD/);
 assert.match(observed.requests[2].url,/race=8/);
 assert.equal(observed.requests[2].opts.headers['X-Keiba-Request'],'private');
 assert.equal(observed.get('jraResultCandidates').children.length,4);
 assert.match(observed.get('jraResultCandidates').children.at(-1).textContent,
  /判定保留/);
 assert.match(observed.get('jraResultCandidates').children[1].textContent,
  /3連単 7－8－2：100円あたり 26,050円（候補）/);
 assert.match(observed.get('jraResultStatus').textContent,
  /正式的中・実購入・仮想収支には反映していません/);
 assert.ok(!observed.get('jraResultCandidates').children.some(x=>
  /【未確定・参考計算】/.test(x.textContent)),
  'no verified prestart receipt means no investment/return scenario');
 assert.equal(observed.storage.size,0,'official candidate never writes storage');
 // For a real record, compare only after the existing server endpoint
 // has verified the original prestart HMAC receipt (no paid JRDB calls).
 const chosenReceipt={
  snapshot:{date:'2026-11-08',track:'京都',race:8,
   sourceKind:'prestart-locked',actualPurchase:false,
   scheduleVerified:false,predictionVerified:false,
   lockedAt:'2026-11-08T09:00:00+09:00',
   scheduledOffAt:'2026-11-08T13:50:00+09:00',
   trifectaTickets:[[7,8,2],[7,8,5]],trioTickets:[]},
  signature:'a'.repeat(64)
 };
 const stored={
  archiveEnabled:true,persistentStorageReady:true,available:true,
  raceCount:1,receipts:[chosenReceipt]
 };
 const verified={
  available:true,serverSigned:true,captureAuditVerified:false,
  officialScheduleVerified:false,officialFeedConnected:false,
  review:{actualPurchase:false,unitYen:100,reviewedRaces:0,
   pendingRaces:1,roiPercent:null,totalInvestedYen:0,totalReturnedYen:0,
   races:[{date:'2026-11-08',track:'京都',race:8,status:'pending',
    trifectaPoints:2,trioPoints:0}]}
 };
 const matched=boot('?date=2026-11-08',null,null,stored,candidate,verified);
 await new Promise(r=>setImmediate(r));
 matched.get('jraResultTrack').value='京都';
 matched.get('jraResultRace').value='8';
 matched.get('jraResultUrl').value=officialURL;
 await matched.get('jraResultCheck').onclick();
 assert.equal(matched.requests.length,5,
  'one JRA page + one receipt archive read + one HMAC verify');
 assert.equal(matched.requests.filter(x=>
  x.url.startsWith('/api/jra/result-candidate?')).length,1);
 assert.equal(matched.requests[4].url,'/api/owner-100yen-verify-receipts');
 assert.equal(matched.requests[4].opts.method,'POST');
 assert.equal(matched.requests[4].opts.headers['X-Keiba-Request'],'private');
 assert.equal(JSON.parse(matched.requests[4].opts.body).receipts.length,1);
 assert.match(matched.get('jraResultStatus').textContent,
  /予想内 1組（未確定）/);
 assert.ok(matched.get('jraResultCandidates').children.some(x=>
  /候補一致：7－8－2／100円あたり候補払戻 26,050円/.test(x.textContent)));
 const singleScenario=matched.get('jraResultCandidates').children.at(-1).textContent;
 assert.match(singleScenario,/【未確定・参考計算】/);
 assert.match(singleScenario,/2点×100円＝200円/);
 assert.match(singleScenario,/参考払戻 26,050円／参考差額 \+25,850円/);
 assert.match(singleScenario,/公式回収率と記録には一切算入しません/);
 assert.equal(matched.storage.size,0);
 // Dead heat: multiple JRA candidate winners may both be in frozen tickets.
 const deadHeat={...candidate,podiumShape:'third_place_dead_heat',
  matchingTrifectaCount:2,matchingTrioCount:2,
  trifectaCandidates:[
   {ticket:[7,8,2],payoutYen:26050},
   {ticket:[7,8,5],payoutYen:48920}
  ],
  trioCandidates:[
   {ticket:[2,7,8],payoutYen:2320},
   {ticket:[5,7,8],payoutYen:5510}
  ]};
 const multi=boot('?date=2026-11-08',null,null,stored,deadHeat,verified);
 await new Promise(r=>setImmediate(r));
 multi.get('jraResultTrack').value='京都';
 multi.get('jraResultRace').value='8';
 multi.get('jraResultUrl').value=officialURL;
 await multi.get('jraResultCheck').onclick();
 assert.match(multi.get('jraResultStatus').textContent,
  /結果候補 2組中、予想内 2組（未確定）/);
 assert.match(multi.get('jraResultCandidates').children.at(-1).textContent,
  /参考払戻 74,970円／参考差額 \+74,770円/);
 assert.equal(multi.storage.size,0);
 // JRA first place A/B dead heat: both ordered winning tickets, but
 // only the first one was sealed in the owner's immutable archive.
 const firstTie={...candidate,podiumShape:'first_place_dead_heat',
  matchingTrifectaCount:2,matchingTrioCount:1,
  trifectaCandidates:[
   {ticket:[7,8,2],payoutYen:29050},
   {ticket:[8,7,2],payoutYen:32920}
  ]};
 const firstTied=boot('?date=2026-11-08',null,null,stored,firstTie,verified);
 await new Promise(r=>setImmediate(r));
 firstTied.get('jraResultTrack').value='京都';
 firstTied.get('jraResultRace').value='8';
 firstTied.get('jraResultUrl').value=officialURL;
 await firstTied.get('jraResultCheck').onclick();
 assert.match(firstTied.get('jraResultStatus').textContent,
  /結果候補 2組中、予想内 1組（未確定）/);
 assert.match(firstTied.get('jraResultCandidates').children.at(-1).textContent,
  /参考払戻 29,050円／参考差額 \+28,850円/);
 assert.equal(firstTied.storage.size,0);
 // Second-place dead heat is also two ordered tickets but never
 // requires the subsequent fourth-place horse.
 const secondTie={...firstTie,podiumShape:'second_place_dead_heat',
  trifectaCandidates:[
   {ticket:[7,8,2],payoutYen:29050},
   {ticket:[7,2,8],payoutYen:32920}
  ]};
 const secondTied=boot('?date=2026-11-08',null,null,null,secondTie);
 await new Promise(r=>setImmediate(r));
 secondTied.get('jraResultTrack').value='京都';
 secondTied.get('jraResultRace').value='8';
 secondTied.get('jraResultUrl').value=officialURL;
 await secondTied.get('jraResultCheck').onclick();
 assert.match(secondTied.get('jraResultStatus').textContent,/固定済み予想との比較は保留/);
 assert.equal(secondTied.storage.size,0);
 assert.ok(!secondTied.get('jraResultCandidates').children.some(x=>
  /【未確定・参考計算】/.test(x.textContent)));
 // A spoofed server envelope claiming a podium match cannot create a
 // contradictory 3連単/3連複 result, payout or apparent hit.
 const forgedTrio={...firstTie,
  trioCandidates:[{ticket:[2,5,8],payoutYen:2320}]};
 const badFirst=boot('?date=2026-11-08',null,null,null,forgedTrio);
 await new Promise(r=>setImmediate(r));
 badFirst.get('jraResultTrack').value='京都';
 badFirst.get('jraResultRace').value='8';
 badFirst.get('jraResultUrl').value=officialURL;
 await badFirst.get('jraResultCheck').onclick();
 assert.equal(badFirst.get('jraResultCandidates').children.length,0);
 assert.match(badFirst.get('jraResultStatus').textContent,
  /安全に確認できませんでした/);
 assert.equal(badFirst.storage.size,0);
 assert.equal(badFirst.get('jraResultCandidates').children.length,0);
 const forgedCount={...firstTie,matchingTrifectaCount:1};
 const badCount=boot('?date=2026-11-08',null,null,null,forgedCount);
 await new Promise(r=>setImmediate(r));
 badCount.get('jraResultTrack').value='京都';
 badCount.get('jraResultRace').value='8';
 badCount.get('jraResultUrl').value=officialURL;
 await badCount.get('jraResultCheck').onclick();
 assert.equal(badCount.get('jraResultCandidates').children.length,0);
 assert.equal(badCount.storage.size,0);
 // Even when the already signed formation missed the observed
 // single-page candidate, a scenario is *negative*, never an official loss.
 const missCandidate={...candidate,
  trifectaCandidates:[{ticket:[2,7,8],payoutYen:2320}]};
 const missed=boot('?date=2026-11-08',null,null,stored,missCandidate,verified);
 await new Promise(r=>setImmediate(r));
 missed.get('jraResultTrack').value='京都';
 missed.get('jraResultRace').value='8';
 missed.get('jraResultUrl').value=officialURL;
 await missed.get('jraResultCheck').onclick();
 assert.match(missed.get('jraResultStatus').textContent,
  /結果候補 1組中、予想内 0組（未確定）/);
 assert.ok(missed.get('jraResultCandidates').children.some(x=>
  /参考払戻 0円／参考差額 −200円/.test(x.textContent)));
 assert.equal(missed.storage.size,0);
 // Forged / contradictory server verification MUST NOT be a claimed hit.
 const forgedVerify={...verified,
  officialFeedConnected:true};
 const withheld=boot('?date=2026-11-08',null,null,
  stored,candidate,forgedVerify);
 await new Promise(r=>setImmediate(r));
 withheld.get('jraResultTrack').value='京都';
 withheld.get('jraResultRace').value='8';
 withheld.get('jraResultUrl').value=officialURL;
 await withheld.get('jraResultCheck').onclick();
 assert.doesNotMatch(withheld.get('jraResultStatus').textContent,
  /予想内 1組/);
 assert.match(withheld.get('jraResultCandidates').children.at(-1).textContent,
  /判定保留/);
 assert.ok(!withheld.get('jraResultCandidates').children.some(x=>
  /【未確定・参考計算】/.test(x.textContent)));
 assert.equal(withheld.storage.size,0);
 // A signed receipt from a different race is never used for comparison.
 const unrelated=structuredClone(chosenReceipt);
 unrelated.snapshot.race=7;
 const otherArchive={...stored,receipts:[unrelated]};
 const noRace=boot('?date=2026-11-08',null,null,
  otherArchive,candidate,verified);
 await new Promise(r=>setImmediate(r));
 noRace.get('jraResultTrack').value='京都';
 noRace.get('jraResultRace').value='8';
 noRace.get('jraResultUrl').value=officialURL;
 await noRace.get('jraResultCheck').onclick();
 assert.equal(noRace.requests.length,4,'no matching receipt: never verify a fabricated R');
 assert.match(noRace.get('jraResultStatus').textContent,/未登録/);
 assert.equal(noRace.storage.size,0);
 observed.get('day').value='2026-11-07';
 observed.get('day').onchange();
 assert.equal(observed.get('jraResultCandidates').children.length,0);
 assert.match(observed.get('jraResultStatus').textContent,/未実行/);
 const invalidOfficial=boot('?date=2026-11-08',null,null,null,
  {...candidate,officialJraVerified:true});
 await new Promise(r=>setImmediate(r));
 invalidOfficial.get('jraResultTrack').value='京都';
 invalidOfficial.get('jraResultRace').value='8';
 invalidOfficial.get('jraResultUrl').value=officialURL;
 await invalidOfficial.get('jraResultCheck').onclick();
 assert.equal(invalidOfficial.get('jraResultCandidates').children.length,0);
 assert.match(invalidOfficial.get('jraResultStatus').textContent,
  /安全に確認できませんでした/);
 const wrongUrl=boot('?date=2026-11-08',null,null,null,candidate);
 await new Promise(r=>setImmediate(r));
 wrongUrl.get('jraResultTrack').value='京都';
 wrongUrl.get('jraResultRace').value='8';
 wrongUrl.get('jraResultUrl').value='https://evil.test/a';
 await wrongUrl.get('jraResultCheck').onclick();
 assert.equal(wrongUrl.requests.length,2,'malformed URL makes no network call');
 const todayOrFuture=boot('?date=2099-01-02',null,null,null,candidate);
 await new Promise(r=>setImmediate(r));
 todayOrFuture.get('jraResultTrack').value='京都';
 todayOrFuture.get('jraResultRace').value='8';
 todayOrFuture.get('jraResultUrl').value=officialURL;
 await todayOrFuture.get('jraResultCheck').onclick();
 assert.equal(todayOrFuture.requests.length,2,
  'future result is never fetched');
 assert.equal(todayOrFuture.storage.size,0);
 const b=boot('?date=2099-02-31');
 await new Promise(r=>setImmediate(r));
 assert.notEqual(b.get('day').value,'2099-02-31');
 assert.equal(b.requests.length,2);
 const c=boot('?date=2099-03-01');
 await new Promise(r=>setImmediate(r));
 let release;
 const pause=new Promise(resolve=>{release=resolve});
 c.delay(pause);
 const stale=c.get('load').onclick();
 assert.equal(c.get('load').disabled,true);
 c.get('day').value='2099-03-02';
 c.get('day').onchange();
 assert.equal(c.get('load').disabled,false);
 release();
 await stale;
 assert.match(c.get('status').textContent,/選んで確認/);
 assert.equal(c.get('summary').children.length,0);
 assert.equal(c.storage.size,0);
 // Read-only official-result fixture tests the newly added slot-miss
 // column without connecting a real results feed or altering local tickets.
 const fake={
  version:'keiba-100yen-review-1',unitYen:100,actualPurchase:false,
  races:[
   {date:'2099-01-02',track:'東京',race:1,status:'verified_result',
    trifectaPoints:40,trioPoints:0,investedYen:4000,returnedYen:0,
    trifectaMissReason:'winner_wrong_slot'},
   {date:'2099-01-02',track:'東京',race:2,status:'pending',
    trifectaPoints:30,trioPoints:0,investedYen:null,returnedYen:null,
    trifectaMissReason:null}
  ],venueBreakdown:[],reviewedRaces:1,pendingRaces:1,
  totalInvestedYen:4000,totalReturnedYen:0,totalProfitYen:-4000,
  roiPercent:0,firstCandidateHits:0,firstCandidateEligibleRaces:1,
  pendingStakeYen:3000,note:'架空の検証'
 };
 const d=boot('?date=2099-01-02',fake);
 await new Promise(r=>setImmediate(r));
 assert.equal(d.get('races').children.length,1);
 const dashboard=d.get('summary').children;
 assert.equal(dashboard[2].children[1].textContent,'7,000円');
 assert.equal(dashboard[3].children[1].textContent,'4,000円');
 assert.equal(dashboard[6].children[1].textContent,'0.0%');
 // Results awaiting verification must not count as realized loss or ROI.
 const badStake=boot('?date=2099-01-02',{...fake,pendingStakeYen:-100});
 await new Promise(r=>setImmediate(r));
 assert.equal(badStake.get('summary').children.length,0);
 assert.match(badStake.get('status').textContent,/安全な集計ができません/);
 const t=d.get('races').children[0].children[0];
 const head=t.children[0].children[0];
 assert.ok(head.children.some(x=>x.textContent==='3連単の検証'));
 const body=t.children[1];
 assert.match(body.children[0].children[4].textContent,/1着馬を2・3着に評価/);
 assert.equal(body.children[1].children[4].textContent,'結果待ち');
 assert.equal(d.storage.size,0);

 // The optional postrace comparison must NOT run on page open.
 const sample={
  version:'owner-prestart-tse-comparison-1',date:'2099-01-02',
  researchOnly:true,privateOwnerOnly:true,officialJraVerified:false,
  independentJraVerified:false,payoutVerified:false,roiPercent:null,
  officialHitCount:null,realPredictionReady:false,actualPurchase:false,
  bettingReady:false,changesExistingReceipts:false,providerReadCount:1,
  raceCount:2,observedRaceCount:1,pendingRaceCount:1,
  provisionalExactCombinationCount:0,provisionalFirstCandidateCount:0,
  races:[
   {track:'東京',race:1,providerStatus:'provider_podium_observed',
    trifectaPoints:40,firstCandidateObserved:false,secondCandidateObserved:true,
    thirdCandidateObserved:true,exactCombinationObserved:false,
    firstMissType:'wrong_slot',officialVerified:false},
   {track:'京都',race:2,providerStatus:'pending',trifectaPoints:30,
    firstCandidateObserved:null,secondCandidateObserved:null,
    thirdCandidateObserved:null,exactCombinationObserved:null,
    firstMissType:null,officialVerified:false}
  ]
 };
 const e=boot('?date=2099-01-02',fake,sample);
 await new Promise(r=>setImmediate(r));
 assert.equal(e.requests.length,2);
 const tickets=n=>{
  const all=[];
  for(let x=1;x<=18&&all.length<n;x++)
   for(let y=1;y<=18&&all.length<n;y++)
    for(let z=1;z<=18&&all.length<n;z++)
     if(x!==y&&x!==z&&y!==z)all.push([x,y,z]);
  return all;
 };
 const createSigned=(track,race,n)=>({
  snapshot:{date:'2099-01-02',track,race,
   sourceKind:'prestart-locked',actualPurchase:false,
   scheduleVerified:false,predictionVerified:false,
   lockedAt:'2099-01-01T12:00:00+09:00',
   scheduledOffAt:'2099-01-02T10:00:00+09:00',
   trifectaTickets:tickets(n),trioTickets:[]},
  signature:'a'.repeat(64)
 });
 const signed=[createSigned('東京',1,40),createSigned('京都',2,30)];
 e.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
 await e.get('provisionalCheck').onclick();
 assert.equal(e.requests.length,4);
 assert.match(e.requests[2].url,/owner-archive-read/);
 assert.equal(e.requests[3].url,'/api/owner-prestart-tse-review');
 assert.equal(e.requests[3].opts.method,'POST');
 assert.equal(e.requests[3].opts.headers['X-Keiba-Request'],'private');
 assert.equal(JSON.parse(e.requests[3].opts.body).receipts.length,2);
 assert.match(e.get('provisionalStatus').textContent,/この端末の固定記録 2Rをすべて対象/);
 assert.match(e.get('provisionalStatus').textContent,/公式の結果・的中・払戻・回収率に加算していません/);
 assert.equal(e.get('provisionalRaces').children.length,3);
 assert.match(e.get('provisionalRaces').children[1].textContent,/勝ち馬を2・3着候補に配置/);
 assert.match(e.get('provisionalRaces').children[2].textContent,/保留/);
 assert.equal(e.storage.size,1);
 e.get('day').value='2099-01-03';e.get('day').onchange();
 assert.equal(e.get('provisionalRaces').children.length,0);

 const forged=boot('?date=2099-01-02',fake,
  {...sample,officialJraVerified:true});
 await new Promise(r=>setImmediate(r));
 forged.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
 await forged.get('provisionalCheck').onclick();
 assert.equal(forged.get('provisionalRaces').children.length,0);
 assert.match(forged.get('provisionalStatus').textContent,/暫定照合ができませんでした/);

 // A response may not silently omit or fabricate a signed race, nor report
 // different point counts from the signed original.
 for(const mutate of [
  obj=>obj.races.pop(),
  obj=>obj.races[1].track='阪神',
  obj=>obj.races[0].trifectaPoints=39,
  obj=>obj.races[1].race=1,
  obj=>obj.races[0].track='京都',
 ]){
  const altered=JSON.parse(JSON.stringify(sample));mutate(altered);
  const bad=boot('?date=2099-01-02',fake,altered);
  await new Promise(r=>setImmediate(r));
  bad.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
  await bad.get('provisionalCheck').onclick();
  assert.equal(bad.get('provisionalRaces').children.length,0);
  assert.match(bad.get('provisionalStatus').textContent,/暫定照合ができませんでした/);
  assert.equal(bad.storage.size,1);
 }
 // The archive can be configured but empty; legacy local receipts still count.
 const emptyArchive=boot('?date=2099-01-02',fake,sample,{
  archiveEnabled:true,persistentStorageReady:true,available:false,
  raceCount:0,receipts:[]
 });
 await new Promise(r=>setImmediate(r));
 emptyArchive.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
 await emptyArchive.get('provisionalCheck').onclick();
 assert.match(emptyArchive.get('provisionalStatus').textContent,/この端末の固定記録 2Rをすべて対象/);
 const archive=boot('?date=2099-01-02',fake,sample,{
  archiveEnabled:true,persistentStorageReady:true,available:true,
  raceCount:2,receipts:signed
 });
 await new Promise(r=>setImmediate(r));
 await archive.get('provisionalCheck').onclick();
 assert.equal(archive.requests.length,4);
 assert.match(archive.get('provisionalStatus').textContent,/サーバー固定記録 2Rをすべて対象/);
 assert.equal(archive.storage.size,0);
 // Malformed local records are rejected before another provider read.
 const corrupt=boot('?date=2099-01-02',fake,sample);
 await new Promise(r=>setImmediate(r));
 const tampered=JSON.parse(JSON.stringify(signed));
 tampered[0].snapshot.trifectaTickets.push([1,2,3]);
 corrupt.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(tampered));
 await corrupt.get('provisionalCheck').onclick();
 assert.equal(corrupt.requests.length,3);
 assert.match(corrupt.get('provisionalStatus').textContent,/暫定照合ができませんでした/);
 const missing=boot('?date=2099-01-02',fake,sample);
 await new Promise(r=>setImmediate(r));
 await missing.get('provisionalCheck').onclick();
 assert.equal(missing.requests.length,3);
 assert.equal(missing.storage.size,0);
 const staleProvisional=boot('?date=2099-01-02',fake,sample);
 await new Promise(r=>setImmediate(r));
 staleProvisional.storage.set('keiba-nine-owner-server-receipts-v1',JSON.stringify(signed));
 let releaseProvisional;
 const holdProvisional=new Promise(resolve=>{releaseProvisional=resolve});
 staleProvisional.delay(holdProvisional);
 const waiting=staleProvisional.get('provisionalCheck').onclick();
 staleProvisional.get('day').value='2099-01-03';
 staleProvisional.get('day').onchange();
 releaseProvisional();await waiting;
 assert.equal(staleProvisional.get('provisionalRaces').children.length,0);
 assert.equal(staleProvisional.storage.size,1);
 // /thj is an explicit JRDB source comparison, never a JRA-certified
 // official payout or a mutation of the signed prestart ledger.
 const thj={
  version:'owner-prestart-thj-100yen-reference-1',date:'2099-01-02',
  source:'jrdb_thj_provider_reference',unitYen:100,providerReadCount:1,
  raceCount:2,observedRaces:1,pendingRaces:1,pendingStakeYen:3000,
  reviewedInvestedYen:4000,reviewedReturnedYen:26050,
  reviewedProfitYen:22050,reviewedRoiPercent:651.25,
  providerMatchedRaces:1,
  races:[
   {track:'東京',race:1,status:'provider_observed',
    trifectaPoints:40,investedYen:4000,returnedYen:26050,
    providerMatchedTickets:1,officialJraVerified:false},
   {track:'京都',race:2,status:'refund_review',
    trifectaPoints:30,investedYen:null,returnedYen:null,
    providerMatchedTickets:null,officialJraVerified:false}
  ],
  researchOnly:true,privateOwnerOnly:true,officialJraVerified:false,
  payoutOfficiallyVerified:false,actualPurchase:false,predictionReady:false,
  changesExistingReceipts:false,writesPersistentResults:false
 };
 const thjView=boot('?date=2099-01-02',fake,sample,
  {archiveEnabled:true,persistentStorageReady:true,available:true,
   raceCount:2,receipts:signed},null,null,thj);
 await new Promise(r=>setImmediate(r));
 assert.equal(thjView.requests.length,2,
  'payoff check cannot run merely because the review page loaded');
 const beforeThj=thjView.requests.length;
 await thjView.get('thjCheck').onclick();
 assert.equal(thjView.requests.length,beforeThj+2);
 assert.equal(thjView.requests[3].url,'/api/owner-prestart-thj-review');
 assert.equal(thjView.requests[3].opts.method,'POST');
 assert.equal(thjView.requests[3].opts.headers['X-Keiba-Request'],'private');
 assert.equal(JSON.parse(thjView.requests[3].opts.body).receipts.length,2);
 assert.match(thjView.get('thjStatus').textContent,/JRDB払戻1R.*未確定1R/);
 assert.equal(thjView.get('thjSummary').children.length,6);
 assert.match(thjView.get('thjSummary').children.at(-1).children[1].textContent,
  /651.3%/);
 assert.equal(thjView.get('thjRaces').children.length,2);
 assert.match(thjView.get('thjRaces').children[1].textContent,/返還確認が必要/);
 assert.equal(thjView.storage.size,0);
 thjView.get('day').value='2099-01-03';
 thjView.get('day').onchange();
 assert.equal(thjView.get('thjRaces').children.length,0);
 assert.equal(thjView.get('thjSummary').children.length,0);
 for(const mutate of [
  x=>x.officialJraVerified=true,
  x=>x.races[0].returnedYen=9999,
  x=>x.races[1].returnedYen=0,
  x=>x.races[0].track='福島',
  x=>x.races[0].trifectaPoints=39
 ]){
  const invalid=JSON.parse(JSON.stringify(thj));mutate(invalid);
  const noFraud=boot('?date=2099-01-02',fake,sample,
   {archiveEnabled:true,persistentStorageReady:true,available:true,
    raceCount:2,receipts:signed},null,null,invalid);
  await new Promise(r=>setImmediate(r));
  await noFraud.get('thjCheck').onclick();
  assert.equal(noFraud.get('thjSummary').children.length,0);
  assert.match(noFraud.get('thjStatus').textContent,/安全に照合できません/);
  assert.equal(noFraud.storage.size,0);
 }
 console.log('Owner 100-yen review: provisional comparison opt-in/read-only PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
