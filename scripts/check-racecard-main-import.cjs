/* Run with Node 20+: offline adapter output must remain valid in the main app importer.
   All horses and grades are fictional. No network, persistent data or betting. */
'use strict';
const fs=require('node:fs');
const vm=require('node:vm');
global.window=globalThis;
require('../racecard-engine.js');
require('../racecard-batch.js');
require('../racecard-preview-bridge.js');
const html=fs.readFileSync('keiba-nine-beta51-feed-record.html','utf8');
function between(start,end){
 const i=html.indexOf(start);
 if(i<0)throw Error('main-app parser start not found: '+start);
 const j=html.indexOf(end,i+start.length);
 if(j<0)throw Error('main-app parser end not found: '+end);
 return html.slice(i,j);
}
const identity=between('const identity40=','\n');
const parserSource=[
 "const TRACKS=new Set(['東京','京都','新潟','中山','阪神','中京','福島','小倉','札幌','函館']);",
 between('const toArray40=','const when40='),
 between('function norm40(','// Optional enriched fields'),
 between('const AXES41=','const gradeStyle41='),
 identity,
 between('function formatParse40(','function validate40()')
].join('\n');
const parse=vm.runInNewContext(parserSource+'\nformatParse40');
function check(condition,label){if(!condition)throw Error(label)}
const gradeRows=[
 ['S','S','S','S','S'],
 ['S','S','S','S','A'],
 ['S','S','S','A','B'],
 ['S','A','S','B','B'],
 ['A','A','A','B','B'],
 ['A','B','A','B','C'],
 ['B','B','B','C','C']
];
const keys=['recent','training','course','pedigree','pace'];
const horses=gradeRows.map((g,i)=>({
 number:i+1,name:'架空テスト馬'+(i+1),scratched:false,
 evaluations:Object.fromEntries(keys.map((axis,j)=>[axis,{grade:g[j],note:'内部テスト用の架空根拠を示す文章'}]))
}));
const clone=x=>JSON.parse(JSON.stringify(x));
const bundle={kind:'keiba-nine-racecards',schema:1,source:'内部テスト（架空）',licenseConfirmed:true,racecards:[
 {date:'2026-11-07',track:'京都',race:1,horses:clone(horses)},
 {date:'2026-11-07',track:'京都',race:2,horses:clone(horses)}
]};
delete bundle.racecards[1].horses[0].evaluations.training;
const pack=global.KeibaNinePreviewBridge.toPortablePreview(bundle,'2026-11-03T11:00:00.000Z');
const rows=parse(JSON.stringify(pack));
check(rows.length===2,'main app must parse both races');
check(rows[0].recordType==='test'&&rows[0].status==='draft'&&rows[0].tri.length===40,'valid evidence imports draft preview with 40 tickets');
check(rows[1].status==='skip'&&rows[1].tri.length===0,'missing evidence imports skip without tickets');
check(rows.every(r=>r.recordType==='test'&&r.off===''&&r.trio.length===0),'no automatic live bet or invented trio');
check(rows[0].horses.length===7&&rows[0].horses[0].name==='架空テスト馬1','horse names and grades survive');
const large={...bundle,racecards:Array.from({length:120},(_,i)=>({
 date:'2026-11-'+String(7+Math.floor(i/36)).padStart(2,'0'),
 track:['京都','東京','福島'][Math.floor(i/12)%3],race:i%12+1,
 horses:clone(horses)
}))};
const largePack=global.KeibaNinePreviewBridge.toPortablePreview(large,'2026-11-03T11:00:00.000Z');
const largeRows=parse(JSON.stringify(largePack));
check(largeRows.length===120&&largeRows.every(r=>r.recordType==='test'),'main parser accepts 120 preview races');
check(largeRows.every(r=>r.tri.length<=48),'every race stays within 48 tickets');
console.log('Main-app preview importer compatibility: 7 checks passed');
