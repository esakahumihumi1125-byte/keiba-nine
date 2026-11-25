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
from collections import deque
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
    MAX_FILE_SWITCHES, MAX_READ_BYTES, default_race_day, validate_day,
)

VERSION = "owner-jvlink-local-day-history-read-4"
MAX_RACE_STREAM_STEPS = 5000
MAX_RCVN_STREAM_STEPS = 80000
MAX_RCVN_SCAN_SECONDS = 60
MAX_MATCHED_HISTORIES = 5000
MAX_CONTEXT_RA = 10000  # bounded in-memory historical race-context buffer
FIELDS = {
    "RACE": {b"RA2": 1272, b"SE2": 555},
    "RCVN": {b"RA7": 1272, b"SE7": 555},
}


def read_source_once(jv, dataspec, *, day=None, max_steps=None,
                     relevant_ids=None, sleep=None, monotonic=None,
                     max_download_wait=MAX_DOWNLOAD_WAIT_SECONDS,
                     max_rcvn_seconds=MAX_RCVN_SCAN_SECONDS,
                     diagnostics=None):
    """Bounded single JVOpen+JVGets+JVClose stream, no retries or disk I/O.

    RACE retains only requested-day RA2/SE2 (up to 5,000 reads). If
    relevant_ids are passed, RCVN keeps ONLY matching SE7 plus a bounded
    buffer of 10,000 RA7 race-context rows in process memory. Once a
    matching SE7 identifies a needed race, retain its RA7 rather than
    allowing later unrelated records to evict it. The remaining buffer
    is a trailing window of unmatched RA7. Unrelated RA7 and all IDs are
    discarded before any local JSON/HTML is created. If context was
    evicted before its SE7 appeared, distance/going stays unknown.
    This is NOT a complete historical database.
    RCVN scans at most 80,000 steps/60 seconds after JVOpen. Reaching
    either limit is a HOLD, not an assertion of historical completeness.
    """
    if diagnostics is not None and (type(diagnostics) is not dict or diagnostics):
        raise JvLocalCheckError("DAY_HISTORY_DIAGNOSTIC_INPUT_INVALID")
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
    # Real RCVN delivered >5,000 RA7 rows before any SE7 on the owner PC.
    # Keep a bounded trailing context window while selecting only relevant SE.
    context_ra = deque()
    context_index = {}
    needed_ra = set()
    pinned_ra = {}

    def trim_context():
        while len(context_ra) + len(pinned_ra) > MAX_CONTEXT_RA:
            old_key, _ = context_ra.popleft()
            bucket = context_index[old_key]
            bucket.popleft()
            if not bucket:
                del context_index[old_key]

    def pin_context(key, record):
        previous = pinned_ra.get(key)
        if previous is not None and previous != record:
            raise JvLocalCheckError("DAY_HISTORY_INCOMPLETE_OR_MISMATCHED")
        pinned_ra[key] = record
        trim_context()
    if diagnostics is not None:
        diagnostics.update({"ra7RowsObserved": 0, "se7RowsObserved": 0,
                            "matchedSe7Rows": 0, "streamCompleted": False})
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
                if diagnostics is not None:
                    diagnostics["streamCompleted"] = True
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
                # Only aggregate counts. Never expose registration IDs or
                # raw licensed provider records to terminal output / JSON.
                if diagnostics is not None:
                    diagnostics["ra7RowsObserved" if record[:3] == b"RA7"
                                else "se7RowsObserved"] += 1
                if record[:3] == b"RA7":
                    # Historical RA7 does not contain horse IDs. Retain only
                    # a bounded in-memory candidate set; match to selected
                    # runners' SE7 before exposing any race context.
                    race_key = record[11:27]
                    if race_key in needed_ra:
                        pin_context(race_key, record)
                    else:
                        context_ra.append((race_key, record))
                        context_index.setdefault(race_key, deque()).append(record)
                        trim_context()
                    continue
                if record[:3] != b"SE7" or record[30:40] not in relevant_ids:
                    continue
                if diagnostics is not None:
                    diagnostics["matchedSe7Rows"] += 1
                if len(observed) >= MAX_MATCHED_HISTORIES:
                    raise JvLocalCheckError("DAY_HISTORY_RCVN_MATCH_LIMIT")
                race_key = record[11:27]
                if race_key not in needed_ra:
                    needed_ra.add(race_key)
                    # Compare all still-buffered revisions BEFORE eviction.
                    bucket = context_index.get(race_key)
                    if bucket:
                        candidate = bucket[0]
                        if any(row != candidate for row in bucket):
                            raise JvLocalCheckError("DAY_HISTORY_INCOMPLETE_OR_MISMATCHED")
                        pin_context(race_key, candidate)
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
    if dataspec == "RCVN" and relevant_ids is not None:
        return observed + list(pinned_ra.values())
    return observed



