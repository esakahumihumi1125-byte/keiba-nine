/* Offline iPhone manual 3連単 notebook: browser data only, no provider. */
'use strict';
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-private-manual-tickets.js','utf8');
const storage=new Map(),writes=[];
const localStorage={
 getItem:k=>storage.get(k)||null,
 setItem(k,v){writes.push(k);storage.set(k,v)}
};
function boot(){
 const nodes=new Map();
 function element(tag='div'){
  return {tag,value:'',textContent:'',className:'',disabled:false,children:[],
   dataset:{},onchange:null,onclick:null,href:'',download:'',type:'',
   setAttribute(k,v){this[k]=v;},
   append(...items){this.children.push(...items)},
   replaceChildren(...items){this.children=[...items]},
   click(){this.clicked=true}
  };
 }
 function el(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);}
 const urls=[];
 const URL={createObjectURL(x){urls.push(x);return 'blob:synthetic'},revokeObjectURL(x){urls.push(x)}};
 vm.runInNewContext(js,{document:{getElementById:el,createElement:element},
  localStorage,Date,Set,Number,String,JSON,Blob,URL,confirm:()=>true,console});
 return {el,nodes,urls};
}
const first=boot(),$=first.el;
assert.equal($('mFirst').children.length,18);
assert.equal($('mSecond').children.length,18);
assert.equal($('mThird').children.length,18);
assert.equal($('mSave').disabled,true);
assert.equal(storage.size,0);
$('mDate').value='2026-11-07';$('mDate').onchange();
$('mTrack').value='東京';$('mTrack').onchange();
$('mRace').value='1';$('mRace').onchange();
const choose=(id,n)=>$(id).children[n-1].onclick();
choose('mFirst',1);choose('mFirst',2);
for(let i=1;i<=4;i++)choose('mSecond',i);
for(let i=1;i<=8;i++)choose('mThird',i);
assert.equal($('mCount').textContent,'36点','overlapping positions must not be purchased twice');
assert.equal($('mCost').textContent,'3,600円');
assert.equal($('mSave').disabled,false);
assert.equal($('mTickets').children.length,36);
assert.ok($('mTickets').children.every(x=>{
 const n=x.textContent.split('-');return new Set(n).size===3;
}));
$('mSave').onclick();
assert.match($('mMsg').textContent,/下書きを保存/);
const key='keiba-nine-owner-ticket-drafts-v1';
let records=JSON.parse(storage.get(key));
assert.equal(records.length,1);assert.equal(records[0].date,'2026-11-07');
assert.deepEqual(Array.from(records[0].first),[1,2]);
assert.equal(records[0].purchased,undefined,'must not claim actual purchases');
assert.equal($('mSaved').children.length,1);
$('mDate').value='2026-11-08';$('mDate').onchange();
assert.equal($('mSaved').children.length,1); // one "none for day" paragraph
assert.match($('mSaved').children[0].textContent,/ありません/);
assert.equal($('mCount').textContent,'0点','other day does not display prior formation');
$('mDate').value='2026-11-07';$('mDate').onchange();
assert.equal($('mSaved').children.length,1,'record returns with its day');
assert.equal($('mCount').textContent,'36点','same track and race restores draft');
$('mExport').onclick();
assert.equal(first.urls.length,2,'backup blob created and revoked');
for(let i=9;i<=18;i++)choose('mThird',i);
assert.equal($('mCount').textContent,'96点','18 numbers must create more than 48');
assert.equal($('mSave').disabled,true,'invalid oversized formation must never save');
assert.equal($('mTickets').children.length,0,'do not render huge ticket list');
assert.equal(JSON.parse(storage.get(key))[0].third.length,8,'oversized entry did not overwrite');
$('mReset').onclick();
assert.equal($('mCount').textContent,'0点');
assert.equal($('mSaved').children.length,1,'reset cannot delete a saved record');
// Exact upper limit: two first picks, five second picks, eight third picks.
choose('mFirst',1);choose('mFirst',2);
for(let n=1;n<=5;n++)choose('mSecond',n);
for(let n=1;n<=8;n++)choose('mThird',n);
assert.equal($('mCount').textContent,'48点');
assert.equal($('mCost').textContent,'4,800円');
assert.equal($('mSave').disabled,false,'48 points is valid');
choose('mThird',9);
assert.equal($('mCount').textContent,'56点');
assert.equal($('mSave').disabled,true,'56 points is invalid');
$('mReset').onclick();
const second=boot(),get=second.el;
get('mDate').value='2026-11-07';get('mDate').onchange();
get('mTrack').value='東京';get('mTrack').onchange();
get('mRace').value='1';get('mRace').onchange();
assert.equal(get('mCount').textContent,'36点','same storage restores across reload');
assert.ok(writes.length>=1);
assert.ok(!js.includes('fetch('),'must not call paid or public APIs');
assert.ok(!js.includes('innerHTML'),'only use textContent for saved local data');
console.log('Manual private 3連単 notebook: 35+ offline points, storage, date and safety checks passed');
