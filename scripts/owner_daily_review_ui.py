"""Authenticated read-only daily retrospective interface.

Only the generic UI and validation code live in GitHub.
Owner retrospective facts are loaded via the private Render environment.
"""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b"><title>KEIBA NINE｜振り返り</title>
<link rel="stylesheet" href="/owner-daily-review.css"></head><body><main>
<nav><a href="/">← 本人用ホーム</a><a href="/owner-review">端末記録の分析へ</a></nav>
<h1>🏇 競馬ナイン｜今日の反省会</h1>
<p class="caution">これは<strong>前日暫定予想をすべて購入したと仮定した検証</strong>です。
実際の購入履歴・払戻ではありません。JRA公式の全レース照合も未完了。
予想、保存済みの実購入記録、回収率データは変更しません。</p>
<p id="dailyStatus" class="muted" role="status">本人用の検証レポートを読み込み中…</p>
<section><h2 id="reviewTitle">集計結果</h2><div id="summaryStats" class="stats"></div><p id="coverage" class="muted"></p></section>
<section><h2>競馬場別の内訳</h2><div id="venueSummary"></div></section>
<section><h2>的中した組み合わせ</h2><p class="muted">払戻は3連単1点100円あたり。結果は再検証対象で、購入を証明するものではありません。</p><div id="hits"></div></section>
<section><h2>勝負度で絞った場合</h2><div id="strongStats"></div></section>
<section><h2>次回の予想で改善する点</h2><ol id="lessons"></ol>
<p class="muted">1日分の傾向なので、次回の的中率・回収率を保証するものではありません。</p></section>
<p class="bottom"><a href="/owner-preday-forecast">予想ページへ</a>　<a href="/my-tickets">馬券記録へ</a></p>
</main><script src="/owner-daily-review.js" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#edf4ff;font:15px/1.65 system-ui,sans-serif}main{max-width:760px;margin:auto;padding:18px 14px 48px}nav{display:flex;justify-content:space-between;gap:12px}a{color:#f1d18a}h1{font-size:26px;color:#f2d080;margin:20px 0 12px}h2{font-size:19px;margin:0 0 10px}section{background:#142b43;border:1px solid #496985;border-radius:14px;padding:15px;margin:14px 0}.caution{background:#322b25;color:#ffe7b8;padding:13px;border:1px solid #9c7d4e;border-radius:12px;font-size:13px}.muted{font-size:13px;color:#c6d5e5}.stats{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.stat{background:#0f2238;border:1px solid #425e77;border-radius:10px;padding:11px}.stat label{display:block;color:#bcd2e9;font-size:12px}.stat strong{display:block;font-size:23px;color:#f4d487;font-variant-numeric:tabular-nums}.stat strong.negative{color:#f4abab}.stat strong.positive{color:#b2e6c8}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:14px}th,td{padding:10px 4px;border-bottom:1px solid #46607a;text-align:right}th:first-child,td:first-child{text-align:left}th{color:#f1d18a}td small{font-size:11px;color:#d2dfef}.scroll{overflow-x:auto}.hit{border-bottom:1px solid #405d74;padding:9px 0;display:flex;gap:10px;align-items:baseline;justify-content:space-between}.hit strong{font-size:14px}.hit span{font-variant-numeric:tabular-nums;white-space:nowrap}.win{color:#b8efce}.bottom{padding:8px 0}ol{padding-left:23px}li{margin:10px 0} @media(max-width:370px){.stats{grid-template-columns:1fr}table{font-size:12px}}"""

