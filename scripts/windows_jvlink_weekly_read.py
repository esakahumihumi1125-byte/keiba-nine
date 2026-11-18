"""Local, user-initiated ONE weekly JV-Link read for ARC RACE research.

This file must run ONLY on the owner's Windows computer. It does not connect
to Render, GitHub, JRDB or a web endpoint, and never prints or saves raw
JRA-VAN records, horse IDs, secrets, passwords, or download paths.

A successful read provides private RA/SE *candidates*, NOT proof of timely
delivery, scratch updates, going, final post time, licensing, or betting
readiness. JVOpen option 2 ("this-week data") is intentionally fixed. NO
historical setup, retries, realtime polling or automatic scheduled calls.
"""
import argparse
from datetime import date, datetime, timedelta
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
import time

from jvdata_ra_se_candidate import (
    parse_jvdata_prestart_racecard,
    RA_LENGTH, SE_LENGTH,
)
from owner_jvdata_local_report import render_weekly_candidate_summary
from jrdb_coverage import CoverageError

VERSION = "owner-jvlink-weekly-local-candidates-1"
# pywin32 JVGets can retain its requested buffer for each read. Bound
# a one-click diagnostic instead of risking multi-GB use on a small PC.
MAX_RECORDS = 5000
MAX_FILE_SWITCHES = 200
MAX_DOWNLOAD_WAIT_SECONDS = 90
MAX_RACES = 36
MAX_READ_BYTES = 110000
RACE_ID = re.compile(rb"[0-9]{16}\Z")
DATE = re.compile(r"20[0-9]{6}\Z")


class JvLocalCheckError(ValueError):
    """Only stable labels are user-visible, never COM error details."""


def next_saturday(today=None):
    """Default the one-click test to the next Saturday in PC-local Japan time."""
    local_date = today or date.today()
    return (local_date + timedelta(days=(5 - local_date.weekday()) % 7)).strftime("%Y%m%d")


def validate_day(day):
    if type(day) is not str or DATE.fullmatch(day) is None:
        raise JvLocalCheckError("DATE_INVALID")
    try:
        candidate = datetime.strptime(day, "%Y%m%d").date()
    except ValueError:
        raise JvLocalCheckError("DATE_INVALID") from None
    today = date.today()
    # Today or upcoming weekend only; no historical bulk backfill.
    if not today <= candidate <= date.fromordinal(today.toordinal() + 7):
        raise JvLocalCheckError("DATE_OUTSIDE_NEXT_WEEK")
    return day


