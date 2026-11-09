/* Owner-only auto-draft mobile UI: synthetic DOM and local receipt preservation. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-auto-forecast.js','utf8');
const STORAGE='keiba-nine-owner-server-receipts-v1';
const day='20990101', date='2099-01-01';
const pairs=[['S','S',8,'S'],['S','A',7,'A'],['A','A',6,'A'],
 ['A','B',5,'B'],['B','B',4,'B'],['B','C',3,'C'],['C','C',2,'C']];
const runners=pairs.map(([training,recent,twoFactorPoints,twoFactorGrade],i)=>({
 number:i+1,training,recent,twoFactorPoints,twoFactorGrade,
 weightedResearchPoints:30*({S:3,A:2,B:1,C:0}[training])+
                         3*({S:3,A:2,B:1,C:0}[recent]),
 pastFourthCorner:'insufficient',comparisonRank:i+1
}));
const first=[1,2],second=[1,2,3,4,5],third=[1,2,3,4,5,6,7];
const tickets=[];
for(const a of first)for(const b of second)for(const c of third)
 if(a!==b&&a!==c&&b!==c)tickets.push([a,b,c]);
const sortedTickets=tickets.slice().sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
const POLICY=[
 ['training','調教',30,true],['recent','近走',3,true],
 ['course_distance','コース・距離',20,true],['pace','展開・脚質',20,true],
 ['ground','馬場',12,true],['pedigree','血統',8,false],
 ['draw_weight','枠・斤量',3,false],['jockey_stable','騎手・厩舎',2,false],
 ['rotation','ローテ',1,false],['body_condition','馬体重',1,false]
];
function withTenPreview(r){
 r.tenFactorPreview={
  version:'owner-ten-factor-contract-1',policyVersion:'research-5',
  factorCount:10,totalWeight:100,normalization:'weighted_mean_over_100',
  scoreUnit:'0_to_100',gradeThresholds:{S:85,A:70,B:55},
  researchOnly:true,overallPredictionReady:false,officialJraVerified:false,
  autoPurchase:false,fullPredictionRaceCount:0,
  requiredForOverall:'all_ten_verified_before_start',
  factors:POLICY.map(([key,label,weight,core])=>({key,label,weight,core})),
  raceCount:r.races.length,
  races:r.races.map(row=>({
   track:row.track,race:row.race,runnerCount:row.runners.length,
   overallReady:false,fullTenFactorCount:0,
   sourceGradeMode:'two_factor_provisional_only',
   trainingLedRecheckIsWinPick:false,
   trainingLedRecheckNeeds:['course_distance','pace','ground'],
   trainingLedRecheckNumbers:(row.status==='provisional_draft'
    ?row.runners.filter(h=>['S','A'].includes(h.training)&&
      ['B','C'].includes(h.recent)).map(h=>h.number).sort((a,b)=>a-b):[]),
   horses:row.runners.map(h=>{
    const grades=Object.fromEntries(POLICY.map(([key])=>
     [key,key==='training'?h.training:key==='recent'?h.recent:'未評価']));
    return {number:h.number,grades,score:null,overallGrade:'未評価',
     overallRank:null,verifiedFactorCount:0,
     provisionalFactorCount:['training','recent'].filter(k=>grades[k]!=='未評価').length,
     missing:POLICY.map(([k])=>k).filter(k=>grades[k]==='未評価')};
   })
  }))
 };
 return r;
}
function withSourcePassport(r){
 const source=new Map(r.sourceMaterials.races.map(x=>[x.track+'|'+x.race,x]));
 const course=new Map(r.raceContext.races.map(x=>[x.track+'|'+x.race,x]));
 const drafts=new Map(r.races.map(x=>[x.track+'|'+x.race,x]));
 const materialAvailable=r.sourceMaterials.status==='observed';
 r.sourcePassport={
  version:'owner-day-source-passport-1',policyVersion:'research-5',
  raceCount:r.races.length,sourceAuditAvailable:true,
  observedMaterialRaces:materialAvailable?r.races.length:0,
  gradedFactors:0,verifiedPredictions:0,
  independentJraVerified:false,purchaseReady:false,newProviderRequests:0,
  reason:'unvalidated_source_observations_only',
  races:r.tenFactorPreview.races.map(ten=>{
   const id=ten.track+'|'+ten.race,material=source.get(id),context=course.get(id);
   const original=drafts.get(id);
   return {
    track:ten.track,race:ten.race,draftStatus:original.status,
    programmeRunnerCount:materialAvailable?material.runnerCount:ten.runnerCount,
    provisionalTrainingCount:ten.horses.filter(h=>h.grades.training!=='未評価').length,
    provisionalRecentCount:ten.horses.filter(h=>h.grades.recent!=='未評価').length,
    sourceMaterialsObserved:materialAvailable,
    additionalFieldCounts:materialAvailable?structuredClone(material.counts):null,
    courseContextPresent:context.courseInfoPresent,
    goingContextPresent:context.goingAvailable,
    raceDayBodyweightVerifiedCount:0,officialJraVerified:false,
    verifiedFactorCount:0,
    unassessedFactorKeys:POLICY.slice(2).map(x=>x[0]),
    completeTenFactorReady:false,independentResultsConnected:false,
    purchaseReady:false
   };
  })
 };
 return r;
}
const research=()=>({
 version:'jrdb-owner-auto-draft-1',date:day,researchOnly:true,
 privateOwnerOnly:true,officialJraVerified:false,
 overallPredictionReady:false,bettingReady:false,autoPurchase:false,
 sourceReadCount:4,unitYen:100,raceCount:1,draftCount:1,holdCount:0,holdReasons:{},
 weightedResearchOrder:'training30_recent3',weightedResearchMax:99,
 weightedResearchPolicy:'research-5',
 serverStamped:true,captureAuditVerified:false,researchReceiptCount:1,
 archiveEnabled:false,archiveRecordCount:0,archiveConflictCount:0,
 raceContext:{
  version:'race-context-1',raceCount:1,courseInfoPresentCount:1,
  goingAvailableCount:1,raceConditionsVerified:false,predictionReady:false,
  conditionProviderReadCount:1,conditionProviderFetchStatus:'received',
  races:[{
   track:'東京',race:1,surface:'芝',distance_m:2000,turn:'左',
   going:'重',goingAvailable:true,conditionSnapshotPresent:true,
   conditionUpdateRecorded:true,courseInfoPresent:true,
   horseCourseSuitabilityAssessed:false,
   horseGoingSuitabilityAssessed:false,predictionReady:false
  }]
 },
 sourceMaterials:{version:'owner-draft-material-coverage-1',status:'unavailable',
  observedFactorSlots:0,gradedNewFactors:0,officialJraVerified:false,races:[]},
 races:[{
  track:'東京',race:1,status:'provisional_draft',reason:'two_factor_only',
  postTime:'12:00',researchOnly:true,officialJraVerified:false,
  overallPredictionReady:false,bettingReady:false,autoPurchase:false,
  runners,first,second,third,tickets,points:40,amountYen:4000
 }]
});
function resultWith(signature){
 const result=research();
 result.researchReceipts=[{
  signature, snapshot:{
   date,track:'東京',race:1,sourceKind:'prestart-locked',
   actualPurchase:false,lockedAt:'2099-01-01T09:00:00+09:00',
   scheduledOffAt:'2099-01-01T12:00:00+09:00',
   trifectaTickets:sortedTickets,trioTickets:[],
   scheduleVerified:false,predictionVerified:false
  }
 }];
 return withSourcePassport(withTenPreview(result));
}
function full36RaceDraft(){
 // Three-venue, 36R fixture: 1 prestart signed draft and 35 later holds.
 // Never fabricate historical rankings for post-off races.
 const data=resultWith('a'.repeat(64));
 const first=data.races[0],ten=data.tenFactorPreview.races[0],
  context=data.raceContext.races[0],passport=data.sourcePassport.races[0];
 const coords=['東京','京都','福島'].flatMap(track=>
  Array.from({length:12},(_,i)=>({track,race:i+1})));
 data.races=coords.map(({track,race},i)=>i===0?structuredClone(first):{
  ...structuredClone(first),track,race,status:'hold',
  reason:'after_provisional_off',runners:[],first:[],second:[],third:[],
  tickets:[],points:0,amountYen:0
 });
 data.raceCount=36;data.draftCount=1;data.holdCount=35;
 data.holdReasons={after_provisional_off:35};
 data.tenFactorPreview.races=coords.map(({track,race},i)=>
  i===0?structuredClone(ten):{
   ...structuredClone(ten),track,race,runnerCount:0,horses:[],
   trainingLedRecheckNumbers:[]});
 data.tenFactorPreview.raceCount=36;
 data.raceContext.races=coords.map(({track,race})=>({
  ...structuredClone(context),track,race,
 }));
 data.raceContext.raceCount=36;
 data.raceContext.courseInfoPresentCount=coords.length;
 data.raceContext.goingAvailableCount=coords.length;
 data.sourcePassport.races=coords.map(({track,race},i)=>
  i===0?structuredClone(passport):{
   ...structuredClone(passport),track,race,draftStatus:'hold',
   programmeRunnerCount:0,provisionalTrainingCount:0,
   provisionalRecentCount:0,
  });
 data.sourcePassport.raceCount=36;
 return data;
}
function researchBand(samples,hits,complete){
 if(!complete)return ['未評価','incomplete_history'];
 if(samples<3)return ['未評価','sample_below_three'];
 if(samples===5&&hits===0)return ['C','observed_five_without_top_three'];
 if(hits>=2&&3*hits>=2*samples)return ['S','observed_two_thirds_top_three'];
 if(hits>=1&&3*hits>=samples)return ['A','observed_one_third_top_three'];
 return ['B','observed_limited_top_three'];
}
function populateHistoricalBands(report){
 const history=report.ownerRunnerHistory;
 report.historicalEvidenceBands={
  version:'owner-condition-evidence-hypothesis-1',
  sourceVersion:'owner-runner-course-going-observation-2',
  minComparableSamples:3,courseDistanceWeight:20,goingWeight:12,
  evidenceBandsNotSuitability:true,negativeBandNeverExcludesRebound:true,
  researchOnly:true,privateOwnerOnly:true,officialJraVerified:false,
  overallScoreReady:false,winnerPickReady:false,bettingReady:false,
  raceCount:history.raceCount,
  races:history.races.map(row=>({
   track:row.track,race:row.race,runnerCount:row.runnerCount,
   overallScoreReady:false,winnerPickReady:false,
   runners:row.runners.map(h=>{
    const c=researchBand(h.comparableRuns,h.comparableTopThreeRuns,
     h.historyLookupComplete);
    const g=!h.currentGoingRecorded?['未評価','current_going_unknown']:
     !h.historyLookupComplete||h.knownGoingRuns!==h.comparableRuns
      ?['未評価','incomplete_history']
      :researchBand(h.matchingCurrentGoingRuns,
        h.matchingCurrentGoingTopThreeRuns,true);
    return {number:h.number,courseEvidenceBand:c[0],courseReason:c[1],
      goingEvidenceBand:g[0],goingReason:g[1]};
   })
  }))
 };
 return report;
}
function populatePace(report){
 const paceRaces=report.ownerRunnerHistory.races.map(row=>{
  const proposed=row.runners.map(h=>({
   number:h.number,pastFourthCorner:runners.find(x=>x.number===h.number)
    ?.pastFourthCorner||'insufficient'
  }));
  const count=label=>proposed.filter(x=>x.pastFourthCorner===label).length;
  const front=count('frontObserved'),back=count('backObserved'),
        mixed=count('mixedObserved'),unknown=count('insufficient');
  const adequate=row.runnerCount>=3&&(row.runnerCount-unknown)>=3&&
   5*(row.runnerCount-unknown)>=3*row.runnerCount;
  const scenario=!adequate?'coverage_insufficient':front===0?'no_front_observed':
   front===1?'single_front_observed':front===2?'two_front_observed':
   'multiple_front_observed';
  const rows=proposed.map(v=>{
   let band='未評価',reason='insufficient_position_coverage';
   if(adequate&&v.pastFourthCorner!=='insufficient'){
    if(scenario==='single_front_observed'){
     [band,reason]=v.pastFourthCorner==='frontObserved'?
       ['S','possible_single_front_advantage']:
       ['B','low_observed_front_pressure'];
    }else if(scenario==='two_front_observed'){
     [band,reason]=v.pastFourthCorner==='frontObserved'?
       ['A','two_front_candidates']:['B','uncertain_chase_scenario'];
    }else if(scenario==='multiple_front_observed'){
     [band,reason]=v.pastFourthCorner==='backObserved'?
       ['A','possible_late_run_if_pressured']:
       v.pastFourthCorner==='frontObserved'?
        ['B','multiple_front_candidates']:['B','mixed_position_under_pressure'];
    }else{
     [band,reason]=['未評価','no_observed_front_candidate'];
    }
   }
   return {...v,scenarioFitBand:band,reason};
  });
  return {track:row.track,race:row.race,runnerCount:row.runnerCount,
   frontObserved:front,backObserved:back,mixedObserved:mixed,
   insufficient:unknown,coverageAdequate:adequate,
   pacePressureScenario:scenario,runners:rows,
   paceForecastReady:false,gradeReady:false,bettingReady:false};
 });
 report.paceScenarioHypotheses={
  version:'owner-pace-scenario-hypothesis-1',raceCount:paceRaces.length,
  races:paceRaces,factorWeight:20,minObservedFieldShare:'3/5',
  minObservedRunners:3,researchOnly:true,privateOwnerOnly:true,
  officialJraVerified:false,scenarioNotActualPace:true,
  bandNotVerifiedFactorGrade:true,overallScoreReady:false,
  winnerPickReady:false,bettingReady:false
 };
 return report;
}
function populateReboundReview(report,sourceRunners=runners){
 const results=report.ownerRunnerHistory.races.map(row=>{
  const course=report.historicalEvidenceBands.races.find(
   x=>x.track===row.track&&x.race===row.race);
  const pace=report.paceScenarioHypotheses.races.find(
   x=>x.track===row.track&&x.race===row.race);
  const watch=sourceRunners.filter(h=>['S','A'].includes(h.training)&&
   ['B','C'].includes(h.recent)).map(h=>{
    const c=course.runners.find(x=>x.number===h.number);
    const p=pace.runners.find(x=>x.number===h.number);
    const bands={course_distance:c.courseEvidenceBand,
      pace:p.scenarioFitBand,ground:c.goingEvidenceBand};
    const factors=['course_distance','pace','ground'];
    const supports=factors.filter(k=>['S','A'].includes(bands[k]));
    const missing=factors.filter(k=>bands[k]==='未評価');
    const cross=supports.includes('pace')&&(
      supports.includes('course_distance')||supports.includes('ground'));
    const overlap=!cross&&supports.includes('course_distance')&&
      supports.includes('ground');
    return {number:h.number,trainingProvisional:h.training,
     recentProvisional:h.recent,courseEvidenceBand:bands.course_distance,
     paceScenarioBand:bands.pace,goingEvidenceBand:bands.ground,
     supportingContextFactors:supports,unassessedContextFactors:missing,
     contextSignalCount:supports.length,
     reviewState:cross?'cross_source_review':
       overlap?'overlapping_history_only':'need_more_evidence',
     evidenceOnly:true,winPickReady:false};
   }).sort((a,b)=>a.number-b.number);
   return {track:row.track,race:row.race,runnerCount:row.runnerCount,
    watchCount:watch.length,watch,winPickReady:false,gradedTenFactors:0};
 });
 report.reboundContextReview={
  version:'owner-rebound-context-review-1',policyVersion:'research-5',
  raceCount:results.length,watchCount:results.reduce((n,r)=>n+r.watchCount,0),
  crossSourceReviewCount:results.reduce((n,r)=>n+
    r.watch.filter(h=>h.reviewState==='cross_source_review').length,0),
  races:results,factorWeights:{
   training:30,recent:3,course_distance:20,pace:20,ground:12
  },
  researchOnly:true,privateOwnerOnly:true,officialJraVerified:false,
  overallScoreReady:false,winPickReady:false,bettingReady:false,
  autoPurchase:false,modifiesFrozenPicks:false,
  contextRequiresPaceAndHistory:true,historyOnlySignalsMayOverlap:true
 };
 return report;
}
function populateCapture(report){
 const row=report.reboundContextReview.races[0];
 const originals=row.watch.map(x=>({number:x.number,reviewState:x.reviewState}));
 report.watchCapture={
  version:'owner-rebound-watch-receipt-1',date:day,
  serverSigned:true,officialFeedConnected:false,jraScheduleVerified:false,
  officialResultsVerified:false,actualPurchase:false,purchaseReady:false,
  receiptCount:originals.length?1:0,postOffOrMissingTimeRaces:0,
  receipts:originals.length?[{
   snapshot:{version:'owner-rebound-watch-receipt-1',date:day,
    track:'東京',race:1,sourceKind:'server-prestart-research-watch',
    capturedAt:'2099-01-01T00:00:00+00:00',
    scheduledOffAt:'2099-01-01T03:00:00+00:00',
    watch:originals,researchOnly:true,officialJraVerified:false,
    actualPurchase:false,winnerPickReady:false,captureAuditVerified:false
   },signature:'a'.repeat(64)}]:[]
 };
 return report;
}
function historical(){
 return populateCapture(populateReboundReview(populatePace(populateHistoricalBands({
  version:'bounded-history-1',date:day,predictionReady:false,
  goingSuitabilityAssessed:false,historyComplete:false,
  referencedPastRaces:2,selectedPastRaces:1,deferredPastRaces:1,
  draCalls:1,dkaCalls:1,maxTotalCalls:16,
  privateHistoryFactors:{
   version:'private-course-ground-materials-1',raceCount:1,
   predictionReady:false,bettingReady:false,
   races:[{track:'東京',race:1,runnerCount:7,
    predictionReady:false,bettingReady:false,suitabilityAssessed:false,
    overallRankReady:false,verifiedFactorCount:0,
    observationOnlyFactors:['pace','course_distance','ground'],
    runnersWithComparableCourse:5,runnersWithKnownGoingComparable:3,
    runnersWithWetComparable:2,runnersMatchingCurrentGoing:2,
    runnersWithIncompleteHistory:3}]
  },
  ownerRunnerHistory:{
   version:'owner-runner-course-going-observation-2',raceCount:1,
   researchOnly:true,privateOwnerOnly:true,officialJraVerified:false,
   gradeReady:false,predictionReady:false,bettingReady:false,
   races:[{
    track:'東京',race:1,runnerCount:7,gradeReady:false,
    courseSuitabilityAssessed:false,goingSuitabilityAssessed:false,
    paceForecastReady:false,
    runners:[1,2,3,4,5,6,7].map(number=>({
     number,comparableRuns:number<=5?1:0,
     comparableTopThreeRuns:number===4?1:0,
     knownGoingRuns:number<=3?1:0,
     matchingCurrentGoingRuns:number<=2?1:0,
     matchingCurrentGoingTopThreeRuns:number===2?1:0,
     wetGoingRuns:number<=2?1:0,
     wetTopThreeRuns:number===2?1:0,missingPastProgrammes:0,
     historyLookupComplete:false,currentGoingRecorded:true
    }))
   }]
  },
  realAssessmentPreflight:{
   version:'real-assessment-preflight-1',realGradeReady:false,
   realPredictionReady:false,purchaseReady:false
  }
 }))));
}
function withFiveFactor(report){
 const original=report.historicalEvidenceBands.races[0].runners;
 const pace=report.paceScenarioHypotheses.races[0].runners;
 const cards=original.map(row=>{
  const match=pace.find(p=>p.number===row.number);
  const current=runners.find(h=>h.number===row.number);
  return {
   number:row.number,
   bands:{
    training:current.training,recent:current.recent,
    course_distance:row.courseEvidenceBand,
    pace:match.scenarioFitBand,ground:row.goingEvidenceBand
   },
   explanations:{
    course_distance:row.courseReason,
    pace:match.reason,ground:row.goingReason
   },
   actualGradesVerified:0,overallScore:null,overallRank:null
  };
 });
 const keys=['training','recent','course_distance','pace','ground'];
 const weights=[30,3,20,20,12];
 report.fiveFactorHypotheses={
  version:'owner-five-factor-hypotheses-1',policyVersion:'research-5',
  raceCount:1,factors:keys.map((key,i)=>({key,weight:weights[i]})),
  hypothesisBandsNotVerifiedGrades:true,
  materialCoverageDoesNotMeanPrediction:true,
  researchOnly:true,privateOwnerOnly:true,officialJraVerified:false,
  overallPredictionReady:false,verifiedFactorCount:0,
  bettingReady:false,autoPurchase:false,
  races:[{
   track:'東京',race:1,runnerCount:cards.length,
   verifiedFactorCount:0,overallReady:false,bettingReady:false,
   bandsPresentByFactor:Object.fromEntries(keys.map(k=>[
    k,cards.filter(x=>x.bands[k]!=='未評価').length])),
   runners:cards
  }]
 };
 return report;
}
function withTenFactor(report){
 withFiveFactor(report);
 const five=report.fiveFactorHypotheses.races[0].runners;
 const items=five.map(x=>({
  number:x.number,provisionalBands:{...x.bands},
  sourceStates:{
   pedigree:x.number===1?'complete_fields_observed':'partial_fields_observed',
   draw_weight:'complete_fields_observed',
   jockey_stable:'complete_fields_observed',
   rotation:x.number<=4?'days14to55':'unknown',
   body_condition:'race_day_bodyweight_unavailable'
  },
  bodyShapeCodePresent:x.number===1,
  verifiedGrades:0,overallScore:null,overallRank:null
 }));
 const count=key=>items.filter(h=>key==='rotation'
  ?h.sourceStates.rotation!=='unknown':
  key==='body_condition'?false:
   h.sourceStates[key]==='complete_fields_observed').length;
 const weights=Object.fromEntries(POLICY.map(row=>[row[0],row[2]]));
 report.tenFactorSourceInventory={
  version:'owner-ten-factor-source-inventory-1',policyVersion:'research-5',
  raceCount:1,factorCount:10,totalWeight:100,factorWeights:weights,
  independentJraVerified:false,overallPredictionReady:false,
  verifiedGrades:0,researchOnly:true,privateOwnerOnly:true,
  bettingReady:false,autoPurchase:false,
  races:[{
   track:'東京',race:1,runnerCount:items.length,runners:items,
   remainingFieldCoverage:Object.fromEntries(
    ['pedigree','draw_weight','jockey_stable','rotation','body_condition']
      .map(k=>[k,count(k)])),
   verifiedGrades:0,overallReady:false,independentJraVerified:false,
   bettingReady:false
  }]
 };
 return report;
}
function prestart(){
 return {
  version:'private-prestart-body-1',date:day,raceCount:1,
  races:[{
   track:'東京',race:1,registered:7,prestartRowsMatched:6,
   prestartRowsMissing:1,bodyWeightRecords:4,weightChangeRecords:3,
   paddockRecords:3,bodyStateCodeRecords:2,providerWithdrawnReports:0,
   sourceDataUpdatedAtVerified:false,officialBodyWeightVerified:false,
   bodyConditionGraded:false,realPredictionReady:false,ticketReady:false
  }],
  summary:{matchedRows:6,weightRecords:4,paddockRecords:3,missingRows:1},
  sourceRequestsRequired:['tra','tky','tpd'],rawHorseRecordsIncluded:false,
  oddsUsed:false,officialBodyWeightVerified:false,bodyConditionGraded:false,
  realPredictionReady:false,purchaseReady:false
 };
}
function boot(){
 const storage=new Map(),elements=new Map(),requests=[];
 let next=resultWith('a'.repeat(64)),historicalResponse=historical(),
  historyOk=true,providerCorrupt=false,holdFetch=null,
  prestartResponse=prestart(),prestartOk=true,
  configured=true,connectionOK=true,connectionCount=1,
  receiptVerificationOk=true,archiveReady=false,archiveCorrupt=false,
  autoDraftOk=true,officialPdfLinks=[{track:'東京',
    url:'https://www.jra.go.jp/keiba/rpdf/2026/sample-tokyo.pdf'}],
  officialPdfOk=true;
 let now='2099-01-01T00:00:00Z',onVisibility=null;
 function node(tag){
  return {
   tag,children:[],textContent:'',className:'',value:'',disabled:false,
   dataset:{},onclick:null,role:null,
   append(...children){this.children.push(...children)},
   replaceChildren(...children){this.children=children},
   setAttribute(k,v){this[k]=v},
   querySelectorAll(name){return this.children.filter(x=>x.tag===name)},
  };
 }
 function get(id){if(!elements.has(id))elements.set(id,node('div'));return elements.get(id)}
 const document={
  visibilityState:'visible',
  getElementById:get,createElement:node,createDocumentFragment:()=>node('fragment'),
  addEventListener:(name,fn)=>{if(name==='visibilitychange')onVisibility=fn}
 };
 const localStorage={
  getItem:k=>storage.get(k)||null,
  setItem(k,v){storage.set(k,v)},
 };
 const fetch=async(url,options)=>{
  requests.push({url,options});
  const pause=holdFetch;holdFetch=null;
  if(pause)await pause;
  if(url.startsWith('/api/jra/official-pdf-links?')){
   return {ok:officialPdfOk,json:async()=>({
    version:'jra-official-pdf-link-discovery-1',
    date:new URL('http://localhost'+url).searchParams.get('date'),
    indexUrl:'https://www.jra.go.jp/keiba/rpdf/',
    links:structuredClone(officialPdfLinks),
    linkFound:officialPdfLinks.length>0,pdfContentsRead:false,
    officialRunnerNumbersVerified:false,entryChangeVerified:false,
    predictionReady:false,bettingReady:false,
   })};
  }
  if(url==='/api/setup')return {ok:true,json:async()=>({
   jrdbConfigured:configured,liveConnectionVerified:false,
   realPredictionEnabled:false,prestartBodyEnabled:false
  })};
  if(url.startsWith('/api/jrdb/connection-test?'))return {
   ok:connectionOK,json:async()=>({
    date:day,connectionVerified:true,predictionReady:false,
    providerDataStored:false,programmeCount:connectionCount
   })
  };
  if(url==='/api/jrdb/history')
   return {ok:historyOk,json:async()=>structuredClone(historicalResponse)};
  if(url.startsWith('/api/jrdb/prestart-body?'))
   return {ok:prestartOk&&url.endsWith('date='+day),
    json:async()=>structuredClone(prestartResponse)};
  if(url.startsWith('/api/owner-archive-read?')){
   if(!archiveReady)return {ok:true,json:async()=>({
    archiveEnabled:false,persistentStorageReady:false,available:false,
    raceCount:0,receipts:[],actualPurchase:false,
    officialScheduleVerified:false,captureAuditVerified:false,
    officialFeedConnected:false
   })};
   const requested=new URL('http://localhost'+url).searchParams.get('date');
   const rows=JSON.parse(storage.get(STORAGE)||'[]').filter(
    r=>r.snapshot.date===requested);
   const saved=structuredClone(rows);
   if(archiveCorrupt&&saved.length)saved[0].snapshot.trifectaTickets[0][0]=19;
   return {ok:true,json:async()=>({
    archiveEnabled:true,persistentStorageReady:true,available:saved.length>0,
    raceCount:saved.length,receipts:saved,actualPurchase:false,
    officialScheduleVerified:false,captureAuditVerified:false,
    officialFeedConnected:false
   })};
  }
  if(url==='/api/owner-100yen-verify-receipts'){
   const args=JSON.parse(options.body);
   const signed=args.receipts;
   const valid=receiptVerificationOk&&Array.isArray(signed)&&signed.length>0&&
    signed.every(x=>x.signature==='a'.repeat(64));
   return {ok:valid,json:async()=>valid?{
    available:true,serverSigned:true,captureAuditVerified:false,
    officialScheduleVerified:false,officialFeedConnected:false,
    review:{version:'keiba-100yen-review-1',unitYen:100,actualPurchase:false,
      reviewedRaces:0,pendingRaces:signed.length,totalInvestedYen:0,
      totalReturnedYen:0,roiPercent:null,
      races:signed.map(x=>({status:'pending',track:x.snapshot.track,
       race:x.snapshot.race,date:x.snapshot.date}))}
   }:{error:'server_authorization_failure'}};
  }
  if(url==='/api/owner-rebound-verify'){
   const args=JSON.parse(options.body);
   return {ok:true,json:async()=>({
    available:true,serverSigned:true,jraScheduleVerified:false,
    officialFeedConnected:false,
    review:{reviewedRaces:0,pendingRaces:args.receipts.length,
      outcomeCalibrationReady:false}
   })};
  }
  if(url==='/api/owner-rebound-provider-check'){
   const args=JSON.parse(options.body);
   const snap=args.receipts[0].snapshot;
   const horse=snap.watch[0];
   return {ok:true,json:async()=>({
    version:'owner-rebound-provider-check-1',date:args.date,
    sourceKind:'jrdb-tse-provider-observation',
    providerSourceReadCount:1,raceCount:args.receipts.length,
    races:args.receipts.map((receipt,i)=>({
     track:receipt.snapshot.track,race:receipt.snapshot.race,
     watchCount:receipt.snapshot.watch.length,
     providerStatus:i===0?'first_place_observed':'pending',
     observedFirstNumber:i===0?horse.number:null,
     observedFirstInWatch:i===0?true:null,
     observedFirstInPriorityWatch:i===0?
      horse.reviewState==='cross_source_review':null,
     officialVerified:false,confirmedWatchHit:null,
     confirmedPredictionHit:null
    })),
    observedRaceCount:1,observedFirstInWatchCount:1,
    observedFirstInPriorityCount:horse.reviewState==='cross_source_review'?1:0,
    verifiedRaceCount:0,verifiedWatchHitCount:null,
    officialJraVerified:providerCorrupt?true:false,
    jraIndependentConfirmation:false,officialFeedConnected:false,
    outcomeCalibrationReady:false,bettingReady:false,actualPurchase:false,
    payoutVerified:false,roiPercent:null,
    sourceIncompleteCouldChange:true,researchOnly:true,
    privateOwnerOnly:true
   })};
  }
  if(url.startsWith('/api/jrdb/owner-auto-draft?')&&!autoDraftOk)
   return {ok:false,json:async()=>({error:'temporary_provider_unavailable'})};
  return {ok:true,json:async()=>structuredClone(next)};
 };
 class FakeDate extends Date{
  constructor(...args){super(...(args.length?args:[now]))}
 }
 const context={document,localStorage,fetch,Intl,URL,Date:FakeDate,JSON,Set,Map,Number,
  String,Array,Error,Promise,Object};
 vm.runInNewContext(js,context);
 get('autoDay').value=date;
 return {get,storage,requests,setServer:x=>next=withTenPreview(x),
  setServerRaw:x=>next=x,
  setAutoDraftOk:x=>autoDraftOk=x,
  setHistorical:x=>historicalResponse=x,setHistoryOk:x=>historyOk=x,
  setPrestart:x=>prestartResponse=x,setPrestartOk:x=>prestartOk=x,
  setConfigured:x=>configured=x,setConnectionOK:x=>connectionOK=x,
  setReceiptVerificationOk:x=>receiptVerificationOk=x,
  setArchiveReady:x=>archiveReady=x,
  setArchiveCorrupt:x=>archiveCorrupt=x,
  setOfficialPdfLinks:x=>officialPdfLinks=x,
  setOfficialPdfOk:x=>officialPdfOk=x,
  setConnectionCount:x=>connectionCount=x,
  setProviderCorrupt:x=>providerCorrupt=x,
  waitNextFetch:promise=>{holdFetch=promise},
  advanceClock:iso=>{now=iso},resume:()=>{if(onVisibility)onVisibility()}};
}
(async()=>{
 const a=boot();
 // Visiting the owner-only page triggers the first read automatically.
 await new Promise(r=>setImmediate(r));
 assert.equal(a.requests.length,1);
 assert.equal(a.get('autoRun').disabled,false);
 assert.equal(a.get('autoHistoryAudit').disabled,false);
 // JRDB connection probe is a deliberate, independently limited action.
 assert.equal(a.requests.filter(r=>r.url==='/api/setup').length,0);
 assert.equal(a.requests.filter(r=>
  r.url.startsWith('/api/jrdb/connection-test?')).length,0);
 const receiptBeforeConnection=a.storage.get(STORAGE);
 await a.get('autoConnectionCheck').onclick();
 assert.equal(a.requests.filter(r=>r.url==='/api/setup').length,1);
 const sourceChecks=a.requests.filter(r=>
  r.url.startsWith('/api/jrdb/connection-test?'));
 assert.equal(sourceChecks.length,1);
 assert.equal(sourceChecks[0].url,'/api/jrdb/connection-test?date='+day);
 assert.equal(sourceChecks[0].options.credentials,'same-origin');
 assert.match(a.get('autoConnectionStatus').textContent,/接続成功：1R/);
 assert.equal(a.storage.get(STORAGE),receiptBeforeConnection);
 a.setConfigured(false);
 await a.get('autoConnectionCheck').onclick();
 assert.equal(a.requests.filter(r=>
  r.url.startsWith('/api/jrdb/connection-test?')).length,1);
 assert.match(a.get('autoConnectionStatus').textContent,/設定が未完了/);
 a.setConfigured(true);
 a.setConnectionOK(false);
 await a.get('autoConnectionCheck').onclick();
 assert.match(a.get('autoConnectionStatus').textContent,/接続確認ができません/);
 a.setConnectionOK(true);
 a.setConnectionCount(0);
 await a.get('autoConnectionCheck').onclick();
 assert.match(a.get('autoConnectionStatus').textContent,/開催レース0件/);
 const requestsBeforeWrongDate=a.requests.length;
 a.get('autoDay').value='2099-02-31';
 await a.get('autoConnectionCheck').onclick();
 assert.equal(a.requests.length,requestsBeforeWrongDate);
 assert.match(a.get('autoConnectionStatus').textContent,/正しく選択/);
 a.get('autoDay').value=date;
 assert.equal(a.storage.get(STORAGE),receiptBeforeConnection);
 // JRA PDF discovery must be explicitly requested, use the chosen
 // day, render only official PDF links, and never claim runner verification.
 const jraButton=a.get('autoOfficialPdf');
 assert.equal(a.requests.filter(r=>
  r.url.startsWith('/api/jra/official-pdf-links?')).length,0);
 const picksBeforePdf=a.storage.get(STORAGE),requestsBeforePdf=a.requests.length;
 await jraButton.onclick();
 assert.equal(a.requests.length,requestsBeforePdf+1);
 const officialReq=a.requests.find(r=>
  r.url.startsWith('/api/jra/official-pdf-links?'));
 assert.equal(officialReq.url,'/api/jra/official-pdf-links?date=2099-01-01');
 assert.equal(officialReq.options.credentials,'same-origin');
 assert.equal(officialReq.options.headers['X-Keiba-Request'],'private');
 assert.equal(a.get('autoOfficialPdfLinks').children.length,1);
 assert.equal(a.get('autoOfficialPdfLinks').children[0].href,
  'https://www.jra.go.jp/keiba/rpdf/2026/sample-tokyo.pdf');
 assert.equal(a.get('autoOfficialPdfLinks').children[0].rel,
  'noopener noreferrer');
 assert.match(a.get('autoOfficialPdfStatus').textContent,/馬番・取消・馬場・発走時刻は自動照合していません/);
 assert.equal(a.storage.get(STORAGE),picksBeforePdf);
 a.setOfficialPdfLinks([]);
 await jraButton.onclick();
 assert.match(a.get('autoOfficialPdfStatus').textContent,/まだ検出できません/);
 assert.equal(a.get('autoOfficialPdfLinks').children.length,0);
 for(const bad of [
  'https://evil.test/keiba/rpdf/card.pdf',
  'http://www.jra.go.jp/keiba/rpdf/card.pdf',
  'https://www.jra.go.jp/keiba/rpdf/card.pdf?spoof=1',
  'https://www.jra.go.jp/keiba/rpdf/card.html',
 ]){
  a.setOfficialPdfLinks([{track:'東京',url:bad}]);
  await jraButton.onclick();
  assert.equal(a.get('autoOfficialPdfLinks').children.length,0);
  assert.match(a.get('autoOfficialPdfStatus').textContent,/確認できませんでした/);
 }
 a.setOfficialPdfLinks([
  {track:'東京',url:'https://www.jra.go.jp/keiba/rpdf/2026/sample-a.pdf'},
  {track:'東京',url:'https://www.jra.go.jp/keiba/rpdf/2026/sample-b.pdf'},
 ]);
 await jraButton.onclick();
 assert.equal(a.get('autoOfficialPdfLinks').children.length,0);
 assert.match(a.get('autoOfficialPdfStatus').textContent,/確認できませんでした/);
 a.setOfficialPdfLinks([
  {track:'東京',url:'https://www.jra.go.jp/keiba/rpdf/2026/sample-tokyo.pdf'},
 ]);
 a.setOfficialPdfOk(false);
 await jraButton.onclick();
 assert.equal(a.get('autoOfficialPdfLinks').children.length,0);
 a.setOfficialPdfOk(true);
 assert.equal(a.storage.get(STORAGE),picksBeforePdf);
 assert.equal(a.requests.filter(r=>
  r.url.startsWith('/api/jrdb/owner-auto-draft?')).length,1);
 // Separate iPhone instance: switching dates while an official HTML
 // index request is slow must not restore an old day's links. Keep the
 // primary fixture's history state intact for existing research tests.
 const pdfStale=boot();
 await new Promise(r=>setImmediate(r));
 const localBeforeStale=pdfStale.storage.get(STORAGE);
 let releaseJra;
 const pauseJra=new Promise(resolve=>{releaseJra=resolve});
 pdfStale.waitNextFetch(pauseJra);
 const lateJra=pdfStale.get('autoOfficialPdf').onclick();
 assert.equal(pdfStale.get('autoOfficialPdf').disabled,true);
 pdfStale.get('autoDay').value='2099-01-02';
 pdfStale.get('autoDay').onchange();
 assert.equal(pdfStale.get('autoOfficialPdf').disabled,false);
 assert.equal(pdfStale.get('autoOfficialPdfLinks').children.length,0);
 releaseJra();
 await lateJra;
 assert.equal(pdfStale.get('autoOfficialPdfLinks').children.length,0);
 assert.match(pdfStale.get('autoOfficialPdfStatus').textContent,/未確認/);
 assert.equal(pdfStale.storage.get(STORAGE),localBeforeStale);
 // No paid body source read until an explicit owner click.
 assert.equal(a.requests.filter(x=>x.url.startsWith('/api/jrdb/prestart-body?')).length,0);
 const beforeBody=a.storage.get(STORAGE);
 await a.get('autoPrestartBody').onclick();
 const bodyRequests=a.requests.filter(x=>x.url.startsWith('/api/jrdb/prestart-body?'));
 assert.equal(bodyRequests.length,1);
 assert.equal(bodyRequests[0].url,'/api/jrdb/prestart-body?date='+day);
 assert.equal(bodyRequests[0].options.credentials,'same-origin');
 assert.equal(a.get('autoPrestartRaces').children.length,1);
 assert.match(a.get('autoPrestartStatus').textContent,/馬体重記録 4頭/);
 assert.match(a.get('autoPrestartRaces').children[0].children[1].textContent,/JRA公式未確認/);
 assert.equal(a.storage.get(STORAGE),beforeBody);
 const wrongBody=prestart();
 wrongBody.races[0].bodyWeightRecords=18;
 a.setPrestart(wrongBody);
 await a.get('autoPrestartBody').onclick();
 assert.equal(a.get('autoPrestartRaces').children.length,0);
 assert.match(a.get('autoPrestartStatus').textContent,/照合できません/);
 assert.equal(a.storage.get(STORAGE),beforeBody);
 a.setPrestart(prestart());
 a.get('autoDay').value='2099-01-02';
 const callsBefore=a.requests.length;
 await a.get('autoPrestartBody').onclick();
 // The authenticated server rejects the mismatched day before reading JRDB.
 assert.equal(a.requests.length,callsBefore+1);
 assert.match(a.get('autoPrestartStatus').textContent,/照合できません/);
 a.get('autoDay').value=date;
 // History has strict user opt-in. Automatic page load must not fetch it.
 assert.equal(a.requests.filter(r=>r.url==='/api/jrdb/history').length,0);
 const oldRecord=a.storage.get(STORAGE);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.requests.filter(r=>r.url==='/api/jrdb/history').length,1);
 assert.equal(a.requests.filter(r=>r.url==='/api/owner-rebound-verify').length,1);
 const capturedFirst=a.storage.get('keiba-nine-owner-rebound-watch-receipts-v1');
 assert.ok(capturedFirst);
 assert.equal(JSON.parse(capturedFirst).length,1);
 assert.match(a.get('autoHistoryWatchSave').textContent,/新規 1R/);
 assert.equal(a.get('autoWatchResultCheck').disabled,false);
 assert.equal(a.requests.filter(r=>
  r.url==='/api/owner-rebound-provider-check').length,0,
  'never fetch postrace results automatically');
 await a.get('autoWatchResultCheck').onclick();
 assert.equal(a.requests.filter(r=>
  r.url==='/api/owner-rebound-provider-check').length,1);
 const providerRequest=a.requests.find(r=>
  r.url==='/api/owner-rebound-provider-check');
 assert.equal(providerRequest.options.method,'POST');
 assert.equal(providerRequest.options.credentials,'same-origin');
 assert.deepEqual(Object.keys(JSON.parse(providerRequest.options.body)).sort(),
  ['date','receipts']);
 assert.match(a.get('autoWatchResultStatus').textContent,/JRA公式照合が未完了/);
 assert.match(a.get('autoWatchResultRaces').children[0].children[1].textContent,
  /JRA公式未確認/);
 assert.equal(a.storage.get('keiba-nine-owner-rebound-watch-receipts-v1'),
  capturedFirst);
 a.setProviderCorrupt(true);
 await a.get('autoWatchResultCheck').onclick();
 assert.equal(a.get('autoWatchResultRaces').children.length,0);
 assert.match(a.get('autoWatchResultStatus').textContent,/暫定照合ができません/);
 assert.equal(a.storage.get('keiba-nine-owner-rebound-watch-receipts-v1'),
  capturedFirst);
 a.setProviderCorrupt(false);
 const auditRequest=a.requests.find(r=>r.url==='/api/jrdb/history');
 assert.equal(auditRequest.options.method,'POST');
 assert.equal(auditRequest.options.credentials,'same-origin');
 assert.equal(JSON.parse(auditRequest.options.body).limit,8);
 assert.equal(JSON.parse(auditRequest.options.body).date,day);
 assert.equal(a.get('autoHistoryAuditRaces').children.length,1);
 assert.match(a.get('autoHistoryAuditStatus').textContent,/予想・購入・保存済み/);
 const historyCard=a.get('autoHistoryAuditRaces').children[0];
 const horsePanel=historyCard.children.find(x=>x.tag==='details'&&
  /馬番ごとの同条件実績/.test(x.children[0]?.textContent||''));
 assert.ok(horsePanel);
 assert.equal(horsePanel.children.length,8);
 assert.match(horsePanel.children[4].textContent,/4番.*3着以内 1回/);
 assert.match(horsePanel.children[4].textContent,/巻き返し再審査対象/);
 assert.match(horsePanel.children[4].textContent,/研究目安 未評価/);
 assert.match(historyCard.children[4].textContent,/過去4角の観測/);
 assert.match(historyCard.children[4].textContent,/位置取りの資料不足/);
 assert.match(horsePanel.children[4].textContent,/展開シナリオの研究目安 未評価/);
 const reboundPanel=historyCard.children.find(x=>x.tag==='details'&&
  /巻き返し再審査/.test(x.children[0]?.textContent||''));
 assert.ok(reboundPanel);
 assert.match(reboundPanel.children[1].textContent,/4番.*調教 A・近走 B/);
 assert.match(reboundPanel.children[1].textContent,/根拠不足/);
 assert.match(reboundPanel.children[1].textContent,/買い目変更なし/);
 // The provisional 3-to-5-run good-condition score is NOT a real
 // ranking, ticket or 10-factor score.
 // Five-factor overlay must match already-validated source hypotheses
 // and cannot mutate saved research tickets or claim a 10-factor score.
 a.setHistorical(withFiveFactor(historical()));
 await a.get('autoHistoryAudit').onclick();
 const fivePanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/馬番別5項目/.test(x.children[0]?.textContent||''));
 assert.ok(fivePanel);
 assert.equal(fivePanel.children.length,9);
 assert.match(fivePanel.children[2].textContent,/1番｜調教 S／近走 S/);
 assert.match(fivePanel.children[2].textContent,/研究用・総合点なし/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 // Ten-source inventory: all ten slots can be inspected without turning
 // a present field into a grade or modifying an earlier signed 3連単.
 a.setHistorical(withTenFactor(historical()));
 await a.get('autoHistoryAudit').onclick();
 const tenPanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/10項目の資料状況/.test(x.children[0]?.textContent||''));
 assert.ok(tenPanel);
 assert.equal(tenPanel.children.length,9);
 assert.match(tenPanel.children[2].textContent,/1番｜血統 資料あり/);
 assert.match(tenPanel.children[2].textContent,/当日馬体重未取得/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 const tamperedTen=withTenFactor(historical());
 tamperedTen.tenFactorSourceInventory.races[0].runners[0]
  .sourceStates.body_condition='good_bodyweight';
 a.setHistorical(tamperedTen);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
 const alteredFive=withFiveFactor(historical());
 alteredFive.fiveFactorHypotheses.races[0].runners[0].bands.ground='S';
 a.setHistorical(alteredFive);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
 a.setHistorical(historical());
 const positive=historical();
 positive.historyComplete=true;
 positive.referencedPastRaces=3;
 positive.selectedPastRaces=3;
 positive.deferredPastRaces=0;
 positive.draCalls=3;
 positive.dkaCalls=2;
 positive.privateHistoryFactors.races[0].runnersWithIncompleteHistory=0;
 for(const h of positive.ownerRunnerHistory.races[0].runners)
  h.historyLookupComplete=true;
 const rebound=positive.ownerRunnerHistory.races[0].runners[3];
 rebound.comparableRuns=3;
 rebound.comparableTopThreeRuns=2;
 rebound.knownGoingRuns=3;
 rebound.matchingCurrentGoingRuns=3;
 rebound.matchingCurrentGoingTopThreeRuns=2;
 rebound.wetGoingRuns=3;
 rebound.wetTopThreeRuns=2;
 positive.privateHistoryFactors.races[0].runnersWithKnownGoingComparable=4;
 positive.privateHistoryFactors.races[0].runnersMatchingCurrentGoing=3;
 positive.privateHistoryFactors.races[0].runnersWithWetComparable=3;
 populateCapture(populateReboundReview(populateHistoricalBands(positive)));
 a.setHistorical(positive);
 await a.get('autoHistoryAudit').onclick();
 const reviewed=a.get('autoHistoryAuditRaces').children[0];
 const horseRows=reviewed.children.find(x=>x.tag==='details'&&
  /馬番ごとの同条件実績/.test(x.children[0]?.textContent||''));
 assert.match(horseRows.children[4].textContent,/コース好走実績の研究目安 S/);
 assert.match(horseRows.children[4].textContent,/今回馬場の研究目安 S/);
 assert.match(horseRows.children[4].textContent,/総合点と買い目には不反映/);
 const correlated=reviewed.children.find(x=>x.tag==='details'&&
  /巻き返し再審査/.test(x.children[0]?.textContent||''));
 assert.match(correlated.children[1].textContent,/同一過去走に基づく材料のみ/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 assert.equal(a.storage.get('keiba-nine-owner-rebound-watch-receipts-v1'),
  capturedFirst,'newer result must not replace first watch receipt');
 assert.match(a.get('autoHistoryWatchSave').textContent,/既存 1R/);
 a.setHistorical(historical());
 assert.match(a.get('autoHistoryAuditRaces').children[0].children[1].textContent,/5\/7頭/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 // Invalid observations must never render or rewrite frozen research.
 const malformed=historical();
 malformed.privateHistoryFactors.races[0].runnersWithComparableCourse=99;
 a.setHistorical(malformed);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 const badHypothesis=historical();
 badHypothesis.historicalEvidenceBands.races[0].runners[0].courseEvidenceBand='S';
 a.setHistorical(badHypothesis);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 const badPaceBand=historical();
 badPaceBand.paceScenarioHypotheses.races[0].runners[0].scenarioFitBand='S';
 a.setHistorical(badPaceBand);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 const badFrontCount=historical();
 badFrontCount.paceScenarioHypotheses.races[0].frontObserved=7;
 a.setHistorical(badFrontCount);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 const badCapture=historical();
 badCapture.watchCapture.receipts[0].snapshot.watch[0].reviewState='cross_source_review';
 a.setHistorical(badCapture);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.equal(a.storage.get('keiba-nine-owner-rebound-watch-receipts-v1'),capturedFirst);
 const badReview=historical();
 badReview.reboundContextReview.races[0].watch[0].reviewState='cross_source_review';
 a.setHistorical(badReview);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 const badJoin=historical();
 badJoin.reboundContextReview.races[0].watch[0].recentProvisional='S';
 a.setHistorical(badJoin);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 const mismatchedHorse=historical();
 mismatchedHorse.ownerRunnerHistory.races[0].runners[0].number=18;
 a.setHistorical(mismatchedHorse);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 const badDate=historical();
 badDate.date='20990102';
 a.setHistorical(badDate);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 a.setHistorical(historical());
 a.setHistoryOk(false);
 await a.get('autoHistoryAudit').onclick();
 assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
 a.setHistoryOk(true);
 assert.match(a.requests[0].url,/\/api\/jrdb\/owner-auto-draft\?date=20990101$/);
 assert.equal(a.requests[0].options.headers['X-Keiba-Request'],'private');
 assert.equal(a.get('autoSummary').textContent.includes('1R中、研究用自動案 1R'),true);
 assert.equal(a.get('autoTenWeights').children.length,10);
 assert.match(a.get('autoRaces').children[0].children[0].children[4].textContent,
  /調教30：近走3での仮順位/);
 assert.match(a.get('autoTenStatus').textContent,/残り8項目は未評価/);
 assert.match(a.get('autoSummary').textContent,/馬場資料の存在 1R/);
 assert.match(a.get('autoSourceSummary').textContent,/資料進捗：1R中/);
 assert.match(a.get('autoSourceSummary').textContent,/調教の仮評価がある馬 7頭/);
 assert.match(a.get('autoSourceSummary').textContent,/近走 7頭/);
 assert.match(a.get('autoSourceSummary').textContent,/コース条件 1R/);
 assert.match(a.get('autoSourceSummary').textContent,/当日馬場資料 1R/);
 assert.match(a.get('autoSourceSummary').textContent,/正式採点0\/10/);
 assert.match(a.get('autoSourceSummary').textContent,/買い目は変更しません/);
 assert.match(a.get('autoMorningStatus').textContent,/2099-01-01：番組 1R/);
 assert.match(a.get('autoMorningStatus').textContent,/研究用3連単下書き 1R／見送り 0R/);
 assert.match(a.get('autoMorningStatus').textContent,/10項目本採点.*未完了/);
 assert.match(a.get('autoMorningStatus').textContent,/サーバー永続保存は未設定/);
 const quickSingle=a.get('autoVenues').children.at(-1);
 assert.equal(quickSingle.dataset.mode,'drafts');
 assert.match(quickSingle.textContent,/下書きのみ 1R/);
 const requestsBeforeDraftOnly=a.requests.length;
 const receiptsBeforeDraftOnly=a.storage.get(STORAGE);
 quickSingle.onclick();
 assert.equal(a.get('autoRaces').children[0].children.length,1);
 assert.match(a.get('autoViewingStatus').textContent,/下書き 1Rを表示/);
 assert.equal(quickSingle['aria-pressed'],'true');
 assert.equal(a.requests.length,requestsBeforeDraftOnly);
 assert.equal(a.storage.get(STORAGE),receiptsBeforeDraftOnly);
 a.get('autoVenues').children[0].onclick();
 assert.equal(quickSingle['aria-pressed'],'false');
 // iPhone selector shows one race without refetching or editing a receipt.
 const selector=a.get('autoRacePick');
 assert.equal(selector.disabled,false);
 assert.equal(selector.children.length,2);
 assert.equal(selector.children[1].value,'東京|1');
 const originalRequests=a.requests.length;
 const frozenBeforeSelection=a.storage.get(STORAGE);
 selector.value='東京|1';
 selector.onchange();
 assert.match(a.get('autoViewingStatus').textContent,/選択中：東京 1R/);
 assert.equal(a.get('autoRaces').children[0].children.length,1);
 assert.equal(a.get('autoRaces').children[0].children[0].open,true);
 assert.equal(a.requests.length,originalRequests);
 assert.equal(a.storage.get(STORAGE),frozenBeforeSelection);
 selector.value='不正|19';
 selector.onchange();
 assert.equal(selector.value,'');
 assert.match(a.get('autoViewingStatus').textContent,/全場 1R/);
 assert.equal(a.requests.length,originalRequests);
 assert.equal(a.storage.get(STORAGE),frozenBeforeSelection);
 a.get('autoVenues').children[1].onclick();
 assert.match(a.get('autoViewingStatus').textContent,/東京 1R/);
 assert.equal(selector.value,'');
 a.get('autoVenues').children[0].onclick();
 assert.match(a.get('autoViewingStatus').textContent,/全場 1R/);

 assert.match(a.get('autoRaces').children[0].children[0].children[1].textContent,
  /芝／2000m／左／重（JRDB資料）/);
 assert.match(a.get('autoRaces').children[0].children[0].children[2].textContent,
  /過去4角の位置取り観測/);
 const firstDetail=a.get('autoRaces').children[0].children[0];
 assert.equal(firstDetail.children.filter(x=>x.className==='ten-horse').length,7);
 const firstTen=firstDetail.children.find(x=>x.className==='ten-horse');
 assert.match(firstTen.children[0].textContent,/総合 未評価/);
 assert.equal(firstTen.children[1].children.length,10);
 const watchText=a.get('autoRaces').children[0].children[0].children
  .map(x=>x.textContent||'').join(' ');
 assert.match(watchText,/巻き返し条件の確認待ち/);
 assert.match(watchText,/コース距離・展開・馬場を確認/);
 assert.match(firstTen.children[1].children[0].children[1].textContent,/S（仮）/);
 assert.match(firstTen.children[1].children[2].children[1].textContent,/未評価/);
 const sourcePanel=firstDetail.children.find(x=>x.className==='source-passport');
 assert.ok(sourcePanel);
 assert.match(sourcePanel.children[0].textContent,/正式採点0\/10/);
 assert.match(sourcePanel.children[1].textContent,/調教の仮評価 7頭/);
 assert.match(sourcePanel.children[2].textContent,/件数は照合保留/);
 assert.match(sourcePanel.children[3].textContent,/当日馬場情報 あり/);
 assert.match(sourcePanel.children[4].textContent,/未評価の8項目/);
 assert.match(sourcePanel.children[4].textContent,/コース・距離20点/);
 assert.match(sourcePanel.children[4].textContent,/馬体重1点/);
 const nextSteps=sourcePanel.children[5];
 assert.equal(nextSteps.className,'source-next');
 assert.match(nextSteps.children[0].textContent,/次に確認する資料/);
 assert.match(nextSteps.children[1].textContent,/血統・枠斤量・騎手厩舎・ローテ/);
 assert.match(nextSteps.children[2].textContent,/当日馬体重の確認/);
 assert.match(nextSteps.children[3].textContent,/根拠に基づく採点/);
 assert.match(nextSteps.children[4].textContent,/JRA公式.*独立照合/);
 assert.match(sourcePanel.children[6].textContent,/JRA公式.*未接続/);
 const tamperedPassport=resultWith('c'.repeat(64));
 tamperedPassport.sourcePassport.races[0].verifiedFactorCount=10;
 a.setServerRaw(tamperedPassport);
 const beforePassportFail=a.storage.get(STORAGE);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoTenStatus').textContent,/確認できません/);
 assert.equal(a.storage.get(STORAGE),beforePassportFail);
 assert.match(a.get('autoSourceSummary').textContent,/取得に失敗しました/);
 assert.match(a.get('autoMorningStatus').textContent,/新しい暫定予想は表示していません/);
 assert.match(a.get('autoFixedConsistency').textContent,/再分析結果は未確認/);
 // Do not rerun the original receipt: first-write-wins is intentional.
 // The next test below supplies its own response and preserves this record.
 assert.match(a.get('autoSavedStatus').textContent,/再分析に失敗.*固定済み研究記録 1R/);
 assert.equal(a.get('autoRaces').children.length,0);
 assert.equal(a.get('autoVenues').children.length,0);
 const firstSave=JSON.parse(a.storage.get(STORAGE));
 assert.equal(firstSave.length,1);
 assert.match(a.get('autoHistoryStatus').textContent,/固定 1R/);
 assert.equal(a.get('autoHistory').children.length,1);
 const history=a.get('autoHistory').children[0];
 assert.match(history.children[0].textContent,/3連単 40点/);
 assert.match(history.children[2].textContent,/1着候補：1・2番/);
 assert.match(history.children[5].textContent,/1→2→3/);
 assert.equal(firstSave[0].signature,'a'.repeat(64));
 assert.equal(firstSave[0].snapshot.trifectaTickets.length,40);
 // Authenticated on-demand verification of frozen receipts is deliberately
 // stateless. The client may not mistake it for persistent server storage,
 // actual purchases, ROI or an independently confirmed race schedule.
 const verifyBtn=a.get('autoReceiptVerify');
 assert.equal(a.get('autoDay').value,date);
 const requestsBeforeProof=a.requests.length;
 const unchangedBeforeProof=a.storage.get(STORAGE);
 assert.match(a.get('autoReceiptVerifyStatus').textContent,/未確認/);
 await verifyBtn.onclick();
 const receiptProofs=a.requests.filter(x=>
  x.url==='/api/owner-100yen-verify-receipts');
 assert.equal(receiptProofs.length,1);
 assert.equal(a.requests.length,requestsBeforeProof+1);
 assert.equal(receiptProofs[0].options.method,'POST');
 assert.equal(receiptProofs[0].options.credentials,'same-origin');
 assert.equal(receiptProofs[0].options.headers['X-Keiba-Request'],'private');
 assert.equal(receiptProofs[0].options.headers['Content-Type'],'application/json');
 assert.deepEqual(Object.keys(JSON.parse(receiptProofs[0].options.body)).sort(),
  ['date','receipts']);
 assert.match(a.get('autoReceiptVerifyStatus').textContent,/照合成功：1R/);
 assert.match(a.get('autoReceiptVerifyStatus').textContent,/サーバー保存は未検証/);
 assert.equal(a.storage.get(STORAGE),unchangedBeforeProof);
 a.setReceiptVerificationOk(false);
 await verifyBtn.onclick();
 assert.match(a.get('autoReceiptVerifyStatus').textContent,/確認できませんでした/);
 assert.equal(a.storage.get(STORAGE),unchangedBeforeProof);
 a.setReceiptVerificationOk(true);
 // A locally modified ticket must never be silently accepted by the server.
 const replacedRecord=JSON.parse(unchangedBeforeProof);
 replacedRecord[0].signature='f'.repeat(64);
 a.storage.set(STORAGE,JSON.stringify(replacedRecord));
 await verifyBtn.onclick();
 assert.match(a.get('autoReceiptVerifyStatus').textContent,/確認できませんでした/);
 assert.equal(a.storage.get(STORAGE),JSON.stringify(replacedRecord));
 a.storage.set(STORAGE,unchangedBeforeProof);
 // A selected day without receipts never sends any verification request.
 a.get('autoDay').value='2099-01-02';
 a.get('autoDay').onchange();
 const afterDaySwitch=a.requests.length;
 await verifyBtn.onclick();
 assert.equal(a.requests.length,afterDaySwitch);
 assert.match(a.get('autoReceiptVerifyStatus').textContent,/ありません/);
 a.get('autoDay').value='2099-01-01';
 a.get('autoDay').onchange();
 assert.equal(a.storage.get(STORAGE),unchangedBeforeProof);

 // Server archive viewer must be strictly opt-in and must never
 // create/replace research receipts, or claim disabled Postgres is enabled.
 assert.equal(a.requests.filter(x=>x.url.startsWith('/api/owner-archive-read?')).length,0);
 const savedBeforeArchive=a.storage.get(STORAGE);
 const archiveBtn=a.get('autoArchiveRead');
 await archiveBtn.onclick();
 assert.match(a.get('autoArchiveStatus').textContent,/永続保存は未設定/);
 assert.equal(a.get('autoArchiveRaces').children.length,0);
 assert.equal(a.storage.get(STORAGE),savedBeforeArchive);
 let archiveCalls=a.requests.filter(x=>
  x.url.startsWith('/api/owner-archive-read?'));
 assert.equal(archiveCalls.length,1);
 assert.equal(archiveCalls[0].url,'/api/owner-archive-read?date=2099-01-01');
 assert.equal(archiveCalls[0].options.credentials,'same-origin');
 a.setArchiveReady(true);
 await archiveBtn.onclick();
 archiveCalls=a.requests.filter(x=>
  x.url.startsWith('/api/owner-archive-read?'));
 assert.equal(archiveCalls.length,2);
 assert.match(a.get('autoArchiveStatus').textContent,/サーバー保存済みの研究記録 1R/);
 assert.match(a.get('autoArchiveStatus').textContent,/iPhoneには書き戻していません/);
 assert.equal(a.get('autoArchiveRaces').children.length,1);
 assert.match(a.get('autoArchiveRaces').children[0].children[0].textContent,/東京 1R.*40点/);
 assert.equal(a.storage.get(STORAGE),savedBeforeArchive);
 a.setArchiveCorrupt(true);
 await archiveBtn.onclick();
 assert.match(a.get('autoArchiveStatus').textContent,/安全に確認できません/);
 assert.equal(a.get('autoArchiveRaces').children.length,0);
 assert.equal(a.storage.get(STORAGE),savedBeforeArchive);
 a.setArchiveCorrupt(false);
 a.get('autoDay').value='2099-01-02';
 a.get('autoDay').onchange();
 const archiveBeforeDate=a.requests.length;
 await archiveBtn.onclick();
 assert.equal(a.requests.length,archiveBeforeDate+1);
 assert.match(a.get('autoArchiveStatus').textContent,/この開催日のサーバー保存済み/);
 a.get('autoDay').value='2099-01-01';
 a.get('autoDay').onchange();
 assert.equal(a.storage.get(STORAGE),savedBeforeArchive);
 // A later forecast is NOT allowed to overwrite the earlier frozen receipt.
 a.setServer(resultWith('b'.repeat(64)));
 await a.get('autoRun').onclick();
 assert.equal(JSON.parse(a.storage.get(STORAGE))[0].signature,'a'.repeat(64));
 assert.match(a.get('autoSavedStatus').textContent,/新規 0R/);
 assert.equal(a.get('autoHistory').children.length,1);
 assert.match(a.get('autoFixedConsistency').textContent,/今回の暫定案と馬番が一致 1R/);
 // Real Saturday failure mode: the provider returns a NEW but perfectly
 // shaped 40-point formation after a prior signed 40-point first write.
 // The newer formation must NOT be mistaken for the frozen prestart picks.
 const changed=resultWith('c'.repeat(64));
 const secondChanged=[1,2,3,4,6];
 const laterTickets=[];
 for(const firstNumber of [1,2])
  for(const secondNumber of secondChanged)
   for(const thirdNumber of [1,2,3,4,5,6,7])
    if(new Set([firstNumber,secondNumber,thirdNumber]).size===3)
     laterTickets.push([firstNumber,secondNumber,thirdNumber]);
 assert.equal(laterTickets.length,40);
 changed.races[0].second=secondChanged;
 changed.races[0].tickets=laterTickets;
 changed.researchReceipts[0].snapshot.trifectaTickets=structuredClone(laterTickets);
 const fixedBeforeConflict=a.storage.get(STORAGE),callsBeforeConflict=a.requests.length;
 a.setServerRaw(changed);
 await a.get('autoRun').onclick();
 assert.equal(a.requests.length,callsBeforeConflict+1);
 assert.equal(a.storage.get(STORAGE),fixedBeforeConflict);
 assert.match(a.get('autoSavedStatus').textContent,/新規 0R/);
 assert.match(a.get('autoFixedConsistency').textContent,/買い目の不一致 1R/);
 assert.match(a.get('autoFixedConsistency').textContent,/最初の買い目を確認/);
 assert.equal(a.get('autoVenues').children.some(x=>x.dataset.mode==='drafts'),false);
 const changedCard=a.get('autoRaces').children[0].children[0];
 assert.equal(changedCard.children.some(x=>x.className==='formation'),false);
 assert.match(changedCard.children.at(-1).textContent,/以前の固定買い目と不一致/);
 assert.equal(a.get('autoHistory').children.length,1);
 assert.match(a.get('autoHistory').children[0].children[5].textContent,/1→2→3/);
 a.setServer(resultWith('b'.repeat(64)));
 await a.get('autoRun').onclick();
 assert.match(a.get('autoFixedConsistency').textContent,/今回の暫定案と馬番が一致 1R/);
 assert.equal(a.get('autoRaces').children[0].children[0].children.some(x=>x.className==='formation'),true);
 assert.equal(a.storage.get(STORAGE),fixedBeforeConflict);
 // An actual JRDB HTTP failure must show an error instead of stale new
 // picks while leaving first-write tickets readable for backup/signing.
 a.setAutoDraftOk(false);
 const reqBeforeNetworkError=a.requests.length;
 await a.get('autoRun').onclick();
 assert.equal(a.requests.length,reqBeforeNetworkError+1);
 assert.equal(a.get('autoRaces').children.length,0);
 assert.equal(a.get('autoVenues').children.length,0);
 assert.match(a.get('autoMorningStatus').textContent,/新しい暫定予想は表示していません/);
 assert.match(a.get('autoSavedStatus').textContent,/再分析に失敗.*固定済み研究記録 1R/);
 assert.match(a.get('autoHistoryStatus').textContent,/発走前固定 1R/);
 assert.equal(a.get('autoHistory').children.length,1);
 assert.equal(a.storage.get(STORAGE),fixedBeforeConflict);
 a.setAutoDraftOk(true);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoFixedConsistency').textContent,/今回の暫定案と馬番が一致 1R/);
 assert.equal(a.storage.get(STORAGE),fixedBeforeConflict);
 // Invalid graded/threshold payloads must never be rendered as 10-factor
 // finished predictions or be saved as new signed receipts.
 const beforeInvalidTen=a.storage.get(STORAGE);
 const badTen=resultWith('a'.repeat(64));
 badTen.tenFactorPreview.factors[0].weight=99;
 a.setServerRaw(badTen);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoTenStatus').textContent,/確認できません/);
 assert.equal(a.get('autoTenWeights').children.length,0);
 assert.equal(a.storage.get(STORAGE),beforeInvalidTen);
 // A corrupt current-going source must not be displayed as a trusted
 // racing condition or cause any new receipt write.
 const badCondition=resultWith('a'.repeat(64));
 badCondition.raceContext.races[0].going='unsupported';
 a.setServerRaw(badCondition);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoTenStatus').textContent,/確認できません/);
 assert.equal(a.storage.get(STORAGE),beforeInvalidTen);
 // A bad response signature must not mutate frozen picks or purchases.
 const corrupted=resultWith('not-an-authentic-signature');
 a.setServer(corrupted);
 const before=a.storage.get(STORAGE);
 await a.get('autoRun').onclick();
 assert.equal(a.storage.get(STORAGE),before);
 assert.match(a.get('autoSavedStatus').textContent,/保存はできませんでした/);
 assert.equal(a.storage.has('keiba-nine-owner-real-purchases-v1'),false);
 // A malformed runner source holds only that race and never saves tickets.
 const bad=research();
 bad.races=[{...bad.races[0],status:'hold',reason:'invalid_two_factor',
  validationIssue:'runner_shape',runners:[],first:[],second:[],third:[],
  tickets:[],points:0,amountYen:0}];
 bad.draftCount=0;bad.holdCount=1;bad.holdReasons={invalid_two_factor:1};
 bad.researchReceipts=[];bad.researchReceiptCount=0;
 a.setServer(bad);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoRaces').children[0].children[0].children[2].textContent,/馬番別資料の形式/);
 assert.equal(a.storage.get(STORAGE),before);
 // An older archived formation wins over a changed reanalysis. No newer
 // selection is exposed as a draft or written to this device.
 const conflict=research();
 conflict.races=[{...conflict.races[0],status:'hold',
   reason:'archived_earlier_draft',runners:[],first:[],second:[],
   third:[],tickets:[],points:0,amountYen:0}];
 conflict.draftCount=0;conflict.holdCount=1;
 conflict.holdReasons={archived_earlier_draft:1};
 conflict.archiveEnabled=true;conflict.archiveRecordCount=1;
 conflict.archiveConflictCount=1;
 conflict.researchReceipts=[];conflict.researchReceiptCount=0;
 a.setServer(conflict);
 await a.get('autoRun').onclick();
 assert.match(a.get('autoSummary').textContent,/既存の固定買い目を優先 1R/);
 assert.match(a.get('autoRaces').children[0].children[0].children[2].textContent,/先にサーバーへ固定済み/);
 assert.equal(a.storage.get(STORAGE),before);
 // No new prestart forecast means no new record, not a fabricated loss.
 const empty=research();
 empty.races=[{...empty.races[0],status:'hold',reason:'after_provisional_off',
  first:[],second:[],third:[],tickets:[],points:0,amountYen:0}];
 empty.draftCount=0;empty.holdCount=1;empty.holdReasons={after_provisional_off:1};
 empty.researchReceipts=[];empty.researchReceiptCount=0;
 a.setServer(empty);
 await a.get('autoRun').onclick();
 assert.equal(a.storage.get(STORAGE),before);
 assert.match(a.get('autoSavedStatus').textContent,/ありません/);
 assert.match(a.get('autoMorningStatus').textContent,/研究用3連単下書き 0R／見送り 1R/);
 assert.match(a.get('autoMorningStatus').textContent,/買い目を無理に作りません/);
 assert.equal(a.get('autoVenues').children.filter(x=>x.dataset.mode==='drafts').length,0);
 // A date switch while a slow fetch is in flight must remain operable,
 // and older data must not silently overwrite the selected day's status.
 const b=boot();
 await new Promise(r=>setImmediate(r));
 let release;
 const pause=new Promise(resolve=>{release=resolve});
 b.waitNextFetch(pause);
 const stale=b.get('autoRun').onclick();
 assert.equal(b.get('autoRun').disabled,true);
 b.get('autoDay').value='2099-01-02';
 b.get('autoDay').onchange();
 assert.equal(b.get('autoRun').disabled,false);
 assert.equal(b.get('autoHistoryAudit').disabled,true);
 assert.equal(b.get('autoHistoryAuditRaces').children.length,0);
 assert.equal(b.get('autoWatchResultCheck').disabled,true);
 assert.match(b.get('autoSavedStatus').textContent,/ありません/);
 assert.equal(b.get('autoHistory').children.length,0);
 release();
 await stale;
 assert.equal(b.get('autoSummary').textContent,'未取得');
 assert.match(b.get('autoMorningStatus').textContent,/取得結果を確認中/);
 b.get('autoDay').value='2099-01-01';
 b.get('autoDay').onchange();
 assert.match(b.get('autoSavedStatus').textContent,/固定済み研究記録 1R/);
 assert.equal(b.get('autoHistory').children.length,1);
 assert.equal(b.get('autoRun').disabled,false);
 // A long-running PWA that crosses midnight should select the new JST day
 // exactly once when visible, without background polling.
 const c=boot();
 await new Promise(r=>setImmediate(r));
 const nextDay=resultWith('d'.repeat(64));
 nextDay.date='20990102';
 nextDay.researchReceipts[0].snapshot.date='2099-01-02';
 nextDay.researchReceipts[0].snapshot.lockedAt='2099-01-02T09:00:00+09:00';
 nextDay.researchReceipts[0].snapshot.scheduledOffAt='2099-01-02T12:00:00+09:00';
 c.setServer(nextDay);
 c.advanceClock('2099-01-01T16:00:00Z');
 c.resume();
 await new Promise(r=>setImmediate(r));
 assert.equal(c.get('autoDay').value,'2099-01-02');
 assert.equal(c.requests.length,2);
 assert.equal(c.get('autoHistory').children.length,1);
 c.resume();
 assert.equal(c.requests.length,2);
 // A deliberately chosen old date cannot be replaced by resume events.
 c.get('autoDay').value='2099-01-01';c.get('autoDay').onchange();
 c.advanceClock('2099-01-02T16:00:00Z');
 c.resume();
 assert.equal(c.get('autoDay').value,'2099-01-01');
 assert.equal(c.requests.length,2);
 // A full Sunday: 36 race selectors, no extra JRDB calls or synthetic
 // post-off grades. Selecting a different track never mutates first-write
 // receipt, nor can a malformed stale selection choose another race.
 const full=boot();
 await new Promise(r=>setImmediate(r));
 full.setServerRaw(full36RaceDraft());
 await full.get('autoRun').onclick();
 assert.match(full.get('autoSummary').textContent,/36R中、研究用自動案 1R／見送り 35R/);
 assert.match(full.get('autoMorningStatus').textContent,/番組 36R／発走前の研究用3連単下書き 1R／見送り 35R/);
 assert.match(full.get('autoMorningStatus').textContent,/サーバー永続保存は未設定/);
 const draftOnly36=full.get('autoVenues').children.at(-1);
 assert.match(draftOnly36.textContent,/下書きのみ 1R/);
 const beforeDraftFilter36=full.requests.length;
 const beforeDraftStore36=full.storage.get(STORAGE);
 draftOnly36.onclick();
 assert.equal(full.get('autoRaces').children[0].children.length,1);
 assert.match(full.get('autoRaces').children[0].children[0].children[0].textContent,/東京 1R 研究用自動案 40点/);
 assert.equal(full.requests.length,beforeDraftFilter36);
 assert.equal(full.storage.get(STORAGE),beforeDraftStore36);
 full.get('autoVenues').children[0].onclick();
 const all36=full.get('autoRacePick');
 assert.equal(all36.disabled,false);
 assert.equal(all36.children.length,37);
 assert.match(full.get('autoViewingStatus').textContent,/全場 36R/);
 const paidRequestsBeforePick=full.requests.length;
 const archivedBeforePick=full.storage.get(STORAGE);
 all36.value='京都|12';
 all36.onchange();
 assert.equal(full.get('autoRaces').children[0].children.length,1);
 assert.match(full.get('autoViewingStatus').textContent,/京都 12R/);
 assert.match(full.get('autoRaces').children[0].children[0].children[0].textContent,/京都 12R 見送り/);
 const heldPanel=full.get('autoRaces').children[0].children[0].children.find(
  x=>x.className==='source-passport');
 assert.ok(heldPanel);
 assert.match(heldPanel.children[0].textContent,/正式採点0\/10/);
 const nextHeld=heldPanel.children.find(x=>x.className==='source-next');
 assert.ok(nextHeld);
 assert.ok(!nextHeld.children.some(x=>/調教の仮評価不足 0頭/.test(x.textContent||'')));
 assert.equal(full.requests.length,paidRequestsBeforePick);
 assert.equal(full.storage.get(STORAGE),archivedBeforePick);
 full.get('autoVenues').children[1].onclick();
 assert.equal(all36.value,'');
 assert.match(full.get('autoViewingStatus').textContent,/東京 12R/);
 assert.equal(full.get('autoRaces').children[0].children.length,12);
 full.get('autoVenues').children[0].onclick();
 assert.equal(full.get('autoRaces').children[0].children.length,36);
 assert.equal(full.requests.length,paidRequestsBeforePick);
 assert.equal(full.storage.get(STORAGE),archivedBeforePick);
 assert.ok(!js.includes('innerHTML'),'no DOM HTML injection');
 assert.ok(!js.includes('owner-real-purchases-v1'),'do not write actual purchases');
 console.log('Owner auto forecast: 40-point signed save, idempotency, tamper block, no purchased writes PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
