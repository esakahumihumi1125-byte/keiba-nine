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
<p id="vanJrdb" role="status">本人用の参考予想を確認中…</p>
<p class="small">JRDB番組取得が失敗する場合に、認証・権限・応答形式を切り分けるための診断です。
本人が押したときだけ、JRDB β版の番組API（/tra）へ1回接続診断します。
使い方・契約内容によって通信回数の制限がある場合があります。
取得した有料行、認証キー、馬名は保存・画面表示しません。</p>
<button id="vanJrdbProbe" type="button" disabled>JRDBの実接続を1回診断</button>
<p id="vanJrdbProbeStatus" role="status" class="small">接続診断は未実行。参考予想の存在はAPI接続成功を意味しません。</p></section>
<section><h2>2．JRA-VANの研究用ファイル</h2>
<p>PCの <code>ARC-RACE-private</code> に保存された
<code>jvdata-candidate-YYYYMMDD.json</code>（RACEだけを1回読む）または <code>jvdata-one-race-YYYYMMDD-xx-xx.json</code> を選択してください。
PCの「jvdata-candidate-YYYYMMDD.json」なら同じ日の全Rの候補を一度に比較できます。過去走の研究ファイル「jvdata-one-race-...json」も1Rずつ比較できます。JRA-VANの取得自体はこの画面から実行しません。</p>
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
function compareWeeklyJvCandidate(fileData,reference){
 if(!reference||reference.schema!=='keiba-nine-private-preday-review-v1'||
    reference.sourceKind!=='owner-private-authored-preday'||
    reference.predictionReady!==false||reference.officialJraVerified!==false||
    reference.purchased!==false||
    !Array.isArray(reference.races)||reference.races.length<1||
    reference.races.length>36||
    !/^\d{4}-\d{2}-\d{2}$/.test(reference.date))
  throw Error('JRDB前日参考予想の形式が不正です。');
 if(!fileData||fileData.version!=='owner-jvlink-weekly-local-candidates-1'||
    fileData.source!=='private_jvlink_weekly_ra_se_candidate'||
    fileData.date!==reference.date||
    fileData.privateOwnerOnly!==true||fileData.researchOnly!==true||
    fileData.providerDataRawIncluded!==false||
    fileData.collectionTimeIndependentlyVerified!==false||
    fileData.allScheduledVenuesVerified!==false||
    fileData.independentJraVerified!==false||
    fileData.officialScratchesVerified!==false||
    fileData.officialGoingVerified!==false||
    fileData.officialFinalPostTimeVerified!==false||
    fileData.productionPredictionReady!==false||
    fileData.bettingReady!==false||fileData.autoPurchase!==false||
    !Array.isArray(fileData.races)||fileData.races.length<1||
    fileData.races.length>36||fileData.raceCount!==fileData.races.length)
  throw Error('開催日が違うか、本人PCのJRA-VAN一括研究用ファイルではありません。');
 const seen=new Map();
 for(const card of fileData.races){
  if(!card||!TRACKS.has(card.track)||!Number.isInteger(card.race)||
     card.race<1||card.race>12||
     card.sourceRecordCategory!=='numbered_racecard_not_final_changes'||
     card.privateInputOnly!==true||
     card.finalStarterListVerified!==false||
     card.scratchStatusVerified!==false||
     card.latestGoingVerified!==false||
     card.officialFinalPostTimeVerified!==false||
     card.formalTenFactorReady!==false||
     card.bettingReady!==false||
     typeof card.postTimeCandidate!=='string'||
     !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(card.postTimeCandidate)||
     !Number.isInteger(card.distanceMetersCandidate)||
     card.distanceMetersCandidate<400||card.distanceMetersCandidate>10000||
     !['芝','ダート'].includes(card.surfaceCandidate)||
     !Number.isInteger(card.registeredRunnerCount)||
     card.registeredRunnerCount<3||card.registeredRunnerCount>18||
     !Array.isArray(card.horseNumbersCandidate)||
     card.horseNumbersCandidate.length!==card.registeredRunnerCount||
     card.horseNumbersCandidate.some(n=>!Number.isInteger(n)||n<1||n>18)||
     new Set(card.horseNumbersCandidate).size!==card.registeredRunnerCount)
   throw Error('JRA-VANの出走馬番候補に不正な形式があります。');
  const key=card.track+'|'+card.race;
  if(seen.has(key))throw Error('JRA-VAN候補のレースが重複しています。');
  seen.set(key,card);
 }
 const examined=[],refSeen=new Set();
 for(const row of reference.races){
  if(!row||!TRACKS.has(row.track)||!Number.isInteger(row.race)||
     row.race<1||row.race>12||refSeen.has(row.track+'|'+row.race)||
     !Number.isInteger(row.field)||row.field<3||row.field>18||
     !Array.isArray(row.rank)||row.rank.length<3||
     row.rank.length>7||!['買い候補','見送り'].includes(row.status))
   throw Error('JRDBの参考レース情報を検査できません。');
  const key=row.track+'|'+row.race;refSeen.add(key);
  const source=seen.get(key);
  if(!source){
   examined.push({track:row.track,race:row.race,
     status:'jvlink_not_observed',candidateFieldsConsistent:false});
   continue;
  }
  const numbers=new Set(source.horseNumbersCandidate);
  const course=row.course;
  const distanceMatch=typeof course==='string' &&
   Number((course.match(/(\d{3,4})M/)||[])[1])===source.distanceMetersCandidate;
  const surfaceMatch=typeof course==='string' &&
    ((course.includes('芝')&&source.surfaceCandidate==='芝')||
     (course.includes('ダ')&&source.surfaceCandidate==='ダート'));
  const fieldMatch=row.field===numbers.size;
  const timeMatch=row.time===source.postTimeCandidate;
  const chosenNumbersPresent=row.rank.every(n=>numbers.has(n));
  const candidateFieldsConsistent=Boolean(
    distanceMatch&&surfaceMatch&&fieldMatch&&timeMatch&&chosenNumbersPresent);
  examined.push({track:row.track,race:row.race,
    status:candidateFieldsConsistent?'candidate_fields_consistent':'hold_source_mismatch',
    candidateFieldsConsistent,timeMatch,distanceMatch,surfaceMatch,
    fieldMatch,chosenNumbersPresent});
 }
 const observed=new Set(seen.keys());
 const unexpected=[...observed].filter(x=>!refSeen.has(x));
 const consistent=examined.filter(x=>x.candidateFieldsConsistent).length;
 return {
  date:reference.date,editorialRaceCount:reference.races.length,
  observedJvRaceCount:fileData.races.length,
  consistentCandidateRaceCount:consistent,
  missingJvRaces:examined.filter(x=>x.status==='jvlink_not_observed').length,
  mismatchJvRaces:examined.filter(x=>x.status==='hold_source_mismatch').length,
  unexpectedJvRaceCount:unexpected.length,
  races:examined,
  allHorseIdentityMatched:false,
  officialStarterListVerified:false,officialScratchesVerified:false,
  officialGoingVerified:false,formalTenFactorReady:false,bettingReady:false,
  referenceCardAndJvCandidateFieldsAllConsistent:
    consistent===reference.races.length&&unexpected.length===0,
  note:'一括照合は馬番・頭数・予定時刻・距離・芝ダの研究用候補のみ。JRDB全頭馬名の独立照合、当日JRA最終情報、正式10項目は未確認。'
 };
}
function normalizeJrdbProbeResult(code,body,day){
 if(!/^\d{8}$/.test(day)||!body||typeof body!=='object'||Array.isArray(body))
  throw Error('接続診断の形式が不正です。');
 if(code!==200){
  // The server returns Japanese, credential-free hints. Never expose a raw
  // paid source response or stack trace in the UI.
  const known=[
   'JRDBのAPIキーまたはユーザー認証キーが正しいか確認してください。',
   'JRDB β版アカウントの利用権限・有効期限を確認してください。',
   'JRDBの通信回数制限です。再試行の間隔を空けてください。',
   'JRDBとの通信に失敗しました。接続先やβ版アカウントを確認してください。',
   'JRDBからの番組形式または開催日が一致しません。β版の仕様を確認してください。',
   'JRDB β版の専用APIキーと非公開接続設定が必要です。'
  ];
  return {connected:false,
    label:known.includes(body.error)?body.error:
      'JRDB接続診断に失敗。接続先・認証・応答形式を確認してください。'};
 }
 if(body.date!==day||body.connectionVerified!==true||
    !Number.isInteger(body.programmeCount)||
    body.programmeCount<0||body.programmeCount>100||
    body.providerDataStored!==false||body.predictionReady!==false)
  throw Error('JRDB実接続診断の安全状態を確認できません。');
 return {connected:true,
   label:'JRDB β版への接続は成功。番組の候補'+body.programmeCount+
    '件。ただしJRA-VAN全頭照合・正式10項目予想・JRA公式取消確認は未完了。'};
}
if(typeof module!=='undefined'&&module.exports){
 module.exports={compareLocalJvWithJrdb,compareWeeklyJvCandidate,normalizeJrdbProbeResult};return;
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
  $('vanJrdbProbe').disabled=false;
 }catch(e){
  $('vanJrdb').textContent=e.message;
  $('vanCheck').disabled=true;
  $('vanJrdbProbe').disabled=true;
 }
}
$('vanJrdbProbe').addEventListener('click',async()=>{
 if(!forecast)return;
 const button=$('vanJrdbProbe'),status=$('vanJrdbProbeStatus');
 const day=forecast.date.replace(/-/g,'');
 if(!/^20\d{6}$/.test(day)){
  status.textContent='予想日付が不正です。診断しません。';
  return;
 }
 button.disabled=true;
 status.textContent='本人操作によりJRDBの番組APIを1回だけ照合しています…';
 try{
  const response=await fetch('/api/jrdb/connection-test?date='+encodeURIComponent(day),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const body=await response.json();
  const normalized=normalizeJrdbProbeResult(response.status,body,day);
  status.textContent=normalized.label;
 }catch(_){
  status.textContent='通信または応答形式を確認できません。再試行を繰り返さず、接続設定を確認してください。';
 }finally{button.disabled=false;}
});
$('vanCheck').addEventListener('click',async()=>{
 if(!forecast)return;
 const status=$('vanResult'),file=$('vanFile').files?.[0],button=$('vanCheck');
 button.disabled=true;
 $('vanDetails').replaceChildren();
 try{
  if(!file||!/^jvdata-(?:one-race-20\d{6}-\d{2}-\d{2}|candidate-20\d{6})\.json$/.test(file.name)||
     file.size<1||file.size>2000000)
   throw Error('PCに保存された2MB以内のjvdata-candidate-...jsonまたはjvdata-one-race-...jsonを選んでください。');
  const raw=await file.text();
  if(raw.length>2000000)throw Error('ファイルが大きすぎます。');
  const parsed=JSON.parse(raw);
  if(parsed.version==='owner-jvlink-weekly-local-candidates-1'){
   const weekly=compareWeeklyJvCandidate(parsed,forecast);
   status.textContent=weekly.date+'｜JRA-VAN観測'+weekly.observedJvRaceCount+
    'R／JRDB参考'+weekly.editorialRaceCount+'R。研究用候補の矛盾なし'+
    weekly.consistentCandidateRaceCount+'R、未観測'+weekly.missingJvRaces+
    'R、候補不一致'+weekly.mismatchJvRaces+'R、予想外の候補'+
    weekly.unexpectedJvRaceCount+'R。正式予想ではありません。';
   const desc=document.createElement('p');desc.className='small';
   desc.textContent=weekly.note;$('vanDetails').append(desc);
   for(const item of weekly.races){
    const p=document.createElement('p');
    p.className=item.candidateFieldsConsistent?'good':'warn';
    p.textContent=item.track+item.race+'R：'+(
     item.status==='candidate_fields_consistent'?'候補の項目に矛盾なし':
     item.status==='jvlink_not_observed'?'JRA-VAN候補未観測':
     'JRDB参考との不一致（保留）');
    $('vanDetails').append(p);
   }
  }else{
   const report=compareLocalJvWithJrdb(parsed,forecast);
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
  }
 }catch(e){status.textContent=e.message||'照合できませんでした。';}
 finally{button.disabled=false;}
});
load();
})();"""
