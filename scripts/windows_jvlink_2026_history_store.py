"""Local owner-only 2026 RA/SE archive, not a training dataset.

One normal JVOpen (option 1), no setup/parallel/retry. Keep licensed records
only in LOCALAPPDATA; never upload them. Source revisions are immutable and
not proof of pre-race availability. No odds features, grade or prediction.
"""
import hashlib
import os
from pathlib import Path
import shutil
import sqlite3
import struct
import sys
import tempfile
import time
from datetime import datetime, timedelta

from windows_jvlink_weekly_read import JST, JvLocalCheckError

FROMTIME = "20260101000000"
YEAR = "2026"
MAX_STEPS = 1500000
MAX_SECONDS = 3600
MIN_FREE = 3 * 1024**3
MAX_RAW_BYTES = 1024**3
LENGTHS = {b"RA": 1272, b"SE": 555}
DATABASE = "jvdata-2026-race-history.sqlite3"


def _record(raw):
    kind = raw[:2]
    if kind not in LENGTHS:
        return None
    if len(raw) != LENGTHS[kind] or raw[-2:] != b"\r\n" or not raw[2:3].isdigit():
        raise JvLocalCheckError("HISTORY_RECORD_INVALID")
    created, identity = raw[3:11], raw[11:27]
    if not identity.isdigit() or not created.isdigit():
        raise JvLocalCheckError("HISTORY_IDENTITY_INVALID")
    if identity[:4] != YEAR.encode() or not b"01" <= identity[8:10] <= b"10":
        return None
    try:
        day = identity[:8].decode("ascii")
        datetime.strptime(day, "%Y%m%d")
        datetime.strptime(created.decode("ascii"), "%Y%m%d")
        if not all(1 <= int(identity[i:i+2]) <= 12 for i in (10, 12, 14)):
            raise ValueError()
    except ValueError:
        raise JvLocalCheckError("HISTORY_IDENTITY_INVALID") from None
    return (hashlib.sha256(raw).digest(), kind.decode(), raw[2:3].decode(),
            day, identity.decode(), created.decode(), raw)


