"""Owner-local cross-course 36R workbench. No server-side race or member-data ingestion.

The page is a static authenticated UI. It reads existing owner browser storage
to show readiness; it does not verify official JRA entries or calculate AI picks.
"""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>競馬ナイン｜全開催R準備一覧</title>
<link rel="stylesheet" href="/owner-race-workbench.css"></head>
<body><main><a href="/">← 本人用ホームへ</a>
<h1>全開催Rの準備一覧</h1>
<p class="warning">本人用・端末内だけの進捗一覧です。<b>JRDB想定メールと本人転記メモの一致は、JRA公式の出走確定や取消確認ではありません。</b> AI予想・自動投票もしていません。</p>
<section><h2>開催日を選択</h2>
<label for="workDate">開催日</label><input id="workDate" type="date">
<div class="quick"><button type="button" id="workSaturday">次の土曜</button>
<button type="button" id="workSunday">次の日曜</button></div>
<div class="quick"><label for="workExtraTrack">競馬場が一覧にない場合</label>
<select id="workExtraTrack"><option value="">競馬場を追加表示</option>
<option>札幌</option><option>函館</option><option>福島</option><option>新潟</option>
<option>東京</option><option>中山</option><option>中京</option><option>京都</option>
<option>阪神</option><option>小倉</option></select>
<button type="button" id="workAddTrack">追加表示</button></div>
<div class="quick"><button type="button" id="workReload">端末内の記録を再読込</button><button type="button" id="workOnlyActions" aria-pressed="false">作業対象Rだけ表示：OFF</button></div><p id="workStatus" role="status" class="hint">端末に保存された資料を確認します。</p></section>
<section><h2>最大36Rの準備状況</h2>
<div id="workSummary" class="summary" role="status"></div><div id="workLedger" class="ledger-summary" role="status">購入記録を確認しています。</div>
<div class="next-queue"><h3>次に準備するレース</h3><p class="hint">本人が保存した資料の不足・不一致から作った作業リストです。優先順位は発走順・勝率・公式情報の確定ではありません。</p><div id="workNext" aria-label="次に準備するレースと操作"></div></div>
<div class="legend">未取込／JRDB想定／馬番メモ一致／評価途中／評価入力済／3連単下書き／実購入記録</div>
<div id="workMeetings" aria-label="各競馬場の12R準備"></div></section>
<section><h2>実戦で必要な確認</h2>
<p class="hint">1Rの枠をタップすると、端末内にある資料の段階と、評価・3連単画面へのリンクが出るで。URLには日付・競馬場・Rだけを引き継ぐ。本人の馬名・JRDB本文・買い目・購入情報は送らない。</p>
<div class="quick"><a href="/jrdb-mail-local">JRDB想定メール・馬番メモの取込</a>
<a href="/owner-backup">5種類の記録をバックアップ</a><a href="/my-tickets#actualPurchasePanel">結果の振り返りを開く</a></div>
<p class="warning">発走時刻、出走取消、馬場、馬番、購入締切はJRA公式で別途確認。実購入記録は本人が登録した記録であり、投票・購入の完了確認ではありません。</p>
<a href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式の出馬表を確認</a>
</section>
</main><script defer src="/owner-race-workbench.js"></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#eff4ff;font:15px/1.5 system-ui,sans-serif}main{max-width:760px;margin:auto;padding:18px 12px 48px}h1{font-size:25px}h2{font-size:19px;margin:0 0 10px}a{color:#f5d27c}section{background:#142b44;border:1px solid #4d6885;border-radius:14px;margin:14px 0;padding:14px}.warning{color:#ffe4a9;background:#302b24;border:1px solid #957a4b;padding:11px;border-radius:10px;font-size:13px}.hint{color:#c5d6e7;font-size:13px}.legend{color:#c4d2df;font-size:12px;margin:8px 0 14px}.quick{display:flex;gap:8px;margin:10px 0;flex-wrap:wrap;align-items:center}.quick label{width:100%}.quick a,.quick button{flex:1;min-width:125px;text-align:center}input,select,button{font:inherit;min-height:43px;background:#0b2035;color:white;border:1px solid #8099b4;border-radius:8px;padding:8px}input[type=date]{width:100%}button{cursor:pointer}button:focus-visible,a:focus-visible{outline:2px solid #f2d17d}.summary{color:#f1d481;font-weight:700}.ledger-summary{margin:12px 0;padding:12px;border:1px solid #627f98;border-radius:10px;background:#10243a;color:#e1eafa;font-size:13px;line-height:1.8}.race-btn[data-stage=pending]{background:#66502d;color:#fff0ce}.next-queue{margin-top:16px;padding:11px;border:1px solid #456d85;border-radius:10px;background:#10263b}.next-queue h3{margin:0;font-size:16px}.queue-row{display:flex;flex-wrap:wrap;justify-content:space-between;gap:7px;padding:10px 0;border-top:1px solid #40576d}.queue-row strong{font-size:14px}.queue-row p{width:100%;margin:0;color:#cbd9e7;font-size:12px}.queue-row a{border:1px solid #aab7c4;border-radius:8px;padding:6px 10px;align-self:center;min-height:36px}.queue-alert strong{color:#ffca9e}.race-btn[hidden]{display:none!important}.quick button[aria-pressed=true]{background:#2d594b;border-color:#c0dfcc;color:#fff}.venue{padding:10px;margin:13px 0;background:#0e233a;border:1px solid #46637f;border-radius:11px}.venue h3{margin:2px 0 8px;font-size:17px}.race-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.race-btn{border:1px solid #66768d;padding:6px 3px;min-height:63px;background:#28394c}.race-btn .race-no{display:block;font-weight:800;font-size:15px}.race-btn small{display:block;line-height:1.3;font-size:10px;white-space:normal}.race-btn[data-stage=empty]{color:#c7cbd0}.race-btn[data-stage=mail]{background:#2a3e52}.race-btn[data-stage=roster]{background:#294c52}.race-btn[data-stage=partial]{background:#63512f}.race-btn[data-stage=graded]{background:#31513f}.race-btn[data-stage=draft]{background:#46548a}.race-btn[data-stage=actual]{background:#5a4376}.race-btn[data-stage=stale]{background:#633e3b;color:#ffe8c2}.race-btn[aria-pressed=true]{outline:2px solid #f2d17d;outline-offset:1px}.race-detail{margin-top:12px;border:1px solid #5a7a96;padding:10px;border-radius:9px}.race-detail p{margin:6px 0;font-size:13px}.actions{display:flex;flex-wrap:wrap;gap:8px;margin:9px 0}.actions a{padding:8px;border:1px solid #a4b8c8;border-radius:8px;min-height:39px}.error{color:#ffc1a3}"""

