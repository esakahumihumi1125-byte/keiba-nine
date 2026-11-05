"""Authenticated, no-autofetch, owner-only day-wide data-readiness screen.

All scripts/styles are same-origin static assets. No licensed data renders
until a user explicitly invokes the protected five-request day endpoint.
"""

HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>競馬ナイン｜全R資料の一括チェック</title>
<link rel="stylesheet" href="/day-pipeline.css"></head><body><main>
<header><a href="/">← 本人用ホームへ</a><h1>🏇 全場・全R 自動分析の準備</h1>
<p class="lead">JRDBの認証が使えるようになったら、開催日を選ぶだけで全レースの資料件数をまとめて照合する画面やで。</p>
<p class="warning">現在の実戦予想エンジンは未接続。資料件数が揃ってもS/A/B/C評価・3連単は自動生成されません。
JRA公式最終照合と実データの予想精度検証は別工程です。購入・記録・公開はしません。</p></header>
<section class="panel"><h2>接続状態</h2><p id="state" role="status">接続設定を確認中…</p></section>
<section class="panel"><h2>1日分をまとめてチェック</h2>
<label for="date">対象開催日</label><input id="date" type="date" required>
<button id="run" type="button" disabled>全レースの資料を一括確認する</button>
<p id="message" class="hint" role="status">API β版の認証が届くまでは実行できません。</p>
<p class="hint">本人がボタンを押したときだけJRDBの番組・出走馬・調教・近走・馬場を各1回取得します。
画面表示だけで、サーバーへの保存や定期的な自動取得はしません。</p>
<hr><h2>当日だけの直前資料（別操作）</h2>
<button id="prestartRun" type="button" disabled>当日の馬体重・パドック資料の件数を確認</button>
<p id="prestartMessage" class="hint" role="status">API β版の認証と直前資料用の安全設定が済むまでは停止中。</p>
<p class="hint">別操作で番組・登録馬・直前資料を各1回取得。オッズは使用せず、馬体重や指数の値も表示しません。</p><hr><h2>残り2項目：過去距離・馬場の資料チェック</h2>
<button id="historyRun" type="button" disabled>過去の距離・馬場を最大8レース分照合する</button>
<p id="historyMessage" class="hint" role="status">JRDBの専用認証と履歴取得設定が届くまでは停止中。</p>
<p class="hint">本人が押した時だけ別途取得。1回につき当日5種類＋過去番組最大8件・過去馬場最大8件。
資料を照合しても、実戦の適性評価や馬券購入には進みません。</p></section>
<section class="panel" id="report" hidden><h2>レース別の確認結果</h2>
<p id="summary"></p><section id="factorProgress" hidden><h2>調教・近走の暫定資料評価（実戦評価ではありません）</h2><p id="factorSummary"></p><div id="factorRows"></div></section><section id="sourceMaterials" hidden><h2>10項目の資料チェック（8項目に資料の手掛かり）</h2><p id="sourceMaterialsSummary"></p><div id="sourceMaterialsRows"></div></section><div id="rows"></div><section id="review" hidden><h2>発走前の優先チェック</h2><p id="reviewSummary"></p><div id="reviewRows"></div></section></section>
<section class="panel" id="historyReport" hidden><h2>過去の距離・馬場の資料照合</h2>
<p id="historySummary"></p><div id="historyRows"></div>
<p class="hint">今回の資料だけでは能力・馬場適性を断定しません。実戦予想は未接続です。</p></section>
<section class="panel" id="prestartReport" hidden><h2>当日の馬体資料（件数のみ）</h2><p id="prestartSummary"></p><div id="prestartRows"></div></section>
<footer>登録済み馬の名前・馬番・有料の生データは表示しません。これは資料取得の準備状況であり、レース予想ではありません。</footer>
</main><script src="/day-pipeline.js" defer></script></body></html>"""

CSS = """
*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#edf4ff;font:15px/1.65 system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding:18px 14px 45px}h1{font-size:24px;margin:14px 0}
h2{font-size:19px;margin:0 0 8px}a{color:#efd18b}.lead{color:#cbd9ea}
.panel{background:#152d4b;border:1px solid #385372;border-radius:15px;padding:16px;margin:14px 0}
.warning{background:#403322;color:#ffe1ab;border-left:3px solid #d4a858;border-radius:9px;padding:13px}
label{display:block;font-weight:700;margin-bottom:7px}input{display:block;min-height:48px;width:100%;background:#0b2139;color:white;font:18px system-ui,sans-serif;border:1px solid #65819c;border-radius:9px;padding:9px}
button{font:inherit;min-height:50px;width:100%;border:0;border-radius:10px;background:#f1cd78;color:#14283b;font-weight:800;margin-top:12px}
button:disabled{opacity:.48}.hint{font-size:13px;color:#c0d0e4}
.race{margin:10px 0;background:#0b2139;border:1px solid #385571;border-radius:10px;padding:12px}.race strong{font-size:16px}.race p{margin:5px 0;color:#bdcce0;font-size:13px}
footer{color:#aebfd4;font-size:13px}
"""

JS = """
'use strict';
(function(){
 const $=id=>document.getElementById(id);
 const date=$('date'), button=$('run'), status=$('state'), message=$('message');
 const prestart=$('prestartRun'), prestartMessage=$('prestartMessage');
 const history=$('historyRun'), historyMessage=$('historyMessage');
 let selectedDateVersion=0;
 function jstDate(){
  const values=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
   timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit'
  }).formatToParts(new Date()).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
  return values.year+'-'+values.month+'-'+values.day;
 }
 date.value=jstDate();
 const make=(tag,content)=>{const el=document.createElement(tag);el.textContent=content;return el;};
 async function getJson(path){
  const response=await fetch(path,{credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private'}});
  const data=await response.json();
  if(!response.ok)throw Error(data.error||'通信できませんでした。');
  return data;
 }
 async function init(){
  try{
   const data=await getJson('/api/setup');
   if(!data.jrdbConfigured){
    status.textContent='JRDB API β版の認証情報待ち。実データ取得は停止中です。';
    message.textContent='アカウント発行後、本人専用の設定を確認してから接続テストします。';
    return;
   }
   status.textContent='認証設定あり（接続成功・利用許諾・予想生成の確認ではありません）。';
   button.disabled=false;
   message.textContent='実行すると対象日の5種類の資料を各1回確認します。';
   if(data.historyConfigured===true){
    history.disabled=false;
    historyMessage.textContent='取得上限を守り、押した時だけ過去資料の照合を開始します。';
   }
   if(data.prestartBodyEnabled===true){
    prestart.disabled=false;
    prestartMessage.textContent='開催日の当日に本人が操作したときだけ直前資料を確認できます。';
   }
  }catch(_){
   status.textContent='設定を確認できませんでした。ログイン状態を確認してな。';
  }
 }
 date.addEventListener('change',()=>{
  selectedDateVersion+=1;
  $('report').hidden=true;
  $('review').hidden=true;
  $('factorProgress').hidden=true;
  $('factorRows').replaceChildren();
  $('sourceMaterials').hidden=true;
  $('sourceMaterialsRows').replaceChildren();
  $('historyReport').hidden=true;
  $('historyRows').replaceChildren();
  $('prestartReport').hidden=true;
  $('prestartRows').replaceChildren();
  $('rows').replaceChildren();
  $('reviewRows').replaceChildren();
  message.textContent='開催日を変更しました。以前の資料チェックは非表示にしたで。';
 });
 history.addEventListener('click',async()=>{
  const iso=date.value;
  if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(iso)){
   historyMessage.textContent='開催日を選んでな。';return;
  }
  const requestedVersion=selectedDateVersion;
  history.disabled=true;
  $('historyReport').hidden=true;
  $('historyRows').replaceChildren();
  historyMessage.textContent='指定日の過去レースを上限8件で照合中…';
  try{
   const response=await fetch('/api/jrdb/history',{
    method:'POST',credentials:'same-origin',cache:'no-store',
    headers:{'Content-Type':'application/json','X-Keiba-Request':'private'},
    body:JSON.stringify({date:iso.replaceAll('-',''),limit:8})
   });
   const data=await response.json();
   if(requestedVersion!==selectedDateVersion||date.value!==iso)return;
   if(!response.ok)throw Error(data.error||'過去資料を確認できませんでした。');
   const full=data.allTenFactorSources,gate=data.realAssessmentPreflight,
    quality=data.evidenceQuality, historical=data.privateHistoryFactors;
   if(data.version!=='bounded-history-1'||data.predictionReady!==false||
      data.goingSuitabilityAssessed!==false||
      !Number.isInteger(data.selectedPastRaces)||data.selectedPastRaces<0||
      data.selectedPastRaces>8||!Number.isInteger(data.deferredPastRaces)||
      data.deferredPastRaces<0||
      !Number.isInteger(data.draCalls)||data.draCalls<0||data.draCalls>8||
      !Number.isInteger(data.dkaCalls)||data.dkaCalls<0||data.dkaCalls>8||
      data.maxTotalCalls!==16||!full||
      full.version!=='combined-ten-factor-observations-1'||
      full.predictionReady!==false||full.bettingReady!==false||
      !gate||gate.version!=='real-assessment-preflight-1'||
      gate.realGradeReady!==false||gate.realPredictionReady!==false||
      gate.purchaseReady!==false||!quality||
      quality.predictionReady!==false||quality.suitabilityAssessed!==false||
      !historical||historical.version!=='private-course-ground-materials-1'||
      historical.predictionReady!==false||historical.bettingReady!==false||
      !Array.isArray(full.races)||full.raceCount>120||
      full.raceCount!==full.races.length||
      quality.raceCount!==full.raceCount||gate.raceCount!==full.raceCount||
      historical.raceCount!==full.raceCount)
    throw Error('過去の資料を安全な形式で表示できませんでした。');
   $('historySummary').textContent='過去番組 '+data.draCalls+'件／馬場 '+
    data.dkaCalls+'件を確認（上限各8件）。未照合 '+data.deferredPastRaces+
    '件、番組欠損 '+data.unavailablePastProgrammes+
    '件。10項目に資料枠を接続しても、実戦の総合S/A/B/Cは未確定。';
   const rows=$('historyRows'), seen=new Set();
   for(const r of full.races){
    const key=r.track+':'+r.race;
    if(seen.has(key)||r.sourceMaterialSlots!==10||
       r.unmappedFactorCount!==0||r.verifiedFactorCount!==0||
       r.officialJraFinalVerification!==false||
       r.overallRankReady!==false||r.predictionReady!==false||
       r.bettingReady!==false||
       !Number.isInteger(r.runnerCount)||r.runnerCount<0||r.runnerCount>18||
       !Number.isInteger(r.runnersWithComparableCourse)||
       !Number.isInteger(r.runnersWithKnownGoingComparable)||
       r.runnersWithComparableCourse<0||
       r.runnersWithComparableCourse>r.runnerCount||
       r.runnersWithKnownGoingComparable<0||
       r.runnersWithKnownGoingComparable>r.runnersWithComparableCourse)
     throw Error('履歴資料のレース照合に失敗しました。');
    seen.add(key);
    const el=document.createElement('details');el.className='race';
    el.append(make('summary',r.track+r.race+'R｜比較できた距離の履歴：'+
      r.runnersWithComparableCourse+'/'+r.runnerCount+'頭'));
    el.append(make('p','馬場状態まで比較可能：'+
      r.runnersWithKnownGoingComparable+'/'+r.runnerCount+'頭'));
    el.append(make('p','履歴不足の馬：'+r.runnersWithIncompleteHistory+
      '頭／過去距離・馬場の能力評価は未実施。'));
    rows.append(el);
   }
   $('historyReport').hidden=false;
   historyMessage.textContent='過去資料の件数照合が完了。実戦予想・購入・記録は変更してへんで。';
  }catch(e){
   if(requestedVersion===selectedDateVersion&&date.value===iso)
    historyMessage.textContent=e.message||'過去資料の照合に失敗しました。';
  }finally{history.disabled=false;}
 });
 prestart.addEventListener('click',async()=>{
  const iso=date.value;
  if(iso!==jstDate()){
   prestartMessage.textContent='直前情報は日本時間の今日の開催日だけ確認できるで。';
   return;
  }
  const requestedVersion=selectedDateVersion;
  prestart.disabled=true;
  $('prestartReport').hidden=true;
  prestartMessage.textContent='直前資料の件数を確認しています…';
  try{
   const data=await getJson('/api/jrdb/prestart-body?date='+encodeURIComponent(iso.replaceAll('-','')));
   if(requestedVersion!==selectedDateVersion||date.value!==iso)return;
   if(data.version!=='private-prestart-body-1'||data.rawHorseRecordsIncluded!==false||
      data.oddsUsed!==false||data.realPredictionReady!==false||
      data.purchaseReady!==false||!Array.isArray(data.races)||
      data.raceCount!==data.races.length||data.races.length>120)
    throw Error('直前資料を安全に表示できませんでした。');
   $('prestartSummary').textContent=data.raceCount+'R確認／馬体重の報告 '+
    data.summary.weightRecords+'頭分／パドック資料 '+data.summary.paddockRecords+
    '頭分／直前情報の未対応 '+data.summary.missingRows+
    '頭分。評価や購入はしていません。';
   const rows=$('prestartRows');rows.replaceChildren();
   for(const r of data.races){
    if(r.realPredictionReady!==false||r.ticketReady!==false||
       r.bodyConditionGraded!==false||r.officialBodyWeightVerified!==false)
      throw Error('予想や公式確定の扱いを拒否しました。');
    const el=make('article','');el.className='race';
    el.append(make('strong',r.track+r.race+'R｜登録 '+r.registered+'頭'));
    el.append(make('p','馬体重の報告 '+r.bodyWeightRecords+
      '頭／増減 '+r.weightChangeRecords+'頭／パドック資料 '+
      r.paddockRecords+'頭／未対応 '+r.prestartRowsMissing+'頭'));
    el.append(make('p','出走取消・馬体状態のJRA公式最終確認なし。買い目なし。'));
    rows.append(el);
   }
   $('prestartReport').hidden=false;
   prestartMessage.textContent='直前資料の件数だけを確認したで。買い目・記録への反映はなし。';
  }catch(e){if(requestedVersion===selectedDateVersion&&date.value===iso)
   prestartMessage.textContent=e.message||'直前資料を確認できませんでした。';}
  finally{prestart.disabled=false;}
 });
 button.addEventListener('click',async()=>{
  const iso=date.value;
  if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(iso)){message.textContent='開催日を選んでな。';return;}
  const requestedVersion=selectedDateVersion;
  const before=button.disabled;button.disabled=true;$('report').hidden=true;
  message.textContent='対象日の資料件数を確認しています…';
  try{
   const result=await getJson('/api/jrdb/day-pipeline?date='+encodeURIComponent(iso.replaceAll('-','')));
   if(requestedVersion!==selectedDateVersion||date.value!==iso)return;
   if(result.realPredictionReady!==false||result.purchaseReady!==false||
      result.rawHorseRecordsIncluded!==false||result.sourceRequestCount!==5||
      !Array.isArray(result.races)||result.races.length>120||
      result.recordType==='live-prediction')
      throw Error('実戦予想としての扱いを拒否しました。');
   const sum=result.summary;
   $('summary').textContent=result.raceCount+'R確認／頭数件数一致 '+sum.matchedEntryCountRaces+
    'R／調教未対応 '+sum.missingTrainingRecords+'頭分／1週前 '+sum.missingLastWeekRecords+
    '頭分／近走 '+sum.missingRecentRecords+'頭分。公式照合と実戦予想は未実施。';
   const rows=$('rows');rows.replaceChildren();
   for(const item of result.races){
    const row=make('article','');row.className='race';
    row.append(make('strong',item.track+item.race+'R｜'+(item.postTimeFromProvider||'時刻未確認')));
    row.append(make('p','登録 '+item.registered+'頭／番組 '+(item.expected==null?'未確認':item.expected)+
      '頭。調教未対応 '+item.trainingUnaccounted+'／1週前 '+item.lastWeekUnaccounted+
      '／近走 '+item.recentUnaccounted+'頭分。'));
    row.append(make('p','取得元馬場 '+(item.sourceGoingRecorded?'記録あり':'未確認')+
      '｜JRA公式照合なし・総合評価なし・買い目なし'));
    rows.append(row);
   }
   const progress=result.factorProgress;
   const factors=$('factorProgress');factors.hidden=true;
   if(progress){
    if(progress.version!=='day-factor-progress-1'||
       progress.date!==iso.replaceAll('-','')||
       progress.raceCount!==result.raceCount||
       progress.realOverallGradeReady!==false||
       progress.realPredictionReady!==false||
       progress.purchaseReady!==false||
       progress.rawHorseRecordsIncluded!==false||
       !Array.isArray(progress.races)||progress.races.length!==progress.raceCount)
      throw Error('調教・近走の暫定評価情報を安全に表示できませんでした。');
    const ps=progress.summary;
    $('factorSummary').textContent='調教の暫定評価 '+ps.runnersWithTrainingProvisional+
     '頭分／近走の暫定評価 '+ps.runnersWithRecentProvisional+
     '頭分／両方に暫定評価 '+ps.runnersWithBothProvisional+
     '頭分／2段階以上の不一致 '+ps.runnersWithLargeGradeDisagreement+
     '頭分。実戦の総合評価・勝率・買い目ではありません。';
    const factorRows=$('factorRows');factorRows.replaceChildren();
    for(const r of progress.races){
     if(r.realOverallGradeReady!==false||r.realPredictionReady!==false||
        r.ticketReady!==false||r.officialRaceVerified!==false||
        r.fullTenFactorsGraded!==0||r.remainingFactorsUnassessed!==8)
      throw Error('未検証の暫定評価を実戦予想として表示できません。');
     const card=make('article','');card.className='race';
     card.append(make('strong',r.track+r.race+'R｜'+r.registered+'頭の研究用資料'));
     card.append(make('p','調教の暫定評価 '+r.trainingExperimentalGraded+
       '頭／近走の暫定評価 '+r.recentExperimentalGraded+
       '頭／両方が暫定評価 '+r.bothExperimentalGraded+'頭'));
     const labels=['S','A','B','C','未評価'];
     const histogram=field=>labels.map(g=>g+' '+r[field][g]).join('・');
     card.append(make('p','調教のみ：'+histogram('trainingGradeCounts')));
     card.append(make('p','近走のみ：'+histogram('recentGradeCounts')));
     card.append(make('p','残り8項目・JRA公式照合は未確認。3連単なし。'));
     factorRows.append(card);
    }
    factors.hidden=false;
   }
   const materials=result.sourceMaterials;
   const materialSection=$('sourceMaterials');materialSection.hidden=true;
   if(materials){
    if(materials.version!=='private-eight-materials-1'||
       materials.date!==iso.replaceAll('-','')||
       materials.raceCount!==result.raceCount||
       materials.verifiedOverallFactors!==0||
       materials.realPredictionReady!==false||
       materials.purchaseReady!==false||
       materials.rawHorseRecordsIncluded!==false||
       !Array.isArray(materials.mappedSourceSlots)||
       materials.mappedSourceSlots.length!==8||
       !Array.isArray(materials.unmappedHistorySlots)||
       materials.unmappedHistorySlots.length!==2||
       !Array.isArray(materials.races)||materials.races.length!==result.raceCount)
     throw Error('10項目の資料情報を安全に表示できませんでした。');
    const counts=materials.summary;
    $('sourceMaterialsSummary').textContent='10項目中、資料の8枠を接続／距離・馬場適性の過去照合は未接続。'+
     '登録 '+counts.totalRegistered+'頭分・血統(父と母父) '+counts.pedigreePresent+
     '頭分・枠と斤量 '+counts.drawAndWeightPresent+
     '頭分・騎手/厩舎 '+counts.personnelPresent+'頭分。'+
     'これは資料の有無だけで、能力評価や購入推奨ではありません。';
    const materialRows=$('sourceMaterialsRows');materialRows.replaceChildren();
    const observed=new Set(result.races.map(r=>r.track+':'+r.race));
    for(const r of materials.races){
     const n=r.registered, c=r.counts;
     if(!observed.has(r.track+':'+r.race)||
        r.observedSourceSlots!==8||r.unmappedHistorySlots!==2||
        r.unverifiedFactorGrades!==10||r.provisionalFactorsOnly!==2||
        r.officialJraVerified!==false||r.overallRankReady!==false||
        r.realPredictionReady!==false||r.ticketReady!==false||
        !Number.isInteger(n)||n<0||n>18||!c)
      throw Error('レース別の資料件数を安全に表示できません。');
     const names=[
      ['pedigreeParentsRecorded','父・母父'],['drawAndAssignedWeightRecorded','枠と斤量'],
      ['lastRaceDateRecorded','前走日付'],['jockeyTrainerNamesRecorded','騎手・厩舎'],
      ['conformationCodeRecorded','馬体形状コード'],
      ['pastCornerObservedForPaceResearch','過去4角位置']
     ];
     if(!names.every(([key])=>Number.isInteger(c[key])&&c[key]>=0&&c[key]<=n))
      throw Error('提供元の資料件数が範囲外です。');
     const panel=document.createElement('details');panel.className='race';
     panel.append(make('summary',r.track+r.race+'R｜'+n+'頭の資料状況を表示'));
     for(const [key,label] of names){panel.append(make('p',label+'：'+c[key]+'/'+n+'頭分'));}
     panel.append(make('p','過去の距離・馬場照合と実戦の10項目評価は未実施。'));
     materialRows.append(panel);
    }
    materialSection.hidden=false;
   }
   const queue=result.reviewQueue;
   const review=$('review');
   review.hidden=true;
   if(queue){
    if(queue.version!=='private-day-review-1'||queue.realPredictionReady!==false||
       queue.purchaseReady!==false||queue.officialFinalVerified!==false||
       queue.raceCount!==result.raceCount||!Array.isArray(queue.races)||
       queue.races.length!==queue.raceCount)
      throw Error('発走前の確認状況を安全に表示できませんでした。');
    $('reviewSummary').textContent='発走前2時間以内 '+queue.racesWithinTwoHours+
      'R／優先確認 '+queue.racesNeedingManualPriorityCheck+
      'R／発走時刻経過 '+queue.racesPassedPost+
      'R。これは資料の確認順で、公式確定・購入推奨ではありません。';
    const reviewRows=$('reviewRows');reviewRows.replaceChildren();
    const ageLabels={
     no_going_report:'提供元の馬場情報なし',
     no_update_timestamp:'馬場更新時刻なし',
     timestamp_in_future:'更新時刻が未来',
     recent_reported:'直近60分以内の報告',
     old_or_other_date_reported:'古い報告または別日'
    };
    const priorityLabels={
     urgent_manual_check:'発走2時間以内・要確認',
     post_time_passed:'発走時刻経過',
     not_near_start:'開始まで余裕あり・別日'
    };
    for(const item of queue.races){
     if(!(item.sourceGoingAgeStatus in ageLabels)||
        !(item.reviewPriority in priorityLabels)||
        item.realPredictionReady!==false||item.ticketReady!==false||
        item.independentJraVerified!==false||!Array.isArray(item.blockers)||
        !item.blockers.every(x=>typeof x==='string'&&x.length<150))
       throw Error('不明な確認状態を表示できません。');
     const el=make('article','');el.className='race';
     el.append(make('strong',item.track+item.race+'R｜'+priorityLabels[item.reviewPriority]));
     const minutes=item.minutesUntilListedPost;
     const due=minutes==null?'発走時刻は未確認':
       minutes>0?'発走まで約'+minutes+'分':
       '発走予定時刻を'+Math.abs(minutes)+'分経過';
     el.append(make('p',due+'｜馬場資料 '+ageLabels[item.sourceGoingAgeStatus]+'｜公式照合なし'));
     el.append(make('p',item.blockers.join('／')));
     reviewRows.append(el);
    }
    review.hidden=false;
   }
   $('report').hidden=false;
   message.textContent='資料件数と発走前の確認優先順を整理しました。購入や保存はしていません。';
  }catch(e){if(requestedVersion===selectedDateVersion&&date.value===iso)
   message.textContent=e.message||'資料の照合に失敗しました。';}
  finally{button.disabled=before;}
 });
 init();
})();
"""
