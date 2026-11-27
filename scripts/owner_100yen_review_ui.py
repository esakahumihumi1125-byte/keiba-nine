"""Owner-only, read-only frozen 100-yen hypothetical review page.

Only derived statistics leave the server; no source rows, paid provider data,
purchase records, credentials or snapshots are saved by this UI.
"""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>ARC RACE｜100円仮想収支</title>
<link rel="stylesheet" href="/owner-100yen-review.css"></head><body><main>
<nav><a href="/">← 本人用ホーム</a><a href="/owner-jrdb-day-research">全R研究へ</a></nav>
<h1>ARC RACE <small>本人用・100円仮想収支</small></h1>
<p class="notice"><strong>実購入・実際の払戻ではありません。</strong>
発走前に保存・固定された買い目のみ1点100円で仮購入した計算です。
公式結果を独立確認できないレースは「結果待ち」のまま保留し、
投資額・回収率の確定値に混ぜません。過去の買い目を後から作ったり変更したりしません。</p>
<section><label for="day">開催日</label><input id="day" type="date">
<div class="weekend-actions">
<button id="recentSaturday" type="button">直近の土曜を確認</button>
<button id="recentSunday" type="button">直近の日曜を確認</button>
</div>
<button id="load" type="button">この日の100円仮想収支を確認</button>
<p class="muted">直近の土日ボタンは日付選択と保存済み記録の再表示だけ。変則開催は日付を選んでください。新しいJRDBの有料照会や予想・購入はしません。</p>
<p id="status" class="muted" role="status">開催日を選んで確認してください。</p><p class="muted">端末内だけの固定記録は、別端末・ブラウザでは見られない場合があります。<a href="/owner-backup">発走前記録のバックアップ・復元</a></p></section>
<section><h2>全体の集計</h2>
<div id="summary" class="summary"></div><p class="muted" id="coverage"></p></section>
<section><h2>競馬場別</h2><div id="venue"></div></section>
<section><h2>各レース</h2><div id="races"></div></section>
<section><h2>JRDB暫定着順との参考比較（任意）</h2>
<p class="muted">発走前に固定したサーバー署名付き3連単だけを、JRDBのレース後暫定着順と比較します。押したときだけJRDB成績を最大1回取得。JRA公式の的中判定・払い戻し・100円仮想収支とは完全に別です。同着・取消・不完全資料は判定保留にします。</p>
<button id="provisionalCheck" type="button">固定3連単とJRDB暫定着順を参考照合</button>
<p id="provisionalStatus" class="muted" role="status">まだ照合していません。自動で成績APIは呼びません。</p>
<div id="provisionalRaces"></div></section>
<section id="providerPayoffReference"><h2>JRDB払戻で100円仮想収支を参考照合</h2>
<p class="muted">発走前に保存した署名付き研究用3連単だけを、JRDBの払戻資料（/thj）と照合します。<strong>実購入・JRA公式独立確認・正式な回収率ではありません。</strong>欠損・返還・組番が読めない場合は保留にします。ここを押した時だけJRDBを最大1回照会。既存記録は変更しません。</p>
<button id="thjCheck" type="button">保存した3連単の仮想払戻を照合（1回）</button>
<p id="thjStatus" class="muted" role="status">未実行。JRDBへの払戻照会はしていません。</p>
<div id="thjSummary" class="summary"></div><p id="thjCoverage" class="muted"></p><div id="thjVenues"></div><div id="thjRaces"></div>
</section>
<details id="jraResultCandidatePanel"><summary>JRAの結果ページを1Rだけ読み取る（候補・任意）</summary>
<p class="muted">JRAのレース結果ページのURLを公式サイトからコピーして入力してください。当日または過去の公開済み結果から選択した1Rを1回確認し、<b>同じ日の署名付き発走前3連単があれば、候補の組み合わせと参考比較</b>します。固定記録がない場合はJRA形式の候補だけ表示。公式結果の最終認証・返還確認・的中証明は未完成で、仮想収支には加算しません。</p>
<label for="jraResultMode">比較する発走前固定予想</label>
<select id="jraResultMode"><option value="legacy">従来の2項目固定予想</option><option value="research79">5項目79点（この端末の固定予想）</option></select>
<p class="muted">2方式を混ぜず、選択した予想だけを比較します。</p>
<label for="jraResultTrack">競馬場</label>
<select id="jraResultTrack">
<option value="">競馬場を選択</option>
<option>札幌</option><option>函館</option><option>福島</option><option>新潟</option><option>東京</option><option>中山</option><option>中京</option><option>京都</option><option>阪神</option><option>小倉</option>
</select>
<label for="jraResultRace">レース</label><input id="jraResultRace" type="number" min="1" max="12" step="1" value="1">
<label for="jraResultUrl">JRA公式結果ページのURL</label>
<input id="jraResultUrl" type="url" maxlength="500" inputmode="url" spellcheck="false" autocomplete="off" placeholder="https://www.jra.go.jp/JRADB/accessS.html?CNAME=...">
<p class="muted"><a href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式サイトで結果ページを探す</a>（このリンクでは自動照会しません）</p>
<button id="jraResultCheck" type="button">JRA結果候補と固定3連単を参考照合（1回）</button>
<p id="jraResultStatus" class="muted" role="status">未実行。ここを開くだけではJRAへ照会しません。</p>
<div id="jraResultCandidates"></div>
</details>
<p class="muted">表示専用です。予想・購入・記録・JRDBの原資料は変更しません。
公式結果の自動取り込みが未完成の場合、仮想回収率は未確定のまま表示されます。</p>
</main><script src="/owner-100yen-review.js?v=20261127-r79-jra" defer></script></body></html>"""

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
input,button,select{display:block;width:100%;padding:12px;margin:8px 0;font:inherit;border-radius:9px;min-height:46px}
input{background:#092034;color:#eef4ff;border:1px solid #8297ad}select{background:#092034;color:#eef4ff;border:1px solid #8297ad}details{margin:14px 0;padding:12px;background:#142b43;border:1px solid #496782;border-radius:14px}details summary{cursor:pointer;font-weight:800;color:#edce87;min-height:40px}
button{background:#e8ca83;color:#172a3d;border:0;font-weight:800}button:disabled{opacity:.5}
.weekend-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}
.weekend-actions button{background:#254963;color:#eef6ff;border:1px solid #527994;font-size:13px}
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
  v.races.length>36||!Number.isSafeInteger(v.totalInvestedYen)||
  v.totalInvestedYen<0||!Number.isSafeInteger(v.pendingStakeYen)||
  v.pendingStakeYen<0||!Number.isSafeInteger(v.totalReturnedYen)||
  v.totalReturnedYen<0)throw Error('集計形式が一致しません');
 return v;
}
function clear(){for(const k of ['summary','venue','races'])$(k).replaceChildren();
 $('coverage').textContent='';}
function draw(input){
 const v=check(input),total=$('summary');clear();
 total.append(stat('結果確認済み',v.reviewedRaces+'R'),
  stat('結果待ち',v.pendingRaces+'R'),
  stat('固定済み100円仮想投資（結果待ち含む）',
   yen(v.totalInvestedYen+v.pendingStakeYen)),
  stat('仮想投資（結果確認済みのみ）',yen(v.totalInvestedYen)),
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
    !Number.isInteger(input.provisionalFirstCandidateCount)||
    !Number.isInteger(input.provisionalSecondCandidateCount)||
    !Number.isInteger(input.provisionalThirdCandidateCount)||
    !Number.isInteger(input.provisionalAllThreeSlotsCount)||
    !Number.isInteger(input.provisionalCombinationGapCount)||
    [input.provisionalFirstCandidateCount,
     input.provisionalSecondCandidateCount,
     input.provisionalThirdCandidateCount,
     input.provisionalAllThreeSlotsCount,
     input.provisionalCombinationGapCount,
     input.provisionalExactCombinationCount].some(n=>n<0||n>input.observedRaceCount))
  throw Error('暫定比較の検証不可');
 const seen=new Set();let observed=0,exact=0,first=0,second=0,third=0,
  allSlots=0;
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
   second+=Number(race.secondCandidateObserved);
   third+=Number(race.thirdCandidateObserved);
   allSlots+=Number(race.firstCandidateObserved&&
     race.secondCandidateObserved&&race.thirdCandidateObserved);
  }else if(race.firstMissType!==null)throw Error('判定保留に矛盾');
 }
 if(seen.size!==expected.size)throw Error('固定Rの比較対象が欠落');
 if(input.observedRaceCount!==observed||
    input.pendingRaceCount!==input.raceCount-observed||
    input.provisionalExactCombinationCount!==exact||
    input.provisionalFirstCandidateCount!==first||
    input.provisionalSecondCandidateCount!==second||
    input.provisionalThirdCandidateCount!==third||
    input.provisionalAllThreeSlotsCount!==allSlots||
    input.provisionalCombinationGapCount!==allSlots-exact||
    (input.providerReadCount===0&&observed!==0))
  throw Error('暫定着順の件数不一致');
 return input;
}
function localRecordCoverageNote(day,serverReceipts){
 // Read-only diagnostics. Never merge different storage/signing domains,
 // and never interpret a local signature-shaped value as authenticated.
 try{
  const raw=localStorage.getItem(LOCKED_STORAGE);
  if(!raw)return '';
  if(raw.length>650000)throw Error('size');
  const all=JSON.parse(raw);
  if(!Array.isArray(all)||all.length>360)throw Error('shape');
  const chosen=all.filter(x=>x?.snapshot?.date===day);
  if(!chosen.length)return '';
  expectedPreliminaryRaces(chosen,day);
  const server=new Map(serverReceipts.map(x=>[
   x.snapshot.track+'|'+x.snapshot.race,x.signature]));
  let localOnly=0,different=0;
  for(const x of chosen){
   const k=x.snapshot.track+'|'+x.snapshot.race;
   if(!server.has(k))localOnly++;
   else if(server.get(k)!==x.signature)different++;
  }
  return localOnly||different?
   ' 端末側に別の記録候補 '+localOnly+'R、署名が異なる同一R '+different+
   'Rがあります（未検証）。今回の集計に混ぜず、バックアップ画面で確認してください。':'';
 }catch(_){return ' 端末側の記録形式を確認できません。サーバー記録のみを使用します。';}
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
   return {receipts:record.receipts,source:'サーバー固定',
    coverageNote:localRecordCoverageNote(day,record.receipts)};
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
 return {receipts:chosen,source:'この端末の固定',coverageNote:' 端末内の記録のみ。別端末の記録は含みません。'};
}
function showPreliminary(data){
 const p=$('provisionalRaces');p.replaceChildren();
 p.append(el('p','JRDB暫定着順で比較できた '+data.observedRaceCount+
  'R／保留 '+data.pendingRaceCount+'R。'+
  '1着候補 '+data.provisionalFirstCandidateCount+'R／'+
  '2着候補 '+data.provisionalSecondCandidateCount+'R／'+
  '3着候補 '+data.provisionalThirdCandidateCount+'R。'+
  '全着順が候補枠内 '+data.provisionalAllThreeSlotsCount+'R／'+
  'そのうち組合せ漏れ '+data.provisionalCombinationGapCount+'R／'+
  '3連単の参考一致 '+data.provisionalExactCombinationCount+'R。'+
  'これはJRDB暫定比較で、公式的中率・払戻ではありません。','muted'));
 const reason={first_candidate:'1着候補内',wrong_slot:'勝ち馬を2・3着候補に配置',
  not_selected:'勝ち馬を候補から除外'};
 for(const race of data.races){
  const status=race.providerStatus==='pending'?'暫定着順未成立・保留':
    '1着'+(race.firstCandidateObserved?'○':'×')+
    ' 2着'+(race.secondCandidateObserved?'○':'×')+
    ' 3着'+(race.thirdCandidateObserved?'○':'×')+
    '｜3連単の参考一致 '+(race.exactCombinationObserved?'あり':'なし')+
    '｜'+reason[race.firstMissType];
  p.append(el('p',race.track+race.race+'R｜'+status+
   '（JRA公式・払戻は未照合）','muted'));
 }
}
let preliminaryRequest=0;
function clearPreliminary(){
 clearThj();
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
  const {receipts,source,coverageNote}=await signedForPreliminary(day);
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
   'JRA公式の結果・的中・払戻・回収率に加算していません。'+coverageNote;
 }catch(_){
  if(seq===preliminaryRequest)
   $('provisionalStatus').textContent='暫定照合ができませんでした。記録・仮想収支は変更していません。';
 }finally{
  if(seq===preliminaryRequest)btn.disabled=false;
 }
};

const THJ_VERSION='owner-prestart-thj-100yen-reference-1';
let thjRequest=0;
function clearThj(){
 thjRequest++;
 $('thjSummary').replaceChildren();
 $('thjCoverage').textContent='';
 $('thjVenues').replaceChildren();
 $('thjRaces').replaceChildren();
 $('thjStatus').textContent='未実行。JRDBへの払戻照会はしていません。';
 $('thjCheck').disabled=false;
}
function checkThj(raw,day,expected){
 if(!raw||raw.version!==THJ_VERSION||raw.date!==day||
    raw.source!=='jrdb_thj_provider_reference'||raw.unitYen!==100||
    raw.researchOnly!==true||raw.privateOwnerOnly!==true||
    raw.officialJraVerified!==false||raw.payoutOfficiallyVerified!==false||
    raw.actualPurchase!==false||raw.predictionReady!==false||
    raw.changesExistingReceipts!==false||
    raw.writesPersistentResults!==false||
    ![0,1].includes(raw.providerReadCount)||
    !Array.isArray(raw.races)||raw.raceCount!==raw.races.length||
    raw.raceCount!==expected.size||raw.raceCount<1||raw.raceCount>36||
    !Number.isInteger(raw.observedRaces)||!Number.isInteger(raw.pendingRaces)||
    raw.observedRaces+raw.pendingRaces!==raw.raceCount||
    !Number.isInteger(raw.reviewedInvestedYen)||raw.reviewedInvestedYen<0||
    !Number.isInteger(raw.reviewedReturnedYen)||raw.reviewedReturnedYen<0||
    !Number.isInteger(raw.reviewedProfitYen)||
    !Number.isInteger(raw.pendingStakeYen)||raw.pendingStakeYen<0||
    !Number.isInteger(raw.providerMatchedRaces)||raw.providerMatchedRaces<0)
  throw Error('JRDB払戻資料の形式を確認できません');
 const seen=new Set(), allowed=new Set([
  'pending','refund_review','format_review','provider_observed']);
 let observed=0,invested=0,returned=0,pending=0,hits=0;
 for(const r of raw.races){
  const key=r?.track+'|'+r?.race;
  if(seen.has(key)||!Number.isInteger(r?.race)||r.race<1||r.race>12||
     expected.get(key)!==r.trifectaPoints||!allowed.has(r.status)||
     r.officialJraVerified!==false)
   throw Error('JRDB払戻レースを照合できません');
  seen.add(key);
  if(r.status==='provider_observed'){
   if(r.investedYen!==100*r.trifectaPoints||
      !Number.isInteger(r.returnedYen)||r.returnedYen<0||
      !Number.isInteger(r.providerMatchedTickets)||r.providerMatchedTickets<0||
      r.providerMatchedTickets>6||r.providerMatchedTickets>r.trifectaPoints||
      (r.returnedYen===0)!==(r.providerMatchedTickets===0))
    throw Error('JRDB払戻計算に矛盾');
   observed++;invested+=r.investedYen;returned+=r.returnedYen;
   hits+=Number(r.providerMatchedTickets>0);
  }else{
   if(r.investedYen!==null||r.returnedYen!==null||
      r.providerMatchedTickets!==null)
    throw Error('未確定払戻を集計に含めません');
   pending+=r.trifectaPoints*100;
  }
 }
 if(raw.observedRaces!==observed||raw.pendingRaces!==raw.raceCount-observed||
    raw.reviewedInvestedYen!==invested||
    raw.reviewedReturnedYen!==returned||
    raw.reviewedProfitYen!==returned-invested||
    raw.pendingStakeYen!==pending||
    raw.providerMatchedRaces!==hits||
    (raw.providerReadCount===0&&observed!==0)||
    (invested===0?raw.reviewedRoiPercent!==null:
      typeof raw.reviewedRoiPercent!=='number'||
      !Number.isFinite(raw.reviewedRoiPercent)||
      Math.abs(raw.reviewedRoiPercent-returned*100/invested)>0.011))
  throw Error('JRDB払戻合計が一致しません');
 return raw;
}
$('thjCheck').onclick=async()=>{
 if($('thjCheck').disabled)return;
 const day=$('day').value,seq=++thjRequest,button=$('thjCheck');
 $('thjSummary').replaceChildren();$('thjRaces').replaceChildren();
 $('thjCoverage').textContent='';$('thjVenues').replaceChildren();
 if(!validDay(day)){
  $('thjStatus').textContent='開催日を正しく選んでください。';return;
 }
 button.disabled=true;
 $('thjStatus').textContent='固定記録の署名確認後、JRDBの払戻資料を照合中…';
 try{
  const {receipts,source,coverageNote}=await signedForPreliminary(day);
  if(seq!==thjRequest||$('day').value!==day)return;
  const expected=expectedPreliminaryRaces(receipts,day);
  const resp=await fetch('/api/owner-prestart-thj-review',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},
   body:JSON.stringify({date:day,receipts})
  });
  if(!resp.ok)throw Error('JRDB source unavailable');
  const data=checkThj(await resp.json(),day,expected);
  if(seq!==thjRequest||$('day').value!==day)return;
  $('thjSummary').append(
   stat('JRDB払戻確認済み',data.observedRaces+'R'),
   stat('要確認・結果待ち',data.pendingRaces+'R'),
   stat('参考投資（確認済みのみ）',yen(data.reviewedInvestedYen)),
   stat('JRDB参考払戻',yen(data.reviewedReturnedYen)),
   stat('参考収支',data.observedRaces?yen(data.reviewedProfitYen):'未確定'),
   stat('JRDB参考回収率',pct(data.reviewedRoiPercent))
  );
  $('thjCoverage').textContent='固定済み合計 '+yen(data.reviewedInvestedYen+data.pendingStakeYen)+
   '／収支計算対象外 '+yen(data.pendingStakeYen)+'（'+data.pendingRaces+
   'R）。未確定分を不的中や0円払戻とは扱いません。';
  const venues=new Map();
  for(const row of data.races){
   if(!venues.has(row.track))venues.set(row.track,{done:0,pending:0,stake:0,returned:0,held:0,hits:0});
   const v=venues.get(row.track);
   if(row.status==='provider_observed'){
    v.done++;v.stake+=row.investedYen;v.returned+=row.returnedYen;
    v.hits+=Number(row.providerMatchedTickets>0);
   }else{v.pending++;v.held+=100*row.trifectaPoints;}
  }
  for(const [track,v] of venues){
   const section=el('div',undefined,'stat');
   section.append(el('strong',track),el('p','確認 '+v.done+'R／保留 '+v.pending+
    'R／候補一致 '+v.hits+'R','muted'),
    el('p','参考投資 '+yen(v.stake)+'／参考払戻 '+yen(v.returned),'muted'),
    el('p','参考収支 '+(v.done?yen(v.returned-v.stake):'未確定')+
     '／参考回収率 '+pct(v.stake?v.returned*100/v.stake:null),'muted'),
    el('p','集計対象外 '+yen(v.held),'muted'));
   $('thjVenues').append(section);
  }
  const labels={pending:'払戻未取得',refund_review:'返還確認が必要',
   format_review:'組番形式確認が必要',provider_observed:'JRDB払戻資料あり'};
  for(const row of [...data.races].sort((a,b)=>a.track.localeCompare(b.track,'ja')||a.race-b.race)){
   $('thjRaces').append(el('p',row.track+' '+row.race+'R｜'+
     labels[row.status]+'｜3連単 '+row.trifectaPoints+'点'+
     (row.status==='provider_observed'?
      '｜参考払戻 '+yen(row.returnedYen):'｜仮想収支は保留'),'muted'));
  }
  $('thjStatus').textContent=source+' '+data.raceCount+'Rを対象にJRDB払戻'+
    data.observedRaces+'Rを参考照合。未確定'+data.pendingRaces+
    'Rは収支から除外。JRA公式結果は独立未確認、実購入なし。'+
    '保存済みの3連単・正式収支には反映していません。'+coverageNote;
 }catch(_){
  if(seq===thjRequest)
   $('thjStatus').textContent='JRDB払戻を安全に照合できませんでした。'+
     '買い目・保存済み記録・正式収支は変更していません。';
 }finally{if(seq===thjRequest)button.disabled=false;}
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

// Public official-site observation is deliberately distinct from
// independent JRA certification, immutable prestart picks and simulated ROI.
const JRA_PROBE_VERSION='owner-jra-public-result-probe-1';
const JRA_TRACKS=new Set(['札幌','函館','福島','新潟','東京','中山',
 '中京','京都','阪神','小倉']);
let jraCandidateRequest=0;
function clearJraCandidate(){
 jraCandidateRequest++;
 $('jraResultCandidates').replaceChildren();
 $('jraResultStatus').textContent='未実行。新しい結果候補の照会はしていません。';
 $('jraResultCheck').disabled=false;
}
function validateJraCandidate(obj,day,track,race){
 if(!obj||obj.version!==JRA_PROBE_VERSION||
    obj.date!==day||obj.track!==track||obj.race!==race||
    obj.sourceHostAllowlisted!==true||
    obj.visibleRaceIdentityMatched!==true||
    obj.payoutLayoutParsed!==true||obj.podiumChecked!==true||
    obj.payoutMatchesDisplayedPodium!==true||
    obj.officialJraVerified!==false||
    obj.sourceAuthenticityAttested!==false||
    obj.finalityVerified!==false||obj.refundsVerified!==false||
    obj.settlementReady!==false||obj.officialRoiPercent!==null||
    obj.actualPurchase!==false||obj.researchOnly!==true||
    obj.changesExistingReceipts!==false||
    obj.changesExistingRoi!==false||obj.sourceReadCount!==1||
    !Array.isArray(obj.trifectaCandidates)||
    !Array.isArray(obj.trioCandidates)||
    obj.trifectaCandidates.length<1||obj.trifectaCandidates.length>18||
    obj.trioCandidates.length<1||obj.trioCandidates.length>18||
    !['single_third_place','third_place_dead_heat',
      'first_place_dead_heat','second_place_dead_heat'].includes(obj.podiumShape)||
    obj.matchingTrifectaCount!==obj.trifectaCandidates.length||
    obj.matchingTrioCount!==obj.trioCandidates.length)
   throw Error('Unverified result candidate');
 for(const [kind,rows] of [
  ['3連単',obj.trifectaCandidates],['3連複',obj.trioCandidates]]){
  const seen=new Set();
  for(const row of rows){
   if(!row||Object.keys(row).sort().join(',')!=='payoutYen,ticket'||
      !Array.isArray(row.ticket)||row.ticket.length!==3||
      row.ticket.some(n=>!Number.isInteger(n)||n<1||n>18)||
      new Set(row.ticket).size!==3||
      !Number.isInteger(row.payoutYen)||row.payoutYen<100||
      row.payoutYen>1000000000)
    throw Error('Malformed result candidate');
   const normalized=kind==='3連複'
    ?[...row.ticket].sort((a,b)=>a-b):row.ticket;
   if(kind==='3連複'&&row.ticket.join(',')!==normalized.join(','))
    throw Error('Noncanonical trio');
   const key=normalized.join('-');
   if(seen.has(key))throw Error('Repeated result candidate');
   seen.add(key);
  }
 }
 // A displayed podium must imply the same unordered three-horse
 // combinations as the exact 3連単 rows. Independent browser check
 // rejects a forged payout even if the server claims podiumChecked=true.
 const derived=new Set(obj.trifectaCandidates.map(row=>
  row.ticket.slice().sort((a,b)=>a-b).join('-')));
 const reported=new Set(obj.trioCandidates.map(row=>row.ticket.join('-')));
 if(derived.size!==reported.size||derived.size!==obj.trioCandidates.length||
    [...derived].some(key=>!reported.has(key))||
    (obj.podiumShape==='single_third_place'&&obj.trifectaCandidates.length!==1)||
    (obj.podiumShape!=='single_third_place'&&obj.trifectaCandidates.length<2))
  throw Error('Result podium and payout candidate mismatch');
 return obj;
}
// Only the server can confirm an HMAC signed *prestart* receipt.
// Never compare browser-edited picks to public result candidates as an
// apparent hit. This does not certify a JRA result or add virtual returns.
async function matchJraCandidateToResearch79(report,day,track,race,seq){
 const compact=day.replaceAll('-','');
 const raw=localStorage.getItem('keiba-nine-owner-research6-draft-receipts-v1');
 if(raw&&raw.length>2200000)throw Error('Research79 storage size');
 const all=JSON.parse(raw||'[]');
 if(!Array.isArray(all)||all.length>360)throw Error('Research79 storage shape');
 const chosen=all.filter(x=>x?.snapshot?.date===compact&&
  x.snapshot.track===track&&x.snapshot.race===race);
 if(!chosen.length)return {kind:'no_receipt',text:'この端末に選択Rの79点固定予想はありません。結果候補だけ表示しています。'};
 if(chosen.length!==1)throw Error('Duplicate research79 receipt');
 const entry=chosen[0],p=entry.snapshot;
 if(typeof entry.signature!=='string'||!/^[a-f0-9]{64}$/.test(entry.signature)||
    p.version!=='owner-research6-draft-receipt-1'||
    p.sourceKind!=='prestart-unverified-research6-79-draft'||
    p.policyVersion!=='research-6'||p.researchWeight!==79||
    p.remainingUnassessedWeight!==21||p.researchOnly!==true||
    p.officialJraVerified!==false||p.predictionReady!==false||p.actualPurchase!==false||
    !Number.isInteger(p.points)||p.points<1||p.points>40||
    p.amountYen!==p.points*100||!Array.isArray(p.tickets)||p.tickets.length!==p.points||
    p.tickets.some(t=>!Array.isArray(t)||t.length!==3||new Set(t).size!==3||
     t.some(n=>!Number.isInteger(n)||n<1||n>18))||
    !Number.isFinite(Date.parse(p.capturedAt))||!Number.isFinite(Date.parse(p.scheduledOffAt))||
    Date.parse(p.capturedAt)>=Date.parse(p.scheduledOffAt)||Date.now()<Date.parse(p.scheduledOffAt))
  throw Error('Invalid or not yet off research79 receipt');
 const picks=new Set(p.tickets.map(t=>t.join('-')));
 if(picks.size!==p.points)throw Error('Duplicate research79 tickets');
 const res=await fetch('/api/owner-research6-draft-verify',{
  method:'POST',cache:'no-store',credentials:'same-origin',
  headers:{'X-Keiba-Request':'private','Content-Type':'application/json','Accept':'application/json'},
  body:JSON.stringify({date:compact,receipts:chosen})
 });
 if(!res.ok)throw Error('Research79 verification failed');
 const v=await res.json();
 if(seq!==jraCandidateRequest)return null;
 if(!v||v.version!=='owner-research6-draft-verify-1'||v.serverSigned!==true||
    v.recordCount!==1||v.researchOnly!==true||v.privateOwnerOnly!==true||
    v.officialJraVerified!==false||v.independentJraScheduleVerified!==false||
    v.formalPredictionReady!==false||v.resultComparisonReady!==false||
    v.bettingReady!==false||v.actualPurchase!==false||v.autoPurchase!==false)
  throw Error('Contradictory research79 verification');
 const matched=report.trifectaCandidates.filter(x=>picks.has(x.ticket.join('-')));
 const stakeYen=p.points*100,candidateReturnedYen=matched.reduce((sum,row)=>sum+row.payoutYen,0);
 if(!Number.isSafeInteger(candidateReturnedYen)||candidateReturnedYen<0||
    candidateReturnedYen>18000000000)throw Error('Unsafe arithmetic');
 return {kind:'matched',source:'この端末の固定79点研究予想',points:p.points,matched,
  candidateCount:report.trifectaCandidates.length,stakeYen,candidateReturnedYen,
  candidateDifferenceYen:candidateReturnedYen-stakeYen};
}
async function matchJraCandidateToLockedDraft(report,day,track,race,seq){
 const {receipts,source}=await signedForPreliminary(day);
 if(seq!==jraCandidateRequest)return null;
 const expected=expectedPreliminaryRaces(receipts,day);
 const label=track+'|'+race;
 if(!expected.has(label))
  return {kind:'no_receipt',text:'このレースの署名付き発走前3連単は未登録です。結果候補だけ表示しています。'};
 const chosen=receipts.filter(x=>x.snapshot.track===track&&x.snapshot.race===race);
 if(chosen.length!==1)throw Error('Race receipt mismatch');
 const res=await fetch('/api/owner-100yen-verify-receipts',{
  method:'POST',cache:'no-store',credentials:'same-origin',
  headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
           'Accept':'application/json'},
  body:JSON.stringify({date:day,receipts:chosen})
 });
 if(!res.ok)throw Error('Signed receipt verification unavailable');
 const result=await res.json();
 if(seq!==jraCandidateRequest)return null;
 const review=result?.review;
 const raceRow=review?.races?.[0];
 if(result.available!==true||result.serverSigned!==true||
    result.captureAuditVerified!==false||
    result.officialScheduleVerified!==false||
    result.officialFeedConnected!==false||
    review?.actualPurchase!==false||review?.unitYen!==100||
    review?.reviewedRaces!==0||review?.pendingRaces!==1||
    review?.roiPercent!==null||review?.totalInvestedYen!==0||
    review?.totalReturnedYen!==0||
    !Array.isArray(review?.races)||review.races.length!==1||
    raceRow?.date!==day||raceRow?.track!==track||raceRow?.race!==race||
    raceRow?.status!=='pending'||raceRow?.trioPoints!==0||
    raceRow?.trifectaPoints!==expected.get(label))
  throw Error('Unsigned or contradictory receipt review');
 const picks=new Set(chosen[0].snapshot.trifectaTickets.map(x=>x.join('-')));
 if(picks.size!==raceRow.trifectaPoints)throw Error('Ticket count mismatch');
 const matched=report.trifectaCandidates.filter(x=>picks.has(x.ticket.join('-')));
 // Scenario only: a valid prestart HMAC receipt and a non-final,
 // unverified *single-page* JRA payout candidate. Assume no refunds.
 // Never promote this arithmetic to officially settled 100円 ROI.
 const stakeYen=picks.size*100;
 const candidateReturnedYen=matched.reduce((sum,row)=>sum+row.payoutYen,0);
 const candidateDifferenceYen=candidateReturnedYen-stakeYen;
 if(!Number.isSafeInteger(stakeYen)||stakeYen<100||stakeYen>4800||
    !Number.isSafeInteger(candidateReturnedYen)||
    candidateReturnedYen<0||candidateReturnedYen>18000000000||
    !Number.isSafeInteger(candidateDifferenceYen))
  throw Error('Unsafe unverified candidate arithmetic');
 return {kind:'matched',source,points:picks.size,matched,
  candidateCount:report.trifectaCandidates.length,
  stakeYen,candidateReturnedYen,candidateDifferenceYen};
}
// In-flight response belongs to the old selection. Reset on every change,
 // including typing a replacement URL before the first request completes.
 for(const id of ['jraResultMode','jraResultTrack','jraResultRace','jraResultUrl']){
  $(id).onchange=clearJraCandidate;
  $(id).oninput=clearJraCandidate;
 }
 $('jraResultCheck').onclick=async()=>{
 if($('jraResultCheck').disabled)return;
 const seq=++jraCandidateRequest,day=$('day').value,
  track=$('jraResultTrack').value,
  race=Number($('jraResultRace').value),
  url=$('jraResultUrl').value.trim(),mode=$('jraResultMode').value||'legacy',
  button=$('jraResultCheck');
 $('jraResultCandidates').replaceChildren();
 const today=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
 if(!['legacy','research79'].includes(mode)||!validDay(day)||day>today||!JRA_TRACKS.has(track)||
    !Number.isInteger(race)||race<1||race>12||
    url.length>500||!/^https:\/\/(?:www\.jra\.go\.jp|jra\.jp|app\.jra\.jp|sp\.jra\.jp)\/JRADB\/accessS\.html\?CNAME=/.test(url)||
    url.includes('#')){
  $('jraResultStatus').textContent=
   '当日または過去の開催日・競馬場・1〜12Rと、公開済みのJRA公式結果ページのURLを確認してください。';
  return;
 }
 button.disabled=true;
 $('jraResultStatus').textContent='指定したJRA公式ページを1回だけ確認中。固定済みの予想や収支は変更しません。';
 try{
  const query='date='+encodeURIComponent(day)+'&track='+encodeURIComponent(track)+
   '&race='+race+'&url='+encodeURIComponent(url);
  const res=await fetch('/api/jra/result-candidate?'+query,{
   cache:'no-store',credentials:'same-origin',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(!res.ok)throw Error('Official page unavailable');
  const report=validateJraCandidate(await res.json(),day,track,race);
  if(seq!==jraCandidateRequest)return;
  const holder=$('jraResultCandidates');
  holder.append(el('p',track+race+'R｜JRA形式の払戻候補。'+
    '最終確定・返還・実購入・100円仮想収支は未確認。','muted'));
  for(const [name,rows] of [
   ['3連単',report.trifectaCandidates],['3連複',report.trioCandidates]]){
   for(const row of rows){
    holder.append(el('p',name+' '+row.ticket.join('－')+
     '：100円あたり '+yen(row.payoutYen)+'（候補）','muted'));
   }
  }
  // Optional same-tap comparison uses the already saved prestart
  // HMAC receipt. It never triggers JRDB reads or writes results/ROI.
  let matchState='固定済み予想との比較は保留。';
  try{
   const compared=mode==='research79'?
    await matchJraCandidateToResearch79(report,day,track,race,seq):
    await matchJraCandidateToLockedDraft(report,day,track,race,seq);
   if(seq!==jraCandidateRequest)return;
   if(compared?.kind==='matched'){
    matchState=compared.source+'の署名付き3連単'+compared.points+
      '点と比較：結果候補 '+compared.candidateCount+
      '組中、予想内 '+compared.matched.length+'組（未確定）。';
    holder.append(el('p',matchState,'pending'));
    for(const entry of compared.matched)
     holder.append(el('p','候補一致：'+entry.ticket.join('－')+
      '／100円あたり候補払戻 '+yen(entry.payoutYen),'muted'));
    // The amount is NOT an official return, official ROI, actual purchase
    // or an archived result: render transiently for this single race only.
    const difference=(compared.candidateDifferenceYen>=0?'+':'−')+
     yen(Math.abs(compared.candidateDifferenceYen));
    holder.append(el('p',
     '【未確定・参考計算】発走前固定の3連単 '+compared.points+
     '点×100円＝'+yen(compared.stakeYen)+
     '。表示したJRA払戻候補がすべて最終有効・返還0円と仮定した場合、'+
     '参考払戻 '+yen(compared.candidateReturnedYen)+
     '／参考差額 '+difference+'。'+
     '最終結果・返還は未認証。公式回収率と記録には一切算入しません。','pending'));
    if(!compared.matched.length)
     holder.append(el('p',
      '一致する3連単候補はありません（結果が最終確定した証拠ではありません）。','muted'));
   }else if(compared?.kind==='no_receipt'){
    matchState=compared.text;
    holder.append(el('p',matchState,'muted'));
   }
  }catch(_){
   if(seq!==jraCandidateRequest)return;
   holder.append(el('p',
    '署名付き発走前記録を確認できず、予想との一致は判定保留です。','muted'));
  }
  if(seq!==jraCandidateRequest)return;
  $('jraResultStatus').textContent='JRA形式の着順と払戻候補を照合。'+
   matchState+' 正式的中・実購入・仮想収支には反映していません。';
 }catch(_){
  if(seq===jraCandidateRequest)
   $('jraResultStatus').textContent=
    'JRA結果ページの候補を安全に確認できませんでした。'+
    '公式ページを直接確認してください。予想・収支は無変更です。';
 }finally{
  if(seq===jraCandidateRequest)button.disabled=false;
 }
};

let request=0;
function validDay(day){
 if(typeof day!=='string'||!/^20\d{2}-\d{2}-\d{2}$/.test(day))return false;
 const d=new Date(day+'T12:00:00Z');
 return Number.isFinite(d.valueOf())&&d.toISOString().slice(0,10)===day;
}
function recentWeekendDate(targetDay,now=new Date()){
 const tokyo=now.toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
 const d=new Date(tokyo+'T12:00:00Z');
 if(!Number.isFinite(d.valueOf())||!validDay(tokyo))throw Error('日付を確認できません');
 const delta=(d.getUTCDay()-targetDay+7)%7;
 d.setUTCDate(d.getUTCDate()-delta);
 return d.toISOString().slice(0,10);
}
const selected=typeof location!=='undefined'&&typeof location.search==='string'
 ?/^\?date=(20\d{2}-\d{2}-\d{2})$/.exec(location.search):null;
const fromForecast=selected&&validDay(selected[1])?selected[1]:null;
const today=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
const dayOfWeek=new Date(today+'T12:00:00Z').getUTCDay();
$('day').value=fromForecast||recentWeekendDate(dayOfWeek===6?6:0);
$('day').onchange=()=>{
 request++;$('load').disabled=false;clear();
 $('status').textContent='開催日を選んで確認してください。';
 clearPreliminary();clearJraCandidate();
};
function chooseRecentWeekend(weekday){
 $('day').value=recentWeekendDate(weekday);
 $('day').onchange();
 $('load').onclick();
}
$('recentSaturday').onclick=()=>chooseRecentWeekend(6);
$('recentSunday').onclick=()=>chooseRecentWeekend(0);
$('load').onclick=async()=>{
 const seq=++request,day=$('day').value,button=$('load');clear();
 if(!validDay(day)){
  $('status').textContent='開催日を選択してください。';return;}
 button.disabled=true;$('status').textContent='本人用の固定済み予想を確認中…';
 try{
  const {body,signed,serverArchived}=await readReport(day);
  if(seq!==request)return;
  if(!body.available){
   $('status').textContent='この日の発走前固定済み買い目は未登録です（この端末・接続先で未確認）。別端末の記録は未確認です。仮想収支を作成していません。';
   return;
  }
  draw(body.review);
  $('status').textContent=serverArchived?
   '非公開サーバーに保存した署名付き研究記録。公式発走時刻と結果は未照合・実購入ではありません。':
   signed?
    '端末内のサーバー署名付き研究記録。別端末への永続保存とは異なります。公式発走時刻と結果は未照合・実購入ではありません。':
    '保存済みのプレビューを読み込みました。発走前の独立監査・公式結果は未接続です。';
 }catch(_){if(seq===request)$('status').textContent='安全な集計ができませんでした。予想・購入記録には影響しません。';}
 finally{if(seq===request)button.disabled=false;}
};
// Review only already frozen research records. No paid JRDB calls or
// forecast generation, and no storage writes are triggered by opening.
if(document.visibilityState!=='hidden')$('load').onclick();
})();"""
