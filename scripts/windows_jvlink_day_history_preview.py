"""Explicit owner-PC, local-only current RACE + RCVN historical preview.

This opt-in single operation reads each data-spec once (option 2), holds
provider RA/SE records only in process memory, and saves ONLY a stripped
per-horse-number research report under LOCALAPPDATA.

NO raw JV-Data, registration IDs, horse names, secrets, source filenames or
full historical database are saved or sent to GitHub, Render or the browser.
A valid report is still not a final JRA card, verified historical delivery,
formal score, wager, or production prediction.
"""
import argparse
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import time

from jrdb_coverage import CoverageError
from owner_jvdata_day_history_bridge import build_local_day_history
from jvdata_ra_se_candidate import parse_jvdata_prestart_racecard
from jrdb_program_preview import TRACKS
from jrdb_evidence_readiness import _valid_date
from windows_jvlink_weekly_read import (
    DATE, JST, JvLocalCheckError, MAX_DOWNLOAD_WAIT_SECONDS,
    MAX_FILE_SWITCHES, MAX_READ_BYTES, next_saturday, validate_day,
)

VERSION = "owner-jvlink-local-day-history-read-3"
MAX_RACE_STREAM_STEPS = 5000
MAX_RCVN_STREAM_STEPS = 80000
MAX_RCVN_SCAN_SECONDS = 60
MAX_MATCHED_HISTORIES = 5000
FIELDS = {
    "RACE": {b"RA2": 1272, b"SE2": 555},
    "RCVN": {b"RA7": 1272, b"SE7": 555},
}


def read_source_once(jv, dataspec, *, day=None, max_steps=None,
                     relevant_ids=None, sleep=None, monotonic=None,
                     max_download_wait=MAX_DOWNLOAD_WAIT_SECONDS,
                     max_rcvn_seconds=MAX_RCVN_SCAN_SECONDS):
    """Bounded single JVOpen+JVGets+JVClose stream, no retries or disk I/O.

    RACE retains only requested-day RA2/SE2 (up to 5,000 reads). If
    relevant_ids are passed, RCVN keeps ONLY matching SE7 in memory, never
    entire history or unrelated RA7, because the user's first real read
    found 5,000+ RA7 before reaching any SE7. The research output has
    unknown past race surface/distance until separately verified.
    RCVN scans at most 80,000 steps/60 seconds after JVOpen. Reaching
    either limit is a HOLD, not an assertion of historical completeness.
    """
    cap = MAX_RACE_STREAM_STEPS if dataspec == "RACE" else MAX_RCVN_STREAM_STEPS
    if max_steps is None:
        max_steps = cap
    if (dataspec not in FIELDS
            or type(max_steps) is not int or not 1 <= max_steps <= cap
            or type(max_download_wait) not in (int, float)
            or not 0 < max_download_wait <= MAX_DOWNLOAD_WAIT_SECONDS
            or type(max_rcvn_seconds) not in (int, float)
            or not 0 < max_rcvn_seconds <= MAX_RCVN_SCAN_SECONDS
            or (dataspec == "RACE"
                and (type(day) is not str or DATE.fullmatch(day) is None
                     or relevant_ids is not None))
            or (relevant_ids is not None
                and (dataspec != "RCVN" or type(relevant_ids) is not set
                     or not 1 <= len(relevant_ids) <= 648
                     or any(type(x) is not bytes or len(x) != 10
                            or not x.isalnum() for x in relevant_ids)))):
        raise JvLocalCheckError("DAY_HISTORY_BUDGET_OR_INPUT_INVALID")
    sleep = sleep or time.sleep
    monotonic = monotonic or time.monotonic
    opened = False
    first_pending_at = None
    observed = []
    try:
        response = jv.JVOpen(dataspec, "00000000000000", 2, 0, 0, "")
        if (not isinstance(response, (tuple, list))
                or not response or type(response[0]) is not int):
            raise JvLocalCheckError("DAY_HISTORY_OPEN_SHAPE_INVALID")
        if response[0] == -1:
            raise JvLocalCheckError("DAY_HISTORY_" + dataspec + "_NO_NEW_DATA")
        if response[0] != 0:
            raise JvLocalCheckError("DAY_HISTORY_" + dataspec + "_UNAVAILABLE")
        opened = True
        file_switches = 0
        scan_started_at = monotonic()
        for _ in range(max_steps):
            if (dataspec == "RCVN"
                    and monotonic() - scan_started_at >= max_rcvn_seconds):
                raise JvLocalCheckError("DAY_HISTORY_RCVN_TIME_LIMIT")
            result = jv.JVGets(bytearray(), MAX_READ_BYTES, bytearray())
            if (not isinstance(result, (tuple, list)) or len(result) != 3
                    or type(result[0]) is not int):
                raise JvLocalCheckError("DAY_HISTORY_READ_SHAPE_INVALID")
            code, raw, _filename = result
            if code == 0:
                break
            if code == -1:
                file_switches += 1
                if file_switches > MAX_FILE_SWITCHES:
                    raise JvLocalCheckError("DAY_HISTORY_TOO_MANY_FILES")
                continue
            if code == -3:
                if first_pending_at is None:
                    first_pending_at = monotonic()
                remaining = max_download_wait - (monotonic() - first_pending_at)
                if remaining <= 0:
                    raise JvLocalCheckError("DAY_HISTORY_DOWNLOAD_PENDING")
                sleep(min(2, remaining))
                continue
            if code < -1:
                raise JvLocalCheckError("DAY_HISTORY_READ_FAILED")
            first_pending_at = None
            try:
                record = raw.tobytes() if hasattr(raw, "tobytes") else bytes(raw)
            except (AttributeError, TypeError, ValueError, OverflowError):
                raise JvLocalCheckError("DAY_HISTORY_RECORD_INVALID") from None
            if code < 3 or code > MAX_READ_BYTES or len(record) < code:
                raise JvLocalCheckError("DAY_HISTORY_RECORD_INVALID")
            record = record[:code]
            expected = FIELDS[dataspec].get(record[:3])
            if expected is None:
                continue
            if len(record) != expected or record[-2:] != b"\r\n":
                raise JvLocalCheckError("DAY_HISTORY_RECORD_INVALID")
            if dataspec == "RACE":
                if record[11:19].decode("ascii", errors="replace") != day:
                    continue
            elif relevant_ids is not None:
                # Do not retain unrelated RA7 or any other horse's SE7.
                # Past RA details stay unverified; this is first a proof of
                # actual current-horse / past-result identity matching.
                if record[:3] != b"SE7" or record[30:40] not in relevant_ids:
                    continue
                if len(observed) >= MAX_MATCHED_HISTORIES:
                    raise JvLocalCheckError("DAY_HISTORY_RCVN_MATCH_LIMIT")
            observed.append(record)
        else:
            raise JvLocalCheckError("DAY_HISTORY_" + dataspec + "_BUDGET_LIMIT")
    finally:
        if opened:
            try:
                if jv.JVClose() != 0:
                    raise JvLocalCheckError("DAY_HISTORY_CLOSE_FAILED")
            except JvLocalCheckError:
                raise
            except Exception:
                raise JvLocalCheckError("DAY_HISTORY_CLOSE_FAILED") from None
    return observed



