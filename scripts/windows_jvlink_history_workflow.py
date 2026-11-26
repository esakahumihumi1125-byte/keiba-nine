"""Owner-initiated local archive workflow. No uploads, retries or purchases.

Inspect existing files read-only before any JV-Link call. Acquire missing
RACE, SLOP and WOOD sequentially after explicit consent. Completed archives
remain on disk if a later step fails; the next manual run skips them.
A successful stream is not proof of complete historical coverage.
"""
from contextlib import closing
from datetime import datetime
import os
from pathlib import Path
import sqlite3
import struct
import sys

from windows_jvlink_2026_history_store import DATABASE, FROMTIME, save_archive
from windows_jvlink_workout_store import save_workouts
from windows_jvlink_weekly_read import JST, JvLocalCheckError

SOURCES = (
    ("RACE", DATABASE, "arc-race-local-history-1"),
    ("SLOP", "jvdata-2026-slop.sqlite3", "arc-race-workout-1"),
    ("WOOD", "jvdata-2026-wood.sqlite3", "arc-race-workout-1"),
)


def _folder_check(folder):
    if not folder.is_absolute() or folder.is_symlink() or folder.parent.is_symlink():
        raise JvLocalCheckError("WORKFLOW_LOCAL_PATH_INVALID")


def inspect(folder):
    """Return only statuses and counts; never print source rows or paths."""
    folder = Path(folder)
    _folder_check(folder)
    result = {}
    for spec, filename, schema in SOURCES:
        path = folder / filename
        if path.is_symlink():
            raise JvLocalCheckError("WORKFLOW_ARCHIVE_INVALID")
        if not path.exists():
            result[spec] = None
            continue
        if not path.is_file():
            raise JvLocalCheckError("WORKFLOW_ARCHIVE_INVALID")
        try:
            with closing(sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)) as conn:
                conn.execute("PRAGMA query_only=ON")
                manifest = dict(conn.execute("SELECT key,value FROM manifest"))
                if (manifest.get("schema")!=schema or manifest.get("dataspec")!=spec
                        or manifest.get("stream_completed")!="yes"
                        or manifest.get("fromtime")!=FROMTIME):
                    raise JvLocalCheckError("WORKFLOW_ARCHIVE_INVALID")
                if spec=="RACE":
                    count=dict(conn.execute("SELECT kind,COUNT(*) FROM records GROUP BY kind"))
                    if not count.get("RA") or not count.get("SE"):
                        raise JvLocalCheckError("WORKFLOW_ARCHIVE_INVALID")
                    result[spec]=count
                else:
                    count=conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
                    if not count:
                        raise JvLocalCheckError("WORKFLOW_ARCHIVE_INVALID")
                    result[spec]={"records":count}
        except sqlite3.Error:
            raise JvLocalCheckError("WORKFLOW_ARCHIVE_INVALID") from None
    return result


def acquire_missing(folder, jv_factory, *, emit=print):
    folder=Path(folder)
    existing=inspect(folder)
    for spec, _, _ in SOURCES:
        if existing[spec] is not None:
            emit(spec+"_ARCHIVE=EXISTING_SKIP")
            continue
        emit(spec+"_ARCHIVE=READING")
        try:
            jv=jv_factory()
            if jv.JVInit("UNKNOWN")!=0:
                raise JvLocalCheckError("WORKFLOW_INIT_FAILED")
            if spec=="RACE":
                save_archive(jv,folder)
            else:
                save_workouts(jv,folder,spec)
        except Exception:
            emit(spec+"_ARCHIVE=FAILED_NO_RETRY")
            raise
        emit(spec+"_ARCHIVE=STREAM_COMPLETE")
    return inspect(folder)


def main():
    if os.name!="nt" or struct.calcsize("P")!=8 or datetime.now(JST).year!=2026:
        print("ARC_RACE_HISTORY_WORKFLOW=WINDOWS_64BIT_2026_REQUIRED")
        return 1
    try:
        base=Path(os.environ.get("LOCALAPPDATA",""))
        if not base.is_absolute():
            raise JvLocalCheckError("WORKFLOW_LOCAL_PATH_INVALID")
        folder=base/"ARC-RACE-private"/"licensed-history"
        existing=inspect(folder)
        for spec,value in existing.items():
            print(spec+"_ARCHIVE="+("MISSING" if value is None else "EXISTING"))
        missing=[spec for spec,value in existing.items() if value is None]
        if missing:
            print("Active personal licence required. Source records must be deleted when access ends.")
            print("One normal read per missing source: "+", ".join(missing))
            print("Local disk only. No automatic retry, upload, or purchase.")
            if input("Type YES to acquire the missing sources: ").strip()!="YES":
                print("ARC_RACE_HISTORY_WORKFLOW=CANCELLED")
                return 0
            import win32com.client
            existing=acquire_missing(folder,lambda:win32com.client.Dispatch("JVDTLab.JVLink"))
        for spec, counts in existing.items():
            for kind,count in counts.items():
                print(spec+"_"+kind.upper()+"="+str(count))
        print("ARC_RACE_HISTORY_WORKFLOW=THREE_ARCHIVES_PRESENT_COVERAGE_UNVERIFIED")
        print("FORMAL_TEN_FACTOR_READY=NO")
        print("Run the course/workout studies separately while the licence is active.")
        return 0
    except JvLocalCheckError as error:
        print("ARC_RACE_HISTORY_WORKFLOW="+str(error))
    except (Exception,KeyboardInterrupt):
        print("ARC_RACE_HISTORY_WORKFLOW=FAILED_OR_INTERRUPTED")
    return 1


if __name__=="__main__":
    sys.exit(main())
