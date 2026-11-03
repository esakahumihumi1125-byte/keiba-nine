# KEIBA NINE — private evidence readiness (JRDB beta; not activated)

This is a **private diagnostic only**. It does not produce races predictions,
rank horses S/A/B, or place bets. It never copies JRDB content to GitHub Pages
or the public JSON feed.

## Sources and functionality

On the existing **owner-authenticated**, separately hosted Python service:

- `/tra`: race programme, date, track and expected headcount.
- `/tky`: horse entry number and horse ID for matching.
- `/tcy`: current-week workout analysis indicators; last-week fields checked separately.
- `/tze`: up to five past-run dates. No result on/after the target race date is counted.

The new private `/api/jrdb/evidence?date=YYYYMMDD` route runs read-only
requests and returns only counts **per race**, such as programme runners,
observed entry rows, workout indicators, last-week indicators and previous-race
history indicators. It does not return horse names, JRDB metrics or model tips.

Training can have a missing horse number; the adapter joins by the 12-character
horse ID when the current horse entry is uniquely identified. Contradictions
cause a redacted error. All work is in memory. No data is persisted.

The private iPhone console's **調教・近走の資料状況を確認** button now
shows, for each race, how many registered horses have no matched current
workout record, prior-week record, or previous-race date in the beta source.
These are reported as `trainingUnaccounted`, `lastWeekUnaccounted` and
`pastRunUnaccounted`. The optional `evidenceGaps` contains Japanese
data-presence labels only, never horse IDs, names or source metrics.
The response additionally contains `gapRaceCount` and `unaccountedTotals`
across the source programme; it makes no claim that the source programme
covers every official JRA race.

**Unaccounted is not a diagnosis of a missing upload or an invalid race.**
First-time starters can have no previous runs, and a provider may legitimately
have no prior-week workout field. A fully zeroed unaccounted summary is
**not** a validated runner list, real prediction or wagering recommendation.

This is merely an audit of **data presence**, not data completeness or quality.
A zero past-run count can be entirely legitimate for first-time starters.
Matching numbers alone do not prove the entry set is complete or cancellations
are reflected. Even when all records are present, the API reports
`predictionsReady: 0` and `fullyVerifiedRaces: 0`.

## 10項目評価への準備段階（2026-11-03）

本人専用の `/api/jrdb/evidence?date=YYYYMMDD` は、
従来の資料件数のほかに `assessmentPreflight` を返します。
`scripts/jrdb_factor_preflight.py` が、**すでに集計・照合された件数だけ**を
10項目の研究評価基準（調教、近走、コース・距離、展開、馬場、血統、
枠・斤量、騎手・厩舎、ローテ、馬体）に整理します。

- 調教・近走：「資料件数一致」「一部あり」「記録なし／新馬など対象外の可能性」を区別。
- 残り8項目：現状は「提供元データからの自動紐付け未実装」と明示。
- **10項目すべてで** `grade: 未評価`、`assessmentComplete: false`。
- `gradedFactors: 0`、`readyForPrediction: 0` のまま保持。
- 本人専用iPhone画面ではレースごとに「10項目の評価準備を見る」を展開できる。
- 元の馬名、馬ID、調教指数、有料の競馬データ、認証キーを応答にコピーしない。

**資料件数が一致しても実戦の予想を許可しません。** その後は提供元の利用条件と
原データの仕様を確認し、各評価の根拠・発走前の時刻・馬場／取消／出走馬名を
独立に検証する必要があります。現在の研究用の重みやS/A/B/C閾値は仮説であり、
予測精度と回収率の実績を示すものではありません。

## 調教指数からの暫定S/A/B/C提案（研究用のみ）

`scripts/jrdb_training_hypothesis.py` は、JRDBの `/tcy` に含まれる
`oikirisisu`（追切指数）と `siagarisisu`（仕上指数）を読み、
**両方の指数が揃っている馬に限り**、競馬ナイン独自の暫定ランクを計算します。
出典：https://jrdb-api.keiba.bigtime.world/docs/fields
（公式フィールド説明では、高い値の方が良く、60を基準とします。）

独自の仮閾値は、２指数の低い方で S=75以上、A=60以上、
B=45以上、C=45未満。**正式なJRDBランクではありません。**
数字の根拠は過去の回収率・勝率で較正しておらず、
データの傾向を試すための研究仮説です。どちらかが未提供なら「未評価」にします。
馬IDと馬番の照合が曖昧・矛盾する場合や、指数の形式が異常な場合は処理を止めます。

