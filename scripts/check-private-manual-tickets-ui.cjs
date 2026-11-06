/* Offline iPhone manual 3連単 notebook: browser data only, no provider. */
'use strict';
const fs=require('node:fs'), vm=require('node:vm'), assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-private-manual-tickets.js','utf8');
const storage=new Map(),writes=[];
const localStorage={
 getItem:k=>storage.get(k)||null,
 setItem(k,v){writes.push(k);storage.set(k,v)}
};
function boot(confirmDecision=true,hash='',handoff=null){
 const nodes=new Map();
 const transientKey='keiba-nine-scorecard-bulk-transfer-v1';
 const transient=new Map(handoff?[[transientKey,JSON.stringify(handoff)]]:[]);
 const transientWrites=[];
 const sessionStorage={getItem:k=>transient.get(k)||null,setItem:(k,v)=>{transientWrites.push(k);transient.set(k,v)},removeItem:k=>transient.delete(k)};
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
 const urls=[],navigation=[];let reply='1-2-3';
 const URL={createObjectURL(x){urls.push(x);return 'blob:synthetic'},revokeObjectURL(x){urls.push(x)}};
 vm.runInNewContext(js,{document:{getElementById:el,createElement:element},
  localStorage,sessionStorage,Date,Set,Number,String,JSON,Blob,URL,URLSearchParams,
  window:{location:{assign:u=>navigation.push(u),hash,pathname:'/my-tickets',search:''},
          history:{replaceState:()=>{}}},confirm:msg=>typeof confirmDecision==='function'?confirmDecision(msg):confirmDecision,prompt:()=>reply,console});
 return {el,nodes,urls,navigation,transient,transientWrites,setPrompt:s=>{reply=s}};
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
assert.match($('mNumberReview').textContent,/馬番メモが未登録/,'unmapped picks need official entry check');
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
assert.match(m('mNumberReview').textContent,/選択した馬番は本人転記の馬番メモにあります/,'matched owner memo is informational only');
m('mFirst').children[3].onclick();
assert.match(m('mNumberReview').textContent,/4番.*未登録/,'unknown selected number is highlighted');
m('mFirst').children[3].onclick();

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
assert.match(m('mNumberReview').textContent,/馬番メモが未登録または更新/,'stale source requires recheck');
m('mSecond').children[1].onclick();m('mThird').children[2].onclick();
assert.equal(m('mCount').textContent,'1点');
assert.equal(m('mSave').disabled,false,'source warnings do not silently block explicit operator draft');

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
const pendingDate=boot(false),pd=pendingDate.el;
pd('mDate').value='2026-11-05';pd('mDate').onchange();
pd('mTrack').value='京都';pd('mTrack').onchange();
pd('mRace').value='1';pd('mRace').onchange();
pd('mFirst').children[0].onclick();
pd('mSecond').children[1].onclick();
pd('mThird').children[2].onclick();
assert.equal(pd('mCount').textContent,'1点');
const beforeBlocked=storage.get(key),blockedWriteCount=writes.length;
pd('mSaturday').onclick();
assert.equal(pd('mDate').value,'2026-11-05','declining date change protects unsaved picks');
assert.equal(pd('mCount').textContent,'1点','declining date change preserves current formation');
assert.match(pd('mMsg').textContent,/日付を変えずに保持/);
assert.equal(storage.get(key),beforeBlocked);
assert.equal(writes.length,blockedWriteCount,'blocked quick jump never writes');
const malformedCoverage=boot(),bad=malformedCoverage.el;
storage.set('keiba-nine-jrdb-personal-mail-v1','not valid JSON');
bad('mDate').value='2026-11-07';bad('mDate').onchange();
bad('mTrack').value='東京';bad('mTrack').onchange();
bad('mRace').value='2';bad('mRace').onchange();
assert.match(bad('mRaceBoardStatus').textContent,/JRDB想定メール 0R/,'broken mail cannot appear as checked coverage');
storage.set('keiba-nine-jrdb-personal-mail-v1',JSON.stringify([{...memoMeeting,races:[
  {race:2,postTime:'10:30',expected:3,horses:['架空馬A','架空馬B','架空馬C']}]}]));
storage.set('keiba-nine-owner-manual-numbers-v1',JSON.stringify([memoRecord]));
const partial=boot(),part=partial.el;
part('mDate').value='2026-11-07';part('mDate').onchange();
part('mTrack').value='東京';part('mTrack').onchange();
part('mRace').value='2';part('mRace').onchange();
assert.match(part('mRaceBoardStatus').textContent,/本人の馬名一致メモ 1R/);
storage.set('keiba-nine-owner-manual-numbers-v1',JSON.stringify([{...memoRecord,rows:[
 {number:1,name:'架空馬A'},{number:1,name:'架空馬B'},{number:2,name:'架空馬C'}]}]));
part('mTrack').onchange();
assert.match(part('mRaceBoardStatus').textContent,/本人の馬名一致メモ 0R/,'duplicated horse number is not a matched memo');
assert.ok(!js.includes('fetch('),'local JRDB readiness board does not send mail data to a server');


// Date-wide readiness: only meetings actually present in local mail/drafts appear.
storage.set('keiba-nine-jrdb-personal-mail-v1',JSON.stringify([
 memoMeeting,
 {kind:'jrdb-provisional',date:'2026-11-07',track:'京都',races:[
  {race:1,postTime:'10:05',expected:3,horses:['架空京都A','架空京都B','架空京都C']}]},
 {kind:'jrdb-provisional',date:'2026-11-07',track:'福島',races:[
  {race:1,postTime:'09:45',expected:3,horses:['架空福島A','架空福島B','架空福島C']}]}
]));
storage.set('keiba-nine-owner-manual-numbers-v1',JSON.stringify([memoRecord]));
const daywide=boot(),dw=daywide.el;
dw('mDate').value='2026-11-07';dw('mDate').onchange();
assert.equal(dw('mDayCoverage').children.length,3,'only 3 connected venues for that date');
assert.match(dw('mDayCoverageSummary').textContent,/端末内3場／想定メール3R／馬名一致メモ1R／下書き2R・40点/);
assert.match(dw('mDayCoverageSummary').textContent,/4,000円.*未購入/);
assert.equal(dw('mDayCoverage').children[0].children[0].textContent,'福島');
assert.equal(dw('mDayCoverage').children[1].children[0].textContent,'東京');
assert.equal(dw('mDayCoverage').children[2].children[0].textContent,'京都');
const beforeVenueTap=storage.get(key),beforeVenueWrites=writes.length;
dw('mDayCoverage').children[0].onclick();
assert.equal(dw('mTrack').value,'福島','one tap opens first venue');
assert.match(dw('mRaceBoardStatus').textContent,/JRDB想定メール 1R/);
dw('mDayCoverage').children[2].onclick();
assert.equal(dw('mTrack').value,'京都','one tap switches to existing saved venue');
assert.equal(dw('mCount').textContent,'4点','venue tap reloads only saved formation');
assert.equal(storage.get(key),beforeVenueTap,'venue navigation never overwrites drafts');
assert.equal(writes.length,beforeVenueWrites,'venue readiness navigation is read-only');
dw('mDate').value='2026-11-09';dw('mDate').onchange();
assert.equal(dw('mDayCoverage').children.length,0,'next date must not inherit any venue');
assert.match(dw('mDayCoverageSummary').textContent,/まだありません/);
const dayCanceled=boot(false),dc=dayCanceled.el;
dc('mDate').value='2026-11-07';dc('mDate').onchange();
dc('mTrack').value='京都';dc('mTrack').onchange();
dc('mRace').value='1';dc('mRace').onchange();
dc('mFirst').children[3].onclick();
const dirtyPoints=dc('mCount').textContent;
dc('mDayCoverage').children[1].onclick();
assert.equal(dc('mTrack').value,'京都','unsaved changes block venue-switch');
assert.equal(dc('mCount').textContent,dirtyPoints);
assert.match(dc('mMsg').textContent,/切替をやめました/);
const beforeStale=storage.get(key),staleWrites=writes.length;
storage.set('keiba-nine-jrdb-personal-mail-v1',JSON.stringify([
 {...memoMeeting,races:[{...memoMeeting.races[0],horses:['別の馬A','架空馬B','架空馬C']}]}
]));
dc('mDate').onchange();
assert.match(dc('mDayCoverageSummary').textContent,/馬名一致メモ0R/,'changed mail invalidates aggregate memo count');
assert.equal(storage.get(key),beforeStale,'read-only coverage did not mutate draft data');
assert.equal(writes.length,staleWrites,'mail coverage views never write draft or purchase data');
assert.ok(!js.includes('fetch('),'aggregate cannot transmit licensed member data');


// Rank helper: user-supplied S/A/B is only an operator formation tool, not a prediction.
const rankPage=boot(),rank=rankPage.el;
rank('mDate').value='2026-11-14';rank('mDate').onchange();
rank('mTrack').value='福島';rank('mTrack').onchange();
rank('mRace').value='8';rank('mRace').onchange();
rank('mRankS').value='①②';
rank('mRankA').value='③④';
rank('mRankB').value='⑤⑥⑦⑧';
const beforeRanks=storage.get(key),beforeRankWrites=writes.length;
rank('mRankBuild').onclick();
assert.equal(rank('mCount').textContent,'36点','2 S + 2 A + 4 B should build 36 tickets');
assert.match(rank('mRankStatus').textContent,/30〜40点の目安内/);
assert.equal(rank('mCost').textContent,'3,600円');
assert.equal(rank('mTickets').children.length,36,'all generated combinations are reviewable');
assert.equal(new Set(rank('mTickets').children.map(x=>x.textContent)).size,36);
assert.equal(rank('mSave').disabled,false,'user may save generated selection explicitly');
assert.equal(storage.get(key),beforeRanks,'rank helper never persists drafts');
assert.equal(writes.length,beforeRankWrites,'rank helper never writes purchase/draft data');
const good36=rank('mTickets').children.map(x=>x.textContent).join(',');
for(const invalid of [
 {s:'①②③',a:'④',b:'⑤'},
 {s:'①②',a:'②③',b:'④'},
 {s:'①',a:'A',b:'③'},
 {s:'⑲',a:'②',b:'③'},
 {s:'①',a:'②',b:''}
]){
 rank('mRankS').value=invalid.s;rank('mRankA').value=invalid.a;rank('mRankB').value=invalid.b;
 rank('mRankBuild').onclick();
 assert.match(rank('mRankStatus').textContent,/編成できません/,'bad input rejected');
 assert.equal(rank('mTickets').children.map(x=>x.textContent).join(','),good36,'failed rank helper keeps previous selections');
}
rank('mRankS').value='①';rank('mRankA').value='②';rank('mRankB').value='③';
rank('mRankBuild').onclick();
assert.equal(rank('mCount').textContent,'1点','small inputs do not inflate to 30-40');
assert.match(rank('mRankStatus').textContent,/30〜40点には届かない/);
assert.equal(storage.get(key),beforeRanks);
const cancelledRanks=boot(false),cr=cancelledRanks.el;
cr('mDate').value='2026-11-14';cr('mDate').onchange();
cr('mTrack').value='福島';cr('mTrack').onchange();
cr('mRace').value='9';cr('mRace').onchange();
cr('mFirst').children[0].onclick();cr('mSecond').children[1].onclick();cr('mThird').children[2].onclick();
cr('mRankS').value='④⑤';cr('mRankA').value='⑥⑦';cr('mRankB').value='⑧⑨⑩⑪';
cr('mRankBuild').onclick();
assert.equal(cr('mCount').textContent,'1点','cancel keeps already edited formation');
assert.equal(storage.get(key),beforeRanks,'cancel does not persist');
assert.ok(!js.includes('fetch('),'rank helper performs no remote analyses or transfers');


// Unsaved operator selections must be protected on every navigation surface.
const guarded=boot(false),g=guarded.el;
g('mDate').value='2026-11-14';g('mDate').onchange();
g('mTrack').value='福島';g('mTrack').onchange();
g('mRace').value='1';g('mRace').onchange();
g('mFirst').children[0].onclick();
g('mSecond').children[1].onclick();
g('mThird').children[2].onclick();
assert.equal(g('mCount').textContent,'1点');
const beforeGuard=storage.get(key),beforeGuardWrites=writes.length;
g('mNextRace').onclick();
assert.equal(g('mRace').value,'1','next-R button blocked when unsaved');
g('mRaceBoard').children[1].onclick();
assert.equal(g('mRace').value,'1','12R grid blocked when unsaved');
g('mRace').value='3';g('mRace').onchange();
assert.equal(g('mRace').value,'1','direct race dropdown restored after cancel');
g('mTrack').value='東京';g('mTrack').onchange();
assert.equal(g('mTrack').value,'福島','track dropdown restored after cancel');
g('mDate').value='2026-11-15';g('mDate').onchange();
assert.equal(g('mDate').value,'2026-11-14','date picker restored after cancel');
assert.match(g('mMsg').textContent,/切り替えをやめました/);
g('mDate').onchange();
assert.equal(g('mCount').textContent,'1点','same date re-check cannot discard unsaved input');
assert.equal(storage.get(key),beforeGuard,'navigation cannot save a ticket');
assert.equal(writes.length,beforeGuardWrites,'navigation never mutates localStorage');
const approved=boot(true),ap=approved.el;
ap('mDate').value='2026-11-14';ap('mDate').onchange();
ap('mTrack').value='福島';ap('mTrack').onchange();
ap('mRace').value='1';ap('mRace').onchange();
ap('mFirst').children[0].onclick();ap('mSecond').children[1].onclick();ap('mThird').children[2].onclick();
ap('mNextRace').onclick();
assert.equal(ap('mRace').value,'2','explicitly approved navigation is allowed');
assert.equal(ap('mCount').textContent,'0点','new unsaved race starts empty');


// Date/track/R-only handoff into manual scorecard, never leaks members or selections.
const jumpPage=boot(true),jp=jumpPage.el;
jp('mDate').value='2026-11-07';jp('mDate').onchange();
jp('mTrack').value='東京';jp('mTrack').onchange();
jp('mRace').value='7';jp('mRace').onchange();
const beforeJump=storage.get(key),jumpWrites=writes.length;
jp('mScorecardOpen').onclick();
assert.equal(jumpPage.navigation.length,1);
assert.ok(jumpPage.navigation[0].startsWith('/my-scorecard#select=v1&'));
const options=new URLSearchParams(jumpPage.navigation[0].split('#')[1]);
assert.equal(options.get('date'),'2026-11-07');
assert.equal(options.get('track'),'東京');
assert.equal(options.get('race'),'7');
assert.equal(options.size,4,'no horse numbers, grades or licensed email in route');
assert.equal(storage.get(key),beforeJump);
assert.equal(writes.length,jumpWrites);
const stopPage=boot(false),sp=stopPage.el;
sp('mDate').value='2026-11-07';sp('mDate').onchange();
sp('mTrack').value='東京';sp('mTrack').onchange();
sp('mRace').value='7';sp('mRace').onchange();
sp('mFirst').children[0].onclick();
sp('mSecond').children[1].onclick();
sp('mThird').children[2].onclick();
sp('mScorecardOpen').onclick();
assert.equal(stopPage.navigation.length,0,'unsaved 3連単 must not be lost via scorecard jump');
assert.equal(sp('mCount').textContent,'1点');


// Owner-entered factor grades appear on the same day's all-R board, without being
// misrepresented as AI predictions or official runner verification.
const scoreKey='keiba-nine-owner-factor-notes-v1';
const mailKey='keiba-nine-jrdb-personal-mail-v1';
const memoKey='keiba-nine-owner-manual-numbers-v1';
const dateScore='2099-02-03',horseNames=['架空A','架空B','架空C'];
const sourceRace={race:1,postTime:'10:10',expected:3,horses:horseNames};
const sourceMark=JSON.stringify([sourceRace.postTime,sourceRace.expected,sourceRace.horses]);
const scoreMail={kind:'jrdb-provisional',date:dateScore,track:'東京',races:[sourceRace]};
const scoredMemo={date:dateScore,track:'東京',race:1,sourceMark,
 rows:horseNames.map((name,i)=>({number:i+1,name}))};
const completeScore='1 架空A S A B A B\n2 架空B A A S B A\n3 架空C B B A C B';
const scoreNotes=[
 {date:dateScore,track:'東京',race:1,text:completeScore,sourceMark,
  savedAt:'2099-02-02T10:00:00Z'},
 {date:dateScore,track:'東京',race:2,text:'1 S A B ? A',sourceMark:null,
  savedAt:'2099-02-02T10:00:00Z'},
 {date:dateScore,track:'東京',race:3,text:completeScore,sourceMark:'old-memo',
  savedAt:'2099-02-02T10:00:00Z'}
];
storage.set(mailKey,JSON.stringify([scoreMail]));
storage.set(memoKey,JSON.stringify([scoredMemo]));
storage.set(scoreKey,JSON.stringify(scoreNotes));
const boardScore=boot(),sc=boardScore.el;
sc('mDate').value=dateScore;sc('mDate').onchange();
sc('mTrack').value='東京';sc('mTrack').onchange();
sc('mRace').value='1';sc('mRace').onchange();
assert.equal(sc('mRaceBoard').children.length,12);
assert.equal(sc('mRaceBoard').children[0].children[3].textContent,'本人採点済');
assert.equal(sc('mRaceBoard').children[1].children[3].textContent,'採点途中');
assert.equal(sc('mRaceBoard').children[2].children[3].textContent,'要再確認');
assert.equal(sc('mRaceBoard').children[3].children[3].textContent,'採点未着手');
assert.match(sc('mRaceBoard').children[0].className,/has-factor-score/);
assert.match(sc('mRaceBoardStatus').textContent,/本人の5項目採点 済1R／途中1R／要再確認1R/);
assert.equal(sc('mDayCoverage').children.length,1);
assert.match(sc('mDayCoverage').children[0].children[1].textContent,/本人採点済1R・途中1R・要再確認1R/);
assert.match(sc('mDayCoverageSummary').textContent,/本人の5項目採点：済1R／途中1R／再確認1R/);
const originalFactorWrites=writes.length;
sc('mRaceBoard').children[1].onclick();
assert.equal(writes.length,originalFactorWrites,'board navigation never writes factor scores');
// If source data changes, the old scored memo must no longer appear complete.
const altered={...sourceRace,postTime:'10:15'};
storage.set(mailKey,JSON.stringify([{...scoreMail,races:[altered]}]));
sc('mRace').onchange();
assert.equal(sc('mRaceBoard').children[0].children[3].textContent,'要再確認');
assert.match(sc('mDayCoverageSummary').textContent,/再確認2R/);
// Corrupt score-note storage cannot be presented as zero or as approved ranking.
storage.set(scoreKey,JSON.stringify([{...scoreNotes[0],race:13}]));
sc('mRace').onchange();
assert.equal(sc('mRaceBoard').children[0].children[3].textContent,'採点メモ要確認');
assert.match(sc('mDayCoverageSummary').textContent,/保存した採点メモの形式が不正/);
storage.set(scoreKey,JSON.stringify(scoreNotes));
storage.set(mailKey,JSON.stringify([scoreMail]));
// A standalone private score note makes a venue visible even without JRDB mail.
const standalone={date:'2099-02-10',track:'京都',race:7,
 text:completeScore,sourceMark:null,savedAt:'2099-02-09T12:00:00Z'};
storage.set(scoreKey,JSON.stringify([standalone]));
const onlyScore=boot(),on=onlyScore.el;
on('mDate').value='2099-02-10';on('mDate').onchange();
assert.equal(on('mDayCoverage').children.length,1,'independent private score note surfaces the venue');
assert.equal(on('mDayCoverage').children[0].children[0].textContent,'京都');
assert.match(on('mDayCoverage').children[0].children[1].textContent,/本人採点済1R/);
assert.equal(on('mRaceBoard').children.length,0,'a venue is not invented as selected');



// Private saved drafts can be reviewed even when the user did not buy a ticket.
const reviewOnly=boot(),rv=reviewOnly.el,reviewDate='2099-03-01';
rv('mDate').value=reviewDate;rv('mDate').onchange();
rv('mTrack').value='京都';rv('mTrack').onchange();
rv('mRace').value='3';rv('mRace').onchange();
rv('mFirst').children[0].onclick();
rv('mSecond').children[1].onclick();
rv('mThird').children[2].onclick();
rv('mSave').onclick();
const draftRow=rv('mSaved').children[0];
assert.equal(draftRow.children[4].textContent,'実際の1〜3着を入力');
assert.match(rv('mDraftReviewSummary').textContent,/着順入力 0／1R/);
const purchaseKey='keiba-nine-owner-real-purchases-v1';
const purchaseBefore=storage.get(purchaseKey);
reviewOnly.setPrompt('1-1-2');draftRow.children[4].onclick();
assert.match(rv('mMsg').textContent,/異なる3頭/);
assert.equal(JSON.parse(storage.get(key)).find(x=>x.date===reviewDate).result,null);
reviewOnly.setPrompt('①②③');draftRow.children[4].onclick();
assert.deepEqual(JSON.parse(storage.get(key)).find(x=>x.date===reviewDate).result,[1,2,3]);
assert.match(rv('mDraftReviewSummary').textContent,/3連単組み合わせ内 1R/);
reviewOnly.setPrompt('4-2-3');rv('mSaved').children[0].children[4].onclick();
assert.match(rv('mDraftReviewSummary').textContent,/1着候補の取りこぼし 1R/);
assert.match(rv('mSaved').children[0].children[1].textContent,/1着候補から漏れ/);
assert.equal(storage.get(purchaseKey),purchaseBefore,'draft review never settles or creates real purchases');
reviewOnly.setPrompt('');rv('mSaved').children[0].children[4].onclick();
assert.equal(JSON.parse(storage.get(key)).find(x=>x.date===reviewDate).result,null,'clear only result');
reviewOnly.setPrompt('1-2-3');rv('mSaved').children[0].children[4].onclick();
// Saving the same formation again must not erase an already reviewed result.
rv('mSave').onclick();
assert.deepEqual(JSON.parse(storage.get(key)).find(x=>x.date===reviewDate).result,[1,2,3]);
// A changed formation makes the old result comparison invalid.
rv('mFirst').children[3].onclick();
rv('mSave').onclick();
assert.equal(JSON.parse(storage.get(key)).find(x=>x.date===reviewDate).result,null);
// Restoring older backups with no result field remains supported by the same parser.
const oldDraft=JSON.parse(storage.get(key)).find(x=>x.date===reviewDate);
delete oldDraft.result;
assert.ok(!Object.hasOwn(oldDraft,'result'));
const resumed=boot(),rm=resumed.el;
rm('mDate').value=reviewDate;rm('mDate').onchange();
rm('mTrack').value='京都';rm('mTrack').onchange();
rm('mRace').value='3';rm('mRace').onchange();
assert.match(rm('mDraftReviewSummary').textContent,/着順入力 0／1R/);
assert.ok(!js.includes('fetch('),'result review remains local-only');


// Bulk result notes are dry-run first, only for saved drafts on the selected date.
const multiReview=boot(),mr=multiReview.el;
mr('mDate').value=reviewDate;mr('mDate').onchange();
const matchLine=reviewDate+' 京都3R ①②③';
mr('mResultBulkText').value=matchLine+'\n'+matchLine;
const bulkBefore=storage.get(key),bulkWrites=writes.length;
mr('mResultBulkCheck').onclick();
assert.equal(mr('mResultBulkSave').disabled,true,'duplicate race blocks whole batch');
assert.equal(storage.get(key),bulkBefore);
mr('mResultBulkText').value=matchLine+'\n'+reviewDate+' 京都4R 1-2-3';
mr('mResultBulkCheck').onclick();
assert.match(mr('mResultBulkStatus').textContent,/下書き未保存/);
assert.equal(storage.get(key),bulkBefore,'missing drafts do not create results');
mr('mResultBulkText').value=matchLine;
mr('mResultBulkCheck').onclick();
assert.equal(mr('mResultBulkSave').disabled,false);
assert.equal(mr('mResultBulkPreview').children.length,1);
assert.match(mr('mResultBulkPreview').children[0].textContent,/3連単の組み合わせ内/);
assert.equal(storage.get(key),bulkBefore,'preview does not write');
assert.equal(writes.length,bulkWrites);
mr('mResultBulkText').value=matchLine+'\n';
mr('mResultBulkSave').onclick();
assert.equal(mr('mResultBulkSave').disabled,true,'modified input invalidates confirmation');
assert.equal(storage.get(key),bulkBefore);
mr('mResultBulkText').value=matchLine;
mr('mResultBulkCheck').onclick();
mr('mResultBulkSave').onclick();
assert.deepEqual(JSON.parse(storage.get(key)).find(x=>x.date===reviewDate).result,[1,2,3]);
assert.match(mr('mDraftReviewSummary').textContent,/3連単組み合わせ内 1R/);
assert.equal(storage.get(purchaseKey),purchaseBefore,'bulk outcomes never invent JRA purchases');
const afterResult=storage.get(key);
const cancelledBatch=boot(false),cb=cancelledBatch.el;
cb('mDate').value=reviewDate;cb('mDate').onchange();
cb('mResultBulkText').value=reviewDate+' 京都3R 4-2-3';
cb('mResultBulkCheck').onclick();
cb('mResultBulkSave').onclick();
assert.equal(storage.get(key),afterResult,'cancelled bulk result replacement keeps current notes');
// Another browser view changed drafts after preview: stop potentially stale overwrite.
const staleBatch=boot(),sb=staleBatch.el;
sb('mDate').value=reviewDate;sb('mDate').onchange();
sb('mResultBulkText').value=reviewDate+' 京都3R 4-2-3';
sb('mResultBulkCheck').onclick();
storage.set(key,JSON.stringify(JSON.parse(storage.get(key)).map(x=>x.date===reviewDate?{...x,savedAt:'2099-03-01T10:00:00Z'}:x)));
const beforeStaleReview=storage.get(key);
sb('mResultBulkSave').onclick();
assert.equal(storage.get(key),beforeStaleReview,'newer edits block old bulk review');
assert.match(sb('mResultBulkStatus').textContent,/もう一度検査/);


// Same-origin manual-scorecard batch: receiving NEVER creates a saved draft,
// purchase record, result or provider request. Existing bulk checker is reused.
const scoreBatchText=[
 '2026-11-07 東京11R',
 '1着：1・2',
 '2着：1・2・3・4',
 '3着：1・2・3・4・5・6・7・8',
 '',
 '2026-11-07 京都2R',
 '1着：1・2',
 '2着：1・2・3',
 '3着：1・2・3',
].join('\n');
const receivedPayload={
 version:'scorecard-bulk-v1',createdAt:new Date().toISOString(),
 date:'2026-11-07',count:2,points:40,text:scoreBatchText
};
const beforeHandoffDrafts=storage.get(key);
const beforeHandoffWrites=writes.length;
const recipient=boot(true,'#scorebatch=v1',receivedPayload);
const h=recipient.el;
assert.equal(h('mBulkPaste').value,scoreBatchText);
assert.equal(h('mDate').value,'2026-11-07');
assert.equal(h('mBulkPreview').children.length,2,'all races passed through existing bulk checker');
assert.equal(h('mBulkApply').disabled,false,'owner can review and explicitly save');
assert.match(h('mBulkStatus').textContent,/40点.*未保存/);
assert.equal(recipient.transient.size,0,'one-time temporary payload removed after import');
assert.equal(storage.get(key),beforeHandoffDrafts,'no bulk draft saved automatically');
assert.equal(writes.length,beforeHandoffWrites);
assert.equal(h('mBulkPreview').children[0].children[2].textContent.split(' ／ ').length,36);
assert.equal(h('mBulkPreview').children[1].children[2].textContent.split(' ／ ').length,4);
const all36Text=['福島','東京','京都'].flatMap(track=>
 Array.from({length:12},(_,i)=>[
  '2026-11-07 '+track+(i+1)+'R',
  '1着：1・2',
  '2着：1・2・3・4',
  '3着：1・2・3・4・5・6・7・8',
 ].join('\n'))).join('\n\n');
const fullDay=boot(true,'#scorebatch=v1',{
 ...receivedPayload,text:all36Text,count:36,points:1296,
});
assert.equal(fullDay.el('mBulkPreview').children.length,36,'bulk checker handles all 36R at once');
assert.equal(fullDay.el('mBulkApply').disabled,false);
assert.equal(fullDay.transient.size,0,'full 36R transfer is one-time');
assert.equal(storage.get(key),beforeHandoffDrafts,'36R preview is not an automatic save');
const invalidBatch={...receivedPayload,points:41};
const reject=boot(true,'#scorebatch=v1',invalidBatch),rj=reject.el;
assert.equal(rj('mBulkApply').disabled,true,'tampered count rejected');
assert.equal(rj('mBulkPaste').value,'');
assert.match(rj('mBulkStatus').textContent,/引き継ぎ停止/);
assert.equal(reject.transient.size,0);
const ancient=boot(true,'#scorebatch=v1',{
 ...receivedPayload,createdAt:'2020-01-01T00:00:00.000Z',
});
assert.equal(ancient.el('mBulkApply').disabled,true,'transfer expires');
assert.match(ancient.el('mBulkStatus').textContent,/期限切れ/);
const missingTransfer=boot(true,'#scorebatch=v1');
assert.equal(missingTransfer.el('mBulkApply').disabled,true);
assert.match(missingTransfer.el('mBulkStatus').textContent,/引き継ぎ停止/);
const noTransfer=boot(true,'',receivedPayload);
assert.equal(noTransfer.el('mBulkApply').disabled,true);
assert.equal(noTransfer.transient.size,1,'do not read a temporary payload without the exact URL token');
assert.equal(storage.get(key),beforeHandoffDrafts,'all transfer cases leave purchase and draft ledgers intact');


{
// Manually confirmed JRA scratch/withdrawn numbers are LOCAL memos, not
// provider-verified data. Fail closed on unsaved notes, conflicts and corruption.
const SCRATCH='keiba-nine-owner-scratch-notes-v1';
const beforeScratchDraft=storage.get(key);
const beforeScratchPurchase=storage.get(purchaseKey);
const ws=boot(),w=ws.el;
w('mDate').value='2026-11-14';w('mDate').onchange();
w('mTrack').value='東京';w('mTrack').onchange();
w('mRace').value='5';w('mRace').onchange();
w('mFirst').children[0].onclick();    // 1
w('mSecond').children[1].onclick();   // 2
w('mThird').children[2].onclick();    // 3
w('mThird').children[3].onclick();    // 4
assert.equal(w('mCount').textContent,'2点');
assert.equal(w('mSave').disabled,false);
assert.match(w('mScratchStatus').textContent,/未確認/);
w('mScratchInput').value='③';w('mScratchInput').oninput();
assert.equal(w('mSave').disabled,true,'unsaved withdrawal note prevents saving');
assert.match(w('mScratchStatus').textContent,/未保存/);
w('mScratchSave').onclick();
assert.equal(JSON.parse(storage.get(SCRATCH)).length,1);
assert.deepEqual(JSON.parse(storage.get(SCRATCH))[0].numbers,[3]);
assert.equal(w('mSave').disabled,true,'withdrawn horse included in ticket candidates');
assert.match(w('mScratchStatus').textContent,/保存停止.*3番/);
w('mSave').onclick(); // direct handler invocation cannot bypass disabled button
assert.equal(storage.get(key),beforeScratchDraft);
assert.equal(storage.get(purchaseKey),beforeScratchPurchase);
w('mThird').children[2].onclick(); // drop 3
assert.equal(w('mSave').disabled,false,'safe ticket becomes savable after excluding withdrawn horse');
w('mSave').onclick();
assert.ok(JSON.parse(storage.get(key)).some(x=>
 x.date==='2026-11-14'&&x.track==='東京'&&x.race===5&&
 x.third.length===1&&x.third[0]===4));
const afterScratchSafe=storage.get(key);
w('mScratchInput').value='③⑦';w('mScratchInput').oninput();
assert.equal(w('mSave').disabled,true,'note edits must be explicitly stored first');
w('mScratchSave').onclick();
assert.deepEqual(JSON.parse(storage.get(SCRATCH))[0].numbers,[3,7]);
assert.equal(storage.get(key),afterScratchSafe,'scratch notes do not mutate stored drafts');
w('mScratchInput').value='③③';w('mScratchSave').onclick();
assert.deepEqual(JSON.parse(storage.get(SCRATCH))[0].numbers,[3,7],
 'duplicate numbers rejected without overwriting valid scratch memo');
w('mScratchInput').value='③⑦';w('mScratchInput').oninput();
assert.equal(w('mSave').disabled,false);
w('mDate').value='2026-11-15';w('mDate').onchange();
assert.equal(w('mScratchInput').value,'','date-switch cannot leak previous race scratch notes');
w('mDate').value='2026-11-14';w('mDate').onchange();
assert.equal(w('mScratchInput').value,'3・7','saved scratch memo restored per race');

// 36R preview is rechecked at final save, even if another browser/tab adds a
// scratch after preview. No purchase or draft data can be overwritten.
const dayScratch=boot(),ds=dayScratch.el;
ds('mDate').value='2026-11-14';ds('mDate').onchange();
ds('mBulkPaste').value=[
 '2026-11-14 東京1R','1着：1','2着：2','3着：3',
 '','2026-11-14 京都1R','1着：1','2着：2','3着：4'
].join('\n');
ds('mBulkReview').onclick();
assert.equal(ds('mBulkApply').disabled,false,'initial safe candidate was reviewed');
const safeBulkSnapshot=storage.get(key);
const scratchBeforeInterleave=JSON.parse(storage.get(SCRATCH));
storage.set(SCRATCH,JSON.stringify([...scratchBeforeInterleave,{
 date:'2026-11-14',track:'東京',race:1,numbers:[3],
 savedAt:'2026-11-06T00:00:00.000Z'
}]));
ds('mBulkApply').onclick();
assert.equal(ds('mBulkApply').disabled,true,'new withdrawal after preview invalidates pending save');
assert.match(ds('mBulkStatus').textContent,/一括保存停止.*東京1R/);
assert.equal(storage.get(key),safeBulkSnapshot,'interleaving must preserve old drafts');
assert.equal(storage.get(purchaseKey),beforeScratchPurchase);
ds('mBulkReview').onclick();
assert.equal(ds('mBulkApply').disabled,true,'bulk review detects cancelled third candidate');
assert.match(ds('mBulkStatus').textContent,/一括検査できません.*東京1R/);
// The same guard applies when 36R are received from the scorecard handoff.
const scratchHandoff=boot(true,'#scorebatch=v1',{
 version:'scorecard-bulk-v1',createdAt:new Date().toISOString(),
 date:'2026-11-14',count:1,points:1,
 text:'2026-11-14 東京1R\n1着：1\n2着：2\n3着：3'
});
assert.equal(scratchHandoff.el('mBulkApply').disabled,true,'scorecard transfer cannot bypass withdrawn guard');
assert.equal(scratchHandoff.transient.size,0);
assert.equal(storage.get(key),safeBulkSnapshot);
// Cancellation can change WHILE the confirmation dialog is open. Both
// single-R overwrite and all-R apply must recheck immediately before writing.
const atSingle=storage.get(key);
const guardSingle=boot(()=>{
 const notes=JSON.parse(storage.get(SCRATCH));
 storage.set(SCRATCH,JSON.stringify(notes.map(n=>
  n.date==='2026-11-14'&&n.track==='東京'&&n.race===5?
   {...n,numbers:[3,5,7]}:n)));
 return true;
}),gs=guardSingle.el;
gs('mDate').value='2026-11-14';gs('mDate').onchange();
gs('mTrack').value='東京';gs('mTrack').onchange();
gs('mRace').value='5';gs('mRace').onchange();
gs('mThird').children[3].onclick(); // remove saved #4
gs('mThird').children[4].onclick(); // #5 still allowed before confirmation
assert.equal(gs('mSave').disabled,false);
gs('mSave').onclick();
assert.equal(storage.get(key),atSingle,'post-confirm scratch recheck protects single draft');
assert.match(gs('mMsg').textContent,/保存停止.*5番/);
const atBulk=storage.get(key);
const guardBulk=boot(()=>{
 storage.set(SCRATCH,JSON.stringify([...JSON.parse(storage.get(SCRATCH)),{
  date:'2026-11-14',track:'京都',race:1,numbers:[4],
  savedAt:'2026-11-06T00:00:00.000Z'
 }]));
 return true;
}),gb=guardBulk.el;
gb('mDate').value='2026-11-14';gb('mDate').onchange();
gb('mBulkPaste').value='2026-11-14 京都1R\n1着：1\n2着：2\n3着：4';
gb('mBulkReview').onclick();
assert.equal(gb('mBulkApply').disabled,false);
gb('mBulkApply').onclick();
assert.equal(storage.get(key),atBulk,'post-confirm scratch recheck protects day batch');
assert.equal(gb('mBulkApply').disabled,true);
assert.match(gb('mBulkStatus').textContent,/一括保存停止.*京都1R/);
assert.equal(storage.get(purchaseKey),beforeScratchPurchase);

// Corrupted scratch storage means UNKNOWN, never "no withdrawals."
storage.set(SCRATCH,'{"wrong":"shape"}');
const corrupt=boot(),cc=corrupt.el;
cc('mDate').value='2026-11-14';cc('mDate').onchange();
cc('mTrack').value='東京';cc('mTrack').onchange();
cc('mRace').value='5';cc('mRace').onchange();
assert.match(cc('mScratchStatus').textContent,/破損/);
assert.equal(cc('mSave').disabled,true);
cc('mBulkPaste').value='2026-11-14 京都1R\n1着：1\n2着：2\n3着：4';
cc('mBulkReview').onclick();
assert.equal(cc('mBulkApply').disabled,true,'malformed global notes block all bulk saves');
assert.match(cc('mBulkStatus').textContent,/一括検査できません/);
storage.delete(SCRATCH);
assert.equal(storage.get(purchaseKey),beforeScratchPurchase);

}
console.log('Manual private 3連単 notebook: 35+ offline points, storage, date and safety checks passed');
