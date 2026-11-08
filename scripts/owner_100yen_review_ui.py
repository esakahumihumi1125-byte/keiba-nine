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
  $('races').append(table(['レース','状態','3連単点数','3連複点数','仮想収支'],
   v.races.map(x=>[x.track+x.race+'R',
   x.status==='pending'?'結果待ち':'公式結果を確認',x.trifectaPoints,x.trioPoints,
   x.status==='pending'?'未確定':yen(x.returnedYen-x.investedYen)])));
 }else $('races').append(el('p','この日の発走前固定済み予想はありません。','empty'));
}
let request=0;
$('day').value=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
$('day').onchange=()=>{request++;clear();$('status').textContent='開催日を選んで確認してください。';};
$('load').onclick=async()=>{
 const seq=++request,day=$('day').value,button=$('load');clear();
 if(!/^20\d{2}-\d{2}-\d{2}$/.test(day)){
  $('status').textContent='開催日を選択してください。';return;}
 button.disabled=true;$('status').textContent='本人用の固定済み予想を確認中…';
 try{
  const res=await fetch('/api/owner-100yen-review?date='+encodeURIComponent(day),{
   cache:'no-store',credentials:'same-origin',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
  const body=await res.json();
  if(!res.ok)throw Error(body.error||'集計を表示できません。');
  if(seq!==request)return;
  if(!body.available){
   $('status').textContent='この日の発走前固定済み買い目は未登録です。仮想収支を作成していません。';
   return;
  }
  draw(body.review);
  $('status').textContent='発走前の固定済み買い目だけを読み込みました。実購入とは別の集計です。';
 }catch(_){if(seq===request)$('status').textContent='安全な集計ができませんでした。予想・購入記録には影響しません。';}
 finally{if(seq===request)button.disabled=false;}
};
})();"""
