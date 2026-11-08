"""One-click owner-only 36R research view, no source storage or purchases."""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>KEIBA NINE｜JRDB開催日分析</title>
<link rel="stylesheet" href="/owner-jrdb-day-research.css">
</head><body><main>
<nav><a href="/">本人用ホーム</a><a href="/my-tickets">馬券記録（別画面）</a></nav>
<h1>KEIBA NINE <small>本人用・JRDB β版</small></h1>
<h2>開催日ごとの調教・近走を一括確認</h2>
<p class="warning"><strong>仮の2項目評価で、実戦の総合順位や3連単予想ではありません。</strong>
JRA公式の出走取消・馬場・発走時刻と8項目の評価は未接続。
表示は本人の研究用だけで、買い目や購入記録を自動作成・変更しません。</p>
<section>
<label for="day">開催日</label><input type="date" id="day">
<button type="button" id="dayLoad">この日の全Rをまとめて分析</button>
<p class="muted">押したときだけJRDB番組・出走馬・調教・近走を各1回読みます。
キーや元の指数、馬名は表示・保存しません。</p>
<p id="status" role="status" class="muted">開催日を選んで分析を押してな。</p>
</section>
<section>
<h2>レース別の暫定評価</h2>
<p id="stats" class="muted">未取得</p>
<div id="venueFilters" class="venue-filters" role="group" aria-label="競馬場で絞り込み"></div>
<p id="venueStats" class="muted" aria-live="polite"></p>
<div id="results"></div>
</section>
<p class="muted">Sは金色、Aは赤色。順位は調教と近走の両方がある馬だけの
仮並びで、勝率・総合評価・購入推奨ではありません。
未評価の馬を過小評価しないようにします。</p>
</main><script src="/owner-jrdb-day-research.js" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}
body{background:#09172b;color:#eef4ff;margin:0;font:15px/1.6 system-ui,sans-serif}
main{max-width:760px;margin:auto;padding:18px 14px 46px}
h1{font-size:25px;color:#f3d17f;margin:14px 0}h1 small{display:block;font-size:13px;color:#cddded}
h2{font-size:18px;margin:5px 0 12px}nav{display:flex;gap:16px}
a{color:#f6da93}section{background:#152c44;border:1px solid #4d6b89;
padding:14px;border-radius:13px;margin:14px 0}
.warning{background:#322b25;color:#ffe5b4;border:1px solid #9b8355;
padding:12px;border-radius:10px;font-size:13px}
.muted{color:#bdcee1;font-size:13px}
input,button{width:100%;padding:12px;font:inherit;border-radius:10px;
min-height:46px;margin:6px 0 8px}
input{background:#0f2439;color:#fff;border:1px solid #8aa3bc}
button{background:#e8c774;color:#182b41;border:0;font-weight:800}
button:disabled{opacity:.6}
.venue-filters{display:flex;flex-wrap:wrap;gap:7px}
.venue-filter{width:auto;flex:1 1 100px;min-height:44px;margin:3px 0 7px;
 background:#29445e;color:#f2f6fc;border:1px solid #6485a5}
.venue-filter[aria-pressed="true"]{background:#e8c774;color:#182b41;border-color:#e8c774}
details{margin:9px 0;background:#12263c;border:1px solid #476581;border-radius:10px;padding:10px}
summary{cursor:pointer;color:#f4ddaa;font-weight:700;font-size:14px}
.race-badge{display:inline-block;color:#c3deed;font-size:12px;padding-left:6px}
.runner-row{background:#203952;border-radius:8px;display:flex;flex-wrap:wrap;
align-items:center;gap:7px;padding:9px;margin:7px 0}
.number{font-size:19px;font-weight:850;min-width:42px}
.rank{color:#c3d1e4;font-size:12px;min-width:49px}
.grade{font-size:13px;font-weight:800;background:#344d64;border-radius:6px;padding:3px 7px}
.grade-S{color:#f0d078}.grade-A{color:#ff9ea7}
.grade-B{color:#9bd2fd}.grade-C{color:#c4cbd6}
.observed{font-size:12px;color:#bfccdc;flex-basis:100%}
.error{color:#ffc1b5}
@media(max-width:380px){.number{min-width:35px}.rank{min-width:43px}.runner-row{gap:5px}}"""

JS = """(()=>{'use strict';
const $=id=>document.getElementById(id);
const GRADES=new Set(['S','A','B','C','未評価']);
const POS={frontObserved:'過去4角：前方観測',backObserved:'過去4角：後方観測',
 mixedObserved:'過去4角：混在',insufficient:'過去4角：資料不足'};
function dom(tag,text,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n;}
function checkDetails(race){
 const d=race.research;
 if(!d||d.version!=='jrdb-owner-runner-research-1'||!d.privateOwnerOnly||
    !d.researchOnly||d.overallRankReady!==false||d.officialJraVerified!==false||
    d.predictionReady!==false||d.bettingReady!==false||
    d.track!==race.track||d.race!==race.race||
    !Array.isArray(d.runners)||d.runners.length>18||d.runnerCount!==d.runners.length)
   throw Error('馬番別データの形式が不正です');
 const seen=new Set();let both=0;
 for(const h of d.runners){
  if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
      seen.has(h.number)||!GRADES.has(h.training)||!GRADES.has(h.recent)||
      !Object.prototype.hasOwnProperty.call(POS,h.pastFourthCorner)||
      !Number.isInteger(h.completeFactors)||h.completeFactors<0||
      h.completeFactors>2||
      h.completeFactors!==Number(h.training!=='未評価')+Number(h.recent!=='未評価')||
      (h.completeFactors<2&&h.researchOrder!==null)||
      (h.completeFactors===2&&(!Number.isInteger(h.researchOrder)||h.researchOrder<1)))
    throw Error('馬番別資料の照合に失敗しました');
  seen.add(h.number);if(h.completeFactors===2)both++;
 }
 if(both!==d.completeTwoFactorCount)throw Error('2項目の頭数が一致しません');
 return d;
}
function drawRunner(h){
 const row=dom('div',undefined,'runner-row');
 row.append(dom('span',h.number+'番','number'),
  dom('span',h.researchOrder===null?'資料不足':'仮'+h.researchOrder+'位','rank'));
 for(const [name,grade] of [['調教',h.training],['近走',h.recent]]){
  row.append(dom('span',name+' '+grade,'grade'+(grade==='未評価'?'':' grade-'+grade)));
 }
 row.append(dom('div',POS[h.pastFourthCorner]+'（脚質の断定ではありません）','observed'));
 return row;
}
function draw(data,requested){
 if(!data||data.version!=='jrdb-owner-day-research-1'||
    data.date!==requested||data.privateOwnerOnly!==true||
    data.researchOnly!==true||data.officialJraVerified!==false||
    data.overallRankReady!==false||data.predictionReady!==false||
    data.bettingReady!==false||data.sourceReadCount!==4||
    !Array.isArray(data.races)||data.races.length>120||
    data.raceCount!==data.races.length||
    data.researchAvailableCount+data.needsReviewCount!==data.raceCount)
  throw Error('開催日データの形式が違います');
 const keys=new Set(),nodes=[],byVenue=new Map();
 for(const race of data.races){
  if(!race||!Number.isInteger(race.race)||race.race<1||race.race>12||
      typeof race.track!=='string'||race.track.length>6||
      keys.has(race.track+'-'+race.race))
   throw Error('レース番号が重複・不正です');
  keys.add(race.track+'-'+race.race);
  if(!['needs_review','research_only'].includes(race.status))
   throw Error('レースの資料状態が不正です');
  const group=dom('details');
  const title=dom('summary',race.track+' '+race.race+'R');
  if(race.status==='needs_review'){
   if(race.research!==null)throw Error('照合前の資料を表示できません');
   title.append(dom('span','要確認','race-badge'));
   group.append(title,dom('p','資料に不整合があるため、このレースの暫定ランクは出しません。','error'));
  }else{
   const d=checkDetails(race);
   title.append(dom('span',d.runnerCount+'頭／2項目あり '+d.completeTwoFactorCount+'頭','race-badge'));
   group.append(title);
   for(const horse of d.runners)group.append(drawRunner(horse));
  }
  const count=byVenue.get(race.track)||{total:0,ready:0};
  count.total++;
  if(race.status==='research_only')count.ready++;
  byVenue.set(race.track,count);
  nodes.push({track:race.track,node:group});
 }
 const filters=$('venueFilters');
 filters.replaceChildren();
 function showVenue(track){
  const visible=document.createDocumentFragment();
  for(const entry of nodes)if(!track||entry.track===track)visible.append(entry.node);
  $('results').replaceChildren(visible);
  for(const button of filters.querySelectorAll('button'))
   button.setAttribute('aria-pressed',String(button.dataset.track===track));
  const summary=track?byVenue.get(track):null;
  $('venueStats').textContent=summary?
   track+' '+summary.total+'R／暫定評価あり '+summary.ready+'R／要確認 '+(summary.total-summary.ready)+'R。':
   '全場 '+data.raceCount+'Rを表示中。競馬場を押すと、その競馬場のレースだけを確認できます。';
 }
 for(const track of ['',...byVenue.keys()]){
  const count=byVenue.get(track);
  const button=dom('button',track?track+' '+count.total+'R':'すべて '+data.raceCount+'R','venue-filter');
  button.type='button';
  button.dataset.track=track;
  button.setAttribute('aria-pressed','false');
  button.onclick=()=>showVenue(track);
  filters.append(button);
 }
 showVenue('');
 $('stats').textContent=data.raceCount+'R中、研究資料あり '+data.researchAvailableCount+
 'R／要確認 '+data.needsReviewCount+'R。JRA公式照合・総合予想・馬券生成は未実施。';
}
let latest=0;
$('day').value=new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
$('day').onchange=()=>{
 latest++;
 $('results').replaceChildren();
 $('venueFilters').replaceChildren();
 $('venueStats').textContent='';
 $('stats').textContent='未取得';
};
$('dayLoad').onclick=async()=>{
 const requestId=++latest,button=$('dayLoad'),day=$('day').value.replaceAll('-','');
 if(!/^20[0-9]{6}$/.test(day)){ $('status').textContent='開催日を選んでな。';return; }
 button.disabled=true;
 $('status').textContent='開催日分のJRDB研究資料を照合中…';
 $('stats').textContent='取得中';$('results').replaceChildren();
 try{
  const res=await fetch('/api/jrdb/day-runner-research?date='+encodeURIComponent(day),{
   cache:'no-store',credentials:'same-origin',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const data=await res.json();
  if(!res.ok)throw Error(data.error||'取得できませんでした');
  if(requestId!==latest||$('day').value.replaceAll('-','')!==day)return;
  draw(data,day);
  $('status').textContent='研究資料を更新。保存・公開・馬券購入は行っていません。';
 }catch(e){
  if(requestId===latest){
   $('status').textContent='取得できません：'+e.message;
   $('stats').textContent='取得失敗／予想未作成';
  }
 }finally{if(requestId===latest)button.disabled=false;}
};
})();"""
