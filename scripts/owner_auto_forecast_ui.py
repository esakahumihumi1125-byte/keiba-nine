"""Owner private iPhone view for automatic JRDB two-factor provisional draft."""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>KEIBA NINE｜本人用・自動暫定予想</title>
<link rel="stylesheet" href="/owner-auto-forecast.css"></head><body><main>
<nav><a href="/">← 本人用ホーム</a><a href="/owner-jrdb-day-research">2項目の根拠</a></nav>
<h1>KEIBA NINE <small>本人用・自動暫定予想</small></h1>
<p class="warning"><strong>実戦用の確定予想ではありません。</strong>
JRDBの調教・近走2項目だけで参考評価と3連単の下書きを自動計算します。
血統・適性・枠・展開・馬場など残り8項目、JRA公式出走取消・発走時刻の照合はまだ未完成。
資料が不足したレースは見送り。実際の投票・購入・記録への保存は一切行いません。</p>
<section>
<label for="autoDay">開催日</label><input id="autoDay" type="date">
<button id="autoRun" type="button">全場・全Rを再分析する</button>
<details><summary>JRDB実接続の確認（任意）</summary>
<p class="muted">本人が押した時だけ設定を確認し、設定済みなら番組APIへ1回接続。未設定ならJRDBへの追加通信なし。買い目・収支・購入記録は変更しません。</p>
<button id="autoConnectionCheck" type="button">選択日のJRDB接続を確認</button>
<p id="autoConnectionStatus" class="muted" role="status">診断は未実行。</p>
</details>
<p class="muted">画面を開いたら本人用の当日分を一度だけ自動取得。
再分析ボタンを押した場合は番組・出走馬・調教・近走を各1回取得し、
馬場情報の追加取得も最大1回だけ試みます。取得できなくても既存の発走前記録は維持します。
バックグラウンド定期取得は未接続。発走済みレースの3連単は後付けで作成しません。</p>
<p id="autoStatus" class="muted" role="status">開催日を選んで自動作成を押してな。</p>
<p id="autoSavedStatus" class="muted" role="status">発走前の買い目は端末内の研究記録として保存できます。実購入の記録とは別です。</p>
<p class="muted">サーバー保存が未設定の間は、iPhoneの保存領域が消えると研究記録も失われる可能性があります。
<a href="/owner-backup">固定済み買い目など8種類の端末記録をバックアップする</a>。
既存の端末記録を消したり、別の版の保存内容を上書きしたりしません。</p>
<a id="autoReviewLink" href="/owner-100yen-review">固定した研究用買い目を100円仮想収支で確認</a>
</section>
<section>
<h2>過去の同条件実績を照合</h2>
<p class="muted">必要なときだけ過去番組・馬場を最大8件照合（追加APIアクセスは最大16回）。
資料の数は適性点数や勝率ではありません。未取得や新馬を能力不足とは判断しません。
同条件の過去3〜5走が十分に確認できた場合だけ「好走実績の研究目安 S〜C」を表示します。
さらに過去4角の位置取りから、先行候補の競合状況と研究用の展開仮説を表示します。
これは10項目の正式なS〜C、勝率、1着候補の決定ではありません。</p>
<button id="autoHistoryAudit" type="button" disabled>過去の同条件を最大8件照合する</button>
<p class="muted">発走前に照合した巻き返し候補は署名を検証し、iPhone内に最初の候補を固定します。事後の再分析で候補を上書きしません。これは公式結果や馬券購入の証明ではありません。</p>
<p id="autoHistoryWatchSave" class="muted" role="status">発走前の候補記録は未確認。</p>
<button id="autoWatchResultCheck" type="button" disabled>固定した巻き返し候補とJRDB成績を参考照合</button>
<p class="muted">署名済み候補がこのiPhoneにある開催日だけ利用できます。押した時のみJRDBの成績を1回取得。
JRDBはJRA公式から独立した結果確認ではないので、表示は暫定値です。公式的中・回収率に加算しません。</p>
<p id="autoWatchResultStatus" class="muted" role="status">発走前の固定候補がありません。</p>
<div id="autoWatchResultRaces"></div>
<p id="autoHistoryAuditStatus" class="muted" role="status">暫定予想の取得後に利用できます。</p>
<div id="autoHistoryAuditRaces"></div>
</section>
<section>
<h2>当日の馬体重資料（任意）</h2>
<p class="muted">押したときだけJRDB直前情報から馬体重・前走比の記録件数を照合。原数値・オッズ・パドック指数は画面に出しません。JRA公式の確定値や馬体評価ではありません。</p>
<button id="autoPrestartBody" type="button">今日の馬体重資料を確認</button>
<p id="autoPrestartStatus" class="muted" role="status">本人操作時だけ追加API照合。予想・買い目・回収率は変更しません。</p>
<div id="autoPrestartRaces"></div>
</section>
<section>
<h2>発走前に固定した買い目の履歴</h2>
<button id="autoReceiptVerify" type="button">この日の固定買い目をサーバーで署名確認</button>
<p id="autoReceiptVerifyStatus" class="muted" role="status">未確認。端末内の署名付き研究記録だけを本人用サーバーで検証します。原データの追加取得や買い目の変更はありません。</p>
<p class="muted">署名が正しくてもJRA公式の発走時刻・結果・実購入・サーバー保存を証明するものではありません。サーバー保存が未設定なら、別途バックアップが必要です。</p>
<p id="autoHistoryStatus" class="muted" role="status">この端末の固定記録を読み込み中です。</p>
<div id="autoHistory"></div>
<p class="muted">端末内の固定済み買い目を読み取り専用で表示します。
署名はこの画面では検証していません。後付け予想ではありません。</p>
<a href="/owner-backup">8種類の記録をバックアップ・復元する</a>
</section>
<section><h2>10項目の配点と評価状況</h2>
<p id="autoTenStatus" class="muted" role="status">予想資料の取得後に表示します。</p>
<div id="autoTenWeights" class="ten-weights"></div>
<p class="muted">総合S：85点以上／A：70点以上／B：55点以上／C：55点未満。
10項目の根拠がそろうまでは総合点・総合順位は「未評価」です。</p>
</section>
<section>
<h2>全Rの結果</h2><p id="autoSummary" class="muted">未取得</p>
<p id="autoSourceSummary" class="muted" role="status">全Rの資料進捗は未取得です。</p>
<div id="autoVenues" class="venue-tabs" role="group" aria-label="競馬場を絞り込む"></div>
<label for="autoRacePick">見たいレースを選ぶ（全場・全Rから選択）</label>
<select id="autoRacePick" disabled><option value="">全Rを一覧表示</option></select>
<p id="autoViewingStatus" class="muted" role="status">レースを取得すると選択できます。</p>
<div id="autoRaces"></div>
</section>
<p class="muted">Sは金色、Aは赤色。調教・近走のS/A/B/Cはそれぞれの仮評価。仮順位は調教30：近走3の配点で算出し、
総合10項目ランクや勝率とは区別しています。
買い目は重複除外・最大40点・1点100円換算。結果を見てから買い目を作ることはできません。</p>
</main><script src="/owner-auto-forecast.js" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}
body{margin:0;background:#09172b;color:#eff5ff;font:15px/1.55 system-ui,sans-serif}
main{max-width:780px;margin:auto;padding:16px 13px 46px}
h1{font-size:24px;color:#f0d07e;margin:17px 0}
h1 small{display:block;color:#c7d7e7;font-size:13px}
h2{font-size:19px;margin:0 0 10px}
nav{display:flex;justify-content:space-between;gap:12px}a{color:#f0d185}
section{background:#142b43;border:1px solid #4d6b85;border-radius:14px;padding:14px;margin:14px 0}
.warning{background:#342d25;color:#ffe6b5;border:1px solid #9b8052;border-radius:10px;padding:12px;font-size:13px}
.muted{font-size:13px;color:#c3d3e3}
label{display:block;font-weight:700}
input,button,select{font:inherit;min-height:45px;padding:11px;border-radius:10px;margin:7px 0;width:100%}
input,select{background:#0c2135;color:white;border:1px solid #90a6b9}
button{background:#e8c774;color:#182b41;border:0;font-weight:800}
button:disabled,select:disabled{opacity:.55}
.venue-tabs{display:flex;flex-wrap:wrap;gap:7px}
.venue-tabs button{flex:1 1 100px;width:auto;background:#2b425b;color:#eaf3ff}
.venue-tabs button[aria-pressed=true]{background:#e8c774;color:#152a3d}
details{border:1px solid #45617e;background:#10263d;border-radius:11px;margin:8px 0;padding:10px}
summary{font-weight:800;color:#f2d596;cursor:pointer;min-height:35px}
.hold{color:#e9bfae;font-size:13px;margin:8px 0}
.runner{display:flex;align-items:center;flex-wrap:wrap;gap:7px;
 background:#213a54;border-radius:9px;padding:8px;margin:6px 0}
.number{font-size:19px;font-weight:850;min-width:44px}
.rank{font-size:12px;min-width:43px;color:#c6d5e7}
.grade{padding:3px 7px;border-radius:6px;background:#3b5065;font-weight:800;font-size:12px}
.S{color:#f3d475}.A{color:#ffa6b1}.B{color:#a4d8ff}.C{color:#dde2ed}
.notes{font-size:12px;color:#c1d3e7;flex-basis:100%}
.formation{background:#192f46;border:1px solid #456582;border-radius:10px;padding:12px;margin:10px 0}
.formation strong{color:#e8ca81}
.formation p{margin:6px 0}
.picks{font-weight:800;color:#f0e4c9;letter-spacing:.02em;overflow-wrap:anywhere}
.ticket-list{font:12px/1.75 system-ui,sans-serif;color:#cbd8e6;overflow-wrap:anywhere}
.ten-weights,.ten-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}
.ten-weight,.ten-slot{background:#253e58;border-radius:7px;padding:7px;font-size:12px}
.ten-weight{display:flex;justify-content:space-between;gap:4px}
.ten-weight b{color:#f5d284}
.ten-horse{margin:6px 0 9px 13px}
.ten-horse summary{font-size:13px;min-height:27px;color:#cdddff}
.ten-slot span{display:block;color:#b9cadc}
.ten-slot b{display:inline-block;color:#e9efff;margin-top:4px}
.ten-slot b.S{color:#f3d475}.ten-slot b.A{color:#ffa6b1}.ten-slot b.B{color:#a4d8ff}
.history-coverage{border:1px solid #45617e;background:#182f48;border-radius:10px;margin:7px 0;padding:10px}
.history-coverage strong{color:#f3d475}.history-coverage p{font-size:12px;margin:4px 0}
@media(max-width:380px){.number{min-width:34px}.rank{min-width:35px}}
"""

JS = r"""(()=>{'use strict';
const $=id=>document.getElementById(id);
const GRADES=new Set(['S','A','B','C','未評価']);
const TEN=[
 ['training','調教',30],['recent','近走',3],
 ['course_distance','コース・距離',20],['pace','展開・脚質',20],
 ['ground','馬場',12],['pedigree','血統',8],
 ['draw_weight','枠・斤量',3],['jockey_stable','騎手・厩舎',2],
 ['rotation','ローテ',1],['body_condition','馬体重',1]
];
const MISSING={
 missing_training_indices:'調教：追切・仕上指数の片方または両方が不足',
 no_linked_training_record:'調教：この馬に照合できる資料なし',
 no_usable_history:'近走：評価に使える過去走なし',
 only_one_usable_run:'近走：使える資料が1走のみ（現基準は2走必要）',
 insufficient_scored_runs:'近走：着順と指数がそろう資料が2走未満',
 no_linked_recent_record:'近走：この馬に照合できる資料なし',
 training_unassessed:'調教：資料不足・理由の再確認が必要',
 recent_unassessed:'近走：資料不足・理由の再確認が必要'
};
function missingText(h){return (Array.isArray(h.missingReasons)?h.missingReasons:[])
 .filter(k=>Object.hasOwn(MISSING,k)).map(k=>MISSING[k]).join('／');}
const RECEIPTS_KEY='keiba-nine-owner-server-receipts-v1';
// Safe, fixed server diagnostics. Do not display raw provider error text.
const FAILURE_STAGE={
 programme:'番組取得・形式確認',entries:'出走馬取得',training:'調教取得',
 recent:'近走取得',day_research:'全レース資料照合',
 draft_generation:'研究用買い目生成',receipt_signing:'発走前記録の署名',
 receipt_archiving:'サーバー記録の固定保存'
};
const FAILURE_KIND={
 provider:'API通信・権限',programme_format:'番組形式',
 source_validation:'資料間の整合性',receipt_guard:'記録の署名検証',
 invalid_data:'資料形式'
};
// Stable server-authored categories only. Never print raw API errors.
const FAILURE_DETAIL={
 bad_request_contract:'日付と番組の契約',server_clock:'サーバー時刻',
 research_header:'全日資料の形式',research_slot:'レース資料形式',
 research_slot_duplicate:'重複・不正なレース資料',
 programme_slot:'番組内のレース形式',
 race_set_mismatch:'番組と分析対象の一致',
 unverified_research:'未確認資料の扱い',
 race_programme_identity:'レース番組の識別',
 race_research_identity:'番組と仮評価の識別',
 formation_size:'買い目点数の検算',other:'未分類の照合条件'
};
const REASONS={
 missing_research:'このレースの資料に不整合あり・自動判定を見送り',
 runner_count_mismatch:'出走頭数が資料と不一致',
 too_few_runners:'4頭未満で候補を作成できない',
 missing_factors:'一部の馬の調教または近走が未評価',
 missing_post_time:'暫定発走時刻を安全に確認できない',
 after_provisional_off:'暫定発走時刻を過ぎたため後付け買い目なし',
 ambiguous_equal_grade_boundary:'同評価の馬が候補の境界にいるため選定保留',
 invalid_two_factor:'このレースの調教・近走の資料検証に不一致があり、安全のため見送り',
 archived_earlier_draft:'このRの別の買い目が先にサーバーへ固定済み。再分析の買い目は表示しません。固定済み記録は100円仮想収支で確認'
};
const SHORT_HOLDS={
 after_provisional_off:'発走済み',missing_factors:'調教・近走不足',
 ambiguous_equal_grade_boundary:'候補同点',missing_research:'資料確認',
 invalid_two_factor:'2項目不整合',runner_count_mismatch:'頭数不一致',
 too_few_runners:'少頭数',missing_post_time:'発走時刻未確認',
 archived_earlier_draft:'既存の固定買い目を優先'
};
const RUNNER_ISSUES={
 contract:'2項目評価の形式',runner_shape:'馬番別資料の形式',
 completeness:'評価済み項目数',rank_order:'評価順位',
 incomplete_rank:'未評価馬の順位',missing_reasons:'未評価の理由',
 summary_count:'評価済み頭数'
};
const MATERIAL_LABELS={
 pedigree:'父・母父',drawWeight:'枠・斤量',rotation:'前走日付',
 personnel:'騎手・厩舎',body:'馬体形状',pastCorner:'過去4角'
};
const POS={
 frontObserved:'過去4角：前方観測',
 backObserved:'過去4角：後方観測',
 mixedObserved:'過去4角：混在',
 insufficient:'過去4角：資料不足'
};
const dom=(tag,value,cls)=>{const d=document.createElement(tag);
 if(value!==undefined)d.textContent=String(value);if(cls)d.className=cls;return d;};
function validateTen(data){
 const p=data.tenFactorPreview;
 if(!p||p.version!=='owner-ten-factor-contract-1'||p.policyVersion!=='research-5'||
    p.factorCount!==10||p.totalWeight!==100||
    p.gradeThresholds?.S!==85||p.gradeThresholds?.A!==70||
    p.gradeThresholds?.B!==55||p.researchOnly!==true||
    p.overallPredictionReady!==false||p.officialJraVerified!==false||
    p.fullPredictionRaceCount!==0||p.raceCount!==data.raceCount||
    p.requiredForOverall!=='all_ten_verified_before_start'||
    !Array.isArray(p.factors)||p.factors.length!==10||
    !Array.isArray(p.races)||p.races.length!==data.raceCount)
  throw Error('10項目データの形式不正');
 for(let i=0;i<10;i++){
  const f=p.factors[i],expected=TEN[i];
  if(!f||f.key!==expected[0]||f.label!==expected[1]||
     f.weight!==expected[2])throw Error('10項目配点の不一致');
 }
 const source=new Map(data.races.map(r=>[r.track+'|'+r.race,r])),seen=new Set();
 for(const r of p.races){
  const id=r.track+'|'+r.race,actual=source.get(id);
  if(!actual||seen.has(id)||r.overallReady!==false||
     r.fullTenFactorCount!==0||!Array.isArray(r.horses)||
     r.runnerCount!==actual.runners.length||r.horses.length!==actual.runners.length||
     r.trainingLedRecheckIsWinPick!==false||
     !Array.isArray(r.trainingLedRecheckNumbers)||
     !Array.isArray(r.trainingLedRecheckNeeds)||
     r.trainingLedRecheckNeeds.join('|')!=='course_distance|pace|ground')
   throw Error('10項目レースの不一致');
  seen.add(id);
  const horses=new Map(actual.runners.map(h=>[h.number,h]));
  const duplicates=new Set();
  for(const h of r.horses){
   if(!h||duplicates.has(h.number)||!horses.has(h.number)||
      h.overallGrade!=='未評価'||h.overallRank!==null||h.score!==null||
      h.verifiedFactorCount!==0||!h.grades||Object.keys(h.grades).length!==10||
      !Array.isArray(h.missing))throw Error('10項目馬番の形式不正');
   duplicates.add(h.number);
   let count=0;
   for(const [key] of TEN){
    const grade=h.grades[key],original=horses.get(h.number);
    if(!GRADES.has(grade)||
       (key==='training'&&grade!==original.training)||
       (key==='recent'&&grade!==original.recent)||
       (key!=='training'&&key!=='recent'&&grade!=='未評価'))
     throw Error('未検証の10項目評価を拒否');
    if((key==='training'||key==='recent')&&grade!=='未評価')count++;
   }
   if(h.provisionalFactorCount!==count||h.missing.length!==10-count)
     throw Error('10項目の採点数が不一致');
  }
  const watch=r.horses.filter(h=>
   actual.status==='provisional_draft'&&
   ['S','A'].includes(h.grades.training)&&
   ['B','C'].includes(h.grades.recent))
   .map(h=>h.number).sort((a,b)=>a-b);
  const declared=r.trainingLedRecheckNumbers;
  if(declared.length!==watch.length||
     declared.some((n,i)=>n!==watch[i]))
   throw Error('巻き返し資料の照合が不一致');
 }
 return p;
}
function validateContext(data){
 const ctx=data.raceContext;
 if(!ctx||ctx.version!=='race-context-1'||
    ctx.raceCount!==data.raceCount||!Array.isArray(ctx.races)||
    ctx.races.length!==data.raceCount||
    ctx.raceConditionsVerified!==false||ctx.predictionReady!==false||
    !Number.isInteger(ctx.courseInfoPresentCount)||
    !Number.isInteger(ctx.goingAvailableCount)||
    ctx.conditionProviderReadCount!==(data.raceCount?1:0)||
    !['received','unavailable'].includes(ctx.conditionProviderFetchStatus))
  throw Error('レース条件の形式が不正です');
 const existing=new Map(data.races.map(r=>[r.track+'|'+r.race,r])),seen=new Set();
 let present=0,known=0;
 for(const r of ctx.races){
  if(!r||typeof r.track!=='string'||!Number.isInteger(r.race)||
     !existing.has(r.track+'|'+r.race)||seen.has(r.track+'|'+r.race)||
     ![null,'芝','ダート','障害'].includes(r.surface)||
     !(r.distance_m===null||
       (Number.isInteger(r.distance_m)&&r.distance_m>=100&&r.distance_m<=10000))||
     ![null,'右','左','直線'].includes(r.turn)||
     !['良','稍重','重','不良','未確認'].includes(r.going)||
     typeof r.goingAvailable!=='boolean'||
     typeof r.courseInfoPresent!=='boolean'||
     typeof r.conditionSnapshotPresent!=='boolean'||
     typeof r.conditionUpdateRecorded!=='boolean'||
     r.horseCourseSuitabilityAssessed!==false||
     r.horseGoingSuitabilityAssessed!==false||r.predictionReady!==false)
   throw Error('レース条件に未検証値があります');
  const key=r.track+'|'+r.race;seen.add(key);
  const info=r.surface!==null&&r.distance_m!==null&&r.turn!==null;
  if(info!==r.courseInfoPresent||
     (r.going!=='未確認')!==r.goingAvailable||
     (r.goingAvailable&&!r.conditionSnapshotPresent)||
     (r.conditionUpdateRecorded&&!r.conditionSnapshotPresent)||
     (r.surface==='障害'&&r.goingAvailable))
   throw Error('レース条件と資料の状態が不一致');
  present+=Number(r.courseInfoPresent);
  known+=Number(r.goingAvailable);
 }
 if(present!==ctx.courseInfoPresentCount||known!==ctx.goingAvailableCount)
  throw Error('レース条件の集計が不一致');
 return ctx;
}
function validateSourcePassport(data){
 const a=data.sourcePassport;
 if(a===undefined)return null; // older private snapshots stay readable
 if(!a||a.version!=='owner-day-source-passport-1'||
    a.policyVersion!=='research-5'||
    a.newProviderRequests!==0||a.gradedFactors!==0||
    a.verifiedPredictions!==0||a.independentJraVerified!==false||
    a.purchaseReady!==false||typeof a.sourceAuditAvailable!=='boolean'||
    !Array.isArray(a.races))
  throw Error('10項目資料進捗の形式不正');
 if(!a.sourceAuditAvailable){
  if(a.raceCount!==0||a.races.length!==0||
     a.reason!=='source_audit_unavailable')
   throw Error('資料進捗の照合保留形式不正');
  return a;
 }
 if(a.reason!=='unvalidated_source_observations_only'||
    a.raceCount!==data.raceCount||a.races.length!==data.raceCount||
    a.observedMaterialRaces!==
     (data.sourceMaterials.status==='observed'?data.raceCount:0))
  throw Error('資料進捗のレース数不一致');
 const draft=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 const provisional=new Map(data.tenFactorPreview.races.map(r=>[r.track+'|'+r.race,r]));
 const course=new Map(data.raceContext.races.map(r=>[r.track+'|'+r.race,r]));
 const material=new Map(data.sourceMaterials.races.map(r=>[r.track+'|'+r.race,r]));
 const eight=TEN.map(([key])=>key).filter(k=>!['training','recent'].includes(k));
 const observed=['pedigree','drawWeight','rotation','personnel','body','pastCorner'];
 const seen=new Set();
 for(const row of a.races){
  const id=row?.track+'|'+row?.race,original=draft.get(id);
  const ten=provisional.get(id),ctx=course.get(id),src=material.get(id);
  if(!original||!ten||!ctx||seen.has(id)||
     row.draftStatus!==original.status||
     !Number.isInteger(row.programmeRunnerCount)||
     row.programmeRunnerCount<0||row.programmeRunnerCount>18||
     !Number.isInteger(row.provisionalTrainingCount)||
     !Number.isInteger(row.provisionalRecentCount)||
     row.officialJraVerified!==false||
     row.verifiedFactorCount!==0||
     row.completeTenFactorReady!==false||
     row.independentResultsConnected!==false||
     row.purchaseReady!==false||
     row.raceDayBodyweightVerifiedCount!==0||
     row.courseContextPresent!==ctx.courseInfoPresent||
     row.goingContextPresent!==ctx.goingAvailable||
     !Array.isArray(row.unassessedFactorKeys)||
     row.unassessedFactorKeys.join('|')!==eight.join('|'))
   throw Error('レース別資料進捗に不整合');
  seen.add(id);
  const count=key=>ten.horses.filter(h=>GRADES.has(h.grades[key])&&
   h.grades[key]!=='未評価').length;
  if(row.provisionalTrainingCount!==count('training')||
     row.provisionalRecentCount!==count('recent'))
   throw Error('仮評価頭数の不整合');
  if(data.sourceMaterials.status==='observed'){
   if(!src||row.sourceMaterialsObserved!==true||
      row.programmeRunnerCount!==src.runnerCount||
      !row.additionalFieldCounts||
      Object.keys(row.additionalFieldCounts).length!==observed.length||
      observed.some(k=>row.additionalFieldCounts[k]!==src.counts[k])||
      (original.status==='provisional_draft'&&
       row.programmeRunnerCount!==ten.runnerCount))
    throw Error('観測資料と頭数の不整合');
  }else if(row.sourceMaterialsObserved!==false||
           row.additionalFieldCounts!==null||
           row.programmeRunnerCount!==ten.runnerCount)
   throw Error('未取得資料の取り違え');
 }
 if(seen.size!==data.raceCount)throw Error('レース別資料進捗不足');
 return a;
}
function validate(data,day){
 if(!data||data.version!=='jrdb-owner-auto-draft-1'||data.date!==day||
  data.researchOnly!==true||data.privateOwnerOnly!==true||
  data.officialJraVerified!==false||data.overallPredictionReady!==false||
  data.bettingReady!==false||data.autoPurchase!==false||
  typeof data.archiveEnabled!=='boolean'||
  !Number.isInteger(data.archiveRecordCount)||data.archiveRecordCount<0||
  !Number.isInteger(data.archiveConflictCount)||data.archiveConflictCount<0||
  (data.archiveConflictCount>0&&!data.archiveEnabled)||
  !data.sourceMaterials||
  data.sourceMaterials.version!=='owner-draft-material-coverage-1'||
  !['observed','unavailable'].includes(data.sourceMaterials.status)||
  data.sourceMaterials.officialJraVerified!==false||
  data.sourceMaterials.gradedNewFactors!==0||
  !Array.isArray(data.sourceMaterials.races)||
  (data.sourceMaterials.status==='unavailable'&&
   (data.sourceMaterials.observedFactorSlots!==0||
    data.sourceMaterials.races.length!==0))||
  (data.sourceMaterials.status==='observed'&&
   (data.sourceMaterials.observedFactorSlots!==8||
    data.sourceMaterials.races.length!==data.raceCount))||
  data.sourceReadCount!==4||data.unitYen!==100||
  data.weightedResearchOrder!=='training30_recent3'||
  data.weightedResearchMax!==99||data.weightedResearchPolicy!=='research-5'||
  !Array.isArray(data.races)||data.races.length>120||
  data.raceCount!==data.races.length||
  data.draftCount+data.holdCount!==data.raceCount||
  !data.holdReasons||typeof data.holdReasons!=='object'||
  Array.isArray(data.holdReasons)||
  Object.entries(data.holdReasons).some(([key,n])=>
    !Object.hasOwn(SHORT_HOLDS,key)||!Number.isInteger(n)||
    n<=0||n>data.raceCount)||
  Object.values(data.holdReasons).reduce((total,n)=>total+n,0)!==data.holdCount)
  throw Error('自動暫定予想の形式が不正です');
 const materials=new Map();
 for(const row of data.sourceMaterials.races){
  if(!row||typeof row.track!=='string'||!Number.isInteger(row.race)||
   !Number.isInteger(row.runnerCount)||row.runnerCount<0||row.runnerCount>18||
   !row.counts||Object.keys(row.counts).length!==6||
   Object.keys(MATERIAL_LABELS).some(k=>
     !Number.isInteger(row.counts[k])||row.counts[k]<0||
     row.counts[k]>row.runnerCount)||materials.has(row.track+'|'+row.race))
    throw Error('観測資料の形式が不正です');
  materials.set(row.track+'|'+row.race,row);
 }
 const seen=new Set();
 for(const r of data.races){
  if(!r||!Number.isInteger(r.race)||r.race<1||r.race>12||
   typeof r.track!=='string'||!['hold','provisional_draft'].includes(r.status)||
   r.researchOnly!==true||r.officialJraVerified!==false||
   r.overallPredictionReady!==false||r.bettingReady!==false||
   r.autoPurchase!==false||seen.has(r.track+'|'+r.race)||
   !Array.isArray(r.runners)||r.runners.length>18||
   !Array.isArray(r.first)||!Array.isArray(r.second)||
   !Array.isArray(r.third)||!Array.isArray(r.tickets)||
   r.points!==r.tickets.length||r.points>40||r.amountYen!==r.points*100)
   throw Error('レース別データが不正です');
  seen.add(r.track+'|'+r.race);
  if(data.sourceMaterials.status==='observed'){
   const material=materials.get(r.track+'|'+r.race);
   if(!material||Number.isInteger(r.horseCount)&&
      material.runnerCount!==r.horseCount)
     throw Error('資料とレース頭数が一致しません');
  }
  const numbers=new Set();
  for(const h of r.runners){
   if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
    numbers.has(h.number)||!GRADES.has(h.training)||
    !GRADES.has(h.recent)||!GRADES.has(h.twoFactorGrade)||
    !(h.pastFourthCorner in POS)||
    !(h.twoFactorPoints===null||Number.isInteger(h.twoFactorPoints))||
    !(h.weightedResearchPoints===null||
      (Number.isInteger(h.weightedResearchPoints)&&
       h.weightedResearchPoints>=0&&h.weightedResearchPoints<=99))||
    !(h.comparisonRank===null||(Number.isInteger(h.comparisonRank)&&h.comparisonRank>=1))||
    (h.weightedResearchPoints===null)!==(h.comparisonRank===null))
     throw Error('馬番別データが不正です');
   numbers.add(h.number);
  }
  if(r.status==='hold'){
   if(!Object.hasOwn(REASONS,r.reason)||r.points!==0||
      r.first.length||r.second.length||r.third.length||
      (r.reason==='invalid_two_factor'&&
       (!Object.hasOwn(RUNNER_ISSUES,r.validationIssue)||r.runners.length!==0)))
    throw Error('見送り理由が不正です');
  }else{
   if(r.reason!=='two_factor_only'||r.first.length<2||r.first.length>3||
    r.second.length<=r.first.length||r.second.length>6||
    r.third.length<r.second.length||r.third.length>10||!r.points)
    throw Error('候補が不正です');
   const unique=new Set();
   for(const t of r.tickets){
    if(!Array.isArray(t)||t.length!==3||new Set(t).size!==3||
     !t.every(n=>numbers.has(n))||!r.first.includes(t[0])||
     !r.second.includes(t[1])||!r.third.includes(t[2])||
     unique.has(t.join('-')))throw Error('買い目が不正です');
    unique.add(t.join('-'));
   }
  }
 }
 validateTen(data);
 validateContext(data);
 validateSourcePassport(data);
 return data;
}
function runnerView(h,index){
 const p=dom('div',undefined,'runner');
 p.append(dom('span',h.number+'番','number'),
  dom('span',h.comparisonRank===null?'未評価':'仮'+h.comparisonRank+'位','rank'),
  dom('span','調教 '+h.training,'grade '+h.training),
  dom('span','近走 '+h.recent,'grade '+h.recent),
  dom('span',POS[h.pastFourthCorner]+' ※脚質確定ではない','notes'));
 if(missingText(h))p.append(dom('span',missingText(h),'notes'));
 return p;
}
function renderTenHorse(h){
 const details=dom('details',undefined,'ten-horse');
 details.append(dom('summary',h.number+'番：10項目／総合 未評価（'+
   h.provisionalFactorCount+'項目は仮評価）'));
 const grid=dom('div',undefined,'ten-grid');
 for(const [key,label,weight] of TEN){
  const slot=dom('div',undefined,'ten-slot'),grade=h.grades[key];
  slot.append(dom('span',label+' '+weight+'点'),
    dom('b',grade+(grade==='未評価'?'':'（仮）'),grade==='未評価'?'':grade));
  grid.append(slot);
 }
 details.append(grid);return details;
}
function renderTenHeader(p){
 const host=$('autoTenWeights');host.replaceChildren();
 for(const f of p.factors){
  const el=dom('div',undefined,'ten-weight');
  el.append(dom('span',f.label),dom('b',f.weight+'点'));host.append(el);
 }
 $('autoTenStatus').textContent='100点配分／10項目。調教・近走は仮評価で、残り8項目は未評価。総合点・総合順位は未作成。';
}
function formation(r){
 const block=dom('div',undefined,'formation');
 block.append(dom('strong','3連単・2項目だけの研究用自動下書き（1着'+r.first.length+'頭）'),
  dom('p','1着：'+r.first.join('・')+'番','picks'),
  dom('p','2着：'+r.second.join('・')+'番','picks'),
  dom('p','3着：'+r.third.join('・')+'番','picks'),
  dom('p',r.points+'点／1点100円なら'+r.amountYen.toLocaleString('ja-JP')+'円（仮計算・未購入）'),
  dom('p',r.tickets.map(t=>t.join('→')).join(' / '),'ticket-list'));
 return block;
}
function summarizeDaySourcePassport(a, expectedCount){
 // Read only the validated, same-request count passport. Never infer
 // verified grades or JRA matching from material presence.
 if(!a)return '資料進捗一覧は旧版のデータに含まれていません。正式10項目の評価は未完了。';
 if(!a.sourceAuditAvailable)
  return '資料の件数集計は照合保留。総合10項目の正式採点・JRA公式照合は未完了。';
 const rows=a.races,aggregate=(key)=>rows.reduce((total,r)=>total+r[key],0);
 const course=rows.filter(r=>r.courseContextPresent).length;
 const going=rows.filter(r=>r.goingContextPresent).length;
 const observed=rows.filter(r=>r.sourceMaterialsObserved).length;
 if(rows.length!==expectedCount)throw Error('集計レース数の不一致');
 return '資料進捗：'+rows.length+'R中、調教の仮評価がある馬 '+
  aggregate('provisionalTrainingCount')+'頭／近走 '+aggregate('provisionalRecentCount')+
  '頭。コース条件 '+course+'R／当日馬場資料 '+going+
  'R／追加資料の件数照合 '+observed+
  'R。正式採点0/10・JRA公式独立照合なし。買い目は変更しません。';
}
function sourceNextChecks(row){
 // Data-presence triage, not a factor score, medical-style "risk" score,
 // win probability, prediction ranking or purchase recommendation.
 const items=[],total=row.programmeRunnerCount;
 const lacks=(have,label)=>{
  if(Number.isInteger(total)&&total>0&&have<total)
   items.push(label+' '+(total-have)+'頭を確認');
 };
 // Zero in a held post-off race may be a deliberately hidden roster.
 if(row.draftStatus==='provisional_draft'){
  lacks(row.provisionalTrainingCount,'調教の仮評価不足');
  lacks(row.provisionalRecentCount,'近走の仮評価不足');
 }
 if(!row.courseContextPresent)items.push('コース・距離の番組情報を確認');
 if(!row.goingContextPresent)items.push('当日の馬場情報を確認');
 if(!row.sourceMaterialsObserved){
  items.push('血統・枠斤量・騎手厩舎・ローテの元資料を確認');
 }else if(row.draftStatus==='provisional_draft'){
  const fields=[['pedigree','父・母父'],['drawWeight','枠・負担重量'],
   ['rotation','前走間隔'],['personnel','騎手・厩舎'],['pastCorner','過去4角']];
  for(const [key,label] of fields)lacks(row.additionalFieldCounts[key],label+'の記録不足');
 }
 // Body "count" in /tky is conformation, never an actual weigh-in.
 items.push('当日馬体重の確認（形状コードは代用不可）');
 items.push('各項目の適性・展開・能力の根拠に基づく採点');
 items.push('JRA公式の出走馬・取消・馬場・発走時刻を独立照合');
 return items;
}
function render(input,day){
 const data=validate(input,day),p=data.tenFactorPreview,ctx=data.raceContext;
 const tenRows=new Map(p.races.map(r=>[r.track+'|'+r.race,r]));
 const courseRows=new Map(ctx.races.map(r=>[r.track+'|'+r.race,r]));
 const passport=data.sourcePassport?.sourceAuditAvailable?
  new Map(data.sourcePassport.races.map(r=>[r.track+'|'+r.race,r])):null;
 const host=$('autoRaces'),tabs=$('autoVenues'),
  select=$('autoRacePick'),nodes=[],groups=new Map();
 select.disabled=true;select.replaceChildren();
 const allOption=dom('option','全Rを一覧表示');allOption.value='';
 select.append(allOption);select.value='';
 host.replaceChildren();tabs.replaceChildren();renderTenHeader(p);
 $('autoSourceSummary').textContent=summarizeDaySourcePassport(
  data.sourcePassport,data.raceCount);
 for(const race of data.races){
  const detail=dom('details'),title=dom('summary',
   race.track+' '+race.race+'R '+
   (race.status==='provisional_draft'?'研究用自動案 '+race.points+'点':'見送り'));
  detail.append(title);
  const course=courseRows.get(race.track+'|'+race.race);
  const condition=course.goingAvailable?course.going+'（JRDB資料）':'馬場未確認';
  detail.append(dom('p','コース条件：'+(course.surface||'芝・ダート未確認')+
    '／'+(course.distance_m===null?'距離未確認':course.distance_m+'m')+
    '／'+(course.turn||'回り未確認')+'／'+condition,'muted'));
  if(race.runners.length){
   const front=race.runners.filter(h=>h.pastFourthCorner==='frontObserved').length;
   const back=race.runners.filter(h=>h.pastFourthCorner==='backObserved').length;
   const mixed=race.runners.filter(h=>h.pastFourthCorner==='mixedObserved').length;
   const unknown=race.runners.length-front-back-mixed;
   detail.append(dom('p','過去4角の位置取り観測：前方 '+front+
     '頭／後方 '+back+'頭／混在 '+mixed+'頭／資料不足 '+unknown+
     '頭（今回の展開予測・適性点数ではありません）','muted'));
  }
  if(race.status==='hold'){
   const extra=race.reason==='invalid_two_factor'&&
     Object.hasOwn(RUNNER_ISSUES,race.validationIssue)
     ?'（'+RUNNER_ISSUES[race.validationIssue]+'）':'';
   detail.append(dom('p',REASONS[race.reason]+extra,'hold'));
  }
  const tenRace=tenRows.get(race.track+'|'+race.race);
  if(tenRace.trainingLedRecheckNumbers.length){
   detail.append(dom('p','巻き返し条件の確認待ち：'+
     tenRace.trainingLedRecheckNumbers.map(n=>n+'番').join('・')+
     '。調教の仮評価が高く近走評価が低い馬。'+
     'コース距離・展開・馬場を確認してから1着候補を再審査（自動追加・購入なし）。',
     'hold'));
  }
  if(race.runners.length){
   detail.append(dom('p','調教30：近走3での仮順位（10項目総合評価ではない）','muted'));
   for(const [i,h] of race.runners.entries()){
    detail.append(runnerView(h,i));
    const ten=tenRows.get(race.track+'|'+race.race).horses.find(x=>x.number===h.number);
    detail.append(renderTenHorse(ten));
   }
  }
  if(data.sourceMaterials.status==='observed'){
   const item=data.sourceMaterials.races.find(x=>
     x.track===race.track&&x.race===race.race);
   const evidence=Object.entries(MATERIAL_LABELS)
    .map(([key,label])=>label+' '+item.counts[key]+'/'+item.runnerCount)
    .join('／');
   detail.append(dom('p','資料の有無（採点ではない）：'+evidence,'muted'),
    dom('p','コース距離・馬場適性は未接続。調教・近走以外の8項目は未採点。','muted'));
  }else{
   detail.append(dom('p','追加8項目の資料確認は未完了（予想・買い目とは別）。','muted'));
  }
  if(passport){
   const row=passport.get(race.track+'|'+race.race);
   const panel=dom('details',undefined,'source-passport');
   panel.append(dom('summary','10項目の資料進捗（正式採点0/10）'));
   panel.append(dom('p','調教の仮評価 '+row.provisionalTrainingCount+
    '頭／近走の仮評価 '+row.provisionalRecentCount+
    '頭。両方とも正式採点ではなく、残り8項目は未評価。','muted'));
   if(row.sourceMaterialsObserved){
    panel.append(dom('p','既存資料の記録数：'+
     Object.entries(MATERIAL_LABELS).map(([k,label])=>
      label+' '+row.additionalFieldCounts[k]+'/'+row.programmeRunnerCount+'頭').join('／')+
     '。記録の存在は能力や適性を示しません。','muted'));
   }else panel.append(dom('p','追加資料の件数は照合保留。0件扱いにしません。','muted'));
   panel.append(dom('p','コース情報 '+(row.courseContextPresent?'あり':'未確認')+
    '／当日馬場情報 '+(row.goingContextPresent?'あり':'未確認')+
    '。過去の位置取りや馬体形状コードは、展開予測・当日馬体重の採点ではありません。','muted'));
   panel.append(dom('p','未評価の8項目：'+
    TEN.filter(([key])=>row.unassessedFactorKeys.includes(key))
     .map(([,label,weight])=>label+weight+'点').join('／')+
    '。資料の記録数だけでS/A/B/Cの評価はできません。','muted'));
   const next=dom('details',undefined,'source-next');
   next.append(dom('summary','次に確認する資料（買い目は変えない）'));
   for(const text of sourceNextChecks(row))
    next.append(dom('p','・'+text,'muted'));
   panel.append(next);
   panel.append(dom('p','JRA公式出走馬・取消・馬場・発走時刻の独立確認：未接続。'+
    '総合評価・確定予想・購入は未実施。過去資料は下の任意照合で確認できます。','muted'));
   detail.append(panel);
  }
  if(race.status==='provisional_draft')detail.append(formation(race));
  const raceKey=race.track+'|'+race.race;
  nodes.push({key:raceKey,track:race.track,node:detail});
  const option=dom('option',race.track+' '+race.race+'R｜'+
   (race.status==='provisional_draft'?'研究用下書き '+race.points+'点':'見送り'));
  option.value=raceKey;select.append(option);
  groups.set(race.track,(groups.get(race.track)||0)+1);
 }
 // Selection uses an already verified day snapshot. No extra JRDB calls,
 // no prediction reconstruction, no receipt or purchase write.
 function show(track,key=''){
  const frag=document.createDocumentFragment();
  let visible=0;
  for(const item of nodes){
   if(key?item.key===key:!track||item.track===track){
    item.node.open=Boolean(key);
    frag.append(item.node);visible++;
   }
  }
  host.replaceChildren(frag);
  $('autoViewingStatus').textContent=key
   ?'選択中：'+key.replace('|',' ')+'R。研究用データのみ。'
   :track?track+' '+visible+'Rを表示（正式予想ではありません）'
   :'全場 '+visible+'Rを表示。レース選択で1Rだけ開けます。';
  for(const b of tabs.querySelectorAll('button'))b.setAttribute(
   'aria-pressed',String(b.dataset.track===track));
 }
 select.disabled=nodes.length===0;
 select.onchange=()=>{
  const key=select.value;
  // Do not accept a stale or forged ID from an old day.
  if(key&&!nodes.some(r=>r.key===key)){
   select.value='';show('');return;
  }
  show(key?nodes.find(r=>r.key===key).track:'',key);
 };
 for(const track of ['',...groups.keys()]){
  const button=dom('button',track?track+' '+groups.get(track)+'R':'全場 '+data.raceCount+'R');
  button.type='button';button.dataset.track=track;
  button.setAttribute('aria-pressed','false');
  button.onclick=()=>{select.value='';show(track);};tabs.append(button);
 }
 show('');
 const breakdown=Object.entries(data.holdReasons).sort((a,b)=>b[1]-a[1])
  .map(([reason,count])=>SHORT_HOLDS[reason]+' '+count+'R').join('／');
 $('autoSummary').textContent=data.raceCount+'R中、研究用自動案 '+data.draftCount+
  'R／見送り '+data.holdCount+'R。'+
  (breakdown?'内訳：'+breakdown+'。':'')+
  'JRDBの2項目だけを買い目に使用。コース条件の存在 '+ctx.courseInfoPresentCount+
  'R／馬場資料の存在 '+ctx.goingAvailableCount+'R（適性は未評価）。追加資料：'+
  (data.sourceMaterials.status==='observed'?'血統・枠などの材料を確認（採点なし）':'照合保留')+
  '。JRA公式照合や正式な投票は未実施。';
}
function localReceiptStatus(day){
 // Only inspect previously sealed local snapshots. Never treat draft
 // predictions or server response content as actual purchases.
 if(!/^20[0-9]{6}$/.test(day))return '開催日を選択してください。';
 try{
  const raw=localStorage.getItem(RECEIPTS_KEY);
  if(!raw)return 'この開催日の端末内固定済み研究記録はありません。';
  if(raw.length>650000)throw Error('large');
  const values=JSON.parse(raw);
  if(!Array.isArray(values)||values.length>360)throw Error('shape');
  const selected=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
  const ids=new Set();
  for(const entry of values){
   if(!entry||!entry.snapshot||typeof entry.signature!=='string')
    throw Error('receipt');
   const s=entry.snapshot;
   if(s.date===selected){
    if(typeof s.track!=='string'||!Number.isInteger(s.race))
     throw Error('identity');
    ids.add(s.track+'|'+s.race);
   }
  }
  return ids.size?'この開催日の端末内固定済み研究記録 '+ids.size+
   'R。既存の買い目は変更しません。':
   'この開催日の端末内固定済み研究記録はありません。';
 }catch(_){
  return '端末内の固定記録を確認できません。既存データは変更しません。';
 }
}
function selectedReceiptsForVerification(day){
 // Reuse only the locally locked per-day receipts. This code NEVER submits
 // paid JRDB rows or secrets, and cannot create retrospective race tickets.
 if(!/^20[0-9]{6}$/.test(day))throw Error('bad_date');
 const date=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 const raw=localStorage.getItem(RECEIPTS_KEY);
 if(!raw)return [];
 if(raw.length>650000)throw Error('oversized_store');
 const values=JSON.parse(raw);
 if(!Array.isArray(values)||values.length>360)throw Error('bad_store');
 const seen=new Set(),selected=[];
 const tracks=new Set(['札幌','函館','福島','新潟','東京',
  '中山','中京','京都','阪神','小倉']);
 for(const entry of values){
  const p=entry?.snapshot;
  if(!p||typeof p.date!=='string'||typeof entry.signature!=='string'||
     !/^[a-f0-9]{64}$/.test(entry.signature))
   throw Error('bad_receipt');
  if(p.date!==date)continue;
  if(!tracks.has(p.track)||!Number.isInteger(p.race)||
     p.race<1||p.race>12||seen.has(p.track+'|'+p.race)||
     p.sourceKind!=='prestart-locked'||p.actualPurchase!==false||
     p.scheduleVerified!==false||p.predictionVerified!==false||
     !Array.isArray(p.trifectaTickets)||p.trifectaTickets.length<1||
     p.trifectaTickets.length>48||
     !Array.isArray(p.trioTickets)||p.trioTickets.length!==0||
     typeof p.lockedAt!=='string'||typeof p.scheduledOffAt!=='string'||
     !Number.isFinite(Date.parse(p.lockedAt))||
     !Number.isFinite(Date.parse(p.scheduledOffAt))||
     Date.parse(p.lockedAt)>=Date.parse(p.scheduledOffAt))
   throw Error('invalid_source');
  const combinations=new Set();
  for(const ticket of p.trifectaTickets){
   if(!Array.isArray(ticket)||ticket.length!==3||
      ticket.some(n=>!Number.isInteger(n)||n<1||n>18)||
      new Set(ticket).size!==3||combinations.has(ticket.join('-')))
    throw Error('invalid_ticket');
   combinations.add(ticket.join('-'));
  }
  seen.add(p.track+'|'+p.race);
  selected.push(entry);
 }
 if(selected.length>36)throw Error('too_many');
 return selected;
}
function showFixedHistory(day){
 const root=$('autoHistory'),label=$('autoHistoryStatus');
 root.replaceChildren();
 if(!/^20[0-9]{6}$/.test(day)){label.textContent='開催日を選択してください。';return;}
 const selected=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 try{
  const raw=localStorage.getItem(RECEIPTS_KEY);
  if(!raw){label.textContent='この日の固定記録は端末にありません。別のSafari・ホーム画面やバックアップも確認できます。';return;}
  if(raw.length>650000)throw Error('large');
  const records=JSON.parse(raw);
  if(!Array.isArray(records)||records.length>360)throw Error('shape');
  const seen=new Set(),rows=[];
  const venues=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
  for(const r of records){
   if(!r||!r.snapshot||typeof r.signature!=='string'||
      !/^[0-9a-f]{64}$/.test(r.signature))throw Error('record');
   const s=r.snapshot;
   if(s.date!==selected)continue;
   const key=s.track+'|'+s.race;
   if(!venues.has(s.track)||!Number.isInteger(s.race)||s.race<1||s.race>12||
      seen.has(key)||s.sourceKind!=='prestart-locked'||
      s.actualPurchase!==false||s.scheduleVerified!==false||
      s.predictionVerified!==false||
      typeof s.lockedAt!=='string'||typeof s.scheduledOffAt!=='string'||
      !/(?:Z|[+-]\d\d:\d\d)$/.test(s.lockedAt)||
      !/(?:Z|[+-]\d\d:\d\d)$/.test(s.scheduledOffAt)||
      !Number.isFinite(Date.parse(s.lockedAt))||
      !Number.isFinite(Date.parse(s.scheduledOffAt))||
      Date.parse(s.lockedAt)>=Date.parse(s.scheduledOffAt)||
      !Array.isArray(s.trifectaTickets)||s.trifectaTickets.length>48||
      !Array.isArray(s.trioTickets)||s.trioTickets.length>48)
     throw Error('unsafe');
   const unique=new Set();
   for(const t of s.trifectaTickets){
    if(!Array.isArray(t)||t.length!==3||
       t.some(n=>!Number.isInteger(n)||n<1||n>18)||
       new Set(t).size!==3||unique.has(t.join('-')))throw Error('ticket');
    unique.add(t.join('-'));
   }
   seen.add(key);rows.push(s);
  }
  rows.sort((a,b)=>a.track.localeCompare(b.track,'ja')||a.race-b.race);
  if(!rows.length){label.textContent='この日の固定記録は端末にありません。別のSafari・ホーム画面やバックアップも確認できます。';return;}
  label.textContent='発走前固定 '+rows.length+'R（端末保存・署名は未検証・実購入なし）。';
  for(const s of rows){
   const tickets=s.trifectaTickets;
   const detail=dom('details');
   detail.append(dom('summary',s.track+' '+s.race+'R｜3連単 '+tickets.length+
     '点｜100円換算 '+(tickets.length*100).toLocaleString('ja-JP')+'円'));
   detail.append(dom('p','固定日時：'+s.lockedAt+'／暫定発走時刻：'+
      s.scheduledOffAt,'muted'));
   if(tickets.length){
    const set=i=>[...new Set(tickets.map(t=>t[i]))].sort((a,b)=>a-b).join('・');
    detail.append(dom('p','1着候補：'+set(0)+'番','picks'),
     dom('p','2着に含む：'+set(1)+'番','picks'),
     dom('p','3着に含む：'+set(2)+'番','picks'),
     dom('p',tickets.map(t=>t.join('→')).join(' / '),'ticket-list'));
   }
   root.append(detail);
  }
 }catch(_){
  root.replaceChildren();
  label.textContent='固定記録の形式が不正です。既存記録は変更せず、バックアップを確認してください。';
 }
}
function saveAutoReceipts(data,day){
 if(data.serverStamped!==true||data.captureAuditVerified!==false||
  !Array.isArray(data.researchReceipts)||data.researchReceipts.length>36||
  data.researchReceiptCount!==data.researchReceipts.length)
  throw Error('署名付き研究記録の形式を確認できません');
 const signed=data.researchReceipts,expectedDay=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 const available=new Map(data.races.filter(r=>r.status==='provisional_draft')
  .map(r=>[r.track+'|'+r.race,r]));
 const seen=new Set();
 for(const row of signed){
  const s=row&&row.snapshot,entry=s&&available.get(s.track+'|'+s.race);
  const id=s&&s.date+'|'+s.track+'|'+s.race;
  if(!s||!entry||seen.has(id)||s.date!==expectedDay||
   s.sourceKind!=='prestart-locked'||s.actualPurchase!==false||
   s.scheduleVerified!==false||s.predictionVerified!==false||
   typeof row.signature!=='string'||!/^[0-9a-f]{64}$/.test(row.signature)||
   !Array.isArray(s.trifectaTickets)||s.trifectaTickets.length!==entry.points||
   !Array.isArray(s.trioTickets)||s.trioTickets.length!==0||
   !s.trifectaTickets.every(t=>Array.isArray(t)&&t.length===3)||
   JSON.stringify(entry.tickets.map(t=>t.join('-')).sort())!==
   JSON.stringify(s.trifectaTickets.map(t=>t.join('-')).sort())||
   typeof s.lockedAt!=='string'||typeof s.scheduledOffAt!=='string')
    throw Error('固定用の研究記録を照合できません');
  seen.add(id);
 }
 if(!signed.length)return localReceiptStatus(day)+
  ' 発走前に新しく固定できる研究用買い目はありません。';
 const raw=localStorage.getItem(RECEIPTS_KEY);
 if(raw&&raw.length>650000)throw Error('端末内の固定記録が上限を超えました');
 const existing=JSON.parse(raw||'[]');
 if(!Array.isArray(existing)||existing.length>360)throw Error('保存済みの記録形式を確認できません');
 const identities=new Set(existing.map(x=>{
  if(!x||!x.snapshot||typeof x.signature!=='string')throw Error('古い記録に不整合があります');
  return x.snapshot.date+'|'+x.snapshot.track+'|'+x.snapshot.race;
 }));
 let added=0;
 const combined=existing.slice();
 for(const receipt of signed){
  const s=receipt.snapshot,id=s.date+'|'+s.track+'|'+s.race;
  if(identities.has(id))continue; // The first research receipt wins.
  identities.add(id);combined.push(receipt);added++;
 }
 if(combined.length>360)throw Error('保存数の上限です');
 if(added)localStorage.setItem(RECEIPTS_KEY,JSON.stringify(combined));
 return '署名付き研究記録：新規 '+added+'R／既存の固定記録は上書きせず維持。'+
  '保存先はこのiPhone内のみ（Safariとホーム画面で別の場合あり）。';
}

const WATCH_STORAGE='keiba-nine-owner-rebound-watch-receipts-v1';
let request=0,followingToday=true,historySeq=0,watchResultSeq=0,
 prestartSeq=0,connectionSeq=0,receiptVerifySeq=0,
 historyDay='',historyCoordinates=new Set(),
 historyRosters=new Map(),historyReboundWatch=new Map(),historyStyles=new Map(),
 historyGrades=new Map(),historyStatuses=new Map();
function clearHistory(){
 receiptVerifySeq++;
 $('autoReceiptVerify').disabled=false;
 $('autoReceiptVerifyStatus').textContent='署名は未確認。保存済み記録は変更していません。';
 connectionSeq++;
 $('autoConnectionCheck').disabled=false;
 $('autoConnectionStatus').textContent='診断は未実行。';
 prestartSeq++;
 $('autoPrestartRaces').replaceChildren();
 $('autoPrestartStatus').textContent='本人操作時だけ追加API照合。予想や買い目は変更しません。';
 $('autoPrestartBody').disabled=false;
 historySeq++;historyDay='';historyCoordinates=new Set();
 historyRosters=new Map();historyReboundWatch=new Map();historyStyles=new Map();
 historyGrades=new Map();historyStatuses=new Map();
 $('autoHistoryAudit').disabled=true;
 $('autoHistoryAuditRaces').replaceChildren();
 $('autoHistoryAuditStatus').textContent='暫定予想の取得後に利用できます。';
 $('autoHistoryWatchSave').textContent='発走前の候補記録は未確認。';
 watchResultSeq++;
 $('autoWatchResultRaces').replaceChildren();
 $('autoWatchResultStatus').textContent='発走前の固定候補がありません。';
 refreshWatchResultsAvailability();
}
function storedWatchDay(day){
 const raw=localStorage.getItem(WATCH_STORAGE);
 if(raw&&raw.length>700000)throw Error('保存した候補記録が大きすぎます');
 const stored=JSON.parse(raw||'[]');
 if(!Array.isArray(stored)||stored.length>360)throw Error('保存した候補記録が不正');
 const selected=stored.filter(x=>x&&x.snapshot&&x.snapshot.date===day);
 if(selected.length>36)throw Error('同日の候補が多すぎます');
 const used=new Set();
 for(const row of selected){
  if(!row||!row.snapshot||typeof row.signature!=='string'||
     !/^[0-9a-f]{64}$/.test(row.signature))
   throw Error('保存した署名が不正');
  const s=row.snapshot,id=s.date+'|'+s.track+'|'+s.race;
  if(used.has(id)||!Array.isArray(s.watch)||!s.watch.length||
     s.version!=='owner-rebound-watch-receipt-1')
   throw Error('保存した候補の形式不正');
  used.add(id);
 }
 return selected;
}
function refreshWatchResultsAvailability(preserveStatus=false){
 const day=$('autoDay').value.replaceAll('-','');
 try{
  const saved=storedWatchDay(day);
  $('autoWatchResultCheck').disabled=!saved.length;
  if(saved.length&&!preserveStatus){
   $('autoWatchResultStatus').textContent=
    '発走前の署名付き巻き返し候補：'+saved.length+
    'R。JRDB成績の参考照合は押したときだけ実行。';
  }
 }catch(_){
  $('autoWatchResultCheck').disabled=true;
  $('autoWatchResultStatus').textContent=
   '保存済み候補に不整合があります。成績照合は実行しません。';
 }
}
function validateProviderCheck(result,receipts,day){
 if(!result||result.version!=='owner-rebound-provider-check-1'||
    result.date!==day||
    result.sourceKind!=='jrdb-tse-provider-observation'||
    result.officialJraVerified!==false||
    result.jraIndependentConfirmation!==false||
    result.officialFeedConnected!==false||
    result.outcomeCalibrationReady!==false||
    result.bettingReady!==false||
    result.actualPurchase!==false||
    result.payoutVerified!==false||
    result.roiPercent!==null||
    result.researchOnly!==true||
    result.privateOwnerOnly!==true||
    result.sourceIncompleteCouldChange!==true||
    result.verifiedRaceCount!==0||
    result.verifiedWatchHitCount!==null||
    !Number.isInteger(result.providerSourceReadCount)||
    result.providerSourceReadCount<0||result.providerSourceReadCount>1||
    !Number.isInteger(result.raceCount)||
    result.raceCount!==receipts.length||
    !Array.isArray(result.races)||result.races.length!==receipts.length||
    !Number.isInteger(result.observedRaceCount)||
    !Number.isInteger(result.observedFirstInWatchCount)||
    !Number.isInteger(result.observedFirstInPriorityCount))
  throw Error('暫定成績の形式が不正');
 const byKey=new Map(receipts.map(x=>[
  x.snapshot.track+'|'+x.snapshot.race,x.snapshot
 ]));
 let observed=0,observedWatched=0,observedPriority=0;
 const seen=new Set();
 for(const r of result.races){
  if(!r||typeof r.track!=='string'||!Number.isInteger(r.race)||
     !Number.isInteger(r.watchCount)||
     r.officialVerified!==false||r.confirmedWatchHit!==null||
     r.confirmedPredictionHit!==null||
     !['pending','first_place_observed'].includes(r.providerStatus))
   throw Error('暫定成績が不正');
  const key=r.track+'|'+r.race,prev=byKey.get(key);
  if(!prev||seen.has(key)||r.watchCount!==prev.watch.length)
   throw Error('発走前記録と成績のレース不一致');
  seen.add(key);
  if(r.providerStatus==='pending'){
   if(r.observedFirstNumber!==null||r.observedFirstInWatch!==null||
      r.observedFirstInPriorityWatch!==null)
    throw Error('未確認レースの値が不正');
   continue;
  }
  const winner=r.observedFirstNumber;
  if(!Number.isInteger(winner)||winner<1||winner>18||
     typeof r.observedFirstInWatch!=='boolean'||
     typeof r.observedFirstInPriorityWatch!=='boolean')
   throw Error('暫定1着馬番が不正');
  const state=prev.watch.find(x=>x.number===winner)?.reviewState;
  if(r.observedFirstInWatch!==(state!==undefined)||
     r.observedFirstInPriorityWatch!==(state==='cross_source_review'))
   throw Error('暫定1着と発走前候補が不一致');
  observed++;
  if(r.observedFirstInWatch)observedWatched++;
  if(r.observedFirstInPriorityWatch)observedPriority++;
 }
 if(seen.size!==receipts.length||
    observed!==result.observedRaceCount||
    observedWatched!==result.observedFirstInWatchCount||
    observedPriority!==result.observedFirstInPriorityCount)
  throw Error('暫定成績の集計が不一致');
 return result;
}
function validateWatchCapture(capture,history){
 if(!capture||capture.version!=='owner-rebound-watch-receipt-1'||
    capture.date!==historyDay||capture.serverSigned!==true||
    capture.officialFeedConnected!==false||
    capture.jraScheduleVerified!==false||
    capture.officialResultsVerified!==false||
    capture.actualPurchase!==false||capture.purchaseReady!==false||
    !Number.isInteger(capture.receiptCount)||capture.receiptCount<0||
    capture.receiptCount>36||
    !Number.isInteger(capture.postOffOrMissingTimeRaces)||
    !Array.isArray(capture.receipts)||
    capture.receipts.length!==capture.receiptCount)
   throw Error('発走前の候補記録が不正');
 const races=new Map(history.reboundContextReview.races.map(
  r=>[r.track+'|'+r.race,r]));
 const seen=new Set();
 for(const entry of capture.receipts){
  if(!entry||!entry.snapshot||typeof entry.signature!=='string'||
     !/^[0-9a-f]{64}$/.test(entry.signature))
   throw Error('候補の署名形式が不正');
  const p=entry.snapshot,id=p.track+'|'+p.race,source=races.get(id);
  if(!source||seen.has(id)||p.date!==historyDay||
     p.version!=='owner-rebound-watch-receipt-1'||
     p.sourceKind!=='server-prestart-research-watch'||
     p.researchOnly!==true||p.officialJraVerified!==false||
     p.actualPurchase!==false||p.winnerPickReady!==false||
     p.captureAuditVerified!==false||!Array.isArray(p.watch)||
     !p.watch.length||p.watch.length!==source.watchCount||
     typeof p.capturedAt!=='string'||
     typeof p.scheduledOffAt!=='string')
   throw Error('候補の開催日・レースが不一致');
  const captured=Date.parse(p.capturedAt),off=Date.parse(p.scheduledOffAt);
  if(!Number.isFinite(captured)||!Number.isFinite(off)||captured>=off||
     new Date(off).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'})
      .replaceAll('-','')!==historyDay)
   throw Error('発走前の記録時刻が不一致');
  seen.add(id);
  const sourceByNumber=new Map(source.watch.map(r=>[r.number,r.reviewState]));
  let last=0;
  for(const h of p.watch){
   if(!h||!Number.isInteger(h.number)||h.number<=last||
      h.number>18||h.reviewState!==sourceByNumber.get(h.number))
    throw Error('固定された候補の馬番・根拠が不一致');
   last=h.number;
  }
 }
 return capture;
}
function saveReboundWatch(receipts){
 if(!receipts.length)return '発走前の署名付き候補なし（対象レースが開始済み、または候補なし）。';
 const raw=localStorage.getItem(WATCH_STORAGE);
 if(raw&&raw.length>700000)throw Error('端末の保存記録が大きすぎます');
 const stored=JSON.parse(raw||'[]');
 if(!Array.isArray(stored)||stored.length>360)throw Error('保存記録が不正');
 const identities=new Set();
 for(const entry of stored){
  if(!entry||!entry.snapshot||typeof entry.signature!=='string'||
     !/^[0-9a-f]{64}$/.test(entry.signature))
   throw Error('既存の候補記録の形式を確認できません');
  const p=entry.snapshot,key=p.date+'|'+p.track+'|'+p.race;
  if(identities.has(key))throw Error('既存の候補記録が重複しています');
  identities.add(key);
 }
 const combined=stored.slice();let added=0,unchanged=0;
 for(const entry of receipts){
  const p=entry.snapshot,key=p.date+'|'+p.track+'|'+p.race;
  if(identities.has(key)){unchanged++;continue;}
  identities.add(key);combined.push(entry);added++;
 }
 if(combined.length>360)throw Error('保存件数の上限です');
 if(added)localStorage.setItem(WATCH_STORAGE,JSON.stringify(combined));
 return '発走前の巻き返し候補を署名検証して固定：新規 '+added+
  'R／既存 '+unchanged+'R。端末保存のためSafariとホーム画面で別の場合があります。';
}
function validateHistory(h){
 if(!h||h.version!=='bounded-history-1'||h.date!==historyDay||
    h.predictionReady!==false||h.goingSuitabilityAssessed!==false||
    typeof h.historyComplete!=='boolean'||h.maxTotalCalls!==16||
    !Number.isInteger(h.draCalls)||h.draCalls<0||h.draCalls>8||
    !Number.isInteger(h.dkaCalls)||h.dkaCalls<0||h.dkaCalls>h.draCalls||
    !Number.isInteger(h.referencedPastRaces)||h.referencedPastRaces<0||
    !Number.isInteger(h.selectedPastRaces)||h.selectedPastRaces<0||
    h.selectedPastRaces>8||h.selectedPastRaces>h.referencedPastRaces||
    !Number.isInteger(h.deferredPastRaces)||
    h.deferredPastRaces!==h.referencedPastRaces-h.selectedPastRaces||
    !h.privateHistoryFactors||
    h.privateHistoryFactors.version!=='private-course-ground-materials-1'||
    h.privateHistoryFactors.predictionReady!==false||
    h.privateHistoryFactors.bettingReady!==false||
    h.privateHistoryFactors.raceCount!==historyCoordinates.size||
    !Array.isArray(h.privateHistoryFactors.races)||
    h.privateHistoryFactors.races.length!==historyCoordinates.size||
    !h.ownerRunnerHistory||
    h.ownerRunnerHistory.version!=='owner-runner-course-going-observation-2'||
    h.ownerRunnerHistory.researchOnly!==true||
    h.ownerRunnerHistory.privateOwnerOnly!==true||
    h.ownerRunnerHistory.officialJraVerified!==false||
    h.ownerRunnerHistory.gradeReady!==false||
    h.ownerRunnerHistory.predictionReady!==false||
    h.ownerRunnerHistory.bettingReady!==false||
    h.ownerRunnerHistory.raceCount!==historyCoordinates.size||
    !Array.isArray(h.ownerRunnerHistory.races)||
    h.ownerRunnerHistory.races.length!==historyCoordinates.size||
    !h.historicalEvidenceBands||
    h.historicalEvidenceBands.version!=='owner-condition-evidence-hypothesis-1'||
    h.historicalEvidenceBands.sourceVersion!=='owner-runner-course-going-observation-2'||
    h.historicalEvidenceBands.minComparableSamples!==3||
    h.historicalEvidenceBands.courseDistanceWeight!==20||
    h.historicalEvidenceBands.goingWeight!==12||
    h.historicalEvidenceBands.evidenceBandsNotSuitability!==true||
    h.historicalEvidenceBands.negativeBandNeverExcludesRebound!==true||
    h.historicalEvidenceBands.researchOnly!==true||
    h.historicalEvidenceBands.privateOwnerOnly!==true||
    h.historicalEvidenceBands.officialJraVerified!==false||
    h.historicalEvidenceBands.overallScoreReady!==false||
    h.historicalEvidenceBands.winnerPickReady!==false||
    h.historicalEvidenceBands.bettingReady!==false||
    h.historicalEvidenceBands.raceCount!==historyCoordinates.size||
    !Array.isArray(h.historicalEvidenceBands.races)||
    h.historicalEvidenceBands.races.length!==historyCoordinates.size||
    !h.paceScenarioHypotheses||
    h.paceScenarioHypotheses.version!=='owner-pace-scenario-hypothesis-1'||
    h.paceScenarioHypotheses.factorWeight!==20||
    h.paceScenarioHypotheses.minObservedFieldShare!=='3/5'||
    h.paceScenarioHypotheses.minObservedRunners!==3||
    h.paceScenarioHypotheses.researchOnly!==true||
    h.paceScenarioHypotheses.privateOwnerOnly!==true||
    h.paceScenarioHypotheses.officialJraVerified!==false||
    h.paceScenarioHypotheses.scenarioNotActualPace!==true||
    h.paceScenarioHypotheses.bandNotVerifiedFactorGrade!==true||
    h.paceScenarioHypotheses.overallScoreReady!==false||
    h.paceScenarioHypotheses.winnerPickReady!==false||
    h.paceScenarioHypotheses.bettingReady!==false||
    h.paceScenarioHypotheses.raceCount!==historyCoordinates.size||
    !Array.isArray(h.paceScenarioHypotheses.races)||
    h.paceScenarioHypotheses.races.length!==historyCoordinates.size||
    !h.reboundContextReview||
    h.reboundContextReview.version!=='owner-rebound-context-review-1'||
    h.reboundContextReview.policyVersion!=='research-5'||
    h.reboundContextReview.researchOnly!==true||
    h.reboundContextReview.privateOwnerOnly!==true||
    h.reboundContextReview.officialJraVerified!==false||
    h.reboundContextReview.overallScoreReady!==false||
    h.reboundContextReview.winPickReady!==false||
    h.reboundContextReview.bettingReady!==false||
    h.reboundContextReview.autoPurchase!==false||
    h.reboundContextReview.modifiesFrozenPicks!==false||
    h.reboundContextReview.contextRequiresPaceAndHistory!==true||
    h.reboundContextReview.historyOnlySignalsMayOverlap!==true||
    !h.reboundContextReview.factorWeights||
    Object.keys(h.reboundContextReview.factorWeights).length!==5||
    ['training','recent','course_distance','pace','ground']
     .some((k,i)=>h.reboundContextReview.factorWeights[k]!==[30,3,20,20,12][i])||
    h.reboundContextReview.raceCount!==historyCoordinates.size||
    !Array.isArray(h.reboundContextReview.races)||
    h.reboundContextReview.races.length!==historyCoordinates.size||
    !Number.isInteger(h.reboundContextReview.watchCount)||
    !Number.isInteger(h.reboundContextReview.crossSourceReviewCount)||
    h.reboundContextReview.crossSourceReviewCount>h.reboundContextReview.watchCount||
    !h.realAssessmentPreflight||
    h.realAssessmentPreflight.version!=='real-assessment-preflight-1'||
    h.realAssessmentPreflight.realGradeReady!==false||
    h.realAssessmentPreflight.realPredictionReady!==false||
    h.realAssessmentPreflight.purchaseReady!==false)
  throw Error('過去資料形式不正');
 const perRace=new Map();
 for(const item of h.ownerRunnerHistory.races){
  if(!item||typeof item.track!=='string'||!Number.isInteger(item.race)||
     item.gradeReady!==false||item.courseSuitabilityAssessed!==false||
     item.goingSuitabilityAssessed!==false||item.paceForecastReady!==false||
     !Number.isInteger(item.runnerCount)||item.runnerCount<0||
     item.runnerCount>18||!Array.isArray(item.runners)||
     item.runnerCount!==item.runners.length)throw Error('馬番別の履歴形式が不正');
  const id=item.track+'|'+item.race;
  if(!historyCoordinates.has(id)||perRace.has(id))
   throw Error('馬番別履歴のレースが一致しません');
  const roster=historyRosters.get(id),seenHorse=new Set();
  for(const h of item.runners){
   if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
      seenHorse.has(h.number)||!Number.isInteger(h.comparableRuns)||
      !Number.isInteger(h.comparableTopThreeRuns)||
      !Number.isInteger(h.knownGoingRuns)||
      !Number.isInteger(h.matchingCurrentGoingRuns)||
      !Number.isInteger(h.matchingCurrentGoingTopThreeRuns)||
      !Number.isInteger(h.wetGoingRuns)||
      !Number.isInteger(h.wetTopThreeRuns)||
      !Number.isInteger(h.missingPastProgrammes)||
      ![h.comparableRuns,h.comparableTopThreeRuns,h.knownGoingRuns,
        h.matchingCurrentGoingRuns,h.matchingCurrentGoingTopThreeRuns,
        h.wetGoingRuns,h.wetTopThreeRuns,h.missingPastProgrammes
       ].every(n=>n>=0&&n<=5)||
      h.comparableTopThreeRuns>h.comparableRuns||
      h.knownGoingRuns>h.comparableRuns||
      h.matchingCurrentGoingRuns>h.knownGoingRuns||
      h.matchingCurrentGoingTopThreeRuns>h.matchingCurrentGoingRuns||
      h.wetGoingRuns>h.knownGoingRuns||
      h.wetTopThreeRuns>h.wetGoingRuns||
      typeof h.historyLookupComplete!=='boolean'||
      typeof h.currentGoingRecorded!=='boolean'||
      (!h.currentGoingRecorded&&(h.matchingCurrentGoingRuns!==0||
        h.matchingCurrentGoingTopThreeRuns!==0)))
     throw Error('馬番別履歴の件数不一致');
   seenHorse.add(h.number);
  }
  // A held race has no complete owner-draft roster: hide its per-horse
  // observations instead of joining to numbers with uncertain identity.
  const rosterVerified=roster&&roster.size===item.runnerCount&&
   item.runners.every(h=>roster.has(h.number));
  // A complete roster must match exactly. Only an unassessed/held race
  // may fall back to redacted race-level counters.
  if(roster&&roster.size>0&&!rosterVerified)
   throw Error('現在の馬番と過去資料の馬番が不一致');
  perRace.set(id,{...item,runners:rosterVerified?item.runners:[],
   rosterVerified:!!rosterVerified});
 }
 // Independently recompute descriptive bands from checked 0..5 counts.
 // They do not create real suitability grades or 3連単 candidates.
 function expectedBand(n,hits,complete){
  if(!complete)return ['未評価','incomplete_history'];
  if(n<3)return ['未評価','sample_below_three'];
  if(n===5&&hits===0)return ['C','observed_five_without_top_three'];
  if(hits>=2&&3*hits>=2*n)return ['S','observed_two_thirds_top_three'];
  if(hits>=1&&3*hits>=n)return ['A','observed_one_third_top_three'];
  return ['B','observed_limited_top_three'];
 }
 const bandRaces=new Set();
 for(const b of h.historicalEvidenceBands.races){
  if(!b||typeof b.track!=='string'||!Number.isInteger(b.race)||
     !Number.isInteger(b.runnerCount)||b.runnerCount<0||
     b.runnerCount>18||!Array.isArray(b.runners)||
     b.runners.length!==b.runnerCount||
     b.overallScoreReady!==false||b.winnerPickReady!==false)
   throw Error('過去好走指標の形式不正');
  const id=b.track+'|'+b.race,actual=perRace.get(id);
  if(!actual||bandRaces.has(id)||actual.runnerCount!==b.runnerCount)
   throw Error('過去好走指標のレース不一致');
  bandRaces.add(id);
  const source=new Map(actual.runners.length
   ?actual.runners.map(x=>[x.number,x]):h.ownerRunnerHistory.races.find(
     x=>x.track===b.track&&x.race===b.race).runners.map(x=>[x.number,x]));
  const details=new Map();
  for(const a of b.runners){
   if(!a||!Number.isInteger(a.number)||details.has(a.number)||
      !source.has(a.number))throw Error('過去好走指標の馬番不一致');
   const v=source.get(a.number);
   const course=expectedBand(v.comparableRuns,v.comparableTopThreeRuns,
    v.historyLookupComplete);
   const ground=!v.currentGoingRecorded?['未評価','current_going_unknown']:
    !v.historyLookupComplete||v.knownGoingRuns!==v.comparableRuns
     ?['未評価','incomplete_history']
     :expectedBand(v.matchingCurrentGoingRuns,
                   v.matchingCurrentGoingTopThreeRuns,true);
   if(a.courseEvidenceBand!==course[0]||a.courseReason!==course[1]||
      a.goingEvidenceBand!==ground[0]||a.goingReason!==ground[1])
    throw Error('過去好走指標の採点根拠が一致しません');
   details.set(a.number,a);
  }
  if(details.size!==actual.runnerCount)
   throw Error('過去好走指標の馬番不足');
  actual.experimental=details;
 }
 if(bandRaces.size!==historyCoordinates.size)
  throw Error('過去好走指標のレース不足');
 // Compare each scenario with independent current-day runner positions and
 // recompute its coverage / pressure and exploratory fit before displaying.
 const paceRaces=new Set();
 const styles=['frontObserved','backObserved','mixedObserved','insufficient'];
 function paceBand(style,pressure,enough){
  if(!enough||style==='insufficient')return ['未評価','insufficient_position_coverage'];
  if(pressure==='single_front_observed')
   return style==='frontObserved'?['S','possible_single_front_advantage']:
    ['B','low_observed_front_pressure'];
  if(pressure==='two_front_observed')
   return style==='frontObserved'?['A','two_front_candidates']:
    ['B','uncertain_chase_scenario'];
  if(pressure==='multiple_front_observed')
   return style==='backObserved'?['A','possible_late_run_if_pressured']:
    style==='frontObserved'?['B','multiple_front_candidates']:
    ['B','mixed_position_under_pressure'];
  return ['未評価','no_observed_front_candidate'];
 }
 for(const pace of h.paceScenarioHypotheses.races){
  if(!pace||typeof pace.track!=='string'||!Number.isInteger(pace.race)||
     !Number.isInteger(pace.runnerCount)||pace.runnerCount<0||
     pace.runnerCount>18||!Array.isArray(pace.runners)||
     pace.runners.length!==pace.runnerCount||
     !['frontObserved','backObserved','mixedObserved','insufficient']
       .every(k=>Number.isInteger(pace[k])&&pace[k]>=0&&pace[k]<=18)||
     pace.gradeReady!==false||pace.bettingReady!==false||
     pace.paceForecastReady!==false||typeof pace.coverageAdequate!=='boolean')
   throw Error('展開仮説の形式不正');
  const id=pace.track+'|'+pace.race,history=perRace.get(id);
  if(!history||paceRaces.has(id)||history.runnerCount!==pace.runnerCount)
   throw Error('展開仮説のレース不一致');
  paceRaces.add(id);
  const front=pace.frontObserved,back=pace.backObserved,mixed=pace.mixedObserved;
  const insufficient=pace.insufficient;
  const n=pace.runnerCount;
  const enough=n>=3&&(n-insufficient)>=3&&(n-insufficient)*5>=3*n;
  const pressure=!enough?'coverage_insufficient':
   front===0?'no_front_observed':
   front===1?'single_front_observed':
   front===2?'two_front_observed':'multiple_front_observed';
  if(front+back+mixed+insufficient!==n||
     pace.coverageAdequate!==enough||pace.pacePressureScenario!==pressure)
   throw Error('展開仮説の先行候補数が不一致');
  const known=historyStyles.get(id)||new Map(),seenHorse=new Set();
  const roster=historyRosters.get(id)||new Set();
  for(const row of pace.runners){
   if(!row||!Number.isInteger(row.number)||row.number<1||row.number>18||
      seenHorse.has(row.number)||!styles.includes(row.pastFourthCorner))
    throw Error('展開仮説の馬番形式不正');
   seenHorse.add(row.number);
   const score=paceBand(row.pastFourthCorner,pressure,enough);
   if(row.scenarioFitBand!==score[0]||row.reason!==score[1]||
      (roster.size>0&&known.get(row.number)!==row.pastFourthCorner))
    throw Error('展開仮説の根拠が不一致');
  }
  const totals=Object.fromEntries(styles.map(k=>[k,0]));
  for(const row of pace.runners)totals[row.pastFourthCorner]++;
  if(seenHorse.size!==n||styles.some(k=>totals[k]!==pace[k]))
   throw Error('展開仮説の頭数が不一致');
  if(roster.size>0&&(roster.size!==n||pace.runners.some(r=>!roster.has(r.number))))
   throw Error('展開仮説の出走馬が不一致');
  history.paceScenario=pace;
  history.paceByNumber=new Map(pace.runners.map(r=>[r.number,r]));
 }
 if(paceRaces.size!==historyCoordinates.size)
  throw Error('展開仮説の対象レースが不足');
 const seen=new Set(),results=[];
 for(const row of h.privateHistoryFactors.races){
  if(!row||typeof row.track!=='string'||!Number.isInteger(row.race)||
     row.predictionReady!==false||row.bettingReady!==false||
     row.suitabilityAssessed!==false||row.overallRankReady!==false||
     row.verifiedFactorCount!==0||
     !Number.isInteger(row.runnerCount)||row.runnerCount<0||row.runnerCount>18||
     !Array.isArray(row.observationOnlyFactors)||
     row.observationOnlyFactors.join('|')!=='pace|course_distance|ground')
   throw Error('過去資料の評価状態不正');
  const id=row.track+'|'+row.race;
  if(!historyCoordinates.has(id)||seen.has(id))throw Error('開催レース不一致');
  seen.add(id);
  const stats=['runnersWithComparableCourse','runnersWithKnownGoingComparable',
   'runnersWithWetComparable','runnersMatchingCurrentGoing',
   'runnersWithIncompleteHistory'];
  if(stats.some(k=>!Number.isInteger(row[k])||row[k]<0||row[k]>row.runnerCount)||
     row.runnersWithKnownGoingComparable>row.runnersWithComparableCourse||
     row.runnersWithWetComparable>row.runnersWithKnownGoingComparable||
     row.runnersMatchingCurrentGoing>row.runnersWithKnownGoingComparable)
   throw Error('過去資料集計不正');
  const details=perRace.get(id);
  if(!details||details.runnerCount!==row.runnerCount)
   throw Error('馬番別履歴と集計が不一致');
  if(details.runners.length){
   const sum=(key)=>details.runners.filter(h=>h[key]>0).length;
   if(sum('comparableRuns')!==row.runnersWithComparableCourse||
      sum('knownGoingRuns')!==row.runnersWithKnownGoingComparable||
      sum('wetGoingRuns')!==row.runnersWithWetComparable||
      sum('matchingCurrentGoingRuns')!==row.runnersMatchingCurrentGoing)
    throw Error('馬番別履歴の集計が不一致');
  }
  results.push({...row,ownerRunnerDetails:details});
 }
 if(seen.size!==historyCoordinates.size)throw Error('過去レース不足');
 const reviewedRaces=new Set(), factors=['course_distance','pace','ground'];
 let allWatch=0,allPriority=0;
 for(const race of h.reboundContextReview.races){
  if(!race||typeof race.track!=='string'||!Number.isInteger(race.race)||
     !Number.isInteger(race.runnerCount)||race.runnerCount<0||
     race.runnerCount>18||race.winPickReady!==false||
     race.gradedTenFactors!==0||
     !Number.isInteger(race.watchCount)||race.watchCount<0||
     !Array.isArray(race.watch)||race.watchCount!==race.watch.length)
   throw Error('巻き返し確認用資料が不正');
  const id=race.track+'|'+race.race,entry=perRace.get(id);
  if(!entry||reviewedRaces.has(id)||race.runnerCount!==entry.runnerCount)
   throw Error('巻き返し確認用レースが不一致');
  reviewedRaces.add(id);
  const seenNumbers=new Set(),validOriginal=historyGrades.get(id)||new Map();
  const currentWatch=historyReboundWatch.get(id)||new Set();
  const currentIsDraft=historyStatuses.get(id)==='provisional_draft';
  let hasCross=0;
  for(const q of race.watch){
   if(!q||!Number.isInteger(q.number)||q.number<1||q.number>18||
      seenNumbers.has(q.number)||q.evidenceOnly!==true||
      q.winPickReady!==false||
      !['S','A'].includes(q.trainingProvisional)||
      !['B','C'].includes(q.recentProvisional)||
      !Array.isArray(q.supportingContextFactors)||
      !Array.isArray(q.unassessedContextFactors)||
      !Number.isInteger(q.contextSignalCount))
    throw Error('巻き返し候補の形式が不正');
   seenNumbers.add(q.number);
   const source=entry.experimental?.get(q.number),
         pace=entry.paceByNumber?.get(q.number);
   if(!source||!pace)throw Error('巻き返し候補の元資料が不一致');
   const snapshot={
    course_distance:source.courseEvidenceBand,
    pace:pace.scenarioFitBand,
    ground:source.goingEvidenceBand
   };
   const supports=factors.filter(k=>['S','A'].includes(snapshot[k]));
   const unknown=factors.filter(k=>snapshot[k]==='未評価');
   const cross=supports.includes('pace')&&
    (supports.includes('course_distance')||supports.includes('ground'));
   const overlap=!cross&&supports.includes('course_distance')&&
    supports.includes('ground');
   const state=cross?'cross_source_review':
    overlap?'overlapping_history_only':'need_more_evidence';
   if(q.courseEvidenceBand!==snapshot.course_distance||
      q.paceScenarioBand!==snapshot.pace||
      q.goingEvidenceBand!==snapshot.ground||
      q.contextSignalCount!==supports.length||
      q.supportingContextFactors.join('|')!==supports.join('|')||
      q.unassessedContextFactors.join('|')!==unknown.join('|')||
      q.reviewState!==state)
    throw Error('巻き返し候補の根拠と判定が不一致');
   if(currentIsDraft){
    const latest=validOriginal.get(q.number);
    if(!latest||!currentWatch.has(q.number)||
       q.trainingProvisional!==latest.training||
       q.recentProvisional!==latest.recent)
     throw Error('巻き返し候補と当日暫定評価の不一致');
   }
   if(cross)hasCross++;
  }
  // Do not blend an older snapshot with a newly selected/changed field.
  if(currentIsDraft&&(
      seenNumbers.size!==currentWatch.size||
      [...currentWatch].some(n=>!seenNumbers.has(n))))
   throw Error('発走前の巻き返し候補と過去資料が不一致');
  allWatch+=race.watchCount;
  allPriority+=hasCross;
  entry.reboundReview=currentIsDraft?race.watch:[];
  entry.reboundPriorityCount=currentIsDraft?hasCross:0;
 }
 if(reviewedRaces.size!==historyCoordinates.size||
    allWatch!==h.reboundContextReview.watchCount||
    allPriority!==h.reboundContextReview.crossSourceReviewCount)
  throw Error('巻き返し集計と馬番が不一致');
 // The five-band summary is new; absent in previously saved snapshots.
 // Accept only the previously checked course/going and pace observations.
 if(h.fiveFactorHypotheses!==undefined){
  const five=h.fiveFactorHypotheses,weights={
   training:30,recent:3,course_distance:20,pace:20,ground:12};
  if(!five||five.version!=='owner-five-factor-hypotheses-1'||
     five.policyVersion!=='research-5'||five.raceCount!==historyCoordinates.size||
     five.researchOnly!==true||five.privateOwnerOnly!==true||
     five.hypothesisBandsNotVerifiedGrades!==true||
     five.materialCoverageDoesNotMeanPrediction!==true||
     five.officialJraVerified!==false||five.overallPredictionReady!==false||
     five.verifiedFactorCount!==0||five.bettingReady!==false||
     five.autoPurchase!==false||!Array.isArray(five.races)||
     five.races.length!==historyCoordinates.size||
     !Array.isArray(five.factors)||five.factors.length!==5||
     five.factors.some((f,i)=>f?.key!==Object.keys(weights)[i]||
      f.weight!==weights[f.key]))
   throw Error('5項目研究資料の形式不正');
  const seenFive=new Set(),validBands=new Set(['S','A','B','C','未評価']);
  for(const race of five.races){
   const id=race?.track+'|'+race?.race,detail=perRace.get(id);
   if(!detail||seenFive.has(id)||race.runnerCount!==detail.runnerCount||
      race.verifiedFactorCount!==0||race.overallReady!==false||
      race.bettingReady!==false||!Array.isArray(race.runners)||
      race.runners.length!==race.runnerCount||!race.bandsPresentByFactor)
    throw Error('5項目研究レースの照合不一致');
   seenFive.add(id);
   const historical=detail.experimental,scenarios=detail.paceByNumber;
   const prior=historyGrades.get(id)||new Map(),count=Object.fromEntries(
    Object.keys(weights).map(k=>[k,0]));
   const seenHorse=new Set();
   for(const horse of race.runners){
    if(!Number.isInteger(horse?.number)||seenHorse.has(horse.number)||
       horse.actualGradesVerified!==0||horse.overallScore!==null||
       horse.overallRank!==null||!horse.bands||
       Object.keys(horse.bands).length!==5||
       !horse.explanations||Object.keys(horse.explanations).length!==3||
       !historical.has(horse.number)||!scenarios.has(horse.number))
     throw Error('5項目研究馬番の形式不正');
    seenHorse.add(horse.number);
    const h0=historical.get(horse.number),p0=scenarios.get(horse.number);
    if(horse.bands.course_distance!==h0.courseEvidenceBand||
       horse.bands.ground!==h0.goingEvidenceBand||
       horse.bands.pace!==p0.scenarioFitBand||
       horse.explanations.course_distance!==h0.courseReason||
       horse.explanations.ground!==h0.goingReason||
       horse.explanations.pace!==p0.reason)
     throw Error('5項目研究の元データ不一致');
    const original=prior.get(horse.number);
    if(historyStatuses.get(id)==='provisional_draft'&&
       (!original||horse.bands.training!==original.training||
        horse.bands.recent!==original.recent))
     throw Error('5項目研究の調教・近走不一致');
    for(const key of Object.keys(weights)){
     if(!validBands.has(horse.bands[key]))throw Error('5項目の未確認値');
     count[key]+=Number(horse.bands[key]!=='未評価');
    }
   }
   if(seenHorse.size!==race.runnerCount||
      Object.keys(count).some(k=>count[k]!==race.bandsPresentByFactor[k]))
    throw Error('5項目研究の頭数・資料件数不一致');
   detail.fiveFactor=race;
  }
  if(seenFive.size!==historyCoordinates.size)
   throw Error('5項目研究レース不足');
 }
 // The new ten-factor inventory is optional for old saved snapshots.
 // It only describes where fields exist; ZERO factors are fully assessed.
 if(h.tenFactorSourceInventory!==undefined){
  const inv=h.tenFactorSourceInventory,expected=new Map(
   TEN.map(([key,,weight])=>[key,weight]));
  if(!h.fiveFactorHypotheses||!inv||
     inv.version!=='owner-ten-factor-source-inventory-1'||
     inv.policyVersion!=='research-5'||
     inv.raceCount!==historyCoordinates.size||
     inv.factorCount!==10||inv.totalWeight!==100||
     inv.verifiedGrades!==0||inv.researchOnly!==true||
     inv.privateOwnerOnly!==true||
     inv.independentJraVerified!==false||
     inv.overallPredictionReady!==false||
     inv.bettingReady!==false||inv.autoPurchase!==false||
     !inv.factorWeights||Object.keys(inv.factorWeights).length!==10||
     [...expected].some(([key,weight])=>inv.factorWeights[key]!==weight)||
     !Array.isArray(inv.races)||inv.races.length!==historyCoordinates.size)
    throw Error('10項目の資料一覧の形式不正');
  const allowed=new Set(['complete_fields_observed',
   'partial_fields_observed','no_fields_observed']);
  const intervals=new Set(['under14Days','days14to55','days56plus','unknown']);
  const remaining=['pedigree','draw_weight','jockey_stable',
   'rotation','body_condition'];
  const seenRaces=new Set();
  for(const race of inv.races){
   const id=race?.track+'|'+race?.race,detail=perRace.get(id);
   if(!detail?.fiveFactor||seenRaces.has(id)||
      race.runnerCount!==detail.runnerCount||
      race.verifiedGrades!==0||race.overallReady!==false||
      race.independentJraVerified!==false||race.bettingReady!==false||
      !Array.isArray(race.runners)||race.runners.length!==race.runnerCount||
      !race.remainingFieldCoverage||
      Object.keys(race.remainingFieldCoverage).length!==5)
    throw Error('10項目の資料とレースが不一致');
   seenRaces.add(id);
   const five=new Map(detail.fiveFactor.runners.map(h=>[h.number,h]));
   const sourceSeen=new Set(),totals=Object.fromEntries(remaining.map(k=>[k,0]));
   for(const horse of race.runners){
    if(!Number.isInteger(horse?.number)||sourceSeen.has(horse.number)||
       !five.has(horse.number)||horse.verifiedGrades!==0||
       horse.overallScore!==null||horse.overallRank!==null||
       typeof horse.bodyShapeCodePresent!=='boolean'||
       !horse.provisionalBands||
       Object.keys(horse.provisionalBands).length!==5||
       !horse.sourceStates||Object.keys(horse.sourceStates).length!==5)
     throw Error('10項目の馬番・採点状態が不正');
    sourceSeen.add(horse.number);
    if(['training','recent','course_distance','pace','ground'].some(k=>
       horse.provisionalBands[k]!==five.get(horse.number).bands[k]))
     throw Error('10項目の暫定ランクと資料が不一致');
    if(['pedigree','draw_weight','jockey_stable'].some(k=>
        !allowed.has(horse.sourceStates[k]))||
       !intervals.has(horse.sourceStates.rotation)||
       horse.sourceStates.body_condition!=='race_day_bodyweight_unavailable')
     throw Error('未評価の資料状態に不正な値');
    for(const k of remaining){
     totals[k]+=Number(k==='body_condition'?false:
      k==='rotation'?horse.sourceStates[k]!=='unknown':
      horse.sourceStates[k]==='complete_fields_observed');
    }
   }
   if(sourceSeen.size!==race.runnerCount||
      remaining.some(k=>totals[k]!==race.remainingFieldCoverage[k]))
    throw Error('10項目の頭数・資料集計不一致');
   detail.tenInventory=race;
  }
  if(seenRaces.size!==historyCoordinates.size)
   throw Error('10項目のレース不足');
 }
 validateWatchCapture(h.watchCapture,h);
 return results;
}
function jstToday(){return new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});}
$('autoDay').value=jstToday();
function updateReviewLink(){
 const day=$('autoDay').value;
 const valid=/^20\d{2}-\d{2}-\d{2}$/.test(day)&&
  !Number.isNaN(new Date(day+'T12:00:00Z').valueOf())&&
  new Date(day+'T12:00:00Z').toISOString().slice(0,10)===day;
 $('autoReviewLink').href='/owner-100yen-review'+
  (valid?'?date='+encodeURIComponent(day):'');
}
$('autoDay').onchange=()=>{
 // Preserve an explicitly selected day across subsequent app resumes.
 followingToday=false;
 // Invalidate the old response and unlock the button. A slow old request
 // must not leave the new day permanently disabled on iPhone.
 request++;$('autoRun').disabled=false;
 updateReviewLink();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 clearHistory();
 $('autoSummary').textContent='未取得';
 $('autoSourceSummary').textContent='全Rの資料進捗は未取得です。';
 $('autoTenWeights').replaceChildren();
 $('autoTenStatus').textContent='10項目の評価を取得していません。';
 $('autoSavedStatus').textContent=localReceiptStatus(
  $('autoDay').value.replaceAll('-',''));
 showFixedHistory($('autoDay').value.replaceAll('-',''));
 $('autoStatus').textContent='開催日を選んでな。';
};
// One explicit, owner-authenticated /tra request. No background probe.
$('autoConnectionCheck').onclick=async()=>{
 const button=$('autoConnectionCheck'),selected=$('autoDay').value;
 if(button.disabled)return;
 if(!/^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/.test(selected)||
    Number.isNaN(new Date(selected+'T12:00:00Z').valueOf())||
    new Date(selected+'T12:00:00Z').toISOString().slice(0,10)!==selected){
  $('autoConnectionStatus').textContent='開催日を正しく選択してください。';
  return;
 }
 const seq=++connectionSeq,day=selected.replaceAll('-','');
 button.disabled=true;
 $('autoConnectionStatus').textContent='接続設定を確認中…';
 try{
  const res=await fetch('/api/setup',{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(seq!==connectionSeq||selected!==$('autoDay').value)return;
  if(!res.ok)throw Error('setup');
  const cfg=await res.json();
  if(seq!==connectionSeq||selected!==$('autoDay').value)return;
  if(!cfg||typeof cfg.jrdbConfigured!=='boolean'||
     cfg.liveConnectionVerified!==false||
     cfg.realPredictionEnabled!==false||
     typeof cfg.prestartBodyEnabled!=='boolean')
   throw Error('setup_contract');
  if(!cfg.jrdbConfigured){
   $('autoConnectionStatus').textContent=
    'JRDB接続設定が未完了です。RenderのAPIキー・利用設定を確認。番組APIは呼び出していません。';
   return;
  }
  $('autoConnectionStatus').textContent='JRDB番組APIへ1回接続中…';
  const test=await fetch('/api/jrdb/connection-test?date='+encodeURIComponent(day),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const value=await test.json();
  if(seq!==connectionSeq||selected!==$('autoDay').value)return;
  if(!test.ok||!value||value.date!==day||
     value.connectionVerified!==true||value.predictionReady!==false||
     value.providerDataStored!==false||
     !Number.isInteger(value.programmeCount)||value.programmeCount<0||
     value.programmeCount>120)
   throw Error('probe');
  $('autoConnectionStatus').textContent=
   'JRDB番組APIに接続成功：'+value.programmeCount+'R分。'+
   (value.programmeCount===0
    ?'開催レース0件。実際の出走馬データは未確認。'
    :'番組形式を受信できました。')+
   ' 10項目の本採点・JRA公式照合は別途必要。';
 }catch(_){if(seq===connectionSeq){
  $('autoConnectionStatus').textContent=
   '接続確認ができません。日付・JRDB利用権限・本人用設定を確認してください。保存済み記録は無変更です。';
 }}finally{if(seq===connectionSeq)button.disabled=false;}
};
$('autoRun').onclick=async()=>{
 const button=$('autoRun');
 if(button.disabled)return;
 const seq=++request,day=$('autoDay').value.replaceAll('-','');
 if(!/^20[0-9]{6}$/.test(day)){
  $('autoStatus').textContent='開催日を選択してください。';return;
 }
 button.disabled=true;$('autoStatus').textContent='JRDB資料を一括照合し、自動暫定案を作成中…';
 clearHistory();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 try{
  const result=await fetch('/api/jrdb/owner-auto-draft?date='+encodeURIComponent(day),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const body=await result.json();
  if(!result.ok){
   const step=Object.hasOwn(FAILURE_STAGE,body.failureStage)
     ?FAILURE_STAGE[body.failureStage]:null;
   const kind=Object.hasOwn(FAILURE_KIND,body.failureKind)
     ?FAILURE_KIND[body.failureKind]:'未確認';
   const detail=Object.hasOwn(FAILURE_DETAIL,body.failureDetail)
     ?'／条件：'+FAILURE_DETAIL[body.failureDetail]:'';
   throw Error(step?'停止した工程：'+step+'（'+kind+detail+'）。未完成の買い目は表示しません。'
     :'JRDB接続・出走資料・認証状態を確認してください。');
  }
  if(seq!==request)return;
  render(body,day);
  historyDay=day;
  historyCoordinates=new Set(body.races.map(r=>r.track+'|'+r.race));
  historyRosters=new Map(body.races.map(r=>[
   r.track+'|'+r.race,new Set(r.runners.map(h=>h.number))
  ]));
  historyReboundWatch=new Map(body.tenFactorPreview.races.map(r=>[
   r.track+'|'+r.race,new Set(r.trainingLedRecheckNumbers)
  ]));
  historyStyles=new Map(body.races.map(r=>[
   r.track+'|'+r.race,new Map(r.runners.map(h=>[h.number,h.pastFourthCorner]))
  ]));
  historyGrades=new Map(body.races.map(r=>[
   r.track+'|'+r.race,new Map(r.runners.map(h=>[
    h.number,{training:h.training,recent:h.recent}
   ]))
  ]));
  historyStatuses=new Map(body.races.map(r=>[r.track+'|'+r.race,r.status]));
  $('autoHistoryAudit').disabled=historyCoordinates.size===0;
  $('autoHistoryAuditStatus').textContent=historyCoordinates.size
   ?'必要なときに過去の同条件資料を確認できます。':'この開催日のレースはありません。';
  try{
   const localStatus=saveAutoReceipts(body,day);
   $('autoSavedStatus').textContent=body.archiveEnabled
    ?'サーバー固定済み '+body.archiveRecordCount+'R／前の買い目を優先したレース '+
      body.archiveConflictCount+'R。'+localStatus
    :'サーバー保存は未設定。'+localStatus;
   showFixedHistory(day);
  }catch(_){
   $('autoSavedStatus').textContent='研究記録の端末保存はできませんでした。結果表示と実購入記録には影響しません。';
  }
  $('autoStatus').textContent='暫定評価を自動生成しました。作成できないレースは無理に選定していません。';
 }catch(error){if(seq===request){
  const detail=error&&typeof error.message==='string'&&
   error.message.startsWith('停止した工程：')?error.message:null;
  $('autoStatus').textContent=detail||
   '安全な自動生成ができません。JRDB接続・出走資料・認証状態を確認してください。';
  $('autoSummary').textContent='予想は未作成';
  $('autoSourceSummary').textContent='資料進捗の取得に失敗しました。以前の集計は表示しません。';
  $('autoTenWeights').replaceChildren();
  $('autoTenStatus').textContent='10項目の評価を確認できません。';}}
 finally{if(seq===request)button.disabled=false;}
};
// The existing signed-receipt verifier does NOT contact JRDB, settle
// racing results, create receipts, write a server archive or purchase bets.
$('autoReceiptVerify').onclick=async()=>{
 const button=$('autoReceiptVerify');
 if(button.disabled)return;
 const day=$('autoDay').value.replaceAll('-','');
 const seq=++receiptVerifySeq;
 button.disabled=true;
 $('autoReceiptVerifyStatus').textContent='端末内記録を確認中…';
 try{
  const signed=selectedReceiptsForVerification(day);
  if(seq!==receiptVerifySeq)return;
  if(!signed.length){
   $('autoReceiptVerifyStatus').textContent=
    'この日の固定済み研究記録はありません。発走後に買い目は作成しません。';
   return;
  }
  const formatted=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
  const payload=JSON.stringify({date:formatted,receipts:signed});
  if(payload.length>60000)throw Error('request_too_large');
  $('autoReceiptVerifyStatus').textContent='本人専用サーバーで署名を検証中…';
  const resp=await fetch('/api/owner-100yen-verify-receipts',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body:payload
  });
  const result=await resp.json();
  if(seq!==receiptVerifySeq||day!==$('autoDay').value.replaceAll('-'))return;
  if(!resp.ok||result?.available!==true||result.serverSigned!==true||
     result.captureAuditVerified!==false||
     result.officialScheduleVerified!==false||
     result.officialFeedConnected!==false||
     result.review?.version!=='keiba-100yen-review-1'||
     result.review.actualPurchase!==false||
     result.review.unitYen!==100||
     result.review.reviewedRaces!==0||
     result.review.pendingRaces!==signed.length||
     result.review.totalInvestedYen!==0||
     result.review.totalReturnedYen!==0||
     result.review.roiPercent!==null||
     !Array.isArray(result.review.races)||
     result.review.races.length!==signed.length||
     result.review.races.some(r=>r.status!=='pending'))
   throw Error('unverified');
  $('autoReceiptVerifyStatus').textContent=
   'サーバー署名の照合成功：'+signed.length+
   'R。すべて結果未確認の研究記録。JRA公式時刻・結果・実購入・サーバー保存は未検証。'+
   '元の買い目と仮想収支は変更していません。';
 }catch(_){if(seq===receiptVerifySeq){
  $('autoReceiptVerifyStatus').textContent=
   '署名を確認できませんでした。保存済みの記録は消さず、バックアップと接続設定を確認してください。';
 }}finally{if(seq===receiptVerifySeq)button.disabled=false;}
};
$('autoHistoryAudit').onclick=async()=>{
 const button=$('autoHistoryAudit'),day=historyDay;
 if(button.disabled||!day||day!==$('autoDay').value.replaceAll('-',''))return;
 button.disabled=true;const seq=++historySeq;
 $('autoHistoryAuditStatus').textContent='過去の同条件を照合中…';
 $('autoHistoryAuditRaces').replaceChildren();
 try{
  const res=await fetch('/api/jrdb/history',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},
   body:JSON.stringify({date:day,limit:8})
  });
  const raw=await res.json();
  if(seq!==historySeq)return;
  if(!res.ok)throw Error('履歴機能は利用不可');
  const rows=validateHistory(raw);
  // The server checks signatures, not just browser-provided timestamps.
  // Never send an outcome or an officialVerified flag from the device.
  let watchSaveStatus='発走前の署名付き候補はまだ固定できていません。';
  if(raw.watchCapture.receiptCount){
   try{
    const verified=await fetch('/api/owner-rebound-verify',{
     method:'POST',credentials:'same-origin',cache:'no-store',
     headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
      'Accept':'application/json'},
     body:JSON.stringify({date:day,receipts:raw.watchCapture.receipts})
    });
    const output=await verified.json();
    if(seq!==historySeq)return;
    if(!verified.ok||output.serverSigned!==true||
       output.jraScheduleVerified!==false||
       output.officialFeedConnected!==false||!output.review||
       output.review.reviewedRaces!==0||
       output.review.pendingRaces!==raw.watchCapture.receiptCount||
       output.review.outcomeCalibrationReady!==false)
     throw Error('署名の確認ができません');
    watchSaveStatus=saveReboundWatch(raw.watchCapture.receipts);
    refreshWatchResultsAvailability();
   }catch(_){
    watchSaveStatus='候補の署名検証・端末固定ができませんでした。過去の記録は変更していません。';
   }
  }else{
   watchSaveStatus=saveReboundWatch([]);
  }
  $('autoHistoryWatchSave').textContent=watchSaveStatus;
  for(const row of rows){
   const card=dom('div',undefined,'history-coverage');
   card.append(dom('strong',row.track+' '+row.race+'R'),
    dom('p','芝・ダートと近い距離の過去出走：'+
      row.runnersWithComparableCourse+'/'+row.runnerCount+'頭'),
    dom('p','馬場を確認できた過去出走：'+row.runnersWithKnownGoingComparable+
      '頭／今回と同じ馬場での出走歴：'+row.runnersMatchingCurrentGoing+
      '頭／重・不良の出走歴：'+row.runnersWithWetComparable+'頭'),
    dom('p','履歴不足：'+row.runnersWithIncompleteHistory+
      '頭。適性・10項目総合点は未評価。'));
   const details=row.ownerRunnerDetails,pace=details.paceScenario;
   if(details.rosterVerified&&details.fiveFactor){
    const five=dom('details');
    five.append(dom('summary','馬番別5項目の研究目安を見る（正式採点0/10）'));
    five.append(dom('p','調教30・近走3は暫定ランク。距離20・展開20・馬場12は過去観測の仮説。買い目は変更しません。','muted'));
    for(const horse of details.fiveFactor.runners){
     const b=horse.bands;
     five.append(dom('p',horse.number+'番｜調教 '+b.training+
      '／近走 '+b.recent+'／距離 '+b.course_distance+
      '／展開 '+b.pace+'／馬場 '+b.ground+
      '（研究用・総合点なし）','muted'));
    }
    card.append(five);
   }
   if(details.rosterVerified&&details.tenInventory){
    const ten=dom('details');
    ten.append(dom('summary','10項目の資料状況（残り5項目・正式採点0/10）'));
    ten.append(dom('p','血統・枠斤量・騎手厩舎・ローテは資料があるかの確認のみ。馬体形状コードは当日の馬体重ではありません。総合点・馬券は未確定。','muted'));
    const names={
     complete_fields_observed:'資料あり',
     partial_fields_observed:'一部あり',
     no_fields_observed:'資料不足',
     under14Days:'中13日以内',days14to55:'中14〜55日',
     days56plus:'中56日以上',unknown:'間隔不明',
     race_day_bodyweight_unavailable:'当日馬体重未取得'
    };
    for(const horse of details.tenInventory.runners){
     const v=horse.sourceStates;
     ten.append(dom('p',horse.number+'番｜血統 '+names[v.pedigree]+
      '／枠斤量 '+names[v.draw_weight]+
      '／騎手厩舎 '+names[v.jockey_stable]+
      '／ローテ '+names[v.rotation]+
      '／馬体重 '+names[v.body_condition]+'（評価未実施）','muted'));
    }
    card.append(ten);
   }
   const pressureLabel={
    coverage_insufficient:'位置取りの資料不足',
    no_front_observed:'明確な先行候補を確認できず',
    single_front_observed:'先行候補1頭（単独の可能性）',
    two_front_observed:'先行候補2頭（競合の可能性）',
    multiple_front_observed:'先行候補3頭以上（先行争いの可能性）'
   };
   card.append(dom('p','過去4角の観測：前方 '+pace.frontObserved+
    '頭／後方 '+pace.backObserved+'頭／混在 '+pace.mixedObserved+
    '頭／資料不足 '+pace.insufficient+'頭。展開仮説：'+
    pressureLabel[pace.pacePressureScenario]+'（実際のペース未予測）','muted'));
   const watch=details.reboundReview||[];
   if(details.rosterVerified&&watch.length){
    const review=dom('details');
    review.append(dom('summary','調教が良い巻き返し再審査：'+watch.length+
     '頭（重点確認 '+details.reboundPriorityCount+'頭）'));
    const states={
     cross_source_review:'重点再審査：展開＋同条件の材料あり',
     overlapping_history_only:'同一過去走に基づく材料のみ：展開確認待ち',
     need_more_evidence:'根拠不足：追加資料の確認待ち'
    };
    for(const horse of watch){
     review.append(dom('p',horse.number+'番｜調教 '+horse.trainingProvisional+
      '・近走 '+horse.recentProvisional+
      '／コース '+horse.courseEvidenceBand+
      '・展開 '+horse.paceScenarioBand+
      '・馬場 '+horse.goingEvidenceBand+
      '｜'+states[horse.reviewState]+
      '（研究用。1着候補の自動追加・買い目変更なし）','muted'));
    }
    card.append(review);
   }
   if(details.rosterVerified){
    const panel=dom('details');
    panel.append(dom('summary','馬番ごとの同条件実績を見る（参考資料）'));
    const watch=historyReboundWatch.get(row.track+'|'+row.race)||new Set();
    for(const h of details.runners){
     const line=dom('p',h.number+'番｜同条件 '+h.comparableRuns+
       '走（3着以内 '+h.comparableTopThreeRuns+'回）／同じ馬場 '+
       h.matchingCurrentGoingRuns+'走（3着以内 '+
       h.matchingCurrentGoingTopThreeRuns+'回）／重・不良 '+h.wetGoingRuns+
       '走（3着以内 '+h.wetTopThreeRuns+'回）'+
       (watch.has(h.number)?'｜調教好調・近走低評価の巻き返し再審査対象':'')+
       '。コース好走実績の研究目安 '+details.experimental.get(h.number).courseEvidenceBand+
       '／今回馬場の研究目安 '+details.experimental.get(h.number).goingEvidenceBand+
       '／展開シナリオの研究目安 '+
       details.paceByNumber.get(h.number).scenarioFitBand+
       '（過去4角の仮説・実際の展開は未予測、総合点と買い目には不反映）。','muted');
     panel.append(line);
    }
    card.append(panel);
   }else{
    card.append(dom('p','馬番を照合できないため個別の観測数は非表示。','muted'));
   }
   $('autoHistoryAuditRaces').append(card);
  }
  $('autoHistoryAuditStatus').textContent='過去番組の追加照合 '+raw.draCalls+
   '回／馬場 '+raw.dkaCalls+'回。未取得の過去レース '+raw.deferredPastRaces+
   '件。'+(raw.historyComplete?'指定範囲を照合済み。':'履歴に未確認あり。')+
   ' 予想・購入・保存済みの買い目は変更しません。';
 }catch(_){if(seq===historySeq){
  $('autoHistoryAuditRaces').replaceChildren();
  $('autoHistoryAuditStatus').textContent=
   '過去資料の照合ができません。履歴機能の設定・資料形式を確認してください。'+
   '予想と固定済みの買い目は変更していません。';
 }}finally{if(seq===historySeq&&day===historyDay)button.disabled=false;}
};
// Never use source count alone to grade body condition or change a ticket.
function validatePrestartBody(raw,day){
 if(!raw||raw.version!=='private-prestart-body-1'||raw.date!==day||
    !Number.isInteger(raw.raceCount)||raw.raceCount<0||raw.raceCount>120||
    !Array.isArray(raw.races)||raw.races.length!==raw.raceCount||
    raw.rawHorseRecordsIncluded!==false||raw.oddsUsed!==false||
    raw.officialBodyWeightVerified!==false||raw.bodyConditionGraded!==false||
    raw.realPredictionReady!==false||raw.purchaseReady!==false||
    !Array.isArray(raw.sourceRequestsRequired)||
    raw.sourceRequestsRequired.join('|')!=='tra|tky|tpd'||
    !raw.summary)throw Error('直前馬体資料の形式不正');
 const countKeys=['registered','prestartRowsMatched','prestartRowsMissing',
  'bodyWeightRecords','weightChangeRecords','paddockRecords',
  'bodyStateCodeRecords','providerWithdrawnReports'];
 const totals={matchedRows:0,weightRecords:0,paddockRecords:0,missingRows:0};
 const seen=new Set();
 for(const row of raw.races){
  const id=row?.track+'|'+row?.race;
  if(!row||typeof row.track!=='string'||!row.track||
     !Number.isInteger(row.race)||row.race<1||row.race>12||
     seen.has(id)||countKeys.some(k=>!Number.isInteger(row[k])||
      row[k]<0||row[k]>18)||
     row.registered!==row.prestartRowsMatched+row.prestartRowsMissing||
     ['bodyWeightRecords','weightChangeRecords','paddockRecords',
      'bodyStateCodeRecords','providerWithdrawnReports'].some(k=>
       row[k]>row.prestartRowsMatched)||
     row.weightChangeRecords>row.bodyWeightRecords||
     row.sourceDataUpdatedAtVerified!==false||
     row.officialBodyWeightVerified!==false||
     row.bodyConditionGraded!==false||
     row.realPredictionReady!==false||row.ticketReady!==false)
   throw Error('直前馬体資料の頭数不一致');
  seen.add(id);
  totals.matchedRows+=row.prestartRowsMatched;
  totals.weightRecords+=row.bodyWeightRecords;
  totals.paddockRecords+=row.paddockRecords;
  totals.missingRows+=row.prestartRowsMissing;
 }
 if(Object.keys(totals).some(k=>raw.summary[k]!==totals[k]))
  throw Error('直前馬体資料の集計不一致');
 return raw.races;
}
$('autoPrestartBody').onclick=async()=>{
 const button=$('autoPrestartBody');
 if(button.disabled)return;
 const day=$('autoDay').value.replaceAll('-','');
 // The private server, not the device clock, enforces Japan's current date
 // before any JRDB paid request. The client only rejects invalid input shape.
 if(!/^20[0-9]{6}$/.test(day)){
  $('autoPrestartStatus').textContent='開催日を選択してください。';
  return;
 }
 const seq=++prestartSeq;
 button.disabled=true;$('autoPrestartRaces').replaceChildren();
 $('autoPrestartStatus').textContent='当日の馬体資料を照合中…';
 try{
  const r=await fetch('/api/jrdb/prestart-body?date='+encodeURIComponent(day),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const raw=await r.json();
  if(seq!==prestartSeq||$('autoDay').value.replaceAll('-','')!==day)return;
  if(!r.ok)throw Error('直前資料が利用不可');
  const rows=validatePrestartBody(raw,day);
  for(const row of rows){
   const card=dom('div',undefined,'history-coverage');
   card.append(dom('strong',row.track+' '+row.race+'R'),
    dom('p','馬体重 '+row.bodyWeightRecords+'/'+row.registered+
     '頭／前走比 '+row.weightChangeRecords+'頭／未照合 '+
     row.prestartRowsMissing+'頭（JRA公式未確認・採点なし）','muted'));
   $('autoPrestartRaces').append(card);
  }
  $('autoPrestartStatus').textContent='直前資料 '+raw.summary.matchedRows+
   '頭照合／馬体重記録 '+raw.summary.weightRecords+
   '頭。総合点・保存済み3連単・仮想収支は変更しません。';
 }catch(_){if(seq===prestartSeq){
  $('autoPrestartRaces').replaceChildren();
  $('autoPrestartStatus').textContent=
   '直前資料を照合できません。本人用の設定・接続を確認。既存記録は無変更です。';
 }}finally{if(seq===prestartSeq)button.disabled=false;}
};
$('autoWatchResultCheck').onclick=async()=>{
 const button=$('autoWatchResultCheck'),seq=++watchResultSeq,
  day=$('autoDay').value.replaceAll('-','');
 if(button.disabled)return;
 button.disabled=true;
 $('autoWatchResultRaces').replaceChildren();
 $('autoWatchResultStatus').textContent='JRDB成績を参考照合中…';
 try{
  const selected=storedWatchDay(day);
  if(!selected.length)throw Error('候補記録なし');
  const res=await fetch('/api/owner-rebound-provider-check',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},
   body:JSON.stringify({date:day,receipts:selected})
  });
  const raw=await res.json();
  if(seq!==watchResultSeq)return;
  if(!res.ok)throw Error('JRDB成績照合不可');
  const result=validateProviderCheck(raw,selected,day);
  for(const r of result.races){
   const card=dom('div',undefined,'history-coverage');
   card.append(dom('strong',r.track+' '+r.race+'R'));
   const label=r.providerStatus==='pending'
    ?'資料不足・発走前・成績未反映のいずれか。結果待ち。'
    :'JRDBが示す1着馬番 '+r.observedFirstNumber+'番。'+
     (r.observedFirstInWatch
      ?'発走前の注目候補に含まれる。'
      :'発走前の注目候補には含まれない。')+
     (r.observedFirstInPriorityWatch?'重点再審査対象にも含まれる。':'')+
     '（参考照合・JRA公式未確認）';
   card.append(dom('p',label,'muted'));
   $('autoWatchResultRaces').append(card);
  }
  $('autoWatchResultStatus').textContent=
   'JRDB成績の1着馬番を確認できた '+result.observedRaceCount+'R／'+
   result.raceCount+'R、候補に含まれた '+result.observedFirstInWatchCount+
   'R（重点再審査 '+result.observedFirstInPriorityCount+
   'R）。JRA公式照合が未完了のため、正式な的中・回収率には算入しません。'+
   'サーバー結果は端末の固定候補を変更しません。';
 }catch(_){if(seq===watchResultSeq){
  $('autoWatchResultRaces').replaceChildren();
  $('autoWatchResultStatus').textContent=
   '結果の暫定照合ができませんでした。JRDB接続・署名・通信状況を確認。'+
   '公式成績や保存済み候補は変更していません。';
 }}finally{
  if(seq===watchResultSeq)
   refreshWatchResultsAvailability(true);
 }
};
refreshWatchResultsAvailability();
$('autoSavedStatus').textContent=localReceiptStatus(
 $('autoDay').value.replaceAll('-',''));
showFixedHistory($('autoDay').value.replaceAll('-',''));
updateReviewLink();
// If the iPhone PWA stays open over midnight, the next foreground visit
// automatically selects the NEW JST calendar day and triggers once.
// Never poll in background. Never override a user-selected historical date.
function resumeOwnerDay(){
 if(document.visibilityState==='hidden'||!followingToday)return;
 const today=jstToday();
 if(today===$('autoDay').value)return;
 request++;$('autoRun').disabled=false;
 $('autoDay').value=today;
 updateReviewLink();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 clearHistory();
 $('autoSummary').textContent='未取得';
 $('autoSourceSummary').textContent='全Rの資料進捗は未取得です。';
 $('autoTenWeights').replaceChildren();
 $('autoTenStatus').textContent='10項目の評価を取得していません。';
 $('autoSavedStatus').textContent=localReceiptStatus(today.replaceAll('-',''));
 showFixedHistory(today.replaceAll('-',''));
 $('autoStatus').textContent='新しい開催日の研究用自動案を確認します。';
 $('autoRun').onclick();
}
if(typeof document.addEventListener==='function')
 document.addEventListener('visibilitychange',resumeOwnerDay);
if(typeof window!=='undefined'&&typeof window.addEventListener==='function')
 window.addEventListener('pageshow',event=>{if(event.persisted)resumeOwnerDay();});
// Opening the authenticated owner page triggers the initial day once.
// No timers, background provider polling, or auto-purchase.
if(document.visibilityState!=='hidden')$('autoRun').onclick();
})();"""
