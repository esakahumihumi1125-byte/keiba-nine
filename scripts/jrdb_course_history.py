"""Private course/distance *observation* join using /tze and historical /dra.

No JRDB network calls here. Provider-licensed rows stay in private memory.
Return no runner identities or live prediction to the authenticated browser.
One run at a comparable distance is NOT proof of course suitability.
"""
from collections import defaultdict

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import (
    audit_evidence_coverage, HORSE_ID, NUMBER, KEY, _valid_date
)
from jrdb_program_preview import normalize_program_rows, ProgrammeFormatError
from jrdb_recent_hypothesis import _place

VERSION = "course-history-evidence-1"
MAX_HISTORIC_PROGRAMMES = 600
DISTANCE_WINDOW_METRES = 200


def _historical_index(history, requested_date):
    if not isinstance(history, list) or len(history) > MAX_HISTORIC_PROGRAMMES:
        raise CoverageError("Past programme collection is invalid")
    by_key = {}
    for raw in history:
        if not isinstance(raw, dict):
            raise CoverageError("Invalid past programme")
        date, key = raw.get("racedate"), raw.get("racekey")
        if not _valid_date(date) or date >= requested_date:
            raise CoverageError("Past programme date invalid")
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in by_key:
            raise CoverageError("Duplicate or invalid past programme race key")
        try:
            normalized = normalize_program_rows([raw], date)[0]
        except ProgrammeFormatError:
            raise CoverageError("Invalid past programme data") from None
        by_key[key] = normalized
    return by_key


def build_course_history_observations(programme, entries, previous, historical, requested_date):
    """Per-runner internal observations, NOT horse aptitude grades.

    Reconcile /tze race_back_N_racekey/date with /dra racekey/racedate.
    Historical records may be absent: keep them missing; never infer a match.
    """
    audit_evidence_coverage(programme, entries, [], previous, requested_date)
    past_index = _historical_index(historical, requested_date)
    roster = defaultdict(dict)
    by_id = {}
    for row in entries:
        key, num, hid = row["racekey"], row["horse_number"], row.get("horse_id")
        roster[key][num] = row
        if hid:
            by_id[key, hid] = num
    current = {r["racekey"]: r for r in programme}
    observed = {}
    referenced = set()
    for row in previous:
        key, num, hid = row["racekey"], row.get("horse_number"), row.get("horse_id")
        via_number = num if isinstance(num, str) and NUMBER.fullmatch(num) and num in roster[key] else None
        via_id = by_id.get((key, hid)) if isinstance(hid, str) and HORSE_ID.fullmatch(hid) else None
        if via_number and via_id and via_number != via_id:
            raise CoverageError("Runner identity conflict")
        runner = via_id or via_number
        if runner is None:
            continue
        identity = key, runner
        if identity in observed:
            raise CoverageError("Duplicate previous-run record for one horse")
        old_seen = set()
        stats = {
            "datedRuns": 0, "linkedPastProgrammes": 0, "missingPastProgrammes": 0,
            "sameSurfaceRuns": 0, "nearDistanceRuns": 0, "sameTrackRuns": 0,
            "sameTurnRuns": 0, "sameSurfaceNearDistanceRuns": 0,
            "topThreeComparableRuns": 0,
        }
        target = current[key]
        for i in range(1, 6):
            prefix = f"race_back_{i}_"
            day = row.get(prefix + "racedate")
            past_key = row.get(prefix + "racekey")
            if day is None or day == "":
                if past_key is not None and past_key != "":
                    raise CoverageError("Past race key without date")
                continue
            stats["datedRuns"] += 1
            if past_key is None or past_key == "":
                stats["missingPastProgrammes"] += 1
                continue
            if not isinstance(past_key, str) or not KEY.fullmatch(past_key):
                raise CoverageError("Invalid past race key")
            if past_key in old_seen or past_key == key:
                raise CoverageError("Duplicate prior race for runner")
            old_seen.add(past_key)
            referenced.add(past_key)
            past = past_index.get(past_key)
            if past is None:
                stats["missingPastProgrammes"] += 1
                continue
            if past["racedate"] != day:
                raise CoverageError("Previous-run and past-programme date mismatch")
            stats["linkedPastProgrammes"] += 1
            if past["track"] == target["track"]:
                stats["sameTrackRuns"] += 1
            if (past.get("turn") is not None and target.get("turn") is not None
                    and past["turn"] == target["turn"]):
                stats["sameTurnRuns"] += 1
            both_distance = (type(past.get("distance_m")) is int
                             and type(target.get("distance_m")) is int)
            close = both_distance and abs(past["distance_m"] - target["distance_m"]) <= DISTANCE_WINDOW_METRES
            if close:
                stats["nearDistanceRuns"] += 1
            same_surface = (past.get("surface") in ("芝", "ダート")
                            and past.get("surface") == target.get("surface"))
            if same_surface:
                stats["sameSurfaceRuns"] += 1
            if same_surface and close:
                stats["sameSurfaceNearDistanceRuns"] += 1
                placing = _place(row.get(prefix + "order_of_finish"), "finish")
                if placing is not None and placing <= 3:
                    stats["topThreeComparableRuns"] += 1
        observed[identity] = stats
    if set(past_index) - referenced:
        raise CoverageError("Unexpected historical programme rows outside referenced history")
    all_races = []
    for race in programme:
        key = race["racekey"]
        horses = {}
        for num in sorted(roster[key]):
            horses[num] = observed.get((key, num), {
                "datedRuns": 0, "linkedPastProgrammes": 0, "missingPastProgrammes": 0,
                "sameSurfaceRuns": 0, "nearDistanceRuns": 0, "sameTrackRuns": 0,
                "sameTurnRuns": 0, "sameSurfaceNearDistanceRuns": 0,
                "topThreeComparableRuns": 0,
            })
        all_races.append({
            "racekey": key, "track": race["track"], "race": race["race"],
            "byNumber": horses, "courseSuitabilityAssessed": False,
            "goingSuitabilityAssessed": False, "predictionReady": False
        })
    return all_races


