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
// Stress check: 120 races / 18 runners / long private evidence notes must fit the local transfer.
const letters=['S','A','B','C'],weights=[25,25,20,15,15],scores=new Map();
for(let n=0;n<1024;n++){
 const row=keys.map((_,j)=>letters[Math.floor(n/Math.pow(4,j))%4]);
 const score=row.reduce((sum,grade,j)=>sum+(4-letters.indexOf(grade))*weights[j],0);
 if(!scores.has(score))scores.set(score,row);
}
const unique=[...scores].sort((a,b)=>b[0]-a[0]).slice(0,18);
const largeHorses=unique.map(([,row],i)=>({
 number:i+1,name:'架空の長文テスト馬'+(i+1),scratched:false,
 evaluations:Object.fromEntries(keys.map((k,j)=>[k,{grade:row[j],note:'絶対に外へ出さない架空の内部テスト根拠'.repeat(25).slice(0,500)}]))
}));
const tracks=['東京','京都','福島'];
const largeBundle={kind:'keiba-nine-racecards',schema:1,source:'大容量内部検証',licenseConfirmed:true,
 racecards:Array.from({length:120},(_,i)=>({
  date:'2026-11-'+String(1+Math.floor(i/36)).padStart(2,'0'),
  track:tracks[Math.floor(i/12)%3],race:i%12+1,
  horses:JSON.parse(JSON.stringify(largeHorses))
 }))};
const largeRows=root.KeibaNinePreviewBridge.toDraftRows(largeBundle);
const transfer=JSON.stringify({kind:'keiba-nine-local-preview',schema:1,createdAt:123456789,forecasts:largeRows});
ok(largeRows.length===120&&largeRows.every(r=>r.status==='draft'),'120 fully scored race previews');
ok(transfer.length<490000,'local transfer remains within 490k characters');
ok(!transfer.includes('絶対に外へ出さない架空の内部テスト根拠'),'evidence source notes not exported by the bridge');
const portable=root.KeibaNinePreviewBridge.toPortablePreview(bundle,'2026-11-03T11:00:00.000Z');
ok(portable.kind==='keiba-nine-test-preview'&&portable.schema===1,'portable export schema');
ok(portable.forecasts.length===2&&portable.forecasts.every(r=>r.recordType==='test'&&r.off===''),'portable export never live');
ok(portable.forecasts[0].status==='draft'&&portable.forecasts[1].status==='skip','portable draft and skip');
ok(portable.generatedAt==='2026-11-03T11:00:00.000Z'&&portable.source==='自動テスト','portable source and timestamp');
const largePortable=root.KeibaNinePreviewBridge.toPortablePreview(largeBundle,'2026-11-03T11:00:00.000Z');
const json=JSON.stringify(largePortable);
const utf8Bytes=encodeURIComponent(json).replace(/%[0-9A-F]{2}/gi,'x').length;
ok(utf8Bytes<490000,'maximum 120 race UTF-8 export remains below main-app file import limit');
ok(!json.includes('絶対に外へ出さない架空の内部テスト根拠'),'portable backup excludes source evidence notes');
ok(largePortable.forecasts.every(r=>r.recordType==='test'&&['draft','skip'].includes(r.status)),'full field cannot be promoted to final');
root.KeibaNinePreviewBridgeTests={passed:20};
})(window);
