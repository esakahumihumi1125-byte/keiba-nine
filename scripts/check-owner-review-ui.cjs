/* Read-only per-position accuracy review, synthetic and offline only. */
'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const js=fs.readFileSync('/tmp/keiba-owner-result-review.js','utf8');
const DRAFT='keiba-nine-owner-ticket-drafts-v1',PURCHASE='keiba-nine-owner-real-purchases-v1';
const date='2099-02-14',track='東京';
const key=(race,t='東京')=>({date,track:t,race});
const form=(race,first,second,third,result=undefined)=>({
 ...key(race),first,second,third,savedAt:'2099-02-13T12:00:00Z',
 ...(result===undefined?{}:{result})
});
function count(x){const s=new Set();for(const a of x.first)for(const b of x.second)for(const c of x.third)
 if(a!==b&&a!==c&&b!==c)s.add(a+'-'+b+'-'+c);return s.size;}
function purchase(r,id,result=undefined){
 const x={...r,id,unit:100,stake:100*count(r),payout:null,
 purchasedAt:'2099-02-14T12:00:00Z'};
 if(result===undefined)delete x.result;else x.result=result;
 delete x.savedAt;
 return x;
}
function fixture(){
 const a=form(1,[1,2],[1,2,3],[1,2,3,4],[2,1,4]);
 const b=form(2,[1],[2,4],[3,4],[4,2,3]);
 const c=form(3,[1],[2],[3,4],[1,4,3]);
 const d=form(4,[1],[2],[3],[1,2,4]);
 const e=form(5,[1],[2],[3]);
 const f=form(6,[1],[2],[3],[1,2,3]);
 const x=form(7,[1],[2],[3]);
 const y=form(8,[1],[2],[3]);
 const z=form(9,[1],[2],[3]);
 return {
  [DRAFT]:[a,b,c,d,e,f],
  [PURCHASE]:[
   purchase(a,'real-a-1',[2,1,4]),purchase(a,'real-a-2',[2,1,4]),
   purchase(f,'real-conflict',[3,2,1]),
   purchase(x,'real-only',[1,2,3]),
   purchase(y,'real-dup-1',[1,2,3]),purchase(y,'real-dup-2',[1,2,3]),
   purchase(z,'real-pending')
  ]
 };
}
function boot(initial=fixture()){
 const storage=new Map(Object.entries(initial).map(([k,v])=>[k,JSON.stringify(v)]));
 const nodes=new Map(),events={};
 function element(tag='div'){
  return {tag,children:[],textContent:'',className:'',href:'',value:'',onclick:null,onchange:null,
   append(...children){this.children.push(...children)},
   replaceChildren(...children){this.children=[...children]}};
 }
 function el(id){if(!nodes.has(id))nodes.set(id,element());return nodes.get(id);}
 let writes=0;
 const localStorage={
  getItem:k=>storage.get(k)||null,
  setItem(){writes++;throw Error('review is read only')},
  removeItem(){writes++;throw Error('review is read only')}
 };
 el('reviewScope').value='all';
 vm.runInNewContext(js,{
  document:{getElementById:el,createElement:element},localStorage,
  window:{addEventListener:(name,fn)=>{events[name]=fn}},
  Date,JSON,Set,Map,Number,String,Error,console
 });
 return {el,events,storage,get writes(){return writes}};
}
let app=boot(),$=app.el;
assert.equal(app.writes,0);
assert.match($('reviewStatus').textContent,/対象 9R/);
assert.match($('reviewStatus').textContent,/結果の未入力 2R/);
assert.match($('reviewStatus').textContent,/着順メモ不一致 1R/);
const stats=id=>$(id).children.map(x=>x.textContent).join('\n');
assert.match(stats('reviewDraftStats'),/結果を比較できた予想：4件／6件/);
assert.match(stats('reviewDraftStats'),/1着馬を1着候補に入れた：3／4件/);
assert.match(stats('reviewDraftStats'),/2着馬を2着候補に入れた：3／4件/);
assert.match(stats('reviewDraftStats'),/3着馬を3着候補に入れた：3／4件/);
assert.match(stats('reviewDraftStats'),/3連単の組み合わせ内：1／4件/);
assert.match(stats('reviewDraftStats'),/勝ち馬が1着候補外：1件（2・3着候補にはいた：1件）/);
assert.match(stats('reviewPurchaseStats'),/結果を比較できた予想：3件／5件/);
assert.match(stats('reviewPurchaseStats'),/3連単の組み合わせ内：3／3件/);
const details=$('reviewDetails').children;
assert.equal(details.length,9);
const byRace=n=>details.find(x=>x.children[0].textContent===date+' 東京'+n+'R');
const first=byRace(1),second=byRace(2),third=byRace(3),fourth=byRace(4);
assert.ok(first.children.some(x=>/同一買い目2件/.test(x.textContent)),'duplicate purchases grouped once');
assert.match(second.children[2].textContent,/1着 候補外（2・3着候補にあり）/);
assert.match(third.children[2].textContent,/2着 候補外/);
assert.match(fourth.children[2].textContent,/3着 候補外/);
assert.match(byRace(6).children[1].textContent,/食い違って/);
assert.match(byRace(6).children[2].textContent,/照合保留/);
assert.match(byRace(5).children[2].textContent,/着順メモ未入力/);
assert.equal(byRace(1).children.at(-1).href,'/my-tickets#select=v1&date='+date+'&track=%E6%9D%B1%E4%BA%AC&race=1');
assert.equal(app.writes,0);
$('reviewScope').value='day';$('reviewDate').value='2099-02-15';
$('reviewScope').onchange();
assert.match($('reviewStatus').textContent,/対象 0R/);
assert.match(stats('reviewDraftStats'),/0件／0件/);
assert.match(stats('reviewDraftStats'),/まだ比較可能な着順メモがありません/);
$('reviewDate').value=date;$('reviewDate').onchange();
assert.match($('reviewStatus').textContent,/対象 9R/);
$('reviewScope').value='all';$('reviewScope').onchange();
app.storage.set(DRAFT,JSON.stringify([{...fixture()[DRAFT][0],result:[1,1,2]}]));
$('reviewRefresh').onclick();
assert.match($('reviewStatus').textContent,/集計を停止しました/);
assert.equal($('reviewDraftStats').children.length,0);
assert.equal($('reviewDetails').children.length,0,'corruption must never produce a score');
assert.equal(app.writes,0);
app=boot({...fixture(),[DRAFT]:[fixture()[DRAFT][0],fixture()[DRAFT][0]]});
assert.match(app.el('reviewStatus').textContent,/集計を停止しました/,'duplicate draft same race rejected');
app=boot({...fixture(),[PURCHASE]:[fixture()[PURCHASE][0],fixture()[PURCHASE][0]]});
assert.match(app.el('reviewStatus').textContent,/集計を停止しました/,'duplicate purchases rejected');
app=boot({[DRAFT]:[],[PURCHASE]:[]});
assert.match(app.el('reviewStatus').textContent,/対象 0R/);
assert.equal(app.el('reviewDetails').children.length,1);
assert.match(app.el('reviewDetails').children[0].textContent,/表示する予想下書き/);
assert.ok(typeof app.events.pageshow==='function');
app.events.pageshow({persisted:true});
assert.equal(app.writes,0);
assert.ok(!js.includes('fetch('),'no network fetch in private review');
assert.ok(!js.includes('XMLHttpRequest'),'no XHR in private review');
assert.ok(!js.includes('innerHTML'),'no injecting saved user text into HTML');

