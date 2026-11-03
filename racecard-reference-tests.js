/* Offline racecard cross-check regression tests; all names and data fictional. */
(function(root){
'use strict';
const k=['recent','training','course','pedigree','pace'],grades=[
 ['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],['S','A','S','B','B'],
 ['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']];
const horses=grades.map((row,i)=>({number:i+1,name:'架空'+(i+1)+'号',scratched:false,evaluations:Object.fromEntries(k.map((x,j)=>[x,{grade:row[j],note:'架空の検証用根拠です'}]))}));
const base={kind:'keiba-nine-racecards',schema:1,source:'許諾済テスト',licenseConfirmed:true,racecards:[
 {date:'2026-11-07',track:'京都',race:1,off:'10:00',horses},
 {date:'2026-11-07',track:'京都',race:2,horses:JSON.parse(JSON.stringify(horses))}
]};
const reference={kind:'keiba-nine-racecard-reference',schema:1,source:'別資料（架空）',checkedAt:'2026-11-06T17:30:00+09:00',races:base.racecards.map(r=>({
 date:r.date,track:r.track,race:r.race,complete:true,off:r.off,
 horses:r.horses.map(h=>({number:h.number,name:h.name,scratched:h.scratched}))
}))};
const copy=x=>JSON.parse(JSON.stringify(x));
function assert(c,m){if(!c)throw Error(m)}
function reject(r,m){let passed=false;try{root.KeibaNineReference.validateReference(r)}catch(e){passed=true}assert(passed,m)}
let count=0;
function check(c,m){assert(c,m);count++}
check(root.KeibaNineReference.compareBundle(base,reference).matched,'matching data');
check(root.KeibaNineReference.compareBundle(base,reference).passed===2,'two matched races');
const renamed=copy(base);renamed.racecards[0].horses[0].name='別の架空馬';
check(!root.KeibaNineReference.compareBundle(renamed,reference).matched,'name mismatch');
const scr=copy(base);scr.racecards[0].horses[0].scratched=true;
check(root.KeibaNineReference.compareBundle(scr,reference).issues.some(x=>x.includes('取消状態が不一致')),'scratch mismatch');
const uncertain=copy(base);delete uncertain.racecards[0].horses[0].scratched;
check(!root.KeibaNineReference.compareBundle(uncertain,reference).matched,'unknown scratch blocked');
const removed=copy(base);removed.racecards[0].horses.shift();
check(root.KeibaNineReference.compareBundle(removed,reference).issues.some(x=>x.includes('照合元にいる馬')),'extra horse in reference');
const extra=copy(base);extra.racecards[0].horses.push({number:8,name:'架空8号',scratched:false});
check(root.KeibaNineReference.compareBundle(extra,reference).issues.some(x=>x.includes('照合元にありません')),'horse missing from reference');
const missing=copy(reference);missing.races.shift();
check(root.KeibaNineReference.compareBundle(base,missing).failed===1,'missing reference race');
const off=copy(base);off.racecards[0].off='10:05';
check(root.KeibaNineReference.compareBundle(off,reference).issues.some(x=>x.includes('発走時刻')),'start time mismatch');
const refsWithoutOff=copy(reference);delete refsWithoutOff.races[0].off;
check(root.KeibaNineReference.compareBundle(base,refsWithoutOff).matched,'optional reference off accepted');
const normalized=copy(reference);normalized.races[0].horses[0].name='架空１号';
check(root.KeibaNineReference.compareBundle(base,normalized).matched,'unicode NFKC normalization');
const incomplete=copy(reference);incomplete.races[0].complete=false;reject(incomplete,'incomplete card rejected');count++;
const invalidDay=copy(reference);invalidDay.races[0].date='2026-02-30';reject(invalidDay,'invalid date rejected');count++;
const dup=copy(reference);dup.races.push(copy(dup.races[0]));reject(dup,'duplicate race rejected');count++;
const dupNumber=copy(reference);dupNumber.races[0].horses[1].number=1;reject(dupNumber,'duplicate horse rejected');count++;
const badFlag=copy(reference);delete badFlag.races[0].horses[0].scratched;reject(badFlag,'missing scratch field rejected');count++;
const badTimestamp=copy(reference);badTimestamp.checkedAt='2026-11-06 17:30';reject(badTimestamp,'timezone required');count++;
const changedNumber=copy(reference);changedNumber.races[0].horses[0].number=10;
check(!root.KeibaNineReference.compareBundle(base,changedNumber).matched,'wrong number rejected');
const sourceText=root.KeibaNineReference.compareBundle(base,reference).notice;
check(sourceText.includes('保証しません'),'no false official claims');

const asOf=Date.parse('2026-11-06T18:00:00+09:00');
check(root.KeibaNineReference.assessFreshness(reference,asOf).status==='recent','current timestamp recognized');
check(root.KeibaNineReference.assessFreshness(reference,asOf).usable===true,'current timestamp eligible for preview');
check(root.KeibaNineReference.assessFreshness(reference,Date.parse('2026-11-05T15:00:00+09:00')).status==='future','future-dated confirmation blocked');
const stale=copy(reference);stale.checkedAt='2026-11-01T10:00:00+09:00';
check(root.KeibaNineReference.assessFreshness(stale,asOf).status==='stale','older than 72 hours on future race blocked');
check(!root.KeibaNineReference.assessFreshness(stale,asOf).usable,'stale timestamp cannot unlock preview');
check(root.KeibaNineReference.assessFreshness(stale,Date.parse('2026-11-10T10:00:00+09:00')).status==='historical','old race treated as historical');
check(root.KeibaNineReference.assessFreshness(stale,Date.parse('2026-11-10T10:00:00+09:00')).usable,'historical comparison remains available as test preview');
const nowRef=copy(reference);nowRef.checkedAt=new Date().toISOString();
check(root.KeibaNineReference.compareBundle(base,nowRef).readyForPreview,'matched reference with current timestamp can preview');
const expired=copy(reference);expired.checkedAt='2000-01-01T00:00:00+09:00';
check(!root.KeibaNineReference.compareBundle(base,expired).readyForPreview || root.KeibaNineReference.compareBundle(base,expired).freshness.status==='historical','expired or past-race reference not falsely classified as recent');
root.KeibaNineReferenceTests={passed:count};
})(window);
