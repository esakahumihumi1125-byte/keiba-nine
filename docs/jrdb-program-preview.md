# KEIBA NINE — JRDB private programme preview (pre-connection)

## What works without the API account

The repository now contains a **private-only** normalizer in
`scripts/jrdb_program_preview.py`. It understands JRDB's `/v1/tra`
8-character lowercase hexadecimal-style race keys, `racedate` (YYYYMMDD),
`racecourse_cd`, `post_time` (HHMM), `distance` (metres),
`track_type`, `headcount` and `race_name`.

The owner-authenticated WSGI console uses this normalizer for
`/api/jrdb/program?date=YYYYMMDD`. It returns **only**:
date, racekey, track, race number, race name, scheduled post time, surface,
distance and headcount; flags always indicate programme-only, horses unverified,
predictions unmade. Raw API rows, analysis, paid provider fields and credentials
are not sent to the browser. Invalid race keys or mismatched dates cause a
redacted error rather than exposing the provider payload.

`python -m unittest discover -s tests -p 'test_*.py'` runs all synthetic
unit tests without credentials, paid requests or real race data.

## What is not yet connected

- The private HTTPS hosting server has **not** been deployed.
- JRDB beta API credentials have **not** been issued/added.
- `JRDB_PRIVATE_ENABLED` remains off.
- Horse entries, training, recent performance, ML evaluation, and forecast
  generation are **not** connected. The `/tra` race program alone is not
  sufficient to produce credible betting tickets.
- No changes to the public GitHub Pages app or public forecast feed.
- Do not put a JRDB account password, API key or JRDB-derived forecast in
  GitHub commits, public JSON, action logs or a public site.

## After JRDB beta access arrives

1. Provision a secured, owner-only HTTPS runtime **separate from** GitHub Pages.
2. Put `JRDB_API_KEY` and `JRDB_AUTH_KEY` into that runtime's **private** secret store.
   The normal member login password is not necessarily the API token.
3. Verify no access without authentication and no public raw-data endpoint.
4. Enable the private integration only on that private runtime and test one date.
5. Confirm the actual beta response schema before extending adapters.
6. Add authorized private horse and workout feeds, then evaluate prediction
   logic; keep tests and real records strictly separate.

JRDB official programme reference:
https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tra

**Important:** JRDB authorized private personal use does not mean authorization
to redistribute even derived predictions. Public/sale integration is a separate
agreement.
