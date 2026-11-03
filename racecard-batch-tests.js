/* KEIBA NINE offline batch adapter regression checks. */
(function(root){
'use strict';
if(!root.KeibaNineBatch||!root.KeibaNineRacecard)throw Error('Load racecard-engine.js and racecard-batch.js first');
const tracks=['京都','東京','福島'];
const keys=['recent','training','course','pedigree','pace'];
const grades=[['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],['S','A','S','B','B'],['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']];
const horses=grades.map((line,i)=>({number:i+1,name:'ダミー馬'+(i+1),scratched:false,evaluations:Object.fromEntries(keys.map((k,j)=>[k,{grade:line[j],note:'内部テスト用ダミー根拠情報'}]))}));
const card=(track,race,date='2026-11-07')=>({date,track,race,horses:JSON.parse(JSON.stringify(horses))});
const sample={kind:'keiba-nine-racecards',schema:1,source:'内部自動テスト用',licenseConfirmed:true,racecards:tracks.flatMap(t=>Array.from({length:12},(_,i)=>card(t,i+1)))};
const copy=x=>JSON.parse(JSON.stringify(x));
function ok(v,message){if(!v)throw Error(message)}
function rejects(x,message){let fail=false;try{root.KeibaNineBatch.analyzeBundle(x)}catch(_){fail=true}ok(fail,message)}
const analysis=root.KeibaNineBatch.analyzeBundle(sample);
ok(analysis.total===36&&analysis.ready===36&&analysis.skipped===0,'36 race batch');
ok(analysis.entries.every(e=>e.analysis.combinations.length===40),'40 distinct tickets in every race');
ok(analysis.entries[0].track==='福島'&&analysis.entries[35].track==='京都','stable JRA track ordering');
const noEvidence=copy(sample);
delete noEvidence.racecards[0].horses[1].evaluations.training;
const mixed=root.KeibaNineBatch.analyzeBundle(noEvidence);
ok(mixed.total===36&&mixed.ready===35&&mixed.skipped===1,'missing evidence skips only affected race');
const duplicate=copy(sample);duplicate.racecards.push(copy(duplicate.racecards[0]));
rejects(duplicate,'duplicate race rejected');
const badLicense=copy(sample);badLicense.licenseConfirmed=false;
rejects(badLicense,'missing licence acknowledgement rejected');
const conflictSource=copy(sample);conflictSource.racecards[0].source='別の提供元';
rejects(conflictSource,'conflicting per-race source rejected');
const invalidHorse=copy(sample);invalidHorse.racecards[0].horses[0].number=19;
rejects(invalidHorse,'invalid horse number rejected');
const future=copy(sample);future.racecards.push(card('京都',1,'2026-11-08'));
ok(root.KeibaNineBatch.analyzeBundle(future).total===37,'different date can contain same track and R');
const tooMany=copy(sample);tooMany.racecards=Array.from({length:121},(_,i)=>card(tracks[Math.floor(i/12)%3],i%12+1,'2026-11-'+String(7+Math.floor(i/36)).padStart(2,'0')));
rejects(tooMany,'over 120 racecards rejected');
const empty=copy(sample);empty.racecards=[];
rejects(empty,'empty input rejected');
root.KeibaNineBatchTests={passed:11,description:'36 all-race fixture, 40 tickets, ordering, partial skip, duplicates, license, source, horse number, multi-day, upper limit, empty'};
})(window);
