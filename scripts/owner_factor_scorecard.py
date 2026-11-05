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
</head><body><main><a href="/">← 本人用ホーム</a>
<h1>5項目の手動評価</h1>
<p class="warning">これは<b>本人が入力する仮評価の計算表</b>です。JRA・JRDBの実データ取得、AIによる調教分析、実馬の予想はまだ行っていません。実戦で使う前に公式出馬表・取消を確認してください。</p>
<section><h2>① 開催日・競馬場・レース</h2><div class="fields">
<label for="scoreDate">日付</label><input type="date" id="scoreDate">
<label for="scoreTrack">競馬場</label><select id="scoreTrack">
<option value="">選択してください</option>
<option>札幌</option><option>函館</option><option>福島</option><option>新潟</option><option>東京</option><option>中山</option><option>中京</option><option>京都</option><option>阪神</option><option>小倉</option>
</select>
<label for="scoreRace">レース（1〜12R）</label><input id="scoreRace" type="number" min="1" max="12" step="1" value="1">
</div></section>
<section><h2>② 馬番と5項目の評価を貼る</h2>
<p class="hint">1頭1行で「馬番　調教　近走　適性　血統　展開」を入力。馬名は省略可。各項目は<b>S・A・B・C</b>。丸数字①〜⑱にも対応。最低3頭、最大18頭。</p>
<button type="button" id="scoreFromMemo" class="memo-load">本人の馬番・馬名メモから読み込む（採点は空欄）</button><p id="scoreMemoStatus" role="status" class="hint">JRDBの想定メールと一致する本人転記メモがある場合だけ、馬番・馬名を引き継げます。JRA公式の独立照合ではありません。</p><p id="scoreDraftStatus" role="status" class="hint">途中の評価はこの端末内に自動保存します。購入記録には入りません。</p><div id="scoreMemoGrid" aria-label="本人入力の5項目採点"></div><textarea id="scoreInput" rows="10" maxlength="4000" spellcheck="false" placeholder="① 架空馬A S A A B S&#10;② 架空馬B A A S B A&#10;③ 架空馬C A B A A B&#10;④ 架空馬D B A B S A"></textarea>
<p class="hint">重み：調教25%／近走25%／適性20%／血統10%／展開20%。各項目をS=4、A=3、B=2、C=1として100点換算。人気やオッズは使わない。これは実績ある予測モデルではありません。</p>
<button type="button" id="scoreReview">総合評価と3連単候補を計算</button><button type="button" id="scoreClearDraft" class="clear-note">このRの途中評価を削除</button>
<p id="scoreStatus" role="status" class="hint">入力したデータはこのページ内だけで計算し、保存・送信しません。</p></section>
<section><h2>③ 総合評価順と買い目候補</h2>
<div id="scoreRanks" aria-label="総合評価順"></div>
<p id="scoreFormation" class="hint">評価を計算すると着順候補と実点数を表示します。</p>
<button type="button" id="scoreHandoff" disabled>3連単下書き画面へ渡す（未保存）</button>
<p class="hint">このボタンで引き継ぐのは日付・競馬場・R・馬番の着順候補だけ。馬名・評価・元データはURLやサーバーへ渡しません。移動先でも本人確認があり、保存も馬券購入も自動では行いません。</p>
</section>
<section><h2>判断時の注意</h2><p class="hint">総合S：85点以上、A：70点以上、B：55点以上、C：55点未満（暫定基準）。1着は相対上位2頭、2着は上位4頭、3着は上位8頭まで。点数が少なければ無理に増やしません。S馬がいない場合も相対上位は表示しますが、勝てるという意味ではありません。全着順の馬番が実際に出走するかはJRA公式で別途照合してください。</p>
<a href="/my-tickets">手動で3連単を作る</a></section>
</main><script defer src="/owner-scorecard.js"></script></body></html>"""

CSS = """.clear-note{background:#344a62;color:#ffda9e;border:1px solid #ab826f;margin-top:10px}*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#f1f5ff;font:16px/1.6 system-ui,sans-serif}main{max-width:680px;padding:20px 14px 50px;margin:auto}h1{font-size:27px}h2{font-size:20px;margin:0 0 10px}a{color:#edca70}section{background:#142f4a;border:1px solid #456780;border-radius:14px;padding:17px;margin:16px 0}.warning{padding:12px;background:#322b22;border:1px solid #ae8755;border-radius:10px;color:#ffe7aa;font-size:14px}.hint{font-size:13px;color:#d0dfef;line-height:1.7}.fields{display:grid;gap:5px}.fields label{font-weight:700;margin-top:7px}input,select,textarea{width:100%;font:inherit;background:#0a2238;color:#f4f7ff;border:1px solid #7190ae;border-radius:9px;padding:11px;min-height:46px}textarea{min-height:225px;line-height:1.6}button{width:100%;min-height:49px;font:inherit;font-weight:800;color:#10253d;background:#edca70;border:0;border-radius:10px;padding:12px}button:disabled{opacity:.45}.memo-load{background:#2f506a;color:#ffe5a6;border:1px solid #9eacb8;margin-bottom:9px}.memo-horse{border:1px solid #54758e;border-radius:10px;padding:11px;margin:10px 0}.memo-horse strong{display:block;margin-bottom:5px}.memo-horse-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.memo-horse-fields label{display:block;font-size:12px;color:#d5e7f4}.memo-horse-fields select{min-height:45px;padding:7px}.memo-horse-fields label:nth-child(5){grid-column:1/-1}.score-row{padding:12px;border-bottom:1px solid #365778}.score-row strong{display:block}.score-s{color:#f7d36e}.score-a{color:#ff8f88}.score-b{color:#a3d0fa}.score-c{color:#c9ced5}.score-row small{display:block;font-size:12px;color:#bbccdd}.score-form{padding:13px;background:#11273a;border:1px solid #516f8a;border-radius:9px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}"""

JS = r"""(()=>{'use strict';
/* No network or writes: read optional same-browser manually copied roster; grades remain operator-entered. */
const $=id=>document.getElementById(id);
const TRACKS=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
const GRADE=Object.freeze({S:4,A:3,B:2,C:1});
const WEIGHTS=Object.freeze([25,25,20,10,20]);
const NOTE_KEY='keiba-nine-owner-factor-notes-v1',MAX_NOTES=300;
const CIRCLES='①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱';
let preview=null,suppressDraftWrite=false,memoSourceMark=null;
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
function planFormation(rows){
 const top=rows.map(x=>x.number);
 const first=top.slice(0,Math.min(2,top.length));
 const second=top.slice(0,Math.min(4,top.length));
 const third=top.slice(0,Math.min(8,top.length));
 const points=combinations(first,second,third);
 if(!points||points>48)throw Error('フォーメーションを48点以内に組めませんでした。');
 return {first,second,third,points};
}
function invalidate(){
 preview=null;$('scoreHandoff').disabled=true;
 $('scoreRanks').replaceChildren();
 $('scoreFormation').textContent='入力が変わりました。再計算してください。';
 $('scoreStatus').textContent='未計算です。計算しても保存・購入されません。';
}
function savedNoteValid(x){
 return x&&typeof x==='object'&&dateValid(x.date)&&TRACKS.has(x.track)&&
  Number.isInteger(x.race)&&x.race>=1&&x.race<=12&&
  typeof x.text==='string'&&x.text.length>0&&x.text.length<=4000&&
  typeof x.savedAt==='string'&&x.savedAt.length>=10&&x.savedAt.length<=32&&
  (x.sourceMark===null||(typeof x.sourceMark==='string'&&x.sourceMark.length>0&&x.sourceMark.length<=1500));
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
 if(suppressDraftWrite)return;
 try{
  const choice=identity(),raw=$('scoreInput').value;
  if(raw.length>4000)throw Error('評価の入力は4000文字以内にしてな。');
  const saved=notesRead(),id=noteKey(choice);
  const rest=saved.filter(x=>noteKey(x)!==id);
  if(raw.trim()){
   if(rest.length>=MAX_NOTES)throw Error('途中評価の保存上限300Rです。');
   rest.push({...choice,text:raw,sourceMark:memoSourceMark,savedAt:new Date().toISOString()});
  }
  localStorage.setItem(NOTE_KEY,JSON.stringify(rest));
  $('scoreDraftStatus').textContent=raw.trim()?
   choice.track+choice.race+'Rの途中評価をこの端末に保存しました（購入・予想確定ではありません）。':
   'このRの途中評価を端末から消去しました。';
 }catch(e){
  $('scoreDraftStatus').textContent='端末内保存に失敗：'+(e instanceof Error?e.message:'容量を確認してな。');
 }
}
const LABELS=['調教','近走','適性','血統','展開'];
let memoRows=null;
function resetMemoGrid(){
 memoRows=null;memoSourceMark=null;$('scoreMemoGrid').replaceChildren();
}
function changeScoreRace(){
 resetMemoGrid();invalidate();restoreCurrentNote();
 $('scoreMemoStatus').textContent='本人の馬番メモは必要なら読み込み直してな。';
}
for(const id of ['scoreDate','scoreTrack','scoreRace']){
 $(id).oninput=changeScoreRace;$(id).onchange=changeScoreRace;
}
$('scoreInput').oninput=()=>{resetMemoGrid();invalidate();saveDraft()};
$('scoreInput').onchange=()=>{resetMemoGrid();invalidate();saveDraft()};
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
 $('scoreMemoStatus').textContent='本人メモから'+memoRows.length+'頭を表示。未評価'+missing+
  '項目。すべてS/A/B/Cで選んでから計算してな（公式馬番・取消は未確認）。';
 saveDraft();
}

function drawMemoGrid(){
 const grid=$('scoreMemoGrid');
 for(const row of memoRows){
   const card=document.createElement('div'),name=document.createElement('strong'),fields=document.createElement('div');
   card.className='memo-horse';fields.className='memo-horse-fields';
   name.textContent=row.number+'番 '+row.name;card.append(name);
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
  resetMemoGrid();
  memoRows=roster.rows;memoSourceMark=roster.sourceMark;
  drawMemoGrid();
  renderMemoInput();
 }catch(e){
  $('scoreMemoStatus').textContent='読み込めません：'+(e instanceof Error?e.message:'資料を確認してな。');
 }
};
$('scoreDate').value=new Date(Date.now()+9*60*60*1000).toISOString().slice(0,10);
function receiveRaceSelection(){
 if(!window.location||typeof window.location.hash!=='string'||
    !window.location.hash.startsWith('#select='))return;
 const fragment=window.location.hash;
 try{
  if(fragment.length>170)throw Error('指定が長すぎます。');
  const p=new URLSearchParams(fragment.slice(1));
  const keys=['select','date','track','race'];
  if([...p.keys()].length!==4||keys.some(k=>p.getAll(k).length!==1)||
     p.get('select')!=='v1')throw Error('形式が不正です。');
  const date=p.get('date'),track=p.get('track'),race=Number(p.get('race'));
  if(!dateValid(date)||!TRACKS.has(track)||!Number.isInteger(race)||race<1||race>12)
   throw Error('日付・競馬場・Rが不正です。');
  $('scoreDate').value=date;$('scoreTrack').value=track;$('scoreRace').value=String(race);
  $('scoreStatus').textContent=date+' '+track+race+'Rを選択。本人の馬番メモを読み込むか、5項目を入力してな。';
 }catch(e){
  $('scoreStatus').textContent='レース選択を受け取れませんでした：'+
   (e instanceof Error?e.message:'形式を確認してな。');
 }finally{
  try{window.history&&window.history.replaceState(null,'',window.location.pathname+window.location.search)}
  catch(_){}
 }
}
receiveRaceSelection();

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
  $('scoreFormation').className='score-form';
  $('scoreFormation').textContent='1着 '+formation.first.join('・')+
   '／2着 '+formation.second.join('・')+'／3着 '+formation.third.join('・')+
   '　＝ '+formation.points+'点／100円なら'+(formation.points*100).toLocaleString('ja-JP')+
   '円（未購入・未保存）。'+
   (rows[0].score<70?'最高評価でも70点未満。買うか見送るかは慎重に判断してな。':'');
  $('scoreStatus').textContent=select.date+' '+select.track+select.race+'R：'+rows.length+
   '頭の手入力評価を計算しました。AI予想ではなく、人気・オッズは未使用。';
  preview={raw,select,rows,formation};
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
 if(!confirm('本人入力の5項目から計算した3連単'+p.formation.points+
  '点を、未保存の下書きとして渡しますか？\nAIの実馬予想ではありません。移動先でも確認してください。'))return;
 const query=new URLSearchParams();
 query.set('import','v1');query.set('date',current.date);
 query.set('track',current.track);query.set('race',String(current.race));
 for(const key of ['first','second','third'])query.set(key,p.formation[key].join(','));
 // URL fragment is not sent to Render. Contains ONLY date/venue/race/numbers.
 window.location.assign('/my-tickets#'+query.toString());
};
})();"""
