/* Offline manual historical lookup UI regression: no provider traffic. */
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const script = fs.readFileSync('/tmp/keiba-private-console.js', 'utf8');
const nodes = new Map(), requests = [];
const FACTORS = ['training','recent','course_distance','pace','ground',
                 'pedigree','draw_weight','jockey_stable','rotation','body_condition'];
const materialsFactors = Object.fromEntries(FACTORS.map(key=>[
 key,{grade:'未評価',assessmentComplete:false,observedRunnerCount:
  ({training:2,recent:2,course_distance:2,ground:1})[key]??null}
]));
function el(id) {
 if (!nodes.has(id)) nodes.set(id, {
  id, value:'',disabled:false,textContent:'',files:[],children:[],
  replaceChildren(){this.children=[];},
  append(child){this.children.push(child)},
  onclick:null,onchange:null,
 });
 return nodes.get(id);
}
async function fetchMock(url, options) {
 requests.push({url,options});
 if (url === '/api/status')
  return {ok:true,json:async()=>({jrdbConfigured:true,historyConfigured:true})};
 if (url === '/api/jrdb/history')
  return {ok:true,json:async()=>({
    selectedPastRaces:2,deferredPastRaces:1,
    unavailablePastProgrammes:0,unavailablePastConditions:1,
    predictionReady:false,goingSuitabilityAssessed:false,
    tenFactorMaterials:{predictionReady:false,bettingReady:false,gradedFactors:0,
      races:[{track:'東京',race:1,runnerCount:3,predictionReady:false,bettingReady:false,
              gradedFactors:0,factors:materialsFactors}]},
    allTenFactorSources:{
      version:'combined-ten-factor-observations-1',
      raceCount:1,predictionReady:false,bettingReady:false,
      races:[{track:'東京',race:1,runnerCount:3,
        sourceMaterialSlots:10,provisionalFactorSlots:2,
        observationOnlySlots:8,unmappedFactorCount:0,
        verifiedFactorCount:0,runnersWithComparableCourse:2,
        runnersWithKnownGoingComparable:1,runnersWithIncompleteHistory:1,
        runnersWithBothPersonnelNames:2,runnersWithConformationCodes:1,
        historySuitabilityAssessed:false,jockeyTrainerPerformanceAssessed:false,
        bodyConditionAssessed:false,raceDayBodyWeightFetched:false,
        officialJraFinalVerification:false,overallRankReady:false,
        predictionReady:false,bettingReady:false}]
    },
    privateHistoryFactors:{
      version:'private-course-ground-materials-1',
      raceCount:1,predictionReady:false,bettingReady:false,
      races:[{track:'東京',race:1,runnerCount:3,
       runnersWithComparableCourse:2,runnersWithKnownGoingComparable:1,
       runnersWithWetComparable:1,runnersMatchingCurrentGoing:1,
       runnersWithIncompleteHistory:1,unknownComparableGoingRuns:1,
       runnersWithCurrentGoingUnknown:0,
       observationOnlyFactors:['pace','course_distance','ground'],
       unmappedFactorCount:5,verifiedFactorCount:0,suitabilityAssessed:false,
       overallRankReady:false,predictionReady:false,bettingReady:false}]
    },
    evidenceQuality:{predictionReady:false,predictionConfidenceAssessed:false,
      races:[{track:'東京',race:1,runnerCount:3,unlinkedPastRuns:1,
        courseComparableSamples:{none:1,oneOrTwo:1,threePlus:1},
        knownGoingComparableSamples:{none:2,oneOrTwo:1,threePlus:0}}]},
    goingSummary:{races:[
      {track:'東京',race:1,heavyComparableRuns:1,heavyTopThreeRuns:1,
       poorComparableRuns:0,poorTopThreeRuns:0,unknownComparableRuns:1}
    ]}
  })};
 throw new Error('Unexpected request: '+url);
}
const document = {getElementById:el,createElement:tag=>({
 tag,className:'',textContent:'',children:[],append(c){this.children.push(c)}
})};
vm.runInNewContext(script,{document,fetch:fetchMock,Date,console,JSON,encodeURIComponent});
async function settle(){
 await new Promise(resolve=>setImmediate(resolve));
 await new Promise(resolve=>setImmediate(resolve));
}
(async()=>{
 await settle();
 assert.equal(requests.length,1,'history lookup must never be automatic');
 assert.equal(requests[0].url,'/api/status');
 assert.equal(el('history').disabled,false,'manual lookup enabled only by separate opt in');
 assert.equal(typeof el('history').onclick,'function');
 el('date').value='2026-11-07';
 await el('history').onclick();
 assert.equal(requests.length,2,'one manual click creates only one browser request');
 const request=requests[1];
 assert.equal(request.url,'/api/jrdb/history');
 assert.equal(request.options.method,'POST');
 assert.equal(request.options.credentials,'same-origin');
 assert.equal(request.options.headers['X-Keiba-Request'],'private');
 assert.deepEqual(JSON.parse(request.options.body),{date:'20261107',limit:8});
 assert.match(el('message').textContent,/照合 2件／残り 1件/);
 assert.match(el('message').textContent,/適性評価・予想は未実施/);
 assert.equal(el('races').children.length,1);
 assert.match(el('races').children[0].textContent,/距離比較 3走以上 1頭/);
 assert.match(el('races').children[0].textContent,/馬場比較 3走以上 0頭/);
 assert.match(el('races').children[0].textContent,/過去番組の未照合 1走/);
 assert.match(el('races').children[0].textContent,/予想信頼度：未算定/);
 assert.match(el('races').children[0].textContent,/10項目の資料：調教 2\/3頭/);
 assert.match(el('races').children[0].textContent,/距離 2\/3頭、馬場 1\/3頭/);
 assert.match(el('races').children[0].textContent,/残り6項目は未接続/);
 assert.match(el('races').children[0].textContent,/コース比較あり 2頭/);
 assert.match(el('races').children[0].textContent,/馬場比較あり 1頭/);
 assert.match(el('races').children[0].textContent,/履歴未完成 1頭/);
 assert.match(el('races').children[0].textContent,/10項目の資料枠：10\/10接続/);
 assert.match(el('races').children[0].textContent,/騎手・厩舎の両名あり 2頭/);
 assert.match(el('races').children[0].textContent,/馬体形状コードあり 1頭/);
 assert.match(el('races').children[0].textContent,/当日の馬体重・増減は未取得/);
 assert.match(el('races').children[0].textContent,/確定評価 0項目/);
 assert.match(el('races').children[0].textContent,/総合S\/A\/B\/C未作成/);
 assert.equal(el('history').disabled,false);
 assert.ok(!script.includes('innerHTML'));
 assert.ok(!requests.some(r=>r.url.includes('api_key')));
 console.log('Manual private history UI: 22 checks passed');
})().catch(err=>{console.error(err);process.exitCode=1});
