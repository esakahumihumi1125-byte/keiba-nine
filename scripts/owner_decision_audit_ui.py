"""Private, read-only buy-vs-hold research audit from owner preday snapshot.

A manually entered race finish is NOT JRA verification. Results stay ONLY in
browser memory, never sent to the server or stored. No forecast modification,
new provider requests, real betting, or official P/L claims.
"""

HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>ARC RACE｜買う・見送る検証</title>
<link rel="stylesheet" href="/owner-decision-audit.css"></head>
<body><main><nav><a href="/">← ホーム</a> <a href="/owner-preday-forecast">前日参考予想へ</a></nav>
<h1>買い候補・見送りの検証</h1>
<p class="notice"><strong>研究用・結果は自己入力。</strong>保存済みの本人用前日参考予想と、入力した着順を比較します。
結果をJRA公式と自動照合したものではありません。払戻、取消、返還は未検証。
正式な回収率、実際の馬券購入、的中証明ではありません。
<strong>発走前に固定した判断と、現在の参考予想は別扱いにし、結果を見て後から前日予想として固定することはできません。</strong></p>
<section><h2>① 本人用の参考予想</h2>
<p id="sourceStatus" class="muted" role="status">登録済み予想を読み込み中…</p>
<label for="auditDate">検証する開催日</label> <input id="auditDate" type="date">
<button id="loadCaptured" type="button">この日の発走前記録を開く</button>
<button id="freezeDecision" type="button" disabled>残りのレースを発走前に固定</button>
<p id="captureStatus" class="muted" role="status">固定済み記録がない場合は、現在の参考予想との比較のみ可能です。</p>
<p class="muted">固定操作は本人のタップ時のみ。サーバー時刻で発走前のRを署名し、ブラウザ内に最初の記録を保存します。
すでに発走したRは固定しません。公式発走時刻・取消は未照合です。
Safariとホーム画面アプリでは保存領域が別になる場合があります。</p>
</section>
<section><h2>② JRA結果ページから1Rだけ読み取る（任意）</h2>
<p class="muted">JRA公式サイトの<strong>レース結果ページ</strong>のURLをコピーし、対象Rを選択。
本人が「読み取る」を押したときだけ1ページを確認します。表示の着順・払戻は<b>参考候補</b>で、
確定結果や返還・公式認証とは扱いません。<strong>複数の3連単が払われる同着レースは自動転記しません。</strong>
JRAサイトのページ構造が変わった場合も転記を止めます。</p>
<label for="jraAuditRace">比較するレース</label>
<select id="jraAuditRace" aria-label="JRA結果照合の競馬場・レース"></select>
<label for="jraAuditUrl">JRA公式結果ページURL</label>
<input id="jraAuditUrl" type="url" maxlength="500" spellcheck="false" autocomplete="off"
 inputmode="url" placeholder="https://www.jra.go.jp/JRADB/accessS.html?CNAME=...">
<p class="muted"><a href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式サイトから結果ページを探す</a></p>
<button id="jraAuditFetch" type="button" disabled>1Rの結果候補を読み取る</button>
<p id="jraAuditStatus" role="status" class="muted">未実行。JRAへの自動照会・一括取得はしません。</p>
<div id="jraAuditCandidates"></div>
</section>
<section><h2>③ 着順を確認・入力（端末内のみ）</h2>
<p class="muted">1行につき「競馬場・レース番号・1〜3着・3連単100円払戻（任意）」。
例：<code>京都3 13-15-4 701850</code>、<code>福島7 7-3-1 42510</code>。
払戻が不明なら最後の金額は省略してOK。未入力Rは未照合扱いです。</p>
<textarea id="results" rows="7" maxlength="6000" spellcheck="false"
 placeholder="京都3 13-15-4 701850&#10;福島7 7-3-1 42510"></textarea>
