"""Owner-local retrospective workout validation, not formal training grades.

Compare horses in the same completed race only on shared workout dates,
training center, course and direction. Use the latest shared day/condition
per pair and median on that day. No tuning on outcomes, odds, data export,
source writes, purchase or model persistence.
"""
from collections import Counter, defaultdict
from contextlib import closing
from datetime import datetime
from itertools import combinations
import os
from pathlib import Path
import sqlite3
from statistics import median
import sys

from owner_jvdata_workout_features import observations_before
from windows_jvlink_history_walkforward import completed_races
from windows_jvlink_2026_history_store import DATABASE
from windows_jvlink_weekly_read import JST, JvLocalCheckError


METRICS = ("lastFurlongTenths", "lastFurlongGainTenths")


def _comparable(observations):
    groups = defaultdict(list)
    for row in observations:
        key = (row["date"], row["center"], row["surface"],
               row["course"] or "", row["direction"] or "")
        for metric in METRICS:
            value = row[metric]
            if type(value) is int:
                groups[(key, metric)].append(value)
    return {key: median(values) for key, values in groups.items()}


def evaluate(race_conn, workout_conns, *, as_of_day):
    if not workout_conns or not set(workout_conns) <= {"SLOP", "WOOD"}:
        raise JvLocalCheckError("WORKOUT_STUDY_SCOPE_INVALID")
    results = {spec: {"racesObserved": 0, "racesWithComparablePairs": 0,
                      "runnersObserved": 0, "totalRunners": 0,
                      "heldWorkoutKeys": 0,
                      "metrics": {metric: Counter() for metric in METRICS}}
               for spec in workout_conns}
    skipped = Counter()
    for key, race, reason in completed_races(race_conn, as_of_day=as_of_day):
        if reason:
            skipped[reason] += 1
            continue
        horses = race[-1]
        ids = {horse for horse, _ in horses}
        for spec, conn in workout_conns.items():
            stat = results[spec]
            report = observations_before(conn, spec, key[:8], ids)
            rows = report["byPrivateHorseId"]
            stat["racesObserved"] += 1
            stat["totalRunners"] += len(horses)
            stat["runnersObserved"] += sum(bool(rows[h]) for h in ids)
            stat["heldWorkoutKeys"] += report["heldWorkoutKeys"]
            summaries = {h: _comparable(rows[h]) for h in ids}
            found = False
            for (a, finish_a), (b, finish_b) in combinations(horses, 2):
                shared = summaries[a].keys() & summaries[b].keys()
                for metric in METRICS:
                    candidates = [x for x in shared if x[1] == metric]
                    if not candidates:
                        continue
                    # Latest shared day, then stable lexical condition tie
                    # break, independent of clock values and race outcomes.
                    selected = max(candidates)
                    x, y = summaries[a][selected], summaries[b][selected]
                    if metric == "lastFurlongTenths":
                        x, y = -x, -y
                    stat["metrics"][metric][
                        "tied" if x == y else "concordant"
                        if (x > y) == (finish_a < finish_b) else "discordant"
                    ] += 1
                    found = True
            stat["racesWithComparablePairs"] += int(found)
    for stat in results.values():
        for metric, counts in stat["metrics"].items():
            good, bad, tied = (counts[k] for k in ("concordant", "discordant", "tied"))
            stat["metrics"][metric] = {
                "concordant":good,"discordant":bad,"tied":tied,
                "comparablePairs":good+bad+tied,
                "directionalAgreementPercent": round(100*good/(good+bad),2)
                if good+bad else None,
            }
    return {"bySpec":results,"skippedRaceReasons":dict(skipped),
            "retrospectiveFinalRoster":True,"prestartAvailabilityVerified":False,
            "formalTrainingGradeReady":False,"modelSaved":False,
            "newProviderRequests":0}


def _open(folder, name):
    path = folder / name
    if path.is_symlink() or not path.is_file():
        raise JvLocalCheckError("WORKOUT_STUDY_ARCHIVE_MISSING")
    conn = sqlite3.connect(path.as_uri()+"?mode=ro", uri=True)
    conn.execute("PRAGMA query_only=ON")
    return conn


def main():
    if os.name != "nt":
        print("ARC_RACE_WORKOUT_STUDY=WINDOWS_REQUIRED")
        return 1
    print("Active personal licence required. Local retrospective study; no source export.")
    if input("Type YES to analyze (Enter = cancel): ").strip() != "YES":
        print("ARC_RACE_WORKOUT_STUDY=CANCELLED")
        return 0
    try:
        from contextlib import ExitStack
        base = Path(os.environ.get("LOCALAPPDATA",""))
        folder = base/"ARC-RACE-private"/"licensed-history"
        if not base.is_absolute() or folder.is_symlink() or folder.parent.is_symlink():
            raise JvLocalCheckError("WORKOUT_STUDY_PATH_INVALID")
        with ExitStack() as stack:
            races = stack.enter_context(closing(_open(folder,DATABASE)))
            workouts = {}
            for spec in ("SLOP","WOOD"):
                name = "jvdata-2026-"+spec.lower()+".sqlite3"
                if (folder/name).exists():
                    workouts[spec] = stack.enter_context(closing(_open(folder,name)))
            report = evaluate(races,workouts,as_of_day=datetime.now(JST).strftime("%Y%m%d"))
        print("ARC_RACE_WORKOUT_STUDY=RETROSPECTIVE_ONLY")
        for spec, stat in report["bySpec"].items():
            print(spec+"_RACES="+str(stat["racesObserved"]))
            print(spec+"_COMPARABLE_RACES="+str(stat["racesWithComparablePairs"]))
            print(spec+"_RUNNERS_OBSERVED="+str(stat["runnersObserved"])+"/"+str(stat["totalRunners"]))
            for metric, values in stat["metrics"].items():
                print(spec+"_"+metric+"_PAIRS="+str(values["comparablePairs"]))
                print(spec+"_"+metric+"_AGREEMENT_PERCENT="+str(values["directionalAgreementPercent"]))
        print("FORMAL_TRAINING_GRADE_READY=NO")
        return 0
    except Exception:
        print("ARC_RACE_WORKOUT_STUDY=FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
