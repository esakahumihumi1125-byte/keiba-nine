"""Owner-local retrospective workout validation, not formal training grades.

Compare horses in the same completed race only on shared workout dates,
training center, course and direction. Use the latest shared day/condition
per pair and median on that day. No tuning on outcomes, odds, data export,
source writes, purchase or model persistence.
"""
from collections import Counter
from contextlib import closing
from datetime import datetime
from itertools import combinations
from fractions import Fraction
import os
from pathlib import Path
import sqlite3
import sys

from owner_jvdata_workout_features import (
    observations_before, comparable_workout_values, compare_workout_summaries, SPEC_METRICS,
)
from windows_jvlink_history_walkforward import completed_races
from windows_jvlink_2026_history_store import DATABASE
from windows_jvlink_weekly_read import JST, JvLocalCheckError


# Fixed before examining any outcomes; no fitted weights.
HOLDOUT_START = "20260701"


def composite_direction(by_spec):
    """Equal weight across available surfaces, then metrics within surface.

    Require at least two distinct clock/acceleration metrics. A missing
    comparison contributes no vote; a measured tie contributes zero.
    The output is a research-only pair direction, not a probability or grade.
    """
    nonempty = [v for v in by_spec.values() if v]
    if len({m for v in nonempty for m in v}) < 2:
        return None
    mean = sum((Fraction(sum(v.values()), len(v)) for v in nonempty), Fraction())
    return (mean > 0) - (mean < 0)


def _agreement(counts):
    good, bad, tied = (counts[k] for k in ("concordant", "discordant", "tied"))
    return {"concordant":good,"discordant":bad,"tied":tied,
            "comparablePairs":good+bad+tied,
            "directionalAgreementPercent":round(100*good/(good+bad),2)
            if good+bad else None}


def evaluate(race_conn, workout_conns, *, as_of_day):
    if not workout_conns or not set(workout_conns) <= {"SLOP", "WOOD"}:
        raise JvLocalCheckError("WORKOUT_STUDY_SCOPE_INVALID")
    results = {spec: {"racesObserved": 0, "racesWithComparablePairs": 0,
                      "runnersObserved": 0, "totalRunners": 0,
                      "heldWorkoutKeys": 0,
                      "metrics": {metric: Counter() for metric in SPEC_METRICS[spec]}}
               for spec in workout_conns}
    skipped = Counter()
    composite = {period: Counter() for period in ("earlier", "holdout")}
    for key, race, reason in completed_races(race_conn, as_of_day=as_of_day):
        if reason:
            skipped[reason] += 1
            continue
        horses = race[-1]
        ids = {horse for horse, _ in horses}
        pairs = list(combinations(horses, 2))
        comparisons = { (a,b): {} for (a,_), (b,_) in pairs }
        for spec, conn in workout_conns.items():
            stat = results[spec]
            report = observations_before(conn, spec, key[:8], ids)
            rows = report["byPrivateHorseId"]
            stat["racesObserved"] += 1
            stat["totalRunners"] += len(horses)
            stat["runnersObserved"] += sum(bool(rows[h]) for h in ids)
            stat["heldWorkoutKeys"] += report["heldWorkoutKeys"]
            summaries = {h: comparable_workout_values(rows[h]) for h in ids}
            found = False
            for (a, finish_a), (b, finish_b) in pairs:
                votes = compare_workout_summaries(summaries[a], summaries[b], spec)
                comparisons[(a,b)][spec] = votes
                for metric, direction in votes.items():
                    stat["metrics"][metric][
                        "tied" if direction == 0 else "concordant"
                        if (direction > 0) == (finish_a < finish_b) else "discordant"
                    ] += 1
                    found = True
            stat["racesWithComparablePairs"] += int(found)
        period = "holdout" if key[:8] >= HOLDOUT_START else "earlier"
        for (a, finish_a), (b, finish_b) in pairs:
            direction = composite_direction(comparisons[(a,b)])
            counts = composite[period]
            counts["totalPairs"] += 1
            if direction is None:
                counts["insufficient"] += 1
                continue
            counts["tied" if direction == 0 else "concordant"
                   if (direction > 0) == (finish_a < finish_b) else "discordant"] += 1
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
            "compositeStudy": {period: {**_agreement(counts),
                "totalPairs": counts["totalPairs"], "insufficient": counts["insufficient"]}
                for period, counts in composite.items()},
            "holdoutStart": HOLDOUT_START, "weightsFitted": False,
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
                print(spec+"_"+metric+"_TIES="+str(values["tied"]))
                print(spec+"_"+metric+"_AGREEMENT_PERCENT="+str(values["directionalAgreementPercent"]))
        for period, values in report["compositeStudy"].items():
            print("COMPOSITE_"+period.upper()+"_PAIRS="+str(values["comparablePairs"])+"/"+str(values["totalPairs"]))
            print("COMPOSITE_"+period.upper()+"_AGREEMENT_PERCENT="+str(values["directionalAgreementPercent"]))
            print("COMPOSITE_"+period.upper()+"_TIES="+str(values["tied"]))
        print("FORMAL_TRAINING_GRADE_READY=NO")
        return 0
    except Exception:
        print("ARC_RACE_WORKOUT_STUDY=FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