JS = r"""(()=>{'use strict';
// Read-only local progress. No fetch / XHR / server data transfer or purchase.
const $=id=>document.getElementById(id);
const MAIL='keiba-nine-jrdb-personal-mail-v1';
const NUMBERS='keiba-nine-owner-manual-numbers-v1';
const SCORES='keiba-nine-owner-factor-notes-v1';
const DRAFTS='keiba-nine-owner-ticket-drafts-v1';
const PURCHASES='keiba-nine-owner-real-purchases-v1';
const TRACKS=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
const KEYS=[MAIL,NUMBERS,SCORES,DRAFTS,PURCHASES],LIMITS=[48,576,300,300,500];
const MAX_RACES=36;
let current=null,additions=new Set(),onlyActions=false;
function jstDate(){
 return new Date(Date.now()+9*3600000).toISOString().slice(0,10);
}
function validDate(value){
 if(typeof value!=='string'||!/^20\d{2}-\d{2}-\d{2}$/.test(value))return false;
 const date=new Date(value+'T12:00:00Z');
 return Number.isFinite(date.valueOf())&&date.toISOString().slice(0,10)===value;
}
function key(x){return x.date+'|'+x.track+'|'+x.race;}
function readData(){
 const result={};
 for(let i=0;i<KEYS.length;i++){
  const k=KEYS[i],raw=localStorage.getItem(k);
  if(raw&&raw.length>2500000)throw Error('端末内の保存データが大きすぎます。');
  const value=JSON.parse(raw||'[]');
  if(!Array.isArray(value)||value.length>LIMITS[i]||value.some(x=>!x||typeof x!=='object'))
   throw Error('端末内の保存データを確認してください（'+(i+1)+'番目）。');
  result[k]=value;
 }
 if(!result[PURCHASES].every(validPurchaseRecord)||
    new Set(result[PURCHASES].map(x=>x.id)).size!==result[PURCHASES].length)
  throw Error('購入記録に金額・買い目の不整合かID重複があります。データを保護するため集計を停止しました。');
 return result;
}
function meetingFor(data,date,track){
 return data[MAIL].find(x=>x.kind==='jrdb-provisional'&&x.date===date&&x.track===track);
}
function nameMemoMatches(memo,source){
 if(!memo||!source||!Array.isArray(source.horses)||
  !Number.isInteger(source.expected)||source.expected<1||source.expected>18||
  !Array.isArray(memo.rows)||memo.rows.length!==source.expected||
  memo.sourceMark!==JSON.stringify([source.postTime,source.expected,source.horses]))return false;
 const names=new Set(source.horses),seenNumbers=new Set(),seenNames=new Set();
 if(names.size!==source.expected)return false;
 for(const row of memo.rows){
  if(!row||!Number.isInteger(row.number)||row.number<1||row.number>18||
   typeof row.name!=='string'||!names.has(row.name)||
   seenNumbers.has(row.number)||seenNames.has(row.name))return false;
  seenNumbers.add(row.number);seenNames.add(row.name);
 }
 return true;
}
function scoreCompleted(note){
 if(!note||typeof note.text!=='string')return false;
 const lines=note.text.trim().split(/\r?\n/).filter(Boolean);
 if(lines.length<3||lines.length>18)return false;
 const used=new Set();
 for(const line of lines){
  const x=line.trim().replace(/[①-⑱]/g,n=>String('①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱'.indexOf(n)+1)).split(/\s+/);
  const grade=x.slice(x.length-5);
  const no=Number(x[0]);
  if(!Number.isInteger(no)||no<1||no>18||used.has(no)||
   (x.length!==6&&x.length!==7)||
   grade.some(g=>!['S','A','B','C'].includes(g)))return false;
  used.add(no);
 }
 return true;
}
function draftPoints(d){
 if(!d||!Array.isArray(d.first)||!Array.isArray(d.second)||!Array.isArray(d.third))return 0;
 const out=new Set();
 for(const a of d.first)for(const b of d.second)for(const c of d.third)
  if([a,b,c].every(n=>Number.isInteger(n)&&n>=1&&n<=18)&&a!==b&&a!==c&&b!==c)out.add(a+'-'+b+'-'+c);
 return out.size>48?0:out.size;
}
function validFinish(result){
 return Array.isArray(result)&&result.length===3&&
  result.every(n=>Number.isInteger(n)&&n>=1&&n<=18)&&new Set(result).size===3;
}
function validPurchaseRecord(x){
 if(!x||!validDate(x.date)||!TRACKS.includes(x.track)||
    !Number.isInteger(x.race)||x.race<1||x.race>12||
    typeof x.id!=='string'||!/^[0-9a-z-]{1,80}$/.test(x.id)||
    !Number.isSafeInteger(x.unit)||x.unit<100||x.unit>100000||x.unit%100!==0||
    !Number.isSafeInteger(x.stake)||x.stake<100||
    (x.payout!==null&&(!Number.isSafeInteger(x.payout)||x.payout<0))||
    (Object.prototype.hasOwnProperty.call(x,'result')&&x.result!==null&&!validFinish(x.result))||
    typeof x.purchasedAt!=='string'||x.purchasedAt.length>32)return false;
 const count=draftPoints(x);
 return count>=1&&x.stake===count*x.unit;
}
function yen(amount){return amount.toLocaleString('ja-JP')+'円';}
function summarizePurchases(data,date){
 const day=data[PURCHASES].filter(x=>x.date===date);
 const paid=day.filter(x=>x.payout!==null);
 const pending=day.filter(x=>x.payout===null);
 const invested=paid.reduce((sum,x)=>sum+x.stake,0);
 const returned=paid.reduce((sum,x)=>sum+x.payout,0);
 const pendingStake=pending.reduce((sum,x)=>sum+x.stake,0);
 const profit=returned-invested;
 const roi=invested?(returned/invested*100).toFixed(1)+'%':'—';
 return '選択日の本人入力・全競馬場｜払戻確定 '+paid.length+
  '件／確定投資 '+yen(invested)+'／確定払戻 '+yen(returned)+
  '／確定収支 '+(profit>0?'+':'')+yen(profit)+'／回収率 '+roi+
  '／未確定 '+pending.length+'件・投資 '+yen(pendingStake)+
  '（回収率には未計上。JRAの購入履歴と未照合）';
}
function raceStatus(data,date,track,race){
 const m=meetingFor(data,date,track);
 const source=m&&Array.isArray(m.races)&&m.races.find(x=>x.race===race);
 const memo=data[NUMBERS].find(x=>x.date===date&&x.track===track&&x.race===race);
 const note=data[SCORES].find(x=>x.date===date&&x.track===track&&x.race===race);
 const ticket=data[DRAFTS].find(x=>x.date===date&&x.track===track&&x.race===race);
 const actual=data[PURCHASES].filter(x=>x.date===date&&x.track===track&&x.race===race);
 const unsettled=actual.filter(x=>x.payout===null);
 const reviewed=actual.filter(x=>validFinish(x.result));
 const reviewPending=actual.filter(x=>x.payout!==null&&!validFinish(x.result));
 const matching=nameMemoMatches(memo,source);
 const stale=!!(memo&&!matching)||!!(note&&note.sourceMark!==null&&note.sourceMark!==undefined&&
   (!matching||note.sourceMark!==memo.sourceMark));
 const graded=scoreCompleted(note)&&(!note.sourceMark||matching)&&!stale;
 const points=draftPoints(ticket),hasTicket=!!ticket&&points>0;
 const state=stale?'stale':unsettled.length?'pending':actual.length?'actual':hasTicket?'draft':graded?'graded':note?'partial':
   matching?'roster':source?'mail':'empty';
 const labels={stale:'資料再確認',pending:'払戻入力待ち',actual:'購入記録',draft:'3連単下書',graded:'採点入力済',
  partial:'評価途中',roster:'馬番メモ',mail:'JRDB想定',empty:'未取込'};
 return {state,label:labels[state],source:!!source,matching,hasMemo:!!memo,
  hasScore:!!note,graded,stale,points,actual:actual.length,pending:unsettled.length,
  reviewed:reviewed.length,reviewPending:reviewPending.length,post:source&&source.postTime};
}
function tracksFor(data,date){
 const tracks=new Set(additions);
 for(const k of KEYS)for(const item of data[k]){
  if(item.date===date&&TRACKS.includes(item.track))tracks.add(item.track);
 }
 // These two dates have confirmed *JRDB provisional mailings*, not verified JRA racecards.
 if(date==='2026-11-07'||date==='2026-11-08')
  for(const venue of ['東京','京都','福島'])tracks.add(venue);
 return TRACKS.filter(x=>tracks.has(x)).slice(0,3);
}
function jumpUrl(path,date,track,race){
 const p=new URLSearchParams();
 p.set('select','v1');p.set('date',date);
 p.set('track',track);p.set('race',String(race));
 return path+'#'+p.toString();
}
function create(tag,text){
 const node=document.createElement(tag);
 if(text!==undefined)node.textContent=String(text);
 return node;
}
function statusText(s){
 return [
  s.source?'JRDB想定確定メール：登録あり（JRA公式照合ではない）':'JRDB想定確定メール：未取込',
  s.matching?'馬番・馬名メモ：想定メールと一致（本人転記）':s.hasMemo?'馬番メモ：元資料との不一致・再確認':'馬番メモ：未登録',
  s.hasScore?s.stale?'5項目評価：元資料を再確認':s.graded?'5項目評価：本人入力が全項目完了':'5項目評価：保存途中':'5項目評価：未入力',
  s.points?'3連単下書き：'+s.points+'点（未購入）':'3連単下書き：なし',
  s.actual?'実購入記録：本人入力 '+s.actual+'件（払戻未確定 '+s.pending+'件・着順メモ済 '+s.reviewed+'件・JRA購入完了は未確認）':'実購入記録：なし'
 ].join('／');
}

function nextAction(s){
 // Requires real locally stored progress, never invents a race or predicts a winner.
 if(s.stale)return {priority:0,label:'資料が不一致・再確認',link:'/jrdb-mail-local',cta:'馬番メモを確認'};
 if(s.pending>0)return {priority:1,label:'払戻未確定 '+s.pending+'件',link:'/my-tickets',cta:'払戻を入力'};
 if(s.reviewPending>0)return {priority:1.5,label:'着順の振り返り未入力 '+s.reviewPending+'件',link:'/my-tickets',cta:'着順を記録'};
 if(s.actual>0)return null;
 if(s.graded&&!s.points)return {priority:2,label:'評価入力済・買い目未作成',link:'/my-tickets',cta:'3連単を作る'};
 if(s.hasScore&&!s.graded&&!s.points)return {priority:3,label:'手動評価の入力途中',link:'/my-scorecard',cta:'評価を続ける'};
 if(s.matching&&!s.hasScore&&!s.points)return {priority:4,label:'馬番メモあり・評価未入力',link:'/my-scorecard',cta:'評価を始める'};
 if(s.source&&!s.matching&&!s.hasScore&&!s.points)return {priority:5,label:'想定メールあり・馬番未照合',link:'/jrdb-mail-local',cta:'馬番を照合'};
 if(s.points>0&&!s.actual)return {priority:6,label:'3連単下書きあり・購入記録なし',link:'/my-tickets',cta:'下書きを確認'};
 return null;
}
function renderNextQueue(items,date){
 const root=$('workNext');root.replaceChildren();
 if(!items.length){
  root.append(create('p','対応候補はありません。資料未取込のRは準備済みではありません。JRA公式で開催と出馬表を確認してな。'));
  return;
 }
 items.sort((a,b)=>a.action.priority-b.action.priority||a.race-b.race||
  TRACKS.indexOf(a.track)-TRACKS.indexOf(b.track));
 for(const item of items.slice(0,6)){
  const div=create('div');div.className='queue-row'+(item.action.priority===0?' queue-alert':'');
  const name=create('strong',item.track+item.race+'R｜'+item.action.label);
  const explanation=create('p','端末内の資料から判断。JRA出走確定・取消・公式時刻は別途確認。');
  const link=create('a',item.action.cta);
  link.href=item.action.link==='/jrdb-mail-local'?item.action.link:
   jumpUrl(item.action.link,date,item.track,item.race);
  div.append(name,link,explanation);root.append(div);
 }
 if(items.length>6)root.append(create('p','ほか'+(items.length-6)+'R。各競馬場の一覧から選んでな。'));
}
function render(){
 $('workMeetings').replaceChildren();
 $('workNext').replaceChildren();
 $('workSummary').textContent='';
 $('workLedger').textContent='';
 const date=$('workDate').value;
 if(!validDate(date)){$('workStatus').textContent='正しい日付を選んでな。';return;}
 try{
  const data=readData(),venues=tracksFor(data,date);
  current={data,date};
  $('workLedger').textContent=summarizePurchases(data,date);
  if(!venues.length){
   renderNextQueue([],date);
   $('workStatus').textContent='この開催日の保存資料がありません。想定メールを取り込むか、競馬場を追加表示してな。';
   $('workSummary').textContent='表示0R';
   return;
  }
  let rows=0,countMail=0,countMemo=0,countGrade=0,countTicket=0,countActual=0,stale=0,reviewQueue=0;
  const nextItems=[];
  for(const venue of venues){
   const section=create('section');section.className='venue';
   const head=create('h3',venue+'｜1R〜12R');
   const grid=create('div');grid.className='race-grid';
   const detail=create('div');
   detail.className='race-detail';detail.textContent='確認したいRをタップしてな。';
   section.append(head,grid,detail);
   for(let race=1;race<=12;race++){
    const s=raceStatus(data,date,venue,race);
    const action=nextAction(s);
    if(action)nextItems.push({track:venue,race,action});
    countMail+=Number(s.source);countMemo+=Number(s.matching);
    countGrade+=Number(s.graded);countTicket+=Number(s.points>0);
    countActual+=Number(s.actual>0);stale+=Number(s.stale);
    reviewQueue+=Number(s.reviewPending>0);
    const tile=create('button');tile.type='button';tile.className='race-btn';
    tile.dataset.stage=s.state;tile.setAttribute('aria-pressed','false');
    tile.hidden=onlyActions&&!action;
    tile.setAttribute('aria-label',venue+race+'R：'+s.label);
    tile.append(create('span',race+'R'),create('small',s.label));
    tile.children[0].className='race-no';
    tile.onclick=()=>{
     for(const btn of grid.children)btn.setAttribute('aria-pressed','false');
     tile.setAttribute('aria-pressed','true');detail.replaceChildren();
     detail.append(create('strong',date+' '+venue+race+'R｜'+s.label),
      create('p',statusText(s)),
      create('p','想定メールの発走情報：'+(s.post||'未取込')+'。公式発走時刻ではありません。'));
     if(s.stale)detail.append(create('p','元の資料に差異があります。馬番メモと評価を再確認してください。'));
     const actions=create('div');actions.className='actions';
     for(const [label,path] of [['評価する','/my-scorecard'],['3連単を作る','/my-tickets']]){
      const a=create('a',label);a.href=jumpUrl(path,date,venue,race);actions.append(a);
     }
     const memoLink=create('a','馬番メモへ');memoLink.href='/jrdb-mail-local';
     actions.append(memoLink);detail.append(actions);
    };
    grid.append(tile);rows++;
   }
   $('workMeetings').append(section);
  }
  renderNextQueue(nextItems,date);
  $('workSummary').textContent=rows+'R表示／JRDB想定'+countMail+'R／馬番メモ一致'+countMemo+
   'R／評価入力完了'+countGrade+'R／3連単下書き'+countTicket+'R／実購入記録'+countActual+
   'R／着順メモ未入力'+reviewQueue+'R／元資料要再確認'+stale+'R';
  $('workStatus').textContent=date+'：'+venues.join('・')+
   'の端末内準備を表示。JRAの出走確定・実際の着順・予想成績の保証ではありません。';
 }catch(e){
  current=null;$('workMeetings').replaceChildren();
  $('workLedger').textContent='購入記録の集計を停止しました。バックアップを保管して内容を確認してください。';
  $('workStatus').textContent='端末内の保存資料を読み込めません：'+
   (e instanceof Error?e.message:'保存状態を確認してな。');
  $('workSummary').textContent='不正な記録を無視して「準備完了」とは表示しません。';
 }
}
function nextWeekend(day){
 const date=new Date(Date.now()+9*3600000);
 const add=(day-date.getUTCDay()+7)%7;
 date.setUTCDate(date.getUTCDate()+add);
 return date.toISOString().slice(0,10);
}
$('workOnlyActions').onclick=()=>{
 onlyActions=!onlyActions;
 $('workOnlyActions').setAttribute('aria-pressed',String(onlyActions));
 $('workOnlyActions').textContent='作業対象Rだけ表示：'+(onlyActions?'ON':'OFF');
 render();
};
$('workReload').onclick=()=>{
 render();
 if(current)$('workStatus').textContent+='（端末の保存内容を読み直しました）';
};
// Returning from a scorecard or 3連単 in Safari may restore this page from BFCache.
// Refresh only read-only status on navigation return. No setItem, fetch or upload.
if(typeof window!=='undefined'&&window.addEventListener)
 window.addEventListener('pageshow',e=>{if(e.persisted)render()});
$('workSaturday').onclick=()=>{$('workDate').value=nextWeekend(6);additions=new Set();render()};
$('workSunday').onclick=()=>{$('workDate').value=nextWeekend(0);additions=new Set();render()};
$('workDate').onchange=()=>{additions=new Set();render()};
$('workAddTrack').onclick=()=>{
 const value=$('workExtraTrack').value;
 if(!TRACKS.includes(value)){$('workStatus').textContent='追加表示する競馬場を選んでな。';return;}
 if(additions.size>=3||((current&&tracksFor(current.data,$('workDate').value).length)>=3&&
  !tracksFor(current.data,$('workDate').value).includes(value))){
  $('workStatus').textContent='一度に表示できるのは最大3競馬場・36Rです。';return;
 }
 additions.add(value);render();
};
try{
 const stored=readData(),today=jstDate(),dates=new Set();
 for(const k of KEYS)for(const x of stored[k])if(validDate(x.date))dates.add(x.date);
 const upcoming=[...dates].filter(x=>x>=today).sort();
 $('workDate').value=upcoming[0]||nextWeekend(6);
}catch(_){$('workDate').value=nextWeekend(6)}
render();
})();"""
