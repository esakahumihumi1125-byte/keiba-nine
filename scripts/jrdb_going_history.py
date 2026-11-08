"""Private, offline /dka past-going observations; never assign aptitude ranks.

Use only owner-held /tra,/tky,/tze,/dra,/dka and optional /tka rows.
No network, persistence, public feed, raw horse output, or live prediction.
"""
import re

from jrdb_coverage import CoverageError
from jrdb_course_history import (
    _historical_index, build_course_history_observations, DISTANCE_WINDOW_METRES,
)
from jrdb_evidence_readiness import _valid_date, HORSE_ID, NUMBER
from jrdb_recent_hypothesis import _place

VERSION = "going-history-observation-1"
HOLDING = re.compile(r"[0-9a-f]{6}\Z", re.ASCII)
GOING = {"1": "良", "2": "稍重", "3": "重", "4": "不良"}
COUNTERS = (
    "sameSurfaceKnownGoingRuns", "sameSurfaceUnknownGoingRuns",
    "knownGoingComparableRuns", "unknownGoingComparableRuns",
    "heavyComparableRuns", "poorComparableRuns",
    "heavyTopThreeRuns", "poorTopThreeRuns",
    "sameCurrentGoingComparableRuns", "sameCurrentGoingTopThreeRuns",
)


def _decode_going(value):
    if value is None or value == "":
        return None
    if type(value) is not str or value not in (*GOING, "01", "02", "03", "04"):
        raise CoverageError("Invalid going code")
    return GOING[value[-1]]


def _index_conditions(rows, allowed_pairs, target_date, *, is_past):
    """Reject conditions not associated with an already verified programme."""
    if not isinstance(rows, list) or len(rows) > 600:
        raise CoverageError("Invalid historical going collection")
    result = {}
    for row in rows:
        if not isinstance(row, dict):
            raise CoverageError("Invalid going row")
        holding, date = row.get("holdingkey"), row.get("racedate")
        if (not isinstance(holding, str) or not HOLDING.fullmatch(holding)
                or not _valid_date(date) or (holding, date) not in allowed_pairs
                or (date >= target_date if is_past else date != target_date)):
            raise CoverageError("Going holding/date does not match programme")
        pair = holding, date
        if pair in result:
            raise CoverageError("Duplicate venue condition")
        result[pair] = {
            "芝": _decode_going(row.get("turf_condition_cd")),
            "ダート": _decode_going(row.get("dirt_condition_cd")),
        }
    return result


def build_going_history_observations(programme, entries, previous, historical,
                                     historical_conditions, current_conditions,
                                     requested_date):
    """Count observed wet-track finishes without inferring suitability.

    Previous runs must first join a /dra racekey AND exact racedate.
    /dka conditions must then join its six-character holding key AND date.
    Counts only compare the same surface; comparable also means +/-200 m.
    Unknown past/current conditions remain unknown, never a negative result.
    """
    course = build_course_history_observations(
        programme, entries, previous, historical, requested_date
    )
    past = _historical_index(historical, requested_date)
    past_pairs = {(key[:6], row["racedate"]) for key, row in past.items()}
    today_pairs = {(row["racekey"][:6], requested_date) for row in programme}
    old_going = _index_conditions(
        historical_conditions, past_pairs, requested_date, is_past=True
    )
    now_going = _index_conditions(
        current_conditions, today_pairs, requested_date, is_past=False
    )
    roster = {(e["racekey"], e["horse_number"]) for e in entries}
    by_id = {(e["racekey"], e["horse_id"]): e["horse_number"]
             for e in entries if e.get("horse_id")}
    target = {r["racekey"]: r for r in programme}
    records = {}
    for race in course:
        key = race["racekey"]
        current = target[key]
        surf = current.get("surface")
        current_condition = now_going.get((key[:6], requested_date), {}).get(surf)
        records[key] = {
            "racekey": key, "track": race["track"], "race": race["race"],
            "currentGoingRecorded": current_condition is not None,
            "byNumber": {number: {**stats, **dict.fromkeys(COUNTERS, 0)}
                         for number, stats in race["byNumber"].items()},
            "goingSuitabilityAssessed": False, "predictionReady": False,
        }
    for row in previous:
        key, number, horse_id = (row["racekey"], row.get("horse_number"),
                                 row.get("horse_id"))
        by_number = number if (isinstance(number, str)
                               and NUMBER.fullmatch(number)
                               and (key, number) in roster) else None
        by_horse_id = by_id.get((key, horse_id)) if (
            isinstance(horse_id, str) and HORSE_ID.fullmatch(horse_id)) else None
        runner = by_horse_id or by_number
        if runner is None:
            continue  # Identity was already audited; no anonymous joining.
        stats = records[key]["byNumber"][runner]
        current = target[key]
        surf = current.get("surface")
        current_condition = now_going.get((key[:6], requested_date), {}).get(surf)
        for n in range(1, 6):
            prefix = f"race_back_{n}_"
            past_key = row.get(prefix + "racekey")
            old = past.get(past_key)
            if old is None:
                continue  # Missing /dra cannot be treated as a going mismatch.
            if surf not in ("芝", "ダート") or old.get("surface") != surf:
                continue
            condition = old_going.get((past_key[:6], old["racedate"]), {}).get(surf)
            if condition is None:
                stats["sameSurfaceUnknownGoingRuns"] += 1
            else:
                stats["sameSurfaceKnownGoingRuns"] += 1
            distance_ok = (type(current.get("distance_m")) is int
                           and type(old.get("distance_m")) is int
                           and abs(current["distance_m"] - old["distance_m"])
                           <= DISTANCE_WINDOW_METRES)
            if not distance_ok:
                continue
            if condition is None:
                stats["unknownGoingComparableRuns"] += 1
                continue
            stats["knownGoingComparableRuns"] += 1
            placing = _place(row.get(prefix + "order_of_finish"), "finish")
            if current_condition is not None and condition == current_condition:
                stats["sameCurrentGoingComparableRuns"] += 1
                if placing is not None and placing <= 3:
                    stats["sameCurrentGoingTopThreeRuns"] += 1
            if condition in ("重", "不良"):
                category = "heavy" if condition == "重" else "poor"
                stats[category + "ComparableRuns"] += 1
                if placing is not None and placing <= 3:
                    stats[category + "TopThreeRuns"] += 1
    return list(records.values())


