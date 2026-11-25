"""Private retrospective research, not verified prestart replay or a wager.

Reads a completed local SQLite archive read-only. Only RA7/SE7 groups with
complete normal finishing orders. Prior observations must have a strictly
earlier race AND creation day. Current final roster/course are retrospective,
so metrics are not deployable forecast accuracy. No exported rows or model.
"""
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import groupby
import os
from pathlib import Path
import sqlite3
import sys

from jrdb_coverage import CoverageError
from owner_jvdata_horse_history_coverage import _past_result_identity
from owner_jvdata_horse_history_preview import (
    _historical_ra_context, parse_historical_se7_observation,
)
from windows_jvlink_2026_history_store import DATABASE, _record
from windows_jvlink_weekly_read import JST, JvLocalCheckError


def completed_races(conn, *, as_of_day):
    """Yield retrospective labels only, never expose paid rows to a caller UI."""
    manifest = dict(conn.execute("SELECT key,value FROM manifest"))
    if (manifest.get("schema") != "arc-race-local-history-1"
            or manifest.get("stream_completed") != "yes"):
        raise JvLocalCheckError("WALKFORWARD_ARCHIVE_INVALID")
    limit = (datetime.strptime(as_of_day, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d")
    cursor = conn.execute(
        "SELECT race_key,kind,category,created_day,raw,digest,race_day "
        "FROM records ORDER BY race_key")
    for key, group in groupby(cursor, key=lambda r:r[0]):
        rows = list(group)
        if len(rows) > 500:
            raise JvLocalCheckError("WALKFORWARD_TOO_MANY_REVISIONS")
        if not rows or key[:8] >= as_of_day:
            continue
        valid = True
        for stored_key, kind, category, created, raw, digest, day in rows:
            parsed = _record(raw)
            if (parsed is None or parsed[:6] != (digest, kind, category, day, stored_key, created)
                    or created > as_of_day):
                valid = False
                break
        if not valid:
            yield key, None, "archive_row_conflict"
            continue
        # Conservative: deletion or cancellation and any conflicting
        # final revisions remain excluded; do not guess source precedence.
        if any(r[2] in ("0","9") for r in rows):
            yield key, None, "cancel_or_delete"
            continue
        ras = [r for r in rows if r[1:3] == ("RA","7")]
        ses = [r for r in rows if r[1:3] == ("SE","7")]
        if (len(ras) != 1 or not 4 <= len(ses) <= 18
                or any(r[3] < key[:8] for r in ras+ses)):
            yield key, None, "missing_or_conflicting_final_rows"
            continue
        try:
            _, context = _historical_ra_context(ras[0][4], limit, as_of_day)
            n = context["historicalStarterCount"]
            if (context["surface"] not in ("芝","ダート")
                    or context["distanceMeters"] is None
                    or n != len(ses) or context["historicalFinishersCount"] != n):
                raise CoverageError("Incomplete normal field")
            horses, numbers, places = [], set(), set()
            for row in ses:
                raw = row[4]
                horse, _ = _past_result_identity(raw, limit)
                run = parse_historical_se7_observation(raw, limit)
                number = int(raw[28:30])
                finish = run["finishPosition"]
                if (not 1 <= number <= 18 or number in numbers or finish is None
                        or run["hasAbnormalCode"] or finish in places
                        or any(h[0] == horse for h in horses)):
                    raise CoverageError("Ambiguous result")
                numbers.add(number)
                places.add(finish)
                horses.append((horse, finish))
            if places != set(range(1,n+1)):
                raise CoverageError("Missing finishing positions")
        except (ValueError, TypeError, CoverageError):
            yield key, None, "incomplete_or_abnormal_field"
            continue
        yield key, (max(r[3] for r in ras+ses), key[8:10],
                    context["surface"], context["distanceMeters"], horses), None


def evaluate(conn, *, as_of_day):
    """Sequential top-three frequency baseline versus uniform field chance.

    A prior horse's exact venue, surface and distance bucket (200m) are
    matched. Smooth with three pseudo-observations of uniform field chance.
    Only races with evidence for all horses are scored. Earlier observations
    are admitted when their *creation day* is strictly before the target.
    """
    skipped, pending, history = Counter(), [], defaultdict(lambda:[0,0])
    count = runners = 0
    baseline_loss = model_loss = 0.0
    for key, record, reason in completed_races(conn, as_of_day=as_of_day):
        if reason:
            skipped[reason] += 1
            continue
        day = key[:8]
        # Keep the same-day boundary even when multiple venues are read.
        ready = [x for x in pending if x[0] < day]
        pending = [x for x in pending if x[0] >= day]
        for _, venue, surface, distance, horses in ready:
            for horse, finish in horses:
                stats = history[(horse,venue,surface,distance//200)]
                stats[0] += 1
                stats[1] += int(finish <= 3)
        available, venue, surface, distance, horses = record
        stats = [history.get((h,venue,surface,distance//200)) for h,_ in horses]
        if all(s is not None and s[0] > 0 for s in stats):
            p = 3/len(horses)
            count += 1
            runners += len(horses)
            for (_,finish), (n,hits) in zip(horses,stats):
                y = int(finish <= 3)
                predicted = (hits+3*p)/(n+3)
                model_loss += (predicted-y)**2
                baseline_loss += (p-y)**2
        else:
            skipped["prior_course_history_incomplete"] += 1
        pending.append(record)
    return {"evaluatedRaces":count,"evaluatedRunners":runners,
            "skippedRaces":dict(skipped),
            "modelBrier":round(model_loss/runners,6) if runners else None,
            "uniformBrier":round(baseline_loss/runners,6) if runners else None,
            "retrospectiveFinalRoster":True,"prestartAvailabilityVerified":False,
            "formalTenFactorReady":False,"modelSaved":False,
            "newProviderRequests":0}


def main():
    if os.name != "nt":
        print("ARC_RACE_WALKFORWARD=WINDOWS_REQUIRED")
        return 1
    print("Active licence required. Local retrospective course study, no data exported.")
    if input("Type YES to analyze (Enter = cancel): ").strip() != "YES":
        print("ARC_RACE_WALKFORWARD=CANCELLED")
        return 0
    try:
        base = Path(os.environ.get("LOCALAPPDATA",""))
        path = base/"ARC-RACE-private"/"licensed-history"/DATABASE
        if not base.is_absolute() or path.is_symlink() or not path.is_file():
            raise JvLocalCheckError("WALKFORWARD_ARCHIVE_NOT_FOUND")
        conn = sqlite3.connect(path.as_uri()+"?mode=ro",uri=True)
        try:
            conn.execute("PRAGMA query_only=ON")
            report = evaluate(conn, as_of_day=datetime.now(JST).strftime("%Y%m%d"))
        finally:
            conn.close()
        print("ARC_RACE_WALKFORWARD=RETROSPECTIVE_ONLY")
        print("EVALUATED_RACES="+str(report["evaluatedRaces"]))
        print("EVALUATED_RUNNERS="+str(report["evaluatedRunners"]))
        print("MODEL_BRIER="+str(report["modelBrier"]))
        print("UNIFORM_BRIER="+str(report["uniformBrier"]))
        print("FORMAL_TEN_FACTOR_READY=NO")
        return 0
    except Exception:
        print("ARC_RACE_WALKFORWARD=FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
