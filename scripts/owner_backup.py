"""Owner-only complete local backup for an iPhone home-screen web app.

No member data is read by Python. This module only serves static UI code.
All personal and licensed records remain in the owner's browser or their
chosen private backup file. Never send backups to public GitHub or Render.
"""

HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>競馬ナイン｜本人用まとめてバックアップ</title>
<link rel="stylesheet" href="/owner-backup.css"></head><body><main>
<a href="/">← 本人用ホームへ</a>
<h1>本人用データのバックアップ</h1>
<p class="warning">この画面は端末内だけで動作します。JRDB想定メール・本人の馬番メモを含む場合があるため、ファイルは個人用に保管し、公開・共有しないでください。サーバー・Google・GitHubに自動送信しません。</p>
<section><h2>今の保存内容</h2><p id="backupSummary" role="status">端末内を確認します。</p>
<button id="backupDownload" type="button">6種類の記録を1つのJSONに保存</button>
<p class="hint">3連単の下書き／実際の購入記録／JRDB想定メールから転記した記録／本人が照合した馬番メモ／5項目評価の途中メモ／前日情報（馬番・馬名・脚質）をまとめて書き出します。保存先はiPhoneの「ファイル」など自分で管理できる場所を選んでください。</p></section>
<section><h2>別の端末・Safariから復元</h2>
<label for="backupFile">上で保存したJSONを選択</label>
<input id="backupFile" type="file" accept=".json,application/json">
<p id="backupPreview" class="hint" role="status">選択しただけでは復元しません。内容を検査し、6種類すべての現在の記録を置き換える前に確認します。</p>
<button id="backupRestore" type="button" disabled>確認して6種類の記録を復元</button>
<p class="warning">復元は現在の6種類の記録を全件上書きします。実購入記録も含まれます。必ず先に今のデータを書き出してください。復元後はページを開き直すと新しい記録が見えます。</p></section>
<section><h2>知っておきたいこと</h2><p class="hint">ホーム画面版とSafariは別の保存領域になる場合があります。「ホーム画面に追加した同じアプリ」からバックアップ・復元してください。JSONはパスワードで暗号化されていません。JRDBの有料情報を含む場合は会員本人以外へ渡さないでください。</p>
<a href="/my-tickets">3連単下書き・購入記録へ</a></section>
</main><script defer src="/owner-backup.js"></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#eef3fc;font:16px/1.6 system-ui,sans-serif}main{max-width:670px;padding:20px 14px 50px;margin:auto}h1{font-size:25px}h2{font-size:19px;margin:0 0 8px}a{color:#f3d17e}section{background:#162d49;border:1px solid #47637f;border-radius:15px;padding:16px;margin:16px 0}.warning{padding:12px;background:#322c23;border:1px solid #aa8952;color:#ffeba9;border-radius:10px;font-size:13px}.hint{font-size:13px;color:#ccdbeb}button{width:100%;margin:12px 0;min-height:48px;background:#edca70;color:#14253b;font:inherit;font-weight:800;border:0;border-radius:10px}button:disabled{opacity:.45}input{width:100%;min-height:46px;padding:10px;margin:8px 0;border:1px solid #8096aa;border-radius:10px;color:#fff;background:#0a2037}label{display:block;font-weight:700}"""