def select_one_complete_prestart_race(current, day, *, as_of):
    """Select ONE complete RA2/SE2 candidate before any RCVN request.

    This is a pure, in-memory preflight. First find exact race identities,
    reject divergent replay rows and check the entire runner count. A single
    partial race must not trigger a potentially billable historical download.
    Prefer the earliest still-upcoming, fully numbered race, not just the
    first RA file row. No race identifiers, paid rows or horse IDs are logged.
    """
    if (not isinstance(current, (list, tuple))
            or not isinstance(as_of, datetime) or as_of.tzinfo is None
            or as_of.utcoffset() is None):
        raise JvLocalCheckError("DAY_HISTORY_PRESTART_INPUT_INVALID")
    ra_by_key, se_by_key = {}, {}
    for raw in current:
        if (type(raw) is not bytes or len(raw) < 40
                or raw[:3] not in (b"RA2", b"SE2")
                or raw[11:19] != day.encode("ascii")):
            raise JvLocalCheckError("DAY_HISTORY_CURRENT_CARD_INVALID")
        identity = raw[11:27]
        if len(identity) != 16 or not identity.isdigit():
            raise JvLocalCheckError("DAY_HISTORY_CURRENT_CARD_INVALID")
        if raw[:3] == b"RA2":
            previous = ra_by_key.get(identity)
            if previous is not None and previous != raw:
                raise JvLocalCheckError("DAY_HISTORY_CURRENT_ROSTER_CONFLICT")
            ra_by_key[identity] = raw
        else:
            horse_key = (identity, raw[28:30])
            previous = se_by_key.get(horse_key)
            if previous is not None and previous != raw:
                raise JvLocalCheckError("DAY_HISTORY_CURRENT_ROSTER_CONFLICT")
            se_by_key[horse_key] = raw

    eligible = []
    any_complete = False
    for identity, ra in ra_by_key.items():
        horse_rows = [row for (key, _number), row in se_by_key.items()
                      if key == identity]
        try:
            parsed = parse_jvdata_prestart_racecard(ra, horse_rows, day)
        except CoverageError:
            # An incomplete pre-publication race is not a verified starter
            # list and may not be used to justify an RCVN lookup.
            continue
        any_complete = True
        off_time = datetime.strptime(
            day + parsed["postTimeCandidate"], "%Y%m%d%H:%M"
        ).replace(tzinfo=JST)
        if as_of.astimezone(JST) >= off_time:
            continue
        eligible.append((off_time, parsed["track"], parsed["race"], ra,
                         tuple(horse_rows)))
    if not any_complete:
        raise JvLocalCheckError("DAY_HISTORY_NO_COMPLETE_RACE")
    if not eligible:
        raise JvLocalCheckError("DAY_HISTORY_ALL_RACES_STARTED")
    eligible.sort(key=lambda row: (row[0], row[1], row[2]))
    _off, _track, _number, ra, horses = eligible[0]
    return [ra, *horses]


