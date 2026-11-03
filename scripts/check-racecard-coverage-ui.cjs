/* Mobile coverage display regression with fictional fixtures; no API or browser required. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm');
global.window=globalThis;
require('../racecard-engine.js');
require('../racecard-batch.js');
require('../racecard-coverage.js');
require('../racecard-reference.js');
require('../racecard-preview-bridge.js');
const html=fs.readFileSync('racecard-batch.html','utf8');
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(x=>x[1]).pop();
if(!script)throw Error('Batch controller missing');
const dom=new Map();
const get=id=>{
 if(!dom.has(id))dom.set(id,{
  id,value:'',textContent:'',disabled:false,files:[],options:[],selectedIndex:0,events:{},
  addEventListener(event,fn){this.events[event]=fn},
  replaceChildren(){this.options=[];this.value='';this.selectedIndex=0},
  add(option){this.options.push(option);if(this.options.length===1)this.value=option.value}
 });
 return dom.get(id);
};
class Option{constructor(label,value){this.label=label;this.value=value}}
vm.runInNewContext(script,{document:{getElementById:get},window:globalThis,Option,console});
const axes=['recent','training','course','pedigree','pace'];
const grades=[['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],['S','A','S','B','B'],['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']];
const horses=grades.map((g,i)=>({
 number:i+1,name:'架空テスト馬'+(i+1),scratched:false,
 evaluations:Object.fromEntries(axes.map((key,j)=>[key,{grade:g[j],note:'架空のテストで使う根拠の文章です'}]))
}));
const tracks=['東京','京都','福島'];
const bundle={kind:'keiba-nine-racecards',schema:1,source:'架空の出馬表',licenseConfirmed:true,
 program:{source:'仮のJRA日程（テスト用）',checkedAt:'2026-11-06T17:00:00+09:00',
  sessions:tracks.map(track=>({date:'2026-11-07',track,races:Array.from({length:12},(_,i)=>i+1)}))},
 racecards:tracks.flatMap(track=>Array.from({length:12},(_,i)=>({
  date:'2026-11-07',track,race:i+1,horses:JSON.parse(JSON.stringify(horses))
 })))
};
const copy=x=>JSON.parse(JSON.stringify(x));
let n=0;
function ok(value,label){if(!value)throw Error(label);n++}
function run(b){get('raw').value=JSON.stringify(b);get('analyze').events.click()}
run(bundle);
ok(get('status').textContent.includes('形式チェック完了'),'valid batch');
ok(get('coverageStatus').textContent.includes('全36R'),'declared 36R all ready');
ok(get('coverageResult').textContent.includes('京都｜12/12R'),'per-venue status');
const partial=copy(bundle);partial.racecards=partial.racecards.filter(r=>r.track!=='京都'||r.race!==6);
run(partial);
ok(get('coverageStatus').textContent.includes('未完了'),'missing race is not complete');
ok(get('coverageResult').textContent.includes('未取得：6R'),'missing Kyoto 6R displayed');
const noEvidence=copy(bundle);delete noEvidence.racecards[0].horses[0].evaluations.training;
run(noEvidence);
ok(get('coverageResult').textContent.includes('評価待ち・見送り：1R'),'not evaluated is reported');
ok(!get('coverageStatus').textContent.includes('全36R'),'incomplete does not show complete banner');
const noProgram=copy(bundle);delete noProgram.program;run(noProgram);
ok(get('coverageStatus').textContent.includes('網羅性は判定できません'),'without explicit program no all-R claim');
const invalid=copy(bundle);invalid.program.sessions[0].races.push(13);run(invalid);
ok(get('status').textContent.includes('検証NG'),'invalid program fails');
ok(get('savePreview').disabled===true,'failed program cannot export');
console.log('Declared race program UI: '+n+' checks passed');
