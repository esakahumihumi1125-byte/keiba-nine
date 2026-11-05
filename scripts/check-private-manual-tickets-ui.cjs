/* Offline iPhone manual 3連単 notebook: browser data only, no provider. */
'use strict';
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-private-manual-tickets.js','utf8');
const storage=new Map(),writes=[];
const localStorage={
 getItem:k=>storage.get(k)||null,
 setItem(k,v){writes.push(k);storage.set(k,v)}
};
function boot(confirmDecision=true){
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
 function el(id){if(!nodes.has(id)){const node=element();if(id==='mBulkApply')node.disabled=true;nodes.set(id,node);}return nodes.get(id);}
 const urls=[];
 const URL={createObjectURL(x){urls.push(x);return 'blob:synthetic'},revokeObjectURL(x){urls.push(x)}};
 vm.runInNewContext(js,{document:{getElementById:el,createElement:element},
  localStorage,Date,Set,Number,String,JSON,Blob,URL,confirm:()=>confirmDecision,console});
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
assert.equal($('mRaceBoard').children.length,0,'track must be selected before showing 12R board');
$('mDate').value='2026-11-07';$('mDate').onchange();
assert.equal($('mImport').onchange,originalImport,'date switching must not rebind the import handler');
$('mTrack').value='東京';$('mTrack').onchange();
$('mRace').value='1';$('mRace').onchange();
assert.equal($('mRaceBoard').children.length,12,'selected track shows all 12 race buttons');
assert.equal($('mRaceBoard').children[0].children[1].textContent,'未入力');
assert.match($('mRaceBoardStatus').textContent,/保存済み0R／未入力12R/);
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
assert.match($('mDaySummary').textContent,/1R／36点／3,600円/,'day totals show only unsent drafts');
assert.match($('mRaceBoardStatus').textContent,/保存済み1R／未入力11R/);
assert.equal($('mRaceBoard').children[0].children[1].textContent,'36点保存');
const beforeBoardTap=storage.get(key),beforeBoardWrites=writes.length;
$('mRaceBoard').children[1].onclick();
assert.equal($('mRace').value,'2','one-tap grid selects 2R');
assert.equal($('mCount').textContent,'0点','new unfilled race starts empty');
assert.equal($('mRaceBoard').children[1]['aria-pressed'],'true');
$('mRaceBoard').children[0].onclick();
assert.equal($('mRace').value,'1');
assert.equal($('mCount').textContent,'36点','grid reopens previously saved formation');
assert.equal(storage.get(key),beforeBoardTap,'grid navigation must not alter saved records');
assert.equal(writes.length,beforeBoardWrites,'grid navigation must not write localStorage');
$('mSaved').children[0].children[2].onclick();
assert.equal($('mCount').textContent,'36点','edit opens saved race without changing points');
assert.match($('mMsg').textContent,/下書きを表示したで/,'edit gives clear next-step feedback');
$('mDate').value='2026-11-08';$('mDate').onchange();
assert.equal($('mSaved').children.length,1); // one "none for day" paragraph
assert.match($('mSaved').children[0].textContent,/ありません/);
assert.equal($('mCount').textContent,'0点','other day does not display prior formation');
assert.match($('mDaySummary').textContent,/0R／0点／0円/,'other date must not inherit costs');
assert.match($('mRaceBoardStatus').textContent,/保存済み0R／未入力12R/);
assert.equal($('mRaceBoard').children[0].children[1].textContent,'未入力','other date cannot show old saved status');
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
assert.match(m('mRaceBoardStatus').textContent,/JRDB想定メール 1R／本人の馬名一致メモ 1R/);
assert.equal(m('mRaceBoard').children[1].children[2].textContent,'馬名一致メモ','matched mail/typed horses are marked only as owner memo');
assert.equal(m('mRaceBoard').children[0].children[2].textContent,'出走資料未取込');
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
assert.match(m('mRaceBoardStatus').textContent,/JRDB想定メール 1R／本人の馬名一致メモ 0R/,'changed mail invalidates old memo coverage');
assert.equal(m('mRaceBoard').children[1].children[2].textContent,'想定メールあり');
m('mFirst').children[0].onclick();
assert.equal(m('mFirstNames').textContent,'選択中：1番','stale name must not appear on selected horse');

assert.equal(writes.length,beforeMemoWrites,'read-only memo viewing must never write localStorage');

// Saturday 2026-11-07: batch-copy multiple already-authored formations.
// Preview and rejected input never write drafts/purchases, and save is atomic.
const batch=boot(),b=batch.el;
assert.equal(typeof b('mBulkReview').onclick,'function');
assert.equal(b('mBulkApply').disabled,true);
const batchInput='2026-11-07 東京1R\n1着：①②\n2着：①②③④\n3着：①②③④⑤⑥⑦⑧\n\n2026-11-07 京都1R\n1着：①\n2着：②③\n3着：②③④';
b('mBulkPaste').value=batchInput;
const beforeBatch=storage.get(key),writesBeforeBatch=writes.length;
b('mBulkReview').onclick();
assert.equal(b('mBulkPreview').children.length,2,'two races preview separately');
assert.match(b('mBulkPreview').children[0].children[0].textContent,/東京1R：36点/);
assert.match(b('mBulkPreview').children[0].children[0].textContent,/既存を上書き/);
assert.match(b('mBulkPreview').children[1].children[0].textContent,/京都1R：4点/);
assert.match(b('mBulkPreview').children[0].children[1].textContent,/1着 1・2／2着 1・2・3・4/);
const previewTickets=b('mBulkPreview').children[0].children[2].textContent.split('：')[1].split(' ／ ');
assert.equal(previewTickets.length,36,'preview must show the full 36 actual tickets');
assert.equal(new Set(previewTickets).size,36,'preview tickets should all be unique');
assert.ok(previewTickets.every(x=>new Set(x.split('-')).size===3),'no ticket repeats a horse');
assert.equal(b('mBulkApply').disabled,false);
assert.equal(storage.get(key),beforeBatch,'preview never saves anything');
assert.equal(writes.length,writesBeforeBatch);
b('mBulkApply').onclick();
let afterBatch=JSON.parse(storage.get(key));
assert.equal(afterBatch.some(r=>r.date==='2026-11-07'&&r.track==='京都'&&r.race===1),true);
assert.equal(afterBatch.filter(r=>r.date==='2026-11-07'&&r.track==='東京'&&r.race===1).length,1,
 'reimport updates the same race instead of duplicating it');
assert.equal(b('mBulkPaste').value,'','successful batch clears textarea');
assert.match(b('mBulkStatus').textContent,/2レースの下書き/);
b('mDate').value='2026-11-07';b('mDate').onchange();
assert.match(b('mDaySummary').textContent,/2R／40点／4,000円/,'batch summaries must count both races without duplicates');
assert.equal(b('mBulkApply').disabled,true);
const locked=storage.get(key),writesBeforeErrors=writes.length;
for(const bad of [
 '2026-11-07 東京1R\n1着：①\n2着：②\n3着：③\n余計な行',
 '2026-11-07 東京1R\n1着：①\n2着：②\n3着：③\n\n2026-11-07 東京1R\n1着：①\n2着：②\n3着：③',
 '2026-11-31 東京1R\n1着：①\n2着：②\n3着：③',
 '2026-11-07 東京1R\n1着：①②\n2着：①②③④⑤\n3着：①②③④⑤⑥⑦⑧⑨',
]){
 b('mBulkPaste').value=bad;b('mBulkReview').onclick();
 assert.equal(b('mBulkApply').disabled,true,'bad batch cannot save');
 assert.match(b('mBulkStatus').textContent,/一括検査できません/);
}
assert.equal(storage.get(key),locked);
assert.equal(writes.length,writesBeforeErrors,'invalid batch does not touch storage');
const canceled=boot(false),c=canceled.el;
c('mBulkPaste').value='2026-11-08 京都2R\n1着：①\n2着：②\n3着：③';
c('mBulkReview').onclick();
const beforeCancel=storage.get(key);
c('mBulkApply').onclick();
assert.equal(storage.get(key),beforeCancel,'cancel rejects batch without writes');
c('mBulkPaste').value=batchInput;c('mBulkReview').onclick();
c('mBulkPaste').value=batchInput+'\n';
c('mBulkApply').onclick();
assert.equal(storage.get(key),beforeCancel,'changed input needs a fresh preview');
assert.equal(c('mBulkApply').disabled,true);
assert.ok(!js.includes('fetch('),'batch import must not upload to any API');

// Weekend shortcuts use local Japan calendar dates, without writing drafts.
const weekend=boot(),w=weekend.el,writeCount=writes.length,existingBackup=storage.get(key);
w('mSaturday').onclick();
assert.equal(new Date(w('mDate').value+'T12:00:00Z').getUTCDay(),6,'Saturday jump chooses a Saturday');
const saturday=w('mDate').value;
w('mSunday').onclick();
assert.equal(new Date(w('mDate').value+'T12:00:00Z').getUTCDay(),0,'Sunday jump chooses a Sunday');
assert.notEqual(w('mDate').value,saturday,'Saturday and Sunday are different race dates');
assert.equal(storage.get(key),existingBackup,'date navigation does not edit saved drafts');
assert.equal(writes.length,writeCount,'date navigation has no storage writes');
const malformedCoverage=boot(),bad=malformedCoverage.el;
storage.set('keiba-nine-jrdb-personal-mail-v1','not valid JSON');
bad('mDate').value='2026-11-07';bad('mDate').onchange();
bad('mTrack').value='東京';bad('mTrack').onchange();
assert.match(bad('mRaceBoardStatus').textContent,/JRDB想定メール 0R/,'broken mail cannot appear as checked coverage');
storage.set('keiba-nine-jrdb-personal-mail-v1',JSON.stringify([{...memoMeeting,races:[
  {race:2,postTime:'10:30',expected:3,horses:['架空馬A','架空馬B','架空馬C']}]}]));
storage.set('keiba-nine-owner-manual-numbers-v1',JSON.stringify([memoRecord]));
const partial=boot(),part=partial.el;
part('mDate').value='2026-11-07';part('mDate').onchange();
part('mTrack').value='東京';part('mTrack').onchange();
assert.match(part('mRaceBoardStatus').textContent,/本人の馬名一致メモ 1R/);
storage.set('keiba-nine-owner-manual-numbers-v1',JSON.stringify([{...memoRecord,rows:[
 {number:1,name:'架空馬A'},{number:1,name:'架空馬B'},{number:2,name:'架空馬C'}]}]));
part('mTrack').onchange();
assert.match(part('mRaceBoardStatus').textContent,/本人の馬名一致メモ 0R/,'duplicated horse number is not a matched memo');
assert.ok(!js.includes('fetch('),'local JRDB readiness board does not send mail data to a server');

console.log('Manual private 3連単 notebook: 35+ offline points, storage, date and safety checks passed');
