"""Owner-only /tra + /tka pre-race course and going context.

This is a bounded presence/consistency check, not a horse suitability
assessment. Do not return provider rows, horse names or any prediction.
"""
import re
from datetime import datetime

from jrdb_program_preview import TRACKS

VERSION = "race-context-1"
HOLDING = re.compile(r"[0-9]{6}\Z", re.ASCII)
DATE = re.compile(r"[0-9]{8}\Z", re.ASCII)
GOING = {"1": "良", "2": "稍重", "3": "重", "4": "不良"}
SURFACES = {"芝", "ダート", "障害"}


class RaceContextError(ValueError):
    """Private input data is inconsistent or unsupported."""


def _going(value):
    if value is None or value == "":
        return "未確認"
    if isinstance(value, str) and value in GOING:
        return GOING[value]
    if isinstance(value, str) and value in ("01", "02", "03", "04"):
        return GOING[value[1:]]
    raise RaceContextError("Invalid going code")


def audit_race_context(programme, holding_rows, requested_date):
    """Map confirmed venue conditions to normalized races without predicting."""
    if not isinstance(requested_date, str) or not DATE.fullmatch(requested_date):
        raise RaceContextError("Invalid target date")
    try:
        datetime.strptime(requested_date, "%Y%m%d")
    except ValueError:
        raise RaceContextError("Invalid calendar date") from None
    if not isinstance(programme, list) or len(programme) > 120:
        raise RaceContextError("Invalid programme")
    if not isinstance(holding_rows, list) or len(holding_rows) > 120:
        raise RaceContextError("Invalid venue collection")
    venues = {}
    for row in holding_rows:
        if not isinstance(row, dict):
            raise RaceContextError("Invalid venue row")
        key = row.get("holdingkey")
        if not isinstance(key, str) or not HOLDING.fullmatch(key):
            raise RaceContextError("Invalid holding key")
        track = TRACKS.get(key[:2])
        if not track or row.get("racedate") != requested_date:
            raise RaceContextError("Venue/date mismatch")
        if track in venues:
            # Two conditions for the same track cannot silently replace one another.
            raise RaceContextError("Duplicate venue condition")
        turf = _going(row.get("turf_condition_cd"))
        dirt = _going(row.get("dirt_condition_cd"))
        updated = row.get("updated_at")
        if updated is not None and updated != "":
            if not isinstance(updated, str) or len(updated) > 40:
                raise RaceContextError("Invalid condition timestamp")
            try:
                ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    raise ValueError()
            except ValueError:
                raise RaceContextError("Invalid condition timestamp") from None
        venues[track] = {"turf": turf, "dirt": dirt,
                         "updateRecorded": bool(updated)}
    observed = set()
    result = []
    for race in programme:
        if not isinstance(race, dict) or race.get("racedate") != requested_date:
            raise RaceContextError("Invalid programme race")
        track, number = race.get("track"), race.get("race")
        if track not in TRACKS.values() or type(number) is not int or not 1 <= number <= 12:
            raise RaceContextError("Invalid track or race")
        if (track, number) in observed:
            raise RaceContextError("Duplicate race")
        observed.add((track, number))
        surface = race.get("surface")
        if surface is not None and surface not in SURFACES:
            raise RaceContextError("Invalid surface")
        distance = race.get("distance_m")
        if distance is not None and (type(distance) is not int or not 100 <= distance <= 10000):
            raise RaceContextError("Invalid distance")
        turn = race.get("turn")
        if turn is not None and turn not in ("右", "左", "直線"):
            raise RaceContextError("Invalid turn direction")
        venue = venues.get(track)
        going = ("未確認" if venue is None or surface not in ("芝", "ダート")
                 else venue["turf"] if surface == "芝" else venue["dirt"])
        context_present = surface is not None and distance is not None and turn is not None
        result.append({
            "track": track, "race": number, "surface": surface,
            "distance_m": distance, "turn": turn,
            "going": going, "goingAvailable": going != "未確認",
            "conditionSnapshotPresent": venue is not None,
            "conditionUpdateRecorded": bool(venue and venue["updateRecorded"]),
            "courseInfoPresent": context_present,
            "horseCourseSuitabilityAssessed": False,
            "horseGoingSuitabilityAssessed": False,
            "predictionReady": False,
        })
    return {
        "version": VERSION, "raceCount": len(result),
        "courseInfoPresentCount": sum(x["courseInfoPresent"] for x in result),
        "goingAvailableCount": sum(x["goingAvailable"] for x in result),
        "raceConditionsVerified": False, "predictionReady": False,
        "races": result,
        "note": ("番組の芝/ダート・距離・回り方向と開催馬場データの存在を確認。"
                 "馬場の最新性、取消、競走馬の距離/コース/不良馬場適性は未検証。"
                 "馬ごとの比較・適性ランク・買い目は一切作成していません。")
    }