JS = r"""(()=>{'use strict';
const $=id=>document.getElementById(id);
const yen=n=>n.toLocaleString('ja-JP')+'円';
const pct=(n,d)=>d?(n/d*100).toFixed(1)+'%':'—';
const ORDER=['東京','京都','福島'];
function node(tag,txt,cls){
 const el=document.createElement(tag);
 if(txt!==undefined)el.textContent=String(txt);
 if(cls)el.className=cls;
 return el;
}
function stat(label,value,kind){
 const item=node('div',undefined,'stat'),tag=node('label',label);
 const v=node('strong',value,kind||'');
 item.append(tag,v);return item;
}
function validate(data){
 if(!data||data.sourceKind!=='owner-retrospective-provisional'||
   data.actualPurchase!==false||data.jraAllVerified!==false||
   data.complete!==false||typeof data.date!=='string'||!/^20\d{2}-\d\d-\d\d$/.test(data.date)||
   !Number.isInteger(data.racesReviewed)||data.racesReviewed>35||
   data.unit!==100||data.pointsPerRace!==30||
   !Array.isArray(data.venues)||data.venues.length!==3||
   !Array.isArray(data.hits)||!Array.isArray(data.findings)||!data.strong)
  throw Error('形式が一致しません。');
 const n=data.venues.reduce((sum,v)=>sum+v.racesReviewed,0);
 const h=data.venues.reduce((sum,v)=>sum+v.trifectaHits,0);
 const payout=data.venues.reduce((sum,v)=>sum+v.payout,0);
 if(n!==data.racesReviewed||h!==data.hits.length||
   data.strong.races>n||data.strong.payout>payout)
  throw Error('集計が一致しません。');
 return data;
}
function render(data){
 const v=validate(data);
 const invest=v.racesReviewed*v.unit*v.pointsPerRace;
 const paid=v.venues.reduce((x,r)=>x+r.payout,0);
 const hits=v.hits.length;
 $('reviewTitle').textContent=v.date+'（暫定・'+v.racesReviewed+'R）';
 const box=$('summaryStats');box.replaceChildren();
 box.append(stat('3連単的中',hits+'/'+v.racesReviewed+'R'),
   stat('回収率（全R仮購入）',pct(paid,invest)),
   stat('仮想投資',yen(invest)),
   stat('仮想払戻',yen(paid)),
   stat('仮想収支',yen(paid-invest),paid-invest<0?'negative':'positive'));
 $('coverage').textContent=v.scopeNote;
 const table=node('table'),head=node('thead'),tr=node('tr');
 for(const title of ['会場','対象','3連単','1着候補内','仮想回収率']){
  tr.append(node('th',title));
 }
 head.append(tr);table.append(head);
 const tbody=node('tbody');
 for(const venue of ORDER){
  const record=v.venues.find(x=>x.name===venue);
  if(!record)continue;
  const row=node('tr');
  for(const value of [venue,record.racesReviewed+'R',
    record.trifectaHits+'/'+record.racesReviewed,
    record.firstCandidateHits+'/'+record.racesReviewed,
    pct(record.payout,record.racesReviewed*v.unit*v.pointsPerRace)]){
   row.append(node('td',value));
  }
  tbody.append(row);
 }
 table.append(tbody);
 const holder=node('div',undefined,'scroll');holder.append(table);
 $('venueSummary').replaceChildren(holder);
 const hitHolder=$('hits');hitHolder.replaceChildren();
 for(const venue of ORDER){
  const venueHits=v.hits.filter(h=>h.track===venue).sort((a,b)=>a.race-b.race);
  if(!venueHits.length)continue;
  hitHolder.append(node('h3',venue+'（'+venueHits.length+'R）'));
  for(const h of venueHits){
   const row=node('div',undefined,'hit');
   row.append(node('strong',venue+h.race+'R  '+h.combination.join('→')),
     node('span',yen(h.payout),'win'));hitHolder.append(row);
  }
 }
 const strong=v.strong,spent=strong.races*v.unit*v.pointsPerRace;
 $('strongStats').replaceChildren(
  stat('対象',strong.races+'R'),
  stat('的中',strong.hits+'R'),
  stat('仮想回収率',pct(strong.payout,spent)),
  stat('仮想収支',yen(strong.payout-spent),strong.payout-spent<0?'negative':'positive')
 );
 $('strongStats').className='stats';
 const lesson=$('lessons');lesson.replaceChildren();
 for(const text of v.findings)lesson.append(node('li',text));
 $('dailyStatus').textContent='本人用の非公開レポートを読み込みました。実購入記録は変更していません。';
}
async function load(){
 try{
  const r=await fetch('/api/owner-daily-review',{
   cache:'no-store',credentials:'same-origin',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(!r.ok)throw Error('取得できません。');
  const body=await r.json();
  if(!body||body.available!==true){
   $('dailyStatus').textContent='振り返りレポートはまだ登録されていません。';
   return;
  }
  render(body.review);
 }catch(_){
  $('dailyStatus').textContent='レポートを表示できません。既存の予想と実購入記録は安全です。';
 }
}
load();
})();"""