def read_local_day_history(day, *, jv_factory=None, captured_at=None):
    """One RACE read and one RCVN read, no unattended resubmission."""
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
        if jv.JVInit("UNKNOWN") != 0:
            raise JvLocalCheckError("JVINIT_FAILED")
        current = read_source_once(jv, "RACE", day=day)
        if not current:
            raise JvLocalCheckError("DAY_HISTORY_NO_CURRENT_CARDS")
        # Do not fetch RCVN before one actual prestart race's complete
        # roster is validated. Only selected horse IDs may enter RCVN.
        observed_at = captured_at or datetime.now(JST)
        current = select_one_complete_prestart_race(
            current, day, as_of=observed_at)
        # IDs remain process-local; JSON/HTML contains only race and numbers.
        current_ids = {raw[30:40] for raw in current if raw[:3] == b"SE2"}
        if not current_ids:
            raise JvLocalCheckError("DAY_HISTORY_NO_CURRENT_HORSES")
        history = read_source_once(jv, "RCVN", relevant_ids=current_ids)
        if not history:
            raise JvLocalCheckError("DAY_HISTORY_NO_MATCHED_RCVN_HORSE_ROWS")
        # Always recheck the local clock after the second provider read.
        # It is unsafe to label a race "prestart" solely because it was
        # prestart when the first request began.
        completed_at = captured_at or datetime.now(JST)
        return build_local_day_history(
            current, history, day, captured_at=completed_at,
        )
    except JvLocalCheckError:
        raise
    except CoverageError:
        raise JvLocalCheckError("DAY_HISTORY_INCOMPLETE_OR_MISMATCHED") from None
    except Exception:
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_READ_FAILED") from None


def _display_value(v):
    if v is None:
        return "—"
    return escape(str(v))


def local_html(report):
    """Display only the already sanitized report; no network or JS."""
    if (not isinstance(report, dict)
            or report.get("version") != "owner-jvdata-local-day-history-bridge-1"
            or report.get("privateOwnerOnly") is not True
            or report.get("productionPredictionReady") is not False
            or report.get("bettingReady") is not False):
        raise CoverageError("Invalid local history report")
    lines = [
        "<!doctype html><html lang='ja'><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>ARC RACE 過去走候補（PC内のみ）</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:1000px;",
        "margin:auto;padding:18px;background:#f5f7fb;color:#152237}",
        "section{background:white;padding:14px;border-radius:12px;",
        "margin:14px 0;box-shadow:0 1px 7px #cad4e5}",
        "table{border-collapse:collapse;width:100%;font-size:13px}",
        "td,th{border-bottom:1px solid #dbe2ec;padding:6px;text-align:left}",
        "details{margin:8px 0}summary{font-weight:700;cursor:pointer}",
        ".warning{padding:12px;border:1px solid #c5a660;border-radius:8px}",
        "</style><h1>ARC RACE | 過去走の研究用候補</h1>",
        "<p class='warning'>⚠ 出走取消・最終馬場・発走時刻変更は未確認。",
        "実履歴の網羅性や利用可能時刻も未確認。正式採点・購入には使用不可。</p>",
    ]
    for race in report["races"]:
        title = "{} {}R".format(_display_value(race["track"]), race["race"])
        lines.append("<section><h2>" + title + "</h2>")
        for horse in race["byNumber"]:
            label = "{}番 / 過去走観測 {}件".format(
                horse["number"], horse["observedRecordCount"],
            )
            lines.append("<details><summary>" + label + "</summary>")
            lines.append("<table><tr><th>日付</th><th>コース</th><th>着順</th>"
                         "<th>距離</th><th>馬場</th><th>上がり3F</th></tr>")
            for run in horse["recentObservedRuns"]:
                rows = (
                    run.get("date"), run.get("surface"),
                    run.get("finishPosition"), run.get("distanceMeters"),
                    run.get("going"), run.get("last3fTenths"),
                )
                lines.append("<tr>" + "".join(
                    "<td>" + _display_value(x) + "</td>" for x in rows
                ) + "</tr>")
            lines.append("</table></details>")
        lines.append("</section>")
    lines.append("</html>")
    return "".join(lines)


