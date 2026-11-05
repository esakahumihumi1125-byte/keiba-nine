/* Offline cross-course owner race dashboard tests: no external member data. */
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('/tmp/keiba-owner-race-workbench.js','utf8');
const keys={
 mail:'keiba-nine-jrdb-personal-mail-v1',
 memo:'keiba-nine-owner-manual-numbers-v1',
 score:'keiba-nine-owner-factor-notes-v1',
 ticket:'keiba-nine-owner-ticket-drafts-v1',
 purchase:'keiba-nine-owner-real-purchases-v1'
};
const date='2099-01-09';
function source(race,postTime='09:55'){
 return {race,postTime,expected:3,horses:['架空A','架空B','架空C']};
}
const marks=JSON.stringify(['09:55',3,['架空A','架空B','架空C']]);
function mkMail(track){return {kind:'jrdb-provisional',date,track,races:[source(1),source(2,'10:25')]}}
function mkMemo(track,race=1,sourceMark=marks){return {date,track,race,sourceMark,rows:[
 {number:1,name:'架空A'},{number:2,name:'架空B'},{number:3,name:'架空C'}]}}
const finished='1 架空A S A B A S\n2 架空B A A B C B\n3 架空C B B B C A';
function fixtures(){
 return {
  [keys.mail]:[mkMail('東京'),mkMail('京都'),mkMail('福島')],
  [keys.memo]:[mkMemo('東京'),mkMemo('京都',2,'old-source')],
  [keys.score]:[
   {date,track:'東京',race:1,text:finished,savedAt:'2099-01-08T18:00:00+09:00',sourceMark:marks},
   {date,track:'京都',race:2,text:finished,savedAt:'2099-01-08T18:00:00+09:00',sourceMark:'old-source'},
   {date,track:'福島',race:1,text:'1 架空A A ? ? ? ?',savedAt:'2099-01-08T18:00:00+09:00',sourceMark:null}
  ],
  [keys.ticket]:[{date,track:'東京',race:1,first:[1],second:[2],third:[3],savedAt:'2099-01-08T18:00:00+09:00'}],
  [keys.purchase]:[{date,track:'東京',race:1,id:'unit-01',first:[1],second:[2],third:[3],stake:100,payout:null,unit:100,purchasedAt:'2099-01-09T09:00:00+09:00'}]
 };
}
function boot(initial=fixtures()){
 const storage=new Map(Object.entries(initial).map(([k,v])=>[k,JSON.stringify(v)]));
 const nodes=new Map(),writes=[],links=[],events={};
 function element(tag='div'){
  return {tag,value:'',textContent:'',className:'',children:[],
   dataset:{},hidden:false,disabled:false,onclick:null,onchange:null,type:'',href:'',
   attrs:{},setAttribute(k,v){this.attrs[k]=v},
   append(...args){this.children.push(...args)},
   replaceChildren(...args){this.children=[...args]}};
 }
 function el(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id)}
 const ctx={
  document:{getElementById:el,createElement:element},
  window:{addEventListener:(event,handler)=>{events[event]=handler}},
  localStorage:{getItem:k=>storage.get(k)||null,setItem(k,v){writes.push(k);throw Error('Dashboard writes forbidden')}},
  Date,JSON,String,Number,Set,Map,URLSearchParams,Error,console
 };
 vm.runInNewContext(js,ctx);
 return {el,storage,writes,links,events};
}
const page=boot(),e=page.el;
assert.equal(e('workDate').value,date,'readiness defaults to upcoming saved date');
assert.match(e('workStatus').textContent,/2099-01-09/);
assert.equal(e('workMeetings').children.length,3,'3 racecourses grouped');
assert.equal(e('workMeetings').children.reduce((n,x)=>n+x.children[1].children.length,0),36,'all 36R accessible');
assert.match(e('workSummary').textContent,/36R表示/);
assert.match(e('workSummary').textContent,/JRDB想定6R/);
assert.match(e('workSummary').textContent,/馬番メモ一致1R/);
assert.match(e('workSummary').textContent,/評価入力完了1R/);
assert.match(e('workSummary').textContent,/3連単下書き1R/);
assert.match(e('workSummary').textContent,/実購入記録1R/);
assert.match(e('workSummary').textContent,/元資料要再確認1R/);
const workQueue=e('workNext');
assert.equal(workQueue.children.length,6,'six races including unpaid purchase need preparation');
assert.match(workQueue.children[0].children[0].textContent,/京都2R.*資料が不一致/,'stale materials first');
assert.equal(workQueue.children[0].children[1].href,'/jrdb-mail-local');
assert.match(workQueue.children[1].children[0].textContent,/東京1R.*払戻未確定/,'pending payout is actionable');
assert.ok(workQueue.children[1].children[1].href.startsWith('/my-tickets#select=v1&'));
assert.match(workQueue.children[2].children[0].textContent,/福島1R.*入力途中/,'partial manual factor scores after pending payout');
assert.ok(workQueue.children[2].children[1].href.startsWith('/my-scorecard#select=v1&'));
const queueParams=new URLSearchParams(workQueue.children[2].children[1].href.split('#')[1]);
assert.equal(queueParams.get('date'),date);
assert.equal(queueParams.get('track'),'福島');
assert.equal(queueParams.get('race'),'1');
assert.equal(queueParams.size,4,'queue URL must never contain horse/member/grade data');
assert.ok(workQueue.children.every(x=>!x.textContent.includes('架空A')));
assert.equal(page.writes.length,0,'next-action queue is also read-only');