def select_complete_prestart_races(current, day, *, as_of, flat_only=False):
    """Validate all pre-off card candidates without any historical provider call.

    Rejects duplicate conflicting rows. An incomplete race is omitted rather
    than contaminating a complete one. No past data or private horse IDs are
    logged or stored; candidates remain process-local until one RCVN read.
    """
    if (type(flat_only) is not bool
            or not isinstance(current, (list, tuple))
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
    any_upcoming = False
    for identity, ra in ra_by_key.items():
        horse_rows = [row for (key, _number), row in se_by_key.items()
                      if key == identity]
        try:
            parsed = parse_jvdata_prestart_racecard(ra, horse_rows, day)
        except CoverageError:
            continue
        any_complete = True
        off_time = datetime.strptime(
            day + parsed["postTimeCandidate"], "%Y%m%d%H:%M"
        ).replace(tzinfo=JST)
        if as_of.astimezone(JST) >= off_time:
            continue
        any_upcoming = True
        # Flat-only study never promotes jumps or an unknown RA course.
        if flat_only and (parsed.get("surfaceCandidate") not in ("芝", "ダート")
                          or type(parsed.get("distanceMetersCandidate")) is not int):
            continue
        eligible.append((off_time, parsed["track"], parsed["race"],
                         [ra, *horse_rows]))
    if not any_complete:
        raise JvLocalCheckError("DAY_HISTORY_NO_COMPLETE_RACE")
    if not eligible:
        if flat_only and any_upcoming:
            raise JvLocalCheckError("DAY_HISTORY_NO_SUPPORTED_FLAT_PRESTART")
        raise JvLocalCheckError("DAY_HISTORY_ALL_RACES_STARTED")
    if len(eligible) > 36:
        raise JvLocalCheckError("DAY_HISTORY_TOO_MANY_RACE_CANDIDATES")
    eligible.sort(key=lambda row: (row[0], row[1], row[2]))
    return eligible


def select_one_complete_prestart_race(current, day, *, as_of, flat_only=False):
    """Backward-compatible single-race prestart selection."""
    return select_complete_prestart_races(
        current, day, as_of=as_of, flat_only=flat_only,
    )[0][3]


def read_local_day_history(day, *, jv_factory=None, captured_at=None,
                           flat_only=False, all_flat_races=False,
                           diagnostics=None):
    """One RACE read and one RCVN read, no unattended resubmission.

    Opt-in all_flat_races exports ALL complete upcoming flat card candidates
    from the same source reads. It never treats absent SE7 as a debut or
    confirms an official JRA starter roster. The default remains one race.
    """
    validate_day(day)
    if type(all_flat_races) is not bool or (all_flat_races and flat_only is not True):
        raise JvLocalCheckError("DAY_HISTORY_BATCH_MODE_INVALID")
    if diagnostics is not None and (type(diagnostics) is not dict or diagnostics):
        raise JvLocalCheckError("DAY_HISTORY_DIAGNOSTIC_INPUT_INVALID")
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
        candidates = select_complete_prestart_races(
            current, day, as_of=observed_at, flat_only=flat_only)
        # In flat-only mode, match ALL eligible flat starters in a SINGLE
        # RCVN scan. A sole first-race match failure should not force the
        # owner into repeated paid JRA-VAN reads for later races.
        selected = candidates if flat_only else candidates[:1]
        ids = {row[30:40] for _off, _track, _race, card in selected
               for row in card if row[:3] == b"SE2"}
        if not ids:
            raise JvLocalCheckError("DAY_HISTORY_NO_CURRENT_HORSES")
        scan = {}
        history = read_source_once(jv, "RCVN", relevant_ids=ids,
                                   diagnostics=scan)
        if diagnostics is not None:
            diagnostics.update({"candidateFlatRaceCount": len(selected),
                                "candidateHorseCount": len(ids), **scan})
        matched_ids = {raw[30:40] for raw in history if raw[:3] == b"SE7"}
        # Recheck the actual clock after the provider read. Never create
        # retroactive candidate picks for races which have already started.
        completed_at = captured_at or datetime.now(JST)
        upcoming = [(off, card) for off, _track, _race, card in selected
                    if completed_at.astimezone(JST) < off]
        if all_flat_races:
            # A single complete RACE+RCVN read can now produce 1-36 cards.
            # Never reconstitute a race which has started during the scan.
            if not upcoming:
                raise JvLocalCheckError("DAY_HISTORY_ALL_RACES_STARTED")
            matched = sum(bool({raw[30:40] for raw in card
                                if raw[:3] == b"SE2"} & matched_ids)
                          for _off, card in upcoming)
            if not matched:
                raise JvLocalCheckError("DAY_HISTORY_NO_MATCHED_RCVN_HORSE_ROWS")
            if diagnostics is not None:
                diagnostics["prestartFlatRaceCount"] = len(upcoming)
                diagnostics["racesWithObservedPriorRows"] = matched
            return build_local_day_history(
                [raw for _off, card in upcoming for raw in card],
                history, day, captured_at=completed_at,
            )
        for _off, card in upcoming:
            card_ids = {raw[30:40] for raw in card if raw[:3] == b"SE2"}
            if card_ids & matched_ids:
                return build_local_day_history(
                    card, history, day, captured_at=completed_at,
                )
        if any(completed_at.astimezone(JST) < off
               for off, _track, _race, _card in selected):
            raise JvLocalCheckError("DAY_HISTORY_NO_MATCHED_RCVN_HORSE_ROWS")
        raise JvLocalCheckError("DAY_HISTORY_ALL_RACES_STARTED")
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
        lines.append("<section><h2>" + title + "</h2><p>"
                     "過去RA7とSE7の同一レース照合ができた場合のみ"
                     "過去の距離・馬場を表示。今回の馬場・適性とは別です。</p>")
        for horse in race["byNumber"]:
            label = "{}番 / 過去走観測 {}件".format(
                horse["number"], horse["observedRecordCount"],
            )
            lines.append("<details><summary>" + label + "</summary>")
            lines.append("<table><tr><th>過去開催日</th><th>過去の芝・ダ</th>"
                         "<th>過去着順</th><th>過去距離</th>"
                         "<th>当時馬場</th><th>上がり3F候補</th></tr>")
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
    appdata = os.environ.get("LOCALAPPDATA")
    if not appdata or not Path(appdata).is_absolute():
        raise JvLocalCheckError("DAY_HISTORY_LOCALAPPDATA_UNAVAILABLE")
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



def save_private_day_local(report):
    """Create-only multi-race JSON + HTML, never alter saved one-race files.

    The multiple racecards are already redacted by build_local_day_history.
    This never writes provider records, horse registration IDs or a public
    upload; 1-36 race coordinates are checked before a filesystem write.
    """
    if (not isinstance(report, dict)
            or report.get("version") != "owner-jvdata-local-day-history-bridge-1"
            or report.get("privateOwnerOnly") is not True
            or report.get("researchOnly") is not True
            or report.get("formalTenFactorReady") is not False
            or report.get("productionPredictionReady") is not False
            or report.get("officialStarterListVerified") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False
            or type(report.get("date")) is not str
            or not _valid_date(report["date"])
            or type(report.get("raceCount")) is not int
            or not 1 <= report["raceCount"] <= 36
            or not isinstance(report.get("races"), list)
            or len(report["races"]) != report["raceCount"]):
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_REPORT_INVALID")
    seen = set()
    for row in report["races"]:
        if (not isinstance(row, dict)
                or row.get("track") not in TRACKS.values()
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12
                or (row["track"], row["race"]) in seen
                or row.get("bettingReady") is not False
                or row.get("graded") is not False):
            raise JvLocalCheckError("DAY_HISTORY_LOCAL_REPORT_INVALID")
        seen.add((row["track"], row["race"]))
    folder_text = os.environ.get("LOCALAPPDATA")
    if not folder_text or not Path(folder_text).is_absolute():
        raise JvLocalCheckError("DAY_HISTORY_LOCALAPPDATA_UNAVAILABLE")
    folder = Path(folder_text) / "ARC-RACE-private"
    try:
        folder.mkdir(parents=True, exist_ok=True)
        bodies = (
            json.dumps(report, ensure_ascii=False, indent=2),
            local_html(report),
        )
    except (OSError, CoverageError, TypeError, ValueError):
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_REPORT_INVALID") from None
    base = "jvdata-all-flat-races-" + report["date"]
    targets = [folder / (base + ext) for ext in (".json", ".html")]
    if any(target.exists() or target.is_symlink() for target in targets):
        raise JvLocalCheckError("DAY_HISTORY_ALREADY_SAVED")
    staged, linked = [], []
    try:
        for body in bodies:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=folder, prefix=".arc-race-all-",
                suffix=".tmp", delete=False,
            ) as output:
                temp_path = Path(output.name)
                staged.append(temp_path)
                output.write(body)
                output.flush()
                os.fsync(output.fileno())
        for source, target in zip(staged, targets):
            os.link(source, target)
            linked.append(target)
    except FileExistsError:
        for target in linked:
            target.unlink(missing_ok=True)
        raise JvLocalCheckError("DAY_HISTORY_ALREADY_SAVED") from None
    except OSError:
        for target in linked:
            target.unlink(missing_ok=True)
        raise JvLocalCheckError("DAY_HISTORY_LOCAL_SAVE_FAILED") from None
    finally:
        for stage in staged:
            stage.unlink(missing_ok=True)
    return targets[1]


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="ARC RACE private this-week JRA-VAN RACE+RCVN preview"
    )
    parser.add_argument("--date", default=None, help="YYYYMMDD; today on Sat/Sun, next Saturday otherwise")
    parser.add_argument("--flat-only", action="store_true",
                        help="Skip jump/unknown course before history read")
    parser.add_argument("--all-flat-races", action="store_true",
                        help="One RACE+RCVN scan for all complete prestart flat racecards")
    args = parser.parse_args(argv)
    day = args.date or default_race_day()
    diagnostics = {}
    try:
        report = read_local_day_history(
            day, flat_only=args.flat_only or args.all_flat_races,
            all_flat_races=args.all_flat_races, diagnostics=diagnostics)
        target = (save_private_day_local(report) if args.all_flat_races
                  else save_private_local(report))
        print("ARC_RACE_DAY_HISTORY=SUCCESS_RESEARCH_ONLY")
        print("RACE_COUNT=" + str(report["raceCount"]))
        if args.all_flat_races:
            print("ALL_FLAT_PRESTART_RESEARCH=YES")
            print("RACES_WITH_PRIOR_OBSERVATIONS=" + str(
                diagnostics.get("racesWithObservedPriorRows", 0)))
        print("FORMAL_PREDICTION=NO")
        print("PRIVATE_LOCAL_VIEW=READY")
        if diagnostics.get("streamCompleted"):
            print("RCVN_RA7_ROWS_OBSERVED=" + str(diagnostics["ra7RowsObserved"]))
            print("RCVN_SE7_ROWS_OBSERVED=" + str(diagnostics["se7RowsObserved"]))
            print("RCVN_MATCHED_SE7_ROWS=" + str(diagnostics["matchedSe7Rows"]))
        if hasattr(os, "startfile"):
            try:
                os.startfile(str(target))
            except OSError:
                print("PRIVATE_LOCAL_VIEW_OPEN=MANUAL")
        return 0
    except JvLocalCheckError as error:
        print("ARC_RACE_DAY_HISTORY=" + str(error))
        if diagnostics.get("streamCompleted"):
            print("CANDIDATE_FLAT_RACES=" + str(diagnostics["candidateFlatRaceCount"]))
            print("CANDIDATE_HORSES=" + str(diagnostics["candidateHorseCount"]))
            print("RCVN_RA7_ROWS_OBSERVED=" + str(diagnostics["ra7RowsObserved"]))
            print("RCVN_SE7_ROWS_OBSERVED=" + str(diagnostics["se7RowsObserved"]))
            print("RCVN_MATCHED_SE7_ROWS=" + str(diagnostics["matchedSe7Rows"]))
        print("FORMAL_PREDICTION=NO")
        return 1


if __name__ == "__main__":
    sys.exit(main())
