# KEIBA NINE — approved public auto-publication (not activated)

This is a controlled feed **publisher**, not an automated prediction engine, JRDB scraper, ChatGPT task integration, or private account bridge.

## Current app

BETA 5.1 already reads keiba-nine-auto-feed.json on GitHub Pages and refreshes while open. Existing 2.7 real/test record separation is unchanged. This new GitHub Action validates an authorized original forecast JSON feed and updates just that JSON. It is disabled until configured.

## Before enabling

Confirm that the source contains only original, publicly licensed predictions. Do not publish JRDB paid datasets, copied protected racecards, credentials, private user details, or unlicensed third-party content. The JSON approval flags do not verify legal rights by themselves.

GitHub repository Settings → Secrets and variables → Actions:

- Secret KEIBA_NINE_PUBLIC_FEED_URL: complete HTTPS URL of authorized JSON.
- Variable KEIBA_NINE_PUBLIC_FEED_HOST: exact source hostname (without scheme or path).
- Variable KEIBA_NINE_PUBLICATION_ENABLED: set to true only after testing the source, terms and actual prediction data. Leave unset otherwise.

Required JSON: schema 1, date, timezone-aware generatedAt, source.name, rightsNote, publicReleaseApproved:true, originalForecast:true, forecasts matching the BETA 5.1 schema. Final race forecasts need a complete matching raceCard (active horse names/numbers, source, checkedAt) and evidence references.

Validations reject synthetic/test input, invalid race numbers, duplicate races, invalid combination counts, outdated input and new predictions after race start. Previously published started races remain unchanged. The Action does not place bets, operate My KEIBA, update Google Sheets, or process private JRDB/API secrets.

## Scheduling limits

Checks are scheduled at 09:00–16:30 JST every 30 minutes; GitHub Action execution can be delayed. This is not an exact ten-minute pre-race service. The BETA 5.1 browser fetches the new file on load and checks again roughly every five minutes while the page is visible.

Without the actual original live forecast source, enabling this workflow cannot generate any forecasts. ChatGPT's scheduled race messages do not automatically enter the GitHub feed.
