"""Owner-private historical SE7 observation preview (not a 10-factor grade).

Only consumes already licensed, locally supplied SE7 records. Reuses the
strict current-day RA2/SE2 horse-identity join; does no JV-Link or HTTP I/O.
Fields follow JV-Data specification 4.9.0.1 SE record (555 bytes).
Do not publish or send the returned per-horse observations to Render.
"""
from datetime import datetime, timezone, timedelta

from jrdb_coverage import CoverageError
from jvdata_ra_se_candidate import (
    RA_LENGTH, parse_jvdata_prestart_racecard, _ascii,
)
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from owner_jvdata_horse_history_coverage import (
    _past_result_identity, MAX_HISTORY_RECORDS, JST,
)

VERSION = "owner-jvdata-history-observation-preview-1"
MAX_VISIBLE_PRIOR_RUNS = 5
MAX_HISTORICAL_RA = 10000
# JV-Data 2009 track codes (flat only). Obstacle or unknown surfaces are
# deliberately left unclassified rather than guessed.
TURF_TRACK_CODES = frozenset(f"{n:02d}" for n in range(10, 23))
DIRT_TRACK_CODES = frozenset(f"{n:02d}" for n in (23, 24, 25, 26, 29))
SAND_TRACK_CODES = frozenset(("27", "28"))


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
        "historicalStarterCount": None,  # actual starters from matched RA7
        "historicalFinishersCount": None,
        "source": "private_historical_SE7_unverified_availability",
    }
    return result


def _historical_ra_context(raw, target_day, capture_day):
    """Parse race-distance/going context from one matching past RA7 record.

    Key is all of date, venue, meeting number, meeting day and race. If an
    RA7 is not supplied, SE7 alone must never invent race distance/going.
    """
    if (type(raw) is not bytes or len(raw) != RA_LENGTH
            or raw[:3] != b"RA7" or raw[-2:] != b"\r\n"):
        raise CoverageError("Unsupported historical race result record")
    created = _ascii(raw, 3, 11)
    year, month_day = _ascii(raw, 11, 15), _ascii(raw, 15, 19)
    venue, meeting, meeting_day, race = (
        _ascii(raw, 19, 21), _ascii(raw, 21, 23),
        _ascii(raw, 23, 25), _ascii(raw, 25, 27),
    )
    racedate = year + month_day
    if (not _valid_date(racedate) or not _valid_date(created)
            or racedate >= target_day or created > target_day
            or created > capture_day or venue not in TRACKS
            or not 1 <= int(meeting) <= 12
            or not 1 <= int(meeting_day) <= 12
            or not 1 <= int(race) <= 12):
        raise CoverageError("Historical RA identity or cutoff mismatch")

    distance = _optional_number(raw, 697, 701, maximum=10000)
    if distance is not None and distance < 400:
        distance = None
    try:
        code = raw[705:707].decode("ascii")
    except UnicodeDecodeError:
        raise CoverageError("Invalid historical track code") from None
    if code in TURF_TRACK_CODES:
        surface = "芝"
        going = _optional_number(raw, 888, 889, maximum=4)
    elif code in DIRT_TRACK_CODES:
        surface = "ダート"
        going = _optional_number(raw, 889, 890, maximum=4)
    elif code in SAND_TRACK_CODES:
        surface = "サンド"
        going = None
    else:
        # Obstacles may cross surfaces; avoid importing the wrong going.
        surface, going = None, None
    # JV-Data RA fields 46-48, positions 882/884/886 (1-based).
    # Actual starters exclude scratches; finishers exclude nonfinishers.
    registered = _optional_number(raw, 881, 883, maximum=18)
    starters = _optional_number(raw, 883, 885, maximum=18)
    finishers = _optional_number(raw, 885, 887, maximum=18)
    if (registered is not None and starters is not None and starters > registered):
        starters = finishers = None
    if starters is None or (finishers is not None and finishers > starters):
        finishers = None
    return (racedate, venue, meeting, meeting_day, race), {
        "distanceMeters": distance,
        "surface": surface,
        "goingCode": going,
        "going": {
            1: "良", 2: "稍重", 3: "重", 4: "不良",
        }.get(going),
        "historicalTrackCode": code if code != "00" else None,
        "historicalStarterCount": starters,
        "historicalFinishersCount": finishers,
        "historicalRaceContextMatched": True,
    }