def save_private_local(report):
    """Atomic create-only JSON/HTML under LOCALAPPDATA. No overwrite."""
    appdata = os.environ.get("LOCALAPPDATA")
    if not appdata or not Path(appdata).is_absolute():
        raise JvLocalCheckError("DAY_HISTORY_LOCALAPPDATA_UNAVAILABLE")
    # One preview per original race; never overwrite the previous first-R
    # research record when another race becomes the earliest live option.
    if (not isinstance(report, dict)
            or report.get("version") != "owner-jvdata-local-day-history-bridge-1"
            or type(report.get("date")) is not str
            or not _valid_date(report["date"])
            or type(report.get("raceCount")) is not int
            or report["raceCount"] != 1
            or not isinstance(report.get("races"), list)
            or len(report["races"]) != 1
            or not isinstance(report["races"][0], dict)
            or type(report["races"][0].get("race")) is not int
            or not 1 <= report["races"][0]["race"] <= 12
            or report["races"][0].get("track") not in TRACKS.values()):
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_REPORT_INVALID")
    race = report["races"][0]
    track_code = next(code for code, name in TRACKS.items()
                      if name == race["track"])
    folder = Path(appdata) / "ARC-RACE-private"
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_SAVE_FAILED") from None
    base = "jvdata-one-race-{}-{}-{:02d}".format(
        report["date"], track_code, race["race"])
    targets = [folder / (base + ext) for ext in (".json", ".html")]
    try:
        bodies = (
            json.dumps(report, ensure_ascii=False, indent=2),
            local_html(report),
        )
    except (CoverageError, TypeError, ValueError):
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_REPORT_INVALID") from None
    staged = []
    linked = []
    try:
        for body in bodies:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=folder, prefix=".arc-race-history-",
                suffix=".tmp", delete=False,
            ) as output:
                pending = Path(output.name)
                staged.append(pending)
                output.write(body)
                output.flush()
                os.fsync(output.fileno())
        for source, dest in zip(staged, targets):
            os.link(source, dest)
            linked.append(dest)
    except FileExistsError:
        for path in linked:
            path.unlink(missing_ok=True)
        raise JvLocalCheckError("DAY_HISTORY_ALREADY_SAVED") from None
    except OSError:
        for path in linked:
            path.unlink(missing_ok=True)
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_SAVE_FAILED") from None
    finally:
        for path in staged:
            path.unlink(missing_ok=True)
    return targets[1]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="ARC RACE private this-week JRA-VAN RACE+RCVN preview"
    )
    parser.add_argument("--date", default=None, help="YYYYMMDD; next Saturday if omitted")
    args = parser.parse_args(argv)
    day = args.date or next_saturday()
    try:
        report = read_local_day_history(day)
        target = save_private_local(report)
        print("ARC_RACE_DAY_HISTORY=SUCCESS_RESEARCH_ONLY")
        print("RACE_COUNT=" + str(report["raceCount"]))
        print("FORMAL_PREDICTION=NO")
        print("PRIVATE_LOCAL_VIEW=READY")
        if hasattr(os, "startfile"):
            try:
                os.startfile(str(target))
            except OSError:
                print("PRIVATE_LOCAL_VIEW_OPEN=MANUAL")
        return 0
    except JvLocalCheckError as error:
        print("ARC_RACE_DAY_HISTORY=" + str(error))
        print("FORMAL_PREDICTION=NO")
        return 1


if __name__ == "__main__":
    sys.exit(main())