def summarize_course_history_observations(races):
    """Emit only race-level counts, no horse numbers, racekeys or history."""
    if not isinstance(races, list) or len(races) > 120:
        raise ValueError("Invalid course history evidence")
    result = []
    seen = set()
    for race in races:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise ValueError("Invalid course history race")
        key = (race.get("track"), race.get("race"))
        if key in seen:
            raise ValueError("Duplicate course history race")
        seen.add(key)
        stats = list(race["byNumber"].values())
        for row in stats:
            if (not isinstance(row, dict) or
                    any(type(row.get(k)) is not int or row[k] < 0 for k in (
                        "datedRuns", "linkedPastProgrammes", "missingPastProgrammes",
                        "sameSurfaceRuns", "nearDistanceRuns", "sameTrackRuns",
                        "sameTurnRuns", "sameSurfaceNearDistanceRuns",
                        "topThreeComparableRuns"))):
                raise ValueError("Malformed course evidence")
            if row["datedRuns"] != row["linkedPastProgrammes"] + row["missingPastProgrammes"]:
                raise ValueError("Historical data coverage is inconsistent")
            if (row["sameSurfaceNearDistanceRuns"] > min(row["sameSurfaceRuns"], row["nearDistanceRuns"])
                    or row["topThreeComparableRuns"] > row["sameSurfaceNearDistanceRuns"]):
                raise ValueError("Comparable history counts are inconsistent")
        result.append({
            "track": race["track"], "race": race["race"],
            "runnerCount": len(stats),
            "linkedPastRuns": sum(x["linkedPastProgrammes"] for x in stats),
            "unlinkedPastRuns": sum(x["missingPastProgrammes"] for x in stats),
            "runnersWithComparableRun": sum(x["sameSurfaceNearDistanceRuns"] > 0 for x in stats),
            "runnersWithTwoComparableRuns": sum(x["sameSurfaceNearDistanceRuns"] >= 2 for x in stats),
            "topThreeComparableObservations": sum(x["topThreeComparableRuns"] for x in stats),
            "courseSuitabilityAssessed": False,
            "goingSuitabilityAssessed": False, "predictionReady": False,
        })
    return {
        "version": VERSION, "races": result, "predictionReady": False,
        "note": ("過去の番組と近走のレースキー・日付を照合し、同じ芝ダート、"
                 "前後200m以内の距離で走った履歴の存在だけを確認。"
                 "適性の優劣、馬場適性、クラス水準、コース内外、勝率を推測せず、"
                 "総合評価・買い目は出しません。")
    }
