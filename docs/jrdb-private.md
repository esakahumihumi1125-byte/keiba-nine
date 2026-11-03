# JRDB personal integration — preparation only

Status: disabled by default. No live request or credential configuration has been performed.

The current GitHub repository and Pages site are public. Neither JRDB source data
nor predictions derived from it may be placed in public feeds, commits, logs,
Actions artifacts, backups shared with others, or public web responses.
A “personal” label or an unlisted URL does not restrict access.

## Prepared client

`scripts/jrdb_private.py` contains private-only POST readers for `/v1/tra`
(programme), `/v1/tky` (horse entries), `/v1/tcy` (training), and `/v1/tze`
(previous runs). These endpoints are enabled only in an owner-authenticated private
backend. The client returns rows in memory, writes no feed files, blocks redirects,
limits response size, rejects invalid dates, and omits credentials and returned
data from error messages. Tests use synthetic responses; they are not live tests.
Provider beta endpoint paths and schemas must be reconfirmed against the issued beta
account documentation before any real request.

Official sources checked 2026-10-26:
- https://jrdb-api.keiba.bigtime.world/
- https://jrdb-api.keiba.bigtime.world/docs/authentication

## Before activation

1. Obtain the separate JRDB API beta test account and verify its current entitlement. The provider advised that the beta could be tested with a Basic subscription; the eventual production API was planned for the AI tier. These are not interchangeable with a Basic member login. Confirm the provider's latest instructions before activation.
2. Provision an owner-only backend and private storage; verify unauthenticated
   and other-user requests are denied, including direct data URLs.
3. Configure `JRDB_API_KEY` and `JRDB_AUTH_KEY` using the backend's secret manager.
   Never put their values into chat, browser HTML, GitHub commits, or public logs.
4. Only in that private backend, set `JRDB_PRIVATE_ENABLED=1`. This flag itself
   does not implement access control. GitHub Actions execution remains blocked.
5. Perform a live connection test there, then implement schema mapping and
   private prediction storage. Preserve the existing public/test ledger separately.

Public distribution of derived predictions needs separate permission/contract;
member authentication, commercial licensing and referrals must not be treated
as already available. This preparation does not enable any of them.

## Current integration boundary (2026-11-03)

- The Basic membership application and beta-account request have been submitted to the provider, but dedicated beta API credentials have not been confirmed as issued.
- Never repurpose the Basic member password as `JRDB_API_KEY` or `JRDB_AUTH_KEY`.
- No credentials are added to the public repository or GitHub Actions; there is no public race-data or derived-prediction pipeline.
- `scripts/private_service.py` exposes owner-only connectivity/coverage diagnostics, **not** operational real-data forecasting.
- Historical failed PR check notifications do not indicate current main is failing: check the current GitHub Actions result rather than relying on the old email.
