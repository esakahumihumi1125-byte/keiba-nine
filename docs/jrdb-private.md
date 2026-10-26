# JRDB personal integration — preparation only

Status: disabled by default. No live request or credential configuration has been performed.

The current GitHub repository and Pages site are public. Neither JRDB source data
nor predictions derived from it may be placed in public feeds, commits, logs,
Actions artifacts, backups shared with others, or public web responses.
A “personal” label or an unlisted URL does not restrict access.

## Prepared client

`scripts/jrdb_private.py` implements only the documented POST `/v1/tra` race
program request. It returns rows in memory and has no file output, browser code,
public route, or connection to the forecast generator. It blocks redirects,
limits response size, rejects invalid dates, and omits credentials and returned
data from error messages. Tests use synthetic responses; they are not live tests.

Official sources checked 2026-10-26:
- https://jrdb-api.keiba.bigtime.world/
- https://jrdb-api.keiba.bigtime.world/docs/authentication

## Before activation

1. Confirm the account has the appropriate JRDB API subscription.
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
