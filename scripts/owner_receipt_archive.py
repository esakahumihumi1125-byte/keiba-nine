"""Opt-in, owner-only Postgres archive for server-signed prestart research receipts.

Feature flag is OFF by default. The table must be provisioned separately
from migrations/owner_receipt_archive.sql on a private persistent Postgres.
No paid JRDB rows, purchase history or official JRA result claims are stored.
The earliest inserted receipt wins; a retry cannot replace historical picks.
"""
import json
from urllib.parse import urlsplit

from owner_prestart_receipt import (
    _selected_day, verify_preview_receipts, ReceiptError,
)

FLAG = "KEIBA_OWNER_RECEIPT_ARCHIVE_ENABLED"
DSN_KEY = "KEIBA_OWNER_RECEIPT_ARCHIVE_DATABASE_URL"
SIGNING_KEY = "KEIBA_OWNER_RECEIPT_SIGNING_SECRET"
MAX_DAY = 36

INSERT = """
INSERT INTO owner_prestart_receipts
 (race_day, track, race_no, receipt_json)
SELECT %s, %s, %s, CAST(%s AS jsonb)
WHERE clock_timestamp() < CAST(%s AS timestamptz)
ON CONFLICT (race_day, track, race_no) DO NOTHING
"""
SELECT = """
SELECT receipt_json FROM owner_prestart_receipts
WHERE race_day = %s ORDER BY track, race_no
"""


class ArchiveUnavailable(RuntimeError):
    pass


def archive_enabled(settings):
    return settings.get(FLAG) == "1"


def archive_signing_secret(settings):
    """Use an independent long-lived secret, never the owner's login password.

    Enabling persistence without it must fail closed. A changed login password
    must not invalidate the separately signed historical research receipts.
    """
    if not archive_enabled(settings):
        raise ArchiveUnavailable("Archive is disabled")
    value = settings.get(SIGNING_KEY)
    if (not isinstance(value, str) or len(value) < 48
            or len(value) > 512 or len(set(value)) < 16):
        raise ArchiveUnavailable("Independent archive signing key missing")
    return value


def archive_config(settings):
    """Configuration validation without ever logging connection details."""
    if settings.get(FLAG) != "1":
        raise ArchiveUnavailable("Archive is not enabled")
    if settings.get("KEIBA_RENDER_PRIVATE_ONLY") != "1" or settings.get(
            "KEIBA_RENDER_PREVIEW_ONLY") == "1":
        raise ArchiveUnavailable("Private service required")
    if settings.get("GITHUB_ACTIONS") == "true":
        raise ArchiveUnavailable("CI must not contact archive")
    archive_signing_secret(settings)
    dsn = settings.get(DSN_KEY)
    if not isinstance(dsn, str) or not 30 <= len(dsn) <= 4096:
        raise ArchiveUnavailable("Persistent Postgres not configured")
    try:
        parsed = urlsplit(dsn)
        if (parsed.scheme not in ("postgres", "postgresql")
                or not parsed.hostname or not parsed.path.strip("/")
                or not parsed.username or not parsed.password or parsed.fragment):
            raise ArchiveUnavailable("Invalid archive connection settings")
    except (ValueError, AttributeError):
        raise ArchiveUnavailable("Invalid archive connection settings") from None
    return dsn


def _connect(dsn):
    # Imported only when feature is explicitly enabled; no production DB is
    # opened by application startup, preview, CI or anonymous browsing.
    import psycopg
    return psycopg.connect(dsn, sslmode="require", connect_timeout=5)


def _stored_payload(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (TypeError, ValueError):
            raise ArchiveUnavailable("Invalid stored record") from None
    if (not isinstance(value, dict)
            or set(value) != {"snapshot", "signature"}):
        raise ArchiveUnavailable("Invalid stored record")
    return value


def _read_rows(cursor, day, password):
    cursor.execute(SELECT, (day,))
    rows = cursor.fetchall()
    if not isinstance(rows, list) or len(rows) > MAX_DAY:
        raise ArchiveUnavailable("Invalid archive row count")
    receipts = []
    for record in rows:
        if not isinstance(record, (tuple, list)) or len(record) != 1:
            raise ArchiveUnavailable("Invalid archive row")
        receipts.append(_stored_payload(record[0]))
    # Validates signatures, dates, uniqueness, timestamp ordering and tickets.
    try:
        verify_preview_receipts(receipts, password, day)
    except ReceiptError:
        raise ArchiveUnavailable("Archived signatures cannot be validated") from None
    return receipts


def save_first_and_read(settings, password, day, new_receipts, connect=None):
    """Insert each race at most once and return verified original receipts.

    All changes in one Postgres transaction. Any failure aborts the request:
    never fallback to a new client receipt pretending it was archived.
    """
    dsn = archive_config(settings)
    _selected_day(day)
    try:
        verify_preview_receipts(new_receipts, password, day)
        connector = connect or _connect
        with connector(dsn) as conn:
            with conn.cursor() as cursor:
                for receipt in new_receipts:
                    snapshot = receipt["snapshot"]
                    cursor.execute(
                        INSERT,
                        (day, snapshot["track"], snapshot["race"],
                         json.dumps(receipt, ensure_ascii=False, separators=(",", ":")),
                         snapshot["scheduledOffAt"]))
                saved = _read_rows(cursor, day, password)
                # A missing submitted race must never be called saved.
                requested = {(p["snapshot"]["track"], p["snapshot"]["race"])
                             for p in new_receipts}
                archived = {(p["snapshot"]["track"], p["snapshot"]["race"])
                            for p in saved}
                if not requested.issubset(archived):
                    raise ArchiveUnavailable("Receipt archive is incomplete")
                return saved
    except (ArchiveUnavailable, ReceiptError):
        raise ArchiveUnavailable("Cannot safely archive receipts") from None
    except Exception:
        # Do not log DSN, provider rows, SQL parameters or exception strings.
        raise ArchiveUnavailable("Receipt archive unavailable") from None


def read_day(settings, password, day, connect=None):
    """Retrieve previously saved signed records; never modifies the database."""
    dsn = archive_config(settings)
    _selected_day(day)
    try:
        connector = connect or _connect
        with connector(dsn) as conn:
            with conn.cursor() as cursor:
                return _read_rows(cursor, day, password)
    except ArchiveUnavailable:
        raise
    except Exception:
        raise ArchiveUnavailable("Receipt archive unavailable") from None
