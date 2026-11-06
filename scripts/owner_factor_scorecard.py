"""Owner-local, manually entered 5-factor scorecard.

This does NOT fetch JRA/JRDB records and does NOT implement predictive AI.
It converts user-entered factor grades to transparent relative scores and
an optional 3連単 draft handoff via a client-only URL fragment.
"""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="競馬ナイン本人用">
<title>競馬ナイン｜5項目の手動評価</title>
<link rel="stylesheet" href="/owner-scorecard.css">
</head><body><main><a href="/">← 本人用ホーム</a> <a href="/owner-races">全開催R一覧へ</a>
<h1>5項目の手動評価</h1>
<p class="warning">これは<b>本人が入力する仮評価の計算表</b>です。JRA・JRDBの実データ取得、AIによる調教分析、実馬の予想はまだ行っていません。実戦で使う前に公式出馬表・取消を確認してください。</p>
<section><h2>① 開催日・競馬場・レース</h2><div class="fields">
<label for="scoreDate">日付</label><input type="date" id="scoreDate">
<label for="scoreTrack">競馬場</label><select id="scoreTrack">
<option value="">選択してください</option>
<option>札幌</option><option>函館</option><option>福島</option><option>新潟</option><option>東京</option><option>中山</option><option>中京</option><option>京都</option><option>阪神</option><option>小倉</option>
</select>
<label for="scoreRace">レース（1〜12R）</label><input id="scoreRace" type="number" min="1" max="12" step="1" value="1">
</div><p id="scoreDayStatus" class="hint" role="status">日付・競馬場を選ぶと12Rの入力状況を表示します。</p><p id="scoreAllDayStatus" class="hint" role="status">同日の保存済みRを確認します。未登録の開催を36Rと数えません。</p><div id="scoreVenueGrid" class="score-venue-grid" role="group" aria-label="保存済み会場別の採点進捗"></div><p id="scoreVenueStatus" class="hint" role="status">会場をタップすると、その会場の未評価Rへ移動できます。未登録の場は表示しません。</p><button type="button" id="scoreNextPending" class="memo-load" disabled>次の未評価・要再確認Rへ</button><p id="scoreNextPendingStatus" class="hint" role="status">採点済みのRを飛ばし、同日に保存された未評価・要再確認Rへ移動します。予想や馬券は自動作成しません。</p><button type="button" id="scoreTrialJump" class="memo-load">選択中のRをJRDB研究用・調教／近走の自動試算で開く</button><p id="scoreTrialJumpStatus" class="hint" role="status">API認証が発行された場合だけ利用できます。移動先で本人が実行を押すまで有料データの取得はしません。5項目の総合予想・馬券ではありません。</p><div id="scoreRaceGrid" class="score-race-grid" role="group" aria-label="選択した競馬場の1R〜12R評価メモ"></div><p class="hint">評価状況はこの端末の手入力メモのみ。公式の開催・出走・取消情報を表すものではありません。</p></section>
<section><h2>② 馬番と5項目の評価を貼る</h2>
<p class="hint">1頭1行で「馬番　調教　近走　適性　血統　展開」を入力。馬名は省略可。各項目は<b>S・A・B・C</b>。丸数字①〜⑱にも対応。最低3頭、最大18頭。</p>
<button type="button" id="scoreFromMemo" class="memo-load">本人の馬番・馬名メモから読み込む（採点は空欄）</button>
<button type="button" id="scoreFromPreday" class="memo-load">JRDB前日情報からこのRの馬番を仮入力</button>
<button type="button" id="scoreSeedPredayDay" class="memo-load">JRDB前日情報から選択日の全Rを一括仮登録（既存評価は上書きしない）</button>
<p id="scorePredayStatus" class="hint" role="status">「前日情報」を本人用メール取り込み画面で登録してから使えます。馬番・馬名はJRDB前日資料、JRA公式の出走確定ではありません。5項目は未評価で開始します。</p><p id="scoreMemoStatus" role="status" class="hint">JRDBの想定メールと一致する本人転記メモがある場合だけ、馬番・馬名を引き継げます。JRA公式の独立照合ではありません。</p><p id="scoreDraftStatus" role="status" class="hint">途中の評価はこの端末内に自動保存します。購入記録には入りません。</p><button type="button" id="scoreRetryDraft" class="memo-load">このRの途中評価をもう一度保存</button><p id="scoreNavigationStatus" role="status" class="hint">保存されていない評価がある場合は、別Rへの移動を止めます。</p><p id="scorePaceStatus" class="hint" role="status">脚質情報は、JRDB前日情報を取り込んだレースだけ表示します。予測された展開・能力ランクではありません。</p>
<div id="scoreMemoGrid" aria-label="本人入力の5項目採点"></div><textarea id="scoreInput" rows="10" maxlength="4000" spellcheck="false" placeholder="① 架空馬A S A A B S&#10;② 架空馬B A A S B A&#10;③ 架空馬C A B A A B&#10;④ 架空馬D B A B S A"></textarea>
<p class="hint">重み：調教25%／近走25%／適性20%／血統10%／展開20%。各項目をS=4、A=3、B=2、C=1として100点換算。人気やオッズは使わない。これは実績ある予測モデルではありません。</p>
<button type="button" id="scoreReview">総合評価と3連単候補を計算</button><button type="button" id="scoreClearDraft" class="clear-note">このRの途中評価を削除</button>
<p id="scoreStatus" role="status" class="hint">途中評価は本人用の端末内に自動保存します。サーバー送信・馬券購入・正式な予想確定はしません。</p></section>
<section><h2>③ 総合評価順と買い目候補</h2>
<div id="scoreRanks" aria-label="総合評価順"></div>
<div id="scoreWinnerReview" aria-label="総合3〜5位の1着候補再点検"></div>
<p id="scoreFormation" class="hint">評価を計算すると着順候補と実点数を表示します。</p>
<button type="button" id="scoreHandoff" disabled>3連単下書き画面へ渡す（未保存）</button>
<p class="hint">このボタンで引き継ぐのは日付・競馬場・R・馬番の着順候補だけ。馬名・評価・元データはURLやサーバーへ渡しません。移動先でも本人確認があり、保存も馬券購入も自動では行いません。</p>
</section>
<section><h2>④ 選択日の全Rを自動で下書き化</h2>
<p class="hint">この端末に保存された<b>本人手入力の5項目が全部そろったレース</b>だけ、同じ計算方法で3連単フォーメーションをまとめて作れます。最大36R。新しいレースのAI分析・JRA公式の出走確認は行いません。</p>
<button type="button" id="scoreDayBuild">この日に採点済みの全Rをまとめて計算</button>
<p id="scoreDayBatchStatus" class="hint" role="status">計算しても保存済みの馬券や購入記録には一切反映しません。</p>
<div id="scoreDayBatchPreview" aria-label="一括下書き候補の点数"></div>
<label for="scoreDayBatchText" class="hint">引き継ぐ馬番だけの4行形式（編集不可）</label>
<textarea id="scoreDayBatchText" rows="7" readonly spellcheck="false" placeholder="採点済みRを計算すると、ここに日付・競馬場・Rと1着／2着／3着候補だけが並びます。"></textarea>
<button type="button" id="scoreDayTransfer" disabled>全Rを3連単下書き画面で検査（未保存）</button>
<p class="hint">引き継ぎ先で全買い目を確認してから、本人が明示的に保存します。データは同じブラウザーの一時領域だけで引き継ぎ、URL・GitHub・サーバーへ馬名、採点やJRDB本文は送りません。実購入はしません。</p></section>
<section><h2>判断時の注意</h2><p class="hint">総合S：85点以上、A：70点以上、B：55点以上、C：55点未満（暫定・検証前の基準）。1着は相対上位2頭、2着は上位4頭、3着は上位8頭まで。点数が少なければ無理に増やしません。S馬がいない場合も相対上位は表示しますが、勝てるという意味ではありません。全着順の馬番が実際に出走するかはJRA公式で別途照合してください。</p>
<a href="/my-tickets">手動で3連単を作る</a></section>
</main><script defer src="/owner-scorecard.js"></script></body></html>"""

CSS = """.score-day-win{margin-top:10px;border-top:1px solid #58728a;padding-top:8px}.score-day-win summary{cursor:pointer;color:#edcb81;font-size:14px;font-weight:700}.score-day-first-btn{margin:5px 0;min-height:40px;padding:8px 10px;color:#e9f1fc;background:#25465d;border:1px solid #678bab;font-size:13px;text-align:left}.score-day-first-btn[aria-pressed="true"]{color:#ffe1a0;outline:2px solid #edca70;background:#655124}.score-day-win summary:focus-visible{outline:2px solid #edca70}.score-day-batch-card .winner-review-flag{display:block;margin-top:7px;color:#ffe3a2}.winner-review{border:1px solid #587790;border-radius:10px;padding:11px;margin:10px 0;background:#102b45}.winner-review p{margin:6px 0;font-size:13px;color:#e3e8ef}.winner-review h3{font-size:15px;color:#f2d588;margin:2px 0 8px}.winner-review-btn{font-weight:700;font-size:14px;line-height:1.5;color:#d6e3f2;background:#23445f;border:1px solid #678ca4;padding:9px;margin:5px 0;text-align:left}.winner-review-btn[aria-pressed="true"]{background:#715c2b;color:#ffe7a6;border-color:#e3c877;outline:2px solid #edca70}.winner-review small{display:block;color:#bbcddd}.winner-review .winner-review-flag{color:#ffe5a5}.score-day-ranks{margin-top:10px;border-top:1px solid #456982;padding-top:6px}.score-day-ranks summary{cursor:pointer;color:#cbdcec;font-size:13px;font-weight:700}.score-day-ranks p{padding:5px 4px;margin:2px 0;font-size:13px}.score-day-ranks summary:focus-visible{outline:2px solid #edca70}.score-day-batch-card{padding:10px;margin:9px 0;border:1px solid #5c7b93;border-radius:9px;background:#10243a}.score-day-batch-card strong{display:block;color:#e9d18c}.score-day-batch-card span{font-size:13px;color:#d4e1ed}#scoreDayBatchText{margin:12px 0;min-height:130px;font-size:14px}#scoreDayTransfer{margin-top:10px}#scoreDayBatchPreview{margin-top:10px}.clear-note{background:#344a62;color:#ffda9e;border:1px solid #ab826f;margin-top:10px}*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#f1f5ff;font:16px/1.6 system-ui,sans-serif}main{max-width:680px;padding:20px 14px 50px;margin:auto}h1{font-size:27px}h2{font-size:20px;margin:0 0 10px}a{color:#edca70}section{background:#142f4a;border:1px solid #456780;border-radius:14px;padding:17px;margin:16px 0}.warning{padding:12px;background:#322b22;border:1px solid #ae8755;border-radius:10px;color:#ffe7aa;font-size:14px}.hint{font-size:13px;color:#d0dfef;line-height:1.7}.fields{display:grid;gap:5px}.fields label{font-weight:700;margin-top:7px}input,select,textarea{width:100%;font:inherit;background:#0a2238;color:#f4f7ff;border:1px solid #7190ae;border-radius:9px;padding:11px;min-height:46px}textarea{min-height:225px;line-height:1.6}button{width:100%;min-height:49px;font:inherit;font-weight:800;color:#10253d;background:#edca70;border:0;border-radius:10px;padding:12px}button:disabled{opacity:.45}#scoreRaceGrid{margin:9px 0}.score-race-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.score-race-grid button{margin:0;min-height:54px;padding:8px 4px;font-size:13px;line-height:1.35;background:#24415c;color:#e4edf8;border:1px solid #5c7891}.score-race-grid button[aria-pressed="true"]{outline:2px solid #edca70;outline-offset:1px}.score-race-grid button.score-done{background:#2c5945}.score-race-grid button.score-stale{background:#5b3943}.score-race-grid button.score-partial{background:#51482d}.score-venue-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:10px 0}.score-venue-grid button{font-size:13px;line-height:1.5;text-align:left;background:#26435e;color:#f0f4f9;border:1px solid #6d8ca2;min-height:62px;padding:11px}.score-venue-grid button[aria-pressed="true"]{outline:2px solid #edca70;outline-offset:1px}.memo-load{background:#2f506a;color:#ffe5a6;border:1px solid #9eacb8;margin-bottom:9px}.memo-horse{border:1px solid #54758e;border-radius:10px;padding:11px;margin:10px 0}.memo-horse strong{display:block;margin-bottom:5px}.memo-horse-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.memo-horse-fields label{display:block;font-size:12px;color:#d5e7f4}.memo-horse-fields select{min-height:45px;padding:7px}.memo-horse-fields label:nth-child(5){grid-column:1/-1}.score-row{padding:12px;border-bottom:1px solid #365778}.score-row strong{display:block}.score-s{color:#f7d36e}.score-a{color:#ff8f88}.score-b{color:#a3d0fa}.score-c{color:#c9ced5}.score-row small{display:block;font-size:12px;color:#bbccdd}.score-form{padding:13px;background:#11273a;border:1px solid #516f8a;border-radius:9px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}"""

JS = r"""(()=>{'use strict';
/* No network or writes: read optional same-browser manually copied roster; grades remain operator-entered. */
const $=id=>document.getElementById(id);
const TRACKS=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
const GRADE=Object.freeze({S:4,A:3,B:2,C:1});
const WEIGHTS=Object.freeze([25,25,20,10,20]);
const NOTE_KEY='keiba-nine-owner-factor-notes-v1',MAX_NOTES=300;
const CIRCLES='①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱';
let preview=null,memoSourceMark=null,predaySourceMark=null;
function dateValid(date){
 if(typeof date!=='string'||!/^20\d{2}-\d{2}-\d{2}$/.test(date))return false;
 const d=new Date(date+'T12:00:00Z');
 return Number.isFinite(d.valueOf())&&d.toISOString().slice(0,10)===date;
}
function identity(){
 const date=$('scoreDate').value,track=$('scoreTrack').value,race=Number($('scoreRace').value);
 if(!dateValid(date)||!TRACKS.has(track)||!Number.isInteger(race)||race<1||race>12)
  throw Error('日付・競馬場・1〜12Rを選択してな。');
 return {date,track,race};
}
function parseGrades(text){
 if(typeof text!=='string'||!text.trim()||text.length>4000)
  throw Error('最低3頭の馬番と5項目を入力してな。');
 const raw=text.replace(/[①-⑱]/g,n=>' '+(CIRCLES.indexOf(n)+1)+' ').normalize('NFKC');
 const lines=raw.split(/\r?\n/).map(t=>t.trim()).filter(Boolean);
 if(lines.length<3||lines.length>18)throw Error('1レースにつき3〜18頭を入力してな。');
 const seen=new Set(),names=new Set(),rows=[];
 for(const [index,line] of lines.entries()){
  const parts=line.split(/\s+/);
  if(parts.length!==6&&parts.length!==7)
   throw Error((index+1)+'行目：馬番・（馬名）・調教・近走・適性・血統・展開の順にしてな。');
  const value=Number(parts[0]);
  if(!/^(?:[1-9]|1[0-8])$/.test(parts[0])||seen.has(value))
   throw Error((index+1)+'行目：1〜18の馬番が重複または不正です。');
  seen.add(value);
  const hasName=parts.length===7,name=hasName?parts[1]:'';
  if(name&&(name.length>35||names.has(name)||/[<>]/.test(name)))throw Error('馬名が不正・重複、または長すぎます。');
  if(name)names.add(name);
  const grades=parts.slice(hasName?2:1);
  if(grades.length!==5||grades.some(x=>!Object.hasOwn(GRADE,x)))
   throw Error((index+1)+'行目：5項目はS/A/B/Cのみ入力してな。');
  const numeric=grades.map(x=>GRADE[x]);
  const sum=numeric.reduce((t,n,i)=>t+n*WEIGHTS[i],0);
  const score=sum/4;
  const tier=score>=85?'S':score>=70?'A':score>=55?'B':'C';
  rows.push({number:value,name,grades,numeric,score,tier});
 }
 rows.sort((a,b)=>b.score-a.score||
  b.numeric[0]-a.numeric[0]||b.numeric[2]-a.numeric[2]||
  b.numeric[1]-a.numeric[1]||b.numeric[4]-a.numeric[4]||
  b.numeric[3]-a.numeric[3]||a.number-b.number);
 return rows;
}
function combinations(first,second,third){
 const tickets=new Set();
 for(const a of first)for(const b of second)for(const c of third){
  if(a!==b&&a!==c&&b!==c)tickets.add(a+'-'+b+'-'+c);
 }
 return tickets.size;
}
function planFormation(rows,extraFirst=null){
 const top=rows.map(x=>x.number);
 if(extraFirst!==null&&!top.slice(2,5).includes(extraFirst))
  throw Error('1着の追加は総合3〜5位の馬番を1頭だけ選んでください。');
 const first=top.slice(0,Math.min(2,top.length));
 if(extraFirst!==null)first.push(extraFirst);
 const second=top.slice(0,Math.min(4,top.length));
 let third=top.slice(0,Math.min(8,top.length));
 let points=combinations(first,second,third);
 // Three winner candidates increase points. Concentrate third choices
 // instead of silently exceeding the 48-ticket budget.
 if(extraFirst!==null){
  while(points>40&&third.length>3){
   third=third.slice(0,-1);
   points=combinations(first,second,third);
  }
 }
 if(!points||points>48)throw Error('フォーメーションを48点以内に組めませんでした。');
 return {first,second,third,points};
}
const WIN_FACTORS=['調教','近走','適性','血統','展開'];
function reconsiderWin(rows){
 return rows.slice(2,5).map((horse,i)=>{
  const basis=[0,1,2,4].filter(k=>horse.numeric[k]>=3);
  return {
   number:horse.number,rank:i+3,
   gradeFactors:basis.map(k=>WIN_FACTORS[k]),
   reviewFlag:basis.length>=2&&(horse.numeric[0]>=3||horse.numeric[4]>=3)
  };
 });
}
function displayFormation(p){
 const formation=p.formation,rows=p.rows;
 $('scoreFormation').className='score-form';
 $('scoreFormation').textContent='1着 '+formation.first.join('・')+
  '／2着 '+formation.second.join('・')+'／3着 '+formation.third.join('・')+
  '　＝ '+formation.points+'点／100円なら'+(formation.points*100).toLocaleString('ja-JP')+
  '円（未購入・未保存）。'+
  (p.extraFirst!==null?'総合3〜5位の1頭を本人操作で追加。点数を40点以内にするため3着候補を絞っています。':'')+
  (rows[0].score<70?'最高評価でも70点未満。買うか見送るかは慎重に判断してな。':'');
}
function renderWinnerReview(p){
 const host=$('scoreWinnerReview');host.replaceChildren();
 const panel=document.createElement('div'),title=document.createElement('h3'),note=document.createElement('p');
 panel.className='winner-review';
 title.textContent='1着候補の再点検（総合3〜5位）';
 note.textContent='過去の反省を踏まえ、調教・近走・適性・展開のA以上が複数ある馬を再確認。これは本人入力の項目チェックであり、勝率・AI評価ではありません。候補追加は本人が明示選択した場合だけ。';
 panel.append(title,note);
 const defaults=document.createElement('button');
 defaults.type='button';defaults.className='winner-review-btn';
 defaults.setAttribute('aria-pressed',String(p.extraFirst===null));
 defaults.textContent='1着は基本2頭のまま（'+p.rows.slice(0,2).map(x=>x.number).join('・')+'番）';
 defaults.onclick=()=>updateWinnerChoice(null);
 panel.append(defaults);
 for(const item of reconsiderWin(p.rows)){
  const b=document.createElement('button');b.type='button';
  b.className='winner-review-btn';
  b.setAttribute('aria-pressed',String(p.extraFirst===item.number));
  b.textContent='総合'+item.rank+'位・'+item.number+'番を1着候補に追加'+
   (item.reviewFlag?'｜A以上の材料：'+item.gradeFactors.join('・'):'｜勝ち切り材料は要確認');
  b.onclick=()=>updateWinnerChoice(item.number);
  panel.append(b);
 }
 const foot=document.createElement('small');
 foot.textContent='追加すると1着候補3頭・3着候補を絞った40点以内の案に変更。追加しても保存・購入はしません。';
 panel.append(foot);host.append(panel);
}
function updateWinnerChoice(number){
 const p=preview;
 if(!p||p.raw!==$('scoreInput').value){
  invalidate();return;
 }
 try{
  if(JSON.stringify(identity())!==JSON.stringify(p.select))
   throw Error('別のレースへ変更されています。');
  verifyMemoHasNotChanged();
  p.formation=planFormation(p.rows,number);
  p.extraFirst=number;
  displayFormation(p);renderWinnerReview(p);
  $('scoreStatus').textContent=number===null?
   '基本の2頭軸に戻しました（未保存・未購入）。':
   number+'番を1着候補に追加して再計算しました（手動見直し・未保存・未購入）。';
 }catch(e){
  invalidate();
  $('scoreStatus').textContent='1着候補の見直しを停止：'+
   (e instanceof Error?e.message:'もう一度採点してください。');
 }
}
function invalidate(){
 preview=null;$('scoreHandoff').disabled=true;
 $('scoreRanks').replaceChildren();$('scoreWinnerReview').replaceChildren();
 $('scoreFormation').textContent='入力が変わりました。再計算してください。';
 $('scoreStatus').textContent='未計算です。計算しても保存・購入されません。';
}
function savedNoteValid(x){
 return x&&typeof x==='object'&&dateValid(x.date)&&TRACKS.has(x.track)&&
  Number.isInteger(x.race)&&x.race>=1&&x.race<=12&&
  typeof x.text==='string'&&x.text.length>0&&x.text.length<=4000&&
  typeof x.savedAt==='string'&&x.savedAt.length>=10&&x.savedAt.length<=32&&
  (x.sourceMark===null||(typeof x.sourceMark==='string'&&x.sourceMark.length>0&&x.sourceMark.length<=1500))&&
  (!Object.hasOwn(x,'researchSource')||
    [RESEARCH_DRAFT_TAG,PREDAY_RESEARCH_TAG].includes(x.researchSource))&&
  (!Object.hasOwn(x,'predaySourceMark')||
    (x.researchSource===PREDAY_RESEARCH_TAG&&typeof x.predaySourceMark==='string'&&
     x.predaySourceMark.length>=20&&x.predaySourceMark.length<=1500))&&
  (x.researchSource!==PREDAY_RESEARCH_TAG||Object.hasOwn(x,'predaySourceMark'));
}
function noteKey(x){return x.date+'|'+x.track+'|'+x.race}
function notesRead(){
 const rows=JSON.parse(localStorage.getItem(NOTE_KEY)||'[]');
 if(!Array.isArray(rows)||rows.length>MAX_NOTES||!rows.every(savedNoteValid)||
    new Set(rows.map(noteKey)).size!==rows.length)
  throw Error('途中評価の保存形式が不正です。上書きを停止しました。');
 return rows;
}
function saveDraft(){
 try{
  const choice=identity(),raw=$('scoreInput').value;
  if(raw.length>4000)throw Error('評価の入力は4000文字以内にしてな。');
  const saved=notesRead(),id=noteKey(choice);
  const rest=saved.filter(x=>noteKey(x)!==id);
  if(raw.trim()){
   if(rest.length>=MAX_NOTES)throw Error('途中評価の保存上限300Rです。');
   rest.push({...choice,text:raw,sourceMark:memoSourceMark,
    ...(researchSource?{researchSource}:{}),
    ...(predaySourceMark?{predaySourceMark}:{}),savedAt:new Date().toISOString()});
  }
  localStorage.setItem(NOTE_KEY,JSON.stringify(rest));
  $('scoreDraftStatus').textContent=raw.trim()?
   choice.track+choice.race+'Rの途中評価をこの端末に保存しました（購入・予想確定ではありません）。':
   'このRの途中評価を端末から消去しました。';
 }catch(e){
  $('scoreDraftStatus').textContent='端末内保存に失敗：'+(e instanceof Error?e.message:'容量を確認してな。');
 }
 renderDayGrid();
}
$('scoreRetryDraft').onclick=()=>saveDraft();
const LABELS=['調教','近走','適性','血統','展開'];
const RESEARCH_DRAFT_TAG='jrdb-two-factor-research-v1';
const PREDAY_RESEARCH_TAG='jrdb-preday-roster-v1';
const PREDAY_KEY='keiba-nine-jrdb-preday-runners-v1';
let memoRows=null,researchSource=null;
function resetMemoGrid(){
 memoRows=null;memoSourceMark=null;predaySourceMark=null;$('scoreMemoGrid').replaceChildren();
 $('scorePaceStatus').textContent='脚質は前日情報の馬番を読み込むと表示します（未確認は未確認のまま）。';
}
function readPredayRace(choice){
 const raw=JSON.parse(localStorage.getItem(PREDAY_KEY)||'[]');
 if(!Array.isArray(raw)||raw.length>48)throw Error('前日情報の形式を確認できません。');
 const day=raw.find(x=>x&&x.kind==='jrdb-preday-provisional'&&
  x.date===choice.date&&x.track===choice.track);
 const race=day&&Array.isArray(day.races)&&day.races.find(x=>x&&x.race===choice.race);
 if(!race||!Number.isInteger(race.expected)||race.expected<3||race.expected>18||
    !/^\d\d:\d\d$/.test(race.postTime)||!Array.isArray(race.runners)||
    race.runners.length!==race.expected)
  throw Error(choice.track+choice.race+'Rの前日情報が未取り込みです。');
 const used=new Set(),names=new Set(),rows=[];
 for(const h of race.runners){
  if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
     typeof h.name!=='string'||!h.name||h.name.length>35||
     !/^[^\s<>]+$/.test(h.name)||!['逃','先','差','追','未確認'].includes(h.style)||
     used.has(h.number)||names.has(h.name))
   throw Error('前日情報の馬番・馬名・脚質が不正です。');
  used.add(h.number);names.add(h.name);
  rows.push({number:h.number,name:h.name,style:h.style,grades:['?','?','?','?','?']});
 }
 return {rows:rows.sort((a,b)=>a.number-b.number),
  sourceMark:JSON.stringify([race.postTime,race.expected,race.runners])};
}
function predayNoteMatches(note){
 if(!note||!note.predaySourceMark)return true;
 const live=readPredayRace(note);
 if(live.sourceMark!==note.predaySourceMark)return false;
 const lines=note.text.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 if(lines.length!==live.rows.length)return false;
 const names=new Map();
 for(const line of lines){
  const m=/^([1-9]|1[0-8])\s+([^\s<>]+)\s+(?:[SABC?]\s+){4}[SABC?]$/.exec(line);
  if(!m||names.has(+m[1]))return false;
  names.set(+m[1],m[2]);
 }
 return live.rows.every(r=>names.get(r.number)===r.name);
}

function memoNoteMatches(note){
 if(!note||note.sourceMark===null)return true;
 const live=readMatchingMemo(note);
 if(live.sourceMark!==note.sourceMark)return false;
 const lines=note.text.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
 if(lines.length!==live.rows.length)return false;
 const names=new Map();
 for(const line of lines){
  const match=/^([1-9]|1[0-8])\s+([^\s<>]+)\s+(?:[SABC?]\s+){4}[SABC?]$/.exec(line);
  if(!match||names.has(Number(match[1])))return false;
  names.set(Number(match[1]),match[2]);
 }
 return live.rows.every(row=>names.get(row.number)===row.name);
}
function scoreNoteState(note){
 if(!note)return {text:'未着手',className:'score-empty'};
 if(note.predaySourceMark){
  try{if(!predayNoteMatches(note))return {text:'要再確認（前日情報変更）',className:'score-stale'};}
  catch(_){return {text:'要再確認（前日情報不明）',className:'score-stale'};}
 }
 if(note.sourceMark!==null){
  try{if(!memoNoteMatches(note))return {text:'要再確認',className:'score-stale'};}
  catch(_){return {text:'要再確認',className:'score-stale'};}
 }
 try{parseGrades(note.text);return {text:note.researchSource?'採点済・研究用':'採点済',className:'score-done'};}
 catch(_){return {text:note.researchSource?'途中・研究用':'途中',className:'score-partial'};}
}
function renderDayGrid(){
 const grid=$('scoreRaceGrid'),venueGrid=$('scoreVenueGrid');
 $('scoreNextPending').disabled=true;
 grid.replaceChildren();venueGrid.replaceChildren();
 let selected;
 try{selected=identity();}
 catch(_){
  $('scoreDayStatus').textContent='日付・競馬場・1〜12Rを選んでな。';
  $('scoreAllDayStatus').textContent='正しい日付と競馬場を選択してな。';
  return;
 }
 let notes;
 try{notes=notesRead();}
 catch(e){
  $('scoreDayStatus').textContent='保存済み評価の読み込み不可：'+
   (e instanceof Error?e.message:'端末の記録を確認してな。');
  $('scoreAllDayStatus').textContent='保存済みの全場の進捗を安全に読み取れません。';
  return;
 }
 const today=notes.filter(x=>x.date===selected.date);
 const allStates=today.map(x=>scoreNoteState(x).className);
 const totalDone=allStates.filter(x=>x==='score-done').length;
 const totalStale=allStates.filter(x=>x==='score-stale').length;
 const totalPartial=allStates.filter(x=>x==='score-partial').length;
 $('scoreAllDayStatus').textContent=selected.date+' 全場合計：'+today.length+
  'R登録／採点済'+totalDone+'R／途中'+totalPartial+
  'R／要再確認'+totalStale+'R。'+
  (today.length===36?'36Rの入力枠あり。':'未登録の開催・Rは集計対象外。')+
  'JRA公式出走・取消未照合。';
 $('scoreNextPending').disabled=totalPartial+totalStale===0;
 // Render only venues backed by notes on the selected date. A 36R count
 // is not evidence that JRA actually has those starts or runners confirmed.
 for(const track of TRACKS){
  const entries=today.filter(x=>x.track===track);
  if(!entries.length)continue;
  const states=entries.map(x=>scoreNoteState(x).className);
  const graded=states.filter(x=>x==='score-done').length;
  const stale=states.filter(x=>x==='score-stale').length;
  const pending=states.filter(x=>x==='score-partial').length;
  const button=document.createElement('button');
  button.type='button';
  button.className=stale?'score-stale':pending?'score-partial':'score-done';
  button.textContent=track+'　'+entries.length+'/12R｜採点済'+graded+
   '・途中'+pending+'・再確認'+stale;
  button.setAttribute('aria-pressed',String(track===selected.track));
  button.onclick=()=>{
   try{
    const from=identity(),fresh=notesRead();
    if(currentScoreHasUnsavedInput()){
     $('scoreVenueStatus').textContent='現在の入力と保存済み評価が違います。移動せず入力を確認してな。';
     return;
    }
    const actual=fresh.filter(x=>x.date===from.date&&x.track===track);
    if(!actual.length)throw Error('この会場の保存済みRがなくなりました。');
    const target=actual.filter(x=>{
     const state=scoreNoteState(x).className;
     return state==='score-partial'||state==='score-stale';
    }).sort((a,b)=>a.race-b.race)[0]||
     actual.slice().sort((a,b)=>a.race-b.race)[0];
    if(track!==from.track||target.race!==from.race){
     $('scoreTrack').value=track;$('scoreRace').value=String(target.race);
     changeScoreRace();
    }
    $('scoreVenueStatus').textContent=from.date+' '+track+target.race+
     'Rを開きました（'+scoreNoteState(target).text+'）。JRA公式未照合。';
   }catch(e){
    $('scoreVenueStatus').textContent='会場を移動できません：'+
     (e instanceof Error?e.message:'保存内容を確認してな。');
   }
  };
  venueGrid.append(button);
 }
 const mine=today.filter(x=>x.track===selected.track);
 const byRace=new Map(mine.map(x=>[x.race,x]));
 let done=0,partial=0,stale=0;
 for(let race=1;race<=12;race++){
  const status=scoreNoteState(byRace.get(race));
  if(status.className==='score-done')done++;
  if(status.className==='score-partial')partial++;
  if(status.className==='score-stale')stale++;
  const button=document.createElement('button');
  button.type='button';button.className=status.className;
  button.textContent=race+'R　'+status.text;
  button.setAttribute('aria-pressed',String(race===selected.race));
  button.onclick=()=>{
   if(Number($('scoreRace').value)===race)return;
   $('scoreRace').value=String(race);
   changeScoreRace();
  };
  grid.append(button);
 }
 $('scoreDayStatus').textContent=selected.date+' '+selected.track+
  '：採点済'+done+'R／途中'+partial+'R／要再確認'+stale+
  'R／未着手'+(12-done-partial-stale)+'R。'+
  '同日の全会場の保存メモ'+today.length+'R（公式出走表は未照合）。';
}
$('scoreNextPending').onclick=()=>{
 try{
  const selected=identity(),all=notesRead();
  const today=all.filter(x=>x.date===selected.date);
  // Do not bypass protection for stale-source notes with newly typed text.
  if(currentScoreHasUnsavedInput()){
   $('scoreNextPendingStatus').textContent='このRの入力が保存済みメモと違います。現在の評価を確認してから移動してな。';
   return;
  }
  const candidates=today.filter(x=>{
   const state=scoreNoteState(x).className;
   return state==='score-partial'||state==='score-stale';
  }).sort((a,b)=>a.race-b.race||
     [...TRACKS].indexOf(a.track)-[...TRACKS].indexOf(b.track));
  if(!candidates.length){
   $('scoreNextPendingStatus').textContent='選択日の保存済みRに未評価・要再確認はありません（未登録Rは含みません）。';
   renderDayGrid();return;
  }
  const currentIndex=candidates.findIndex(x=>noteKey(x)===noteKey(selected));
  const next=candidates[(currentIndex+1)%candidates.length];
  const currentKey=noteKey(selected);
  if(noteKey(next)!==currentKey){
   $('scoreTrack').value=next.track;$('scoreRace').value=String(next.race);
   changeScoreRace();
  }
  $('scoreNextPendingStatus').textContent=selected.date+' '+next.track+next.race+
   'Rへ移動。'+scoreNoteState(next).text+'。前日資料に基づく手動評価で、公式出走・取消は未照合。';
 }catch(e){
  $('scoreNextPendingStatus').textContent='次のRを開けません：'+
   (e instanceof Error?e.message:'保存内容を確認してな。');
 }
};
let lastScoreSelection=null;
function currentScoreHasUnsavedInput(){
 // The current textarea belongs to lastScoreSelection, not necessarily the
 // newly selected controls. A corrupt storage snapshot must block navigation.
 if(!lastScoreSelection)return Boolean($('scoreInput').value.trim());
 try{
  const previous=notesRead().find(x=>noteKey(x)===noteKey(lastScoreSelection));
  const stale=previous&&scoreNoteState(previous).className==='score-stale';
  const raw=$('scoreInput').value;
  return stale?Boolean(raw.trim()):raw!==(previous?.text||'');
 }catch(_){return true;}
}
function changeScoreRace(){
 let requested;
 try{requested=identity();}catch(_){requested=null;}
 if(lastScoreSelection&&(!requested||
     noteKey(lastScoreSelection)!==noteKey(requested))){
  if(currentScoreHasUnsavedInput()){
   $('scoreDate').value=lastScoreSelection.date;
   $('scoreTrack').value=lastScoreSelection.track;
   $('scoreRace').value=String(lastScoreSelection.race);
   $('scoreNavigationStatus').textContent='未保存の評価があります。移動を止めました。このRを再保存してから切り替えてな。';
   return;
  }
 }
 $('scoreNavigationStatus').textContent='保存されていない評価がある場合は、別Rへの移動を止めます。';
 resetMemoGrid();researchSource=null;invalidate();restoreCurrentNote();renderDayGrid();
 $('scoreMemoStatus').textContent='本人の馬番メモは必要なら読み込み直してな。';
 lastScoreSelection=requested;
}
for(const id of ['scoreDate','scoreTrack','scoreRace']){
 $(id).oninput=changeScoreRace;$(id).onchange=changeScoreRace;
}
$('scoreTrialJump').onclick=()=>{
 try{
  const c=identity();
  if(currentScoreHasUnsavedInput()||
     (lastScoreSelection&&noteKey(c)!==noteKey(lastScoreSelection))){
   $('scoreTrialJumpStatus').textContent='現在のRに未保存の評価があります。端末に保存してから移動してな。';
   return;
  }
  // Only calendar coordinates travel in the fragment. No names, member
  // source, factor grades, ticket numbers, or credentials leave this page.
  const p=new URLSearchParams({select:'v1',date:c.date,track:c.track,race:String(c.race)});
  window.location.assign('/owner-auto-trial#'+p.toString());
 }catch(e){
  $('scoreTrialJumpStatus').textContent='研究用の試算画面を開けません：'+
   (e instanceof Error?e.message:'開催日・競馬場・Rを確認してな。');
 }
};
function onScoreInputChange(){
 // Textarea edits must never strip the source snapshot from a JRDB pre-day
 // note. Otherwise a valid researchSource could be persisted without its
 // required sourceMark, poisoning the entire owner note store.
 const oldPreday=predaySourceMark;
 resetMemoGrid();
 predaySourceMark=oldPreday;
 invalidate();saveDraft();
}
$('scoreInput').oninput=onScoreInputChange;
$('scoreInput').onchange=onScoreInputChange;
function readMatchingMemo(select){
 const mail=JSON.parse(localStorage.getItem('keiba-nine-jrdb-personal-mail-v1')||'[]');
 const notes=JSON.parse(localStorage.getItem('keiba-nine-owner-manual-numbers-v1')||'[]');
 if(!Array.isArray(mail)||mail.length>48||!Array.isArray(notes)||notes.length>576)
  throw Error('保存資料の形式が不正です。');
 const meeting=mail.find(x=>x&&x.kind==='jrdb-provisional'&&
  x.date===select.date&&x.track===select.track);
 const source=meeting&&Array.isArray(meeting.races)&&meeting.races.find(r=>r&&r.race===select.race);
 const memo=notes.find(x=>x&&x.date===select.date&&x.track===select.track&&x.race===select.race);
 if(!source||!memo||!Array.isArray(source.horses)||!Array.isArray(memo.rows)||
    !Number.isInteger(source.expected)||source.expected<3||source.expected>18||
    source.horses.length!==source.expected||memo.rows.length!==source.expected||
    memo.sourceMark!==JSON.stringify([source.postTime,source.expected,source.horses]))
  throw Error('このRの想定メールと一致する本人馬番メモがありません。');
 const names=new Set(source.horses),usedNumbers=new Set(),usedNames=new Set();
 if(names.size!==source.expected)throw Error('元の想定馬名に重複があります。');
 const rows=[];
 for(const row of memo.rows){
  if(!row||!Number.isInteger(row.number)||row.number<1||row.number>18||
     typeof row.name!=='string'||!row.name||row.name.length>35||
     !/^[^\s<>]+$/.test(row.name)||!names.has(row.name)||
     usedNames.has(row.name)||usedNumbers.has(row.number))
   throw Error('本人メモの馬番・馬名が一致していません。');
  usedNumbers.add(row.number);usedNames.add(row.name);
  rows.push({number:row.number,name:row.name,grades:['?','?','?','?','?']});
 }
 return {rows:rows.sort((a,b)=>a.number-b.number),sourceMark:memo.sourceMark};
}
function verifyMemoHasNotChanged(){
 if(predaySourceMark){
  const choice=identity(),live=readPredayRace(choice);
  const current={...choice,text:$('scoreInput').value,predaySourceMark};
  if(live.sourceMark!==predaySourceMark||!predayNoteMatches(current))
   throw Error('JRDB前日情報の馬番・馬名が変更または一致しません。再照合してな。');
  if(memoRows&&(live.rows.length!==memoRows.length||
     live.rows.some((r,i)=>r.number!==memoRows[i].number||r.name!==memoRows[i].name)))
   throw Error('採点画面の馬番・馬名が更新されています。');
  return;
 }
 if(!memoRows)return;
 const live=readMatchingMemo(identity());
 if(live.sourceMark!==memoSourceMark||live.rows.length!==memoRows.length||live.rows.some((r,i)=>
  r.number!==memoRows[i].number||r.name!==memoRows[i].name))
  throw Error('本人の馬番メモが更新されています。公式出馬表を確認して読み込み直してください。');
}
function renderMemoInput(){
 $('scoreInput').value=memoRows.map(row=>
  row.number+' '+row.name+' '+row.grades.join(' ')).join('\n');
 invalidate();
 const missing=memoRows.reduce((n,row)=>n+row.grades.filter(x=>x==='?').length,0);
 $('scoreMemoStatus').textContent=(researchSource===PREDAY_RESEARCH_TAG?'JRDB前日資料から':'本人メモから')+memoRows.length+'頭を表示。未評価'+missing+
  '項目。すべてS/A/B/Cで選んでから計算してな（公式馬番・取消は未確認）。';
 saveDraft();
}

function drawMemoGrid(){
 const grid=$('scoreMemoGrid');
 if(predaySourceMark){
  try{
   const live=readPredayRace(identity());
   const counts={逃:0,先:0,差:0,追:0,未確認:0};
   for(const r of live.rows)counts[r.style]++;
   $('scorePaceStatus').textContent='JRDB前日情報の脚質（本人用・未検証）：'+
    ['逃','先','差','追','未確認'].map(k=>k+counts[k]).join('・')+
    '。未確認の新馬などは自動補完しません。これだけで展開S/A/B/Cは付けません。';
  }catch(_){$('scorePaceStatus').textContent='脚質情報を再確認できません。前日資料を確認してな。';}
 }

 for(const row of memoRows){
   const card=document.createElement('div'),name=document.createElement('strong'),fields=document.createElement('div');
   card.className='memo-horse';fields.className='memo-horse-fields';
   name.textContent=row.number+'番 '+row.name+(row.style?'｜脚質 '+row.style+'（前日資料）':'');card.append(name);
   for(let index=0;index<LABELS.length;index++){
    const label=document.createElement('label'),menu=document.createElement('select');
    label.textContent=LABELS[index];
    menu.setAttribute('aria-label',row.number+'番 '+row.name+' '+LABELS[index]);
    for(const value of ['', 'S', 'A', 'B', 'C']){
     const option=document.createElement('option');
     option.value=value;option.textContent=value||'未評価';
     menu.append(option);
    }
    menu.value=Object.hasOwn(GRADE,row.grades[index])?row.grades[index]:'';
    menu.onchange=()=>{
     if(!memoRows)return;
     row.grades[index]=Object.hasOwn(GRADE,menu.value)?menu.value:'?';
     renderMemoInput();
    };
    label.append(menu);fields.append(label);
   }
   card.append(fields);grid.append(card);
  }
}
$('scoreFromMemo').onclick=()=>{
 try{
  const choice=identity();
  const roster=readMatchingMemo(choice);
  if($('scoreInput').value.trim()&&!confirm('現在の5項目入力を置き換えて、本人の馬番・馬名メモから'+
   roster.rows.length+'頭を読み込みますか？ 現在の評価入力は上書きされます。'))return;
  resetMemoGrid();researchSource=null;
  memoRows=roster.rows;memoSourceMark=roster.sourceMark;
  drawMemoGrid();
  renderMemoInput();
 }catch(e){
  $('scoreMemoStatus').textContent='読み込めません：'+(e instanceof Error?e.message:'資料を確認してな。');
 }
};

$('scoreFromPreday').onclick=()=>{
 try{
  const c=identity(),src=readPredayRace(c);
  if($('scoreInput').value.trim()&&
     !confirm(c.track+c.race+'Rの現在の入力を、JRDB前日情報の馬番だけで置き換えますか？\n評価はすべて未評価に戻ります。'))return;
  resetMemoGrid();memoRows=src.rows;memoSourceMark=null;
  predaySourceMark=src.sourceMark;researchSource=PREDAY_RESEARCH_TAG;
  drawMemoGrid();renderMemoInput();
  $('scorePredayStatus').textContent=c.track+c.race+'Rの'+src.rows.length+
   '頭を仮入力。採点は未評価。前日資料のためJRA公式出馬表・取消を別途照合してください。';
 }catch(e){$('scorePredayStatus').textContent='このRを取り込めません：'+
  (e instanceof Error?e.message:'資料を確認してな。');}
};
$('scoreSeedPredayDay').onclick=()=>{
 try{
  const date=$('scoreDate').value;
  if(!dateValid(date))throw Error('先に正しい日付を選んでな。');
  const source=JSON.parse(localStorage.getItem(PREDAY_KEY)||'[]');
  if(!Array.isArray(source)||source.length>48)
   throw Error('JRDB前日情報の保存形式が不正です。');
  const day=source.filter(x=>x&&x.date===date&&x.kind==='jrdb-preday-provisional');
  if(!day.length)throw Error('この開催日の前日情報がありません。先にメールを取り込んでな。');
  const all=[];
  for(const m of day){
   if(!TRACKS.has(m.track)||!Array.isArray(m.races)||m.races.length>12)
    throw Error('前日情報の競馬場かレース数が不正です。');
   for(const race of m.races){
    const choice={date,track:m.track,race:race.race},src=readPredayRace(choice);
    all.push({...choice,text:src.rows.map(h=>h.number+' '+h.name+' ? ? ? ? ?').join('\n'),
     sourceMark:null,predaySourceMark:src.sourceMark,
     researchSource:PREDAY_RESEARCH_TAG,savedAt:new Date().toISOString()});
   }
  }
  if(!all.length||all.length>36||new Set(all.map(noteKey)).size!==all.length)
   throw Error('全Rの件数または重複が不正です。');
  const old=notesRead(),existing=new Set(old.map(noteKey));
  const additions=all.filter(x=>!existing.has(noteKey(x)));
  if(!additions.length){
   $('scorePredayStatus').textContent='この日の前日情報にある全Rは登録済み。既存評価は上書きしません。';
   return;
  }
  if(old.length+additions.length>MAX_NOTES)throw Error('評価メモ300Rの上限に達します。');
  if(currentScoreHasUnsavedInput())throw Error('現在のRに未保存の評価があります。再保存してから一括仮登録してな。');
  if(!confirm(date+'：JRDB前日資料'+day.length+'開催から未登録'+additions.length+
    'Rの馬番を仮入力しますか？\n既存の途中採点・買い目・実購入記録は変更しません。'))return;
  localStorage.setItem(NOTE_KEY,JSON.stringify(old.concat(additions)));
  restoreCurrentNote();renderDayGrid();
  $('scorePredayStatus').textContent=date+'：'+additions.length+'Rを馬番だけ仮登録。'+
   '既存'+(all.length-additions.length)+'Rの評価は維持。5項目のAI自動採点・馬券は未実施。'+
   'JRA公式出走・取消の照合も未完了です。';
 }catch(e){$('scorePredayStatus').textContent='全R仮登録できません：'+
  (e instanceof Error?e.message:'前日情報を確認してな。');}
};

function chooseRecentPredayAsDefault(){
 // Auto-select the next saved owner pre-day meeting after the current JST
 // date. Only reading localStorage: never writes, grades, seeds or buys.
 const today=new Date(Date.now()+9*60*60*1000).toISOString().slice(0,10);
 $('scoreDate').value=today;
 let raw=null;
 try{raw=localStorage.getItem(PREDAY_KEY);}
 catch(_){return;}
 if(!raw)return;
 try{
  const meetings=JSON.parse(raw);
  if(!Array.isArray(meetings)||meetings.length>48||
    new Set(meetings.map(x=>x?.date+'|'+x?.track)).size!==meetings.length||
    !meetings.every(x=>x&&x.kind==='jrdb-preday-provisional'&&
      dateValid(x.date)&&TRACKS.has(x.track)&&Array.isArray(x.races)&&
      x.races.length>=1&&x.races.length<=12&&
      x.races.every(r=>r&&Number.isInteger(r.race)&&r.race>=1&&r.race<=12)))
   throw Error('invalid pre-day records');
  const order=[...TRACKS];
  const upcoming=meetings.filter(x=>x.date>=today).sort((a,b)=>
    a.date.localeCompare(b.date)||order.indexOf(a.track)-order.indexOf(b.track));
  if(!upcoming.length)return;
  const m=upcoming[0],races=m.races.map(x=>x.race);
  $('scoreDate').value=m.date;
  $('scoreTrack').value=m.track;
  $('scoreRace').value=String(races.includes(1)?1:Math.min(...races));
  const count=meetings.filter(x=>x.date===m.date).length;
  $('scorePredayStatus').textContent=m.date+'の前日情報を検出。'+
   count+'競馬場から'+m.track+'を自動選択したで。'+
   '全R仮登録は下のボタンで本人確認後に実施。JRA公式未照合。';
 }catch(_){
  $('scorePredayStatus').textContent='前日情報の保存形式に問題があります。'+
   '確認するまで自動選択せず、元の記録は上書きしません。';
 }
}
chooseRecentPredayAsDefault();
function receiveRaceSelection(){
 if(!window.location||typeof window.location.hash!=='string'||
    !window.location.hash.startsWith('#select='))return;
 const fragment=window.location.hash;
 try{
  if(fragment.length>170)throw Error('指定が長すぎます。');
  const p=new URLSearchParams(fragment.slice(1));
  const keys=['select','date','track','race'];
  const seedRequested=p.get('seed')==='day-v1';
  const expectedKeys=seedRequested?[...keys,'seed']:keys;
  if([...p.keys()].length!==expectedKeys.length||
     expectedKeys.some(k=>p.getAll(k).length!==1)||
     p.get('select')!=='v1')throw Error('形式が不正です。');
  const date=p.get('date'),track=p.get('track'),race=Number(p.get('race'));
  if(!dateValid(date)||!TRACKS.has(track)||!Number.isInteger(race)||race<1||race>12)
   throw Error('日付・競馬場・Rが不正です。');
  $('scoreDate').value=date;$('scoreTrack').value=track;$('scoreRace').value=String(race);
  $('scoreStatus').textContent=date+' '+track+race+'Rを選択。本人の馬番メモを読み込むか、5項目を入力してな。';
  if(seedRequested){
   // Only the private pre-day link requests seeding. The scorecard's
   // confirmation dialog and its no-overwrite checks still gate writes.
   $('scoreSeedPredayDay').onclick();
  }
 }catch(e){
  $('scoreStatus').textContent='レース選択を受け取れませんでした：'+
   (e instanceof Error?e.message:'形式を確認してな。');
 }finally{
  try{window.history&&window.history.replaceState(null,'',window.location.pathname+window.location.search)}
  catch(_){}
 }
}
receiveRaceSelection();

function restoreCurrentNote(){
 resetMemoGrid();
 $('scoreInput').value='';
 try{
  const selected=identity();
  const note=notesRead().find(x=>noteKey(x)===noteKey(selected));
  researchSource=note?.researchSource||null;
  if(!note){
   $('scoreDraftStatus').textContent='このレースの途中評価はまだ保存されていません。';
   return;
  }
  if(note.predaySourceMark&&!predayNoteMatches(note))
   throw Error('JRDB前日情報が変更されています。評価を自動復元できません。');
  if(note.sourceMark!==null){
   const live=readMatchingMemo(selected);
   if(live.sourceMark!==note.sourceMark)
    throw Error('元の想定メール・馬番メモが更新されています。保存済み評価は自動復元しません。');
   const lines=note.text.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
   if(lines.length!==live.rows.length)throw Error('保存した馬番と現在の資料の頭数が違います。');
   const graded=new Map();
   for(const line of lines){
    const match=/^([1-9]|1[0-8])\s+([^\s<>]+)\s+([SABC?])\s+([SABC?])\s+([SABC?])\s+([SABC?])\s+([SABC?])$/.exec(line);
    if(!match||graded.has(Number(match[1])))throw Error('保存した評価行の形式が不正です。');
    graded.set(Number(match[1]),{name:match[2],grades:match.slice(3)});
   }
   for(const row of live.rows){
    const old=graded.get(row.number);
    if(!old||old.name!==row.name)throw Error('保存した馬番・馬名が現在の資料と異なります。');
    row.grades=old.grades;
   }
   memoRows=live.rows;memoSourceMark=live.sourceMark;
   drawMemoGrid();
  }else{
   // Ordinary owner notes (including JRDB research-only 2-factor prefill)
   // can reopen selector fields after relaunch. Unknown or malformed rows
   // remain untouched free text; nothing is inferred or silently corrected.
   const lines=note.text.split(/\r?\n/).map(x=>x.trim()).filter(Boolean);
   if(lines.length>=3&&lines.length<=18){
    const seenNums=new Set(),seenNames=new Set(),parsed=[];
    let valid=true;
    for(const line of lines){
     const parts=line.split(/\s+/),hasName=parts.length===7;
     const num=Number(parts[0]),name=hasName?parts[1]:'';
     const grades=parts.slice(hasName?2:1);
     if((parts.length!==6&&parts.length!==7)||
        !/^(?:[1-9]|1[0-8])$/.test(parts[0])||
        seenNums.has(num)||name.length>35||
        (name&&!/^[^\s<>]+$/.test(name))||
        (name&&seenNames.has(name))||
        grades.length!==5||grades.some(g=>!['S','A','B','C','?'].includes(g))){
      valid=false;break;
     }
     seenNums.add(num);if(name)seenNames.add(name);
     parsed.push({number:num,name,grades});
    }
    if(valid){
     if(note.predaySourceMark){
      const fresh=readPredayRace(selected);
      const byNumber=new Map(fresh.rows.map(h=>[h.number,h.style]));
      for(const row of parsed)row.style=byNumber.get(row.number)||'未確認';
     }
     memoRows=parsed;memoSourceMark=null;
     predaySourceMark=note.predaySourceMark||null;drawMemoGrid();
    }
   }
  }
  $('scoreInput').value=note.text;
  $('scoreDraftStatus').textContent=selected.track+selected.race+
   'Rの途中評価を端末から復元しました（未購入・未確定）。'+
   (researchSource===PREDAY_RESEARCH_TAG?
     'JRDB前日資料の馬番を使った本人評価。JRA公式未照合。':
     (researchSource?'JRDB研究用の未検証2項目を含みます。公式未照合。':''));
 }catch(e){
  resetMemoGrid();
  $('scoreInput').value='';
  $('scoreDraftStatus').textContent='途中評価を復元できません：'+
   (e instanceof Error?e.message:'端末内の記録を確認してな。');
 }
}
$('scoreClearDraft').onclick=()=>{
 try{
  const selected=identity();
  if(!confirm(selected.date+' '+selected.track+selected.race+
   'Rの途中評価を、この端末内から削除しますか？\n3連単下書きと購入記録は変更しません。'))return;
  const rest=notesRead().filter(x=>noteKey(x)!==noteKey(selected));
  localStorage.setItem(NOTE_KEY,JSON.stringify(rest));
  resetMemoGrid();researchSource=null;$('scoreInput').value='';invalidate();
  $('scoreDraftStatus').textContent='このRの途中評価を削除しました。購入・下書きには変更なし。';
  renderDayGrid();
 }catch(e){
  $('scoreDraftStatus').textContent='削除できません：'+
   (e instanceof Error?e.message:'端末保存の状態を確認してな。');
 }
};
restoreCurrentNote();renderDayGrid();
// Initialise the navigation guard even when the chosen race came from a
// one-time pre-day URL hash, before the first oninput/onchange event.
try{lastScoreSelection=identity();}catch(_){lastScoreSelection=null;}

/* Owner-only, explicit one-time JRDB RESEARCH prefill; never an AI forecast. */
function receiveResearchPrefill(){
 if(typeof window==='undefined'||!window.location||
    window.location.hash!=='#research=v1')return;
 try{if(window.history&&typeof window.history.replaceState==='function')
  window.history.replaceState(null,'',
   window.location.pathname+(window.location.search||''));}catch(_){}
 if(typeof sessionStorage==='undefined'){
  $('scoreMemoStatus').textContent='研究用の仮入力を受け取れません：一時領域がありません。';return;
 }
 const KEY='keiba-nine-owner-research-scorecard-handoff-v1';
 let raw;
 try{raw=sessionStorage.getItem(KEY);sessionStorage.removeItem(KEY);}
 catch(_){$('scoreMemoStatus').textContent='研究用の仮入力を読み取れません。';return;}
 try{
  if(!raw||raw.length>4800)throw Error('一時データが見つからないか大きすぎます。');
  const d=JSON.parse(raw);
  const keys=['version','createdAt','date','track','race','researchOnly',
              'officialJraVerified','predictionReady','runners'];
  if(!d||typeof d!=='object'||Object.keys(d).length!==keys.length||
     keys.some(k=>!Object.hasOwn(d,k))||
     d.version!=='jrdb-research-to-scorecard-v1'||
     d.researchOnly!==true||d.officialJraVerified!==false||
     d.predictionReady!==false||!dateValid(d.date)||!TRACKS.has(d.track)||
     !Number.isInteger(d.race)||d.race<1||d.race>12||
     !Array.isArray(d.runners)||d.runners.length<3||d.runners.length>18)
   throw Error('研究用2項目の形式・開催情報が不正です。');
  const when=Date.parse(d.createdAt),age=Date.now()-when;
  if(typeof d.createdAt!=='string'||!Number.isFinite(when)||
     !Number.isFinite(age)||age<0||age>600000)
   throw Error('仮入力が期限切れです。');
  const seen=new Set(),allowed=['S','A','B','C','未評価'],rows=[];
  for(const h of d.runners){
   if(!h||typeof h!=='object'||Object.keys(h).length!==3||
      !Object.hasOwn(h,'number')||!Object.hasOwn(h,'training')||
      !Object.hasOwn(h,'recent')||!Number.isInteger(h.number)||
      h.number<1||h.number>18||seen.has(h.number)||
      !allowed.includes(h.training)||!allowed.includes(h.recent))
    throw Error('馬番と暫定2項目が一致していません。');
   seen.add(h.number);
   rows.push({number:h.number,name:'',
    grades:[h.training==='未評価'?'?':h.training,
            h.recent==='未評価'?'?':h.recent,'?','?','?']});
  }
  if(!rows.some(h=>h.grades[0]!=='?'||h.grades[1]!=='?'))
   throw Error('引き継げる調教・近走の仮評価がありません。');
  const target={date:d.date,track:d.track,race:d.race};
  // Opening the research transfer must not silently replace the previous
  // race's unsaved text, even if the owner agreed to replace the target R.
  if(lastScoreSelection&&noteKey(lastScoreSelection)!==noteKey(target)&&
      currentScoreHasUnsavedInput())
   throw Error('現在のRに未保存の評価があります。再保存してから研究用データを開いてな。');
  const existing=notesRead().find(n=>n.date===d.date&&n.track===d.track&&n.race===d.race);
  if((existing||$('scoreInput').value.trim())&&!confirm(
    '既存の評価をJRDB研究用の調教・近走2項目で置き換えますか？\n適性・血統・展開は未評価になります。'))return;
  $('scoreDate').value=d.date;$('scoreTrack').value=d.track;
  $('scoreRace').value=String(d.race);
  changeScoreRace();
  if(noteKey(identity())!==noteKey(target))
   throw Error('現在のRに未保存の評価があります。研究用の引き継ぎを停止しました。');
  resetMemoGrid();memoRows=rows.sort((a,b)=>a.number-b.number);
  memoSourceMark=null;researchSource=RESEARCH_DRAFT_TAG;
  drawMemoGrid();renderMemoInput();
  $('scoreMemoStatus').textContent=d.track+d.race+
   'RのJRDB研究用・未検証の調教／近走だけを仮入力。'+
   '適性・血統・展開は全馬未評価。公式出走表・取消も未照合です。';
  $('scoreStatus').textContent='研究用の暫定2項目を受け取りました。'+
   '実戦AI予想や3連単は未作成です。';
 }catch(e){
  $('scoreMemoStatus').textContent='研究用の仮入力を受け取れません：'+
   (e instanceof Error?e.message:'内容を確認してください。');
 }
}
receiveResearchPrefill();

$('scoreReview').onclick=()=>{
 invalidate();
 try{
  verifyMemoHasNotChanged();
  const select=identity(),raw=$('scoreInput').value,rows=parseGrades(raw);
  const formation=planFormation(rows),host=$('scoreRanks');
  for(let index=0;index<rows.length;index++){
   const r=rows[index],line=document.createElement('div'),header=document.createElement('strong'),details=document.createElement('small');
   line.className='score-row score-'+r.tier.toLowerCase();
   header.textContent=(index+1)+'位　'+r.number+'番'+(r.name?' '+r.name:'')+
     '　総合'+r.tier+'　'+r.score.toFixed(1)+'点';
   details.textContent='調教 '+r.grades[0]+'／近走 '+r.grades[1]+'／適性 '+
    r.grades[2]+'／血統 '+r.grades[3]+'／展開 '+r.grades[4];
   line.append(header,details);host.append(line);
  }
  preview={raw,select,rows,formation,extraFirst:null};
  displayFormation(preview);
  renderWinnerReview(preview);
  $('scoreStatus').textContent=select.date+' '+select.track+select.race+'R：'+rows.length+
   '頭の保存評価を計算しました。'+
   (researchSource===PREDAY_RESEARCH_TAG?
     'JRDB前日資料の仮馬番を使用（JRA公式未照合）。5項目は本人入力。':
     (researchSource?'JRDB研究用の未検証2項目を含み、公式未照合。':'本人入力による仮評価。'))+
   'AIの実戦予想ではなく、人気・オッズは未使用。';
  $('scoreHandoff').disabled=false;
 }catch(e){
  $('scoreStatus').textContent='計算できません：'+(e instanceof Error?e.message:'入力を確認してな。');
 }
};
$('scoreHandoff').onclick=()=>{
 const p=preview;
 if(!p||p.raw!==$('scoreInput').value){
  invalidate();$('scoreStatus').textContent='入力が変わりました。再計算してな。';return;
 }
 let current;
 try{current=identity();}catch(_){invalidate();return;}
 if(JSON.stringify(current)!==JSON.stringify(p.select)){invalidate();return;}
 try{verifyMemoHasNotChanged()}catch(e){
  invalidate();$('scoreStatus').textContent='引き継ぎ停止：'+(e instanceof Error?e.message:'馬番メモが更新されました。');return;
 }
 if(!confirm('本人の5項目から計算した3連単'+p.formation.points+
  '点を、未保存の下書きとして渡しますか？\n'+
  (researchSource===PREDAY_RESEARCH_TAG?
     'JRDB前日資料の仮馬番です。JRA公式照合が必要です。\n':
     (researchSource?'JRDB研究用の未検証2項目を含みます。公式確認が必要です。\n':''))+
  'AIの実馬予想ではありません。移動先でも確認してください。'))return;
 const query=new URLSearchParams();
 query.set('import','v1');query.set('date',current.date);
 query.set('track',current.track);query.set('race',String(current.race));
 for(const key of ['first','second','third'])query.set(key,p.formation[key].join(','));
 // URL fragment is not sent to Render. Contains ONLY date/venue/race/numbers.
 window.location.assign('/my-tickets#'+query.toString());
};

/* Private one-day bulk conversion of SAVED, fully manual five-factor notes.
 * No JRDB/JRA/AI inference. The temporary handoff contains race coordinates
 * and number-only formations, never grades, names or licensed raw materials.
 */
const SCORE_DAY_TRANSFER='keiba-nine-scorecard-bulk-transfer-v1';
let pendingScoreDay=null;
function clearScoreDay(message){
 pendingScoreDay=null;
 $('scoreDayTransfer').disabled=true;
 $('scoreDayBatchText').value='';
 $('scoreDayBatchPreview').replaceChildren();
 $('scoreDayBatchStatus').textContent=message||'未計算。手入力の採点済みレースだけが対象です。';
}
function compileScoreDay(date){
 if(!dateValid(date))throw Error('先に正しい開催日を選んでな。');
 const day=notesRead().filter(note=>note.date===date);
 if(day.length>36)throw Error('この日の保存評価が36Rを超えています。不要な記録を整理してください。');
 const ready=[],skipped=[];
 for(const note of day){
  const state=scoreNoteState(note);
  if(state.className!=='score-done'){
   skipped.push(note.track+note.race+'R：'+state.text);
   continue;
  }
  const rows=parseGrades(note.text);
  const formation=planFormation(rows);
  if(formation.points<1||formation.points>48)throw Error(note.track+note.race+'Rの点数が不正です。');
  ready.push({...note,formation,extraFirst:null,gradedRows:rows,winReview:reconsiderWin(rows),headcount:rows.length,topScore:rows[0].score,
   ranked:rows.map((horse,index)=>({number:horse.number,tier:horse.tier,score:horse.score,rank:index+1}))});
 }
 const trackOrder=[...TRACKS];
 ready.sort((a,b)=>trackOrder.indexOf(a.track)-trackOrder.indexOf(b.track)||a.race-b.race);
 return recomputeScoreDay({
  date,ready,skipped,
  // Detect edits to saved notes and source provenance before navigating.
  snapshot:JSON.stringify(day),
 });
}
function recomputeScoreDay(day){
 const text=day.ready.map(x=>[
  x.date+' '+x.track+x.race+'R',
  '1着：'+x.formation.first.join('・'),
  '2着：'+x.formation.second.join('・'),
  '3着：'+x.formation.third.join('・'),
 ].join('\n')).join('\n\n');
 if(text.length>25000||day.ready.length>36)
  throw Error('一括入力の上限を超えています。');
 day.text=text;day.count=day.ready.length;
 day.points=day.ready.reduce((n,x)=>n+x.formation.points,0);
 return day;
}
function renderScoreDayBatch(result){
 const host=$('scoreDayBatchPreview');host.replaceChildren();
 for(const item of result.ready){
  const card=document.createElement('div');card.className='score-day-batch-card';
  const h=document.createElement('strong'),p=document.createElement('span');
  h.textContent=item.track+item.race+'R｜'+item.formation.points+
   '点／'+(item.formation.points*100).toLocaleString('ja-JP')+'円相当';
  p.textContent='1着 '+item.formation.first.join('・')+
   ' ／ 2着 '+item.formation.second.join('・')+
   ' ／ 3着 '+item.formation.third.join('・')+
   '（'+item.headcount+'頭の本人入力評価から計算。未購入）';
  const flagged=item.winReview.filter(x=>x.reviewFlag);
  const warning=document.createElement('span');
  warning.className=flagged.length?'winner-review-flag':'';
  warning.textContent=flagged.length?
   '1着候補の再点検：'+flagged.map(x=>x.rank+'位'+x.number+'番（'+x.gradeFactors.join('・')+'）').join('／')+
   '。追加する場合は下のボタンで選択してください。':
   '総合3〜5位の追加1着候補は、本人入力の基準では自動抽出されませんでした。';
  const ranks=document.createElement('details'),title=document.createElement('summary');
  ranks.className='score-day-ranks';
  title.textContent='全馬の総合評価順を見る（手入力5項目）';
  ranks.append(title);
  for(const horse of item.ranked){
   const line=document.createElement('p');
   line.className='score-'+horse.tier.toLowerCase();
   line.textContent=horse.rank+'位 '+horse.number+'番　総合'+horse.tier+
     ' '+horse.score.toFixed(1)+'点';
   ranks.append(line);
  }
  const controls=document.createElement('details'),heading=document.createElement('summary');
  controls.className='score-day-win';
  heading.textContent='このRの1着候補を見直す（上位2頭／最大3頭）';
  controls.append(heading);
  const choices=[{number:null,rank:0,reviewFlag:false},...item.winReview];
  for(const choice of choices){
   const button=document.createElement('button');button.type='button';
   button.className='score-day-first-btn';
   button.setAttribute('aria-pressed',String(item.extraFirst===choice.number));
   button.textContent=choice.number===null?
    '基本2頭のまま（'+item.gradedRows.slice(0,2).map(h=>h.number).join('・')+'）':
    '総合'+choice.rank+'位 '+choice.number+'番を1着に追加'+
    (choice.reviewFlag?'｜A以上 '+choice.gradeFactors.join('・'):'｜勝ち切り根拠は要確認');
   button.onclick=()=>changeScoreDayWinner(noteKey(item),choice.number);
   controls.append(button);
  }
  if(item.researchSource===RESEARCH_DRAFT_TAG)
   warning.textContent+='【研究用】JRDBの未検証な調教・近走の仮評価を含みます。JRA公式未照合。';
  if(item.researchSource===PREDAY_RESEARCH_TAG)
   warning.textContent+='【前日資料】JRDBの仮馬番に基づく本人評価で、JRA公式出走・取消は未照合。';
  card.append(h,p,warning,ranks,controls);host.append(card);
 }
 $('scoreDayBatchText').value=result.text;
 $('scoreDayBatchStatus').textContent=result.date+'：'+result.count+
  'Rの手動採点を一括計算／'+result.points+'点、100円換算'+
  (result.points*100).toLocaleString('ja-JP')+'円（未購入）。'+
  (result.skipped.length?'除外：'+result.skipped.join('／')+'。':'')+
  '3〜5位の1着候補追加は本人選択のみ。JRA公式出走・取消は未照合。';
}
function changeScoreDayWinner(key,extraFirst){
 const pending=pendingScoreDay;
 if(!pending||pending.date!==$('scoreDate').value)return;
 try{
  const current=compileScoreDay(pending.date);
  if(current.snapshot!==pending.snapshot)
   throw Error('保存済み評価の元データが変更されました。');
  const item=pending.ready.find(x=>noteKey(x)===key);
  const source=current.ready.find(x=>noteKey(x)===key);
  if(!item||!source||pending.ready.length!==current.ready.length)
   throw Error('対象Rが変更されました。');
  const next=planFormation(source.gradedRows,extraFirst);
  item.formation=next;item.extraFirst=extraFirst;
  recomputeScoreDay(pending);
  renderScoreDayBatch(pending);
  $('scoreDayTransfer').disabled=false;
 }catch(e){
  clearScoreDay('1着候補を変更できません：'+
   (e instanceof Error?e.message:'再計算してください。'));
 }
}
$('scoreDayBuild').onclick=()=>{
 clearScoreDay();
 try{
  const date=$('scoreDate').value,result=compileScoreDay(date);
  if(!result.count)throw Error('この日に手入力の5項目が完成したレースはありません。');
  renderScoreDayBatch(result);
  pendingScoreDay=result;
  $('scoreDayTransfer').disabled=false;
 }catch(e){
  clearScoreDay('一括計算できません：'+(e instanceof Error?e.message:'評価を確認してください。'));
 }
};
$('scoreDayTransfer').onclick=()=>{
 const planned=pendingScoreDay;
 if(!planned||planned.date!==$('scoreDate').value||
    planned.text!==$('scoreDayBatchText').value){
  clearScoreDay('開催日・内容が変更されました。再計算してな。');return;
 }
 let current;
 try{current=compileScoreDay(planned.date);}
 catch(e){
  clearScoreDay('保存元の再検査に失敗：'+(e instanceof Error?e.message:'再計算してください。'));return;
 }
 if(!current.count||current.snapshot!==planned.snapshot||
    current.ready.length!==planned.ready.length){
  clearScoreDay('端末内の評価や元資料が更新されています。もう一度一括計算してな。');return;
 }
 try{
  for(let i=0;i<current.ready.length;i++){
   const now=current.ready[i],old=planned.ready[i];
   if(noteKey(now)!==noteKey(old))throw Error('レースの順序が変わりました。');
   now.formation=planFormation(now.gradedRows,old.extraFirst);
  }
  recomputeScoreDay(current);
  if(current.text!==planned.text||current.points!==planned.points||
     planned.text!==$('scoreDayBatchText').value)
   throw Error('候補を再検証できません。');
 }catch(e){
  clearScoreDay('1着候補・点数が変更されています：'+
   (e instanceof Error?e.message:'再計算してください。'));return;
 }
 if(typeof sessionStorage==='undefined'){
  $('scoreDayBatchStatus').textContent='このブラウザーでは一時的な引き継ぎを使えません。下のテキストを手動でコピーしてな。';
  return;
 }
 if(!confirm(planned.count+'R・'+planned.points+
   '点の3連単候補を下書き画面へ移しますか？\n本人手入力からの自動組立で、実際の予想・購入ではありません。'))return;
 try{
  sessionStorage.setItem(SCORE_DAY_TRANSFER,JSON.stringify({
   version:'scorecard-bulk-v1',
   createdAt:new Date().toISOString(),
   date:planned.date,count:planned.count,
   points:planned.points,text:planned.text,
  }));
 }catch(_){
  $('scoreDayBatchStatus').textContent='一時領域に引き継ぎを保存できませんでした。テキストを手動でコピーしてな。';
  return;
 }
 window.location.assign('/my-tickets#scorebatch=v1');
};
for(const id of ['scoreDate','scoreTrack','scoreRace']){
 const field=$(id),oldInput=field.oninput,oldChange=field.onchange;
 field.oninput=(...args)=>{clearScoreDay();if(oldInput)oldInput(...args)};
 field.onchange=(...args)=>{clearScoreDay();if(oldChange)oldChange(...args)};
}
for(const id of ['scoreInput']){
 const field=$(id),oldInput=field.oninput,oldChange=field.onchange;
 field.oninput=(...args)=>{clearScoreDay();if(oldInput)oldInput(...args)};
 field.onchange=(...args)=>{clearScoreDay();if(oldChange)oldChange(...args)};
}
})();"""