def preview_jvdata_horse_history(current_ra, current_se, historical_se, day,
                                 *, captured_at, historical_ra=None):
    """Show the most recent five *observed* SE7 results for each horse number.

    The return object is strictly an owner-local diagnostic, never a formal
    feature input. Missing runs do not prove a debut; odds are not included.
    """
    card = parse_jvdata_prestart_racecard(current_ra, current_se, day)
    if (not isinstance(historical_se, (list, tuple))
            or len(historical_se) > MAX_HISTORY_RECORDS):
        raise CoverageError("Invalid historical result collection")
    if (historical_ra is not None
            and (not isinstance(historical_ra, (list, tuple))
                 or len(historical_ra) > MAX_HISTORICAL_RA)):
        raise CoverageError("Invalid historical race context collection")
    if (not isinstance(captured_at, datetime)
            or captured_at.tzinfo is None
            or captured_at.utcoffset() is None):
        raise CoverageError("Invalid historical collection timestamp")
    local_capture = captured_at.astimezone(JST)
    before_off = local_capture < datetime.strptime(
        day + card["postTimeCandidate"], "%Y%m%d%H:%M",
    ).replace(tzinfo=JST)
    capture_day = local_capture.strftime("%Y%m%d")

    course_by_race, raw_by_race = {}, {}
    for raw_ra in historical_ra or ():
        key, context = _historical_ra_context(raw_ra, day, capture_day)
        previous = raw_by_race.get(key)
        if previous is not None:
            if previous != raw_ra:
                raise CoverageError("Conflicting historical RA revisions")
            continue
        raw_by_race[key] = raw_ra
        course_by_race[key] = context

    current_id_to_number = {
        _ascii(row, 30, 40): int(_ascii(row, 28, 30))
        for row in current_se
    }
    records = {num: {} for num in current_id_to_number.values()}
    for raw in historical_se:
        horse_id, past_race_key = _past_result_identity(raw, day)
        # The SE creation date cannot be later than a historical local
        # snapshot. Date-only comparison is necessary but NOT proof that
        # the record had been published at its capture hour.
        if raw[3:11].decode("ascii") > capture_day:
            raise CoverageError("Historical record created after local capture")
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
        observations = []
        if before_off:
            for key, raw in recent[:MAX_VISIBLE_PRIOR_RUNS]:
                observation = parse_historical_se7_observation(raw, day)
                context = course_by_race.get(key)
                observation.update(context or {
                    "goingCode": None, "historicalTrackCode": None,
                    "historicalRaceContextMatched": False,
                })
                # Context must be consistent with the observed runner.
                # Leave the denominator unknown rather than count a rank
                # outside the reported field or finishers.
                starters = observation["historicalStarterCount"]
                finishers = observation["historicalFinishersCount"]
                finish = observation["finishPosition"]
                positions = [x for x in observation["cornerPositions"] if x is not None]
                if starters is not None and any(x > starters for x in positions + ([finish] if finish is not None else [])):
                    observation["historicalStarterCount"] = None
                    observation["historicalFinishersCount"] = None
                elif finishers is not None and finish is not None and finish > finishers:
                    observation["historicalFinishersCount"] = None
                observations.append(observation)
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
        "historicalRaContextJoined": (
            any(run["historicalRaceContextMatched"]
                for horse in by_number
                for run in horse["recentObservedRuns"])
            if before_off else False
        ),
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
            "同一レースの過去RA7があれば距離・芝ダート・当時馬場も内部候補へ付与。"
            "提供時点・網羅性未検証、正式採点・予想・馬券には未接続。"
        ),
    }
