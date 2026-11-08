"""Private /tze last-five-run research hypotheses. No live bets or publication.

Official /tze field names: race_back_N_racedate/order_of_finish/idm/
later3f_time/corner4_order. No race margin or opponent-strength rating is
inferred. Uncalibrated thresholds are a KEIBA NINE *hypothesis*, not JRDB grades.

Input must be normalized private rows and can contain paid source records.
Only aggregate counts may cross the owner-only HTTP boundary.
"""
from collections import defaultdict
from datetime import datetime
import math

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import (
    audit_evidence_coverage, HORSE_ID, NUMBER, _valid_date
)

VERSION = "recent-hypothesis-1"
GRADES = ("S", "A", "B", "C", "未評価")
# Hypothetical weighted average of the most recent three finish-verified IDMs.
# No historical validation, win probability, relative odds or class normalization.
THRESHOLDS = ((70, "S"), (55, "A"), (40, "B"), (-100, "C"))


def _decimal(raw, *, minimum, maximum, label):
    if raw is None or raw == "":
        return None
    if type(raw) is bool:
        raise CoverageError("Invalid previous-run " + label)
    if type(raw) is str:
        # Provider may deliver numerical values as strings.
        if not raw or len(raw) > 15 or any(c not in "-.0123456789" for c in raw):
            raise CoverageError("Invalid previous-run " + label)
        try:
            value = float(raw)
        except ValueError:
            raise CoverageError("Invalid previous-run " + label) from None
    elif type(raw) in (int, float):
        value = float(raw)
    else:
        raise CoverageError("Invalid previous-run " + label)
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise CoverageError("Out-of-range previous-run " + label)
    return value


def _place(value, field):
    # Official beta /tze uses 0 for unavailable finish/corner data.
    # It is never a finishing position or a top-four observation.
    num = _decimal(value, minimum=0, maximum=30, label=field)
    if num is not None and not num.is_integer():
        raise CoverageError("Non-integer past position")
    return None if num is None or num == 0 else int(num)


def _last3f(value):
    # JRDB documents one-tenth-of-a-second integers: 360 means 36.0 s.
    # Accept fractional seconds in test/older normalized data, but never
    # interpret 360 as 360 seconds or count a 0 placeholder as a workout.
    number = _decimal(value, minimum=0, maximum=900, label="last3F")
    if number is None or number == 0:
        return None
    if number >= 200:
        if not number.is_integer():
            raise CoverageError("Unexpected fractional tenths of a second")
        number /= 10
    if not 20 <= number <= 90:
        raise CoverageError("Out-of-range previous-run last3F")
    return number


def _extract(row, target_date):
    runs = []
    seen_dates = set()
    last_date = target_date
    for i in range(1, 6):
        prefix = f"race_back_{i}_"
        day = row.get(prefix + "racedate")
        fields = (
            row.get(prefix + "order_of_finish"),
            row.get(prefix + "idm"),
            row.get(prefix + "later3f_time"),
            row.get(prefix + "corner4_order"),
        )
        placing = _place(fields[0], "finish")
        idm = _decimal(fields[1], minimum=-100, maximum=200, label="IDM")
        later = _last3f(fields[2])
        fourth = _place(fields[3], "corner4")
        # Unfilled beta columns can carry a race date with four zero-value
        # placeholders. These are NOT four additional completed starts.
        blank = (placing is None and later is None and fourth is None
                 and (idm is None or idm == 0))
        if day is None or day == "":
            if not blank:
                raise CoverageError("Past performance without a race date")
            continue
        if not _valid_date(day) or day >= target_date:
            raise CoverageError("Invalid or future previous-run date")
        if blank:
            continue
        if day >= last_date or day in seen_dates:
            raise CoverageError("Duplicate, future or disordered previous-run date")
        seen_dates.add(day)
        last_date = day
        runs.append({
            "date": day, "finish": placing, "idm": idm,
            "later3f": later, "corner4": fourth
        })
    return runs


def _provisional(historical):
    recent = [r for r in historical if r["finish"] is not None and r["idm"] is not None][:3]
    # Needs two completed runs. A debutant must remain ungraded.
    if len(recent) < 2:
        return "未評価"
    weights = (3, 2, 1)
    average = sum(r["idm"] * weights[i] for i, r in enumerate(recent)) / sum(weights[:len(recent)])
    return next(g for boundary, g in THRESHOLDS if average >= boundary)


