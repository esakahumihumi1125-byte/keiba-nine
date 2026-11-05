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
q('mRace').value='1';q('mRace').onchange(); // DOM mock has no HTML select default
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
// Pasting a ChatGPT-style formation changes only unsaved picks, never storage.
const paste=boot(),p=paste.el;
assert.equal(typeof p('mApplyPaste').onclick,'function');
p('mPaste').value='1着：①②\n2着：①②③④\n3着：①②③④⑤⑥⑦⑧';
const savedBeforePaste=storage.get('keiba-nine-owner-ticket-drafts-v1');
p('mApplyPaste').onclick();
assert.match(p('mMsg').textContent,/日付・競馬場・レース/,'required race coordinate');
assert.equal(p('mCount').textContent,'0点');
p('mDate').value='2026-11-08';p('mDate').onchange();
p('mTrack').value='東京';p('mTrack').onchange();
p('mRace').value='1';p('mRace').onchange();
p('mApplyPaste').onclick();
assert.equal(p('mCount').textContent,'36点','circled digits may be adjacent');
assert.equal(p('mCost').textContent,'3,600円');
assert.equal(p('mSave').disabled,false);
assert.match(p('mMsg').textContent,/まだ保存・購入はしていません/);
assert.deepEqual(p('mFirst').children.filter(n=>n.className.includes('selected')).map(x=>Number(x.textContent)),[1,2]);
assert.equal(storage.get('keiba-nine-owner-ticket-drafts-v1'),savedBeforePaste,
 'Importing a formation must never save or overwrite the notebook');
p('mPaste').value='1着：1,2\n2着：1,2,3,4,5\n3着：1,2,3,4,5,6,7,8,9';
p('mApplyPaste').onclick();
assert.match(p('mMsg').textContent,/48点を超え/);
assert.equal(p('mCount').textContent,'36点','Oversized paste never replaces the previous selection');
for(const bad of [
 '1着：①①\n2着：②③\n3着：④⑤',
 '1着：①\n1着：②\n3着：③',
 '1着：1,2\n2着：2,3\n3着：0,4',
 '1着：1,2\n2着：2,3\n3着：4,5\nオッズ 3.2',
 '1着：12\n2着：12\n3着：12',
 '1着：㉑\n2着：2\n3着：3',
]){
 p('mPaste').value=bad;p('mApplyPaste').onclick();
 assert.match(p('mMsg').textContent,/反映できません/);
 assert.equal(p('mCount').textContent,'36点','Invalid paste must not alter picks');
}
p('mPaste').value='１着候補：１、２\n２着：１・２・３・４\n３着：１・２・３・４・５・６・７・８';
p('mApplyPaste').onclick();
assert.equal(p('mCount').textContent,'36点','Full-width numbers and Japanese delimiters work');
assert.equal(storage.get('keiba-nine-owner-ticket-drafts-v1'),savedBeforePaste);
const second=boot(),get=second.el;
get('mDate').value='2026-11-07';get('mDate').onchange();
get('mTrack').value='東京';get('mTrack').onchange();
get('mRace').value='1';get('mRace').onchange();
assert.equal(get('mCount').textContent,'36点','same storage restores across reload');
assert.ok(writes.length>=1);
assert.ok(!js.includes('fetch('),'must not call paid or public APIs');
assert.ok(!js.includes('innerHTML'),'only use textContent for saved local data');

// Read-only link to the manual, SAME-ORIGIN horse-number memo.
const memoMeeting={kind:'jrdb-provisional',date:'2026-11-07',track:'東京',
 races:[{race:2,postTime:'10:30',expected:3,horses:['架空馬A','架空馬B','架空馬C']}]};
const memoRecord={date:'2026-11-07',track:'東京',race:2,
 sourceMark:JSON.stringify(['10:30',3,['架空馬A','架空馬B','架空馬C']]),
 rows:[{number:3,name:'架空馬C'},{number:1,name:'架空馬A'},{number:2,name:'架空馬B'}]};
storage.set('keiba-nine-jrdb-personal-mail-v1',JSON.stringify([memoMeeting]));
storage.set('keiba-nine-owner-manual-numbers-v1',JSON.stringify([memoRecord]));
const memoPage=boot(),m=memoPage.el;
m('mDate').value='2026-11-07';m('mDate').onchange();
m('mTrack').value='東京';m('mTrack').onchange();
m('mRace').value='2';m('mRace').onchange();
assert.equal(m('mRosterRows').children.length,3,'same-race memo should show three names');
assert.equal(m('mRosterRows').children[0].textContent,'1番 架空馬A','memo sorted by horse number');
assert.match(m('mRosterStatus').textContent,/本人が手入力/);
assert.equal(m('mCount').textContent,'0点','memo must not auto-create a formation');
assert.equal(m('mFirstNames').textContent,'','no selection should not show labels');
m('mFirst').children[0].onclick();
assert.match(m('mFirstNames').textContent,/1番 架空馬A/,'chosen horse shows mapped name');
assert.equal(m('mSecondNames').textContent,'','only a chosen position gets a label');
m('mSecond').children[1].onclick();
m('mThird').children[2].onclick();
assert.equal(m('mCount').textContent,'1点','read-only names do not change formation math');
assert.match(m('mThirdNames').textContent,/3番 架空馬C/);

const beforeMemoWrites=writes.length;
m('mRace').value='3';m('mRace').onchange();
assert.equal(m('mRosterRows').children.length,0,'other race must not inherit names');
m('mRace').value='2';m('mRace').onchange();
storage.set('keiba-nine-jrdb-personal-mail-v1',
 JSON.stringify([{...memoMeeting,races:[{...memoMeeting.races[0],horses:['別の馬A','架空馬B','架空馬C']}]}]));
m('mRace').onchange();
assert.equal(m('mRosterRows').children.length,0,'changed source cannot display stale names');
assert.match(m('mRosterStatus').textContent,/再照合/);
m('mFirst').children[0].onclick();
assert.equal(m('mFirstNames').textContent,'選択中：1番','stale name must not appear on selected horse');

assert.equal(writes.length,beforeMemoWrites,'read-only memo viewing must never write localStorage');
console.log('Manual private 3連単 notebook: 35+ offline points, storage, date and safety checks passed');
