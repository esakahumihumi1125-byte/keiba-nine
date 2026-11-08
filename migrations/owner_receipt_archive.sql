-- Run once as an admin on a persistent, owner-private Postgres.
-- NEVER run against the public preview or a database shared with public pages.
-- Service application account should only be GRANTED SELECT and INSERT
-- on this table. Do not grant UPDATE, DELETE, TRUNCATE or DDL to the service role.
-- No JRDB raw rows or JRA official results belong in this archive.

CREATE TABLE IF NOT EXISTS owner_prestart_receipts (
    race_day date NOT NULL,
    track text NOT NULL CHECK (
        track IN ('札幌','函館','福島','新潟','東京',
                  '中山','中京','京都','阪神','小倉')
    ),
    race_no smallint NOT NULL CHECK (race_no BETWEEN 1 AND 12),
    receipt_json jsonb NOT NULL CHECK (jsonb_typeof(receipt_json) = 'object'),
    inserted_at_utc timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT owner_prestart_receipts_first_capture_pk
        PRIMARY KEY (race_day, track, race_no)
);

COMMENT ON TABLE owner_prestart_receipts IS
    'Owner-only server-signed provisional prestart 100-yen research receipts. Not purchases or official JRA validation.';

-- Security: use a SEPARATE least-privileged application role.
-- Replace <owner_app_role> locally only; never commit credentials.
-- REVOKE ALL ON owner_prestart_receipts FROM PUBLIC;
-- GRANT SELECT, INSERT ON owner_prestart_receipts TO <owner_app_role>;
-- REVOKE UPDATE, DELETE, TRUNCATE ON owner_prestart_receipts FROM <owner_app_role>;

-- Production archiving is intentionally OFF until the owner chooses a
-- persistent database, access restrictions, backups and recovery plan.