def build_recent_hints(programme, entries, previous, requested_date):
    """Return INTERNAL horse-number research observations, never a wager."""
    audit_evidence_coverage(programme, entries, [], previous, requested_date)
    roster = defaultdict(dict)
    id_map = {}
    for row in entries:
        key, number, hid = row["racekey"], row["horse_number"], row.get("horse_id")
        roster[key][number] = True
        if hid:
            id_map[(key, hid)] = number
    seen = set()
    observations = {}
    for row in previous:
        key = row["racekey"]
        number, hid = row.get("horse_number"), row.get("horse_id")
        by_num = number if isinstance(number, str) and NUMBER.fullmatch(number) and number in roster[key] else None
        by_id = id_map.get((key, hid)) if isinstance(hid, str) and HORSE_ID.fullmatch(hid) else None
        if by_id and by_num and by_id != by_num:
            raise CoverageError("Previous-run identity disagreement")
        joined = by_id or by_num
        if joined is None:
            continue
        if (key, joined) in seen:
            raise CoverageError("Duplicate previous-run record for runner")
        seen.add((key, joined))
        history = _extract(row, requested_date)
        past_three = history[:3]
        observations[(key, joined)] = {
            "grade": _provisional(history),
            "assessmentStatus": ("assessed" if _provisional(history) != "未評価"
                else "no_usable_history" if not history
                else "only_one_usable_run" if len(history) == 1 and history[0]["finish"] is not None and history[0]["idm"] is not None
                else "insufficient_scored_runs"),
            "datedRuns": len(history),
            "completedRuns": sum(r["finish"] is not None for r in history),
            "topThree": sum(r["finish"] is not None and r["finish"] <= 3 for r in past_three),
            "frontAtFourth": sum(r["corner4"] is not None and r["corner4"] <= 4 for r in past_three),
            "fourthObserved": sum(r["corner4"] is not None for r in past_three),
            "late3fObserved": sum(r["later3f"] is not None for r in past_three),
        }
    result = []
    for race in programme:
        key = race["racekey"]
        stats = {}
        for n in sorted(roster[key]):
            stats[n] = observations.get((key, n), {
                "grade": "未評価", "assessmentStatus": "no_linked_recent_record", "datedRuns": 0, "completedRuns": 0,
                "topThree": 0, "frontAtFourth": 0, "fourthObserved": 0,
                "late3fObserved": 0
            })
        result.append({
            "racekey": key, "track": race["track"], "race": race["race"],
            "byNumber": stats, "researchOnly": True, "predictionReady": False
        })
    return result


def summarize_recent_hints(hints):
    """Only per-race aggregate information; no identifiers, history or IDM."""
    if not isinstance(hints, list) or len(hints) > 120:
        raise ValueError("Invalid recent hints")
    seen = set()
    result = []
    for race in hints:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise ValueError("Invalid internal recent-run race")
        identity = (race.get("track"), race.get("race"))
        if identity in seen:
            raise ValueError("Duplicate recent-run race")
        seen.add(identity)
        counts = {g: 0 for g in GRADES}
        front = observed = last3f = recent_records = 0
        for stats in race["byNumber"].values():
            grade = stats.get("grade")
            if grade not in counts:
                raise ValueError("Invalid grade")
            counts[grade] += 1
            front += stats["frontAtFourth"]
            observed += stats["fourthObserved"]
            last3f += stats["late3fObserved"]
            recent_records += stats["datedRuns"]
        result.append({
            "track": race["track"], "race": race["race"],
            "gradeCounts": counts,
            "graded": sum(counts[g] for g in GRADES[:4]),
            "ungraded": counts["未評価"],
            "historicalRunsObserved": recent_records,
            "frontAtFourthObservations": front,
            "fourthPositionObservations": observed,
            "late3fObservations": last3f,
            "researchOnly": True, "predictionReady": False
        })
    return {
        "version": VERSION, "races": result, "predictionReady": False,
        "note": ("直近3走の着順・IDMで暫定ランクを研究。2走以上なければ未評価。"
                 "S>=70、A>=55、B>=40、それ未満Cは未検証の独自閾値。"
                 "4角位置・上がり3Fは観測数のみ表示し、着差・相手関係・"
                 "先行力・上がり性能を確定評価しない。オッズ・人気を使用しない。"
                 "馬場・血統・展開の評価も未実施なので買い目は作成しない。")
    }
