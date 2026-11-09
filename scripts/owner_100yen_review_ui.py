"""Owner-only, read-only frozen 100-yen hypothetical review page.

Only derived statistics leave the server; no source rows, paid provider data,
purchase records, credentials or snapshots are saved by this UI.
"""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>KEIBA NINE｜100円仮想収支</title>
<link rel="stylesheet" href="/owner-100yen-review.css"></head><body><main>
<nav><a href="/">← 本人用ホーム</a><a href="/owner-jrdb-day-research">全R研究へ</a></nav>
<h1>KEIBA NINE <small>本人用・100円仮想収支</small></h1>
<p class="notice"><strong>実購入・実際の払戻ではありません。</strong>
発走前に保存・固定された買い目のみ1点100円で仮購入した計算です。
公式結果を独立確認できないレースは「結果待ち」のまま保留し、
投資額・回収率の確定値に混ぜません。過去の買い目を後から作ったり変更したりしません。</p>
<section><label for="day">開催日</label><input id="day" type="date">
<button id="load" type="button">この日の100円仮想収支を確認</button>
<p id="status" class="muted" role="status">開催日を選んで確認してください。</p></section>
<section><h2>全体の集計</h2>
<div id="summary" class="summary"></div><p class="muted" id="coverage"></p></section>
<section><h2>競馬場別</h2><div id="venue"></div></section>
<section><h2>各レース</h2><div id="races"></div></section>
<section><h2>JRDB暫定着順との参考比較（任意）</h2>
<p class="muted">発走前に固定したサーバー署名付き3連単だけを、JRDBのレース後暫定着順と比較します。押したときだけJRDB成績を最大1回取得。JRA公式の的中判定・払い戻し・100円仮想収支とは完全に別です。同着・取消・不完全資料は判定保留にします。</p>
<button id="provisionalCheck" type="button">固定3連単とJRDB暫定着順を参考照合</button>
<p id="provisionalStatus" class="muted" role="status">まだ照合していません。自動で成績APIは呼びません。</p>
<div id="provisionalRaces"></div></section>
<p class="muted">表示専用です。予想・購入・記録・JRDBの原資料は変更しません。
公式結果の自動取り込みが未完成の場合、仮想回収率は未確定のまま表示されます。</p>
</main><script src="/owner-100yen-review.js" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}
body{background:#09172b;color:#edf4ff;margin:0;font:15px/1.6 system-ui,sans-serif}
main{max-width:760px;margin:auto;padding:16px 14px 46px}
nav{display:flex;justify-content:space-between;gap:10px}a{color:#edce87}
h1{font-size:25px;color:#edce87;margin:18px 0}
h1 small{display:block;color:#c6d6e7;font-size:13px}
h2{font-size:18px;margin:0 0 12px}
.notice{background:#322e26;color:#ffe5af;padding:12px;border:1px solid #8a794f;border-radius:12px}
section{background:#142b43;border:1px solid #496782;border-radius:14px;padding:14px;margin:14px 0}
label{display:block;font-weight:700}
input,button{display:block;width:100%;padding:12px;margin:8px 0;font:inherit;border-radius:9px;min-height:46px}
input{background:#092034;color:#eef4ff;border:1px solid #8297ad}
button{background:#e8ca83;color:#172a3d;border:0;font-weight:800}button:disabled{opacity:.5}
.summary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.stat{background:#0b2137;border:1px solid #4c6580;border-radius:9px;padding:11px}
.stat small{color:#c5d7e5;display:block;font-size:12px}
.stat strong{display:block;font-size:21px;color:#eacb83;font-variant-numeric:tabular-nums}
.muted{color:#c3d2e2;font-size:13px}.empty{padding:10px 0;color:#c4d1e1}
.table-scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}
td,th{padding:9px 5px;border-bottom:1px solid #405d76;white-space:nowrap;text-align:right}
td:first-child,th:first-child{text-align:left}th{font-size:12px;color:#eace91}
.pending{color:#edce91}.ok{color:#addcc5}
@media(max-width:370px){.summary{grid-template-columns:1fr}td,th{font-size:12px}}
"""

JS = r"""(()=>{'use strict';
const $=id=>document.getElementById(id);
const el=(tag,text,klass)=>{const v=document.createElement(tag);
 if(text!==undefined)v.textContent=String(text);if(klass)v.className=klass;return v;};
const yen=n=>Number.isInteger(n)?n.toLocaleString('ja-JP')+'円':'—';
const pct=n=>typeof n==='number'&&Number.isFinite(n)?n.toFixed(1)+'%':'未確定';
const MISS={
 trifecta_hit:'的中',winner_not_selected:'1着馬を評価外',
 winner_wrong_slot:'1着馬を2・3着に評価',second_not_selected:'2着馬を評価外',
 second_wrong_slot:'2着馬を別着順に評価',
 third_not_selected:'3着馬を評価外',
 third_wrong_slot:'3着馬を別着順に評価',
 combination_missing:'組み合わせ漏れ'
};
function stat(name,value){const x=el('div',undefined,'stat');
 x.append(el('small',name),el('strong',value));return x;}
function table(headers,rows){const root=el('div',undefined,'table-scroll');
 const t=el('table'),thead=el('thead'),hr=el('tr');
 for(const h of headers)hr.append(el('th',h));thead.append(hr);t.append(thead);
 const tbody=el('tbody');for(const values of rows){const tr=el('tr');
  for(const v of values)tr.append(el('td',v));tbody.append(tr);}t.append(tbody);
 root.append(t);return root;}
function check(v){
 if(!v||v.version!=='keiba-100yen-review-1'||v.unitYen!==100||
  v.actualPurchase!==false||!Array.isArray(v.races)||
  !Array.isArray(v.venueBreakdown)||!Number.isInteger(v.reviewedRaces)||
  !Number.isInteger(v.pendingRaces)||v.reviewedRaces+v.pendingRaces!==v.races.length||
  v.races.length>36||typeof v.totalInvestedYen!=='number'||
  typeof v.totalReturnedYen!=='number')throw Error('集計形式が一致しません');
 return v;
}
function clear(){for(const k of ['summary','venue','races'])$(k).replaceChildren();
 $('coverage').textContent='';}
function draw(input){
 const v=check(input),total=$('summary');clear();
 total.append(stat('結果確認済み',v.reviewedRaces+'R'),
  stat('結果待ち',v.pendingRaces+'R'),
  stat('仮想投資（確認済みのみ）',yen(v.totalInvestedYen)),
  stat('仮想払戻（確認済みのみ）',yen(v.totalReturnedYen)),
  stat('仮想収支',v.reviewedRaces?yen(v.totalProfitYen):'未確定'),
  stat('仮想回収率',pct(v.roiPercent)),
  stat('1着候補の的中',v.firstCandidateHits+'/'+v.firstCandidateEligibleRaces+'R'));
 $('coverage').textContent='結果待ち '+yen(v.pendingStakeYen)+'分の買い目は確定集計の対象外。'+v.note;
 if(v.venueBreakdown.length){
  $('venue').append(table(['会場','確認','保留','3連単的中','3連複的中','仮想回収率'],
   v.venueBreakdown.map(x=>[x.track,x.reviewedRaces+'R',x.pendingRaces+'R',
    x.trifectaHits+'R',x.trioHits+'R',pct(x.roiPercent)])));
 }else $('venue').append(el('p','対象となる固定済み買い目はありません。','empty'));
 if(v.races.length){
  $('races').append(table(['レース','状態','3連単点数','3連複点数','3連単の検証','仮想収支'],
   v.races.map(x=>[x.track+x.race+'R',
   x.status==='pending'?'結果待ち':'公式結果を確認',x.trifectaPoints,x.trioPoints,
   x.status==='pending'?'結果待ち':
    !x.trifectaPoints?'3連単なし':
    Object.hasOwn(MISS,x.trifectaMissReason)?MISS[x.trifectaMissReason]:'要再確認',
   x.status==='pending'?'未確定':yen(x.returnedYen-x.investedYen)])));
 }else $('races').append(el('p','この日の発走前固定済み予想はありません。','empty'));
}
const LOCKED_STORAGE='keiba-nine-owner-server-receipts-v1';

const PRELIMINARY='owner-prestart-tse-comparison-1';
// The original signed races and point counts are the *only* expected review
// scope. A silently dropped or extra race cannot pass as complete.
function expectedPreliminaryRaces(receipts,day){
 if(!Array.isArray(receipts)||receipts.length<1||receipts.length>36)
  throw Error('比較する固定記録の件数が不正');
 const expected=new Map();
 const venues=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
 for(const entry of receipts){
  const s=entry?.snapshot;
  if(!s||typeof entry.signature!=='string'||
     !/^[0-9a-f]{64}$/.test(entry.signature)||
     s.date!==day||s.sourceKind!=='prestart-locked'||
     s.actualPurchase!==false||s.scheduleVerified!==false||
     s.predictionVerified!==false||!venues.includes(s.track)||
     !Number.isInteger(s.race)||s.race<1||s.race>12||
     !Array.isArray(s.trifectaTickets)||s.trifectaTickets.length<1||
     s.trifectaTickets.length>48||
     !Array.isArray(s.trioTickets)||s.trioTickets.length!==0)
   throw Error('発走前固定の署名付き3連単形式が不正');
  const key=s.track+'|'+s.race;
  if(expected.has(key))throw Error('比較対象のレースが重複');
  const combos=new Set();
  for(const ticket of s.trifectaTickets){
   if(!Array.isArray(ticket)||ticket.length!==3||
      ticket.some(n=>!Number.isInteger(n)||n<1||n>18)||
      new Set(ticket).size!==3)
    throw Error('固定3連単の形式が不正');
   combos.add(ticket.join('-'));
  }
  if(combos.size!==s.trifectaTickets.length)throw Error('固定3連単が重複');
  expected.set(key,combos.size);
 }
 return expected;
}
function checkedPreliminary(input,day,expected){
 if(!input||input.version!==PRELIMINARY||input.date!==day||
    input.researchOnly!==true||input.privateOwnerOnly!==true||
    input.officialJraVerified!==false||input.independentJraVerified!==false||
    input.payoutVerified!==false||input.roiPercent!==null||
    input.officialHitCount!==null||input.realPredictionReady!==false||
    input.actualPurchase!==false||input.bettingReady!==false||
    input.changesExistingReceipts!==false||
    ![0,1].includes(input.providerReadCount)||
    !Number.isInteger(input.raceCount)||input.raceCount<1||input.raceCount>36||
    !(expected instanceof Map)||input.raceCount!==expected.size||
    !Array.isArray(input.races)||input.races.length!==input.raceCount||
    !Number.isInteger(input.observedRaceCount)||
    !Number.isInteger(input.pendingRaceCount)||
    !Number.isInteger(input.provisionalExactCombinationCount)||
    !Number.isInteger(input.provisionalFirstCandidateCount))
  throw Error('暫定比較の検証不可');
 const seen=new Set();let observed=0,exact=0,first=0;
 for(const race of input.races){
  const id=race?.track+'|'+race?.race;
  if(seen.has(id)||!Number.isInteger(race?.race)||race.race<1||
     race.race>12||!['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'].includes(race.track)||
     !Number.isInteger(race.trifectaPoints)||race.trifectaPoints<1||
     race.trifectaPoints>48||race.officialVerified!==false||
     expected.get(id)!==race.trifectaPoints||
     !['pending','provider_podium_observed'].includes(race.providerStatus))
   throw Error('暫定着順の馬番不一致');
  seen.add(id);
  const yes=race.providerStatus==='provider_podium_observed';
  for(const k of ['firstCandidateObserved','secondCandidateObserved',
                   'thirdCandidateObserved','exactCombinationObserved']){
   if(yes?typeof race[k]!=='boolean':race[k]!==null)
    throw Error('暫定着順の未確定値不正');
  }
  if(yes){
   if(!['first_candidate','wrong_slot','not_selected'].includes(race.firstMissType)||
      (race.firstCandidateObserved!==(race.firstMissType==='first_candidate'))||
      (race.exactCombinationObserved &&
       !(race.firstCandidateObserved&&race.secondCandidateObserved&&race.thirdCandidateObserved)))
    throw Error('暫定比較値の矛盾');
   observed++;
   exact+=Number(race.exactCombinationObserved);
   first+=Number(race.firstCandidateObserved);
  }else if(race.firstMissType!==null)throw Error('判定保留に矛盾');
 }
 if(seen.size!==expected.size)throw Error('固定Rの比較対象が欠落');
 if(input.observedRaceCount!==observed||
    input.pendingRaceCount!==input.raceCount-observed||
    input.provisionalExactCombinationCount!==exact||
    input.provisionalFirstCandidateCount!==first||
    (input.providerReadCount===0&&observed!==0))
  throw Error('暫定着順の件数不一致');
 return input;
}
async function signedForPreliminary(day){
 // Explicit tap only. Prefer original server archive if it exists.
 const r=await fetch('/api/owner-archive-read?date='+encodeURIComponent(day),{
  cache:'no-store',credentials:'same-origin',
  headers:{'X-Keiba-Request':'private','Accept':'application/json'}
 });
 if(!r.ok)throw Error('固定記録の確認ができません');
 const record=await r.json();
 if(record?.archiveEnabled===true){
  if(record.persistentStorageReady!==true||
     !Array.isArray(record.receipts)||
     !Number.isInteger(record.raceCount)||
     record.raceCount!==record.receipts.length||
     record.available!==(record.raceCount>0))
   throw Error('サーバー固定記録の形式が不正');
  if(record.raceCount>0)
   return {receipts:record.receipts,source:'サーバー固定'};
  // When the archive has 0R, older local-only signed records may exist.
  // Never merge receipts signed with different keys into one request.
 }else if(record?.archiveEnabled!==false||record.available!==false||
          record.persistentStorageReady!==false)
  throw Error('固定記録の状態が未確認');
 const raw=localStorage.getItem(LOCKED_STORAGE);
 if(!raw||raw.length>650000)throw Error('この端末に署名付き固定記録なし');
 const all=JSON.parse(raw);
 if(!Array.isArray(all)||all.length>360)throw Error('固定記録形式が不正');
 const chosen=all.filter(x=>x?.snapshot?.date===day);
 if(chosen.length<1||chosen.length>36)throw Error('対象日の固定記録なし');
 return {receipts:chosen,source:'この端末の固定'};
}
function showPreliminary(data){
 const p=$('provisionalRaces');p.replaceChildren();
 p.append(el('p','暫定1〜3着を検出 '+data.observedRaceCount+
  'R／保留 '+data.pendingRaceCount+'R。固定3連単との参考一致 '+
  data.provisionalExactCombinationCount+'R／1着候補にいた '+
  data.provisionalFirstCandidateCount+'R（いずれも未確定・公式的中率ではありません）。','muted'));
 const reason={first_candidate:'1着候補内',wrong_slot:'勝ち馬を2・3着候補に配置',
  not_selected:'勝ち馬を候補から除外'};
 for(const race of data.races){
  const status=race.providerStatus==='pending'?'暫定着順未成立・保留':
    '参考一致 '+(race.exactCombinationObserved?'あり':'なし')+'／'+
    reason[race.firstMissType];
  p.append(el('p',race.track+race.race+'R｜'+status+
   '（JRA公式・払戻は未照合）','muted'));
 }
}
let preliminaryRequest=0;
function clearPreliminary(){
 preliminaryRequest++;
 $('provisionalRaces').replaceChildren();
 $('provisionalStatus').textContent='まだ照合していません。自動で成績APIは呼びません。';
 $('provisionalCheck').disabled=false;
}
$('provisionalCheck').onclick=async()=>{
 const seq=++preliminaryRequest,day=$('day').value,btn=$('provisionalCheck');
 $('provisionalRaces').replaceChildren();
 if(!validDay(day)){
  $('provisionalStatus').textContent='開催日を選び直してください。';return;
 }
 btn.disabled=true;
 $('provisionalStatus').textContent='本人用の固定記録を検証中。JRDB成績は発走後のみ取得します。';
 try{
  const {receipts,source}=await signedForPreliminary(day);
  if(seq!==preliminaryRequest)return;
  const expected=expectedPreliminaryRaces(receipts,day);
  const res=await fetch('/api/owner-prestart-tse-review',{
   method:'POST',cache:'no-store',credentials:'same-origin',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json','Accept':'application/json'},
   body:JSON.stringify({date:day,receipts})
  });
  if(!res.ok)throw Error('成績照合失敗');
  const report=checkedPreliminary(await res.json(),day,expected);
  if(seq!==preliminaryRequest)return;
  showPreliminary(report);
  $('provisionalStatus').textContent=source+'記録 '+expected.size+
   'Rをすべて対象にJRDB暫定着順との参考比較が完了。'+
   'この保存元以外の未固定・別保存レースは含みません。'+
   'JRA公式の結果・的中・払戻・回収率に加算していません。';
 }catch(_){
  if(seq===preliminaryRequest)
   $('provisionalStatus').textContent='暫定照合ができませんでした。記録・仮想収支は変更していません。';
 }finally{
  if(seq===preliminaryRequest)btn.disabled=false;
 }
};

async function readReport(day){
 // A durable private archive wins when configured; if no archived races exist,
 // older local-only signed research receipts remain readable as a fallback.
 const archivedResponse=await fetch(
  '/api/owner-100yen-archived?date='+encodeURIComponent(day),{
   cache:'no-store',credentials:'same-origin',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
 if(!archivedResponse.ok)throw Error('サーバーの保存済み記録を確認できません。');
 const archived=await archivedResponse.json();
 if(archived&&archived.archiveEnabled===true&&archived.available===true){
  return {body:archived,signed:true,serverArchived:true};
 }
 const raw=localStorage.getItem(LOCKED_STORAGE);
 if(raw){
  if(raw.length>650000)throw Error('固定記録が大きすぎます');
  const all=JSON.parse(raw);
  if(!Array.isArray(all)||all.length>360)throw Error('固定記録の形式が違います');
  const selected=all.filter(x=>x&&x.snapshot&&x.snapshot.date===day);
  if(selected.length){
   const res=await fetch('/api/owner-100yen-verify-receipts',{
    method:'POST',credentials:'same-origin',cache:'no-store',
    headers:{'X-Keiba-Request':'private','Content-Type':'application/json','Accept':'application/json'},
    body:JSON.stringify({date:day,receipts:selected})
   });
   const body=await res.json();
   if(!res.ok)throw Error('署名付き記録の検証に失敗しました');
   if(body.serverSigned!==true||body.captureAuditVerified!==false||
      body.officialScheduleVerified!==false||body.officialFeedConnected!==false)
    throw Error('固定記録の検証状態を確認できません');
   return {body,signed:true};
  }
 }
 const res=await fetch('/api/owner-100yen-review?date='+encodeURIComponent(day),{
  cache:'no-store',credentials:'same-origin',
  headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
 const body=await res.json();
 if(!res.ok)throw Error(body.error||'集計を表示できません。');
 return {body,signed:false};
}

let request=0;
function validDay(day){
 if(typeof day!=='string'||!/^20\d{2}-\d{2}-\d{2}$/.test(day))return false;
 const d=new Date(day+'T12:00:00Z');
 return Number.isFinite(d.valueOf())&&d.toISOString().slice(0,10)===day;
}
const selected=typeof location!=='undefined'&&typeof location.search==='string'
 ?/^\?date=(20\d{2}-\d{2}-\d{2})$/.exec(location.search):null;
const fromForecast=selected&&validDay(selected[1])?selected[1]:null;
$('day').value=fromForecast||
 new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
$('day').onchange=()=>{
 request++;$('load').disabled=false;clear();
 $('status').textContent='開催日を選んで確認してください。';
 clearPreliminary();
};
$('load').onclick=async()=>{
 const seq=++request,day=$('day').value,button=$('load');clear();
 if(!validDay(day)){
  $('status').textContent='開催日を選択してください。';return;}
 button.disabled=true;$('status').textContent='本人用の固定済み予想を確認中…';
 try{
  const {body,signed,serverArchived}=await readReport(day);
  if(seq!==request)return;
  if(!body.available){
   $('status').textContent='この日の発走前固定済み買い目は未登録です。仮想収支を作成していません。';
   return;
  }
  draw(body.review);
  $('status').textContent=serverArchived?
   '非公開サーバーに保存した署名付き研究記録。公式発走時刻と結果は未照合・実購入ではありません。':
   signed?
    '端末内のサーバー署名付き研究記録。公式発走時刻と結果は未照合・実購入ではありません。':
    '保存済みのプレビューを読み込みました。発走前の独立監査・公式結果は未接続です。';
 }catch(_){if(seq===request)$('status').textContent='安全な集計ができませんでした。予想・購入記録には影響しません。';}
 finally{if(seq===request)button.disabled=false;}
};
// Review only already frozen research records. No paid JRDB calls or
// forecast generation, and no storage writes are triggered by opening.
if(document.visibilityState!=='hidden')$('load').onclick();
})();"""