def collect(jv, conn, *, folder, clock=time.monotonic, sleep=time.sleep,
            max_steps=MAX_STEPS, max_seconds=MAX_SECONDS,
            free_bytes=None):
    """Single completed stream or no committed archive. Fake COM testable."""
    if not 1 <= max_steps <= MAX_STEPS or not 0 < max_seconds <= MAX_SECONDS:
        raise JvLocalCheckError("HISTORY_BUDGET_INVALID")
    free_bytes = free_bytes or (lambda: shutil.disk_usage(folder).free)
    if free_bytes() < MIN_FREE:
        raise JvLocalCheckError("HISTORY_DISK_SPACE_LOW")
    conn.execute("CREATE TABLE records (digest BLOB PRIMARY KEY, kind TEXT NOT NULL,"
                 " category TEXT NOT NULL, race_day TEXT NOT NULL,"
                 " race_key TEXT NOT NULL, created_day TEXT NOT NULL, raw BLOB NOT NULL)")
    conn.execute("CREATE INDEX race_index ON records(race_day, race_key, kind)")
    conn.execute("CREATE TABLE manifest (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    opened = False
    raw_bytes = 0
    start = clock()
    pending_at = None
    try:
        answer = jv.JVOpen("RACE", FROMTIME, 1, 0, 0, "")
        if not isinstance(answer, (list, tuple)) or not answer or type(answer[0]) is not int:
            raise JvLocalCheckError("HISTORY_OPEN_INVALID")
        if answer[0] != 0:
            raise JvLocalCheckError("HISTORY_OPEN_NOT_READY")
        opened = True
        for step in range(max_steps):
            if clock()-start >= max_seconds:
                raise JvLocalCheckError("HISTORY_TIME_LIMIT")
            if step % 1000 == 0 and free_bytes() < MIN_FREE:
                raise JvLocalCheckError("HISTORY_DISK_SPACE_LOW")
            response = jv.JVGets(bytearray(), 110000, bytearray())
            if (not isinstance(response, (list, tuple)) or len(response) != 3
                    or type(response[0]) is not int):
                raise JvLocalCheckError("HISTORY_READ_INVALID")
            code, data, _ = response
            if code == 0:
                break
            if code == -1:
                continue
            if code == -3:
                pending_at = clock() if pending_at is None else pending_at
                if clock()-pending_at >= 180:
                    raise JvLocalCheckError("HISTORY_DOWNLOAD_PENDING")
                sleep(1)
                continue
            if not 3 <= code <= 110000:
                raise JvLocalCheckError("HISTORY_READ_FAILED")
            pending_at = None
            raw = data.tobytes() if hasattr(data, "tobytes") else bytes(data)
            if len(raw) < code:
                raise JvLocalCheckError("HISTORY_READ_INVALID")
            row = _record(raw[:code])
            if row is None:
                continue
            added = conn.execute("INSERT OR IGNORE INTO records VALUES(?,?,?,?,?,?,?)", row)
            if added.rowcount:
                raw_bytes += code
                if raw_bytes > MAX_RAW_BYTES:
                    raise JvLocalCheckError("HISTORY_SIZE_LIMIT")
        else:
            raise JvLocalCheckError("HISTORY_STEP_LIMIT")
    finally:
        if opened and jv.JVClose() != 0:
            raise JvLocalCheckError("HISTORY_CLOSE_FAILED")
    counts = dict(conn.execute("SELECT kind,COUNT(*) FROM records GROUP BY kind"))
    if not counts.get("RA") or not counts.get("SE"):
        raise JvLocalCheckError("HISTORY_RA_SE_NOT_BOTH_OBSERVED")
    conn.executemany("INSERT INTO manifest VALUES(?,?)", [
        ("schema", "arc-race-local-history-1"), ("dataspec", "RACE"),
        ("fromtime", FROMTIME), ("option", "1"), ("stream_completed", "yes"),
        ("coverage_verified", "no"), ("prestart_availability_verified", "no"),
        ("captured_at_jst", datetime.now(JST).isoformat()),
        ("raw_data_delete_on_contract_end", "yes")])
    conn.commit()
    return counts


def save_archive(jv, folder, **kwargs):
    folder = Path(folder)
    if not folder.is_absolute() or folder.is_symlink():
        raise JvLocalCheckError("HISTORY_LOCAL_PATH_INVALID")
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = folder / DATABASE
    if target.exists() or target.is_symlink():
        raise JvLocalCheckError("HISTORY_EXISTS_NOT_OVERWRITTEN")
    fd, name = tempfile.mkstemp(prefix=".history-", suffix=".sqlite3", dir=folder)
    os.close(fd)
    staged = Path(name)
    try:
        with sqlite3.connect(staged) as conn:
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA secure_delete=ON")
            counts = collect(jv, conn, folder=folder, **kwargs)
        # sqlite context manager commits but does not close its handle.
        conn.close()
        os.link(staged, target)
        return counts
    finally:
        # Close before unlink on Windows, including exceptional paths.
        if 'conn' in locals():
            conn.close()
        for file in (staged, Path(str(staged)+"-journal")):
            file.unlink(missing_ok=True)


def main():
    if os.name != "nt" or struct.calcsize("P") != 8:
        print("ARC_RACE_HISTORY=WINDOWS_64BIT_REQUIRED")
        return 1
    print("Private 2026 RA/SE data archive. Active licence / permitted personal use required.")
    print("All source records and training datasets must be removed when access ends.")
    print("No external upload. Normal RACE read once. No automatic retry or purchase.")
    if input("Type YES to start (Enter = cancel): ").strip() != "YES":
        print("ARC_RACE_HISTORY=CANCELLED")
        return 0
    try:
        now = datetime.now(JST)
        if now.date() < datetime(2026, 1, 1).date() or now.date() >= datetime(2027, 1, 1).date():
            raise JvLocalCheckError("HISTORY_SCOPE_OUTSIDE_CURRENT_YEAR")
        base = os.environ.get("LOCALAPPDATA", "")
        if not Path(base).is_absolute():
            raise JvLocalCheckError("HISTORY_LOCAL_PATH_INVALID")
        folder = Path(base) / "ARC-RACE-private" / "licensed-history"
        if folder.is_symlink() or folder.parent.is_symlink():
            raise JvLocalCheckError("HISTORY_LOCAL_PATH_INVALID")
        if (folder / DATABASE).exists():
            raise JvLocalCheckError("HISTORY_EXISTS_NOT_OVERWRITTEN")
        import win32com.client
        jv = win32com.client.Dispatch("JVDTLab.JVLink")
        if jv.JVInit("UNKNOWN") != 0:
            raise JvLocalCheckError("HISTORY_INIT_FAILED")
        counts = save_archive(jv, folder)
        print("ARC_RACE_HISTORY=SUCCESS_PARTIAL_COVERAGE_UNVERIFIED")
        print("RA_RECORDS=" + str(counts["RA"]))
        print("SE_RECORDS=" + str(counts["SE"]))
    except JvLocalCheckError as error:
        print("ARC_RACE_HISTORY=" + str(error))
        return 1
    except (Exception, KeyboardInterrupt):
        print("ARC_RACE_HISTORY=FAILED_OR_INTERRUPTED")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
