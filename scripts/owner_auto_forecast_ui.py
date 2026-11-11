"""Owner private iPhone view for automatic JRDB two-factor provisional draft."""
HTML = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#09172b">
<title>KEIBA NINE｜本人用・自動暫定予想</title>
<link rel="stylesheet" href="/owner-auto-forecast.css"></head><body><main>
<nav class="owner-nav">
<a href="https://esakahumihumi1125-byte.github.io/keiba-nine/keiba-nine-beta51-feed-record.html" rel="noopener noreferrer">← KEIBA NINE本体へ</a>
<a href="/">本人用ホーム</a>
<a href="/owner-jrdb-day-research">2項目の根拠</a>
<a href="https://esakahumihumi1125-byte.github.io/keiba-nine/keiba-nine-beta51-feed-record.html#win5" rel="noopener noreferrer">WIN5（別画面）</a>
</nav>
<h1>KEIBA NINE <small>本人用・予想</small></h1>
<p class="warning"><strong>現在は研究用の暫定予想です。</strong>調教・近走の2項目で3連単を試算しています。
正式10項目の予想とJRA公式照合は未完成。自動購入はしません。</p>
<section class="daily-start">
<h2>1. 予想を見る</h2>
<label for="autoDay">開催日</label><input id="autoDay" type="date">
<button id="autoSaturdayQuick" class="primary-cta" type="button">次の土曜の予想を見る</button>
<button id="autoSundayQuick" class="secondary-cta" type="button">次の日曜の予想を見る</button>
<button id="autoRun" class="secondary-cta" type="button">全場・全Rを再分析する</button>
<p class="muted">土日の1タップ取得は直前の木曜以降。取得済みの結果は再利用し、連打による追加照会はしません。JRDBのAPI照会には契約に応じた料金・制限があります。</p>
<details><summary>日付だけを切り替える（追加照会なし）</summary>
<div class="day-shortcuts" role="group" aria-label="週末の開催日を選ぶ">
<button id="autoSaturday" type="button">次の土曜日を選ぶ</button>
<button id="autoSunday" type="button">次の日曜日を選ぶ</button>
</div>
<p class="muted">土日ボタンは日付だけを切り替え、追加のJRDB照会をしません。</p></details>
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
<p class="muted">通常の土日に画面を開いた場合だけ、本人用の当日分を一度自動取得。平日・変則開催は日付を選んで手動取得。
再分析ボタンを押した場合は番組・出走馬・調教・近走を各1回取得し、
馬場情報の追加取得も最大1回だけ試みます。取得できなくても既存の発走前記録は維持します。
バックグラウンド定期取得は未接続。発走済みレースの3連単は後付けで作成しません。</p>
<p id="autoStatus" class="muted" role="status">開催日を選んで自動作成を押してな。</p>
<h2>2. 今日の予想状況</h2>
<p id="autoMorningStatus" class="muted" role="status">開催日の取得結果を確認中です。発走前研究用の暫定案であり、正式な10項目予想ではありません。</p>
<p id="autoOperationalNext" class="muted" role="status">開催日の次の操作：当日の取得結果を確認中。</p>
<nav class="quick-links" aria-label="画面内の移動">
<a id="autoDraftShortcut" href="#autoVenues">買い目あり：未取得</a>
<a href="#autoVenues">全レース一覧</a><a href="#fixedHistorySection">固定した買い目</a></nav>
<details><summary>取得・資料の詳しい状態</summary>
<p id="autoProgrammeCoverage" class="muted" role="status">開催場別の取得R数：まだ確認していません。</p>
<p id="autoReadProof" class="muted" role="status">JRDB資料の照会状況は未確認です。番組0Rと全資料取得は別です。</p>
<p id="autoRecordSafety" class="muted" role="status">固定記録の保管状態：まだ確認していません。</p></details>
<a href="#autoVenues">開催日のレース一覧に進む</a>
<p class="muted"><a href="#autoHistoryAudit">過去の同条件照合へ進む</a>（旧85点の比較と新配点79点の研究用下書きを確認。追加の有料API取得は本人がボタンを押した時のみ）</p>
<details><summary>JRA公式の出馬表PDFを開く（任意）</summary>
<p class="muted">本人が押した時だけJRA公式ページから開催場別の出馬表PDFリンクを探します。PDFの内容は自動解析しません。出走馬・取消・馬場・発走時刻を公式情報と自分で照合するための補助です。</p>
<button id="autoOfficialPdf" type="button">選択日のJRA公式PDFリンクを探す</button>
<p id="autoJraReleaseGuide" class="muted" role="status">選択日の出馬表公開目安を計算中。</p>
<p id="autoJraCrosscheck" class="muted" role="status">JRA公式照合：0R（未実施）。</p>
<p id="autoOfficialPdfStatus" class="muted" role="status">未確認。PDFリンクの存在だけではJRA公式照合済みとは扱いません。</p>
<div id="autoOfficialPdfLinks"></div>
<a href="https://www.jra.go.jp/keiba/rpdf/" target="_blank" rel="noopener noreferrer">JRA公式の出馬表一覧を開く</a>
</details>
<details><summary>開催日朝の使い方（3ステップ）</summary>
<p class="muted">① 当日の朝、本人用アプリを開く。自動取得が終わったら「開催日の利用状況」で番組R数・下書き数・見送り数を確認する。0Rやエラーの場合は無理に買い目を作らない。</p>
<p class="muted">② 下の「下書きのみ」を選ぶか、競馬場・レースを選択して1着／2着／3着の3連単と重複除外した点数を確認する。これは調教・近走だけの研究用下書きで、10項目の本予想や投票推奨ではない。</p>
<p class="muted">③ 発走前の固定記録を確認し、必要に応じて「12種類の記録をバックアップ・復元する」で保管する。サーバー永続保存と公式結果の照合はまだ別の作業。投票するならJRA公式で出走馬・取消・馬場・発走時刻を別途確認し、自分で判断する。</p>
</details>
<details><summary>端末の保存状況と再分析の差分</summary>
<p id="autoSavedStatus" class="muted" role="status">発走前の買い目は端末内の研究記録として保存できます。実購入の記録とは別です。</p>
<p id="autoFixedConsistency" class="muted" role="status">この日の最初の固定買い目と、再分析結果を比較する前です。署名検証は別操作です。</p></details>
<p class="muted">サーバー保存が未設定の間は、iPhoneの保存領域が消えると研究記録も失われる可能性があります。
<a href="/owner-backup">固定済み買い目など12種類の端末記録をバックアップする</a>。
既存の端末記録を消したり、別の版の保存内容を上書きしたりしません。</p>
<a id="autoReviewLink" href="/owner-100yen-review">固定した研究用買い目を100円仮想収支で確認</a>
</section>
<section id="forecastRacesSection">
<h2>3. 競馬場・レースを選ぶ</h2>
<p class="muted">競馬場・レースを選び、1着／2着／3着と点数を確認します（研究用の暫定案）。</p><p id="autoSummary" class="muted">未取得</p>
<p id="autoSourceSummary" class="muted" role="status">全Rの資料進捗は未取得です。</p>
<details id="autoHoldPanel"><summary>見送りの理由からレースを探す</summary>
<p class="muted">発走済み・資料不足・候補同点などの原因別に、そのレースだけを表示します。再分析や新しい買い目は作りません。</p>
<div id="autoHoldReasons" class="venue-tabs" role="group" aria-label="見送り理由で絞り込む"></div>
<p id="autoHoldStatus" class="muted" role="status">開催日を取得すると見送り理由を確認できます。</p>
</details>
<div id="autoVenues" class="venue-tabs" role="group" aria-label="競馬場を絞り込む"></div>
<label for="autoRacePick">見たいレースを選ぶ（全場・全Rから選択）</label>
<select id="autoRacePick" disabled><option value="">全Rを一覧表示</option></select>
<p id="autoViewingStatus" class="muted" role="status">レースを取得すると選択できます。</p>
<div id="autoRaces"></div>
</section>
<section id="fixedHistorySection">
<h2>4. 発走前に固定した買い目</h2>
<p class="muted">最初に保存した買い目は再分析で上書きしません。</p>
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
<a href="/owner-backup">12種類の記録をバックアップ・復元する</a>
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
<p id="autoTenStatus" class="muted" role="status">予想資料の取得後に表示します。</p>
<div id="autoTenWeights" class="ten-weights"></div>
<p class="muted">総合S：85点以上／A：70点以上／B：55点以上／C：55点未満。
10項目の根拠がそろうまでは総合点・総合順位は「未評価」です。</p>
<details><summary>正式100点の計算方法・安全確認</summary>
<p class="muted">各項目の配点に対してS＝満点、A＝2/3、B＝1/3、C＝0として足し合わせます。新100点配点（research-6）：コース・距離17／展開・脚質17／血統6／騎手・厩舎10。合計100点満点。旧70点・82点・85点の署名済み研究履歴は旧配点のまま保持し、正式100点とは混ぜません。例えば調教A＝20/30点・近走C＝0/3点・残り8項目がすべてS＝67/67点なら、合計87点のS。近走だけで総合を決めません。</p>
<p class="muted">ただしこれは<b>独立した根拠で10項目を検証できた時だけ</b>動く正式採点エンジンの計算式です。現在のJRDB調教・近走ランクは仮評価で、正式採点には昇格していません。8項目の能力判定、JRA公式の出走・取消・馬場・発走時刻の独立照合、当日馬体重、発走前の照合が不足する間は総合点・正式買い目を出しません。</p>
<p class="muted">根拠不足、発走済み、取消・出走確認の保留、点数同点の候補境界では正式3連単を作りません。表示中の3連単は引き続き2項目による研究用下書きです。</p>
</details>
</section>

