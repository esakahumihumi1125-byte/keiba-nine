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

This is merely an audit of **data presence**, not data completeness or quality.
A zero past-run count can be entirely legitimate for first-time starters.
Matching numbers alone do not prove the entry set is complete or cancellations
are reflected. Even when all records are present, the API reports
`predictionsReady: 0` and `fullyVerifiedRaces: 0`.

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
