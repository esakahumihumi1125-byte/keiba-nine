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
<textarea id="scoreInput" rows="10" maxlength="4000" spellcheck="false" placeholder="① 架空馬A S A A B S&#10;② 架空馬B A A S B A&#10;③ 架空馬C A B A A B&#10;④ 架空馬D B A B S A"></textarea>
<p class="hint">重み：調教25%／近走25%／適性20%／血統10%／展開20%。各項目をS=4、A=3、B=2、C=1として100点換算。人気やオッズは使わない。これは実績ある予測モデルではありません。</p>
<button type="button" id="scoreReview">総合評価と3連単候補を計算</button>
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

CSS = """*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#f1f5ff;font:16px/1.6 system-ui,sans-serif}main{max-width:680px;padding:20px 14px 50px;margin:auto}h1{font-size:27px}h2{font-size:20px;margin:0 0 10px}a{color:#edca70}section{background:#142f4a;border:1px solid #456780;border-radius:14px;padding:17px;margin:16px 0}.warning{padding:12px;background:#322b22;border:1px solid #ae8755;border-radius:10px;color:#ffe7aa;font-size:14px}.hint{font-size:13px;color:#d0dfef;line-height:1.7}.fields{display:grid;gap:5px}.fields label{font-weight:700;margin-top:7px}input,select,textarea{width:100%;font:inherit;background:#0a2238;color:#f4f7ff;border:1px solid #7190ae;border-radius:9px;padding:11px;min-height:46px}textarea{min-height:225px;line-height:1.6}button{width:100%;min-height:49px;font:inherit;font-weight:800;color:#10253d;background:#edca70;border:0;border-radius:10px;padding:12px}button:disabled{opacity:.45}.score-row{padding:12px;border-bottom:1px solid #365778}.score-row strong{display:block}.score-s{color:#f7d36e}.score-a{color:#ff8f88}.score-b{color:#a3d0fa}.score-c{color:#c9ced5}.score-row small{display:block;font-size:12px;color:#bbccdd}.score-form{padding:13px;background:#11273a;border:1px solid #516f8a;border-radius:9px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}"""

JS = r"""(()=>{'use strict';
/* No network, storage, AI, or member-data ingestion: only operator-entered grades. */
const $=id=>document.getElementById(id);
const TRACKS=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
const GRADE=Object.freeze({S:4,A:3,B:2,C:1});
const WEIGHTS=Object.freeze([25,25,20,10,20]);
const CIRCLES='①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱';
let preview=null;
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
  if(name&&(name.length>35||names.has(name)))throw Error('馬名が長すぎるか重複しています。');
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
for(const id of ['scoreDate','scoreTrack','scoreRace','scoreInput']){
 $(id).oninput=invalidate;$(id).onchange=invalidate;
}
$('scoreDate').value=new Date(Date.now()+9*60*60*1000).toISOString().slice(0,10);
$('scoreReview').onclick=()=>{
 invalidate();
 try{
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