const tokyo=e('workMeetings').children.find(v=>v.children[0].textContent.startsWith('東京'));
const kyoto=e('workMeetings').children.find(v=>v.children[0].textContent.startsWith('京都'));
const fukushima=e('workMeetings').children.find(v=>v.children[0].textContent.startsWith('福島'));
assert.ok(tokyo&&kyoto&&fukushima);
const t1=tokyo.children[1].children[0];
assert.equal(t1.dataset.stage,'pending');
assert.match(e('workLedger').textContent,/未確定 1件・投資 100円/);
assert.match(e('workLedger').textContent,/回収率 —/);
assert.match(t1.attrs['aria-label'],/払戻入力待ち/);
assert.equal(kyoto.children[1].children[1].dataset.stage,'stale');
assert.equal(fukushima.children[1].children[0].dataset.stage,'partial');
assert.equal(tokyo.children[1].children[1].dataset.stage,'mail');
assert.equal(tokyo.children[1].children[2].dataset.stage,'empty');
t1.onclick();
const detail=tokyo.children[2];
assert.match(detail.children[1].textContent,/JRA公式照合ではない/);
assert.match(detail.children[1].textContent,/本人入力 1件/);
assert.equal(t1.attrs['aria-pressed'],'true');
const buttons=detail.children[3].children;
assert.equal(buttons.length,3);
assert.ok(buttons[0].href.startsWith('/my-scorecard#select=v1&'));
assert.ok(buttons[1].href.startsWith('/my-tickets#select=v1&'));
assert.equal(buttons[2].href,'/jrdb-mail-local');
const params=new URLSearchParams(buttons[0].href.split('#')[1]);
assert.equal(params.get('date'),date);
assert.equal(params.get('track'),'東京');
assert.equal(params.get('race'),'1');
assert.equal(params.size,4,'only date, track, race sent as fragment');
assert.ok(!buttons[0].href.includes('架空A'));
assert.ok(!buttons[1].href.includes('架空A'));
assert.equal(page.writes.length,0,'dashboard never saves or purchases anything');
kyoto.children[1].children[1].onclick();
assert.match(kyoto.children[2].children[1].textContent,/元資料との不一致/);
assert.match(kyoto.children[2].children[1].textContent,/元資料を再確認/);
// iPhone UI: filter only actionable, and refresh after Safari BFCache return.
assert.equal(e('workOnlyActions').textContent,'','toggle initial accessible text is in HTML');
e('workOnlyActions').onclick();
assert.equal(e('workOnlyActions').attrs['aria-pressed'],'true');
assert.match(e('workOnlyActions').textContent,/ON/);
const activeGrid=e('workMeetings').children;
const tokyoFiltered=activeGrid.find(x=>x.children[0].textContent.startsWith('東京'));
const kyotoFiltered=activeGrid.find(x=>x.children[0].textContent.startsWith('京都'));
assert.equal(tokyoFiltered.children[1].children[0].hidden,false,'unsettled payout still appears in action-only view');
assert.equal(tokyoFiltered.children[1].children[1].hidden,false,'JRDB provisional still needs roster');
assert.equal(tokyoFiltered.children[1].children[2].hidden,true,'unknown races are not marked actionable');
assert.equal(kyotoFiltered.children[1].children[1].hidden,false,'stale memo is actionable');
assert.match(e('workSummary').textContent,/36R表示/,'full coverage remains visible in summary');
e('workOnlyActions').onclick();
assert.equal(e('workOnlyActions').attrs['aria-pressed'],'false');
assert.equal(e('workMeetings').children[0].children[1].children.every(x=>x.hidden===false),true,
 'OFF shows all 12 races per course');
