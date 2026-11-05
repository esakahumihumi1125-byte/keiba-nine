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
画面表示だけで、サーバーへの保存や定期的な自動取得はしません。</p></section>
<section class="panel" id="report" hidden><h2>レース別の確認結果</h2>
<p id="summary"></p><div id="rows"></div><section id="review" hidden><h2>発走前の優先チェック</h2><p id="reviewSummary"></p><div id="reviewRows"></div></section></section>
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
  }catch(_){
   status.textContent='設定を確認できませんでした。ログイン状態を確認してな。';
  }
 }
 button.addEventListener('click',async()=>{
  const iso=date.value;
  if(!/^\\d{4}-\\d{2}-\\d{2}$/.test(iso)){message.textContent='開催日を選んでな。';return;}
  const before=button.disabled;button.disabled=true;$('report').hidden=true;
  message.textContent='対象日の資料件数を確認しています…';
  try{
   const result=await getJson('/api/jrdb/day-pipeline?date='+encodeURIComponent(iso.replaceAll('-','')));
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
  }catch(e){message.textContent=e.message||'資料の照合に失敗しました。';}
  finally{button.disabled=before;}
 });
 init();
})();
"""
