"""Owner private iPhone view for automatic JRDB two-factor provisional draft."""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>ARC RACE｜本人用・研究予想</title>
<link rel="stylesheet" href="/owner-auto-forecast.css?theme=arc-blue-20261124-race-nav"></head><body class="owner-simple owner-preday-view"><main>
<details class="owner-menu"><summary>関連ページ・WIN5</summary><nav class="owner-nav">
<a href="https://esakahumihumi1125-byte.github.io/keiba-nine/keiba-nine-beta51-feed-record.html" rel="noopener noreferrer">← KEIBA NINE本体へ</a>
<a href="/">本人用ホーム</a>
<a href="/owner-jrdb-day-research">2項目の根拠</a>
<a href="https://esakahumihumi1125-byte.github.io/keiba-nine/keiba-nine-beta51-feed-record.html#win5" rel="noopener noreferrer">WIN5（別画面）</a>
</nav></details>
<header class="arc-brand" aria-label="ARC RACE アークレース">
<svg class="arc-brand-mark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 144 100" role="img" aria-label="円弧と競走馬の横顔">
<defs><linearGradient id="arc-brand-gold" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="#fff1bc"/><stop offset=".48" stop-color="#d8ac55"/><stop offset="1" stop-color="#99702d"/></linearGradient></defs>
<path d="M9 83 C26 25 69 7 113 18" fill="none" stroke="url(#arc-brand-gold)" stroke-width="5" stroke-linecap="round"/>
<path d="M17 88 C40 46 72 28 116 32" fill="none" stroke="#3d97ce" stroke-width="3.5" stroke-linecap="round"/>
<path d="M75 54 Q90 49 100 37 L108 23 L114 34 L124 27 L127 47 L139 58 Q143 64 136 72 L123 76 Q117 76 111 70 L100 68 Q94 77 93 90" fill="#0a192b" stroke="url(#arc-brand-gold)" stroke-width="3.8" stroke-linejoin="round" stroke-linecap="round"/>
<path d="M100 37 Q83 37 65 49 Q78 48 90 44 M94 43 Q77 46 57 61 Q78 59 88 53" fill="url(#arc-brand-gold)"/>
<circle cx="126" cy="57" r="2" fill="#fff0b5"/>
</svg>
<div class="arc-brand-copy"><h1>ARC RACE</h1><p class="arc-brand-jp">アークレース</p><p class="arc-brand-sub">AI競馬予想・データ分析</p><p class="arc-brand-engine">Powered by <strong>UMETRIC</strong></p></div>
</header>
<p class="arc-legacy-context">本人用・研究予想（従来のKEIBA NINEと保存記録・接続先は共通）</p>
<nav class="arc-main-tabs" aria-label="アークレースの主な画面">
<a href="#autoDailyStart">予想を取得</a>
<a href="#forecastRacesSection">レース一覧</a>
<a href="#fixedHistorySection">結果・記録</a>
<a id="autoQualityLink" href="/owner-100yen-review">精度検証</a>
</nav>
<nav class="owner-view-switch" aria-label="予想の表示を切り替える">
<button id="ownerPredayMode" type="button" aria-pressed="true">前日参考予想</button>
<button id="ownerJrdbMode" type="button" aria-pressed="false">JRDB研究予想</button>
<button id="ownerDetailToggle" type="button" aria-pressed="false">詳しい設定</button>
</nav>
<p class="warning"><strong>現在は研究用の暫定予想です。</strong>調教・近走の2項目で3連単を試算しています。
正式10項目の予想とJRA公式照合は未完成。自動購入はしません。</p>
<section class="daily-start" id="autoDailyStart">
<h2>1. 予想を見る</h2>
<label for="autoDay">開催日</label><input id="autoDay" type="date">
<div class="owner-weekend-actions">
<button id="autoSaturdayQuick" class="primary-cta" type="button">土曜の予想を取得・表示（1回）</button>
<button id="autoSundayQuick" class="secondary-cta" type="button">日曜の予想を取得・表示（1回）</button>
<button id="autoMondayQuick" class="secondary-cta" type="button" hidden disabled>開催月曜の予想を取得・表示（1回）</button>
</div>
<button id="autoRun" class="secondary-cta" type="button">全場・全Rを再分析する</button>
<details class="owner-instructions"><summary>取得方法・通信設定の説明</summary>
<p class="muted">土日の1タップ取得は直前の木曜以降。JRA公表済みの月曜開催（祝日・再編競馬）は金曜以降に1タップ取得できます。取得済みデータは開いている画面で再利用します。また、発走前固定済みの研究記録がある日は20分以内の再訪問でその履歴を表示し、再照会を控えます。新しい配信資料を見たい場合は「全場・全Rを再分析する」を押してください。JRDBのAPI照会には契約に応じた料金・制限があります。</p>
<details><summary>日付だけを切り替える（追加照会なし）</summary>
<div class="day-shortcuts" role="group" aria-label="週末の開催日を選ぶ">
<button id="autoSaturday" type="button">次の土曜日を選ぶ</button>
<button id="autoSunday" type="button">次の日曜日を選ぶ</button>
<button id="autoMonday" type="button" hidden disabled>次の開催月曜日を選ぶ</button>
</div>
<p class="muted">日付を選ぶボタンは追加のJRDB照会をしません。開催月曜ボタンはJRA公表済みの対象日だけ表示します。その他の変則開催は開催日入力で選べます。</p></details>
<details><summary>土曜の無料・設定事前診断（任意）</summary>
<p class="muted">本人専用サービスの設定・選択日・サーバーの日本時間をチェック。JRDB・JRA・買い目APIは呼ばず、設定された秘密情報も表示しません。設定が揃っていてもJRDB実接続と10項目予想は未検証です。</p>
<button id="autoPreflight" type="button">選択日の無料事前診断</button>
<p id="autoPreflightStatus" class="muted" role="status">事前診断は未実行。レースデータや購入記録は変更しません。</p>
</details>

<details><summary>JRDB実接続の確認（任意）</summary>
<p class="muted">本人が押した時だけ設定を確認し、設定済みなら番組APIへ1回接続。未設定ならJRDBへの追加通信なし。買い目・収支・購入記録は変更しません。</p>
<button id="autoConnectionCheck" type="button">選択日のJRDB接続を確認</button>
<p id="autoConnectionStatus" class="muted" role="status">診断は未実行。</p>
</details>
<p class="muted">通常の土日とJRA公表済みの2026年開催月曜（祝日・再編競馬）には、本人用画面を開いた時だけ当日分を一度取得。その他の平日・変則開催は日付を選んで手動取得。
番組0Rを取得した後は、同じ端末で30分以内に画面を開き直しても自動照会を控えます（0Rは開催なしを意味しません）。配信更新後に取り直す場合は「全場・全Rを再分析する」を押してください。
再分析ボタンを押した場合は番組・出走馬・調教・近走を各1回取得し、
馬場情報の追加取得も最大1回だけ試みます。取得できなくても既存の発走前記録は維持します。
バックグラウンド定期取得は未接続。発走済みレースの3連単は後付けで作成しません。</p>
</details>
<p id="autoStatus" class="muted" role="status">開催日を選んで自動作成を押してな。</p>
<p id="autoStoragePulse" class="muted" role="status">サーバーの発走前固定件数：未確認（確認時のJRDB追加照会0回）。iPhoneの端末保存とは別です。</p>
<p id="autoEasyPulse" class="auto-easy-pulse" role="status">開催日を取得すると、予想あり・見送りの件数を表示します。</p>
<div class="owner-readiness-brief" aria-label="見送り内訳と次の操作（新規取得なし）">
<p id="autoHoldBreakdown" class="muted" role="status">見送り理由の内訳はJRDB資料を取得すると表示します。</p>
<p id="autoOperationalNext" class="muted" role="status">開催日の次の操作：当日の取得結果を確認中。</p>
</div>
<a id="autoForecastJump" class="owner-forecast-cta" href="#forecastRacesSection">予想一覧をすぐ見る（追加のJRDB照会なし）</a>
<nav class="quick-links" aria-label="画面内の移動">
<a id="autoDraftShortcut" href="#autoVenues">買い目あり：未取得</a>
<a href="#autoVenues">全レース一覧</a><a href="#fixedHistorySection">固定した買い目</a></nav>
<div class="owner-quick-research">
<p id="autoReferencePulse" class="muted" role="status">見送りレースの参考候補は未取得です。</p>
<button id="autoReferenceOpen" type="button" class="secondary-cta" disabled>資料不足でも確認できる参考候補を見る</button>
<button id="autoWorkoutQuickOpen" type="button" class="secondary-cta" disabled>全場の調教S/Aを確認（未取得）</button>
<p class="muted">「買い目あり」は研究用3連単。「参考候補」は見送りRの署名なし研究例。「調教S/A」は馬番の仮評価だけ。いずれも正式10項目・JRA公式照合・購入ではありません。</p>
</div>
</section>
<section class="owner-preday-recovery" aria-label="別系統の全レース前日参考予想">
<h2>前日参考予想｜競馬場を選ぶ</h2>
<p><strong>全レースの前日参考予想はこちら</strong>：サーバーに登録済みの開催日・全Rについて、1着・2着・3着候補を別画面で表示します。下の「JRDB調教・近走2項目」の研究用下書き件数とは別です。4Rなどの表示は前日参考予想24Rが消えた意味ではありません。</p>
<a class="owner-forecast-cta" id="autoPredayRecovery" href="/owner-preday-forecast">配信済みの前日参考予想をすぐ見る（別画面・追加の有料取得なし）</a>
<button type="button" class="secondary-cta" id="autoPredayInlineLoad">前日参考予想を再確認（無料・追加JRDB照会なし）</button>
<p id="autoPredayInlineStatus" class="muted" role="status">選択開催日の前日参考予想を自動確認中（JRDB有料照会0回）。</p>
<div id="autoPredayInlineRaces" aria-label="前日参考予想のレース一覧"></div>
<p class="muted">参考予想もJRA公式未照合（最終出走・取消・馬場・発走時刻）で、正式10項目採点・購入推奨ではありません。JRDB APIが403で停止するときも、この別経路を利用できます。</p>
</section>
<section id="forecastRacesSection">
<h2>2. 予想を見る・競馬場を選ぶ</h2>
<p class="muted">競馬場を押して、レースと1着・2着・3着を確認（調教・近走の研究用）。</p>
<p id="autoRaceQuickSummary" class="auto-race-quick" role="status">JRDB2項目の研究用下書きは未取得です。前日参考予想は別画面にあります。</p>
<details id="autoCombinedResearchPanel" class="owner-reference-quick" open>
<summary>競馬場別の暫定3連単・参考候補（研究用・未購入）</summary>
<div id="autoCombinedResearchRows" aria-label="全R研究用1着2着3着候補一覧"></div>
<p id="autoCombinedResearchStatus" class="auto-race-quick" role="status">まだ未取得。研究用下書きと署名なし参考例は、混同せず一画面にまとめます。</p>
<button id="autoCombinedResearchExport" type="button" class="secondary-cta" disabled>この日の全R研究一覧をiPhoneに保存（追加照会なし）</button>
<p id="autoCombinedResearchExportStatus" class="muted" role="status">未保存。閲覧用のテキストファイルであり、発走前署名やサーバー永続保存の代わりにはなりません。</p>
<p class="muted">「下書き」はJRDB2項目の署名付き研究案、「参考」は見送りRの署名なし研究例です。どちらも正式10項目・JRA公式の最終出走/取消/馬場/時刻は未照合で、実購入ではありません。参考候補は既存の買い目・固定記録・回収率に追加しません。</p>
<details id="autoCombinedNoPickPanel"><summary id="autoCombinedNoPickTitle">買い目・参考候補を表示しないR：未取得</summary>
<div id="autoCombinedNoPickRows" aria-label="見送りや発走済み等のR"></div>
</details>
</details>
<a class="owner-forecast-cta" href="/owner-preday-forecast">全レースの前日参考予想を見る（追加の有料取得なし）</a>
<details id="autoMultiQuickPanel" class="owner-reference-quick">
<summary id="autoMultiQuickTitle">調教・距離・展開など複数項目の参考：未取得</summary>
<p class="muted">全馬共通で採点できた調教・距離・展開などの暫定項目を使用した、別の1着・2着・3着研究候補です。上の2項目で発走前に固定した買い目は変更しません。ここは署名なし・未購入、正式100点・JRA公式確認・回収率にも反映しません。</p>
<div id="autoMultiQuickRaces"></div>
</details>
<details id="autoReferenceQuickPanel" class="owner-reference-quick">
<summary id="autoReferenceQuickTitle">見送りレースの参考候補：未取得</summary>
<p class="muted">署名なし・未購入の研究参考だけを一覧表示。各方式で検証済みの画面表示から転記し、同じRはひとつにまとめます。未評価の馬に架空の点数を入れず、正式10項目・JRA確定出走・購入や仮想回収率とは別です。</p>
<div id="autoReferenceQuickRaces"></div>
</details>
<details id="autoFixedQuickPanel" class="owner-fixed-quick">
<summary id="autoFixedQuickTitle">この端末の発走前固定：確認中</summary>
<p class="muted">以前に発走前固定した研究用3連単の<strong>閲覧専用履歴</strong>です。新しい予想・正式10項目採点・JRA公式照合・実購入ではありません。署名の真正性は別の検証ボタンで確認します。</p>
<p id="autoFixedQuickStatus" class="muted" role="status">この端末の固定記録を確認中です。</p>
<div id="autoFixedQuickRaces"></div>
</details>
<details class="owner-race-diagnostics"><summary>全Rの内訳・資料状況</summary><p id="autoSummary" class="muted">未取得</p></details><div id="autoVenues" class="venue-tabs" role="group" aria-label="競馬場を絞り込む"></div>
<label for="autoRacePick">見たいレースを選ぶ（全場・全Rから選択）</label>
<select id="autoRacePick" disabled><option value="">全Rを一覧表示</option></select>
<button id="autoNextDraft" type="button" class="secondary-cta" disabled>次の下書きRへ（未取得）</button>
<p class="muted">このボタンはJRDBの暫定発走時刻順です。JRA公式の発走時刻・取消を確認してください。</p>
<p id="autoViewingStatus" class="muted" role="status">レースを取得すると選択できます。</p>
<div id="autoRaces"></div>
<details id="autoHoldPanel"><summary>見送りの理由からレースを探す</summary>
<p class="muted">発走済み・資料不足・候補同点などの原因別に、そのレースだけを表示します。再分析や新しい買い目は作りません。</p>
<div id="autoHoldReasons" class="venue-tabs" role="group" aria-label="見送り理由で絞り込む"></div>
<p id="autoHoldStatus" class="muted" role="status">開催日を取得すると見送り理由を確認できます。</p>
</details>
<details id="autoResearchTools" class="owner-research-tools">
<summary>詳しい分析・調教資料を見る（任意）</summary>
<p id="autoUncertainRecentHint" class="muted" role="status">近走不足の追加研究：未取得。</p><p id="autoHeldTie48Hint" class="muted" role="status">同点見送りの48点以内参考：未取得。</p>
<p id="autoSourceSummary" class="muted" role="status">全Rの資料進捗は未取得です。</p>
<p id="autoTrainingFeedStatus" class="muted" role="status">調教元データの行数・馬番照合状況はまだ未確認です。</p>
<p id="autoTrackWorkouts" class="muted" role="status">調教S/Aの参考表示：JRDB資料の取得前です。</p>
<details id="autoWorkoutQuickPanel"><summary>全場の調教S/A馬番を発走順に見る（見送りRも）</summary>
<p class="muted">JRDB調教の未検証S/Aだけを馬番で一覧表示します。近走・展開・馬場・JRA最終出走確認を含めた総合順位や1着候補ではありません。行を押すと該当レースを表示するだけで、追加の有料通信や馬券購入は行いません。</p>
<p id="autoWorkoutQuickStatus" class="muted" role="status">未取得。開催日を読み込むと追加照会なしで一覧が作られます。</p>
<div id="autoWorkoutQuickRows" class="day-shortcuts"></div>
</details>
<details id="autoEvidenceGapPanel"><summary>正式10項目の不足資料を確認（追加照会なし）</summary>
<p class="muted">取得済みのJRDB資料がある頭数だけを集計。過去4角などの観測は今回の展開予測ではなく、資料の有無も正式な採点結果ではありません。発走前固定記録・買い目は変更しません。</p>
<pre id="autoEvidenceGapReport" class="acceptance-report" role="status">まだ未取得です。発走前の研究用データを取得すると、追加照会なしで表示します。</pre>
<p class="muted">10項目・合計100点の配点ごとに、取得済みの同じ資料から観測件数と、不足している資料の確認優先順を表示します。資料ありでもS/A/B/Cの採点やJRA公式照合が済んだ意味ではありません。追加の有料照会や保存・購入操作は行いません。</p>
<pre id="autoTenEvidenceMatrix" class="acceptance-report" role="status">10項目の資料確認はまだです。資料を再取得せず、すでに受信した内容のみ集計します。</pre>
<details id="autoJvHistoryJoinPanel"><summary>JRA-VANの保存済み全R過去走とJRDB馬番資料を照合（PC内ファイル・無料）</summary>
<p class="muted">同じ開催日のJRDB研究資料をこの画面で取得した後、本人のPCで保存済みの <code>jvdata-all-flat-races-YYYYMMDD.json</code> を選択して照合できます。ファイル本文・馬名・馬ID・過去走詳細は<strong>送信・保存しません</strong>。馬番の集合が一致しても、同じ馬の本人確認・JRA公式出走や正式10項目評価の証明にはなりません。3連単・固定記録・仮想収支は変更しません。</p>
<input id="autoJvHistoryFile" type="file" accept=".json,application/json">
<button id="autoJvHistoryCompare" type="button">取得済みJRDBとJRA-VANを馬番単位で照合（追加のAPI照会0回）</button>
<p id="autoJvHistoryStatus" class="muted" role="status">未照合。JRDBを取得した後に保存済みJRA-VANファイルを選んでください。</p>
<div id="autoJvHistoryRows" aria-label="開催場・レース別の資料照合結果"></div>
</details>
</details>

<details id="autoMissingFactorPanel"><summary>調教・近走不足の内訳（追加照会なし）</summary>
<p class="muted">既に取得したレース別の資料だけで未評価理由を集計します。過去走が少ない馬を0点扱いしたり、固定買い目を変えたりしません。</p>
<p id="autoMissingFactorSummary" class="muted" role="status">開催日を取得すると未評価の内訳を確認できます。</p>
<details><summary>資料不足のレース別内訳を見る</summary>
<div id="autoMissingFactorRaces"></div>
</details></details>
<details id="autoComparableFactorPanel"><summary>調教＋追加項目を使った3連単参考（見送りR・下書きR）</summary>
<p class="muted">見送りレースでも、全馬の調教30点・コース距離17点・展開脚質17点がそろう場合は、主要64点分を使って参考フォーメーションを検討します。それ以外は従来どおり共通の評価項目70点分以上が必要です。近走など欠けた項目は全馬から除外し、0点扱いしません。これは未校正の研究用で、正式100点予想・JRA公式照合・購入・固定記録・収支には反映しません。</p>
<p id="autoComparableFactorStatus" class="muted" role="status">見送りRの追加研究は未取得です。</p>
<div id="autoComparableFactorRaces"></div>
<h3>すでに2項目の下書きがあるRも比較</h3>
<p class="muted">既存の下書きとは別に、全馬で比較できる追加項目を使った1着／2着／3着の研究参考を表示します。元の固定買い目は上書きせず、正式100点評価・JRA公式確認・投票可能な買い目ではありません。</p>
<p id="autoProvisionalFactorStatus" class="muted" role="status">下書きRの追加研究は未取得です。</p>
<div id="autoProvisionalFactorRaces"></div>
</details>
<details id="autoUncertainRecentPanel"><summary>新馬戦候補・近走が少ないRの研究候補（署名・購入なし）</summary>
<p class="muted">JRDB番組名が新馬戦で、全馬の観測された近走が0走のときだけ「新馬戦候補」と区別します。番組名や過去走の空欄だけでは全馬の初出走を証明しません。近走3点の不足をC・0点扱いせず、欠けている評価がどんなS/A/B/Cでも、調教30点による候補グループが変わらない場合に限り、参考のフォーメーションを表示します。単独の調教最上位馬が明確な場合のみ1頭軸の研究例も扱いますが、勝ち馬の保証ではありません。正式10項目採点でもJRA公式出走確認でもなく、実際の購入・固定記録・仮想収支に入れません。</p>
<p id="autoUncertainRecentStatus" class="muted" role="status">レース取得前。追加資料を勝手に補完しません。</p>
<div id="autoUncertainRecentRaces"></div>
</details>
<details id="autoHeldTie48Panel"><summary>同点で見送りのRを48点以内で検証（署名・購入なし）</summary>
<p class="muted">調教30・近走3の両方が評価済みでも、同じ得点の馬が候補の境界にまたがると従来40点の下書きは見送ります。馬番順で同点馬を切らず、最大48点の中に収まるレースだけ参考の1/2/3着グループを表示。正式100点予想、勝率・JRA公式照合、実購入や保存済み馬券の変更ではありません。</p>
<p id="autoHeldTie48Status" class="muted" role="status">レース取得前。同点馬を勝手に選びません。</p>
<div id="autoHeldTie48Races"></div>
</details>
<details id="autoTkyTrainingPanel"><summary>調教資料不足Rの調教矢印・別指数（参考のみ）</summary>
<p class="muted">JRDB出走馬データ（/tky）の「調教矢印」は1〜5の状態評価。JRDB公式の説明に従い、矢印を指数より優先して表示します。別の「調教指数」は数値が高い順の参考で、矢印と結果が異なる場合は矢印を優先。どちらも追切・仕上指数（/tcy）とは別物です。矢印と指数の方向が逆の組数は確認用だけに表示します。同点や欠測は比較せず、欠測馬は最下位扱いしません。正式調教30点・10項目100点や3連単、発走前固定記録、購入には反映しません。</p>
<p id="autoTkyTrainingStatus" class="muted" role="status">発走前の資料が未取得です。</p>
<div id="autoTkyTrainingRows"></div>
</details>
<details id="autoTkyArrowFormationPanel"><summary>調教矢印が全頭そろうRの署名なし3連単参考（最大48点）</summary>
<p class="muted">JRDB /tkyの調教矢印を第一優先、全頭の別指数も揃う場合だけ同じ矢印内の指数順を使う研究用の組み合わせです。指数が一部欠けた場合は全指数を無視。矢印が1頭でも欠けたRや同点を切らないと組めないRは表示しません。<strong>正式10項目予想・JRA公式確認・馬券購入や保存記録ではありません。</strong></p>
<p id="autoTkyArrowFormationStatus" class="muted" role="status">発走前の調教矢印を確認していません。</p>
<div id="autoTkyArrowFormationRows"></div>
</details>

</details>
</section>
<section id="autoDayDetailSection">
<h2>3. 公式情報・取得状況・詳しい分析</h2>
<p class="muted">研究用3連単を見るだけなら、上の予想一覧から。馬券購入の判断前にはJRA公式の出走・取消・馬場・発走時刻を別に確認してください。追加分析と記録の管理もここから利用できます。</p>
<details id="autoDayDiagnostics"><summary>取得状況・見送り内訳を詳しく見る</summary>
<p id="autoMorningStatus" class="muted" role="status">開催日の取得結果を確認中です。発走前研究用の暫定案であり、正式な10項目予想ではありません。</p>
<p id="autoSnapshotAge" class="muted" role="status">JRDB受信時刻：未取得。以前の固定履歴とは別です。</p>
<details id="autoAcceptancePanel"><summary>土日の動作チェック（追加のJRDB照会なし）</summary>
<p class="muted">この画面で取得済みのデータと、このiPhoneの保存済み研究記録の件数だけを確認します。馬番・馬名・オッズ・認証キー・署名・買い目そのものは表示しません。</p>
<button id="autoAcceptanceCheck" type="button">選択日の取得・保存状況を確認</button>
<pre id="autoAcceptanceReport" class="acceptance-report" role="status">未確認。押した時だけ端末内の既存情報を集計します。</pre>
</details>
</details>
<p class="owner-official-shortcut"><a id="autoOfficialQuickLink" href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式出馬表を開いて出走・取消・発走時刻を確認</a> <span class="muted">（手動確認・自動照合0R）</span></p>
<p id="autoAdvanceHeadline" class="muted" role="status">JRA事前競馬番組（予定時刻・距離）：JRDB取得後に無料で自動比較。正式な最終照合ではありません。</p>
<details><summary>取得・資料の詳しい状態</summary>
<p id="autoProgrammeCoverage" class="muted" role="status">開催場別の取得R数：まだ確認していません。</p>
<p id="autoReadProof" class="muted" role="status">JRDB資料の照会状況は未確認です。番組0Rと全資料取得は別です。</p>
<p id="autoRecordSafety" class="muted" role="status">固定記録の保管状態：まだ確認していません。</p></details>
<a href="#autoVenues">開催日のレース一覧に進む</a>
<p class="muted"><a href="#autoHistoryAudit">過去の同条件照合へ進む</a>（旧85点の比較と新配点79点の研究用下書きを確認。追加の有料API取得は本人がボタンを押した時のみ）</p>
<details id="autoAdvancePanel"><summary>JRA競馬番組の予定時刻・距離を全場まとめて比較（無料）</summary>
<p class="muted">JRDB全R取得が正常終了したとき、JRA公表の事前競馬番組を無料で1回だけ自動比較。下のボタンで再比較もできます。これは発表当初の予定であり、出走馬・取消・当日馬場・変更後の最終発走時刻は証明できません。JRDBへの追加有料通信0回、失敗時も既存予想・固定記録は変更しません。</p>
<button id="autoAdvanceCompare" type="button">JRA予定時刻・コースを全場比較（無料）</button>
<p id="autoAdvanceStatus" class="muted" role="status">開催日のJRDB資料を読み込んだ後に確認できます。</p>
<p class="muted"><a id="autoAdvanceDirect" href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式の開催日程を直接開く（照合できない場合）</a></p>
<div id="autoAdvanceDifferences"></div>
</details>
<details><summary>JRA公式の出馬表PDFを開く（任意）</summary>
<p class="muted">本人が押した時だけJRA公式ページから開催場別の出馬表PDFリンクを探します。PDFの内容は自動解析しません。出走馬・取消・馬場・発走時刻を公式情報と自分で照合するための補助です。</p>
<button id="autoOfficialPdf" type="button">選択日のJRA公式PDFリンクを探す</button>
<p id="autoJraReleaseGuide" class="muted" role="status">選択日の出馬表公開目安を計算中。</p>
<a id="autoOfficialWebCard" href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式のWeb出馬表で馬番・出走馬を確認する</a>
<p class="muted">Web出馬表はPDF一覧と公開時期が異なります。正式10項目予想に必要な出走馬・取消・馬場・発走時刻の自動照合は未接続。公式ページを開くだけで照合済みとはしません。</p>
<p id="autoJraCrosscheck" class="muted" role="status">JRA公式照合：0R（未実施）。</p>
<p id="autoOfficialPdfStatus" class="muted" role="status">未確認。PDFリンクの存在だけではJRA公式照合済みとは扱いません。</p>
<div id="autoOfficialPdfLinks"></div>
<a href="https://www.jra.go.jp/keiba/rpdf/" target="_blank" rel="noopener noreferrer">JRA公式の出馬表一覧を開く</a>
<details><summary>選択中の1RでJRA Web出馬表の馬番・時刻・コース候補を確認（任意）</summary>
<p class="muted">下の一覧で対象Rを選び、「JRA公式URLを探して比較」を押してください。JRA公式の公開ページへ最大3回アクセス（JRDBの有料照会0回）します。公式ページの構造が変わった場合は見つからないことがあります。その場合は下のURL欄に手入力もできます。表示馬番の比較は参考情報のみ。出走・取消・馬場の正式照合や正式採点、固定買い目には反映しません。</p>
<button id="autoOfficialCardDiscover" type="button" class="secondary-cta">選択RのJRA公式URLを探して比較（追加JRDB 0回）</button>
<p id="autoOfficialCardLinkStatus" class="muted" role="status">未検索。公式出馬表へのリンクを探しただけでは照合済みにはなりません。</p>
<a id="autoOfficialCardResolved" href="https://www.jra.go.jp/keiba/" target="_blank" rel="noopener noreferrer">JRA公式の出馬表一覧を開く（選択Rのリンクは未特定）</a>
<label for="autoOfficialCardUrl">JRA公式Web出馬表のURL（自動で見つからない場合）</label>
<input id="autoOfficialCardUrl" type="url" maxlength="250" autocomplete="off" placeholder="https://sp.jra.jp/JRADB/accessD.html?CNAME=...">
<button id="autoOfficialCardCheck" type="button">選択中の1Rの馬番・時刻・コース候補を比較</button>
<p id="autoOfficialCardStatus" class="muted" role="status">未確認。JRDBの有料再取得や買い目更新は行いません。</p>
</details>
<details id="autoResultCandidatePanel"><summary>発走後のJRA結果候補と固定3連単を比較（研究用・任意）</summary>
<p class="muted">過去の開催日でもiPhoneに残っている「発走前固定済み」のレースを直接選べます。JRDBの再取得は不要です。JRA公式結果ページURLを貼ると、まず本人用サーバーで固定買い目の署名を確認し、成功した場合だけJRA表示の払戻候補を比較します。一致した払戻候補がある場合は1点100円の参考差額・参考回収率も試算しますが、結果確定・返還・原本認証は未検証のため正式的中・正式回収率・実購入には反映しません。一致候補がなくても外れとは断定しません。追加JRDB照会・保存変更は0回です。</p>
<label for="autoResultSavedRace">この端末に固定済みのレース（過去の日付も可）</label>
<select id="autoResultSavedRace" disabled></select>
<p id="autoResultSavedRaceStatus" class="muted" role="status">保存済みの発走前固定記録を確認中。未保存のレースは選択できません。</p>
<label for="autoResultCandidateUrl">選択RのJRA公式レース結果ページURL</label>
<input id="autoResultCandidateUrl" type="url" maxlength="500" autocomplete="off" placeholder="https://www.jra.go.jp/JRADB/accessS.html?CNAME=...">
<button id="autoResultCandidateCheck" type="button" class="secondary-cta">この1Rの3連単払戻候補を照合</button>
<p id="autoResultCandidateStatus" class="muted" role="status">結果候補の比較は未実行です。発走前固定記録・回収率は変更しません。</p>
</details>
</details>
<details><summary>開催日朝の使い方（3ステップ）</summary>
<p class="muted">① 当日の朝、本人用アプリを開く。自動取得が終わったら「開催日の利用状況」で番組R数・下書き数・見送り数を確認する。0Rやエラーの場合は無理に買い目を作らない。</p>
<p class="muted">② 下の「下書きのみ」を選ぶか、競馬場・レースを選択して1着／2着／3着の3連単と重複除外した点数を確認する。これは調教・近走だけの研究用下書きで、10項目の本予想や投票推奨ではない。</p>
<p class="muted">③ 発走前の固定記録を確認し、必要に応じて「15種類の記録をバックアップ・復元する」で保管する。サーバー永続保存と公式結果の照合はまだ別の作業。投票するならJRA公式で出走馬・取消・馬場・発走時刻を別途確認し、自分で判断する。</p>
</details>
<details><summary>端末の保存状況と再分析の差分</summary>
<p id="autoSavedStatus" class="muted" role="status">発走前の買い目は端末内の研究記録として保存できます。実購入の記録とは別です。</p>
<p id="autoFixedConsistency" class="muted" role="status">この日の最初の固定買い目と、再分析結果を比較する前です。署名検証は別操作です。</p></details>
<p class="muted">サーバー保存が未設定の間は、iPhoneの保存領域が消えると研究記録も失われる可能性があります。
<a href="/owner-backup">固定済み買い目など15種類の端末記録をバックアップする</a>。
既存の端末記録を消したり、別の版の保存内容を上書きしたりしません。</p>
<a id="autoReviewLink" href="/owner-100yen-review">固定した研究用買い目を100円仮想収支で確認</a>
<details id="autoAdvancedResearch" class="owner-advanced-research"><summary>さらに分析する：JRDB 5項目79点の研究・調教資料（任意）</summary>
<section id="autoFiveQuickSection" class="owner-five-quick">
<h3>JRDB 5項目の3連単研究（追加分析）</h3>
<p class="muted">調教30・近走3・コース17・展開17・馬場12の79点分を比較。正式100点予想ではありません。過去番組・馬場のJRDB追加照会は最大16回。ボタンを押すまで照会しません。</p>
<button id="autoFiveQuick" type="button" disabled>5項目の研究用3連単を追加分析（最大16照会）</button>
<label class="auto-five-consent"><input id="autoFiveWeekendOptIn" type="checkbox"> 土日の当日、アプリを開いて基本データを取得したら、5項目の追加分析も自動で1回だけ実行する</label>
<p id="autoFiveWeekendStatus" class="muted" role="status">自動追加分析はOFF。許可するまで追加のJRDB履歴照会はしません。</p>
<p class="muted">ONでもアプリを開いた時だけ実行（バックグラウンドなし）。開催日ごとに過去番組・馬場を最大16回、失敗時の自動再試行なし。発走前のレースがなければ照会せず、翌開催日以降もOFFに変更できます。正式10項目・JRA公式照合ではありません。</p>
<p id="autoFiveQuickStatus" class="muted" role="status">開催日の基本資料を取得すると使えます。新しい79点下書きは未取得です。</p>
<div id="autoFiveQuickSaved"></div>
<details class="owner-five-sparse-panel" id="autoMainWorkoutPanel">
<summary>JRDB本追切の調教資料を確認（任意・調教30点の根拠）</summary>
<p class="muted">本人が押した時だけJRDBの番組・出走馬・本追切データを計3回取得。追切日・終い・追切指数の記録有無を登録馬と照合します。指数値・調教タイム・オッズは表示せず、採点・3連単・結果は変更しません。</p>
<button id="autoMainWorkoutCheck" type="button" disabled>当日のJRDB本追切を照合（追加3照会）</button>
<p id="autoMainWorkoutStatus" class="muted" role="status">基本資料の取得後、発走前の当日だけ照合できます。</p>
<div id="autoMainWorkoutRaces"></div>
<div class="owner-training-pair">
<p class="muted">調教分析（/tcy）と本追切（/tch）の資料を同じ馬で突き合わせます。**4回の追加JRDB照会**が必要。指数値の大小・一致や正式30点採点には使いません。</p>
<button id="autoTcyTchCompare" type="button" disabled>調教分析＋本追切の両方を照合（追加4照会）</button>
<p id="autoTcyTchStatus" class="muted" role="status">本人操作でのみ4資料を比較します。自動では照会しません。</p>
<div id="autoTcyTchRaces"></div>
</div>
<details class="owner-five-sparse-panel">
<summary>過去の調教指数と実際の着順を参考照合（任意）</summary>
<p class="muted">JRDBの過去競走馬情報（dky）と過去成績（dse）を同じ馬で照合します。選んだ過去1日につき追加2照会。<strong>今週の追切指数と同一指標ではなく、JRA公式結果や時系列検証も未確認</strong>の研究です。正式な調教30点・買い目・回収率に使用しません。</p>
<label for="autoHistoricalTrainingDay">比較する過去開催日（日本時間）</label>
<input id="autoHistoricalTrainingDay" type="date">
<button id="autoHistoricalTrainingCheck" type="button">この過去1日の調教指数と着順を比較（追加2照会）</button>
<p id="autoHistoricalTrainingStatus" class="muted" role="status">本人がボタンを押すまで追加照会しません。初期設定は前週日曜日です。</p>
<div id="autoHistoricalTrainingRaces"></div>
</details>
</details>
<details id="autoFiveSparsePanel" class="owner-five-sparse-panel">
<summary>近走未評価でも境界が変わらない参考3連単・発走前記録</summary>
<p class="muted">近走3点が未評価でも、S〜Cのどれになっても候補区切りが変わらない場合だけの研究参考例です。残り4項目は全頭観測済み。<strong>正式10項目予想・馬券推奨・実購入・確定回収率ではありません。</strong></p>
<p id="autoFiveSparseStatus" class="muted" role="status">5項目の過去資料を取得すると参考候補を確認します。</p>
<div id="autoFiveSparseRaces"></div>
<p id="autoFiveSparseSavedStatus" class="muted" role="status">この端末の発走前固定研究例は未確認です。</p>
<div id="autoFiveSparseSaved"></div>
</details>
</section>
</details>
</section>
<section id="fixedHistorySection">
<h2>4. 発走前に固定した買い目</h2>
<p class="muted">最初に保存した買い目は再分析で上書きしません。</p>
<details><summary>発走前の調教S/A/B/Cを結果と比較（ランク間＋同ランク内の研究）</summary>
<p class="muted">通常のJRDB資料取得時、まだ発走していないレースの「同じ調教評価内での指数順」を、本人用サーバーが署名してこの端末に初回固定します。指数の原数値・架空の30点得点・3連単は保存しません。Safariとホーム画面の保存領域は異なる場合があります。</p>
<p id="autoWorkoutLockStatus" class="muted" role="status">選択日の発走前調教順位記録は未確認です。</p>
<button id="autoWorkoutProviderCheck" type="button" disabled>固定した調教順位をJRDB暫定着順と比較（任意・結果取得1回）</button>
<p id="autoWorkoutProviderStatus" class="muted" role="status">固定記録がある開催日だけ確認できます。結果照会はボタンを押した時だけです。</p>
<div id="autoWorkoutProviderSummary"></div>
<p id="autoWorkoutPairHistory" class="muted" role="status">過去日の暫定結果を積み上げた研究記録はまだありません。</p>
<p id="autoWorkoutCrossHistory" class="muted" role="status">調教ランク間の固定研究記録はまだありません。</p>
<button id="autoWorkoutCrossVerify" type="button" disabled>保存したランク間比較の署名を確認（JRDB追加0回）</button>
<p id="autoWorkoutCrossVerifyStatus" class="muted" role="status">初回固定済みランク間比較のみ再確認できます。</p>
<button id="autoWorkoutPairVerify" type="button" disabled>保存した結果の署名を確認（JRDB追加取得0回）</button>
<p id="autoWorkoutPairVerifyStatus" class="muted" role="status">同じiPhoneに結果の初回固定記録がある場合だけ確認できます。</p>
<p class="muted">発走前に固定したランクを使い、S対A・A対Bなどのランク間の先着関係と、同ランク内の指数順を別々に調査。取消・着順欠損は保留。ランク間も独立した署名で端末に初回固定し、複数開催日で比較できます。正式30点・JRA公式結果・回収率・既存買い目は変更しません。</p>
</details>
<button id="autoReceiptVerify" type="button">この日の固定買い目をサーバーで署名確認</button>
<p id="autoReceiptVerifyStatus" class="muted" role="status">未確認。端末内の署名付き研究記録だけを本人用サーバーで検証します。原データの追加取得や買い目の変更はありません。</p>
<p class="muted">署名が正しくてもJRA公式の発走時刻・結果・実購入・サーバー保存を証明するものではありません。サーバー保存が未設定なら、別途バックアップが必要です。</p>
<details><summary>サーバー保存済みの記録を見る（保存設定がある場合のみ）</summary>
<p class="muted">この操作は保存済みの研究用買い目を読み取るだけです。JRDB有料データの追加取得、発走後の予想生成、iPhone記録の復元・上書き、実購入は行いません。</p>
<button id="autoArchiveRead" type="button">選択日のサーバー固定記録を確認</button>
<p id="autoArchiveStatus" class="muted" role="status">未確認。保存用データベースが未設定なら、その旨を表示します。</p>
<div id="autoArchiveRaces"></div>
</details>
<p id="autoHistoryStatus" class="muted" role="status">この端末の固定記録を読み込み中です。</p>
<div id="autoHistory"></div>
<p class="muted">端末内の固定済み買い目を読み取り専用で表示します。
署名はこの画面では検証していません。後付け予想ではありません。</p>
<a href="/owner-backup">16種類の記録をバックアップ・復元する</a>
</section>
<details class="advanced-panel"><summary>追加分析・詳しい設定（必要なときだけ）</summary>
<section>
<h2>過去の同条件実績を照合</h2>
<p class="muted">必要なときだけ過去番組・馬場を最大8件照合（追加APIアクセスは最大16回）。
資料の数は適性点数や勝率ではありません。未取得や新馬を能力不足とは判断しません。
同条件の過去3〜5走が十分に確認できた場合だけ「好走実績の研究目安 S〜C」を表示します。
さらに過去4角の位置取りから、先行候補の競合状況と研究用の展開仮説を表示します。
これは10項目の正式なS〜C、勝率、1着候補の決定ではありません。</p>
<button id="autoHistoryAudit" type="button" disabled>過去の同条件を最大8件照合する</button>
<details><summary>騎手・厩舎10点の過去実データ接続テスト（任意）</summary>
<label><input id="autoHistoryStaffSample" type="checkbox"> 騎手・厩舎の過去資料を追加照合する（選択時のみ有料API照会）</label>
<label for="autoHistoryStaffRaceLimit">追加照合の件数</label>
<select id="autoHistoryStaffRaceLimit"><option value="1" selected>過去1R（追加最大2回）</option><option value="3">過去3R（追加最大6回）</option></select>
<p class="muted">チェックしなければ追加のAPI取得はなし。過去1R/3Rは既存履歴プランの先頭からのみ選択。3Rであっても予想精度の検証や正式10点の採点には不足です。馬名・馬ID・騎手/厩舎コード・着順原票は表示しません。買い目や回収率にも使いません。</p>
<p id="autoHistoryStaffStatus" class="muted" role="status">騎手・厩舎の追加照合はOFF。</p>
<p id="autoHistoryStaffArchiveStatus" class="muted" role="status">3R研究の開催日別保存は未確認。</p>
<button id="autoHistoryStaffArchiveVerify" type="button" disabled>保存した研究記録の署名を再確認</button>
<p id="autoHistoryStaffArchiveVerifyStatus" class="muted">研究記録は購入・正式採点に使いません。</p>
<div id="autoHistoryStaffArchiveList"></div>
</details>
<p class="muted">発走前に照合した巻き返し候補は署名を検証し、iPhone内に最初の候補を固定します。事後の再分析で候補を上書きしません。これは公式結果や馬券購入の証明ではありません。</p>
<p id="autoHistoryWatchSave" class="muted" role="status">発走前の候補記録は未確認。</p>
<details><summary>発走前に固定した重点3項目70点の研究記録</summary>
<p class="muted">調教30・コース距離20・展開20の<b>未検証の研究値</b>を、発走前に本人用サーバーが署名した場合だけiPhoneに初回固定します。これは正式な100点予想・勝率・3連単・JRA公式結果ではありません。発走後の後付け採点や再分析による上書きはしません。</p>
<p id="autoCoreSaveStatus" class="muted" role="status">まだ研究用70点の署名付き固定記録は確認していません。</p>
<button id="autoCoreVerify" type="button">この日の70点研究記録の署名を確認</button>
<p id="autoCoreVerifyStatus" class="muted" role="status">未確認。署名の検証だけで成績や回収率は集計しません。</p>
<button id="autoCoreProviderCheck" type="button" disabled>固定70点とレース後のJRDB成績を参考比較</button>
<p class="muted">このiPhoneで最初に固定した研究値がある場合だけ利用可能。押した時のみJRDB成績を最大1回取得し、暫定1〜3着と比較します。JRA公式照合、正式的中率、回収率、予想の修正は行いません。</p>
<p id="autoCoreProviderStatus" class="muted" role="status">署名付き70点研究記録のある開催日を選んでください。</p>
<div id="autoCoreProviderRaces"></div>
<div id="autoCoreSaved"></div>
</details>
<details><summary>発走前に固定した5項目85点の研究記録（正式未評価）</summary>
<p class="muted">調教30・近走3・コース距離20・展開20・馬場12の未検証の研究値です。履歴の照合時にサーバーが発走前と確認し、署名できた馬だけを初回固定します。正式100点、馬券、勝率、JRA結果ではありません。</p>
<p id="autoFiveSaveStatus" class="muted" role="status">85点研究の保存状況は未確認です。</p>
<button id="autoFiveProviderCheck" type="button" disabled>固定85点とレース後のJRDB成績を参考比較</button>
<p class="muted">発走前に本人用サーバーが署名した85点研究値だけを使います。押したときに限りJRDBの暫定成績を最大1回取得。正式な的中率・勝率・回収率・公式結果ではありません。</p>
<p id="autoFiveProviderStatus" class="muted" role="status">この日の署名済み85点記録がある場合だけ利用できます。</p>
<div id="autoFiveProviderRaces"></div>
<div id="autoFiveSaved"></div>
</details>
<details><summary>新配点79点・発走前に固定した3連単研究下書き</summary>
<p class="muted">「過去の同条件を照合」で新79点の研究下書きが作れたレースは、本人用サーバーで署名を検証してこの端末に**最初の買い目だけ**保存します。正式10項目・JRA公式照合・実購入ではなく、後から結果を見た修正もできません。旧85点の記録とは別です。</p>
<p id="autoResearch6DraftSaveStatus" class="muted" role="status">新79点研究下書きの初回固定は未確認です。</p>
<button id="autoResearch6DraftVerify" type="button">この日の79点下書きの署名を確認</button>
<p id="autoResearch6DraftVerifyStatus" class="muted" role="status">署名確認は未実行です。結果や回収率は集計しません。</p>
<div id="autoResearch6DraftSaved"></div>
</details>
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
<p class="muted">押したときだけJRDB直前情報から馬番別の馬体重・前走比の記録有無を照合。原数値・オッズ・パドック指数は画面に出しません。JRA公式の確定値や馬体評価ではありません。</p>
<button id="autoPrestartBody" type="button">今日の馬体重資料を確認</button>
<p id="autoPrestartStatus" class="muted" role="status">本人操作時だけ追加API照合。予想・買い目・回収率は変更しません。</p>
<div id="autoPrestartRaces"></div>
</section>

<section><h2>10項目の配点と評価状況</h2>
<p class="muted" id="autoPolicy100Notice">ARC RACEの評価配点は<strong>10項目・合計100点</strong>です。下に表示する内訳は現行research-6の100点方式です。調教・近走はまだ研究用の仮評価、残り8項目とJRA公式照合は未完成のため、正式な総合得点や買い目には反映しません。過去の署名済み記録・研究用の下書きは変更しません。</p>

<p id="autoTenStatus" class="muted" role="status">予想資料の取得後に表示します。</p>
<p id="autoFormalShadowStatus" class="muted" role="status">正式10項目エンジンと当日資料の接続は未確認。発走前の実資料が揃うまで正式得点・買い目は出しません。</p>
<div id="autoTenWeights" class="ten-weights"></div>
<p class="muted">総合S：85点以上／A：70点以上／B：55点以上／C：55点未満。
10項目の根拠がそろうまでは総合点・総合順位は「未評価」です。</p>
<details><summary>0.01点単位の細分化採点（研究段階・実レース未接続）</summary>
<p class="muted">S/A/B/Cは画面用の評価帯に残し、内部では調教30点の例ならS：27.00〜30.00点、A：22.00〜26.99点、B：15.00〜21.99点、C：0〜14.99点と細かく区別する試験エンジンを用意しています。10項目の配点合計100点は変更せず、正式な総合S/A/B/Cの境界は85／70／55点のままです。</p>
<p class="muted">これは架空データでの計算テストだけです。実馬の調教タイム・コース適性・展開・馬場などを検証済みの採点基準へつなぐ作業は未完了。JRDBのコードが存在するだけで29.5点などを作らず、根拠の欠ける馬には内部100点や順位を表示しません。現行の調教・近走2項目による下書き、署名済み買い目、購入記録、仮想収支は変更していません。</p>
</details>
<details><summary>正式100点の計算方法・安全確認</summary>
<p class="muted">各項目の配点に対してS＝満点、A＝2/3、B＝1/3、C＝0として足し合わせます。新100点配点（research-6）：コース・距離17／展開・脚質17／血統6／騎手・厩舎10。合計100点満点。旧70点・82点・85点の署名済み研究履歴は旧配点のまま保持し、正式100点とは混ぜません。例えば調教A＝20/30点・近走C＝0/3点・残り8項目がすべてS＝67/67点なら、合計87点のS。近走だけで総合を決めません。</p>
<p class="muted">ただしこれは<b>独立した根拠で10項目を検証できた時だけ</b>動く正式採点エンジンの計算式です。現在のJRDB調教・近走ランクは仮評価で、正式採点には昇格していません。8項目の能力判定、JRA公式の出走・取消・馬場・発走時刻の独立照合、当日馬体重、発走前の照合が不足する間は総合点・正式買い目を出しません。</p>
<p class="muted">根拠不足、発走済み、取消・出走確認の保留、点数同点の候補境界では正式3連単を作りません。表示中の3連単は引き続き2項目による研究用下書きです。</p>
</details>
</section>

</details>
<p class="muted">Sは金色、Aは赤色。調教・近走のS/A/B/Cはそれぞれの仮評価。仮順位は調教30：近走3の配点で算出し、
総合10項目ランクや勝率とは区別しています。
買い目は重複除外・原則40点以内、同点見送りだったRだけ最大48点・1点100円換算。結果を見てから買い目を作ることはできません。</p>
</main><script src="/owner-auto-forecast.js?v=20261124-race-nav" defer></script></body></html>"""

CSS = """*{box-sizing:border-box}html{color-scheme:dark}
body{margin:0;background:radial-gradient(ellipse 108% 35% at 82% 0%,#24669a7a,transparent 75%),linear-gradient(160deg,#103a61,#0b2745 55%,#071a30 100%);min-height:100vh;color:#eff5ff;font:15px/1.55 system-ui,sans-serif}
main{max-width:780px;margin:auto;padding:16px 13px 46px}
.owner-preday-recovery{margin:12px 0 18px;padding:13px;border:1px solid #648aa6;border-radius:13px;background:#143452}
.owner-preday-recovery p{margin:0 0 9px;font-size:14px;line-height:1.6}
.owner-preday-recovery strong{color:#f1d48d}
.owner-preday-recovery .owner-forecast-cta{margin:8px 0 0}
h1{font-size:24px;color:#f0d07e;margin:17px 0}
h1 small{display:block;color:#c7d7e7;font-size:13px}
/* ARC RACE B direction: dynamic gold/blue course arcs + readable horse silhouette.
   Presentation only: no storage, provider calls, prediction or auth changes. */
.arc-brand{display:flex;align-items:center;gap:11px;overflow:hidden;margin:12px 0 15px;padding:13px 10px;background:linear-gradient(125deg,#071322 0%,#10263c 75%,#0a1a2d 100%);border:1px solid #bc954b;border-radius:17px;box-shadow:inset 0 1px 0 #edca7850,0 10px 22px #020a1538}
.arc-brand-mark{width:100px;height:86px;flex:0 0 100px;filter:drop-shadow(0 0 6px #d7a84c38)}
.arc-brand-copy{min-width:0}
.arc-brand-copy h1{margin:0;color:#f0cf80;font:italic 800 clamp(25px,5.7vw,37px)/1.05 Georgia,'Times New Roman',serif;letter-spacing:.025em;white-space:nowrap;text-shadow:0 0 14px #d6a85522}
.arc-brand-jp{margin:2px 0;color:#f2dbaa;font-size:13px;letter-spacing:.13em}
.arc-brand-sub{margin:3px 0 0;font-size:12px;color:#e6eef7}
.arc-brand-engine{margin:0;font-size:11px;color:#9ab9d6}
.arc-brand-engine strong{color:#f1cb76;letter-spacing:.045em}
@media(max-width:360px){.arc-brand{gap:6px;padding:9px 6px}.arc-brand-mark{width:80px;height:75px;flex-basis:80px}.arc-brand-copy h1{font-size:25px}.arc-brand-sub{font-size:11px}}
@media(prefers-reduced-motion:reduce){.arc-brand-mark{animation:none}}

.arc-legacy-context{font-size:12px;color:#b9cbe0;margin:-7px 0 13px}

/* Owner iPhone first: racecards before optional research, no behavior change. */
html{scroll-behavior:smooth}
main{padding-bottom:65px}
.arc-main-tabs{position:sticky;top:0;z-index:15;display:grid;
 grid-template-columns:repeat(4,minmax(0,1fr));gap:5px;
 margin:9px 0 12px;padding:7px;border:1px solid #6787a3;
 border-radius:12px;background:#0b2138f5;box-shadow:0 3px 13px #06142783}
.arc-main-tabs a{display:flex;align-items:center;justify-content:center;
 min-height:43px;padding:6px 4px;border-radius:8px;
 color:#f3db9c;background:#24415d;font-size:13px;font-weight:800;
 text-decoration:none;text-align:center}
.arc-main-tabs a:focus-visible,.quick-links a:focus-visible{outline:3px solid #e8c774}
.arc-main-tabs #autoQualityLink{background:#215980;color:#f5e4b8}
#autoDailyStart,#forecastRacesSection,#fixedHistorySection{scroll-margin-top:74px}
.owner-menu{background:transparent;border:0;margin:0;padding:0}
.owner-menu>summary{display:inline-flex;align-items:center;
 min-height:30px;color:#bcd0e1;font-weight:600;font-size:12px}
.owner-menu .owner-nav{margin:5px 0 9px;padding:7px;background:#10263d;border-radius:9px}
.owner-weekend-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.owner-weekend-actions button{margin:5px 0;min-height:58px;padding:9px 6px;
 font-size:14px;line-height:1.3;background:#2b425b;color:#eff5ff;
 border:1px solid #7894af}
.owner-weekend-actions button[data-selected="true"]{background:#e8c774;
 color:#182b41;border-color:#e8c774}
.auto-easy-pulse,.auto-race-quick{padding:12px;border:1px solid #7f9eb9;
 background:#102f4d;border-radius:11px;color:#f1d48c;
 font-weight:850;font-size:18px;line-height:1.48;overflow-wrap:anywhere}
.auto-race-quick{font-size:16px;margin:10px 0}
.owner-forecast-cta{display:block;background:#246da1;color:#fff;
 text-align:center;font-size:17px;font-weight:850;padding:14px 11px;
 min-height:52px;border:1px solid #83b7df;border-radius:11px;
 margin:11px 0;text-decoration:none;box-shadow:0 3px 12px #071d30}
.owner-forecast-cta:focus-visible{outline:3px solid #f5d691;outline-offset:3px}
.owner-advanced-research>summary{font-size:16px;font-weight:800;color:#eed28c}
.owner-five-quick{margin:13px 0;padding:12px;border:1px solid #6c91ac;
 border-radius:12px;background:#132d45}
.owner-five-quick h3{margin:0;font-size:17px;color:#edd28b}
.owner-five-quick button{min-height:47px;width:100%;font-weight:800}
.owner-five-sparse-panel{margin:9px 0;padding:10px;border:1px solid #426b8c;
 background:#11273c;border-radius:10px}
.owner-five-sparse-panel summary{font-size:14px;font-weight:750;color:#d3e4f5}
.owner-five-sparse-card{margin:9px 0;padding:9px;border:1px solid #5782a2;
 border-radius:8px}
.owner-five-sparse-card .picks{font-size:16px;margin:4px 0}
.auto-five-consent{display:flex;align-items:flex-start;gap:9px;
 font-size:15px;font-weight:700;margin:12px 0 4px}
.auto-five-consent input{width:21px;height:21px;min-width:21px;
 margin:2px 0 0;accent-color:#83bee9}
.owner-five-quick-card{margin:8px 0;padding:10px;border:1px solid #567c9d;
 border-radius:10px;background:#0e2439}
.owner-five-quick-card .picks{font-size:17px;margin:6px 0}
.owner-reference-quick{margin:10px 0 14px;padding:12px;border:1px solid #718fae;
 background:#10283f;border-radius:12px}
.owner-reference-quick>summary{font-weight:850;color:#f1d28e;font-size:16px}
.owner-reference-quick-card{border:1px solid #537c9f;padding:10px;
 border-radius:10px;margin:9px 0;background:#132c45}
.owner-research-draft{border-color:#69b8e9}
.owner-research-reference{border-color:#6d8baf}
.owner-research-hold{border-color:#455e78;background:#102337}
.owner-workout-only{font-size:15px;font-weight:850;line-height:1.45;
 margin:5px 0;overflow-wrap:anywhere}
.owner-workout-S{color:#f3d475}
.owner-workout-A{color:#ffa6b1}
.owner-workout-B{color:#a4d8ff}
.owner-workout-C{color:#dce2eb}
.owner-factor-agreement{color:#f1dbad;font-size:12px;
 line-height:1.5;font-weight:700;margin:8px 0 4px}
.owner-race-jump{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));
 gap:5px;margin:9px 0 13px}
.owner-race-jump button{margin:0;min-height:42px;width:100%;
 background:#244762;border:1px solid #6f97b7;color:#e7effb;
 border-radius:8px;font-size:14px;font-weight:850;padding:5px 1px}
.owner-race-jump button[aria-pressed="true"]{background:#e8c774;
 color:#172b40;border-color:#f1d38b}
.owner-race-jump button:focus-visible{outline:3px solid #e8c774;outline-offset:2px}
@media(max-width:355px){.owner-race-jump{grid-template-columns:repeat(5,minmax(0,1fr))}}
.owner-reference-quick-card .picks{font-size:15px;font-weight:750;margin:5px 0;
 overflow-wrap:anywhere}
.owner-reference-quick-card button{font-size:14px;min-height:45px;width:100%;
 background:#236596;border:1px solid #85b5d5;color:#fff;font-weight:800}
.owner-fixed-quick{margin:10px 0;border:1px solid #7995af;
 padding:10px;border-radius:12px;background:#142c44}
.owner-fixed-quick>summary{font-weight:800;color:#f3d58e;font-size:15px}
.owner-fixed-card{margin:9px 0;padding:9px;border:1px solid #587b9b;
 border-radius:9px;background:#102439}
.owner-fixed-card .picks{margin:5px 0;font-size:17px}
.owner-fixed-card details{margin-top:7px;font-size:13px}
.owner-instructions,.owner-research-tools{margin:12px 0}
.owner-research-tools>summary{font-size:15px}
.quick-links{margin:7px 0}
.quick-links a{font-weight:750}
@media(max-width:520px){
 .arc-brand{padding:8px 9px;margin:7px 0 10px;gap:8px}
 .arc-brand-mark{width:73px;height:60px;flex-basis:73px}
 .arc-brand-copy h1{font-size:26px}
 .arc-brand-jp{font-size:11px;margin:0}
 .arc-brand-sub{font-size:10px;margin:1px 0}
 .arc-brand-engine{font-size:10px}
 .arc-legacy-context{margin:0 0 7px}
 section{padding:11px;margin:9px 0}
 .warning{padding:9px}
 .owner-weekend-actions button{font-size:13px}
}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}

h2{font-size:19px;margin:0 0 10px}
nav{display:flex;justify-content:space-between;gap:12px}a{color:#f0d185}
.owner-nav{flex-wrap:wrap;gap:6px 12px;justify-content:flex-start}
.owner-nav a{display:inline-flex;align-items:center;min-height:34px;font-size:13px}
section{background:#173b5b;border:1px solid #517999;border-radius:14px;padding:14px;margin:14px 0}
.daily-start{border-color:#9c895e}
.acceptance-report{white-space:pre-wrap;overflow-wrap:anywhere;border:1px solid #536d84;background:#0d2339;color:#dbe9f7;border-radius:10px;padding:10px;font-size:13px;line-height:1.65}
.primary-cta{background:#e8c774;color:#182b41}
.secondary-cta{background:#2b425b;color:#eff5ff;border:1px solid #7894af}
.quick-links{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.quick-links a{flex:1 1 130px;text-align:center;border:1px solid #7894af;border-radius:9px;background:#213a54;text-decoration:none;padding:10px}
.advanced-panel{margin:16px 0}
.warning{background:#342d25;color:#ffe6b5;border:1px solid #9b8052;border-radius:10px;padding:12px;font-size:13px}
.muted{font-size:13px;color:#c3d3e3}
label{display:block;font-weight:700}
input,button,select{font:inherit;min-height:45px;padding:11px;border-radius:10px;margin:7px 0;width:100%}
input,select{background:#0c2135;color:white;border:1px solid #90a6b9}
button{background:#e8c774;color:#182b41;border:0;font-weight:800}
button:disabled,select:disabled{opacity:.55}
.day-shortcuts{display:flex;gap:8px}
.day-shortcuts button{flex:1;min-width:0;background:#2b425b;color:#eaf3ff;
 font-size:13px;padding:8px}
.venue-tabs{display:flex;flex-wrap:wrap;gap:7px}
.venue-tabs button{flex:1 1 100px;width:auto;background:#2b425b;color:#eaf3ff}
.venue-tabs button[aria-pressed=true]{background:#e8c774;color:#152a3d}
details{border:1px solid #45617e;background:#10263d;border-radius:11px;margin:8px 0;padding:10px}
summary{font-weight:800;color:#f2d596;cursor:pointer;min-height:35px}
.hold{color:#e9bfae;font-size:13px;margin:8px 0}
.runner{display:flex;align-items:center;flex-wrap:wrap;gap:7px;
 background:#1e4567;border-radius:9px;padding:8px;margin:6px 0}
.number{font-size:19px;font-weight:850;min-width:44px}
.rank{font-size:12px;min-width:43px;color:#c6d5e7}
.grade{padding:3px 7px;border-radius:6px;background:#3b5065;font-weight:800;font-size:12px}
.S{color:#f3d475}.A{color:#ffa6b1}.B{color:#a4d8ff}.C{color:#dde2ed}
.notes{font-size:12px;color:#c1d3e7;flex-basis:100%}
.formation{background:#173c5d;border:1px solid #456582;border-radius:10px;padding:12px;margin:10px 0}
.formation strong{color:#e8ca81}
.formation p{margin:6px 0}
.picks{font-weight:850;font-size:18px;line-height:1.45;
 color:#f0e4c9;letter-spacing:.02em;overflow-wrap:anywhere}
.ticket-breakdown{margin-top:10px;background:#10263d}
.ticket-breakdown summary{font-size:14px}
.horse-research{margin:9px 0}
.horse-research>summary{font-size:14px;color:#d5e2f1}
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
.race-study{display:flex;flex-wrap:wrap;gap:7px;padding:8px 9px;margin:9px 0;background:#193a58;border:1px solid #43617c;border-radius:9px}
.race-study span{display:inline-block;padding:4px 6px;border-radius:5px;font-size:12px;font-weight:750}
.race-study .workout-s{color:#f3d475;background:#564728}
.race-study .workout-a{color:#ffa6b1;background:#513345}
.race-study .study-neutral{color:#d9e8f7;background:#294560}
.manual-entry-link{display:block;text-align:center;border:1px solid #8aa7c0;border-radius:9px;padding:11px 7px;margin:12px 0;color:#e9f2fd;text-decoration:none;background:#284866;font-weight:800}
.history-coverage{border:1px solid #45617e;background:#182f48;border-radius:10px;margin:7px 0;padding:10px}
.history-coverage strong{color:#f3d475}.history-coverage p{font-size:12px;margin:4px 0}
@media(max-width:380px){.number{min-width:34px}.rank{min-width:35px}}

/* Compact owner mode: date -> source -> venue -> 12R. All existing
   evidence, results, and settings remain accessible in detailed mode. */
.owner-view-switch{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin:8px 0 12px}
.owner-view-switch button{margin:0;min-height:48px;background:#203c59;
 color:#dce9f7;border:1px solid #6285a7;font-size:14px;padding:8px 6px}
.owner-view-switch button[aria-pressed="true"]{background:#e8c774;color:#132a41;border-color:#f3d991}
#ownerDetailToggle{grid-column:1/-1;min-height:40px;background:#1a3550;
 color:#c5d7e9;font-size:13px}
#ownerDetailToggle[aria-pressed="true"]{background:#365a77;color:white}
.owner-view-switch button:focus-visible{outline:3px solid #f4d68c;outline-offset:2px}
body.owner-simple .daily-start{padding:12px;margin:8px 0;border:1px solid #7f99b2}
body.owner-simple .daily-start input[type="date"]{font-size:18px;font-weight:800;min-height:48px}
body.owner-simple .owner-weekend-actions button{min-height:50px;margin:2px 0;font-size:14px}
body.owner-simple #autoMondayQuick:not([hidden]){grid-column:1/-1}
body.owner-simple .owner-preday-recovery h2{font-size:18px;color:#f3d78b}
body.owner-simple .owner-preday-recovery{margin:8px 0;padding:11px}
body.owner-simple .owner-preday-recovery .owner-reference-quick-card .picks,
body.owner-simple #autoCombinedResearchRows .picks{font-size:19px;line-height:1.7}
body.owner-simple .owner-preday-recovery .venue-tabs button,
body.owner-simple #autoCombinedResearchRows .venue-tabs button{font-size:16px;font-weight:850;min-height:47px}
body.owner-simple .owner-reference-quick-card{padding:12px;margin:8px 0}
body.owner-simple .owner-reference-quick-card strong{font-size:17px}
body.owner-simple .owner-reference-quick-card .muted{font-size:12px;line-height:1.45}
body.owner-simple:not(.owner-detailed).owner-preday-view #forecastRacesSection,
body.owner-simple:not(.owner-detailed).owner-jrdb-view .owner-preday-recovery{display:none}
body.owner-simple:not(.owner-detailed) .owner-instructions,
body.owner-simple:not(.owner-detailed) #autoStoragePulse,
body.owner-simple:not(.owner-detailed) #autoHoldBreakdown,
body.owner-simple:not(.owner-detailed) .quick-links,
body.owner-simple:not(.owner-detailed) .owner-quick-research,
body.owner-simple:not(.owner-detailed) #autoForecastJump,
body.owner-simple:not(.owner-detailed) #autoDayDetailSection,
body.owner-simple:not(.owner-detailed) #fixedHistorySection,
body.owner-simple:not(.owner-detailed) .advanced-panel,
body.owner-simple:not(.owner-detailed) #autoMultiQuickPanel,
body.owner-simple:not(.owner-detailed) #autoReferenceQuickPanel,
body.owner-simple:not(.owner-detailed) #autoFixedQuickPanel,
body.owner-simple:not(.owner-detailed) #autoCombinedResearchExport,
body.owner-simple:not(.owner-detailed) #autoCombinedResearchExportStatus,
body.owner-simple:not(.owner-detailed) #autoCombinedNoPickPanel,
body.owner-simple:not(.owner-detailed) #autoVenues,
body.owner-simple:not(.owner-detailed) #autoRacePick,
body.owner-simple:not(.owner-detailed) #autoNextDraft,
body.owner-simple:not(.owner-detailed) #autoViewingStatus,
body.owner-simple:not(.owner-detailed) #autoRaces,
body.owner-simple:not(.owner-detailed) #autoHoldPanel,
body.owner-simple:not(.owner-detailed) #autoResearchTools,
body.owner-simple:not(.owner-detailed) #forecastRacesSection>.owner-race-diagnostics,
body.owner-simple:not(.owner-detailed) #forecastRacesSection>label,
body.owner-simple:not(.owner-detailed) #forecastRacesSection>p.muted,
body.owner-simple:not(.owner-detailed) .owner-preday-recovery>p:first-of-type,
body.owner-simple:not(.owner-detailed) .owner-preday-recovery>p:last-child{display:none}
body.owner-simple:not(.owner-detailed) .owner-readiness-brief{background:transparent;border:0;padding:0;margin:4px 0}
body.owner-simple:not(.owner-detailed) #autoOperationalNext{font-size:12px;line-height:1.45;margin:5px 0}
body.owner-simple:not(.owner-detailed) #autoStatus{font-size:12px;line-height:1.45}
body.owner-simple:not(.owner-detailed) .owner-preday-recovery .owner-forecast-cta{font-size:13px;padding:9px;min-height:40px}
body.owner-simple:not(.owner-detailed) #autoPredayInlineLoad{min-height:39px;font-size:12px;padding:6px;margin:4px 0}
body.owner-simple:not(.owner-detailed) .auto-easy-pulse{font-size:15px;padding:9px}
body.owner-simple:not(.owner-detailed) #autoCombinedResearchPanel{padding:9px}
body.owner-simple:not(.owner-detailed) #autoCombinedResearchPanel>p.muted{display:none}
body.owner-simple:not(.owner-detailed) #autoCombinedResearchStatus{font-size:13px;padding:8px}
body.owner-simple:not(.owner-detailed) #autoPredayInlineStatus{font-size:13px;margin:5px 0}
@media(max-width:440px){
 .owner-view-switch{gap:5px}
 .owner-view-switch button{font-size:13px;min-height:44px}
 body.owner-simple .arc-legacy-context{display:none}
 body.owner-simple .arc-main-tabs{margin:5px 0}
 body.owner-simple .arc-main-tabs a{min-height:40px;padding:5px 1px;font-size:12px}
}
"""

JS = r"""(()=>{'use strict';
const $=id=>document.getElementById(id);
const GRADES=new Set(['S','A','B','C','未評価']);
const TEN=[
 ['training','調教',30],['recent','近走',3],
 ['course_distance','コース・距離',17],['pace','展開・脚質',17],
 ['ground','馬場',12],['pedigree','血統',6],
 ['draw_weight','枠・斤量',3],['jockey_stable','騎手・厩舎',10],
 ['rotation','ローテ',1],['body_condition','馬体重',1]
];
const MISSING={
 missing_training_indices:'調教：追切・仕上指数の片方または両方が不足',
 no_linked_training_record:'調教：この馬に照合できる資料なし',
 no_usable_history:'近走：評価に使える過去走なし',
 only_one_usable_run:'近走：使える資料が1走のみ（現基準は2走必要）',
 insufficient_scored_runs:'近走：着順と指数がそろう資料が2走未満',
 crossfeed_run_count_mismatch:'近走：JRDBの過去走参照と観測走数が不一致',
 no_linked_recent_record:'近走：この馬に照合できる資料なし',
 training_unassessed:'調教：資料不足・理由の再確認が必要',
 recent_unassessed:'近走：資料不足・理由の再確認が必要'
};
function missingText(h){return (Array.isArray(h.missingReasons)?h.missingReasons:[])
 .filter(k=>Object.hasOwn(MISSING,k)).map(k=>MISSING[k]).join('／');}
// Read-only classification of already-redacted runner reason codes.
// No provider identities, paid fields, extra HTTP reads, or new rankings.
const RECENT_GAPS=[
 ['no_linked_recent_record','近走資料の馬別照合なし'],
 ['no_usable_history','評価に使える過去走なし'],
 ['only_one_usable_run','評価可能な過去走1走のみ'],
 ['insufficient_scored_runs','着順・指数ペア不足'],
 ['crossfeed_run_count_mismatch','JRDB過去走参照と観測走数の不一致'],
 ['recent_unassessed','理由の再確認が必要']
];
const TRAINING_GAPS=[
 ['no_linked_training_record','調教資料の馬別照合なし'],
 ['missing_training_indices','追切・仕上指数不足'],
 ['training_unassessed','理由の再確認が必要']
];
function missingFactorHoldBreakdown(data){
 const held=data.races.filter(row=>row.status==='hold'&&row.reason==='missing_factors');
 const rec=Object.fromEntries(RECENT_GAPS.map(([k])=>[k,0]));
 const tr=Object.fromEntries(TRAINING_GAPS.map(([k])=>[k,0]));
 let recTotal=0,trTotal=0,both=0,unknownRaces=0;
 const races=[];
 for(const race of held){
  let recent=0,training=0,pairs=0;
  for(const h of race.runners){
   const t=h.training==='未評価',r=h.recent==='未評価';
   const reasons=Array.isArray(h.missingReasons)?h.missingReasons:[];
   if(t){
    const found=TRAINING_GAPS.map(([key])=>key).filter(key=>reasons.includes(key));
    tr[found.length===1?found[0]:'training_unassessed']++;
    trTotal++;training++;
   }
   if(r){
    const found=RECENT_GAPS.map(([key])=>key).filter(key=>reasons.includes(key));
    rec[found.length===1?found[0]:'recent_unassessed']++;
    recTotal++;recent++;
   }
   if(t&&r){both++;pairs++;}
  }
  const available=race.runners.length>0&&(training+recent)>0;
  if(!available)unknownRaces++;
  races.push({track:race.track,race:race.race,training,recent,pairs,available});
 }
 const describe=(types,counts)=>types.filter(([key])=>counts[key]>0)
  .map(([key,label])=>label+' '+counts[key]+'頭').join('／');
 const summary=!held.length
  ?'調教・近走不足による見送りは0R。資料不足を勝手に推測しません。'
  :'調教・近走不足で見送り '+held.length+'R。近走未評価 '+recTotal+
   '頭（'+(describe(RECENT_GAPS,rec)||'内訳未確認')+'）。調教未評価 '+
   trTotal+'頭（'+(describe(TRAINING_GAPS,tr)||'内訳未確認')+
   '）。両方未評価 '+both+'頭。'+
   (unknownRaces?'馬別内訳が確認できないレース '+unknownRaces+'R。':'')+
   '未評価の件数は能力0点ではなく、正式10項目予想や購入推奨でもありません。';
 return {summary,races};
}
// Optional /tky reference vs /tze recent source diagnostic from the same
// paid-read snapshot. Cross-check against already validated held horse counts.
// It never fills an unknown grade, modifies a draft, or starts a new request.
function safeRecentCrossfeed(data,day){
 const p=data.recentCrossfeedDiagnostic;
 if(p===undefined)return null; // Older service/fixture.
 const names=['more_prior_references_than_tze_runs',
  'no_prior_reference_visible','only_one_dated_run_visible',
  'multiple_unscored_runs_visible','reference_or_tze_coverage_unknown'];
 const safeCounts=counts=>counts&&typeof counts==='object'&&!Array.isArray(counts)&&
  Object.keys(counts).length===names.length&&
  names.every(k=>Number.isInteger(counts[k])&&counts[k]>=0&&counts[k]<=2160);
 if(!p||p.version!=='owner-recent-crossfeed-diagnostics-1'||
    p.date!==day||p.raceCount!==data.raceCount||
    p.researchOnly!==true||p.privateOwnerOnly!==true||
    p.officialJraVerified!==false||p.formalRecentGradesVerified!==0||
    p.newProviderRequests!==0||p.existingTicketsChanged!==false||
    p.existingReceiptsChanged!==false||!safeCounts(p.reasonCounts)||
    !Number.isInteger(p.unassessedRecentCount)||
    !Array.isArray(p.races)||p.races.length>data.holdCount||
    p.examinedHeldRaces!==p.races.length||
    names.reduce((n,k)=>n+p.reasonCounts[k],0)!==p.unassessedRecentCount)
  return null;
 const verified=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 const byRace=new Map(),totals=Object.fromEntries(names.map(k=>[k,0]));
 for(const r of p.races){
  if(!r||typeof r.track!=='string'||!Number.isInteger(r.race)||
     !safeCounts(r.reasonCounts)||!Number.isInteger(r.unassessedRecentCount))
   return null;
  const key=r.track+'|'+r.race,base=verified.get(key);
  if(!base||byRace.has(key)||base.status!=='hold'||
     base.reason!=='missing_factors'||!Array.isArray(base.runners)||
     r.unassessedRecentCount!==base.runners.filter(h=>h.recent==='未評価').length||
     names.reduce((n,k)=>n+r.reasonCounts[k],0)!==r.unassessedRecentCount)
   return null;
  byRace.set(key,r);
  for(const k of names)totals[k]+=r.reasonCounts[k];
 }
 if(names.some(k=>totals[k]!==p.reasonCounts[k]))return null;
 return {byRace,counts:totals,total:p.unassessedRecentCount};
}
const RECEIPTS_KEY='keiba-nine-owner-server-receipts-v1';
const WORKOUT_LOCK_STORAGE='keiba-nine-owner-workout-order-locks-v1';
const WORKOUT_PAIR_STORAGE='keiba-nine-owner-workout-pair-observations-v1';
const WORKOUT_CROSS_STORAGE='keiba-nine-owner-workout-cross-band-observations-v1';
let workoutProviderSeq=0,workoutPairVerifySeq=0,workoutCrossVerifySeq=0;
// Safe, fixed server diagnostics. Do not display raw provider error text.
const FAILURE_STAGE={
 programme:'番組取得・形式確認',entries:'出走馬取得',training:'調教取得',
 recent:'近走取得',day_research:'全レース資料照合',
 draft_generation:'研究用買い目生成',receipt_signing:'発走前記録の署名',
 receipt_archiving:'サーバー記録の固定保存',
 final_prestart_gate:'発走前時刻の最終確認'
};
const FAILURE_KIND={
 provider:'JRDB API通信・応答',
 provider_auth:'JRDB認証（401：APIキー・認証キーを確認）',
 provider_entitlement:'JRDB利用権限（403：β版の利用権限を確認）',
 provider_rate_limit:'JRDB通信回数の制限（429：間隔を空けて再試行）',
 programme_format:'番組形式',
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
 formation_size:'買い目点数の検算',
 ticket_integrity:'3連単の重複・形式',
 clock_invalid:'発走前の時刻形式',
 report_contract:'予想レポートの形式',
 race_identity:'競馬場・レース番号の整合',
 hold_integrity:'見送りRの買い目混入',
 off_time:'発走時刻の一致',
 amount_integrity:'点数・金額の整合',
 receipt_identity:'署名記録の識別',
 receipt_draft_mismatch:'署名記録と予想の一致',
 receipt_set_mismatch:'署名記録の不足・余分',
 receipt_count_mismatch:'署名記録の件数',
 receipt_integrity:'署名記録の最終整合',
 other:'未分類の照合条件'
};
const REASONS={
 missing_research:'このレースの資料に不整合あり・自動判定を見送り',
 runner_count_mismatch:'出走頭数が資料と不一致',
 too_few_runners:'4頭未満で候補を作成できない',
 missing_factors:'一部の馬の調教または近走が未評価',
 missing_post_time:'暫定発走時刻を安全に確認できない',
 unconfirmed_runner_count:'JRDB番組の登録頭数が未確認のため出走馬の件数を照合できません。研究用3連単は作りません',
 after_provisional_off:'暫定発走時刻を過ぎたため後付け買い目なし',
 ambiguous_equal_grade_boundary:'同評価の馬が候補の境界にいるため選定保留',
 invalid_two_factor:'このレースの調教・近走の資料検証に不一致があり、安全のため見送り',
 archived_earlier_draft:'このRの別の買い目が先にサーバーへ固定済み。再分析の買い目は表示しません。固定済み記録は100円仮想収支で確認',
 provider_withdrawal:'JRDB資料に出走取消の報告あり。研究用3連単は作成せず、JRA公式で取消・出走馬を確認してください。以前の固定買い目があっても有効とは限りません'
};
const SHORT_HOLDS={
 after_provisional_off:'発走済み',missing_factors:'調教・近走不足',
 ambiguous_equal_grade_boundary:'候補同点',missing_research:'資料確認',
 invalid_two_factor:'2項目不整合',runner_count_mismatch:'頭数不一致',
 too_few_runners:'少頭数',missing_post_time:'発走時刻未確認',
 unconfirmed_runner_count:'番組頭数未確認',
 archived_earlier_draft:'既存の固定買い目を優先',
 provider_withdrawal:'提供元の取消報告'
};
const RUNNER_ISSUES={
 contract:'2項目評価の形式',runner_shape:'馬番別資料の形式',
 completeness:'評価済み項目数',rank_order:'評価順位',
 incomplete_rank:'未評価馬の順位',missing_reasons:'未評価の理由',
 summary_count:'評価済み頭数'
};
// Only predetermined private diagnostics, never provider values or raw errors.
const REVIEW_STAGES={
 entries:'出走馬・登録頭数',
 training:'調教資料の整合性',
 recent:'近走資料の整合性',
 runner_join:'調教と近走の馬番照合'
};
const MATERIAL_LABELS={
 pedigree:'父・母父',drawWeight:'枠・斤量',rotation:'前走日付',
 personnel:'騎手・厩舎',body:'馬体形状',pastCorner:'過去4角'
};
const SOURCE_SIGNAL_LABELS={
 runningStyle:'脚質コード',surfaceAptitude:'当該芝ダート適性コード',
 distanceAptitude:'距離適性コード',goingAptitude:'重馬場適性コード',
 paceIndices:'テン・ペース・上がり・位置指数の4項目'
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
 if(!p||p.version!=='owner-ten-factor-contract-1'||p.policyVersion!=='research-6'||
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
   const provisionalWeight=TEN.reduce((sum,[k,,weight])=>
    sum+(['training','recent'].includes(k)&&h.grades[k]!=='未評価'?weight:0),0);
   const missing=TEN.filter(([k])=>h.grades[k]==='未評価').map(([k])=>k);
   const prioritized=TEN.filter(([k])=>missing.includes(k))
    .slice().sort((a,b)=>b[2]-a[2])
    .map(([key])=>key);
   // Compare the provisional arithmetic with the independent, already
   // validated original 2-factor grades. Never accept a browser score
   // that silently treats an ungraded item as zero.
   const gradeUnits={S:3,A:2,B:1,C:0};
   const active=actual.status==='provisional_draft';
   const breakdown=Object.fromEntries(['training','recent'].map(k=>[
    k,active&&h.grades[k]!=='未評価'
     ?gradeUnits[h.grades[k]]*(k==='training'?10:1):null
   ]));
   const scoreReady=Object.values(breakdown).every(v=>v!==null);
   const earned=scoreReady?breakdown.training+breakdown.recent:null;
   if(!h.provisionalBreakdown||
      Object.keys(h.provisionalBreakdown).length!==2||
      h.provisionalBreakdown.training!==breakdown.training||
      h.provisionalBreakdown.recent!==breakdown.recent||
      h.provisionalScoreReady!==scoreReady||
      h.provisionalPoints33!==earned||
      h.provisionalMaxPoints!==33)
    throw Error('調教・近走の暫定自動採点に不整合');
   if(h.provisionalFactorCount!==count||h.missing.length!==10-count||
      h.missing.join('|')!==missing.join('|')||
      h.provisionalWeightCapacity!==provisionalWeight||
      h.unassessedWeightCapacity!==100-provisionalWeight||
      h.verifiedWeightCapacity!==0||
      !Array.isArray(h.priorityMissingFactors)||
      h.priorityMissingFactors.join('|')!==prioritized.join('|'))
     throw Error('10項目の配点資料カバー率が不一致');
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
// Optional live four-source drill-down. Each value is source column presence,
// not a skill grade. Do not infer JRA starters, actual bodyweight, suitability,
// prediction readiness or a 10-factor score. Legacy cached previews without
// this optional report retain the previous UI.
// Across all eligible, prestart draft horses, count SOURCE COLUMN PRESENCE
// only. A missing optional report, a held race and a 0R programme must NEVER
// appear as 0/0 graded horses. No paid reads, source rows, rankings, odds,
// tickets, provisional score or runner IDs leave this text-only summary.
function evidenceGapSummary(data, sourceByRace){
 const report=data.runnerSourceEvidence;
 if(!data.raceCount)return '番組0R：資料を集計できません。開催なしとは断定しません。正式10項目の採点は未完了。';
 if(!report||report.raceCount===0)
  return '馬別の追加資料は照合保留（未取得ではなく、状況未確認）。正式10項目の採点は未完了。';
 const totals={pedigree:0,draw_weight:0,jockey_stable:0,rotation:0,past_corner:0};
 let horses=0,events=0;
 for(const row of report.races){
  if(row.status!=='observed')continue;
  const byHorse=sourceByRace.get(row.track+'|'+row.race);
  if(!byHorse||byHorse.size!==row.runners.length)
   return '馬別資料の集計を保留。正式10項目の採点は未完了。';
  events++;
  for(const observed of byHorse.values()){
   horses++;
   for(const key of Object.keys(totals)){
    if(observed[key])totals[key]++;
   }
  }
 }
 if(!horses||!events)
  return '発走前下書きの馬別追加資料は未照合。正式10項目の採点は未完了。';
 const fields=[
  ['past_corner','展開17点の参考：過去4角'],
  ['jockey_stable','騎手・厩舎10点：名前の記録'],
  ['pedigree','血統6点：父・母父'],
  ['draw_weight','枠・斤量3点：両方の記録'],
  ['rotation','ローテ1点：前走日の記録']
 ];
 const out=['【正式10項目の資料ギャップ】',
  '発走前の下書き：'+events+'R／馬別資料の照合：'+horses+'頭',
  '下の数は資料がある頭数です。得点・勝率・S/A/B/Cではありません。'];
 for(const [key,label] of fields){
  out.push(label+' '+totals[key]+'/'+horses+'頭');
 }
 out.push('コース・距離17点：今回の馬別適性を独立に検証できていません。');
 out.push('馬場12点：今回の馬別適性を独立に検証できていません。');
 out.push('当日馬体重1点：今回の実測値と前走比を確認できていません。');
 out.push('調教30点・近走3点：現時点は仮評価（正式な採点ではありません）。');
 out.push('JRA出走馬・取消・発走時刻：独立照合が未完成。');
 out.push('正式総合100点：未作成。既存3連単への変更0件・JRDB追加照会0回。');
 if(report.unavailableRaceCount)
  out.push('追加資料を照合できなかったR：'+report.unavailableRaceCount+
   'R（資料0頭とみなさず、別途確認）。');
 return out.join('\n');
}
// Same-snapshot, per-factor coverage: a diagnostic, NEVER an ability score.
// Use already validated owner data, never trigger a paid source fetch.
function tenEvidenceMatrix(data,sourceByRace){
 const p=data.tenFactorPreview;
 const output=['【10項目・100点｜実データ確認表】',
  '※「仮評価」「記録あり」は正式な能力得点・適性・勝率ではありません。'];
 if(!data.raceCount){
  output.push('番組0R：未集計。開催なしとは判定しません。');
  output.push('正式採点0/10｜JRA公式独立照合は未完了｜追加JRDB照会0回');
  return output.join('\n');
 }
 const passport=data.sourcePassport?.sourceAuditAvailable
  ?data.sourcePassport.races:null;
 const rows=passport||[];
 const draftRaces=p.races.filter(r=>r.runnerCount>0);
 const provisionalDenominator=draftRaces.reduce((s,r)=>s+r.runnerCount,0);
 const provisionalCount={training:0,recent:0};
 for(const race of draftRaces){
  for(const horse of race.horses)
   for(const key of ['training','recent'])
    provisionalCount[key]+=Number(horse.grades[key]!=='未評価');
 }
 const material={pace:0,pedigree:0,draw_weight:0,jockey_stable:0,rotation:0};
 let materialDenominator=0,observedRaces=0;
 if(data.runnerSourceEvidence){
  for(const row of data.runnerSourceEvidence.races){
   if(row.status!=='observed')continue;
   const byNumber=sourceByRace.get(row.track+'|'+row.race);
   if(!byNumber)throw Error('同一レース資料照合の不一致');
   observedRaces++;
   materialDenominator+=byNumber.size;
   for(const flags of byNumber.values()){
    material.pace+=Number(flags.past_corner);
    for(const key of ['pedigree','draw_weight','jockey_stable','rotation'])
     material[key]+=Number(flags[key]);
   }
  }
 }
 const materialLabel=(key,detail)=>{
  if(!materialDenominator)return '元資料の馬別記録は未集計（取得なしを0頭扱いしない）';
  return detail+' '+material[key]+'/'+materialDenominator+
   '頭（照合済み'+observedRaces+'Rのみ。未確認Rは別）';
 };
 const sourceRaces=rows.length||data.raceCount;
 const programCount=(key)=>
  passport?rows.filter(r=>r[key]).length+'/'+sourceRaces+
   'R（番組・開催場の資料。馬別適性は未評価）':
   '番組・開催場の資料は未集計';
 const summaries={
  training:provisionalDenominator
   ?'調教の仮ランク '+provisionalCount.training+'/'+provisionalDenominator+'頭'
   :'仮ランク未集計（発走前対象馬なし）',
  recent:provisionalDenominator
   ?'近走の仮ランク '+provisionalCount.recent+'/'+provisionalDenominator+'頭'
   :'仮ランク未集計（発走前対象馬なし）',
  course_distance:programCount('courseContextPresent'),
  pace:materialLabel('pace','過去4角位置の記録')+'。今回の展開は未評価',
  ground:programCount('goingContextPresent'),
  pedigree:materialLabel('pedigree','父・母父の記録'),
  draw_weight:materialLabel('draw_weight','枠・斤量の記録'),
  jockey_stable:materialLabel('jockey_stable','騎手・厩舎名の記録'),
  rotation:materialLabel('rotation','前走間隔の記録'),
  body_condition:'当日馬体重の実測値・前走比は未検証（馬体形状コードは代用不可）'
 };
 for(const [key,label,weight] of TEN)
  output.push(label+' '+weight+'点｜'+summaries[key]+'｜正式採点は未評価');
 // Data-readiness priorities are derived from the already validated
 // SAME-snapshot counters. They never become earned points or grades.
 const gaps=[];
 const addGap=(key,covered,total,unit)=>{
  if(!Number.isInteger(covered)||!Number.isInteger(total)||
     total<=0||covered<0||covered>total)throw Error('項目別資料件数の不整合');
  if(covered===total)return;
  const entry=TEN.find(([name])=>name===key);
  if(!entry)throw Error('不明な評価項目');
  gaps.push({key,label:entry[1],weight:entry[2],missing:total-covered,
   total,unit});
 };
 if(provisionalDenominator){
  for(const key of ['training','recent'])
   addGap(key,provisionalCount[key],provisionalDenominator,'頭');
 }
 if(passport){
  addGap('course_distance',rows.filter(r=>r.courseContextPresent).length,
   sourceRaces,'R');
  addGap('ground',rows.filter(r=>r.goingContextPresent).length,sourceRaces,'R');
 }
 if(materialDenominator){
  for(const key of ['pace','pedigree','draw_weight','jockey_stable','rotation'])
   addGap(key,material[key],materialDenominator,'頭');
 }
 gaps.sort((a,b)=>b.weight-a.weight||
  b.missing/b.total-a.missing/a.total||a.label.localeCompare(b.label,'ja'));
 output.push('【次に確認する資料（配点が大きい順・能力得点ではない）】');
 if(gaps.length){
  for(const gap of gaps.slice(0,3))
   output.push(gap.label+' '+gap.weight+'点：記録未確認 '+
    gap.missing+'/'+gap.total+gap.unit+'（観測対象内のみ）');
  if(gaps.length>3)output.push('ほか '+(gaps.length-3)+
   '項目にも記録未確認あり。上の10項目の内訳を確認。');
 }else if(!provisionalDenominator&&!materialDenominator){
  output.push('馬別の観測資料は未集計。未取得を0頭・0点扱いしません。');
 }else{
  output.push('今回の観測対象内に明確な件数不足はありません。ただし、資料ありは正式採点済みを意味しません。');
 }
 if(!materialDenominator)
  output.push('血統・枠斤量・騎手厩舎・ローテ・過去4角：馬別資料の確認は保留中。');
 output.push('別途必須：当日馬体重の実測確認・JRA公式4点の独立照合・10項目の評価基準検証。');
 output.push('正式採点0/10｜JRA公式の出走馬・取消・馬場・発走時刻は未照合');
 output.push('既存買い目・署名済み発走前記録は変更なし｜追加JRDB照会0回');
 return output.join('\n');
}
function validatedRunnerSourceEvidence(data){
 const report=data.runnerSourceEvidence, result=new Map();
 if(report===undefined)return result;
 const keys=['pedigree','draw_weight','jockey_stable','rotation','past_corner'];
 if(!report||report.version!=='owner-runner-source-hints-1'||
    report.verifiedNewFactorCount!==0||report.officialJraVerified!==false||
    report.overallPredictionReady!==false||report.bettingReady!==false||
    report.researchOnly!==true||report.privateOwnerOnly!==true||
    report.newProviderRequests!==0||report.rawSourceRowsIncluded!==false||
    !Array.isArray(report.factorFields)||report.factorFields.join('|')!==keys.join('|')||
    !Array.isArray(report.races)||report.raceCount!==report.races.length||
    !Number.isInteger(report.observedRaceCount)||
    !Number.isInteger(report.unavailableRaceCount))
   throw Error('追加10項目資料の形式不正');
 if(report.raceCount===0){
  if(report.observedRaceCount!==0||report.unavailableRaceCount!==0)
   throw Error('資料欠損の集計不一致');
  return result;
 }
 if(report.raceCount!==data.raceCount)throw Error('追加資料のレース数不一致');
 const drafts=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 let observed=0, unavailable=0;
 for(const row of report.races){
  const id=row?.track+'|'+row?.race,original=drafts.get(id);
  if(!original||result.has(id)||!['held','observed','unavailable'].includes(row.status)||
     !Array.isArray(row.runners)||row.runners.length>18)
   throw Error('追加資料の競馬場照合不一致');
  if(row.status==='held'){
   if(original.status!=='hold'||row.runners.length)
    throw Error('見送りRに馬番資料を再生成できません');
   result.set(id,new Map());
   continue;
  }
  if(row.status==='unavailable'){
   if(row.runners.length)throw Error('未取得馬番資料を拒否');
   unavailable++;
   result.set(id,new Map());
   continue;
  }
  observed++;
  if(original.status!=='provisional_draft'||row.runners.length!==original.runners.length)
   throw Error('未検証の馬番資料を拒否');
  const horseNumbers=new Set(original.runners.map(h=>h.number)),byHorse=new Map();
  for(const horse of row.runners){
   if(!horse||!horseNumbers.has(horse.number)||byHorse.has(horse.number)||
      horse.verifiedFactorCount!==0||
      !horse.observed||Object.keys(horse.observed).length!==keys.length||
      keys.some(key=>typeof horse.observed[key]!=='boolean'))
    throw Error('馬ごとの10項目資料不一致');
   byHorse.set(horse.number,horse.observed);
  }
  result.set(id,byHorse);
 }
 if(result.size!==drafts.size||report.observedRaceCount!==observed||
    report.unavailableRaceCount!==unavailable)
  throw Error('追加10項目資料の件数不一致');
 return result;
}
function validateContext(data){
 const ctx=data.raceContext;
 if(!ctx||ctx.version!=='race-context-1'||ctx.date!==data.date||
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
    a.policyVersion!=='research-6'||
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
     data.sourceMaterials.races.length)
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
  if(src){
   if(row.sourceMaterialsObserved!==true||
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
// A separately guarded, read-only view of genuine two-index comparison.
 // No third-party paid index is copied into browser storage or returned.
function validateWorkoutIndexOrder(data,day){
 const study=data.workoutIndexOrder;
 if(study===undefined)return new Map(); // old response version
 if(!study||study.version!=='owner-workout-index-order-1'||
    study.date!==day||study.raceCount!==data.raceCount||
    study.researchOnly!==true||study.privateOwnerOnly!==true||
    study.scoreReady!==false||study.officialJraVerified!==false||
    study.predictionReady!==false||study.bettingReady!==false||
    study.sourcePublicationTimeVerified!==false||
    study.rawIndexesIncluded!==false||
    study.ticketsIssued!==0||study.newProviderRequests!==0||
    study.changesExistingReceipts!==false||
    !Array.isArray(study.races)||study.studiedRaceCount!==study.races.length||
    study.races.length>data.raceCount)
   throw Error('調教指数内比較の形式が不正です');
 const source=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 const out=new Map();
 for(const row of study.races){
  const id=row?.track+'|'+row?.race,base=source.get(id);
  if(!base||out.has(id)||!Array.isArray(row.runners)||
     !Number.isInteger(row.runnerCount)||row.runnerCount!==base.runners.length||
     row.runnerCount!==row.runners.length||row.runnerCount<2||
     row.runnerCount>18||
     row.rankingScope!=='workout_index_within_band_only'||
     !Number.isInteger(row.differentIndexPairsWithinBand)||
     !Number.isInteger(row.exactTiePairsWithinBand)||
     row.differentIndexPairsWithinBand<0||row.exactTiePairsWithinBand<0||
     row.differentIndexPairsWithinBand+row.exactTiePairsWithinBand>153)
    throw Error('調教指数比較のレース照合に不一致');
  const old=new Map(base.runners.map(h=>[h.number,h])),used=new Set();
  const bandOrder={S:0,A:1,B:2,C:3};
  let previousBand=-1,previousRank=0;
  for(const h of row.runners){
   if(!h||!Number.isInteger(h.number)||used.has(h.number)||
      !Object.hasOwn(bandOrder,h.trainingBand)||
      !Number.isInteger(h.withinBandRank)||
      h.withinBandRank<1||h.withinBandRank>row.runnerCount||
      old.get(h.number)?.training!==h.trainingBand)
    throw Error('調教指数比較の馬番照合に不一致');
   const order=bandOrder[h.trainingBand];
   if(order<previousBand||
      (order===previousBand&&h.withinBandRank<previousRank))
    throw Error('調教指数比較の順序に不一致');
   previousBand=order;previousRank=h.withinBandRank;
   used.add(h.number);
  }
  if(used.size!==base.runners.length)
   throw Error('調教指数比較に未照合の馬あり');
  out.set(id,row);
 }
 return out;
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
  !['observed','partial','unavailable'].includes(data.sourceMaterials.status)||
  data.sourceMaterials.officialJraVerified!==false||
  data.sourceMaterials.gradedNewFactors!==0||
  !Array.isArray(data.sourceMaterials.races)||
  (data.sourceMaterials.status==='unavailable'&&
   (data.sourceMaterials.observedFactorSlots!==0||
    data.sourceMaterials.races.length!==0))||
  (data.sourceMaterials.status==='observed'&&
   (data.sourceMaterials.observedFactorSlots!==8||
    data.sourceMaterials.races.length!==data.raceCount))||
  (data.sourceMaterials.status==='partial'&&
   (data.sourceMaterials.observedFactorSlots!==8||
    data.sourceMaterials.races.length<1||
    data.sourceMaterials.races.length>data.raceCount))||
  ![1,4].includes(data.sourceReadCount)||
  (data.sourceReadCount===1&&
   (data.raceCount!==0||data.sourceMaterials.status!=='unavailable'))||
  data.unitYen!==100||
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
     row.counts[k]>row.runnerCount)||
   (row.sourceSignals!==undefined&&(
     !row.sourceSignals||typeof row.sourceSignals!=='object'||
     Array.isArray(row.sourceSignals)||
     Object.keys(row.sourceSignals).length!==5||
     Object.keys(SOURCE_SIGNAL_LABELS).some(k=>
       !Number.isInteger(row.sourceSignals[k])||
       row.sourceSignals[k]<0||row.sourceSignals[k]>row.runnerCount)))||
   materials.has(row.track+'|'+row.race))
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
   r.points!==r.tickets.length||r.points>48||r.amountYen!==r.points*100)
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
    !validRecentObserved(h.recentObserved)||
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
      (Object.hasOwn(r,'reviewStage')&&
       (r.reason!=='missing_research'||
        !Object.hasOwn(REVIEW_STAGES,r.reviewStage)))||
      (r.reason==='invalid_two_factor'&&
       (!Object.hasOwn(RUNNER_ISSUES,r.validationIssue)||r.runners.length!==0)))
    throw Error('見送り理由が不正です');
  }else{
   if(r.reason!=='two_factor_only'||r.first.length<1||r.first.length>3||
    r.second.length<=r.first.length||r.second.length>8||
    r.third.length<r.second.length||r.third.length>12||!r.points)
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
 validateWorkoutIndexOrder(data,day);
 return data;
}
function validRecentObserved(v){
 if(v===undefined||v===null)return true; // older snapshots
 if(!v||typeof v!=='object'||Array.isArray(v))return false;
 const keys=['datedRuns','completedRuns','topThreeObserved',
  'fourthCornerObserved','late3fObserved'];
 if(Object.keys(v).length!==keys.length||keys.some(k=>!Object.hasOwn(v,k)))
  return false;
 const [dated,completed,top,corner,late]=keys.map(k=>v[k]);
 return [dated,completed,top,corner,late].every(Number.isInteger)&&
  dated>=0&&dated<=5&&completed>=0&&completed<=dated&&
  top>=0&&top<=Math.min(3,completed)&&
  corner>=0&&corner<=Math.min(3,dated)&&
  late>=0&&late<=Math.min(3,dated);
}
function oneRunObservation(h){
 const o=h.recentObserved;
 if(!o)return '';
 // One observed and finish-verified race now permits only the 3-point
 // recent research hypothesis. Explicitly warn about sample size on
 // every affected runner; no fake second run or formal grade.
 if(o.datedRuns===1&&o.completedRuns===1&&
    ['S','A','B','C'].includes(h.recent))
  return '【近走1走のみ】確認済みの1走から近走3点分の仮ランクを算出。'+
   '比較材料が少なく、正式100点評価・勝率・JRA公式照合ではありません。';
 if(h.recent!=='未評価'||!o.datedRuns)return '';
 return 'JRDBで確認できた過去走 '+o.datedRuns+'走／着順確認 '+
  o.completedRuns+'走'+
  (o.completedRuns?'／確認できた直近最大3走で3着以内 '+
   o.topThreeObserved+'回':'（着順未確認）')+
  '。近走ランクは未評価のまま、能力得点・買い目には反映しません。';
}
function boundedTwoFactorResearchRange(h){
 // /99 is the scale of provisional ordinal TRAINING (30x0..3) plus
 // RECENT (3x0..3), NOT a score out of the formal 100-point scale.
 // An absent beta grade occupies its full possible contribution:
 // never impute it as C, zero, or a low-ranked horse.
 const ordinal={S:3,A:2,B:1,C:0};
 const knownTraining=Object.hasOwn(ordinal,h.training);
 const knownRecent=Object.hasOwn(ordinal,h.recent);
 if(knownTraining&&knownRecent)return '';
 const low=(knownTraining?ordinal[h.training]*30:0)+
  (knownRecent?ordinal[h.recent]*3:0);
 const high=low+(knownTraining?0:90)+(knownRecent?0:9);
 return '2項目研究の推定可能範囲 '+low+'〜'+high+
  '/99（未評価分は0点扱いせず、最良〜最低の可能性を残す）';
}
function runnerView(h,index){
 const p=dom('div',undefined,'runner');
 p.append(dom('span',h.number+'番','number'),
  dom('span',h.comparisonRank===null?'未評価':'仮'+h.comparisonRank+'位','rank'),
  dom('span','調教 '+h.training,'grade '+h.training),
  dom('span','近走 '+h.recent,'grade '+h.recent),
  dom('span',POS[h.pastFourthCorner]+' ※脚質確定ではない','notes'));
 const range=boundedTwoFactorResearchRange(h);
 if(range)p.append(dom('span',range,'notes'));
 const observed=oneRunObservation(h);
 if(observed)p.append(dom('span',observed,'notes'));
 if(missingText(h))p.append(dom('span',missingText(h),'notes'));
 return p;
}
const AUTO_FACTOR_REASONS=Object.freeze({
 pace_fast:'先行型が半数以上：差し・好位差しを加点する仮説',
 pace_slow:'先行型が4分の1以下：前に行く馬を加点する仮説',
 pace_balanced:'先行型の割合が中間：好位・自在性を加点する仮説',
 styles_missing:'脚質未確認の馬がいるため展開は未採点',
 staff_relative_midrank:'騎手指数・厩舎指数のレース内順位を等分（同値は同点）',
 staff_missing:'騎手・厩舎指数が全頭分そろわず比較保留',
 rotation_14_56:'前走から14〜56日：間隔を80/100とする仮説',
 rotation_7_90:'前走から7〜90日（14〜56日以外）：65/100とする仮説',
 rotation_outside:'前走から7日未満または90日超：50/100とする仮説',
 previous_date_missing:'前走日が未確認。新馬も0点にしません',
 course_context_missing:'芝・ダートまたは距離の情報不足。障害戦は研究対象外',
 distance_code_missing:'距離適性コード不明のため未評価（0点扱いしない）',
 distance_only_versatile:'万能型の距離適性コード。コース実績は未反映',
 distance_only_match:'距離帯と適性コードが一致する仮説。コース実績は未反映',
 distance_only_adjacent:'隣接する距離帯の仮説。コース実績は未反映',
 distance_only_far:'距離帯に差がある仮説。コース実績は未反映',
 ground_going_unknown:'開催馬場が未取得・不一致。推測で点を入れません',
 ground_source_after_cutoff:'馬場の更新時刻が予想固定後。未来の情報を参考採点に使いません',
 ground_good_not_scored:'良馬場は重馬場適性コードだけでは評価できません',
 ground_mudder_code_missing:'重馬場適性コードが不明。0点扱いしません',
 ground_soft_mudder_1:'JRDB重馬場適性「得意」。軟らかい馬場のみの参考仮説',
 ground_soft_mudder_2:'JRDB重馬場適性「普通」。軟らかい馬場のみの参考仮説',
 ground_soft_mudder_3:'JRDB重馬場適性「苦手」。軟らかい馬場のみの参考仮説'
});
function automaticFactorRace(data,day,race){
 const a=data.automaticFactorScores;
 if(!a)return null; // Older server/cached responses remain usable.
 if(a.version!=='owner-automatic-factor-scores-3'||a.policyVersion!=='research-6'||
    a.date!==day.replaceAll('-','')||a.maximumPoints!==57||
    !Array.isArray(a.factorKeys)||a.factorKeys.join('|')!=='pace|jockey_stable|rotation|course_distance|ground'||
    a.modelCalibrated!==false||a.officialJraVerified!==false||
    a.overallPredictionReady!==false||a.newProviderRequests!==0||
    !Array.isArray(a.races)||a.races.length>120||
    !Number.isFinite(Date.parse(a.capturedAt)))return null;
 const rows=a.races.filter(x=>x.track===race.track&&x.race===race.race);
 if(rows.length!==1)return null;
 const row=rows[0];
 if(row.status!=='scored'||row.reason!==null||row.postTime!==race.postTime||
    !Array.isArray(row.horses)||row.horses.length<4||row.horses.length>18||
    !Array.isArray(race.runners)||race.runners.length!==row.horses.length)
  return null;
 // A five-factor research score must reference the exact same runner numbers
 // as the already validated two-factor day snapshot, not just the same R.
 const sourceNumbers=new Set();
 for(const horse of race.runners){
  if(!horse||!Number.isInteger(horse.number)||horse.number<1||
     horse.number>18||sourceNumbers.has(horse.number))return null;
  sourceNumbers.add(horse.number);
 }
 const seen=new Set();
 for(const h of row.horses){
  if(!Number.isInteger(h.number)||h.number<1||h.number>18||seen.has(h.number)||
     !h.factors||Object.keys(h.factors).sort().join('|')!=='course_distance|ground|jockey_stable|pace|rotation')return null;
  seen.add(h.number);
  for(const [key,weight] of [['course_distance',17],['ground',12],['pace',17],['jockey_stable',10],['rotation',1]]){
   const v=h.factors[key];
   if(!v||v.weight!==weight||!Object.hasOwn(AUTO_FACTOR_REASONS,v.reason))return null;
   if(v.score===null){if(v.points!==null||v.grade!=='未評価')return null;}
   else{
    if(!Number.isFinite(v.score)||v.score<0||v.score>100||
       !Number.isFinite(v.points)||Math.abs(v.points-v.score*weight/100)>.000051||
       v.grade!==(v.score>=85?'S':v.score>=70?'A':v.score>=55?'B':'C'))return null;
   }
  }
 }
 if(seen.size!==sourceNumbers.size||
    [...seen].some(number=>!sourceNumbers.has(number)))return null;
 return row;
}
function renderAutomaticFactors(row){
 const panel=dom('details',undefined,'automatic-factors');
 panel.append(dom('summary','自動採点：距離適性・馬場適性・展開・騎手厩舎・ローテ（最大57点分）'));
 panel.append(dom('p','既存のJRDB資料から算出。採点ルールは検証前で、総合100点・勝率ではありません。'+
  '距離はコース実績を含まず、馬場は稍重以上でのみ参考採点。買い目には未反映です。','muted'));
 for(const h of row.horses){
  const horse=dom('details',undefined,'ten-horse');
  const brief=[['course_distance','距離'],['ground','馬場'],['pace','展開'],['jockey_stable','騎手厩舎'],['rotation','ローテ']]
   .map(([key,label])=>label+':'+(h.factors[key].points===null?'未評価':
    h.factors[key].points.toFixed(2)+'点')).join('｜');
  horse.append(dom('summary',h.number+'番｜'+brief));
  for(const [key,label] of [['course_distance','距離適性（コース未評価）'],['ground','重馬場適性（条件付き）'],['pace','展開・脚質'],['jockey_stable','騎手・厩舎'],['rotation','ローテ']]){
   const v=h.factors[key];
   horse.append(dom('p',label+'：'+(v.points===null?'未評価':
    v.points.toFixed(2)+'/'+v.weight+'点 '+v.grade+'（仮）'),v.grade==='未評価'?'muted':'grade '+v.grade));
   horse.append(dom('p',AUTO_FACTOR_REASONS[v.reason],'muted'));
  }
  panel.append(horse);
 }
 return panel;
}
function eligibleResearchFactorPanel(automatic,day,race,elapsed,changedLock){
 return Boolean(automatic&&!elapsed&&!changedLock&&!draftExpiredOnDevice(day,race.postTime));
}
// Optional same-day, server-derived 33+57 research subtotal. Reject forged,
// stale, missing or different-runner data. This cannot promote any runner to
// a verified full-ten 100pt grade, nor change sealed 3連単 tickets.
function sevenFactorRace(data,day,race,automatic,sourceMaterials){
 const p=data.sevenFactorCoverage;
 const held=race.status==='hold';
 if(held&&(!['missing_factors','ambiguous_equal_grade_boundary'].includes(race.reason)||
    !Array.isArray(race.tickets)||race.tickets.length!==0||
    race.points!==0||race.amountYen!==0))return null;
 if(!p||!automatic||!(race.status==='provisional_draft'||held)||
    p.version!=='owner-seven-factor-coverage-1'||p.policyVersion!=='research-6'||
    p.date!==day.replaceAll('-','')||p.raceCount!==data.raceCount||
    p.maximumPossibleAssessedWeight!==90||p.remainingUnmappedWeight!==10||
    (p.remainingFactorFieldsOnly!==undefined&&p.remainingFactorFieldsOnly!==true)||
    (p.racedayBodyWeightFromDayRead!==undefined&&p.racedayBodyWeightFromDayRead!==false)||
    p.modelCalibrated!==false||p.researchOnly!==true||
    p.privateOwnerOnly!==true||p.officialJraVerified!==false||
    p.overallPredictionReady!==false||p.publishable!==false||
    p.bettingReady!==false||p.autoPurchase!==false||p.ticketsIssued!==0||
    p.changesExistingDrafts!==false||p.changesExistingReceipts!==false||
    p.newProviderRequests!==0||!Array.isArray(p.races)||
    p.races.length!==data.raceCount||
    (held&&(p.heldCoverageNeverRanksOrBets!==true||
      !Number.isInteger(p.heldPartialRaceCount))))return null;
 const rows=p.races.filter(r=>r.track===race.track&&r.race===race.race);
 if(rows.length!==1||rows[0].status!==(held?'partial_held':'partial')||
    (held&&rows[0].heldResearchNeverFormsTickets!==true)||
    !Array.isArray(rows[0].horses)||
    rows[0].horses.length!==race.runners.length)return null;
 const ten=data.tenFactorPreview.races.find(r=>
  r.track===race.track&&r.race===race.race);
 if(!ten||ten.horses.length!==race.runners.length)return null;
 const source=new Map(race.runners.map(r=>[r.number,r]));
 const previews=new Map(ten.horses.map(r=>[r.number,r]));
 const optional=new Map(automatic.horses.map(r=>[r.number,r]));
 const seen=new Set(),out=new Map();
 const weights={course_distance:17,ground:12,pace:17,jockey_stable:10,rotation:1,
  pedigree:6,draw_weight:3,body_condition:1};
 const ordinal=['course_distance','ground','pace','jockey_stable','rotation'];
 const allMissing=['pedigree','draw_weight','body_condition'];
 for(const h of rows[0].horses){
  if(!h||!Number.isInteger(h.number)||seen.has(h.number)||
     !source.has(h.number)||!previews.has(h.number)||!optional.has(h.number)||
     !Number.isFinite(h.researchSubtotal)||h.researchSubtotal<0||
     !Number.isInteger(h.assessedWeight)||!Number.isInteger(h.unassessedWeight)||
     h.assessedWeight+h.unassessedWeight!==100||
     h.assessedWeight<(held?30:33)||h.assessedWeight>90||
     h.unassessedWeight<10||h.overallGrade!=='未評価'||
     h.finalScore100!==null||h.overallRank!==null||
     !Array.isArray(h.unassessedFactors))return null;
  seen.add(h.number);
  const prior=previews.get(h.number),current=optional.get(h.number);
  const coreGrades={S:3,A:2,B:1,C:0},coreWeights={training:30,recent:3};
  if(!prior||!prior.grades||!prior.provisionalBreakdown)return null;
  let subtotal=0,capacity=0;
  const missing=allMissing.slice();
  for(const key of ['training','recent']){
   const grade=prior.grades[key],fromRace=source.get(h.number)?.[key];
   if(grade!==fromRace)return null;
   if(grade==='未評価'){
    if(!held)return null;
    missing.push(key);
   }else if(Object.hasOwn(coreGrades,grade)){
    const points=coreGrades[grade]*coreWeights[key]/3;
    subtotal+=points;capacity+=coreWeights[key];
    if(!held&&prior.provisionalBreakdown[key]!==points)return null;
   }else return null;
   if(held&&prior.provisionalBreakdown[key]!==null)return null;
  }
  if(held){
   if(prior.provisionalScoreReady!==false||
      prior.provisionalPoints33!==null)return null;
  }else{
   if(prior.provisionalScoreReady!==true||
      !Number.isInteger(prior.provisionalPoints33)||
      prior.provisionalPoints33!==subtotal||capacity!==33)return null;
  }
  for(const key of ordinal){
   const factor=current.factors[key];
   if(factor.points===null)missing.push(key);
   else{capacity+=weights[key];subtotal+=factor.points;}
  }
  if(h.remainingMaterialReadiness!==undefined){
   const m=h.remainingMaterialReadiness;
   const flags=sourceMaterials?.get(h.number);
   const valid=['not_checked','fields_observed','fields_missing'];
   if(h.remainingEvidenceIsNotScore!==true||!m||
      Object.keys(m).sort().join('|')!=='body_condition|draw_weight|pedigree'||
      m.body_condition!=='raceday_bodyweight_not_available'||
      !valid.includes(m.pedigree)||!valid.includes(m.draw_weight))return null;
   for(const key of ['pedigree','draw_weight']){
    // A source-confirmed status must match the independently validated
    // availability flags (neither is a race-day fitness or grade claim).
    if(m[key]!=='not_checked'&&
       (!flags||m[key]!==(
        flags[key]?'fields_observed':'fields_missing')))return null;
   }
  }
  if(capacity!==h.assessedWeight||
     Math.abs(subtotal-h.researchSubtotal)>.0051||
     missing.length!==h.unassessedFactors.length||
     missing.some(key=>!h.unassessedFactors.includes(key))||
     h.unassessedWeight!==100-capacity||
     h.researchSubtotal>capacity+.0001)return null;
  out.set(h.number,h);
 }
 return seen.size===race.runners.length?out:null;
}
function renderTenHorse(h,source,automatic,seven){
 const additions=automatic?.factors||{};
 const scored=Object.entries(additions).filter(([,v])=>v.score!==null);
 const addedCapacity=scored.reduce((sum,[,v])=>sum+v.weight,0);
 const knownCapacity=h.provisionalWeightCapacity+addedCapacity;
 const details=dom('details',undefined,'ten-horse');
 details.append(dom('summary',h.number+'番：'+
  (h.provisionalScoreReady?'暫定 '+h.provisionalPoints33+'/33点':'暫定点 未算出')+
  '｜総合 未評価（評価項目'+knownCapacity+
  '点分／未評価'+(100-knownCapacity)+'点分）'+
  (seven?'｜仮小計 '+seven.researchSubtotal.toFixed(2)+'/'+
   seven.assessedWeight+'点枠':'')));
 const grid=dom('div',undefined,'ten-grid');
 for(const [key,label,weight] of TEN){
  const slot=dom('div',undefined,'ten-slot'),extra=additions[key],grade=extra?.grade||h.grades[key];
  slot.append(dom('span',label+' '+weight+'点'),
    dom('b',grade+(grade==='未評価'?'':'（仮）')+(extra?.points!=null?' '+extra.points.toFixed(2)+'点':''),grade==='未評価'?'':grade));
  grid.append(slot);
 }
 details.append(grid);
 details.append(dom('p',h.provisionalScoreReady
  ?'自動算出（仮説）：調教 '+h.provisionalBreakdown.training+
   '/30点 ＋ 近走 '+h.provisionalBreakdown.recent+
   '/3点 ＝ '+h.provisionalPoints33+
   '/33点。下記の追加採点も検証前です。正式な100点総合点・評価順位ではありません。'
  :'調教と近走の両方が揃わないか、見送り対象のため暫定得点を算出しません。'+
   '不足を0点に置き換えません。','muted'));
 if(source){
  const labels=[['pedigree','血統（父・母父）'],['draw_weight','枠・負担重量'],
   ['jockey_stable','騎手・厩舎の名前'],
   ['rotation','前走からの間隔'],['past_corner','過去4角位置']];
  details.append(dom('p','JRDB資料の有無：'+labels.map(([key,label])=>
   label+' '+(source[key]?'資料あり':'資料不足')).join('／')+
   '。資料ありは適性や能力の評価ではありません。馬体重当日値は未確認。','muted'));
 }else{
  details.append(dom('p','JRDBの馬別追加資料は照合保留。未評価項目は下記に表示します。','muted'));
 }
 if(automatic){
  for(const [key,v] of Object.entries(additions)){
   const label=TEN.find(([k])=>k===key)[1];
   details.append(dom('p',label+'：'+AUTO_FACTOR_REASONS[v.reason],'muted'));
  }
 }
 details.append(dom('p','未評価の項目（配点が大きい順）：'+
  h.priorityMissingFactors.filter(key=>!scored.some(([k])=>k===key)).map(key=>{
   const entry=TEN.find(([k])=>k===key);
   return entry[1]+entry[2]+'点';
  }).join('／')+'。ここでの点数は配点であり能力得点ではありません。','muted'));
 if(seven?.remainingMaterialReadiness){
  const m=seven.remainingMaterialReadiness;
  const named=value=>value==='fields_observed'?'資料あり（採点未検証）':
   value==='fields_missing'?'資料不足':'資料照合待ち';
  details.append(dom('p','【残り3項目・計10点の資料】血統6点：'+
   named(m.pedigree)+'／枠・斤量3点：'+named(m.draw_weight)+
   '／当日馬体重1点：未取得。資料があっても適性評価とは別で、'+
   '正式な配点10点分はすべて未評価です。','muted'));
 }
 if(seven)details.append(dom('p',
  '研究用の既知項目のみ合算：採点できた'+seven.assessedWeight+
  '点枠で小計 '+seven.researchSubtotal.toFixed(2)+'点。未評価 '+
  seven.unassessedWeight+'点枠は0点扱いせず、正式100点・S/A/B/C総合順位・'+
  '購入用予想には使いません。','muted'));
 return details;
}
// The real-day full-ten GATE is deliberately read-only: no trusted
// 10-factor grades, no independently certified JRA, no formal tickets.
// Validate every count and same-day race identity before presenting even
// this optional progress marker. Old provider snapshots remain compatible.
function formalGateShadowStatus(data,day){
 const p=data.formalGateShadow;
 const unavailable='正式10項目ゲート接続：この取得では未確認。正式採点・購入用買い目は未提供です。';
 if(!p)return unavailable;
 const count=k=>Number.isInteger(p[k])&&p[k]>=0&&p[k]<=36;
 const expected=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 const states=new Set(['blocked_missing_verified_evidence',
  'past_off_no_retroactive_gate','roster_or_schedule_unavailable']);
 if(p.version!=='owner-live-formal-shadow-1'||p.date!==day||
    p.raceCount!==data.raceCount||p.raceCount>36||
    !count('prestartFormalGateRuns')||!count('blockedMissingEvidenceRaces')||
    !count('pastOffRaces')||!count('rosterOrTimeUnavailableRaces')||
    p.prestartFormalGateRuns!==p.blockedMissingEvidenceRaces||
    p.blockedMissingEvidenceRaces+p.pastOffRaces+
     p.rosterOrTimeUnavailableRaces!==p.raceCount||
    p.verifiedFormalFactorCount!==0||p.verifiedTotalScoreCount!==0||
    p.formalTrifectaCount!==0||p.ticketsIssued!==0||
    p.officialJraVerified!==false||p.overallPredictionReady!==false||
    p.bettingReady!==false||p.newProviderRequests!==0||
    p.changesExistingDrafts!==false||p.changesExistingReceipts!==false||
    p.researchOnly!==true||p.privateOwnerOnly!==true||
    !Array.isArray(p.races)||p.races.length!==p.raceCount||
    expected.size!==data.raceCount)return unavailable;
 const seen=new Set(),totals=[0,0,0];
 for(const row of p.races){
  if(!row||typeof row.track!=='string'||!Number.isInteger(row.race)||
     !states.has(row.status)||row.formalScoreReady!==false||
     row.officialJraVerified!==false||row.bettingReady!==false)return unavailable;
  const key=row.track+'|'+row.race;
  if(!expected.has(key)||seen.has(key))return unavailable;
  seen.add(key);
  totals[row.status==='blocked_missing_verified_evidence'?0:
    row.status==='past_off_no_retroactive_gate'?1:2]++;
 }
 if(totals[0]!==p.blockedMissingEvidenceRaces||
    totals[1]!==p.pastOffRaces||
    totals[2]!==p.rosterOrTimeUnavailableRaces)return unavailable;
 return '正式10項目ゲートへの当日資料接続：発走前の照合試験 '+
  p.prestartFormalGateRuns+'/'+p.raceCount+'R／'+
  '検証済み10項目 0／正式採点 0R／正式3連単 0点。'+
  '発走済み '+p.pastOffRaces+'R・馬番/時刻不足 '+
  p.rosterOrTimeUnavailableRaces+'R。'+
  'JRDBの研究用S/A/B/Cは正式点に流用せず、JRA公式最終照合も未完了です。';
}
function renderTenHeader(p){
 const host=$('autoTenWeights');host.replaceChildren();
 for(const f of p.factors){
  const el=dom('div',undefined,'ten-weight');
  el.append(dom('span',f.label),dom('b',f.weight+'点'));host.append(el);
 }
 $('autoTenStatus').textContent='正式配点100点／10項目。調教30点＋近走3点は仮説ランクから自動採点（最大33点）、距離適性17・馬場12（稍重以上のみ）・展開17・騎手厩舎10・ローテ1は資料が揃った馬を追加参考採点。各馬の欄に得点と理由を表示します。総合100点の採点は未完成です。';
}
// Grades on a racecard are observations from the existing two-factor
// source, not a horse ranking or a predicted winner. Never substitute 0 for
// an unknown recent grade, infer official starters, or construct tickets.
function researchRaceSpotlight(race){
 const seen=(factor,grade)=>race.runners.filter(h=>h[factor]===grade)
  .map(h=>h.number+'番');
 const s=seen('training','S'),a=seen('training','A');
 const recentMissing=race.runners.filter(h=>h.recent==='未評価').length;
 const p=dom('div',undefined,'race-study');
 p.append(dom('span','調教S（仮）：'+(s.length?s.join('・'):'該当なし'),'workout-s'),
  dom('span','調教A（仮）：'+(a.length?a.join('・'):'該当なし'),'workout-a'),
  dom('span','近走未評価：'+recentMissing+'頭','study-neutral'));
 p.append(dom('span','※調教・近走の一部資料だけ。1着候補・正式順位ではありません。','study-neutral'));
 return p;
}
// Explain exact TWO-FACTOR ties without creating a third-place cut,
// inventing an S-to-C total, signing tickets, or reading new paid data.
// A race whose provisional off time elapsed is never reconstructed.
function heldTieGroups(race,day){
 if(race.status!=='hold'||race.reason!=='ambiguous_equal_grade_boundary'||
    draftExpiredOnDevice(day,race.postTime))return null;
 const weights={S:3,A:2,B:1,C:0},scores=new Map();
 if(!Array.isArray(race.runners)||race.runners.length<4)return null;
 for(const h of race.runners){
  if(!Object.hasOwn(weights,h.training)||!Object.hasOwn(weights,h.recent))
   return null;
  const score=30*weights[h.training]+3*weights[h.recent];
  if(h.weightedResearchPoints!==score)return null;
  if(!scores.has(score))scores.set(score,[]);
  scores.get(score).push(h.number);
 }
 const groups=[...scores].sort((a,b)=>b[0]-a[0])
  .map(([,numbers])=>numbers.slice().sort((a,b)=>a-b));
 if(!groups.some(numbers=>numbers.length>1))return null;
 const panel=dom('details',undefined,'tie-group-study');
 panel.append(dom('summary','同点の馬番グループを見る（買い目なし）'));
 for(const [i,numbers] of groups.entries()){
  panel.append(dom('p','仮比較第'+(i+1)+'群：'+
   numbers.map(n=>n+'番').join('・')+
   (numbers.length>1?'（同評価・群内順位なし）':''),'muted'));
 }
 panel.append(dom('p','調教30・近走3の未検証比較だけで同評価のため保留。'+
  '次はコース距離17・展開17・馬場12などの独立した根拠を確認。'+
  '勝ち馬順位・正式100点・3連単・購入を確定しません。','muted'));
 return panel;
}
function formation(r){
 const block=dom('div',undefined,'formation');
 const combinations=dom('details',undefined,'ticket-breakdown');
 combinations.append(
  dom('summary','全'+r.points+'点の組合せを見る'),
  dom('p',r.tickets.map(t=>t.join('→')).join(' / '),'ticket-list'));
 block.append(dom('strong','3連単・2項目だけの研究用自動下書き（1着'+r.first.length+'頭）'),
  dom('p','1着：'+r.first.join('・')+'番','picks'),
  dom('p','2着：'+r.second.join('・')+'番','picks'),
  dom('p','3着：'+r.third.join('・')+'番','picks'),
  dom('p',r.points+'点／1点100円なら'+r.amountYen.toLocaleString('ja-JP')+'円（仮計算・未購入）'),
  ...(r.first.length===2&&r.second.length===6&&r.third.length===6&&r.points===40
   ?[dom('p','同点を切らず、2着・3着とも6頭まで拡張した40点の研究例。'+
      '正式10項目の完成予想ではありません。','muted')]:[]),
  ...(r.first.length===1||r.points>40||r.second.length>6||r.third.length>9
   ?[dom('p','従来の40点方式では同点の境界が分けられず見送りだったR。'+
      '同点を馬番で切らず最大48点に収めた新しい発走前研究用下書きです。'+
      'JRA公式照合・正式100点採点・実購入ではありません。','muted')]:[]),
  combinations);
 return block;
}
function dayMaterialGaps(a){
 // A count of incomplete raw *fields*, not 10-factor grades. Do not
 // label unreceived source material as zero or invent JRA verification.
 const observed=a.races.filter(row=>row.sourceMaterialsObserved);
 if(!observed.length)
  return '追加資料の項目別不足は未集計（元資料が照合保留）。';
 const keys=[
  ['personnel','騎手・厩舎'],['pedigree','父・母父'],
  ['drawWeight','枠・斤量'],['rotation','ローテ'],
  ['pastCorner','過去4角の記録']
 ];
 const summary=keys.map(([key,label])=>{
  const misses=observed.filter(row=>row.programmeRunnerCount>0&&
   row.additionalFieldCounts[key]<row.programmeRunnerCount).length;
  return label+' '+misses+'R';
 }).join('／');
 return '元資料が全頭分そろわないR数（照合済み'+observed.length+'Rのみ）：'+
  summary+'。'+(observed.length===a.races.length?'':'残り'+
   (a.races.length-observed.length)+'Rの元資料は未確認。')+
  '当日馬体重は別の直前情報が必要。資料が揃っても能力評価・正式得点ではありません。';
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
  'R。正式採点0/10・JRA公式独立照合なし。買い目は変更しません。'+
  ' '+dayMaterialGaps(a);
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
// Group validated hold codes near the top without another paid read.
// A provisional off-time hold must not be misreported as missing data.
function holdBreakdownSummary(data){
 if(data.raceCount===0)
  return '【見送り内訳】番組0R。開催なし・資料未配信・取得不備は未確認。';
 if(data.holdCount===0)
  return '【見送り内訳】取得時点では0R（JRA公式の独立照合は未完了）。';
 const priority=[
  ['missing_factors','調教・近走不足'],
  ['ambiguous_equal_grade_boundary','候補同点'],
  ['after_provisional_off','暫定発走時刻経過']
 ];
 const known=new Set(priority.map(([key])=>key));
 const reasons=[
  ...priority.filter(([key])=>data.holdReasons[key]>0)
   .map(([key,label])=>label+' '+data.holdReasons[key]+'R'),
  ...Object.entries(data.holdReasons)
   .filter(([key,count])=>count>0&&!known.has(key))
   .sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]))
   .map(([key,count])=>(SHORT_HOLDS[key]||'要確認')+' '+count+'R')
 ];
 return '【見送り '+data.holdCount+'Rの内訳】'+reasons.join('／')+
  '。取得時点の暫定判定。発走時刻経過は資料不足ではありません。'+
  'JRA公式の出走・取消・発走時刻は未照合です。';
}
function morningStatus(data,day,localStatus,expiredCount=0,displayableCount=null){
 const iso=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 if(data.raceCount===0)
  return iso+'：JRDB番組0R。開催なし・提供前・資料不足の区別は未確認。予想は作成していません。固定済みの以前の研究記録は変更しません。';
 // Report only still-displayable prestart drafts. Receipts already signed
 // before off-time remain immutable but do not mean a new bet is available.
 const visible=displayableCount===null
  ?Math.max(0,data.draftCount-expiredCount):displayableCount;
 const blockedActive=Math.max(0,data.draftCount-expiredCount-visible);
 return iso+'：番組 '+data.raceCount+'R／発走前の研究用3連単下書き '+
  visible+'R／見送り '+data.holdCount+'R。'+
  (expiredCount?'暫定発走時刻経過で新案非表示 '+expiredCount+'R。':'')+
  (blockedActive?'固定済み記録との不一致・確認保留で新案非表示 '+blockedActive+'R。':'')+
  (visible===0
    ?(data.draftCount===0
      ?'資料不足などで全R見送り。買い目を無理に作りません。'
      :'暫定発走時刻経過のため新案は表示できません。')+
     '現在表示できる新しい3連単はありません。固定済みの履歴は下で確認できます。'
    :'下の「下書きのみ」から買い目を選べます。')+
  ' 発走前固定の状態：'+localStatus+
  ' 10項目本採点・JRA公式出走取消／発走時刻の独立確認は未完了。'+
  (data.archiveEnabled?'サーバー保存は別途検証が必要。':'サーバー永続保存は未設定。');
}
// Actionable readiness without adding a paid fetch or promoting any factor.
// Summarize the already-validated JRDB race slots only. A missing slot is
// NEVER asserted to be a JRA cancellation, absence or official schedule.
function programmeCoverage(data){
 const venues=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
 const slots=new Map();
 for(const race of data.races){
  if(!venues.includes(race.track)||!Number.isInteger(race.race)||
     race.race<1||race.race>12)throw Error('開催場・Rの照合不可');
  if(!slots.has(race.track))slots.set(race.track,new Set());
  if(slots.get(race.track).has(race.race))throw Error('重複開催R');
  slots.get(race.track).add(race.race);
 }
 if(data.raceCount===0)
  return 'JRDB番組：0R。開催なしとは断定できません。JRA公式の開催場・番組は未照合。';
 const rows=[...slots].sort((a,b)=>venues.indexOf(a[0])-venues.indexOf(b[0]))
  .map(([venue,seen])=>{
   const absent=Array.from({length:12},(_,i)=>i+1).filter(n=>!seen.has(n));
   return venue+' '+seen.size+'/12R'+(absent.length?
    '（1〜12R中未検出候補 '+absent.map(n=>n+'R').join('・')+'）':
    '（1〜12Rすべて検出）');
  });
 return 'JRDB番組：'+data.raceCount+'R／'+slots.size+'場。'+rows.join('／')+
  '。未検出は開催中止・取消を意味しません。JRA公式との全場・全R照合は未完成。';
}
// Show structural local receipt counts only, never claim HMAC verification,
// durable server storage, actual bets, or results.
// One-tap operational acceptance report. All values are counts from the
// ALREADY validated private snapshot, never JRDB source rows/horse numbers,
// names, betting combinations, signatures or official JRA conclusions.
// It makes NO fetch and can never reconstruct a post-start formation.
function dayAcceptanceReport(day){
 const out=['【本人用・取得と保存の確認】'];
 if(!/^20\d{6}$/.test(day)){
  return '開催日の指定が不正です。取得・保存の確認はできません。';
 }
 out.push('対象日：'+day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6));
 const saved=(()=>{
  try{return selectedReceiptsForVerification(day).length;}
  catch(_){return null;}
 })();
 out.push('端末の発走前固定研究記録：'+
  (saved===null?'照合保留（保存内容を変更せずバックアップを確認）':
   saved+'R（署名の真正性は別途確認）'));
 const report=latestDisplayedReport;
 if(!report||latestDisplayedDay!==day){
  out.push('今回のJRDB取得：未実施（再訪問時に保存履歴だけ表示している場合を含む）');
  out.push('番組・資料・3連単の新案：未取得。0Rと断定しません。');
 }else{
  // If any client state was replaced, fail closed instead of misreporting
  // accepted R counts. validate() does not perform any paid reads.
  try{validate(report,day);}
  catch(_){return '取得内容の照合ができません。固定記録を変更せず、以前の履歴を確認してください。';}
  out.push('JRDB番組：'+report.raceCount+'R（JRA公式開催場との照合は未実施）');
  out.push('今回のJRDB主要ソース照会：'+report.sourceReadCount+
   '回（'+(report.raceCount===0?'番組のみ':'番組・出走馬・調教・近走')+'）');
  out.push('研究用3連単下書き：'+report.draftCount+
   'R／見送り：'+report.holdCount+'R／署名付き記録の受信：'+
   report.researchReceiptCount+'R');
  if(report.raceCount===0)
   out.push('番組0Rは配信前・取得不備・開催なしを区別できません。');
  else{
   const courses=new Map();
   for(const row of report.races){
    const n=courses.get(row.track)||{found:0,drafts:0,holds:0};
    n.found++;
    if(row.status==='provisional_draft')n.drafts++;
    else n.holds++;
    courses.set(row.track,n);
   }
   const names=['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'];
   for(const [venue,n] of [...courses].sort((a,b)=>names.indexOf(a[0])-names.indexOf(b[0]))){
    out.push(venue+'：番組'+n.found+'/12R／下書き'+n.drafts+
     'R／見送り'+n.holds+'R');
   }
   if(report.holdCount){
    const causes=Object.entries(report.holdReasons).filter(([,n])=>n>0)
     .sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]))
     .map(([reason,n])=>(SHORT_HOLDS[reason]||'原因未確認')+' '+n+'R');
    out.push('見送りの主な理由：'+causes.join('／'));
   }
   out.push('追加資料の件数照合：'+report.sourceMaterials.status+
    '／当日馬場の取得状態：'+report.raceContext.conditionProviderFetchStatus);
  }
 }
 out.push('正式10項目の実証済み総合予想：未完成');
 out.push('JRA公式の出走・取消・馬場・発走時刻の独立照合：未完成');
 out.push('公式結果による確定回収率：未接続／自動購入なし');
 out.push('この集計は画面表示だけ。JRDB追加照会0回・買い目変更0件。');
 return out.join('\n');
}
$('autoAcceptanceCheck').onclick=()=>{
 const day=$('autoDay').value.replaceAll('-','');
 $('autoAcceptanceReport').textContent=dayAcceptanceReport(day);
};
// A successful HTTP response is not proof that the provider has current
// roster or cancellations. This is solely the iPhone receive clock for the
// currently displayed, validated same-day response, never a JRA timestamp.
function showSnapshotFreshness(){
 const day=$('autoDay').value.replaceAll('-','');
 if(!latestReadAtMs||!latestDisplayedReport||latestDisplayedDay!==day){
  $('autoSnapshotAge').textContent='JRDB受信時刻：未取得（この画面の新しい資料なし）。固定履歴とは別です。';
  return;
 }
 const elapsed=Math.max(0,new Date().valueOf()-latestReadAtMs);
 const minutes=Math.floor(elapsed/60000),old=elapsed>=15*60000;
 const jst=new Date(latestReadAtMs).toLocaleTimeString('ja-JP',{
  timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'
 });
 // A received EMPTY /tra response is not a completed card. Distinguish
 // it from an aged successful draft without creating a second paid call.
 if(latestDisplayedReport.raceCount===0){
  $('autoSnapshotAge').textContent=
   (old?'【番組0R・受信15分以上】':'【番組0R・配信状況未確認】')+
   'このiPhoneがJRDBの番組0R応答を '+jst+' に受信（約'+minutes+'分前）。'+
   '今週の資料がまだ配信されていない可能性があります。開催なしと断定できません。'+
   '提供元の更新時刻もJRA公式の独立照合も未確認。自動で有料再照会しません。';
  return;
 }
 $('autoSnapshotAge').textContent=
  (old?'【受信から15分以上・再確認推奨】':'【受信時刻の目安】')+
  'このiPhoneがJRDB応答を '+jst+' に受信（約'+minutes+'分前）。'+
  (old?'新しい取消・馬場・発走時刻を反映した保証はありません。':'これは提供元の最終更新時刻ではありません。')+
  'JRA公式の独立照合は未実施。再取得は「全場・全Rを再分析する」を明示的に押した場合だけ。';
}
function renderTrainingSourceDelivery(data,day){
 const target=$('autoTrainingFeedStatus'),p=data.trainingSourceDelivery;
 if(p===undefined){
  target.textContent='調教データの元レコード件数はこの応答では未取得。'+
   '「見送り」の中に資料未到着・照合未完了が混在する可能性があります。';
  return;
 }
 const fields=['entryRowsReturned','entriesMatchedDayProgramme',
  'trainingRowsReturned','trainingRowsKnownRace','trainingRowsCurrentRaceDate',
  'trainingRacesWithRows','trainingLinkedRunners',
  'trainingRunnersWithBothIndices','trainingRacesWithBothIndices',
  'trainingIdentityConflicts','trainingDuplicateRunnerRows',
  'recentRowsReturned','recentRowsCurrentRaceDate'];
 const states=new Set(['programme_not_returned','training_not_queried',
  'training_empty_response','training_no_current_race',
  'training_current_race_date_mismatch','training_no_runner_match',
  'training_indices_missing','training_identity_conflict',
  'training_partial_index_coverage','training_index_rows_present']);
 try{
  if(!p||p.version!=='owner-training-source-delivery-1'||
     p.date!==day||p.raceCount!==data.raceCount||
     p.sourceReadCount!==data.sourceReadCount||
     p.researchOnly!==true||p.privateOwnerOnly!==true||
     p.officialJraVerified!==false||p.scoreReady!==false||
     p.predictionReady!==false||p.bettingReady!==false||
     p.newProviderRequests!==0||p.retainedLicensedRows!==false||
     p.changesExistingDrafts!==false||p.changesExistingReceipts!==false||
     !states.has(p.status)||Object.keys(p).some(x=>x==='horses'||x==='racekey')||
     fields.some(key=>!Number.isInteger(p[key])||p[key]<0||p[key]>50000)||
     p.entriesMatchedDayProgramme>p.entryRowsReturned||
     p.trainingRowsKnownRace>p.trainingRowsReturned||
     p.trainingRowsCurrentRaceDate>p.trainingRowsKnownRace||
     p.trainingLinkedRunners>p.entriesMatchedDayProgramme||
     p.trainingRunnersWithBothIndices>p.trainingLinkedRunners||
     p.trainingRacesWithRows>p.raceCount||
     p.trainingRacesWithBothIndices>p.trainingRacesWithRows||
     p.recentRowsCurrentRaceDate>p.recentRowsReturned||
     p.trainingDuplicateRunnerRows>p.trainingRowsCurrentRaceDate||
     p.trainingIdentityConflicts>p.trainingRowsCurrentRaceDate||
     (p.status==='training_empty_response'&&p.trainingRowsReturned!==0)||
     (p.status==='training_no_current_race'&&
      !(p.trainingRowsReturned>0&&p.trainingRowsKnownRace===0))||
     (p.status==='training_current_race_date_mismatch'&&
      !(p.trainingRowsKnownRace>0&&p.trainingRowsCurrentRaceDate===0))||
     (p.status==='training_no_runner_match'&&
      !(p.trainingRowsCurrentRaceDate>0&&p.trainingLinkedRunners===0))||
     (p.status==='training_indices_missing'&&
      !(p.trainingLinkedRunners>0&&p.trainingRunnersWithBothIndices===0))||
     (p.status==='training_identity_conflict'&&
      p.trainingIdentityConflicts+p.trainingDuplicateRunnerRows===0)||
     (p.status==='training_partial_index_coverage'&&
      !(p.trainingRunnersWithBothIndices>0&&
       p.trainingRunnersWithBothIndices<p.entriesMatchedDayProgramme))||
     (p.status==='training_index_rows_present'&&
      !(p.trainingRunnersWithBothIndices>0&&
       p.trainingRunnersWithBothIndices===p.entriesMatchedDayProgramme))||
     (p.status==='programme_not_returned'&&data.raceCount!==0))
   throw Error('unverified_workout_delivery');
  const notes={
   programme_not_returned:'番組が0R。調教は照会していません。',
   training_not_queried:'調教ソースは未照会。',
   training_empty_response:'調教の応答が0行。未配信・取得時点・APIの事情など、原因は未特定。',
   training_no_current_race:'調教の応答はあるが選択日のレースキーと一致する行は0件。照合条件を要確認。',
   training_current_race_date_mismatch:'レースキーに該当する調教行はあるが開催日が一致せず、資料は未評価。',
   training_no_runner_match:'該当日の調教行はあるが出走馬と結び付く頭数が0。馬番・IDの照合を要確認。',
   training_indices_missing:'調教行は馬と照合できたが追切・仕上の両指数が揃った馬は0頭。',
   training_identity_conflict:'調教の馬番・IDに不整合または重複あり。安全のため再確認が必要。',
   training_partial_index_coverage:'調教指数が揃う馬と未評価の馬が混在。',
   training_index_rows_present:'確認できた出走馬は両方の調教指数が存在（正式採点ではない）。'
  };
  target.textContent='【調教元データの受信・照合】'+notes[p.status]+
   '｜出走馬 '+p.entriesMatchedDayProgramme+'頭／調教応答 '+p.trainingRowsReturned+
   '行／当日レースとの一致 '+p.trainingRowsCurrentRaceDate+
   '行／馬と照合 '+p.trainingLinkedRunners+
   '頭／両指数あり '+p.trainingRunnersWithBothIndices+
   '頭。近走応答 '+p.recentRowsReturned+'行。'+
   '元データが0行でも配信されていないとは断定できず、見送りは馬の弱さを意味しません。'+
   '再取得は上の「全場・全Rを再分析する」を自分で押したときだけ。';
 }catch(_){
  target.textContent='調教元データの診断を安全に検証できません。'+
   '予想・署名・買い目は変えず、再取得前に資料状況を確認してください。';
 }
}
// Fixed, source-safe /tka diagnostics; this is a reason for MISSING
// course going, never evidence of official JRA going or a 12pt grade.
const GOING_FAILURE_LABELS={
 provider_request_rejected:'APIが要求を受け付けず（400/422）',
 provider_auth:'認証失敗（401）',
 provider_entitlement:'契約・アクセス権限（403）',
 provider_endpoint_missing:'API経路が見つからず（404）',
 provider_timeout:'通信時間切れ（408）',
 provider_rate_limit:'API呼び出し制限（429）',
 provider_server_error:'提供元サーバーエラー（5xx）',
 provider_transport_or_decode:'通信・応答の読取に失敗',
 provider_response_too_large:'応答サイズ超過',
 provider_response_contract:'応答形式・要求日付などが不一致',
 provider_credentials_missing:'認証設定不足',
 provider_credentials_invalid:'認証形式不正',
 provider_base_unapproved:'接続先設定を確認',
 provider_disabled:'接続機能が無効',
 provider_other:'提供元エラーの詳細未分類',
 condition_timestamp_format:'更新日時の形式不正',
 going_code:'馬場コード不正',
 holding_key:'開催キー不正',
 venue_date_mismatch:'開催日・競馬場の不一致',
 duplicate_venue:'同じ開催場の重複',
 context_schema_other:'資料形式の不一致',
 context_missing_field:'必要項目が不足',
 context_type:'資料の値の型不正',
 context_value:'資料値の不正',
 context_other:'馬場資料の照合不可'
};
function goingFetchStatus(data){
 const ctx=data.raceContext,code=ctx?.conditionProviderFailureCode;
 if(!ctx||ctx.conditionProviderReadCount!==1)return '';
 if(ctx.conditionProviderFetchStatus==='received')return '／馬場補助資料も受信（JRA公式照合は別）';
 if(!code)return '／馬場補助資料は未取得（原因未記録）';
 const reason=Object.hasOwn(GOING_FAILURE_LABELS,code)
  ?GOING_FAILURE_LABELS[code]:'詳細未確認';
 return '／馬場補助資料は保留：'+reason+
  '。馬場12点は無理に採点せず、4つの基本データは維持。';
}
function sourceReadProof(data){
 // This reports *provider reads*, not actual verified runner records,
 // official JRA information, calibrated grades or purchase readiness.
 if(data.raceCount===0)
  return '【番組0R・予想未作成】JRDB照会 '+data.sourceReadCount+
   '回。'+(data.sourceReadCount===1?
    '番組だけ取得。出走馬・調教・近走・馬場は照会していません。':
    '以前の方式で番組以外の資料も照会（実際の出走馬は未確認）。')+
   '開催なしとは断定できません。新規3連単・署名0件。';
 return '【番組あり・資料照会完了】JRDBの番組／出走馬／調教／近走を '+
  data.sourceReadCount+'回照会。番組 '+data.raceCount+
  'R／2項目の研究用3連単 '+data.draftCount+'R／見送り '+data.holdCount+
  'R／今回受け取った署名 '+data.researchReceiptCount+
  '件。資料の充足・正式10項目採点・JRA公式照合は別。'+
  goingFetchStatus(data);
}
function recordRetentionStatus(data,day){
 let count;
 try{count=selectedReceiptsForVerification(day).length;}
 catch(_){
  return '【端末固定記録の確認失敗】件数を信用できません。以前のデータは変更せず、バックアップと署名確認を優先。';
 }
 return '固定研究記録：この端末に '+count+'R（署名は未検証）／'+
  (data.archiveEnabled?
   'サーバー固定の報告 '+data.archiveRecordCount+'R（実際の読取確認は別操作）':
   'サーバー永続保存は未設定')+
  '。Safariとホーム画面の保存領域は異なる場合があります。バックアップ画面で別に保管してください。';
}
function operationalNextStep(data,fixed,expiredCount=0,displayableCount=null){
 const warning='JRA公式の出走・取消・馬場・発走時刻は未照合。正式100点予想・実購入ではありません。';
 const visible=displayableCount===null
  ?Math.max(0,data.draftCount-expiredCount):displayableCount;
 if(data.raceCount===0)
  return '【番組0R・確認保留】JRDBが0件でも開催なしとは断定できません。'+
   '次：日付・公開状況・JRDB接続を確認。後付けの買い目は作りません。'+warning;
 const reasons=Object.entries(data.holdReasons).filter(([,count])=>count>0)
  .sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
 const lead=reasons.slice(0,2).map(([reason,count])=>
  SHORT_HOLDS[reason]+' '+count+'R').join('／');
 if(data.draftCount>0&&visible===0&&expiredCount===data.draftCount)
  return '【発走時刻経過・新案0R】受信済み下書き '+data.draftCount+
   'Rはすべて端末で確認した時点で暫定発走時刻を過ぎました。'+
   '新しい買い目は表示せず、以前の固定履歴だけを確認してください。'+warning;
 if(data.draftCount===0)
  return '【全'+data.raceCount+'R見送り】'+
   (lead?'主な理由：'+lead+'。':'理由の詳細はレース別に確認。')+
   '次：下の見送り理由ボタンで資料不足と発走済みを区別。'+
   '無理に3連単を作りません。'+warning;
 if(fixed.unavailable||fixed.blocked.size>0)
  return '【固定記録の確認が必要】表示可能な研究用下書き '+visible+
   'R中、固定済み記録との照合保留・不一致 '+fixed.blocked.size+
   'R。次：固定記録の署名確認・バックアップを優先。'+
   '異なる新しい買い目を表示しません。'+warning;
 return '【研究用下書きあり】全'+data.raceCount+'R中、研究用3連単 '+visible+
  'R／見送り '+data.holdCount+'R。'+
  (expiredCount?'暫定発走時刻経過・新案非表示 '+expiredCount+'R。':'')+
  (lead?'主な見送り：'+lead+'。':'')+
  '次：「下書きのみ」で1着・2着・3着と点数を確認。'+
  (data.sourceMaterials.status==='unavailable'?
   '追加8項目の資料件数は照合保留。':'')+warning;
}
function validateStoredResearchLedger(existing){
 if(!Array.isArray(existing)||existing.length>360)
  throw Error('保存済みの記録形式を確認できません');
 // Reject corrupt or repeated records on ANY date before appending to the
 // shared ledger. A different-day duplicate must not silently survive while
 // the current day's new predictions are marked "saved".
 const identities=new Set(),tracks=new Set(['札幌','函館','福島','新潟','東京',
  '中山','中京','京都','阪神','小倉']);
 for(const old of existing){
  const p=old?.snapshot,id=p&&p.date+'|'+p.track+'|'+p.race;
  if(!p||typeof p.date!=='string'||!/^20\d{2}-\d{2}-\d{2}$/.test(p.date)||
     !Number.isFinite(Date.parse(p.date+'T12:00:00Z'))||
     new Date(p.date+'T12:00:00Z').toISOString().slice(0,10)!==p.date||
     !tracks.has(p.track)||!Number.isInteger(p.race)||p.race<1||p.race>12||
     identities.has(id)||typeof old.signature!=='string'||
     !/^[a-f0-9]{64}$/.test(old.signature)||
     p.sourceKind!=='prestart-locked'||p.actualPurchase!==false||
     p.scheduleVerified!==false||p.predictionVerified!==false||
     typeof p.lockedAt!=='string'||typeof p.scheduledOffAt!=='string'||
     !/(?:Z|[+-]\d\d:\d\d)$/.test(p.lockedAt)||
     !/(?:Z|[+-]\d\d:\d\d)$/.test(p.scheduledOffAt)||
     !Number.isFinite(Date.parse(p.lockedAt))||
     !Number.isFinite(Date.parse(p.scheduledOffAt))||
     Date.parse(p.lockedAt)>=Date.parse(p.scheduledOffAt)||
     !Array.isArray(p.trifectaTickets)||p.trifectaTickets.length<1||
     p.trifectaTickets.length>48||!Array.isArray(p.trioTickets)||
     p.trioTickets.length!==0)
   throw Error('古い記録に不整合があります');
  const tickets=new Set();
  for(const ticket of p.trifectaTickets){
   if(!Array.isArray(ticket)||ticket.length!==3||
      ticket.some(n=>!Number.isInteger(n)||n<1||n>18)||
      new Set(ticket).size!==3||tickets.has(ticket.join('-')))
    throw Error('古い買い目に不整合があります');
   tickets.add(ticket.join('-'));
  }
  identities.add(id);
 }
 return identities;
}
function sameTicketSet(first,second){
 const canon=items=>items.map(t=>t.join('-')).sort().join('|');
 return canon(first)===canon(second);
}
function compareFixedWithDrafts(data,day){
 // Read the FIRST local prestart lock. Never rewrite it, and never
 // assume a syntactically valid HMAC string has been verified by server.
 // Ambiguous saved data blocks the newly generated formation display.
 try{
  // A bad record on another day also blocks displaying a newly generated
  // formation: the first-write ledger cannot be trusted until recovered.
  const raw=localStorage.getItem(RECEIPTS_KEY);
  if(raw){
   if(raw.length>650000)throw Error('oversized_store');
   validateStoredResearchLedger(JSON.parse(raw));
  }
  const receipts=selectedReceiptsForVerification(day);
  const byRace=new Map(receipts.map(row=>[
   row.snapshot.track+'|'+row.snapshot.race,row.snapshot]));
  const blocked=new Set(),held=[];
  let matches=0,conflicts=0;
  for(const race of data.races){
   const key=race.track+'|'+race.race,previous=byRace.get(key);
   if(!previous)continue;
   if(race.status!=='provisional_draft'){
    held.push(key);continue;
   }
   if(sameTicketSet(previous.trifectaTickets,race.tickets))matches++;
   else{blocked.add(key);conflicts++;}
  }
  const unlisted=[...byRace.keys()].filter(k=>
   !data.races.some(r=>r.track+'|'+r.race===k)).length;
  return {blocked,unavailable:false,
   total:receipts.length,matches,conflicts,held:held.length,unlisted};
 }catch(_){
  return {blocked:new Set(data.races.filter(r=>
   r.status==='provisional_draft').map(r=>r.track+'|'+r.race)),
   unavailable:true,total:null,matches:0,conflicts:0,held:0,unlisted:0};
 }
}
function fixedComparisonMessage(report){
 if(report.unavailable)
  return '【保存記録の確認が必要】端末の固定済み研究記録を安全に読み取れません。再分析の買い目は表示しません。バックアップと署名検証を確認してください。元の記録は変更していません。';
 if(report.conflicts)
  return '【買い目の不一致 '+report.conflicts+
   'R】再分析の下書きと最初に端末へ固定した3連単が異なります。再分析の新しい買い目は表示せず、下の「発走前に固定した買い目の履歴」で最初の買い目を確認してください。既存の固定買い目は上書きしていません。署名検証は別操作です。';
 if(report.total)
  return '端末に固定済みの研究記録 '+report.total+'R。今回の暫定案と馬番が一致 '+
   report.matches+'R／今回は見送り '+report.held+'R／番組にない保存済み記録 '+
   report.unlisted+'R。固定済みを後から変更しません。署名検証は別操作です。';
 return 'この開催日の端末に固定済みの研究記録はまだありません。発走前に生成した研究用下書きのみ、初回に限り固定保存します。';
}
function clearDraftShortcut(){
 $('autoMultiQuickRaces').replaceChildren();
 $('autoMultiQuickPanel').open=false;
 $('autoMultiQuickTitle').textContent='調教・距離・展開など複数項目の参考：未取得';
 const quick=$('autoReferenceQuickRaces');
 quick.replaceChildren();
 $('autoReferenceQuickPanel').open=false;
 $('autoReferenceQuickTitle').textContent='見送りレースの参考候補：未取得';
 const shortcut=$('autoDraftShortcut');
 shortcut.textContent='買い目あり：未取得';
 shortcut.onclick=null;
 $('autoUncertainRecentRaces').replaceChildren();
 $('autoHeldTie48Races').replaceChildren();
 $('autoCombinedResearchRows').replaceChildren();
 $('autoCombinedNoPickRows').replaceChildren();
 $('autoCombinedResearchStatus').textContent='この開催日の研究用候補は未取得です。';
 $('autoCombinedResearchExport').disabled=true;
 $('autoCombinedResearchExport').onclick=null;
 $('autoCombinedResearchExportStatus').textContent='この開催日の保存用研究一覧は未取得です。';
 $('autoCombinedNoPickTitle').textContent='買い目・参考候補を表示しないR：未取得';
 $('autoCombinedNoPickPanel').open=false;
 $('autoCombinedResearchPanel').open=false;
 $('autoComparableFactorRaces').replaceChildren();
 $('autoComparableFactorStatus').textContent='追加研究は未取得です。';
 $('autoTkyTrainingRows').replaceChildren();
 $('autoTkyTrainingStatus').textContent='発走前の資料が未取得です。';
 $('autoHeldTie48Hint').textContent='同点見送りの48点以内参考：未取得。';
 $('autoHeldTie48Status').textContent='レース取得前。同点馬を勝手に選びません。';
 $('autoTrainingFeedStatus').textContent='調教元データの行数・馬番照合状況はまだ未確認です。';
 $('autoWorkoutQuickRows').replaceChildren();
 $('autoWorkoutQuickStatus').textContent='未取得。追加照会なしで一覧を作ります。';
 const workoutJump=$('autoWorkoutQuickOpen');
 workoutJump.disabled=true;
 workoutJump.textContent='全場の調教S/Aを確認（未取得）';
 workoutJump.onclick=null;
 $('autoUncertainRecentHint').textContent='近走不足の追加研究：未取得。';
 $('autoUncertainRecentStatus').textContent='レース取得前。追加資料を勝手に補完しません。';
 const next=$('autoNextDraft');
 next.disabled=true;
 next.textContent='次の下書きRへ（未取得）';
 next.onclick=null;
 // The fallback link must never survive a date change, failed fetch or
 // stale response. It does not create or sign a new forecast.
 $('autoReferenceOpen').disabled=true;
 $('autoReferenceOpen').onclick=null;
 $('autoReferencePulse').textContent='見送りレースの参考候補は未取得です。';
}
// iPhone Safari may stay on one race screen while the clock passes an off.
// Hide fresh, unpurchased research formations at the earliest JRDB
// PROVISIONAL off without a new API request or a storage mutation.
// On wake from iOS suspension, the existing pageshow/visibility guard
// also checks the current clock. Neither clock is JRA-official proof.
let automaticOffTimer=null,automaticOffGeneration=0;
function clearAutomaticOffTimer(){
 automaticOffGeneration++;
 if(automaticOffTimer!==null&&typeof clearTimeout==='function')
  clearTimeout(automaticOffTimer);
 automaticOffTimer=null;
}
function armAutomaticOffTimer(data,day){
 clearAutomaticOffTimer();
 // Timer is armed only after a validated, accepted response.
 // A later date change or response invalidation cancels this timer, and
 // the callback performs the full identity/date check again.
 if(typeof setTimeout!=='function'||
    latestDisplayedReport!==data||latestDisplayedDay!==day||
    $('autoDay').value.replaceAll('-','')!==day)return;
 const iso=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 const now=new Date().getTime();
 if(!Number.isFinite(now))return;
 let next=Infinity;
 const referenced=new Set([
  ...(data.uncertainRecentResearch?.races||[]),
  ...(data.heldTie48Research?.races||[]),
  ...(data.comparableFactorResearch?.races||[]),
  ...(data.tkyTrainingStudy?.races||[]),
  ...(data.tkyArrowFormationPreview?.races||[])
 ].map(r=>r.track+'|'+r.race));
 for(const race of data.races){
  if(!(race.status==='provisional_draft'||
       (race.status==='hold'&&referenced.has(race.track+'|'+race.race)))||
     draftExpiredOnDevice(day,race.postTime))
   continue;
  const off=Date.parse(iso+'T'+race.postTime+':00+09:00');
  if(Number.isFinite(off)&&off>now&&off<next)next=off;
 }
 if(!Number.isFinite(next))return;
 const generation=automaticOffGeneration;
 const delay=Math.max(1000,Math.min(2147480000,next-now+100));
 automaticOffTimer=setTimeout(()=>{
  automaticOffTimer=null;
  if(generation!==automaticOffGeneration||
     latestDisplayedReport!==data||latestDisplayedDay!==day||
     $('autoDay').value.replaceAll('-','')!==day)return;
  const expired=data.races.filter(r=>r.status==='provisional_draft'&&
   draftExpiredOnDevice(day,r.postTime)).length;
  const expiredResearch=data.races.some(r=>
   r.status==='hold'&&referenced.has(r.track+'|'+r.race)&&
   draftExpiredOnDevice(day,r.postTime));
  if(expired>latestExpiredDraftCount||expiredResearch){
   latestExpiredDraftCount=expired;
   render(data,day); // Purely read/display; never re-sign, buy or fetch.
   $('autoStatus').textContent='発走予定時刻を過ぎた研究用の新しい買い目を自動で非表示にしました。発走前の固定履歴はそのままです。JRA公式の実際の発走時刻は別途確認してください。';
  }
  // Device clocks can jump backwards; schedule the next safe local check.
  armAutomaticOffTimer(data,day);
 },delay);
}
function renderUncertainRecent(data,day){
 const host=$('autoUncertainRecentRaces');
 const status=$('autoUncertainRecentStatus');
 const hint=$('autoUncertainRecentHint');
 host.replaceChildren();
 const p=data.uncertainRecentResearch;
 if(p===undefined){
  hint.textContent='近走不足の追加研究：未取得。';
  status.textContent='この日の資料不足を補う参考処理は未取得です。見送りを維持します。';
  return;
 }
 try{
  if(!p||p.version!=='owner-uncertain-recent-preview-1'||
     p.date!==day||p.raceCount!==data.raceCount||
     p.researchOnly!==true||p.privateOwnerOnly!==true||
     p.independentJraVerified!==false||
     p.officialJraVerified!==false||p.formalTenFactorReady!==false||
     p.predictionReady!==false||p.bettingReady!==false||
     p.changesExistingDrafts!==false||p.changesExistingReceipts!==false||
     p.newProviderRequests!==0||p.ticketsIssued!==0||
     !Number.isInteger(p.reviewedPrestartMissingFactorRaces)||
     p.reviewedPrestartMissingFactorRaces<0||
     p.reviewedPrestartMissingFactorRaces>data.holdCount||
     !Array.isArray(p.races)||p.races.length>data.holdCount||
     p.safeResearchPreviewCount!==p.races.length)
   throw Error('unknown_recent_contract');
  const original=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
  const seen=new Set(),cards=[];
  for(const row of p.races){
   if(!row||!Number.isInteger(row.race)||
      typeof row.track!=='string'||row.status!=='bounded_recent_uncertainty_only'||
      !Number.isInteger(row.points)||row.points<6||row.points>48||
      !Number.isInteger(row.missingRecentCount)||row.missingRecentCount<1||
      !Number.isInteger(row.assessedTrainingCount)||row.assessedTrainingCount<4||
      row.assessedTrainingCount>18||
      row.eachCutoffProvenForAllRecentGrades!==true||
      row.officialJraVerified!==false||row.formalScoreReady!==false||
      row.predictionReady!==false||row.bettingReady!==false||
      row.receiptIssued!==false||row.actualPurchase!==false||
      (row.newcomerRaceCandidate!==undefined&&
       typeof row.newcomerRaceCandidate!=='boolean'))
    throw Error('unknown_recent_race');
   const key=row.track+'|'+row.race;
   const base=original.get(key);
   if(seen.has(key)||!base||base.status!=='hold'||
      base.reason!=='missing_factors'||!Array.isArray(base.runners)||
      base.runners.length!==row.assessedTrainingCount||
      base.runners.some(h=>!['S','A','B','C'].includes(h.training))||
      base.runners.filter(h=>h.recent==='未評価').length!==row.missingRecentCount||
      (base.runners.length>5&&row.points<12)||
      (row.newcomerRaceCandidate===true&&(
       base.newcomerRaceCandidate!==true||
       row.missingRecentCount!==row.assessedTrainingCount||
       base.runners.some(h=>h.recent!=='未評価'||
        h.recentObserved?.datedRuns!==0||
        h.recentObserved?.completedRuns!==0))))
    throw Error('unknown_recent_roster');
   seen.add(key);
   const setRoster=new Set(base.runners.map(h=>h.number));
   const groups=[row.first,row.second,row.third];
   if(groups.some((g,j)=>!Array.isArray(g)||
       g.length<(j===0?1:j===1?2:3)||
       g.length>(j===0?3:j===1?8:18)||
       new Set(g).size!==g.length||
       g.some(n=>!Number.isInteger(n)||!setRoster.has(n)))||
      groups.some((g,j)=>j>0&&groups[j-1].some(n=>!g.includes(n)))||
      row.points!==groups[0].length*(groups[1].length-1)*
       (groups[2].length-2))
    throw Error('unknown_recent_formation');
   // New wider second/third groups must be independently reconstructed
   // from each horse's *observed* workout and bounded missing-recent
   // interval; the UI must not trust a forged "stable" source flag.
   if(row.second.length>5||row.third.length>10||base.runners.length<=5){
    const values={S:3,A:2,B:1,C:0};
    const ordered=base.runners.map(h=>{
     if(!h||!Number.isInteger(h.number)||
        !Object.hasOwn(values,h.training)||
        !(h.recent==='未評価'||Object.hasOwn(values,h.recent)))
      throw Error('unknown_recent_wide_source');
     const floor=30*values[h.training]+
       (h.recent==='未評価'?0:3*values[h.recent]);
     return {number:h.number,floor,
      ceiling:floor+(h.recent==='未評価'?9:0)};
    }).sort((a,b)=>b.floor-a.floor||b.ceiling-a.ceiling||
      a.number-b.number);
    if(new Set(ordered.map(h=>h.number)).size!==ordered.length)
     throw Error('unknown_recent_wide_roster');
    const stable=n=>n===ordered.length||(
      n>0&&n<ordered.length&&
      Math.min(...ordered.slice(0,n).map(h=>h.floor))>
      Math.max(...ordered.slice(n).map(h=>h.ceiling)));
    const candidates=(secondCap,thirdCap)=>{
     const found=[];
     for(const first of [1,2,3]){
      if(!stable(first))continue;
      for(let second=first+1;
          second<=Math.min(secondCap,ordered.length);second++){
       if(!stable(second))continue;
       for(let third=second;
           third<=Math.min(thirdCap,ordered.length);third++){
        if(!stable(third))continue;
        const points=first*(second-1)*(third-2);
        if(points>=(ordered.length<=5?6:12)&&points<=48)
         found.push({first,second,third,points});
       }
      }
     }
     return found;
    };
    // The server now compares ALL stable cutoffs through 18 runners before
    // selecting 30-40 points. A narrow 12-24 point option must not reject
    // a better 30-40 point research reference with a wider complete tier.
    // Keep the same tie/unknown-grade safeguards and ordering as the server.
    const wide=candidates(8,18).sort((a,b)=>
       Number(30<=b.points&&b.points<=40)-
        Number(30<=a.points&&a.points<=40)||
       Number(41<=b.points&&b.points<=48)-
        Number(41<=a.points&&a.points<=48)||
       Number(b.first===2)-Number(a.first===2)||
       Number(b.first===1)-Number(a.first===1)||
       b.points-a.points);
    const selected=wide[0];
    if(!selected||
       row.first.join(',')!==ordered.slice(0,selected.first)
        .map(h=>h.number).join(',')||
       row.second.join(',')!==ordered.slice(0,selected.second)
        .map(h=>h.number).join(',')||
       row.third.join(',')!==ordered.slice(0,selected.third)
        .map(h=>h.number).join(',')||
       row.points!==selected.points)
     throw Error('unknown_recent_wide_comparison_mismatch');
   }
   if(draftExpiredOnDevice(day,base.postTime))continue;
   const card=dom('details');
   card.append(dom('summary',row.track+' '+row.race+
    (row.newcomerRaceCandidate===true?
     'R｜新馬戦候補（番組名）・調教中心の参考':
     'R｜不足近走でも候補範囲が不変・参考')+
    row.points+'通り'));
   card.append(dom('p','1着候補 '+row.first.join('・')+
    '／2着候補 '+row.second.join('・')+
    '／3着候補 '+row.third.join('・'),'picks'));
   if(row.newcomerRaceCandidate===true)card.append(dom('p',
    'JRDB番組名は新馬戦候補、観測できた近走は全馬0走。初出走の独立確認ではなく、近走は採点しません。調教の仮評価で候補の区切りが安定した研究用参考のみです。','muted'));
   card.append(dom('p','近走未評価 '+row.missingRecentCount+
    '頭。JRDB暫定発走 '+base.postTime+
    '。これは署名なし研究例で、正式100点予想・購入可能な馬券ではありません。'+
    'JRA公式出走・取消・馬場・時刻は未検証。','muted'));
   if(row.first.length===1)card.append(dom('p',
    '調教の暫定評価で単独トップが、近走の未評価S〜Cのどの場合でも入れ替わらないため、1頭軸の参考例を表示。正式な1着予想・購入指示ではありません。','muted'));
   if(row.second.length>5||row.third.length>10)card.append(dom('p',
    '近走が欠けた馬を仮にCや最下位にせず、候補境界が不変な場合だけ2着・3着の同評価群を拡張。最大48点の署名なし参考。','muted'));
   if(row.third.length===base.runners.length)card.append(dom('p',
    '注意：3着候補にはこのレースの全頭が含まれます。全頭を高評価した意味ではなく、近走不足と同点を保留した研究例です。','muted'));

   cards.push(card);
  }
  host.replaceChildren(...cards);
  hint.textContent=cards.length?
   '近走不足からの追加参考 '+cards.length+'R（署名なし）。下の詳細に表示。':
   '近走不足からの追加参考0R。条件を満たさないレースは見送り。';
  status.textContent=p.races.length
   ?'近走不足の'+p.reviewedPrestartMissingFactorRaces+
    'Rを検討。参考グループ '+cards.length+'R'+
    (cards.length<p.races.length?'（発走予定時刻経過分は非表示）':'')+
    '。本来の見送り数と固定済み買い目は変えません。'
   :'近走不足でも確実に分けられる候補グループは0R。'+
    '無理な補完をせず、見送りを維持します。';
 }catch(_){
  host.replaceChildren();
  hint.textContent='近走不足の追加研究は形式確認ができないため非表示。';
  status.textContent='追加の参考候補を安全に確認できません。元の研究用予想と固定記録は無変更です。';
 }
}
function renderTkyTrainingStudy(data,day){
 const host=$('autoTkyTrainingRows'),status=$('autoTkyTrainingStatus');
 host.replaceChildren();
 const study=data.tkyTrainingStudy;
 if(study===undefined){
  status.textContent='別系統の調教指数資料はこの応答では未確認。通常の見送りを維持します。';
  return;
 }
 try{
  if(!study||study.version!=='owner-tky-training-index-study-2'||
     study.date!==day||study.raceCount!==data.raceCount||
     study.sourceMetric!=='tky_training_index_and_training_arrow'||
     study.trainingArrowPriority!==true||
     study.trainingSourceDistinctFromTcy!==true||
     study.researchOnly!==true||study.privateOwnerOnly!==true||
     study.officialJraVerified!==false||study.modelCalibrated!==false||
     study.training30Ready!==false||study.predictionReady!==false||
     study.bettingReady!==false||study.ticketsIssued!==0||
     study.newProviderRequests!==0||study.changesExistingDrafts!==false||
     study.changesExistingReceipts!==false||
     study.rawIndicesIncluded!==false||
     !Array.isArray(study.races)||study.races.length>data.raceCount||
     study.studiedRaceCount!==study.races.length)
   throw Error('tky_training_contract');
  const originals=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
  const used=new Set(),cards=[];
  for(const item of study.races){
   const key=item?.track+'|'+item?.race,original=originals.get(key);
   if(!original||used.has(key)||original.status!=='hold'||
      original.reason!=='missing_factors'||
      !Array.isArray(original.runners)||
      !original.runners.some(h=>h.training==='未評価')||
      !Number.isInteger(item.rosterCount)||
      item.rosterCount!==original.runners.length||
      item.rosterCount<4||item.rosterCount>18||
      !Number.isInteger(item.observedCount)||
      item.observedCount<0||item.observedCount>item.rosterCount||
      item.unassessedCount!==item.rosterCount-item.observedCount||
      !Number.isInteger(item.arrowObservedCount)||
      item.arrowObservedCount<0||item.arrowObservedCount>item.rosterCount||
      item.arrowUnobservedCount!==item.rosterCount-item.arrowObservedCount||
      !Number.isInteger(item.comparableDirectionPairs)||
      item.comparableDirectionPairs<0||
      item.comparableDirectionPairs>
       Math.min(item.observedCount,item.arrowObservedCount)*
       (Math.min(item.observedCount,item.arrowObservedCount)-1)/2||
      !Number.isInteger(item.disagreeDirectionPairs)||
      item.disagreeDirectionPairs<0||
      item.disagreeDirectionPairs>item.comparableDirectionPairs||
      item.observedCount<2&&item.arrowObservedCount<2||
      item.rankingScope!=='tky_arrow_first_index_descriptive_only'||
      !Array.isArray(item.runners)||item.runners.length!==item.observedCount||
      !Array.isArray(item.arrows)||item.arrows.length!==item.arrowObservedCount)
    throw Error('tky_training_roster');
   used.add(key);
   const roster=new Set(original.runners.map(h=>h.number)),observed=new Set();
   const band=[];
   let previousRank=0;
   for(const horse of item.runners){
    if(!horse||Object.keys(horse).sort().join(',')!=='number,observedRank'||
       !Number.isInteger(horse.number)||!roster.has(horse.number)||
       observed.has(horse.number)||!Number.isInteger(horse.observedRank)||
       horse.observedRank<1||horse.observedRank>item.observedCount||
       (band.length===0&&horse.observedRank!==1)||
       (band.length&&horse.observedRank<previousRank))
     throw Error('tky_training_rank');
    observed.add(horse.number);
    band.push(horse.observedRank);
    previousRank=horse.observedRank;
   }
   const distinct=[...new Set(band)];
   for(let i=1;i<distinct.length;i++){
    const prior=distinct[i-1];
    if(distinct[i]!==band.filter(n=>n<=prior).length+1)
     throw Error('tky_training_rank_gaps');
   }
   const conditionLevel={
    'デキ抜群':1,'上昇':2,'平行線':3,'やや下降':4,'デキ落ち':5
   };
   const arrowSeen=new Set();
   let lastCondition=0,lastArrowNumber=0;
   for(const itemArrow of item.arrows){
    if(!itemArrow||
       Object.keys(itemArrow).sort().join(',')!=='condition,number'||
       !Number.isInteger(itemArrow.number)||
       !roster.has(itemArrow.number)||arrowSeen.has(itemArrow.number)||
       !Object.hasOwn(conditionLevel,itemArrow.condition))
     throw Error('tky_training_arrow_roster');
    const severity=conditionLevel[itemArrow.condition];
    if(severity<lastCondition||
       (severity===lastCondition&&itemArrow.number<=lastArrowNumber))
     throw Error('tky_training_arrow_order');
    lastCondition=severity;lastArrowNumber=itemArrow.number;
    arrowSeen.add(itemArrow.number);
   }
   if(draftExpiredOnDevice(day,original.postTime))continue;
   const card=dom('details');
   card.append(dom('summary',item.track+' '+item.race+
    'R｜調教矢印 '+item.arrowObservedCount+'頭／指数 '+item.observedCount+
    '頭（全'+item.rosterCount+'頭）'));
   card.append(dom('p',item.arrows.length?
    '調教矢印を優先：'+item.arrows.map(h=>
     h.number+'番 '+h.condition).join('／'):
    '調教矢印は未取得（数値だけで馬の状態を決めません）','picks'));
   card.append(dom('p',item.runners.length?
    '別の調教指数の数値順（状態評価ではない）：'+item.runners.map(h=>
      h.observedRank+'位 '+h.number+'番').join('／'):
    '別の調教指数の数値比較は資料不足','muted'));
   card.append(dom('p',
    'JRDBは調教矢印の評価を数値指数より優先するよう説明しています。'+
    (item.comparableDirectionPairs?
     '矢印と指数の順序が逆の組 '+item.disagreeDirectionPairs+
     '／'+item.comparableDirectionPairs+'組（比較できた組だけ）。':
     '矢印と指数を方向比較できた組はありません。')+
    (item.arrowUnobservedCount?'矢印不明 '+item.arrowUnobservedCount+'頭。':'')+
    (item.unassessedCount?'指数不明 '+item.unassessedCount+'頭。':'')+
    '欠測はデキ落ちの意味ではありません。/tcyの追切・仕上指数とは別で、'+
    '正式調教30点・総合順位・正式3連単には使用しません。','muted'));
   cards.push(card);
  }
  host.replaceChildren(...cards);
  status.textContent=cards.length?
   '調教資料不足の見送りから、調教矢印と別指数の参考情報が確認できた '+
   cards.length+'R。矢印を優先し、正式採点・馬券は変更なし。':
   '調教矢印・別指数を比較できる発走前の見送りレースは0R。';
 }catch(_){
  host.replaceChildren();
  status.textContent='別系統の調教指数の照合が一致せず非表示。既存予想・記録は無変更。';
 }
}
function renderTkyArrowFormations(data,day){
 const host=$('autoTkyArrowFormationRows'),status=$('autoTkyArrowFormationStatus');
 host.replaceChildren();
 const p=data.tkyArrowFormationPreview;
 if(p===undefined){
  status.textContent='調教矢印の参考グループは未取得。元の見送りを維持します。';
  return;
 }
 try{
  const study=data.tkyTrainingStudy;
  if(!p||p.version!=='owner-tky-arrow-formation-preview-1'||
     p.date!==day||p.raceCount!==data.raceCount||
     !Array.isArray(p.races)||p.races.length>data.raceCount||
     p.safeReferenceCount!==p.races.length||
     !Number.isInteger(p.reviewedPrestartStudies)||
     !study||study.version!=='owner-tky-training-index-study-2'||
     study.date!==day||study.raceCount!==data.raceCount||
     !Array.isArray(study.races)||
     p.reviewedPrestartStudies!==study.races.length||
     p.researchOnly!==true||p.privateOwnerOnly!==true||
     p.officialJraVerified!==false||p.formalTenFactorReady!==false||
     p.predictionReady!==false||p.bettingReady!==false||
     p.newProviderRequests!==0||p.ticketsIssued!==0||
     p.changesExistingDrafts!==false||p.changesExistingReceipts!==false)
   throw Error('arrow_reference_contract');
  const originalBy=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
  const studyBy=new Map(study.races.map(r=>[r.track+'|'+r.race,r]));
  if(studyBy.size!==study.races.length)throw Error('arrow_duplicate_source');
  const used=new Set(),cards=[];
  const levels={'デキ抜群':1,'上昇':2,'平行線':3,'やや下降':4,'デキ落ち':5};
  for(const item of p.races){
   const id=item?.track+'|'+item?.race,original=originalBy.get(id),
         source=studyBy.get(id);
   if(!original||!source||used.has(id)||
      original.status!=='hold'||original.reason!=='missing_factors'||
      !Array.isArray(original.runners)||
      item.rosterCount!==original.runners.length||
      item.rosterCount!==original.horseCount||
      item.rosterCount<4||item.rosterCount>18||
      source.rosterCount!==item.rosterCount||
      source.arrowObservedCount!==item.rosterCount||
      source.arrowUnobservedCount!==0||
      !Array.isArray(source.arrows)||source.arrows.length!==item.rosterCount||
      !Array.isArray(source.runners)||
      source.observedCount!==source.runners.length||
      source.unassessedCount!==item.rosterCount-source.observedCount||
      item.arrowObservedCount!==item.rosterCount||
      item.indexObservedCount!==source.observedCount||
      item.partialIndexIgnored!==(source.observedCount!==item.rosterCount)||
      item.rankingScope!==(source.observedCount===item.rosterCount?
       'arrow_then_index_rank':'arrow_only')||
      item.status!=='unsigned_arrow_first_research'||
      item.tiedSourceTiersNotSplit!==true||
      item.researchOnly!==true||item.officialJraVerified!==false||
      item.formalScoreReady!==false||item.predictionReady!==false||
      item.bettingReady!==false||item.receiptIssued!==false||
      item.actualPurchase!==false||
      !Array.isArray(item.first)||!Array.isArray(item.second)||
      !Array.isArray(item.third)||
      !Number.isInteger(item.points)||item.points<1||item.points>48)
    throw Error('arrow_reference_row');
   used.add(id);
   const roster=new Set(original.runners.map(h=>h.number));
   if(roster.size!==item.rosterCount||
      !original.runners.some(h=>h.training==='未評価'))
    throw Error('arrow_reference_roster');
   const arrow=new Map(),index=new Map();
   let prevLevel=0,prevNumber=0,prevRank=0;
   for(const h of source.arrows){
    if(!h||Object.keys(h).sort().join(',')!=='condition,number'||
       !Number.isInteger(h.number)||!roster.has(h.number)||
       arrow.has(h.number)||!Object.hasOwn(levels,h.condition))
     throw Error('arrow_reference_arrow');
    const level=levels[h.condition];
    if(level<prevLevel||(level===prevLevel&&h.number<=prevNumber))
     throw Error('arrow_reference_arrow_order');
    prevLevel=level;prevNumber=h.number;arrow.set(h.number,level);
   }
   for(const h of source.runners){
    if(!h||Object.keys(h).sort().join(',')!=='number,observedRank'||
       !Number.isInteger(h.number)||!roster.has(h.number)||
       index.has(h.number)||!Number.isInteger(h.observedRank)||
       h.observedRank<1||h.observedRank>source.observedCount||
       h.observedRank<prevRank)
     throw Error('arrow_reference_index');
    prevRank=h.observedRank;index.set(h.number,h.observedRank);
   }
   if(arrow.size!==item.rosterCount||index.size!==source.observedCount)
    throw Error('arrow_reference_source_coverage');
   const completeIndex=index.size===item.rosterCount;
   const keyOf=n=>[arrow.get(n),...(completeIndex?[index.get(n)]:[])];
   const cmp=(a,b)=>{
    const x=keyOf(a),y=keyOf(b);
    for(let i=0;i<x.length;i++)if(x[i]!==y[i])return x[i]-y[i];
    return a-b;
   };
   const ranked=[...roster].sort(cmp);
   const boundary=n=>n===ranked.length||
     keyOf(ranked[n-1]).join('|')!==keyOf(ranked[n]).join('|');
   let expected=null;
   for(const first of [2,3,1]){
    if(!boundary(first))continue;
    const options=[];
    for(let second=first+1;second<=Math.min(8,ranked.length);second++){
     if(!boundary(second))continue;
     for(let third=Math.max(3,second);
         third<=Math.min(12,ranked.length);third++){
      if(!boundary(third))continue;
      const count=first*(second-1)*(third-2);
      if(count>=1&&count<=48)options.push({first,second,third,count});
     }
    }
    if(options.length){
     options.sort((a,b)=>
      Number(30<=b.count&&b.count<=40)-Number(30<=a.count&&a.count<=40)||
      b.count-a.count||b.third-a.third||a.second-b.second);
     expected=options[0];break;
    }
   }
   if(!expected||item.points!==expected.count||
      item.first.join(',')!==ranked.slice(0,expected.first).join(',')||
      item.second.join(',')!==ranked.slice(0,expected.second).join(',')||
      item.third.join(',')!==ranked.slice(0,expected.third).join(','))
    throw Error('arrow_reference_formation_mismatch');
   if(draftExpiredOnDevice(day,original.postTime))continue;
   const card=dom('details');
   card.append(dom('summary',item.track+' '+item.race+'R｜調教矢印から'+
    item.points+'点の署名なし参考（未購入）'));
   card.append(dom('p','1着 '+item.first.map(n=>n+'番').join('・'),'picks'));
   card.append(dom('p','2着 '+item.second.map(n=>n+'番').join('・'),'picks'));
   card.append(dom('p','3着 '+item.third.map(n=>n+'番').join('・'),'picks'));
   card.append(dom('p',
    (completeIndex?'同じ矢印内だけ指数順位を参考。':
     '指数に欠測があるため全頭で指数順位は使わず矢印のみ。')+
    '馬番順の同点切りなし。正式な調教30点・総合予想・JRA確認や保存済み買い目には使いません。','muted'));
   cards.push(card);
  }
  host.replaceChildren(...cards);
  status.textContent=cards.length?
    '調教資料不足で保留中のうち、全頭の矢印が確認できた'+
    cards.length+'Rに参考の1/2/3着グループを表示。署名・購入・固定なし。':
    '発走前に矢印の全頭比較から組める参考グループは0R。通常の見送りを維持。';
 }catch(_){
  host.replaceChildren();
  status.textContent='調教矢印の参考グループの照合に不整合があり非表示。既存の馬券・記録は無変更。';
 }
}
function renderComparableFactorResearch(data,day,forDraft=false){
 const host=$(forDraft?'autoProvisionalFactorRaces':'autoComparableFactorRaces');
 const status=$(forDraft?'autoProvisionalFactorStatus':'autoComparableFactorStatus');
 host.replaceChildren();
 const p=forDraft?data.provisionalFactorResearch:data.comparableFactorResearch;
 const limit=forDraft?data.draftCount:data.holdCount;
 const reviewed=forDraft?p?.reviewedPrestartDraftRaces:p?.reviewedHeldRaces;
 if(p===undefined){status.textContent='追加研究は未取得です。';return;}
 try{
  if(!p||p.version!==(forDraft?
       'owner-provisional-seven-factor-reference-1':
       'owner-comparable-factor-formation-3')||
    p.date!==day||p.raceCount!==data.raceCount||
    p.researchOnly!==true||p.privateOwnerOnly!==true||
    p.officialJraVerified!==false||p.formalTenFactorReady!==false||
    p.predictionReady!==false||p.bettingReady!==false||
    p.ticketsIssued!==0||p.newProviderRequests!==0||
    p.changesExistingDrafts!==false||p.changesExistingReceipts!==false||
    p.changesExistingRoi!==false||
    !Number.isInteger(reviewed)||reviewed<0||
    reviewed>limit||
    !Array.isArray(p.races)||p.unsignedReferenceCount!==p.races.length||
    p.races.length>limit||
    p.minimumComparableWeight!==64||
    !p.diagnostics||typeof p.diagnostics!=='object')throw Error('comparable_header');
  const causes=['ineligible','time_unavailable','roster_mismatch',
    'training_missing','factor_invalid','insufficient_shared_weight',
    'tie_or_point_limit','preview'];
  if(Object.keys(p.diagnostics).sort().join('|')!==causes.slice().sort().join('|')||
     causes.some(key=>!Number.isInteger(p.diagnostics[key])||
      p.diagnostics[key]<0||p.diagnostics[key]>limit)||
     causes.reduce((sum,key)=>sum+p.diagnostics[key],0)!==reviewed||
     p.diagnostics.preview!==p.unsignedReferenceCount)
   throw Error('comparable_diagnostics');
  const originals=new Map(data.races.map(r=>[r.track+'|'+r.race,r])),
   grades={S:3,A:2,B:1,C:0},
   keys=['training','recent','course_distance','pace','ground','jockey_stable','rotation'],
   weights={training:30,recent:3,course_distance:17,pace:17,ground:12,jockey_stable:10,rotation:1};
  const seen=new Set(),cards=[];
  for(const row of p.races){
   const id=row?.track+'|'+row?.race,base=originals.get(id);
   if(!row||seen.has(id)||!base||
     base.status!==(forDraft?'provisional_draft':'hold')||
     (!forDraft&&!['missing_factors','ambiguous_equal_grade_boundary'].includes(base.reason))||
     row.status!==(forDraft?'provisional_comparable_research_only':'comparable_research_only')||
     row.postTime!==base.postTime||
     row.tiesNeverSplit!==true||row.missingNeverImputed!==true||
     row.officialJraVerified!==false||row.formalScoreReady!==false||
     row.bettingReady!==false||row.receiptIssued!==false||
     row.actualPurchase!==false||!Number.isInteger(row.points)||
     row.points<12||row.points>48)throw Error('comparable_race');
   seen.add(id);
   const auto=automaticFactorRace(data,day,base);
   if(!auto||!Array.isArray(base.runners)||base.runners.length!==auto.horses.length||
      base.runners.length!==base.horseCount)throw Error('comparable_roster');
   const map=new Map(auto.horses.map(h=>[h.number,h.factors])),
     roster=new Set(base.runners.map(h=>h.number));
   if(map.size!==base.runners.length||roster.size!==base.runners.length||
      [...map.keys()].some(n=>!roster.has(n))||
      base.runners.some(h=>!Object.hasOwn(grades,h.training)))throw Error('comparable_training');
   const available=['training'];
   if(base.runners.every(h=>Object.hasOwn(grades,h.recent)))available.push('recent');
   for(const k of keys.slice(2))
    if(auto.horses.every(h=>h.factors[k].points!==null))available.push(k);
   if(!Array.isArray(row.comparedKeys)||!Array.isArray(row.excludedKeys)||
      JSON.stringify(available)!==JSON.stringify(row.comparedKeys)||
      JSON.stringify(keys.filter(k=>!available.includes(k)))!==JSON.stringify(row.excludedKeys)||
      row.comparedWeight!==available.reduce((sum,k)=>sum+weights[k],0)||
      row.comparedWeight<64||
      (row.comparedWeight<70&&
       (!available.includes('course_distance')||
        !available.includes('pace'))))throw Error('comparable_weights');
   const ranked=base.runners.map(h=>{
    let point=weights.training*grades[h.training]/3;
    if(available.includes('recent'))point+=weights.recent*grades[h.recent]/3;
    for(const k of available.slice(1))if(k!=='recent')point+=map.get(h.number)[k].points;
    return {number:h.number,score:Math.round(point*10000)};
   }).sort((a,b)=>b.score-a.score||a.number-b.number);
   const groups=[row.first,row.second,row.third];
   if(groups.some((g,i)=>!Array.isArray(g)||g.length<(i===0?1:i===1?2:3)||
     g.length>(i===0?3:i===1?8:18)||
     JSON.stringify(g)!==JSON.stringify(ranked.slice(0,g.length).map(h=>h.number))||
     (g.length<ranked.length&&ranked[g.length-1].score===ranked[g.length].score))||
     groups[1].length<=groups[0].length||groups[2].length<groups[1].length||
     row.points!==groups[0].length*(groups[1].length-1)*(groups[2].length-2))
    throw Error('comparable_shape');
   if(draftExpiredOnDevice(day,base.postTime))continue;
   const card=dom('details');
   card.append(dom('summary',row.track+' '+row.race+'R｜研究用 '+row.points+
     '点（共通配点'+row.comparedWeight+'点分）'));
   card.append(dom('p','1着 '+row.first.join('・')+'番／2着 '+
     row.second.join('・')+'番／3着 '+row.third.join('・')+'番','picks'));
   card.append(dom('p','全馬共通の評価：'+available.join('・')+
     '。欠けた項目は全馬から除外。正式100点・勝率・JRA公式照合ではありません。'+
     '買い目の署名・保存・購入・仮想収支は行いません。','muted'));
   cards.push(card);
  }
  host.replaceChildren(...cards);
  const counts=p.diagnostics;
  status.textContent=(forDraft?'既存下書きRの比較：':'見送りRの内訳：')+
    '検査'+reviewed+'R／'+
    '表示できる研究参考'+cards.length+'R／'+
    '調教不足'+counts.training_missing+'R／'+
    '全馬共通の評価不足'+counts.insufficient_shared_weight+'R／'+
    '同点・点数条件'+counts.tie_or_point_limit+'R／'+
    '頭数などの不一致'+counts.roster_mismatch+'R／'+
    '資料形式不一致'+counts.factor_invalid+'R／'+
    '発走時刻経過等'+counts.time_unavailable+'R。'+
    'これは正式予想件数ではありません。';
 }catch(_){
  host.replaceChildren();
  status.textContent='比較材料が安全に検証できず、参考候補は非表示です。';
 }
}
function renderHeldTie48(data,day){
 const host=$('autoHeldTie48Races'),
  hint=$('autoHeldTie48Hint'),status=$('autoHeldTie48Status');
 host.replaceChildren();
 const p=data.heldTie48Research;
 if(p===undefined){
  hint.textContent='同点見送りの48点以内参考：未取得。';
  status.textContent='この日の同点補助研究は未取得。通常の見送りを維持します。';
  return;
 }
 try{
  if(!p||p.version!=='owner-held-tie-48-preview-1'||
     p.date!==day||p.raceCount!==data.raceCount||
     p.researchOnly!==true||p.privateOwnerOnly!==true||
     p.officialJraVerified!==false||p.formalTenFactorReady!==false||
     p.predictionReady!==false||p.bettingReady!==false||
     p.changesExistingDrafts!==false||
     p.changesExistingReceipts!==false||
     p.newProviderRequests!==0||p.ticketsIssued!==0||
     !Number.isInteger(p.reviewedPrestartTieHolds)||
     p.reviewedPrestartTieHolds<0||
     p.reviewedPrestartTieHolds>data.holdCount||
     !Array.isArray(p.races)||p.races.length>data.holdCount||
     p.unsignedReferenceCount!==p.races.length)
   throw Error('held_tie_contract');
  const originals=new Map(data.races.map(r=>[r.track+'|'+r.race,r])),
   seen=new Set(),cards=[],scale={S:3,A:2,B:1,C:0};
  for(const row of p.races){
   const id=row?.track+'|'+row?.race,base=originals.get(id);
   if(!row||typeof row.track!=='string'||!Number.isInteger(row.race)||
      seen.has(id)||!base||base.status!=='hold'||
      base.reason!=='ambiguous_equal_grade_boundary'||
      row.status!=='unsplit_complete_two_factor_hold'||
      row.completeRunnerCount!==base.runners.length||
      row.allTiedScoreBoundariesUnsplit!==true||
      row.researchOnly!==true||row.officialJraVerified!==false||
      row.formalScoreReady!==false||row.predictionReady!==false||
      row.bettingReady!==false||row.receiptIssued!==false||
      row.actualPurchase!==false||!Number.isInteger(row.points)||
      row.points<12||row.points>48)
    throw Error('held_tie_identity');
   seen.add(id);
   const ranked=base.runners.map(h=>{
    if(!Object.hasOwn(scale,h.training)||
       !Object.hasOwn(scale,h.recent)||
       h.weightedResearchPoints!==30*scale[h.training]+3*scale[h.recent])
     throw Error('held_tie_score_missing');
    return {number:h.number,score:h.weightedResearchPoints};
   }).sort((a,b)=>b.score-a.score||a.number-b.number);
   const groups=[row.first,row.second,row.third];
   if(groups.some((g,i)=>!Array.isArray(g)||
       g.length<(i===0?1:i===1?2:3)||
       g.length>(i===0?3:i===1?6:12)||
       JSON.stringify(g)!==JSON.stringify(ranked.slice(0,g.length).map(x=>x.number))||
       (g.length<ranked.length&&
        ranked[g.length-1].score===ranked[g.length].score))||
      groups[1].length<=groups[0].length||
      groups[2].length<groups[1].length||
      row.points!==groups[0].length*(groups[1].length-1)*
       (groups[2].length-2))
    throw Error('held_tie_formation');
   if(draftExpiredOnDevice(day,base.postTime))continue;
   const card=dom('details');
   card.append(dom('summary',row.track+' '+row.race+
    'R｜同点群を維持した研究用 '+row.points+'通り'));
   card.append(dom('p','1着候補 '+row.first.join('・')+
    '／2着候補 '+row.second.join('・')+
    '／3着候補 '+row.third.join('・'),'picks'));
   card.append(dom('p','調教・近走の暫定33点分だけの比較。従来40点の境界では見送りだったR。'+
    '同点馬は丸ごと候補群に残し、最大48通りまでの署名なし研究例。'+
    'JRA公式出走・取消・馬場・発走時刻は未確認。馬券購入・固定記録には反映しません。','muted'));
   cards.push(card);
  }
  host.replaceChildren(...cards);
  hint.textContent=cards.length?
   '同点見送りからの48点以内参考 '+cards.length+'R（署名なし）。':
   '同点見送りからの追加参考0R。無理に順位を付けません。';
  status.textContent='同点で見送り '+p.reviewedPrestartTieHolds+
   'Rを検討。参考 '+cards.length+'R'+
   (cards.length<p.races.length?'（発走時刻経過分は非表示）':'')+
   '。通常の見送り数・発走前固定記録は無変更。';
 }catch(_){
  host.replaceChildren();
  hint.textContent='同点の追加研究は安全確認できず非表示。';
  status.textContent='同点の参考候補を検証できません。保存済み予想・購入記録に変更はありません。';
 }
}
// Read-only training S/A digest for the owner: never an overall horse
// grade, winner pick, or permission to revive expired provisional tickets.
function renderWorkoutQuick(data,day){
 const host=$('autoWorkoutQuickRows'),status=$('autoWorkoutQuickStatus');
 host.replaceChildren();
 const rows=data.races.filter(r=>r.runners.length>0&&
  !draftExpiredOnDevice(day,r.postTime))
  .sort((a,b)=>a.postTime.localeCompare(b.postTime));
 const picks=[];
 for(const race of rows){
  const s=race.runners.filter(h=>h.training==='S').map(h=>h.number);
  const a=race.runners.filter(h=>h.training==='A').map(h=>h.number);
  if(!s.length&&!a.length)continue;
  const no=race.race,track=race.track,post=race.postTime;
  const key=track+'|'+no;
  const button=dom('button',post+' '+track+no+'R｜調教S '+
   (s.length?s.join('・')+'番':'なし')+'／A '+
   (a.length?a.join('・')+'番':'なし')+
   '｜'+(race.status==='hold'?'研究用下書きは見送り':'研究用下書きあり'));
  button.type='button';
  button.onclick=()=>{
   // Check the device clock on tap; a stale open accordion must never
   // advertise a post-off race as an actionable opportunity.
   if($('autoDay').value.replaceAll('-','')!==day||
      draftExpiredOnDevice(day,post)){
    status.textContent='選択日または暫定発走時刻が変わりました。'+
     '発走済みの研究案は再表示しません。';
    return;
   }
   const target=$('autoRacePick');
   if(target.disabled)return;
   target.value=key;
   if(typeof target.onchange==='function')target.onchange();
   const section=$('forecastRacesSection');
   if(typeof section?.scrollIntoView==='function')
    section.scrollIntoView({behavior:'smooth',block:'start'});
  };
  picks.push(button);
 }
 host.replaceChildren(...picks);
 const jump=$('autoWorkoutQuickOpen');
 jump.disabled=picks.length===0;
 jump.textContent=picks.length?
  '全場の調教S/Aを確認（参考 '+picks.length+'R）':
  '全場の調教S/Aを確認（該当0R）';
 jump.onclick=()=>{
  if(jump.disabled)return;
  // Never reopen stale or changed-day data, nor create a new provider read.
  if(latestDisplayedReport!==data||latestDisplayedDay!==day||
     $('autoDay').value.replaceAll('-','')!==day||
     !rows.some(r=>!draftExpiredOnDevice(day,r.postTime))){
   jump.disabled=true;
   jump.textContent='調教S/Aは期限切れ・日付変更のため再確認が必要';
   return;
  }
  $('autoResearchTools').open=true;
  const panel=$('autoWorkoutQuickPanel');
  panel.open=true;
  if(typeof panel.scrollIntoView==='function')
   panel.scrollIntoView({behavior:'smooth',block:'start'});
 };
 status.textContent=picks.length
  ?'発走予定時刻前の調教S/A参考 '+picks.length+'R。'+
   '表示は調教だけの仮評価で、総合予想の買い目や勝負度ではありません。'
  :'発走前に表示できる調教S/A参考Rは0R。'+
   '資料未取得・発走済み・S/Aなしを区別して確認してください。';
}
function quickReferencePicks(card){
 // HTMLElement.children is an HTMLCollection in real Safari, NOT an Array.
 // The older direct .children.slice(1) threw when the first held R gained
 // a valid study, discarding the otherwise successful 36R response.
 return Array.from(card.children).slice(1)
  .filter(el=>el.className==='picks')
  .map(el=>el.textContent)
  .filter(x=>typeof x==='string'&&x.length>0&&x.length<240)
  .slice(0,3);
}
function renderMultiFactorQuick(data,day){
 const host=$('autoMultiQuickRaces'),panel=$('autoMultiQuickPanel'),
  title=$('autoMultiQuickTitle'),source=$('autoProvisionalFactorRaces');
 host.replaceChildren();
 const byRace=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 const rows=[],seen=new Set();
 // Source cards exist only AFTER the original strict source/roster/grade/
 // boundary/cutoff validator rendered them. Never read raw optional JSON.
 for(const card of source.children){
  const heading=card.children?.[0]?.textContent;
  const match=typeof heading==='string'?
   /^([^｜\s]{2,4})\s+(1[0-2]|[1-9])R｜/.exec(heading):null;
  if(!match)continue;
  const key=match[1]+'|'+Number(match[2]),race=byRace.get(key);
  if(!race||race.status!=='provisional_draft'||seen.has(key)||
     draftExpiredOnDevice(day,race.postTime))continue;
  const picks=quickReferencePicks(card);
  if(picks.length!==1||!/^1着 .+／2着 .+／3着 .+番$/.test(picks[0]))
   continue;
  seen.add(key);
  rows.push({race,card,heading,picks});
 }
 rows.sort((a,b)=>a.race.postTime.localeCompare(b.race.postTime)||
  a.race.track.localeCompare(b.race.track,'ja')||a.race.race-b.race.race);
 for(const item of rows){
  const entry=dom('div',undefined,'owner-reference-quick-card');
  entry.append(dom('p',item.race.postTime+'予定（JRDB）｜'+
   item.heading+'｜未署名の別案','muted'));
  entry.append(dom('p',item.picks[0],'picks'));
  const open=dom('button','根拠を見る（追加照会・購入なし）');
  open.type='button';
  open.onclick=()=>{
   if(latestDisplayedReport!==data||latestDisplayedDay!==day||
      $('autoDay').value.replaceAll('-','')!==day||
      draftExpiredOnDevice(day,item.race.postTime)){
    open.disabled=true;
    title.textContent='開催日変更・発走時刻経過のため古い参考は非表示';
    return;
   }
   $('autoResearchTools').open=true;
   $('autoComparableFactorPanel').open=true;
   item.card.open=true;
   if(typeof item.card.scrollIntoView==='function')
    item.card.scrollIntoView({behavior:'smooth',block:'start'});
  };
  entry.append(open);
  host.append(entry);
 }
 title.textContent=rows.length?
  '調教・距離・展開など複数項目の参考 '+rows.length+
  'R（署名なし・2項目固定とは別）':
  '調教・距離・展開など複数項目の参考 0R（未検証・未購入）';
 panel.open=rows.length>0&&rows.length<=8;
}

function combinedResearchIndex(data,day,draftNodes,referenceRows){
 // The caller ran the strict full-day validator and each optional
 // reference renderer (including grade bounds and race roster checks).
 // Do NOT read optional raw server previews a second time.
 if(!data||!Array.isArray(data.races)||data.raceCount!==data.races.length||
    !Array.isArray(draftNodes)||!Array.isArray(referenceRows)||
    typeof day!=='string'||!/^20\d{6}$/.test(day))
  throw Error('combined_study_bad_input');
 const dayRaces=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 if(dayRaces.size!==data.raceCount)throw Error('combined_study_duplicate_race');
 const seen=new Set(),picks=[];
 for(const item of draftNodes){
  const race=dayRaces.get(item?.key);
  if(!race||item.draft!==true||race.status!=='provisional_draft'||
     seen.has(item.key)||
     !Number.isInteger(race.points)||race.points<1||race.points>48||
     !Array.isArray(race.first)||!Array.isArray(race.second)||
     !Array.isArray(race.third)||race.first.length<1||
     race.second.length<2||race.third.length<3)
   throw Error('combined_study_draft');
  // If the provisional off passes between validation and display,
  // quietly omit the newly expired study instead of failing the full day.
  if(draftExpiredOnDevice(day,race.postTime))continue;
  seen.add(item.key);
  picks.push({key:item.key,track:race.track,race:race.race,
   postTime:race.postTime,type:'prestart_draft',
   title:'JRDB2項目の研究用下書き '+race.points+'点（未購入）',
   lines:['1着 '+race.first.join('・'),'2着 '+race.second.join('・'),
    '3着 '+race.third.join('・')]});
 }
 for(const item of referenceRows){
  const race=item?.race;
  const key=race?.track+'|'+race?.race;
  if(!race||dayRaces.get(key)!==race||race.status!=='hold'||
     seen.has(key)||
     !item.panel||typeof item.panel.label!=='string'||
     !['共通評価','近走不足','同点見送り','調教矢印'].includes(item.panel.label)||
     !Array.isArray(item.picks)||item.picks.length<1||
     item.picks.length>3||item.picks.some(line=>
      typeof line!=='string'||line.length<1||line.length>239))
   throw Error('combined_study_reference');
  if(draftExpiredOnDevice(day,race.postTime))continue;
  seen.add(key);
  picks.push({key,track:race.track,race:race.race,
   postTime:race.postTime,type:'unsigned_reference',
   title:item.panel.label+'による研究参考（署名なし・未購入）',
   lines:[...item.picks]});
 }
 picks.sort((a,b)=>a.postTime.localeCompare(b.postTime)||
  a.track.localeCompare(b.track,'ja')||a.race-b.race);
 const excluded=data.races.filter(r=>!seen.has(r.track+'|'+r.race))
  .map(r=>({track:r.track,race:r.race,postTime:r.postTime,
   status:r.status}));
 const signed=picks.filter(r=>r.type==='prestart_draft').length;
 const unsigned=picks.length-signed;
 if(picks.length+excluded.length!==data.raceCount||
    unsigned>data.holdCount||signed>data.draftCount)
  throw Error('combined_study_accounting');
 return {picks,excluded,signed,unsigned,dayCount:data.raceCount};
}
function combinedResearchDownloadText(summary,day,createdAt){
 // A portable list of already-visible *research* numbers, not receipts.
 // Mobile user gesture is required to download; neither the device clock
 // nor this text file independently proves capture before scheduled off.
 if(!summary||!Array.isArray(summary.picks)||
    !Array.isArray(summary.excluded)||
    !Number.isInteger(summary.dayCount)||summary.dayCount<1||
    summary.dayCount>36||
    summary.picks.length+summary.excluded.length!==summary.dayCount||
    summary.signed+summary.unsigned!==summary.picks.length||
    typeof day!=='string'||!/^20\d{6}$/.test(day)||
    typeof createdAt!=='string'||
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{3})?Z$/.test(createdAt))
  throw Error('unsafe_research_download');
 const clean=text=>String(text).replace(/[\u0000-\u001f\u007f]+/g,' ').slice(0,240);
 const iso=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 const lines=[
  'ARC RACE｜全R研究参考・閲覧専用（未購入）',
  '開催日：'+iso,
  'ファイル作成時刻（端末申告・独立検証なし）：'+createdAt,
  '対象：'+summary.dayCount+'R　JRDB2項目の研究下書き：'+
   summary.signed+'R　署名なし参考例：'+summary.unsigned+
   'R　新しい候補表示なし：'+summary.excluded.length+'R',
  '注意：このファイル自体は発走前保存の署名を持たず、正式10項目採点・JRA公式照合・購入・仮想収支の証明ではありません。',
  '固定済み研究用買い目を復元するためのバックアップではありません。別途、本人用バックアップ画面から署名付き端末記録を保存してください。',
  '同じRの研究下書きと参考候補は重複計上しません。見送り20Rの参考例は未購入です。',
  '',
 ];
 const all=[
  ...summary.picks.map(r=>({...r,unshown:false})),
  ...summary.excluded.map(r=>({...r,unshown:true}))
 ].sort((a,b)=>a.postTime.localeCompare(b.postTime)||
  a.track.localeCompare(b.track,'ja')||a.race-b.race);
 for(const row of all){
  if(!/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(row.postTime)||
     !Number.isInteger(row.race)||row.race<1||row.race>12||
     typeof row.track!=='string'||row.track.length>4)
   throw Error('unsafe_download_race');
  lines.push(clean(row.postTime)+'予定（JRDB）｜'+clean(row.track)+
   ' '+row.race+'R｜'+(row.unshown?'新しい候補なし':clean(row.title)));
  if(row.unshown){
   lines.push('  見送り・時刻経過・固定競合など。研究用候補を作り直していません。');
  }else{
   if(!Array.isArray(row.lines)||row.lines.length<1||
      row.lines.length>3)throw Error('unsafe_download_lines');
   for(const line of row.lines){
    if(typeof line!=='string'||line.length<1||line.length>239)
     throw Error('unsafe_download_line');
    lines.push('  '+clean(line));
   }
  }
 }
 return lines.join('\n')+'\n';
}
// Show the evidence that *really exists* for a held race. Never turn a
// missing recent grade into C/0, a complete two-factor score or a formation.
// The source full-day validator already checked roster/grades. Revalidate the
// redacted numbers here because this is the one-screen fallback path.
function safeHeldWorkoutEvidence(race){
 if(!race||race.status!=='hold'||
    !['missing_factors','ambiguous_equal_grade_boundary'].includes(race.reason)||
    !Array.isArray(race.runners)||race.runners.length<4||
    race.runners.length>18||race.horseCount!==race.runners.length)
  return null;
 const groups={S:[],A:[],B:[],C:[]},seen=new Set();
 let trainingMissing=0,recentMissing=0;
 for(const h of race.runners){
  if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
     seen.has(h.number)||
     !['S','A','B','C','未評価'].includes(h.training)||
     !['S','A','B','C','未評価'].includes(h.recent))
   return null;
  seen.add(h.number);
  recentMissing+=Number(h.recent==='未評価');
  if(h.training==='未評価')trainingMissing++;
  else groups[h.training].push(h.number);
 }
 if(trainingMissing===race.runners.length)return null;
 for(const band of Object.keys(groups))
  groups[band].sort((a,b)=>a-b);
 return {groups,trainingMissing,recentMissing};
}
// Compare 1st-place candidate *membership* only after the existing
// multi-factor renderer has validated the same-day/roster/points/grades and
// produced visible reference cards. No raw optional server payload is trusted
// or converted into signed picks, scores, win probabilities or wagers.
function validatedDraftFirstAgreement(data,day,rendered){
 const result=new Map(),raceByKey=new Map(data.races.map(r=>[
  r.track+'|'+r.race,r
 ]));
 if(!rendered||!rendered.children)return result;
 for(const card of rendered.children){
  const heading=card?.children?.[0]?.textContent;
  const picks=card?.children?.[1]?.textContent;
  const match=typeof heading==='string'?
   /^([^｜\s]{2,4})\s+(1[0-2]|[1-9])R｜研究用 ([1-9]\d?)点（共通配点(\d{2})点分）$/.exec(heading):null;
  const pick=typeof picks==='string'?
   /^1着 ((?:1[0-8]|[1-9])(?:・(?:1[0-8]|[1-9])){0,2})番／2着 /.exec(picks):null;
  if(!match||!pick)continue;
  const key=match[1]+'|'+Number(match[2]),race=raceByKey.get(key);
  const weight=Number(match[4]),nums=pick[1].split('・').map(Number);
  if(!race||race.status!=='provisional_draft'||
     draftExpiredOnDevice(day,race.postTime)||
     !Number.isInteger(weight)||weight<64||weight>90||
     new Set(nums).size!==nums.length||
     !nums.every(n=>Number.isInteger(n)&&n>=1&&n<=18)||
     !Array.isArray(race.first)||race.first.length<1||
     race.first.length>3||new Set(race.first).size!==race.first.length)
   continue;
  const old=new Set(race.first),next=new Set(nums);
  const common=nums.filter(n=>old.has(n)).length;
  const kind=common===old.size&&old.size===next.size?'一致':
   common>0?'一部一致':'相違';
  result.set(key,'追加項目との1着候補比較：'+kind+
   '（共通評価'+weight+'点分・研究用）'+
   '｜2項目の固定下書きは変更なし。的中率検証やJRA公式照合は未実施。');
 }
 return result;
}
function renderCombinedResearchRows(data,day,draftNodes,referenceRows,agreement=new Map()){
 const result=combinedResearchIndex(data,day,draftNodes,referenceRows);
 const host=$('autoCombinedResearchRows'),missing=$('autoCombinedNoPickRows');
 host.replaceChildren();missing.replaceChildren();
 const venues=[...new Set(data.races.map(r=>r.track))];
 const venueButtons=dom('div',undefined,'venue-tabs');
 const raceButtons=dom('div',undefined,'owner-race-jump');
 const cards=dom('div');
 const picksByKey=new Map(result.picks.map(r=>[r.key,r]));
 host.append(venueButtons,raceButtons,cards);
 function showVenue(track){
  cards.replaceChildren();
  raceButtons.replaceChildren();
  for(const button of venueButtons.children)
   button.ariaPressed=String(button.textContent===track);
  // Display all scheduled races in this venue, including those on hold.
  // Never infer missing horse numbers or turn references into signed picks.
  const entries=data.races.filter(r=>r.track===track)
   .sort((a,b)=>a.race-b.race);
  for(const race of entries){
   const key=race.track+'|'+race.race;
   const pick=picksByKey.get(key);
   const expired=draftExpiredOnDevice(day,race.postTime);
   const kind=pick&&!expired
    ?pick.type==='prestart_draft'?'owner-research-draft':'owner-research-reference'
    :'owner-research-hold';
   const card=dom('div',undefined,'owner-reference-quick-card '+kind);
   card.append(dom('strong',race.track+' '+race.race+'R'));
   if(pick&&!expired){
    card.append(dom('p',race.postTime+'予定（JRDB）｜'+pick.title,'muted'));
    for(const line of pick.lines)card.append(dom('p',line,'picks'));
    if(pick.type==='prestart_draft'&&agreement.has(key))
     card.append(dom('p',agreement.get(key),'owner-factor-agreement'));
   }else{
    const reason=expired?'発走予定時刻経過・新しい買い目は非表示':
     race.status==='hold'
      ?'見送り・参考候補なし（'+
       (Object.hasOwn(REASONS,race.reason)?REASONS[race.reason]:'資料確認待ち')+'）'
      :'新しい買い目は非表示（端末固定などを確認）';
    card.append(dom('p',race.postTime+'予定（JRDB）｜'+reason,'muted'));
    // A held race may have genuine workout bands even when two-factor
    // tickets are impossible. Display ONLY those redacted bands, pre-off.
    // It remains a non-betting row, does not join combinedResearchIndex
    // picks, and never receives a receipt or ROI calculation.
    if(!expired&&race.status==='hold'){
     const evidence=safeHeldWorkoutEvidence(race);
     if(evidence){
      for(const grade of ['S','A','B','C']){
       const nums=evidence.groups[grade];
       if(nums.length)
        card.append(dom('p','調教'+grade+'：'+nums.join('・')+
         '番（馬番順・仮評価）','owner-workout-only owner-workout-'+grade));
      }
      const missing=[];
      if(evidence.recentMissing)missing.push('近走未評価'+evidence.recentMissing+'頭');
      if(evidence.trainingMissing)missing.push('調教未評価'+evidence.trainingMissing+'頭');
      card.append(dom('p','調教資料のみ参考表示'+
       (missing.length?'｜'+missing.join('・'):'')+
       '｜3連単の買い目なし・正式10項目未評価','muted'));
     }
    }
   }
   cards.append(card);
  }
  // 1〜12R are jump/filter controls only. Never fetch, regenerate,
  // edit receipts or switch the source's saved date.
  const selectors=[{race:0,label:'全R'},
   ...entries.map(r=>({race:r.race,label:r.race+'R'}))];
  const controls=[];
  function selectRace(number){
   for(let i=0;i<entries.length;i++)
    cards.children[i].hidden=number!==0&&entries[i].race!==number;
   for(const item of controls)
    item.button.ariaPressed=String(item.race===number);
  }
  for(const item of selectors){
   const button=dom('button',item.label);
   button.type='button';
   button.onclick=()=>selectRace(item.race);
   controls.push({...item,button});
   raceButtons.append(button);
  }
  selectRace(0);
 }
 for(const track of venues){
  const button=dom('button',track);
  button.type='button';
  button.onclick=()=>showVenue(track);
  venueButtons.append(button);
 }
 if(venues.length)showVenue(venues[0]);
 for(const r of result.excluded){
  const reason=r.status==='hold'?'見送り（参考候補なし・資料不足など）':
   '新しい買い目は非表示（時刻経過・固定競合など）';
  missing.append(dom('p',r.track+' '+r.race+'R｜'+
   r.postTime+'予定（JRDB）｜'+reason,'muted'));
 }
 $('autoCombinedResearchStatus').textContent='全'+result.dayCount+
  'R｜発走前研究用下書き '+result.signed+
  'R｜署名なし追加参考 '+result.unsigned+
  'R｜新しい買い目・参考候補なし '+result.excluded.length+
  'R。参考例は見送りRに含まれ、正式10項目予想・購入・発走前固定には含まれません。追加JRDB照会0回。';
 $('autoCombinedNoPickTitle').textContent='新しい買い目・参考候補なし '+
  result.excluded.length+'R（詳細）';
 $('autoCombinedResearchPanel').open=venues.length>0;
 $('autoCombinedNoPickPanel').open=false;
 const exportButton=$('autoCombinedResearchExport');
 const exportStatus=$('autoCombinedResearchExportStatus');
 exportButton.disabled=result.dayCount===0;
 exportStatus.textContent='この日の研究一覧を保存できます。別途、署名付き固定記録は本人用の16種類バックアップで保護してください。';
 exportButton.onclick=()=>{
  // No HTTP request, source-data download, localStorage mutation, receipt
  // issuing, result inference or wager. Snapshot the currently time-safe
  // browser-validated display ONLY in an explicit owner tap.
  if(exportButton.disabled||latestDisplayedReport!==data||
     latestDisplayedDay!==day||$('autoDay').value.replaceAll('-','')!==day){
   exportStatus.textContent='取得日が変わりました。古い候補を保存せず、開催日と予想一覧を確認してください。';
   return;
  }
  let url=null;
  try{
   const fresh=combinedResearchIndex(data,day,draftNodes,referenceRows);
   const report=combinedResearchDownloadText(fresh,day,new Date().toISOString());
   if(report.length>35000)throw Error('download_oversize');
   const blob=new Blob([report],{type:'text/plain;charset=utf-8'});
   url=URL.createObjectURL(blob);
   const link=document.createElement('a');
   link.href=url;
   link.download='arc-race-'+day+'-research-view.txt';
   link.hidden=true;
   document.body.append(link);
   link.click();
   link.remove();
   exportStatus.textContent='全'+fresh.dayCount+'Rの研究一覧のファイル保存を開始しました。iPhoneの「ファイル」で実際に保存できたか確認してください。参考案は署名なし。固定買い目のバックアップは別です。';
  }catch(_){
   exportStatus.textContent='研究一覧のファイルを安全に作成できません。予想・端末固定記録・有料JRDB照会には影響ありません。';
  }finally{
   if(url!==null){
    // Safari downloads must first be handed to WebKit; revoking on the
    // very same stack can cancel a valid iPhone file download.
    if(typeof setTimeout==='function')
     setTimeout(()=>URL.revokeObjectURL(url),5000);
    else URL.revokeObjectURL(url);
   }
  }
 };
 return result;
}
function render(input,day){
 const data=validate(input,day),p=data.tenFactorPreview,ctx=data.raceContext;
 const workoutOrder=validateWorkoutIndexOrder(data,day);
 renderUncertainRecent(data,day);
 renderHeldTie48(data,day);
 renderComparableFactorResearch(data,day);
 renderComparableFactorResearch(data,day,true);
 // An unpurchased, independently validated multi-factor comparison is
 // no longer buried several nested panels deep on iPhone.
 renderMultiFactorQuick(data,day);
 renderTkyTrainingStudy(data,day);
 renderTkyArrowFormations(data,day);
 // Existing server research already has its own strict race/roster/time
 // validation inside each renderer. Surface only those *visible* cards;
 // never turn a held race into a signed or purchased 3連単.
 const referencePanels=[
  {id:'autoComparableFactorRaces',panel:'autoComparableFactorPanel',label:'共通評価'},
  {id:'autoUncertainRecentRaces',panel:'autoUncertainRecentPanel',label:'近走不足'},
  {id:'autoHeldTie48Races',panel:'autoHeldTie48Panel',label:'同点見送り'},
  {id:'autoTkyArrowFormationRows',panel:'autoTkyArrowFormationPanel',label:'調教矢印'}
 ].map(item=>({...item,count:$(item.id).children.length}))
  .filter(item=>item.count>0);
 // Build a one-glance, per-race index ONLY from cards that the
 // independent browser-side research validators have already rendered.
 // Never read an unvalidated research payload to populate this index.
 const quick=$('autoReferenceQuickRaces'),quickPanel=$('autoReferenceQuickPanel'),
  quickTitle=$('autoReferenceQuickTitle');
 quick.replaceChildren();
 const validatedRaceKeys=new Map(data.races.map(r=>[r.track+'|'+r.race,r]));
 const seenQuick=new Set(),quickRows=[];
 for(const panel of referencePanels){
  const parent=$(panel.id);
  for(const card of parent.children){
   const heading=card.children?.[0]?.textContent;
   const match=typeof heading==='string'?
    /^([^｜\s]{2,4})\s+(1[0-2]|[1-9])R｜/.exec(heading):null;
   if(!match)continue;
   const key=match[1]+'|'+Number(match[2]),race=validatedRaceKeys.get(key);
   if(!race||race.status!=='hold'||seenQuick.has(key)||
      draftExpiredOnDevice(day,race.postTime))continue;
   const picks=quickReferencePicks(card);
   if(!picks.length)continue;
   seenQuick.add(key);
   quickRows.push({race,card,panel,heading,picks});
  }
 }
 quickRows.sort((a,b)=>a.race.postTime.localeCompare(b.race.postTime)||
  a.race.track.localeCompare(b.race.track,'ja')||a.race.race-b.race.race);
 // Reuse ONLY browser-validated and already rendered reference cards.
 const referenceByRace=new Map(quickRows.map(item=>[
  item.race.track+'|'+item.race.race,item
 ]));
 for(const item of quickRows){
  const row=dom('div',undefined,'owner-reference-quick-card');
  row.append(dom('p',item.race.postTime+'予定（JRDB）｜'+
   item.panel.label+'｜'+item.heading,'muted'));
  for(const text of item.picks)row.append(dom('p',text,'picks'));
  const open=dom('button','研究根拠を確認（未購入）');
  open.type='button';
  open.onclick=()=>{
   if(latestDisplayedReport!==data||latestDisplayedDay!==day||
      $('autoDay').value.replaceAll('-','')!==day||
      draftExpiredOnDevice(day,item.race.postTime)){
    open.disabled=true;
    $('autoReferencePulse').textContent=
     '開催日変更または発走予定時刻経過。古い参考候補を開けません。';
    return;
   }
   // No HTTP fetch, localStorage write, receipt signature, ticket handoff
   // or real purchase. Reuse the already validated, visible source card.
   $('autoResearchTools').open=true;
   $(item.panel.panel).open=true;
   item.card.open=true;
   if(typeof item.card.scrollIntoView==='function')
    item.card.scrollIntoView({behavior:'smooth',block:'start'});
  };
  row.append(open);
  quick.append(row);
 }
 quickTitle.textContent=quickRows.length?
  '見送りレースの参考候補 '+quickRows.length+'R（研究用・未購入）':
  '見送りレースの参考候補 0R（正式予想ではありません）';
 quickPanel.open=quickRows.length>0&&quickRows.length<=8;
 const referenceButton=$('autoReferenceOpen');
 // Panels are METHODS, not distinct races. A single race can have several
 // independently validated reference methods. Count only the unique,
 // time-safe per-R cards actually visible in the quick index.
 const referenceCount=quickRows.length;
 $('autoReferencePulse').textContent=referenceCount
  ?'見送りのうち参考候補 '+referenceCount+'R（'+
   referencePanels.map(item=>item.label+' '+item.count+'件').join('／')+
   '）。同じRの重複は除外。研究用・未購入です。'
  :'見送りレースから発走前に確認できる参考候補は0R。欠損を0点に補完しません。';
 referenceButton.disabled=referenceCount===0;
 referenceButton.onclick=()=>{
  if(referenceCount===0||latestDisplayedReport!==data||
     latestDisplayedDay!==day||
     $('autoDay').value.replaceAll('-','')!==day||
     !quickRows.some(item=>!draftExpiredOnDevice(day,item.race.postTime))){
   referenceButton.disabled=true;
   $('autoReferencePulse').textContent='表示期間が変わりました。古い参考候補は開けません。';
   return;
  }
  // Show the per-R quick index FIRST; no need to browse deep research
  // panels just to see the 1st/2nd/3rd candidate numbers. Retain the
  // existing detailed research panel for inspecting evidence.
  quickPanel.open=true;
  const selected=$(referencePanels[0].panel);
  $('autoResearchTools').open=true;
  selected.open=true;
  if(typeof quickPanel.scrollIntoView==='function')
   quickPanel.scrollIntoView({behavior:'smooth',block:'start'});
 };
 renderWorkoutQuick(data,day);
 const materialByRace=validatedRunnerSourceEvidence(data);
 $('autoEvidenceGapReport').textContent=evidenceGapSummary(data,materialByRace);
 $('autoTenEvidenceMatrix').textContent=tenEvidenceMatrix(data,materialByRace);
 const deviceExpired=new Set(data.races.filter(x=>
   x.status==='provisional_draft'&&draftExpiredOnDevice(day,x.postTime)
 ).map(x=>x.track+'|'+x.race));
 jraDraftTracks=new Set(data.races.map(x=>x.track));updateJraCrosscheck();
 const fixed=compareFixedWithDrafts(data,day);
 // The top status is written after the safe display count is known.
 // Old first-write disagreements must not count as actionable picks.
 $('autoProgrammeCoverage').textContent=programmeCoverage(data);
 $('autoReadProof').textContent=sourceReadProof(data);
 renderTrainingSourceDelivery(data,day);
 const tenRows=new Map(p.races.map(r=>[r.track+'|'+r.race,r]));
 const courseRows=new Map(ctx.races.map(r=>[r.track+'|'+r.race,r]));
 const passport=data.sourcePassport?.sourceAuditAvailable?
  new Map(data.sourcePassport.races.map(r=>[r.track+'|'+r.race,r])):null;
 const host=$('autoRaces'),tabs=$('autoVenues'),
  holdTabs=$('autoHoldReasons'),select=$('autoRacePick'),
  nodes=[],groups=new Map();
 holdTabs.replaceChildren();$('autoHoldStatus').textContent=
  data.holdCount?'見送り '+data.holdCount+'R。理由を選択できます。':
   'この開催日に見送りはありません。';
 select.disabled=true;select.replaceChildren();
 const allOption=dom('option','全Rを一覧表示');allOption.value='';
 select.append(allOption);select.value='';
 host.replaceChildren();tabs.replaceChildren();renderTenHeader(p);
 $('autoFormalShadowStatus').textContent=formalGateShadowStatus(data,day);
 // Release no-longer-visible horse summary references on every render.
 prestartBodyMarkers=new Map();
 // Warning display nodes are per render; all values are safe fixed phrases.
 advanceRaceMarkers=new Map();
 $('autoFixedConsistency').textContent=fixedComparisonMessage(fixed);
 $('autoSourceSummary').textContent=summarizeDaySourcePassport(
  data.sourcePassport,data.raceCount);
 const workoutRows=data.races.filter(r=>r.runners.length>0);
 $('autoTrackWorkouts').textContent=
  '【全Rの調教参考】馬別の仮評価を表示できる '+workoutRows.length+
  '/'+data.raceCount+'R。調教S・A馬の馬番は各レースを開いて確認。'+
  '資料が未評価の馬を低評価とは扱いません。正式順位・購入推奨ではありません。';
 const gaps=missingFactorHoldBreakdown(data);
 const crossfeed=safeRecentCrossfeed(data,day);
 const lookupCross=key=>crossfeed?.byRace.get(key)?.reasonCounts?.
  more_prior_references_than_tze_runs||0;
 $('autoMissingFactorSummary').textContent=gaps.summary+
  (crossfeed&&crossfeed.total?
   ' JRDBの過去レース参照と近走観測を追加比較：参照の方が多い要調査 '+
   crossfeed.counts.more_prior_references_than_tze_runs+'頭／'+
   '過去参照が確認できない '+crossfeed.counts.no_prior_reference_visible+'頭／'+
   '1走観測 '+crossfeed.counts.only_one_dated_run_visible+'頭／'+
   '複数走あるが未採点 '+crossfeed.counts.multiple_unscored_runs+'頭／'+
   '資料の識別不明 '+crossfeed.counts.reference_or_tze_coverage_unknown+
   '頭。参照なしは新馬の証明ではありません。近走点は未評価のままです。':'');
 const gapHost=$('autoMissingFactorRaces');gapHost.replaceChildren();
 for(const row of gaps.races)
  gapHost.append(dom('p',row.track+' '+row.race+'R｜'+
   (row.available?'調教未評価 '+row.training+'頭／近走未評価 '+
    row.recent+'頭／両方 '+row.pairs+'頭'+
    (lookupCross(row.track+'|'+row.race)?
     '／JRDB過去参照の不足疑い '+lookupCross(row.track+'|'+row.race)+'頭':''):
    '馬別内訳は未確認（0頭という意味ではありません）'),'muted'));
 for(const race of data.races){
  const key=race.track+'|'+race.race,
   changedLock=fixed.blocked.has(key),elapsed=deviceExpired.has(key);
  const reference=race.status==='hold'?referenceByRace.get(key):null;
  const detail=dom('details'),title=dom('summary',
   race.track+' '+race.race+'R '+
   (race.status==='provisional_draft'
    ?elapsed?'端末受信後に発走時刻経過・新案非表示':
      changedLock?'固定済みとの不一致・再分析案非表示':
      '研究用自動案 '+race.points+'点｜1着候補 '+race.first.join('・')+'番'
    :'見送り'+(race.runners.length?'｜調教S '+race.runners.filter(h=>h.training==='S').length+
      '頭・A '+race.runners.filter(h=>h.training==='A').length+'頭（仮）':'')+
      (reference?'｜参考候補あり（研究用・未購入）':'')));
  detail.append(title);
  // Warn in the collapsed race heading so the important status is visible.
  // Do not insert a child: existing formation/horse-analysis order stays intact.
  const baseRaceHeading=title.textContent;
  if(advanceRaceWarnings.has(key))
   title.textContent=baseRaceHeading+'｜⚠ JRA事前予定差異・要確認';
  advanceRaceMarkers.set(key,{node:title,base:baseRaceHeading});
  const automatic=automaticFactorRace(data,day,race);
  const eligible=eligibleResearchFactorPanel(automatic,day,race,elapsed,changedLock);
  const seven=eligible?sevenFactorRace(data,day,race,automatic,
   materialByRace.get(key)):null;
  if(eligible)detail.append(renderAutomaticFactors(automatic));
  const course=courseRows.get(race.track+'|'+race.race);
  const condition=course.goingAvailable?course.going+'（JRDB資料）':'馬場未確認';
  detail.append(dom('p','コース条件：'+(course.surface||'芝・ダート未確認')+
    '／'+(course.distance_m===null?'距離未確認':course.distance_m+'m')+
    '／'+(course.turn||'回り未確認')+'／'+condition,'muted'));
  // Keep an eligible prestart formation as the very first racecard action.
  // No formation can be recreated after the local provisional off-time.
  if(race.status==='provisional_draft'&&!elapsed&&!changedLock)
   detail.append(formation(race));
  if(race.runners.length){
   const front=race.runners.filter(h=>h.pastFourthCorner==='frontObserved').length;
   const back=race.runners.filter(h=>h.pastFourthCorner==='backObserved').length;
   const mixed=race.runners.filter(h=>h.pastFourthCorner==='mixedObserved').length;
   const unknown=race.runners.length-front-back-mixed;
   detail.append(dom('p','過去4角の位置取り観測：前方 '+front+
     '頭／後方 '+back+'頭／混在 '+mixed+'頭／資料不足 '+unknown+
     '頭（今回の展開予測・適性点数ではありません）','muted'));
  }
  const orderStudy=workoutOrder.get(key);
  if(orderStudy&&!draftExpiredOnDevice(day,race.postTime)&&
     !changedLock){
   const panel=dom('details',undefined,'real-workout-band-order');
   panel.append(dom('summary',
    '調教S/A/B/Cの同評価内を指数で比較（研究用・'+
    orderStudy.runnerCount+'頭）'));
   for(const band of ['S','A','B','C']){
    const peers=orderStudy.runners.filter(h=>h.trainingBand===band);
    if(!peers.length)continue;
    panel.append(dom('p',band+'評価内の指数順：'+peers.map(h=>
     h.number+'番（同'+band+'内'+h.withinBandRank+'位）').join('／'),'muted'));
   }
   panel.append(dom('p','同じS評価でも追切・仕上の弱い方の指数で差を表示。'+
    '指数の原数値・換算30点は出していません。指数内の順位は正式な馬の強さ・'+
    '3連単の1着候補・総合100点ではありません。提供元の公開時刻も未検証。','muted'));
   detail.append(panel);
  }
  if(race.status==='hold'){
   const extra=race.reason==='invalid_two_factor'&&
     Object.hasOwn(RUNNER_ISSUES,race.validationIssue)
     ?'（'+RUNNER_ISSUES[race.validationIssue]+'）'
     :race.reason==='missing_research'&&
       Object.hasOwn(REVIEW_STAGES,race.reviewStage)
      ?'（要確認：'+REVIEW_STAGES[race.reviewStage]+'）':'';
   detail.append(dom('p',REASONS[race.reason]+extra,'hold'));
   const ties=heldTieGroups(race,day);
   if(ties)detail.append(ties);
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
   const horses=dom('details',undefined,'horse-research');
   horses.append(dom('summary','馬ごとの調教・近走の仮評価を見る（'+
    race.runners.length+'頭）'));
   horses.append(dom('p',race.status==='hold'
    ?'見送りRは調教S→A→B→C→未評価の順に参考表示。'+
     '馬番や同ランク内の順序は強さ・総合順位を意味しません。'+
     '近走3点の欠損を推測補完せず、研究用の買い目は作成しません。'
    :'調教30：近走3での仮順位（10項目総合評価ではない）','muted'));
   // Missing recent grades leave nearly every held runner unranked.
   // Display those held horses by the OBSERVED TRAINING BAND only, so
   // stronger workout evidence is visible without inventing recent or
   // a 100-point score. This is a copied display list; the source
   // report, signatures, receipts, and draft formations remain untouched.
   const heldBands={S:0,A:1,B:2,C:3,'未評価':4};
   const displayed=race.status==='hold'
    ?race.runners.slice().sort((a,b)=>
      heldBands[a.training]-heldBands[b.training]||a.number-b.number)
    :race.runners;
   for(const [i,h] of displayed.entries()){
    horses.append(runnerView(h,i));
    const ten=tenRows.get(race.track+'|'+race.race).horses.find(x=>x.number===h.number);
    const tenCard=renderTenHorse(ten,materialByRace.get(key)?.get(h.number),
     !elapsed&&!changedLock&&!draftExpiredOnDevice(day,race.postTime)
      ?automatic?.horses.find(x=>x.number===h.number):null,
     seven?.get(h.number));
    // A later explicit same-day JRDB /tpd read annotates the existing
    // heading, never the grade, tickets or research score.
    if(race.status==='provisional_draft'&&!elapsed&&!changedLock){
     const node=tenCard.children[0];
     prestartBodyMarkers.set(key+'|'+h.number,{node,base:node.textContent});
    }
    horses.append(tenCard);
   }
   detail.append(horses);
  }
  const item=data.sourceMaterials.races.find(x=>
    x.track===race.track&&x.race===race.race);
  if(item){
   const evidence=Object.entries(MATERIAL_LABELS)
    .map(([key,label])=>label+' '+item.counts[key]+'/'+item.runnerCount)
    .join('／');
   detail.append(dom('p','資料の有無（採点ではない）：'+evidence,'muted'));
   if(item.sourceSignals)detail.append(dom('p',
    'JRDBの追加指標の有無（採点なし）：'+
    Object.entries(SOURCE_SIGNAL_LABELS).map(([key,label])=>
     label+' '+item.sourceSignals[key]+'/'+item.runnerCount+'頭').join('／')+
    '。コードや指数の値から勝率・適性を自動推定したものではありません。','muted'));
   detail.append(dom('p','距離適性・馬場・展開・騎手厩舎・ローテの参考採点は、このRの自動採点欄で確認できます。コース実績・馬場適性は未評価で、総合100点は未完成。','muted'));
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
  if(race.status==='provisional_draft'){
   if(elapsed)
    detail.append(dom('p','【発走時刻経過】JRDB暫定発走時刻を端末で再確認し、'+
     '新しい買い目を非表示にしました。保存済みの発走前研究記録は変更しません。'+
     'JRA公式発走時刻は別途確認してください。','hold'));
   else if(fixed.blocked.has(race.track+'|'+race.race))
    detail.append(dom('p',fixed.unavailable
     ?'端末固定記録の確認に失敗。新しい3連単案は非表示。保存済み記録を確認してな。'
     :'【以前の固定買い目と不一致】新しい下書きの3連単を非表示にしました。下の発走前固定履歴を確認してな。',
     'hold'));
  }
  // Append optional study and manual-entry actions AFTER the old
  // racecard: preserve all established content and first-view order.
  if(race.runners.length)detail.append(researchRaceSpotlight(race));
  else detail.append(dom('p','馬番別の仮評価は未取得・照合保留。'+
   '発走後に研究用の買い目を作り直しません。','muted'));
  // Race-only handoff: the recipient parses #select=v1 with a valid
  // date/track/R and does NOT import horse numbers, save or buy tickets.
  const manual=dom('a','このRの3連単を自分で作る（手動・未購入）');
  manual.className='manual-entry-link';
  manual.href='/my-tickets#select=v1&date='+day.slice(0,4)+'-'+
   day.slice(4,6)+'-'+day.slice(6,8)+
   '&track='+encodeURIComponent(race.track)+'&race='+race.race;
  detail.append(manual);
  if(reference){
   // A read-only copy of already checked, visible research; never a
   // second signing, betting, ticket handoff, or result-record action.
   const study=dom('details',undefined,'inline-validated-research');
   study.append(dom('summary','見送りRの参考1・2・3着（'+
    reference.panel.label+'・研究用・購入連携なし）'));
   for(const picks of reference.picks)study.append(dom('p',picks,'picks'));
   study.append(dom('p','比較できた項目だけの研究用参考。'+
    'JRA最終照合・正式100点採点・購入・固定・収支計算は未実施。'+
    '発走予定時刻が過ぎたレースでは非表示になります。','muted'));
   detail.append(study);
  }
  const raceKey=race.track+'|'+race.race;
  nodes.push({key:raceKey,track:race.track,postTime:race.postTime,
   draft:race.status==='provisional_draft'&&!changedLock&&!elapsed,
   holdReason:race.status==='hold'?race.reason:null,node:detail});
  const option=dom('option',race.track+' '+race.race+'R｜'+
   (race.status==='provisional_draft'
    ?elapsed?'発走時刻経過・新案非表示':
      changedLock?'固定済みと不一致・新案非表示':
      '研究用下書き '+race.points+'点':
      reference?'見送り・参考候補あり（研究用）':'見送り'));
  option.value=raceKey;select.append(option);
  groups.set(race.track,(groups.get(race.track)||0)+1);
 }
 // Selection uses an already verified day snapshot. No extra JRDB calls,
 // no prediction reconstruction, no receipt or purchase write.
 function show(track,key='',draftsOnly=false,holdReason=''){
  // Invalidate previous JRA single-R candidate when race selection changes.
  resetResolvedJraCard();
  $('autoOfficialCardUrl').value='';
  $('autoOfficialCardStatus').textContent='選択中のレースではJRA Web出馬表の候補比較は未確認。買い目は無変更です。';
  // A tab or race-selection tap may happen long after the first render.
  // Re-evaluate the local clock before exposing any on-screen formation.
  const expiredNow=data.races.filter(x=>x.status==='provisional_draft'&&
   draftExpiredOnDevice(day,x.postTime)).length;
  // Research references must disappear on late user navigation, too.
  const oldReferenceExpired=quickRows.some(item=>
   draftExpiredOnDevice(day,item.race.postTime));
  if(expiredNow>deviceExpired.size||oldReferenceExpired){
   latestExpiredDraftCount=expiredNow;
   render(data,day); // Display-only, no network or receipt writes.
   $('autoStatus').textContent=oldReferenceExpired
    ?'発走予定時刻を過ぎた見送りRの研究用参考候補を非表示にしました。固定履歴・買い目は変更していません。'
    :'受信後に発走時刻を過ぎた下書きを非表示に更新しました。';
   return;
  }
  const frag=document.createDocumentFragment();
  let visible=0;
  for(const item of nodes){
   if(key?item.key===key:
     holdReason?item.holdReason===holdReason:
     draftsOnly?item.draft:!track||item.track===track){
    item.node.open=Boolean(key);
    frag.append(item.node);visible++;
   }
  }
  host.replaceChildren(frag);
  $('autoViewingStatus').textContent=key
   ?'選択中：'+key.replace('|',' ')+'R。研究用データのみ。'
   :holdReason?'見送り理由：'+SHORT_HOLDS[holdReason]+' '+visible+
     'Rを表示。発走後に新しい買い目は作りません。'
   :draftsOnly?'発走前の研究用下書き '+visible+'Rを表示（確定予想ではありません）'
   :track?track+' '+visible+'Rを表示（正式予想ではありません）'
   :'全場 '+visible+'Rを表示。レース選択で1Rだけ開けます。';
  for(const b of tabs.querySelectorAll('button'))b.setAttribute(
   'aria-pressed',String(!key&&!holdReason&&
    (b.dataset.mode==='drafts'?draftsOnly:
     !draftsOnly&&b.dataset.track===track)));
  for(const b of holdTabs.querySelectorAll('button'))
   b.setAttribute('aria-pressed',String(!key&&b.dataset.reason===holdReason));
  updateNextDraft();
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
  button.type='button';button.dataset.track=track;button.dataset.mode='venue';
  button.setAttribute('aria-pressed','false');
  button.onclick=()=>{select.value='';show(track);};tabs.append(button);
 }
 // A stable sort keeps original programme order for equal HH:MM values.
 const displayableDrafts=nodes.filter(item=>item.draft)
  .sort((a,b)=>a.postTime.localeCompare(b.postTime));
 const nextDraft=$('autoNextDraft');
 function updateNextDraft(){
  // JRDB provisional post-time order only, NEVER an official JRA schedule.
  // A held, locally expired or frozen-conflict R is never a navigation target.
  const current=displayableDrafts.findIndex(item=>item.key===select.value);
  const available=displayableDrafts.length>0&&current<displayableDrafts.length-1;
  nextDraft.disabled=!available;
  nextDraft.textContent=!displayableDrafts.length
   ?'次の下書きRはありません（見送り・未取得）'
   :available?'次の下書きRへ（暫定発走時刻順）':'最後の下書きRです';
 }
 nextDraft.onclick=()=>{
  if(latestDisplayedReport!==data||latestDisplayedDay!==day||
     $('autoDay').value.replaceAll('-','')!==day){
   nextDraft.disabled=true;
   $('autoViewingStatus').textContent=
    '古い開催日の下書きは開けません。開催日を確認してください。';
   return;
  }
  if(nextDraft.disabled)return;
  const position=displayableDrafts.findIndex(item=>item.key===select.value);
  const target=displayableDrafts[position+1];
  if(!target){updateNextDraft();return;}
  select.value=target.key;
  show(target.track,target.key); // Local clock rechecked by show(), no provider call.
 };
 const safeDraftCount=displayableDrafts.length;
 // Reuse ONLY the already validated, time-safe, receipt-compatible primary
 // formations and independently verified-on-screen, UNSIGNED reference
 // previews. Never convert reference-only held R to paid/signed tickets.
 const agreement=validatedDraftFirstAgreement(
  data,day,$('autoProvisionalFactorRaces'));
 renderCombinedResearchRows(data,day,displayableDrafts,quickRows,agreement);
 // Display validated counts only; these are provisional research drafts,
 // never full-ten grades, JRA-verified entries or purchases.
 // Reference-only R are a SUBSET of held races, never extra betting
 // forecasts. Show the same deduplicated, browser-verified count at top.
 const easyCount='全'+data.raceCount+'R｜研究用下書き '+
  safeDraftCount+'R｜見送り '+data.holdCount+'R'+
  (quickRows.length?'（うち発走前参考 '+quickRows.length+'R・未購入）':'');
 const hiddenCount=Math.max(0,data.draftCount-safeDraftCount);
 $('autoEasyPulse').textContent='JRDB2項目方式｜'+easyCount+
  (hiddenCount?'｜新規非表示 '+hiddenCount+'R':'')+
  '（正式10項目・JRA公式照合は未完成）';
 $('autoRaceQuickSummary').textContent=easyCount+
  '。これはJRDB調教・近走2項目方式だけの件数で、登録済みの全レース前日参考予想の件数ではありません。前日参考予想は直下のリンクから見られます。';
 const singleDraft=safeDraftCount===1?displayableDrafts[0]:null;
 const shortcut=$('autoDraftShortcut');
 shortcut.textContent=singleDraft
  ?'買い目あり 1Rだけ見る（'+singleDraft.key.replace('|',' ')+'R）'
  :safeDraftCount?'買い目あり '+safeDraftCount+'Rだけ見る':
  '買い目あり 0R（未作成・見送り）';
 shortcut.onclick=()=>{
  // A held HTTP response, date change, or error must not reopen old
  // predictions. This shortcut only filters the validated local result.
  if(latestDisplayedReport!==data||latestDisplayedDay!==day||
     $('autoDay').value.replaceAll('-','')!==day){
   $('autoViewingStatus').textContent='この開催日の予想は未取得です。日付を確認してください。';
   return;
  }
  select.value=singleDraft?singleDraft.key:'';
  // One available race: show the existing verified racecard already open,
  // without rerunning paid sources or recalculating any betting formation.
  if(singleDraft)show(singleDraft.track,singleDraft.key);
  else show('','',safeDraftCount>0);
 };
 const hiddenByFixed=Math.max(0,data.draftCount-deviceExpired.size-safeDraftCount);
 $('autoHoldBreakdown').textContent=holdBreakdownSummary(data);
 $('autoOperationalNext').textContent=operationalNextStep(
  data,fixed,deviceExpired.size,safeDraftCount);
 $('autoMorningStatus').textContent=morningStatus(
  data,day,localReceiptStatus(day),deviceExpired.size,safeDraftCount);
 if(safeDraftCount>0){
  const draftButton=dom('button','下書きのみ '+safeDraftCount+'R');
  draftButton.type='button';draftButton.dataset.track='';
  draftButton.dataset.mode='drafts';
  draftButton.setAttribute('aria-pressed','false');
  draftButton.onclick=()=>{select.value='';show('','',true);};
  tabs.append(draftButton);
 }
 // Only prevalidated reasons: render a read-only filter from this snapshot.
 // No extra provider requests, no receipt writes and no 10-factor scoring.
 for(const [reason,count] of Object.entries(data.holdReasons)
   .filter(([,n])=>n>0).sort((a,b)=>b[1]-a[1])){
  const button=dom('button',SHORT_HOLDS[reason]+' '+count+'R');
  button.type='button';button.dataset.reason=reason;
  button.setAttribute('aria-pressed','false');
  button.onclick=()=>{select.value='';show('','',false,reason);};
  holdTabs.append(button);
 }
 // When holds (or locally expired/blocked drafts) overwhelm a small
 // set of eligible drafts, put the useful 1/2/3-place cards first — even
 // on a one-venue 12R meeting. Keep the full programme available via 全場.
 // This is display-only: no JRDB read, receipt edit, scoring or purchase.
 const compactForecastFirst=safeDraftCount>0&&safeDraftCount<=8&&
  data.raceCount-safeDraftCount>=8;
 show('', '', compactForecastFirst);
 const breakdown=Object.entries(data.holdReasons).sort((a,b)=>b[1]-a[1])
  .map(([reason,count])=>SHORT_HOLDS[reason]+' '+count+'R').join('／');
 const expandedTies=data.races.filter(r=>
  r.status==='provisional_draft'&&
  r.first.length===2&&r.second.length===6&&r.third.length===6&&
  r.points===40&&!deviceExpired.has(r.track+'|'+r.race)&&
  !fixed.blocked.has(r.track+'|'+r.race)).length;
 $('autoSummary').textContent=data.raceCount+'R中、研究用自動案 '+
  safeDraftCount+'R／見送り '+data.holdCount+'R。'+
  (expandedTies?'同点を切らず2着候補を6頭に拡張 '+expandedTies+
   'R（研究用・40点）。':'')+
  (deviceExpired.size?'端末受信後に発走時刻経過で新案非表示 '+
   deviceExpired.size+'R。':'')+
  (breakdown?'内訳：'+breakdown+'。':'')+
  'JRDBの2項目だけを買い目に使用。コース条件の存在 '+ctx.courseInfoPresentCount+
  'R／馬場資料の存在 '+ctx.goingAvailableCount+'R（適性は未評価）。追加資料：'+
  (data.sourceMaterials.status==='observed'
    ?'血統・枠などの材料を確認（採点なし）'
    :data.sourceMaterials.status==='partial'
     ?'血統・枠などの資料 '+data.sourceMaterials.races.length+
      '/'+data.raceCount+'Rを確認（他のRは照合保留・採点なし）'
     :'照合保留')+
  '。JRA公式照合や正式な投票は未実施。';
 return {visibleCount:safeDraftCount,expiredCount:deviceExpired.size,
  blockedCount:hiddenByFixed};
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
function renderFixedQuick(day,expand=false){
 // A saved prestart record is always history, not a newly produced pick.
 // Read-only: no provider read, ledger write, HMAC issuance, purchase or
 // official-result attestation.
 const panel=$('autoFixedQuickPanel'),rows=$('autoFixedQuickRaces'),
  title=$('autoFixedQuickTitle'),status=$('autoFixedQuickStatus');
 rows.replaceChildren();
 title.textContent='この端末の発走前固定：確認中';
 if(!/^20[0-9]{6}$/.test(day)){
  status.textContent='開催日を選択してください。記録は変更しません。';
  panel.open=false;return 0;
 }
 try{
  const raw=localStorage.getItem(RECEIPTS_KEY);
  if(!raw){
   title.textContent='この端末の発走前固定：0R';
   status.textContent='選択日の保存記録はありません。Safariとホーム画面の保存領域は異なることがあります。';
   panel.open=false;return 0;
  }
  if(raw.length>650000)throw Error('oversized_store');
  // Cross-day corruption must never be promoted as a valid saved ticket.
  validateStoredResearchLedger(JSON.parse(raw));
  const saved=selectedReceiptsForVerification(day).map(x=>x.snapshot)
   .sort((a,b)=>a.track.localeCompare(b.track,'ja')||a.race-b.race);
  title.textContent='この端末の発走前固定：'+saved.length+'R（追加照会なし）';
  status.textContent=saved.length
   ?'最初に固定した研究用買い目をそのまま表示。署名は未検証／JRA公式未照合／実購入なし。'
   :'この日の固定記録はありません。既存の保存内容は変更していません。';
  for(const record of saved){
   const picks=record.trifectaTickets;
   const card=dom('div',undefined,'owner-fixed-card');
   card.append(dom('p',record.track+' '+record.race+'R｜発走前に固定した3連単 '+
    picks.length+'点（100円換算 '+(picks.length*100).toLocaleString('ja-JP')+'円）','muted'));
   for(const [i,label] of ['1着','2着','3着'].entries()){
    const horses=[...new Set(picks.map(x=>x[i]))].sort((a,b)=>a-b);
    card.append(dom('p',label+'に含む：'+horses.map(n=>n+'番').join('・'),'picks'));
   }
   const exact=dom('details');
   exact.append(dom('summary','固定した '+picks.length+'点の組み合わせ'));
   exact.append(dom('p',picks.map(t=>t.join('→')).join(' / '),'ticket-list'));
   card.append(exact);
   rows.append(card);
  }
  panel.open=Boolean(expand&&saved.length);
  return saved.length;
 }catch(_){
  rows.replaceChildren();
  title.textContent='この端末の固定記録：確認が必要';
  status.textContent='保存記録に不整合があるため非表示。元のデータは変更しません。バックアップと署名確認をお願いします。';
  panel.open=false;return 0;
 }
}
function draftExpiredOnDevice(day,postTime){
 // A second CLIENT-SIDE fail-closed check after the server response arrives.
 // The device clock is NOT independently verified, nor is JRDB's off-time
 // an official JRA schedule. Treat either an invalid value or an elapsed
 // provisional off-time as a reason to HIDE an unpurchased new draft.
 if(!/^20[0-9]{6}$/.test(day)||
    typeof postTime!=='string'||
    !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(postTime))return true;
 const iso=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8)+
  'T'+postTime+':00+09:00';
 const off=Date.parse(iso),deviceNow=new Date().getTime();
 return !Number.isFinite(off)||!Number.isFinite(deviceNow)||deviceNow>=off;
}
function saveAutoReceipts(data,day){
 if(data.serverStamped!==true||data.captureAuditVerified!==false||
  !Array.isArray(data.researchReceipts)||data.researchReceipts.length>36||
  data.researchReceiptCount!==data.researchReceipts.length)
  throw Error('署名付き研究記録の形式を確認できません');
 const signed=data.researchReceipts,expectedDay=day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8);
 // Every newly offered draft must have its own server-issued prestart
 // receipt. Otherwise, never display a formation that cannot be locked.
 if(signed.length!==data.draftCount)
  throw Error('研究用下書きと署名付き記録の件数が不一致です');
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
   typeof entry.postTime!=='string'||
   !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(entry.postTime)||
   s.scheduledOffAt!==expectedDay+'T'+entry.postTime+':00+09:00'||
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
 const identities=validateStoredResearchLedger(existing);
 let added=0,expiredSkipped=0;
 const combined=existing.slice();
 const incoming=[];
 for(const receipt of signed){
  const s=receipt.snapshot,id=s.date+'|'+s.track+'|'+s.race;
  if(identities.has(id))continue; // The first research receipt wins.
  const matching=available.get(s.track+'|'+s.race);
  if(draftExpiredOnDevice(day,matching.postTime)){
   expiredSkipped++;continue; // Never first-write a late HTTP response.
  }
  identities.add(id);incoming.push(receipt);combined.push(receipt);added++;
 }
 if(combined.length>360)throw Error('保存数の上限です');
 // Prevalidate both the old and incoming snapshots. A syntactically
 // well-formed server signature is NOT a cryptographic verification,
 // but malformed ticket/timestamps must not poison the local ledger.
 validateStoredResearchLedger(combined);
 if(added){
  // Recheck close to the storage write; a race may expire while the
  // 36R response is being inspected. If this happens, keep other races.
  const fresh=incoming.filter(receipt=>
   !draftExpiredOnDevice(day,
    available.get(receipt.snapshot.track+'|'+receipt.snapshot.race).postTime));
  if(fresh.length!==incoming.length){
   expiredSkipped+=incoming.length-fresh.length;
   added=fresh.length;
   combined.splice(existing.length,combined.length-existing.length,...fresh);
   validateStoredResearchLedger(combined);
  }
 }
 if(added){
  const payload=JSON.stringify(combined);
  if(payload.length>650000)throw Error('端末保存領域の推奨上限を超えます');
  localStorage.setItem(RECEIPTS_KEY,payload);
  // iOS WebKit may be interrupted or the storage layer may fail. A write
  // call returning is not evidence that the immutable record can be read.
  // Never render a new formation if the same bytes cannot be read back.
  if(localStorage.getItem(RECEIPTS_KEY)!==payload)
   throw Error('端末の保存結果を再読込できません');
  if(day===$('autoDay').value.replaceAll('-',''))
   updateSavedResultRaceOptions(day);
 }
 return '署名付き研究記録：新規 '+added+'R／受信後に発走時刻経過で新規保存しなかった'+
  expiredSkipped+'R／既存の固定記録は上書きせず維持。'+
  '保存先はこのiPhone内のみ（Safariとホーム画面で別の場合あり）。';
}

// Separate, signed, read-only research record. Unlike bet receipts this
// contains only training bands and within-band index ranks. The server does
// cryptographic verification before EVER using it with postrace /tse rows.
function validateWorkoutPairReceipt(row,prestart){
 const p=row?.snapshot,b=prestart?.snapshot;
 if(!p||!b||typeof row.signature!=='string'||
    !/^[a-f0-9]{64}$/.test(row.signature)||
    Object.keys(p).sort().join(',')!==
     'actualPurchase,date,modelCalibrated,observedAt,officialJraVerified,pairCounts,predictionReady,prestartSignature,race,researchOnly,resultSourceComplete,runnerCount,scheduledOffAt,sourceKind,sourcePublicationVerified,track,version'||
    p.version!=='owner-workout-pair-observation-receipt-1'||
    p.sourceKind!=='jrdb-tse-provisional-workout-pairs'||
    p.researchOnly!==true||p.officialJraVerified!==false||
    p.resultSourceComplete!==true||p.sourcePublicationVerified!==false||
    p.modelCalibrated!==false||p.predictionReady!==false||
    p.actualPurchase!==false||p.date!==b.date||
    p.track!==b.track||p.race!==b.race||
    p.scheduledOffAt!==b.scheduledOffAt||
    p.prestartSignature!==prestart.signature||
    p.runnerCount!==b.raceRunnerCount||
    !Number.isFinite(Date.parse(p.observedAt))||
    Date.parse(p.observedAt)<Date.parse(p.scheduledOffAt))
  throw Error('保存済み暫定結果の照合形式が不正');
 const bands=['S','A','B','C'],keys=['concordant','discordant','equalIndexExcluded'];
 if(!p.pairCounts||Object.keys(p.pairCounts).sort().join(',')!=='A,B,C,S')
  throw Error('暫定結果の集計帯が不正');
 for(const band of bands){
  const peers=b.horses.filter(h=>h.trainingBand===band);
  const row=p.pairCounts[band];
  if(!row||Object.keys(row).sort().join(',')!==
     'concordant,discordant,equalIndexExcluded'||
     keys.some(key=>!Number.isInteger(row[key])||row[key]<0||row[key]>153))
   throw Error('暫定結果のペア集計が不正');
  const expected=peers.length*(peers.length-1)/2;
  let equal=0;
  for(let i=0;i<peers.length;i++)
   for(let j=i+1;j<peers.length;j++)
    if(peers[i].withinBandRank===peers[j].withinBandRank)equal++;
  if(row.concordant+row.discordant+row.equalIndexExcluded!==expected||
     row.equalIndexExcluded!==equal)
   throw Error('暫定結果の母数が発走前順位と一致しません');
 }
 return p;
}
function savedWorkoutPairEntries(day){
 const raw=localStorage.getItem(WORKOUT_PAIR_STORAGE);
 if(raw&&raw.length>550000)throw Error('調教結果の保存上限');
 const all=JSON.parse(raw||'[]');
 if(!Array.isArray(all)||all.length>360)throw Error('調教結果記録の形式不正');
 const lockRaw=localStorage.getItem(WORKOUT_LOCK_STORAGE);
 if(lockRaw&&lockRaw.length>450000)throw Error('発走前順位の保存上限');
 const lockEntries=JSON.parse(lockRaw||'[]');
 if(!Array.isArray(lockEntries)||lockEntries.length>360)
  throw Error('発走前順位の保存形式不正');
 const frozen=new Map();
 for(const receipt of lockEntries){
  const p=validateWorkoutLockReceipt(receipt),id=p.date+'|'+p.track+'|'+p.race;
  if(frozen.has(id))throw Error('発走前順位が重複');
  frozen.set(id,receipt);
 }
 const found=new Set(),selected=[],totals={};
 for(const band of ['S','A','B','C'])
  totals[band]={concordant:0,discordant:0,equalIndexExcluded:0};
 const days=new Set();
 for(const receipt of all){
  const p=receipt?.snapshot;
  if(!p||typeof p.date!=='string')throw Error('調教の暫定結果記録が不正');
  const id=p.date+'|'+p.track+'|'+p.race;
  if(found.has(id))throw Error('同じレースの暫定結果記録が重複');
  found.add(id);
  validateWorkoutPairReceipt(receipt,frozen.get(id));
  days.add(p.date);
  if(p.date===day)selected.push(receipt);
  for(const band of Object.keys(totals))
   for(const k of Object.keys(totals[band]))
    totals[band][k]+=p.pairCounts[band][k];
 }
 if(selected.length>36)throw Error('選択日の暫定結果が多すぎます');
 return {all,selected,found,days:days.size,totals};
}
function showSavedWorkoutPairHistory(day){
 try{
  const data=savedWorkoutPairEntries(day);
  $('autoWorkoutPairVerify').disabled=!data.selected.length;
  let a=0,b=0,tied=0;
  for(const row of Object.values(data.totals)){
   a+=row.concordant;b+=row.discordant;tied+=row.equalIndexExcluded;
  }
  $('autoWorkoutPairHistory').textContent=
   '初回保存済みのJRDB暫定比較：'+data.days+'開催日・'+data.all.length+
   'R／同ランク内の指数順と着順が一致 '+a+'組、不一致 '+b+
   '組、指数同点 '+tied+'組（比較除外）。'+
   'ペア同士には相関があるため、組数は独立した試行回数ではありません。'+
   '保存済み結果の署名は再検証前。JRA公式未照合・採点校正未完了。';
 }catch(_){
  $('autoWorkoutPairVerify').disabled=true;
  $('autoWorkoutPairHistory').textContent=
   '結果の保存状態が確認できません。元の記録を消さずバックアップを確認。';
 }
}
function saveWorkoutPairReceipts(result,receipts,day){
 if(!Array.isArray(result.pairObservationReceipts)||
    result.pairObservationReceiptCount!==result.pairObservationReceipts.length||
    result.pairObservationReceiptCount!==result.studiedRaceCount||
    result.pairObservationReceiptCount>36)
  throw Error('JRDB暫定結果の署名形式が不正');
 const originals=new Map(receipts.map(row=>{
  const p=validateWorkoutLockReceipt(row);
  return [p.track+'|'+p.race,row];
 }));
 const observed=new Map(result.races.filter(r=>
  r.providerStatus==='complete_provisional_order').map(r=>
  [r.track+'|'+r.race,r]));
 const ids=new Set();
 for(const row of result.pairObservationReceipts){
  const p=row?.snapshot,id=p?.track+'|'+p?.race;
  if(!p||p.date!==day||ids.has(id)||!observed.has(id))
   throw Error('JRDB暫定結果のレース同定失敗');
  ids.add(id);
  validateWorkoutPairReceipt(row,originals.get(id));
  if(JSON.stringify(p.pairCounts)!==JSON.stringify(observed.get(id).pairCounts))
   throw Error('JRDB暫定結果の署名と集計不一致');
 }
 if(ids.size!==observed.size)
  throw Error('JRDB暫定結果の固定数が一致しません');
 const {all,found}=savedWorkoutPairEntries(day);
 const combined=all.slice();
 let added=0,previous=0;
 for(const row of result.pairObservationReceipts){
  const p=row.snapshot,id=p.date+'|'+p.track+'|'+p.race;
  if(found.has(id)){previous++;continue;}
  combined.push(row);found.add(id);added++;
 }
 if(combined.length>360)throw Error('暫定結果の保存件数上限');
 if(added){
  const payload=JSON.stringify(combined);
  if(payload.length>550000)throw Error('暫定結果記録の容量上限');
  localStorage.setItem(WORKOUT_PAIR_STORAGE,payload);
  if(localStorage.getItem(WORKOUT_PAIR_STORAGE)!==payload)
   throw Error('結果保存を再確認できません');
 }
 showSavedWorkoutPairHistory(day);
 return {added,previous};
}
// New independent HMAC domain: pairs across different original training
// grades. Kept completely separate from the older within-grade receipts.
const CROSS_GRADE_KEYS=['S>A','S>B','S>C','A>B','A>C','B>C'];
function validateWorkoutCrossReceipt(entry,prestart){
 const p=entry?.snapshot,b=prestart?.snapshot;
 const fields=['version','date','track','race','sourceKind','observedAt',
  'scheduledOffAt','prestartSignature','runnerCount','crossBandPairs',
  'researchOnly','officialJraVerified','resultSourceComplete',
  'sourcePublicationVerified','modelCalibrated','predictionReady',
  'actualPurchase'];
 if(!p||!b||Object.keys(entry).sort().join(',')!=='signature,snapshot'||
    !/^[a-f0-9]{64}$/.test(entry.signature||'')||
    Object.keys(p).sort().join(',')!==fields.sort().join(',')||
    p.version!=='owner-workout-cross-band-observation-1'||
    p.sourceKind!=='jrdb-tse-cross-band-training-research'||
    p.researchOnly!==true||p.officialJraVerified!==false||
    p.resultSourceComplete!==true||p.sourcePublicationVerified!==false||
    p.modelCalibrated!==false||p.predictionReady!==false||
    p.actualPurchase!==false||p.date!==b.date||p.track!==b.track||
    p.race!==b.race||p.scheduledOffAt!==b.scheduledOffAt||
    p.prestartSignature!==prestart.signature||
    p.runnerCount!==b.raceRunnerCount||
    !Number.isFinite(Date.parse(p.observedAt))||
    Date.parse(p.observedAt)<Date.parse(p.scheduledOffAt))
  throw Error('ランク間の署名記録に不整合');
 if(!p.crossBandPairs||
    Object.keys(p.crossBandPairs).sort().join(',')!==
     CROSS_GRADE_KEYS.slice().sort().join(','))
  throw Error('ランク間の比較ペア種が不正');
 for(const key of CROSS_GRADE_KEYS){
  const row=p.crossBandPairs[key],labels=key.split('>');
  if(!row||Object.keys(row).sort().join(',')!=='concordant,discordant'||
     !Number.isInteger(row.concordant)||!Number.isInteger(row.discordant)||
     row.concordant<0||row.discordant<0||
     row.concordant+row.discordant!==
       b.horses.filter(h=>h.trainingBand===labels[0]).length*
       b.horses.filter(h=>h.trainingBand===labels[1]).length)
   throw Error('ランク間の比較母数が発走前評価と不一致');
 }
 return p;
}
function savedWorkoutCrossEntries(day){
 const raw=localStorage.getItem(WORKOUT_CROSS_STORAGE);
 if(raw&&raw.length>440000)throw Error('ランク間研究記録の容量上限');
 const all=JSON.parse(raw||'[]');
 if(!Array.isArray(all)||all.length>360)
  throw Error('ランク間研究記録の件数が不正');
 const lockRaw=localStorage.getItem(WORKOUT_LOCK_STORAGE);
 if(lockRaw&&lockRaw.length>450000)throw Error('調教順位固定の容量上限');
 const locks=JSON.parse(lockRaw||'[]');
 if(!Array.isArray(locks)||locks.length>360)
  throw Error('調教順位固定の形式不正');
 const before=new Map();
 for(const row of locks){
  const p=validateWorkoutLockReceipt(row),id=p.date+'|'+p.track+'|'+p.race;
  if(before.has(id))throw Error('調教順位固定の重複');
  before.set(id,row);
 }
 const seen=new Set(),selected=[],days=new Set(),totals=
  Object.fromEntries(CROSS_GRADE_KEYS.map(k=>[
    k,{concordant:0,discordant:0}]));
 for(const entry of all){
  const p=entry?.snapshot;
  if(!p)throw Error('ランク間研究記録の内容不正');
  const id=p.date+'|'+p.track+'|'+p.race;
  if(seen.has(id))throw Error('ランク間研究記録の二重固定');
  seen.add(id);validateWorkoutCrossReceipt(entry,before.get(id));
  days.add(p.date);
  if(p.date===day)selected.push(entry);
  for(const k of CROSS_GRADE_KEYS){
   totals[k].concordant+=p.crossBandPairs[k].concordant;
   totals[k].discordant+=p.crossBandPairs[k].discordant;
  }
 }
 if(selected.length>36)throw Error('調教ランク間の同日件数が不正');
 return {all,selected,seen,days:days.size,totals};
}
function showSavedWorkoutCrossHistory(day){
 try{
  const d=savedWorkoutCrossEntries(day);
  $('autoWorkoutCrossVerify').disabled=!d.selected.length;
  const good=Object.values(d.totals).reduce((a,r)=>a+r.concordant,0);
  const opposite=Object.values(d.totals).reduce((a,r)=>a+r.discordant,0);
  $('autoWorkoutCrossHistory').textContent=
   '調教ランク間の初回固定：'+d.days+'開催日・'+d.all.length+
   'R／上位評価が先着 '+good+'組／逆転 '+opposite+
   '組。複数ペアは独立した試行ではありません。'+
   '保存済み記録の署名は未再検証、JRA公式結果・調教30点は未確認。';
 }catch(_){
  $('autoWorkoutCrossVerify').disabled=true;
  $('autoWorkoutCrossHistory').textContent=
   'ランク間研究記録の整合性を確認できません。元のデータは変更していません。';
 }
}
function saveWorkoutCrossReceipts(result,receipts,day){
 if(!Array.isArray(result.crossBandObservationReceipts)||
    result.crossBandObservationReceiptCount!==
      result.crossBandObservationReceipts.length||
    result.crossBandObservationReceiptCount!==result.studiedRaceCount||
    result.crossBandObservationReceiptCount>36)
  throw Error('ランク間研究の署名件数が不正');
 const originals=new Map(receipts.map(row=>{
  const p=validateWorkoutLockReceipt(row);
  return [p.track+'|'+p.race,row];
 }));
 const studied=new Map(result.races.filter(r=>
  r.providerStatus==='complete_provisional_order').map(r=>
  [r.track+'|'+r.race,r]));
 const counted=new Set();
 for(const row of result.crossBandObservationReceipts){
  const p=row?.snapshot,id=p?.track+'|'+p?.race;
  if(!p||p.date!==day||counted.has(id)||!studied.has(id))
   throw Error('ランク間研究の対象R不正');
  counted.add(id);
  validateWorkoutCrossReceipt(row,originals.get(id));
  for(const k of CROSS_GRADE_KEYS)
   if(JSON.stringify(p.crossBandPairs[k])!==
      JSON.stringify(studied.get(id).crossBandPairs[k]))
    throw Error('ランク間署名の結果ペアが不一致');
 }
 if(counted.size!==studied.size)
  throw Error('ランク間研究記録の対象数が不一致');
 const {all,seen}=savedWorkoutCrossEntries(day);
 const next=all.slice();let added=0,previous=0;
 for(const item of result.crossBandObservationReceipts){
  const p=item.snapshot,id=p.date+'|'+p.track+'|'+p.race;
  if(seen.has(id)){previous++;continue;}
  next.push(item);seen.add(id);added++;
 }
 if(next.length>360)throw Error('ランク間研究の保存上限');
 if(added){
  const payload=JSON.stringify(next);
  if(payload.length>440000)throw Error('ランク間研究の容量上限');
  localStorage.setItem(WORKOUT_CROSS_STORAGE,payload);
  if(localStorage.getItem(WORKOUT_CROSS_STORAGE)!==payload)
   throw Error('ランク間研究の保存再確認失敗');
 }
 showSavedWorkoutCrossHistory(day);
 return {added,previous};
}
function validateWorkoutLockReceipt(receipt){
 const p=receipt?.snapshot;
 if(!p||typeof receipt.signature!=='string'||
    !/^[a-f0-9]{64}$/.test(receipt.signature)||
    p.version!=='owner-workout-order-lock-1'||
    p.sourceKind!=='prestart-workout-index-order'||
    p.researchOnly!==true||p.officialJraVerified!==false||
    p.modelCalibrated!==false||p.predictionReady!==false||
    p.actualPurchase!==false||typeof p.date!=='string'||
    !/^20\d{6}$/.test(p.date)||
    !['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'].includes(p.track)||
    !Number.isInteger(p.race)||p.race<1||p.race>12||
    !Number.isInteger(p.raceRunnerCount)||p.raceRunnerCount<2||
    p.raceRunnerCount>18||!Array.isArray(p.horses)||
    p.horses.length!==p.raceRunnerCount||
    typeof p.capturedAt!=='string'||typeof p.scheduledOffAt!=='string'||
    !Number.isFinite(Date.parse(p.capturedAt))||
    !Number.isFinite(Date.parse(p.scheduledOffAt))||
    Date.parse(p.capturedAt)>=Date.parse(p.scheduledOffAt))
  throw Error('調教順位の固定記録が不正');
 const off=new Date(p.scheduledOffAt).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'}).replaceAll('-','');
 if(off!==p.date)throw Error('発走日付不一致');
 let last=0;
 const groups={S:[],A:[],B:[],C:[]};
 for(const h of p.horses){
  if(!h||Object.keys(h).sort().join(',')!=='number,trainingBand,withinBandRank'||
     !Number.isInteger(h.number)||h.number<=last||h.number>18||
     !Object.hasOwn(groups,h.trainingBand)||
     !Number.isInteger(h.withinBandRank)||h.withinBandRank<1||
     h.withinBandRank>18)
   throw Error('調教順位の馬番データ不一致');
  groups[h.trainingBand].push(h.withinBandRank);
  last=h.number;
 }
 for(const ranks of Object.values(groups)){
  const unique=[...new Set(ranks)].sort((a,b)=>a-b);
  if(unique.length&&unique[0]!==1)throw Error('調教指数内順位が不正');
  for(let i=1;i<unique.length;i++)
   if(unique[i]!==ranks.filter(x=>x<=unique[i-1]).length+1)
    throw Error('調教指数内の同順位が不正');
 }
 return p;
}
function savedWorkoutLocksDay(day){
 if(!/^20\d{6}$/.test(day))throw Error('開催日不正');
 const raw=localStorage.getItem(WORKOUT_LOCK_STORAGE);
 if(raw&&raw.length>450000)throw Error('固定調教記録の保存上限');
 const all=JSON.parse(raw||'[]');
 if(!Array.isArray(all)||all.length>360)throw Error('固定調教記録の形式不正');
 const ids=new Set(),selected=[];
 for(const row of all){
  const p=validateWorkoutLockReceipt(row),id=p.date+'|'+p.track+'|'+p.race;
  if(ids.has(id))throw Error('固定調教記録の重複');
  ids.add(id);
  if(p.date===day)selected.push(row);
 }
 if(selected.length>36)throw Error('選択日の固定調教記録が多すぎます');
 return {all,selected,ids};
}
function showSavedWorkoutLocks(day){
 try{
  const {selected}=savedWorkoutLocksDay(day);
  $('autoWorkoutProviderCheck').disabled=!selected.length;
  $('autoWorkoutLockStatus').textContent=selected.length?
   'この端末に初回固定した発走前調教指数内順位 '+selected.length+
   'R。署名の暗号学的確認は結果比較時に実施。正式採点・買い目・収支は変更しません。':
   'この日の発走前調教指数順位は未保存。開催日の発走前取得から記録します。';
 }catch(_){
  $('autoWorkoutProviderCheck').disabled=true;
  $('autoWorkoutLockStatus').textContent=
   '調教指数の固定記録を読み取れません。保存済みデータを消さずに確認してください。';
 }
}
function saveWorkoutLocks(data,day){
 if(!Object.hasOwn(data,'workoutOrderReceipts')){
  showSavedWorkoutLocks(day);return;
 }
 if(!Array.isArray(data.workoutOrderReceipts)||
    data.workoutOrderReceipts.length>36||
    data.workoutOrderReceiptCount!==data.workoutOrderReceipts.length)
  throw Error('調教研究記録の件数不正');
 const study=validateWorkoutIndexOrder(data,day),drafts=new Map(
  data.races.map(r=>[r.track+'|'+r.race,r]));
 const fresh=new Set();
 for(const receipt of data.workoutOrderReceipts){
  const p=validateWorkoutLockReceipt(receipt),id=p.track+'|'+p.race,
        group=study.get(id),race=drafts.get(id);
  if(p.date!==day||fresh.has(id)||!group||!race||
     race.postTime!==new Date(p.scheduledOffAt).toLocaleTimeString('en-GB',{
       timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit',hour12:false
     })||
     JSON.stringify(group.runners.slice().sort((a,b)=>a.number-b.number))!==
     JSON.stringify(p.horses))
   throw Error('調教研究記録と取得資料が不一致');
  fresh.add(id);
 }
 const {all,ids}=savedWorkoutLocksDay(day),next=all.slice();
 let added=0,unchanged=0;
 for(const receipt of data.workoutOrderReceipts){
  const p=receipt.snapshot,id=p.date+'|'+p.track+'|'+p.race;
  if(ids.has(id)){unchanged++;continue;} // immutable first-write wins
  ids.add(id);next.push(receipt);added++;
 }
 if(next.length>360)throw Error('調教研究記録の保存上限');
 if(added){
  const data=JSON.stringify(next);
  if(data.length>450000)throw Error('調教研究記録の容量上限');
  localStorage.setItem(WORKOUT_LOCK_STORAGE,data);
  if(localStorage.getItem(WORKOUT_LOCK_STORAGE)!==data)
   throw Error('調教研究記録の保存確認失敗');
 }
 showSavedWorkoutLocks(day);
 $('autoWorkoutLockStatus').textContent+=' 今回新規 '+added+'R／初回記録を維持 '+unchanged+'R。';
}
const WATCH_STORAGE='keiba-nine-owner-rebound-watch-receipts-v1';
const CORE_STORAGE='keiba-nine-owner-three-core-receipts-v1';
const FIVE_STORAGE='keiba-nine-owner-five-core-receipts-v1';
const R6_DRAFT_STORAGE='keiba-nine-owner-research6-draft-receipts-v1';
const SPARSE_RESEARCH_STORAGE='keiba-nine-owner-sparse-five-reference-receipts-v1';
const STAFF_STUDY_STORAGE='keiba-nine-owner-staff-study-sessions-v1';
let fiveQuickReadDay='';
let tchStudySeq=0,trainingCompareSeq=0;
const AUTO_FIVE_CONSENT_KEY='keiba-nine-owner-five-weekend-consent-v1';
const AUTO_FIVE_ONCE_KEY='keiba-nine-owner-five-weekend-attempt-v1';
let request=0,followingToday=true,preflightSeq=0,
 latestDisplayedDay='',latestDisplayedReport=null,latestReadAtMs=0,
 latestExpiredDraftCount=0,historySeq=0,watchResultSeq=0,
 prestartSeq=0,connectionSeq=0,receiptVerifySeq=0,archiveReadSeq=0,
 r6VerifySeq=0,staffArchiveVerifySeq=0,
 officialPdfSeq=0,coreVerifySeq=0,coreProviderSeq=0,fiveProviderSeq=0,
 jraDraftTracks=new Set(),jraPdfTracks=new Set(),jraPdfChecked=false,
 historyDay='',historyCoordinates=new Set(),
 historyRosters=new Map(),historyReboundWatch=new Map(),historyStyles=new Map(),
 historyGrades=new Map(),historyStatuses=new Map();
// Source-presence notes from an explicit /tpd read live only in this view.
let prestartBodyMarkers=new Map();
function clearPrestartBodyNotes(){
 for(const marker of prestartBodyMarkers.values())
  marker.node.textContent=marker.base;
}
function applyPrestartBodyNotes(rows,day,report){
 if(!report||latestDisplayedDay!==day||latestDisplayedReport!==report||
    report.date!==day||!Array.isArray(report.races)||
    !Array.isArray(rows)||rows.length!==report.raceCount)return 0;
 const expected=new Map(report.races.map(r=>[r.track+'|'+r.race,r]));
 if(expected.size!==report.races.length)return 0;
 let added=0;
 for(const row of rows){
  const key=row.track+'|'+row.race,base=expected.get(key);
  if(!base||base.status!=='provisional_draft'||base.horseCount!==row.registered||
     !Array.isArray(base.runners)||base.runners.length!==row.registered||
     draftExpiredOnDevice(day,base.postTime))continue;
  const numbers=new Set(base.runners.map(h=>h.number));
  if(numbers.size!==base.runners.length||row.runners.length!==numbers.size||
     row.runners.some(h=>!numbers.has(h.number)))continue;
  for(const h of row.runners){
   const marker=prestartBodyMarkers.get(key+'|'+h.number);
   if(!marker)continue;
   const observed=h.bodyWeightRecorded&&h.weightChangeRecorded;
   marker.node.textContent=marker.base+
    (observed?'｜JRDB直前馬体：体重＋前走比あり':'｜JRDB直前馬体：資料不足')+
    '（JRA未照合・馬体1点は未評価）';
   added++;
  }
 }
 return added;
}
function clearHistory(){
 fiveProviderSeq++;
 $('autoFiveProviderRaces').replaceChildren();
 $('autoFiveProviderStatus').textContent='固定85点の暫定成績比較は未実行。公式結果ではありません。';
 coreProviderSeq++;
 $('autoCoreProviderRaces').replaceChildren();
 $('autoCoreProviderStatus').textContent='研究値のレース後比較は未実行。既存記録は変更していません。';
 coreVerifySeq++;
 $('autoCoreVerify').disabled=false;
 $('autoCoreVerifyStatus').textContent='署名は未確認。研究値は正式100点ではありません。';
 showSavedCore($('autoDay').value.replaceAll('-',''));
 showSavedFive($('autoDay').value.replaceAll('-',''));
 showSavedResearch6Drafts($('autoDay').value.replaceAll('-',''));
 showSavedStaffStudySessions();
 staffArchiveVerifySeq++;
 $('autoHistoryStaffArchiveVerifyStatus').textContent='研究記録の署名はこの選択では未検証。';
 r6VerifySeq++;
 $('autoResearch6DraftVerifyStatus').textContent='固定79点下書きの署名は未確認です。';
 officialPdfSeq++;
 $('autoOfficialPdf').disabled=false;
 $('autoOfficialPdfStatus').textContent='公式PDFリンクは未確認。出馬表の内容を自動照合していません。';
 $('autoOfficialPdfLinks').replaceChildren();
 jraDraftTracks=new Set();jraPdfTracks=new Set();jraPdfChecked=false;
 updateJraReleaseGuide();updateJraCrosscheck();
 archiveReadSeq++;
 $('autoArchiveRead').disabled=false;
 $('autoArchiveStatus').textContent='サーバー保存済みの研究記録は未確認です。';
 $('autoArchiveRaces').replaceChildren();
 receiptVerifySeq++;
 $('autoReceiptVerify').disabled=false;
 $('autoReceiptVerifyStatus').textContent='署名は未確認。保存済み記録は変更していません。';
 connectionSeq++;
 $('autoConnectionCheck').disabled=false;
 $('autoConnectionStatus').textContent='診断は未実行。';
 prestartSeq++;
 clearPrestartBodyNotes();
 $('autoPrestartRaces').replaceChildren();
 $('autoPrestartStatus').textContent='本人操作時だけ追加API照合。予想や買い目は変更しません。';
 $('autoPrestartBody').disabled=false;
 historySeq++;historyDay='';historyCoordinates=new Set();
 historyRosters=new Map();historyReboundWatch=new Map();historyStyles=new Map();
 historyGrades=new Map();historyStatuses=new Map();
 $('autoHistoryAudit').disabled=true;
 tchStudySeq++;trainingCompareSeq++;
 $('autoTcyTchCompare').disabled=true;
 $('autoTcyTchRaces').replaceChildren();
 $('autoTcyTchStatus').textContent=
  '開催日の基本資料を取得後、本人が押した時だけ調教2資料を比較できます。';
 $('autoMainWorkoutCheck').disabled=true;
 $('autoMainWorkoutRaces').replaceChildren();
 $('autoMainWorkoutStatus').textContent=
  '基本資料の取得後、発走前の当日だけ本追切を照合できます。';
 renderSparseFiveReference(null,$('autoDay').value.replaceAll('-',''));
 renderSavedSparse($('autoDay').value.replaceAll('-',''));
 fiveQuickReadDay='';
 $('autoFiveQuick').disabled=true;
 $('autoFiveQuickStatus').textContent='基本資料の取得前です。過去番組は追加照会していません。';
 renderFiveQuickSaved($('autoDay').value.replaceAll('-',''));
 $('autoHistoryAuditRaces').replaceChildren();
 $('autoHistoryAuditStatus').textContent='暫定予想の取得後に利用できます。';
 $('autoHistoryStaffStatus').textContent='過去1Rの騎手・厩舎追加照合はまだ未実行。';
 $('autoHistoryWatchSave').textContent='発走前の候補記録は未確認。';
 watchResultSeq++;
 $('autoWatchResultRaces').replaceChildren();
 $('autoWatchResultStatus').textContent='発走前の固定候補がありません。';
 refreshWatchResultsAvailability();
}
// Signed pre-off, owner-only observations, not prediction purchases.
// Use immutable first write per race and NEVER overwrite on recomputation.
function savedCoreDay(day){
 if(!/^20[0-9]{6}$/.test(day))throw Error('研究記録の日付が不正');
 const raw=localStorage.getItem(CORE_STORAGE);
 if(raw&&raw.length>1800000)throw Error('研究記録が大きすぎます');
 const all=JSON.parse(raw||'[]');
 if(!Array.isArray(all)||all.length>360)throw Error('研究記録の保存形式が不正');
 const seen=new Set(),selected=[];
 for(const item of all){
  const p=item?.snapshot;
  if(!p||typeof item.signature!=='string'||!/^[a-f0-9]{64}$/.test(item.signature)||
     p.version!=='owner-three-core-receipt-1'||
     p.sourceKind!=='prestart-uncalibrated-70-research'||
     p.researchOnly!==true||p.officialJraVerified!==false||
     p.sourceHypothesesUncalibrated!==true||
     p.actualPurchase!==false||p.predictionReady!==false||
     !Number.isInteger(p.race)||p.race<1||p.race>12||
     typeof p.track!=='string'||typeof p.date!=='string'||
     !Array.isArray(p.horses)||p.horses.length<1||p.horses.length>18||
     p.observedRunnerCount!==p.horses.length||
     !Number.isInteger(p.raceRunnerCount)||p.raceRunnerCount<p.horses.length||
     p.raceRunnerCount>18)
    throw Error('保存済みの70点研究記録が不正');
  const key=p.date+'|'+p.track+'|'+p.race;
  if(seen.has(key))throw Error('研究記録に重複あり');
  seen.add(key);
  if(p.date===day)selected.push(item);
 }
 if(selected.length>36)throw Error('開催日の研究記録が多すぎます');
 return selected;
}
function showSavedCore(day){
 $('autoCoreSaved').replaceChildren();
 try{
  const records=savedCoreDay(day);
  $('autoCoreProviderCheck').disabled=!records.length;
  $('autoCoreSaveStatus').textContent=records.length
   ?'端末に初回固定した70点研究値 '+records.length+
     'R。現在の署名は未検証。3連単・正式回収率には含めません。'
   :'この日の固定済み70点研究記録はありません。発走後に新しい研究値は作りません。';
  for(const row of records){
   const p=row.snapshot,card=dom('details');
   card.append(dom('summary',p.track+' '+p.race+'R｜研究用70点・'+p.horses.length+'頭分'),
    dom('p','固定 '+p.capturedAt+'／JRDB暫定発走 '+p.scheduledOffAt+
     '。公式出走確認・成績未照合。','muted'));
   for(const horse of p.horses){
    card.append(dom('p',horse.number+'番｜調教 '+horse.bands.training+
     '・コース '+horse.bands.course_distance+'・展開 '+horse.bands.pace+
     '｜研究値 '+(horse.rawThirdPoints/3).toFixed(2)+'/70点','muted'));
   }
   $('autoCoreSaved').append(card);
  }
 }catch(_){
  $('autoCoreProviderCheck').disabled=true;
  $('autoCoreSaveStatus').textContent=
   '保存済み70点研究記録を確認できません。元データを削除・上書きせずバックアップを確保してください。';
 }
}
function validateCoreCapture(capture,rows,day){
 if(!capture||capture.version!=='owner-three-core-receipt-1'||
    capture.date!==day||capture.serverSigned!==true||
    capture.researchOnly!==true||capture.privateOwnerOnly!==true||
    capture.jraScheduleVerified!==false||
    capture.officialResultsVerified!==false||
    capture.calibrationReady!==false||capture.bettingReady!==false||
    capture.actualPurchase!==false||
    !Number.isInteger(capture.receiptCount)||
    capture.receiptCount<0||capture.receiptCount>36||
    !Number.isInteger(capture.postOffOrMissingTimeRaces)||
    capture.postOffOrMissingTimeRaces<0||
    !Array.isArray(capture.receipts)||
    capture.receipts.length!==capture.receiptCount)
  throw Error('70点研究の署名記録が不正');
 const byRace=new Map(rows.filter(r=>r.ownerRunnerDetails?.threeCore).map(r=>[
  r.track+'|'+r.race,r.ownerRunnerDetails.threeCore
 ]));
 const seen=new Set(),points={S:3,A:2,B:1,C:0},
       weights={training:30,course_distance:20,pace:20};
 for(const record of capture.receipts){
  const p=record?.snapshot,identity=p?.track+'|'+p?.race,
        source=byRace.get(identity);
  if(!p||typeof record.signature!=='string'||
     !/^[a-f0-9]{64}$/.test(record.signature)||
     !source||seen.has(identity)||p.version!==capture.version||
     p.date!==day||p.sourceKind!=='prestart-uncalibrated-70-research'||
     p.researchOnly!==true||p.officialJraVerified!==false||
     p.sourceHypothesesUncalibrated!==true||
     p.actualPurchase!==false||p.predictionReady!==false||
     typeof p.capturedAt!=='string'||typeof p.scheduledOffAt!=='string'||
     p.raceRunnerCount!==source.runnerCount||
     !Array.isArray(p.horses)||p.horses.length<1||
     p.horses.length>18||p.observedRunnerCount!==p.horses.length||
     p.observedRunnerCount>p.raceRunnerCount)
    throw Error('70点研究の開催日・馬番が不一致');
  seen.add(identity);
  const captured=Date.parse(p.capturedAt),off=Date.parse(p.scheduledOffAt);
  if(!Number.isFinite(captured)||!Number.isFinite(off)||
     captured>=off||off-captured>7*86400000||
     new Date(off).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'})
      .replaceAll('-','')!==day)
   throw Error('70点研究が発走前に固定されていません');
  const horseMap=new Map(source.horses.map(h=>[h.number,h])),used=new Set();
  let prev=0;
  for(const h of p.horses){
   const original=horseMap.get(h?.number);
   if(!original||!Number.isInteger(h.number)||h.number<=prev||h.number>18||
      used.has(h.number)||!h.bands||
      Object.keys(h.bands).length!==3||
      Object.keys(weights).some(k=>
       h.bands[k]!==original.bands[k]||
       !Object.hasOwn(points,h.bands[k]))||
      !Number.isInteger(h.rawThirdPoints)||
      h.rawThirdPoints!==original.rawThirdPoints||
      h.rawThirdPoints!==Object.keys(weights).reduce(
       (n,k)=>n+weights[k]*points[h.bands[k]],0))
    throw Error('70点研究の元資料に不一致');
   used.add(h.number);prev=h.number;
  }
  if(used.size!==source.completeCoreObserved||
     source.horses.some(h=>(h.rawThirdPoints!==null)!==used.has(h.number)))
   throw Error('70点研究の評価頭数が不一致');
 }
 return capture.receipts;
}
function saveCoreReceipts(receipts){
 if(!receipts.length)return '発走前に固定できる研究用70点はありません。';
 const raw=localStorage.getItem(CORE_STORAGE);
 if(raw&&raw.length>1800000)throw Error('研究記録が大きすぎます');
 const previous=JSON.parse(raw||'[]');
 if(!Array.isArray(previous)||previous.length>360)
  throw Error('研究記録の保存形式が不正');
 const used=new Set();
 for(const record of previous){
  const p=record?.snapshot;
  if(!p||typeof record.signature!=='string'||
     !/^[a-f0-9]{64}$/.test(record.signature))
   throw Error('以前の研究記録が不正');
  const id=p.date+'|'+p.track+'|'+p.race;
  if(used.has(id))throw Error('以前の研究記録に重複');
  used.add(id);
 }
 const combined=previous.slice();let added=0,existing=0;
 for(const record of receipts){
  const p=record.snapshot,id=p.date+'|'+p.track+'|'+p.race;
  if(used.has(id)){existing++;continue;}
  used.add(id);combined.push(record);added++;
 }
 if(combined.length>360||JSON.stringify(combined).length>1800000)
  throw Error('70点研究記録の保存上限');
 if(added)localStorage.setItem(CORE_STORAGE,JSON.stringify(combined));
 return '発走前研究値を初回固定：新規 '+added+'R／既存 '+existing+
  'R（上書きなし）。署名付き、予測精度・正式結果は未検証。';
}

function validateSavedFiveEntry(entry){
 const p=entry?.snapshot,keys=['training','course_distance','pace','ground','recent'],
       weights={training:30,course_distance:20,pace:20,ground:12,recent:3},
       points={S:3,A:2,B:1,C:0};
 if(!p||typeof entry.signature!=='string'||
    !/^[a-f0-9]{64}$/.test(entry.signature)||
    p.version!=='owner-five-core-receipt-1'||
    p.sourceKind!=='prestart-uncalibrated-85-research'||
    p.researchOnly!==true||p.sourceHypothesesUncalibrated!==true||
    p.officialJraVerified!==false||p.predictionReady!==false||
    p.actualPurchase!==false||!/^20\d{6}$/.test(p.date)||
    !['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉'].includes(p.track)||
    !Number.isInteger(p.race)||p.race<1||p.race>12||
    !Number.isInteger(p.raceRunnerCount)||p.raceRunnerCount<1||
    p.raceRunnerCount>18||!Array.isArray(p.horses)||
    !Number.isInteger(p.observedRunnerCount)||
    p.observedRunnerCount<1||p.observedRunnerCount>p.raceRunnerCount||
    p.observedRunnerCount!==p.horses.length||
    Object.keys(p).length!==15||
    typeof p.capturedAt!=='string'||typeof p.scheduledOffAt!=='string')
  throw Error('85点研究の署名付き記録の構造が不正');
 const captured=Date.parse(p.capturedAt),off=Date.parse(p.scheduledOffAt);
 if(!Number.isFinite(captured)||!Number.isFinite(off)||captured>=off||
    off-captured>7*86400000||
    new Date(off).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'})
      .replaceAll('-','')!==p.date)
  throw Error('85点研究の保存時刻が不正');
 let previous=0;
 for(const horse of p.horses){
  if(!horse||Object.keys(horse).length!==3||!Number.isInteger(horse.number)||
     horse.number<=previous||horse.number>18||
     !horse.bands||Object.keys(horse.bands).length!==5||
     keys.some(k=>!Object.hasOwn(points,horse.bands[k]))||
     !Number.isInteger(horse.rawThirdPoints)||
     horse.rawThirdPoints!==keys.reduce(
      (sum,k)=>sum+weights[k]*points[horse.bands[k]],0))
   throw Error('85点研究の馬番・計算値が不正');
  previous=horse.number;
 }
 return p;
}
function savedFiveDay(day){
 if(!/^20\d{6}$/.test(day))throw Error('開催日が不正');
 const raw=localStorage.getItem(FIVE_STORAGE);
 if(raw&&raw.length>2000000)throw Error('85点記録が大きすぎます');
 const all=JSON.parse(raw||'[]');
 if(!Array.isArray(all)||all.length>360)throw Error('85点の保存数が不正');
 const keys=new Set(),picked=[];
 for(const entry of all){
  const p=validateSavedFiveEntry(entry),key=p.date+'|'+p.track+'|'+p.race;
  if(keys.has(key))throw Error('保存済み85点の競馬場・R重複');
  keys.add(key);if(p.date===day)picked.push(entry);
 }
 if(picked.length>36)throw Error('85点の開催日記録が多すぎます');
 return {all,picked};
}
function showSavedFive(day){
 $('autoFiveSaved').replaceChildren();
 try{
  const {picked}=savedFiveDay(day);
  $('autoFiveProviderCheck').disabled=!picked.length;
  $('autoFiveSaveStatus').textContent=picked.length?
   'この端末に初回固定した研究85点 '+picked.length+
    'R。署名はこの表示では未検証。正式100点・結果・回収率に加算しません。':
   'この日には固定した85点研究値がありません。発走後の後付け生成は禁止。';
  for(const row of picked){
   const p=row.snapshot,card=dom('details');
   card.append(dom('summary',p.track+p.race+'R｜研究85点・'+p.horses.length+'頭分'));
   for(const h of p.horses)
    card.append(dom('p',h.number+'番｜調教 '+h.bands.training+
     '／近走 '+h.bands.recent+'／コース '+h.bands.course_distance+
     '／展開 '+h.bands.pace+'／馬場 '+h.bands.ground+
     '｜研究比較値 '+(h.rawThirdPoints/3).toFixed(2)+'/85（未検証）','muted'));
   $('autoFiveSaved').append(card);
  }
 }catch(_){
  $('autoFiveProviderCheck').disabled=true;
  $('autoFiveSaveStatus').textContent=
   '保存済み85点研究の確認不可。既存データを消さず、バックアップを確保してください。';
 }
}
function validateFiveCapture(capture,rows,day){
 if(!capture||capture.version!=='owner-five-core-receipt-1'||
    capture.date!==day||capture.serverSigned!==true||
    capture.researchOnly!==true||capture.privateOwnerOnly!==true||
    capture.jraScheduleVerified!==false||
    capture.officialResultsVerified!==false||
    capture.calibrationReady!==false||capture.bettingReady!==false||
    capture.actualPurchase!==false||!Number.isInteger(capture.receiptCount)||
    capture.receiptCount<0||capture.receiptCount>36||
    !Array.isArray(capture.receipts)||
    capture.receiptCount!==capture.receipts.length||
    !Number.isInteger(capture.postOffOrMissingTimeRaces)||
    capture.postOffOrMissingTimeRaces<0)
  throw Error('85点研究の発走前証明が不正');
 const byRace=new Map(rows.filter(x=>x.ownerRunnerDetails?.fiveCore)
  .map(x=>[x.track+'|'+x.race,x.ownerRunnerDetails.fiveCore]));
 const seen=new Set();
 for(const entry of capture.receipts){
  const p=validateSavedFiveEntry(entry),id=p.track+'|'+p.race,
        source=byRace.get(id);
  if(p.date!==day||seen.has(id)||!source||
     p.raceRunnerCount!==source.runnerCount||
     p.observedRunnerCount!==source.completeObserved)
   throw Error('85点の研究対象が元の馬番と不一致');
  seen.add(id);
  const byNumber=new Map(source.horses.map(h=>[h.number,h]));
  const observed=new Set();
  for(const h of p.horses){
   const original=byNumber.get(h.number);
   if(!original||original.rawThirdPoints!==h.rawThirdPoints||
      Object.keys(h.bands).some(k=>h.bands[k]!==original.bands[k]))
    throw Error('85点の研究値が元資料と不一致');
   observed.add(h.number);
  }
  if(source.horses.some(h=>(h.rawThirdPoints!==null)!==observed.has(h.number)))
   throw Error('85点研究の未評価馬が矛盾');
 }
 return capture.receipts;
}
function saveFiveReceipts(receipts,day){
 if(!receipts.length)return '発走前に固定できる研究用85点はありません。';
 const saved=savedFiveDay(day),all=saved.all,seen=new Set(all.map(x=>{
  const p=x.snapshot;return p.date+'|'+p.track+'|'+p.race;
 }));
 let added=0,old=0;const combined=all.slice();
 for(const entry of receipts){
  const p=validateSavedFiveEntry(entry),id=p.date+'|'+p.track+'|'+p.race;
  if(seen.has(id)){old++;continue;}
  combined.push(entry);seen.add(id);added++;
 }
 if(combined.length>360||JSON.stringify(combined).length>2000000)
  throw Error('85点研究の端末保存上限');
 if(added)localStorage.setItem(FIVE_STORAGE,JSON.stringify(combined));
 return '研究85点を発走前に初回固定：新規'+added+
  'R／既存'+old+'R（上書きなし）。正式10項目・的中率未評価。';
}

function validateResearch6DraftEntry(entry){
 if(!entry||Object.keys(entry).sort().join(',')!=='signature,snapshot'||
    typeof entry.signature!=='string'||!/^[a-f0-9]{64}$/.test(entry.signature))
  throw Error('研究79点下書きの署名の形式が不正');
 const p=entry.snapshot;
 const expected=['version','date','track','race','sourceKind',
   'capturedAt','scheduledOffAt','policyVersion','researchWeight',
   'remainingUnassessedWeight','runnerCount','first','second','third',
   'tickets','points','amountYen','researchOnly','officialJraVerified',
   'predictionReady','actualPurchase'].sort().join(',');
 if(!p||Object.keys(p).sort().join(',')!==expected||
    p.version!=='owner-research6-draft-receipt-1'||
    p.sourceKind!=='prestart-unverified-research6-79-draft'||
    p.policyVersion!=='research-6'||p.researchWeight!==79||
    p.remainingUnassessedWeight!==21||p.researchOnly!==true||
    p.officialJraVerified!==false||p.predictionReady!==false||
    p.actualPurchase!==false||
    typeof p.date!=='string'||!/^20\d{6}$/.test(p.date)||
    !['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']
     .includes(p.track)||
    !Number.isInteger(p.race)||p.race<1||p.race>12||
    !Number.isInteger(p.runnerCount)||p.runnerCount<4||p.runnerCount>18||
    !Number.isInteger(p.points)||!Number.isInteger(p.amountYen)||
    !Array.isArray(p.first)||!Array.isArray(p.second)||
    !Array.isArray(p.third)||!Array.isArray(p.tickets)||
    p.first.length<2||p.first.length>3||
    p.second.length<=p.first.length||p.second.length>5||
    p.third.length<p.second.length||p.third.length>9||
    p.third.length>p.runnerCount||
    typeof p.capturedAt!=='string'||typeof p.scheduledOffAt!=='string'||
    !/(?:Z|[+-]\d\d:\d\d)$/.test(p.capturedAt)||
    !/(?:Z|[+-]\d\d:\d\d)$/.test(p.scheduledOffAt))
  throw Error('固定した79点下書きの内容が不正');
 const captured=new Date(p.capturedAt),off=new Date(p.scheduledOffAt);
 if(!Number.isFinite(captured.valueOf())||!Number.isFinite(off.valueOf())||
    captured>=off||off-captured>7*86400000||
    off.toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'})
     .replaceAll('-','')!==p.date)
  throw Error('固定した79点下書きの発走時刻が不正');
 const num=a=>Array.isArray(a)&&a.length>0&&
    a.every(n=>Number.isInteger(n)&&n>=1&&n<=18)&&
    new Set(a).size===a.length;
 if(!num(p.first)||!num(p.second)||!num(p.third)||
    p.first.join('|')!==p.second.slice(0,p.first.length).join('|')||
    p.second.join('|')!==p.third.slice(0,p.second.length).join('|'))
  throw Error('固定79点の候補馬番が不正');
 const expectedTickets=[];
 for(const a of p.first)for(const b of p.second)for(const c of p.third)
  if(a!==b&&a!==c&&b!==c)expectedTickets.push([a,b,c]);
 if(expectedTickets.length<1||expectedTickets.length>40||
    JSON.stringify(expectedTickets)!==JSON.stringify(p.tickets)||
    p.points!==expectedTickets.length||
    p.amountYen!==p.points*100)
  throw Error('固定79点の3連単票数が不正');
 return p;
}
function savedResearch6DraftDay(day){
 if(!/^20\d{6}$/.test(day))throw Error('79点下書きの開催日が不正');
 const raw=localStorage.getItem(R6_DRAFT_STORAGE);
 if(raw&&raw.length>2200000)throw Error('79点下書きが保存上限を超過');
 const all=JSON.parse(raw||'[]');
 if(!Array.isArray(all)||all.length>360)throw Error('79点下書きの保存数が不正');
 const seen=new Set(),picked=[];
 for(const item of all){
  const p=validateResearch6DraftEntry(item),
   id=p.date+'|'+p.track+'|'+p.race;
  if(seen.has(id))throw Error('固定79点下書きに馬番重複あり');
  seen.add(id);
  if(p.date===day)picked.push(item);
 }
 if(picked.length>36)throw Error('一日分の79点下書きが多すぎます');
 return {all,picked};
}
// A separate, unsigned observation that never becomes a HMAC receipt,
// a formal ranking, a wager or an item in 100-yen official settlement.
// Recompute all cutoff proof against validated 79-point research bands.
function validateSparseFiveReference(raw){
 const v=raw.sparseFiveRecentReferences;
 if(v===undefined)return null; // Legacy /history fixture.
 const refs=raw?.newWeightFiveResearch?.races,
       held=raw?.research6FiveDrafts?.races;
 if(!v||v.version!=='owner-sparse-five-79-reference-1'||
    v.policyVersion!=='research-6'||v.date!==historyDay||
    v.raceCount!==historyCoordinates.size||
    !Number.isInteger(v.reviewedPrestartMissingFactorRaces)||
    v.reviewedPrestartMissingFactorRaces<0||
    !Number.isInteger(v.safeResearchPreviewCount)||
    v.safeResearchPreviewCount<0||
    v.safeResearchPreviewCount>v.reviewedPrestartMissingFactorRaces||
    !Array.isArray(v.races)||v.races.length!==v.safeResearchPreviewCount||
    v.researchOnly!==true||v.privateOwnerOnly!==true||
    v.formalTenFactorReady!==false||v.officialJraVerified!==false||
    v.predictionReady!==false||v.bettingReady!==false||
    v.actualPurchase!==false||v.ticketsIssued!==0||
    v.changesExistingReceipts!==false||
    v.changesExistingTickets!==false||
    v.changesExistingRoi!==false||v.newProviderRequests!==0||
    !v.heldReasons||typeof v.heldReasons!=='object'||
    !Array.isArray(refs)||!Array.isArray(held)||
    refs.length!==historyCoordinates.size||
    held.length!==historyCoordinates.size)
  throw Error('未評価近走の参考資料形式が不正');
 const reasons=new Set(['too_few_runners','other_factors_missing',
                        'no_missing_recent','unstable_boundary']);
 let withheld=0;
 for(const [k,n] of Object.entries(v.heldReasons)){
  if(!reasons.has(k)||!Number.isInteger(n)||n<0)throw Error('研究保留理由が不正');
  withheld+=n;
 }
 if(withheld+v.safeResearchPreviewCount!==
    v.reviewedPrestartMissingFactorRaces)
  throw Error('研究参考件数が不一致');
 const studied=new Map(refs.map(r=>[r.track+'|'+r.race,r])),
       originals=new Map(held.map(r=>[r.track+'|'+r.race,r]));
 if(studied.size!==refs.length||originals.size!==held.length)
  throw Error('参考資料のレース重複');
 const weights={training:30,course_distance:17,pace:17,ground:12,recent:3},
       points={S:3,A:2,B:1,C:0},keys=Object.keys(weights);
 const candidates=[],used=new Set();
 for(const candidate of v.races){
  const id=candidate?.track+'|'+candidate?.race,
        source=studied.get(id),before=originals.get(id);
  if(used.has(id)||!source||!before||
     before.status!=='hold'||before.reason!=='incomplete_five_factors'||
     candidate.status!=='bounded_missing_recent_reference'||
     candidate.eachCutoffProvenForEveryRecentGrade!==true||
     candidate.receiptIssued!==false||
     candidate.predictionReady!==false||
     candidate.officialJraVerified!==false||
     candidate.bettingReady!==false||candidate.actualPurchase!==false||
     !Number.isInteger(candidate.missingRecentCount)||
     candidate.missingRecentCount<1||
     !Array.isArray(candidate.first)||!Array.isArray(candidate.second)||
     !Array.isArray(candidate.third)||!Number.isInteger(candidate.points)||
     candidate.points<12||candidate.points>40||
     !Array.isArray(source.horses)||source.horses.length<4||
     source.horses.length>18||source.runnerCount!==source.horses.length||
     before.runnerCount!==source.runnerCount)
   throw Error('近走不明の参考馬番不一致');
  used.add(id);
  let missing=0;
  const ranks=source.horses.map(h=>{
   if(!h||!Number.isInteger(h.number)||h.number<1||h.number>18||
      !h.bands||keys.some(k=>!Object.hasOwn(points,h.bands[k])&&
                             h.bands[k]!=='未評価'))
    throw Error('参考馬の観測情報が不正');
   const gaps=keys.filter(k=>h.bands[k]==='未評価');
   if(gaps.some(k=>k!=='recent'))throw Error('近走以外の欠損を軽視できません');
   missing+=gaps.length;
   const floor=keys.reduce((s,k)=>s+(h.bands[k]==='未評価'?
       0:weights[k]*points[h.bands[k]]),0);
   return {number:h.number,floor,ceiling:floor+gaps.length*9};
  });
  if(new Set(ranks.map(x=>x.number)).size!==ranks.length||
     missing!==candidate.missingRecentCount)
   throw Error('未評価近走の頭数不一致');
  ranks.sort((a,b)=>b.floor-a.floor||b.ceiling-a.ceiling||a.number-b.number);
  const arrays=[candidate.first,candidate.second,candidate.third];
  const [a,b,c]=arrays.map(x=>x.length);
  if(a<1||a>3||b<=a||b>5||c<b||c>9||c>ranks.length||
     a*(b-1)*(c-2)!==candidate.points||
     arrays.some((v,i)=>new Set(v).size!==v.length||
       v.some((n,j)=>n!==ranks[j].number))||
     [a,b,c].some(n=>n<ranks.length&&
       Math.min(...ranks.slice(0,n).map(x=>x.floor))<=
       Math.max(...ranks.slice(n).map(x=>x.ceiling))))
   throw Error('参考3連単の区切りは近走不明で変わり得る');
  candidates.push({...candidate,postTime:before.postTime});
 }
 return candidates;
}
function renderSparseFiveReference(refs,day){
 const root=$('autoFiveSparseRaces'),status=$('autoFiveSparseStatus');
 root.replaceChildren();
 if(refs===null){
  status.textContent='この履歴資料には未評価近走の参考機能がありません。追加照会はしません。';
  $('autoFiveSparsePanel').open=false;
  return;
 }
 let current=0;
 for(const r of refs){
  if(!r.postTime||draftExpiredOnDevice(day,r.postTime))continue;
  const box=dom('div',undefined,'owner-five-sparse-card');
  box.append(dom('p',r.track+' '+r.race+'R｜参考'+r.points+
    '点・近走未評価'+r.missingRecentCount+
    '頭｜署名・保存なし／正式予想ではない','muted'));
  box.append(dom('p','1着候補：'+r.first.join('・')+'番','picks'),
   dom('p','2着候補：'+r.second.join('・')+'番','picks'),
   dom('p','3着候補：'+r.third.join('・')+'番','picks'));
  root.append(box);current++;
 }
 status.textContent=current
  ?'近走不明でも境界が安定した研究参考例 '+current+
   'R（発走前のみ）。この表示は署名なし。サーバーで発走前研究記録として署名できた場合のみ初回固定。正式予想・実購入・結果集計とは別です。'
  :'参考例は0R。全頭の他4項目が不足、順位境界が変動する、または発走後の場合は表示しません。';
 $('autoFiveSparsePanel').open=current>0;
}
// Different HMAC domain from complete 79-point draft tickets. A proof
// of prestart research capture only; never a formal recommendation or ROI.
function validateSparseSavedEntry(entry){
 if(!entry||typeof entry!=='object'||Array.isArray(entry)||
    Object.keys(entry).sort().join(',')!=='signature,snapshot'||
    typeof entry.signature!=='string'||!/^[a-f0-9]{64}$/.test(entry.signature))
  throw Error('発走前研究例の署名形式不正');
 const p=entry.snapshot;
 const fields=['version','date','track','race','sourceKind','capturedAt',
   'scheduledOffAt','policyVersion','runnerCount','missingRecentCount',
   'first','second','third','tickets','points','amountYen',
   'researchOnly','scoreCalibrated','officialJraVerified',
   'predictionReady','bettingReady','actualPurchase'];
 if(!p||typeof p!=='object'||Array.isArray(p)||
    Object.keys(p).sort().join(',')!==fields.sort().join(',')||
    p.version!=='owner-sparse-five-reference-receipt-1'||
    p.sourceKind!=='prestart-sparse-recent-79-research-record'||
    p.policyVersion!=='research-6'||p.researchOnly!==true||
    p.scoreCalibrated!==false||p.officialJraVerified!==false||
    p.predictionReady!==false||p.bettingReady!==false||
    p.actualPurchase!==false||
    typeof p.date!=='string'||!/^20\d{6}$/.test(p.date)||
    !['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']
       .includes(p.track)||
    !Number.isInteger(p.race)||p.race<1||p.race>12||
    !Number.isInteger(p.runnerCount)||p.runnerCount<4||p.runnerCount>18||
    !Number.isInteger(p.missingRecentCount)||
    p.missingRecentCount<1||p.missingRecentCount>p.runnerCount||
    typeof p.capturedAt!=='string'||typeof p.scheduledOffAt!=='string'||
    !/(?:Z|[+-]\d\d:\d\d)$/.test(p.capturedAt)||
    !/(?:Z|[+-]\d\d:\d\d)$/.test(p.scheduledOffAt))
  throw Error('発走前研究例の形が不正');
 const locked=new Date(p.capturedAt),off=new Date(p.scheduledOffAt);
 if(!Number.isFinite(locked.valueOf())||!Number.isFinite(off.valueOf())||
    locked>=off||off-locked>7*86400000||
    off.toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'})
     .replaceAll('-','')!==p.date)
  throw Error('発走前の研究時刻不一致');
 const validNumbers=a=>Array.isArray(a)&&a.length>0&&
  a.every(n=>Number.isInteger(n)&&n>=1&&n<=18)&&
  new Set(a).size===a.length;
 if(!validNumbers(p.first)||!validNumbers(p.second)||
    !validNumbers(p.third)||p.first.length>3||
    p.second.length<=p.first.length||p.second.length>5||
    p.third.length<p.second.length||p.third.length>9||
    p.third.length>p.runnerCount||
    p.first.join('|')!==p.second.slice(0,p.first.length).join('|')||
    p.second.join('|')!==p.third.slice(0,p.second.length).join('|'))
  throw Error('参考候補の区切りが不正');
 const tickets=[];
 for(const a of p.first)for(const b of p.second)for(const c of p.third)
  if(a!==b&&b!==c&&a!==c)tickets.push([a,b,c]);
 if(!Array.isArray(p.tickets)||tickets.length<12||tickets.length>40||
    JSON.stringify(tickets)!==JSON.stringify(p.tickets)||
    p.points!==tickets.length||p.amountYen!==p.points*100)
  throw Error('参考3連単の全組合せが不正');
 return p;
}
function savedSparseDay(day){
 if(!/^20\d{6}$/.test(day))throw Error('研究履歴の日付不正');
 const raw=localStorage.getItem(SPARSE_RESEARCH_STORAGE);
 if(raw&&raw.length>600000)throw Error('研究履歴が保存上限');
 const rows=JSON.parse(raw||'[]');
 if(!Array.isArray(rows)||rows.length>360)throw Error('研究履歴の配列不正');
 const seen=new Set(),chosen=[];
 for(const entry of rows){
  const snap=validateSparseSavedEntry(entry),id=snap.date+'|'+snap.track+'|'+snap.race;
  if(seen.has(id))throw Error('研究履歴の同日同R重複');
  seen.add(id);
  if(snap.date===day)chosen.push(entry);
 }
 if(chosen.length>36)throw Error('研究履歴の同日件数不正');
 return {all:rows,chosen};
}
function renderSavedSparse(day){
 const container=$('autoFiveSparseSaved'),status=$('autoFiveSparseSavedStatus');
 container.replaceChildren();
 try{
  const {chosen}=savedSparseDay(day);
  status.textContent=chosen.length
   ?'この端末に発走前固定した近走未評価の研究例 '+chosen.length+
     'R。サーバー署名は今は未再検証。正式予想・購入・回収率への反映はなし。'
   :'選択日の発走前固定済み参考研究例は0R。';
  for(const entry of chosen){
   const p=entry.snapshot,box=dom('div',undefined,'owner-five-sparse-card');
   box.append(dom('p',p.track+' '+p.race+'R｜発走前に固定した研究例 '+
    p.points+'組｜近走未評価'+p.missingRecentCount+
    '頭（参考100円換算'+p.amountYen.toLocaleString('ja-JP')+
    '円・未購入）','muted'));
   box.append(dom('p','1着 '+p.first.join('・')+'番','picks'),
    dom('p','2着 '+p.second.join('・')+'番','picks'),
    dom('p','3着 '+p.third.join('・')+'番','picks'));
   const detail=dom('details');
   detail.append(dom('summary','保存された参考組合せ '+p.points+'組'));
   detail.append(dom('p',p.tickets.map(x=>x.join('→')).join(' / '),'ticket-list'));
   box.append(detail);container.append(box);
  }
  if(chosen.length)$('autoFiveSparsePanel').open=true;
  return chosen.length;
 }catch(_){
  container.replaceChildren();
  status.textContent='保存済み近走未評価研究例の形式に不整合。表示せず、既存データを変更しません。';
  return 0;
 }
}
function validateSparseResearchCapture(capture,refs,day){
 if(!capture||capture.version!=='owner-sparse-five-reference-receipt-1'||
    capture.date!==day||capture.serverSigned!==true||
    capture.researchOnly!==true||capture.privateOwnerOnly!==true||
    capture.officialJraVerified!==false||
    capture.predictionReady!==false||capture.bettingReady!==false||
    capture.actualPurchase!==false||
    capture.changesExistingReceipts!==false||
    capture.changesExistingRoi!==false||
    !Number.isInteger(capture.receiptCount)||capture.receiptCount<0||
    capture.receiptCount>36||!Array.isArray(capture.receipts)||
    capture.receipts.length!==capture.receiptCount||
    !Number.isInteger(capture.expiredBeforeSigning)||
    capture.expiredBeforeSigning<0||
    capture.expiredBeforeSigning+capture.receiptCount>refs.length)
  throw Error('未評価近走の研究署名件数が不正');
 const byRace=new Map(refs.map(r=>[r.track+'|'+r.race,r])),seen=new Set();
 for(const entry of capture.receipts){
  const p=validateSparseSavedEntry(entry),id=p.track+'|'+p.race,r=byRace.get(id);
  if(p.date!==day||seen.has(id)||!r||
     r.status!=='bounded_missing_recent_reference'||
     r.points!==p.points||r.missingRecentCount!==p.missingRecentCount||
     p.runnerCount<Math.max(...r.third)||p.points!==p.amountYen/100||
     r.postTime!==p.scheduledOffAt.substring(11,16)||
     JSON.stringify(r.first)!==JSON.stringify(p.first)||
     JSON.stringify(r.second)!==JSON.stringify(p.second)||
     JSON.stringify(r.third)!==JSON.stringify(p.third))
    throw Error('保存予定の参考例と元資料が一致しない');
  seen.add(id);
 }
 return capture.receipts;
}
function saveSparseResearchOnce(receipts,day){
 if(!receipts.length)return '発走前の近走未評価研究例は0R。';
 const {all}=savedSparseDay(day),seen=new Set(all.map(x=>{
  const p=x.snapshot;return p.date+'|'+p.track+'|'+p.race;
 }));
 const next=all.slice();let added=0,old=0,late=0;
 for(const entry of receipts){
  const p=validateSparseSavedEntry(entry),id=p.date+'|'+p.track+'|'+p.race;
  if(seen.has(id)){old++;continue;}
  if(draftExpiredOnDevice(day,p.scheduledOffAt.substring(11,16))){late++;continue;}
  next.push(entry);seen.add(id);added++;
 }
 const payload=JSON.stringify(next);
 if(next.length>360||payload.length>600000)throw Error('近走未評価の履歴保存上限');
 if(added){
  localStorage.setItem(SPARSE_RESEARCH_STORAGE,payload);
  if(localStorage.getItem(SPARSE_RESEARCH_STORAGE)!==payload)
   throw Error('固定記録を読み返せません');
 }
 return '近走未評価研究例の初回固定：新規'+added+
  'R／既存'+old+'R／発走後の保存を中止'+late+
  'R。以前の研究例は上書きしません。';
}
function renderFiveQuickSaved(day,expanded=false){
 // Only already signed AND locally first-locked 79-point research tickets
 // are displayed here. Never turn an unverified score/unsaved suggestion
 // into a primary forecast; no provider access, no storage writes.
 const root=$('autoFiveQuickSaved'),label=$('autoFiveQuickStatus');
 root.replaceChildren();
 try{
  const records=savedResearch6DraftDay(day).picked;
  for(const entry of records){
   const p=entry.snapshot,card=dom('div',undefined,'owner-five-quick-card');
   card.append(dom('p',p.track+' '+p.race+'R｜保存済み研究用3連単 '+
    p.points+'点（100円換算 '+p.amountYen.toLocaleString('ja-JP')+
    '円）','muted'));
   card.append(dom('p','1着 '+p.first.join('・')+'番','picks'),
    dom('p','2着 '+p.second.join('・')+'番','picks'),
    dom('p','3着 '+p.third.join('・')+'番','picks'));
   const detail=dom('details');
   detail.append(dom('summary','発走前に固定した全'+p.points+'点を確認'));
   detail.append(dom('p',p.tickets.map(t=>t.join('→')).join(' / '),'ticket-list'));
   card.append(detail);root.append(card);
  }
  label.textContent=records.length
   ?'この端末に発走前固定済み '+records.length+
    'R。署名の真正性はこの表示では未検証／JRA公式未照合。以前の買い目を変更していません。'
   :'この日の79点3連単の固定記録は0Rです。資料不足・発走後・同点保留の可能性があります。';
  return records.length;
 }catch(_){
  root.replaceChildren();
  label.textContent='79点の端末内研究記録に不整合があります。買い目は非表示、元データは変更していません。';
  return 0;
 }
}
function showSavedResearch6Drafts(day){
 $('autoResearch6DraftSaved').replaceChildren();
 try{
  const {picked}=savedResearch6DraftDay(day);
  $('autoResearch6DraftVerify').disabled=!picked.length;
  $('autoResearch6DraftSaveStatus').textContent=picked.length?
   'このiPhoneに初回固定した新79点3連単下書き '+picked.length+
   'R（署名未検証）。公式結果・実購入・回収率とは別です。':
   '選択日の新79点3連単下書きは未固定。発走後には追加しません。';
  for(const entry of picked){
   const p=entry.snapshot,card=dom('details');
   card.append(dom('summary',p.track+p.race+'R｜新79点の初回固定'+p.points+'点'));
   card.append(dom('p','1着 '+p.first.join('・')+'／2着 '+p.second.join('・')+
    '／3着 '+p.third.join('・')+'／100円換算 '+p.amountYen.toLocaleString()+
    '円（未購入・正式予想ではない）','muted'));
   $('autoResearch6DraftSaved').append(card);
  }
 }catch(_){
  $('autoResearch6DraftVerify').disabled=true;
  $('autoResearch6DraftSaveStatus').textContent=
   '保存済み79点下書きを確認できません。元データを消さずバックアップしてください。';
 }
}
function validateResearch6DraftCapture(capture,rows,day){
 if(!capture||capture.version!=='owner-research6-draft-receipt-1'||
    capture.date!==day||capture.serverSigned!==true||
    capture.researchOnly!==true||capture.privateOwnerOnly!==true||
    capture.jraScheduleVerified!==false||
    capture.officialJraVerified!==false||
    capture.predictionReady!==false||capture.bettingReady!==false||
    capture.actualPurchase!==false||
    capture.changesExistingReceipts!==false||
    capture.changesExistingRoi!==false||
    !Number.isInteger(capture.receiptCount)||capture.receiptCount<0||
    capture.receiptCount>36||!Array.isArray(capture.receipts)||
    capture.receipts.length!==capture.receiptCount||
    !Number.isInteger(capture.expiredBeforeSigning)||
    capture.expiredBeforeSigning<0)
  throw Error('研究79点下書きの初回署名が不正');
 const byRace=new Map(rows.filter(x=>x.ownerRunnerDetails?.research6FiveDraft)
  .map(x=>[x.track+'|'+x.race,x.ownerRunnerDetails.research6FiveDraft]));
 const used=new Set();
 for(const entry of capture.receipts){
  const p=validateResearch6DraftEntry(entry),id=p.track+'|'+p.race,
   draft=byRace.get(id);
  if(p.date!==day||used.has(id)||!draft||
     draft.status!=='five_factor_research_draft'||
     draft.runnerCount!==p.runnerCount||
     draft.points!==p.points||draft.amountYen!==p.amountYen||
     draft.postTime!==p.scheduledOffAt.substring(11,16)||
     JSON.stringify(draft.first)!==JSON.stringify(p.first)||
     JSON.stringify(draft.second)!==JSON.stringify(p.second)||
     JSON.stringify(draft.third)!==JSON.stringify(p.third)||
     JSON.stringify(draft.tickets)!==JSON.stringify(p.tickets))
   throw Error('研究79点下書きの元資料との一致を確認できません');
  used.add(id);
 }
 return capture.receipts;
}
function saveResearch6DraftReceipts(receipts,day){
 if(!receipts.length)return '79点研究用の固定可能な3連単下書きはありません。';
 const {all}=savedResearch6DraftDay(day),seen=new Set(all.map(x=>{
  const p=x.snapshot;return p.date+'|'+p.track+'|'+p.race;
 }));
 let added=0,retained=0;
 const combined=all.slice();
 for(const entry of receipts){
  const p=validateResearch6DraftEntry(entry),id=p.date+'|'+p.track+'|'+p.race;
  if(seen.has(id)){retained++;continue;}
  seen.add(id);combined.push(entry);added++;
 }
 if(combined.length>360||JSON.stringify(combined).length>2200000)
  throw Error('研究79点下書きの端末保存上限');
 if(added)localStorage.setItem(R6_DRAFT_STORAGE,JSON.stringify(combined));
 return '新79点3連単の署名付き初回固定：新規 '+added+
   'R／既存 '+retained+'R（絶対に上書きしません）。';
}

function validateStaffStudyEntry(entry){
 if(!entry||typeof entry!=='object'||Array.isArray(entry)||
    Object.keys(entry).sort().join(',')!=='signature,snapshot'||
    typeof entry.signature!=='string'||!/^[a-f0-9]{64}$/.test(entry.signature))
  throw Error('騎手厩舎研究記録の署名形式が不正');
 const p=entry.snapshot;
 if(!p||typeof p!=='object'||Array.isArray(p)||
    Object.keys(p).sort().join(',')!==
     'actualPurchase,capturedAt,date,formalTenPointReady,independentHistoricRaceDedupVerified,officialJraVerified,researchOnly,sourceKind,summary,version'||
    p.version!=='owner-staff-study-receipt-1'||
    p.sourceKind!=='private-server-three-race-aggregate-unverified'||
    p.researchOnly!==true||p.officialJraVerified!==false||
    p.actualPurchase!==false||p.formalTenPointReady!==false||
    p.independentHistoricRaceDedupVerified!==false||
    typeof p.date!=='string'||!/^20\d{6}$/.test(p.date)||
    typeof p.capturedAt!=='string'||!/(?:Z|[+-]\d\d:\d\d)$/.test(p.capturedAt)||
    !Number.isFinite(new Date(p.capturedAt).valueOf()))
  throw Error('開催日別の騎手厩舎研究記録が不正');
 const x=p.summary,counts=['requestedRaceLimit','selectedPastRaceCount',
  'providerReadCount','providerReadBudget','completedJoinRaceCount',
  'heldOrIncompleteRaceCount','totalJoinedRunnerObservations',
  'distinctJockeyCount','distinctTrainerCount','distinctPairCount',
  'pairsSeenInTwoOrMoreRaces','pairRunnerObservations',
  'observedFirstPlaceCount','observedTopThreeCount'];
 const falseKeys=['pastResultPublicationVerified','independentJraVerified',
  'fullTenFactorReady','jockeyTrainerPerformanceAssessed','holdoutValidated',
  'predictionReady','bettingReady','autoPurchase','actualPurchase',
  'changesExistingReceipts','changesExistingTickets','changesExistingRoi'];
 if(!x||typeof x!=='object'||Array.isArray(x)||
    Object.keys(x).length!==counts.length+falseKeys.length+8||
    counts.some(k=>!Number.isInteger(x[k])||x[k]<0)||
    falseKeys.some(k=>x[k]!==false)||
    x.researchOnly!==true||x.privateOwnerOnly!==true||
    x.additionalPaidReadsOnlyOnExplicitOptIn!==true||
    typeof x.providerUnavailable!=='boolean'||
    x.version!=='owner-past-staff-batch-1'||
    x.sourceFamily!=='private_dky_dse_bounded_races'||
    x.formalTenPointGrade!=='未評価'||x.formalTenPointScore!==null||
    x.requestedRaceLimit!==3||x.providerReadBudget!==6||
    x.selectedPastRaceCount<1||x.selectedPastRaceCount>3||
    x.providerReadCount<1||
    x.providerReadCount>2*x.selectedPastRaceCount||
    x.completedJoinRaceCount+x.heldOrIncompleteRaceCount!==
      x.selectedPastRaceCount||
    x.totalJoinedRunnerObservations<x.completedJoinRaceCount*3||
    x.totalJoinedRunnerObservations>x.completedJoinRaceCount*18||
    x.pairRunnerObservations!==x.totalJoinedRunnerObservations||
    x.observedFirstPlaceCount!==x.completedJoinRaceCount||
    x.observedTopThreeCount!==3*x.completedJoinRaceCount||
    x.distinctPairCount>x.totalJoinedRunnerObservations||
    x.pairsSeenInTwoOrMoreRaces>x.distinctPairCount||
    (!x.providerUnavailable&&x.providerReadCount!==2*x.selectedPastRaceCount))
  throw Error('騎手厩舎研究記録の件数・未評価状態が不正');
 return p;
}
function savedStaffStudySessions(){
 const raw=localStorage.getItem(STAFF_STUDY_STORAGE);
 if(raw&&raw.length>150000)throw Error('騎手厩舎研究記録の保存上限');
 const saved=JSON.parse(raw||'[]');
 if(!Array.isArray(saved)||saved.length>120)
  throw Error('騎手厩舎研究記録の保存件数が不正');
 const dates=new Set();
 for(const row of saved){
  const p=validateStaffStudyEntry(row);
  if(dates.has(p.date))throw Error('開催日別の研究記録が重複');
  dates.add(p.date);
 }
 return saved;
}
function showSavedStaffStudySessions(){
 $('autoHistoryStaffArchiveList').replaceChildren();
 try{
  const saved=savedStaffStudySessions();
  $('autoHistoryStaffArchiveVerify').disabled=!saved.length;
  $('autoHistoryStaffArchiveStatus').textContent=saved.length?
   '開催日別に初回固定した3R研究 '+saved.length+
   '日分。別の日に同じ過去Rを参照する可能性があり、独立母数・騎手能力として合算しません。':
   '過去3R研究の初回固定はまだありません（iPhone端末内保存）。';
  for(const row of saved.slice().sort((a,b)=>b.snapshot.date.localeCompare(a.snapshot.date))){
   const p=row.snapshot,x=p.summary,card=dom('details');
   card.append(dom('summary',p.date.slice(0,4)+'/'+p.date.slice(4,6)+'/'+
    p.date.slice(6)+'｜照合'+x.completedJoinRaceCount+
    'R・保留'+x.heldOrIncompleteRaceCount+'R'));
   card.append(dom('p','追加API照会'+x.providerReadCount+
    '回／出走観測'+x.totalJoinedRunnerObservations+
    '件／同一ペア'+x.distinctPairCount+
    '組｜形式未検証のまま能力に加点しません。','muted'));
   $('autoHistoryStaffArchiveList').append(card);
  }
 }catch(_){
  $('autoHistoryStaffArchiveVerify').disabled=true;
  $('autoHistoryStaffArchiveStatus').textContent=
   '保存済みの騎手厩舎研究記録が不正。元の内容を変更せずバックアップを確認してください。';
 }
}
function firstWriteStaffStudyEntry(entry){
 const snap=validateStaffStudyEntry(entry),all=savedStaffStudySessions();
 if(all.some(row=>row.snapshot.date===snap.date))
  return '開催日'+snap.date+'の初回研究記録を保持。再照合による上書きはしません。';
 const combined=[...all,entry];
 if(combined.length>120||JSON.stringify(combined).length>150000)
  throw Error('開催日別の騎手厩舎研究保存上限');
 localStorage.setItem(STAFF_STUDY_STORAGE,JSON.stringify(combined));
 return '騎手厩舎3R研究の初回記録を'+snap.date+'で固定（端末内、署名付き）。';
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
 // Parent names are not a bloodline performance assessment.
 if(h.pedigreeEvidencePreflight!==undefined){
  const p=h.pedigreeEvidencePreflight;
  if(!p||p.version!=='owner-pedigree-evidence-preflight-1'||
     p.policyVersion!=='research-5'||p.factor!=='pedigree'||
     p.weight!==8||p.raceCount!==historyCoordinates.size||
     p.pedigreeGradesVerified!==0||
     p.independentCohortAvailable!==false||
     p.temporalValidationComplete!==false||
     p.researchOnly!==true||p.privateOwnerOnly!==true||
     p.officialJraVerified!==false||p.overallPredictionReady!==false||
     p.bettingReady!==false||p.autoPurchase!==false||
     p.changesExistingTickets!==false||p.changesExistingReceipts!==false||
     !Array.isArray(p.races)||p.races.length!==historyCoordinates.size)
   throw Error('血統8点の準備資料の形式不正');
  const seen=new Set();
  for(const race of p.races){
   const id=race?.track+'|'+race?.race,detail=perRace.get(id);
   if(seen.has(id)||!detail?.tenInventory||
      race.runnerCount!==detail.runnerCount||
      !Number.isInteger(race.parentageCompleteCount)||
      race.parentageCompleteCount!==detail.tenInventory.remainingFieldCoverage.pedigree||
      race.independentCohortValidatedCount!==0||
      race.verifiedPedigreeGrades!==0||race.pedigreeScoreReady!==false||
      !Array.isArray(race.horses)||race.horses.length!==race.runnerCount)
    throw Error('血統8点の頭数・資料が不一致');
   seen.add(id);
   const source=new Map(detail.tenInventory.runners.map(x=>[x.number,x]));
   const numbers=new Set();
   for(const horse of race.horses){
    const n=horse?.number,base=source.get(n);
    if(!Number.isInteger(n)||n<1||n>18||numbers.has(n)||
       !base||!horse.parentageSourceState||
       horse.parentageSourceState!==base.sourceStates.pedigree||
       horse.parentageComplete!==(horse.parentageSourceState==='complete_fields_observed')||
       horse.independentCohortValidated!==false||
       horse.conditionMatched!==false||
       horse.outOfTimeCalibrated!==false||
       horse.grade!=='未評価'||horse.score8!==null||
       horse.bettingReady!==false||!Array.isArray(horse.missingEvidence))
     throw Error('血統8点の個別証拠が不一致');
    const expected=(horse.parentageComplete?[]:['parentage_fields_incomplete']).concat([
     'independent_condition_matched_cohort_unavailable',
     'temporal_holdout_not_validated'
    ]);
    if(horse.missingEvidence.join(',')!==expected.join(','))
     throw Error('血統8点の不足資料が不一致');
    numbers.add(n);
   }
   if(numbers.size!==race.runnerCount)
    throw Error('血統8点の馬番不足');
   detail.pedigreePreflight=race;
  }
  if(seen.size!==historyCoordinates.size)
   throw Error('血統8点のレース不足');
 }
 // The three supporting inputs have six weight points, but only field
 // presence is available. Do not let a forged grade enter a visible ticket.
 if(h.supportSixPreflight!==undefined){
  const p=h.supportSixPreflight,weights={draw_weight:3,jockey_stable:2,rotation:1};
  if(!p||p.version!=='owner-support-six-preflight-1'||
     p.policyVersion!=='research-5'||p.weightTotal!==6||
     !p.factors||Object.keys(p.factors).length!==3||
     Object.keys(weights).some(k=>p.factors[k]!==weights[k])||
     p.raceCount!==historyCoordinates.size||p.verifiedFactorCount!==0||
     p.conditionMatchedEffectValidated!==false||
     p.temporalValidationComplete!==false||
     p.researchOnly!==true||p.privateOwnerOnly!==true||
     p.officialJraVerified!==false||p.overallPredictionReady!==false||
     p.bettingReady!==false||p.autoPurchase!==false||
     p.changesExistingTickets!==false||p.changesExistingReceipts!==false||
     !Array.isArray(p.races)||p.races.length!==historyCoordinates.size)
   throw Error('残り6点の準備資料の形式不正');
  const seen=new Set(),keys=Object.keys(weights),
        codes={
         draw_weight:['draw_or_carried_weight_missing',
          'field_and_weight_effects_unvalidated','temporal_holdout_not_validated'],
         jockey_stable:['jockey_or_trainer_missing',
          'comparable_personnel_performance_unvalidated','temporal_holdout_not_validated'],
         rotation:['last_run_interval_missing',
          'condition_matched_rotation_effect_unvalidated','temporal_holdout_not_validated']
        };
  for(const race of p.races){
   const id=race?.track+'|'+race?.race,details=perRace.get(id);
   if(seen.has(id)||!details?.tenInventory||
      race.runnerCount!==details.runnerCount||
      race.verifiedFactorCount!==0||race.scoreReady!==false||
      !race.fieldCompleteCounts||Object.keys(race.fieldCompleteCounts).length!==3||
      !Number.isInteger(race.allThreeFieldCompleteCount)||
      !Array.isArray(race.horses)||race.horses.length!==race.runnerCount)
    throw Error('残り6点の頭数不一致');
   seen.add(id);
   const source=new Map(details.tenInventory.runners.map(x=>[x.number,x]));
   const counts=Object.fromEntries(keys.map(k=>[k,0]));
   const numbers=new Set();let all=0;
   for(const horse of race.horses){
    const n=horse?.number,from=source.get(n);
    if(!Number.isInteger(n)||n<1||n>18||numbers.has(n)||
       !from||!horse.sourceStates||!horse.fieldPresent||
       !horse.missingEvidence||!horse.grades||!horse.scores||
       Object.keys(horse.sourceStates).length!==3||
       Object.keys(horse.fieldPresent).length!==3||
       Object.keys(horse.missingEvidence).length!==3||
       Object.keys(horse.grades).length!==3||
       Object.keys(horse.scores).length!==3||
       horse.conditionalEffectVerified!==false||
       horse.outOfTimeValidated!==false||horse.bettingReady!==false)
     throw Error('残り6点の馬番・評価不一致');
    numbers.add(n);
    let presenceWeight=0,complete=0;
    for(const k of keys){
     const expected=k==='rotation'?
      from.sourceStates[k]!=='unknown':
      from.sourceStates[k]==='complete_fields_observed';
     if(horse.sourceStates[k]!==from.sourceStates[k]||
        horse.fieldPresent[k]!==expected||
        horse.grades[k]!=='未評価'||horse.scores[k]!==null||
        !Array.isArray(horse.missingEvidence[k])||
        horse.missingEvidence[k].join(',')!==
        (expected?codes[k].slice(1):codes[k]).join(','))
      throw Error('残り6点の資料と根拠の不一致');
     counts[k]+=Number(expected);
     complete+=Number(expected);
     if(expected)presenceWeight+=weights[k];
    }
    if(horse.fieldPresenceWeight!==presenceWeight)
     throw Error('残り6点の資料カバー配点に不正');
    if(complete===3)all++;
   }
   if(numbers.size!==race.runnerCount||
      all!==race.allThreeFieldCompleteCount||
      keys.some(k=>race.fieldCompleteCounts[k]!==counts[k]||
       counts[k]!==details.tenInventory.remainingFieldCoverage[k]))
    throw Error('残り6点の資料件数が不一致');
   details.supportSixPreflight=race;
  }
  if(seen.size!==historyCoordinates.size)
   throw Error('残り6点のレース不足');
 }
 // This is an optional *uncalibrated* 70-weight research comparison
 // from the same fully checked historical response; not a formal score.
 if(h.threeCoreResearch!==undefined){
  const core=h.threeCoreResearch,w={training:30,course_distance:20,pace:20};
  if(!core||core.version!=='owner-three-core-research-1'||
     core.policyVersion!=='research-5'||core.raceCount!==historyCoordinates.size||
     core.researchOnly!==true||core.privateOwnerOnly!==true||
     core.coreWeightTotal!==70||!core.coreFactorWeights||
     Object.keys(core.coreFactorWeights).length!==3||
     Object.keys(w).some(k=>core.coreFactorWeights[k]!==w[k])||
     core.factorGradesVerified!==0||core.overallPredictionReady!==false||
     core.formalScoreReady!==false||core.officialJraVerified!==false||
     core.bettingReady!==false||core.autoPurchase!==false||
     core.changesExistingTickets!==false||
     core.historicalBandsNotCalibrated!==true||
     !Array.isArray(core.races)||core.races.length!==historyCoordinates.size)
    throw Error('重点3項目の研究資料が不正');
  const seenCoreRaces=new Set(),allowed=new Set(['S','A','B','C','未評価']),
        points={S:3,A:2,B:1,C:0};
  for(const race of core.races){
   const id=race?.track+'|'+race?.race,details=perRace.get(id);
   if(seenCoreRaces.has(id)||!details?.fiveFactor||!details?.tenInventory||
      race.runnerCount!==details.runnerCount||
      race.formalGradeReady!==false||race.trifectaReady!==false||
      race.researchOnly!==true||!Array.isArray(race.horses)||
      race.horses.length!==race.runnerCount||
      !race.missingByFactor||Object.keys(race.missingByFactor).length!==3||
      !Number.isInteger(race.completeCoreObserved)||
      race.completeCoreObserved<0||race.completeCoreObserved>race.runnerCount)
    throw Error('重点3項目の馬番が不一致');
   seenCoreRaces.add(id);
   const five=new Map(details.fiveFactor.runners.map(x=>[x.number,x])),
         inv=new Map(details.tenInventory.runners.map(x=>[x.number,x])),
         seen=new Set(),missingCount=Object.fromEntries(
          Object.keys(w).map(k=>[k,0]));
   let complete=0;
   for(const h0 of race.horses){
    const n=h0?.number,source=five.get(n),material=inv.get(n);
    if(!Number.isInteger(n)||n<1||n>18||seen.has(n)||
       !source||!material||h0.scoreIsCalibrated!==false||
       h0.formalScore100!==null||h0.formalGrade!=='未評価'||
       h0.formalRank!==null||h0.bettingReady!==false||
       !h0.bands||Object.keys(h0.bands).length!==3||
       !Array.isArray(h0.missing)||h0.missing.length>3||
       !Number.isInteger(h0.observedCoreCount))
     throw Error('重点3項目の研究馬番が不正');
    seen.add(n);
    const missing=[];
    for(const key of Object.keys(w)){
     if(!allowed.has(h0.bands[key])||
        h0.bands[key]!==source.bands[key]||
        h0.bands[key]!==material.provisionalBands[key])
      throw Error('重点3項目の研究材料が不一致');
     if(h0.bands[key]==='未評価'){
      missing.push(key);missingCount[key]++;
     }
    }
    const expected=missing.length?null:Object.keys(w).reduce(
     (sum,key)=>sum+w[key]*points[h0.bands[key]],0);
    if(h0.missing.join(',')!==missing.join(',')||
       h0.observedCoreCount!==3-missing.length||
       h0.rawThirdPoints!==expected||
       h0.evidenceScore70!==(expected===null?null:
        Math.round(expected*100/3)/100))
     throw Error('重点3項目の計算が不一致');
    if(expected!==null)complete++;
   }
   if(seen.size!==race.runnerCount||complete!==race.completeCoreObserved||
      Object.keys(w).some(k=>missingCount[k]!==race.missingByFactor[k]))
    throw Error('重点3項目の集計が不一致');
   details.threeCore=race;
  }
  if(seenCoreRaces.size!==historyCoordinates.size)
   throw Error('重点3項目の照合レース不足');
 }
 // Four-factor 82-weight extension is purely observational. Validate
 // against same-run matched 70-point research, current going and roster;
 // missing going NEVER contributes C/zero or a partial normalized score.
 if(h.fourCoreResearch!==undefined){
  const ext=h.fourCoreResearch,
        w={training:30,course_distance:20,pace:20,ground:12};
  if(!ext||ext.version!=='owner-four-core-research-1'||
     ext.policyVersion!=='research-5'||
     ext.raceCount!==historyCoordinates.size||
     ext.researchOnly!==true||ext.privateOwnerOnly!==true||
     ext.observedWeightTotal!==82||!ext.factorWeights||
     Object.keys(ext.factorWeights).length!==4||
     Object.keys(w).some(k=>ext.factorWeights[k]!==w[k])||
     ext.factorGradesVerified!==0||ext.overallPredictionReady!==false||
     ext.formalScoreReady!==false||ext.officialJraVerified!==false||
     ext.bettingReady!==false||ext.autoPurchase!==false||
     ext.changesExistingTickets!==false||
     ext.changesExistingCoreReceipts!==false||
     ext.historicalBandsNotCalibrated!==true||
     ext.goingSuitabilityVerified!==false||
     !Array.isArray(ext.races)||ext.races.length!==historyCoordinates.size)
   throw Error('重点4項目の研究資料が不正');
  const seenCoreRaces=new Set(),allowed=new Set(['S','A','B','C','未評価']),
        points={S:3,A:2,B:1,C:0};
  for(const race of ext.races){
   const id=race?.track+'|'+race?.race,details=perRace.get(id);
   if(seenCoreRaces.has(id)||!details?.threeCore||!details?.fiveFactor||
      !details?.tenInventory||race.runnerCount!==details.runnerCount||
      race.formalGradeReady!==false||race.trifectaReady!==false||
      race.researchOnly!==true||!Array.isArray(race.horses)||
      race.horses.length!==race.runnerCount||
      !race.missingByFactor||Object.keys(race.missingByFactor).length!==4||
      !Number.isInteger(race.completeObserved)||
      race.completeObserved<0||race.completeObserved>race.runnerCount)
    throw Error('重点4項目の馬番が不一致');
   seenCoreRaces.add(id);
   const prior=new Map(details.threeCore.horses.map(x=>[x.number,x])),
         five=new Map(details.fiveFactor.runners.map(x=>[x.number,x])),
         inv=new Map(details.tenInventory.runners.map(x=>[x.number,x])),
         seen=new Set(),missingCount=Object.fromEntries(
          Object.keys(w).map(k=>[k,0]));
   let complete=0;
   for(const horse of race.horses){
    const n=horse?.number,fromThree=prior.get(n),
          fromFive=five.get(n),fromTen=inv.get(n);
    if(!Number.isInteger(n)||n<1||n>18||seen.has(n)||
       !fromThree||!fromFive||!fromTen||
       horse.scoreIsCalibrated!==false||
       horse.formalScore100!==null||horse.formalGrade!=='未評価'||
       horse.formalRank!==null||horse.bettingReady!==false||
       !horse.bands||Object.keys(horse.bands).length!==4||
       !Array.isArray(horse.missing)||horse.missing.length>4||
       !Number.isInteger(horse.observedFactorCount))
     throw Error('重点4項目の研究馬番が不正');
    seen.add(n);
    const missing=[];
    for(const key of Object.keys(w)){
     if(!allowed.has(horse.bands[key])||
        horse.bands[key]!==fromFive.bands[key]||
        horse.bands[key]!==fromTen.provisionalBands[key]||
        (key!=='ground'&&horse.bands[key]!==fromThree.bands[key]))
      throw Error('重点4項目の資料が不一致');
     if(horse.bands[key]==='未評価'){
      missing.push(key);missingCount[key]++;
     }
    }
    const expected=missing.length?null:Object.keys(w).reduce(
      (sum,key)=>sum+w[key]*points[horse.bands[key]],0);
    if(horse.missing.join(',')!==missing.join(',')||
       horse.observedFactorCount!==4-missing.length||
       horse.rawThirdPoints!==expected||
       horse.evidenceScore82!==(expected===null?null:
          Math.round(expected*100/3)/100)||
       (expected!==null&&
        expected!==fromThree.rawThirdPoints+
        w.ground*points[horse.bands.ground]))
     throw Error('重点4項目の計算が不一致');
    if(expected!==null)complete++;
   }
   if(seen.size!==race.runnerCount||complete!==race.completeObserved||
      Object.keys(w).some(k=>missingCount[k]!==race.missingByFactor[k]))
    throw Error('重点4項目の集計が不一致');
   details.fourCore=race;
  }
  if(seenCoreRaces.size!==historyCoordinates.size)
   throw Error('重点4項目の照合レース不足');
 }
 // An 85-weight research comparison adds only 3 points of recent
 // observations. Never infer a formal S/A/B/C or overwrite 70-point locks.
 if(h.fiveCoreResearch!==undefined){
  const ext=h.fiveCoreResearch,
        w={training:30,course_distance:20,pace:20,ground:12,recent:3};
  if(!ext||ext.version!=='owner-five-core-research-1'||
     ext.policyVersion!=='research-5'||
     ext.raceCount!==historyCoordinates.size||
     ext.researchOnly!==true||ext.privateOwnerOnly!==true||
     ext.observedWeightTotal!==85||!ext.factorWeights||
     Object.keys(ext.factorWeights).length!==5||
     Object.keys(w).some(k=>ext.factorWeights[k]!==w[k])||
     ext.factorGradesVerified!==0||ext.overallPredictionReady!==false||
     ext.formalScoreReady!==false||ext.officialJraVerified!==false||
     ext.bettingReady!==false||ext.autoPurchase!==false||
     ext.changesExistingTickets!==false||
     ext.changesExistingCoreReceipts!==false||
     ext.historicalBandsNotCalibrated!==true||
     ext.recentResultRankNotPrediction!==true||
     !Array.isArray(ext.races)||ext.races.length!==historyCoordinates.size)
   throw Error('重点5項目の研究資料が不正');
  const seenRaces=new Set(),grades=new Set(['S','A','B','C','未評価']),
        pts={S:3,A:2,B:1,C:0};
  for(const race of ext.races){
   const id=race?.track+'|'+race?.race,details=perRace.get(id);
   if(seenRaces.has(id)||!details?.fourCore||!details?.fiveFactor||
      !details?.tenInventory||race.runnerCount!==details.runnerCount||
      race.formalGradeReady!==false||race.trifectaReady!==false||
      race.researchOnly!==true||!Array.isArray(race.horses)||
      race.horses.length!==race.runnerCount||
      race.comparisonIsFormalRank!==false||
      !Array.isArray(race.comparisonGroups)||
      !Array.isArray(race.unassessedNumbers)||
      !race.missingByFactor||Object.keys(race.missingByFactor).length!==5||
      !Number.isInteger(race.completeObserved)||
      race.completeObserved<0||race.completeObserved>race.runnerCount)
     throw Error('重点5項目の馬番が不一致');
   seenRaces.add(id);
   const prior=new Map(details.fourCore.horses.map(x=>[x.number,x])),
         five=new Map(details.fiveFactor.runners.map(x=>[x.number,x])),
         inv=new Map(details.tenInventory.runners.map(x=>[x.number,x])),
         seen=new Set(),missingCount=Object.fromEntries(
           Object.keys(w).map(k=>[k,0]));
   let complete=0;
   for(const horse of race.horses){
    const n=horse?.number,fromFour=prior.get(n),
          fromFive=five.get(n),fromTen=inv.get(n);
    if(!Number.isInteger(n)||n<1||n>18||seen.has(n)||
       !fromFour||!fromFive||!fromTen||
       horse.scoreIsCalibrated!==false||
       horse.formalScore100!==null||horse.formalGrade!=='未評価'||
       horse.formalRank!==null||horse.bettingReady!==false||
       !horse.bands||Object.keys(horse.bands).length!==5||
       !Array.isArray(horse.missing)||horse.missing.length>5||
       !Number.isInteger(horse.observedFactorCount))
      throw Error('重点5項目の研究馬番が不正');
    seen.add(n);
    const missing=[];
    for(const key of Object.keys(w)){
     if(!grades.has(horse.bands[key])||
        horse.bands[key]!==fromFive.bands[key]||
        horse.bands[key]!==fromTen.provisionalBands[key]||
        (key!=='recent'&&horse.bands[key]!==fromFour.bands[key]))
      throw Error('重点5項目の資料が不一致');
     if(horse.bands[key]==='未評価'){
      missing.push(key);missingCount[key]++;
     }
    }
    const expected=missing.length?null:Object.keys(w).reduce(
       (sum,k)=>sum+w[k]*pts[horse.bands[k]],0);
    if(horse.missing.join(',')!==missing.join(',')||
       horse.observedFactorCount!==5-missing.length||
       horse.rawThirdPoints!==expected||
       horse.evidenceScore85!==(expected===null?null:
         Math.round(expected*100/3)/100)||
       (expected!==null&&(fromFour.rawThirdPoints===null||
         expected!==fromFour.rawThirdPoints+
            w.recent*pts[horse.bands.recent])))
      throw Error('重点5項目の計算が不一致');
    if(expected!==null)complete++;
   }
   if(seen.size!==race.runnerCount||complete!==race.completeObserved||
      Object.keys(w).some(k=>missingCount[k]!==race.missingByFactor[k]))
    throw Error('重点5項目の集計が不一致');
   const buckets=new Map(),unassessed=[];
   for(const h of race.horses){
    if(h.rawThirdPoints===null){unassessed.push(h.number);continue;}
    if(!buckets.has(h.rawThirdPoints))buckets.set(h.rawThirdPoints,[]);
    buckets.get(h.rawThirdPoints).push(h.number);
   }
   const expectedGroups=[...buckets.keys()].sort((a,b)=>b-a).map(raw=>({
    rawThirdPoints:raw,numbers:buckets.get(raw).sort((a,b)=>a-b)
   }));
   if(JSON.stringify(race.comparisonGroups)!==JSON.stringify(expectedGroups)||
      JSON.stringify(race.unassessedNumbers)!==
       JSON.stringify(unassessed.sort((a,b)=>a-b)))
    throw Error('研究用85点の比較順が元データと不一致');
   details.fiveCore=race;
  }
  if(seenRaces.size!==historyCoordinates.size)
    throw Error('重点5項目の照合レース不足');
 }
 // New policy's first five factors total 79, derived ONLY from the
 // validated legacy 85 snapshot. Never reinterpret signed 85 as new points.
 if(h.newWeightFiveResearch!==undefined){
  const fresh=h.newWeightFiveResearch,keys=[
   'training','course_distance','pace','ground','recent'],
   weights={training:30,course_distance:17,pace:17,ground:12,recent:3},
   oldWeights={training:30,course_distance:20,pace:20,ground:12,recent:3},
   pts={S:3,A:2,B:1,C:0};
  if(!fresh||fresh.version!=='owner-new-weight-five-research-1'||
     fresh.policyVersion!=='research-6'||
     fresh.sourcePolicyVersion!=='research-5'||
     fresh.raceCount!==historyCoordinates.size||
     fresh.observedWeightTotal!==79||
     !fresh.factorWeights||
     Object.keys(fresh.factorWeights).length!==5||
     keys.some(k=>fresh.factorWeights[k]!==weights[k])||
     fresh.factorGradesVerified!==0||
     fresh.overallPredictionReady!==false||
     fresh.formalScoreReady!==false||
     fresh.officialJraVerified!==false||
     fresh.bettingReady!==false||fresh.autoPurchase!==false||
     fresh.researchOnly!==true||fresh.privateOwnerOnly!==true||
     fresh.historicalBandsNotCalibrated!==true||
     fresh.coursePaceEvidenceNotFormalGrade!==true||
     fresh.coursePaceEvidenceWeight!==34||
     fresh.goingEvidenceNotFormalGrade!==true||
     fresh.goingEvidenceWeight!==12||
     fresh.resultVerified!==false||
     fresh.changesExistingTickets!==false||
     fresh.changesExistingCoreReceipts!==false||
     fresh.changesExistingFiveReceipts!==false||
     fresh.extraProviderCalls!==0||
     !Array.isArray(fresh.races)||fresh.races.length!==historyCoordinates.size)
   throw Error('新配点79点の研究契約不一致');
  const seenRaces=new Set();
  for(const race of fresh.races){
   const id=race?.track+'|'+race?.race,detail=perRace.get(id);
   if(!detail?.fiveCore||seenRaces.has(id)||
      race.runnerCount!==detail.runnerCount||
      race.researchOnly!==true||race.formalGradeReady!==false||
      race.trifectaReady!==false||
      race.comparisonIsFormalRank!==false||
      !Array.isArray(race.horses)||race.horses.length!==race.runnerCount||
      !Array.isArray(race.comparisonGroups)||
      !Array.isArray(race.unassessedNumbers)||
      !race.missingByFactor||Object.keys(race.missingByFactor).length!==5)
    throw Error('新配点79点のレース不一致');
   seenRaces.add(id);
   const old=new Map(detail.fiveCore.horses.map(x=>[x.number,x])),
    seen=new Set(),missingCounts=Object.fromEntries(keys.map(k=>[k,0])),
    bins=new Map(),unknown=[];
   for(const horse of race.horses){
    const n=horse?.number,prior=old.get(n);
    if(!prior||!Number.isInteger(n)||n<1||n>18||seen.has(n)||
       horse.scoreIsCalibrated!==false||
       horse.formalScore100!==null||horse.formalGrade!=='未評価'||
       horse.formalRank!==null||horse.bettingReady!==false||
       !horse.bands||Object.keys(horse.bands).length!==5||
       !Array.isArray(horse.missing)||
       !Number.isInteger(horse.observedFactorCount))
     throw Error('新配点79点の馬番・根拠不一致');
    seen.add(n);
    const missing=[];
    for(const k of keys){
     if(!Object.prototype.hasOwnProperty.call(pts,horse.bands[k])&&
        horse.bands[k]!=='未評価')throw Error('新配点79点の不正な帯');
     if(horse.bands[k]!==prior.bands[k])
      throw Error('旧85点の研究帯を書き換えています');
     if(horse.bands[k]==='未評価'){
      missing.push(k);missingCounts[k]++;
     }
    }
    const expected=missing.length?null:keys.reduce(
     (sum,k)=>sum+weights[k]*pts[horse.bands[k]],0);
    // Validate course + pace 34-weight diagnostic independently of
    // the other three bands. Missing evidence is NULL, never a C grade.
    const pairMissing=['course_distance','pace'].some(k=>
     horse.bands[k]==='未評価');
    const pairRaw=pairMissing?null:
     17*pts[horse.bands.course_distance]+17*pts[horse.bands.pace];
    const pairScore=pairRaw===null?null:Math.round(pairRaw*100/3)/100;
    if(horse.coursePaceEvidenceNotFormalGrade!==true||
       horse.coursePaceEvidenceRawThirdPoints!==pairRaw||
       horse.coursePaceEvidenceScore34!==pairScore)
     throw Error('コース・展開の34点研究算術不一致');
    const goingRaw=horse.bands.ground==='未評価'?null:
     12*pts[horse.bands.ground];
    const goingScore=goingRaw===null?null:Math.round(goingRaw*100/3)/100;
    if(horse.goingEvidenceNotFormalGrade!==true||
       horse.goingEvidenceRawThirdPoints!==goingRaw||
       horse.goingEvidenceScore12!==goingScore)
     throw Error('馬場12点研究の算術不一致');
    if(horse.missing.join('|')!==missing.join('|')||
       horse.observedFactorCount!==5-missing.length||
       horse.rawThirdPoints!==expected||
       horse.evidenceScore79!==(expected===null?null:
        Math.round(expected*100/3)/100))
     throw Error('新配点79点の算術不一致');
    if(expected===null)unknown.push(n);
    else{
     if(!bins.has(expected))bins.set(expected,[]);
     bins.get(expected).push(n);
    }
   }
   if(seen.size!==old.size||
      race.completeObserved!==seen.size-unknown.length||
      keys.some(k=>race.missingByFactor[k]!==missingCounts[k]))
    throw Error('新配点79点の研究頭数不一致');
   const groups=[...bins.keys()].sort((a,b)=>b-a).map(raw=>({
    rawThirdPoints:raw,numbers:bins.get(raw).sort((a,b)=>a-b)
   }));
   if(JSON.stringify(race.comparisonGroups)!==JSON.stringify(groups)||
      JSON.stringify(race.unassessedNumbers)!==
       JSON.stringify(unknown.sort((a,b)=>a-b)))
    throw Error('新配点79点の比較順不一致');
   detail.newWeightFive=race;
  }
  if(seenRaces.size!==historyCoordinates.size)
   throw Error('新配点79点のレース欠落');
 }
 // Research-6 course 17 / pace 17 / going 12: source readiness only.
 // Cross-check the summary and every runner against independently checked
 // ownerRunnerHistory and paceScenarioHypotheses before displaying.
 if(h.research6ThreeFactorSourceGaps!==undefined){
  const v=h.research6ThreeFactorSourceGaps,weights={
   course_distance:17,pace:17,ground:12},keys=Object.keys(weights),
   observedKeys=['courseComparableObserved','courseHistoryComplete',
    'currentGoingRecorded','sameGoingObserved','pacePositionObserved',
    'paceScenarioObserved','allThreeSourcesObserved'],
   gapKeys=['noCourseComparableRuns','courseHistoryIncomplete',
    'currentGoingUnknown','noSameGoingRuns','paceScenarioUnassessed'];
  if(!v||v.version!=='owner-research6-three-factor-source-gaps-2'||
     v.policyVersion!=='research-6'||v.weightTotal!==46||
     v.minimumComparableRuns!==3||
     !v.factorWeights||Object.keys(v.factorWeights).length!==3||
     keys.some(k=>v.factorWeights[k]!==weights[k])||
     v.extraProviderCalls!==0||v.researchOnly!==true||
     v.privateOwnerOnly!==true||v.officialJraVerified!==false||
     v.courseSuitabilityAssessed!==false||v.paceForecastReady!==false||
     v.goingSuitabilityAssessed!==false||v.formalGradesVerified!==0||
     v.independentTimeCutVerified!==false||
     v.conditionMatchedHoldoutValidated!==false||
     v.factorRubricsCalibrated!==false||
     v.historicalResultPublicationTimesVerified!==false||
     v.independentSourceFamiliesVerified!==false||
     v.overallPredictionReady!==false||v.bettingReady!==false||
     v.changesExistingTickets!==false||
     !Array.isArray(v.races)||v.raceCount!==historyCoordinates.size||
     v.races.length!==historyCoordinates.size)
   throw Error('3項目46点の資料判定形式が不正');
  const sourceRaces=new Map(h.ownerRunnerHistory.races.map(
   r=>[r.track+'|'+r.race,r]));
  const seen=new Set();
  const int=(n,max)=>Number.isInteger(n)&&n>=0&&n<=max;
  for(const race of v.races){
   const id=race?.track+'|'+race?.race,detail=perRace.get(id),
    raw=sourceRaces.get(id),pace=detail?.paceScenario;
   if(!detail||!raw||!pace||seen.has(id)||
      race.runnerCount!==detail.runnerCount||
      !Array.isArray(race.runners)||race.runners.length!==race.runnerCount||
      !race.observed||!race.gaps||!race.minimumSampleCoverage||
      Object.keys(race.minimumSampleCoverage).length!==4||
      Object.values(race.minimumSampleCoverage)
       .some(n=>!int(n,race.runnerCount))||
      Object.keys(race.observed).length!==observedKeys.length||
      Object.keys(race.gaps).length!==gapKeys.length||
      observedKeys.some(k=>!int(race.observed[k],race.runnerCount))||
      gapKeys.some(k=>!int(race.gaps[k],race.runnerCount))||
      race.allThreeAreResearchOnly!==true||
      race.formalGradesVerified!==0||race.bettingReady!==false)
    throw Error('3項目46点の対象レース・未評価状態が不一致');
   seen.add(id);
   const historical=new Map(raw.runners.map(x=>[x.number,x])),
    paceByNumber=detail.paceByNumber,sourceSeen=new Set(),
    stats=Object.fromEntries([...observedKeys,...gapKeys].map(k=>[k,0])),
    minimum={
     courseDistanceAtLeastThree:0,sameGoingAtLeastThree:0,
     paceScenarioObserved:0,allThreeMinimumStudySamples:0
    };
   if(historical.size!==race.runnerCount||
      paceByNumber.size!==race.runnerCount)
    throw Error('3項目46点の馬番集合が不一致');
   for(const runner of race.runners){
    const n=runner?.number,c0=historical.get(n),s=paceByNumber.get(n);
    if(!int(n,18)||n<1||sourceSeen.has(n)||!c0||!s||
       !runner.sourcePresent||
       Object.keys(runner.sourcePresent).length!==3||
       !Array.isArray(runner.missingSourceFactors)||
       !runner.minimumStudySamples||
       Object.keys(runner.minimumStudySamples).length!==3||
       !Array.isArray(runner.sampleGaps)||
       runner.formalGradesVerified!==0||
       runner.formalGradeReady!==false||
       runner.officialJraVerified!==false||
       runner.holdoutValidated!==false)
     throw Error('3項目46点の馬番または資料フラグが不正');
    sourceSeen.add(n);
    const course=c0.comparableRuns>0,
     historyComplete=c0.historyLookupComplete,
     currentGoing=c0.currentGoingRecorded,
     sameGoing=currentGoing&&c0.matchingCurrentGoingRuns>0,
     position=s.pastFourthCorner!=='insufficient',
     paceObserved=pace.coverageAdequate&&s.scenarioFitBand!=='未評価',
     expected={course_distance:course&&historyComplete,
      pace:paceObserved,ground:sameGoing&&historyComplete},
     missing=keys.filter(k=>!expected[k]),
     sample={course_distance:historyComplete&&c0.comparableRuns>=3,
      pace:paceObserved,
      ground:historyComplete&&currentGoing&&c0.matchingCurrentGoingRuns>=3},
     blockers=[];
    if(!historyComplete)blockers.push('course_history_incomplete');
    if(c0.comparableRuns<3)blockers.push('course_sample_below_three');
    if(!currentGoing)blockers.push('current_going_not_recorded');
    if(c0.matchingCurrentGoingRuns<3)blockers.push('same_going_sample_below_three');
    if(!paceObserved)blockers.push('pace_scenario_unobserved');
    if(keys.some(k=>runner.sourcePresent[k]!==expected[k])||
       runner.missingSourceFactors.join('|')!==missing.join('|')||
       runner.allThreeSourcesPresent!==(missing.length===0)||
       keys.some(k=>runner.minimumStudySamples[k]!==sample[k])||
       runner.allThreeStudySamplesMet!==keys.every(k=>sample[k])||
       runner.sampleGaps.join('|')!==blockers.join('|'))
     throw Error('3項目46点の馬別資料判定が矛盾');
    stats.courseComparableObserved+=Number(course);
    stats.courseHistoryComplete+=Number(historyComplete);
    stats.currentGoingRecorded+=Number(currentGoing);
    stats.sameGoingObserved+=Number(sameGoing);
    stats.pacePositionObserved+=Number(position);
    stats.paceScenarioObserved+=Number(paceObserved);
    stats.allThreeSourcesObserved+=Number(
     course&&historyComplete&&sameGoing&&paceObserved);
    stats.noCourseComparableRuns+=Number(!course);
    stats.courseHistoryIncomplete+=Number(!historyComplete);
    stats.currentGoingUnknown+=Number(!currentGoing);
    stats.noSameGoingRuns+=Number(currentGoing&&!sameGoing);
    stats.paceScenarioUnassessed+=Number(!paceObserved);
    minimum.courseDistanceAtLeastThree+=Number(sample.course_distance);
    minimum.sameGoingAtLeastThree+=Number(sample.ground);
    minimum.paceScenarioObserved+=Number(sample.pace);
    minimum.allThreeMinimumStudySamples+=Number(
     keys.every(k=>sample[k]));
   }
   if(sourceSeen.size!==race.runnerCount||
      observedKeys.some(k=>race.observed[k]!==stats[k])||
      gapKeys.some(k=>race.gaps[k]!==stats[k])||
      Object.keys(minimum).some(k=>race.minimumSampleCoverage[k]!==minimum[k]))
    throw Error('3項目46点の資料件数が原履歴と一致しません');
   detail.threeFactorSourceGaps=race;
  }
  if(seen.size!==historyCoordinates.size)
   throw Error('3項目46点のレースが不足');
 }
 // Research-6 remaining 21-weight presence: never a scored factor.
 if(h.remaining21SourceGaps!==undefined){
  const v=h.remaining21SourceGaps,
   keys=['pedigree','draw_weight','jockey_stable','rotation','body_condition'],
   weights={pedigree:6,draw_weight:3,jockey_stable:10,rotation:1,body_condition:1},
   explanations={
    pedigree:'父・母父の独立した同条件実績と時系列検証',
    draw_weight:'枠と相対斤量の同条件成績と時系列検証',
    jockey_stable:'騎手・厩舎の条件別成績と馬の能力差調整',
    rotation:'前走間隔に応じた条件別成績と時系列検証',
    body_condition:'発走前の当日馬体重と前走比・JRA独立確認'
   };
  if(!v||v.version!=='owner-remaining21-source-gaps-1'||
     v.policyVersion!=='research-6'||v.sourcePolicyVersion!=='research-5'||
     v.raceCount!==historyCoordinates.size||
     v.initialResearchWeight!==79||v.remainingWeight!==21||
     v.totalWeight!==100||
     v.pedigreeStaffWeight!==16||v.pedigreeStaffGradesVerified!==0||
     v.independentPedigreeCohortValidated!==false||
     v.conditionMatchedStaffResultsValidated!==false||
     v.outOfTimePerformanceValidated!==false||
     !v.factorWeights||
     Object.keys(v.factorWeights).length!==5||
     keys.some(k=>v.factorWeights[k]!==weights[k])||
     v.verifiedFactorCount!==0||v.formallyEvaluatedHorseCount!==0||
     v.officialJraVerified!==false||v.independentResultsVerified!==false||
     v.historicalBandsCalibrated!==false||
     v.overallPredictionReady!==false||v.bettingReady!==false||
     v.autoPurchase!==false||v.researchOnly!==true||
     v.privateOwnerOnly!==true||v.extraProviderCalls!==0||
     v.changesExistingReceipts!==false||
     v.changesExistingTickets!==false||v.changesExistingRoi!==false||
     !Array.isArray(v.races)||v.races.length!==historyCoordinates.size||
     !Number.isInteger(v.priorSourceFourCompleteCount))
   throw Error('新配点21点の資料確認形式が不正');
  const seenRaces=new Set();let overallComplete=0;
  for(const race of v.races){
   const id=race?.track+'|'+race?.race,detail=perRace.get(id);
   if(!detail?.newWeightFive||!detail?.tenInventory||seenRaces.has(id)||
      race.runnerCount!==detail.runnerCount||race.gradeReady!==false||
      race.trifectaReady!==false||
      !Array.isArray(race.horses)||race.horses.length!==race.runnerCount||
      !race.sourceCoverageByFactor||
      Object.keys(race.sourceCoverageByFactor).length!==5||
      !Number.isInteger(race.priorSourceFourCompleteCount)||
      !Number.isInteger(race.research79ObservedCount)||
      !Number.isInteger(race.pedigreeParentageCompleteCount)||
      !Number.isInteger(race.staffIdentityCompleteCount)||
      !Number.isInteger(race.bothPedigreeStaffCompleteCount)||
      race.pedigreeStaffVerifiedGrades!==0)
    throw Error('新配点21点のレースと研究値が不一致');
   seenRaces.add(id);
   const old=new Map(detail.newWeightFive.horses.map(x=>[x.number,x])),
     source=new Map(detail.tenInventory.runners.map(x=>[x.number,x])),
     count=Object.fromEntries(keys.map(k=>[k,0])),seen=new Set();
   let priorComplete=0,observed79=0;
   for(const horse of race.horses){
    const n=horse?.number,a=old.get(n),b=source.get(n);
    if(!Number.isInteger(n)||n<1||n>18||seen.has(n)||!a||!b||
       horse.research79Observed!==(a.evidenceScore79!==null)||
       horse.research79!==a.evidenceScore79||
       !horse.sourceStates||!horse.sourceFieldsPresent||
       !horse.missingValidation||!Array.isArray(horse.missingSourceFields)||
       Object.keys(horse.sourceStates).length!==5||
       Object.keys(horse.sourceFieldsPresent).length!==5||
       Object.keys(horse.missingValidation).length!==5||
       horse.verifiedFactorCount!==0||horse.formalScore100!==null||
       horse.formalGrade!=='未評価'||horse.bettingReady!==false||
       !Number.isInteger(horse.sourceFieldCoverageEquivalent21))
     throw Error('新配点21点の馬番・得点の不正');
    seen.add(n);let coverage=0,fields=0;
    const missing=[];
    for(const k of keys){
     const state=b.sourceStates[k],
      ok=k==='body_condition'?false:
       k==='rotation'?state!=='unknown':
       state==='complete_fields_observed';
     if(horse.sourceStates[k]!==state||
        horse.sourceFieldsPresent[k]!==ok||
        horse.missingValidation[k]!==explanations[k])
      throw Error('新配点21点の根拠資料の不一致');
     if(ok)coverage+=weights[k];
     else missing.push(k);
     count[k]+=Number(ok);fields+=Number(ok);
    }
    if(horse.sourceFieldCoverageEquivalent21!==coverage||
       JSON.stringify(horse.missingSourceFields)!==JSON.stringify(missing))
     throw Error('新配点21点の資料カバー計算不一致');
    const parent=horse.sourceFieldsPresent.pedigree,
     staff=horse.sourceFieldsPresent.jockey_stable;
    const expectedGaps={
     pedigree:[...(parent?[]:['parentage_fields_incomplete']),
      'independent_condition_cohort_unavailable','temporal_holdout_not_validated'],
     jockey_stable:[...(staff?[]:['jockey_or_trainer_fields_incomplete']),
      'condition_matched_staff_results_unvalidated','temporal_holdout_not_validated'],
    };
    if(horse.pedigreeStaffSourceCoverage16!==6*Number(parent)+10*Number(staff)||
       horse.pedigreeStaffScoreReady!==false||
       JSON.stringify(horse.pedigreeStaffMissingEvidence)!==
        JSON.stringify(expectedGaps)||
       JSON.stringify(horse.pedigreeStaffGrades)!==
        JSON.stringify({pedigree:'未評価',jockey_stable:'未評価'})||
       !horse.pedigreeStaffScores||
       Object.keys(horse.pedigreeStaffScores).length!==2||
       horse.pedigreeStaffScores.pedigree!==null||
       horse.pedigreeStaffScores.jockey_stable!==null)
     throw Error('血統6・騎手厩舎10の採点前根拠に不整合');
    priorComplete+=Number(fields===4);
    observed79+=Number(horse.research79Observed);
   }
   if(seen.size!==old.size||seen.size!==source.size||
      race.priorSourceFourCompleteCount!==priorComplete||
      race.research79ObservedCount!==observed79||
      race.pedigreeParentageCompleteCount!==count.pedigree||
      race.staffIdentityCompleteCount!==count.jockey_stable||
      race.bothPedigreeStaffCompleteCount!==race.horses.filter(h=>
       h.sourceFieldsPresent.pedigree&&
       h.sourceFieldsPresent.jockey_stable).length||
      keys.some(k=>race.sourceCoverageByFactor[k]!==count[k]||
       count[k]!==detail.tenInventory.remainingFieldCoverage[k]))
    throw Error('新配点21点の件数不一致');
   overallComplete+=priorComplete;
   detail.remaining21=race;
  }
  if(seenRaces.size!==historyCoordinates.size||
     overallComplete!==v.priorSourceFourCompleteCount)
   throw Error('新配点21点の対象不足');
 }
 // research-6 theoretical score ranges; never formal win probabilities.
 if(h.research6Uncertainty!==undefined){
  const u=h.research6Uncertainty,
   five=['training','course_distance','pace','ground','recent'],
   rest=['pedigree','draw_weight','jockey_stable','rotation','body_condition'],
   w={training:30,recent:3,course_distance:17,pace:17,ground:12,
    pedigree:6,draw_weight:3,jockey_stable:10,rotation:1,body_condition:1},
   pts={S:3,A:2,B:1,C:0};
  if(!u||u.version!=='owner-research6-uncertainty-intervals-1'||
     u.policyVersion!=='research-6'||
     u.raceCount!==historyCoordinates.size||
     !Array.isArray(u.races)||u.races.length!==historyCoordinates.size||
     !u.factorWeights||Object.keys(u.factorWeights).length!==10||
     Object.keys(w).some(k=>u.factorWeights[k]!==w[k])||
     u.observedFactorWeightCeiling!==79||u.alwaysUnassessedWeight!==21||
     u.jockeyStableUnassessedWeight!==10||
     u.verifiedFactorCount!==0||u.formalScoreReady!==false||
     u.officialJraVerified!==false||u.bettingReady!==false||
     u.autoPurchase!==false||u.researchOnly!==true||
     u.privateOwnerOnly!==true||u.extraProviderCalls!==0||
     u.changesExistingReceipts!==false||
     u.changesExistingTickets!==false||
     u.changesExistingRoi!==false)
   throw Error('研究用100点幅の形式が不正');
  const seenRaces=new Set();
  for(const race of u.races){
   const id=race?.track+'|'+race?.race,d=perRace.get(id);
   if(!d?.newWeightFive||!d?.remaining21||seenRaces.has(id)||
      race.runnerCount!==d.runnerCount||race.researchOnly!==true||
      race.formalRankReady!==false||race.trifectaReady!==false||
      !Array.isArray(race.horses)||race.horses.length!==race.runnerCount||
      !Number.isInteger(race.strictAdvantagePairCount))
    throw Error('研究用100点幅のレース不一致');
   seenRaces.add(id);
   const prior=new Map(d.newWeightFive.horses.map(x=>[x.number,x])),
    support=new Map(d.remaining21.horses.map(x=>[x.number,x])),
    seen=new Set(),all=[];
   for(const h0 of race.horses){
    const n=h0?.number,p=prior.get(n),g=support.get(n);
    if(!Number.isInteger(n)||n<1||n>18||seen.has(n)||!p||!g||
       !Array.isArray(h0.unassessedFiveFactors)||
       !Array.isArray(h0.arithmeticallyAbove)||
       h0.formalScore100!==null||h0.formalGrade!=='未評価'||
       h0.formalRank!==null||h0.scoreIsCalibrated!==false||
       h0.bettingReady!==false)
     throw Error('研究用100点幅の馬番・正式評価不一致');
    seen.add(n);
    const missing=five.filter(k=>p.bands[k]==='未評価'),
     unassessed=21+missing.reduce((sum,k)=>sum+w[k],0);
    const lower=five.reduce((sum,k)=>sum+
      (p.bands[k]==='未評価'?0:w[k]*pts[p.bands[k]]),0),
     upper=lower+3*unassessed;
    if(h0.observedHypothesisFactors!==5-missing.length||
       h0.unassessedFiveFactors.join('|')!==missing.join('|')||
       h0.unassessedTotalWeight!==unassessed||
       h0.jockeyStableStillUnassessedWeight!==10||
       h0.otherUnassessedWeight!==unassessed-10||
       h0.lowerResearchRawThirdPoints!==lower||
       h0.upperResearchRawThirdPoints!==upper||
       h0.lowerResearchBound!==Math.round(lower*100/3)/100||
       h0.upperResearchBound!==Math.round(upper*100/3)/100||
       (p.rawThirdPoints!==null&&p.rawThirdPoints!==lower))
     throw Error('研究用100点幅の算術不一致');
    all.push(h0);
   }
   if(seen.size!==prior.size||seen.size!==support.size)
    throw Error('研究用100点幅の馬番不足');
   let advantagePairs=0;
   for(const h0 of all){
    const stronger=all.filter(x=>x.number!==h0.number&&
      h0.lowerResearchRawThirdPoints>x.upperResearchRawThirdPoints)
      .map(x=>x.number);
    const best=1+all.filter(x=>x.number!==h0.number&&
      x.lowerResearchRawThirdPoints>h0.upperResearchRawThirdPoints).length,
     worst=1+all.filter(x=>x.number!==h0.number&&
      x.upperResearchRawThirdPoints>=h0.lowerResearchRawThirdPoints).length;
    if(JSON.stringify(h0.arithmeticallyAbove)!==JSON.stringify(stronger)||
       h0.researchPossibleBestRank!==best||
       h0.researchPossibleWorstRank!==worst)
     throw Error('研究用100点幅の順位比較不一致');
    advantagePairs+=stronger.length;
   }
   if(race.strictAdvantagePairCount!==advantagePairs)
    throw Error('研究用100点幅の比較件数不一致');
   d.research6Uncertainty=race;
  }
  if(seenRaces.size!==historyCoordinates.size)
   throw Error('研究用100点幅のレース不足');
 }
 // One owner-only 79/100 research 3連単 draft per prestart slot.
 // This is a newer hypothesis alongside (not replacing) signed legacy 85.
 if(h.research6FiveDrafts!==undefined){
  const v=h.research6FiveDrafts,keys=[
   'training','course_distance','pace','ground','recent'],
   weights={training:30,course_distance:17,pace:17,ground:12,recent:3},
   reasons=new Set(['missing_provisional_off','past_provisional_off',
    'runner_count_unconfirmed','too_few_runners',
    'incomplete_five_factors','tied_cutoff']);
  if(!v||v.version!=='owner-research6-fivecore-drafts-1'||
     v.policyVersion!=='research-6'||v.date!==historyDay||
     v.researchFactorWeight!==79||
     v.remainingUnassessedWeight!==21||v.unitYen!==100||
     !v.factorWeights||Object.keys(v.factorWeights).length!==5||
     keys.some(k=>v.factorWeights[k]!==weights[k])||
     v.officialJraVerified!==false||
     v.overallPredictionReady!==false||v.bettingReady!==false||
     v.autoPurchase!==false||v.actualPurchase!==false||
     v.researchOnly!==true||v.privateOwnerOnly!==true||
     v.extraProviderCalls!==0||
     v.changesExistingReceipts!==false||
     v.changesExistingTickets!==false||v.changesExistingRoi!==false||
     v.raceCount!==historyCoordinates.size||
     !Array.isArray(v.races)||v.races.length!==historyCoordinates.size||
     !Number.isInteger(v.draftCount)||!Number.isInteger(v.holdCount)||
     !v.holdReasons||typeof v.holdReasons!=='object')
   throw Error('79点研究用下書きの形式が不正');
  const seenRaces=new Set(),counts={};let drafts=0,holds=0;
  for(const race of v.races){
   const id=race?.track+'|'+race?.race,d=perRace.get(id),
    prior=d?.newWeightFive;
   if(!prior||seenRaces.has(id)||
      race.runnerCount!==prior.runnerCount||
      race.completeObserved!==prior.completeObserved||
      race.researchOnly!==true||race.officialJraVerified!==false||
      race.overallPredictionReady!==false||race.bettingReady!==false||
      race.autoPurchase!==false||
      !Array.isArray(race.first)||!Array.isArray(race.second)||
      !Array.isArray(race.third)||!Array.isArray(race.tickets)||
      !Array.isArray(race.rankedResearch)||
      !Number.isInteger(race.points)||!Number.isInteger(race.amountYen))
    throw Error('79点研究用下書きの馬番照合不一致');
   seenRaces.add(id);
   if(race.status==='hold'){
    if(!reasons.has(race.reason)||race.points!==0||race.amountYen!==0||
       race.first.length||race.second.length||race.third.length||
       race.tickets.length||race.rankedResearch.length)
     throw Error('保留中の79点下書きに買い目が混入');
    holds++;counts[race.reason]=(counts[race.reason]||0)+1;
   }else if(race.status==='five_factor_research_draft'){
    const runners=prior.horses.slice().sort((a,b)=>
     b.rawThirdPoints-a.rawThirdPoints||a.number-b.number);
    if(race.reason!=='unverified_five_factor_hypotheses'||
       !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(race.postTime)||
       runners.length<4||runners.some(x=>x.rawThirdPoints===null)||
       race.rankedResearch.length!==runners.length||
       race.first.length!==2&&race.first.length!==3||
       race.second.length<=race.first.length||
       race.second.length>5||race.third.length<race.second.length||
       race.third.length>9)
     throw Error('79点研究用下書きの根拠不足');
    for(let i=0;i<runners.length;i++){
     const a=race.rankedResearch[i],b=runners[i];
     const rank=1+runners.filter(x=>
      x.rawThirdPoints>b.rawThirdPoints).length;
     if(!a||a.number!==b.number||a.research79!==b.evidenceScore79||
        a.comparisonRank!==rank)
      throw Error('79点研究用順位が資料と不一致');
    }
    const prefixes=[
     [race.first,race.first.length],
     [race.second,race.second.length],
     [race.third,race.third.length]
    ];
    for(const [numbers,count] of prefixes){
     if(JSON.stringify(numbers)!==JSON.stringify(
        runners.slice(0,count).map(x=>x.number))||
        (count<runners.length&&
         runners[count-1].rawThirdPoints===runners[count].rawThirdPoints))
      throw Error('79点研究用の同点馬を恣意的に除外');
    }
    const expected=[];
    for(const x of race.first)for(const y of race.second)
     for(const z of race.third)
      if(x!==y&&x!==z&&y!==z)expected.push([x,y,z]);
    if(expected.length<1||expected.length>40||
       race.points!==expected.length||
       race.amountYen!==expected.length*100||
       JSON.stringify(race.tickets)!==JSON.stringify(expected))
     throw Error('79点研究用の買い目算術不一致');
    drafts++;
   }else throw Error('79点研究用の状態が不正');
   d.research6FiveDraft=race;
  }
  if(seenRaces.size!==historyCoordinates.size||
     drafts!==v.draftCount||holds!==v.holdCount||
     JSON.stringify(v.holdReasons)!==JSON.stringify(counts))
   throw Error('79点研究用の件数不一致');
 }
 validateWatchCapture(h.watchCapture,h);
 return results;
}
function jstToday(){return new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});}

function updateJraReleaseGuide(){
 const date=$('autoDay').value,now=new Date();
 if(!/^20\d{2}-\d{2}-\d{2}$/.test(date)||
    Number.isNaN(new Date(date+'T12:00:00Z').valueOf())||
    new Date(date+'T12:00:00Z').toISOString().slice(0,10)!==date){
  $('autoJraReleaseGuide').textContent='開催日が不正です。JRA公開目安は未計算。';return;
 }
 const selected=new Date(date+'T12:00:00Z'),weekday=selected.getUTCDay();
 if(weekday!==0&&weekday!==6){
  $('autoJraReleaseGuide').textContent='平日・変則開催は土日の通常発表時刻を適用しません。JRA公式で確認（照合0R）。';return;
 }
 const prev=n=>new Date(selected.valueOf()-n*86400000).toISOString().slice(0,10);
 const thursday=prev(weekday===6?2:3),prior=prev(1);
 // 15 minutes is a UI buffer, not proof that the JRA has published.
 const unnamed=new Date(thursday+'T16:15:00+09:00').valueOf();
 const numbered=new Date(prior+'T10:15:00+09:00').valueOf();
 const stage=now.valueOf()<unnamed?
  '通常の馬番なし出馬表の発表目安は '+thursday+' 16時すぎ':
  now.valueOf()<numbered?
   '馬番なし出馬表の通常目安は経過。馬番付きは '+prior+' 10時すぎが通常目安':
   '馬番付き出馬表の通常公開目安は経過（実際の掲載は未確認）';
 // JRA's published 2026 schedule lists the Queen Elizabeth II Cup on
 // Nov 15. The class-(2) G1 card has an earlier Friday 9am release
 // target than regular cards. Do not apply that timing to all races.
 const earlyG1=date==='2026-11-15'?'エリザベス女王杯（GⅠ）':null;
 const earlyPrior=prev(2); // Nov 15 G1 (Friday 9am), not regular Sunday races.
 const earlyNumbered=new Date(earlyPrior+'T09:15:00+09:00').valueOf();
 const g1Note=earlyG1?(now.valueOf()<earlyNumbered?
  '。'+earlyG1+'の馬番付き出馬表は '+earlyPrior+
   ' 9時すぎが発表目安（その他のレースは通常10時すぎ）':
  '。'+earlyG1+'の9時すぎの発表目安は経過（掲載・取消の確認は別）'):'';
 // JRA also moves PRE-SALE weekend stakes to Friday 9am when a category-(2)
 // G1 is in the same week. This does not apply to every weekend race.
 const advanceStakes=(date==='2026-11-14'||date==='2026-11-15')
  ?'。同週の特例GⅠに伴い、前日発売を行う土日重賞も金曜日9時すぎが発表目安（全レース共通ではありません）':'';
 $('autoJraReleaseGuide').textContent=stage+g1Note+advanceStakes+
  '。GⅠ・一部重賞・変則開催は別時刻。公開目安は掲載保証ではありません。'+
  'JRA公式の馬番・取消・馬場・発走時刻は自動照合していません（0R）。';
}
function updateJraCrosscheck(){
 const tracks=[...jraDraftTracks].sort(),linked=[...jraPdfTracks].sort();
 const missing=tracks.filter(k=>!jraPdfTracks.has(k));
 const extras=linked.filter(k=>!jraDraftTracks.has(k));
 $('autoJraCrosscheck').textContent=
  'JRA公式との独立照合 0R（未実施）。JRDBの開催場 '+
  tracks.length+'場'+(tracks.length?'（'+tracks.join('・')+'）':'（未取得）')+'。'+
  (jraPdfChecked?
   'JRA公式PDFリンク '+linked.length+'場分。'+
   (tracks.length?'リンク未検出 '+missing.length+'場'+
    (missing.length?'（'+missing.join('・')+'）':'')+'。':'')+
   (extras.length?'PDFだけ検出 '+extras.join('・')+'。':''):
   'JRA公式PDFリンクは未検索。')+
  'リンク未検出は開催なしを意味せず、リンク発見も馬番・取消・馬場・発走時刻の一致を証明しません。';
}

// The 2026 Monday race days are JRA-published exceptions, not every
// Monday. A hidden/disabled shortcut must never trigger a paid JRDB call.
// 2026 holiday schedule plus Nov 30 Tokyo reorganisation confirmed
// https://www.jra.go.jp/news/202611/112301.html (Nov 23, 2026).
// Exact known dates only; ordinary Mondays are never inferred.
const CONFIRMED_MONDAY_RACEDAYS=new Set([
 '2026-01-12','2026-09-21','2026-10-12','2026-11-23','2026-11-30'
]);
// The chosen date determines which shortcut is highlighted; neither
// highlighting nor changing a date triggers a provider request.
function highlightSelectedWeekend(){
 const selected=$('autoDay').value;
 const dt=new Date(selected+'T12:00:00Z');
 const weekday=Number.isFinite(dt.valueOf())&&
  dt.toISOString().slice(0,10)===selected?dt.getUTCDay():-1;
 $('autoSaturdayQuick').dataset.selected=String(weekday===6);
 $('autoSundayQuick').dataset.selected=String(weekday===0);
 const monday=nearestJstWeekday(1);
 const canMonday=CONFIRMED_MONDAY_RACEDAYS.has(monday);
 for(const id of ['autoMondayQuick','autoMonday']){
  $(id).hidden=!canMonday;
  $(id).disabled=!canMonday;
 }
 // Published Monday may be holiday or special reorganisation; this
 // shortcut makes no provider read and is not a publication claim.
 const tomorrow=new Date(jstToday()+'T12:00:00Z');
 tomorrow.setUTCDate(tomorrow.getUTCDate()+1);
 const tomorrowIso=tomorrow.toISOString().slice(0,10);
 const mondayType=monday==='2026-11-30'?'月・再編':'月祝';
 $('autoMondayQuick').textContent=(canMonday&&monday===tomorrowIso
  ?'明日'+monday.slice(5).replace('-','/')+'（'+mondayType+'）の全R研究予想を取得（1回）'
  :'開催月曜（'+mondayType+'）の予想を取得・表示（1回）');
 $('autoMondayQuick').dataset.selected=String(
  canMonday&&weekday===1&&selected===monday);
}
$('autoDay').value=jstToday();
updateSavedResultRaceOptions($('autoDay').value.replaceAll('-',''));
highlightSelectedWeekend();
showSavedWorkoutLocks($('autoDay').value.replaceAll('-',''));
showSavedWorkoutPairHistory($('autoDay').value.replaceAll('-',''));
showSavedWorkoutCrossHistory($('autoDay').value.replaceAll('-',''));
updateJraReleaseGuide();updateJraCrosscheck();
function updateReviewLink(){
 const day=$('autoDay').value;
 const valid=/^20\d{2}-\d{2}-\d{2}$/.test(day)&&
  !Number.isNaN(new Date(day+'T12:00:00Z').valueOf())&&
  new Date(day+'T12:00:00Z').toISOString().slice(0,10)===day;
 const target='/owner-100yen-review'+
  (valid?'?date='+encodeURIComponent(day):'');
 $('autoReviewLink').href=target;
 $('autoQualityLink').href=target;
}
$('autoDay').onchange=()=>{
 highlightSelectedWeekend();
 resetResolvedJraCard();
 $('autoOfficialCardUrl').value='';
 resetUnverifiedResultCandidate();
 updateSavedResultRaceOptions($('autoDay').value.replaceAll('-',''));
 $('autoOfficialCardStatus').textContent='開催日を変更しました。JRA公式Web出馬表の候補は未確認です。';
 resetAdvanceProgramme();
 workoutProviderSeq++;
 workoutPairVerifySeq++;
 $('autoWorkoutPairVerifyStatus').textContent='選択日を変更しました。研究結果の署名は未検証。';
 $('autoWorkoutProviderSummary').replaceChildren();
 $('autoWorkoutProviderStatus').textContent='選択日の署名付き調教研究記録がある場合のみ暫定結果を照合できます。';
 showSavedWorkoutLocks($('autoDay').value.replaceAll('-',''));
 showSavedWorkoutPairHistory($('autoDay').value.replaceAll('-',''));
showSavedWorkoutCrossHistory($('autoDay').value.replaceAll('-',''));
 ++preflightSeq;
 $('autoPreflight').disabled=false;
 $('autoPreflightStatus').textContent='選択日が変わりました。無料診断は未実行です。';
 // Preserve an explicitly selected day across subsequent app resumes.
 followingToday=false;
 latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;clearAutomaticOffTimer();
 latestReadAtMs=0;showSnapshotFreshness();
 clearDraftShortcut();
 // Invalidate the old response and unlock the button. A slow old request
 // must not leave the new day permanently disabled on iPhone.
 request++;$('autoRun').disabled=false;
 updateReviewLink();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
 $('autoMissingFactorSummary').textContent='開催日を取得すると未評価の内訳を確認できます。';
 $('autoMissingFactorRaces').replaceChildren();
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 clearHistory();
 $('autoSummary').textContent='未取得';
 $('autoEasyPulse').textContent='この開催日の予想は未取得です。';
 $('autoRaceQuickSummary').textContent='予想は未取得です。';
 $('autoSourceSummary').textContent='全Rの資料進捗は未取得です。';
 $('autoTrackWorkouts').textContent='調教S/Aの参考表示：開催日のデータは未取得です。';
 $('autoReadProof').textContent='開催日を切り替えました。JRDB資料はまだ照会していません。';
 $('autoMorningStatus').textContent='開催日の取得結果を確認中です。正式な10項目予想ではありません。';
 $('autoHoldBreakdown').textContent='見送り理由の内訳はJRDB資料を取得すると表示します。';
 $('autoOperationalNext').textContent='開催日の次の操作：当日の取得結果を確認中。';
 $('autoProgrammeCoverage').textContent='開催場別の取得R数：まだ確認していません。';
 $('autoRecordSafety').textContent='固定記録の保管状態：まだ確認していません。';
 $('autoFixedConsistency').textContent='固定記録と下書きの差異は未確認。既存の記録は変更していません。';
 $('autoTenWeights').replaceChildren();
 $('autoTenStatus').textContent='10項目の評価を取得していません。';
 $('autoFormalShadowStatus').textContent='開催日を変更しました。正式10項目ゲートへの接続は未確認です。';
 $('autoSavedStatus').textContent=localReceiptStatus(
  $('autoDay').value.replaceAll('-',''));
 showFixedHistory($('autoDay').value.replaceAll('-',''));
 renderFixedQuick($('autoDay').value.replaceAll('-',''),true);
 $('autoStatus').textContent='開催日を選んでな。';
};
// Weekend shortcuts only change the date. They do not read paid data.
function nearestJstWeekday(target){
 const today=jstToday();
 const date=new Date(today+'T12:00:00Z');
 if(!Number.isFinite(date.valueOf()))throw Error('Invalid JST date');
 const add=(target-date.getUTCDay()+7)%7;
 date.setUTCDate(date.getUTCDate()+add);
 return date.toISOString().slice(0,10);
}
function chooseUpcomingJstDay(weekday){
 const selected=nearestJstWeekday(weekday),input=$('autoDay');
 if(input.value!==selected){
  input.value=selected;
  input.onchange();
 }else followingToday=false;
 $('autoStatus').textContent=selected+
  'を選択しました。JRDBの追加照会はまだ行っていません。全場・全Rを再分析するボタンで取得できます。';
}
$('autoSaturday').onclick=()=>chooseUpcomingJstDay(6);
$('autoSunday').onclick=()=>chooseUpcomingJstDay(0);
$('autoMonday').onclick=()=>{
 if(!CONFIRMED_MONDAY_RACEDAYS.has(nearestJstWeekday(1))){
  $('autoStatus').textContent='次の月曜日のJRA開催は未確認です。追加照会は0回。';
  return;
 }
 chooseUpcomingJstDay(1);
};
// A single, explicit owner gesture combines date selection and the
// existing ONE guarded owner-auto-draft request. No extra probe/read, no
// background schedule, and no second request while one is in flight.
// A direct weekend tap goes straight to the useful race list only when
// the matching day has actually been validated and rendered. A failed,
 // stale or 0R provider response never jumps to a misleading forecast.
function revealOneTapForecast(selectedDay){
 if(!latestDisplayedReport||latestDisplayedReport.raceCount<=0||
    latestDisplayedDay!==selectedDay||
    $('autoDay').value.replaceAll('-','')!==selectedDay)return;
 // The server's verified draft slots have already passed the normal
 // date/roster/signature and local off-time checks inside render().
 // Reuse THAT existing filtered shortcut instead of dropping a new owner
 // into a full 24/36-R list dominated by held and past-off races.
 // A 0R/held/expired response must never open an actionable-looking card.
 const shortcut=$('autoDraftShortcut');
 if(typeof shortcut.onclick!=='function'||
    !/^買い目あり [1-9][0-9]*Rだけ見る/.test(shortcut.textContent))
  return;
 shortcut.onclick(); // display only: no new request, score or receipt write
 const main=$('forecastRacesSection');
 if(typeof main.scrollIntoView==='function')
  main.scrollIntoView({behavior:'smooth',block:'start'});
}
async function quickWeekendForecast(weekday,buttonId,label,daysBefore){
 const button=$(buttonId);
 if(button.disabled)return;
 if($('autoRun').disabled){
  $('autoStatus').textContent='JRDB照会中です。完了後に'+label+'の取得を押してください。追加照会はしていません。';
  return;
 }
 const selected=nearestJstWeekday(weekday);
 if(weekday===1&&!CONFIRMED_MONDAY_RACEDAYS.has(selected)){
  $('autoStatus').textContent='月曜開催はJRA公表済みの日付だけ1タップ取得できます。追加のJRDB照会は0回。';
  return;
 }
 const releaseDate=new Date(selected+'T12:00:00Z');
 releaseDate.setUTCDate(releaseDate.getUTCDate()-daysBefore);
 const earliest=releaseDate.toISOString().slice(0,10);
 if(jstToday()<earliest){
  $('autoStatus').textContent=label+'のクイック取得は'+
   (weekday===1?'金曜':'木曜')+'以降に利用できます。'+
   'JRDB配信前の可能性があるため今回は有料照会していません。';
  return;
 }
 const selectedDay=selected.replaceAll('-','');
 // Reuse a verified same-day result, even when /tra=0. The operator can
 // explicitly reanalyse after the upstream feed publishes new material.
 if($('autoDay').value===selected&&latestDisplayedReport&&
    latestDisplayedDay===selectedDay){
  if(latestDisplayedReport.raceCount===0){
   $('autoStatus').textContent='【'+label+'番組0R・取得済み】この画面でJRDB番組0件を確認済み。'+
    '押し直しによる追加のJRDB照会は0回。開催なしとは断定できません。'+
    '木曜の配信更新後などに新しい情報を確認する場合は「全場・全Rを再分析する」を押してください。';
   return;
  }
  try{
   latestExpiredDraftCount=latestDisplayedReport.races.filter(r=>
    r.status==='provisional_draft'&&draftExpiredOnDevice(selectedDay,r.postTime)).length;
   render(latestDisplayedReport,selectedDay);
   showSnapshotFreshness();
   $('autoStatus').textContent='【'+label+'データ取得済み】この画面の取得済み研究結果を再表示しました。'+
    '追加のJRDB照会は0回。新しい資料を取得する場合は「全場・全Rを再分析する」を押してください。';
   revealOneTapForecast(selectedDay);
  }catch(_){
   $('autoRaces').replaceChildren();
   $('autoStatus').textContent='保存済み情報の表示を確認できません。'+
    '固定済み履歴を保護し、追加の有料照会は行いません。';
  }
  return;
 }
 button.disabled=true;
 try{
  chooseUpcomingJstDay(weekday);
  if($('autoDay').value!==selected){
   $('autoStatus').textContent='日付が切り替わりました。照会せず、開催日を確認してください。';
   return;
  }
  if(showRecentlyFixedWithoutProvider(selectedDay,label)){
   return;
  }
  // Exactly one authenticated auto-draft request. No probe, retry, or
  // background schedule; the owner must explicitly request reanalysis.
  await $('autoRun').onclick();
  revealOneTapForecast(selectedDay);
 }finally{button.disabled=false;}
}
$('autoSaturdayQuick').onclick=()=>quickWeekendForecast(6,'autoSaturdayQuick','土曜',2);
$('autoSundayQuick').onclick=()=>quickWeekendForecast(0,'autoSundayQuick','日曜',3);
$('autoMondayQuick').onclick=()=>quickWeekendForecast(1,'autoMondayQuick',
 nearestJstWeekday(1)==='2026-11-30'?'月曜再編':'月祝',3);
// Opt-in JRA advance programme: one fixed-site public GET, no JRDB calls.
// Comparing published planned times to /tra does NOT certify official
// starters, scratches, going, current off or final 10-factor readiness.
let advanceProgrammeSeq=0;
let advanceRaceWarnings=new Map(),advanceRaceMarkers=new Map();
function clearAdvanceRaceWarnings(){
 advanceRaceWarnings.clear();
 for(const marker of advanceRaceMarkers.values())
  marker.node.textContent=marker.base;
}
function resetAdvanceProgramme(){
 advanceProgrammeSeq++;
 clearAdvanceRaceWarnings();
 const d=$('autoDay').value;
 const link=$('autoAdvanceDirect');
 if(/^20\d{2}-\d{2}-\d{2}$/.test(d)&&
    Number(d.slice(0,4))>=2020&&Number(d.slice(0,4))<=2035&&
    Number.isFinite(Date.parse(d+'T12:00:00Z'))&&
    new Date(d+'T12:00:00Z').toISOString().slice(0,10)===d){
  const y=d.slice(0,4),m=d.slice(5,7),day=d.slice(8,10);
  link.href='https://www.jra.go.jp/keiba/calendar'+y+'/'+y+'/'+m+'/'+m+day+'.html';
  link.textContent='JRA公式の'+d+'競馬番組（予定）を直接開く';
 }else{
  link.href='https://www.jra.go.jp/keiba/';
  link.textContent='JRA公式の開催日程を直接開く';
 }
 $('autoAdvanceCompare').disabled=false;
 $('autoAdvanceHeadline').textContent='JRA事前競馬番組：未確認。最終出走・取消・馬場・発走時刻は別に確認してください。';
 $('autoAdvanceStatus').textContent='開催日またはJRDB受信資料が変わりました。JRA予定番組は未比較です。';
 $('autoAdvanceDifferences').replaceChildren();
}
$('autoAdvanceCompare').onclick=async()=>{
 const button=$('autoAdvanceCompare'),status=$('autoAdvanceStatus');
 if(button.disabled)return;
 const date=$('autoDay').value,day=date.replaceAll('-','');
 const source=latestDisplayedReport;
 if(!/^20\d{2}-\d{2}-\d{2}$/.test(date)||
    !source||latestDisplayedDay!==day||
    $('autoDay').value.replaceAll('-','')!==latestDisplayedDay){
  status.textContent='先にこの開催日のJRDB全R資料を取得してください。JRAへの追加アクセスは0回。';
  return;
 }
 const seq=++advanceProgrammeSeq;
 clearAdvanceRaceWarnings();
 button.disabled=true;
 $('autoAdvanceDifferences').replaceChildren();
 status.textContent='JRA公表の予定競馬番組を確認中（無料・最終出馬表ではありません）…';
 $('autoAdvanceHeadline').textContent='JRA事前競馬番組：無料で予定時刻・距離を比較中。正式な最終照合ではありません。';
 try{
  const response=await fetch('/api/jra/advance-programme?date='+
   encodeURIComponent(date),{
    credentials:'same-origin',cache:'no-store',
    headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(seq!==advanceProgrammeSeq||date!==$('autoDay').value||
     latestDisplayedReport!==source||latestDisplayedDay!==day)return;
  if(!response.ok)throw Error('jra_advance_unavailable');
  const p=await response.json();
  if(seq!==advanceProgrammeSeq||date!==$('autoDay').value||
     latestDisplayedReport!==source||latestDisplayedDay!==day)return;
  const venues=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
  if(!p||p.version!=='owner-jra-advance-programme-reference-1'||
     p.date!==date||p.referenceKind!=='advance_schedule_not_final_racecard'||
     !Array.isArray(p.races)||p.races.length<24||p.races.length>48||
     p.raceCount!==p.races.length||!Number.isInteger(p.venueCount)||
     p.venueCount<2||p.venueCount>4||
     p.officialFinalCardVerified!==false||
     p.officialStartersVerified!==false||p.officialScratchesVerified!==false||
     p.officialGoingVerified!==false||p.officialPostTimeVerified!==false||
     p.predictionReady!==false||p.bettingReady!==false||
     p.existingTicketsChanged!==false||p.existingReceiptsChanged!==false||
     p.newJrdbRequests!==0)
   throw Error('jra_advance_contract');
  const seen=new Set(),byVenue=new Map();
  for(const row of p.races){
   if(!row||!venues.has(row.track)||!Number.isInteger(row.race)||
      row.race<1||row.race>12||
      typeof row.postTime!=='string'||!/^([01]\d|2[0-3]):[0-5]\d$/.test(row.postTime)||
      !Number.isInteger(row.distanceM)||row.distanceM<600||row.distanceM>5000||
      !(row.surface===null||row.surface==='芝'||row.surface==='ダート'))
    throw Error('jra_advance_race');
   const key=row.track+'|'+row.race;
   if(seen.has(key))throw Error('jra_advance_duplicate');
   seen.add(key);
   byVenue.set(row.track,(byVenue.get(row.track)||0)+1);
  }
  if(byVenue.size!==p.venueCount||
     [...byVenue.values()].some(n=>n!==12))
   throw Error('jra_advance_incomplete');
  if(!Array.isArray(source.races)||source.races.length!==source.raceCount)
   throw Error('source_roster_mismatch');
  const sourceBy=new Map(source.races.map(x=>[x.track+'|'+x.race,x]));
  if(sourceBy.size!==source.races.length)
   throw Error('duplicate_jrdb_slot');
  const contextBy=new Map((source.raceContext?.races||[])
   .map(x=>[x.track+'|'+x.race,x]));
  const alerts=[],raceWarnings=new Map();
  let matched=0,unknown=0,compared=0,missingSlots=0,fieldDiffs=0;
  const warn=(key,label)=>{
   const found=raceWarnings.get(key)||[];
   if(found.length<4&&!found.includes(label))found.push(label);
   raceWarnings.set(key,found);
  };
  for(const row of p.races){
   const key=row.track+'|'+row.race,original=sourceBy.get(key);
   if(!original){
    // Missing races are not field-level differences. Keep all three
    // missing comparisons visible instead of silently reporting 0 issues.
    unknown+=3;missingSlots++;
    alerts.push(row.track+' '+row.race+
     'R｜JRDB受信番組にないレース（事前予定との照合保留）');
    continue;
   }
   const context=contextBy.get(key);
   for(const [field,a,b,format] of [
    ['発走時刻',original.postTime,row.postTime,x=>x],
    ['距離',context?.distance_m,row.distanceM,x=>String(x)+'m'],
    ['芝・ダート',context?.surface,row.surface,x=>x]
   ]){
    if(b===null||a===undefined||a===null||a==='未確認'){
     unknown++;
    }else{
     compared++;
     if(a!==b){
      fieldDiffs++;
      warn(key,field+'がJRA事前予定と不一致');
      alerts.push(row.track+' '+row.race+'R｜'+field+
       '：JRDB '+format(a)+'／JRA予定 '+format(b));
     }else matched++;
    }
   }
  }
  for(const item of source.races){
   if(!seen.has(item.track+'|'+item.race)){
    unknown+=3;missingSlots++;
    warn(item.track+'|'+item.race,'JRA事前競馬番組に該当レースなし');
    alerts.push(item.track+' '+item.race+
     'R｜JRA事前番組にないレース（変更・欠落の可能性を要確認）');
   }
  }
  if(alerts.length>90)throw Error('too_many_alerts');
  // The matching, validated in-memory day only. No final JRA approval.
  advanceRaceWarnings=new Map([...raceWarnings].map(([key,labels])=>[
   key,'【JRA事前予定差異・最終未確認】'+labels.join('／')+
    '。JRA最新出馬表で再確認（研究用買い目・固定履歴は変更なし）。'
  ]));
  for(const [key,marker] of advanceRaceMarkers)
   marker.node.textContent=marker.base+
    (advanceRaceWarnings.has(key)?'｜⚠ JRA事前予定差異・要確認':'');
  const host=$('autoAdvanceDifferences');
  for(const message of alerts)
   host.append(dom('p',message,'muted'));
  $('autoAdvanceHeadline').textContent='JRA事前競馬番組の参考比較：差異 '+fieldDiffs+'項目・番組不一致 '+missingSlots+'R・未比較 '+unknown+'項目。正式な最終照合ではありません。';
  status.textContent='JRA事前番組 '+p.raceCount+'R／JRDB受信 '+source.raceCount+
   'R｜比較 '+compared+'項目・予定と一致 '+matched+
   '項目・差異 '+fieldDiffs+'項目・番組不一致 '+missingSlots+'R・未比較 '+unknown+'項目。'+
   (alerts.length?'下に違いを表示。':'比較できた予定項目で差異はありません。')+
   '【重要】事前の予定表との比較だけ。最終出走・取消・馬場・実際の発走時刻は未照合。';
 }catch(_){
  if(seq===advanceProgrammeSeq){
   $('autoAdvanceDifferences').replaceChildren();
   $('autoAdvanceHeadline').textContent='JRA事前競馬番組：取得できず未確認。研究用予想・固定記録はそのままです。';
   status.textContent='JRA事前番組を自動取得できませんでした。'+
    '上の「JRA公式の競馬番組」を直接開いてください。'+
    '取得元が利用できない・ページ形式が変わった場合は未確認として扱います。'+
    '既存の予想・固定記録は無変更です。';
  }
 }finally{
  if(seq===advanceProgrammeSeq)button.disabled=false;
 }
};
// Optional, JRA-only HTML index lookup. Never use the PDF URL as evidence
// of specific runners, scratches, going, off times, finalized picks or ROI.
$('autoOfficialPdf').onclick=async()=>{
 const button=$('autoOfficialPdf'),date=$('autoDay').value;
 if(button.disabled)return;
 const seq=++officialPdfSeq;
 button.disabled=true;
 $('autoOfficialPdfLinks').replaceChildren();
 $('autoOfficialPdfStatus').textContent='選択日のJRA公式PDFリンクを確認中…';
 try{
  if(!/^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/.test(date)||
     Number.isNaN(new Date(date+'T12:00:00Z').valueOf())||
     new Date(date+'T12:00:00Z').toISOString().slice(0,10)!==date)
   throw Error('invalid_day');
  const resp=await fetch('/api/jra/official-pdf-links?date='+encodeURIComponent(date),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(seq!==officialPdfSeq||date!==$('autoDay').value)return;
  if(!resp.ok)throw Error('official_index_unavailable');
  const info=await resp.json();
  if(seq!==officialPdfSeq||date!==$('autoDay').value)return;
  if(!info||info.version!=='jra-official-pdf-link-discovery-1'||
     info.date!==date||info.indexUrl!=='https://www.jra.go.jp/keiba/rpdf/'||
     info.pdfContentsRead!==false||
     info.officialRunnerNumbersVerified!==false||
     info.entryChangeVerified!==false||
     info.predictionReady!==false||info.bettingReady!==false||
     !Array.isArray(info.links)||info.links.length>10||
     info.linkFound!==(info.links.length>0))
   throw Error('bad_jra_index');
  const courses=new Set(['札幌','函館','福島','新潟','東京','中山',
   '中京','京都','阪神','小倉']),seen=new Set(),validated=[];
  for(const row of info.links){
   if(!row||!courses.has(row.track)||seen.has(row.track)||
      typeof row.url!=='string'||row.url.length>350)
    throw Error('invalid_official_link');
   seen.add(row.track);
   const u=new URL(row.url);
   if(u.protocol!=='https:'||!['www.jra.go.jp','jra.jp'].includes(u.hostname)||
      u.port!==''||!u.pathname.startsWith('/keiba/rpdf/')||
      !u.pathname.toLowerCase().endsWith('.pdf')||u.search||u.hash||
      u.username||u.password)
    throw Error('invalid_official_url');
   validated.push(row);
  }
  jraPdfTracks=new Set(validated.map(x=>x.track));jraPdfChecked=true;
  updateJraCrosscheck();
  const links=$('autoOfficialPdfLinks');
  for(const item of validated){
   const a=dom('a',date+' '+item.track+'｜JRA公式出馬表PDFを開く');
   a.href=item.url;a.target='_blank';a.rel='noopener noreferrer';
   links.append(a);
  }
  $('autoOfficialPdfStatus').textContent=validated.length
   ?'JRA公式の出馬表PDFリンク '+validated.length+
    '競馬場分を確認。PDFの馬番・取消・馬場・発走時刻は自動照合していません。'
   :'PDFリンクはまだ検出できません。未掲載・掲載遅れ・形式変更などの可能性があり、開催なしとは判断しません。';
 }catch(_){if(seq===officialPdfSeq){
  $('autoOfficialPdfLinks').replaceChildren();
  jraPdfTracks=new Set();jraPdfChecked=false;updateJraCrosscheck();
  $('autoOfficialPdfStatus').textContent=
   'JRA公式PDFリンクを確認できませんでした。JRA公式一覧から手動で確認してください。';
 }}finally{if(seq===officialPdfSeq)button.disabled=false;}
};
// Owner opt-in link discovery from JRA's current public homepage.
// This is separate from the independent official four-way verification gate.
function resetResolvedJraCard(){
 $('autoOfficialCardLinkStatus').textContent='未検索。選択中のレースの公式リンクは未特定です。';
 const link=$('autoOfficialCardResolved');
 link.href='https://www.jra.go.jp/keiba/';
 link.textContent='JRA公式の出馬表一覧を開く（選択Rのリンクは未特定）';
}
$('autoOfficialCardDiscover').onclick=async()=>{
 const btn=$('autoOfficialCardDiscover');
 if(btn.disabled)return;
 const status=$('autoOfficialCardLinkStatus');
 const date=$('autoDay').value,key=$('autoRacePick').value;
 const day=date.replaceAll('-','');
 const current=latestDisplayedReport&&latestDisplayedDay===day&&
  latestDisplayedReport.races.find(r=>r.track+'|'+r.race===key);
 if(!current||!/^20\d{2}-\d{2}-\d{2}$/.test(date)){
  status.textContent='先に開催日のレースを1R選んでください。JRAの追加アクセスは0回。';
  return;
 }
 const track=current.track,race=current.race;
 resetResolvedJraCard();
 status.textContent=date+' '+track+' '+race+'R｜JRA公開出馬表リンクを検索中…';
 btn.disabled=true;
 try{
  const resp=await fetch('/api/jra/selected-race-card-link?date='+
   encodeURIComponent(date)+'&track='+encodeURIComponent(track)+
   '&race='+encodeURIComponent(String(race)),{
    credentials:'same-origin',cache:'no-store',
    headers:{'X-Keiba-Request':'private','Accept':'application/json'}
   });
  if(date!==$('autoDay').value||key!==$('autoRacePick').value||
     latestDisplayedDay!==day)return;
  if(!resp.ok)throw Error('official_link_not_found');
  const data=await resp.json();
  if(date!==$('autoDay').value||key!==$('autoRacePick').value||
     latestDisplayedDay!==day)return;
  if(!data||data.version!=='owner-jra-race-link-resolver-1'||
     data.date!==date||data.track!==track||data.race!==race||
     data.officialLinkFound!==true||
     data.officialLinkTargetVerified!==false||
     data.officialRacecardContentsVerified!==false||
     data.officialStartersVerified!==false||
     data.officialScratchesVerified!==false||
     data.officialGoingVerified!==false||
     data.officialPostTimeVerified!==false||
     data.formalTenFactorReady!==false||data.bettingReady!==false||
     data.researchOnly!==true||
     data.existingReceiptsChanged!==false||
     data.existingTicketsChanged!==false||data.newJrdbRequests!==0||
     typeof data.officialRacecardUrl!=='string'||
     data.officialRacecardUrl.length>250)
    throw Error('untrusted_jra_link');
  const u=new URL(data.officialRacecardUrl);
  const codes={札幌:'01',函館:'02',福島:'03',新潟:'04',東京:'05',
   中山:'06',中京:'07',京都:'08',阪神:'09',小倉:'10'};
  const token=u.searchParams.get('CNAME');
  const pattern=/^(?:sw|pw)01dd[de]01(\d{2})(\d{8})(\d{2})(\d{8})\/[a-f0-9]{2}$/i;
  const parsed=typeof token==='string'?pattern.exec(token):null;
  if(u.protocol!=='https:'||
     !['www.jra.go.jp','jra.jp','sp.jra.jp','app.jra.jp','own.jra.jp'].includes(u.hostname)||
     u.port!==''||u.username||u.password||u.hash||
     u.pathname!=='/JRADB/accessD.html'||
     [...u.searchParams.keys()].length!==1||!parsed||
     parsed[1]!==codes[track]||parsed[2].slice(0,4)!==date.slice(0,4)||
     parsed[3]!==String(race).padStart(2,'0')||
     parsed[4]!==day)
    throw Error('untrusted_jra_link_identity');
  const url=u.href;
  $('autoOfficialCardUrl').value=url;
  const link=$('autoOfficialCardResolved');
  link.href=url;link.textContent=date+' '+track+' '+race+'R｜JRA公式出馬表を開く';
  status.textContent='JRA公式サイト内の選択Rリンクを発見。リンク先の内容はまだ未照合。'+
   '続けて時刻・コース候補を比較します（追加JRDB 0回）。';
  // Explicit tap is the authority for BOTH public-only calls; the
  // following existing handler still checks exact day/venue/race and
  // does not mark JRA independently verified or write any tickets.
  await $('autoOfficialCardCheck').onclick();
 }catch(_){
  if(date===$('autoDay').value&&key===$('autoRacePick').value)
   status.textContent='選択RのJRA公式リンクを安全に特定できませんでした。'+
    '下のURL欄で手動照合するか、JRA公式出馬表で直接確認してください。'+
    '買い目は変更していません。';
 }finally{btn.disabled=false;}
};
// Explicit one-race JRA Web card candidate, never an official certification.
// No paid JRDB read, no rank or sealed receipt write. Only a user-selected URL.
$('autoOfficialCardCheck').onclick=async()=>{
 const button=$('autoOfficialCardCheck'),status=$('autoOfficialCardStatus');
 if(button.disabled)return;
 const date=$('autoDay').value,key=$('autoRacePick').value;
 const url=$('autoOfficialCardUrl').value.trim();
 const day=date.replaceAll('-','');
 const current=latestDisplayedReport&&latestDisplayedDay===day&&
  latestDisplayedReport.races.find(row=>row.track+'|'+row.race===key);
 if(!current||!/^20\d{2}-\d{2}-\d{2}$/.test(date)||
    typeof url!=='string'||url.length<50||url.length>250){
  status.textContent='先に開催日の予想から1Rを選び、JRA公式Web出馬表のURLを入力してください。';
  return;
 }
 const race=current.race,track=current.track;
 button.disabled=true;
 status.textContent=date+' '+track+' '+race+'R｜JRAの公開ページを確認中（買い目は変更なし）…';
 try{
  const requestUrl='/api/jra/prestart-card-candidate?date='+
   encodeURIComponent(date)+'&track='+encodeURIComponent(track)+
   '&race='+encodeURIComponent(String(race))+'&url='+encodeURIComponent(url);
  const response=await fetch(requestUrl,{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(date!==$('autoDay').value||key!==$('autoRacePick').value||
     latestDisplayedDay!==day)return;
  if(!response.ok)throw Error('official_header_unavailable');
  const info=await response.json();
  if(date!==$('autoDay').value||key!==$('autoRacePick').value||
     latestDisplayedDay!==day)return;
  if(!info||info.version!=='owner-jra-prestart-card-candidate-1'||
     info.date!==date||info.track!==track||info.race!==race||
     info.officialHostAllowlisted!==true||info.visibleRaceHeaderMatched!==true||
     info.pageContentsParsed!==true||info.researchOnly!==true||
     info.independentSourceAuthenticated!==false||
     info.officialStartersVerified!==false||
     info.officialScratchesVerified!==false||
     info.officialGoingVerified!==false||info.officialPostTimeVerified!==false||
     info.formalTenFactorReady!==false||info.bettingReady!==false||
     info.changesExistingReceipts!==false||info.changesExistingTickets!==false||
     info.newJrdbProviderRequests!==0||
     typeof info.postTimeCandidate!=='string'||
     !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(info.postTimeCandidate)||
     !['芝','ダート','障害'].includes(info.courseSurfaceCandidate)||
     !Number.isInteger(info.distanceMCandidate)||
     info.distanceMCandidate<600||info.distanceMCandidate>5000||
     (info.cancellationCueCandidate!==true&&
      info.cancellationCueCandidate!==null)||
     (info.horseNumbersCandidate!==undefined&&
      info.horseNumbersCandidate!==null&&
      (!Array.isArray(info.horseNumbersCandidate)||
       info.horseNumbersCandidate.length<2||
       info.horseNumbersCandidate.length>18||
       info.horseNumbersCandidate.some((n,i,a)=>
        !Number.isInteger(n)||n<1||n>18||(i>0&&n<=a[i-1]))))||
     (info.goingCandidate===null
      ? info.goingCandidatePresent!==false
      : (!['良','稍重','重','不良'].includes(info.goingCandidate)||
         info.goingCandidatePresent!==true)))
    throw Error('untrusted_jra_header');
  const ctx=latestDisplayedReport.raceContext.races.find(row=>
   row.track===track&&row.race===race);
  if(!ctx)throw Error('missing_local_race_context');
  const timeStatus=info.postTimeCandidate===current.postTime
   ?'発走時刻候補は一致':'発走時刻候補に差あり（要確認）';
  const courseStatus=ctx.surface===info.courseSurfaceCandidate&&
   ctx.distance_m===info.distanceMCandidate
   ?'コース条件候補は一致':'コース条件候補に差あり（要確認）';
  // Only a present, unambiguous display label can be compared. A
  // JRDB /tka outage or unknown going is NEVER treated as "良".
  const observed=info.goingCandidate!==null&&
   latestDisplayedReport.raceContext.conditionProviderFetchStatus==='received'&&
   ctx.goingAvailable===true&&ctx.conditionSnapshotPresent===true&&
   ctx.surface===info.courseSurfaceCandidate&&
   ['良','稍重','重','不良'].includes(ctx.going);
  const goingStatus=info.goingCandidate===null
   ?'JRAページの馬場状態候補なし（照合保留）'
   :!observed?'馬場状態候補あり・JRDB側未確認（照合保留）'
   :ctx.going===info.goingCandidate
    ?'馬場状態候補は一致（正式照合ではない）'
    :'馬場状態候補に差あり（要確認）';
  const visibleNumbers=Array.isArray(info.horseNumbersCandidate)
   ?info.horseNumbersCandidate:null;
  const providerNumbers=Array.isArray(current.runners)
   ?current.runners.map(h=>h.number):[];
  const numberStatus=visibleNumbers===null
   ?'馬番候補は不明（照合保留）'
   :!providerNumbers.length
    ?'JRA表示馬番候補 '+visibleNumbers.length+'頭／JRDB比較資料なし'
    :providerNumbers.length===visibleNumbers.length&&
      providerNumbers.every(n=>visibleNumbers.includes(n))
     ?'JRA表示馬番候補とJRDB受信馬番は一致（正式出走確定ではない）'
     :'【馬番差異】JRA表示馬番候補とJRDB受信馬番に差あり（要確認）';
  const cancellationStatus=info.cancellationCueCandidate===true
   ?'【取消注意】JRA出馬表の馬番欄に取消・除外の表示候補あり。必ず公式サイトで出走馬を再確認'
   :'取消の有無は未確認（表示が見つからなくても取消なしの証明ではない）';
  status.textContent=date+' '+track+' '+race+'R｜JRAページ候補：'+
   info.postTimeCandidate+'・'+info.courseSurfaceCandidate+
   info.distanceMCandidate+'m・'+(info.goingCandidate||'馬場不明')+
   '。'+timeStatus+'／'+courseStatus+'／'+goingStatus+'／'+
   numberStatus+'／'+cancellationStatus+
   '。正式な出走馬・取消・馬場・公式データの真正性と最新性は未照合。'+
   '既存の研究用下書きと固定買い目は変更しません。';
 }catch(_){
  if(date===$('autoDay').value&&key===$('autoRacePick').value)
   status.textContent=date+' '+track+' '+race+
    'R｜JRA公式ページの候補を照合できませんでした。JRA公式で直接確認してください。買い目は変更なし。';
 }finally{button.disabled=false;}
};
// A JRA public-result page is a CANDIDATE, not an attested finalized
// official settlement. A syntactically valid saved HMAC is also not proof
// of server verification. This preview never computes an official ROI,
// marks a losing ticket, issues a receipt or writes to localStorage.
function unverifiedJraResultComparison(info,date,track,race,day,verifiedReceipt){
 if(!info||info.version!=='owner-jra-public-result-probe-1'||
    info.date!==date||info.track!==track||info.race!==race||
    info.sourceHostAllowlisted!==true||
    info.visibleRaceIdentityMatched!==true||
    info.payoutLayoutParsed!==true||info.podiumChecked!==true||
    info.payoutMatchesDisplayedPodium!==true||
    info.officialJraVerified!==false||
    info.sourceAuthenticityAttested!==false||
    info.finalityVerified!==false||info.refundsVerified!==false||
    info.settlementReady!==false||info.officialRoiPercent!==null||
    info.actualPurchase!==false||info.researchOnly!==true||
    info.sourceReadCount!==0||info.changesExistingReceipts!==false||
    info.changesExistingRoi!==false||
    !Array.isArray(info.trifectaCandidates)||
    !Array.isArray(info.trioCandidates)||
    !info.trifectaCandidates.length||
    info.trifectaCandidates.length>18||info.trioCandidates.length>18)
  throw Error('untrusted_jra_result_candidate');
 for(const [mode,rows] of [['trifecta',info.trifectaCandidates],
                          ['trio',info.trioCandidates]]){
  const ids=new Set();
  for(const item of rows){
   if(!item||!Array.isArray(item.ticket)||item.ticket.length!==3||
      item.ticket.some(n=>!Number.isInteger(n)||n<1||n>18)||
      new Set(item.ticket).size!==3||
      !Number.isInteger(item.payoutYen)||item.payoutYen<100||
      item.payoutYen>1000000000)
    throw Error('invalid_result_payout_candidate');
   const key=(mode==='trio'?
    item.ticket.slice().sort((a,b)=>a-b):item.ticket).join('-');
   if(ids.has(key))throw Error('duplicate_result_candidate');
   ids.add(key);
  }
 }
 const raw=localStorage.getItem(RECEIPTS_KEY);
 if(raw){
  if(raw.length>650000)throw Error('oversized_fixed_history');
  validateStoredResearchLedger(JSON.parse(raw));
 }
 const selected=selectedReceiptsForVerification(day);
 const existing=selected.filter(x=>x.snapshot.track===track&&x.snapshot.race===race);
 if(existing.length>1)throw Error('duplicate_fixed_history');
 // The exact first-issued receipt was authenticated by our owner server
 // before the JRA request. A concurrent local edit or replacement must
 // NEVER inherit that verification or be compared as if it were signed.
 if(!verifiedReceipt||existing.length!==1||
    JSON.stringify(existing[0])!==JSON.stringify(verifiedReceipt))
  throw Error('verified_receipt_changed');
 const saved=existing[0]?.snapshot;
 if(!saved)return date+' '+track+' '+race+
  'R｜JRA表示の3連単払戻候補 '+info.trifectaCandidates.length+
  '通りを読取。発走前に固定した研究用3連単はこの端末にありません。'+
  'JRAの確定・返還・出典認証は未検証。仮想収支は未計算、購入記録は無変更。';
 if(!Number.isFinite(Date.parse(saved.scheduledOffAt))||
    new Date().getTime()<Date.parse(saved.scheduledOffAt))
  throw Error('race_has_not_started');
 const pay=new Map(info.trifectaCandidates.map(p=>[
  p.ticket.join('-'),p.payoutYen]));
 const matching=saved.trifectaTickets.filter(t=>pay.has(t.join('-')));
 const possibleYen=matching.reduce((sum,t)=>sum+pay.get(t.join('-')),0);
 if(!Number.isSafeInteger(possibleYen))throw Error('result_amount_invalid');
 const referenceStakeYen=saved.trifectaTickets.length*100;
 // Only show a candidate-page cash-flow ILLUSTRATION when at least one
 // fixed ticket matches. Missing payouts/refunds are NOT a confirmed loss.
 // No return is written to official ROI, saved receipts or purchase records.
 const scenario=matching.length?(()=>{
  const difference=possibleYen-referenceStakeYen;
  const percentage=Number((possibleYen/referenceStakeYen*100).toFixed(1));
  if(!Number.isFinite(percentage))throw Error('result_reference_roi_invalid');
  return '／未確定の候補だけで試算した参考差額 '+
   (difference>=0?'+':'')+difference.toLocaleString('ja-JP')+
   '円・参考回収率 '+percentage.toLocaleString('ja-JP')+
   '%（返還・結果変更は未反映）';
 })():'（一致候補なし。外れ・損失・回収率は未確定）';
 return date+' '+track+' '+race+'R｜最初の固定3連単 '+
  saved.trifectaTickets.length+'点（1点100円、仮の投資額 '+
  referenceStakeYen.toLocaleString('ja-JP')+'円）'+
  '／JRA表示の払戻候補と一致 '+matching.length+'点'+
  (matching.length?'／一致する払戻候補の合計 '+
   possibleYen.toLocaleString('ja-JP')+'円'+scenario:scenario)+
  '。固定買い目の署名は本人用サーバーで検証済み。'+
  'これはJRAの確定結果・返還・出典認証に基づく正式収支ではなく、'+
  '公式的中・損益・回収率の記録は未計算。'+
  '結果保存・実購入・既存記録の変更なし。';
}
// Read ONLY the immutable first-issued local receipts to fill the result
// comparison picker. This makes post-race review possible without a new
// licensed JRDB day read or a current-day prediction response.
function updateSavedResultRaceOptions(day){
 const select=$('autoResultSavedRace'),status=$('autoResultSavedRaceStatus');
 const previous=select.value;
 select.replaceChildren();
 select.value='';select.disabled=true;
 if(!/^20\d{6}$/.test(day)){
  status.textContent='開催日を選択してください。JRDB照会は行いません。';return;
 }
 try{
  const raw=localStorage.getItem(RECEIPTS_KEY);
  if(raw&&raw.length>650000)throw Error('oversized_fixed_ledger');
  if(raw)validateStoredResearchLedger(JSON.parse(raw));
  const saved=selectedReceiptsForVerification(day).map(r=>r.snapshot)
   .sort((a,b)=>a.track.localeCompare(b.track,'ja')||a.race-b.race);
  for(const s of saved){
   const option=dom('option',s.track+' '+s.race+'R｜固定3連単 '+
    s.trifectaTickets.length+'点');
   option.value=s.track+'|'+s.race;
   select.append(option);
  }
  if(saved.length){
   select.disabled=false;
   const ids=new Set(saved.map(r=>r.track+'|'+r.race));
   select.value=ids.has(previous)?previous:saved[0].track+'|'+saved[0].race;
  }
  status.textContent=saved.length
   ?'端末に保存された初回の固定買い目 '+saved.length+'Rから選択。'+
    '追加のJRDB通信0回・署名は未検証・正式結果は未確定。'
   :'この日の端末内固定買い目はありません。再取得せず、'+
    'Safari／ホーム画面の保存領域やバックアップを確認できます。';
 }catch(_){
  select.replaceChildren();select.value='';select.disabled=true;
  status.textContent='固定済み記録を安全に読み取れません。'+
   '買い目・収支は変更せず、バックアップと署名確認をお願いします。';
 }
}
function resetUnverifiedResultCandidate(){
 $('autoResultCandidateUrl').value='';
 $('autoResultCandidateStatus').textContent=
  '選択した固定済みRの結果候補は未確認。既存記録・収支は無変更です。';
}
$('autoResultSavedRace').onchange=()=>resetUnverifiedResultCandidate();
$('autoResultCandidateCheck').onclick=async()=>{
 const button=$('autoResultCandidateCheck');
 if(button.disabled)return;
 const status=$('autoResultCandidateStatus');
 const date=$('autoDay').value,key=$('autoResultSavedRace').value;
 const day=date.replaceAll('-',''),url=$('autoResultCandidateUrl').value.trim();
 if(!/^20\d{2}-\d{2}-\d{2}$/.test(date)||
    $('autoResultSavedRace').disabled||!key||
    url.length<50||url.length>500){
  status.textContent='先にこの日の端末内固定済みレースを選び、'+
   'JRA公式結果ページのURLを入力してください。';return;
 }
 // Never re-fetch a JRDB date to reconstruct an old race or a forecast.
 // Verify the exact first-issued local record and off-time BEFORE
 // any optional public JRA request. Server-side HMAC verification follows,
 // using this exact frozen receipt with no provider data re-fetch.
 let fixed,fixedReceipt;
 try{
  const raw=localStorage.getItem(RECEIPTS_KEY);
  if(raw&&raw.length>650000)throw Error('oversized_ledger');
  if(raw)validateStoredResearchLedger(JSON.parse(raw));
  const found=selectedReceiptsForVerification(day).filter(r=>
   r.snapshot.track+'|'+r.snapshot.race===key);
  if(found.length!==1)throw Error('saved_race_not_found');
  fixedReceipt=found[0];
  fixed=fixedReceipt.snapshot;
 }catch(_){
  status.textContent='このレースの固定済み記録を検証できません。'+
   '結果ページは読まず、保存内容は変更しません。';return;
 }
 const now=new Date().getTime();
 if(!Number.isFinite(now)||!Number.isFinite(Date.parse(fixed.scheduledOffAt))||
    now<Date.parse(fixed.scheduledOffAt)){
  status.textContent='暫定発走時刻より前です。結果候補は発走後のみ照合できます。';return;
 }
 const venue=fixed.track,race=fixed.race;
 button.disabled=true;
 status.textContent=date+' '+venue+' '+race+'R｜固定買い目の署名を本人サーバーで照合中…';
 try{
  const payload=JSON.stringify({date,receipts:[fixedReceipt]});
  if(payload.length>60000)throw Error('receipt_proof_too_large');
  const proof=await fetch('/api/owner-100yen-verify-receipts',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body:payload
  });
  if(date!==$('autoDay').value||key!==$('autoResultSavedRace').value||
     $('autoResultSavedRace').disabled)return;
  if(!proof.ok)throw Error('server_receipt_signature_invalid');
  const verified=await proof.json();
  if(date!==$('autoDay').value||key!==$('autoResultSavedRace').value||
     $('autoResultSavedRace').disabled)return;
  const review=verified?.review,rows=review?.races;
  if(verified?.available!==true||verified.serverSigned!==true||
     verified.captureAuditVerified!==false||
     verified.officialScheduleVerified!==false||
     verified.officialFeedConnected!==false||
     review?.version!=='keiba-100yen-review-1'||
     review.actualPurchase!==false||review.unitYen!==100||
     review.reviewedRaces!==0||review.pendingRaces!==1||
     review.totalInvestedYen!==0||review.totalReturnedYen!==0||
     review.roiPercent!==null||
     !Array.isArray(rows)||rows.length!==1||
     rows[0].date!==date||rows[0].track!==venue||
     rows[0].race!==race||rows[0].status!=='pending'||
     rows[0].trifectaPoints!==fixed.trifectaTickets.length||
     rows[0].trioPoints!==0||
     rows[0].investedYen!==null||rows[0].returnedYen!==null)
    throw Error('receipt_proof_contract');
  // A different local receipt, even if syntactically plausible, cannot
  // use the successful verification of the originally submitted bytes.
  const fresh=selectedReceiptsForVerification(day).filter(r=>
   r.snapshot.track+'|'+r.snapshot.race===key);
  if(fresh.length!==1||JSON.stringify(fresh[0])!==
     JSON.stringify(fixedReceipt))
    throw Error('receipt_changed_during_verification');
  status.textContent=date+' '+venue+' '+race+'R｜署名照合済。JRA結果候補を1回取得中…';
  const response=await fetch('/api/jra/result-candidate?date='+
   encodeURIComponent(date)+'&track='+encodeURIComponent(venue)+
   '&race='+encodeURIComponent(String(race))+'&url='+encodeURIComponent(url),{
    credentials:'same-origin',cache:'no-store',
    headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(date!==$('autoDay').value||key!==$('autoResultSavedRace').value||
     $('autoResultSavedRace').disabled)return;
  if(!response.ok)throw Error('result_candidate_unavailable');
  const candidate=await response.json();
  if(date!==$('autoDay').value||key!==$('autoResultSavedRace').value||
     $('autoResultSavedRace').disabled)return;
  status.textContent=unverifiedJraResultComparison(
   candidate,date,venue,race,day,fixedReceipt);
 }catch(_){
  if(date===$('autoDay').value&&key===$('autoResultSavedRace').value)
   status.textContent='固定記録の署名またはJRA結果候補を安全に照合できません。'+
    '公式サイトで直接確認してください。保存済みの買い目・仮想収支は変更していません。';
 }finally{button.disabled=false;}
};
// Owner-requested, configuration-only check. No paid provider reads.
$('autoPreflight').onclick=async()=>{
 const button=$('autoPreflight'),status=$('autoPreflightStatus');
 if(button.disabled)return;
 const seq=++preflightSeq,day=$('autoDay').value.replaceAll('-','');
 if(!/^20[0-9]{6}$/.test(day)){
  status.textContent='開催日を選択してください。';return;
 }
 button.disabled=true;
 status.textContent='設定の有無だけを確認中（JRDBへの有料照会なし）…';
 try{
  const resp=await fetch('/api/owner-saturday-preflight?date='+
   encodeURIComponent(day),{
    credentials:'same-origin',cache:'no-store',
    headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(!resp.ok)throw Error('preflight_http');
  const data=await resp.json();
  if(seq!==preflightSeq||day!==$('autoDay').value.replaceAll('-',''))return;
  const b=x=>typeof x==='boolean';
  const selectedDate=new Date(day.slice(0,4)+'-'+day.slice(4,6)+'-'+
    day.slice(6,8)+'T12:00:00Z');
  const expectedWeekend=[0,6].includes(selectedDate.getUTCDay());
  const thursday=new Date(selectedDate);
  thursday.setUTCDate(selectedDate.getUTCDate()+
   (selectedDate.getUTCDay()===0?-3:4-selectedDate.getUTCDay()));
  const thursdayDay=thursday.toISOString().slice(0,10).replaceAll('-','');
  const releasePending=expectedWeekend&&data.serverDate<thursdayDay;
  if(!data||data.version!=='owner-saturday-config-preflight-2'||
     data.date!==day||!/^20[0-9]{6}$/.test(data.serverDate)||
     !/^(?:[01][0-9]|2[0-3]):[0-5][0-9]$/.test(data.serverTimeJst)||
     data.serverTimeZone!=='Asia/Tokyo'||
     !b(data.privateServiceConfigured)||!b(data.jrdbCredentialsPresent)||
     !b(data.jrdbCredentialsFormatValid)||
     !b(data.approvedProviderHostConfigured)||!b(data.configurationReady)||
     data.configurationReady!==(data.privateServiceConfigured&&
      data.jrdbCredentialsPresent&&data.jrdbCredentialsFormatValid&&
      data.approvedProviderHostConfigured)||
     data.providerWeeklyUpdateMayBePending!==releasePending||
     data.providerPublicationVerified!==false||
     data.selectedDateAlreadyPast!==(day<data.serverDate)||
     data.selectedDateIsWeekend!==expectedWeekend||
     data.serverClockIndependentlyVerified!==false||
     data.providerConnectionVerified!==false||
     data.liveRaceFeedVerified!==false||
     data.officialJraVerified!==false||
     data.formalTenFactorsReady!==false||
     data.archivePersistenceVerified!==false||
     data.sourceCallsMade!==0||data.researchOnly!==true||
     data.privateOwnerOnly!==true||data.bettingReady!==false||
     data.existingReceiptsChanged!==false||
     data.existingRoiChanged!==false)
   throw Error('preflight_contract');
  const missing=[];
  if(!data.privateServiceConfigured)missing.push('本人専用サービス設定');
  if(!data.jrdbCredentialsPresent)missing.push('JRDBの認証設定');
  if(data.jrdbCredentialsPresent&&!data.jrdbCredentialsFormatValid)
   missing.push('JRDBキーの通信可能な文字形式');
  if(!data.approvedProviderHostConfigured)missing.push('許可されたAPI接続先');
  status.textContent=(data.configurationReady
   ?'本人専用・JRDB認証・接続先の設定項目は揃っています。'
   :'設定不足：'+missing.join('・')+'。')+
   (data.selectedDateAlreadyPast?'指定日は過去日付です。':
    data.selectedDateIsWeekend?'選択日は土日です。':
    '土日以外の開催はJRA公式の開催有無を別途確認。')+
   (data.providerWeeklyUpdateMayBePending
    ?'JRDBの今週データは通常木曜の更新後に配信。対象週はまだ木曜前なので未配信の可能性があります。'
    :'JRDBの実際の配信開始はまだ確認していません。')+
   'サーバー日本時間 '+data.serverDate+' '+data.serverTimeJst+
   '。有料照会0回。JRDB実データ接続・当日番組・JRA公式・10項目の本採点・サーバー永続保存は未確認。';
 }catch(_){if(seq===preflightSeq)
  status.textContent='無料事前診断を完了できませんでした。'+
   'JRDBの有料照会や買い目の保存は行っていません。';
 }finally{if(seq===preflightSeq)button.disabled=false;}
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
 $('autoOfficialCardStatus').textContent='JRDB再分析後はJRA出馬表の候補をもう一度確認してください。';
 const button=$('autoRun');
 if(button.disabled)return;
 const seq=++request,day=$('autoDay').value.replaceAll('-','');
 resetAdvanceProgramme();
 latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;clearAutomaticOffTimer();
 latestReadAtMs=0;showSnapshotFreshness();
 clearDraftShortcut();
 if(!/^20[0-9]{6}$/.test(day)){
  $('autoStatus').textContent='開催日を選択してください。';return;
 }
 button.disabled=true;$('autoStatus').textContent='JRDB資料を一括照合し、自動暫定案を作成中…';
 $('autoEasyPulse').textContent='開催日を取得中。新しい買い目はまだ未確認です。';
 $('autoRaceQuickSummary').textContent='データ確認中。まだ予想は表示していません。';
 $('autoOperationalNext').textContent='JRDB取得・資料検証中。新しい研究用下書きの確認は完了していません。';
 $('autoReadProof').textContent='JRDB資料を照会中。番組R数・4ソース完了・署名はまだ未確認。';
 clearHistory();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
 $('autoMissingFactorSummary').textContent='開催日を取得すると未評価の内訳を確認できます。';
 $('autoMissingFactorRaces').replaceChildren();
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 try{
  let result;
  try{
   result=await fetch('/api/jrdb/owner-auto-draft?date='+encodeURIComponent(day),{
    credentials:'same-origin',cache:'no-store',
    headers:{'X-Keiba-Request':'private','Accept':'application/json'}
   });
  }catch(_){
   // Network disconnects, iPhone suspend, and Render ingress failures
   // are NOT JRDB provider errors. Never echo an untrusted exception,
   // retry a potentially paid call, or create an unsigned formation.
   throw Error('owner_network_failure');
  }
  // Render may return a plain-text/HTML gateway failure rather than our
  // private service's structured JSON. Never render an untrusted body,
  // silently retry a potentially billed call, or show a new formation.
  let body;
  try{body=await result.json();}
  catch(_){
   if(!result.ok&&[502,503,504].includes(result.status))
    throw Error('render_gateway_nonjson');
   throw Error('unverified_server_response');
  }
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
  // Validate the whole source snapshot BEFORE writing any signed record.
  // A new formation must never become visible before the browser has
  // accepted its immutable prestart receipt (or safely returned no drafts).
  validate(body,day);
  let localStatus;
  try{
   localStatus=saveAutoReceipts(body,day);
  }catch(_){
   throw Error('receipt_storage_failed');
  }
  // Optional frozen index evidence is stored separately from signed
  // 3連単, never overwrites the first existing research record, and
  // failure cannot invalidate already safe prestart bet receipt storage.
  try{saveWorkoutLocks(body,day);}
  catch(_){
   $('autoWorkoutLockStatus').textContent=
    '調教指数の初回固定に失敗。既存の研究予想・購入記録は変更していません。';
   $('autoWorkoutProviderCheck').disabled=true;
  }
  const displayed=render(body,day);
  // Keep only a tiny, non-sensitive 0R read marker between Safari
  // navigation/reloads. This is NOT a cached forecast or provider response.
  // Failed/partial responses and signatures never create this marker.
  if(body.raceCount===0)recordWeekendEmptyRead(day);
  else clearWeekendEmptyRead();
  recordWeekendFixedRead(day,body);
  latestDisplayedReport=body;latestDisplayedDay=day;
  latestReadAtMs=new Date().valueOf();showSnapshotFreshness();
  latestExpiredDraftCount=body.races.filter(x=>
   x.status==='provisional_draft'&&draftExpiredOnDevice(day,x.postTime)).length;
  armAutomaticOffTimer(body,day);
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
  $('autoFiveQuick').disabled=historyCoordinates.size===0;
  $('autoMainWorkoutCheck').disabled=historyCoordinates.size===0;
  $('autoTcyTchCompare').disabled=historyCoordinates.size===0;
  $('autoFiveQuickStatus').textContent=historyCoordinates.size
   ?'追加5項目の過去比較は未実行。上のボタンで最大16回照会します。'
   :'JRDB番組が0Rのため5項目の追加照会は不要です。';
  renderFiveQuickSaved(day);
  $('autoHistoryAuditStatus').textContent=historyCoordinates.size
   ?'必要なときに過去の同条件資料を確認できます。':'この開催日のレースはありません。';
  // render already calculated *visible* new picks, including first-write
  // conflicts and elapsed offs. Do not overwrite with raw draftCount.
  $('autoSavedStatus').textContent=body.archiveEnabled
   ?'サーバー固定済み '+body.archiveRecordCount+'R／前の買い目を優先したレース '+
     body.archiveConflictCount+'R。'+localStatus
   :'サーバー保存は未設定。'+localStatus;
  showFixedHistory(day);
  renderFixedQuick(day,displayed.visibleCount===0);
  $('autoRecordSafety').textContent=recordRetentionStatus(body,day);
  // A valid HTTP response is NOT proof of a successful forecast.
  // In particular /tra=0 only means the provider returned no programme;
  // all held/expired drafts must not look like generated picks on iPhone.
  const visibleDrafts=displayed.visibleCount;
  if(body.raceCount===0){
   const ahead=day>jstToday().replaceAll('-','');
   $('autoStatus').textContent=
    '【番組0R・予想未作成】JRDB番組の取得結果は0件。'+
    (ahead?'開催日前のため未配信の可能性があります。':
     '資料の配信前・取得不備・実際の開催なしは区別できません。')+
    '開催なしと断定せず、JRA公式の開催情報を確認してください。';
  }else if(body.draftCount===0){
   $('autoStatus').textContent='【全'+body.raceCount+
    'R見送り・新規3連単0点】調教・近走や発走時刻などの条件が揃わず、研究用の買い目は作成していません。';
  }else if(visibleDrafts===0&&displayed.blockedCount){
   $('autoStatus').textContent='【固定記録の確認が必要・新案非表示】'+
    '再分析と以前の固定買い目が一致しない、または保存確認が必要なため、新しい3連単は表示していません。'+
    '発走前に固定した最初の買い目を下の履歴で確認してください。';
  }else if(visibleDrafts===0){
   $('autoStatus').textContent='【発走時刻経過・新案非表示】'+
    '今回の研究用下書きは端末で確認した時点で暫定発走時刻を過ぎています。新規固定・表示はしていません。';
  }else{
   $('autoStatus').textContent='発走前の研究用暫定案 '+visibleDrafts+
    'Rを確認。正式10項目の予想・JRA公式照合は未完了です。';
  }
  // Optional paid history is only allowed AFTER the base-day response
  // and all local receipt checks finished without throwing.
  if(seq===request&&day===$('autoDay').value.replaceAll('-','')){
   maybeAutoFiveFromBasic(body,day);
   // A single FREE JRA calendar probe follows the explicit successful day
   // read and receipt validation. Never repeat a paid provider read or
   // block research forecasts when JRA's public site is unavailable.
   // Advance programme differences are NOT final JRA racecard verification.
   // The public JRA calendar adapter only supports official 2020-2035\n   // pages. Do not auto-probe synthetic/far-future test dates.\n   const jraCalendarYear=Number(day.slice(0,4));\n   if(body.raceCount>0&&jraCalendarYear>=2020&&jraCalendarYear<=2035)\n    void $('autoAdvanceCompare').onclick();
  }
 }catch(error){if(seq===request){
  latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;clearAutomaticOffTimer();
 latestReadAtMs=0;showSnapshotFreshness();
 clearDraftShortcut();
  const storageFailure=error?.message==='receipt_storage_failed';
  const gatewayFailure=error?.message==='render_gateway_nonjson';
  const networkFailure=error?.message==='owner_network_failure';
  const badResponse=error?.message==='unverified_server_response';
  const detail=error&&typeof error.message==='string'&&
   error.message.startsWith('停止した工程：')?error.message:null;
  $('autoStatus').textContent=storageFailure
   ?'【端末保存失敗】新しい3連単は表示していません。既存の固定履歴を確認し、端末の空き容量・バックアップを確認してください。'
   :networkFailure
   ?'【通信エラー】本人用サーバーから応答を受信できません。新しい買い目は非表示。自動で有料JRDB照会をやり直しません。接続状態を確認してください。'
   :gatewayFailure
   ?'【Render応答エラー（502/503/504）】サーバーの応答が確認できません。新しい買い目は非表示。自動再取得はしません。時間を空けて状態を確認してください。'
   :badResponse
   ?'【応答形式未確認】サーバーから安全なJSONを受信できず、新しい買い目は非表示です。自動再取得はしません。'
   :detail||
   '安全な自動生成ができません。JRDB接続・出走資料・認証状態を確認してください。';
  $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
  $('autoEasyPulse').textContent='取得に失敗。新しい研究用予想は確認できません。上のエラーを確認してください。';
  // The separate private pre-day page is not a JRDB API retry or a formal
  // prediction. Its link remains visible if an API call fails with 403.
  $('autoPredayRecovery').textContent='登録済みの前日参考予想を見る（JRDB APIへの追加照会なし）';
  $('autoRaceQuickSummary').textContent='予想は未取得です。以前の固定記録はそのままです。';
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
 $('autoMissingFactorSummary').textContent='開催日を取得すると未評価の内訳を確認できます。';
 $('autoMissingFactorRaces').replaceChildren();
  $('autoRacePick').disabled=true;
  $('autoRacePick').replaceChildren();
  $('autoRacePick').value='';
  $('autoViewingStatus').textContent='この日の新しい下書きは確認できません。固定履歴は下で確認できます。';
  $('autoSummary').textContent=storageFailure
   ?'新しい下書きは保存できなかったため非表示':'予想は未作成';
  $('autoSavedStatus').textContent=storageFailure
   ?'研究記録の端末保存はできませんでした。以前の固定記録は変更していません。'
   :'再分析に失敗。'+localReceiptStatus(day);
  showFixedHistory(day);
  renderFixedQuick(day,true);
  $('autoFixedConsistency').textContent=storageFailure
   ?'【保存記録の確認が必要】端末への新規固定に失敗したため、新しい買い目は表示していません。以前の固定済み研究記録は変更していません。'
   :'今回の再分析結果は未確認です。以前の固定済み研究記録は変更していません。';
  $('autoMorningStatus').textContent=storageFailure
   ?'JRDBの暫定案を取得しましたが、端末への新規固定保存に失敗。新しい3連単は非表示。以前の固定記録は変更していません。'
   :'JRDB資料を安全に取得できず、新しい暫定予想は表示していません。以前の固定済み研究記録は変更していません。';
  $('autoHoldBreakdown').textContent='取得・保存に失敗したため、見送り内訳は確認できません。以前の固定記録は変更していません。';
  $('autoOperationalNext').textContent=storageFailure
   ?'【端末保存失敗・新規下書きなし】既存の固定履歴を先に確認して、同じiPhoneのバックアップを安全に保管してください。保存できる状態になってから発走前に再取得してください。'
   :networkFailure
   ?'【通信切断・新規予想なし】端末の回線とRenderの稼働を確認。保存済み固定履歴はそのままです。処理の成否が不明な間、追加の有料JRDB照会を連打しないでください。'
   :gatewayFailure
   ?'【Renderの状態確認】502/503/504はネットワークや実行環境の問題でも発生します。既存の固定履歴を確認し、Renderの稼働状況・非公開の処理ログを確認してください。原因が分かるまで追加の有料JRDB照会を連打しないでください。'
   :'【取得失敗・新規予想なし】上の停止工程と401/403/429等の原因表示を確認。登録済みの前日参考予想は上部の別画面ボタンから閲覧できます（別経路・公式未照合）。既存の固定履歴も維持され、正式100点予想は未完成です。';
  $('autoProgrammeCoverage').textContent='取得失敗：開催場別R数は確認できません。';
  $('autoReadProof').textContent='【照会失敗】番組・出走馬・調教・近走の取得完了は未確認。新規予想・署名を確認できません。';
  $('autoRecordSafety').textContent=storageFailure
   ?'【端末への新規固定失敗】新しい買い目は非表示。既存の固定記録は削除・上書きしていません。バックアップ・署名確認を優先してください。'
   :'新規記録なし。以前の固定記録は下の履歴で確認してください（署名は別操作）。';
  $('autoSourceSummary').textContent='資料進捗の取得に失敗しました。以前の集計は表示しません。';
  $('autoTrackWorkouts').textContent='取得失敗：調教S/Aの新しい参考表示はありません。';
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
  if(seq!==receiptVerifySeq||day!==$('autoDay').value.replaceAll('-',''))return;
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
// Read-only archive recovery view. The authenticated server verifies
// signatures, and this browser NEVER writes the returned tickets to storage.
$('autoArchiveRead').onclick=async()=>{
 const button=$('autoArchiveRead'),selected=$('autoDay').value;
 if(button.disabled)return;
 const day=selected.replaceAll('-','');
 const seq=++archiveReadSeq;
 button.disabled=true;
 $('autoArchiveRaces').replaceChildren();
 $('autoArchiveStatus').textContent='サーバー保存の状態を確認中…';
 try{
  if(!/^20[0-9]{2}-[0-9]{2}-[0-9]{2}$/.test(selected)||
     Number.isNaN(new Date(selected+'T12:00:00Z').valueOf())||
     new Date(selected+'T12:00:00Z').toISOString().slice(0,10)!==selected)
   throw Error('invalid_day');
  const response=await fetch('/api/owner-archive-read?date='+encodeURIComponent(selected),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const data=await response.json();
  if(seq!==archiveReadSeq||selected!==$('autoDay').value)return;
  if(!response.ok||!data||
     typeof data.archiveEnabled!=='boolean'||
     typeof data.persistentStorageReady!=='boolean'||
     typeof data.available!=='boolean'||
     data.actualPurchase!==false||
     data.officialScheduleVerified!==false||
     data.captureAuditVerified!==false||
     data.officialFeedConnected!==false||
     !Number.isInteger(data.raceCount)||
     data.raceCount<0||data.raceCount>36||
     !Array.isArray(data.receipts)||data.receipts.length!==data.raceCount)
   throw Error('bad_archive_response');
  if(!data.archiveEnabled){
   if(data.persistentStorageReady!==false||data.available!==false||
      data.raceCount!==0)
    throw Error('inconsistent_disabled_archive');
   $('autoArchiveStatus').textContent=
    'サーバーへの永続保存は未設定です。iPhoneの固定記録は変更せず、バックアップをご利用ください。';
   return;
  }
  if(!data.persistentStorageReady||data.available!==(data.raceCount>0))
   throw Error('inconsistent_enabled_archive');
  const ids=new Set(),tracks=new Set(['札幌','函館','福島','新潟','東京',
   '中山','中京','京都','阪神','小倉']),cards=[];
  for(const entry of data.receipts){
   const p=entry?.snapshot;
   if(!p||Object.keys(entry).sort().join(',')!=='signature,snapshot'||
      typeof entry.signature!=='string'||!/^[0-9a-f]{64}$/.test(entry.signature)||
      p.date!==selected||!tracks.has(p.track)||
      !Number.isInteger(p.race)||p.race<1||p.race>12||
      ids.has(p.track+'|'+p.race)||
      p.sourceKind!=='prestart-locked'||p.actualPurchase!==false||
      p.scheduleVerified!==false||p.predictionVerified!==false||
      typeof p.lockedAt!=='string'||typeof p.scheduledOffAt!=='string'||
      !Number.isFinite(Date.parse(p.lockedAt))||
      !Number.isFinite(Date.parse(p.scheduledOffAt))||
      Date.parse(p.lockedAt)>=Date.parse(p.scheduledOffAt)||
      !Array.isArray(p.trifectaTickets)||p.trifectaTickets.length<1||
      p.trifectaTickets.length>48||
      !Array.isArray(p.trioTickets)||p.trioTickets.length!==0)
    throw Error('invalid_archive_receipt');
   const unique=new Set();
   for(const ticket of p.trifectaTickets){
    if(!Array.isArray(ticket)||ticket.length!==3||
       ticket.some(n=>!Number.isInteger(n)||n<1||n>18)||
       new Set(ticket).size!==3||unique.has(ticket.join('-')))
     throw Error('invalid_archive_ticket');
    unique.add(ticket.join('-'));
   }
   ids.add(p.track+'|'+p.race);
   const card=dom('details'),count=p.trifectaTickets.length;
   card.append(dom('summary',p.track+' '+p.race+'R｜固定済み3連単 '+count+'点'),
    dom('p','サーバー保存済みの発走前研究記録。固定日時 '+p.lockedAt+
     '／暫定発走 '+p.scheduledOffAt,'muted'),
    dom('p',p.trifectaTickets.map(t=>t.join('→')).join(' / '),'ticket-list'));
   cards.push(card);
  }
  // No partial displays if any row has an invalid identity or timestamp.
  $('autoArchiveRaces').replaceChildren(...cards);
  $('autoArchiveStatus').textContent=data.raceCount
   ?'サーバー保存済みの研究記録 '+data.raceCount+
    'Rを確認。本人用サーバーの署名チェック済み。JRA公式・実購入・結果・回収率は未確認。iPhoneには書き戻していません。'
   :'この開催日のサーバー保存済みの研究記録はありません。新しい予想は作りません。';
 }catch(_){if(seq===archiveReadSeq){
  $('autoArchiveRaces').replaceChildren();
  $('autoArchiveStatus').textContent=
   'サーバー保存済みの記録を安全に確認できません。設定・接続を確認してください。iPhone内の記録は無変更です。';
 }}finally{if(seq===archiveReadSeq)button.disabled=false;}
};
function verifyCoreProviderReport(result,receipts,day){
 const weights={training:30,course_distance:20,pace:20},
       tally=Object.fromEntries(Object.keys(weights).map(k=>[
        k,{S:0,A:0,B:0,C:0}
       ]));
 if(!result||result.version!=='owner-three-core-provider-observation-1'||
    result.date!==day||
    result.sourceKind!=='jrdb-tse-unverified-podium-observation'||
    !Number.isInteger(result.providerSourceReadCount)||
    ![0,1].includes(result.providerSourceReadCount)||
    result.raceCount!==receipts.length||
    !Array.isArray(result.races)||result.races.length!==receipts.length||
    !Number.isInteger(result.observedRaceCount)||
    !Number.isInteger(result.observedStudiedWinnerCount)||
    result.observedStudiedWinnerCount>result.observedRaceCount||
    result.verifiedRaceCount!==0||result.confirmedHitCount!==null||
    result.officialJraVerified!==false||
    result.jraIndependentConfirmation!==false||
    result.officialFeedConnected!==false||
    result.outcomeCalibrationReady!==false||
    result.modelAccuracyPercent!==null||
    result.bettingReady!==false||result.actualPurchase!==false||
    result.payoutVerified!==false||result.roiPercent!==null||
    result.historicalBandsNotCalibrated!==true||
    result.sourceIncompleteCouldChange!==true||
    result.researchOnly!==true||result.privateOwnerOnly!==true||
    !result.winnerBandCounts||
    Object.keys(result.winnerBandCounts).sort().join(',')!==
     Object.keys(weights).sort().join(','))
  throw Error('不正な研究成績の応答');
 const originals=new Map(receipts.map(item=>[
  item.snapshot.track+'|'+item.snapshot.race,item.snapshot
 ])),seen=new Set();
 let observed=0,scored=0;
 const out=[];
 for(const row of result.races){
  const id=row?.track+'|'+row?.race,original=originals.get(id);
  if(!original||seen.has(id)||row.scoredRunnerCount!==original.horses.length||
     !['pending','podium_observed'].includes(row.providerStatus)||
     row.officialVerified!==false||row.predictionHitVerified!==null)
   throw Error('70点研究のレース照合に不一致');
  seen.add(id);
  if(row.providerStatus==='pending'){
   if(row.observedPodiumNumbers!==null||row.studiedWinnerObserved!==null||
      row.winnerStudyScore70!==null||row.winnerStudyBands!==null)
    throw Error('保留成績に不要な情報');
   out.push({row,original});continue;
  }
  observed++;
  if(result.providerSourceReadCount!==1||
     !Array.isArray(row.observedPodiumNumbers)||
     row.observedPodiumNumbers.length!==3||
     row.observedPodiumNumbers.some(n=>!Number.isInteger(n)||n<1||n>18)||
     new Set(row.observedPodiumNumbers).size!==3||
     typeof row.studiedWinnerObserved!=='boolean')
   throw Error('暫定3着内の形式が不正');
  const winner=original.horses.find(
   h=>h.number===row.observedPodiumNumbers[0]);
  if(row.studiedWinnerObserved!==Boolean(winner))
   throw Error('固定研究値と勝ち馬番の照合失敗');
  if(winner){
   scored++;
   if(!row.winnerStudyBands||
      Object.keys(row.winnerStudyBands).sort().join(',')!==
       Object.keys(weights).sort().join(',')||
      Object.keys(weights).some(k=>row.winnerStudyBands[k]!==winner.bands[k])||
      row.winnerStudyScore70!==
       Math.round(winner.rawThirdPoints*100/3)/100)
    throw Error('固定70点とサーバーの仮値が違います');
   for(const k of Object.keys(weights))tally[k][winner.bands[k]]++;
  }else if(row.winnerStudyScore70!==null||
           row.winnerStudyBands!==null){
   throw Error('未評価の馬に架空の点数を付与');
  }
  out.push({row,original});
 }
 if(seen.size!==receipts.length||
    observed!==result.observedRaceCount||
    scored!==result.observedStudiedWinnerCount)
  throw Error('重点3項目の暫定集計に不一致');
 for(const k of Object.keys(weights)){
  if(Object.keys(result.winnerBandCounts[k]||{}).sort().join(',')!=='A,B,C,S'||
     Object.keys(tally[k]).some(label=>
      result.winnerBandCounts[k][label]!==tally[k][label]))
   throw Error('暫定集計が元の固定値と不一致');
 }
 return out;
}
function verifyFiveProviderReport(result,receipts,day){
 const keys=['training','course_distance','pace','ground','recent'],
  bands=['S','A','B','C'],tally=Object.fromEntries(keys.map(k=>[
   k,Object.fromEntries(bands.map(b=>[b,0]))])),
  exposure=Object.fromEntries(keys.map(k=>[
   k,Object.fromEntries(bands.map(b=>[b,0]))]));
 if(!result||result.version!=='owner-five-core-provider-observation-1'||
    result.date!==day||
    result.sourceKind!=='jrdb-tse-unverified-five-core-observation'||
    ![0,1].includes(result.providerSourceReadCount)||
    !Number.isInteger(result.providerSourceReadCount)||
    result.raceCount!==receipts.length||
    !Array.isArray(result.races)||result.races.length!==receipts.length||
    !Number.isInteger(result.observedRaceCount)||
    !Number.isInteger(result.observedStudiedWinnerCount)||
    !Number.isInteger(result.observedStudiedRunnerCount)||
    result.observedStudiedRunnerCount<0||
    result.observedStudiedWinnerCount>result.observedRaceCount||
    result.observedStudiedWinnerCount>result.observedStudiedRunnerCount||
    result.verifiedRaceCount!==0||result.confirmedHitCount!==null||
    result.officialJraVerified!==false||
    result.jraIndependentConfirmation!==false||
    result.officialFeedConnected!==false||
    result.outcomeCalibrationReady!==false||
    result.modelAccuracyPercent!==null||result.roiPercent!==null||
    result.bettingReady!==false||result.actualPurchase!==false||
    result.payoutVerified!==false||
    result.historicalBandsNotCalibrated!==true||
    result.sourceIncompleteCouldChange!==true||
    result.researchOnly!==true||result.privateOwnerOnly!==true||
    !result.winnerBandCounts||!result.observedResearchBandExposureCounts||
    Object.keys(result.winnerBandCounts).sort().join(',')!==
     keys.slice().sort().join(',')||
    Object.keys(result.observedResearchBandExposureCounts).sort().join(',')!==
     keys.slice().sort().join(','))
  throw Error('85点の暫定研究応答が不正');
 const originals=new Map(receipts.map(x=>[
  x.snapshot.track+'|'+x.snapshot.race,x.snapshot
 ])),seen=new Set(),verified=[];
 let observed=0,studied=0,eligible=0;
 for(const row of result.races){
  const id=row?.track+'|'+row?.race,p=originals.get(id);
  if(!p||seen.has(id)||row.scoredRunnerCount!==p.horses.length||
     !['pending','podium_observed'].includes(row.providerStatus)||
     row.officialVerified!==false||row.predictionHitVerified!==null)
   throw Error('85点研究のレース照合不一致');
  seen.add(id);
  if(row.providerStatus==='pending'){
   if(row.observedPodiumNumbers!==null||row.studiedWinnerObserved!==null||
      row.winnerStudyScore85!==null||row.winnerStudyBands!==null)
    throw Error('未確定結果に研究点数が混在');
   verified.push(row);continue;
  }
  if(result.providerSourceReadCount!==1||
     !Array.isArray(row.observedPodiumNumbers)||
     row.observedPodiumNumbers.length!==3||
     row.observedPodiumNumbers.some(n=>!Number.isInteger(n)||n<1||n>18)||
     new Set(row.observedPodiumNumbers).size!==3||
     typeof row.studiedWinnerObserved!=='boolean')
   throw Error('85点の暫定着順が不正');
  observed++;
  eligible+=p.horses.length;
  for(const horse of p.horses)
   for(const k of keys)exposure[k][horse.bands[k]]++;
  const winner=p.horses.find(x=>x.number===row.observedPodiumNumbers[0]);
  if(row.studiedWinnerObserved!==Boolean(winner))
   throw Error('85点の固定馬番と結果が不一致');
  if(winner){
   studied++;
   if(!row.winnerStudyBands||
      Object.keys(row.winnerStudyBands).sort().join(',')!==
      keys.slice().sort().join(',')||
      keys.some(k=>winner.bands[k]!==row.winnerStudyBands[k])||
      row.winnerStudyScore85!==Math.round(winner.rawThirdPoints*100/3)/100)
    throw Error('85点固定値の再計算が不一致');
   for(const k of keys)tally[k][winner.bands[k]]++;
  }else if(row.winnerStudyScore85!==null||row.winnerStudyBands!==null){
   throw Error('未評価馬に点数を追加');
  }
  verified.push(row);
 }
 if(seen.size!==receipts.length||observed!==result.observedRaceCount||
    studied!==result.observedStudiedWinnerCount||
    eligible!==result.observedStudiedRunnerCount)
  throw Error('85点暫定集計が不一致');
 for(const k of keys){
  if(Object.keys(result.winnerBandCounts[k]||{}).sort().join(',')!=='A,B,C,S'||
     Object.keys(result.observedResearchBandExposureCounts[k]||{}).sort().join(',')!=='A,B,C,S'||
     bands.some(b=>result.winnerBandCounts[k][b]!==tally[k][b]||
      result.observedResearchBandExposureCounts[k][b]!==exposure[k][b]||
      tally[k][b]>exposure[k][b]))
   throw Error('85点項目別研究母数・暫定勝ち馬の集計不一致');
 }
 return {rows:verified,exposure,tally};
}
function validateWorkoutProviderComparison(value,receipts,day){
 if(!value||value.version!=='owner-workout-order-provider-pairs-1'||
    value.date!==day||value.sourceKind!=='jrdb-tse-provisional-workout-order-pair-review'||
    value.researchOnly!==true||value.privateOwnerOnly!==true||
    value.officialJraVerified!==false||value.accuracyVerified!==false||
    value.calibrationReady!==false||value.scoreReady!==false||
    value.newScoringRubric!==false||value.bettingReady!==false||
    value.predictionReady!==false||value.actualPurchase!==false||
    value.roiPercent!==null||value.payoutVerified!==false||
    value.crossBandHypothesisOnly!==true||
    value.crossBandResultsSigned!==false||
    value.sourceReadsForCrossBand!==0||
    ![0,1].includes(value.sourceReadCount)||
    !Array.isArray(value.races)||value.raceCount!==receipts.length||
    value.races.length!==receipts.length||
    !Number.isInteger(value.studiedRaceCount)||
    value.studiedRaceCount<0||value.studiedRaceCount>receipts.length)
  throw Error('調教比較のレスポンス形式不一致');
 const bands=['S','A','B','C'];
 const expected=new Map(receipts.map(entry=>{
  const p=validateWorkoutLockReceipt(entry);
  return [p.track+'|'+p.race,p];
 }));
 const totals=Object.fromEntries(bands.map(b=>
  [b,{concordant:0,discordant:0,equalIndexExcluded:0}]));
 const keys=['S>A','S>B','S>C','A>B','A>C','B>C'];
 const crossTotals=Object.fromEntries(keys.map(k=>[
   k,{concordant:0,discordant:0}
 ]));
 const rows=[],used=new Set();
 let studied=0;
 for(const row of value.races){
  const id=row?.track+'|'+row?.race,p=expected.get(id);
  if(!p||used.has(id)||row.officialJraVerified!==false||
     row.predictionVerified!==false||
     !['pending','complete_provisional_order'].includes(row.providerStatus))
   throw Error('調教比較の競馬場R不一致');
  used.add(id);
  const complete=row.providerStatus==='complete_provisional_order';
  if(complete){
   studied++;
   if(row.comparedRunnerCount!==p.raceRunnerCount||
      !row.pairCounts||Object.keys(row.pairCounts).sort().join(',')!=='A,B,C,S')
    throw Error('比較人数の不一致');
   if(!row.crossBandPairs||
      Object.keys(row.crossBandPairs).sort().join(',')!==
       keys.slice().sort().join(','))
    throw Error('異なる調教ランク間の比較形式が不正');
   for(const k of keys){
    const pair=row.crossBandPairs[k],labels=k.split('>');
    if(!pair||Object.keys(pair).sort().join(',')!=='concordant,discordant'||
       !Number.isInteger(pair.concordant)||
       !Number.isInteger(pair.discordant)||
       pair.concordant<0||pair.discordant<0)
     throw Error('調教ランク間の比較数が不正');
    const expectedPairs=p.horses.filter(h=>h.trainingBand===labels[0]).length*
      p.horses.filter(h=>h.trainingBand===labels[1]).length;
    if(pair.concordant+pair.discordant!==expectedPairs)
     throw Error('調教ランク間の比較母数が不一致');
    crossTotals[k].concordant+=pair.concordant;
    crossTotals[k].discordant+=pair.discordant;
   }
   for(const b of bands){
    const pairs=row.pairCounts[b];
    if(!pairs||Object.keys(pairs).sort().join(',')!==
       'concordant,discordant,equalIndexExcluded')throw Error('比較項目形式');
    for(const k of ['concordant','discordant','equalIndexExcluded'])
     if(!Number.isInteger(pairs[k])||pairs[k]<0||pairs[k]>153)
      throw Error('比較件数');
    const members=p.horses.filter(h=>h.trainingBand===b);
    const total=members.length*(members.length-1)/2;
    let equal=0;
    for(let i=0;i<members.length;i++)
     for(let j=i+1;j<members.length;j++)
      if(members[i].withinBandRank===members[j].withinBandRank)equal++;
    if(pairs.concordant+pairs.discordant+pairs.equalIndexExcluded!==total||
       pairs.equalIndexExcluded!==equal)
     throw Error('調教比較ペア母数不一致');
    for(const k of Object.keys(totals[b]))totals[b][k]+=pairs[k];
   }
  }else if(row.comparedRunnerCount!==0||row.pairCounts!==null||
            row.crossBandPairs!==null){
   throw Error('保留レースに比較件数');
  }
  rows.push(row);
 }
 if(used.size!==receipts.length||studied!==value.studiedRaceCount||
    !value.observedPairsByTrainingBand||
    Object.keys(value.observedPairsByTrainingBand).sort().join(',')!=='A,B,C,S')
  throw Error('調教比較の全体件数不一致');
 for(const b of bands)
  for(const k of Object.keys(totals[b]))
   if(value.observedPairsByTrainingBand[b]?.[k]!==totals[b][k])
    throw Error('調教比較の集計値不一致');
 if(!value.observedCrossBandPairs||
    Object.keys(value.observedCrossBandPairs).sort().join(',')!==
      keys.slice().sort().join(',')||
    keys.some(k=>value.observedCrossBandPairs[k]?.concordant!==
      crossTotals[k].concordant||
      value.observedCrossBandPairs[k]?.discordant!==crossTotals[k].discordant))
  throw Error('調教S/A/B/Cランク間の合計が不一致');
 return {rows,totals,crossTotals};
}
$('autoWorkoutProviderCheck').onclick=async()=>{
 const day=$('autoDay').value.replaceAll('-','');
 const button=$('autoWorkoutProviderCheck');
 if(button.disabled)return;
 button.disabled=true;
 const seq=++workoutProviderSeq;
 $('autoWorkoutProviderSummary').replaceChildren();
 $('autoWorkoutProviderStatus').textContent=
  '保存済みの調教順位署名を確認してJRDB暫定着順と比較中…';
 try{
  const receipts=savedWorkoutLocksDay(day).selected;
  if(!receipts.length)throw Error('no_signed_workout_study');
  const payload=JSON.stringify({date:day,receipts});
  if(payload.length>170000)throw Error('oversized_workout_study');
  const response=await fetch('/api/owner-workout-order-provider-check',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body:payload
  });
  const result=await response.json();
  if(seq!==workoutProviderSeq||
     day!==$('autoDay').value.replaceAll('-',''))return;
  if(!response.ok)throw Error('provider_workout_result_failed');
  const {rows,totals,crossTotals}=validateWorkoutProviderComparison(result,receipts,day);
  const stored=saveWorkoutPairReceipts(result,receipts,day);
  // Research in a different HMAC domain; no changes to old results.
  const crossStored=saveWorkoutCrossReceipts(result,receipts,day);
  const cards=[];
  for(const row of rows){
   const card=dom('p',row.track+row.race+'R：'+
    (row.providerStatus==='pending'?'暫定着順不足・未確定・保留':
     '同評価内の指数順と暫定着順を照合済み（参考）'),'muted');
   cards.push(card);
  }
  if(result.studiedRaceCount){
   const same=Object.values(totals).reduce((n,x)=>n+x.concordant,0),
    opposite=Object.values(totals).reduce((n,x)=>n+x.discordant,0),
    equal=Object.values(totals).reduce((n,x)=>n+x.equalIndexExcluded,0);
   cards.unshift(dom('p','調教の同評価内：指数順と暫定着順が一致 '+same+
    '組／不一致 '+opposite+'組／元の指数同点で判定対象外 '+
    equal+'組。全頭の発走前固定があるレースだけの比較。','muted'));
  }
  if(result.studiedRaceCount){
   const order=['S>A','S>B','S>C','A>B','A>C','B>C'];
   const agree=order.reduce((v,k)=>v+crossTotals[k].concordant,0);
   const disagree=order.reduce((v,k)=>v+crossTotals[k].discordant,0);
   cards.push(dom('p','異なる調教ランクの順序：S>A>B>Cの仮説に沿った先着 '+
    agree+'組／逆転 '+disagree+'組。'+
    'ランク間の値は今回の画面だけの未署名参考集計（JRDB追加照会0回）。'+
    '正式30点・JRA公式判定ではありません。','muted'));
   const details=dom('details');
   details.append(dom('summary','S対A・A対Bなど6組の内訳'));
   for(const key of order)
    details.append(dom('p',key+'：想定順で先着 '+
     crossTotals[key].concordant+'組／逆転 '+
     crossTotals[key].discordant+'組','muted'));
   cards.push(details);
  }
  $('autoWorkoutProviderSummary').replaceChildren(...cards);
  $('autoWorkoutProviderStatus').textContent=
   'JRDB暫定着順の全頭照合 '+result.studiedRaceCount+'/'+result.raceCount+
   'R。結果が欠けるRは保留。JRA公式の結果・勝率・30点配点の校正・回収率は未確認。'+
   '既存の予想・購入記録は変更していません。'+
   '検証用結果は初回固定 '+stored.added+'R／前回の記録を保持 '+stored.previous+
   'R。ランク間の比較も初回固定 '+crossStored.added+
   'R／既存 '+crossStored.previous+'R。';
 }catch(_){
  if(seq===workoutProviderSeq){
   $('autoWorkoutProviderSummary').replaceChildren();
   $('autoWorkoutProviderStatus').textContent=
    '署名付き調教研究とJRDB暫定着順を安全に比較できませんでした。'+
    '取得・記録を自動で再試行せず、保存済み予想も変更しません。';
  }
 }finally{
  if(seq===workoutProviderSeq&&day===$('autoDay').value.replaceAll('-',''))
   showSavedWorkoutLocks(day);
 }
};
$('autoWorkoutPairVerify').onclick=async()=>{
 const btn=$('autoWorkoutPairVerify'),day=$('autoDay').value.replaceAll('-','');
 if(btn.disabled)return;
 btn.disabled=true;
 const seq=++workoutPairVerifySeq;
 $('autoWorkoutPairVerifyStatus').textContent='保存済みの発走前・レース後の署名を無料確認中…';
 try{
  const selected=savedWorkoutPairEntries(day).selected;
  if(!selected.length)throw Error('no_saved_observations');
  const ids=new Set(selected.map(r=>r.snapshot.track+'|'+r.snapshot.race));
  const prestart=savedWorkoutLocksDay(day).selected.filter(r=>
   ids.has(r.snapshot.track+'|'+r.snapshot.race));
  if(prestart.length!==selected.length)throw Error('prestart_missing');
  const body=JSON.stringify({date:day,prestartReceipts:prestart,receipts:selected});
  if(body.length>250000)throw Error('verification_body_too_large');
  const res=await fetch('/api/owner-workout-pair-verify',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body
  });
  const data=await res.json();
  if(seq!==workoutPairVerifySeq||day!==$('autoDay').value.replaceAll('-',''))return;
  if(!res.ok||data?.version!=='owner-workout-pair-verify-1'||
     data.date!==day||data.verifiedRaceCount!==selected.length||
     data.serverSigned!==true||data.researchOnly!==true||
     data.privateOwnerOnly!==true||data.providerCalls!==0||
     data.officialJraVerified!==false||data.calibrationReady!==false||
     data.formalPredictionReady!==false||data.bettingReady!==false||
     data.changesExistingReceipts!==false)
   throw Error('server_hmac_verification_mismatch');
  $('autoWorkoutPairVerifyStatus').textContent=
   '保存済み結果 '+selected.length+'Rの発走前・レース後署名をサーバーで検証済み。'+
   'JRDB追加取得0回。暫定結果でありJRA公式の着順確認・30点の校正は未実施。';
 }catch(_){
  if(seq===workoutPairVerifySeq)
   $('autoWorkoutPairVerifyStatus').textContent=
    '研究結果の署名を検証できません。元の記録は消さず、バックアップを確認してください。';
 }finally{
  if(seq===workoutPairVerifySeq&&day===$('autoDay').value.replaceAll('-',''))
   showSavedWorkoutPairHistory(day);
 }
};
$('autoWorkoutCrossVerify').onclick=async()=>{
 const day=$('autoDay').value.replaceAll('-','');
 const button=$('autoWorkoutCrossVerify');
 if(button.disabled)return;
 button.disabled=true;
 const seq=++workoutCrossVerifySeq;
 $('autoWorkoutCrossVerifyStatus').textContent='調教ランク間の署名をサーバーで確認中（追加照会0回）…';
 try{
  const selected=savedWorkoutCrossEntries(day).selected;
  if(!selected.length)throw Error('no_cross_history');
  const ids=new Set(selected.map(x=>x.snapshot.track+'|'+x.snapshot.race));
  const prestart=savedWorkoutLocksDay(day).selected.filter(x=>
   ids.has(x.snapshot.track+'|'+x.snapshot.race));
  if(prestart.length!==selected.length)throw Error('missing_prestart');
  const body=JSON.stringify({date:day,prestartReceipts:prestart,receipts:selected});
  if(body.length>250000)throw Error('too_large');
  const response=await fetch('/api/owner-workout-cross-band-verify',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body});
  const value=await response.json();
  if(seq!==workoutCrossVerifySeq||day!==$('autoDay').value.replaceAll('-',''))return;
  if(!response.ok||value.version!=='owner-workout-cross-band-verify-1'||
     value.date!==day||value.verifiedRaceCount!==selected.length||
     value.serverSigned!==true||value.researchOnly!==true||
     value.privateOwnerOnly!==true||value.providerCalls!==0||
     value.officialJraVerified!==false||
     value.calibrationReady!==false||
     value.formalTrainingScore30Ready!==false||
     value.bettingReady!==false||value.actualPurchase!==false||
     value.changesExistingReceipts!==false)
   throw Error('cross_band_signature_bad');
  $('autoWorkoutCrossVerifyStatus').textContent=
   '選択日のランク間研究 '+selected.length+
   'Rのサーバー署名を検証済み。JRDB追加照会0回。'+
   'JRA公式照合・正式30点採点ではありません。';
 }catch(_){
  if(seq===workoutCrossVerifySeq)
   $('autoWorkoutCrossVerifyStatus').textContent=
    'ランク間研究記録の署名を確認できません。元の記録を消さずバックアップを確認してください。';
 }finally{
  if(seq===workoutCrossVerifySeq&&day===$('autoDay').value.replaceAll('-',''))
   showSavedWorkoutCrossHistory(day);
 }
};
$('autoFiveProviderCheck').onclick=async()=>{
 const button=$('autoFiveProviderCheck'),day=$('autoDay').value.replaceAll('-','');
 if(button.disabled)return;
 const seq=++fiveProviderSeq;button.disabled=true;
 $('autoFiveProviderRaces').replaceChildren();
 $('autoFiveProviderStatus').textContent='発走前固定85点とJRDB暫定着順を照合中…';
 try{
  const receipts=savedFiveDay(day).picked;
  if(!receipts.length)throw Error('no_saved_85');
  const payload=JSON.stringify({date:day,receipts});
  if(payload.length>250000)throw Error('oversize_85');
  const res=await fetch('/api/owner-five-core-provider-check',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body:payload
  });
  const result=await res.json();
  if(seq!==fiveProviderSeq||day!==$('autoDay').value.replaceAll('-',''))return;
  if(!res.ok)throw Error('jrdb_85_unavailable');
  const {rows,exposure,tally}=verifyFiveProviderReport(result,receipts,day);
  const keys=['training','course_distance','pace','ground','recent'],
   bands=['S','A','B','C'];
  const cards=[];
  for(const item of rows){
   const card=dom('details');
   card.append(dom('summary',item.track+' '+item.race+'R｜'+
    (item.providerStatus==='pending'?'JRDB暫定成績待ち':'JRDB暫定1〜3着を観測')));
   if(item.providerStatus==='pending'){
    card.append(dom('p','発走前・成績不足・矛盾などにより保留。0点や予想失敗と判定しません。','muted'));
   }else{
    card.append(dom('p','JRDB暫定1〜3着：'+
     item.observedPodiumNumbers.join('→')+'（JRA独立照合なし）','muted'));
    if(item.studiedWinnerObserved){
     card.append(dom('p','1着馬'+item.observedPodiumNumbers[0]+
      '番の発走前研究値 '+item.winnerStudyScore85.toFixed(2)+
      '/85｜調教 '+item.winnerStudyBands.training+
      '・近走 '+item.winnerStudyBands.recent+
      '・コース '+item.winnerStudyBands.course_distance+
      '・展開 '+item.winnerStudyBands.pace+
      '・馬場 '+item.winnerStudyBands.ground,'muted'));
    }else{
     card.append(dom('p','勝ち馬は発走前85点の5項目がそろっていません。未評価のままです。','muted'));
    }
   }
   cards.push(card);
  }
  if(result.observedRaceCount){
   const overview=dom('details');
   overview.append(dom('summary','5項目の発走前研究母数と暫定勝ち馬の帯（正式未検証）'));
   overview.append(dom('p','暫定着順を観測したレースで発走前研究帯を持っていた'+
    result.observedStudiedRunnerCount+'頭が母数。勝ち馬だけのS件数で強さは判断できません。','muted'));
   const labels={training:'調教',recent:'近走',course_distance:'コース距離',
    pace:'展開',ground:'馬場'};
   for(const k of keys)
    overview.append(dom('p',labels[k]+'｜'+
     bands.map(b=>b+'：研究対象'+exposure[k][b]+'頭／JRDB暫定1着'+
      tally[k][b]+'頭').join('、')+'。','muted'));
   overview.append(dom('p','参考母数であり正式な的中率や勝率を意味しません。'+
    'JRA公式結果と時系列未使用期間での校正は未完成。','muted'));
   cards.push(overview);
  }
  $('autoFiveProviderRaces').replaceChildren(...cards);
  $('autoFiveProviderStatus').textContent=
   'JRDB暫定着順を観測 '+result.observedRaceCount+'/'+result.raceCount+
   'R／85点研究が揃っていた1着馬 '+result.observedStudiedWinnerCount+
   'R／同じレースの発走前85点研究対象 '+result.observedStudiedRunnerCount+
   '頭。JRA公式結果・精度・勝率・回収率は未確認。保存済み予想や購入記録は変更なし。';
 }catch(_){if(seq===fiveProviderSeq){
  $('autoFiveProviderRaces').replaceChildren();
  $('autoFiveProviderStatus').textContent=
   '85点研究とJRDB暫定成績を安全に比較できませんでした。署名や通信状況を確認。固定記録は変更なし。';
 }}finally{
  if(seq===fiveProviderSeq&&day===$('autoDay').value.replaceAll('-',''))
   button.disabled=false;
 }
};
$('autoHistoryStaffArchiveVerify').onclick=async()=>{
 const btn=$('autoHistoryStaffArchiveVerify');
 if(btn.disabled)return;
 const seq=++staffArchiveVerifySeq;
 btn.disabled=true;
 $('autoHistoryStaffArchiveVerifyStatus').textContent=
  '開催日別の騎手厩舎研究の署名を再確認中…';
 try{
  const records=savedStaffStudySessions();
  if(!records.length)throw Error('empty_staff_study');
  const body=JSON.stringify({receipts:records});
  if(body.length>250000)throw Error('staff_study_too_large');
  const response=await fetch('/api/owner-staff-study-verify',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body
  });
  const checked=await response.json();
  if(seq!==staffArchiveVerifySeq)return;
  if(!response.ok||checked.version!=='owner-staff-study-verify-1'||
     checked.serverSigned!==true||
     checked.verifiedDateCount!==records.length||
     checked.researchOnly!==true||checked.privateOwnerOnly!==true||
     checked.independentHistoricRaceDedupVerified!==false||
     checked.officialJraVerified!==false||
     checked.formalTenPointReady!==false||checked.bettingReady!==false||
     checked.actualPurchase!==false||checked.sourceProviderReadCount!==0)
   throw Error('Signature mismatch');
  $('autoHistoryStaffArchiveVerifyStatus').textContent=
   '開催日別の研究記録 '+checked.verifiedDateCount+
   '日分の署名を検証。過去R重複の排除・実力10点・JRA結果・回収率の確認ではありません。';
 }catch(_){
  if(seq===staffArchiveVerifySeq)
   $('autoHistoryStaffArchiveVerifyStatus').textContent=
    '研究記録の署名を確認できません。保存済みデータは変更していません。';
 }finally{
  if(seq===staffArchiveVerifySeq)
   btn.disabled=false;
 }
};
$('autoResearch6DraftVerify').onclick=async()=>{
 const button=$('autoResearch6DraftVerify'),day=$('autoDay').value.replaceAll('-','');
 if(button.disabled)return;
 const seq=++r6VerifySeq;
 button.disabled=true;
 $('autoResearch6DraftVerifyStatus').textContent='固定79点の署名をサーバーで確認中…';
 try{
  const {picked}=savedResearch6DraftDay(day);
  if(!picked.length)throw Error('no_signed_draft');
  const body=JSON.stringify({date:day,receipts:picked});
  if(body.length>250000)throw Error('signed_draft_too_large');
  const res=await fetch('/api/owner-research6-draft-verify',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body
  });
  const result=await res.json();
  if(seq!==r6VerifySeq||day!==$('autoDay').value.replaceAll('-',''))return;
  if(!res.ok||result.version!=='owner-research6-draft-verify-1'||
     result.recordCount!==picked.length||result.serverSigned!==true||
     result.researchOnly!==true||result.privateOwnerOnly!==true||
     result.officialJraVerified!==false||
     result.independentJraScheduleVerified!==false||
     result.formalPredictionReady!==false||result.resultComparisonReady!==false||
     result.bettingReady!==false||result.autoPurchase!==false||
     result.actualPurchase!==false)
   throw Error('signature_verification_failed');
  $('autoResearch6DraftVerifyStatus').textContent=
   '新配点79点の発走前署名を確認：'+result.recordCount+
   'R。固定した研究買い目はそのまま。JRA公式・正式予想・実購入・的中・回収率は未確認。';
 }catch(_){if(seq===r6VerifySeq){
  $('autoResearch6DraftVerifyStatus').textContent=
   '固定79点下書きの署名を確認できません。以前の記録は変更していません。';
 }}finally{
  if(seq===r6VerifySeq&&day===$('autoDay').value.replaceAll('-',''))
   button.disabled=false;
 }
};
$('autoCoreProviderCheck').onclick=async()=>{
 const button=$('autoCoreProviderCheck'),day=$('autoDay').value.replaceAll('-','');
 if(button.disabled)return;
 const seq=++coreProviderSeq;button.disabled=true;
 $('autoCoreProviderRaces').replaceChildren();
 $('autoCoreProviderStatus').textContent='署名済み研究値をJRDB成績と参考照合中…';
 try{
  const receipts=savedCoreDay(day);
  if(!receipts.length)throw Error('no_sealed_study');
  const payload=JSON.stringify({date:day,receipts});
  if(payload.length>180000)throw Error('too_large');
  const res=await fetch('/api/owner-three-core-provider-check',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body:payload
  });
  const report=await res.json();
  if(seq!==coreProviderSeq||day!==$('autoDay').value.replaceAll('-',''))return;
  if(!res.ok)throw Error('provider_unavailable');
  const checked=verifyCoreProviderReport(report,receipts,day);
  // Build all cards only after every race and aggregate passed checks.
  const cards=[];
  for(const {row,original} of checked){
   const card=dom('details');
   card.append(dom('summary',row.track+' '+row.race+'R｜'+
    (row.providerStatus==='pending'?'暫定成績未確認':
     'JRDB暫定1〜3着を観測')));
   if(row.providerStatus==='pending'){
    card.append(dom('p','成績不足・混在・発走前などのため保留。勝ち負け、的中、0点を判定しません。','muted'));
   }else{
    card.append(dom('p','JRDB暫定1〜3着：'+
     row.observedPodiumNumbers.join('→')+'（公式独立照合なし）','muted'));
    if(row.studiedWinnerObserved){
     card.append(dom('p','1着馬'+row.observedPodiumNumbers[0]+
      '番の発走前研究値：'+row.winnerStudyScore70.toFixed(2)+
      '/70点｜調教 '+row.winnerStudyBands.training+
      '・コース '+row.winnerStudyBands.course_distance+
      '・展開 '+row.winnerStudyBands.pace,'muted'));
    }else{
     card.append(dom('p','1着馬には、発走前の3項目が全部そろった研究値がありません。未評価として保留します。','muted'));
    }
   }
   cards.push(card);
  }
  $('autoCoreProviderRaces').replaceChildren(...cards);
  $('autoCoreProviderStatus').textContent=
   'JRDB暫定1〜3着を観測 '+report.observedRaceCount+'/'+report.raceCount+
   'R／発走前に3項目そろっていた1着馬 '+report.observedStudiedWinnerCount+
   'R。JRA公式結果・勝率・正式的中・回収率は未照合。'+
   '3連単、固定研究値、購入記録は変更していません。';
 }catch(_){if(seq===coreProviderSeq){
  $('autoCoreProviderRaces').replaceChildren();
  $('autoCoreProviderStatus').textContent=
   '70点研究値とJRDB暫定成績を安全に比較できませんでした。'+
   '署名・通信・成績更新状況を確認。固定値や3連単は変更していません。';
 }}finally{
  if(seq===coreProviderSeq&&day===$('autoDay').value.replaceAll('-',''))
   button.disabled=false;
 }
};
$('autoCoreVerify').onclick=async()=>{
 const button=$('autoCoreVerify'),day=$('autoDay').value.replaceAll('-','');
 if(button.disabled)return;
 const seq=++coreVerifySeq;button.disabled=true;
 $('autoCoreVerifyStatus').textContent='固定済み70点研究記録の署名を確認中…';
 try{
  const receipts=savedCoreDay(day);
  if(!receipts.length){
   $('autoCoreVerifyStatus').textContent='この日の固定済み70点研究記録はありません。';
   return;
  }
  const payload=JSON.stringify({date:day,receipts});
  if(payload.length>180000)throw Error('記録が大きすぎます');
  const res=await fetch('/api/owner-three-core-verify',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},body:payload
  });
  const result=await res.json();
  if(seq!==coreVerifySeq||day!==$('autoDay').value.replaceAll('-',''))return;
  if(!res.ok||result?.version!=='owner-three-core-verify-1'||
     result.serverSigned!==true||result.recordCount!==receipts.length||
     result.researchOnly!==true||result.privateOwnerOnly!==true||
     result.officialJraVerified!==false||
     result.independentJraScheduleVerified!==false||
     result.calibrationReady!==false||result.resultComparisonReady!==false||
     result.bettingReady!==false||result.autoPurchase!==false||
     result.actualPurchase!==false)
   throw Error('署名照合に失敗');
  $('autoCoreVerifyStatus').textContent='サーバー署名確認成功：'+receipts.length+
   'Rの発走前研究値。予想精度・JRA公式結果・馬券・回収率は未検証。元の固定値は変更していません。';
 }catch(_){if(seq===coreVerifySeq){
  $('autoCoreVerifyStatus').textContent=
   '署名を確認できませんでした。記録を編集・削除せずバックアップを確保してください。';
 }}finally{if(seq===coreVerifySeq)button.disabled=false;}
};
$('autoHistoryAudit').onclick=async()=>{
 const button=$('autoHistoryAudit'),day=historyDay;
 if(button.disabled||!day||day!==$('autoDay').value.replaceAll('-',''))return;
 button.disabled=true;const seq=++historySeq;
 const wantStaff=$('autoHistoryStaffSample').checked===true,
  staffBatch=$('autoHistoryStaffRaceLimit').value==='3'?3:1;
 $('autoHistoryStaffStatus').textContent=wantStaff?
  '過去'+staffBatch+'Rの騎手・厩舎を追加最大'+(2*staffBatch)+
  '回のJRDB照会で確認中…':
  '今回は追加の騎手・厩舎照会なし。';
 $('autoHistoryAuditStatus').textContent='過去の同条件を照合中…';
 $('autoHistoryAuditRaces').replaceChildren();
 try{
  const res=await fetch('/api/jrdb/history',{
   method:'POST',credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
    'Accept':'application/json'},
   body:JSON.stringify(wantStaff?
    (staffBatch===3?{date:day,limit:8,staffSample:true,staffBatchRaces:3}:
     {date:day,limit:8,staffSample:true}):
    {date:day,limit:8})
  });
  const raw=await res.json();
  if(seq!==historySeq)return;
  if(!res.ok)throw Error('履歴機能は利用不可');
  const rows=validateHistory(raw);
  // This read-only preview is checked against the already-validated
  // five-factor grades, never a client-supplied score or results feed.
  const sparseFive=validateSparseFiveReference(raw);
  if(raw.sparseFiveCapture!==undefined&&sparseFive===null)
   throw Error('参照資料がない研究署名');
  if(wantStaff&&staffBatch===3){
   const x=raw?.pastStaffBatch;
   const ints=['requestedRaceLimit','selectedPastRaceCount','providerReadCount',
    'providerReadBudget','completedJoinRaceCount','heldOrIncompleteRaceCount',
    'totalJoinedRunnerObservations','distinctJockeyCount','distinctTrainerCount',
    'distinctPairCount','pairsSeenInTwoOrMoreRaces','pairRunnerObservations',
    'observedFirstPlaceCount','observedTopThreeCount'];
   if(!x||x.version!=='owner-past-staff-batch-1'||
      ints.some(k=>!Number.isInteger(x[k])||x[k]<0)||
      x.requestedRaceLimit!==3||x.providerReadBudget!==6||
      x.selectedPastRaceCount>3||
      x.providerReadCount>2*x.selectedPastRaceCount||
      x.completedJoinRaceCount+x.heldOrIncompleteRaceCount!==
        x.selectedPastRaceCount||
      x.providerUnavailable!==true&&x.providerUnavailable!==false||
      (x.providerUnavailable===false&&
       x.providerReadCount!==2*x.selectedPastRaceCount)||
      (x.providerUnavailable===true&&
       (x.providerReadCount<1||x.heldOrIncompleteRaceCount<1))||
      x.totalJoinedRunnerObservations<3*x.completedJoinRaceCount||
      x.totalJoinedRunnerObservations>18*x.completedJoinRaceCount||
      x.pairRunnerObservations!==x.totalJoinedRunnerObservations||
      x.observedFirstPlaceCount!==x.completedJoinRaceCount||
      x.observedTopThreeCount!==3*x.completedJoinRaceCount||
      x.distinctJockeyCount>x.totalJoinedRunnerObservations||
      x.distinctTrainerCount>x.totalJoinedRunnerObservations||
      x.distinctPairCount>x.totalJoinedRunnerObservations||
      x.pairsSeenInTwoOrMoreRaces>x.distinctPairCount||
      (x.completedJoinRaceCount===0&&
       (x.distinctJockeyCount||x.distinctTrainerCount||x.distinctPairCount))||
      x.sourceFamily!=='private_dky_dse_bounded_races'||
      x.pastResultPublicationVerified!==false||
      x.independentJraVerified!==false||
      x.fullTenFactorReady!==false||
      x.jockeyTrainerPerformanceAssessed!==false||
      x.holdoutValidated!==false||
      x.formalTenPointGrade!=='未評価'||x.formalTenPointScore!==null||
      x.predictionReady!==false||x.bettingReady!==false||
      x.autoPurchase!==false||x.actualPurchase!==false||
      x.researchOnly!==true||x.privateOwnerOnly!==true||
      x.changesExistingReceipts!==false||
      x.changesExistingTickets!==false||x.changesExistingRoi!==false||
      x.additionalPaidReadsOnlyOnExplicitOptIn!==true||
      raw?.pastStaffSample!==undefined)
    throw Error('過去3R騎手厩舎の比較資料が不正');
   $('autoHistoryStaffStatus').textContent=
    '過去'+x.selectedPastRaceCount+'Rのうち資料結合'+
    x.completedJoinRaceCount+'R・保留'+x.heldOrIncompleteRaceCount+
    'R。追加照会'+x.providerReadCount+'/6回、出走観測'+
    x.totalJoinedRunnerObservations+'件、同一騎手×厩舎'+
    x.distinctPairCount+'組（2R以上に登場：'+
    x.pairsSeenInTwoOrMoreRaces+
    '組）。10点採点・公式結果・回収率には未使用。';
  }else if(wantStaff){
   if(raw?.pastStaffBatch!==undefined)
    throw Error('指定していない3R追加結果が混入');
   const x=raw?.pastStaffSample;
   const statuses=['joined_private_sample','incomplete_or_ambiguous_historical_result',
    'provider_unavailable','no_referenced_past_race'];
   if(!x||x.version!=='owner-past-staff-sample-1'||
      !statuses.includes(x.status)||
      x.sourceFamily!=='private_dky_dse_past_race'||
      x.pastResultPublicationVerified!==false||
      x.independentJraVerified!==false||
      x.jockeyTrainerPerformanceAssessed!==false||
      x.holdoutValidated!==false||
      x.formalTenPointGrade!=='未評価'||x.formalTenPointScore!==null||
      x.predictionReady!==false||x.bettingReady!==false||
      x.autoPurchase!==false||x.actualPurchase!==false||
      x.researchOnly!==true||x.privateOwnerOnly!==true||
      x.changesExistingReceipts!==false||
      x.changesExistingTickets!==false||x.changesExistingRoi!==false||
      !Number.isInteger(x.providerReadCount)||
      ![0,1,2].includes(x.providerReadCount)||
      x.pastRacesSelected!==Number(x.providerReadCount>0)||
      !['runnerCount','distinctJockeyCount','distinctTrainerCount',
        'distinctPairCount','observedFirstPlaceCount','observedTop3Count']
        .every(k=>Number.isInteger(x[k])&&x[k]>=0&&x[k]<=18)||
      (x.status==='joined_private_sample'&&(
        x.providerReadCount!==2||x.runnerCount<3||
        x.distinctPairCount<1||x.distinctPairCount>x.runnerCount||
        x.distinctJockeyCount<1||x.distinctTrainerCount<1||
        x.observedFirstPlaceCount!==1||
        x.observedTop3Count!==Math.min(3,x.runnerCount)))||
      (x.status!=='joined_private_sample'&&(
        x.runnerCount!==0||x.distinctPairCount!==0))||
      (x.status==='no_referenced_past_race'&&x.providerReadCount!==0)||
      (x.status==='incomplete_or_ambiguous_historical_result'&&
       x.providerReadCount!==2)||
      (x.status==='provider_unavailable'&&
       ![1,2].includes(x.providerReadCount)))
    throw Error('追加騎手・厩舎資料の形式が不正');
   $('autoHistoryStaffStatus').textContent=
    x.status==='joined_private_sample'?
     '過去1Rを資料結合：'+x.runnerCount+'頭、騎手'+
     x.distinctJockeyCount+'種、厩舎'+x.distinctTrainerCount+
     '種、同一ペア'+x.distinctPairCount+
     '組（追加2 API照会）。正式10点の採点・JRA公式照合は未完了。':
    x.status==='no_referenced_past_race'?
     '参照できる過去レースがないため、追加API取得なし。':
     '過去1Rの資料結合は保留（追加'+x.providerReadCount+
     ' API照会を試行）。取消・欠損・同着・API状態等を確認。正式10点には使いません。';
  }else if(raw?.pastStaffSample!==undefined||
            raw?.pastStaffBatch!==undefined){
   throw Error('本人が選んでいない追加取得結果が混入');
  }

  // /dse updated_at is a last-modified marker, never an initial result
  // publication timestamp or independent JRA verification. This data comes
  // ONLY from the explicitly selected staff history read; do not persist it.
  if(raw?.pastResultUpdateAudit!==undefined){
   const x=raw.pastResultUpdateAudit,
    keys=['missingUpdateCount','dateOnlyCount','ambiguousUpdateCount',
     'timestampBeforeCaptureCount','timestampAtOrAfterCaptureCount'],
    staff=staffBatch===3?raw.pastStaffBatch:raw.pastStaffSample,
    validCount=(n,max)=>Number.isInteger(n)&&n>=0&&n<=max;
   if(!wantStaff||!staff||!x||
      x.version!=='owner-dse-update-diagnostic-1'||
      x.source!=='already_fetched_private_dse_updated_at'||
      !validCount(x.observedResponseCount,3)||
      !validCount(x.invalidResponseCount,3)||
      x.invalidResponseCount>x.observedResponseCount||
      !validCount(x.observedResultRowCount,54)||
      keys.some(k=>!validCount(x[k],54))||
      keys.reduce((sum,k)=>sum+x[k],0)!==x.observedResultRowCount||
      x.observedResultRowCount>
       (x.observedResponseCount-x.invalidResponseCount)*18||
      x.observedResponseCount>Math.floor(staff.providerReadCount/2)||
      x.timestampOrderingChecked!==true||
      x.initialPublicationTimeVerified!==false||
      x.sourceTimestampAuthenticityVerified!==false||
      x.historicalResultPublicationTimesVerified!==false||
      x.independentJraVerified!==false||x.officialJraVerified!==false||
      x.formalTenFactorsReady!==false||x.bettingReady!==false||
      x.researchOnly!==true||x.privateOwnerOnly!==true||
      x.extraProviderCalls!==0||x.changesExistingTickets!==false||
      x.changesExistingReceipts!==false||x.changesExistingRoi!==false)
    throw Error('過去結果の更新日時の安全な集計に不一致');
   $('autoHistoryStaffStatus').textContent+=
    ' 過去結果の更新日時：時刻付き'+
    (x.timestampBeforeCaptureCount+x.timestampAtOrAfterCaptureCount)+
    '件／日付のみ'+x.dateOnlyCount+
    '件／不明・不正'+(x.missingUpdateCount+x.ambiguousUpdateCount)+
    '件。更新日時は初回公表日時ではなく、正式採点には使いません。';
  }
  // A three-race aggregate may be sealed by the private server. Only after
  // a fresh, read-only signature verification will this iPhone first-write.
  // We do NOT merge historical IDs across days or grade any rider.
  if(wantStaff&&staffBatch===3&&raw?.pastStaffBatch?.providerReadCount>0){
   try{
    const entry=raw.staffStudyCapture,p=validateStaffStudyEntry(entry);
    const source={...raw.pastStaffBatch};
    delete source.note;
    if(p.date!==day||JSON.stringify(p.summary)!==JSON.stringify(source))
     throw Error('Study receipt does not match the paid sample');
    const response=await fetch('/api/owner-staff-study-verify',{
     method:'POST',credentials:'same-origin',cache:'no-store',
     headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
      'Accept':'application/json'},
     body:JSON.stringify({receipts:[entry]})
    });
    const checked=await response.json();
    if(seq!==historySeq||historyDay!==day)return;
    if(!response.ok||checked.version!=='owner-staff-study-verify-1'||
       checked.serverSigned!==true||checked.verifiedDateCount!==1||
       checked.researchOnly!==true||checked.privateOwnerOnly!==true||
       checked.independentHistoricRaceDedupVerified!==false||
       checked.officialJraVerified!==false||
       checked.formalTenPointReady!==false||checked.bettingReady!==false||
       checked.actualPurchase!==false||checked.sourceProviderReadCount!==0)
     throw Error('Study signature not verified');
    $('autoHistoryStaffArchiveStatus').textContent=
     firstWriteStaffStudyEntry(entry);
    showSavedStaffStudySessions();
   }catch(_){
    $('autoHistoryStaffArchiveStatus').textContent=
     '3Rの研究記録は署名確認・保存できませんでした。以前の初回記録は変更しません。';
   }
  }else if(raw?.staffStudyCapture!==undefined){
   throw Error('Unrequested staff study receipt in history');
  }

  // Core research capture is optional in legacy saved history responses;
  // new private /history calls send it signed before the provisional off.
  // Never ingest user-provided outcomes or update existing 3連単 tickets.
  let coreMessage='この履歴資料には発走前の署名付き70点研究記録がありません。既存記録は変更しません。';
  if(raw.coreCapture!==undefined){
   try{
    const coreReceipts=validateCoreCapture(raw.coreCapture,rows,day);
    if(coreReceipts.length){
     const payload=JSON.stringify({date:day,receipts:coreReceipts});
     if(payload.length>180000)throw Error('70点研究の転送サイズ超過');
     const verified=await fetch('/api/owner-three-core-verify',{
      method:'POST',credentials:'same-origin',cache:'no-store',
      headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
       'Accept':'application/json'},body:payload
     });
     const check=await verified.json();
     if(seq!==historySeq||historyDay!==day)return;
     if(!verified.ok||!check||
        check.version!=='owner-three-core-verify-1'||
        check.serverSigned!==true||check.recordCount!==coreReceipts.length||
        check.researchOnly!==true||check.privateOwnerOnly!==true||
        check.officialJraVerified!==false||
        check.independentJraScheduleVerified!==false||
        check.calibrationReady!==false||
        check.resultComparisonReady!==false||
        check.bettingReady!==false||check.autoPurchase!==false||
        check.actualPurchase!==false)
      throw Error('70点研究の署名検証が失敗');
     coreMessage=saveCoreReceipts(coreReceipts);
    }else{
     coreMessage='この開催日は研究用70点の固定対象がありません。発走済み・資料不足の馬から後付け記録を作りません。';
    }
   }catch(_){
    coreMessage='70点研究の署名検証または端末保存ができません。以前の固定記録は変更しません。';
   }
  }
  showSavedCore(day);
  $('autoCoreSaveStatus').textContent=coreMessage;
  let fiveMessage='この過去資料には発走前に署名した85点研究記録がありません。';
  if(raw.fiveCoreCapture!==undefined){
   try{
    const receipts=validateFiveCapture(raw.fiveCoreCapture,rows,day);
    if(receipts.length){
     const body=JSON.stringify({date:day,receipts});
     if(body.length>250000)throw Error('85点研究の検証サイズ超過');
     const resp=await fetch('/api/owner-five-core-verify',{
      method:'POST',credentials:'same-origin',cache:'no-store',
      headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
       'Accept':'application/json'},body
     });
     const check=await resp.json();
     if(seq!==historySeq||historyDay!==day)return;
     if(!resp.ok||check.version!=='owner-five-core-verify-1'||
        check.serverSigned!==true||check.recordCount!==receipts.length||
        check.researchOnly!==true||check.privateOwnerOnly!==true||
        check.officialJraVerified!==false||
        check.independentJraScheduleVerified!==false||
        check.calibrationReady!==false||check.resultComparisonReady!==false||
        check.bettingReady!==false||check.autoPurchase!==false||
        check.actualPurchase!==false)
      throw Error('85点研究の署名を検証できません');
     fiveMessage=saveFiveReceipts(receipts,day);
    }else fiveMessage='発走前85点の固定対象なし。発走後に追加しません。';
   }catch(_){
    fiveMessage='85点研究の署名・保存に失敗。以前の記録は変更していません。';
   }
  }
  showSavedFive(day);
  $('autoFiveSaveStatus').textContent=fiveMessage;
  // Separate HMAC key domain for new research-6 79-point draft TICKETS.
  // Verify with this owner's private server before first-write to iPhone.
  let r6Message='この履歴には新79点3連単の発走前固定記録がありません。';
  if(raw.research6DraftCapture!==undefined){
   try{
    const receipts=validateResearch6DraftCapture(
     raw.research6DraftCapture,rows,day);
    if(receipts.length){
     const body=JSON.stringify({date:day,receipts});
     if(body.length>250000)throw Error('研究79点下書きの検証サイズ超過');
     const verify=await fetch('/api/owner-research6-draft-verify',{
      method:'POST',credentials:'same-origin',cache:'no-store',
      headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
       'Accept':'application/json'},body
     });
     const check=await verify.json();
     if(seq!==historySeq||historyDay!==day)return;
     if(!verify.ok||!check||
        check.version!=='owner-research6-draft-verify-1'||
        check.serverSigned!==true||
        check.recordCount!==receipts.length||
        check.researchOnly!==true||check.privateOwnerOnly!==true||
        check.officialJraVerified!==false||
        check.independentJraScheduleVerified!==false||
        check.formalPredictionReady!==false||
        check.resultComparisonReady!==false||
        check.bettingReady!==false||check.autoPurchase!==false||
        check.actualPurchase!==false)
      throw Error('研究79点下書きの署名検証失敗');
     r6Message=saveResearch6DraftReceipts(receipts,day);
    }else r6Message='発走前の新79点3連単は固定対象なし。発走後に追加しません。';
   }catch(_){
    r6Message='新79点下書きの署名検証または端末保存に失敗。過去の固定記録は変更していません。';
   }
  }
  showSavedResearch6Drafts(day);
  $('autoResearch6DraftSaveStatus').textContent=r6Message;
  // A completely separate HMAC domain for bounded recent-unknown
  // *research observations*. A signature attests capture time only.
  // Verify server HMAC before local first-write. No purchase/ROI.
  if(raw.sparseFiveCapture!==undefined){
   try{
    const entries=validateSparseResearchCapture(
     raw.sparseFiveCapture,sparseFive,day);
    if(entries.length){
     const body=JSON.stringify({date:day,receipts:entries});
     if(body.length>250000)throw Error('研究記録の検証サイズ超過');
     const reply=await fetch('/api/owner-sparse-five-verify',{
      method:'POST',credentials:'same-origin',cache:'no-store',
      headers:{'X-Keiba-Request':'private','Content-Type':'application/json',
       'Accept':'application/json'},body
     });
     const checked=await reply.json();
     if(seq!==historySeq||historyDay!==day)return;
     if(!reply.ok||checked.version!=='owner-sparse-five-verify-1'||
        checked.serverSigned!==true||checked.recordCount!==entries.length||
        checked.researchOnly!==true||checked.privateOwnerOnly!==true||
        checked.officialJraVerified!==false||
        checked.formalPredictionReady!==false||
        checked.resultComparisonReady!==false||
        checked.bettingReady!==false||checked.actualPurchase!==false||
        checked.newProviderReads!==0)
      throw Error('研究例の署名検証失敗');
    }
    $('autoFiveSparseSavedStatus').textContent=
     saveSparseResearchOnce(entries,day);
   }catch(_){
    $('autoFiveSparseSavedStatus').textContent=
     '近走未評価研究例の署名検証または保存が失敗。以前の記録を変更していません。';
   }
  }
  renderSavedSparse(day);
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
   // One-screen summary after the owner explicitly opts into history reads.
   // Unassessed horses are NEVER sorted below known scores.
   if(details.rosterVerified&&details.fiveCore){
    const core=details.fiveCore,head=core.comparisonGroups.slice(0,3);
    const groups=head.map(g=>g.numbers.map(n=>n+'番').join('＝')+
     '（'+(g.rawThirdPoints/3).toFixed(2)+'/85）');
    const line=groups.length?
     '研究85点比較（上位最大3グループ・同点並列）｜'+groups.join(' ＞ ')+
     (core.comparisonGroups.length>3?' ほかは詳細欄':''):
     '研究85点比較｜5項目がそろう馬は0頭';
    card.append(dom('p',line+'。未評価 '+core.unassessedNumbers.length+
     '頭（順位付けしない）。正式な良い馬順・勝率・買い目ではありません。','muted'));
   }
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
   if(details.rosterVerified&&details.threeCore){
    const core=details.threeCore,trial=dom('details');
    trial.append(dom('summary','重点3項目の研究用70点を見る（正式採点0/10）'));
    trial.append(dom('p','調教30・コース距離20・展開20。過去実績と過去4角による未検証の比較で、総合100点・勝率・正式順位ではありません。1項目でも不足した馬は点数を出しません。3連単と保存記録は変更しません。','muted'));
    trial.append(dom('p','3項目とも研究目安がある馬 '+core.completeCoreObserved+
     '/'+core.runnerCount+'頭。いずれも正式な採点項目としては未承認。','muted'));
    for(const horse of core.horses){
     const b=horse.bands;
     trial.append(dom('p',horse.number+'番｜調教 '+b.training+
      '／コース '+b.course_distance+'／展開 '+b.pace+
      '｜研究用'+(horse.evidenceScore70===null?'未評価':
        ' '+horse.evidenceScore70.toFixed(2)+'/70点')+
      '（正式100点ではありません）','muted'));
    }
    card.append(trial);
   }
   if(details.rosterVerified&&details.fourCore){
    const core=details.fourCore,trial=dom('details');
    trial.append(dom('summary','重点4項目の研究用82点を見る（馬場12点追加・正式採点0/10）'));
    trial.append(dom('p','調教30・コース距離20・展開20・馬場12。過去の馬場別好走を使った未検証の比較です。重・不良への実戦対応能力やJRA公式確認、総合100点、勝率、正式順位ではありません。馬場資料を含め4項目全部そろった馬だけ点数を表示。3連単と固定70点は変更しません。','muted'));
    trial.append(dom('p','4項目の研究帯がそろう馬 '+core.completeObserved+
     '/'+core.runnerCount+'頭。根拠の未確認は0点やCではなく未評価。','muted'));
    for(const horse of core.horses){
     const b=horse.bands;
     trial.append(dom('p',horse.number+'番｜調教 '+b.training+
      '／コース '+b.course_distance+'／展開 '+b.pace+
      '／馬場 '+b.ground+'｜研究用'+(horse.evidenceScore82===null?
       '未評価':' '+horse.evidenceScore82.toFixed(2)+'/82点')+
      '（正式100点ではありません）','muted'));
    }
    card.append(trial);
   }
   if(details.rosterVerified&&details.fiveCore){
    const core=details.fiveCore,panel=dom('details');
    panel.append(dom('summary','重点5項目の研究用85点を見る（近走3点追加・正式採点0/10）'));
    panel.append(dom('p','調教30・近走3・コース距離20・展開20・馬場12。近走の最大影響は3点だけ。過去走・馬場・位置取りから作った未検証の比較で、正式100点、勝率、馬券の順位ではありません。5項目のうち1つでも未評価なら85点も未評価。3連単と固定70点は変更しません。','muted'));
    panel.append(dom('p','5項目の研究帯がそろう馬 '+core.completeObserved+
      '/'+core.runnerCount+'頭。残る15点は血統8・枠斤量3・騎手厩舎2・ローテ1・当日馬体重1。これらは未採点。','muted'));
    for(const horse of core.horses){
     const b=horse.bands;
     panel.append(dom('p',horse.number+'番｜調教 '+b.training+
       '／近走 '+b.recent+'／コース '+b.course_distance+
       '／展開 '+b.pace+'／馬場 '+b.ground+
       '｜研究用'+(horse.evidenceScore85===null?
        '未評価':' '+horse.evidenceScore85.toFixed(2)+'/85点')+
       '（正式100点ではありません）','muted'));
    }
    const order=dom('details');
    order.append(dom('summary','研究用85点の比較順（同点並列・正式順位ではない）'));
    order.append(dom('p','5項目の研究値がそろう馬だけ比較。同点は並列・未評価は除外。正式な良い馬順・勝率・馬券とは別です。','muted'));
    if(core.comparisonGroups.length){
     for(const group of core.comparisonGroups){
      order.append(dom('p',group.numbers.map(n=>n+'番').join('・')+
       '｜研究比較値 '+(group.rawThirdPoints/3).toFixed(2)+'/85点'+
       (group.numbers.length>1?'（同点・順不同）':'')+
       '（勝率ではありません）','muted'));
     }
    }else order.append(dom('p','全5項目がそろう馬は0頭。比較順は付けられません。','muted'));
    if(core.unassessedNumbers.length){
     order.append(dom('p','未評価・比較順から除外：'+
      core.unassessedNumbers.map(n=>n+'番').join('・')+
      '（弱い馬・C判定を意味しません）','muted'));
    }
    panel.append(order);
    card.append(panel);
   }
   if(details.rosterVerified&&details.newWeightFive){
    const fresh=details.newWeightFive,group=fresh.comparisonGroups.slice(0,3);
    const compare=group.length?group.map(g=>
     g.numbers.map(n=>n+'番').join('＝')+
      '（'+(g.rawThirdPoints/3).toFixed(2)+'/79）').join(' ＞ '):
     '全5項目を観測できた馬なし';
    card.append(dom('p','新配点79点研究比較｜'+compare+
      '。未評価 '+fresh.unassessedNumbers.length+
      '頭。research-6の5項目だけを旧85点と同じ資料から再配点。'+
      '正式100点の総合評価・予想順位・買い目ではありません。','muted'));
    const panel=dom('details');
    panel.append(dom('summary','新配点5項目79点の研究比較（正式100点とは別）'));
    panel.append(dom('p','コース17点＋展開17点、馬場12点の研究参考得点を同じ履歴から機械計算。'+
      '資料が足りない馬は未算出。現在のJRA公式馬場の適性を実証した得点ではありません。','muted'));
    panel.append(dom('p','調教30／近走3／コース距離17／展開脚質17／馬場12＝79。'+
      '未確認項目は0点やCにしません。旧70・82・85点の署名記録、'+
      '3連単、回収率は変更しません。','muted'));
    panel.append(dom('p','観測がそろう馬 '+fresh.completeObserved+
      '/'+fresh.runnerCount+'頭。残り21点分の評価とJRA公式の独立照合は未完了。','muted'));
    for(const horse of fresh.horses){
     const b=horse.bands;
     panel.append(dom('p',horse.number+'番｜調教 '+b.training+
      '／近走 '+b.recent+'／コース '+b.course_distance+
      '／展開 '+b.pace+'／馬場 '+b.ground+
      '｜コース17＋展開17の研究参考値 '+
      (horse.coursePaceEvidenceScore34===null?'未算出':
       horse.coursePaceEvidenceScore34.toFixed(2)+'/34点')+
      '｜馬場の研究参考値 '+
      (horse.goingEvidenceScore12===null?'未算出':
       horse.goingEvidenceScore12.toFixed(2)+'/12点')+
      '｜5項目研究用'+(horse.evidenceScore79===null?'未評価':
      ' '+horse.evidenceScore79.toFixed(2)+'/79点')+
      '（いずれも未検証の歴史的仮説で、正式な適性・予想得点ではありません）','muted'));
    }
    card.append(panel);
   }
   if(details.rosterVerified&&details.threeFactorSourceGaps){
    const s=details.threeFactorSourceGaps,p=dom('details'),
     labels={course_distance:'コース・距離',pace:'展開・脚質',ground:'馬場'};
    p.append(dom('summary','コース17・展開17・馬場12：採点前の資料不足を確認'));
    p.append(dom('p','46点分の過去資料を照合。馬番別に資料の充足を配点相当で表示しますが、'+
     'これは能力点・予想順位・1着候補ではありません。JRA公式照合、発走前時刻の確認、'+
     '時系列の未使用期間テスト、採点基準の校正が未完成です。','muted'));
    p.append(dom('p','3項目の資料がそろった馬 '+
     s.observed.allThreeSourcesObserved+'/'+s.runnerCount+
     '頭／コース履歴 '+s.observed.courseComparableObserved+
     '頭／馬場一致履歴 '+s.observed.sameGoingObserved+
     '頭／展開仮説 '+s.observed.paceScenarioObserved+
     '頭（正式採点0/3）','muted'));
    p.append(dom('p','研究用の最低3走の同条件サンプルを満たす馬 '+
     s.minimumSampleCoverage.allThreeMinimumStudySamples+'/'+s.runnerCount+
     '頭。これは正式適性判定ではなく、結果の公表時刻・独立資料元・'+
     '未使用期間の精度検証も未完了です。','muted'));
    const reasons={
     course_history_incomplete:'過去出走の照合が未完了',
     course_sample_below_three:'同コース距離の比較が3走未満',
     current_going_not_recorded:'当日馬場の資料なし',
     same_going_sample_below_three:'同じ馬場の比較が3走未満',
     pace_scenario_unobserved:'位置取りの仮説が不足'
    };
    for(const h0 of s.runners){
     const missing=h0.missingSourceFactors.length?
      h0.missingSourceFactors.map(k=>labels[k]).join('・'):'対象資料は確認済み';
     const factorWeights={course_distance:17,pace:17,ground:12};
     const sourceCovered=Object.keys(labels).reduce((sum,key)=>
      sum+(h0.sourcePresent[key]?factorWeights[key]:0),0);
     const sampleCovered=Object.keys(labels).reduce((sum,key)=>
      sum+(h0.minimumStudySamples[key]?factorWeights[key]:0),0);
     const priorityMissing=Object.keys(labels)
      .filter(key=>!h0.minimumStudySamples[key])
      .sort((a,b)=>factorWeights[b]-factorWeights[a])
      .map(key=>labels[key]+factorWeights[key]+'点');
     p.append(dom('p',h0.number+'番｜コース・距離 '+
      (h0.sourcePresent.course_distance?'資料あり':'不足')+
      '／展開・脚質 '+(h0.sourcePresent.pace?'資料あり':'不足')+
      '／馬場 '+(h0.sourcePresent.ground?'資料あり':'不足')+
      '｜不足：'+missing+
      '｜資料確認の配点相当 '+sourceCovered+'/46（能力点ではない）'+
      '｜研究用最低サンプル確認相当 '+sampleCovered+'/46（採点ではない）'+
      '｜次に確認：'+(priorityMissing.length?
       priorityMissing.join('・'):'最低資料件数は確認済み（正式採点は未評価）')+
      '｜最低サンプル '+(h0.allThreeStudySamplesMet?'3項目達成':'未充足')+
      '｜追加確認：'+(h0.sampleGaps.length?
        h0.sampleGaps.map(k=>reasons[k]).join('・'):'比較件数は確認済み')+
      '｜正式46点：未評価','muted'));
    }
    card.append(p);
   }
   if(details.rosterVerified&&details.remaining21){
    const r=details.remaining21,panel=dom('details');
    panel.append(dom('summary','新配点：残り21点の資料不足を馬番別に確認'));
    panel.append(dom('p','新配点の残り21点＝血統6・枠斤量3・騎手厩舎10'+
     '・ローテ1・当日馬体重1。資料の有無だけを表示します。'+
     '能力評価・正式100点・買い目ではありません。','muted'));
    panel.append(dom('p','前日4項目の資料がすべてある馬 '+
     r.priorSourceFourCompleteCount+'/'+r.runnerCount+
     '頭。新79点研究がそろう馬 '+r.research79ObservedCount+'/'+r.runnerCount+
     '頭。馬体重1点と全10項目の正式能力評価は未完了。','muted'));
    panel.append(dom('p','血統6点・騎手厩舎10点の採点前チェック：父と母父の基本資料 '+
     r.pedigreeParentageCompleteCount+'/'+r.runnerCount+
     '頭、騎手・厩舎の基本資料 '+r.staffIdentityCompleteCount+'/'+r.runnerCount+
     '頭、両方そろう馬 '+r.bothPedigreeStaffCompleteCount+'/'+r.runnerCount+
     '頭。16点の正式採点は0点分（未評価）。名前だけでは評価しません。','muted'));
    const names={pedigree:'血統',draw_weight:'枠斤量',
     jockey_stable:'騎手厩舎',rotation:'ローテ',body_condition:'当日馬体重'};
    for(const horse of r.horses){
     panel.append(dom('p',horse.number+'番｜新79点研究 '+
      (horse.research79Observed?horse.research79.toFixed(2)+'/79':'未評価')+
      '｜残り21点の資料カバー配点相当 '+
      horse.sourceFieldCoverageEquivalent21+'/21（得点ではない）'+
      '｜血統＋騎手厩舎の基本資料 '+
      horse.pedigreeStaffSourceCoverage16+'/16（能力点ではない）'+
      '｜資料不足：'+horse.missingSourceFields.map(k=>names[k]).join('・')+
      '｜全10項目の正式採点は未評価','muted'));
    }
    panel.append(dom('p','次に必要：血統別同条件実績、枠と斤量の検証、'+
     '騎手・厩舎の条件別成績、ローテの時系列比較、当日馬体重、'+
     'JRA公式出走・取消・馬場・発走時刻の独立照合。'+
     '既存の署名記録と収支は変更しません。','muted'));
    card.append(panel);
   }
   if(details.rosterVerified&&details.research6Uncertainty){
    const r=details.research6Uncertainty,p=dom('details');
    p.append(dom('summary','新配点100点・未評価項目による順位変動シミュレーション'));
    p.append(dom('p','注意：5項目のS/A/B/Cも未検証。全馬の残り21点は'+
      '未評価（騎手・厩舎だけで10点）。下記はS～Cを仮置きした'+
      '数学的な幅で、正式100点の採点・勝率・予想順位・買い目ではありません。','muted'));
    p.append(dom('p','未評価の影響を含めても研究帯で算術的に優位な'+
      '組み合わせ '+r.strictAdvantagePairCount+'組。'+
      'この件数は実際の1着候補や有利不利の証明ではありません。','muted'));
    for(const h0 of r.horses){
     p.append(dom('p',h0.number+'番｜研究用の100点仮定幅 '+
      h0.lowerResearchBound.toFixed(2)+'～'+
      h0.upperResearchBound.toFixed(2)+
      '｜未評価幅 '+h0.unassessedTotalWeight+
      '点（騎手厩舎10点含む）'+
      '｜研究順位の可能性 '+h0.researchPossibleBestRank+
      '～'+h0.researchPossibleWorstRank+
      '位｜正式評価：未評価','muted'));
    }
    card.append(p);
   }
   if(details.rosterVerified&&details.research6FiveDraft){
    const draft=details.research6FiveDraft,p=dom('details');
    p.append(dom('summary','新配点79点から作る3連単研究用下書き（正式予想ではない）'));
    p.append(dom('p','調教30・近走3・コース17・展開17・馬場12の'+
      '仮説的な比較のみ。血統6・枠斤量3・騎手厩舎10・ローテ1・'+
      '当日馬体重1は未評価。JRA公式出走馬・取消・馬場・発走時刻も'+
      '未照合で、購入推奨や正式100点予想ではありません。','muted'));
    if(draft.status==='five_factor_research_draft'){
     p.append(dom('p','1着 '+draft.first.join('・')+
      '／2着 '+draft.second.join('・')+
      '／3着 '+draft.third.join('・')+
      '｜'+draft.points+'点・100円換算 '+draft.amountYen.toLocaleString()+
      '円（未購入・署名保存なし）','muted'));
     const all=dom('details');
     all.append(dom('summary','3連単の研究用組み合わせ '+draft.points+'点'));
     all.append(dom('p',draft.tickets.map(t=>t.join('→')).join('　'),'muted'));
     p.append(all);
    }else{
     const descriptions={
      missing_provisional_off:'暫定発走時刻がない',
      past_provisional_off:'暫定発走時刻を過ぎた',
      runner_count_unconfirmed:'JRDB番組の頭数と一致しない',
      too_few_runners:'出走馬が4頭未満',
      incomplete_five_factors:'5項目が全頭そろっていない',
      tied_cutoff:'同点境界で候補を安全に区切れない'
     };
     p.append(dom('p','研究用買い目は保留：'+
      descriptions[draft.reason]+'。未評価の馬を0点扱いして'+
      '無理に点数を作りません。','muted'));
    }
    card.append(p);
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
    const remainingWeights={
     pedigree:6,draw_weight:3,jockey_stable:10,rotation:1,body_condition:1
    };
    const shortNames={
     pedigree:'血統',draw_weight:'枠斤量',jockey_stable:'騎手厩舎',
     rotation:'ローテ',body_condition:'当日馬体重'
    };
    const isCovered=(key,status)=>key==='rotation'?status!=='unknown':
     key==='body_condition'?false:status==='complete_fields_observed';
    let fourSourceReady=0;
    for(const horse of details.tenInventory.runners){
     const v=horse.sourceStates;
     const covered=Object.keys(remainingWeights).filter(k=>isCovered(k,v[k]));
     const coveredWeight=covered.reduce((total,k)=>total+remainingWeights[k],0);
     const missing=Object.keys(remainingWeights).filter(k=>!covered.includes(k));
     if(covered.length===4)fourSourceReady++;
     ten.append(dom('p',horse.number+'番｜血統 '+names[v.pedigree]+
      '／枠斤量 '+names[v.draw_weight]+
      '／騎手厩舎 '+names[v.jockey_stable]+
      '／ローテ '+names[v.rotation]+
      '／馬体重 '+names[v.body_condition]+
      '｜資料カバー配点相当 '+coveredWeight+'/21（実得点ではない）'+
      '｜不足 '+missing.map(k=>shortNames[k]).join('・')+
      '（正式採点0/10）','muted'));
    }
    ten.append(dom('p','正式100点の残り21点の資料準備：前日4分野の資料が全部そろう馬 '+
     fourSourceReady+'/'+details.tenInventory.runnerCount+
     '頭。当日馬体重は未取得なので資料カバーは最大20/21。'+
     '資料カバー配点は能力点・予想スコア・S/A/B/Cではありません。','muted'));
    card.append(ten);
   }
   if(details.rosterVerified&&details.pedigreePreflight){
    const p=details.pedigreePreflight,panel=dom('details');
    panel.append(dom('summary','血統の資料確認（旧方式8点／現行100点配分は6点）'));
    panel.append(dom('p','父・母父が分かるだけではコース・距離・馬場適性は判定できません。血統別の独立した過去実績と未来情報を除いた期間検証が必要です。今は血統S/A/B/Cも現行6点の実得点も付けません。','muted'));
    panel.append(dom('p','父・母父の資料が両方ある馬 '+
     p.parentageCompleteCount+'/'+p.runnerCount+
     '頭。血統の能力評価まで確認できた馬 0/'+p.runnerCount+'頭。','muted'));
    for(const horse of p.horses){
     const state=horse.parentageComplete?'両方あり':
      horse.parentageSourceState==='partial_fields_observed'?'一部不足':'両方不足';
     panel.append(dom('p',horse.number+'番｜父・母父 '+state+
      '／同条件の血統実績 未接続／時系列検証 未実施'+
      '／血統6点 未評価（予想には反映しません）','muted'));
    }
    card.append(panel);
   }
   if(details.rosterVerified&&details.supportSixPreflight){
    const p=details.supportSixPreflight,panel=dom('details');
    panel.append(dom('summary','枠斤量・騎手厩舎・ローテの資料（旧6点／現行14点）'));
    panel.append(dom('p','現行100点配分は枠斤量3・騎手厩舎10・ローテ1。旧方式の研究資料を使い、今は資料があるかだけを確認。同条件の有利不利や成績差・休み明け適性の検証は未完成で、資料が全部あっても実得点は0点ではなく未評価です。','muted'));
    panel.append(dom('p','3項目とも資料がそろう馬 '+
     p.allThreeFieldCompleteCount+'/'+p.runnerCount+
     '頭。能力評価を検証できた馬 0/'+p.runnerCount+'頭。','muted'));
    const explain={
     complete_fields_observed:'資料あり',
     partial_fields_observed:'一部不足',
     no_fields_observed:'資料不足',
     under14Days:'中13日以内',
     days14to55:'中14〜55日',
     days56plus:'中56日以上',
     unknown:'間隔不明'
    };
    for(const h of p.horses){
     const currentWeights={draw_weight:3,jockey_stable:10,rotation:1};
     const currentCovered=Object.keys(currentWeights).reduce((sum,key)=>sum+
      ((key==='rotation'?h.sourceStates[key]!=='unknown':
       h.sourceStates[key]==='complete_fields_observed')?
       currentWeights[key]:0),0);
     panel.append(dom('p',h.number+'番｜枠斤量 '+explain[h.sourceStates.draw_weight]+
      '／騎手厩舎 '+explain[h.sourceStates.jockey_stable]+
      '／ローテ '+explain[h.sourceStates.rotation]+
      '｜現行配点の資料カバー相当 '+currentCovered+'/14（実得点ではない）'+
      '｜正式14点 未評価（3項目とも能力判定なし）','muted'));
    }
    card.append(panel);
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
  fiveQuickReadDay=day;
  renderSparseFiveReference(sparseFive,day);
  renderSavedSparse(day);
  // The HMAC verification and first-write snapshot happened above.
  // Date changes invalidate every in-flight study. The visible list is
  // strictly the locally frozen snapshot, not raw provider data.
  renderFiveQuickSaved(day,true);
  $('autoHistoryAuditStatus').textContent='過去番組の追加照合 '+raw.draCalls+
   '回／馬場 '+raw.dkaCalls+'回。未取得の過去レース '+raw.deferredPastRaces+
   '件。'+(raw.historyComplete?'指定範囲を照合済み。':'履歴に未確認あり。')+
   ' 予想・購入・保存済みの買い目は変更しません。';
 }catch(_){if(seq===historySeq){
  $('autoHistoryAuditRaces').replaceChildren();
  renderSparseFiveReference(null,day);
  $('autoHistoryStaffStatus').textContent=
   '騎手・厩舎の資料確認に失敗。既存の買い目や成績は変更していません。';
  $('autoHistoryAuditStatus').textContent=
   '過去資料の照合ができません。履歴機能の設定・資料形式を確認してください。'+
   '予想と固定済みの買い目は変更していません。';
  renderFiveQuickSaved(day);
  $('autoFiveQuickStatus').textContent=
   'JRDBの5項目追加照合を完了できませんでした。新しい79点買い目は作成せず、以前の固定記録は変更していません。';
 }}finally{if(seq===historySeq&&day===historyDay)button.disabled=false;}
};
// Prominent one-tap path to the EXISTING bounded owner-history pipeline.
// No automatic paid history access on page open, after off, or navigation.
$('autoFiveQuick').onclick=async()=>{
 const button=$('autoFiveQuick'),day=$('autoDay').value.replaceAll('-','');
 if(button.disabled||!/^20[0-9]{6}$/.test(day))return;
 if(fiveQuickReadDay===day){
  renderFiveQuickSaved(day,true);
  $('autoFiveQuickStatus').textContent+='（この画面では追加JRDB照会0回）';
  return;
 }
 if($('autoHistoryAudit').disabled||historyDay!==day){
  $('autoFiveQuickStatus').textContent=
   '基本資料を取得してから5項目の追加分析を実行できます。追加照会は0回。';
  return;
 }
 // The staff beta checkbox adds 2-6 paid reads. This path advertises a
 // strict 16-read cap; never silently opt the owner into the higher cost.
 if($('autoHistoryStaffSample').checked===true){
  $('autoFiveQuickStatus').textContent=
   '騎手・厩舎の追加照合が選択されています。最大16回に収めるにはチェックを外してください。今回は追加照会0回。';
  return;
 }
 button.disabled=true;
 $('autoFiveQuickStatus').textContent='本人操作によりJRDB過去番組・馬場を最大16回照合中…';
 try{
  await $('autoHistoryAudit').onclick();
  if(day!==$('autoDay').value.replaceAll('-',''))return;
  if(fiveQuickReadDay===day){
   const count=renderFiveQuickSaved(day,true);
   $('autoFiveQuickStatus').textContent=
    '5項目の過去照合完了。発走前の署名付き初回固定 '+count+
    'R。資料不足や同点・発走済みは新規保存しません。'+
    '正式10項目、JRA公式照合、実購入とは別です。';
  }else $('autoFiveQuickStatus').textContent=
   '5項目の追加照合を完了できませんでした。以前の固定買い目は変更していません。';
 }finally{
  if(day===$('autoDay').value.replaceAll('-',''))button.disabled=false;
 }
};
// A one-time, explicit iPhone opt-in to a *single* bounded history
// comparison when the authenticated owner page is opened on a normal
// Saturday/Sunday before at least one provisional off. Never a background
// fetch, never a scheduler, never a pre-authorization of horse purchases.
function fiveWeekendConsent(){
 try{return localStorage.getItem(AUTO_FIVE_CONSENT_KEY)==='enabled';}
 catch(_){return false;}
}
function fiveWeekendAlreadyAttempted(day){
 try{return localStorage.getItem(AUTO_FIVE_ONCE_KEY)===day;}
 catch(_){return true;} // Storage unavailable -> no automatic paid calls.
}
function markFiveWeekendAttempt(day){
 try{
  localStorage.setItem(AUTO_FIVE_ONCE_KEY,day);
  return localStorage.getItem(AUTO_FIVE_ONCE_KEY)===day;
 }catch(_){return false;}
}
function maybeAutoFiveFromBasic(body,day){
 if(!fiveWeekendConsent()||$('autoFiveWeekendOptIn').checked!==true)return;
 const date=jstToday().replaceAll('-',''),
  weekendDay=new Date(day.slice(0,4)+'-'+day.slice(4,6)+'-'+
   day.slice(6,8)+'T12:00:00Z');
 if(day!==date||Number.isNaN(weekendDay.valueOf())||
    ![0,6].includes(weekendDay.getUTCDay())||
    !body||body.date!==day||!Array.isArray(body.races)||
    body.raceCount!==body.races.length||body.raceCount===0||
    historyDay!==day||$('autoHistoryAudit').disabled||
    $('autoFiveQuick').disabled)return;
 if(fiveWeekendAlreadyAttempted(day)){
  $('autoFiveWeekendStatus').textContent=
   'この端末で本日分の自動追加分析は既に開始済み（再実行0回）。結果は上の保存済み買い目で確認。必要なら手動で再分析できます。';
  return;
 }
 if(!body.races.some(r=>typeof r.postTime==='string'&&
                        !draftExpiredOnDevice(day,r.postTime))){
  $('autoFiveWeekendStatus').textContent=
   '対象日の発走前レースがないため5項目の自動追加照会0回。過去の買い目は変更しません。';
  return;
 }
 // A staff opt-in can add 2-6 more billable API reads; it never belongs
 // in this strictly capped automatic 16-read history workflow.
 if($('autoHistoryStaffSample').checked===true){
  $('autoFiveWeekendStatus').textContent=
   '騎手・厩舎の追加照合がONのため、最大16回を超えないよう自動実行は中止。追加照会0回。';
  return;
 }
 // First-write the attempt marker BEFORE the first payable provider call.
 // If local persistence fails, no hidden paid query is permitted.
 if(!markFiveWeekendAttempt(day)){
  $('autoFiveWeekendStatus').textContent=
   '端末に当日1回の実行記録を保存できず、自動追加照会を中止。必要なら手動実行してください。';
  return;
 }
 $('autoFiveWeekendStatus').textContent=
  '本人が許可した土日当日の5項目照合を実行中（JRDB追加最大16回・自動再試行なし）…';
 // The same one-tap path and HMAC first-write validation as manual use.
 // The marker remains even on failure to prevent accidental repeat billing.
 void $('autoFiveQuick').onclick().then(()=>{
  if(day!==$('autoDay').value.replaceAll('-',''))return;
  $('autoFiveWeekendStatus').textContent=fiveQuickReadDay===day
   ?'本日分の5項目研究の自動追加照合を1回実行済み。発走前の保存済み買い目は上に表示。正式予想ではありません。'
   :'本日分の自動追加照合を1回試行しましたが完了を確認できません。自動再試行はせず、以前の記録を維持。';
 }).catch(()=>{
  if(day===$('autoDay').value.replaceAll('-',''))
   $('autoFiveWeekendStatus').textContent=
    '5項目の自動照合でエラー。再照会を防ぐため今日は自動再試行しません。';
 });
}
$('autoFiveWeekendOptIn').checked=fiveWeekendConsent();
$('autoFiveWeekendStatus').textContent=fiveWeekendConsent()
 ?'自動追加分析ON：通常の土日当日、本人用アプリを開いた時のみ最大16回の追加JRDB照会。'
 :'自動追加分析OFF：許可するまで5項目の追加JRDB照会は自動実行しません。';
$('autoFiveWeekendOptIn').onchange=()=>{
 const enabled=$('autoFiveWeekendOptIn').checked===true;
 try{
  if(enabled)localStorage.setItem(AUTO_FIVE_CONSENT_KEY,'enabled');
  else localStorage.removeItem(AUTO_FIVE_CONSENT_KEY);
  if(fiveWeekendConsent()!==enabled)throw Error('opt_in_write_failed');
  $('autoFiveWeekendStatus').textContent=enabled
   ?'自動追加分析を許可しました。当日分の基本データがあれば発走前に1回だけ実行します。'
   :'自動追加分析をOFFにしました。新しい自動JRDB履歴照会は行いません。';
  if(enabled&&latestDisplayedDay===$('autoDay').value.replaceAll('-','')&&
     latestDisplayedReport)
   maybeAutoFiveFromBasic(latestDisplayedReport,latestDisplayedDay);
 }catch(_){
  $('autoFiveWeekendOptIn').checked=false;
  $('autoFiveWeekendStatus').textContent=
   '自動設定を保存できませんでした。安全のため自動JRDB履歴照会はOFF。';
 }
};
// Never use source count alone to grade body condition or change a ticket.
function validateMainWorkoutEvidence(raw,day){
 const eligible=historyCoordinates;
 if(!raw||raw.version!=='owner-main-workout-tch-evidence-1'||
    raw.date!==day||raw.raceCount!==eligible.size||
    !Array.isArray(raw.races)||raw.races.length!==eligible.size||
    raw.sourceFamily!=='jrdb_tch_owner_prestart'||
    !Array.isArray(raw.sourceRequestsRequired)||
    raw.sourceRequestsRequired.join('|')!=='tra|tky|tch'||
    raw.researchOnly!==true||raw.privateOwnerOnly!==true||
    raw.horseIdsIncluded!==false||raw.rawWorkoutValuesIncluded!==false||
    raw.oddsUsed!==false||raw.officialJraVerified!==false||
    raw.modelCalibrated!==false||raw.trainingGradeReady!==false||
    raw.overallPredictionReady!==false||raw.bettingReady!==false||
    raw.actualPurchase!==false||raw.changesExistingTickets!==false||
    raw.changesExistingReceipts!==false||raw.changesExistingRoi!==false||
    raw.additionalPaidReadsAfterSource!==0||
    !raw.summary||typeof raw.summary!=='object')
  throw Error('本追切の資料契約に不整合');
 const sums={workoutRows:0,runnersWithWorkout:0,
    runnersWithRecentWorkout:0,runnersWithIndex:0,
    runnersWithDatedIndexTime:0},seen=new Set();
 for(const r of raw.races){
  const id=r?.track+'|'+r?.race;
  if(!eligible.has(id)||seen.has(id)||
     !Number.isInteger(r.registered)||r.registered<0||r.registered>18||
     !Number.isInteger(r.sourceWorkoutRows)||r.sourceWorkoutRows<0||
     r.sourceWorkoutRows>r.registered*30||
     !Array.isArray(r.runners)||r.runners.length!==r.registered||
     r.workoutIndexCalibrated!==false||r.officialJraVerified!==false||
     r.trainingGradeReady!==false||r.trifectaReady!==false)
   throw Error('本追切のレース番号が不正');
  seen.add(id);
  const counts={runnersWithWorkout:0,runnersWithRecentWorkout:0,
                runnersWithIndex:0,runnersWithFinalTime:0,
                runnersWithDatedIndexTime:0};
  const numbers=new Set();
  for(const h of r.runners){
   if(!h||Object.keys(h).length!==10||
      !Number.isInteger(h.number)||h.number<1||h.number>18||
      numbers.has(h.number)||h.trainingGrade!=='未評価'||
      h.trainingScore30!==null||h.modelCalibrated!==false||
      ['mainWorkoutsRecorded','datedWorkoutRecorded',
       'withinSevenDaysRecorded','mainIndexRecorded',
       'finalTimeRecorded','datedIndexTimePairRecorded']
      .some(k=>typeof h[k]!=='boolean')||
      (h.datedWorkoutRecorded&&!h.mainWorkoutsRecorded)||
      (h.withinSevenDaysRecorded&&!h.datedWorkoutRecorded)||
      ((h.mainIndexRecorded||h.finalTimeRecorded)&&
        !h.mainWorkoutsRecorded)||
      (h.datedIndexTimePairRecorded&&
       !(h.datedWorkoutRecorded&&h.mainIndexRecorded&&h.finalTimeRecorded)))
    throw Error('本追切の馬番と観測状態が不正');
   numbers.add(h.number);
   counts.runnersWithWorkout+=Number(h.mainWorkoutsRecorded);
   counts.runnersWithRecentWorkout+=Number(h.withinSevenDaysRecorded);
   counts.runnersWithIndex+=Number(h.mainIndexRecorded);
   counts.runnersWithFinalTime+=Number(h.finalTimeRecorded);
   counts.runnersWithDatedIndexTime+=Number(h.datedIndexTimePairRecorded);
  }
  if(Object.keys(counts).some(k=>r[k]!==counts[k])||
     r.sourceWorkoutRows<r.runnersWithWorkout)
   throw Error('本追切の頭数合計が不正');
  for(const k of Object.keys(sums))
   sums[k]+=k==='workoutRows'?r.sourceWorkoutRows:r[k];
 }
 if(seen.size!==eligible.size||
    Object.keys(sums).some(k=>raw.summary[k]!==sums[k]))
  throw Error('本追切の全R合計が不一致');
 return raw.races;
}
$('autoMainWorkoutCheck').onclick=async()=>{
 const btn=$('autoMainWorkoutCheck'),day=$('autoDay').value.replaceAll('-','');
 if(btn.disabled)return;
 if(historyDay!==day||!/^20[0-9]{6}$/.test(day)){
  $('autoMainWorkoutStatus').textContent=
   '開催日の基本資料を確認してから実行してください。追加JRDB照会0回。';
  return;
 }
 const seq=++tchStudySeq;
 btn.disabled=true;
 $('autoMainWorkoutRaces').replaceChildren();
 $('autoMainWorkoutStatus').textContent=
  '本人操作でJRDB本追切を照合中（番組・出走馬・本追切の最大3照会）…';
 try{
  const reply=await fetch('/api/jrdb/main-workout-evidence?date='+
    encodeURIComponent(day),{credentials:'same-origin',cache:'no-store',
      headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
  const data=await reply.json();
  if(seq!==tchStudySeq||day!==$('autoDay').value.replaceAll('-',''))return;
  if(!reply.ok)throw Error('本追切の追加資料が利用できません');
  const races=validateMainWorkoutEvidence(data,day);
  for(const r of races){
   $('autoMainWorkoutRaces').append(dom('p',
    r.track+' '+r.race+'R｜本追切 '+r.runnersWithWorkout+'/'+r.registered+
    '頭／7日以内 '+r.runnersWithRecentWorkout+
    '頭／追切指数 '+r.runnersWithIndex+
    '頭／日付・指数・終いが揃う '+r.runnersWithDatedIndexTime+
    '頭（調教30点は未評価）','muted'));
  }
  $('autoMainWorkoutStatus').textContent=
   '本追切を'+data.raceCount+'R照合。記録あり '+
   data.summary.runnersWithWorkout+'頭／追切指数あり '+
   data.summary.runnersWithIndex+'頭。資料取得は予想採点ではなく、'+
   'JRA公式未照合。買い目・保存履歴・回収率は変更していません。';
 }catch(_){
  if(seq===tchStudySeq){
   $('autoMainWorkoutRaces').replaceChildren();
   $('autoMainWorkoutStatus').textContent=
    '本追切資料の確認は保留。本人専用のJRDB接続・当日発走前・資料形式を確認。'+
    '買い目・保存・回収率は無変更です。';
  }
 }finally{if(seq===tchStudySeq)btn.disabled=false;}
};
function validateTrainingCrosscheck(raw,day){
 if(!raw||raw.version!=='owner-training-tcy-tch-crosscheck-1'||
    raw.date!==day||raw.raceCount!==historyCoordinates.size||
    !Array.isArray(raw.races)||raw.races.length!==historyCoordinates.size||
    !raw.summary||typeof raw.summary!=='object'||
    !Array.isArray(raw.sourceRequestsRequired)||
    raw.sourceRequestsRequired.join('|')!=='tra|tky|tcy|tch'||
    raw.researchOnly!==true||raw.privateOwnerOnly!==true||
    raw.rawWorkoutValuesIncluded!==false||
    raw.horseIdentifiersIncluded!==false||raw.oddsUsed!==false||
    raw.indexValuesCompared!==false||raw.jraOfficialVerified!==false||
    raw.trainingGradeCalibrated!==false||
    raw.formalTrainingScore30Ready!==false||
    raw.overallPredictionReady!==false||raw.bettingReady!==false||
    raw.actualPurchase!==false||raw.changesExistingTickets!==false||
    raw.changesExistingReceipts!==false||raw.changesExistingRoi!==false||
    raw.additionalProviderRequestsAfterFour!==0)
  throw Error('調教比較の資料形式が不正');
 const keys=['registered','tcyComplete','tchComplete','bothComplete',
  'tcyOnly','tchOnly','neither','tchWorkoutPresent',
  'tchRecentWorkoutPresent'];
 const totals=Object.fromEntries(keys.map(k=>[k,0])),seen=new Set();
 for(const row of raw.races){
  const id=row?.track+'|'+row?.race;
  if(seen.has(id)||!historyCoordinates.has(id)||
     keys.some(k=>!Number.isInteger(row[k])||row[k]<0||
      (k==='registered'?row[k]>18:row[k]>row.registered))||
     row.bothSourcesForEveryRunner!==(row.registered>0&&
       row.bothComplete===row.registered)||
     row.trainingGradeCalibrated!==false||
     row.formalTrainingScore30Ready!==false||
     row.jraOfficialVerified!==false||row.trifectaReady!==false||
     row.tcyComplete!==row.bothComplete+row.tcyOnly||
     row.tchComplete!==row.bothComplete+row.tchOnly||
     row.registered!==row.bothComplete+row.tcyOnly+
       row.tchOnly+row.neither||
     row.tchComplete>row.tchWorkoutPresent||
     row.tchRecentWorkoutPresent>row.tchWorkoutPresent)
   throw Error('調教比較のレース別頭数が矛盾');
  seen.add(id);
  for(const k of keys)totals[k]+=row[k];
 }
 if(seen.size!==historyCoordinates.size||
    keys.some(k=>raw.summary[k]!==totals[k]))
  throw Error('調教比較の全レース合計が矛盾');
 return raw.races;
}
$('autoTcyTchCompare').onclick=async()=>{
 const button=$('autoTcyTchCompare'),day=$('autoDay').value.replaceAll('-','');
 if(button.disabled)return;
 if(historyDay!==day||!/^20[0-9]{6}$/.test(day)){
  $('autoTcyTchStatus').textContent=
   '開催日の基本資料を確認してから手動で実行してください。追加照会0回。';
  return;
 }
 const seq=++trainingCompareSeq;
 button.disabled=true;
 $('autoTcyTchRaces').replaceChildren();
 $('autoTcyTchStatus').textContent=
  '調教分析・本追切を本人の操作で照合中（JRDB追加4回まで）…';
 try{
  const response=await fetch('/api/jrdb/training-source-crosscheck?date='+
   encodeURIComponent(day),{credentials:'same-origin',cache:'no-store',
    headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
  const data=await response.json();
  if(seq!==trainingCompareSeq||
     day!==$('autoDay').value.replaceAll('-',''))return;
  if(!response.ok)throw Error('調教比較資料の取得失敗');
  const races=validateTrainingCrosscheck(data,day);
  for(const race of races){
   $('autoTcyTchRaces').append(dom('p',
    race.track+' '+race.race+'R｜両方の資料が揃う '+
    race.bothComplete+'/'+race.registered+
    '頭／調教分析のみ '+race.tcyOnly+
    '頭／本追切のみ '+race.tchOnly+
    '頭／どちらも不足 '+race.neither+
    '頭（正式調教30点は未評価）','muted'));
  }
  $('autoTcyTchStatus').textContent=
   '調教2資料を'+data.raceCount+'Rで照合。両方揃う '+
   data.summary.bothComplete+'/'+data.summary.registered+
   '頭。指数の一致・調教30点・JRA公式は未検証。'+
   '既存の買い目・保存記録・収支は変更していません。';
 }catch(_){
  if(seq===trainingCompareSeq){
   $('autoTcyTchRaces').replaceChildren();
   $('autoTcyTchStatus').textContent=
    '調教2資料の比較を保留。接続・発走前・資料一致を確認してください。'+
    '以前の予想・記録は変更していません。';
  }
 }finally{
  if(seq===trainingCompareSeq)button.disabled=false;
 }
};
const HIST_TRAIN_ATTEMPT_PREFIX='keiba-nine-owner-historical-training-day-attempt-v1-';
function initializeHistoricalTrainingDay(){
 // Default to last COMPLETED Sunday. Never send paid calls on page load.
 const today=jstToday(),noon=new Date(today+'T12:00:00Z');
 const shift=noon.getUTCDay()||7;
 noon.setUTCDate(noon.getUTCDate()-shift);
 $('autoHistoricalTrainingDay').value=noon.toISOString().slice(0,10);
 const yesterday=new Date(today+'T12:00:00Z');
 yesterday.setUTCDate(yesterday.getUTCDate()-1);
 $('autoHistoricalTrainingDay').max=yesterday.toISOString().slice(0,10);
}
function validateHistoricalTrainingReport(raw,day){
 if(!raw||raw.version!=='owner-historical-training-index-check-1'||
    raw.date!==day||!Number.isInteger(raw.raceCount)||
    raw.raceCount<0||raw.raceCount>120||
    !Array.isArray(raw.races)||raw.races.length!==raw.raceCount||
    !raw.summary||typeof raw.summary!=='object'||
    !raw.ineligibleReasons||typeof raw.ineligibleReasons!=='object'||
    !Array.isArray(raw.sourceRequestsRequired)||
    raw.sourceRequestsRequired.join('|')!=='dky|dse'||
    raw.researchOnly!==true||raw.privateOwnerOnly!==true||
    raw.rawProviderRowsIncluded!==false||
    raw.horseNumbersIncluded!==false||raw.oddsUsed!==false||
    raw.trainingSource!=='dky_training_index_not_tcy_tch'||
    raw.providerResultSource!=='jrdb_dse_not_independent_jra'||
    raw.prestartFeatureSnapshotVerified!==false||
    raw.independentJraVerified!==false||
    raw.outOfTimeValidated!==false||raw.calibrationReady!==false||
    raw.formalTrainingScore30Ready!==false||
    raw.overallPredictionReady!==false||raw.bettingReady!==false||
    raw.actualPurchase!==false||raw.changesExistingTickets!==false||
    raw.changesExistingReceipts!==false||raw.changesExistingRoi!==false||
    raw.additionalProviderReadsAfterTwo!==0)
  throw Error('過去調教研究の資料形式が不正');
 const keys=['registered','trainingIndexRecorded','resultRowsMatched',
   'numericFinishRecorded','runnersWithBoth','eligibleRaces',
   'uniqueIndexTopWon','indexFinishConcordantPairs',
   'indexFinishDiscordantPairs'],
       total=Object.fromEntries(keys.map(k=>[k,0])),
       reasons=['too_few_runners','training_index_missing',
        'race_result_incomplete','single_winner_unconfirmed',
        'top_training_index_tied'],held=Object.fromEntries(reasons.map(k=>[k,0])),
       tracks=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']),
       seen=new Set();
 for(const race of raw.races){
  const id=race?.track+'|'+race?.race,
        n=race?.registered,
        eligible=race?.retrospectiveComparisonEligible;
  if(!race||seen.has(id)||!tracks.has(race.track)||
     !Number.isInteger(race.race)||race.race<1||race.race>12||
     !Number.isInteger(n)||n<1||n>18||
     ['trainingIndexRecorded','resultRowsMatched',
      'numericFinishRecorded','runnersWithBoth'].some(k=>
       !Number.isInteger(race[k])||race[k]<0||race[k]>n)||
     race.runnersWithBoth>Math.min(race.trainingIndexRecorded,
                                   race.numericFinishRecorded)||
     typeof eligible!=='boolean'||
     !Number.isInteger(race.concordantPairs)||race.concordantPairs<0||
     !Number.isInteger(race.discordantPairs)||race.discordantPairs<0||
     race.concordantPairs+race.discordantPairs>n*(n-1)/2||
     race.officialJraVerified!==false||
     race.prestartFeatureSnapshotVerified!==false||
     race.outOfTimeValidated!==false||race.bettingReady!==false)
    throw Error('過去調教研究のレース集計に不正');
  seen.add(id);
  for(const k of keys.slice(0,5))total[k]+=race[k];
  if(eligible){
   if(n<4||race.trainingIndexRecorded!==n||
      race.numericFinishRecorded!==n||
      race.runnersWithBoth!==n||race.ineligibleReason!==null||
      typeof race.topIndexWinnerObserved!=='boolean')
    throw Error('過去調教研究の選抜条件が不正');
   total.eligibleRaces++;
   total.uniqueIndexTopWon+=Number(race.topIndexWinnerObserved);
   total.indexFinishConcordantPairs+=race.concordantPairs;
   total.indexFinishDiscordantPairs+=race.discordantPairs;
  }else{
   if(!reasons.includes(race.ineligibleReason)||
      race.topIndexWinnerObserved!==null||
      race.concordantPairs!==0||race.discordantPairs!==0)
    throw Error('比較保留レースを成果に数えています');
   held[race.ineligibleReason]++;
  }
 }
 if(keys.some(k=>raw.summary[k]!==total[k])||
    Object.keys(raw.ineligibleReasons).some(k=>!reasons.includes(k))||
    reasons.some(k=>(raw.ineligibleReasons[k]||0)!==held[k])||
    raw.summary.eligibleRaces+Object.values(held).reduce((a,b)=>a+b,0)
       !==raw.raceCount)
  throw Error('過去調教研究の集計値に矛盾');
 return raw.races;
}
initializeHistoricalTrainingDay();
$('autoHistoricalTrainingCheck').onclick=async()=>{
 const button=$('autoHistoricalTrainingCheck'),
   chosen=$('autoHistoricalTrainingDay').value,
   day=chosen.replaceAll('-','');
 const today=jstToday().replaceAll('-','');
 const d=new Date(chosen+'T12:00:00Z'),
       n=new Date(jstToday()+'T12:00:00Z');
 if(!/^20\d{2}-\d{2}-\d{2}$/.test(chosen)||
    !Number.isFinite(d.valueOf())||
    d.toISOString().slice(0,10)!==chosen||
    day>=today||(n-d)/86400000>180){
  $('autoHistoricalTrainingStatus').textContent=
   '過去180日以内の終了済み開催日を選択してください。追加照会0回。';
  return;
 }
 const marker=HIST_TRAIN_ATTEMPT_PREFIX+day;
 try{
  if(localStorage.getItem(marker)==='attempted'){
   $('autoHistoricalTrainingStatus').textContent=
    'この端末では選択日を既に1回照会しました。二重の有料照会を防ぐため再取得しません。';
   return;
  }
  // First-write before any potential provider reads, fail closed when
  // private device storage cannot prove the one-day attempt.
  localStorage.setItem(marker,'attempted');
  if(localStorage.getItem(marker)!=='attempted')throw Error('not_persistent');
 }catch(_){
  $('autoHistoricalTrainingStatus').textContent=
   '照会回数を端末に記録できないため、安全のため追加照会0回。';
  return;
 }
 button.disabled=true;
 $('autoHistoricalTrainingRaces').replaceChildren();
 $('autoHistoricalTrainingStatus').textContent=
  '本人の操作でJRDB過去調教・着順を2照会中。自動再照会なし…';
 try{
  const resp=await fetch('/api/jrdb/historical-training-check?date='+
    encodeURIComponent(day),{credentials:'same-origin',cache:'no-store',
     headers:{'X-Keiba-Request':'private','Accept':'application/json'}});
  const data=await resp.json();
  if(!resp.ok)throw Error('provider_not_ready');
  const races=validateHistoricalTrainingReport(data,day);
  if(chosen!==$('autoHistoricalTrainingDay').value)return;
  for(const row of races){
   const status=row.retrospectiveComparisonEligible
     ?'指数最上位の1着 '+(row.topIndexWinnerObserved?'確認':'該当なし')+
       '／順位比較 '+row.concordantPairs+'対'+row.discordantPairs
     :'判定保留（データ欠損・同順位など）';
   $('autoHistoricalTrainingRaces').append(dom('p',
    row.track+' '+row.race+'R｜調教指数 '+
    row.trainingIndexRecorded+'/'+row.registered+
    '頭／着順 '+row.numericFinishRecorded+
    '頭｜'+status,'muted'));
  }
  $('autoHistoricalTrainingStatus').textContent=
   '過去'+data.raceCount+'Rの資料を確認。比較可能 '+
   data.summary.eligibleRaces+'R／指数最上位が1着 '+
   data.summary.uniqueIndexTopWon+'R。過去JRDB資料の参考集計であり、'+
   '発走前スナップショット・正式30点・JRA公式・回収率は未検証。';
 }catch(_){
  if(chosen===$('autoHistoricalTrainingDay').value){
   $('autoHistoricalTrainingRaces').replaceChildren();
   $('autoHistoricalTrainingStatus').textContent=
    '過去調教資料の照合に失敗。安全のため同じ日の自動再照会はしません。'+
    '既存の予想・記録は変更していません。';
  }
 }finally{button.disabled=false;}
};
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
     row.realPredictionReady!==false||row.ticketReady!==false||
     !Array.isArray(row.runners)||row.runners.length!==row.registered)
   throw Error('直前馬体資料の頭数不一致');
  // Only presence booleans can leave the private server. No grades, kg or odds.
  const numbers=new Set(),counts={matched:0,weight:0,change:0};
  for(const h of row.runners){
   if(!h||Object.keys(h).length!==8||
      !Number.isInteger(h.number)||h.number<1||h.number>18||
      numbers.has(h.number)||
      typeof h.prestartRowMatched!=='boolean'||
      typeof h.bodyWeightRecorded!=='boolean'||
      typeof h.weightChangeRecorded!=='boolean'||
      h.jraOfficialWeightVerified!==false||
      h.bodyConditionGrade!=='未評価'||
      h.bodyConditionScore1!==null||h.bettingReady!==false||
      (h.bodyWeightRecorded&&!h.prestartRowMatched)||
      (h.weightChangeRecorded&&!h.bodyWeightRecorded))
    throw Error('直前馬体の個別資料に不正');
   numbers.add(h.number);
   counts.matched+=Number(h.prestartRowMatched);
   counts.weight+=Number(h.bodyWeightRecorded);
   counts.change+=Number(h.weightChangeRecorded);
  }
  if(counts.matched!==row.prestartRowsMatched||
     counts.weight!==row.bodyWeightRecords||
     counts.change!==row.weightChangeRecords)
   throw Error('直前馬体の馬番別件数が不一致');
  seen.add(id);
  totals.matchedRows+=row.prestartRowsMatched;
  totals.weightRecords+=row.bodyWeightRecords;
  totals.paddockRecords+=row.paddockRecords;
  totals.missingRows+=row.prestartRowsMissing;
 }
 if(Object.keys(totals).some(k=>raw.summary[k]!==totals[k]))
  throw Error('直前馬体資料の集計不一致');
 // The new factor 1 source gate MUST match this exact prestart roster.
 // Never transform observation availability into a body-condition grade.
 const pre=raw.bodyOneEvidencePreflight;
 if(!pre||pre.version!=='owner-body-one-evidence-preflight-1'||
    pre.date!==day||pre.policyVersion!=='research-5'||
    pre.factor!=='body_condition'||pre.weight!==1||
    pre.raceCount!==raw.raceCount||
    !Array.isArray(pre.races)||pre.races.length!==raw.raceCount||
    pre.verifiedGradeCount!==0||pre.officialJraVerified!==false||
    pre.sourceTimestampVerified!==false||
    pre.conditionEffectValidated!==false||pre.outOfTimeValidated!==false||
    pre.overallPredictionReady!==false||pre.bettingReady!==false||
    pre.autoPurchase!==false||pre.researchOnly!==true||
    pre.privateOwnerOnly!==true||pre.changesExistingTickets!==false||
    pre.changesExistingReceipts!==false)
  throw Error('馬体1点の資料根拠が不正');
 const originals=new Map(raw.races.map(r=>[r.track+'|'+r.race,r]));
 const seenRaces=new Set();
 for(const gate of pre.races){
  const id=gate?.track+'|'+gate?.race,src=originals.get(id);
  if(!src||seenRaces.has(id)||gate.runnerCount!==src.registered||
     gate.completeMeasuredPairs!==src.weightChangeRecords||
     gate.missingMeasuredPairs!==src.registered-src.weightChangeRecords||
     gate.verifiedGradeCount!==0||gate.scoreReady!==false||
     !Array.isArray(gate.horses)||gate.horses.length!==src.registered)
   throw Error('馬体1点の競馬場・頭数が不一致');
  seenRaces.add(id);
  const originalNumbers=new Map(src.runners.map(h=>[h.number,h]));
  const numbers=new Set();
  for(const h of gate.horses){
   const p=originalNumbers.get(h?.number);
   if(!p||numbers.has(h.number)||
      h.sourcePairPresent!==(p.bodyWeightRecorded&&p.weightChangeRecorded)||
      h.grade!=='未評価'||h.score1!==null||
      h.officialVerified!==false||h.effectValidated!==false||
      h.temporalValidationComplete!==false||h.bettingReady!==false||
      !Array.isArray(h.missingEvidence))
    throw Error('馬体1点の馬番・採点が不正');
   numbers.add(h.number);
   const gaps=[];
   if(!p.prestartRowMatched)gaps.push('prestart_runner_row_unavailable');
   if(!p.bodyWeightRecorded)gaps.push('body_weight_measurement_missing');
   if(!p.weightChangeRecorded)gaps.push('previous_weight_comparison_missing');
   gaps.push('independent_jra_weight_not_verified',
    'body_condition_effect_not_calibrated','temporal_holdout_not_validated');
   if(JSON.stringify(h.missingEvidence)!==JSON.stringify(gaps))
    throw Error('馬体1点の不足根拠が矛盾');
  }
  if(numbers.size!==src.registered)throw Error('馬体1点の馬番欠落');
 }
 if(seenRaces.size!==raw.raceCount)throw Error('馬体1点の対象レース欠落');
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
 clearPrestartBodyNotes();
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
  // Cross-check only already rendered, exact same-date prestart horses.
  // This read is opt-in: no additional provider request or persistence.
  applyPrestartBodyNotes(rows,day,latestDisplayedReport);
  for(const row of rows){
   const card=dom('div',undefined,'history-coverage');
   card.append(dom('strong',row.track+' '+row.race+'R'),
    dom('p','馬体重 '+row.bodyWeightRecords+'/'+row.registered+
     '頭／前走比 '+row.weightChangeRecords+'頭／未照合 '+
     row.prestartRowsMissing+'頭（JRA公式未確認・採点なし）','muted'));
   const panel=dom('details');
   panel.append(dom('summary','馬番別の資料を見る（正式馬体重1点は未評価）'));
   for(const horse of row.runners){
    panel.append(dom('p',horse.number+'番｜馬体重 '+
     (horse.bodyWeightRecorded?'記録あり':'未取得')+
     '／前走比 '+(horse.weightChangeRecorded?'記録あり':'未取得')+
     '｜JRA公式未確認・馬体1点未評価','muted'));
   }
   card.append(panel);
   const evidence=raw.bodyOneEvidencePreflight.races.find(g=>
    g.track===row.track&&g.race===row.race);
   const prep=dom('details');
   prep.append(dom('summary','馬体1点の採点準備：体重＋前走比あり '+
    evidence.completeMeasuredPairs+'/'+row.registered+'頭（正式未評価）'));
   prep.append(dom('p','資料の有無だけを確認しています。JRA公式値・発表時刻・'+
    '体調への効果・時系列検証が未確認なので、記録があっても採点しません。','muted'));
   const labels={
    prestart_runner_row_unavailable:'直前情報行なし',
    body_weight_measurement_missing:'計測体重なし',
    previous_weight_comparison_missing:'前走比なし',
    independent_jra_weight_not_verified:'JRA公式未照合',
    body_condition_effect_not_calibrated:'体調効果未検証',
    temporal_holdout_not_validated:'時系列未検証'};
   for(const h of evidence.horses)
    prep.append(dom('p',h.number+'番｜体重＋前走比 '+
     (h.sourcePairPresent?'記録あり':'不足')+
     '／不足根拠 '+h.missingEvidence.map(k=>labels[k]).join('・')+
     '。馬体1点は未評価。','muted'));
   card.append(prep);
   $('autoPrestartRaces').append(card);
  }
  const pairs=raw.bodyOneEvidencePreflight.races.reduce(
   (total,r)=>total+r.completeMeasuredPairs,0);
  $('autoPrestartStatus').textContent='直前資料 '+raw.summary.matchedRows+
   '頭照合／馬体重記録 '+raw.summary.weightRecords+
   '頭／体重＋前走比の資料ペア '+pairs+
   '頭。馬体1点は未評価。総合点・保存済み3連単・仮想収支は変更しません。';
 }catch(_){if(seq===prestartSeq){
  clearPrestartBodyNotes();
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
renderFixedQuick($('autoDay').value.replaceAll('-',''),true);
renderFiveQuickSaved($('autoDay').value.replaceAll('-',''));
updateReviewLink();
// If the iPhone PWA stays open over midnight, the next foreground visit
// automatically selects the NEW JST calendar day and triggers once.
// Never poll in background. Never override a user-selected historical date.
function resumeOwnerDay(){
 if(document.visibilityState==='hidden')return;
 showSnapshotFreshness();
 if(!followingToday)return;
 const today=jstToday();
 if(today===$('autoDay').value){
  const day=today.replaceAll('-','');
  if(latestDisplayedReport&&latestDisplayedDay===day){
   const expired=latestDisplayedReport.races.filter(x=>
    x.status==='provisional_draft'&&draftExpiredOnDevice(day,x.postTime)).length;
   if(expired>latestExpiredDraftCount){
    latestExpiredDraftCount=expired;
    render(latestDisplayedReport,day); // Only local display; no JRDB read.
    $('autoStatus').textContent='発走時刻を過ぎた下書きを非表示に更新。'+
     '以前の発走前固定履歴は変更していません。';
   }
  }
  return;
 }
 latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;clearAutomaticOffTimer();
 latestReadAtMs=0;showSnapshotFreshness();
 clearDraftShortcut();
 ++preflightSeq;
 $('autoPreflight').disabled=false;
 $('autoPreflightStatus').textContent='開催日が変わりました。無料診断は未実行。';
 request++;$('autoRun').disabled=false;
 $('autoDay').value=today;
 highlightSelectedWeekend();
 updateReviewLink();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
 $('autoMissingFactorSummary').textContent='開催日を取得すると未評価の内訳を確認できます。';
 $('autoMissingFactorRaces').replaceChildren();
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 clearHistory();
 $('autoSummary').textContent='未取得';
 $('autoEasyPulse').textContent='この開催日の予想は未取得です。';
 $('autoRaceQuickSummary').textContent='予想は未取得です。';
 $('autoSourceSummary').textContent='全Rの資料進捗は未取得です。';
 $('autoTrackWorkouts').textContent='調教S/Aの参考表示：開催日のデータは未取得です。';
 $('autoReadProof').textContent='開催日を切り替えました。JRDB資料はまだ照会していません。';
 $('autoMorningStatus').textContent='開催日の取得結果を確認中です。正式な10項目予想ではありません。';
 $('autoHoldBreakdown').textContent='見送り理由の内訳はJRDB資料を取得すると表示します。';
 $('autoOperationalNext').textContent='開催日の次の操作：当日の取得結果を確認中。';
 $('autoProgrammeCoverage').textContent='開催場別の取得R数：まだ確認していません。';
 $('autoRecordSafety').textContent='固定記録の保管状態：まだ確認していません。';
 $('autoFixedConsistency').textContent='固定記録と下書きの差異は未確認。既存の記録は変更していません。';
 $('autoTenWeights').replaceChildren();
 $('autoTenStatus').textContent='10項目の評価を取得していません。';
 $('autoFormalShadowStatus').textContent='開催日を変更しました。正式10項目ゲートへの接続は未確認です。';
 $('autoSavedStatus').textContent=localReceiptStatus(today.replaceAll('-',''));
 showFixedHistory(today.replaceAll('-',''));
 renderFixedQuick(today.replaceAll('-',''),true);
 $('autoStatus').textContent='新しい日付を選択しました。';
 autoFetchOnRegularRaceDay();
}
// Avoid automatic potentially billable JRDB reads on ordinary weekdays.
// Special JRA Monday/holiday meetings remain accessible through the
// explicit "全場・全Rを再分析する" action; this is not a race calendar.
// A safe reload guard for the provider's valid empty programme. Without
// this, navigating home -> forecast -> home -> forecast may repeatedly
// bill an empty /tra read even though no data can be displayed.
// Only the day (YYYYMMDD) and the local observation time are persisted.
// The user can ALWAYS request a new /tra via the explicit reanalysis button.
const AUTO_EMPTY_KEY='keiba-nine-owner-empty-programme-read-v1';
const AUTO_EMPTY_AGE_MS=30*60*1000;
function clearWeekendEmptyRead(){
 try{localStorage.removeItem(AUTO_EMPTY_KEY);}catch(_){}
}
function recordWeekendEmptyRead(day){
 const now=new Date().getTime();
 if(!Number.isFinite(now)||!/^(20[0-9]{6})$/.test(day))return;
 try{localStorage.setItem(AUTO_EMPTY_KEY,JSON.stringify({day,at:now}));}
 catch(_){/* Never block a valid forecast because this optional marker failed. */}
}
function recentWeekendEmptyRead(day){
 try{
  const raw=localStorage.getItem(AUTO_EMPTY_KEY);
  if(!raw||raw.length>100)return false;
  const v=JSON.parse(raw),now=new Date().getTime();
  return v&&Object.keys(v).length===2&&v.day===day&&
   Number.isSafeInteger(v.at)&&Number.isFinite(now)&&
   now>=v.at&&now-v.at<AUTO_EMPTY_AGE_MS;
 }catch(_){return false;}
}
// A valid signed prestart research receipt can be safely *revisited* from
// this iPhone without re-querying the paid provider on every home navigation.
// Only a small day/time/count marker is kept. Never cache the JRDB day feed,
// unverified horse grades or licensed source rows outside the request.
// Existing fixed receipts are preserved as originally received and are never
// treated as independently JRA-verified, actual purchases, or final scores.
const AUTO_FIXED_READ_KEY='keiba-nine-owner-recent-fixed-day-read-v1';
const AUTO_FIXED_READ_AGE_MS=20*60*1000;
function clearWeekendFixedRead(){
 try{localStorage.removeItem(AUTO_FIXED_READ_KEY);}catch(_){}
}
function recordWeekendFixedRead(day,data){
 if(!data||data.raceCount<=0||data.draftCount<=0){
  clearWeekendFixedRead();return;
 }
 try{
  // Only record a successful already-sealed day. A corrupt/missing ledger
  // must never suppress the next legitimate attempt to get a forecast.
  const sealed=selectedReceiptsForVerification(day);
  if(!sealed.length||sealed.length>36){clearWeekendFixedRead();return;}
  const at=new Date().getTime();
  if(!Number.isSafeInteger(at)||!/^(20[0-9]{6})$/.test(day))return;
  localStorage.setItem(AUTO_FIXED_READ_KEY,JSON.stringify({
   day,at,fixedCount:sealed.length
  }));
 }catch(_){clearWeekendFixedRead();}
}
function recentWeekendFixedRead(day){
 try{
  const raw=localStorage.getItem(AUTO_FIXED_READ_KEY);
  if(!raw||raw.length>110)return 0;
  const v=JSON.parse(raw),now=new Date().getTime();
  if(!v||Object.keys(v).length!==3||v.day!==day||
     !Number.isSafeInteger(v.at)||!Number.isSafeInteger(now)||
     !Number.isInteger(v.fixedCount)||v.fixedCount<1||v.fixedCount>36||
     now<v.at||now-v.at>=AUTO_FIXED_READ_AGE_MS)return 0;
  const sealed=selectedReceiptsForVerification(day);
  return sealed.length===v.fixedCount?sealed.length:0;
 }catch(_){return 0;}
}
function showRecentlyFixedWithoutProvider(day,label){
 const count=recentWeekendFixedRead(day);
 if(!count)return false;
 showFixedHistory(day);
 renderFixedQuick(day,true);
 $('autoSavedStatus').textContent=localReceiptStatus(day);
 $('autoSummary').textContent='新規未取得｜端末内の発走前固定 '+count+'R';
 $('autoEasyPulse').textContent='端末に固定済みの研究記録 '+count+
  'Rを表示中。新しいJRDB予想は未取得。';
 $('autoRaceQuickSummary').textContent='新規予想は未取得。過去の固定記録は「結果・記録」で確認できます。';
 $('autoTrackWorkouts').textContent='今回は馬番別調教資料を取得していません。固定済み研究記録のみ表示。';
 $('autoStatus').textContent='【'+label+'・固定履歴を表示】この端末に保存済みの発走前研究用3連単 '+count+
  'Rを表示しています。20分以内に確認済みのため自動JRDB再照会0回。今回の新しい出走資料・予想は取得していません。'+
  '署名の真正性とJRA公式出走・取消・馬場・発走時刻は未検証。';
 $('autoMorningStatus').textContent='以前に発走前固定した研究記録 '+count+
  'R（この画面では新規予想0R）。発走時刻経過後も後付け買い目は作成しません。';
 $('autoHoldBreakdown').textContent='今回は新規JRDB資料を取得していないため、見送り内訳は未確認。';
 $('autoOperationalNext').textContent='新しいJRDB配信を確認したい場合のみ「全場・全Rを再分析する」。'+
  '追加照会を行わず固定履歴を確認するには下の「発走前に固定した買い目の履歴」を開いてください。';
 $('autoReadProof').textContent='以前の端末保存記録を表示。今回のJRDB資料取得・JRA公式照合は未実施。';
 return true;
}
function autoFetchOnRegularRaceDay(){
 const day=$('autoDay').value;
 // Paid auto reads are same-day ONLY; selected future days never trigger them.
 if(day!==jstToday()){
  $('autoStatus').textContent='【次の開催予定 '+day+'】JRDBの新しい予想はまだ取得していません。'+
   '土曜の予想を取得・表示（1回）などの本人操作で配信資料を確認できます。'+
   '未来日の自動JRDB有料照会0回。';
  $('autoMorningStatus').textContent='選択日は未来。研究用予想は未取得で、正式10項目は未完成。';
  $('autoHoldBreakdown').textContent='選択日のJRDB資料は未取得。見送りR数は不明です。';
  $('autoOperationalNext').textContent='開催日の資料が公開された後、該当曜日の予想取得ボタンを押してください。'+
   'この画面を開いただけでは未来日の有料照会0回。';
  return;
 }
 const dt=new Date(day+'T12:00:00Z');
 const normalWeekend=Number.isFinite(dt.valueOf())&&
  dt.toISOString().slice(0,10)===day&&[0,6].includes(dt.getUTCDay());
 // JRA-confirmed 2026 Monday exceptions include Nov 30 Tokyo reorganisation.
 // Reuse the exact existing owner-authenticated, guarded weekend request
 // on page open. No new provider endpoint, automatic polling or purchase.
 const confirmedMonday=CONFIRMED_MONDAY_RACEDAYS.has(day)&&
  Number.isFinite(dt.valueOf())&&dt.toISOString().slice(0,10)===day&&
  dt.getUTCDay()===1;
 if(normalWeekend||confirmedMonday){
  if(recentWeekendEmptyRead(day.replaceAll('-',''))){
   $('autoStatus').textContent='【前回の番組0Rを確認済み】同じ端末で30分以内に番組0件を取得したため、画面を開き直した際の自動JRDB照会は控えました。開催なしとは断定していません。配信更新後の再確認は「全場・全Rを再分析する」を押してください。';
   $('autoMorningStatus').textContent='この画面では新しい番組・買い目は未取得。前回の番組0Rにより再照会を控えています（予想生成成功ではありません）。';
   $('autoHoldBreakdown').textContent='番組0Rの再取得を控えているため、今回の見送り内訳は未確認。';
   $('autoOperationalNext').textContent='【追加照会0回】配信更新を確認したい場合は「全場・全Rを再分析する」。以前の固定買い目は下で確認できます。';
   return;
  }
  if(showRecentlyFixedWithoutProvider(day.replaceAll('-',''),
      confirmedMonday?(day==='2026-11-30'?'JRA開催の月曜再編当日':'JRA開催の月祝当日'):'土日当日')){
   return;
  }
  $('autoRun').onclick();
  return;
 }
 // Friday is the usual publication day for Saturday's race cards.
 // This is a no-cost, honest availability guide, NOT proof JRDB has
 // published programme/entries or that any forecast has been created.
 if(dt.getUTCDay()===5){
  const nextSaturday=nearestJstWeekday(6);
  $('autoStatus').textContent='【金曜・明日 '+nextSaturday+'】明日のJRDB予想はこの画面ではまだ取得していません。'+
   '上の「土曜の予想を取得・表示（1回）」を押すと、本人認証で1回だけ取得・研究用暫定案を作成します。'+
   '取得に成功したR数が出るまでは予想完成と扱いません。';
  $('autoMorningStatus').textContent='明日のJRA公式出馬表が公開済みでも、JRDBの予想作成完了とは別です。'+
   '現在は研究用の調教・近走2項目。正式10項目は未完成。';
  $('autoHoldBreakdown').textContent='土曜日の資料を未取得。見送り内訳はまだ確認できません。';
  $('autoOperationalNext').textContent='次の操作：土曜の予想を取得・表示（1回）。'+
   '本人操作前のJRDB有料照会0回。0Rの場合は配信状況を確認し、開催なしとは断定しません。';
  return;
 }
 $('autoStatus').textContent='通常の平日はJRDBの自動照会を控えています。土日とJRA公表済みの2026年開催月曜（祝日・再編）は当日の本人画面で1回取得。それ以外の変則開催は日付を選んで「全場・全Rを再分析する」を押してください。';
 $('autoMorningStatus').textContent='未確認の平日・変則開催は自動取得なし（有料照会0回）。正式10項目予想の完成を意味しません。';
 $('autoHoldBreakdown').textContent='平日の新規資料を取得していないため、見送り内訳は未確認。';
 $('autoOperationalNext').textContent='次の通常開催：土曜日・日曜日を選ぶ。平日の特別開催はJRA公式で確認後に手動取得。';
}
if(typeof document.addEventListener==='function')
 document.addEventListener('visibilitychange',resumeOwnerDay);
if(typeof window!=='undefined'&&typeof window.addEventListener==='function')
 window.addEventListener('pageshow',event=>{if(event.persisted)resumeOwnerDay();});
resetAdvanceProgramme(); // Safe default official calendar link on first load.
// Opening an authenticated owner page auto-reads on regular weekends AND
// exactly the explicitly confirmed 2026 Monday JRA race days. Other
// weekdays remain manual. No background polling or purchase.
if(document.visibilityState!=='hidden')autoFetchOnRegularRaceDay();
})();"""


# In-page VIEW of a separately stored, private editorial pre-day forecast.
# It makes zero paid source requests and never promotes editorial 24R to
# independently JRA-verified or formal-ten-factor selections.
JS += r"""
;(()=>{'use strict';
const load=document.getElementById('autoPredayInlineLoad');
const status=document.getElementById('autoPredayInlineStatus');
const host=document.getElementById('autoPredayInlineRaces');
const dayInput=document.getElementById('autoDay');
if(!load||!status||!host||!dayInput)return;
const allowed=new Set(['東京','京都','福島','札幌','函館','新潟','中山','中京','阪神','小倉']);
const iso=/^20\d{2}-\d{2}-\d{2}$/;
const hhmm=/^(?:[01]\d|2[0-3]):[0-5]\d$/;
let sequence=0;
function checkedDay(day){
 return typeof day==='string'&&iso.test(day)&&
  Number.isFinite(Date.parse(day+'T12:00:00Z'))&&
  new Date(day+'T12:00:00Z').toISOString().slice(0,10)===day;
}
function nowJst(){
 const fields=Object.fromEntries(new Intl.DateTimeFormat('en-US',{
  timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit',
  hour:'2-digit',minute:'2-digit',hour12:false
 }).formatToParts(new Date()).map(p=>[p.type,p.value]));
 return {date:fields.year+'-'+fields.month+'-'+fields.day,
  time:fields.hour+':'+fields.minute};
}
function node(tag,text,className){
 const n=document.createElement(tag);
 if(text!==undefined)n.textContent=String(text);
 if(className)n.className=className;
 return n;
}
function verifiedRows(envelope,requested){
 if(!envelope||envelope.available!==true||!envelope.forecast)
  throw Error('unavailable');
 const p=envelope.forecast;
 if(p.schema!=='keiba-nine-private-preday-review-v1'||
    p.sourceKind!=='owner-private-authored-preday'||
    p.date!==requested||!checkedDay(p.date)||
    p.predictionReady!==false||p.officialJraVerified!==false||
    p.purchased!==false||!Array.isArray(p.races)||
    p.races.length<1||p.races.length>36||p.raceCount!==p.races.length)
  throw Error('invalid');
 const seen=new Set(),rows=[];
 for(const r of p.races){
  if(!r||!allowed.has(r.track)||!Number.isInteger(r.race)||
     r.race<1||r.race>12||!hhmm.test(r.time)||
     !Number.isInteger(r.field)||r.field<3||r.field>18||
     r.provisional!==true||r.jraOfficialConfirmed!==false||
     r.fullFactorVerified!==false||
     !['買い候補','見送り'].includes(r.status)||
     !Array.isArray(r.rank)||r.rank.length<3||r.rank.length>Math.min(7,r.field)||
     !Array.isArray(r.first)||!Array.isArray(r.second)||
     !Array.isArray(r.third)||!Number.isInteger(r.points)||
     r.points<1||r.points>48)
   throw Error('invalid_row');
  const key=r.track+'|'+r.race;
  if(seen.has(key))throw Error('duplicate_race');
  seen.add(key);
  if(new Set(r.rank).size!==r.rank.length||
     r.rank.some(n=>!Number.isInteger(n)||n<1||n>r.field))
   throw Error('invalid_rank');
  const f=r.first.length,s=r.second.length,t=r.third.length;
  if(f<1||f>3||s<f||t<s||t>r.rank.length||
     ![r.first,r.second,r.third].every(arr=>
      arr.every((num,i)=>num===r.rank[i])))
   throw Error('invalid_formation');
  const tickets=new Set();
  for(const a of r.first)for(const b of r.second)for(const d of r.third)
   if(a!==b&&a!==d&&b!==d)tickets.add(a+'-'+b+'-'+d);
  if(tickets.size!==r.points)throw Error('invalid_points');
  rows.push({track:r.track,race:r.race,time:r.time,
   status:r.status,points:r.points,first:[...r.first],
   second:[...r.second],third:[...r.third]});
 }
 return rows.sort((a,b)=>a.track.localeCompare(b.track,'ja')||a.race-b.race);
}
function clear(){
 sequence++;
 host.replaceChildren();
 load.disabled=false;
 status.textContent='開催日が変わりました。前日参考予想は未表示です。';
}
// The main owner's date picker updates programmatically via onchange.
// Wrap that handler without changing the existing calendar behavior.
const previousChange=dayInput.onchange;
if(typeof previousChange==='function'){
 dayInput.onchange=function(...args){
  clear();
  const result=previousChange.apply(this,args);
  // Recheck the newly selected day from the FREE owner snapshot only.
  if(checkedDay(dayInput.value))void load.onclick();
  return result;
 };
}else if(typeof dayInput.addEventListener==='function'){
 dayInput.addEventListener('change',()=>{clear();if(checkedDay(dayInput.value))void load.onclick();});
}
load.onclick=async()=>{
 if(load.disabled)return;
 const requested=dayInput.value,clock=nowJst(),request=++sequence;
 host.replaceChildren();
 if(!checkedDay(requested)||requested<clock.date){
  status.textContent='開催日を確認してください。過去日の新規参考買い目は表示しません。';
  return;
 }
 load.disabled=true;
 status.textContent='登録済みの前日参考予想を確認中（JRDBへの追加照会なし）。';
 try{
  const response=await fetch('/api/owner-preday-forecast',{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  if(!response.ok)throw Error('unavailable');
  const envelope=await response.json();
  if(request!==sequence||dayInput.value!==requested)return;
  const rows=verifiedRows(envelope,requested);
  const venues=new Map();
  for(const r of rows){
   if(!venues.has(r.track))venues.set(r.track,[]);
   venues.get(r.track).push(r);
  }
  const tabs=node('div',undefined,'venue-tabs');
  const chooser=node('div',undefined,'owner-race-jump');
  const cards=node('div',undefined,'owner-inline-preday-cards');
  function showVenue(track){
   cards.replaceChildren();
   chooser.replaceChildren();
   for(const tab of tabs.children)
    tab.setAttribute('aria-pressed',String(tab.textContent===track));
   const races=venues.get(track)||[];
   for(const r of races){
    const card=node('article',undefined,'owner-reference-quick-card');
    card.append(node('strong',track+' '+r.race+'R'));
    card.append(node('p',r.time+'予定（前日資料）｜'+r.status+
     '｜研究用'+r.points+'点','muted'));
    const clockNow=nowJst();
    const expired=requested===clockNow.date&&r.time<=clockNow.time;
    if(expired){
     card.append(node('p','発走予定時刻を経過。新規の3連単表示はしません。過去の固定記録は結果・記録画面で確認。','muted'));
    }else{
     card.append(node('p','1着 '+r.first.join('・'),'picks'));
     card.append(node('p','2着 '+r.second.join('・'),'picks'));
     card.append(node('p','3着 '+r.third.join('・'),'picks'));
     card.append(node('p','編集済みの前日参考案。JRDB2項目とは別方式。正式10項目・JRA最終出走・取消・馬場・発走時刻は未照合。購入・署名・仮想収支には反映しません。','muted'));
    }
    cards.append(card);
   }
   const choices=[{race:0,label:'全R'},
    ...races.map(r=>({race:r.race,label:r.race+'R'}))];
   const buttons=[];
   function focusRace(number){
    for(let i=0;i<races.length;i++)
     cards.children[i].hidden=number!==0&&races[i].race!==number;
    for(const item of buttons)
     item.button.setAttribute('aria-pressed',String(item.race===number));
   }
   for(const item of choices){
    const button=node('button',item.label);
    button.type='button';
    button.onclick=()=>focusRace(item.race);
    buttons.push({...item,button});
    chooser.append(button);
   }
   focusRace(0);
  }
  for(const track of venues.keys()){
   const button=node('button',track);
   button.type='button';
   button.onclick=()=>showVenue(track);
   tabs.append(button);
  }
  host.replaceChildren(tabs,chooser,cards);
  if(venues.size)showVenue(venues.keys().next().value);
  status.textContent=requested+'｜前日参考 '+rows.length+
   'Rをこの画面に表示（'+venues.size+'場）。JRDB2項目の下書き件数とは別。追加のJRDB照会0回。';
 }catch(error){
  if(request===sequence&&dayInput.value===requested){
   host.replaceChildren();
   status.textContent=error?.message==='unavailable'
    ?'この開催日の前日参考予想は未登録です。配信後に再確認できます。JRDB有料照会0回。'
    :'この日の前日参考予想を安全に表示できません。資料の形式と開催日を確認してください。既存のJRDB下書き・固定記録は無変更です。';
  }
 }finally{
  if(request===sequence)load.disabled=false;
 }
};
// One free authenticated read after the date picker is initialized.
// Never a JRDB paid read, timer, storage write or automatic purchase.
if(checkedDay(dayInput.value))void load.onclick();
})();
"""


# No-cost, authenticated one-screen verification that a research receipt
# truly exists in an enabled server archive. No licensed JRDB reads,
# transmission of tickets, signature disclosure, or browser writes.
JS += r"""
;(()=>{'use strict';
const dayInput=document.getElementById('autoDay');
const output=document.getElementById('autoStoragePulse');
const run=document.getElementById('autoRun');
if(!dayInput||!output||!run)return;
const venues=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
let sequence=0;
const valid=day=>typeof day==='string'&&/^20\d{2}-\d{2}-\d{2}$/.test(day)&&
 Number.isFinite(Date.parse(day+'T12:00:00Z'))&&
 new Date(day+'T12:00:00Z').toISOString().slice(0,10)===day;
async function refresh(){
 const day=dayInput.value,request=++sequence;
 if(!valid(day)){
  output.textContent='開催日を正しく選択してください。サーバーへの保存は未確認です。';
  return;
 }
 output.textContent=day+'｜サーバー固定を無料確認中（JRDB追加照会なし）…';
 try{
  const response=await fetch('/api/owner-prestart-storage-status?date='+
   encodeURIComponent(day),{
   credentials:'same-origin',cache:'no-store',
   headers:{'X-Keiba-Request':'private','Accept':'application/json'}
  });
  const result=await response.json();
  if(sequence!==request||dayInput.value!==day)return;
  if(!response.ok||!result||
     result.version!=='owner-prestart-storage-status-1'||
     result.date!==day||typeof result.archiveEnabled!=='boolean'||
     typeof result.persistentStorageReady!=='boolean'||
     !Number.isInteger(result.serverSavedRaceCount)||
     result.serverSavedRaceCount<0||result.serverSavedRaceCount>36||
     result.verifiedServerSignedRaceCount!==result.serverSavedRaceCount||
     result.providerRequests!==0||result.officialJraVerified!==false||
     result.finalResultsConnected!==false||result.actualPurchase!==false||
     result.completeJraDayVerified!==false||
     result.persistentStorageReady!==result.archiveEnabled||
     !Array.isArray(result.storedRaceCoordinates)||
     result.storedRaceCoordinates.length!==result.serverSavedRaceCount||
     !Array.isArray(result.storedVenueCounts)||result.storedVenueCounts.length>10||
     (!result.archiveEnabled&&result.serverSavedRaceCount!==0))
   throw Error('invalid_server_storage_status');
  const saved=new Set(),countByVenue=new Map();
  for(const r of result.storedRaceCoordinates){
   if(!r||!venues.has(r.track)||!Number.isInteger(r.race)||
      r.race<1||r.race>12||Object.keys(r).length!==2)
    throw Error('invalid_archive_coords');
   const key=r.track+'|'+r.race;
   if(saved.has(key))throw Error('duplicate_archive_coords');
   saved.add(key);
   countByVenue.set(r.track,(countByVenue.get(r.track)||0)+1);
  }
  const seenVenues=new Set();
  for(const entry of result.storedVenueCounts){
   if(!entry||!venues.has(entry.track)||
      !Number.isInteger(entry.raceCount)||entry.raceCount<1||
      entry.raceCount>12||Object.keys(entry).length!==2||
      seenVenues.has(entry.track)||
      countByVenue.get(entry.track)!==entry.raceCount)
    throw Error('invalid_archive_venue_total');
   seenVenues.add(entry.track);
  }
  if(seenVenues.size!==countByVenue.size)throw Error('archive_venue_missing');
  const venueText=result.storedVenueCounts
   .map(x=>x.track+x.raceCount+'R').join('・');
  // The *already fetched* JRDB race list can reveal unsigned/held R without
  // any extra provider call. Missing archive entries do not imply failure:
  // held races may legitimately contain no research ticket at all.
  let unsaved='';
  if(typeof historyDay==='string'&&
     historyDay===day.replaceAll('-','')&&
     typeof historyCoordinates!=='undefined'&&
     historyCoordinates instanceof Set&&historyCoordinates.size>0&&
     historyCoordinates.size<=36){
   const missing=[...historyCoordinates].filter(k=>!saved.has(k));
   if(missing.length){
    const preview=missing.slice(0,8).map(k=>k.replace('|','')).join('・');
    unsaved='／JRDB取得済みのRのうちサーバー未固定'+
     missing.length+'R（'+preview+(missing.length>8?'ほか':'')+
     '）。見送りRも含むため予想失敗件数ではありません。';
   }else{
    unsaved='／JRDBで取得済みのRは全てサーバー固定済み。'+
     'JRA公式照合・正式10項目予想が完成した意味ではありません。';
   }
  }
  if(!result.archiveEnabled){
   output.textContent=day+
    '｜サーバー永続保存は未設定。発走前の研究用買い目が端末にあっても、サーバー保存済みとは扱いません。端末の固定履歴を保護してください。追加のJRDB照会0回。';
  }else if(result.serverSavedRaceCount===0){
   output.textContent=day+
    '｜サーバー保存機能は利用可能ですが、署名を検証できた発走前の研究用3連単は0R。予想作成済みとは扱いません。追加のJRDB照会0回。';
  }else{
   output.textContent=day+'｜サーバー保存済み・署名検証済みの発走前研究用3連単 '+
    result.serverSavedRaceCount+
    'R（'+venueText+'）'+unsaved+
    '。JRA公式出走・発走時刻・結果・購入は未確認。保存していないRは補完していません。追加のJRDB照会0回。';
  }
 }catch(_){
  if(sequence===request&&dayInput.value===day)
   output.textContent=day+
    '｜サーバー保存を安全に確認できません。未確認を「保存済み」と表示しません。端末固定履歴は変更していません。';
 }
}
const priorChange=dayInput.onchange;
if(typeof priorChange==='function'){
 dayInput.onchange=function(...args){
  const result=priorChange.apply(this,args);
  void refresh();
  return result;
 };
}
const priorRun=run.onclick;
if(typeof priorRun==='function'){
 run.onclick=async function(...args){
  const selected=dayInput.value;
  try{return await priorRun.apply(this,args);}
  finally{if(selected===dayInput.value)await refresh();}
 };
}
void refresh();
})();
"""


# Browser-only per-race evidence availability join. The owner can compare
# already fetched JRDB research numbers with his private local JV-Link RACE+
# RCVN JSON without uploading provider records, adding paid requests,
# inferring horse identity or creating new ten-factor scores or tickets.
JS += r"""
;(()=>{'use strict';
const dateInput=document.getElementById('autoDay');
const fileInput=document.getElementById('autoJvHistoryFile');
const compareButton=document.getElementById('autoJvHistoryCompare');
const status=document.getElementById('autoJvHistoryStatus');
const rows=document.getElementById('autoJvHistoryRows');
const fetchButton=document.getElementById('autoRun');
if(!dateInput||!fileInput||!compareButton||!status||!rows||!fetchButton)return;
const tracks=new Set(['札幌','函館','福島','新潟','東京','中山','中京','京都','阪神','小倉']);
const gradeValues=new Set(['S','A','B','C','未評価']);
const dateRe=/^20\d{6}$/;
let seq=0;
function viewNode(tag,text){
 const el=document.createElement(tag);
 el.textContent=String(text);
 return el;
}
function clearState(why){
 seq++;
 rows.replaceChildren();
 fileInput.value='';
 status.textContent=why;
}
function joinForCoverage(source,day,rosters,grades){
 // All PRIVATE data remains in the browser: only bounded counts and
 // provisional horse number sets are evaluated in this function.
 if(!dateRe.test(day)||!source||typeof source!=='object'||Array.isArray(source)||
    source.version!=='owner-jvdata-local-day-history-bridge-1'||
    source.date!==day||source.researchOnly!==true||
    source.privateOwnerOnly!==true||
    source.historySource!=='private_jvlink_rcvn_partial_observations'||
    source.historyCompletenessVerified!==false||
    source.captureTimeIndependentlyVerified!==false||
    source.officialStarterListVerified!==false||
    source.officialScratchStateVerified!==false||
    source.officialGoingVerified!==false||
    source.formalTenFactorReady!==false||
    source.productionPredictionReady!==false||
    source.bettingReady!==false||source.autoPurchase!==false||
    source.newProviderRequests!==0||
    !Array.isArray(source.races)||source.races.length<1||
    source.races.length>36||source.raceCount!==source.races.length||
    !(rosters instanceof Map)||!(grades instanceof Map))
  throw Error('invalid_local_history');
 const local=new Map();
 for(const race of source.races){
  if(!race||!tracks.has(race.track)||!Number.isInteger(race.race)||
     race.race<1||race.race>12||race.historyComplete!==false||
     race.graded!==false||race.bettingReady!==false||
     !Array.isArray(race.byNumber)||race.byNumber.length<3||
     race.byNumber.length>18||
     !Number.isInteger(race.observedHorseHistory)||
     race.observedHorseHistory<0||
     race.observedHorseHistory>race.byNumber.length)
   throw Error('invalid_local_race');
  const coord=race.track+'|'+race.race;
  if(local.has(coord))throw Error('duplicate_local_race');
  const horses=new Map();
  for(const item of race.byNumber){
   if(!item||!Number.isInteger(item.number)||item.number<1||
      item.number>18||horses.has(item.number)||
      item.missingHistoryUnproven!==true||
      item.graded!==false||!Number.isInteger(item.observedRecordCount)||
      item.observedRecordCount<0||item.observedRecordCount>20000||
      !Array.isArray(item.recentObservedRuns)||
      item.recentObservedRuns.length>5||
      item.recentObservedRuns.length>item.observedRecordCount)
    throw Error('invalid_local_horse');
   horses.set(item.number,{observed:item.observedRecordCount>0});
  }
  if([...horses.values()].filter(x=>x.observed).length!==race.observedHorseHistory)
   throw Error('invalid_local_observations');
  local.set(coord,horses);
 }
 if(rosters.size>36||grades.size>36||rosters.size!==grades.size)
  throw Error('invalid_jrdb_coordinates');
 for(const key of grades.keys())if(!rosters.has(key))throw Error('invalid_jrdb_mapping');
 const cards=[];
 for(const [coord,nums] of rosters){
  const parts=coord.split('|'),horseGrades=grades.get(coord);
  if(parts.length!==2||!tracks.has(parts[0])||
     !/^(?:[1-9]|1[0-2])$/.test(parts[1])||
     !(nums instanceof Set)||!(horseGrades instanceof Map)||
     nums.size>18||horseGrades.size!==nums.size)
   throw Error('invalid_jrdb_roster');
  for(const number of nums){
   const g=horseGrades.get(number);
   if(!Number.isInteger(number)||number<1||number>18||
      !g||!gradeValues.has(g.training)||!gradeValues.has(g.recent))
    throw Error('invalid_jrdb_grade');
  }
  const jv=local.get(coord);
  let statusCode='jv_race_not_observed',priorCount=0,dualCount=0;
  if(jv){
   if(nums.size<3){
    statusCode='jrdb_roster_unavailable';
   }else if(jv.size!==nums.size||
      [...nums].some(number=>!jv.has(number))){
    statusCode='number_sets_differ';
   }else{
    statusCode='same_number_set_unverified_identity';
    for(const [number,sourceHorse] of jv){
     if(sourceHorse.observed){
      priorCount++;
      const g=horseGrades.get(number);
      if(g.training!=='未評価'&&g.recent!=='未評価')dualCount++;
     }
    }
   }
  }
  cards.push({track:parts[0],race:Number(parts[1]),status:statusCode,
   candidateCount:nums.size,observedPriorCount:priorCount,
   alsoTwoFactorObservedCount:dualCount});
 }
 const paired=cards.filter(x=>x.status==='same_number_set_unverified_identity');
 return {
  version:'owner-local-jrdb-jv-history-coverage-1',
  date:day,referenceRaceCount:cards.length,
  localRaceCount:local.size,
  numberSetMatchRaceCount:paired.length,
  mismatchedRaceCount:cards.filter(x=>x.status==='number_sets_differ').length,
  missingJvRaceCount:cards.filter(x=>x.status==='jv_race_not_observed').length,
  missingJrdbRosterRaceCount:cards.filter(x=>x.status==='jrdb_roster_unavailable').length,
  unpairedJvRaceCount:[...local.keys()].filter(k=>!rosters.has(k)).length,
  observedPriorHorseNumberCount:paired.reduce((sum,x)=>sum+x.observedPriorCount,0),
  bothSourcesObservedHorseNumberCount:paired.reduce((sum,x)=>sum+x.alsoTwoFactorObservedCount,0),
  cards,officialHorseIdentityVerified:false,officialJraVerified:false,
  formalTenFactorReady:false,bettingReady:false,
  newProviderRequests:0,changesExistingReceipts:false,
 };
}
compareButton.onclick=async()=>{
 if(compareButton.disabled)return;
 const day=dateInput.value.replaceAll('-',''),mySeq=++seq;
 rows.replaceChildren();
 const f=fileInput.files&&fileInput.files[0];
 if(!dateRe.test(day)||historyDay!==day||!(historyRosters instanceof Map)||
    historyRosters.size===0){
  status.textContent='先に選択日のJRDB研究資料を取得してください。JRA-VANはまだ読み込みません。';
  return;
 }
 if(!f||!/^jvdata-all-flat-races-20\d{6}\.json$/.test(f.name)||
    f.name!=='jvdata-all-flat-races-'+day+'.json'||
    !Number.isInteger(f.size)||f.size<1||f.size>8000000){
  status.textContent='同じ開催日の8MB以内のJRA-VAN全R履歴JSONを選んでください。外部へは送信しません。';
  return;
 }
 compareButton.disabled=true;
 status.textContent='端末内でレース・馬番集合を照合中。外部へのファイル送信・追加API照会なし。';
 try{
  const plain=await f.text();
  if(mySeq!==seq||historyDay!==day||dateInput.value.replaceAll('-','')!==day)return;
  if(plain.length>8000000)throw Error('oversize');
  const source=JSON.parse(plain);
  const merged=joinForCoverage(source,day,historyRosters,historyGrades);
  if(mySeq!==seq||historyDay!==day||dateInput.value.replaceAll('-','')!==day)return;
  const display=document.createDocumentFragment();
  const names={
   same_number_set_unverified_identity:'馬番集合一致（同一馬IDは未確認）',
   number_sets_differ:'馬番集合に不一致',
   jv_race_not_observed:'JRA-VAN側のR未収録',
   jrdb_roster_unavailable:'JRDB側の馬番資料不足'
  };
  for(const card of merged.cards){
   const p=viewNode('p',card.track+card.race+'R｜'+names[card.status]+
    '｜JRA-VAN過去走が観測できた馬番 '+card.observedPriorCount+
    '／JRDB調教・近走の仮評価もある馬番 '+card.alsoTwoFactorObservedCount);
   display.append(p);
  }
  rows.replaceChildren(display);
  status.textContent='選択日 '+day+'｜JRDB '+merged.referenceRaceCount+
   'R／JRA-VANファイル '+merged.localRaceCount+
   'R。馬番集合一致 '+merged.numberSetMatchRaceCount+
   'R、不一致 '+merged.mismatchedRaceCount+
   'R、JV側Rなし '+merged.missingJvRaceCount+
   'R、JRDB馬番不足 '+merged.missingJrdbRosterRaceCount+
   'R、対応しないJV側R '+merged.unpairedJvRaceCount+
   'R。同じ馬のID照合・正式10項目・JRA最終出走・馬場は未確認。3連単は作成・変更せず、ファイル送信0回。';
 }catch(_){
  if(mySeq===seq&&dateInput.value.replaceAll('-','')===day){
   rows.replaceChildren();
   status.textContent='JRA-VANファイルを安全に照合できません。日付・馬番・資料の形式を確認してください。JRDB再取得や買い目変更は行いません。';
  }
 }finally{if(mySeq===seq)compareButton.disabled=false;}
};
const previousDayChange=dateInput.onchange;
if(typeof previousDayChange==='function'){
 dateInput.onchange=function(...args){
  clearState('開催日を変更しました。新しい日のファイルを選んでください。');
  return previousDayChange.apply(this,args);
 };
}
const previousRun=fetchButton.onclick;
if(typeof previousRun==='function'){
 fetchButton.onclick=async function(...args){
  clearState('JRDBを再取得中。旧JRA-VANファイルの照合結果を破棄しました。');
  return previousRun.apply(this,args);
 };
}
})();
"""


# Presentation-only switch. No new source reads, bet calculation, paid API
# calls, draft storage, receipt changes, or automatic purchase.
JS += r"""
;(()=>{'use strict';
const preday=document.getElementById('ownerPredayMode');
const jrdb=document.getElementById('ownerJrdbMode');
const detail=document.getElementById('ownerDetailToggle');
const body=document.body;
if(!preday||!jrdb||!detail||!body||
   !body.classList||typeof body.classList.toggle!=='function')return;
function choose(view,jump){
 const isJrdb=view==='jrdb';
 body.classList.toggle('owner-jrdb-view',isJrdb);
 body.classList.toggle('owner-preday-view',!isJrdb);
 preday.setAttribute('aria-pressed',String(!isJrdb));
 jrdb.setAttribute('aria-pressed',String(isJrdb));
 if(jump){
  const section=document.getElementById(isJrdb?'forecastRacesSection':
   'autoPredayInlineRaces');
  if(section&&typeof section.scrollIntoView==='function')
   section.scrollIntoView({behavior:'smooth',block:'start'});
 }
}
function detailed(enabled){
 body.classList.toggle('owner-detailed',enabled);
 detail.setAttribute('aria-pressed',String(enabled));
 detail.textContent=enabled?'簡単表示に戻す':'詳しい設定';
}
preday.onclick=()=>choose('preday',true);
jrdb.onclick=()=>choose('jrdb',true);
detail.onclick=()=>detailed(!body.classList.contains('owner-detailed'));
// When the owner explicitly requests new JRDB analysis, reveal that source.
// Use additive DOM listeners rather than replacing existing authenticated
// onclick handlers: this neither duplicates nor changes a provider request.
for(const id of ['autoSaturdayQuick','autoSundayQuick',
                 'autoMondayQuick','autoRun']){
 const control=document.getElementById(id);
 if(control&&typeof control.addEventListener==='function')
  control.addEventListener('click',()=>choose('jrdb',false));
}
// Explicitly rechecking the *separate* free preday page should display it,
// rather than leaving the owner staring at the other source's race list.
const predayReload=document.getElementById('autoPredayInlineLoad');
if(predayReload&&typeof predayReload.addEventListener==='function')
 predayReload.addEventListener('click',()=>choose('preday',false));
if(typeof document.querySelector==='function'){
 const raceLink=document.querySelector('.arc-main-tabs a[href="#forecastRacesSection"]');
 const resultLink=document.querySelector('.arc-main-tabs a[href="#fixedHistorySection"]');
 if(raceLink&&typeof raceLink.addEventListener==='function')
  raceLink.addEventListener('click',()=>choose('jrdb',false));
 if(resultLink&&typeof resultLink.addEventListener==='function')
  resultLink.addEventListener('click',()=>detailed(true));
}
choose('preday',false);
})();
"""
