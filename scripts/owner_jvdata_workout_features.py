"""Private HC/WC workout observations from licensed local SQLite data.

JV-Data 4.9.0.1, sections 22 and 32. Times in integer tenths of a
second. This is retrospective feature preparation, not calibrated training
grades or evidence of exact pre-race delivery. No network, storage writes,
odds, purchases or export of licensed observations.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import combinations
from fractions import Fraction
from statistics import median

from windows_jvlink_workout_store import workout_record, SPECS
from windows_jvlink_weekly_read import JvLocalCheckError


METRICS = ("lastFurlongTenths", "lastFurlongGainTenths")
TOTAL_METRICS = {"fourFurlongTenths": 4, "sixFurlongTenths": 6}
SPEC_METRICS = {"SLOP": METRICS + ("fourFurlongTenths",),
                "WOOD": METRICS + ("fourFurlongTenths", "sixFurlongTenths")}
LOWER_IS_FASTER = {"lastFurlongTenths", *TOTAL_METRICS}


def comparable_workout_values(observations):
    """Identical-condition daily medians; do not compare missing intervals."""
    groups = defaultdict(list)
    for row in observations:
        key = (row["date"], row["center"], row["surface"],
               row["course"] or "", row["direction"] or "")
        for metric in SPEC_METRICS[row["surface"]]:
            if metric in TOTAL_METRICS:
                value = row.get("totalTenths", {}).get(TOTAL_METRICS[metric])
            else:
                value = row.get(metric)
            if type(value) is int:
                groups[(key, metric)].append(value)
    return {key: median(values) for key, values in groups.items()}


def compare_workout_summaries(a, b, spec):
    """Latest shared date/condition per metric, no clocks or dates returned.

    1 means a has the better observed clock/acceleration, -1 means b,
    0 means equal; absent metric means no comparable observations.
    """
    shared = a.keys() & b.keys()
    outcome = {}
    for metric in SPEC_METRICS[spec]:
        candidates = [k for k in shared if k[1] == metric and k[0][2] == spec]
        if not candidates:
            continue
        selected = max(candidates)
        x, y = a[selected], b[selected]
        if metric in LOWER_IS_FASTER:
            x, y = -x, -y
        outcome[metric] = (x > y) - (x < y)
    return outcome


def composite_direction(by_spec):
    """Fixed equal-surface comparison, requiring two distinct metrics."""
    nonempty = [v for v in by_spec.values() if v]
    if len({m for v in nonempty for m in v}) < 2:
        return None
    mean = sum((Fraction(sum(v.values()), len(v)) for v in nonempty), Fraction())
    return (mean > 0) - (mean < 0)


def runner_composite_index(numbers, comparisons):
    """Descriptive 0..100 index, not a probability or a formal grade.

    Require comparisons against at least half the other runners, and at
    least three opponents. Measured ties count half; missing pairs never
    count as losses. Preserve exact fractions for downstream validation.
    """
    numbers = list(numbers)
    stats = {n: [0, 0, 0] for n in numbers}  # better, worse, equal
    for a, b in combinations(numbers, 2):
        direction = composite_direction(comparisons.get((a, b), {}))
        if direction is not None:
            stats[a][0 if direction > 0 else 1 if direction < 0 else 2] += 1
            stats[b][1 if direction > 0 else 0 if direction < 0 else 2] += 1
    threshold = max(3, (len(numbers) - 1 + 1)//2)
    result = {}
    for number, (better, worse, equal) in stats.items():
        total = better + worse + equal
        result[number] = {
            "better": better, "worse": worse, "equal": equal,
            "comparedOpponents": total, "requiredOpponents": threshold,
            "index": Fraction(100*(2*better+equal), 2*total)
                     if total >= threshold else None,
        }
    return result


def _time(raw, start, length):
    field = raw[start:start+length]
    if not field.isdigit():
        raise JvLocalCheckError("WORKOUT_TIME_INVALID")
    if field in (b"0"*length, b"9"*length):
        return None
    return int(field)


def parse_observation(raw, spec):
    if spec not in SPECS or type(raw) is not bytes:
        raise JvLocalCheckError("WORKOUT_SOURCE_INVALID")
    identity = workout_record(raw, spec)
    if identity is None:
        raise JvLocalCheckError("WORKOUT_SOURCE_INVALID")
    if raw[2:3] == b"0":
        return None
    # 1-based HC totals start at 35, WC at 38. Each total/lap block
    # is seven bytes, followed by the standalone final 1F lap.
    base, maximum = (34, 4) if spec == "SLOP" else (37, 10)
    totals, laps = {}, {}
    for i, furlongs in enumerate(range(maximum, 1, -1)):
        start = base + 7*i
        totals[furlongs] = _time(raw, start, 4)
        laps[furlongs] = _time(raw, start+4, 3)
    laps[1] = _time(raw, base+7*(maximum-1), 3)
    totals[1] = laps[1]
    # Check only fully measured intervals. Missing long WC intervals
    # are common; never fill them by extrapolation.
    for n in range(2, maximum+1):
        if all(x is not None for x in (totals[n], totals[n-1], laps[n])):
            if abs(totals[n]-totals[n-1]-laps[n]) > 1:
                raise JvLocalCheckError("WORKOUT_LAP_TOTAL_CONFLICT")
    if spec == "WOOD" and (raw[34:35] not in tuple(bytes([d]) for d in b"01234")
                           or raw[35:36] not in (b"0",b"1")):
        raise JvLocalCheckError("WORKOUT_COURSE_INVALID")
    return {
        "date": identity[1],
        "center": raw[11:12].decode(),
        "surface": spec,
        "course": raw[34:35].decode() if spec == "WOOD" else None,
        "direction": raw[35:36].decode() if spec == "WOOD" else None,
        "totalTenths": totals,
        "lapTenths": laps,
        "lastFurlongTenths": laps[1],
        # Positive = faster last interval, not proof of fitness.
        "lastFurlongGainTenths": (
            laps[2]-laps[1] if laps[2] is not None and laps[1] is not None else None),
    }


def observations_before(conn, spec, target_day, horse_ids, *, capture_day=None):
    """14 preceding calendar days, with a strict prior creation-day cutoff.

    Internal use only. The registration IDs must come from a matching
    private race roster. No data or IDs should be published. Multiple
    same-day revisions are held rather than resolving unknown order.
    """
    if spec not in SPECS or not isinstance(horse_ids, set) or not 1 <= len(horse_ids) <= 18:
        raise JvLocalCheckError("WORKOUT_TARGET_INVALID")
    if any(type(x) is not str or len(x)!=10 or not x.isascii() or not x.isdigit()
           or x=="0000000000" for x in horse_ids):
        raise JvLocalCheckError("WORKOUT_TARGET_INVALID")
    try:
        target = datetime.strptime(target_day,"%Y%m%d")
        if target.strftime("%Y%m%d") != target_day:
            raise ValueError()
    except (ValueError,TypeError):
        raise JvLocalCheckError("WORKOUT_TARGET_INVALID") from None
    if capture_day is not None:
        try:
            captured = datetime.strptime(capture_day, "%Y%m%d")
            if captured.strftime("%Y%m%d") != capture_day or captured > target:
                raise ValueError()
        except (ValueError, TypeError):
            raise JvLocalCheckError("WORKOUT_CAPTURE_DAY_INVALID") from None
    cutoff = capture_day if capture_day is not None else target_day
    start = (target-timedelta(days=14)).strftime("%Y%m%d")
    manifest = dict(conn.execute("SELECT key,value FROM manifest"))
    if (manifest.get("schema")!="arc-race-workout-1" or manifest.get("dataspec")!=spec
            or manifest.get("stream_completed")!="yes"):
        raise JvLocalCheckError("WORKOUT_ARCHIVE_INVALID")
    rows = conn.execute(
        "SELECT digest,workout_day,workout_key,created_day,category,raw FROM records "
        "WHERE workout_day>=? AND workout_day<? AND created_day<? "
        "ORDER BY workout_key,created_day DESC", (start,cutoff,cutoff))
    groups = defaultdict(list)
    for row in rows:
        if row[2][-10:] not in horse_ids:
            continue
        if workout_record(row[-1],spec) != tuple(row):
            raise JvLocalCheckError("WORKOUT_ARCHIVE_ROW_CONFLICT")
        if row[3] < row[1]:
            raise JvLocalCheckError("WORKOUT_CREATION_DATE_INVALID")
        groups[row[2]].append(row)
        if len(groups)>10000 or len(groups[row[2]])>100:
            raise JvLocalCheckError("WORKOUT_REVISIONS_LIMIT")
    output = {horse:[] for horse in horse_ids}
    held = 0
    for key, records in groups.items():
        newest = [row for row in records if row[3]==records[0][3]]
        if len(newest)!=1:
            held += 1
            continue
        try:
            observation = parse_observation(newest[0][-1],spec)
        except JvLocalCheckError:
            held += 1
            continue
        if observation is not None:
            output[key[-10:]].append(observation)
    return {"byPrivateHorseId":output,"heldWorkoutKeys":held,
            "prestartAvailabilityVerified":False,"coverageVerified":False,
            "formalTrainingGradeReady":False,"newProviderRequests":0}


def race_workout_coverage(connections, number_to_id, *, target_day, capture_day):
    """Owner-local prestart evidence coverage; no clocks, IDs or grades leave this adapter.

    Exclude capture-day creations conservatively even for tomorrow's card.
    A zero count means no accepted records observed, not poor fitness.
    """
    if (not isinstance(connections, dict) or not connections
            or not set(connections) <= set(SPECS)
            or not isinstance(number_to_id, dict) or not 4 <= len(number_to_id) <= 18
            or any(type(n) is not int or not 1 <= n <= 18 for n in number_to_id)
            or any(type(h) is not str for h in number_to_id.values())
            or len(set(number_to_id.values())) != len(number_to_id)):
        raise JvLocalCheckError("WORKOUT_RACE_ROSTER_INVALID")
    horses = {number: {} for number in sorted(number_to_id)}
    held = {}
    pairs = list(combinations(sorted(number_to_id), 2))
    comparisons = {pair: {} for pair in pairs}
    for spec, conn in sorted(connections.items()):
        report = observations_before(conn, spec, target_day,
                                     set(number_to_id.values()), capture_day=capture_day)
        held[spec] = report["heldWorkoutKeys"]
        summaries = {n: comparable_workout_values(report["byPrivateHorseId"][h])
                     for n, h in number_to_id.items()}
        pair_counts = {n: {m: {"better": 0, "worse": 0, "equal": 0}
                          for m in SPEC_METRICS[spec]} for n in number_to_id}
        for a, b in pairs:
            votes = compare_workout_summaries(summaries[a], summaries[b], spec)
            comparisons[(a,b)][spec] = votes
            for metric, direction in votes.items():
                pair_counts[a][metric]["better" if direction > 0 else "worse" if direction < 0 else "equal"] += 1
                pair_counts[b][metric]["worse" if direction > 0 else "better" if direction < 0 else "equal"] += 1
        for number, horse_id in number_to_id.items():
            rows = report["byPrivateHorseId"][horse_id]
            horses[number][spec] = {
                "observedWorkouts": len(rows),
                "sameConditionComparisons": pair_counts[number],
                "last1FCount": sum(type(r["lastFurlongTenths"]) is int for r in rows),
                "accelerationCount": sum(type(r["lastFurlongGainTenths"]) is int for r in rows),
                "fourFCount": sum(type(r["totalTenths"].get(4)) is int for r in rows),
                "sixFCount": (sum(type(r["totalTenths"].get(6)) is int for r in rows)
                              if spec == "WOOD" else None),
            }
    index = runner_composite_index(sorted(number_to_id), comparisons)
    for row in index.values():
        if row["index"] is not None:
            row["index"] = round(float(row["index"]), 2)
    return {"byNumber": [{"number": n, "bySpec": v,
                          "compositeResearch": index[n]} for n, v in horses.items()],
            "heldWorkoutKeysBySpec": held, "formalTrainingGradeReady": False,
            "coverageVerified": False, "prestartAvailabilityVerified": False,
            "researchOnly": True, "newProviderRequests": 0}
