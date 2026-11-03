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