本人専用 `/api/jrdb/evidence` の `trainingHypothesis` は、
レースごとの S/A/B/C/未評価の**頭数だけ**を返し、
個別の馬名・馬ID・元の指数・買い目を公開しません。
10項目の総合評価には昇格させず、`assessmentPreflight` は
未評価のまま、`predictionsReady=0` のまま維持します。
実際に使うにはβ版専用APIアカウントと、安全な非公開HTTPSサーバーが必要です。

## 近走（/tze）の暫定S/A/B/C分析

本人専用の `scripts/jrdb_recent_hypothesis.py` を追加し、
`/tze` の直近最大5走データから、**着順と成績IDMが両方確認できる
新しい順の最大3走**を暫定評価します。少なくとも2走必要です。
新馬、近走の不足、IDMの欠損は「未評価」とし、未出走の成績を作りません。

- 直近から順に3:2:1の重みでIDMを平均する。
- S=70以上、A=55以上、B=40以上、それ未満Cは**競馬ナイン独自の未検証仮説**。
  JRDB公式ランク・勝率・期待値を示す数値ではありません。
- 4角通過順（4番手以内の回数）・上がり3Fは、直近の情報量として別途件数を示す。
  違うコース・馬場の上がり時計を直接比較して強弱を断定しない。
- /tzeの主要項目には**着差・対戦相手の実力を直接比較する数値が揃わない**。
  現時点でこれらを補完して評価したことにはしない。
- 人気順位・単勝オッズのフィールドは計算には使用しない。
- 同じ馬の重複レコード、馬ID・馬番の矛盾、開催日より未来の過去走、
  形式不正な数字は処理を拒否する。

本人専用の `/api/jrdb/evidence` は新たに `recentHypothesis` を返します。
これは日付・競馬場・レースごとの**各ランクの頭数と観測数だけ**。
馬名・馬ID・着順・成績IDM・有料データをブラウザーへコピーしない。
この部分だけでは馬場・距離適性・血統・展開・取消を評価できないため、
`predictionsReady=0` のまま、総合S/A/B/Cや買い目には反映しません。

利用したフィールド名の参照元：JRDB-API
<https://jrdb-api.keiba.bigtime.world/docs/fields>
（`race_back_N_racedate`、`race_back_N_order_of_finish`、
`race_back_N_idm`、`race_back_N_corner4_order`、
`race_back_N_later3f_time`）。

## 調教＋近走の両方がそろった馬の頭数

`scripts/jrdb_dual_factor_readiness.py` は本人専用環境のメモリ内で、
調教と近走の**暫定ランクが両方計算できたか**を同じ馬番に対して照合します。
取得した日付・競馬場・レース・馬番に不一致があれば処理を停止します。

ブラウザーに返す `dualFactorReadiness` はレース単位の
`both`、`trainingOnly`、`recentOnly`、`neither`、`runnerCount`
の頭数だけ。馬番、IDM、指数、元の着順は渡しません。
本人用画面に「調教・近走の両方が暫定評価可能：○/○頭」と表示します。

この段階で**まだ8項目の評価が未確認**であり、調教・近走の
独自仮ランクを総合評価へ昇格させることも、実レースの
3連単の買い目を作成することもしません。利用先は私用の準備診断のみです。

## コース・距離・馬場・4角位置の前処理（2026-11-03）

**コース・距離と馬場の客観的な取得**：

- JRDB公式 `/tra` にある `track_type`（芝/ダート/障害）、
  `distance`（距離）、`turn_cd`（右/左/直線）を安全に正規化します。
- 追加した本人専用の `/tka` 取得処理は、開催日の芝/ダート馬場状態を取得します。
  `holdingkey` の競馬場コード・日付を番組データと照合します。
  日付・競馬場の不一致、重複開催データ、存在しない馬場状態コードは拒否します。
- 本人認証付きの `/api/jrdb/context?date=YYYYMMDD` は、
  レースごとに距離・芝ダート・回り方向・馬場の現在の**取得状況**のみ返します。
  `updated_at` の存在は検査しますが、リアルタイム最新性の保証には使いません。
- 障害や不明な馬場は「未確認」で保持。新たな馬場コードを推測しません。
- `courseInfoPresentCount` と `goingAvailableCount` は情報の存在数であり、
  競走馬のコース適性・不良馬場適性を示しません。
  `horseCourseSuitabilityAssessed=false` と
  `horseGoingSuitabilityAssessed=false` を維持します。

