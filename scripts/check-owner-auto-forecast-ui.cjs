/* Owner-only auto-draft mobile UI: synthetic DOM and local receipt preservation. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-auto-forecast.js','utf8');
const STORAGE='keiba-nine-owner-server-receipts-v1';
const CORE_STORAGE='keiba-nine-owner-three-core-receipts-v1';
const FIVE_STORAGE='keiba-nine-owner-five-core-receipts-v1';
const STAFF_STUDY_STORAGE='keiba-nine-owner-staff-study-sessions-v1';
const R6_STORAGE='keiba-nine-owner-research6-draft-receipts-v1';
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
 ['course_distance','コース・距離',17,true],['pace','展開・脚質',17,true],
 ['ground','馬場',12,true],['pedigree','血統',6,false],
 ['draw_weight','枠・斤量',3,false],['jockey_stable','騎手・厩舎',10,false],
 ['rotation','ローテ',1,false],['body_condition','馬体重',1,false]
];
function withTenPreview(r){
 r.tenFactorPreview={
  version:'owner-ten-factor-contract-1',policyVersion:'research-6',
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
  version:'owner-day-source-passport-1',policyVersion:'research-6',
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
function full35WithGap(){
 const data=full36RaceDraft();
 const except=x=>!(x.track==='福島'&&x.race===6);
 data.races=data.races.filter(except);
 data.raceCount=35;data.holdCount=34;
 data.holdReasons={after_provisional_off:34};
 data.tenFactorPreview.races=data.tenFactorPreview.races.filter(except);
 data.tenFactorPreview.raceCount=35;
 data.raceContext.races=data.raceContext.races.filter(except);
 data.raceContext.raceCount=35;
 data.raceContext.courseInfoPresentCount=35;
 data.raceContext.goingAvailableCount=35;
 data.sourcePassport.races=data.sourcePassport.races.filter(except);
 data.sourcePassport.raceCount=35;
 return data;
}
function full36MixedHolds(){
 const data=full36RaceDraft();
 data.races[12].reason='missing_factors'; // 京都 1R
 data.races[24].reason='ambiguous_equal_grade_boundary'; // 福島 1R
 data.holdReasons={
  after_provisional_off:33,
  missing_factors:1,
  ambiguous_equal_grade_boundary:1,
 };
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
function withThreeCore(report){
 withTenFactor(report);
 const coreKeys=['training','course_distance','pace'];
 const weights={training:30,course_distance:20,pace:20};
 const factors=report.fiveFactorHypotheses.races.map(source=>{
  const horses=source.runners.map(h=>{
   const bands=Object.fromEntries(coreKeys.map(k=>[k,h.bands[k]]));
   const missing=coreKeys.filter(k=>bands[k]==='未評価');
   const values={S:3,A:2,B:1,C:0};
   const raw=missing.length?null:coreKeys.reduce(
    (sum,k)=>sum+weights[k]*values[bands[k]],0);
   return {number:h.number,bands,missing,
    observedCoreCount:3-missing.length,
    rawThirdPoints:raw,evidenceScore70:raw===null?null:
     Math.round(raw*100/3)/100,
    scoreIsCalibrated:false,formalScore100:null,
    formalGrade:'未評価',formalRank:null,bettingReady:false};
  });
  const missingByFactor=Object.fromEntries(coreKeys.map(k=>[
   k,horses.filter(h=>h.missing.includes(k)).length
  ]));
  return {track:source.track,race:source.race,
   runnerCount:horses.length,horses,
   completeCoreObserved:horses.filter(h=>h.rawThirdPoints!==null).length,
   missingByFactor,formalGradeReady:false,trifectaReady:false,
   researchOnly:true};
 });
 report.threeCoreResearch={
  version:'owner-three-core-research-1',policyVersion:'research-5',
  raceCount:factors.length,races:factors,
  coreFactorWeights:weights,coreWeightTotal:70,
  factorGradesVerified:0,overallPredictionReady:false,
  formalScoreReady:false,officialJraVerified:false,
  bettingReady:false,autoPurchase:false,changesExistingTickets:false,
  historicalBandsNotCalibrated:true,
  researchOnly:true,privateOwnerOnly:true
 };
 return report;
}
function withFourCore(report){
 withThreeCore(report);
 const factors=['training','course_distance','pace','ground'];
 const weights={training:30,course_distance:20,pace:20,ground:12};
 const values={S:3,A:2,B:1,C:0};
 const rows=report.fiveFactorHypotheses.races.map(five=>{
  const old=report.threeCoreResearch.races.find(
   r=>r.track===five.track&&r.race===five.race);
  const prior=new Map(old.horses.map(h=>[h.number,h]));
  const horses=five.runners.map(row=>{
   const bands=Object.fromEntries(factors.map(k=>[k,row.bands[k]]));
   const missing=factors.filter(k=>bands[k]==='未評価');
   const raw=missing.length?null:factors.reduce(
    (sum,k)=>sum+weights[k]*values[bands[k]],0);
   return {
    number:row.number,bands,missing,
    observedFactorCount:4-missing.length,rawThirdPoints:raw,
    evidenceScore82:raw===null?null:Math.round(raw*100/3)/100,
    scoreIsCalibrated:false,formalScore100:null,
    formalGrade:'未評価',formalRank:null,bettingReady:false
   };
  });
  const missingByFactor=Object.fromEntries(factors.map(k=>[
   k,horses.filter(h=>h.missing.includes(k)).length
  ]));
  return {track:five.track,race:five.race,runnerCount:horses.length,
   horses,completeObserved:horses.filter(h=>h.rawThirdPoints!==null).length,
   missingByFactor,researchOnly:true,formalGradeReady:false,
   trifectaReady:false};
 });
 report.fourCoreResearch={
  version:'owner-four-core-research-1',policyVersion:'research-5',
  raceCount:rows.length,races:rows,factorWeights:weights,
  observedWeightTotal:82,factorGradesVerified:0,
  overallPredictionReady:false,formalScoreReady:false,
  officialJraVerified:false,bettingReady:false,autoPurchase:false,
  changesExistingTickets:false,changesExistingCoreReceipts:false,
  historicalBandsNotCalibrated:true,goingSuitabilityVerified:false,
  researchOnly:true,privateOwnerOnly:true
 };
 return report;
}
function withFiveCore(report){
 withFourCore(report);
 const factors=['training','course_distance','pace','ground','recent'];
 const weights={training:30,course_distance:20,pace:20,ground:12,recent:3};
 const values={S:3,A:2,B:1,C:0};
 const races=report.fiveFactorHypotheses.races.map(five=>{
  const horses=five.runners.map(h=>{
   const bands=Object.fromEntries(factors.map(k=>[k,h.bands[k]]));
   const missing=factors.filter(k=>bands[k]==='未評価');
   const raw=missing.length?null:factors.reduce((sum,k)=>
    sum+weights[k]*values[bands[k]],0);
   return {number:h.number,bands,missing,
    observedFactorCount:5-missing.length,
    rawThirdPoints:raw,
    evidenceScore85:raw===null?null:Math.round(raw*100/3)/100,
    scoreIsCalibrated:false,formalScore100:null,formalGrade:'未評価',
    formalRank:null,bettingReady:false};
  });
  const missingByFactor=Object.fromEntries(factors.map(k=>[
   k,horses.filter(h=>h.missing.includes(k)).length
  ]));
  const buckets=new Map();
  for(const h of horses){
   if(h.rawThirdPoints!==null){
    if(!buckets.has(h.rawThirdPoints))buckets.set(h.rawThirdPoints,[]);
    buckets.get(h.rawThirdPoints).push(h.number);
   }
  }
  return {track:five.track,race:five.race,
   runnerCount:horses.length,horses,
   completeObserved:horses.filter(h=>h.rawThirdPoints!==null).length,
   comparisonGroups:[...buckets.keys()].sort((a,b)=>b-a).map(raw=>({
    rawThirdPoints:raw,numbers:buckets.get(raw).sort((a,b)=>a-b)
   })),
   unassessedNumbers:horses.filter(h=>h.rawThirdPoints===null)
    .map(h=>h.number).sort((a,b)=>a-b),
   comparisonIsFormalRank:false,
   missingByFactor,researchOnly:true,
   formalGradeReady:false,trifectaReady:false};
 });
 report.fiveCoreResearch={
  version:'owner-five-core-research-1',policyVersion:'research-5',
  raceCount:races.length,races,factorWeights:weights,
  observedWeightTotal:85,factorGradesVerified:0,
  overallPredictionReady:false,formalScoreReady:false,
  officialJraVerified:false,bettingReady:false,autoPurchase:false,
  changesExistingTickets:false,changesExistingCoreReceipts:false,
  historicalBandsNotCalibrated:true,recentResultRankNotPrediction:true,
  researchOnly:true,privateOwnerOnly:true
 };
 return report;
}
function withNewWeightFive(report){
 withFiveCore(report);
 const keys=['training','course_distance','pace','ground','recent'],
  weights={training:30,course_distance:17,pace:17,ground:12,recent:3},
  points={S:3,A:2,B:1,C:0};
 const races=report.fiveCoreResearch.races.map(old=>{
  const horses=old.horses.map(h=>{
   const raw=h.missing.length?null:keys.reduce((n,k)=>
    n+weights[k]*points[h.bands[k]],0);
   return {number:h.number,bands:{...h.bands},missing:[...h.missing],
    observedFactorCount:h.observedFactorCount,rawThirdPoints:raw,
    evidenceScore79:raw===null?null:Math.round(raw*100/3)/100,
    formalScore100:null,formalGrade:'未評価',formalRank:null,
    scoreIsCalibrated:false,bettingReady:false};
  });
  const bins=new Map();
  for(const h of horses){
   if(h.rawThirdPoints===null)continue;
   if(!bins.has(h.rawThirdPoints))bins.set(h.rawThirdPoints,[]);
   bins.get(h.rawThirdPoints).push(h.number);
  }
  return {track:old.track,race:old.race,runnerCount:horses.length,
   horses,completeObserved:horses.filter(h=>h.rawThirdPoints!==null).length,
   missingByFactor:{...old.missingByFactor},
   comparisonGroups:[...bins.keys()].sort((a,b)=>b-a).map(raw=>({
    rawThirdPoints:raw,numbers:bins.get(raw).sort((a,b)=>a-b)
   })),
   unassessedNumbers:horses.filter(h=>h.rawThirdPoints===null)
    .map(h=>h.number).sort((a,b)=>a-b),
   comparisonIsFormalRank:false,researchOnly:true,
   formalGradeReady:false,trifectaReady:false};
 });
 report.newWeightFiveResearch={
  version:'owner-new-weight-five-research-1',
  policyVersion:'research-6',sourcePolicyVersion:'research-5',
  raceCount:races.length,races,factorWeights:weights,
  observedWeightTotal:79,factorGradesVerified:0,
  overallPredictionReady:false,formalScoreReady:false,
  officialJraVerified:false,bettingReady:false,autoPurchase:false,
  researchOnly:true,privateOwnerOnly:true,historicalBandsNotCalibrated:true,
  resultVerified:false,changesExistingTickets:false,
  changesExistingCoreReceipts:false,changesExistingFiveReceipts:false,
  extraProviderCalls:0
 };
 return report;
}
function withRemaining21(report){
 withNewWeightFive(report);
 const keys=['pedigree','draw_weight','jockey_stable','rotation','body_condition'],
  weights={pedigree:6,draw_weight:3,jockey_stable:10,rotation:1,body_condition:1},
  textByFactor={
   pedigree:'父・母父の独立した同条件実績と時系列検証',
   draw_weight:'枠と相対斤量の同条件成績と時系列検証',
   jockey_stable:'騎手・厩舎の条件別成績と馬の能力差調整',
   rotation:'前走間隔に応じた条件別成績と時系列検証',
   body_condition:'発走前の当日馬体重と前走比・JRA独立確認'
  };
 const races=report.newWeightFiveResearch.races.map(five=>{
  const inv=report.tenFactorSourceInventory.races.find(x=>
   x.track===five.track&&x.race===five.race),
   byNumber=new Map(inv.runners.map(x=>[x.number,x]));
  const horses=five.horses.map(h=>{
   const states=byNumber.get(h.number).sourceStates;
   const present=Object.fromEntries(keys.map(k=>[k,
    k==='body_condition'?false:k==='rotation'?
     states[k]!=='unknown':states[k]==='complete_fields_observed']));
   return {
    number:h.number,research79Observed:h.evidenceScore79!==null,
    research79:h.evidenceScore79,sourceStates:{...states},
    sourceFieldsPresent:present,
    sourceFieldCoverageEquivalent21:keys.reduce((sum,k)=>
     sum+(present[k]?weights[k]:0),0),
    missingSourceFields:keys.filter(k=>!present[k]),
    missingValidation:{...textByFactor},verifiedFactorCount:0,
    formalScore100:null,formalGrade:'未評価',bettingReady:false
   };
  });
  return {track:five.track,race:five.race,runnerCount:horses.length,
   horses,priorSourceFourCompleteCount:horses.filter(h=>
    keys.slice(0,4).every(k=>h.sourceFieldsPresent[k])).length,
   research79ObservedCount:horses.filter(h=>h.research79Observed).length,
   sourceCoverageByFactor:{...inv.remainingFieldCoverage},
   gradeReady:false,trifectaReady:false};
 });
 report.remaining21SourceGaps={
  version:'owner-remaining21-source-gaps-1',
  policyVersion:'research-6',sourcePolicyVersion:'research-5',
  raceCount:races.length,races,factorWeights:weights,
  remainingWeight:21,initialResearchWeight:79,totalWeight:100,
  priorSourceFourCompleteCount:races.reduce(
   (sum,x)=>sum+x.priorSourceFourCompleteCount,0),
  verifiedFactorCount:0,formallyEvaluatedHorseCount:0,
  officialJraVerified:false,independentResultsVerified:false,
  historicalBandsCalibrated:false,overallPredictionReady:false,
  bettingReady:false,autoPurchase:false,
  researchOnly:true,privateOwnerOnly:true,extraProviderCalls:0,
  changesExistingReceipts:false,changesExistingTickets:false,
  changesExistingRoi:false
 };
 return report;
}
function withResearch6Uncertainty(report){
 withRemaining21(report);
 const w={training:30,recent:3,course_distance:17,pace:17,ground:12,
  pedigree:6,draw_weight:3,jockey_stable:10,rotation:1,body_condition:1},
  five=['training','course_distance','pace','ground','recent'],
  pts={S:3,A:2,B:1,C:0};
 const races=report.newWeightFiveResearch.races.map(r=>{
  const horses=r.horses.map(h=>{
   const missing=five.filter(k=>h.bands[k]==='未評価');
   const unresolved=21+missing.reduce((sum,k)=>sum+w[k],0),
    lower=five.reduce((sum,k)=>sum+
     (h.bands[k]==='未評価'?0:w[k]*pts[h.bands[k]]),0);
   return {
    number:h.number,observedHypothesisFactors:5-missing.length,
    unassessedFiveFactors:missing,unassessedTotalWeight:unresolved,
    jockeyStableStillUnassessedWeight:10,otherUnassessedWeight:unresolved-10,
    lowerResearchRawThirdPoints:lower,
    upperResearchRawThirdPoints:lower+3*unresolved,
    lowerResearchBound:Math.round(lower*100/3)/100,
    upperResearchBound:Math.round((lower+3*unresolved)*100/3)/100,
    formalScore100:null,formalGrade:'未評価',formalRank:null,
    scoreIsCalibrated:false,bettingReady:false
   };
  });
  for(const h of horses){
   h.arithmeticallyAbove=horses.filter(x=>x.number!==h.number&&
    h.lowerResearchRawThirdPoints>x.upperResearchRawThirdPoints)
    .map(x=>x.number);
   h.researchPossibleBestRank=1+horses.filter(x=>x.number!==h.number&&
    x.lowerResearchRawThirdPoints>h.upperResearchRawThirdPoints).length;
   h.researchPossibleWorstRank=1+horses.filter(x=>x.number!==h.number&&
    x.upperResearchRawThirdPoints>=h.lowerResearchRawThirdPoints).length;
  }
  return {track:r.track,race:r.race,runnerCount:horses.length,
   horses,strictAdvantagePairCount:horses.reduce((sum,h)=>
    sum+h.arithmeticallyAbove.length,0),
   researchOnly:true,formalRankReady:false,trifectaReady:false};
 });
 report.research6Uncertainty={
  version:'owner-research6-uncertainty-intervals-1',
  policyVersion:'research-6',raceCount:races.length,races,
  factorWeights:w,observedFactorWeightCeiling:79,alwaysUnassessedWeight:21,
  jockeyStableUnassessedWeight:10,verifiedFactorCount:0,
  formalScoreReady:false,officialJraVerified:false,bettingReady:false,
  autoPurchase:false,researchOnly:true,privateOwnerOnly:true,
  extraProviderCalls:0,changesExistingReceipts:false,
  changesExistingTickets:false,changesExistingRoi:false
 };
 return report;
}
function withResearch6FiveDrafts(report){
 withNewWeightFive(report);
 const study=report.newWeightFiveResearch;
 const races=study.races.map(r=>({
  track:r.track,race:r.race,postTime:'12:00',
  status:'hold',reason:'incomplete_five_factors',
  first:[],second:[],third:[],tickets:[],points:0,amountYen:0,
  completeObserved:r.completeObserved,runnerCount:r.runnerCount,
  rankedResearch:[],researchOnly:true,overallPredictionReady:false,
  officialJraVerified:false,bettingReady:false,autoPurchase:false
 }));
 report.research6FiveDrafts={
  version:'owner-research6-fivecore-drafts-1',
  policyVersion:'research-6',date:day,
  raceCount:races.length,draftCount:0,holdCount:races.length,
  holdReasons:{incomplete_five_factors:races.length},races,
  unitYen:100,researchFactorWeight:79,
  factorWeights:{training:30,course_distance:17,pace:17,ground:12,recent:3},
  remainingUnassessedWeight:21,
  officialJraVerified:false,researchOnly:true,privateOwnerOnly:true,
  overallPredictionReady:false,bettingReady:false,autoPurchase:false,
  actualPurchase:false,extraProviderCalls:0,
  changesExistingReceipts:false,changesExistingTickets:false,
  changesExistingRoi:false
 };
 return report;
}
function withPastStaffSample(report){
 report.pastStaffSample={
  version:'owner-past-staff-sample-1',status:'joined_private_sample',
  pastRacesSelected:1,providerReadCount:2,
  runnerCount:7,distinctJockeyCount:2,distinctTrainerCount:2,
  distinctPairCount:2,observedFirstPlaceCount:1,observedTop3Count:3,
  sourceFamily:'private_dky_dse_past_race',
  pastResultPublicationVerified:false,independentJraVerified:false,
  jockeyTrainerPerformanceAssessed:false,holdoutValidated:false,
  formalTenPointGrade:'未評価',formalTenPointScore:null,
  predictionReady:false,bettingReady:false,autoPurchase:false,
  actualPurchase:false,researchOnly:true,privateOwnerOnly:true,
  changesExistingReceipts:false,changesExistingTickets:false,
  changesExistingRoi:false
 };
 return report;
}
function withPastStaffBatch(report){
 report.pastStaffBatch={
  version:'owner-past-staff-batch-1',
  requestedRaceLimit:3,selectedPastRaceCount:3,providerReadCount:6,
  providerReadBudget:6,completedJoinRaceCount:3,heldOrIncompleteRaceCount:0,
  providerUnavailable:false,totalJoinedRunnerObservations:21,
  distinctJockeyCount:2,distinctTrainerCount:2,distinctPairCount:2,
  pairsSeenInTwoOrMoreRaces:2,pairRunnerObservations:21,
  observedFirstPlaceCount:3,observedTopThreeCount:9,
  sourceFamily:'private_dky_dse_bounded_races',
  pastResultPublicationVerified:false,independentJraVerified:false,
  fullTenFactorReady:false,jockeyTrainerPerformanceAssessed:false,
  holdoutValidated:false,formalTenPointGrade:'未評価',formalTenPointScore:null,
  predictionReady:false,bettingReady:false,autoPurchase:false,
  actualPurchase:false,researchOnly:true,privateOwnerOnly:true,
  changesExistingReceipts:false,changesExistingTickets:false,
  changesExistingRoi:false,additionalPaidReadsOnlyOnExplicitOptIn:true
 };
 return report;
}
function withSignedStaffStudy(report){
 withPastStaffBatch(report);
 const {note,...summary}=report.pastStaffBatch;
 report.staffStudyCapture={
  signature:'f'.repeat(64),
  snapshot:{
   version:'owner-staff-study-receipt-1',
   date:day,capturedAt:'2026-11-10T11:00:00+09:00',
   sourceKind:'private-server-three-race-aggregate-unverified',
   summary,researchOnly:true,officialJraVerified:false,
   actualPurchase:false,formalTenPointReady:false,
   independentHistoricRaceDedupVerified:false
  }
 };
 return report;
}
function withPedigreePreflight(report){
 withFiveCore(report);
 const inv=report.tenFactorSourceInventory;
 const races=inv.races.map(race=>{
  const horses=race.runners.map(h=>{
   const parentageComplete=h.sourceStates.pedigree==='complete_fields_observed';
   const missingEvidence=(parentageComplete?[]:['parentage_fields_incomplete'])
    .concat(['independent_condition_matched_cohort_unavailable',
     'temporal_holdout_not_validated']);
   return {number:h.number,parentageSourceState:h.sourceStates.pedigree,
    parentageComplete,independentCohortValidated:false,
    conditionMatched:false,outOfTimeCalibrated:false,missingEvidence,
    grade:'未評価',score8:null,bettingReady:false};
  });
  return {track:race.track,race:race.race,runnerCount:race.runnerCount,
   parentageCompleteCount:horses.filter(h=>h.parentageComplete).length,
   independentCohortValidatedCount:0,verifiedPedigreeGrades:0,
   horses,pedigreeScoreReady:false};
 });
 report.pedigreeEvidencePreflight={
  version:'owner-pedigree-evidence-preflight-1',policyVersion:'research-5',
  factor:'pedigree',weight:8,raceCount:races.length,races,
  pedigreeGradesVerified:0,independentCohortAvailable:false,
  temporalValidationComplete:false,researchOnly:true,privateOwnerOnly:true,
  officialJraVerified:false,overallPredictionReady:false,
  bettingReady:false,autoPurchase:false,changesExistingTickets:false,
  changesExistingReceipts:false
 };
 return report;
}
function withSupportSix(report){
 withFiveCore(report);
 const weights={draw_weight:3,jockey_stable:2,rotation:1};
 const gaps={
  draw_weight:['draw_or_carried_weight_missing',
   'field_and_weight_effects_unvalidated','temporal_holdout_not_validated'],
  jockey_stable:['jockey_or_trainer_missing',
   'comparable_personnel_performance_unvalidated','temporal_holdout_not_validated'],
  rotation:['last_run_interval_missing',
   'condition_matched_rotation_effect_unvalidated','temporal_holdout_not_validated']
 };
 const races=report.tenFactorSourceInventory.races.map(race=>{
  const counts=Object.fromEntries(Object.keys(weights).map(k=>[k,0]));
  const horses=race.runners.map(h=>{
   const states=Object.fromEntries(Object.keys(weights).map(k=>[k,h.sourceStates[k]]));
   const present=Object.fromEntries(Object.keys(weights).map(k=>[k,
    k==='rotation'?states[k]!=='unknown':
     states[k]==='complete_fields_observed']));
   for(const k of Object.keys(weights))counts[k]+=Number(present[k]);
   return {number:h.number,sourceStates:states,fieldPresent:present,
    fieldPresenceWeight:Object.keys(weights).reduce((total,k)=>
     total+(present[k]?weights[k]:0),0),
    missingEvidence:Object.fromEntries(Object.keys(weights).map(k=>[k,
     present[k]?gaps[k].slice(1):gaps[k].slice()])),
    grades:Object.fromEntries(Object.keys(weights).map(k=>[k,'未評価'])),
    scores:Object.fromEntries(Object.keys(weights).map(k=>[k,null])),
    conditionalEffectVerified:false,outOfTimeValidated:false,bettingReady:false};
  });
  return {track:race.track,race:race.race,runnerCount:race.runnerCount,
   fieldCompleteCounts:counts,
   allThreeFieldCompleteCount:horses.filter(h=>
    Object.values(h.fieldPresent).every(Boolean)).length,
   verifiedFactorCount:0,scoreReady:false,horses};
 });
 report.supportSixPreflight={
  version:'owner-support-six-preflight-1',policyVersion:'research-5',
  factors:weights,weightTotal:6,raceCount:races.length,races,
  verifiedFactorCount:0,conditionMatchedEffectValidated:false,
  temporalValidationComplete:false,researchOnly:true,privateOwnerOnly:true,
  officialJraVerified:false,overallPredictionReady:false,
  bettingReady:false,autoPurchase:false,
  changesExistingTickets:false,changesExistingReceipts:false
 };
 return report;
}
function prestart(){
 const result={
  version:'private-prestart-body-1',date:day,raceCount:1,
  races:[{
   track:'東京',race:1,registered:7,prestartRowsMatched:6,
   prestartRowsMissing:1,bodyWeightRecords:4,weightChangeRecords:3,
   paddockRecords:3,bodyStateCodeRecords:2,providerWithdrawnReports:0,
   runners:Array.from({length:7},(_,i)=>({
    number:i+1,prestartRowMatched:i<6,
    bodyWeightRecorded:i<4,weightChangeRecorded:i<3,
    jraOfficialWeightVerified:false,bodyConditionGrade:'未評価',
    bodyConditionScore1:null,bettingReady:false
   })),
   sourceDataUpdatedAtVerified:false,officialBodyWeightVerified:false,
   bodyConditionGraded:false,realPredictionReady:false,ticketReady:false
  }],
  summary:{matchedRows:6,weightRecords:4,paddockRecords:3,missingRows:1},
  sourceRequestsRequired:['tra','tky','tpd'],rawHorseRecordsIncluded:false,
  oddsUsed:false,officialBodyWeightVerified:false,bodyConditionGraded:false,
  realPredictionReady:false,purchaseReady:false
 };
 const gate={
  version:'owner-body-one-evidence-preflight-1',
  date:day,policyVersion:'research-5',
  factor:'body_condition',weight:1,raceCount:result.raceCount,
  races:result.races.map(row=>({
   track:row.track,race:row.race,runnerCount:row.registered,
   completeMeasuredPairs:row.weightChangeRecords,
   missingMeasuredPairs:row.registered-row.weightChangeRecords,
   verifiedGradeCount:0,scoreReady:false,
   horses:row.runners.map(h=>{
    const gaps=[];
    if(!h.prestartRowMatched)gaps.push('prestart_runner_row_unavailable');
    if(!h.bodyWeightRecorded)gaps.push('body_weight_measurement_missing');
    if(!h.weightChangeRecorded)gaps.push('previous_weight_comparison_missing');
    gaps.push('independent_jra_weight_not_verified',
     'body_condition_effect_not_calibrated','temporal_holdout_not_validated');
    return {
     number:h.number,sourcePairPresent:h.bodyWeightRecorded&&h.weightChangeRecorded,
     missingEvidence:gaps,grade:'未評価',score1:null,
     officialVerified:false,effectValidated:false,
     temporalValidationComplete:false,bettingReady:false
    };
   })
  })),
  verifiedGradeCount:0,officialJraVerified:false,
  sourceTimestampVerified:false,conditionEffectValidated:false,
  outOfTimeValidated:false,overallPredictionReady:false,
  bettingReady:false,autoPurchase:false,researchOnly:true,
  privateOwnerOnly:true,changesExistingTickets:false,
  changesExistingReceipts:false
 };
 result.bodyOneEvidencePreflight=gate;
 return result;
}
function boot(){
 const storage=new Map(),elements=new Map(),requests=[];
 let next=resultWith('a'.repeat(64)),autoDraftFailure=null,historicalResponse=historical(),
  historyOk=true,providerCorrupt=false,holdFetch=null,
  prestartResponse=prestart(),prestartOk=true,
  configured=true,connectionOK=true,connectionCount=1,
  receiptVerificationOk=true,coreVerificationOk=true,
  coreProviderCorrupt=false,fiveExposureCorrupt=false,
  archiveReady=false,archiveCorrupt=false,
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
  if(url==='/api/owner-staff-study-verify'){
   const req=JSON.parse(options.body||'{}');
   const ok=Array.isArray(req.receipts)&&req.receipts.length>0&&
    req.receipts.every(x=>x.signature==='f'.repeat(64));
   return {ok,json:async()=>ok?{
    version:'owner-staff-study-verify-1',
    serverSigned:true,verifiedDateCount:req.receipts.length,
    researchOnly:true,privateOwnerOnly:true,
    independentHistoricRaceDedupVerified:false,
    officialJraVerified:false,formalTenPointReady:false,
    bettingReady:false,actualPurchase:false,sourceProviderReadCount:0
   }:{error:'invalid signature'}};
  }
  if(url==='/api/owner-research6-draft-verify'){
   const args=JSON.parse(options.body);
   const ok=Array.isArray(args.receipts)&&args.receipts.length>0&&
    args.receipts.every(x=>x.signature==='e'.repeat(64));
   return {ok,json:async()=>ok?{
    version:'owner-research6-draft-verify-1',
    serverSigned:true,recordCount:args.receipts.length,
    researchOnly:true,privateOwnerOnly:true,
    officialJraVerified:false,independentJraScheduleVerified:false,
    formalPredictionReady:false,resultComparisonReady:false,
    bettingReady:false,actualPurchase:false,autoPurchase:false
   }:{error:'bad_signature'}};
  }
  if(url==='/api/owner-three-core-verify'){
   const args=JSON.parse(options.body);
   const valid=coreVerificationOk&&Array.isArray(args.receipts)&&
    args.receipts.every(x=>x.signature==='c'.repeat(64));
   return {ok:valid,json:async()=>valid?{
    version:'owner-three-core-verify-1',serverSigned:true,
    recordCount:args.receipts.length,researchOnly:true,privateOwnerOnly:true,
    officialJraVerified:false,independentJraScheduleVerified:false,
    calibrationReady:false,resultComparisonReady:false,bettingReady:false,
    autoPurchase:false,actualPurchase:false
   }:{error:'signature_mismatch'}};
  }
  if(url==='/api/owner-three-core-provider-check'){
   const args=JSON.parse(options.body);
   const snap=args.receipts[0].snapshot,first=snap.horses[0];
   const scores={training:{S:0,A:0,B:0,C:0},
    course_distance:{S:0,A:0,B:0,C:0},pace:{S:0,A:0,B:0,C:0}};
   for(const k of Object.keys(scores))scores[k][first.bands[k]]++;
   return {ok:true,json:async()=>({
    version:'owner-three-core-provider-observation-1',
    date:args.date,sourceKind:'jrdb-tse-unverified-podium-observation',
    providerSourceReadCount:1,raceCount:args.receipts.length,
    races:args.receipts.map((receipt,i)=>{
     const p=receipt.snapshot;
     return {
      track:p.track,race:p.race,
      providerStatus:i===0?'podium_observed':'pending',
      observedPodiumNumbers:i===0?[first.number,2,3]:null,
      scoredRunnerCount:p.horses.length,
      winnerStudyScore70:i===0?first.rawThirdPoints/3:null,
      winnerStudyBands:i===0?structuredClone(first.bands):null,
      studiedWinnerObserved:i===0?true:null,
      officialVerified:coreProviderCorrupt?true:false,
      predictionHitVerified:null
     };
    }),
    observedRaceCount:1,observedStudiedWinnerCount:1,
    winnerBandCounts:scores,verifiedRaceCount:0,confirmedHitCount:null,
    officialJraVerified:false,jraIndependentConfirmation:false,
    officialFeedConnected:false,outcomeCalibrationReady:false,
    modelAccuracyPercent:null,bettingReady:false,actualPurchase:false,
    payoutVerified:false,roiPercent:null,
    historicalBandsNotCalibrated:true,
    sourceIncompleteCouldChange:true,researchOnly:true,privateOwnerOnly:true
   })};
  }
  if(url==='/api/owner-five-core-provider-check'){
   const args=JSON.parse(options.body);
   const snap=args.receipts[0].snapshot,first=snap.horses[0];
   const keys=['training','course_distance','pace','ground','recent'],
    counts=Object.fromEntries(keys.map(k=>[
     k,{S:0,A:0,B:0,C:0}
    ]));
   for(const k of keys)counts[k][first.bands[k]]++;
   const exposures=Object.fromEntries(keys.map(k=>[k,{S:0,A:0,B:0,C:0}]));
   for(const h of snap.horses)for(const k of keys)exposures[k][h.bands[k]]++;
   if(fiveExposureCorrupt)exposures.training.S++;
   return {ok:true,json:async()=>({
    version:'owner-five-core-provider-observation-1',
    date:args.date,sourceKind:'jrdb-tse-unverified-five-core-observation',
    providerSourceReadCount:1,raceCount:args.receipts.length,
    races:args.receipts.map((receipt,i)=>({
     track:receipt.snapshot.track,race:receipt.snapshot.race,
     providerStatus:i===0?'podium_observed':'pending',
     observedPodiumNumbers:i===0?[first.number,2,3]:null,
     scoredRunnerCount:receipt.snapshot.horses.length,
     winnerStudyScore85:i===0?first.rawThirdPoints/3:null,
     winnerStudyBands:i===0?structuredClone(first.bands):null,
     studiedWinnerObserved:i===0?true:null,
     officialVerified:coreProviderCorrupt?true:false,
     predictionHitVerified:null
    })),
    observedRaceCount:1,observedStudiedWinnerCount:1,
    observedStudiedRunnerCount:snap.horses.length,
    winnerBandCounts:counts,observedResearchBandExposureCounts:exposures,
    verifiedRaceCount:0,confirmedHitCount:null,
    officialJraVerified:false,jraIndependentConfirmation:false,
    officialFeedConnected:false,outcomeCalibrationReady:false,
    modelAccuracyPercent:null,bettingReady:false,actualPurchase:false,
    payoutVerified:false,roiPercent:null,historicalBandsNotCalibrated:true,
    sourceIncompleteCouldChange:true,researchOnly:true,privateOwnerOnly:true
   })};
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
  if(url.startsWith('/api/jrdb/owner-auto-draft?')&&autoDraftFailure)
   return {ok:false,json:async()=>structuredClone(autoDraftFailure)};
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
  setAutoDraftFailure:x=>autoDraftFailure=x,
  setHistorical:x=>historicalResponse=x,setHistoryOk:x=>historyOk=x,
  setPrestart:x=>prestartResponse=x,setPrestartOk:x=>prestartOk=x,
  setConfigured:x=>configured=x,setConnectionOK:x=>connectionOK=x,
  setReceiptVerificationOk:x=>receiptVerificationOk=x,
  setCoreVerificationOk:x=>coreVerificationOk=x,
  setCoreProviderCorrupt:x=>coreProviderCorrupt=x,
  setFiveExposureCorrupt:x=>fiveExposureCorrupt=x,
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
 assert.match(a.get('autoJraCrosscheck').textContent,/独立照合 0R（未実施）/);
 assert.match(a.get('autoJraCrosscheck').textContent,/JRDBの開催場 1場（東京）/);
 assert.match(a.get('autoJraCrosscheck').textContent,/リンク発見も馬番・取消・馬場・発走時刻の一致を証明しません/);
 // Public publishing times are only a clock-based guidance, with NO paid read.
 const guide=boot();
 await new Promise(r=>setImmediate(r));
 const guideRequests=guide.requests.length;
 guide.get('autoDay').value='2099-01-03'; // Saturday, fake now: Jan 1 (Thu morning JST).
 guide.get('autoDay').onchange();
 assert.match(guide.get('autoJraReleaseGuide').textContent,/2099-01-01 16時すぎ/);
 assert.match(guide.get('autoJraCrosscheck').textContent,/JRDBの開催場 0場/);
 assert.equal(guide.requests.length,guideRequests);
 guide.advanceClock('2099-01-02T06:00:00Z');
 guide.get('autoDay').onchange();
 assert.match(guide.get('autoJraReleaseGuide').textContent,/通常公開目安は経過/);
 assert.equal(guide.requests.length,guideRequests);
 guide.get('autoDay').value='2099-01-05'; // weekday rule is explicitly unknown
 guide.get('autoDay').onchange();
 assert.match(guide.get('autoJraReleaseGuide').textContent,/平日・変則開催/);
 guide.get('autoDay').value='2099-01-32';
 guide.get('autoDay').onchange();
 assert.match(guide.get('autoJraReleaseGuide').textContent,/開催日が不正/);
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
 assert.match(a.get('autoJraCrosscheck').textContent,/JRA公式PDFリンク 1場分/);
 assert.match(a.get('autoJraCrosscheck').textContent,/リンク未検出 0場/);
 assert.match(a.get('autoJraCrosscheck').textContent,/独立照合 0R（未実施）/);
 assert.match(a.get('autoOfficialPdfStatus').textContent,/馬番・取消・馬場・発走時刻は自動照合していません/);
 assert.equal(a.storage.get(STORAGE),picksBeforePdf);
 a.setOfficialPdfLinks([]);
 await jraButton.onclick();
 assert.match(a.get('autoOfficialPdfStatus').textContent,/まだ検出できません/);
 assert.equal(a.get('autoOfficialPdfLinks').children.length,0);
 assert.match(a.get('autoJraCrosscheck').textContent,/リンク未検出 1場（東京）/);
 assert.match(a.get('autoJraCrosscheck').textContent,/リンク未検出は開催なしを意味せず/);
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
 assert.match(a.get('autoJraCrosscheck').textContent,/JRA公式PDFリンクは未検索/);
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
 assert.match(a.get('autoPrestartStatus').textContent,/資料ペア 3頭/);
 assert.match(a.get('autoPrestartStatus').textContent,/馬体1点は未評価/);
 assert.match(a.get('autoPrestartRaces').children[0].children[1].textContent,/JRA公式未確認/);
 const bodyPanel=a.get('autoPrestartRaces').children[0].children[2];
 assert.match(bodyPanel.children[0].textContent,/馬番別の資料を見る/);
 assert.match(bodyPanel.children[1].textContent,/1番｜馬体重 記録あり／前走比 記録あり/);
 assert.match(bodyPanel.children[7].textContent,/7番｜馬体重 未取得／前走比 未取得/);
 const bodyGate=a.get('autoPrestartRaces').children[0].children[3];
 assert.match(bodyGate.children[0].textContent,/採点準備：体重＋前走比あり 3\/7頭/);
 assert.match(bodyGate.children[1].textContent,/記録があっても採点しません/);
 assert.match(bodyGate.children[2].textContent,/1番｜体重＋前走比 記録あり/);
 assert.match(bodyGate.children[8].textContent,/7番｜体重＋前走比 不足/);
 assert.match(bodyGate.children[8].textContent,/直前情報行なし/);
 assert.equal(a.storage.get(STORAGE),beforeBody);
 const wrongBody=prestart();
 wrongBody.races[0].bodyWeightRecords=18;
 a.setPrestart(wrongBody);
 await a.get('autoPrestartBody').onclick();
 assert.equal(a.get('autoPrestartRaces').children.length,0);
 assert.match(a.get('autoPrestartStatus').textContent,/照合できません/);
 assert.equal(a.storage.get(STORAGE),beforeBody);
 // Reject forged points, official proof and mismatched counts/horse numbers.
 for(const mutate of [
  h=>h.races[0].runners[0].bodyConditionScore1=1,
  h=>h.races[0].runners[0].bodyConditionGrade='S',
  h=>h.races[0].runners[0].jraOfficialWeightVerified=true,
  h=>h.races[0].runners[0].weightChangeRecorded=false,
  h=>h.races[0].runners[1].number=1,
  h=>h.races[0].runners[6].bodyWeightRecorded=true,
  h=>h.bodyOneEvidencePreflight.races[0].completeMeasuredPairs=7,
  h=>h.bodyOneEvidencePreflight.races[0].horses[0].score1=1,
  h=>h.bodyOneEvidencePreflight.races[0].horses[0].grade='S',
  h=>h.bodyOneEvidencePreflight.races[0].horses[0].officialVerified=true,
  h=>h.bodyOneEvidencePreflight.races[0].horses[6].sourcePairPresent=true,
  h=>h.bodyOneEvidencePreflight.races[0].horses[6].missingEvidence=[],
  h=>h.bodyOneEvidencePreflight.races[0].horses[1].number=1,
  h=>h.bodyOneEvidencePreflight.races[0].race=2,
 ]){
  const forged=prestart();mutate(forged);
  a.setPrestart(forged);
  await a.get('autoPrestartBody').onclick();
  assert.equal(a.get('autoPrestartRaces').children.length,0);
  assert.match(a.get('autoPrestartStatus').textContent,/照合できません/);
  assert.equal(a.storage.get(STORAGE),beforeBody);
 }
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
 assert.equal(tenPanel.children.length,10);
 assert.match(tenPanel.children[2].textContent,/1番｜血統 資料あり/);
 assert.match(tenPanel.children[2].textContent,/当日馬体重未取得/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 // The 70-weight three-core trial consumes the existing validated
 // historical source only. Missing pace/course is never extrapolated.
 const beforeThree=a.requests.length;
 a.setHistorical(withThreeCore(historical()));
 await a.get('autoHistoryAudit').onclick();
 const threePanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/重点3項目の研究用70点/.test(x.children[0]?.textContent||''));
 assert.ok(threePanel);
 assert.equal(threePanel.children.length,10);
 assert.match(threePanel.children[1].textContent,/総合100点・勝率・正式順位ではありません/);
 assert.match(threePanel.children[2].textContent,/正式な採点項目としては未承認/);
 assert.match(threePanel.children[3].textContent,/1番｜調教 S／コース 未評価／展開 未評価/);
 assert.match(threePanel.children[3].textContent,/研究用未評価/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 assert.equal(a.requests.filter(x=>x.url.startsWith('/api/jrdb/owner-auto-draft?')).length,1);
 assert.equal(a.requests.filter(x=>x.url==='/api/jrdb/history').length,4);
 // The fourth ground factor uses the same pre-validated going
 // observation, without writing any first-lock 70-point signed study.
 const beforeFour=a.requests.length,oldCore=a.storage.get(CORE_STORAGE);
 a.setHistorical(withFourCore(historical()));
 await a.get('autoHistoryAudit').onclick();
 const fourPanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/重点4項目の研究用82点/.test(
   x.children[0]?.textContent||''));
 assert.ok(fourPanel);
 assert.equal(fourPanel.children.length,10);
 assert.match(fourPanel.children[1].textContent,/重・不良への実戦対応能力/);
 assert.match(fourPanel.children[2].textContent,/根拠の未確認は0点やCではなく未評価/);
 assert.match(fourPanel.children[3].textContent,/1番｜調教 S／コース 未評価／展開 未評価／馬場/);
 assert.match(fourPanel.children[3].textContent,/研究用未評価/);
 const fourRequests=a.requests.slice(beforeFour);
 assert.equal(fourRequests.filter(r=>r.url==='/api/jrdb/history').length,1);
 assert.equal(fourRequests.filter(r=>
  r.url.startsWith('/api/jrdb/owner-auto-draft?')).length,0);
 assert.ok(fourRequests.every(r=>[
  '/api/jrdb/history','/api/owner-rebound-verify'
 ].includes(r.url)),'no new paid reads for ground study');
 assert.equal(a.storage.get(CORE_STORAGE),oldCore);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 // Fifth recent factor is only three weight; unchanged source calls
 // and the first-write historical study and 3連単 never change.
 const beforeFive=a.requests.length,coreBeforeFive=a.storage.get(CORE_STORAGE);
 a.setHistorical(withFiveCore(historical()));
 await a.get('autoHistoryAudit').onclick();
 const quickCard=a.get('autoHistoryAuditRaces').children[0];
 const quickSummary=quickCard.children.find(x=>x.tag==='p'&&
  /研究85点比較/.test(x.textContent));
 assert.ok(quickSummary,'85-point evidence has a visible, zero-extra-click summary');
 assert.match(quickSummary.textContent,/5項目がそろう馬は0頭/);
 assert.match(quickSummary.textContent,/未評価 7頭/);
 assert.match(quickSummary.textContent,/正式な良い馬順・勝率・買い目ではありません/);
 const fiveCorePanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/重点5項目の研究用85点/.test(
   x.children[0]?.textContent||''));
 assert.ok(fiveCorePanel);
 assert.equal(fiveCorePanel.children.length,11);
 assert.match(fiveCorePanel.children[1].textContent,/近走の最大影響は3点だけ/);
 const evidenceOrder=fiveCorePanel.children.at(-1);
 assert.match(evidenceOrder.children[0].textContent,/研究用85点の比較順/);
 assert.match(evidenceOrder.children[1].textContent,/同点は並列・未評価は除外/);
 assert.match(evidenceOrder.children[2].textContent,/比較順は付けられません/);
 assert.match(evidenceOrder.children[3].textContent,/未評価・比較順から除外/);
 assert.match(evidenceOrder.children[3].textContent,/1番/);
 assert.match(fiveCorePanel.children[2].textContent,/残る15点は血統8・枠斤量3/);
 assert.match(fiveCorePanel.children[3].textContent,/1番｜調教 S／近走 S／コース 未評価／展開 未評価／馬場/);
 assert.match(fiveCorePanel.children[3].textContent,/研究用未評価/);

 // Remaining 15-weight source coverage is NOT a 100-point grade.
 const remainingPanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/10項目の資料状況/.test(
   x.children[0]?.textContent||''));
 assert.ok(remainingPanel);
 assert.match(remainingPanel.children[1].textContent,/総合点・馬券は未確定/);
 assert.match(remainingPanel.children[2].textContent,
  /1番｜血統 資料あり.*資料カバー配点相当 14\/15（実得点ではない）.*不足 当日馬体重/);
 assert.match(remainingPanel.children.at(-1).textContent,/資料カバーは最大14\/15/);
 assert.match(remainingPanel.children.at(-1).textContent,
  /能力点・予想スコア・S\/A\/B\/Cではありません/);

 // Parentage completeness is not a validated eight-weight performance grade.
 const pedigreeBefore=a.requests.length;
 a.setHistorical(withPedigreePreflight(historical()));
 await a.get('autoHistoryAudit').onclick();
 const pedigreePanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/血統8点の採点準備/.test(
   x.children[0]?.textContent||''));
 assert.ok(pedigreePanel);
 assert.match(pedigreePanel.children[1].textContent,/血統S\/A\/B\/Cも8点の実得点も付けません/);
 assert.match(pedigreePanel.children[2].textContent,/血統の能力評価まで確認できた馬 0\/7頭/);
 assert.match(pedigreePanel.children[3].textContent,/1番｜父・母父 両方あり.*血統8点 未評価/);
 assert.equal(a.requests.slice(pedigreeBefore).filter(
  r=>r.url==='/api/jrdb/history').length,1);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 assert.equal(a.storage.get(CORE_STORAGE),coreBeforeFive);
 for(const mutate of [
  h=>h.pedigreeEvidencePreflight.races[0].horses[0].score8=8,
  h=>h.pedigreeEvidencePreflight.races[0].horses[0].grade='S',
  h=>h.pedigreeEvidencePreflight.independentCohortAvailable=true,
  h=>h.pedigreeEvidencePreflight.races[0].parentageCompleteCount=7,
  h=>h.pedigreeEvidencePreflight.races[0].horses[0].missingEvidence=[],
 ]){
  const invalid=withPedigreePreflight(historical());mutate(invalid);
  a.setHistorical(invalid);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 const fiveCalls=a.requests.slice(beforeFive,pedigreeBefore);
 assert.equal(fiveCalls.filter(x=>x.url==='/api/jrdb/history').length,1);
 assert.equal(fiveCalls.filter(x=>x.url.startsWith('/api/jrdb/owner-auto-draft?')).length,0);
 assert.ok(fiveCalls.every(x=>['/api/jrdb/history','/api/owner-rebound-verify'].includes(x.url)));
 assert.equal(a.storage.get(CORE_STORAGE),coreBeforeFive);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 // research-6 has a separate, opt-in 79-weight 5-factor comparison.
 // It must never promote, re-sign, mutate or replace the legacy 85 study.
 const existing85=a.storage.get(FIVE_STORAGE),reqBefore79=a.requests.length;
 a.setHistorical(withNewWeightFive(historical()));
 await a.get('autoHistoryAudit').onclick();
 const new79Card=a.get('autoHistoryAuditRaces').children[0];
 const new79Quick=new79Card.children.find(x=>x.tag==='p'&&
  /新配点79点研究比較/.test(x.textContent));
 assert.ok(new79Quick);
 assert.match(new79Quick.textContent,/未評価 7頭/);
 assert.match(new79Quick.textContent,/正式100点の総合評価・予想順位・買い目ではありません/);
 const panel79=new79Card.children.find(x=>x.tag==='details'&&
  /新配点5項目79点の研究比較/.test(x.children[0]?.textContent||''));
 assert.ok(panel79);
 assert.match(panel79.children[1].textContent,/コース距離17／展開脚質17/);
 assert.match(panel79.children[2].textContent,/残り21点分の評価/);
 assert.match(panel79.children[3].textContent,/1番｜調教 S／近走 S／コース 未評価/);
 assert.match(panel79.children[3].textContent,/研究用未評価/);
 assert.equal(a.requests.slice(reqBefore79).filter(x=>
  x.url==='/api/jrdb/history').length,1);
 assert.equal(a.storage.get(FIVE_STORAGE),existing85);
 assert.equal(a.storage.get(CORE_STORAGE),coreBeforeFive);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 for(const mutate of [
  h=>h.newWeightFiveResearch.races[0].horses[0].evidenceScore79=79,
  h=>h.newWeightFiveResearch.factorWeights.pace=20,
  h=>h.newWeightFiveResearch.races[0].horses[0].formalScore100=79,
  h=>h.newWeightFiveResearch.races[0].comparisonGroups=[{rawThirdPoints:237,numbers:[1]}],
  h=>h.newWeightFiveResearch.sourcePolicyVersion='research-6',
  h=>h.newWeightFiveResearch.officialJraVerified=true,
 ]){
  const fake=withNewWeightFive(historical());mutate(fake);
  a.setHistorical(fake);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(FIVE_STORAGE),existing85);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 a.setHistorical(withNewWeightFive(historical()));
 await a.get('autoHistoryAudit').onclick();

 // Remaining research-6 21 is only presence, never a 100-point score.
 const beforeGap=a.requests.length,old85=a.storage.get(FIVE_STORAGE);
 a.setHistorical(withRemaining21(historical()));
 await a.get('autoHistoryAudit').onclick();
 const gapCard=a.get('autoHistoryAuditRaces').children[0];
 const gapPanel=gapCard.children.find(x=>x.tag==='details'&&
  /新配点：残り21点の資料不足/.test(x.children[0]?.textContent||''));
 assert.ok(gapPanel);
 assert.match(gapPanel.children[1].textContent,/騎手厩舎10/);
 assert.match(gapPanel.children[2].textContent,/正式能力評価は未完了/);
 assert.match(gapPanel.children[3].textContent,
  /1番｜新79点研究 未評価｜残り21点の資料カバー配点相当 20\/21（得点ではない）/);
 assert.match(gapPanel.children[3].textContent,/資料不足：当日馬体重/);
 assert.match(gapPanel.children.at(-1).textContent,/JRA公式出走/);
 assert.equal(a.requests.slice(beforeGap).filter(x=>
  x.url==='/api/jrdb/history').length,1);
 assert.equal(a.storage.get(FIVE_STORAGE),old85);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 for(const mutate of [
  h=>h.remaining21SourceGaps.factorWeights.jockey_stable=2,
  h=>h.remaining21SourceGaps.races[0].horses[0].formalScore100=80,
  h=>h.remaining21SourceGaps.races[0].horses[0].sourceFieldCoverageEquivalent21=21,
  h=>h.remaining21SourceGaps.races[0].horses[0].sourceFieldsPresent.body_condition=true,
  h=>h.remaining21SourceGaps.races[0].horses[0].sourceStates.rotation='unknown',
  h=>h.remaining21SourceGaps.races[0].horses[0].missingSourceFields=[],
  h=>h.remaining21SourceGaps.races[0].research79ObservedCount=7,
  h=>h.remaining21SourceGaps.officialJraVerified=true,
 ]){
  const invalid=withRemaining21(historical());mutate(invalid);
  a.setHistorical(invalid);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(STORAGE),oldRecord);
  assert.equal(a.storage.get(FIVE_STORAGE),old85);
 }
 // Research-6 mathematical intervals are not full 100-point grades.
 const beforeInterval=a.requests.length,old85Interval=a.storage.get(FIVE_STORAGE);
 a.setHistorical(withResearch6Uncertainty(historical()));
 await a.get('autoHistoryAudit').onclick();
 const intervalCard=a.get('autoHistoryAuditRaces').children[0];
 const intervalPanel=intervalCard.children.find(x=>x.tag==='details'&&
  /新配点100点・未評価項目による順位変動シミュレーション/.test(
   x.children[0]?.textContent||''));
 assert.ok(intervalPanel);
 assert.match(intervalPanel.children[1].textContent,/騎手・厩舎だけで10点/);
 assert.match(intervalPanel.children[1].textContent,/正式100点の採点・勝率・予想順位・買い目ではありません/);
 assert.match(intervalPanel.children[3].textContent,/1番｜研究用の100点仮定幅/);
 assert.match(intervalPanel.children[3].textContent,/騎手厩舎10点含む/);
 assert.match(intervalPanel.children[3].textContent,/正式評価：未評価/);
 assert.equal(a.requests.slice(beforeInterval).filter(x=>
  x.url==='/api/jrdb/history').length,1);
 assert.equal(a.storage.get(FIVE_STORAGE),old85Interval);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 for(const mutate of [
  h=>h.research6Uncertainty.factorWeights.jockey_stable=2,
  h=>h.research6Uncertainty.races[0].horses[0].lowerResearchBound=-1,
  h=>h.research6Uncertainty.races[0].horses[0].upperResearchRawThirdPoints=999,
  h=>h.research6Uncertainty.races[0].horses[0].formalScore100=95,
  h=>h.research6Uncertainty.races[0].horses[0].formalGrade='S',
  h=>h.research6Uncertainty.races[0].horses[0].researchPossibleBestRank=0,
  h=>h.research6Uncertainty.races[0].strictAdvantagePairCount=-1,
  h=>h.research6Uncertainty.officialJraVerified=true,
 ]){
  const invalid=withResearch6Uncertainty(historical());mutate(invalid);
  a.setHistorical(invalid);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(FIVE_STORAGE),old85Interval);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 // Research6 five-factor 3連単 preview holds every incomplete race.
 const beforeFiveDraft=a.requests.length,oldFiveDraft=a.storage.get(FIVE_STORAGE);
 a.setHistorical(withResearch6FiveDrafts(historical()));
 await a.get('autoHistoryAudit').onclick();
 const testCard=a.get('autoHistoryAuditRaces').children[0];
 const fiveDraftPanel=testCard.children.find(x=>x.tag==='details'&&
  /新配点79点から作る3連単研究用下書き/.test(
   x.children[0]?.textContent||''));
 assert.ok(fiveDraftPanel);
 assert.match(fiveDraftPanel.children[1].textContent,/血統6・枠斤量3・騎手厩舎10/);
 assert.match(fiveDraftPanel.children[2].textContent,/買い目は保留/);
 assert.match(fiveDraftPanel.children[2].textContent,/5項目が全頭そろっていない/);
 assert.equal(a.requests.slice(beforeFiveDraft).filter(x=>
  x.url==='/api/jrdb/history').length,1);
 assert.equal(a.storage.get(FIVE_STORAGE),oldFiveDraft);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 for(const mutate of [
  h=>h.research6FiveDrafts.factorWeights.pace=20,
  h=>h.research6FiveDrafts.races[0].points=40,
  h=>h.research6FiveDrafts.races[0].tickets=[[1,2,3]],
  h=>h.research6FiveDrafts.races[0].status='five_factor_research_draft',
  h=>h.research6FiveDrafts.races[0].rankedResearch=[{number:1,research79:79}],
  h=>h.research6FiveDrafts.races[0].reason='unknown_reason',
  h=>h.research6FiveDrafts.draftCount=1,
  h=>h.research6FiveDrafts.officialJraVerified=true,
 ]){
  const forged=withResearch6FiveDrafts(historical());mutate(forged);
  a.setHistorical(forged);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(FIVE_STORAGE),oldFiveDraft);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 // Extra historical staff analysis is OPT-IN only, +2 private JRDB reads,
 // never used for true 10-point grades, purchase or old immutable tickets.
 const beforeExtra=a.requests.length,oldFixed85=a.storage.get(FIVE_STORAGE);
 a.get('autoHistoryStaffSample').checked=true;
 a.setHistorical(withPastStaffSample(historical()));
 await a.get('autoHistoryAudit').onclick();
 const extraReq=a.requests.slice(beforeExtra).find(x=>x.url==='/api/jrdb/history');
 assert.ok(extraReq);
 assert.equal(JSON.parse(extraReq.options.body).staffSample,true);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/過去1Rを資料結合：7頭/);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/同一ペア2組/);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/正式10点の採点・JRA公式照合は未完了/);
 assert.equal(a.storage.get(FIVE_STORAGE),oldFixed85);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 for(const change of [
  h=>h.pastStaffSample.formalTenPointScore=10,
  h=>h.pastStaffSample.formalTenPointGrade='S',
  h=>h.pastStaffSample.independentJraVerified=true,
  h=>h.pastStaffSample.distinctPairCount=19,
  h=>h.pastStaffSample.providerReadCount=3,
  h=>h.pastStaffSample.status='verified_10pt',
 ]){
  const forged=withPastStaffSample(historical());change(forged);
  a.setHistorical(forged);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(FIVE_STORAGE),oldFixed85);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 // Three-race mode is still a separately selected, explicitly paid opt-in.
 a.get('autoHistoryStaffSample').checked=true;
 a.get('autoHistoryStaffRaceLimit').value='3';
 const beforeBatch=a.requests.length;
 a.setHistorical(withPastStaffBatch(historical()));
 await a.get('autoHistoryAudit').onclick();
 const batchRequest=a.requests.slice(beforeBatch).find(x=>
  x.url==='/api/jrdb/history');
 assert.deepEqual(JSON.parse(batchRequest.options.body),
  {date:day,limit:8,staffSample:true,staffBatchRaces:3});
 assert.match(a.get('autoHistoryStaffStatus').textContent,/過去3Rのうち資料結合3R・保留0R/);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/追加照会6\/6回/);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/2R以上に登場：2組/);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/10点採点・公式結果・回収率には未使用/);
 assert.equal(a.storage.get(FIVE_STORAGE),oldFixed85);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 for(const mutate of [
  x=>x.pastStaffBatch.formalTenPointScore=10,
  x=>x.pastStaffBatch.formalTenPointGrade='S',
  x=>x.pastStaffBatch.providerReadCount=7,
  x=>x.pastStaffBatch.pairsSeenInTwoOrMoreRaces=19,
  x=>x.pastStaffBatch.completedJoinRaceCount=4,
  x=>x.pastStaffBatch.observedFirstPlaceCount=2,
  x=>x.pastStaffBatch.independentJraVerified=true,
  x=>x.pastStaffBatch.changesExistingRoi=true,
  x=>x.pastStaffBatch.distinctPairCount=25,
 ]){
  const corrupt=withPastStaffBatch(historical());mutate(corrupt);
  a.setHistorical(corrupt);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(FIVE_STORAGE),oldFixed85);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 // Returning to single-race retains the old response shape and budget.
 a.get('autoHistoryStaffRaceLimit').value='1';
 a.setHistorical(withPastStaffSample(historical()));
 const oldRequest=a.requests.length;
 await a.get('autoHistoryAudit').onclick();
 const oneReq=a.requests.slice(oldRequest).find(x=>x.url==='/api/jrdb/history');
 assert.equal(JSON.parse(oneReq.options.body).staffBatchRaces,undefined);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/過去1Rを資料結合：7頭/);
 // A signed redacted 3R study is verified first, then first-write by
 // target date. Rechecking the SAME day cannot replace its initial summary.
 a.get('autoHistoryStaffSample').checked=true;
 a.get('autoHistoryStaffRaceLimit').value='3';
 a.setHistorical(withSignedStaffStudy(historical()));
 const old85BeforeStaff=a.storage.get(FIVE_STORAGE);
 await a.get('autoHistoryAudit').onclick();
 const storedStaff=a.storage.get(STAFF_STUDY_STORAGE);
 assert.ok(storedStaff);
 assert.equal(JSON.parse(storedStaff).length,1);
 assert.equal(JSON.parse(storedStaff)[0].snapshot.summary.providerReadCount,6);
 assert.match(a.get('autoHistoryStaffArchiveStatus').textContent,/開催日別に初回固定/);
 assert.equal(a.get('autoHistoryStaffArchiveList').children.length,1);
 assert.equal(a.get('autoHistoryStaffArchiveVerify').disabled,false);
 await a.get('autoHistoryStaffArchiveVerify').onclick();
 assert.match(a.get('autoHistoryStaffArchiveVerifyStatus').textContent,/1日分の署名を検証/);
 assert.equal(a.storage.get(STAFF_STUDY_STORAGE),storedStaff);
 assert.equal(a.storage.get(FIVE_STORAGE),old85BeforeStaff);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 a.setHistorical(withSignedStaffStudy(historical()));
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.storage.get(STAFF_STUDY_STORAGE),storedStaff,
  'repeat history cannot overwrite signed aggregate for same date');
 for(const mutate of [
  x=>x.staffStudyCapture.snapshot.summary.providerReadCount=7,
  x=>x.staffStudyCapture.snapshot.summary.formalTenPointScore=10,
  x=>x.staffStudyCapture.snapshot.summary.independentJraVerified=true,
  x=>x.staffStudyCapture.snapshot.summary.pairsSeenInTwoOrMoreRaces=99,
  x=>x.staffStudyCapture.snapshot.date='20261102',
  x=>x.staffStudyCapture.snapshot.formalTenPointReady=true,
 ]){
  const bad=withSignedStaffStudy(historical());mutate(bad);
  a.setHistorical(bad);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.storage.get(STAFF_STUDY_STORAGE),storedStaff);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 // Default remains zero staff queries; the request has no staffSample field.
 a.get('autoHistoryStaffSample').checked=false;
 const afterExtra=a.requests.length;
 a.setHistorical(historical());
 await a.get('autoHistoryAudit').onclick();
 const ordinary=a.requests.slice(afterExtra).find(x=>x.url==='/api/jrdb/history');
 assert.ok(ordinary);
 assert.equal(JSON.parse(ordinary.options.body).staffSample,undefined);
 assert.match(a.get('autoHistoryStaffStatus').textContent,/追加の騎手・厩舎照会なし/);
 // Supporting six-weight factors: source fields are not real six points.
 const beforeSix=a.requests.length;
 a.setHistorical(withSupportSix(historical()));
 await a.get('autoHistoryAudit').onclick();
 const supportPanel=a.get('autoHistoryAuditRaces').children[0].children.find(
  x=>x.tag==='details'&&/枠斤量・騎手厩舎・ローテ6点/.test(
   x.children[0]?.textContent||''));
 assert.ok(supportPanel);
 assert.match(supportPanel.children[1].textContent,/実得点は0点ではなく未評価/);
 assert.match(supportPanel.children[2].textContent,/能力評価を検証できた馬 0\/7頭/);
 assert.match(supportPanel.children[3].textContent,
  /1番｜枠斤量 資料あり.*資料カバー配点相当 6\/6（実得点ではない）.*正式6点 未評価/);
 assert.equal(a.requests.slice(beforeSix).filter(
  x=>x.url==='/api/jrdb/history').length,1);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 assert.equal(a.storage.get(CORE_STORAGE),coreBeforeFive);
 for(const mutate of [
  h=>h.supportSixPreflight.races[0].horses[0].scores.draw_weight=3,
  h=>h.supportSixPreflight.races[0].horses[0].grades.jockey_stable='S',
  h=>h.supportSixPreflight.races[0].horses[0].fieldPresenceWeight=0,
  h=>h.supportSixPreflight.races[0].allThreeFieldCompleteCount=0,
  h=>h.supportSixPreflight.races[0].horses[0].missingEvidence.rotation=[],
  h=>h.supportSixPreflight.conditionMatchedEffectValidated=true,
 ]){
  const invalid=withSupportSix(historical());mutate(invalid);
  a.setHistorical(invalid);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(STORAGE),oldRecord);
 }
 // A forged 85-point figure or injected formal readiness fails closed.
 for(const mutate of [
  h=>h.fiveCoreResearch.races[0].horses[0].evidenceScore85=85,
  h=>h.fiveCoreResearch.races[0].horses[0].formalScore100=85,
  h=>h.fiveCoreResearch.recentResultRankNotPrediction=false,
  h=>h.fiveCoreResearch.factorWeights.recent=30,
  h=>h.fiveCoreResearch.races[0].comparisonGroups=[{rawThirdPoints:255,numbers:[1]}],
  h=>h.fiveCoreResearch.races[0].unassessedNumbers=[],
  h=>h.fiveCoreResearch.races[0].comparisonIsFormalRank=true,
 ]){
  const invalid=withFiveCore(historical());mutate(invalid);
  a.setHistorical(invalid);
  await a.get('autoHistoryAudit').onclick();
  assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
  assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
  assert.equal(a.storage.get(STORAGE),oldRecord);
  assert.equal(a.storage.get(CORE_STORAGE),coreBeforeFive);
 }
 // A forged numeric 82-point mark must be rejected before any card.
 const forgedFour=withFourCore(historical());
 forgedFour.fourCoreResearch.races[0].horses[0].evidenceScore82=82;
 a.setHistorical(forgedFour);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
 assert.equal(a.storage.get(STORAGE),oldRecord);
 assert.equal(a.storage.get(CORE_STORAGE),oldCore);
 // A forged numeric 70/70 despite an unobserved core must fail closed.
 const forgedCore=withThreeCore(historical());
 forgedCore.threeCoreResearch.races[0].horses[0].evidenceScore70=70;
 a.setHistorical(forgedCore);
 await a.get('autoHistoryAudit').onclick();
 assert.equal(a.get('autoHistoryAuditRaces').children.length,0);
 assert.match(a.get('autoHistoryAuditStatus').textContent,/照合ができません/);
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
 assert.match(a.get('autoOperationalNext').textContent,/研究用下書きあり/);
 assert.match(a.get('autoOperationalNext').textContent,/全1R中、研究用3連単 1R／見送り 0R/);
 assert.match(a.get('autoOperationalNext').textContent,/JRA公式の出走・取消・馬場・発走時刻は未照合/);
 assert.match(a.get('autoProgrammeCoverage').textContent,/JRDB番組：1R／1場/);
 assert.match(a.get('autoProgrammeCoverage').textContent,/東京 1\/12R（1〜12R中未検出候補 2R/);
 assert.match(a.get('autoProgrammeCoverage').textContent,/未検出は開催中止・取消を意味しません/);
 assert.match(a.get('autoRecordSafety').textContent,/この端末に 1R（署名は未検証）/);
 assert.match(a.get('autoRecordSafety').textContent,/サーバー永続保存は未設定/);
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
 assert.match(sourcePanel.children[4].textContent,/コース・距離17点/);
  assert.match(sourcePanel.children[4].textContent,/展開・脚質17点/);
  assert.match(sourcePanel.children[4].textContent,/血統6点/);
  assert.match(sourcePanel.children[4].textContent,/騎手・厩舎10点/);
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
 assert.match(a.get('autoOperationalNext').textContent,/取得失敗・新規予想なし/);
 assert.match(a.get('autoProgrammeCoverage').textContent,/取得失敗：開催場別R数は確認できません/);
 assert.match(a.get('autoRecordSafety').textContent,/新規記録なし/);
 assert.match(a.get('autoFixedConsistency').textContent,/再分析結果は未確認/);
 // Do not rerun the original receipt: first-write-wins is intentional.
 // The next test below supplies its own response and preserves this record.
 assert.match(a.get('autoSavedStatus').textContent,/再分析に失敗.*固定済み研究記録 1R/);
 assert.equal(a.get('autoRaces').children.length,0);
 assert.equal(a.get('autoVenues').children.length,0);
 assert.equal(a.get('autoHoldReasons').children.length,0);
 const firstSave=JSON.parse(a.storage.get(STORAGE));
 assert.equal(firstSave.length,1);
 // A malformed or repeated receipt from ANOTHER DATE must stop any new
 // appends without deleting the existing archive or touching purchases.
 const crossDay=boot();
 await new Promise(r=>setImmediate(r));
 const base=JSON.parse(crossDay.storage.get(STORAGE));
 const foreign=structuredClone(base[0]);
 foreign.snapshot.date='2099-01-02';
 foreign.snapshot.lockedAt='2099-01-02T09:00:00+09:00';
 foreign.snapshot.scheduledOffAt='2099-01-02T12:00:00+09:00';
 const validCrossDay=JSON.stringify([...base,foreign]);
 crossDay.storage.set(STORAGE,validCrossDay);
 await crossDay.get('autoRun').onclick();
 assert.equal(crossDay.storage.get(STORAGE),validCrossDay);
 assert.match(crossDay.get('autoSavedStatus').textContent,/新規 0R/);
 for(const mutated of [
  [...base,foreign,structuredClone(foreign)],
  [...base,{...foreign,signature:'invalid-signature'}],
  [...base,{...foreign,snapshot:{
   ...foreign.snapshot,trifectaTickets:[[1,2,3],[1,2,3]]
  }}],
  [...base,{...foreign,snapshot:{
   ...foreign.snapshot,lockedAt:'2099-01-02T13:00:00+09:00'
  }}],
 ]){
  const saved=JSON.stringify(mutated);
  crossDay.storage.set(STORAGE,saved);
  await crossDay.get('autoRun').onclick();
  assert.equal(crossDay.storage.get(STORAGE),saved,
   'invalid past ledger must remain untouched for owner recovery');
  assert.match(crossDay.get('autoSavedStatus').textContent,/保存はできませんでした/);
  assert.match(crossDay.get('autoRecordSafety').textContent,/新規固定失敗/);
  assert.equal(crossDay.storage.has('keiba-nine-owner-real-purchases-v1'),false);
 }
 crossDay.storage.set(STORAGE,validCrossDay);
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
 assert.match(a.get('autoOperationalNext').textContent,/固定記録の確認が必要/);
 assert.match(a.get('autoOperationalNext').textContent,/照合保留・不一致 1R/);
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
 assert.match(a.get('autoOperationalNext').textContent,/取得失敗・新規予想なし/);
 assert.match(a.get('autoProgrammeCoverage').textContent,/取得失敗：開催場別R数は確認できません/);
 assert.match(a.get('autoRecordSafety').textContent,/新規記録なし/);
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
 assert.match(a.get('autoRecordSafety').textContent,/端末への新規固定失敗/);
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
 assert.match(a.get('autoOperationalNext').textContent,/全1R見送り/);
 assert.match(a.get('autoOperationalNext').textContent,/主な理由：発走済み 1R/);
 assert.match(a.get('autoOperationalNext').textContent,/無理に3連単を作りません/);
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
 assert.match(b.get('autoProgrammeCoverage').textContent,/まだ確認していません/);
 assert.match(b.get('autoRecordSafety').textContent,/まだ確認していません/);
 assert.match(b.get('autoOperationalNext').textContent,/当日の取得結果を確認中/);
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
 assert.match(full.get('autoOperationalNext').textContent,/全36R中、研究用3連単 1R／見送り 35R/);
 assert.match(full.get('autoMorningStatus').textContent,/サーバー永続保存は未設定/);
 assert.match(full.get('autoProgrammeCoverage').textContent,/JRDB番組：36R／3場/);
 for(const venue of ['東京','京都','福島'])
  assert.match(full.get('autoProgrammeCoverage').textContent,
   new RegExp(venue+' 12\\/12R（1〜12Rすべて検出）'));
 assert.match(full.get('autoRecordSafety').textContent,/この端末に 1R（署名は未検証）/);
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
 // All 36R are already validated before UI filtering. Mixed holds should
 // be navigable with one tap and must never generate past-off tickets.
 // A missing JRDB row is an unconfirmed provider gap, NEVER an official
 // cancelled race. The view cannot create, backfill or alter tickets.
 const gap=boot();
 await new Promise(r=>setImmediate(r));
 const beforeGapStore=gap.storage.get(STORAGE),beforeGapReq=gap.requests.length;
 gap.setServerRaw(full35WithGap());
 await gap.get('autoRun').onclick();
 assert.equal(gap.requests.length,beforeGapReq+1);
 assert.match(gap.get('autoProgrammeCoverage').textContent,/JRDB番組：35R／3場/);
 assert.match(gap.get('autoProgrammeCoverage').textContent,
  /福島 11\/12R（1〜12R中未検出候補 6R）/);
 assert.match(gap.get('autoProgrammeCoverage').textContent,
  /JRA公式との全場・全R照合は未完成/);
 assert.equal(gap.storage.get(STORAGE),beforeGapStore);
 const mixed=boot();
 await new Promise(r=>setImmediate(r));
 mixed.setServerRaw(full36MixedHolds());
 await mixed.get('autoRun').onclick();
 const reasonButtons=mixed.get('autoHoldReasons').children;
 assert.equal(reasonButtons.length,3);
 assert.equal(reasonButtons[0].dataset.reason,'after_provisional_off');
 assert.match(mixed.get('autoOperationalNext').textContent,/主な見送り：発走済み 33R／候補同点 1R/);
 assert.match(reasonButtons[0].textContent,/発走済み 33R/);
 assert.equal(reasonButtons[1].dataset.reason,'missing_factors');
 assert.match(reasonButtons[1].textContent,/調教・近走不足 1R/);
 assert.equal(reasonButtons[2].dataset.reason,'ambiguous_equal_grade_boundary');
 assert.match(reasonButtons[2].textContent,/候補同点 1R/);
 const beforeHoldFilter=mixed.requests.length;
 const beforeHoldStorage=mixed.storage.get(STORAGE);
 reasonButtons[1].onclick();
 assert.equal(reasonButtons[1]['aria-pressed'],'true');
 assert.match(mixed.get('autoViewingStatus').textContent,/見送り理由：調教・近走不足 1R/);
 assert.equal(mixed.get('autoRaces').children[0].children.length,1);
 assert.match(mixed.get('autoRaces').children[0].children[0].children[0].textContent,/京都 1R 見送り/);
 assert.equal(mixed.get('autoRaces').children[0].children[0].children.some(x=>x.className==='formation'),false);
 reasonButtons[2].onclick();
 assert.equal(reasonButtons[1]['aria-pressed'],'false');
 assert.equal(reasonButtons[2]['aria-pressed'],'true');
 assert.equal(mixed.get('autoRaces').children[0].children.length,1);
 assert.match(mixed.get('autoRaces').children[0].children[0].children[0].textContent,/福島 1R 見送り/);
 reasonButtons[0].onclick();
 assert.equal(mixed.get('autoRaces').children[0].children.length,33);
 assert.match(mixed.get('autoViewingStatus').textContent,/見送り理由：発走済み 33R/);
 assert.equal(mixed.requests.length,beforeHoldFilter);
 assert.equal(mixed.storage.get(STORAGE),beforeHoldStorage);
 mixed.get('autoVenues').children[1].onclick();
 assert.equal(mixed.get('autoRaces').children[0].children.length,12);
 assert.equal(reasonButtons[0]['aria-pressed'],'false');
 mixed.get('autoDay').value='2099-01-02';
 mixed.get('autoDay').onchange();
 assert.equal(mixed.get('autoHoldReasons').children.length,0);
 assert.match(mixed.get('autoProgrammeCoverage').textContent,/まだ確認していません/);
 assert.match(mixed.get('autoRecordSafety').textContent,/まだ確認していません/);
 assert.match(mixed.get('autoOperationalNext').textContent,/当日の取得結果を確認中/);
 assert.match(mixed.get('autoHoldStatus').textContent,/開催日を取得すると/);
 assert.equal(mixed.storage.get(STORAGE),beforeHoldStorage);
 // Each 401/403/429 cause is actionable on Saturday without printing
 // untrusted JRDB response text or mutating first-write research tickets.
 const failures=boot();
 await new Promise(r=>setImmediate(r));
 const originalLocked=failures.storage.get(STORAGE);
 for(const [kind,visible] of [
   ['provider_auth','401：APIキー・認証キーを確認'],
   ['provider_entitlement','403：β版の利用権限を確認'],
   ['provider_rate_limit','429：間隔を空けて再試行'],
   ['provider','JRDB API通信・応答'],
 ]){
  failures.setAutoDraftFailure({
   error:'SECRET_UNTRUSTED_PROVIDER_MESSAGE',failureStage:'training',
   failureKind:kind,failureDetail:null
  });
  await failures.get('autoRun').onclick();
  const shown=failures.get('autoStatus').textContent;
  assert.ok(shown.includes(visible),'must show safe diagnostic for '+kind);
  assert.ok(!shown.includes('SECRET_UNTRUSTED'));
  assert.match(shown,/未完成の買い目は表示しません/);
  assert.equal(failures.get('autoRaces').children.length,0);
  assert.equal(failures.get('autoHistory').children.length,1);
  assert.equal(failures.storage.get(STORAGE),originalLocked);
  assert.equal(failures.get('autoRun').disabled,false);
 }
 // The 70-point study is only attested before the provisional off and
 // persisted once on the iPhone, never blended with ordinary 3連単.
 const coreView=boot();
 await new Promise(r=>setImmediate(r));
 const study=withThreeCore(historical());
 study.coreCapture={
  version:'owner-three-core-receipt-1',date:day,serverSigned:true,
  researchOnly:true,privateOwnerOnly:true,jraScheduleVerified:false,
  officialResultsVerified:false,calibrationReady:false,bettingReady:false,
  actualPurchase:false,receiptCount:0,postOffOrMissingTimeRaces:0,
  receipts:[]
 };
 coreView.setHistorical(study);
 const beforeStudy=coreView.requests.length;
 await coreView.get('autoHistoryAudit').onclick();
 assert.equal(coreView.requests.length,beforeStudy+2); // history and rebound
 assert.match(coreView.get('autoCoreSaveStatus').textContent,/固定対象がありません/);
 assert.equal(coreView.get('autoCoreSaved').children.length,0);
 assert.equal(coreView.storage.get(CORE_STORAGE),undefined);
 assert.equal(coreView.requests.filter(r=>r.url==='/api/owner-three-core-verify').length,0);
 const snapshot={
  version:'owner-three-core-receipt-1',date:day,track:'東京',race:1,
  sourceKind:'prestart-uncalibrated-70-research',
  capturedAt:'2099-01-01T09:00:00+09:00',
  scheduledOffAt:'2099-01-01T12:00:00+09:00',
  raceRunnerCount:7,observedRunnerCount:1,
  horses:[{number:1,bands:{
   training:'S',course_distance:'A',pace:'B'
  },rawThirdPoints:150}],
  researchOnly:true,officialJraVerified:false,
  sourceHypothesesUncalibrated:true,actualPurchase:false,
  predictionReady:false
 };
 const sealed={snapshot,signature:'c'.repeat(64)};
 coreView.storage.set(CORE_STORAGE,JSON.stringify([sealed]));
 coreView.get('autoDay').value='2099-01-02';
 coreView.get('autoDay').onchange();
 coreView.get('autoDay').value='2099-01-01';
 coreView.get('autoDay').onchange();
 assert.equal(coreView.get('autoCoreSaved').children.length,1);
 assert.match(coreView.get('autoCoreSaved').children[0].children[0].textContent,/研究用70点・1頭分/);
 const lockedCore=coreView.storage.get(CORE_STORAGE),callCount=coreView.requests.length;
 await coreView.get('autoCoreVerify').onclick();
 assert.equal(coreView.requests.length,callCount+1);
 assert.match(coreView.get('autoCoreVerifyStatus').textContent,/サーバー署名確認成功：1R/);
 assert.equal(coreView.storage.get(CORE_STORAGE),lockedCore);
 // Explicit postrace comparison reads at most one provider query and
 // must not store outcome as a forecast, graded score or purchased ticket.
 const ticketBeforeProvider=coreView.storage.get(STORAGE);
 const requestsBeforeCoreCompare=coreView.requests.length;
 await coreView.get('autoCoreProviderCheck').onclick();
 assert.equal(coreView.requests.length,requestsBeforeCoreCompare+1);
 assert.equal(coreView.requests.at(-1).url,'/api/owner-three-core-provider-check');
 assert.match(coreView.get('autoCoreProviderStatus').textContent,/暫定1〜3着を観測 1\/1R/);
 assert.match(coreView.get('autoCoreProviderStatus').textContent,/JRA公式結果・勝率・正式的中・回収率は未照合/);
 const card=coreView.get('autoCoreProviderRaces').children[0];
 assert.match(card.children[1].textContent,/JRDB暫定1〜3着：1→2→3/);
 assert.match(card.children[2].textContent,/発走前研究値：50.00\/70点/);
 assert.equal(coreView.storage.get(CORE_STORAGE),lockedCore);
 assert.equal(coreView.storage.get(STORAGE),ticketBeforeProvider);
 coreView.setCoreProviderCorrupt(true);
 await coreView.get('autoCoreProviderCheck').onclick();
 assert.match(coreView.get('autoCoreProviderStatus').textContent,/安全に比較できませんでした/);
 assert.equal(coreView.get('autoCoreProviderRaces').children.length,0);
 assert.equal(coreView.storage.get(CORE_STORAGE),lockedCore);
 coreView.setCoreProviderCorrupt(false);
 coreView.setCoreVerificationOk(false);
 await coreView.get('autoCoreVerify').onclick();
 assert.match(coreView.get('autoCoreVerifyStatus').textContent,/署名を確認できませんでした/);
 assert.equal(coreView.storage.get(CORE_STORAGE),lockedCore);
 coreView.setCoreVerificationOk(true);
 coreView.get('autoDay').value='2099-01-03';
 coreView.get('autoDay').onchange();
 assert.equal(coreView.get('autoCoreProviderCheck').disabled,true);
 assert.equal(coreView.get('autoCoreProviderRaces').children.length,0);
 assert.equal(coreView.storage.get(CORE_STORAGE),lockedCore);
 // Five-factor 85-weight observations are frozen once and outcome review
 // never changes research, earlier tickets, purchases or 100-yen ROI.
 const fiveSnapshot={
  version:'owner-five-core-receipt-1',date:day,track:'東京',race:1,
  sourceKind:'prestart-uncalibrated-85-research',
  capturedAt:'2099-01-01T09:00:00+09:00',
  scheduledOffAt:'2099-01-01T12:00:00+09:00',
  raceRunnerCount:7,observedRunnerCount:1,
  horses:[{number:1,bands:{
   training:'S',course_distance:'A',pace:'B',ground:'A',recent:'C'
  },rawThirdPoints:174}],
  researchOnly:true,sourceHypothesesUncalibrated:true,
  officialJraVerified:false,predictionReady:false,actualPurchase:false
 };
 const fiveReceipt={snapshot:fiveSnapshot,signature:'d'.repeat(64)};
 coreView.storage.set(FIVE_STORAGE,JSON.stringify([fiveReceipt]));
 coreView.get('autoDay').value='2099-01-02';coreView.get('autoDay').onchange();
 coreView.get('autoDay').value='2099-01-01';coreView.get('autoDay').onchange();
 assert.equal(coreView.get('autoFiveProviderCheck').disabled,false);
 const originalFive=coreView.storage.get(FIVE_STORAGE);
 const beforeFiveCheck=coreView.requests.length;
 await coreView.get('autoFiveProviderCheck').onclick();
 assert.equal(coreView.requests.length,beforeFiveCheck+1);
 assert.equal(coreView.requests.at(-1).url,'/api/owner-five-core-provider-check');
 assert.match(coreView.get('autoFiveProviderStatus').textContent,/暫定着順を観測 1\/1R/);
 assert.match(coreView.get('autoFiveProviderStatus').textContent,/回収率は未確認/);
 assert.match(coreView.get('autoFiveProviderRaces').children[0]
  .children[2].textContent,/58.00\/85/);
 assert.equal(coreView.get('autoFiveProviderRaces').children.length,2);
 const bandsDetail=coreView.get('autoFiveProviderRaces').children[1];
 assert.match(bandsDetail.children[0].textContent,/研究母数と暫定勝ち馬/);
 assert.match(bandsDetail.children[1].textContent,/研究帯を持っていた1頭が母数/);
 assert.match(bandsDetail.children[2].textContent,/調教｜S：研究対象1頭／JRDB暫定1着1頭/);
 assert.match(coreView.get('autoFiveProviderStatus').textContent,/研究対象 1頭/);
 assert.equal(coreView.storage.get(FIVE_STORAGE),originalFive);
 assert.equal(coreView.storage.get(STORAGE),ticketBeforeProvider);
 coreView.setFiveExposureCorrupt(true);
 await coreView.get('autoFiveProviderCheck').onclick();
 assert.match(coreView.get('autoFiveProviderStatus').textContent,/安全に比較できませんでした/);
 assert.equal(coreView.get('autoFiveProviderRaces').children.length,0);
 assert.equal(coreView.storage.get(FIVE_STORAGE),originalFive);
 coreView.setFiveExposureCorrupt(false);
 coreView.setCoreProviderCorrupt(true);
 await coreView.get('autoFiveProviderCheck').onclick();
 assert.match(coreView.get('autoFiveProviderStatus').textContent,
              /安全に比較できませんでした/);
 assert.equal(coreView.get('autoFiveProviderRaces').children.length,0);
 assert.equal(coreView.storage.get(FIVE_STORAGE),originalFive);
 coreView.setCoreProviderCorrupt(false);
 coreView.get('autoDay').value='2099-01-03';coreView.get('autoDay').onchange();
 assert.equal(coreView.get('autoFiveProviderCheck').disabled,true);
 assert.equal(coreView.get('autoFiveProviderRaces').children.length,0);
 // Signed 79-point prestart tickets are isolated from the older 85 study
 // and remain usable for non-mutating server verification after race off.
 const r6Proof=boot(),r6First=[1,2],r6Second=[1,2,3,4,5],
  r6Third=[1,2,3,4,5,6,7],r6Tickets=[];
 for(const x of r6First)for(const y of r6Second)for(const z of r6Third)
  if(x!==y&&x!==z&&y!==z)r6Tickets.push([x,y,z]);
 const r6Entry={signature:'e'.repeat(64),snapshot:{
  version:'owner-research6-draft-receipt-1',
  date:day,track:'東京',race:1,
  sourceKind:'prestart-unverified-research6-79-draft',
  capturedAt:'2099-01-01T09:00:00+09:00',
  scheduledOffAt:'2099-01-01T12:00:00+09:00',
  policyVersion:'research-6',researchWeight:79,
  remainingUnassessedWeight:21,runnerCount:7,
  first:r6First,second:r6Second,third:r6Third,
  tickets:r6Tickets,points:40,amountYen:4000,
  researchOnly:true,officialJraVerified:false,
  predictionReady:false,actualPurchase:false
 }};
 r6Proof.storage.set(R6_STORAGE,JSON.stringify([r6Entry]));
 r6Proof.get('autoDay').value=date;
 r6Proof.get('autoDay').onchange();
 assert.match(r6Proof.get('autoResearch6DraftSaveStatus').textContent,/初回固定した新79点/);
 assert.equal(r6Proof.get('autoResearch6DraftVerify').disabled,false);
 assert.equal(r6Proof.get('autoResearch6DraftSaved').children.length,1);
 const r6Original=r6Proof.storage.get(R6_STORAGE);
 await r6Proof.get('autoResearch6DraftVerify').onclick();
 assert.match(r6Proof.get('autoResearch6DraftVerifyStatus').textContent,/署名を確認：1R/);
 assert.equal(r6Proof.storage.get(R6_STORAGE),r6Original);
 assert.equal(r6Proof.requests.filter(x=>
  x.url==='/api/owner-research6-draft-verify').length,1);
 assert.equal(r6Proof.requests.filter(x=>x.url==='/api/jrdb/history').length,0);
 const forgedR6=boot();
 forgedR6.storage.set(R6_STORAGE,JSON.stringify([{
  ...r6Entry,snapshot:{...r6Entry.snapshot,amountYen:9900}
 }]));
 forgedR6.get('autoDay').value=date;
 forgedR6.get('autoDay').onchange();
 assert.equal(forgedR6.get('autoResearch6DraftVerify').disabled,true);
 assert.match(forgedR6.get('autoResearch6DraftSaveStatus').textContent,/確認できません/);
 assert.ok(!js.includes('innerHTML'),'no DOM HTML injection');
 assert.ok(!js.includes('owner-real-purchases-v1'),'do not write actual purchases');
 console.log('Owner auto forecast: 40-point signed save, idempotency, tamper block, no purchased writes PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
