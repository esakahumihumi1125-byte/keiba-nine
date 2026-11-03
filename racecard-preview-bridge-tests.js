/* Offline-only preview bridge regression tests. No actual race data. */
(function(root){
'use strict';
const keys=['recent','training','course','pedigree','pace'];
const grades=[['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],['S','A','S','B','B'],['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']];
const horses=grades.map((row,i)=>({number:i+1,name:'架空テスト'+(i+1),scratched:false,evaluations:Object.fromEntries(keys.map((k,j)=>[k,{grade:row[j],note:'内部検証用の架空の根拠です'}]))}));
const bundle={kind:'keiba-nine-racecards',schema:1,source:'自動テスト',licenseConfirmed:true,racecards:[
 {date:'2026-11-07',track:'京都',race:1,horses:JSON.parse(JSON.stringify(horses))},
 {date:'2026-11-07',track:'京都',race:2,horses:JSON.parse(JSON.stringify(horses))}
]};
delete bundle.racecards[1].horses[0].evaluations.training;
function ok(c,what){if(!c)throw Error(what)}
const rows=root.KeibaNinePreviewBridge.toDraftRows(bundle);
ok(rows.length===2,'2 races exported');
ok(rows[0].status==='draft'&&rows[1].status==='skip','draft and skip separated');
ok(rows.every(r=>r.recordType==='test'&&r.confidence==='C'&&r.off===''),'never live, final or claimed off time');
ok(rows[0].triPoints===40&&rows[1].triPoints===0,'ticket counts');
ok(rows[0].first.length===2&&rows[1].first.length===0,'skip includes no tickets');
ok(rows.every(r=>r.trioPool.length===0),'no invented trio recommendations');
ok(rows[0].ranking.length===7&&rows[0].horses[0].name==='架空テスト1','ranking and names');
ok(rows.every(r=>!('raceCard' in r)&&!('evidence' in r)),'no fabricated official confirmations');
ok(rows[1].intent==='見送り'&&rows[0].intent==='参考','intent safely derived');
ok(new Set(rows.map(r=>r.date+'|'+r.track+'|'+r.race)).size===2,'unique races');
root.KeibaNinePreviewBridgeTests={passed:10};
})(window);