**過去走の4角位置は展開の参考資料のみ**：

- `scripts/jrdb_position_observations.py` は、近走最大3走の4角通過順のうち
  2走以上を観測できた馬について、4番手以内の観測が多いか、
  後方観測が多いか、混在しているかを内部で集計します。
- ブラウザーへ出るのは各傾向の**頭数のみ**で、馬番・馬ID・原データは返しません。
- 距離・相手・馬場・ペースの違いを補正していないため、
  この集計だけで逃げ馬、先行力、ハイペースを断定しません。
- `paceForecastAvailable=false`、`predictionReady=false`。
  総合S/A/B/Cや3連単の実戦買い目にはまだつなぎません。

資料元：
<https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tra> /
<https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tka> /
<https://jrdb-api.keiba.bigtime.world/docs/fields>。

## 馬ごとの過去コース・距離照合（研究用・実接続前）

追加した `scripts/jrdb_course_history.py` は、JRDB `/tze` の
`race_back_N_racedate` と `race_back_N_racekey` を
過去番組 `/dra` の `racedate`・`racekey` に**完全一致**で結合する
非公開の照合エンジンです。日付の違う過去レースや不正なキーは拒否します。

履歴が照合できた場合のみ、内部では各馬について
「芝/ダートの種別一致」「距離差が200m以内」「同じ競馬場」「同じ回り」の
観測数と、同じ芝ダートかつ近い距離での3着以内の**記録件数**を数えます。
200mは研究用の比較幅であり、適性を保証する根拠ではありません。
距離が未確認なら不一致と断定せず、未照合として扱います。

ブラウザーへ出すための `summarize_course_history_observations` は、
レース単位で「過去番組が結合できた走数」「照合できない走数」
「比較できる走歴のある頭数」「2走以上ある頭数」の**合計のみ**を返します。
馬番・馬ID・有料の過去走成績・レースキー・馬名は返しません。
`courseSuitabilityAssessed` と `goingSuitabilityAssessed` は常に偽で、
S/A/B/Cの自動付与や3連単・実戦記録への反映はありません。

また、`scripts/jrdb_private.py` に `fetch_historical_race_program(racekey)`
を追加。1回につき厳密な8文字レースキーで過去番組 `/dra` の
**1レースだけ**を要求し、日付範囲の大量取得は許可しません。
β版の認証情報がないので、実際のJRDB通信は行っていません。
この呼出しは現時点で画面や自動実行フローにつないでおらず、
予期しないAPI通信はありません。

### 残る課題

- 本人専用サーバーの安全な設置と、JRDB β専用の認証情報の発行
- `/dra` の履歴データを**取得回数上限付きで**必要なレースに結ぶオーケストレーター
- 過去開催の `/dka`（過去の馬場状態）による日付一致と、今回の馬場との比較
- 出走取消・当日馬場の確認、相手レベルの補正、コース・距離のサンプル数と
  評価基準のバックテスト。これらが終わるまで実戦の適性ランクは出さない

公式仕様：
<https://jrdb-api.keiba.bigtime.world/docs/endpoints/history/dra>
<https://jrdb-api.keiba.bigtime.world/docs/endpoints/history/dka>。

## 重・不良馬場の履歴照合（2026-11-03・実接続前）

追加した `scripts/jrdb_going_history.py` は、既存の `/tze` → `/dra`
過去レースキーと日付の一致を必須にした上で、過去 `/dka` の
開催キー（レースキーの先頭6文字）と開催日の一致を検査します。
JRDBの開催キーには小文字 a〜f が入ることがあります。

- 今走と同じ芝/ダートかつ距離差200m以内の過去走について、
  重（03）・不良（04）で走った件数、3着以内の記録件数を別々に数えます。
- 当日 `/tka` の馬場状態が取得できた場合のみ、同じ馬場の比較走数を数えます。
- 過去の馬場・番組が不足すると「未照合」。不適性とは判断しません。
- 日付・開催キー不一致、重複、無効コードは拒否します。
- ブラウザー向けの診断集計はレース単位の件数のみ。
  馬番・馬ID・馬名・過去個別成績・レースキーは出しません。

`scripts/jrdb_private.py` の `fetch_historical_venue_conditions(racekey)` は
非公開環境から `/dka` の単一レースキーだけを要求します。
広範囲の日付一括取得やGitHub Actionsからの実接続を許しません。

