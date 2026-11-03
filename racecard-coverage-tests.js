/* Program coverage tests; all fixtures are synthetic and do not represent official racing. */
(function(root){
'use strict';
const keys=['recent','training','course','pedigree','pace'];
const grades=[
 ['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],
 ['S','A','S','B','B'],['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']
];
const horses=grades.map((g,i)=>({number:i+1,name:'テスト馬'+i,scratched:false,
 evaluations:Object.fromEntries(keys.map((k,j)=>[k,{grade:g[j],note:'架空テストにおける確認用の根拠情報'}]))}));
const clone=x=>JSON.parse(JSON.stringify(x));
const cards=[...['東京','京都','福島']].flatMap(track=>Array.from({length:12},(_,i)=>({
 date:'2026-11-07',track,race:i+1,horses:clone(horses)
})));
const program={source:'テスト用の仮開催予定（公式ではない）',checkedAt:'2026-11-06T17:00:00+09:00',
 sessions:['東京','京都','福島'].map(track=>({date:'2026-11-07',track,races:Array.from({length:12},(_,i)=>i+1)}))};
const bundle={kind:'keiba-nine-racecards',schema:1,source:'テスト用',licenseConfirmed:true,racecards:cards,program};
function assert(x,msg){if(!x)throw Error(msg)}
let count=0;
function ok(x,msg){assert(x,msg);count++}
function rejects(x,msg){let did=false;try{root.KeibaNineCoverage.auditCoverage(x)}catch(_){did=true}ok(did,msg)}
const full=root.KeibaNineCoverage.auditCoverage(bundle);
ok(full.declared===true,'coverage defined');
ok(full.expected===36&&full.received===36&&full.ready===36,'all 36 races counted');
ok(full.allCardsPresent===true&&full.allPreviewsReady===true,'all data present and evaluated');
ok(full.sessions.length===3&&full.sessions.every(x=>x.ready===12),'three venue group counts');
const partial=clone(bundle);partial.racecards=partial.racecards.filter(x=>x.track!=='京都'||x.race!==6);
const part=root.KeibaNineCoverage.auditCoverage(partial);
ok(!part.allCardsPresent&&part.missing.length===1&&part.missing[0]==='2026-11-07|京都|6','missing Kyoto 6R precisely detected');
ok(part.sessions.find(x=>x.track==='京都').missingRaces[0]===6,'session-level missing race shown');
const noEvidence=clone(bundle);delete noEvidence.racecards[0].horses[0].evaluations.training;
const pending=root.KeibaNineCoverage.auditCoverage(noEvidence);
ok(pending.allCardsPresent&&!pending.allPreviewsReady&&pending.unready.length===1,'available card without evidence not ready');
const unexpected=clone(bundle);unexpected.racecards.push({date:'2026-11-08',track:'東京',race:1,horses:clone(horses)});
const surprise=root.KeibaNineCoverage.auditCoverage(unexpected);
ok(!surprise.allCardsPresent&&surprise.unexpected.length===1,'unscheduled race marked unexpected');
const noPlan=clone(bundle);delete noPlan.program;
const unknown=root.KeibaNineCoverage.auditCoverage(noPlan);
ok(!unknown.declared&&!unknown.allCardsPresent&&!unknown.allPreviewsReady,'no program never implies complete');
const narrower=clone(bundle);narrower.program={...program,sessions:[{date:'2026-11-07',track:'東京',races:[1,2]}]};
const narrowed=root.KeibaNineCoverage.auditCoverage(narrower);
ok(narrowed.expected===2&&narrowed.unexpected.length===34,'program may specify subset; extras flagged');
const badNumber=clone(bundle);badNumber.program.sessions[0].races.push(13);rejects(badNumber,'invalid 13R is rejected');
const duplicated=clone(bundle);duplicated.program.sessions[0].races[2]=2;rejects(duplicated,'duplicate race in program rejected');
const duplicateSession=clone(bundle);duplicateSession.program.sessions.push(clone(duplicateSession.program.sessions[0]));rejects(duplicateSession,'duplicate venue/day rejected');
const incorrectDate=clone(bundle);incorrectDate.program.sessions[0].date='2026-02-30';rejects(incorrectDate,'invalid date rejected');
const noSource=clone(bundle);noSource.program.source='';rejects(noSource,'source required');
const noTime=clone(bundle);noTime.program.checkedAt='2026-11-06 17:00';rejects(noTime,'timezone required');
const tooMany=clone(bundle);tooMany.program.sessions=Array.from({length:11},(_,i)=>({
 date:'2026-11-'+String(7+i).padStart(2,'0'),track:'東京',races:Array.from({length:12},(_,k)=>k+1)
}));rejects(tooMany,'more than 120 expected races rejected');
const multiDay=clone(bundle);multiDay.program.sessions.push({date:'2026-11-08',track:'京都',races:[1,2]});
const multi=root.KeibaNineCoverage.auditCoverage(multiDay);
ok(multi.missing.length===2,'different day race numbers are unique coverage keys');
const reordered=clone(bundle);reordered.racecards.reverse();
ok(root.KeibaNineCoverage.auditCoverage(reordered).allPreviewsReady,'order independence');
root.KeibaNineCoverageTests={passed:count};
})(window);