assert.ok(typeof page.events.pageshow==='function','Safari BFCache page return rechecks saved data');
// Mutate only the simulated iPhone localStorage, not app code, to mimic saving a memo elsewhere.
const revised=fixtures();revised[keys.memo]=[mkMemo('東京',1,'changed'),mkMemo('京都',2,'old-source')];
page.storage.set(keys.memo,JSON.stringify(revised[keys.memo]));
page.events.pageshow({persisted:true});
assert.match(e('workSummary').textContent,/元資料要再確認2R/);
assert.equal(e('workNext').children.length,6,'new stale roster joins queue after browser return');
assert.match(e('workNext').children[0].children[0].textContent,/資料が不一致/);
e('workReload').onclick();
assert.match(e('workStatus').textContent,/読み直しました/);
assert.equal(page.writes.length,0,'neither filter nor refresh writes any user data');

// ROI summary only counts actual-purchase records with explicitly entered payouts.
// A 0 yen payout is a settled loss. Unknown payouts must remain out of ROI.
const ledgerFixture=fixtures();
ledgerFixture[keys.purchase]=[
 {...ledgerFixture[keys.purchase][0],id:'pending-a',payout:null,stake:100,unit:100},
 {...ledgerFixture[keys.purchase][0],id:'paid-win',payout:400,stake:100,unit:100},
 {...ledgerFixture[keys.purchase][0],id:'paid-loss',payout:0,stake:100,unit:100},
 {...ledgerFixture[keys.purchase][0],id:'other-date',date:'2099-01-08',payout:999,stake:100,unit:100}
];
const accounting=boot(ledgerFixture),ac=accounting.el;
ac('workDate').value=date;ac('workDate').onchange();
assert.match(ac('workLedger').textContent,/払戻確定 2件/);
assert.match(ac('workLedger').textContent,/確定投資 200円/);
assert.match(ac('workLedger').textContent,/確定払戻 400円/);
assert.match(ac('workLedger').textContent,/確定収支 \+200円/);
assert.match(ac('workLedger').textContent,/回収率 200\.0%/);
assert.match(ac('workLedger').textContent,/未確定 1件・投資 100円/);
assert.doesNotMatch(ac('workLedger').textContent,/999/,'other date never included');
assert.equal(accounting.writes.length,0,'read-only ROI must not settle tickets');
const closedFixture=fixtures();
closedFixture[keys.purchase]=[{...closedFixture[keys.purchase][0],payout:0}];
const closed=boot(closedFixture);
assert.equal(closed.el('workMeetings').children.find(x=>x.children[0].textContent.startsWith('東京')).children[1].children[0].dataset.stage,'actual');
assert.equal(closed.el('workNext').children.length,6,'settled purchase now needs result-review task');
assert.match(closed.el('workNext').children[1].children[0].textContent,/着順の振り返り未入力/);
assert.match(closed.el('workSummary').textContent,/着順メモ未入力1R/);
const reviewedFixture=fixture();
reviewedFixture[keys.purchase]=[{...reviewedFixture[keys.purchase][0],payout:0,result:[1,2,3]}];
const reviewed=boot(reviewedFixture),rev=reviewed.el;
assert.equal(rev('workNext').children.length,5,'manually reviewed result leaves no task');
assert.match(rev('workSummary').textContent,/着順メモ未入力0R/);
const badResult=fixture();
badResult[keys.purchase]=[{...badResult[keys.purchase][0],payout:0,result:[1,1,3]}];
const rejectedResult=boot(badResult);
assert.match(rejectedResult.el('workLedger').textContent,/集計を停止しました/,'invalid result refuses reporting');
assert.match(closed.el('workLedger').textContent,/回収率 0\.0%/);
// Malformed records must block accounting, not be silently ignored as 0 yen.
const corruptedLedger=fixtures();
corruptedLedger[keys.purchase]=[{...corruptedLedger[keys.purchase][0],stake:200}];
const invalid=boot(corruptedLedger);
assert.match(invalid.el('workStatus').textContent,/読み込めません/);
assert.match(invalid.el('workLedger').textContent,/集計を停止しました/);
assert.equal(invalid.el('workMeetings').children.length,0);
assert.equal(invalid.writes.length,0);


