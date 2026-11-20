"""Review already saved ARC RACE private JSON, entirely offline.

A single click on this script never calls JV-Link, REST APIs, browsers over
HTTP, providers, payment, betting, GitHub or Render. It creates new
research-only sanitized evidence views beside the original report.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from jrdb_coverage import CoverageError
from owner_jvdata_offline_evidence import summarize_one_race, render_evidence_html
from windows_jvlink_weekly_read import JST, JvLocalCheckError

FILE = re.compile(r"jvdata-one-race-(20[0-9]{6})-([0-9]{2})-([0-9]{2})[.]json\Z")
MAX_SAVED_BYTES = 2_000_000


def private_source(day=None, *, appdata=None):
    """Choose latest existing sanitized report, no provider access."""
    if day is None:
        day = datetime.now(JST).strftime("%Y%m%d")
    if not isinstance(day, str) or re.fullmatch(r"20[0-9]{6}", day) is None:
        raise JvLocalCheckError("OFFLINE_EVIDENCE_DATE_INVALID")
    try:
        datetime.strptime(day, "%Y%m%d")
    except ValueError:
        raise JvLocalCheckError("OFFLINE_EVIDENCE_DATE_INVALID") from None
    folder = Path(appdata or os.environ.get("LOCALAPPDATA") or "")
    if not folder.is_absolute():
        raise JvLocalCheckError("OFFLINE_EVIDENCE_LOCALAPPDATA_UNAVAILABLE")
    folder = folder / "ARC-RACE-private"
    if not folder.is_dir() or folder.is_symlink():
        raise JvLocalCheckError("OFFLINE_EVIDENCE_NO_SAVED_RESEARCH")
    options = []
    for path in folder.glob("jvdata-one-race-" + day + "-??-??.json"):
        match = FILE.fullmatch(path.name)
        if match is None or path.is_symlink() or not path.is_file():
            continue
        size = path.stat().st_size
        if 0 < size <= MAX_SAVED_BYTES:
            options.append(path)
    if not options:
        raise JvLocalCheckError("OFFLINE_EVIDENCE_NO_SAVED_RESEARCH")
    return max(options, key=lambda x: (x.stat().st_mtime_ns, x.name))


def save_offline_review(source):
    """Safe, atomic, create-only static HTML + sanitized evidence JSON."""
    if not isinstance(source, Path) or not FILE.fullmatch(source.name):
        raise JvLocalCheckError("OFFLINE_EVIDENCE_BAD_INPUT")
    if source.is_symlink() or not source.is_file():
        raise JvLocalCheckError("OFFLINE_EVIDENCE_BAD_INPUT")
    if source.stat().st_size > MAX_SAVED_BYTES:
        raise JvLocalCheckError("OFFLINE_EVIDENCE_BAD_INPUT")
    try:
        original = json.loads(source.read_text("utf-8"))
        evidence = summarize_one_race(original)
        if evidence["date"] != FILE.fullmatch(source.name).group(1):
            raise CoverageError("Private report/date mismatch")
        html = render_evidence_html(evidence)
        json_body = json.dumps(evidence, ensure_ascii=False, indent=2)
    except (OSError, UnicodeError, ValueError, TypeError, CoverageError):
        raise JvLocalCheckError("OFFLINE_EVIDENCE_BAD_INPUT") from None
    targets = (
        source.with_name(source.stem + "-evidence.json"),
        source.with_name(source.stem + "-evidence.html"),
    )
    if all(p.is_file() and not p.is_symlink() for p in targets):
        return targets[1], evidence
    if any(p.exists() or p.is_symlink() for p in targets):
        raise JvLocalCheckError("OFFLINE_EVIDENCE_TARGET_CONFLICT")
    staged, linked = [], []
    try:
        for body in (json_body, html):
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", prefix=".arc-race-evidence-",
                suffix=".tmp", dir=source.parent, delete=False,
            ) as output:
                stage = Path(output.name)
                staged.append(stage)
                output.write(body)
                output.flush()
                os.fsync(output.fileno())
        for stage, target in zip(staged, targets):
            os.link(stage, target)
            linked.append(target)
    except OSError:
        for path in linked:
            path.unlink(missing_ok=True)
        raise JvLocalCheckError("OFFLINE_EVIDENCE_LOCAL_SAVE_FAILED") from None
    finally:
        for path in staged:
            path.unlink(missing_ok=True)
    return targets[1], evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline owner-only factor evidence")
    parser.add_argument("--date", help="Local JRA date YYYYMMDD; default today JST")
    args = parser.parse_args(argv)
    try:
        source = private_source(args.date)
        target, result = save_offline_review(source)
    except JvLocalCheckError as error:
        print("ARC_RACE_OFFLINE_EVIDENCE=" + str(error))
        return 1
    print("ARC_RACE_OFFLINE_EVIDENCE=READY_UNGRADED")
    print("RUNNERS=" + str(result["runnerCount"]))
    print("HISTORY_OBSERVED_RUNNERS=" + str(result["runnersWithObservedHistory"]))
    print("FORMAL_PREDICTION=NO")
    print("JVLINK_REQUESTS=0")
    if hasattr(os, "startfile"):
        try:
            os.startfile(str(target))
        except OSError:
            print("LOCAL_VIEW_OPEN=MANUAL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