**実際のJRDB接続、本人専用サーバー画面への接続、馬場適性ランク、
10項目総合評価、本番3連単自動予想は未完成です。**
ここでは過去の観測件数を整理するだけで適性・勝率を推定していません。

参照：https://jrdb-api.keiba.bigtime.world/docs/endpoints/history/dka

## 本人用・取得上限付きの過去照合（2026-11-03）

`scripts/jrdb_history_pipeline.py` で、照合可能な直近の過去レースキーを
新しい日付順に重複排除し、**1回最大8レース（内部の絶対上限12）**から
過去番組 `/dra` と過去開催 `/dka` を照合するプランを実装しました。
同じ開催日の `/dka` 取得は1回にまとめ、不要な重複アクセスを避けます。
デフォルト8レースなら過去APIへの呼び出しは最大16回です。
このほか、開催当日の `/tra`、`/tky`、`/tze`、`/tka` の取得が必要です。

- 参照可能な過去の8文字レースキーだけを要求し、日付範囲の検索はしません。
- 過去走の日付だけでキーがない履歴、上限を超えた履歴、API結果が空の履歴は
  それぞれ未照合と扱い、照合済み／不得意と誤表示しません。
- 過去番組と過去馬場のキー・日付の不一致は処理を中止します。
- 通信エラーのレスポンス本文・認証キーはエラーとして返しません。
- 過去の馬名、馬番、個別着順、過去キーはブラウザーに送らず、
  レース単位の観測件数だけを本人用HTTPS画面に表示します。

`scripts/private_service.py` の本人認証付き
`POST /api/jrdb/history` は明示的に押すボタン専用です。
本人専用HTTPSサーバーで **JRDB_PRIVATE_ENABLED=1、KEIBA_HISTORY_ENABLED=1**
の両方を設定し、さらに有効な認証情報がある時だけ実行可能です。
**サーバー起動・アプリ閲覧・GitHub Actions実行・日次通知からは
この過去APIを自動実行しません。** 画面の実行ボタンを押す度に取得が起きます。

この変更で本人用の操作手段は準備できましたが、実際の
JRDB β認証情報と本人専用HTTPSサーバーの設置は未完了です。
予想・ランク・買い目には未接続で、回収率の検証もしていません。

## 過去実績の資料充足度・未照合表示（2026-11-04）

`scripts/jrdb_history_evidence_quality.py` を追加しました。
非公開の過去照合結果を、レースごとの **資料がある頭数** に変換します。
馬名・馬番号・過去の個別着順・有料指標などは出力しません。

- コース・距離：芝/ダートが一致し距離差200m以内の比較走歴を
  **0走／1〜2走／3走以上** の頭数に分類します。
- 馬場：同条件で過去の馬場まで確認できる比較走歴を
  **0走／1〜2走／3走以上** の頭数に分類します。
- 過去の日付付き記録がない頭数、過去番組の未照合が残る頭数と
  件数、開催日の馬場記録の有無も分けて表示します。
- 資料集計で矛盾する件数、負の件数、5走超の架空履歴、重複レースは
  拒否し、予想済みとして扱いません。

過去資料が **3走以上あることは統計上の信頼度を証明しません。**
また、0走に分類された理由には、新馬・未取得・芝ダート不一致・
距離が異なる場合などがあります。得意不得意を推定しないように、
`predictionConfidenceAssessed=false`、`suitabilityAssessed=false`、
`predictionReady=false` を維持します。

本人専用 `POST /api/jrdb/history` の応答に
`evidenceQuality` を追加。iPhone画面の過去馬場照合ボタンの結果として
距離・馬場の各比較走数の頭数と、未照合の過去番組件数を表示します。
従来の手動実行・本人認証・HTTPS・最大8レース照合・秘密情報非公開の
条件は維持され、公開GitHub Pages、実戦記録、3連単の買い目は変更しません。

今後のS/A/B/C適性評価には、取得元と取消情報の独立検証、
各競馬場・距離・馬場での標本数と予想精度のバックテストが必要です。

## 10項目資料表の統合（2026-11-04・非公開研究画面のみ）

新設の `scripts/jrdb_ten_factor_materials.py` が、同一の開催日として
照合済みの出走馬・調教・近走資料件数と、非公開の過去コース/馬場履歴の
比較できる走数を **10項目の資料準備表** として結合します。

