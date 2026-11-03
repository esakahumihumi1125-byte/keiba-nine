/* Racecard reference UI regression checks (offline, fictional fixture only). */
'use strict';
const fs=require('node:fs');
const vm=require('node:vm');
global.window=globalThis;
require('../racecard-engine.js');
require('../racecard-batch.js');
require('../racecard-preview-bridge.js');
require('../racecard-reference.js');
const html=fs.readFileSync('racecard-batch.html','utf8');
const script=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]).pop();
if(!script)throw Error('Inline racecard batch controller was not found');
const els=new Map();
function el(id){
 if(!els.has(id))els.set(id,{
  id,value:'',textContent:'',disabled:false,files:[],options:[],selectedIndex:0,events:{},
  addEventListener(type,fn){this.events[type]=fn},
  replaceChildren(){this.options=[];this.value='';this.selectedIndex=0},
  add(item){this.options.push(item);if(this.options.length===1)this.value=item.value}
 });
 return els.get(id);
}
class Option{constructor(text,value){this.text=text;this.value=value}}
vm.runInNewContext(script,{document:{getElementById:el},window:globalThis,Option,console});
function check(value,label){if(!value)throw Error(label)}
let count=0;
function assert(value,label){check(value,label);count++}
const axes=['recent','training','course','pedigree','pace'];
const gradeRows=[
 ['S','S','S','S','S'],['S','S','S','S','A'],['S','S','S','A','B'],['S','A','S','B','B'],
 ['A','A','A','B','B'],['A','B','A','B','C'],['B','B','B','C','C']];
const horses=gradeRows.map((row,i)=>({
 number:i+1,name:'架空馬'+(i+1),scratched:false,
 evaluations:Object.fromEntries(axes.map((a,j)=>[a,{grade:row[j],note:'架空の単体テスト用根拠情報'}]))
}));
const tomorrowJst=new Date(Date.now()+24*60*60*1000).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
const bundle={kind:'keiba-nine-racecards',schema:1,source:'架空の提供元',licenseConfirmed:true,
 racecards:[{date:tomorrowJst,track:'京都',race:1,horses}]};
const ref={kind:'keiba-nine-racecard-reference',schema:1,source:'別入力（架空）',
 checkedAt:new Date().toISOString(),
 races:[{date:tomorrowJst,track:'京都',race:1,complete:true,
 horses:horses.map(h=>({number:h.number,name:h.name,scratched:false}))}]};
const clone=x=>JSON.parse(JSON.stringify(x));
el('raw').value=JSON.stringify(bundle);
el('analyze').events.click();
assert(el('savePreview').disabled===false,'unreferenced test preview remains possible');
assert(el('sendDraft').disabled===false,'unreferenced test handoff remains possible');
el('referenceRaw').value=JSON.stringify(ref);
el('referenceRaw').events.input();
assert(el('savePreview').disabled===true,'editing reference invalidates prior verification');
el('compareReference').events.click();
assert(el('savePreview').disabled===false,'matched references enable preview');
assert(el('referenceStatus').textContent.includes('一致'),'matched summary visible');
const modified=clone(ref);modified.races[0].horses[0].name='まったく違う馬';
el('referenceRaw').value=JSON.stringify(modified);
el('referenceRaw').events.input();
el('compareReference').events.click();
assert(el('savePreview').disabled===true&&el('sendDraft').disabled===true,'mismatch blocks export and handoff');
assert(el('referenceResult').textContent.includes('馬名が不一致'),'mismatch reason displayed');
el('savePreview').events.click(); // Event handler must fail closed, even if called directly.
assert(el('status').textContent.includes('JSONを保存できません'),'export handler rechecks mismatch');
const scratched=clone(ref);scratched.races[0].horses[0].scratched=true;
el('referenceRaw').value=JSON.stringify(scratched);
el('compareReference').events.click();
assert(el('sendDraft').disabled===true,'scratch mismatch blocks handoff');
el('referenceRaw').value='{bad';
el('compareReference').events.click();
assert(el('sendDraft').disabled===true,'bad JSON blocks handoff');
el('referenceRaw').value=JSON.stringify(ref);
el('compareReference').events.click();
assert(el('sendDraft').disabled===false,'corrected reference restores test preview');
const expired=clone(ref);
expired.checkedAt=new Date(Date.now()-96*60*60*1000).toISOString();
el('referenceRaw').value=JSON.stringify(expired);
el('compareReference').events.click();
assert(el('savePreview').disabled===true&&el('sendDraft').disabled===true,'stale reference blocks both actions');
assert(el('referenceResult').textContent.includes('72時間'),'stale timestamp warning displayed');
const future=clone(ref);
future.checkedAt=new Date(Date.now()+2*60*60*1000).toISOString();
el('referenceRaw').value=JSON.stringify(future);
el('compareReference').events.click();
assert(el('savePreview').disabled===true&&el('sendDraft').disabled===true,'future timestamp blocks preview');
assert(el('referenceResult').textContent.includes('未来'),'future timestamp warning displayed');
el('referenceRaw').value=JSON.stringify(ref);
el('compareReference').events.click();
assert(el('sendDraft').disabled===false,'rechecked recent timestamp restores draft handoff');
console.log('Racecard reference UI gating: '+count+' checks passed');
