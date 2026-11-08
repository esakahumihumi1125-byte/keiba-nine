"""Owner private iPhone view for automatic JRDB two-factor provisional draft."""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>KEIBA NINE｜本人用・自動暫定予想</title>
<link rel="stylesheet" href="/owner-auto-forecast.css"></head><body><main>
<nav><a href="/">← 本人用ホーム</a><a href="/owner-jrdb-day-research">2項目の根拠</a></nav>
<h1>KEIBA NINE <small>本人用・自動暫定予想</small></h1>
<p class="warning"><strong>実戦用の確定予想ではありません。</strong>
JRDBの調教・近走2項目だけで参考評価と3連単の下書きを自動計算します。
血統・適性・枠・展開・馬場など残り8項目、JRA公式出走取消・発走時刻の照合はまだ未完成。
資料が不足したレースは見送り。実際の投票・購入・記録への保存は一切行いません。</p>
<section>
<label for="autoDay">開催日</label><input id="autoDay" type="date">
<button id="autoRun" type="button">全場・全Rを再分析する</button>
<p class="muted">画面を開いたら本人用の当日分を一度だけ自動取得。
再分析ボタンを押した場合も番組・出走馬・調教・近走を各1回取得します。
バックグラウンド定期取得は未接続。発走済みレースの3連単は後付けで作成しません。</p>
<p id="autoStatus" class="muted" role="status">開催日を選んで自動作成を押してな。</p>
<p id="autoSavedStatus" class="muted" role="status">発走前の買い目は端末内の研究記録として保存できます。実購入の記録とは別です。</p>
<a id="autoReviewLink" href="/owner-100yen-review">固定した研究用買い目を100円仮想収支で確認</a>
</section>
<section>
<h2>全Rの結果</h2><p id="autoSummary" class="muted">未取得</p>
<div id="autoVenues" class="venue-tabs" role="group" aria-label="競馬場を絞り込む"></div>
<div id="autoRaces"></div>
</section>
<p class="muted">Sは金色、Aは赤色。S/A/B/Cは2項目による独自の仮評価で、総合ランクや勝率ではありません。
買い目は重複除外・最大40点・1点100円換算。結果を見てから買い目を作ることはできません。</p>
</main><script src="/owner-auto-forecast.js" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}
body{margin:0;background:#09172b;color:#eff5ff;font:15px/1.55 system-ui,sans-serif}
main{max-width:780px;margin:auto;padding:16px 13px 46px}
h1{font-size:24px;color:#f0d07e;margin:17px 0}
h1 small{display:block;color:#c7d7e7;font-size:13px}
h2{font-size:19px;margin:0 0 10px}
nav{display:flex;justify-content:space-between;gap:12px}a{color:#f0d185}
section{background:#142b43;border:1px solid #4d6b85;border-radius:14px;padding:14px;margin:14px 0}
.warning{background:#342d25;color:#ffe6b5;border:1px solid #9b8052;border-radius:10px;padding:12px;font-size:13px}
.muted{font-size:13px;color:#c3d3e3}
label{display:block;font-weight:700}
input,button{font:inherit;min-height:45px;padding:11px;border-radius:10px;margin:7px 0;width:100%}
input{background:#0c2135;color:white;border:1px solid #90a6b9}
button{background:#e8c774;color:#182b41;border:0;font-weight:800}
button:disabled{opacity:.55}
.venue-tabs{display:flex;flex-wrap:wrap;gap:7px}
.venue-tabs button{flex:1 1 100px;width:auto;background:#2b425b;color:#eaf3ff}
.venue-tabs button[aria-pressed=true]{background:#e8c774;color:#152a3d}
details{border:1px solid #45617e;background:#10263d;border-radius:11px;margin:8px 0;padding:10px}
summary{font-weight:800;color:#f2d596;cursor:pointer;min-height:35px}
.hold{color:#e9bfae;font-size:13px;margin:8px 0}
.runner{display:flex;align-items:center;flex-wrap:wrap;gap:7px;
 background:#213a54;border-radius:9px;padding:8px;margin:6px 0}
.number{font-size:19px;font-weight:850;min-width:44px}
.rank{font-size:12px;min-width:43px;color:#c6d5e7}
.grade{padding:3px 7px;border-radius:6px;background:#3b5065;font-weight:800;font-size:12px}
.S{color:#f3d475}.A{color:#ffa6b1}.B{color:#a4d8ff}.C{color:#dde2ed}
.notes{font-size:12px;color:#c1d3e7;flex-basis:100%}
.formation{background:#192f46;border:1px solid #456582;border-radius:10px;padding:12px;margin:10px 0}
.formation strong{color:#e8ca81}
.formation p{margin:6px 0}
.picks{font-weight:800;color:#f0e4c9;letter-spacing:.02em;overflow-wrap:anywhere}
.ticket-list{font:12px/1.75 system-ui,sans-serif;color:#cbd8e6;overflow-wrap:anywhere}
@media(max-width:380px){.number{min-width:34px}.rank{min-width:35px}}
"""

JS = r"""(()=>{'use strict';
const $=id=>document.getElementById(id);
const GRADES=new Set(['S','A','B','C','未評価']);
const MISSING={
 missing_training_indices:'調教：追切・仕上指数の片方または両方が不足',
 no_linked_training_record:'調教：この馬に照合できる資料なし',
 no_usable_history:'近走：評価に使える過去走なし',
 only_one_usable_run:'近走：使える資料が1走のみ（現基準は2走必要）',
 insufficient_scored_runs:'近走：着順と指数がそろう資料が2走未満',
 no_linked_recent_record:'近走：この馬に照合できる資料なし',
 training_unassessed:'調教：資料不足・理由の再確認が必要',
 recent_unassessed:'近走：資料不足・理由の再確認が必要'
};
function missingText(h){return (Array.isArray(h.missingReasons)?h.missingReasons:[])
 .filter(k=>Object.hasOwn(MISSING,k)).map(k=>MISSING[k]).join('／');}
const RECEIPTS_KEY='keiba-nine-owner-server-receipts-v1';
// Safe, fixed server diagnostics. Do not display raw provider error text.
const FAILURE_STAGE={
 programme:'番組取得・形式確認',entries:'出走馬取得',training:'調教取得',
 recent:'近走取得',day_research:'全レース資料照合',
 draft_generation:'研究用買い目生成',receipt_signing:'発走前記録の署名',
 receipt_archiving:'サーバー記録の固定保存'
};
const FAILURE_KIND={
 provider:'API通信・権限',programme_format:'番組形式',
 source_validation:'資料間の整合性',receipt_guard:'記録の署名検証',
 invalid_data:'資料形式'
};
// Stable server-authored categories only. Never print raw API errors.
const FAILURE_DETAIL={
 bad_request_contract:'日付と番組の契約',server_clock:'サーバー時刻',
 research_header:'全日資料の形式',research_slot:'レース資料形式',
 research_slot_duplicate:'重複・不正なレース資料',
 programme_slot:'番組内のレース形式',
 race_set_mismatch:'番組と分析対象の一致',
 unverified_research:'未確認資料の扱い',
 race_programme_identity:'レース番組の識別',
 race_research_identity:'番組と仮評価の識別',
 formation_size:'買い目点数の検算',other:'未分類の照合条件'
};
const REASONS={
 missing_research:'このレースの資料に不整合あり・自動判定を見送り',
 runner_count_mismatch:'出走頭数が資料と不一致',
 too_few_runners:'4頭未満で候補を作成できない',
 missing_factors:'一部の馬の調教または近走が未評価',
 missing_post_time:'暫定発走時刻を安全に確認できない',
 after_provisional_off:'暫定発走時刻を過ぎたため後付け買い目なし',
 ambiguous_equal_grade_boundary:'同評価の馬が候補の境界にいるため選定保留',
 invalid_two_factor:'このレースの調教・近走の資料検証に不一致があり、安全のため見送り',
 archived_earlier_draft:'このRの別の買い目が先にサーバーへ固定済み。再分析の買い目は表示しません。固定済み記録は100円仮想収支で確認'
};
const SHORT_HOLDS={
 after_provisional_off:'発走済み',missing_factors:'調教・近走不足',
 ambiguous_equal_grade_boundary:'候補同点',missing_research:'資料確認',
 invalid_two_factor:'2項目不整合',runner_count_mismatch:'頭数不一致',
 too_few_runners:'少頭数',missing_post_time:'発走時刻未確認',
 archived_earlier_draft:'既存の固定買い目を優先'
};
const RUNNER_ISSUES={
 contract:'2項目評価の形式',runner_shape:'馬番別資料の形式',
 completeness:'評価済み項目数',rank_order:'評価順位',
 incomplete_rank:'未評価馬の順位',missing_reasons:'未評価の理由',
 summary_count:'評価済み頭数'
};
const MATERIAL_LABELS={
 pedigree:'父・母父',drawWeight:'枠・斤量',rotation:'前走日付',
 personnel:'騎手・厩舎',body:'馬体形状',pastCorner:'過去4角'
};
const POS={
 frontObserved:'過去4角：前方観測',
 backObserved:'過去4角：後方観測',
 mixedObserved:'過去4角：混在',
 insufficient:'過去4角：資料不足'
};
const dom=(tag,value,cls)=>{const d=document.createElement(tag);
 if(value!==undefined)d.textContent=String(value);if(cls)d.className=cls;return d;};
function validate(data,day){
 if(!data||data.version!=='jrdb-owner-auto-draft-1'||data.date!==day||
  data.researchOnly!==true||data.privateOwnerOnly!==true||
  data.officialJraVerified!==false||data.overallPredictionReady!==false||
  data.bettingReady!==false||data.autoPurchase!==false||
  typeof data.archiveEnabled!=='boolean'||
  !Number.isInteger(data.archiveRecordCount)||data.archiveRecordCount<0||
  !Number.isInteger(data.archiveConflictCount)||data.archiveConflictCount<0||
  (data.archiveConflictCount>0&&!data.archiveEnabled)||
  !data.sourceMaterials||
  data.sourceMaterials.version!=='owner-draft-material-coverage-1'||
  !['observed','unavailable'].includes(data.sourceMaterials.status)||
  data.sourceMaterials.officialJraVerified!==false||
  data.sourceMaterials.gradedNewFactors!==0||
  !Array.isArray(data.sourceMaterials.races)||
  (data.sourceMaterials.status==='unavailable'&&
   (data.sourceMaterials.observedFactorSlots!==0||
    data.sourceMaterials.races.length!==0))||
  (data.sourceMaterials.status==='observed'&&
   (data.sourceMaterials.observedFactorSlots!==8||
    data.sourceMaterials.races.length!==data.raceCount))||
  data.sourceReadCount!==4||data.unitYen!==100||
  !Array.isArray(data.races)||data.races.length>120||
  data.raceCount!==data.races.length||
  data.draftCount+data.holdCount!==data.raceCount||
  !data.holdReasons||typeof data.holdReasons!=='object'||
  Array.isArray(data.holdReasons)||
  Object.entries(data.holdReasons).some(([key,n])=>
    !Object.hasOwn(SHORT_HOLDS,key)||!Number.isInteger(n)||
    n<=0||n>data.raceCount)||
  Object.values(data.holdReasons).reduce((total,n)=>total+n,0)!==data.holdCount)
  throw Error('自動暫定予想の形式が不正です');
 const materials=new Map();
 for(const row of data.sourceMaterials.races){
  if(!row||typeof row.track!=='string'||!Number.isInteger(row.race)||
   !Number.isInteger(row.runnerCount)||row.runnerCount<0||row.runnerCount>18||
   !row.counts||Object.keys(row.counts).length!==6||
   Object.keys(MATERIAL_LABELS).some(k=>
     !Number.isInteger(row.counts[k])||row.counts[k]<0||
     row.counts[k]>row.runnerCount)||materials.has(row.track+'|'+row.race))
    throw Error('観測資料の形式が不正です');
  materials.set(row.track+'|'+row.race,row);
 }
 const seen=new Set();
 for(const r of data.races){
  if(!r||!Number.isInteger(r.race)||r.race<1||r.race>12||
   typeof r.track!=='string'||!['hold','provisional_draft'].includes(r.status)||
   r.researchOnly!==true||r.officialJraVerified!==false||
   r.overallPredictionReady!==false||r.bettingReady!==false||
   r.autoPurchase!==false||seen.has(r.track+'|'+r.race)||
   !Array.isArray(r.runners)||r.runners.length>18||
   !Array.isArray(r.first)||!Array.isArray(r.second)||
   !Array.isArray(r.third)||!Array.isArray(r.tickets)||
   r.points!==r.tickets.length||r.points>40||r.amountYen!==r.points*100)
   throw Error('レース別データが不正です');
  seen.add(r.track+'|'+r.race);
  if(data.sourceMaterials.status==='observed'){
   const material=materials.get(r.track+'|'+r.race);
   if(!material||Number.isInteger(r.horseCount)&&
      material.runnerCount!==r.horseCount)
     throw Error('資料とレース頭数が一致しません');
  }
  const numbers=new Set();
  for(const h of r.runners){
   if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
    numbers.has(h.number)||!GRADES.has(h.training)||
    !GRADES.has(h.recent)||!GRADES.has(h.twoFactorGrade)||
    !(h.pastFourthCorner in POS)||
    !(h.twoFactorPoints===null||Number.isInteger(h.twoFactorPoints))||
    !(h.comparisonRank===null||(Number.isInteger(h.comparisonRank)&&h.comparisonRank>=1)))
     throw Error('馬番別データが不正です');
   numbers.add(h.number);
  }
  if(r.status==='hold'){
   if(!Object.hasOwn(REASONS,r.reason)||r.points!==0||
      r.first.length||r.second.length||r.third.length||
      (r.reason==='invalid_two_factor'&&
       (!Object.hasOwn(RUNNER_ISSUES,r.validationIssue)||r.runners.length!==0)))
    throw Error('見送り理由が不正です');
  }else{
   if(r.reason!=='two_factor_only'||r.first.length<2||r.first.length>3||
    r.second.length<=r.first.length||r.second.length>6||
    r.third.length<r.second.length||r.third.length>10||!r.points)
    throw Error('候補が不正です');
   const unique=new Set();
   for(const t of r.tickets){
    if(!Array.isArray(t)||t.length!==3||new Set(t).size!==3||
     !t.every(n=>numbers.has(n))||!r.first.includes(t[0])||
     !r.second.includes(t[1])||!r.third.includes(t[2])||
     unique.has(t.join('-')))throw Error('買い目が不正です');
    unique.add(t.join('-'));
   }
  }
 }
 return data;
}
function runnerView(h,index){
 const p=dom('div',undefined,'runner');
 p.append(dom('span',h.number+'番','number'),
  dom('span',h.comparisonRank===null?'未評価':'仮'+h.comparisonRank+'位','rank'),
  dom('span',h.twoFactorGrade,'grade '+h.twoFactorGrade),
  dom('span','調教 '+h.training,'grade '+h.training),
  dom('span','近走 '+h.recent,'grade '+h.recent),
  dom('span',POS[h.pastFourthCorner]+' ※脚質確定ではない','notes'));
 if(missingText(h))p.append(dom('span',missingText(h),'notes'));
 return p;
}
function formation(r){
 const block=dom('div',undefined,'formation');
 block.append(dom('strong','3連単・2項目だけの研究用自動下書き（1着'+r.first.length+'頭）'),
  dom('p','1着：'+r.first.join('・')+'番','picks'),
  dom('p','2着：'+r.second.join('・')+'番','picks'),
  dom('p','3着：'+r.third.join('・')+'番','picks'),
  dom('p',r.points+'点／1点100円なら'+r.amountYen.toLocaleString('ja-JP')+'円（仮計算・未購入）'),
  dom('p',r.tickets.map(t=>t.join('→')).join(' / '),'ticket-list'));
 return block;
}
function render(input,day){
 const data=validate(input,day);
 const host=$('autoRaces'),tabs=$('autoVenues'),nodes=[],groups=new Map();
 host.replaceChildren();tabs.replaceChildren();
 for(const race of data.races){
  const detail=dom('details'),title=dom('summary',
   race.track+' '+race.race+'R '+
   (race.status==='provisional_draft'?'研究用自動案 '+race.points+'点':'見送り'));
  detail.append(title);
  if(race.status==='hold'){
   const extra=race.reason==='invalid_two_factor'&&
     Object.hasOwn(RUNNER_ISSUES,race.validationIssue)
     ?'（'+RUNNER_ISSUES[race.validationIssue]+'）':'';
   detail.append(dom('p',REASONS[race.reason]+extra,'hold'));
  }
  if(race.runners.length){
   detail.append(dom('p','調教・近走の仮評価順（総合評価ではない）','muted'));
   for(const [i,h] of race.runners.entries())detail.append(runnerView(h,i));
  }
  if(data.sourceMaterials.status==='observed'){
   const item=data.sourceMaterials.races.find(x=>
     x.track===race.track&&x.race===race.race);
   const evidence=Object.entries(MATERIAL_LABELS)
    .map(([key,label])=>label+' '+item.counts[key]+'/'+item.runnerCount)
    .join('／');
   detail.append(dom('p','資料の有無（採点ではない）：'+evidence,'muted'),
    dom('p','コース距離・馬場適性は未接続。調教・近走以外の8項目は未採点。','muted'));
  }else{
   detail.append(dom('p','追加8項目の資料確認は未完了（予想・買い目とは別）。','muted'));
  }
  if(race.status==='provisional_draft')detail.append(formation(race));
  nodes.push({track:race.track,node:detail});
  groups.set(race.track,(groups.get(race.track)||0)+1);
 }
 function show(track){
  const frag=document.createDocumentFragment();
  for(const item of nodes)if(!track||item.track===track)frag.append(item.node);
  host.replaceChildren(frag);
  for(const b of tabs.querySelectorAll('button'))b.setAttribute(
    'aria-pressed',String(b.dataset.track===track));
 }
 for(const track of ['',...groups.keys()]){
  const button=dom('button',track?track+' '+groups.get(track)+'R':'全場 '+data.raceCount+'R');
  button.type='button';button.dataset.track=track;
  button.setAttribute('aria-pressed','false');
  button.onclick=()=>show(track);tabs.append(button);
 }
 show('');
 const breakdown=Object.entries(data.holdReasons).sort((a,b)=>b[1]-a[1])
  .map(([reason,count])=>SHORT_HOLDS[reason]+' '+count+'R').join('／');
 $('autoSummary').textContent=data.raceCount+'R中、研究用自動案 '+data.draftCount+
  'R／見送り '+data.holdCount+'R。'+
  (breakdown?'内訳：'+breakdown+'。':'')+
  'JRDBの2項目だけを買い目に使用。追加資料：'+
  (data.sourceMaterials.status==='observed'?'血統・枠などの材料を確認（採点なし）':'照合保留')+
  '。JRA公式照合や正式な投票は未実施。';
}
function localReceiptStatus(day){
 // Only inspect previously sealed local snapshots. Never treat draft
 // predictions or server response content as actual purchases.
 if(!/^20[0-9]{6}$/.test(day))return '開催日を選択してください。';
 try{
  const raw=localStorage.getItem(RECEIPTS_KEY);
  if(!raw)return 'この開催日の端末内固定済み研究記録はありません。';
  if(raw.length>650000)throw Error('large');
  const values=JSON.parse(raw);
  if(!Array.isArray(values)||values.length>360)throw Error('shape');
  const selected=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
  const ids=new Set();
  for(const entry of values){
   if(!entry||!entry.snapshot||typeof entry.signature!=='string')
    throw Error('receipt');
   const s=entry.snapshot;
   if(s.date===selected){
    if(typeof s.track!=='string'||!Number.isInteger(s.race))
     throw Error('identity');
    ids.add(s.track+'|'+s.race);
   }
  }
  return ids.size?'この開催日の端末内固定済み研究記録 '+ids.size+
   'R。既存の買い目は変更しません。':
   'この開催日の端末内固定済み研究記録はありません。';
 }catch(_){
  return '端末内の固定記録を確認できません。既存データは変更しません。';
 }
}
function saveAutoReceipts(data,day){
 if(data.serverStamped!==true||data.captureAuditVerified!==false||
  !Array.isArray(data.researchReceipts)||data.researchReceipts.length>36||
  data.researchReceiptCount!==data.researchReceipts.length)
  throw Error('署名付き研究記録の形式を確認できません');
 const signed=data.researchReceipts,expectedDay=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 const available=new Map(data.races.filter(r=>r.status==='provisional_draft')
  .map(r=>[r.track+'|'+r.race,r]));
 const seen=new Set();
 for(const row of signed){
  const s=row&&row.snapshot,entry=s&&available.get(s.track+'|'+s.race);
  const id=s&&s.date+'|'+s.track+'|'+s.race;
  if(!s||!entry||seen.has(id)||s.date!==expectedDay||
   s.sourceKind!=='prestart-locked'||s.actualPurchase!==false||
   s.scheduleVerified!==false||s.predictionVerified!==false||
   typeof row.signature!=='string'||!/^[0-9a-f]{64}$/.test(row.signature)||
   !Array.isArray(s.trifectaTickets)||s.trifectaTickets.length!==entry.points||
   !Array.isArray(s.trioTickets)||s.trioTickets.length!==0||
   !s.trifectaTickets.every(t=>Array.isArray(t)&&t.length===3)||
   JSON.stringify(entry.tickets.map(t=>t.join('-')).sort())!==
   JSON.stringify(s.trifectaTickets.map(t=>t.join('-')).sort())||
   typeof s.lockedAt!=='string'||typeof s.scheduledOffAt!=='string')
    throw Error('固定用の研究記録を照合できません');
  seen.add(id);
 }
 if(!signed.length)return localReceiptStatus(day)+
  ' 発走前に新しく固定できる研究用買い目はありません。';
 const raw=localStorage.getItem(RECEIPTS_KEY);
 if(raw&&raw.length>650000)throw Error('端末内の固定記録が上限を超えました');
 const existing=JSON.parse(raw||'[]');
 if(!Array.isArray(existing)||existing.length>360)throw Error('保存済みの記録形式を確認できません');
 const identities=new Set(existing.map(x=>{
  if(!x||!x.snapshot||typeof x.signature!=='string')throw Error('古い記録に不整合があります');
  return x.snapshot.date+'|'+x.snapshot.track+'|'+x.snapshot.race;
 }));
 let added=0;
 const combined=existing.slice();
 for(const receipt of signed){
  const s=receipt.snapshot,id=s.date+'|'+s.track+'|'+s.race;
  if(identities.has(id))continue; // The first research receipt wins.
  identities.add(id);combined.push(receipt);added++;
 }
 if(combined.length>360)throw Error('保存数の上限です');
 if(added)localStorage.setItem(RECEIPTS_KEY,JSON.stringify(combined));
 return '署名付き研究記録：新規 '+added+'R／既存の固定記録は上書きせず維持。'+
  '保存先はこのiPhone内のみ（Safariとホーム画面で別の場合あり）。';
}

let request=0;
$('autoDay').value=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
function updateReviewLink(){
 const day=$('autoDay').value;
 const valid=/^20\d{2}-\d{2}-\d{2}$/.test(day)&&
  !Number.isNaN(new Date(day+'T12:00:00Z').valueOf())&&
  new Date(day+'T12:00:00Z').toISOString().slice(0,10)===day;
 $('autoReviewLink').href='/owner-100yen-review'+
  (valid?'?date='+encodeURIComponent(day):'');
}
$('autoDay').onchange=()=>{
 // Invalidate the old response and unlock the button. A slow old request
 // must not leave the new day permanently disabled on iPhone.
 request++;$('autoRun').disabled=false;
 updateReviewLink();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoSummary').textContent='未取得';
 $('autoSavedStatus').textContent=localReceiptStatus(
  $('autoDay').value.replaceAll('-',''));
 $('autoStatus').textContent='開催日を選んでな。';
};
$('autoRun').onclick=async()=>{
 const button=$('autoRun');
 if(button.disabled)return;
 const seq=++request,day=$('autoDay').value.replaceAll('-','');
 if(!/^20[0-9]{6}$/.test(day)){
  $('autoStatus').textContent='開催日を選択してください。';return;
 }
 button.disabled=true;$('autoStatus').textContent='JRDB資料を一括照合し、自動暫定案を作成中…';
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 try{
  const result=await fetch('/api/jrdb/owner-auto-draft?date='+encodeURIComponent(day),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const body=await result.json();
  if(!result.ok){
   const step=Object.hasOwn(FAILURE_STAGE,body.failureStage)
     ?FAILURE_STAGE[body.failureStage]:null;
   const kind=Object.hasOwn(FAILURE_KIND,body.failureKind)
     ?FAILURE_KIND[body.failureKind]:'未確認';
   const detail=Object.hasOwn(FAILURE_DETAIL,body.failureDetail)
     ?'／条件：'+FAILURE_DETAIL[body.failureDetail]:'';
   throw Error(step?'停止した工程：'+step+'（'+kind+detail+'）。未完成の買い目は表示しません。'
     :'JRDB接続・出走資料・認証状態を確認してください。');
  }
  if(seq!==request)return;
  render(body,day);
  try{
   const localStatus=saveAutoReceipts(body,day);
   $('autoSavedStatus').textContent=body.archiveEnabled
    ?'サーバー固定済み '+body.archiveRecordCount+'R／前の買い目を優先したレース '+
      body.archiveConflictCount+'R。'+localStatus
    :'サーバー保存は未設定。'+localStatus;
  }catch(_){
   $('autoSavedStatus').textContent='研究記録の端末保存はできませんでした。結果表示と実購入記録には影響しません。';
  }
  $('autoStatus').textContent='暫定評価を自動生成しました。作成できないレースは無理に選定していません。';
 }catch(error){if(seq===request){
  const detail=error&&typeof error.message==='string'&&
   error.message.startsWith('停止した工程：')?error.message:null;
  $('autoStatus').textContent=detail||
   '安全な自動生成ができません。JRDB接続・出走資料・認証状態を確認してください。';
  $('autoSummary').textContent='予想は未作成';}}
 finally{if(seq===request)button.disabled=false;}
};
$('autoSavedStatus').textContent=localReceiptStatus(
 $('autoDay').value.replaceAll('-',''));
updateReviewLink();
// Opening the authenticated owner page is the only automatic trigger.
// No timers, background provider polling, or auto-purchase.
if(document.visibilityState!=='hidden')$('autoRun').onclick();
})();"""
