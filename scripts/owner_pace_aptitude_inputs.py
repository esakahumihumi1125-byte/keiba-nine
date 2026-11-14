"""Owner-private counts of documented /tky pace and aptitude source fields.

This is source AVAILABILITY, not a fitted course/pace/going score or a
favorable/unfavorable aptitude determination. Raw licensed codes and indices
never leave this function; it makes no network calls, writes or predictions.
"""
import math
from jrdb_coverage import audit_race_coverage, CoverageError

KEYS = ("runningStyle", "surfaceAptitude", "distanceAptitude",
        "goingAptitude", "paceIndices")
PACE_FIELDS = ("ten_index", "pace_index", "agari_index", "ichi_index")
FOOT_STYLES = frozenset(("1", "2", "3", "4"))


def _code_present(value):
    if value is None or value == "":
        return False
    return (type(value) is str and bool(value.strip()) and
            len(value) <= 16 and
            all(32 <= ord(ch) <= 126 for ch in value))


def _index_present(value):
    if value is None or value == "":
        return False
    if type(value) not in (str, int, float):
        return False
    if isinstance(value, str):
        if not value or len(value) > 20 or not value.isascii() or any(
                char not in "0123456789-+." for char in value):
            return False
    try:
        number = float(value)
    except (ValueError, OverflowError):
        return False
    return math.isfinite(number) and -1000000 <= number <= 1000000


def observe_pace_aptitude_input_counts(programme, entries, day):
    """Count existing runner rows using the exact validated programme roster.

    Prefer the matching course surface, not a turf code in a dirt race.
    A declared entry-count mismatch remains unverified and is rejected.
    Unknown codes or absent indices contribute NO availability count.
    """
    baseline = audit_race_coverage(programme, entries, day)
    by_key = {r["racekey"]: r for r in programme}
    result = {key: dict.fromkeys(KEYS, 0) for key in by_key}
    count = {key: 0 for key in by_key}
    for row in entries:
        key = row["racekey"]
        programme_row = by_key[key]
        surface = programme_row.get("surface")
        surface_field = ("turf_tekisei_cd" if surface == "芝" else
                         "dirt_tekisei_cd" if surface == "ダート" else None)
        checks = {
            "runningStyle": row.get("foottype_cd") in FOOT_STYLES
            if type(row.get("foottype_cd")) is str else False,
            "surfaceAptitude": (_code_present(row.get(surface_field))
                                  if surface_field else False),
            "distanceAptitude": _code_present(row.get("distance_aptitude_cd1")),
            "goingAptitude": _code_present(row.get("mudder_cd")),
            "paceIndices": all(_index_present(row.get(field)) for field in PACE_FIELDS),
        }
        for field, observed in checks.items():
            result[key][field] += int(observed)
        count[key] += 1
    if baseline["raceCount"] != len(by_key):
        raise CoverageError("Source input programme mismatch")
    output = []
    for key, row in by_key.items():
        if (type(row.get("headcount")) is not int
                or row["headcount"] != count[key]
                or not 0 <= count[key] <= 18):
            raise CoverageError("Unconfirmed source input runner count")
        output.append({
            "track": row["track"], "race": row["race"],
            "runnerCount": count[key], "counts": result[key],
        })
    output.sort(key=lambda r: (r["track"], r["race"]))
    return output