- 調教：調教レコードが確認できた頭数。
- 近走：日付のある近走レコードが確認できた頭数。
- コース・距離：同じ芝/ダートで距離差200m以内の走歴がある頭数。
- 馬場：その条件で過去の馬場状態まで確認できる走歴がある頭数。
- 展開・脚質、血統、枠/斤量、騎手/厩舎、ローテ、馬体の残り6項目は
  **まだ同じ評価表に結び付いておらず、未接続** と表示します。

資料件数が合致しても根拠の質・予想精度を検証した意味ではありません。
`gradedFactors=0`、全項目 `grade=未評価`、
`predictionReady=false`、`bettingReady=false` を維持します。
調教・近走がない理由には新馬や未提供も含まれます。
過去履歴が上限や欠損で未照合の場合、コース/馬場の資料状態は
`historical_lookup_incomplete` とし、完全に比較できたと誤表示しません。

本人専用の `POST /api/jrdb/history` では、明示操作時に限り
従来の `/tra` `/tky` `/tze` `/tka` に加えて `/tcy` を取得し、
馬ID・開催日を確認してから、上限8レースの過去 `/dra` `/dka` を照合します。
本人用画面には **レース別の集計頭数のみ** を返します。
馬名、馬番、個別のJRDB指標、過去レースキー、認証情報は渡さず、
GitHub Pages・公開JSON・既存の実戦馬券記録には反映しません。

これは10項目の予想・S/A/B/C総合ランク・3連単生成の完成ではありません。
本番には利用許諾を確認したデータ取得、出走取消と当日馬場の照合、
根拠付き評価・バックテスト・本人専用HTTPSサーバーの有効化が必要です。

## 出走取消・当日馬場・発走時刻の提供元確認（2026-11-04）

新しく `scripts/jrdb_race_day_gates.py` を追加。公開用でなく、
本人認証付きHTTPSサーバー内で `/tra` 番組、`/tky` 出走馬、
`/tka` 開催馬場の**元データの有無と整合性**を確認します。

- `/tky.withdrawn_flag` は `0`（提供元で取消報告なし）と
  `1`（提供元で取消報告あり）を区別し、欠損は「未確認」とする。
- 未知のフラグ、重複馬番、違うレース・開催日などは処理を拒否する。
- レースごとに取消報告がある頭数、フラグが未確認の頭数、
  芝・ダート馬場情報の有無、更新日時の記録有無、番組の頭数照合結果を示す。
- 提供元での取消報告がゼロでも **JRA公式での取消・除外確認が必要**。
- 馬場の更新日時が記録されていても、最新の当日馬場と保証しない。
- 発走時刻の記録があってもJRA公式の時刻変更が反映済みとは保証しない。

本人専用 `GET /api/jrdb/race-day?date=YYYYMMDD` は利用者の
明示操作時だけ開催日の `/tra`・`/tky`・`/tka` を取得して、
レースごとの件数と未確認状態を表示する。APIキー、馬ID、馬名、
個別フラグ・レースキーや有料指数は返さない。
GitHub Pagesなどの公開環境では実行しない。

また `/tka` 開催キーの検査を数字のみから小文字16進6文字へ拡張。
JRDB公式仕様では開催日目に `a`〜`f` が入ることがある。

**JRA公式の独立データを自動取得する仕組みは今回まだ追加していない。**
どのレースも `officialScratchesVerified=false`、
`officialGoingVerified=false`、`officialPostTimeVerified=false`、
`predictionReady=false`、`bettingReady=false` とする。
検証済みとして扱うにはJRA公式の取消・馬場・発走時刻との照合と
適切な更新時刻管理が必要。

参照：
https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tky
https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tka
https://jrdb-api.keiba.bigtime.world/docs/fields

## 発走前の時刻・馬場更新の鮮度判定（2026-11-04）

`scripts/jrdb_prestart_freshness.py` により、本人用サーバーの**日本時間**で
発走予定までの時間と、JRDB `/tka` の更新日時（あれば）を比較します。
検査の時計はサーバー内で作成し、スマートフォンの入力やURLパラメータを
信用しません。日時はオフセット付きの ISO 8601 として検証します。

- 開催日が当日か、発走予定時刻が過ぎていないか、発走まで2時間以内か、
  2時間以上先か、発走時刻が未確認かを区別します。
- `/tka.updated_at` が存在する場合は、その記録から何分経過したかを
  数えます。**60分以内は画面を整理するための暫定区分**であり、
  JRAの公式確定・最新の出走取消・馬場やその正確さを保証しません。
- 更新時刻の記載がない、未来日時、違う開催日の馬場情報、馬場未確認は
  それぞれ未確認・古い可能性のある資料として明示します。
