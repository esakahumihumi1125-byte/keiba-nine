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
assert.equal(typeof $('mImport').onchange,'function','JSON restore must be available immediately on first load');
const originalImport=$('mImport').onchange;
assert.equal($('mFirst').children.length,18);
assert.equal($('mSecond').children.length,18);
assert.equal($('mThird').children.length,18);
assert.equal($('mSave').disabled,true);
assert.equal(storage.size,0);
$('mDate').value='2026-11-07';$('mDate').onchange();
assert.equal($('mImport').onchange,originalImport,'date switching must not rebind the import handler');
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
// Quick actions are manual formation helpers; they never save automatically.
const quick=boot(),q=quick.el;
const pick=(id,n)=>q(id).children[n-1].onclick();
q('mDate').value='2026-11-09';q('mDate').onchange();
q('mTrack').value='京都';q('mTrack').onchange();
assert.equal(q('mPrevRace').disabled,true,'1R has no previous race');
q('mNextRace').onclick();
assert.equal(q('mRace').value,'2','next race moves without free text');
assert.equal(q('mPrevRace').disabled,false);
q('mPrevRace').onclick();
assert.equal(q('mRace').value,'1');
q('mRace').value='12';q('mRace').onchange();
assert.equal(q('mNextRace').disabled,true);
q('mNextRace').onclick();
assert.equal(q('mRace').value,'12','12R is the last race');
q('mRace').value='1';q('mRace').onchange();
q('mAxisSingle').onclick();
assert.match(q('mMsg').textContent,/1着候補を1頭/);
pick('mFirst',1);
for(let n=2;n<=7;n++)pick('mSecond',n);
q('mAxisSingle').onclick();
assert.equal(q('mCount').textContent,'30点','one-head 6 partners makes 30 distinct picks');
assert.equal(q('mCost').textContent,'3,000円');
assert.equal(q('mSave').disabled,false);
assert.equal(q('mThird').children.filter(n=>n.className.includes('selected')).length,6);
q('mReset').onclick();
pick('mFirst',1);pick('mFirst',2);
for(let n=3;n<=8;n++)pick('mThird',n);
q('mAxisPair').onclick();
assert.equal(q('mCount').textContent,'12点','two heads can finish first and second in either order');
assert.equal(q('mSecond').children.filter(n=>n.className.includes('selected')).length,2);
assert.equal(q('mTickets').children.length,12);
q('mReset').onclick();
pick('mFirst',1);
for(let n=2;n<=4;n++)pick('mSecond',n);
q('mCopyThird').onclick();
assert.equal(q('mCount').textContent,'6点','copy 2nd to 3rd without duplicate horse per ticket');
q('mReset').onclick();
pick('mFirst',1);
for(let n=2;n<=11;n++)pick('mSecond',n);
q('mAxisSingle').onclick();
assert.equal(q('mCount').textContent,'0点','quick helper refuses more than 48');
assert.match(q('mMsg').textContent,/48点/);
assert.equal(q('mSave').disabled,true,'quick action cannot bypass point cap');
assert.equal(storage.get('keiba-nine-owner-ticket-drafts-v1')!==null,true,
 'existing saved draft is preserved');
const second=boot(),get=second.el;
get('mDate').value='2026-11-07';get('mDate').onchange();
get('mTrack').value='東京';get('mTrack').onchange();
get('mRace').value='1';get('mRace').onchange();
assert.equal(get('mCount').textContent,'36点','same storage restores across reload');
assert.ok(writes.length>=1);
assert.ok(!js.includes('fetch('),'must not call paid or public APIs');
assert.ok(!js.includes('innerHTML'),'only use textContent for saved local data');
console.log('Manual private 3連単 notebook: 35+ offline points, storage, date and safety checks passed');
