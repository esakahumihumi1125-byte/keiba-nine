"""Single owner-triggered offline validation of existing private archives.

No JV-Link requests, writes, model persistence, or prediction issuance.
Only aggregate diagnostics are printed; historical roster is retrospective.
"""
import os
from pathlib import Path
from contextlib import ExitStack, closing
from datetime import datetime
import sys

from windows_jvlink_history_walkforward import evaluate as course_evaluate
from windows_jvlink_workout_pair_study import evaluate as workout_evaluate, _open
from windows_jvlink_2026_history_store import DATABASE
from windows_jvlink_weekly_read import JST


def validate_local(base, *, as_of_day):
    folder = base / "ARC-RACE-private" / "licensed-history"
    if not base.is_absolute() or folder.is_symlink() or folder.parent.is_symlink():
        raise ValueError("Invalid local archive path")
    with ExitStack() as stack:
        races = stack.enter_context(closing(_open(folder, DATABASE)))
        workouts = {
            spec: stack.enter_context(closing(_open(
                folder, "jvdata-2026-"+spec.lower()+".sqlite3")))
            for spec in ("SLOP", "WOOD")
        }
        return {
            "course": course_evaluate(races, as_of_day=as_of_day),
            "workout": workout_evaluate(races, workouts, as_of_day=as_of_day),
        }


def summary_lines(result):
    course, workout = result["course"], result["workout"]
    partial = course["partialCoverage"]
    yield "COURSE_STRICT_RACES="+str(course["evaluatedRaces"])
    yield "COURSE_PARTIAL_RACES="+str(partial["evaluatedRaces"])
    yield "COURSE_PARTIAL_COVERAGE="+str(partial["observedRunners"])+"/"+str(partial["fieldRunners"])
    for field in ("modelBrier", "uniformBrier", "observedModelBrier", "observedUniformBrier"):
        yield "COURSE_"+field.upper()+"="+str(partial[field])
    for spec, stats in sorted(workout["bySpec"].items()):
        for name, row in sorted(stats["metrics"].items()):
            yield spec+"_"+name+"_PAIRS="+str(row["comparablePairs"])
            yield spec+"_"+name+"_AGREEMENT="+str(row["directionalAgreementPercent"])
    for period in ("earlier", "holdout"):
        for label, key in (("COMPOSITE", "compositeStudy"), ("RUNNER", "runnerIndexStudy")):
            row = workout[key][period]
            prefix = label+"_"+period.upper()
            yield prefix+"_PAIRS="+str(row["comparablePairs"])+"/"+str(row["totalPairs"])
            yield prefix+"_AGREEMENT="+str(row["directionalAgreementPercent"])
            yield prefix+"_TIES="+str(row["tied"])
            if key == "runnerIndexStudy":
                yield prefix+"_COVERAGE="+str(row["indexedRunners"])+"/"+str(row["totalRunners"])
    yield "NEW_PROVIDER_REQUESTS=0"
    yield "FORMAL_TEN_FACTOR_READY=NO"


def main():
    if os.name != "nt":
        print("ARC_RACE_VALIDATION=WINDOWS_REQUIRED")
        return 1
    print("Active personal licence required. Read-only retrospective research.")
    if input("Type YES to analyze both studies (Enter = cancel): ").strip() != "YES":
        print("ARC_RACE_VALIDATION=CANCELLED")
        return 0
    try:
        result = validate_local(Path(os.environ.get("LOCALAPPDATA","")),
                                as_of_day=datetime.now(JST).strftime("%Y%m%d"))
        lines = list(summary_lines(result))
        print("ARC_RACE_VALIDATION=RETROSPECTIVE_ONLY")
        for line in lines:
            print(line)
        return 0
    except Exception:
        print("ARC_RACE_VALIDATION=FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
