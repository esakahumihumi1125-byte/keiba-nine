"""Normalize JRDB /tra programme rows for owner-only display.

This module is intentionally NOT a public feed or prediction generator.
It never writes files or includes API keys. Any unverified field stays unknown.
"""
from datetime import datetime
import re


class ProgrammeFormatError(ValueError):
    """Response lacks reliable identifiers for a private preview."""


TRACKS = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
    "05": "東京", "06": "中山", "07": "中京", "08": "京都",
    "09": "阪神", "10": "小倉",
}
SURFACES = {"1": "芝", "2": "ダート", "3": "障害"}
# JRDB beta documentation is inconsistent: /docs/fields says 3=straight,
# while /docs/endpoints/today/tra says 9=straight. Until a live beta
# response resolves this, preserve BOTH documented codes without assigning a
# verified horse/course suitability grade.
TURNS = {"1": "右", "2": "左", "3": "直線", "9": "直線"}
RACE_KEY = re.compile(r"[0-9a-f]{8}\Z", re.ASCII)
POST_TIME = re.compile(r"[0-2][0-9][0-5][0-9]\Z", re.ASCII)
RACE_DATE = re.compile(r"[0-9]{8}\Z", re.ASCII)


def normalize_program_rows(rows, requested_date):
    """Return a bounded, date-matched /tra schedule for private inspection.

    /tra gives race programmes, NOT horse names, workouts, past runs, or
    independent predictions. Never infer those from a programme row.
    """
    if (not isinstance(requested_date, str) or not RACE_DATE.fullmatch(requested_date)):
        raise ProgrammeFormatError("Invalid requested date")
    try:
        datetime.strptime(requested_date, "%Y%m%d")
    except ValueError as exc:
        raise ProgrammeFormatError("Invalid calendar date") from exc
    if not isinstance(rows, list) or len(rows) > 120:
        raise ProgrammeFormatError("Unexpected programme collection")
    results, seen, race_slots = [], set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ProgrammeFormatError("Unexpected programme row")
        key = row.get("racekey")
        if not isinstance(key, str) or not RACE_KEY.fullmatch(key):
            raise ProgrammeFormatError("Invalid JRDB race key")
        course = TRACKS.get(key[:2])
        race_code = key[6:]
        if not course or not race_code.isdigit() or not 1 <= int(race_code) <= 12:
            raise ProgrammeFormatError("Unknown course or race")
        if row.get("racedate") != requested_date:
            raise ProgrammeFormatError("Programme date mismatch")
        # Some beta revisions expose a separate course code. If present,
        # it must agree with the authoritative race key; never silently
        # attach source materials to a different venue.
        raw_course = row.get("racecourse_cd")
        if raw_course is not None and raw_course != key[:2]:
            raise ProgrammeFormatError("Programme venue code mismatch")
        if key in seen:
            raise ProgrammeFormatError("Duplicate programme race key")
        # Different meeting IDs can still point at the SAME visible
        # track + race slot. Reject them now, before a one-day API test
        # falsely counts the slot twice or a picker displays two 1Rs.
        slot = (course, int(race_code))
        if slot in race_slots:
            raise ProgrammeFormatError("Ambiguous duplicate track and race")
        seen.add(key)
        race_slots.add(slot)
        raw_post = row.get("post_time")
        off = None
        if isinstance(raw_post, str) and POST_TIME.fullmatch(raw_post):
            h, m = int(raw_post[:2]), int(raw_post[2:])
            if h <= 23:
                off = f"{h:02d}:{m:02d}"
        raw_distance = row.get("distance")
        distance = None
        if isinstance(raw_distance, str) and raw_distance.isascii() and raw_distance.isdigit():
            value = int(raw_distance)
            if 100 <= value <= 10000:
                distance = value
        name = row.get("race_name")
        if not isinstance(name, str) or not name.strip():
            name = None
        else:
            name = name.strip()[:100]
        count = row.get("headcount")
        if type(count) is not int or not 0 <= count <= 18:
            count = None
        surface = SURFACES.get(row.get("track_type"))
        turn = TURNS.get(row.get("turn_cd"))
        results.append({
            "racekey": key,
            "racedate": requested_date,
            "track": course,
            "race": int(race_code),
            "race_name": name,
            "post_time": off,
            "surface": surface,
            "turn": turn,
            "distance_m": distance,
            "headcount": count,
            "programmeOnly": True,
            "horsesVerified": False,
            "predictionStatus": "未作成",
        })
    return sorted(results, key=lambda r: (r["post_time"] or "99:99", r["track"], r["race"]))