def summarize_going_history_observations(races):
    """Race-level aggregates only: no horse IDs, numbers, results, race keys."""
    if not isinstance(races, list) or len(races) > 120:
        raise ValueError("Invalid going observations")
    output, seen = [], set()
    for race in races:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise ValueError("Invalid going race")
        name, number = race.get("track"), race.get("race")
        if (not isinstance(name, str) or type(number) is not int
                or (name, number) in seen
                or type(race.get("currentGoingRecorded")) is not bool):
            raise ValueError("Invalid or duplicate going race")
        seen.add((name, number))
        stats = list(race["byNumber"].values())
        for row in stats:
            if (not isinstance(row, dict) or
                    any(type(row.get(k)) is not int or row[k] < 0
                        for k in (*COUNTERS, "sameSurfaceRuns",
                                  "sameSurfaceNearDistanceRuns"))):
                raise ValueError("Malformed going observations")
            if (row["sameSurfaceKnownGoingRuns"]
                    + row["sameSurfaceUnknownGoingRuns"] != row["sameSurfaceRuns"]
                    or row["knownGoingComparableRuns"]
                    + row["unknownGoingComparableRuns"] != row["sameSurfaceNearDistanceRuns"]
                    or row["knownGoingComparableRuns"] > row["sameSurfaceKnownGoingRuns"]
                    or (row["heavyComparableRuns"] + row["poorComparableRuns"]
                        > row["knownGoingComparableRuns"])
                    or row["heavyTopThreeRuns"] > row["heavyComparableRuns"]
                    or row["poorTopThreeRuns"] > row["poorComparableRuns"]
                    or row["sameCurrentGoingComparableRuns"] > row["knownGoingComparableRuns"]
                    or row["sameCurrentGoingTopThreeRuns"] > row["sameCurrentGoingComparableRuns"]
                    or (not race["currentGoingRecorded"]
                        and (row["sameCurrentGoingComparableRuns"] != 0
                             or row["sameCurrentGoingTopThreeRuns"] != 0))):
                raise ValueError("Going count contradiction")
        output.append({
            "track": name, "race": number, "runnerCount": len(stats),
            "currentGoingRecorded": race["currentGoingRecorded"],
            "knownComparableRuns": sum(x["knownGoingComparableRuns"] for x in stats),
            "unknownComparableRuns": sum(x["unknownGoingComparableRuns"] for x in stats),
            "heavyComparableRuns": sum(x["heavyComparableRuns"] for x in stats),
            "poorComparableRuns": sum(x["poorComparableRuns"] for x in stats),
            "heavyTopThreeRuns": sum(x["heavyTopThreeRuns"] for x in stats),
            "poorTopThreeRuns": sum(x["poorTopThreeRuns"] for x in stats),
            "matchingCurrentGoingRuns": sum(x["sameCurrentGoingComparableRuns"]
                                            for x in stats),
            "matchingCurrentGoingTopThreeRuns": sum(
                x["sameCurrentGoingTopThreeRuns"] for x in stats
            ),
            "goingSuitabilityAssessed": False, "predictionReady": False,
        })
    return {
        "version": VERSION, "races": output, "predictionReady": False,
        "note": ("過去の開催馬場を日付・開催キーで照合し、同じ芝ダート・距離前後200m"
                 "で重・不良馬場を走った件数と3着以内の記録件数のみ集計。"
                 "未取得は不適性ではなく不明。馬場適性ランク・3連単予想は作成しない。"),
    }
