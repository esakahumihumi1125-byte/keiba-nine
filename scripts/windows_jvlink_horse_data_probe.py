"""Explicit, read-only, owner-PC probe for weekly JRA-VAN RCVN coverage.

This checks whether historical RA/SE records are visible, not whether the
entire past race database is populated. It performs a SINGLE user-initiated
RCVN option=2 read and does not persist any provider records, filenames,
horse identifiers, keys or credentials. All statuses are fixed safe codes.

A verified JVInit alone cannot prove entitlement, publication, completeness,
historical as-of availability, final starters, or formal scoring.
"""
import struct
import sys
import time

from windows_jvlink_weekly_read import (
    JvLocalCheckError, MAX_READ_BYTES,
    MAX_DOWNLOAD_WAIT_SECONDS, MAX_FILE_SWITCHES,
)

VERSION = "owner-jvlink-rcvn-once-2"
# RCVN can place many RA records before any SE records. The previous
# 5,000-record diagnostic never reached the result records on real hardware.
# Bounded scan is still observation-only; not a full-history export.
MAX_PROBE_RECORDS = 80000
MAX_PROBE_SECONDS = 60


def probe_rcvn_once(jv, *, budget=MAX_PROBE_RECORDS,
                    sleep=None, monotonic=None,
                    max_download_wait=MAX_DOWNLOAD_WAIT_SECONDS,
                    max_scan_seconds=MAX_PROBE_SECONDS,
                    stop_when_both=False):
    """Only inspect type/version and record length; never retain raw bytes.

    The record limit is a strict safety cap. Hitting it does NOT prove that
    no more data are present, so the diagnostic reports a partial sample.
    """
    if (type(budget) is not int or not 1 <= budget <= MAX_PROBE_RECORDS
            or type(max_download_wait) not in (int, float)
            or not 0 < max_download_wait <= MAX_DOWNLOAD_WAIT_SECONDS
            or type(max_scan_seconds) not in (int, float)
            or not 0 < max_scan_seconds <= MAX_PROBE_SECONDS
            or type(stop_when_both) is not bool):
        raise JvLocalCheckError("RCVN_READ_BUDGET_INVALID")
    sleep = sleep or time.sleep
    monotonic = monotonic or time.monotonic
    opened = False
    total_records = 0
    numbered_history_ra = numbered_history_se = 0
    other_records = 0
    first_download_wait = None
    hit_limit = True
    hit_time = False
    goal_stop = False
    try:
        # Option 2 = this-week material; NOT historical setup/initial load.
        # Do not automatically repeat a failed JVOpen or request option 3/4.
        result = jv.JVOpen("RCVN", "00000000000000", 2, 0, 0, "")
        if not isinstance(result, (tuple, list)) or not result:
            raise JvLocalCheckError("RCVN_OPEN_SHAPE_INVALID")
        if type(result[0]) is not int:
            raise JvLocalCheckError("RCVN_OPEN_SHAPE_INVALID")
        if result[0] == -1:
            raise JvLocalCheckError("RCVN_NO_NEW_DATA")
        if result[0] != 0:
            raise JvLocalCheckError("RCVN_OPEN_UNAVAILABLE")
        opened = True
        file_switches = 0
        scan_started_at = monotonic()
        for _ in range(budget):
            if monotonic() - scan_started_at >= max_scan_seconds:
                hit_time = True
                hit_limit = False
                break
            item = jv.JVGets(bytearray(), MAX_READ_BYTES, bytearray())
            if not isinstance(item, (tuple, list)) or len(item) != 3:
                raise JvLocalCheckError("RCVN_READ_SHAPE_INVALID")
            code, raw, _filename = item
            if type(code) is not int:
                raise JvLocalCheckError("RCVN_READ_SHAPE_INVALID")
            if code == 0:
                hit_limit = False
                break
            if code == -1:
                file_switches += 1
                if file_switches > MAX_FILE_SWITCHES:
                    raise JvLocalCheckError("RCVN_TOO_MANY_FILES")
                continue
            if code == -3:
                if first_download_wait is None:
                    first_download_wait = monotonic()
                remaining = max_download_wait - (monotonic() - first_download_wait)
                if remaining <= 0:
                    raise JvLocalCheckError("RCVN_DOWNLOAD_PENDING")
                sleep(min(2, remaining))
                continue
            if code < -1:
                raise JvLocalCheckError("RCVN_READ_UNAVAILABLE")
            first_download_wait = None
            try:
                record = raw.tobytes() if hasattr(raw, "tobytes") else bytes(raw)
            except (AttributeError, TypeError, ValueError, OverflowError):
                raise JvLocalCheckError("RCVN_RECORD_INVALID") from None
            if code < 3 or code > MAX_READ_BYTES or len(record) < code:
                raise JvLocalCheckError("RCVN_RECORD_INVALID")
            record = record[:code]
            total_records += 1
            if record[:3] == b"RA7" and len(record) == 1272:
                numbered_history_ra += 1
            elif record[:3] == b"SE7" and len(record) == 555:
                numbered_history_se += 1
            else:
                other_records += 1
            # The user only needs proof that BOTH formats are visible.
            # Stop immediately, rather than scanning the whole provider feed.
            if stop_when_both and numbered_history_ra and numbered_history_se:
                goal_stop = True
                hit_limit = False
                break
    finally:
        if opened:
            try:
                if jv.JVClose() != 0:
                    raise JvLocalCheckError("RCVN_CLOSE_FAILED")
            except JvLocalCheckError:
                raise
            except Exception:
                raise JvLocalCheckError("RCVN_CLOSE_FAILED") from None

    # Fixed flags only: never emit raw provider fields or individual IDs.
    # This is a partial diagnostic even if RA7 and SE7 have been observed.
    status = ("RCVN_HISTORY_RA_SE_OBSERVED_PARTIAL" if goal_stop
              else "RCVN_PARTIAL_TIME_LIMIT" if hit_time
              else "RCVN_PARTIAL_BUDGET_LIMIT" if hit_limit
              else "RCVN_HISTORY_RA_SE_OBSERVED"
              if numbered_history_ra and numbered_history_se
              else "RCVN_NO_RA_SE_RESULT_OBSERVED"
              if total_records
              else "RCVN_EMPTY_READ")
    return {
        "version": VERSION,
        "status": status,
        "historicalRaceRecordsObserved": numbered_history_ra > 0,
        "historicalHorseResultsObserved": numbered_history_se > 0,
        "nonHistoricalRecordsObserved": other_records > 0,
        "readWasBudgetLimited": hit_limit,
        "readWasTimeLimited": hit_time,
        "stoppedWhenBothObserved": goal_stop,
        "weeklyCoverageComplete": False,
        "historicalDatasetComplete": False,
        "futureRaceUsabilityVerified": False,
        "officialFinalJraVerified": False,
        "formalTenFactorReady": False,
        "predictionReady": False,
        "bettingReady": False,
        "autoPurchase": False,
        "providerRecordStored": False,
        "networkUploadPerformed": False,
        "privateOwnerOnly": True,
        "researchOnly": True,
    }


