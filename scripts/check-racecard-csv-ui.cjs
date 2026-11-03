/* Mock mobile CSV importer: checks it only accepts licensed generic CSV.
   This is a synthetic fixture and never downloads or transmits provider records. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm');
global.window=globalThis;
require('../racecard-engine.js');
require('../racecard-batch.js');
require('../racecard-csv.js');
require('../racecard-coverage.js');
require('../racecard-reference.js');
require('../racecard-preview-bridge.js');
const html=fs.readFileSync('racecard-batch.html','utf8');
const inline=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).pop();
if(!inline)throw Error('HTML controller not found');
const nodes=new Map();
function el(id){
 if(!nodes.has(id))nodes.set(id,{
  id,value:'',checked:false,textContent:'',disabled:false,options:[],selectedIndex:0,files:[],events:{},
  addEventListener(name,fn){this.events[name]=fn},
  click(){this.events.click?.()},
  replaceChildren(){this.options=[];this.value='';this.selectedIndex=0},
  add(x){this.options.push(x);if(this.options.length===1)this.value=x.value}
 });
 return nodes.get(id);
}
class Option{constructor(text,value){this.text=text;this.value=value}}
vm.runInNewContext(inline,{document:{getElementById:el},Option,window:globalThis,console});
let count=0;
const ok=(v,name)=>{if(!v)throw Error(name);count++};
const axes=['recent','training','course','pedigree','pace'];
const grades=[
 ['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],
 ['S','A','S','B','B'],['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']
];
const header=['date','track','race','number','name','scratched',...axes.flatMap(x=>[x+'_grade',x+'_note'])];
const quote=x=>/[",\n]/.test(String(x))?'"'+String(x).replace(/"/g,'""')+'"':String(x);
const content=header.join(',')+'\n'+grades.map((g,i)=>[
 '2026-11-07','京都','1',i+1,'架空馬'+(i+1),'false',
 ...axes.flatMap((a,j)=>[g[j],'架空の根拠メモです'])
].map(quote).join(',')).join('\n');
el('csvSource').value='利用条件確認済みの内部テスト資料';
el('csvInput').value=content;
el('csvConvert').click();
ok(el('csvStatus').textContent.includes('利用許諾'),'must ask for licence confirmation first');
ok(el('raw').value==='','unlicensed CSV never reaches racecard JSON');
el('csvLicense').checked=true;
el('csvConvert').click();
ok(el('csvStatus').textContent.includes('1Rを変換'),'one-click valid conversion');
ok(el('status').textContent.startsWith('形式チェック完了'),'existing validator is run');
ok(JSON.parse(el('raw').value).racecards.length===1,'one legitimate-format racecard');
ok(el('coverageStatus').textContent.includes('網羅性は判定できません'),'CSV without program never claims all races complete');
const bad=content.replace('false','unknown');
el('csvInput').value=bad;
el('csvConvert').click();
ok(el('csvStatus').textContent.includes('変換できません'),'invalid CSV reports error');
ok(JSON.parse(el('raw').value).racecards.length===1,'bad CSV does not overwrite previously validated input');
console.log('Generic CSV mobile import: '+count+' checks passed');
