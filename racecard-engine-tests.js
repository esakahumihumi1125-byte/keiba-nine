/* KEIBA NINE racecard engine regression tests (runs in Node or browser). */
(function(root){
'use strict';
const engine=root.KeibaNineRacecard;
if(!engine)throw Error('racecard-engine.js must be loaded first');
const axes=['recent','training','course','pedigree','pace'];
const grades=[
  ['S','S','S','S','S'],
  ['S','S','S','S','A'],
  ['S','S','S','A','B'],
  ['S','A','S','B','B'],
  ['A','A','A','B','B'],
  ['A','B','A','B','C'],
  ['B','B','B','C','C']
];
const sample={source:'internal-only unit test',licenseConfirmed:true,date:'2026-11-07',track:'京都',race:1,horses:grades.map((row,i)=>({number:i+1,name:'ダミー'+(i+1),scratched:false,evaluations:Object.fromEntries(axes.map((a,k)=>[a,{grade:row[k],note:'テスト用ダミー評価の説明'}]))}))};
const clone=x=>JSON.parse(JSON.stringify(x));
function assert(value,msg){if(!value)throw Error(msg)}
function throws(x,msg){let did=false;try{engine.validateRacecard(x)}catch(e){did=true}assert(did,msg)}
const full=engine.analyzeRacecard(sample);
assert(full.ready,'valid evidence must be ready');
assert(full.combinations.length===40,'7-horse formation should yield 40 distinct tickets');
assert(new Set(full.combinations.map(a=>a.join('-'))).size===full.combinations.length,'no duplicates');
const invalidEvidence=clone(sample);delete invalidEvidence.horses[0].evaluations.training;
assert(!engine.analyzeRacecard(invalidEvidence).ready,'missing evidence must be skipped');
const noScratch=clone(sample);delete noScratch.horses[1].scratched;
assert(!engine.analyzeRacecard(noScratch).ready,'unknown scratch status must be skipped');
const scratched=clone(sample);scratched.horses[0].scratched=true;
const r=engine.analyzeRacecard(scratched);
assert(r.ready&&r.combinations.length===32,'scratch must remove a runner and retain 32 tickets');
assert(r.combinations.every(a=>!a.includes(1)),'scratched runner cannot appear');
const tied=clone(sample);tied.horses[2].evaluations=clone(tied.horses[1].evaluations);
assert(!engine.analyzeRacecard(tied).ready,'tie at 1st selection boundary must skip');
const close=clone(sample);for(const h of close.horses)for(const value of Object.values(h.evaluations))value.grade='A';
assert(!engine.analyzeRacecard(close).ready,'all equal scores must skip');
const fullField=clone(sample);
for(let i=8;i<=18;i++)fullField.horses.push({number:i,name:'ダミー'+i,scratched:false,evaluations:Object.fromEntries(axes.map(a=>[a,{grade:'C',note:'テスト用ダミー評価の説明'}]))});
const large=engine.analyzeRacecard(fullField);
assert(large.ready&&large.combinations.length===40,'18 runners must stay within 48 tickets');
assert(large.combinations.every(c=>c.every(n=>n>=1&&n<=7)),'excluded lower-rated runners must not enter formation');
const invalidScratched=clone(sample);invalidScratched.horses[0].scratched='false';throws(invalidScratched,'string scratch flag must fail');
const noLicense=clone(sample);noLicense.licenseConfirmed=false;throws(noLicense,'license acknowledgment required');
const duplicate=clone(sample);duplicate.horses[1].number=duplicate.horses[0].number;throws(duplicate,'duplicate number must fail');
const badDate=clone(sample);badDate.date='2026-02-30';throws(badDate,'invalid date must fail');
const badGrade=clone(sample);badGrade.horses[0].evaluations.recent.grade='A+';throws(badGrade,'invalid grade must fail');
root.KeibaNineRacecardTests={passed:16,details:'valid, count, dedup, missing, scratch status, scratch removal, exclusion, boundary tie, close ratings, invalid data'};
})(typeof window!=='undefined'?window:globalThis);