def collect_weekly_candidate_records(
    jv, day, *, max_records=MAX_RECORDS, sleep=None, monotonic=None,
    max_download_wait=MAX_DOWNLOAD_WAIT_SECONDS
):
    """One JVOpen, bounded JVGets loop and mandatory JVClose.

    RA and SE category-2 records for the requested race day only. Identical
    duplicate records may be replayed, but any conflicting duplicate race
    record makes the *whole output* unsafe and fails closed.
    """
    if (type(max_records) is not int or not 1 <= max_records <= MAX_RECORDS
            or type(max_download_wait) not in (int, float)
            or not 0 < max_download_wait <= MAX_DOWNLOAD_WAIT_SECONDS):
        raise JvLocalCheckError("READ_BUDGET_INVALID")
    # JV-Link -3 indicates data is still downloading, NOT a hard failure.
    # A short, bounded local wait allows a single user-initiated attempt to
    # finish without unbounded retrying, JVOpen repetitions or polling APIs.
    sleep = sleep or time.sleep
    monotonic = monotonic or time.monotonic
    first_download_wait = None
    raw_ra, raw_se, seen_se = {}, {}, set()
    opened = False
    try:
        opened_result = jv.JVOpen("RACE", "00000000000000", 2, 0, 0, "")
        if not isinstance(opened_result, (tuple, list)) or not opened_result:
            raise JvLocalCheckError("JVOPEN_SHAPE_UNEXPECTED")
        if type(opened_result[0]) is not int:
            raise JvLocalCheckError("JVOPEN_SHAPE_UNEXPECTED")
        if opened_result[0] != 0:
            raise JvLocalCheckError("JVOPEN_NOT_READY")
        opened = True
        file_switches = 0
        total_read = 0
        for _ in range(max_records):
            result = jv.JVGets(bytearray(), MAX_READ_BYTES, bytearray())
            if not isinstance(result, (tuple, list)) or len(result) != 3:
                raise JvLocalCheckError("JVGETS_SHAPE_UNEXPECTED")
            code, record, _file = result
            if type(code) is not int:
                raise JvLocalCheckError("JVGETS_SHAPE_UNEXPECTED")
            if code == 0:
                break
            if code == -1:
                file_switches += 1
                if file_switches > MAX_FILE_SWITCHES:
                    raise JvLocalCheckError("TOO_MANY_FILE_SWITCHES")
                continue
            if code == -3:
                if first_download_wait is None:
                    first_download_wait = monotonic()
                remaining = max_download_wait - (monotonic() - first_download_wait)
                if remaining <= 0:
                    raise JvLocalCheckError("JVDOWNLOAD_STILL_PENDING")
                sleep(min(2, remaining))
                continue
            if code < -1:
                raise JvLocalCheckError("JVGETS_FAILED")
            first_download_wait = None
            total_read += 1
            try:
                data = record.tobytes() if hasattr(record, "tobytes") else bytes(record)
            except (TypeError, ValueError, OverflowError, AttributeError):
                raise JvLocalCheckError("JVGETS_DATA_INVALID") from None
            # Some supported pywin32 wrappers append a trailing NUL (or
            # return a padded buffer). The JV-Link positive return value is
            # the exact record byte count. Never parse the padding.
            if code < 3 or code > MAX_READ_BYTES or len(data) < code:
                raise JvLocalCheckError("JVGETS_DATA_INVALID")
            data = data[:code]
            kind = data[:2]
            if kind not in (b"RA", b"SE") or data[2:3] != b"2":
                continue
            if len(data) < 30:
                raise JvLocalCheckError("JVGETS_DATA_INVALID")
            if data[11:19].decode("ascii", errors="ignore") != day:
                continue
            if kind == b"RA" and len(data) != RA_LENGTH:
                raise JvLocalCheckError("RACE_RECORD_INVALID")
            if kind == b"SE" and len(data) != SE_LENGTH:
                raise JvLocalCheckError("HORSE_RECORD_INVALID")
            identity = data[11:27]
            if RACE_ID.fullmatch(identity) is None:
                raise JvLocalCheckError("RACE_ID_INVALID")
            if kind == b"RA":
                old = raw_ra.get(identity)
                if old is not None and old != data:
                    raise JvLocalCheckError("CONFLICTING_RACE_UPDATES")
                raw_ra[identity] = data
            else:
                se_id = (identity, data[28:30])
                if se_id in seen_se:
                    if raw_se[identity][data[28:30]] != data:
                        raise JvLocalCheckError("CONFLICTING_HORSE_UPDATES")
                    continue
                seen_se.add(se_id)
                raw_se.setdefault(identity, {})[data[28:30]] = data
        else:
            raise JvLocalCheckError("WEEKLY_READ_LIMIT_REACHED")
    finally:
        if opened:
            try:
                jv.JVClose()
            except Exception:
                # The existing error must never reveal a JV-Link filename or
                # leave apparently complete data after a failed close.
                raise JvLocalCheckError("JVCLOSE_FAILED") from None

    if len(raw_ra) > MAX_RACES:
        raise JvLocalCheckError("TOO_MANY_RACES")
    if set(raw_se) != set(raw_ra):
        raise JvLocalCheckError("RACE_AND_HORSE_RECORDS_INCOMPLETE")
    cards = []
    for identity in sorted(raw_ra):
        ra = raw_ra[identity]
        se = list(raw_se[identity].values())
        try:
            cards.append(parse_jvdata_prestart_racecard(ra, se, day))
        except CoverageError:
            raise JvLocalCheckError("CANDIDATE_RECORDS_INVALID") from None
    if not cards:
        raise JvLocalCheckError("NO_NUMBERED_CARDS_FOR_DAY")
    coordinate_set = {(r["track"], r["race"]) for r in cards}
    if len(coordinate_set) != len(cards):
        raise JvLocalCheckError("DUPLICATE_RACE_COORDINATES")
    # Exact 12-R per observed venue is a *coverage diagnostic* only. It
    # does not prove whether another JRA venue was scheduled or that
    # the listed starters are final.
    venue_counts = {}
    for r in cards:
        venue_counts[r["track"]] = venue_counts.get(r["track"], 0) + 1
    venue_summary = [{"track": track, "raceCount": venue_counts[track]}
                     for track in sorted(venue_counts)]
    return {
        "version": VERSION,
        "date": day,
        "raceCount": len(cards),
        "races": sorted(cards, key=lambda x: (x["track"], x["race"])),
        "observedVenues": venue_summary,
        "allObservedVenuesHaveTwelveRaces": all(
            count == 12 for count in venue_counts.values()
        ),
        "allScheduledVenuesVerified": False,
        "weekReadRecordCount": total_read,
        "source": "private_jvlink_weekly_ra_se_candidate",
        "independentJraVerified": False,
        "officialScratchesVerified": False,
        "officialGoingVerified": False,
        "officialFinalPostTimeVerified": False,
        "productionPredictionReady": False,
        "bettingReady": False,
        "researchOnly": True,
        "privateOwnerOnly": True,
        "providerDataRawIncluded": False,
        "autoPurchase": False,
        "note": "今週分を本人PCで1回読取。登録馬番候補のみで最新取消・馬場・確定発走時刻は未確認。",
    }