// No incoming mail: status must not imply race is confirmed or AI-grade was performed.
const noMail=boot({
 [keys.mail]:[],[keys.memo]:[],[keys.score]:[],
 [keys.ticket]:[{date,track:'京都',race:4,first:[1],second:[2],third:[3]}],
 [keys.purchase]:[]
});
assert.equal(noMail.el('workMeetings').children.length,1);
const k=noMail.el('workMeetings').children[0].children[1].children[3];
assert.equal(k.dataset.stage,'draft');
assert.equal(noMail.el('workNext').children.length,1);
assert.match(noMail.el('workNext').children[0].children[0].textContent,/下書きあり・購入記録なし/);
assert.ok(noMail.el('workNext').children[0].children[1].href.startsWith('/my-tickets#select=v1&'));

k.onclick();
assert.match(noMail.el('workMeetings').children[0].children[2].children[1].textContent,/未取込/);
assert.match(noMail.el('workMeetings').children[0].children[2].children[1].textContent,/3連単下書き：1点/);
// Corrupt browser data must not be silently treated as an empty or complete race.
page.storage.set(keys.mail,'{');
e('workDate').onchange();
assert.equal(e('workMeetings').children.length,0);
assert.match(e('workStatus').textContent,/読み込めません/);
assert.match(e('workSummary').textContent,/不正な記録/);
assert.equal(e('workNext').children.length,0,'corrupt records must not yield apparently valid recommendations');
// Missing race date: manually add one course; don't claim a fictitious meeting exists.
const empty=boot({[keys.mail]:[],[keys.memo]:[],[keys.score]:[],
 [keys.ticket]:[],[keys.purchase]:[]});
empty.el('workDate').value='2099-02-02';empty.el('workDate').onchange();
assert.equal(empty.el('workMeetings').children.length,0);
assert.match(empty.el('workNext').children[0].textContent,/対応候補はありません/);
assert.match(empty.el('workNext').children[0].textContent,/準備済みではありません/);

empty.el('workExtraTrack').value='中山';empty.el('workAddTrack').onclick();
assert.equal(empty.el('workMeetings').children.length,1);
assert.match(empty.el('workSummary').textContent,/12R表示／JRDB想定0R/);

// Completed user scores without any ticket should offer the 3連単 notebook.
// Even a fully graded local note does NOT mean JRA official race verification.
const gradedOnly=boot({
 [keys.mail]:[],[keys.memo]:[],
 [keys.score]:[{date,track:'東京',race:5,text:finished,sourceMark:null,savedAt:'2099-01-08T09:00:00Z'}],
 [keys.ticket]:[],[keys.purchase]:[]
});
assert.equal(gradedOnly.el('workNext').children.length,1);
assert.match(gradedOnly.el('workNext').children[0].children[0].textContent,/評価入力済・買い目未作成/);
assert.ok(gradedOnly.el('workNext').children[0].children[1].href.startsWith('/my-tickets#select=v1&'));
assert.match(gradedOnly.el('workSummary').textContent,/評価入力完了1R/);
assert.match(gradedOnly.el('workSummary').textContent,/JRDB想定0R/);
// Matching manually numbered horses should offer the scorecard next.
const memoOnly=boot({
 [keys.mail]:[mkMail('東京')],[keys.memo]:[mkMemo('東京')],
 [keys.score]:[],[keys.ticket]:[],[keys.purchase]:[]
});
assert.equal(memoOnly.el('workNext').children[0].children[1].textContent,'評価を始める');
assert.equal(new URLSearchParams(memoOnly.el('workNext').children[0].children[1].href.split('#')[1]).get('race'),'1');
// More than six local mail notices show a bounded queue, with an accurate remainder.
const twelve=boot({
 [keys.mail]:[{kind:'jrdb-provisional',date,track:'京都',races:Array.from(
  {length:12},(_,i)=>({...source(i+1),postTime:'provisional'}))}],
 [keys.memo]:[],[keys.score]:[],[keys.ticket]:[],[keys.purchase]:[]
});
assert.equal(twelve.el('workNext').children.length,7);
assert.match(twelve.el('workNext').children[6].textContent,/ほか6R/);
assert.equal(twelve.writes.length,0);

assert.ok(!js.includes('fetch('),'no data transmitted');
assert.ok(!js.includes('XMLHttpRequest'),'no data transmitted');
assert.ok(!js.includes('localStorage.setItem'),'read-only');
assert.ok(!js.includes('innerHTML'),'never inject member names as HTML');
console.log('Owner 36R local dashboard PASS: 3 venues, stale sources, progress, privacy and deep links');
