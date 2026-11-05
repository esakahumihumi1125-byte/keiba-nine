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
<p id="workStatus" role="status" class="hint">端末に保存された資料を確認します。</p></section>
<section><h2>最大36Rの準備状況</h2>
<div id="workSummary" class="summary" role="status"></div>
<div class="legend">未取込／JRDB想定／馬番メモ一致／評価途中／評価入力済／3連単下書き／実購入記録</div>
<div id="workMeetings" aria-label="各競馬場の12R準備"></div></section>
<section><h2>実戦で必要な確認</h2>
<p class="hint">1Rの枠をタップすると、端末内にある資料の段階と、評価・3連単画面へのリンクが出るで。URLには日付・競馬場・Rだけを引き継ぐ。本人の馬名・JRDB本文・買い目・購入情報は送らない。</p>
<div class="quick"><a href="/jrdb-mail-local">JRDB想定メール・馬番メモの取込</a>
<a href="/owner-backup">5種類の記録をバックアップ</a></div>
<p class="warning">発走時刻、出走取消、馬場、馬番、購入締切はJRA公式で別途確認。実購入記録は本人が登録した記録であり、投票・購入の完了確認ではありません。</p>
<a href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式の出馬表を確認</a>
</section>
</main><script defer src="/owner-race-workbench.js"></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#eff4ff;font:15px/1.5 system-ui,sans-serif}main{max-width:760px;margin:auto;padding:18px 12px 48px}h1{font-size:25px}h2{font-size:19px;margin:0 0 10px}a{color:#f5d27c}section{background:#142b44;border:1px solid #4d6885;border-radius:14px;margin:14px 0;padding:14px}.warning{color:#ffe4a9;background:#302b24;border:1px solid #957a4b;padding:11px;border-radius:10px;font-size:13px}.hint{color:#c5d6e7;font-size:13px}.legend{color:#c4d2df;font-size:12px;margin:8px 0 14px}.quick{display:flex;gap:8px;margin:10px 0;flex-wrap:wrap;align-items:center}.quick label{width:100%}.quick a,.quick button{flex:1;min-width:125px;text-align:center}input,select,button{font:inherit;min-height:43px;background:#0b2035;color:white;border:1px solid #8099b4;border-radius:8px;padding:8px}input[type=date]{width:100%}button{cursor:pointer}button:focus-visible,a:focus-visible{outline:2px solid #f2d17d}.summary{color:#f1d481;font-weight:700}.venue{padding:10px;margin:13px 0;background:#0e233a;border:1px solid #46637f;border-radius:11px}.venue h3{margin:2px 0 8px;font-size:17px}.race-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.race-btn{border:1px solid #66768d;padding:6px 3px;min-height:63px;background:#28394c}.race-btn .race-no{display:block;font-weight:800;font-size:15px}.race-btn small{display:block;line-height:1.3;font-size:10px;white-space:normal}.race-btn[data-stage=empty]{color:#c7cbd0}.race-btn[data-stage=mail]{background:#2a3e52}.race-btn[data-stage=roster]{background:#294c52}.race-btn[data-stage=partial]{background:#63512f}.race-btn[data-stage=graded]{background:#31513f}.race-btn[data-stage=draft]{background:#46548a}.race-btn[data-stage=actual]{background:#5a4376}.race-btn[data-stage=stale]{background:#633e3b;color:#ffe8c2}.race-btn[aria-pressed=true]{outline:2px solid #f2d17d;outline-offset:1px}.race-detail{margin-top:12px;border:1px solid #5a7a96;padding:10px;border-radius:9px}.race-detail p{margin:6px 0;font-size:13px}.actions{display:flex;flex-wrap:wrap;gap:8px;margin:9px 0}.actions a{padding:8px;border:1px solid #a4b8c8;border-radius:8px;min-height:39px}.error{color:#ffc1a3}"""

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
let current=null,additions=new Set();
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
function raceStatus(data,date,track,race){
 const m=meetingFor(data,date,track);
 const source=m&&Array.isArray(m.races)&&m.races.find(x=>x.race===race);
 const memo=data[NUMBERS].find(x=>x.date===date&&x.track===track&&x.race===race);
 const note=data[SCORES].find(x=>x.date===date&&x.track===track&&x.race===race);
 const ticket=data[DRAFTS].find(x=>x.date===date&&x.track===track&&x.race===race);
 const actual=data[PURCHASES].filter(x=>x.date===date&&x.track===track&&x.race===race);
 const matching=nameMemoMatches(memo,source);
 const stale=!!(memo&&!matching)||!!(note&&note.sourceMark!==null&&note.sourceMark!==undefined&&
   (!matching||note.sourceMark!==memo.sourceMark));
 const graded=scoreCompleted(note)&&(!note.sourceMark||matching)&&!stale;
 const points=draftPoints(ticket),hasTicket=!!ticket&&points>0;
 const state=stale?'stale':actual.length?'actual':hasTicket?'draft':graded?'graded':note?'partial':
   matching?'roster':source?'mail':'empty';
 const labels={stale:'資料再確認',actual:'購入記録',draft:'3連単下書',graded:'採点入力済',
  partial:'評価途中',roster:'馬番メモ',mail:'JRDB想定',empty:'未取込'};
 return {state,label:labels[state],source:!!source,matching,hasMemo:!!memo,
  hasScore:!!note,graded,stale,points,actual:actual.length,post:source&&source.postTime};
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
  s.actual?'実購入記録：本人入力 '+s.actual+'件（投票完了は未確認）':'実購入記録：なし'
 ].join('／');
}
function render(){
 $('workMeetings').replaceChildren();
 $('workSummary').textContent='';
 const date=$('workDate').value;
 if(!validDate(date)){$('workStatus').textContent='正しい日付を選んでな。';return;}
 try{
  const data=readData(),venues=tracksFor(data,date);
  current={data,date};
  if(!venues.length){
   $('workStatus').textContent='この開催日の保存資料がありません。想定メールを取り込むか、競馬場を追加表示してな。';
   $('workSummary').textContent='表示0R';
   return;
  }
  let rows=0,countMail=0,countMemo=0,countGrade=0,countTicket=0,countActual=0,stale=0;
  for(const venue of venues){
   const section=create('section');section.className='venue';
   const head=create('h3',venue+'｜1R〜12R');
   const grid=create('div');grid.className='race-grid';
   const detail=create('div');
   detail.className='race-detail';detail.textContent='確認したいRをタップしてな。';
   section.append(head,grid,detail);
   for(let race=1;race<=12;race++){
    const s=raceStatus(data,date,venue,race);
    countMail+=Number(s.source);countMemo+=Number(s.matching);
    countGrade+=Number(s.graded);countTicket+=Number(s.points>0);
    countActual+=Number(s.actual>0);stale+=Number(s.stale);
    const tile=create('button');tile.type='button';tile.className='race-btn';
    tile.dataset.stage=s.state;tile.setAttribute('aria-pressed','false');
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
  $('workSummary').textContent=rows+'R表示／JRDB想定'+countMail+'R／馬番メモ一致'+countMemo+
   'R／評価入力完了'+countGrade+'R／3連単下書き'+countTicket+'R／実購入記録'+countActual+
   'R／元資料要再確認'+stale+'R';
  $('workStatus').textContent=date+'：'+venues.join('・')+
   'の端末内準備を表示。JRAの出走確定や予想成績の保証ではありません。';
 }catch(e){
  current=null;$('workMeetings').replaceChildren();
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
