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