- 発走予定時刻が過ぎたレースを購入可能に戻したり、WIN5の締切後に
  買い目変更を許す動作はありません。

本人専用の `/api/jrdb/race-day` に `prestartFreshness` を追加し、
レースごとの照合準備状況だけをiPhone向けの本人認証画面に表示します。
JRA公式の出走取消・馬場状態・発走予定時刻は現段階で**自動取得していません**。
そのため公式照合フラグは全Rで false、
`officiallyVerifiedRaces=0`、`predictionReady=false`、
`bettingReady=false` を必ず維持します。

本人専用画面には [JRA公式の競馬メニュー](https://www.jra.go.jp/keiba/)
への外部リンクを表示します。これは公式サイトを**人が確認するため**の
リンクであり、リンク先を自動解析したり公式データを検証したものではありません。
JRAのFAQでも当日の馬場情報は「今週の開催お知らせ」に掲載されると説明。
https://www.jra.go.jp/faq/pop02/2_3.html

次の開発課題は、利用が許可された独立データ取得手段の検討、
取消・騎手変更・当日馬場・発走時刻の比較、変更後の再照合、
取得タイミングの証跡管理。現段階の時刻分類では本番予想の有効性を主張しません。

## JRA独立資料との照合エンジン（2026-11-04・実接続前）

`scripts/jra_reference_compare.py` に、別の取得元から渡された**構造化された
出走情報の写し**と、JRDB `/tra`・`/tky`・`/tka` を照合する
非公開・オフライン比較器を追加しました。現時点では実際のJRA公式データを
取得するアダプターやJRAの認証付きフィードは**接続していません**。
手入力・許可済みアダプター候補を想定したデータ形式であり、
入力の名前がJRAでも正当な出所・最新性を証明するものではありません。

- 開催日・競馬場・レース番号・馬番（非公開内部のみ）を照合。
- 出走取消状態、騎手コード、芝/ダート・馬場、発走予定時刻、
  出走馬一覧の一致・差分を、レース単位の**件数とカテゴリ**で報告。
- 欠けた馬番・取消フラグ・騎手コード・馬場は未知として区別。
  一部の情報だけ一致した場合も「完全一致」にはしません。
- 不正日付、知らない競馬場、重複馬番、無効な取消状態、
  不正な騎手コード、追加の想定外フィールドは拒否。
- ブラウザーへは差分の**集計件数のみ**返し、馬番・馬名・
  騎手コード・過去レースキー・有料の馬ごとデータは返しません。

本人用 `/api/jrdb/race-day` は現時点で
`independentComparison.racesMissingReference == raceCount` とし、
**独立JRA参照は未接続**と明示。オンラインのJRAデータを
新たに取得したり、画面から不審な公式スナップショットを送信したりしません。

差分ゼロでも `independentSnapshotAuthenticated=false`、
`referenceCollectionFreshnessVerified=false`、
`officialJraFinalVerification=false`、
`predictionReady=false`、`bettingReady=false` を厳守。
将来は、利用条件を確認した独立データの取得・出所認証・
記録時刻と変更履歴の検証・JRA公式との最終突合を別実装で追加する必要があります。

## Source documentation verified

- https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tra
- https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tky
- https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tcy
- https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tze
- https://jrdb-api.keiba.bigtime.world/docs/fields

Provider data may be held and transformed only inside the **user's own
non-public environment**. Merely obscuring a GitHub Pages URL is not access
control. The ordinary personal membership does not permit publishing JRDB-
derived predictions to the general public.

## Security and activation

- API beta credentials have not been issued/configured.
- This repository is **public**. Do not commit any key, member login/password,
  raw JRDB response, derived private prediction, `.env` file or paid dataset.
- The private HTTPS hosting server is **not** deployed, and use of this source
  is disabled until after a real account, secrets and secure owner access exist.
- GitHub Actions tests use synthetic samples and may **never** call JRDB live
  endpoints; `GITHUB_ACTIONS=true` blocks the client.
- When testing real beta API responses in private, revalidate field names and
  record shape against the official documentation (especially horse identity
  and previous-race dates) before allowing any predictions.
- No OpenAI API or model call is included. ChatGPT scheduled tasks are not a
  bridge to the user's public GitHub Pages instance.

## Validation

`python -m unittest discover -s tests -p 'test_*.py'`

The suite asserts safe denials, duplicate identifiers, bad history dates,
source separation, and no leakage of paid horse-level data.