<button id="auditButton" type="button" disabled>買い候補と見送りを比較</button>
<button id="clearButton" type="button" class="secondary">入力だけ消す</button>
<p id="status" class="muted" role="status">前日参考予想を取得しています。</p></section>
<section><h2>④ 判断の比較</h2>
<div id="summary"><p class="muted">着順を入力すると検証結果を表示します。</p></div>
<div id="details"></div>
<p class="muted">同着・取消・返還・組番変更の判定はこの画面ではできません。
これらがあるレースはこの入力方式で集計せず、公式結果の確認後に別途照合してください。
自己入力した着順・払戻は通信・保存せず、画面を閉じると消えます。</p></section>
</main><script src="/owner-decision-audit.js" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}
body{font:15px/1.65 system-ui,sans-serif;background:#09172b;color:#eaf2fb;margin:0}
main{max-width:780px;margin:auto;padding:16px 13px 42px}
h1{color:#f3cd79;font-size:23px}h2{font-size:18px}
a{color:#f1d48d;margin-right:10px}nav{margin-bottom:18px}
section{background:#142d48;border:1px solid #547493;border-radius:14px;padding:15px;margin:14px 0}
.notice{padding:14px;border:1px solid #ae9360;border-radius:12px;background:#362a1d}
.muted{color:#c3d0e1;font-size:14px}
input[type=date]{background:#0b2035;color:white;border:1px solid #8faccc;border-radius:8px;font:16px system-ui;padding:7px;max-width:100%}
select,input[type=url]{width:100%;max-width:100%;background:#0b2035;color:white;border:1px solid #8faccc;border-radius:9px;font:16px system-ui;padding:9px;margin:8px 0 12px}
textarea{width:100%;min-height:130px;background:#0b2035;color:white;border:1px solid #8faccc;
border-radius:9px;font:16px/1.5 ui-monospace,monospace;padding:12px}
button{background:#23699d;border:1px solid #7ab2db;border-radius:9px;color:white;
font:600 15px system-ui;padding:11px;margin:9px 6px 0 0}
button:disabled{opacity:.5}.secondary{background:transparent}
.panel{border:1px solid #5a7895;border-radius:10px;padding:10px;margin:10px 0}
.panel strong{color:#f2d38c}code{color:#f8d991}
table{border-collapse:collapse;width:100%}th,td{padding:7px;border-bottom:1px solid #4c6078;text-align:left}
.good{color:#a9e8be}.warn{color:#ffcf9a}.stat{font-weight:700;font-size:20px}
"""

JS = r"""(()=>{'use strict';
const tracks=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
const $=id=>document.getElementById(id);
let forecast=null, activeSource=null, isSigned=false, jraAuditRequest=0;
const CAPTURE_PREFIX='arc-race-owner-decision-capture-v1:';
function parseLine(line){
 const clean=line.normalize('NFKC').replace(/[→－–—−]/g,'-').replace(/[、,，]/g,' ').trim();
 const m=clean.match(/^(札幌|函館|福島|新潟|東京|中山|中京|京都|阪神|小倉)\s*(1[0-2]|[1-9])R?\s+(\d{1,2})[-\s]+(\d{1,2})[-\s]+(\d{1,2})(?:\s+(\d{1,9}))?$/);
 if(!m)throw Error('書式を確認：'+line.slice(0,70));
 const track=m[1],race=Number(m[2]),finish=m.slice(3,6).map(Number);
 if(finish.some(n=>n<1||n>18)||new Set(finish).size!==3)
  throw Error('着順の馬番が不正：'+track+race+'R');
 const payout=m[6]===undefined?null:Number(m[6]);
 if(payout!==null&&(!Number.isSafeInteger(payout)||payout<1||payout>99999999))
  throw Error('払戻金が不正：'+track+race+'R');
 return {track,race,finish,payout};
}
function candidateToInputLine(report, day, track, race){
 // This official-website HTML reader is NOT a verified JRA result feed.
 // It only supplies an unconfirmed candidate into the *manual* review box.
 if(!report||report.version!=='owner-jra-public-result-probe-1'||
    report.date!==day||report.track!==track||report.race!==race||
    report.sourceHostAllowlisted!==true||
    report.visibleRaceIdentityMatched!==true||
    report.payoutLayoutParsed!==true||report.podiumChecked!==true||
    report.payoutMatchesDisplayedPodium!==true||
    report.officialJraVerified!==false||
    report.sourceAuthenticityAttested!==false||
    report.finalityVerified!==false||report.refundsVerified!==false||
    report.settlementReady!==false||
    report.officialRoiPercent!==null||
    report.actualPurchase!==false||report.researchOnly!==true||
    report.sourceReadCount!==1||report.changesExistingReceipts!==false||
    report.changesExistingRoi!==false||
    !Array.isArray(report.trifectaCandidates)||
    !Array.isArray(report.trioCandidates)||
    report.trifectaCandidates.length<1||report.trifectaCandidates.length>18||
    report.trioCandidates.length<1||report.trioCandidates.length>18||
    report.matchingTrifectaCount!==report.trifectaCandidates.length||
    report.matchingTrioCount!==report.trioCandidates.length)
  throw Error('JRA形式の結果候補を安全に検査できませんでした。');
 const used=new Set();
 for(const row of report.trifectaCandidates){
  if(!row||!Array.isArray(row.ticket)||row.ticket.length!==3||
     row.ticket.some(n=>!Number.isInteger(n)||n<1||n>18)||
     new Set(row.ticket).size!==3||
     !Number.isInteger(row.payoutYen)||row.payoutYen<100||
     row.payoutYen>1000000000)
   throw Error('3連単の組番・候補払戻が不正です。');
  const key=row.ticket.join('-');
  if(used.has(key))throw Error('結果候補の重複を検出しました。');
  used.add(key);
 }
 // Multiple winning trifectas can indicate dead heats; the single-line
 // entry widget cannot safely preserve them, so require separate review.
 if(report.podiumShape!=='single_third_place'||
    report.trifectaCandidates.length!==1||
    report.trioCandidates.length!==1)
  return {line:null,reason:'同着・複数払戻の可能性があるため自動転記を見送りました。'};
 const row=report.trifectaCandidates[0];
 if(row.payoutYen>99999999)
  return {line:null,reason:'払戻候補が入力上限を超えるため自動転記しません。'};
 const entered=track+race+' '+row.ticket.join('-')+' '+row.payoutYen;
 // Also validate against the input format that will be used for comparison.
 const parsed=parseLine(entered);
 if(parsed.track!==track||parsed.race!==race||
    parsed.finish.join(',')!==row.ticket.join(','))
  throw Error('転記候補の内容が一致しません。');
 return {line:entered,reason:'JRA形式の単一3連単候補です。最終確定・返還は未確認。'};
}
function appendCandidateRow(existing, line){
 if(typeof existing!=='string'||existing.length>6000||
    typeof line!=='string'||!line)
  throw Error('入力欄の形式を確認してください。');
 const parsed=parseLine(line);
 for(const row of existing.split(/\r?\n/)){
  if(!row.trim())continue;
  const previous=parseLine(row);
  if(previous.track===parsed.track&&previous.race===parsed.race)
   throw Error('このレースの着順は入力済みです。既存の入力を上書きしません。');
 }
 const next=[existing.trim(),line].filter(Boolean).join('\n');
 if(next.length>6000)throw Error('入力欄の最大文字数を超えます。');
 return next;
}
function auditForecast(source,typed){
 if(!source||!Array.isArray(source.races)||source.races.length<1||source.races.length>36)
  throw Error('本人用予想の形式が不正です。');
 if(typed.length>6000)throw Error('入力が長すぎます。');
 const lookup=new Map();
 for(const r of source.races){
  if(!tracks.includes(r.track)||!Number.isInteger(r.race)||r.race<1||r.race>12||
     !['買い候補','見送り'].includes(r.status)||!Number.isInteger(r.points)||
     r.points<1||r.points>48||![r.first,r.second,r.third].every(Array.isArray))
   throw Error('予想の対象レースが不正です。');
  const key=r.track+r.race;
  if(lookup.has(key))throw Error('同じ予想レースが重複しています。');
  lookup.set(key,r);
 }
 const lines=typed.split(/\r?\n/).filter(x=>x.trim());
 if(lines.length<1||lines.length>36)throw Error('着順は1〜36レース分を入力してください。');
 const seen=new Set(),items=[];
 for(const line of lines){
  const result=parseLine(line),key=result.track+result.race;
  if(seen.has(key))throw Error('重複した結果：'+key+'R');
  seen.add(key);
  const r=lookup.get(key);
  if(!r)throw Error('この開催日の参考予想にないレース：'+key+'R');
  const [a,b,c]=result.finish;
  const hit=r.first.includes(a)&&r.second.includes(b)&&r.third.includes(c);
  const reason=hit?'3連単内':
    !r.first.includes(a)?'1着候補漏れ':
    !r.second.includes(b)?'2着候補漏れ':'3着候補漏れ';
  items.push({track:r.track,race:r.race,decision:r.status,
              finish:result.finish,payout:result.payout,hit,reason,
              points:r.points,studyStake:r.points*100,
              grossReturn:hit?result.payout||null:0});
 }
 const buckets={buy:{races:0,hits:0,stake:0,knownReturn:0,missingPayout:0},
                hold:{races:0,hits:0,stake:0,knownReturn:0,missingPayout:0}};
 for(const r of items){
  const b=buckets[r.decision==='買い候補'?'buy':'hold'];
  b.races++;b.stake+=r.studyStake;
  if(r.hit){b.hits++;if(r.payout===null)b.missingPayout++;
            else b.knownReturn+=r.payout;}
 }
 return {date:source.date,items,buckets,unreviewed:source.races.length-items.length,
         anyUnknownPayoff:buckets.buy.missingPayout+buckets.hold.missingPayout>0};
}
function capturedToSource(payload){
 if(!payload||payload.schema!=='keiba-nine-owner-decision-receipt-v1'||
   payload.verified!==true||payload.officialScheduleVerified!==false||
   payload.officialResultsVerified!==false||payload.actualPurchase!==false||
   !Array.isArray(payload.captures)||payload.captures.length<1||payload.captures.length>36)
  throw Error('署名済み記録の確認に失敗しました。');
 const races=payload.captures.map(r=>{
  if(r.sourceKind!=='owner-private-prestart-reference'||
     !['買い候補','見送り'].includes(r.decision))
   throw Error('発走前の判断形式が不正です。');
  return {track:r.track,race:r.race,status:r.decision,
          first:r.first,second:r.second,third:r.third,points:r.points};
 });
 return {date:payload.date,races};
}
async function requestDecision(path,body){
 const res=await fetch(path,{
  method:'POST',credentials:'same-origin',cache:'no-store',
  headers:{'Content-Type':'application/json','Accept':'application/json',
           'X-Keiba-Request':'private'},
  body:JSON.stringify(body)
 });
 if(!res.ok)throw Error('サーバー署名・検証に失敗しました。');
 return res.json();
}
function dateJst(){
 const parts=new Intl.DateTimeFormat('en-US',{timeZone:'Asia/Tokyo',
  year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
 const map=Object.fromEntries(parts.map(p=>[p.type,p.value]));
 return map.year+'-'+map.month+'-'+map.day;
}
function stored(day){
 try{
  const raw=localStorage.getItem(CAPTURE_PREFIX+day);
  if(!raw)return [];
  const data=JSON.parse(raw);
  if(!Array.isArray(data)||data.length>36)throw Error('保存済み記録が不正');
  return data;
 }catch(_){throw Error('端末の保存済み署名記録が確認できません。上書きせず、設定を確認してください。');}
}
async function restoreDay(){
 const day=$('auditDate').value;
 activeSource=null;isSigned=false;
 $('auditButton').disabled=true;
 $('results').value='';
 $('summary').replaceChildren(tag('p','入力待ち。','muted'));
 $('details').replaceChildren();
 const saved=stored(day);
 if(saved.length){
  const check=await requestDecision('/api/owner-decision-verify',{
    date:day,captures:saved});
  activeSource=capturedToSource(check);
  isSigned=true;
  $('captureStatus').textContent=day+'｜発走前の署名が検証できた'+
   activeSource.races.length+'Rだけを検証対象にします。未固定Rは含めません。';
 }else if(forecast&&forecast.date===day){
  activeSource=forecast;
  $('captureStatus').textContent=day+'｜発走前の固定記録なし。現在の暫定参考予想との比較のみ。'+
   '発走前に保存済みだった証明にはなりません。';
 }else{
  $('captureStatus').textContent=day+'｜この端末に署名済み記録がなく、'+
    '現在のサーバー予想も対象日ではありません。後からの発走前固定はできません。';
 }
 $('jraAuditRace').replaceChildren();
 if(activeSource){
  for(const row of activeSource.races){
   const opt=document.createElement('option');
   opt.value=row.track+'|'+row.race;
   opt.textContent=row.track+row.race+'R';
   $('jraAuditRace').append(opt);
  }
 }
 $('jraAuditFetch').disabled=!activeSource;
 $('auditButton').disabled=!activeSource;
 $('freezeDecision').disabled=!(forecast&&forecast.date===day&&day>=dateJst());
 $('status').textContent=activeSource?
  (isSigned?'発走前固定済みの判断':'現在の参考予想')+'と自己入力結果を比較できます。':
  '比較対象の予想がありません。';
}
async function freezeDay(){
 const day=$('auditDate').value;
 if(!forecast||forecast.date!==day||day<dateJst())
  throw Error('開催日を確認してください。過去日の発走前固定はできません。');
 const original=stored(day);
 if(original.length){
  // Verify originals BEFORE merging. An invalid/tampered record is never
  // silently overwritten by a newly issued later capture.
  capturedToSource(await requestDecision('/api/owner-decision-verify',{
    date:day,captures:original}));
 }
 const issued=await requestDecision('/api/owner-decision-freeze',{date:day});
 if(issued.schema!=='keiba-nine-owner-decision-receipt-v1'||
    issued.actualPurchase!==false||!Array.isArray(issued.captures))
  throw Error('署名済み発走前記録が不正です。');
 if(!issued.captures.length&& !original.length)
  throw Error('今から発走前に固定できるレースがありません。');
 const seen=new Set(original.map(x=>x.snapshot.track+x.snapshot.race));
 const combined=original.slice();
 for(const entry of issued.captures){
  if(!entry||!entry.snapshot)throw Error('署名されたレース形式が不正です。');
  const key=entry.snapshot.track+entry.snapshot.race;
  if(!seen.has(key)){combined.push(entry);seen.add(key);}
 }
 if(combined.length>36)throw Error('署名済みレース数が上限を超えています。');
 // Verify before writing and preserve first capture per race.
 capturedToSource(await requestDecision('/api/owner-decision-verify',{
    date:day,captures:combined}));
 localStorage.setItem(CAPTURE_PREFIX+day,JSON.stringify(combined));
 await restoreDay();
 $('captureStatus').textContent+=' 追加 '+(combined.length-original.length)+
  'R、既存 '+original.length+'Rは変更なし。取消・公式時刻は未確認。';
}
function tag(name,content,cl){
 const e=document.createElement(name);
 if(content!==undefined)e.textContent=String(content);
 if(cl)e.className=cl;
 return e;
}
function row(parent,title,value){
 const p=tag('p');p.append(tag('strong',title+'：'),tag('span',value));parent.append(p);
}
function renderAudit(report){
 const host=$('summary'),detail=$('details');
 host.replaceChildren();detail.replaceChildren();
 host.append(tag('p',report.date+'｜入力 '+report.items.length+'R・結果未入力 '+report.unreviewed+'R','muted'));
 const table=tag('table'),thead=tag('tr');
 for(const h of ['区分','対象R','的中','仮購入点数相当'])thead.append(tag('th',h));
 table.append(thead);
 for(const [name,b] of [['買い候補',report.buckets.buy],['見送り',report.buckets.hold]]){
  const tr=tag('tr');
  for(const v of [name,b.races,b.hits,Math.round(b.stake/100)+'点'])
   tr.append(tag('td',v));
  table.append(tr);
 }
 host.append(table);
 row(host,'見送りの的中取りこぼし',report.buckets.hold.hits+'R（参考買い目が的中した場合）');
 host.append(tag('p','「買い候補」の的中率・「見送り」の的中率は、入力されたRだけの集計。未入力Rを外れとして数えません。','muted'));
 if(report.anyUnknownPayoff){
  host.append(tag('p','的中した一部Rの払戻が未入力なので、払戻合計は表示しません。','warn'));
 }else{
  const buy=report.buckets.buy,hold=report.buckets.hold;
  row(host,'買い候補の机上払戻',buy.knownReturn.toLocaleString('ja-JP')+'円');
  row(host,'見送りを買ったと仮定した机上払戻',hold.knownReturn.toLocaleString('ja-JP')+'円');
  host.append(tag('p','上記は自己入力払戻と入力済みRだけの比較。取消・返還を差し引いていないため、正式な投資・損益・回収率は出しません。','warn'));
 }
 for(const r of report.items){
  const box=tag('div',undefined,'panel');
  box.append(tag('strong',r.track+r.race+'R｜'+r.decision),
             tag('p','結果入力：'+r.finish.join('→')+'｜'+(r.hit?'組合せ内':'不的中')+'｜'+r.reason,
                 r.hit?'good':'warn'),
             tag('p','参考 '+r.points+'点・'+r.studyStake.toLocaleString('ja-JP')+
                 '円相当（返還未調整）','muted'));
  if(r.decision==='見送り'&&r.hit)
   box.append(tag('strong','見送り的中：購入判断を再点検（後から予想は変更しない）'));
  detail.append(box);
 }
}
// Pure parser/accounting can be verified in Node without a browser or live source.
if(typeof module!=='undefined'&&module.exports){module.exports={parseLine,auditForecast,capturedToSource,candidateToInputLine,appendCandidateRow};return;}
$('jraAuditFetch').addEventListener('click',async()=>{
 if(!activeSource)return;
 const select=$('jraAuditRace').value,day=$('auditDate').value;
 const parts=select.split('|'),track=parts[0],race=Number(parts[1]);
 const url=$('jraAuditUrl').value.trim();
 if(!activeSource.races.some(x=>x.track===track&&x.race===race)){
  $('jraAuditStatus').textContent='検証対象にないレースです。';
  return;
 }
 if(!/^https:\/\/(?:www\.|app\.|sp\.)?jra\.go\.jp\//.test(url)||
    url.length>500||url.includes('#')){
  $('jraAuditStatus').textContent='JRA公式の結果ページURLを確認してください。';
  return;
 }
 const seq=++jraAuditRequest,btn=$('jraAuditFetch');
 btn.disabled=true;
 $('jraAuditCandidates').replaceChildren();
 $('jraAuditStatus').textContent=track+race+'RのJRA形式ページを1回確認しています。'+
   '買い目・固定記録・結果は更新しません。';
 try{
  const q='date='+encodeURIComponent(day)+'&track='+encodeURIComponent(track)+
   '&race='+race+'&url='+encodeURIComponent(url);
  const response=await fetch('/api/jra/result-candidate?'+q,{
   cache:'no-store',credentials:'same-origin',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
  if(!response.ok)throw Error('公式結果ページの候補を読み取れませんでした。');
  const candidate=await response.json();
  const result=candidateToInputLine(candidate,day,track,race);
  if(seq!==jraAuditRequest||day!==$('auditDate').value||
     select!==$('jraAuditRace').value)return;
  for(const r of candidate.trifectaCandidates){
   $('jraAuditCandidates').append(tag('p','3連単の参考候補：'+
    r.ticket.join('→')+'／'+r.payoutYen.toLocaleString('ja-JP')+'円','muted'));
  }
  if(result.line){
   $('results').value=appendCandidateRow($('results').value,result.line);
   $('jraAuditStatus').textContent=track+race+
    'Rの結果候補を着順欄に追加しました。内容を確認して「比較」を押してください。'+
    '最終確定・返還・正式な回収率は未確認です。';
  }else{
   $('jraAuditStatus').textContent=result.reason+' 結果を見直し、入力は保留してください。';
  }
 }catch(e){
  if(seq===jraAuditRequest)
   $('jraAuditStatus').textContent=e.message||'JRA候補の確認に失敗しました。';
 }finally{if(seq===jraAuditRequest)btn.disabled=!activeSource;}
});
$('clearButton').addEventListener('click',()=>{
 $('results').value='';
 $('status').textContent='入力を消しました。予想と購入・記録は変更していません。';
 $('summary').replaceChildren(tag('p','入力待ち。','muted'));
 $('details').replaceChildren();
});
$('auditButton').addEventListener('click',()=>{
 if(!activeSource)return;
 try{
  const report=auditForecast(activeSource,$('results').value);
  renderAudit(report);
  $('status').textContent='本人用参考予想と自己入力した着順の比較が完了。保存・送信なし。';
 }catch(e){$('status').textContent=e.message;}
});
async function load(){
 try{
  const r=await fetch('/api/owner-preday-forecast',{
   cache:'no-store',credentials:'same-origin',
   headers:{'Accept':'application/json','X-Keiba-Request':'private'}});
  if(!r.ok)throw Error('本人用予想を取得できません。');
  const body=await r.json(),f=body.forecast;
  if(body.available!==true||!f||f.sourceKind!=='owner-private-authored-preday'||
    f.predictionReady!==false||f.officialJraVerified!==false||
    f.purchased!==false||!Array.isArray(f.races)||
    !/^\d{4}-\d{2}-\d{2}$/.test(f.date))
   throw Error('安全な本人用参考予想を確認できません。');
  forecast=f;
  $('sourceStatus').textContent=f.date+'｜'+f.races.length+'Rの登録済み参考予想を読込。'
    +' 発走前固定とは別の、現在の参考予想です。';
  if(!$('auditDate').value)$('auditDate').value=f.date;
  await restoreDay();
 }catch(e){
  $('sourceStatus').textContent=e.message;
  $('status').textContent='参考予想が取得できないため集計しません。';
 }
}
$('auditDate').value=dateJst();
$('loadCaptured').addEventListener('click',async()=>{
 try{await restoreDay();}catch(e){$('captureStatus').textContent=e.message;
  $('auditButton').disabled=true;activeSource=null;}
});
$('freezeDecision').addEventListener('click',async()=>{
 const b=$('freezeDecision');b.disabled=true;
 try{await freezeDay();}
 catch(e){$('captureStatus').textContent=e.message;}
 finally{b.disabled=false;}
});
load();
})();"""

# A Node smoke test may extract JS with ast.literal_eval and a DOM stub.
