/* Combined owner ticket page regression, not a mocked isolated receiver. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const manual=fs.readFileSync('/tmp/keiba-private-manual-tickets.js','utf8');
const handoff=fs.readFileSync('/tmp/keiba-private-owner-handoff.js','utf8');
function boot(hash,approved=true){
 let decision=approved;
 const nodes=new Map(),changed=[],history=[];
 const data=new Map();
 function elem(tag='div'){
  return {tag,value:'',textContent:'',className:'',disabled:false,children:[],
   type:'',href:'',dataset:{},onclick:null,onchange:null,download:'',
   setAttribute(k,v){this[k]=v},
   append(...items){this.children.push(...items)},
   replaceChildren(...items){this.children=[...items]},
   click(){},
   scrollIntoView(){}
  };
 }
 function el(id){
  if(!nodes.has(id)){const n=elem();if(id==='mBulkApply')n.disabled=true;nodes.set(id,n)}
  return nodes.get(id);
 }
 const localStorage={
  getItem:k=>data.get(k)||null,
  setItem(k,v){changed.push(k);data.set(k,v)}
 };
 const win={
  location:{hash,pathname:'/my-tickets',search:''},
  history:{replaceState(...args){history.push(args[2])}},
  confirm:()=>decision
 };
 vm.runInNewContext(manual+'\n'+handoff,{
  document:{getElementById:el,createElement:elem},
  window:win,localStorage,URLSearchParams,
  Date,Set,Map,JSON,String,Number,Error,
  Blob,URL:{createObjectURL(){return 'blob:test'},revokeObjectURL(){}},
  confirm:()=>decision,console
 });
 return {el,changed,data,history,setApprove:x=>{decision=x}};
}
// Deep-link from the all-36R workbench must open the actual selected race.
const race=boot('#select=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=6');
assert.equal(race.el('mDate').value,'2099-02-17');
assert.equal(race.el('mTrack').value,'東京');
assert.equal(race.el('mRace').value,'6');
assert.equal(race.el('mCount').textContent,'0点');
assert.equal(race.changed.length,0,'race-selection must never write browser storage');
assert.deepEqual(race.history,['/my-tickets']);
assert.match(race.el('mMsg').textContent,/馬番対応は引き継いでへん/);
// Explicitly confirmed five-factor handoff populates the real editor only.
const ticket=boot('#import=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=5&'+
 'first=1&second=2%2C3%2C4%2C5%2C6%2C7&third=2%2C3%2C4%2C5%2C6%2C7');
assert.equal(ticket.el('mDate').value,'2099-02-17');
assert.equal(ticket.el('mTrack').value,'東京');
assert.equal(ticket.el('mRace').value,'5');
assert.equal(ticket.el('mCount').textContent,'30点');
assert.equal(ticket.el('mCost').textContent,'3,000円');
assert.equal(ticket.el('mSave').disabled,false);
assert.equal(ticket.changed.length,0,'handoff is not purchase/save');
assert.deepEqual(ticket.history,['/my-tickets']);
assert.match(ticket.el('mMsg').textContent,/購入記録には追加されません/);
ticket.setApprove(false);
ticket.el('mNextRace').onclick();
assert.equal(ticket.el('mRace').value,'5',
 'do not lose newly imported unsaved candidates through next-R navigation');
assert.equal(ticket.el('mCount').textContent,'30点');
assert.equal(ticket.changed.length,0,'cancelled navigation cannot write the 3連単 draft');
// User cancellation or extra payload cannot overwrite a formation.
const denied=boot('#import=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=5&'+
 'first=1&second=2&third=3',false);
assert.equal(denied.el('mCount').textContent,'0点');
assert.equal(denied.changed.length,0);
assert.deepEqual(denied.history,['/my-tickets']);
const invalid=boot('#select=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=5&secret=xyz');
assert.equal(invalid.el('mCount').textContent,'0点');
assert.equal(invalid.changed.length,0);
assert.deepEqual(invalid.history,['/my-tickets']);
assert.match(invalid.el('mMsg').textContent,/受け取れませんでした/);

for(const fragment of [
 '#select=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=01',
 '#import=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=15&first=1&second=2&third=3',
 '#import=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=5&first=1%2C1&second=2&third=3',
 '#import=v1&date=2099-02-17&track=%E6%9D%B1%E4%BA%AC&race=5&first=1&second=2&third=3&secret=unused'
]){
 const malformed=boot(fragment);
 assert.equal(malformed.el('mCount').textContent,'0点',fragment);
 assert.equal(malformed.changed.length,0,'invalid fragment cannot save anything');
 assert.deepEqual(malformed.history,['/my-tickets']);
 assert.match(malformed.el('mMsg').textContent,/受け取れませんでした/);
}
console.log('Combined private 3連単 editor + handoff: real date/race/formation navigation and no implicit save PASS');