// Descriptive 5-factor comparisons use only completed, pre-day owner notes.
// Retroactive same-day edits, stale source mappings and contradictory results never count.
const SCORE='keiba-nine-owner-factor-notes-v1';
const MAIL='keiba-nine-jrdb-personal-mail-v1';
const MEMO='keiba-nine-owner-manual-numbers-v1';
const factorNote=(race,text,savedAt='2099-02-13T06:00:00Z',sourceMark=null)=>({
 ...key(race),text,savedAt,sourceMark
});
const noteRows=[
 factorNote(1,'1 架空A S S A B A\n2 架空B A A S A B\n3 架空C B B B B B\n4 架空D B A B B B'),
 factorNote(2,'1 架空A S S S S S\n2 架空B A A A B B\n4 架空D B B S B A'),
 factorNote(3,'1 架空A S S S S S\n2 架空B A A A B B\n4 架空D B B B B B','2099-02-14T01:00:00Z'),
 factorNote(4,'1 架空A S S S S S\n2 架空B A A A B B\n3 架空C B B B B B\n4 架空D B B B B B','2099-02-13T06:00:00Z','stale-mark')
];
const gradeData={...fixture(),[SCORE]:noteRows,[MAIL]:[],[MEMO]:[]};
const grading=boot(gradeData),ge=grading.el;
assert.match(ge('reviewDraftStats').children.map(x=>x.textContent).join(' '),/4件／6件/);
const gradeSummary=ge('reviewFactorStats').children.map(x=>x.textContent).join('\n');
assert.match(gradeSummary,/有効な本人採点 2R／参考集計外 2R/);
assert.match(gradeSummary,/1着候補から漏れた勝ち馬の採点 1R／1着候補に含めた勝ち馬の採点 1R/);
assert.match(gradeSummary,/調教/);
assert.match(gradeSummary,/1着漏れ S:0・A:0・B:1・C:0/);
assert.match(gradeSummary,/適性/);
const gRows=ge('reviewDetails').children;
const rowFor=n=>gRows.find(x=>x.children[0].textContent===date+' 東京'+n+'R');
assert.match(rowFor(1).children.at(-2).textContent,/勝ち馬2番.*2\/4位.*調教A／近走A／適性S/);
assert.match(rowFor(2).children.at(-2).textContent,/勝ち馬4番.*調教B／近走B／適性S/);
assert.match(rowFor(3).children.at(-2).textContent,/当日以降に編集された採点/);
assert.match(rowFor(4).children.at(-2).textContent,/元資料・馬番メモと不一致/);
assert.equal(grading.writes,0,'factor summaries cannot mutate owner storage');
const matchedNames=['架空1','架空2','架空3','架空4'];
const mark=JSON.stringify(['09:55',4,matchedNames]);
const withSource=boot({...fixture(),
 [SCORE]:[factorNote(4,matchedNames.map((name,i)=>(i+1)+' '+name+' S A B A B').join('\n'),'2099-02-13T06:00:00Z',mark)],
 [MAIL]:[{kind:'jrdb-provisional',date,track,races:[{race:4,postTime:'09:55',expected:4,horses:matchedNames}]}],
 [MEMO]:[{...key(4),sourceMark:mark,rows:matchedNames.map((name,i)=>({number:i+1,name}))}]
});
assert.match(withSource.el('reviewFactorStats').children.map(x=>x.textContent).join(' '),/有効な本人採点 1R/);
const staleSource=boot({...fixture(),
 [SCORE]:[factorNote(4,matchedNames.map((name,i)=>(i+1)+' '+name+' S A B A B').join('\n'),'2099-02-13T06:00:00Z',mark)],
 [MAIL]:[{kind:'jrdb-provisional',date,track,races:[{race:4,postTime:'09:55',expected:4,horses:matchedNames}]}],
 [MEMO]:[{...key(4),sourceMark:'changed-source',rows:matchedNames.map((name,i)=>({number:i+1,name}))}]
});
assert.match(staleSource.el('reviewFactorStats').children.map(x=>x.textContent).join(' '),/有効な本人採点 0R/);
const malformed=boot({...fixture(),[SCORE]:[{...noteRows[0],race:19}]});
assert.match(malformed.el('reviewStatus').textContent,/対象 9R/,'bad factor memo does not erase valid outcome comparison');
assert.match(malformed.el('reviewFactorStats').children[0].textContent,/採点の比較は停止/);
assert.equal(malformed.writes,0);

console.log('Owner race-result diagnostics: separated draft/purchase, 1st-3rd misses, dedup, conflict and privacy PASS');