def run_once(*, jv_factory=None):
    """Instantiate the installed local COM interface, no auto-installs."""
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
        if jv.JVInit("UNKNOWN") != 0:
            raise JvLocalCheckError("JVINIT_FAILED")
        return probe_rcvn_once(jv, stop_when_both=True)
    except JvLocalCheckError:
        raise
    except Exception:
        raise JvLocalCheckError("RCVN_CHECK_FAILED") from None


def main():
    try:
        report = run_once()
    except JvLocalCheckError as error:
        print("ARC_RACE_RCVN_CHECK=" + str(error))
        print("NOTE=No raw race data was saved or uploaded.")
        return 1
    print("ARC_RACE_RCVN_CHECK=" + report["status"])
    for key, label in (
        ("historicalRaceRecordsObserved", "RCVN_HISTORICAL_RA_OBSERVED"),
        ("historicalHorseResultsObserved", "RCVN_HISTORICAL_SE_OBSERVED"),
        ("readWasBudgetLimited", "RCVN_PARTIAL_READ"),
        ("readWasTimeLimited", "RCVN_TIME_LIMITED"),
        ("stoppedWhenBothObserved", "RCVN_SE_FOUND_EARLY"),
    ):
        print(label + "=" + ("YES" if report[key] else "NO"))
    print("NOTE=Only record types were checked. No complete history or prediction.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
