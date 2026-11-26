"""Private HC/WC workout observations from licensed local SQLite data.

JV-Data 4.9.0.1, sections 22 and 32. Times in integer tenths of a
second. This is retrospective feature preparation, not calibrated training
grades or evidence of exact pre-race delivery. No network, storage writes,
odds, purchases or export of licensed observations.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from windows_jvlink_workout_store import workout_record, SPECS
from windows_jvlink_weekly_read import JvLocalCheckError


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


def observations_before(conn, spec, target_day, horse_ids):
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
    start = (target-timedelta(days=14)).strftime("%Y%m%d")
    manifest = dict(conn.execute("SELECT key,value FROM manifest"))
    if (manifest.get("schema")!="arc-race-workout-1" or manifest.get("dataspec")!=spec
            or manifest.get("stream_completed")!="yes"):
        raise JvLocalCheckError("WORKOUT_ARCHIVE_INVALID")
    rows = conn.execute(
        "SELECT digest,workout_day,workout_key,created_day,category,raw FROM records "
        "WHERE workout_day>=? AND workout_day<? AND created_day<? "
        "ORDER BY workout_key,created_day DESC", (start,target_day,target_day))
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
