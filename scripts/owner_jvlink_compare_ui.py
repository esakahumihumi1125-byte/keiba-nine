"""Private-only local comparison of JRDB editorial reference and sanitized JV-Link output.

The browser reads the Windows file via File API. No network upload or storage
of its contents; /api/owner-preday-forecast supplies only the already private,
non-licensed editorial pick snapshot. Never assert official final starters,
JRA-VAN completeness, ten-factor grading or formal betting readiness.
"""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>ARC RACE｜JRA-VAN × JRDB 研究用照合</title>
<link rel="stylesheet" href="/owner-jvlink-compare.css"></head><body>
<main><nav><a href="/">← ホーム</a> <a href="/owner-preday-forecast">参考予想へ</a></nav>
<h1>JRA-VAN × JRDB｜データ照合</h1>
<p class="warning"><strong>正式10項目予想は未完成です。</strong>
JRDB前日情報由来の参考予想と、本人PCで取得したJRA-VANの研究用候補を
同じ開催日・競馬場・R・予定時刻・距離・芝ダ・参考候補馬番で照合します。
この段階ではJRDB全頭の馬名一致・JRA最終出走・取消・当日馬場・実過去走の網羅性は保証できません。
一致しても馬券購入にはつながりません。</p>
<section><h2>1．JRDB側の参考予想</h2>
<p id="vanJrdb" role="status">本人用の参考予想を確認中…</p></section>
<section><h2>2．JRA-VANの研究用ファイル</h2>
<p>PCの <code>ARC-RACE-private</code> に保存された
<code>jvdata-one-race-YYYYMMDD-xx-xx.json</code> を選択してください。
現状のPCツールは1回につき1R分の研究用ファイルを作ります。</p>
<label for="vanFile">端末内のJRA-VANファイル</label>
<input type="file" id="vanFile" accept=".json,application/json">
<button id="vanCheck" type="button" disabled>1Rの2資料を照合</button>
<p class="small">ファイルの中身はブラウザ内だけで検証します。サーバー・GitHub・Gmailに送信したり、
自動保存したりしません。本人用資料は他人と共有しないでください。</p>
<p id="vanResult" role="status">JRA-VAN実データはまだ未照合です。</p>
<div id="vanDetails"></div></section>
<section><h2>3．正式予想に必要な残りの確認</h2>
<p>この画面だけで完了しないもの：JRA公式の最終出走馬・取消・馬場・発走時刻の照合、
JRDBの調教・展開・血統などの正式10項目の根拠、JRA-VANの過去走情報の網羅性、2社の全頭同一性確認。</p>
<p>異なるレースや不足データは<strong>未確認／保留</strong>。後から見た結果で発走前の予想を書き換えません。</p>
</section>
</main><script src="/owner-jvlink-compare.js" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}
body{margin:0;background:#09172b;color:#eaf2fb;font:15px/1.6 system-ui,sans-serif}
main{max-width:760px;margin:auto;padding:16px 13px 40px}
a{color:#f1cf79;margin-right:12px}h1{font-size:23px;color:#f1d28f}
h2{font-size:18px}section{background:#142d48;border:1px solid #52708f;
border-radius:13px;padding:14px;margin:15px 0}
.warning{background:#332a22;border:1px solid #9b7e4b;border-radius:11px;padding:14px;color:#f3ddb2}
input{max-width:100%;font:16px system-ui;margin:10px 0;padding:10px;border-radius:10px}
button{font:600 15px system-ui;background:#2674b4;border:1px solid #81b4df;
color:white;border-radius:10px;padding:12px;margin:7px 0}
button:disabled{opacity:.45}.small{font-size:13px;color:#c1d0df}
.good{color:#a5e6bc}.warn{color:#ffd19d}code{font-size:13px;overflow-wrap:anywhere}
"""

JS = r"""(()=>{'use strict';
const $=id=>document.getElementById(id);
const TRACKS=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
const VERSION='owner-jvdata-local-day-history-bridge-1';
let forecast=null;
function compareLocalJvWithJrdb(fileData,reference){
 if(!reference||reference.schema!=='keiba-nine-private-preday-review-v1'||
    !/^\d{4}-\d{2}-\d{2}$/.test(reference.date)||
    !Array.isArray(reference.races)||reference.races.length<1||
    reference.races.length>36||reference.sourceKind!=='owner-private-authored-preday'||
    reference.predictionReady!==false||
    reference.officialJraVerified!==false||
    reference.purchased!==false)
  throw Error('本人用のJRDB参考予想が確認できません。');
 if(!fileData||typeof fileData!=='object'||Array.isArray(fileData)||
    fileData.version!==VERSION||fileData.date!==reference.date||
    fileData.raceCount!==1||fileData.privateOwnerOnly!==true||
    fileData.researchOnly!==true||
    fileData.historySource!=='private_jvlink_rcvn_partial_observations'||
    fileData.historyCompletenessVerified!==false||
    fileData.captureTimeIndependentlyVerified!==false||
    fileData.officialStarterListVerified!==false||
    fileData.officialScratchStateVerified!==false||
    fileData.officialGoingVerified!==false||
    fileData.formalTenFactorReady!==false||
    fileData.productionPredictionReady!==false||
    fileData.bettingReady!==false||
    fileData.autoPurchase!==false||fileData.newProviderRequests!==0||
    !Array.isArray(fileData.races)||fileData.races.length!==1)
  throw Error('開催日が違うか、JRA-VAN本人用研究ファイルではありません。');
 const card=fileData.races[0];
 if(!card||!TRACKS.has(card.track)||!Number.isInteger(card.race)||
    card.race<1||card.race>12||
    typeof card.postTimeCandidate!=='string'||
    !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(card.postTimeCandidate)||
    !Number.isInteger(card.distanceMetersCandidate)||
    card.distanceMetersCandidate<400||card.distanceMetersCandidate>10000||
    !['芝','ダート'].includes(card.surfaceCandidate)||
    !Array.isArray(card.byNumber)||card.byNumber.length<3||
    card.byNumber.length>18||card.historyComplete!==false||
    card.graded!==false||card.bettingReady!==false)
  throw Error('JRA-VANの研究用レース情報が不正です。');
 const referenceCard=reference.races.find(r=>r.track===card.track&&r.race===card.race);
 if(!referenceCard)throw Error('同日JRDB参考予想にこの競馬場・Rがありません。');
 const horseNumbers=new Set();
 let observed=0;
 for(const horse of card.byNumber){
  if(!horse||!Number.isInteger(horse.number)||horse.number<1||
     horse.number>18||horseNumbers.has(horse.number)||
     !Number.isInteger(horse.observedRecordCount)||
     horse.observedRecordCount<0||horse.observedRecordCount>20000||
     horse.missingHistoryUnproven!==true||horse.graded!==false||
     !Array.isArray(horse.recentObservedRuns)||
     horse.recentObservedRuns.length>5)
    throw Error('JRA-VANの馬番・過去走候補が不正です。');
  horseNumbers.add(horse.number);
  if(horse.observedRecordCount>0)observed++;
 }
 const course=referenceCard.course;
 const distanceMatch=typeof course==='string' &&
  Number((course.match(/(\d{3,4})M/)||[])[1])===card.distanceMetersCandidate;
 const surfaceMatch=typeof course==='string' &&
  ((course.includes('芝')&&card.surfaceCandidate==='芝')||
   (course.includes('ダ')&&card.surfaceCandidate==='ダート'));
 const postTimeMatch=referenceCard.time===card.postTimeCandidate;
 const runnerCountMatch=referenceCard.field===horseNumbers.size;
 const pickedNumbersPresent=Array.isArray(referenceCard.rank)&&
  referenceCard.rank.length>=3&&referenceCard.rank.every(n=>horseNumbers.has(n));
 const candidateFieldsConsistent=Boolean(distanceMatch&&surfaceMatch&&
  postTimeMatch&&runnerCountMatch&&pickedNumbersPresent);
 return {
  date:fileData.date,track:card.track,race:card.race,
  candidateRunners:horseNumbers.size,
  editorialRunners:referenceCard.field,
  observedHorseHistories:observed,
  checkedRaceCount:1,
  totalEditorialRaces:reference.races.length,
  distanceMatch,surfaceMatch,postTimeMatch,runnerCountMatch,
  pickedNumbersPresent,candidateFieldsConsistent,
  allHorseIdentityMatched:false,
  officialJraVerified:false,
  currentGoingVerified:false,
  scratchesVerified:false,
  formalTenFactorsReady:false,
  bettingReady:false,
  note:candidateFieldsConsistent?
   '候補の頭数・馬番・予定時刻・距離・芝ダに矛盾なし。ただし全頭の同一性と公式情報は未確認。':
   '候補に不一致があるため保留。出走馬・馬番の再確認が必要。'
 };
}
if(typeof module!=='undefined'&&module.exports){
 module.exports={compareLocalJvWithJrdb};return;
}
async function load(){
 try{
  const response=await fetch('/api/owner-preday-forecast',{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
  if(!response.ok)throw Error('本人用参考予想を取得できません。');
  const value=await response.json();
  if(value.available!==true||!value.forecast)throw Error('参考予想がまだ登録されていません。');
  const f=value.forecast;
  // Validate reference contract WITHOUT trying to upgrade its status.
  if(f.sourceKind!=='owner-private-authored-preday'||
     f.predictionReady!==false||f.officialJraVerified!==false||
     !Array.isArray(f.races)||f.races.length<1||f.races.length>36)
   throw Error('本人用参考予想の安全な形式を確認できません。');
  forecast=f;
  $('vanJrdb').textContent=f.date+'｜JRDB前日資料に基づく参考予想'+
   f.races.length+'Rは読み込み済み。JRA-VANとの全頭照合 0/'+f.races.length+'R。';
  $('vanCheck').disabled=false;
 }catch(e){
  $('vanJrdb').textContent=e.message;
  $('vanCheck').disabled=true;
 }
}
$('vanCheck').addEventListener('click',async()=>{
 if(!forecast)return;
 const status=$('vanResult'),file=$('vanFile').files?.[0],button=$('vanCheck');
 button.disabled=true;
 $('vanDetails').replaceChildren();
 try{
  if(!file||!/^jvdata-one-race-20\d{6}-\d{2}-\d{2}\.json$/.test(file.name)||
     file.size<1||file.size>2000000)
   throw Error('本人PCの2MB以内のjvdata-one-race-...jsonファイルを選んでください。');
  const raw=await file.text();
  if(raw.length>2000000)throw Error('ファイルが大きすぎます。');
  const report=compareLocalJvWithJrdb(JSON.parse(raw),forecast);
  const key=report.track+report.race+'R';
  status.textContent=key+'｜'+(report.candidateFieldsConsistent?'候補に矛盾なし':'候補不一致')+
   '。ただし正式予想・JRA最終確認には進みません。';
  const paragraph=document.createElement('p');
  paragraph.className=report.candidateFieldsConsistent?'good':'warn';
  paragraph.textContent='JRA-VAN候補'+report.candidateRunners+'頭、JRDB参考'+
    report.editorialRunners+'頭。予定時刻'+(report.postTimeMatch?'一致':'不一致')+
    '／距離'+(report.distanceMatch?'一致':'不一致')+
    '／芝・ダ'+(report.surfaceMatch?'一致':'不一致')+
    '／参考上位馬番'+(report.pickedNumbersPresent?'存在':'欠落')+
    '。過去走観測のある馬'+report.observedHorseHistories+'頭。'+report.note;
  $('vanDetails').append(paragraph);
 }catch(e){status.textContent=e.message||'照合できませんでした。';}
 finally{button.disabled=false;}
});
load();
})();"""
