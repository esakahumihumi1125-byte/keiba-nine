/* Safe iPhone day-pipeline flow: mock-only integration, no JRDB or account data. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'), vm=require('node:vm');
const script=fs.readFileSync('/tmp/keiba-jrdb-day-pipeline.js','utf8');
function instance(configured, prestartEnabled=false, deferDay=false, historyEnabled=false){
 const nodes=new Map(), calls=[], delayed=[];
 const el=id=>{
  if(!nodes.has(id))nodes.set(id,{id,value:'',disabled:id==='run'||id==='prestartRun'||id==='historyRun',hidden:id==='report'||id==='review'||id==='factorProgress'||id==='sourceMaterials'||id==='prestartReport'||id==='historyReport',
   textContent:'',children:[],events:{},
   addEventListener(type,fn){this.events[type]=fn},
   replaceChildren(...children){this.children=children},
   append(...children){this.children.push(...children)},
  });
  return nodes.get(id);
 };
 const document={getElementById:el,createElement(tag){
  return {tag,textContent:'',children:[],className:'',
   append(...children){this.children.push(...children)}};
 }};
 let malformed=false;
 const demo={
  realPredictionReady:false,purchaseReady:false,rawHorseRecordsIncluded:false,
  sourceRequestCount:5,raceCount:2,recordType:'test',
  summary:{matchedEntryCountRaces:2,missingTrainingRecords:0,
   missingLastWeekRecords:0,missingRecentRecords:1},
  races:[
   {track:'東京',race:1,postTimeFromProvider:'10:00',registered:2,expected:2,
    trainingUnaccounted:0,lastWeekUnaccounted:0,recentUnaccounted:1,
    sourceGoingRecorded:true},
   {track:'京都',race:1,postTimeFromProvider:'10:05',registered:1,expected:1,
    trainingUnaccounted:0,lastWeekUnaccounted:0,recentUnaccounted:0,
    sourceGoingRecorded:false}
  ],
  sourceMaterials:{
   version:'private-eight-materials-1',date:'20261101',raceCount:2,
   verifiedOverallFactors:0,realPredictionReady:false,purchaseReady:false,
   rawHorseRecordsIncluded:false,
   mappedSourceSlots:['training','recent','pace','pedigree','draw_weight',
    'rotation','jockey_stable','body_condition'],
   unmappedHistorySlots:['course_distance','ground'],
   summary:{totalRegistered:3,pedigreePresent:1,drawAndWeightPresent:1,
    personnelPresent:1,conformationPresent:1,cornerResearchPresent:0,
    rotationDatesPresent:1},
   races:[
    {track:'東京',race:1,registered:2,observedSourceSlots:8,
     unmappedHistorySlots:2,unverifiedFactorGrades:10,provisionalFactorsOnly:2,
     officialJraVerified:false,overallRankReady:false,
     realPredictionReady:false,ticketReady:false,
     counts:{pedigreeParentsRecorded:1,drawAndAssignedWeightRecorded:1,
      lastRaceDateRecorded:1,jockeyTrainerNamesRecorded:1,
      conformationCodeRecorded:1,pastCornerObservedForPaceResearch:0}},
    {track:'京都',race:1,registered:1,observedSourceSlots:8,
     unmappedHistorySlots:2,unverifiedFactorGrades:10,provisionalFactorsOnly:2,
     officialJraVerified:false,overallRankReady:false,
     realPredictionReady:false,ticketReady:false,
     counts:{pedigreeParentsRecorded:0,drawAndAssignedWeightRecorded:0,
      lastRaceDateRecorded:0,jockeyTrainerNamesRecorded:0,
      conformationCodeRecorded:0,pastCornerObservedForPaceResearch:0}}
   ]
  },
  factorProgress:{
   version:'day-factor-progress-1',date:'20261101',raceCount:2,
   realOverallGradeReady:false,realPredictionReady:false,purchaseReady:false,
   rawHorseRecordsIncluded:false,
   summary:{runnersWithTrainingProvisional:2,runnersWithRecentProvisional:1,
    runnersWithBothProvisional:1,runnersWithLargeGradeDisagreement:0},
   races:[
    {track:'東京',race:1,registered:2,trainingExperimentalGraded:2,
     recentExperimentalGraded:1,bothExperimentalGraded:1,
     fullTenFactorsGraded:0,remainingFactorsUnassessed:8,
     realOverallGradeReady:false,realPredictionReady:false,ticketReady:false,
     officialRaceVerified:false,
     trainingGradeCounts:{S:1,A:1,B:0,C:0,'未評価':0},
     recentGradeCounts:{S:1,A:0,B:0,C:0,'未評価':1}},
    {track:'京都',race:1,registered:1,trainingExperimentalGraded:0,
     recentExperimentalGraded:0,bothExperimentalGraded:0,
     fullTenFactorsGraded:0,remainingFactorsUnassessed:8,
     realOverallGradeReady:false,realPredictionReady:false,ticketReady:false,
     officialRaceVerified:false,
     trainingGradeCounts:{S:0,A:0,B:0,C:0,'未評価':1},
     recentGradeCounts:{S:0,A:0,B:0,C:0,'未評価':1}}
   ]
  },
  reviewQueue:{version:'private-day-review-1',raceCount:2,
   officialFinalVerified:false,realPredictionReady:false,purchaseReady:false,
   racesWithinTwoHours:2,racesNeedingManualPriorityCheck:2,
   racesPassedPost:0,races:[
    {track:'東京',race:1,reviewPriority:'urgent_manual_check',
     minutesUntilListedPost:20,sourceGoingAgeStatus:'recent_reported',
     realPredictionReady:false,ticketReady:false,independentJraVerified:false,
     blockers:['JRA公式照合待ち']},
    {track:'京都',race:1,reviewPriority:'urgent_manual_check',
     minutesUntilListedPost:25,sourceGoingAgeStatus:'no_going_report',
     realPredictionReady:false,ticketReady:false,independentJraVerified:false,
     blockers:['馬場資料なし']},
   ]}
 };
 async function fetchMock(url,opts){
  calls.push({url,opts});
  if(url==='/api/setup')return {ok:true,json:async()=>({jrdbConfigured:configured,prestartBodyEnabled:prestartEnabled,historyConfigured:historyEnabled})};
  if(url==='/api/jrdb/history'){
   assert.equal(opts.method,'POST','History must be an explicit owner POST');
   assert.equal(opts.headers['X-Keiba-Request'],'private');
   assert.equal(opts.headers['Content-Type'],'application/json');
   assert.equal(opts.credentials,'same-origin');
   assert.equal(opts.cache,'no-store');
   assert.equal(JSON.parse(opts.body).limit,8);
   assert.equal(JSON.parse(opts.body).date,'20261101');
   return {ok:true,json:async()=>({
    version:'bounded-history-1',predictionReady:false,goingSuitabilityAssessed:false,
    selectedPastRaces:2,deferredPastRaces:1,unavailablePastProgrammes:0,
    draCalls:2,dkaCalls:1,maxTotalCalls:16,
    allTenFactorSources:{
     version:'combined-ten-factor-observations-1',raceCount:2,
     predictionReady:false,bettingReady:false,
     races:[
      {track:'東京',race:1,sourceMaterialSlots:10,
       unmappedFactorCount:0,verifiedFactorCount:0,runnerCount:2,
       runnersWithComparableCourse:1,runnersWithKnownGoingComparable:1,
       runnersWithIncompleteHistory:1,officialJraFinalVerification:false,
       overallRankReady:false,predictionReady:false,bettingReady:false},
      {track:'京都',race:1,sourceMaterialSlots:10,
       unmappedFactorCount:0,verifiedFactorCount:0,runnerCount:1,
       runnersWithComparableCourse:0,runnersWithKnownGoingComparable:0,
       runnersWithIncompleteHistory:1,officialJraFinalVerification:false,
       overallRankReady:false,predictionReady:false,bettingReady:false}
     ]},
    realAssessmentPreflight:{version:'real-assessment-preflight-1',raceCount:2,
     realGradeReady:false,realPredictionReady:false,purchaseReady:false},
    evidenceQuality:{version:'history-evidence-coverage-1',raceCount:2,
     predictionReady:false,suitabilityAssessed:false},
    privateHistoryFactors:{version:'private-course-ground-materials-1',
     raceCount:2,predictionReady:false,bettingReady:false}
   })};
  }
  if(url.startsWith('/api/jrdb/prestart-body?date='))return {ok:true,json:async()=>({
   version:'private-prestart-body-1',rawHorseRecordsIncluded:false,oddsUsed:false,
   realPredictionReady:false,purchaseReady:false,raceCount:1,
   summary:{weightRecords:1,paddockRecords:0,missingRows:0},
   races:[{track:'東京',race:1,registered:2,bodyWeightRecords:1,
    weightChangeRecords:1,paddockRecords:0,prestartRowsMissing:0,
    realPredictionReady:false,ticketReady:false,bodyConditionGraded:false,
    officialBodyWeightVerified:false}]
  })};
  if(url==='/api/jrdb/day-pipeline?date=20261101'){
   if(deferDay)return new Promise(resolve=>delayed.push(resolve));
   return {ok:true,json:async()=>malformed?
    {...demo,reviewQueue:{...demo.reviewQueue,realPredictionReady:true}}:demo};
  }
  throw Error('Unexpected network URL '+url);
 }
 const context={document,fetch:fetchMock,Intl,Date,Object,Math,JSON,Array,
                encodeURIComponent,console};
 vm.runInNewContext(script,context);
 return {el,calls,setMalformed:value=>{malformed=value},
  resolveDay:()=>delayed.forEach(resolve=>resolve({ok:true,json:async()=>demo}))};
}
async function tick(){
 await new Promise(resolve=>setImmediate(resolve));
 await new Promise(resolve=>setImmediate(resolve));
}
(async()=>{
 const offline=instance(false);
 await tick();
 assert.equal(offline.calls.length,1,'Only local setup checks on initial load');
 assert.equal(offline.calls[0].url,'/api/setup');
 assert.equal(offline.el('run').disabled,true,'Paid fetch cannot start without credentials');
 assert.match(offline.el('state').textContent,/認証情報待ち/);
 assert.equal(offline.el('report').hidden,true);
 assert.equal(offline.el('prestartRun').disabled,true);
 assert.equal(offline.el('historyRun').disabled,true);
 const ready=instance(true);
 await tick();
 assert.equal(ready.calls.length,1,'Never fetch JRDB during page load');
 assert.equal(ready.el('run').disabled,false);
 assert.equal(ready.el('historyRun').disabled,true);
 assert.equal(typeof ready.el('run').events.click,'function');
 ready.el('date').value='2026-11-01';
 await ready.el('run').events.click();
 assert.equal(ready.calls.length,2,'One owner click causes one protected API request');
 assert.equal(ready.calls[1].url,'/api/jrdb/day-pipeline?date=20261101');
 assert.equal(ready.calls[1].opts.credentials,'same-origin');
 assert.equal(ready.calls[1].opts.headers['X-Keiba-Request'],'private');
 assert.equal(ready.el('report').hidden,false);
 assert.equal(ready.el('review').hidden,false);
 assert.equal(ready.el('factorProgress').hidden,false);
 assert.equal(ready.el('factorRows').children.length,2);
 assert.equal(ready.el('sourceMaterials').hidden,false);
 assert.equal(ready.el('sourceMaterialsRows').children.length,2);
 assert.equal(ready.el('sourceMaterialsRows').children[0].tag,'details');
 assert.match(ready.el('sourceMaterialsSummary').textContent,/8枠を接続/);
 assert.match(ready.el('factorSummary').textContent,/暫定評価/);
 assert.equal(ready.el('rows').children.length,2);
 assert.equal(ready.el('reviewRows').children.length,2);
 assert.match(ready.el('reviewSummary').textContent,/優先確認 2R/);
 assert.match(ready.el('reviewRows').children[0].children[1].textContent,/直近60分以内の報告/);
 assert.ok(!ready.el('reviewRows').children.some(c=>String(c.textContent).includes('実購入')));
 ready.el('date').value='2026-11-02';
 ready.el('date').events.change();
 assert.equal(ready.el('report').hidden,true,'Previous day must not remain on screen');
 assert.equal(ready.el('reviewRows').children.length,0);
 assert.equal(ready.el('factorRows').children.length,0);
 assert.equal(ready.el('sourceMaterialsRows').children.length,0);
 assert.equal(ready.el('rows').children.length,0);
 ready.el('date').value='2026-11-01';
 ready.setMalformed(true);
 await ready.el('run').events.click();
 assert.equal(ready.el('report').hidden,true,'Forged prediction-ready flags rejected');
 assert.match(ready.el('message').textContent,/安全に表示できません/);
 assert.equal(ready.el('run').disabled,false,'Recover from invalid response');
 const stale=instance(true,false,true);
 await tick();
 stale.el('date').value='2026-11-01';
 const inflight=stale.el('run').events.click();
 await tick();
 assert.equal(stale.calls.length,2);
 stale.el('date').value='2026-11-02';
 stale.el('date').events.change();
 stale.resolveDay();
 await inflight;
 assert.equal(stale.el('report').hidden,true,
  'An older date must never reappear after an in-flight response');
 assert.equal(stale.el('sourceMaterialsRows').children.length,0);
 assert.equal(stale.el('factorRows').children.length,0,
  'Stale response must not recreate factor grades');
 assert.match(stale.el('message').textContent,/開催日を変更/);
 const past=instance(true,false,false,true);
 await tick();
 assert.equal(past.calls.length,1,'Opening page must not start historical fetches');
 assert.equal(past.el('historyRun').disabled,false);
 past.el('date').value='2026-11-01';
 await past.el('historyRun').events.click();
 assert.equal(past.calls.length,2);
 assert.equal(past.calls[1].url,'/api/jrdb/history');
 assert.equal(past.el('historyReport').hidden,false);
 assert.equal(past.el('historyRows').children.length,2);
 assert.match(past.el('historySummary').textContent,/過去番組 2件/);
 past.el('date').value='2026-11-02';
 past.el('date').events.change();
 assert.equal(past.el('historyReport').hidden,true);
 assert.equal(past.el('historyRows').children.length,0);
 assert.equal(past.calls.length,2,'Changing date must not issue another historical request');
 const beforeBody=instance(true,true);
 await tick();
 assert.equal(beforeBody.calls.length,1,'Body endpoint cannot run on page load');
 assert.equal(beforeBody.el('prestartRun').disabled,false);
 const dateOnPage=beforeBody.el('date').value;
 await beforeBody.el('prestartRun').events.click();
 assert.equal(beforeBody.calls.length,2,'Body endpoint requires explicit click');
 assert.equal(beforeBody.calls[1].url,
  '/api/jrdb/prestart-body?date='+dateOnPage.replaceAll('-',''));
 assert.equal(beforeBody.el('prestartReport').hidden,false);
 assert.match(beforeBody.el('prestartSummary').textContent,/馬体重の報告 1頭分/);
 assert.equal(beforeBody.el('prestartRows').children.length,1);
 beforeBody.el('date').value='2099-01-01';
 beforeBody.el('date').events.change();
 assert.equal(beforeBody.el('prestartReport').hidden,true);
 assert.equal(beforeBody.el('prestartRows').children.length,0);
 await beforeBody.el('prestartRun').events.click();
 assert.equal(beforeBody.calls.length,2,'Past/future days must never trigger prestart API');
 assert.match(beforeBody.el('prestartMessage').textContent,/日本時間の今日/);
 assert.ok(!script.includes('localStorage'));
 assert.ok(!script.includes('innerHTML'));
 assert.ok(!script.includes('setInterval'));
 assert.ok(!ready.calls.some(x=>x.url.includes('api_key')));
 console.log('iPhone day pipeline: no automatic JRDB fetch, protected one-click, timing UI, date clearing and forged-response blocking OK');
})().catch(e=>{console.error(e);process.exitCode=1});
