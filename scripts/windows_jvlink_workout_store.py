"""Licensed local HC/WC archive. No network beyond explicit JV-Link read.
Source layout: JV-Data 4.9.0.1, HC 60 bytes, WC 105 bytes.
No grade, model, prestart availability proof or external upload.
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
from datetime import datetime

from windows_jvlink_2026_history_store import FROMTIME, MIN_FREE, MAX_RAW_BYTES
from windows_jvlink_weekly_read import JST, JvLocalCheckError

SPECS = {"SLOP": (b"HC", 60), "WOOD": (b"WC", 105)}
MAX_STEPS = 3000000
MAX_SECONDS = 3600


def workout_record(raw, spec):
    kind, length = SPECS[spec]
    if raw[:2] != kind:
        return None
    if len(raw) != length or raw[-2:] != b"\r\n" or raw[2:3] not in (b"0", b"1"):
        raise JvLocalCheckError("WORKOUT_RECORD_INVALID")
    created, center, day, clock, horse = raw[3:11], raw[11:12], raw[12:20], raw[20:24], raw[24:34]
    if (center not in (b"0", b"1") or not all(x.isdigit() for x in (created, day, clock, horse))
            or horse == b"0000000000"):
        raise JvLocalCheckError("WORKOUT_IDENTITY_INVALID")
    try:
        datetime.strptime(created.decode(), "%Y%m%d")
        datetime.strptime(day.decode(), "%Y%m%d")
        if int(clock[:2]) > 23 or int(clock[2:]) > 59:
            raise ValueError()
    except ValueError:
        raise JvLocalCheckError("WORKOUT_IDENTITY_INVALID") from None
    if day[:4] != b"2026":
        return None
    # Preserve deletion records and all revisions; do not treat them as times.
    return (hashlib.sha256(raw).digest(), day.decode(), raw[11:34].decode(),
            created.decode(), raw[2:3].decode(), raw)


def save_workouts(jv, folder, spec, *, max_steps=MAX_STEPS, max_seconds=MAX_SECONDS,
                  free_bytes=None, clock=time.monotonic, sleep=time.sleep):
    if spec not in SPECS or not 1 <= max_steps <= MAX_STEPS or not 0 < max_seconds <= MAX_SECONDS:
        raise JvLocalCheckError("WORKOUT_SCOPE_INVALID")
    folder = Path(folder)
    if not folder.is_absolute() or folder.is_symlink() or folder.parent.is_symlink():
        raise JvLocalCheckError("WORKOUT_LOCAL_PATH_INVALID")
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    target = folder / ("jvdata-2026-" + spec.lower() + ".sqlite3")
    if target.exists() or target.is_symlink():
        raise JvLocalCheckError("WORKOUT_EXISTS_NOT_OVERWRITTEN")
    free_bytes = free_bytes or (lambda: shutil.disk_usage(folder).free)
    if free_bytes() < MIN_FREE:
        raise JvLocalCheckError("WORKOUT_DISK_SPACE_LOW")
    fd, name = tempfile.mkstemp(prefix=".workout-", suffix=".sqlite3", dir=folder)
    os.close(fd)
    staged = Path(name)
    conn = None
    try:
        conn = sqlite3.connect(staged)
        conn.execute("PRAGMA secure_delete=ON")
        conn.execute("CREATE TABLE records (digest BLOB PRIMARY KEY, workout_day TEXT,"
                     " workout_key TEXT, created_day TEXT, category TEXT, raw BLOB)")
        conn.execute("CREATE INDEX workout_index ON records(workout_day,workout_key)")
        conn.execute("CREATE TABLE manifest(key TEXT PRIMARY KEY,value TEXT)")
        opened = False
        total = 0
        pending = None
        started = clock()
        try:
            answer = jv.JVOpen(spec, FROMTIME, 1, 0, 0, "")
            if not isinstance(answer,(tuple,list)) or not answer or type(answer[0]) is not int or answer[0] != 0:
                raise JvLocalCheckError("WORKOUT_OPEN_NOT_READY")
            opened = True
            for step in range(max_steps):
                if clock()-started >= max_seconds:
                    raise JvLocalCheckError("WORKOUT_TIME_LIMIT")
                if step % 1000 == 0 and free_bytes() < MIN_FREE:
                    raise JvLocalCheckError("WORKOUT_DISK_SPACE_LOW")
                row = jv.JVGets(bytearray(),110000,bytearray())
                if not isinstance(row,(tuple,list)) or len(row)!=3 or type(row[0]) is not int:
                    raise JvLocalCheckError("WORKOUT_READ_INVALID")
                code, data, _ = row
                if code == 0:
                    break
                if code == -1:
                    continue
                if code == -3:
                    pending = clock() if pending is None else pending
                    if clock()-pending >= 180:
                        raise JvLocalCheckError("WORKOUT_DOWNLOAD_PENDING")
                    sleep(1)
                    continue
                if not 3 <= code <= 110000:
                    raise JvLocalCheckError("WORKOUT_READ_FAILED")
                pending = None
                raw = data.tobytes() if hasattr(data,"tobytes") else bytes(data)
                if len(raw)<code:
                    raise JvLocalCheckError("WORKOUT_READ_INVALID")
                parsed = workout_record(raw[:code],spec)
                if parsed is not None:
                    added=conn.execute("INSERT OR IGNORE INTO records VALUES(?,?,?,?,?,?)",parsed)
                    if added.rowcount:
                        total += code
                        if total > MAX_RAW_BYTES:
                            raise JvLocalCheckError("WORKOUT_SIZE_LIMIT")
            else:
                raise JvLocalCheckError("WORKOUT_STEP_LIMIT")
        finally:
            if opened and jv.JVClose()!=0:
                raise JvLocalCheckError("WORKOUT_CLOSE_FAILED")
        count=conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        if not count:
            raise JvLocalCheckError("WORKOUT_NO_MATCHING_RECORDS")
        conn.executemany("INSERT INTO manifest VALUES(?,?)",[
            ("schema","arc-race-workout-1"),("dataspec",spec),("fromtime",FROMTIME),
            ("stream_completed","yes"),("coverage_verified","no"),
            ("prestart_availability_verified","no"),("captured_at_jst",datetime.now(JST).isoformat()),
            ("raw_data_delete_on_contract_end","yes")])
        conn.commit()
        conn.close()
        os.link(staged,target)
        return count
    finally:
        if conn is not None:
            conn.close()
        for p in (staged,Path(str(staged)+"-journal")):
            p.unlink(missing_ok=True)


def main():
    if os.name!="nt" or struct.calcsize("P")!=8:
        print("ARC_RACE_WORKOUT=WINDOWS_64BIT_REQUIRED")
        return 1
    print("Active personal licence required. No external upload. Delete source data when access ends.")
    spec=input("SLOP (hill) or WOOD (woodchip), Enter = cancel: ").strip().upper()
    if spec not in SPECS or input("Type YES to read once: ").strip()!="YES":
        print("ARC_RACE_WORKOUT=CANCELLED")
        return 0
    try:
        base=Path(os.environ.get("LOCALAPPDATA",""))
        if not base.is_absolute() or datetime.now(JST).year!=2026:
            raise JvLocalCheckError("WORKOUT_SCOPE_INVALID")
        import win32com.client
        jv=win32com.client.Dispatch("JVDTLab.JVLink")
        if jv.JVInit("UNKNOWN")!=0:
            raise JvLocalCheckError("WORKOUT_INIT_FAILED")
        count=save_workouts(jv,base/"ARC-RACE-private"/"licensed-history",spec)
        print("ARC_RACE_WORKOUT=SUCCESS_COVERAGE_UNVERIFIED")
        print("RECORDS="+str(count))
        return 0
    except JvLocalCheckError as e:
        print("ARC_RACE_WORKOUT="+str(e))
    except (Exception,KeyboardInterrupt):
        print("ARC_RACE_WORKOUT=FAILED_OR_INTERRUPTED")
    return 1


if __name__=="__main__":
    sys.exit(main())