def run_one_weekly_read(day, *, jv_factory=None):
    """Explicit local invocation; no automatic package installation."""
    validate_day(day)
    if struct.calcsize("P") != 8:
        raise JvLocalCheckError("PYTHON_NOT_64_BIT")
    if jv_factory is None:
        try:
            import win32com.client
        except ImportError:
            raise JvLocalCheckError("PYWIN32_NOT_INSTALLED") from None
        jv_factory = lambda: win32com.client.Dispatch("JVDTLab.JVLink")
    try:
        jv = jv_factory()
    except Exception:
        raise JvLocalCheckError("JVLINK_COM_UNAVAILABLE") from None
    try:
        if jv.JVInit("UNKNOWN") != 0:
            raise JvLocalCheckError("JVINIT_FAILED")
        return collect_weekly_candidate_records(jv, day)
    except JvLocalCheckError:
        raise
    except Exception:
        raise JvLocalCheckError("JVLINK_WEEKLY_READ_FAILED") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description="ARC RACE local one-time JRA-VAN weekly RA/SE read")
    parser.add_argument("--date", help="JST race date YYYYMMDD (default: next Saturday)")
    args = parser.parse_args(argv)
    day = args.date or next_saturday()
    try:
        report = run_one_weekly_read(day)
        # This owner-only JSON contains ONLY the race coordinates, horse
        # numbers and scheduled post-time candidates. It must not be uploaded
        # to public repositories or stored in shared folders.
        local_base = os.environ.get("LOCALAPPDATA")
        if not local_base or not Path(local_base).is_absolute():
            raise JvLocalCheckError("LOCALAPPDATA_UNAVAILABLE")
        folder = Path(local_base) / "ARC-RACE-private"
        try:
            page = render_weekly_candidate_summary(report)
        except CoverageError:
            raise JvLocalCheckError("LOCAL_REPORT_INVALID") from None
        try:
            folder.mkdir(mode=0o700, parents=True, exist_ok=True)
            target = folder / ("jvdata-candidate-" + day + ".json")
            html_target = folder / ("jvdata-candidate-" + day + ".html")
            # Both files must be complete before the final filenames exist.
            # Create local NTFS hard links rather than overwriting snapshots.
            staged_json = None
            staged_html = None
            linked_json = False
            try:
                for body, suffix in (
                    (json.dumps(report, ensure_ascii=False, indent=2), ".json"),
                    (page, ".html"),
                ):
                    with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", dir=folder,
                        prefix=".arc-race-", suffix=".tmp", delete=False
                    ) as output:
                        pending = Path(output.name)
                        if suffix == ".json":
                            staged_json = pending
                        else:
                            staged_html = pending
                        output.write(body)
                        output.flush()
                        os.fsync(output.fileno())
                os.link(staged_json, target)
                linked_json = True
                os.link(staged_html, html_target)
            except OSError:
                if linked_json:
                    target.unlink(missing_ok=True)
                raise
            finally:
                for staged in (staged_json, staged_html):
                    if staged is not None:
                        staged.unlink(missing_ok=True)
        except FileExistsError:
            raise JvLocalCheckError("OUTPUT_EXISTS_NOT_OVERWRITTEN") from None
        except (OSError, TypeError, ValueError):
            raise JvLocalCheckError("PRIVATE_LOCAL_WRITE_FAILED") from None
        print("ARCRACE_WEEKLY_READ=SUCCESS")
        print("LOCAL_COVERAGE_VIEW=READY")
        print("CANDIDATE_RACE_COUNT=" + str(report["raceCount"]))
        print("VENUES_OBSERVED=" + str(len(report["observedVenues"])))
        print("TWELVE_R_PER_OBSERVED_VENUE=" +
              ("YES" if report["allObservedVenuesHaveTwelveRaces"] else "NO"))
        print("NOTE=Only a preliminary RA/SE candidate; verify scheduled venues, late changes and final JRA data.")
        # User already explicitly double-clicked the local tool. Show the
        # local private summary in the default browser; no network requests.
        if hasattr(os, "startfile"):
            try:
                os.startfile(str(html_target))
            except OSError:
                print("LOCAL_COVERAGE_VIEW_OPEN=MANUAL")
        return 0
    except JvLocalCheckError as error:
        print("ARCRACE_WEEKLY_READ=" + str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