JS = r"""(()=>{'use strict';
/* Local-only backup: browser storage + user-selected private files, no upload. */
const KEYS=[
 'keiba-nine-owner-ticket-drafts-v1',
 'keiba-nine-owner-real-purchases-v1',
 'keiba-nine-jrdb-personal-mail-v1',
 'keiba-nine-owner-manual-numbers-v1',
 'keiba-nine-owner-factor-notes-v1',
 'keiba-nine-jrdb-preday-runners-v1'
];
const FORMAT='keiba-nine-owner-local-all-v3',LEGACY_V2='keiba-nine-owner-local-all-v2',LEGACY_V1='keiba-nine-owner-local-all-v1', LIMIT=2500000;
const TRACKS=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
const $=id=>document.getElementById(id);
const raceKey=x=>x.date+'|'+x.track+'|'+x.race;
function validDate(x){
 if(typeof x!=='string'||!/^20\d{2}-\d{2}-\d{2}$/.test(x))return false;
 const date=new Date(x+'T12:00:00Z');
 return Number.isFinite(date.valueOf())&&date.toISOString().slice(0,10)===x;
}
function numbers(a){
 return Array.isArray(a)&&a.length<=18&&a.every(x=>Number.isInteger(x)&&x>=1&&x<=18)&&new Set(a).size===a.length;
}
function points(x){
 const found=new Set();
 for(const a of x.first)for(const b of x.second)for(const c of x.third)
  if(a!==b&&a!==c&&b!==c)found.add(a+'-'+b+'-'+c);
 return found.size;
}
function race(x){
 return x&&typeof x==='object'&&validDate(x.date)&&TRACKS.has(x.track)&&
 Number.isInteger(x.race)&&x.race>=1&&x.race<=12;
}
function selection(x){
 return race(x)&&numbers(x.first)&&numbers(x.second)&&numbers(x.third)&&
 points(x)>=1&&points(x)<=48;
}
function draft(x){
 return selection(x)&&typeof x.savedAt==='string'&&x.savedAt.length<=32&&
 (!Object.prototype.hasOwnProperty.call(x,'result')||
  x.result===null||validFinish(x.result));
}
function validFinish(x){
 return Array.isArray(x)&&x.length===3&&
  x.every(n=>Number.isInteger(n)&&n>=1&&n<=18)&&new Set(x).size===3;
}
function purchase(x){
 return selection(x)&&typeof x.id==='string'&&/^[0-9a-z-]{1,80}$/.test(x.id)&&
 Number.isSafeInteger(x.unit)&&x.unit>=100&&x.unit<=100000&&x.unit%100===0&&
 Number.isSafeInteger(x.stake)&&x.stake===points(x)*x.unit&&
 (x.payout===null||(Number.isSafeInteger(x.payout)&&x.payout>=0))&&
 (!Object.prototype.hasOwnProperty.call(x,'result')||
  x.result===null||validFinish(x.result))&&
 typeof x.purchasedAt==='string'&&x.purchasedAt.length<=32;
}
function sourceRace(x){
 return x&&Number.isInteger(x.race)&&x.race>=1&&x.race<=12&&
 typeof x.postTime==='string'&&/^([01]\d|2[0-3]):[0-5]\d$/.test(x.postTime)&&
 Number.isInteger(x.expected)&&x.expected>=1&&x.expected<=18&&
 Array.isArray(x.horses)&&x.horses.length===x.expected&&
 x.horses.every(name=>typeof name==='string'&&name.length>=1&&name.length<=35)&&
 new Set(x.horses).size===x.horses.length;
}
function mail(x){
 return x&&x.kind==='jrdb-provisional'&&validDate(x.date)&&TRACKS.has(x.track)&&
 Array.isArray(x.races)&&x.races.length>=1&&x.races.length<=12&&
 x.races.every(sourceRace)&&new Set(x.races.map(r=>r.race)).size===x.races.length;
}
function preday(x){
 if(!x||x.kind!=='jrdb-preday-provisional'||!validDate(x.date)||!TRACKS.has(x.track)||
   !Array.isArray(x.races)||x.races.length<1||x.races.length>12)return false;
 const seen=new Set();
 return x.races.every(r=>{
  if(!r||!Number.isInteger(r.race)||r.race<1||r.race>12||seen.has(r.race)||
   typeof r.postTime!=='string'||!/^([01]\d|2[0-3]):[0-5]\d$/.test(r.postTime)||
   !Number.isInteger(r.expected)||r.expected<3||r.expected>18||
   !Array.isArray(r.runners)||r.runners.length!==r.expected)return false;
  seen.add(r.race);
  const ids=new Set(),names=new Set();
  return r.runners.every(h=>{
   if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
    typeof h.name!=='string'||h.name.length<1||h.name.length>35||
    !['逃','先','差','追','未確認'].includes(h.style)||
    ids.has(h.number)||names.has(h.name))return false;
   ids.add(h.number);names.add(h.name);return true;
  });
 });
}
function mapped(x){
 return race(x)&&typeof x.sourceMark==='string'&&x.sourceMark.length<=1500&&
 Array.isArray(x.rows)&&x.rows.length>=1&&x.rows.length<=18&&
 x.rows.every(r=>r&&Number.isInteger(r.number)&&r.number>=1&&r.number<=18&&
 typeof r.name==='string'&&r.name.length>=1&&r.name.length<=35)&&
 new Set(x.rows.map(r=>r.number)).size===x.rows.length&&
 new Set(x.rows.map(r=>r.name)).size===x.rows.length;
}
function scoredNote(x){
 return race(x)&&typeof x.text==='string'&&x.text.length>0&&x.text.length<=4000&&
 typeof x.savedAt==='string'&&x.savedAt.length>=10&&x.savedAt.length<=32&&
 (x.sourceMark===null||
  (typeof x.sourceMark==='string'&&x.sourceMark.length>0&&x.sourceMark.length<=1500))&&
 (!Object.hasOwn(x,'researchSource')||
  ['jrdb-two-factor-research-v1','jrdb-preday-roster-v1'].includes(x.researchSource))&&
 (!Object.hasOwn(x,'predaySourceMark')||
  (x.researchSource==='jrdb-preday-roster-v1'&&
   typeof x.predaySourceMark==='string'&&x.predaySourceMark.length>=20&&
   x.predaySourceMark.length<=1500))&&
 (x.researchSource!=='jrdb-preday-roster-v1'||Object.hasOwn(x,'predaySourceMark'));
}
function sectionsValid(sections,sectionCount=KEYS.length){
 if(!sections||typeof sections!=='object'||Array.isArray(sections)||
    Object.keys(sections).sort().join(',')!==KEYS.slice(0,sectionCount).slice().sort().join(','))throw Error('バックアップの構造が違います。');
 const rules=[{max:300,valid:draft,identity:raceKey},{max:500,valid:purchase,identity:x=>x.id},
  {max:48,valid:mail,identity:x=>x.date+'|'+x.track},
  {max:576,valid:mapped,identity:raceKey},
  {max:300,valid:scoredNote,identity:raceKey},
  {max:48,valid:preday,identity:x=>x.date+'|'+x.track}];
 for(let i=0;i<sectionCount;i++){
  const rows=sections[KEYS[i]],rule=rules[i];
  if(!Array.isArray(rows)||rows.length>rule.max||!rows.every(rule.valid)||
     new Set(rows.map(rule.identity)).size!==rows.length)
   throw Error(['下書き','実購入記録','想定メール','馬番メモ','5項目評価の途中メモ','前日情報'][i]+'の形式が不正か、上限を超えています。');
 }
 const meetings=new Map(sections[KEYS[2]].map(x=>[x.date+'|'+x.track,x]));
 const mappedRows=sections[KEYS[3]];
 let stale=0;
 for(const row of mappedRows){
  const m=meetings.get(row.date+'|'+row.track);
  const source=m&&m.races.find(x=>x.race===row.race);
  if(!source||row.sourceMark!==JSON.stringify([source.postTime,source.expected,source.horses]))stale++;
 }
 let stalePreday=0;
 if(sectionCount===KEYS.length){
  const predays=new Map(sections[KEYS[5]].map(x=>[x.date+'|'+x.track,x]));
  for(const note of sections[KEYS[4]]){
   if(note.researchSource!=='jrdb-preday-roster-v1')continue;
   const m=predays.get(note.date+'|'+note.track),r=m?.races.find(x=>x.race===note.race);
   if(!r||note.predaySourceMark!==JSON.stringify([r.postTime,r.expected,r.runners]))stalePreday++;
  }
 }
 return {counts:KEYS.slice(0,sectionCount).map(k=>sections[k].length),stale,stalePreday};
}
function currentRaw(){
 return KEYS.map(k=>localStorage.getItem(k));
}
function decodeLocal(){
 const sections={};
 for(const k of KEYS)sections[k]=JSON.parse(localStorage.getItem(k)||'[]');
 return sections;
}
function countsLabel(c){
 return '下書き'+c[0]+'R／購入記録'+c[1]+'件／想定メール'+c[2]+'開催／馬番メモ'+c[3]+'R／5項目評価'+(c[4]||0)+'R／前日情報'+(c[5]||0)+'開催';
}
function showCurrent(){
 try{
  const sections=decodeLocal();
  const analysis=sectionsValid(sections);
  $('backupSummary').textContent=countsLabel(analysis.counts)+'。この端末の記録です。';
  $('backupDownload').disabled=false;
 }catch(_){
  $('backupSummary').textContent='保存データに不正な形式があります。個別ページのバックアップを先に確認してな。';
  $('backupDownload').disabled=true;
 }
}
function snapshot(){
 const sections=decodeLocal();sectionsValid(sections);
 const data={format:FORMAT,exportedAt:new Date().toISOString(),sections};
 const raw=JSON.stringify(data);
 if(raw.length>LIMIT)throw Error('データが大きすぎます。個別バックアップを使ってな。');
 return raw;
}
$('backupDownload').onclick=()=>{
 try{
  const payload=snapshot(),blob=new Blob([payload],{type:'application/json;charset=utf-8'});
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='keiba-nine-private-backup-'+new Date().toISOString().slice(0,10)+'.json';
  document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),20000);
  $('backupSummary').textContent='バックアップファイルの保存を開始しました。iPhoneのファイルアプリ等に保存できたか確認してください。';
 }catch(e){
  $('backupSummary').textContent='書き出せません：'+(e instanceof Error?e.message:'保存内容を確認してな。');
 }
};
let pending=null;
function clearPending(){pending=null;$('backupRestore').disabled=true;}
$('backupFile').onchange=async()=>{
 clearPending();
 const chosen=$('backupFile').files&&$('backupFile').files[0];
 if(!chosen){$('backupPreview').textContent='バックアップJSONを選んでください。';return;}
 if(!Number.isInteger(chosen.size)||chosen.size>LIMIT){
  $('backupPreview').textContent='ファイルが大きすぎます（上限2.5MB）。';return;
 }
 try{
  const raw=await chosen.text();
  if(raw.length>LIMIT)throw Error('ファイルが大きすぎます。');
  const parsed=JSON.parse(raw);
  const count=parsed?.format===FORMAT?6:parsed?.format===LEGACY_V2?5:parsed?.format===LEGACY_V1?4:0;
  if(!parsed||(count===0)||!parsed.sections||typeof parsed.exportedAt!=='string'||
     Object.keys(parsed).sort().join(',')!=='exportedAt,format,sections')throw Error('競馬ナインの一括バックアップではありません。');
  sectionsValid(parsed.sections,count);
  const sections={...parsed.sections};
  // Older exports preserve sections they did not know about, without deleting private records.
  const existing=decodeLocal();
  for(let i=count;i<KEYS.length;i++)sections[KEYS[i]]=existing[KEYS[i]];
  const report=sectionsValid(sections);
  const before=currentRaw();
  if(!$('backupFile').files||$('backupFile').files[0]!==chosen)return;
  pending={file:chosen,before,sections,report};
  $('backupRestore').disabled=false;
  $('backupPreview').textContent=countsLabel(report.counts)+
   '。元メールと一致しない馬番メモ'+report.stale+'R。形式検査済み。'+
   (count<6?'旧'+count+'種類のバックアップのため、未収録の記録は現在の端末のまま維持します。':'')+
   '復元すると現在の6種類の記録を置き換えます。';
 }catch(e){
  $('backupPreview').textContent='読み込めません：'+(e instanceof Error?e.message:'ファイルを確認してください。');
 }
};
$('backupRestore').onclick=()=>{
 const p=pending;
 if(!p||!$('backupFile').files||$('backupFile').files[0]!==p.file||
    currentRaw().some((x,i)=>x!==p.before[i])){
  clearPending();$('backupPreview').textContent='選択ファイルまたは現在の記録が変わりました。もう一度選んでな。';return;
 }
 if(!confirm('この端末の下書き・購入記録・想定メール・馬番メモを、バックアップの内容ですべて上書きしますか？\n必ず現在の記録を先にバックアップしてな。'))return;
 try{
  sectionsValid(p.sections);
  for(let i=0;i<KEYS.length;i++)localStorage.setItem(KEYS[i],JSON.stringify(p.sections[KEYS[i]]));
  clearPending();$('backupFile').value='';
  $('backupPreview').textContent='復元しました。本人用の各画面を開き直して内容を確認してな。';
  showCurrent();
 }catch(_){
  // Storage quota can fail on iOS; restore all original values where possible.
  let rolledBack=true;
  for(let i=0;i<KEYS.length;i++){
   try{
    if(p.before[i]===null)localStorage.removeItem(KEYS[i]);
    else localStorage.setItem(KEYS[i],p.before[i]);
   }catch(_){rolledBack=false}
  }
  clearPending();
  $('backupPreview').textContent=rolledBack?
   '保存できず、元の6種類の記録へ戻しました。空き容量を確認してな。':
   '端末の容量不足で完全な復旧を保証できません。アプリ操作を止め、バックアップを保管してください。';
 }
};
showCurrent();
})();"""
