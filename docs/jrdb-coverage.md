# KEIBA NINE — all-course race coverage diagnostic (not activated)

## New private-only functionality

The existing owner-authenticated test console has an additional button:
**全場・全Rの取得状況を確認**.

In a future owner-only HTTPS runtime, it can fetch the official JRDB
`/v1/tra` (programme) and `/v1/tky` (horse entries) for a selected racing date.
It matches on the official `racekey` and `racedate`, then checks whether the
number of unique horse numbers matches the programme's `headcount`.
The returned browser data contains only race date, track, race number,
scheduled start time, expected/observed counts, and verification status.

Provider horse names, indices, workouts and raw source records are not returned
by the coverage endpoint, even when the private API includes them.
No file is written, and neither public GitHub Pages JSON nor personal records
are changed. The connected client remains blocked under GitHub Actions.

## Accuracy limits

A matching entry **count** does not prove all horses are correct.
Scratches, exclusions, withdrawals, duplicate identities, updated racecards,
actual workouts, prior runs and track conditions still require independent
checks. This feature deliberately reports:
`rosterVerified=false`, `workoutsVerified=false`,
`predictionsReady=false` and `fullyVerifiedRaces=0` for every race.

No odds-based selections, ticket suggestions or automated betting are provided.
The service needs both API beta credentials and secure owner-only deployment
before any real retrieval.

Offline tests: `python -m unittest discover -s tests -p 'test_*.py'`

Official endpoints:
- https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tra
- https://jrdb-api.keiba.bigtime.world/docs/endpoints/today/tky

## Activation dependencies

1. Wait for JRDB to issue the beta API key and user authentication key.
   The member login password is not an API key.
2. Prepare HTTPS termination + private owner authentication for the server;
   GitHub Pages cannot execute server-side Python or protect JRDB feed.
3. Store keys only in the private server's secret manager, never in GitHub
   commits, GitHub Pages, shared Google Sheets or the chat.
4. Verify the actual beta response fields and source-license constraints;
   adjust the normalizer if the returned schema differs.
5. Only then enable private, read-only retrieval, and separately build
   training/recent-run analyses and final prediction validation.

Publishing JRDB-derived predictions to non-members remains unauthorized under
ordinary individual membership terms.