</details>
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
.owner-nav{flex-wrap:wrap;gap:6px 12px;justify-content:flex-start}
.owner-nav a{display:inline-flex;align-items:center;min-height:34px;font-size:13px}
section{background:#142b43;border:1px solid #4d6b85;border-radius:14px;padding:14px;margin:14px 0}
.daily-start{border-color:#8b764b}
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
 background:#213a54;border-radius:9px;padding:8px;margin:6px 0}
.number{font-size:19px;font-weight:850;min-width:44px}
.rank{font-size:12px;min-width:43px;color:#c6d5e7}
.grade{padding:3px 7px;border-radius:6px;background:#3b5065;font-weight:800;font-size:12px}
.S{color:#f3d475}.A{color:#ffa6b1}.B{color:#a4d8ff}.C{color:#dde2ed}
.notes{font-size:12px;color:#c1d3e7;flex-basis:100%}
.formation{background:#192f46;border:1px solid #456582;border-radius:10px;padding:12px;margin:10px 0}
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
.history-coverage{border:1px solid #45617e;background:#182f48;border-radius:10px;margin:7px 0;padding:10px}
.history-coverage strong{color:#f3d475}.history-coverage p{font-size:12px;margin:4px 0}
@media(max-width:380px){.number{min-width:34px}.rank{min-width:35px}}
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
 formation_size:'買い目点数の検算',other:'未分類の照合条件'
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
      (Object.hasOwn(r,'reviewStage')&&
       (r.reason!=='missing_research'||
        !Object.hasOwn(REVIEW_STAGES,r.reviewStage)))||
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
 const combinations=dom('details',undefined,'ticket-breakdown');
 combinations.append(
  dom('summary','全'+r.points+'点の組合せを見る'),
  dom('p',r.tickets.map(t=>t.join('→')).join(' / '),'ticket-list'));
 block.append(dom('strong','3連単・2項目だけの研究用自動下書き（1着'+r.first.length+'頭）'),
  dom('p','1着：'+r.first.join('・')+'番','picks'),
  dom('p','2着：'+r.second.join('・')+'番','picks'),
  dom('p','3着：'+r.third.join('・')+'番','picks'),
  dom('p',r.points+'点／1点100円なら'+r.amountYen.toLocaleString('ja-JP')+'円（仮計算・未購入）'),
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
  '件。資料の充足・正式10項目採点・JRA公式照合は別。';
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
 const shortcut=$('autoDraftShortcut');
 shortcut.textContent='買い目あり：未取得';
 shortcut.onclick=null;
}
function render(input,day){
 const data=validate(input,day),p=data.tenFactorPreview,ctx=data.raceContext;
 const deviceExpired=new Set(data.races.filter(x=>
   x.status==='provisional_draft'&&draftExpiredOnDevice(day,x.postTime)
 ).map(x=>x.track+'|'+x.race));
 jraDraftTracks=new Set(data.races.map(x=>x.track));updateJraCrosscheck();
 const fixed=compareFixedWithDrafts(data,day);
 // The top status is written after the safe display count is known.
 // Old first-write disagreements must not count as actionable picks.
 $('autoProgrammeCoverage').textContent=programmeCoverage(data);
 $('autoReadProof').textContent=sourceReadProof(data);
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
 $('autoFixedConsistency').textContent=fixedComparisonMessage(fixed);
 $('autoSourceSummary').textContent=summarizeDaySourcePassport(
  data.sourcePassport,data.raceCount);
 for(const race of data.races){
  const key=race.track+'|'+race.race,
   changedLock=fixed.blocked.has(key),elapsed=deviceExpired.has(key);
  const detail=dom('details'),title=dom('summary',
   race.track+' '+race.race+'R '+
   (race.status==='provisional_draft'
    ?elapsed?'端末受信後に発走時刻経過・新案非表示':
      changedLock?'固定済みとの不一致・再分析案非表示':
      '研究用自動案 '+race.points+'点｜1着候補 '+race.first.join('・')+'番':'見送り'));
  detail.append(title);
  const course=courseRows.get(race.track+'|'+race.race);
  const condition=course.goingAvailable?course.going+'（JRDB資料）':'馬場未確認';
  detail.append(dom('p','コース条件：'+(course.surface||'芝・ダート未確認')+
    '／'+(course.distance_m===null?'距離未確認':course.distance_m+'m')+
    '／'+(course.turn||'回り未確認')+'／'+condition,'muted'));
  // Display validated prestart picks before long analysis; never reveal
  // new tickets after off-time or if a first-write receipt conflicts.
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
  if(race.status==='hold'){
   const extra=race.reason==='invalid_two_factor'&&
     Object.hasOwn(RUNNER_ISSUES,race.validationIssue)
     ?'（'+RUNNER_ISSUES[race.validationIssue]+'）'
     :race.reason==='missing_research'&&
       Object.hasOwn(REVIEW_STAGES,race.reviewStage)
      ?'（要確認：'+REVIEW_STAGES[race.reviewStage]+'）':'';
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
   const horses=dom('details',undefined,'horse-research');
   horses.append(dom('summary','馬ごとの調教・近走の仮評価を見る（'+
    race.runners.length+'頭）'));
   horses.append(dom('p','調教30：近走3での仮順位（10項目総合評価ではない）','muted'));
   for(const [i,h] of race.runners.entries()){
    horses.append(runnerView(h,i));
    const ten=tenRows.get(race.track+'|'+race.race).horses.find(x=>x.number===h.number);
    horses.append(renderTenHorse(ten));
   }
   detail.append(horses);
  }
  const item=data.sourceMaterials.races.find(x=>
    x.track===race.track&&x.race===race.race);
  if(item){
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
  const raceKey=race.track+'|'+race.race;
  nodes.push({key:raceKey,track:race.track,
   draft:race.status==='provisional_draft'&&!changedLock&&!elapsed,
   holdReason:race.status==='hold'?race.reason:null,node:detail});
  const option=dom('option',race.track+' '+race.race+'R｜'+
   (race.status==='provisional_draft'
    ?elapsed?'発走時刻経過・新案非表示':
      changedLock?'固定済みと不一致・新案非表示':
      '研究用下書き '+race.points+'点':'見送り'));
  option.value=raceKey;select.append(option);
  groups.set(race.track,(groups.get(race.track)||0)+1);
 }
 // Selection uses an already verified day snapshot. No extra JRDB calls,
 // no prediction reconstruction, no receipt or purchase write.
 function show(track,key='',draftsOnly=false,holdReason=''){
  // A tab or race-selection tap may happen long after the first render.
  // Re-evaluate the local clock before exposing any on-screen formation.
  const expiredNow=data.races.filter(x=>x.status==='provisional_draft'&&
   draftExpiredOnDevice(day,x.postTime)).length;
  if(expiredNow>deviceExpired.size){
   latestExpiredDraftCount=expiredNow;
   render(data,day); // Display-only, no network or receipt writes.
   $('autoStatus').textContent='受信後に発走時刻を過ぎた下書きを非表示に更新しました。';
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
 const safeDraftCount=nodes.filter(item=>item.draft).length;
 const shortcut=$('autoDraftShortcut');
 shortcut.textContent=safeDraftCount?'買い目あり '+safeDraftCount+'Rだけ見る':
  '買い目あり 0R（未作成・見送り）';
 shortcut.onclick=()=>{
  // A held HTTP response, date change, or error must not reopen old
  // predictions. This shortcut only filters the validated local result.
  if(latestDisplayedReport!==data||latestDisplayedDay!==day||
     $('autoDay').value.replaceAll('-','')!==day){
   $('autoViewingStatus').textContent='この開催日の予想は未取得です。日付を確認してください。';
   return;
  }
  select.value='';
  show('','',safeDraftCount>0);
 };
 const hiddenByFixed=Math.max(0,data.draftCount-deviceExpired.size-safeDraftCount);
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
 show('');
 const breakdown=Object.entries(data.holdReasons).sort((a,b)=>b[1]-a[1])
  .map(([reason,count])=>SHORT_HOLDS[reason]+' '+count+'R').join('／');
 $('autoSummary').textContent=data.raceCount+'R中、研究用自動案 '+
  safeDraftCount+'R／見送り '+data.holdCount+'R。'+
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
 }
 return '署名付き研究記録：新規 '+added+'R／受信後に発走時刻経過で新規保存しなかった'+
  expiredSkipped+'R／既存の固定記録は上書きせず維持。'+
  '保存先はこのiPhone内のみ（Safariとホーム画面で別の場合あり）。';
}

const WATCH_STORAGE='keiba-nine-owner-rebound-watch-receipts-v1';
const CORE_STORAGE='keiba-nine-owner-three-core-receipts-v1';
const FIVE_STORAGE='keiba-nine-owner-five-core-receipts-v1';
const R6_DRAFT_STORAGE='keiba-nine-owner-research6-draft-receipts-v1';
const STAFF_STUDY_STORAGE='keiba-nine-owner-staff-study-sessions-v1';
let request=0,followingToday=true,preflightSeq=0,
 latestDisplayedDay='',latestDisplayedReport=null,
 latestExpiredDraftCount=0,historySeq=0,watchResultSeq=0,
 prestartSeq=0,connectionSeq=0,receiptVerifySeq=0,archiveReadSeq=0,
 r6VerifySeq=0,staffArchiveVerifySeq=0,
 officialPdfSeq=0,coreVerifySeq=0,coreProviderSeq=0,fiveProviderSeq=0,
 jraDraftTracks=new Set(),jraPdfTracks=new Set(),jraPdfChecked=false,
 historyDay='',historyCoordinates=new Set(),
 historyRosters=new Map(),historyReboundWatch=new Map(),historyStyles=new Map(),
 historyGrades=new Map(),historyStatuses=new Map();
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
 $('autoPrestartRaces').replaceChildren();
 $('autoPrestartStatus').textContent='本人操作時だけ追加API照合。予想や買い目は変更しません。';
 $('autoPrestartBody').disabled=false;
 historySeq++;historyDay='';historyCoordinates=new Set();
 historyRosters=new Map();historyReboundWatch=new Map();historyStyles=new Map();
 historyGrades=new Map();historyStatuses=new Map();
 $('autoHistoryAudit').disabled=true;
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
     v.totalWeight!==100||!v.factorWeights||
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
      !Number.isInteger(race.research79ObservedCount))
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
    priorComplete+=Number(fields===4);
    observed79+=Number(horse.research79Observed);
   }
   if(seen.size!==old.size||seen.size!==source.size||
      race.priorSourceFourCompleteCount!==priorComplete||
      race.research79ObservedCount!==observed79||
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
 $('autoJraReleaseGuide').textContent=stage+
  '。GⅠ・一部重賞・変則開催は別時刻。公式の馬番・取消・馬場・発走時刻は未照合（0R）。';
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

$('autoDay').value=jstToday();
updateJraReleaseGuide();updateJraCrosscheck();
function updateReviewLink(){
 const day=$('autoDay').value;
 const valid=/^20\d{2}-\d{2}-\d{2}$/.test(day)&&
  !Number.isNaN(new Date(day+'T12:00:00Z').valueOf())&&
  new Date(day+'T12:00:00Z').toISOString().slice(0,10)===day;
 $('autoReviewLink').href='/owner-100yen-review'+
  (valid?'?date='+encodeURIComponent(day):'');
}
$('autoDay').onchange=()=>{
 ++preflightSeq;
 $('autoPreflight').disabled=false;
 $('autoPreflightStatus').textContent='選択日が変わりました。無料診断は未実行です。';
 // Preserve an explicitly selected day across subsequent app resumes.
 followingToday=false;
 latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;
 clearDraftShortcut();
 // Invalidate the old response and unlock the button. A slow old request
 // must not leave the new day permanently disabled on iPhone.
 request++;$('autoRun').disabled=false;
 updateReviewLink();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 clearHistory();
 $('autoSummary').textContent='未取得';
 $('autoSourceSummary').textContent='全Rの資料進捗は未取得です。';
 $('autoReadProof').textContent='開催日を切り替えました。JRDB資料はまだ照会していません。';
 $('autoMorningStatus').textContent='開催日の取得結果を確認中です。正式な10項目予想ではありません。';
 $('autoOperationalNext').textContent='開催日の次の操作：当日の取得結果を確認中。';
 $('autoProgrammeCoverage').textContent='開催場別の取得R数：まだ確認していません。';
 $('autoRecordSafety').textContent='固定記録の保管状態：まだ確認していません。';
 $('autoFixedConsistency').textContent='固定記録と下書きの差異は未確認。既存の記録は変更していません。';
 $('autoTenWeights').replaceChildren();
 $('autoTenStatus').textContent='10項目の評価を取得していません。';
 $('autoSavedStatus').textContent=localReceiptStatus(
  $('autoDay').value.replaceAll('-',''));
 showFixedHistory($('autoDay').value.replaceAll('-',''));
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
// A single, explicit owner gesture combines date selection and the
// existing ONE guarded owner-auto-draft request. No extra probe/read, no
// background schedule, and no second request while one is in flight.
async function quickWeekendForecast(weekday,buttonId,label,daysBefore){
 const button=$(buttonId);
 if(button.disabled)return;
 if($('autoRun').disabled){
  $('autoStatus').textContent='JRDB照会中です。完了後に'+label+'の取得を押してください。追加照会はしていません。';
  return;
 }
 const selected=nearestJstWeekday(weekday);
 const releaseDate=new Date(selected+'T12:00:00Z');
 releaseDate.setUTCDate(releaseDate.getUTCDate()-daysBefore);
 const earliest=releaseDate.toISOString().slice(0,10);
 if(jstToday()<earliest){
  $('autoStatus').textContent=label+'のクイック取得は木曜以降に利用できます。'+
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
   $('autoStatus').textContent='【'+label+'データ取得済み】この画面の取得済み研究結果を再表示しました。'+
    '追加のJRDB照会は0回。新しい資料を取得する場合は「全場・全Rを再分析する」を押してください。';
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
  // Exactly one authenticated auto-draft request. No probe, retry, or
  // background schedule; the owner must explicitly request reanalysis.
  await $('autoRun').onclick();
 }finally{button.disabled=false;}
}
$('autoSaturdayQuick').onclick=()=>quickWeekendForecast(6,'autoSaturdayQuick','土曜',2);
$('autoSundayQuick').onclick=()=>quickWeekendForecast(0,'autoSundayQuick','日曜',3);
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
 const button=$('autoRun');
 if(button.disabled)return;
 const seq=++request,day=$('autoDay').value.replaceAll('-','');
 latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;
 clearDraftShortcut();
 if(!/^20[0-9]{6}$/.test(day)){
  $('autoStatus').textContent='開催日を選択してください。';return;
 }
 button.disabled=true;$('autoStatus').textContent='JRDB資料を一括照合し、自動暫定案を作成中…';
 $('autoOperationalNext').textContent='JRDB取得・資料検証中。新しい研究用下書きの確認は完了していません。';
 $('autoReadProof').textContent='JRDB資料を照会中。番組R数・4ソース完了・署名はまだ未確認。';
 clearHistory();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
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
  const displayed=render(body,day);
  // Keep only a tiny, non-sensitive 0R read marker between Safari
  // navigation/reloads. This is NOT a cached forecast or provider response.
  // Failed/partial responses and signatures never create this marker.
  if(body.raceCount===0)recordWeekendEmptyRead(day);
  else clearWeekendEmptyRead();
  latestDisplayedReport=body;latestDisplayedDay=day;
  latestExpiredDraftCount=body.races.filter(x=>
   x.status==='provisional_draft'&&draftExpiredOnDevice(day,x.postTime)).length;
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
  // render already calculated *visible* new picks, including first-write
  // conflicts and elapsed offs. Do not overwrite with raw draftCount.
  $('autoSavedStatus').textContent=body.archiveEnabled
   ?'サーバー固定済み '+body.archiveRecordCount+'R／前の買い目を優先したレース '+
     body.archiveConflictCount+'R。'+localStatus
   :'サーバー保存は未設定。'+localStatus;
  showFixedHistory(day);
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
 }catch(error){if(seq===request){
  latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;
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
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
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
  $('autoFixedConsistency').textContent=storageFailure
   ?'【保存記録の確認が必要】端末への新規固定に失敗したため、新しい買い目は表示していません。以前の固定済み研究記録は変更していません。'
   :'今回の再分析結果は未確認です。以前の固定済み研究記録は変更していません。';
  $('autoMorningStatus').textContent=storageFailure
   ?'JRDBの暫定案を取得しましたが、端末への新規固定保存に失敗。新しい3連単は非表示。以前の固定記録は変更していません。'
   :'JRDB資料を安全に取得できず、新しい暫定予想は表示していません。以前の固定済み研究記録は変更していません。';
  $('autoOperationalNext').textContent=storageFailure
   ?'【端末保存失敗・新規下書きなし】既存の固定履歴を先に確認して、同じiPhoneのバックアップを安全に保管してください。保存できる状態になってから発走前に再取得してください。'
   :networkFailure
   ?'【通信切断・新規予想なし】端末の回線とRenderの稼働を確認。保存済み固定履歴はそのままです。処理の成否が不明な間、追加の有料JRDB照会を連打しないでください。'
   :gatewayFailure
   ?'【Renderの状態確認】502/503/504はネットワークや実行環境の問題でも発生します。既存の固定履歴を確認し、Renderの稼働状況・非公開の処理ログを確認してください。原因が分かるまで追加の有料JRDB照会を連打しないでください。'
   :'【取得失敗・新規予想なし】上の停止工程と401/403/429等の原因表示を確認。日付・接続設定・利用権限を見直し、既存の固定履歴を先に確認してください。JRA公式照合と正式100点予想は未完了です。';
  $('autoProgrammeCoverage').textContent='取得失敗：開催場別R数は確認できません。';
  $('autoReadProof').textContent='【照会失敗】番組・出走馬・調教・近走の取得完了は未確認。新規予想・署名を確認できません。';
  $('autoRecordSafety').textContent=storageFailure
   ?'【端末への新規固定失敗】新しい買い目は非表示。既存の固定記録は削除・上書きしていません。バックアップ・署名確認を優先してください。'
   :'新規記録なし。以前の固定記録は下の履歴で確認してください（署名は別操作）。';
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
      '｜研究用'+(horse.evidenceScore79===null?'未評価':
      ' '+horse.evidenceScore79.toFixed(2)+'/79点')+
      '（正式得点ではありません）','muted'));
    }
    card.append(panel);
   }
   if(details.rosterVerified&&details.threeFactorSourceGaps){
    const s=details.threeFactorSourceGaps,p=dom('details'),
     labels={course_distance:'コース・距離',pace:'展開・脚質',ground:'馬場'};
    p.append(dom('summary','コース17・展開17・馬場12：採点前の資料不足を確認'));
    p.append(dom('p','46点分の過去資料を照合。ただし資料があるだけでは'+
     '能力点にはなりません。JRA公式照合、発走前時刻の確認、'+
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
     p.append(dom('p',h0.number+'番｜コース・距離 '+
      (h0.sourcePresent.course_distance?'資料あり':'不足')+
      '／展開・脚質 '+(h0.sourcePresent.pace?'資料あり':'不足')+
      '／馬場 '+(h0.sourcePresent.ground?'資料あり':'不足')+
      '｜不足：'+missing+
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
    const names={pedigree:'血統',draw_weight:'枠斤量',
     jockey_stable:'騎手厩舎',rotation:'ローテ',body_condition:'当日馬体重'};
    for(const horse of r.horses){
     panel.append(dom('p',horse.number+'番｜新79点研究 '+
      (horse.research79Observed?horse.research79.toFixed(2)+'/79':'未評価')+
      '｜残り21点の資料カバー配点相当 '+
      horse.sourceFieldCoverageEquivalent21+'/21（得点ではない）'+
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
     pedigree:8,draw_weight:3,jockey_stable:2,rotation:1,body_condition:1
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
      '｜資料カバー配点相当 '+coveredWeight+'/15（実得点ではない）'+
      '｜不足 '+missing.map(k=>shortNames[k]).join('・')+
      '（正式採点0/10）','muted'));
    }
    ten.append(dom('p','残り15点の資料準備：前日4分野の資料が全部そろう馬 '+
     fourSourceReady+'/'+details.tenInventory.runnerCount+
     '頭。当日馬体重は未取得なので資料カバーは最大14/15。'+
     '資料カバー配点は能力点・予想スコア・S/A/B/Cではありません。','muted'));
    card.append(ten);
   }
   if(details.rosterVerified&&details.pedigreePreflight){
    const p=details.pedigreePreflight,panel=dom('details');
    panel.append(dom('summary','血統8点の採点準備を見る（正式未評価）'));
    panel.append(dom('p','父・母父が分かるだけではコース・距離・馬場適性は判定できません。血統別の独立した過去実績と未来情報を除いた期間検証が必要です。今は血統S/A/B/Cも8点の実得点も付けません。','muted'));
    panel.append(dom('p','父・母父の資料が両方ある馬 '+
     p.parentageCompleteCount+'/'+p.runnerCount+
     '頭。血統の能力評価まで確認できた馬 0/'+p.runnerCount+'頭。','muted'));
    for(const horse of p.horses){
     const state=horse.parentageComplete?'両方あり':
      horse.parentageSourceState==='partial_fields_observed'?'一部不足':'両方不足';
     panel.append(dom('p',horse.number+'番｜父・母父 '+state+
      '／同条件の血統実績 未接続／時系列検証 未実施'+
      '／血統8点 未評価（予想には反映しません）','muted'));
    }
    card.append(panel);
   }
   if(details.rosterVerified&&details.supportSixPreflight){
    const p=details.supportSixPreflight,panel=dom('details');
    panel.append(dom('summary','枠斤量・騎手厩舎・ローテ6点の採点準備（正式未評価）'));
    panel.append(dom('p','枠斤量3・騎手厩舎2・ローテ1。今は資料があるかだけを確認。同条件の有利不利や成績差・休み明け適性の検証は未完成で、資料が全部あっても実得点は0点ではなく未評価です。','muted'));
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
     panel.append(dom('p',h.number+'番｜枠斤量 '+explain[h.sourceStates.draw_weight]+
      '／騎手厩舎 '+explain[h.sourceStates.jockey_stable]+
      '／ローテ '+explain[h.sourceStates.rotation]+
      '｜資料カバー配点相当 '+h.fieldPresenceWeight+'/6（実得点ではない）'+
      '｜正式6点 未評価（3項目とも能力判定なし）','muted'));
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
  $('autoHistoryAuditStatus').textContent='過去番組の追加照合 '+raw.draCalls+
   '回／馬場 '+raw.dkaCalls+'回。未取得の過去レース '+raw.deferredPastRaces+
   '件。'+(raw.historyComplete?'指定範囲を照合済み。':'履歴に未確認あり。')+
   ' 予想・購入・保存済みの買い目は変更しません。';
 }catch(_){if(seq===historySeq){
  $('autoHistoryAuditRaces').replaceChildren();
  $('autoHistoryStaffStatus').textContent=
   '騎手・厩舎の資料確認に失敗。既存の買い目や成績は変更していません。';
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
 latestDisplayedReport=null;latestDisplayedDay='';latestExpiredDraftCount=0;
 clearDraftShortcut();
 ++preflightSeq;
 $('autoPreflight').disabled=false;
 $('autoPreflightStatus').textContent='開催日が変わりました。無料診断は未実行。';
 request++;$('autoRun').disabled=false;
 $('autoDay').value=today;
 updateReviewLink();
 $('autoRaces').replaceChildren();$('autoVenues').replaceChildren();
 $('autoHoldReasons').replaceChildren();
 $('autoHoldStatus').textContent='開催日を取得すると見送り理由を確認できます。';
 $('autoRacePick').disabled=true;
 $('autoRacePick').replaceChildren();
 $('autoRacePick').value='';
 $('autoViewingStatus').textContent='レースを取得すると選択できます。';
 clearHistory();
 $('autoSummary').textContent='未取得';
 $('autoSourceSummary').textContent='全Rの資料進捗は未取得です。';
 $('autoReadProof').textContent='開催日を切り替えました。JRDB資料はまだ照会していません。';
 $('autoMorningStatus').textContent='開催日の取得結果を確認中です。正式な10項目予想ではありません。';
 $('autoOperationalNext').textContent='開催日の次の操作：当日の取得結果を確認中。';
 $('autoProgrammeCoverage').textContent='開催場別の取得R数：まだ確認していません。';
 $('autoRecordSafety').textContent='固定記録の保管状態：まだ確認していません。';
 $('autoFixedConsistency').textContent='固定記録と下書きの差異は未確認。既存の記録は変更していません。';
 $('autoTenWeights').replaceChildren();
 $('autoTenStatus').textContent='10項目の評価を取得していません。';
 $('autoSavedStatus').textContent=localReceiptStatus(today.replaceAll('-',''));
 showFixedHistory(today.replaceAll('-',''));
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
function autoFetchOnRegularRaceDay(){
 const day=$('autoDay').value;
 const dt=new Date(day+'T12:00:00Z');
 const normalWeekend=Number.isFinite(dt.valueOf())&&
  dt.toISOString().slice(0,10)===day&&[0,6].includes(dt.getUTCDay());
 if(normalWeekend){
  if(recentWeekendEmptyRead(day.replaceAll('-',''))){
   $('autoStatus').textContent='【前回の番組0Rを確認済み】同じ端末で30分以内に番組0件を取得したため、画面を開き直した際の自動JRDB照会は控えました。開催なしとは断定していません。配信更新後の再確認は「全場・全Rを再分析する」を押してください。';
   $('autoMorningStatus').textContent='この画面では新しい番組・買い目は未取得。前回の番組0Rにより再照会を控えています（予想生成成功ではありません）。';
   $('autoOperationalNext').textContent='【追加照会0回】配信更新を確認したい場合は「全場・全Rを再分析する」。以前の固定買い目は下で確認できます。';
   return;
  }
  $('autoRun').onclick();
  return;
 }
 $('autoStatus').textContent='平日はJRDBの自動照会を控えています。土曜日・日曜日は上のボタンで選択。祝日の変則開催は日付を選んで「全場・全Rを再分析する」を押してください。';
 $('autoMorningStatus').textContent='平日・変則開催の自動取得は停止中（有料照会0回）。取得するには手動で再分析してください。';
 $('autoOperationalNext').textContent='次の通常開催：土曜日・日曜日を選ぶ。平日の特別開催はJRA公式で確認後に手動取得。';
}
if(typeof document.addEventListener==='function')
 document.addEventListener('visibilitychange',resumeOwnerDay);
if(typeof window!=='undefined'&&typeof window.addEventListener==='function')
 window.addEventListener('pageshow',event=>{if(event.persisted)resumeOwnerDay();});
// Opening an authenticated owner page auto-reads only on regular weekends.
// Special weekday races are explicit manual reads. No polling or purchase.
if(document.visibilityState!=='hidden')autoFetchOnRegularRaceDay();
})();"""
