"""Owner-private historical SE7 observation preview (not a 10-factor grade).

Only consumes already licensed, locally supplied SE7 records. Reuses the
strict current-day RA2/SE2 horse-identity join; does no JV-Link or HTTP I/O.
Fields follow JV-Data specification 4.9.0.1 SE record (555 bytes).
Do not publish or send the returned per-horse observations to Render.
"""
from datetime import datetime, timezone, timedelta

from jrdb_coverage import CoverageError
from jvdata_ra_se_candidate import parse_jvdata_prestart_racecard, _ascii
from owner_jvdata_horse_history_coverage import (
    _past_result_identity, MAX_HISTORY_RECORDS, JST,
)

VERSION = "owner-jvdata-history-observation-preview-1"
MAX_VISIBLE_PRIOR_RUNS = 5


def _optional_number(raw, start, end, *, maximum):
    try:
        value = raw[start:end].decode("ascii")
    except UnicodeDecodeError:
        raise CoverageError("Invalid historical numeric field") from None
    if not value.strip() or value == "0" * (end - start):
        return None
    if not value.isdigit():
        raise CoverageError("Invalid historical numeric field")
    number = int(value)
    # 99 and 999 are often provider sentinels. Never treat them as a rank,
    # speed figure, or an advantage.
    return number if 0 < number <= maximum else None


def _time_tenths(raw):
    """JV-Data SE 4-character run time: mssT; 0000/9999 are unknown."""
    try:
        digits = raw[338:342].decode("ascii")
    except UnicodeDecodeError:
        raise CoverageError("Invalid historical race time") from None
    if digits in ("0000", "9999") or digits.isspace():
        return None
    if not digits.isdigit():
        raise CoverageError("Invalid historical race time")
    mins, secs, tenth = int(digits[0]), int(digits[1:3]), int(digits[3])
    if secs >= 60:
        return None
    result = (mins * 60 + secs) * 10 + tenth
    return result if result > 0 else None


def parse_historical_se7_observation(raw, target_day):
    """Interpret a bounded set of past *facts*, not horse ability.

    Caller must not treat receipt of this SE7 as independently time-verified.
    Race surface/distance is not present here: join the matching historical
    RA before any course/distance comparison. No odds/popularity are read.
    """
    _horse_id, race_key = _past_result_identity(raw, target_day)
    race_day, venue, _meeting, _meeting_day, race = race_key
    abnormal = raw[331:332]
    # Treat a nonzero abnormal code as a caution, not a failure to finish
    # or a bad performance score. Code meanings require separate lookup.
    if abnormal not in tuple(bytes([d]) for d in b"0123456789"):
        raise CoverageError("Invalid historical abnormal field")
    result = {
        "date": race_day,
        "trackCode": venue,
        "race": int(race),
        "finishPosition": _optional_number(raw, 334, 336, maximum=18),
        "runTimeTenths": _time_tenths(raw),
        "cornerPositions": [
            _optional_number(raw, a, a + 2, maximum=18)
            for a in (351, 353, 355, 357)
        ],
        "last3fTenths": _optional_number(raw, 390, 393, maximum=998),
        "historicalRunningStyleCode": _optional_number(
            raw, 552, 553, maximum=4
        ),
        "hasAbnormalCode": abnormal != b"0",
        "distanceMeters": None,  # Requires separately joined historical RA
        "surface": None,
        "going": None,
        "source": "private_historical_SE7_unverified_availability",
    }
    return result


def preview_jvdata_horse_history(current_ra, current_se, historical_se, day,
                                 *, captured_at):
    """Show the most recent five *observed* SE7 results for each horse number.

    The return object is strictly an owner-local diagnostic, never a formal
    feature input. Missing runs do not prove a debut; odds are not included.
    """
    card = parse_jvdata_prestart_racecard(current_ra, current_se, day)
    if (not isinstance(historical_se, (list, tuple))
            or len(historical_se) > MAX_HISTORY_RECORDS):
        raise CoverageError("Invalid historical result collection")
    if (not isinstance(captured_at, datetime)
            or captured_at.tzinfo is None
            or captured_at.utcoffset() is None):
        raise CoverageError("Invalid historical collection timestamp")
    before_off = captured_at.astimezone(JST) < datetime.strptime(
        day + card["postTimeCandidate"], "%Y%m%d%H:%M",
    ).replace(tzinfo=JST)

    current_id_to_number = {
        _ascii(row, 30, 40): int(_ascii(row, 28, 30))
        for row in current_se
    }
    records = {num: {} for num in current_id_to_number.values()}
    for raw in historical_se:
        horse_id, past_race_key = _past_result_identity(raw, day)
        number = current_id_to_number.get(horse_id)
        if number is None:
            continue
        old = records[number].get(past_race_key)
        if old is not None and old != raw:
            raise CoverageError("Conflicting historical performance revision")
        records[number][past_race_key] = raw

    by_number = []
    for number in sorted(records):
        observed = records[number]
        # Race identity, including meeting ID, uniquely keys the record.
        # Descending by original race date; tie-break by full race key.
        recent = sorted(observed.items(), key=lambda row: row[0], reverse=True)
        observations = [
            parse_historical_se7_observation(raw, day)
            for _key, raw in recent[:MAX_VISIBLE_PRIOR_RUNS]
        ] if before_off else []
        by_number.append({
            "number": number,
            "observedRecordCount": len(observed) if before_off else 0,
            "recentObservedRuns": observations,
            "missingHistoryUnproven": True,
            "graded": False,
        })
    return {
        "version": VERSION,
        "date": day, "track": card["track"], "race": card["race"],
        "status": "post_off_capture_hold" if not before_off else (
            "historical_observations_not_graded" if any(records.values())
            else "no_matched_history_observed"
        ),
        "byNumber": by_number,
        "maxRunsPerHorse": MAX_VISIBLE_PRIOR_RUNS,
        "historyComplete": False,
        "dataAvailabilityIndependentlyVerified": False,
        "officialStartersVerified": False,
        "outcomeStatisticsVerified": False,
        "formalTenFactorReady": False,
        "predictionReady": False,
        "bettingReady": False,
        "autoPurchase": False,
        "newProviderRequests": 0,
        "researchOnly": True,
        "ownerPrivateOnly": True,
        "note": (
            "過去SE7の着順・時計・コーナー位置・上がり3Fの候補。"
            "距離・馬場と提供時点未検証、正式採点・予想・馬券には未接続。"
        ),
    }
