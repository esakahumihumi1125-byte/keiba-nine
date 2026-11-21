"""One-click offline, create-only research trial from a saved JRA-VAN race.

No JV-Link, paid API, internet, Render, GitHub, bets or records are modified.
The 3連単 is an unvalidated past-only study, shown only before scheduled off.
"""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tempfile

from jrdb_coverage import CoverageError
from owner_jvdata_horse_history_coverage import JST
from owner_jvdata_offline_trifecta_trial import (
    build_local_trifecta_study, render_local_trifecta_html,
)
from windows_arc_race_saved_history_review import (
    FILE, MAX_SAVED_BYTES, private_source, JvLocalCheckError,
)


def save_offline_trifecta_trial(source, *, as_of=None):
    if (not isinstance(source, Path) or not FILE.fullmatch(source.name)
            or source.is_symlink() or not source.is_file()
            or not 0 < source.stat().st_size <= MAX_SAVED_BYTES):
        raise JvLocalCheckError("LOCAL_TRIFECTA_SOURCE_INVALID")
    try:
        original = json.loads(source.read_text("utf-8"))
        research = build_local_trifecta_study(original, as_of=as_of)
        if research["date"] != FILE.fullmatch(source.name).group(1):
            raise CoverageError("Local day mismatch")
        body_json = json.dumps(research, ensure_ascii=False, indent=2)
        body_html = render_local_trifecta_html(research)
    except (OSError, UnicodeError, ValueError, TypeError, CoverageError):
        raise JvLocalCheckError("LOCAL_TRIFECTA_SOURCE_INVALID") from None

    basename = source.stem + "-trifecta-study"
    json_file = source.with_name(basename + ".json")
    html_file = source.with_name(basename + ".html")
    targets = (json_file, html_file)
    bodies = (body_json, body_html)
    if all(target.is_file() and not target.is_symlink() for target in targets):
        try:
            if any(p.read_text("utf-8") != body for p, body in zip(targets, bodies)):
                raise JvLocalCheckError("LOCAL_TRIFECTA_RESEARCH_CONFLICT")
        except (OSError, UnicodeError):
            raise JvLocalCheckError("LOCAL_TRIFECTA_RESEARCH_CONFLICT") from None
        return html_file, research
    if any(p.exists() or p.is_symlink() for p in targets):
        raise JvLocalCheckError("LOCAL_TRIFECTA_RESEARCH_CONFLICT")

    staged, linked = [], []
    try:
        for text in bodies:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", prefix=".arc-race-trifecta-",
                suffix=".tmp", dir=source.parent, delete=False,
            ) as output:
                path = Path(output.name)
                staged.append(path)
                output.write(text)
                output.flush()
                os.fsync(output.fileno())
        for stage, destination in zip(staged, targets):
            os.link(stage, destination)
            linked.append(destination)
    except OSError:
        for path in linked:
            path.unlink(missing_ok=True)
        raise JvLocalCheckError("LOCAL_TRIFECTA_SAVE_FAILED") from None
    finally:
        for path in staged:
            path.unlink(missing_ok=True)
    return html_file, research


def main(argv=None):
    parser = argparse.ArgumentParser(description="ARC RACE offline history-only trifecta study")
    parser.add_argument("--date", help="race day YYYYMMDD; default today JST")
    args = parser.parse_args(argv)
    today = args.date or datetime.now(JST).strftime("%Y%m%d")
    try:
        source = private_source(today)
        target, report = save_offline_trifecta_trial(source)
    except JvLocalCheckError as exc:
        print("ARC_RACE_LOCAL_TRIFECTA=" + str(exc))
        return 1
    print("ARC_RACE_LOCAL_TRIFECTA=" + report["status"].upper())
    print("POINTS=" + str(report["points"]))
    print("FORMAL_PREDICTION=NO")
    print("NETWORK_CALLS=0")
    if hasattr(os, "startfile"):
        try:
            os.startfile(str(target))
        except OSError:
            print("LOCAL_VIEW_OPEN=MANUAL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
