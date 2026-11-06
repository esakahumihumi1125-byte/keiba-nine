"""Load a PRIVATE owner-only, editorial pre-day forecast from a Render env var.

This contains authored ranking/formation notes only, NOT licensed JRDB records,
provider indices, credentials, API responses or JRA confirmed declarations.
Never put the original file or compressed value into the public repository.
"""
import base64
import json
import re
import zlib
from datetime import date

SCHEMA = "keiba-nine-private-preday-review-v1"
TRACKS = frozenset(("札幌", "函館", "福島", "新潟", "東京",
                    "中山", "中京", "京都", "阪神", "小倉"))
ENV_KEY = "KEIBA_OWNER_FORECAST_ZLIB_B64"
MAX_COMPRESSED = 20000
MAX_DOCUMENT = 100000
KEYS = ("track", "race", "time", "course", "field", "rank",
        "first", "second", "third", "points", "confidence",
        "status", "headNames", "note", "provisional",
        "jraOfficialConfirmed", "fullFactorVerified")


class OwnerForecastError(ValueError):
    pass


def _safe_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", value):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def validate_owner_forecast(value):
    """Fail closed and keep only personal forecast presentation fields."""
    if not isinstance(value, dict) or value.get("schema") != SCHEMA or not _safe_date(value.get("date")):
        raise OwnerForecastError("Invalid private preview format")
    races = value.get("races")
    if not isinstance(races, list) or not 1 <= len(races) <= 36:
        raise OwnerForecastError("Invalid race count")
    entries = set()
    checked = []
    for r in races:
        if not isinstance(r, dict):
            raise OwnerForecastError("Invalid race")
        track, race, field = r.get("track"), r.get("race"), r.get("field")
        key = (track, race)
        if (track not in TRACKS or type(race) is not int or not 1 <= race <= 12
                or key in entries or type(field) is not int or not 3 <= field <= 18):
            raise OwnerForecastError("Race identity/size error")
        entries.add(key)
        if (not isinstance(r.get("time"), str)
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", r["time"])
                or not isinstance(r.get("course"), str)
                or not 2 <= len(r["course"]) <= 12
                or r.get("provisional") is not True
                or r.get("jraOfficialConfirmed") is not False
                or r.get("fullFactorVerified") is not False
                or r.get("status") not in ("買い候補", "見送り")
                or type(r.get("confidence")) is not int
                or not 1 <= r["confidence"] <= 5):
            raise OwnerForecastError("Provisional source status/fields invalid")
        ranking = r.get("rank")
        if (not isinstance(ranking, list) or len(ranking) != 7
                or any(type(n) is not int or n < 1 or n > field for n in ranking)
                or len(set(ranking)) != len(ranking)):
            raise OwnerForecastError("Invalid selection order")
        first, second, third = (r.get("first"), r.get("second"), r.get("third"))
        if (not all(isinstance(a, list) for a in (first, second, third))
                or not 1 <= len(first) <= 3
                or not len(first) <= len(second) <= len(third) <= 7
                or any(a != ranking[:len(a)] for a in (first, second, third))):
            raise OwnerForecastError("Invalid formation")
        combos = {(a, b, c) for a in first for b in second for c in third
                  if a != b and a != c and b != c}
        if (type(r.get("points")) is not int or r["points"] != len(combos)
                or not 1 <= len(combos) <= 48):
            raise OwnerForecastError("Invalid unique ticket count")
        names = r.get("headNames")
        note = r.get("note")
        if (not isinstance(names, list) or len(names) != 2
                or any(n is not None and
                       (not isinstance(n, str) or not 1 <= len(n) <= 35 or
                        any(c in n for c in "<>\n\r"))
                       for n in names)
                or not isinstance(note, str) or len(note) > 240
                or any(c in note for c in "<>\r")):
            raise OwnerForecastError("Invalid authored text")
        checked.append({k: r[k] for k in KEYS})
    checked.sort(key=lambda r: (("東京", "京都", "福島", "札幌", "函館",
                                 "新潟", "中山", "中京", "阪神", "小倉").index(r["track"]),
                                r["race"]))
    return {
        "schema": SCHEMA, "date": value["date"],
        "races": checked,
        "sourceKind": "owner-private-authored-preday",
        "predictionReady": False,
        "officialJraVerified": False,
        "purchased": False,
        "raceCount": len(checked),
    }


def decode_forecast(value):
    if not isinstance(value, str) or not 1 <= len(value) <= MAX_COMPRESSED or not re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", value):
        raise OwnerForecastError("No valid owner forecast configured")
    try:
        raw = base64.urlsafe_b64decode(value + ("=" * (-len(value) % 4)))
        # Limit decompression output to avoid zip-bomb inputs from a bad env value.
        decompress = zlib.decompressobj()
        text = decompress.decompress(raw, MAX_DOCUMENT + 1)
        if (len(text) > MAX_DOCUMENT or not decompress.eof or
                decompress.unconsumed_tail or decompress.unused_data):
            raise OwnerForecastError("Compressed owner forecast is invalid")
        return validate_owner_forecast(json.loads(text.decode("utf-8")))
    except (ValueError, UnicodeDecodeError, zlib.error) as exc:
        raise OwnerForecastError("Private forecast failed validation") from exc
