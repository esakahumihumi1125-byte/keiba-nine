"""Server-signed owner prestart decision captures for BOTH buy and hold races.

Captures are local-browser-only (no database or automatic scheduled capture).
Signing a forecast's *editorial* off time does not establish JRA official
schedule, source completeness, profitable predictions, or actual purchases.
Never sign a started race. No retroactive capture or raw paid provider rows.
"""
from datetime import datetime, date, timedelta, timezone
import hashlib
import hmac
import json
import re

from jrdb_coverage import CoverageError

VERSION = "owner-prestart-buy-hold-capture-v1"
SCHEMA = "keiba-nine-owner-decision-receipt-v1"
JST = timezone(timedelta(hours=9))
MAX_RACES = 36
TRACKS = frozenset(("札幌", "函館", "福島", "新潟", "東京",
                   "中山", "中京", "京都", "阪神", "小倉"))
FIELDS = frozenset(("date", "track", "race", "decision", "lockedAt",
                    "scheduledOffAt", "first", "second", "third",
                    "points", "sourceKind", "actualPurchase",
                    "officialScheduleVerified", "formalPredictionVerified"))


class DecisionReceiptError(ValueError):
    pass


def _day(value):
    if type(value) is not str or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", value):
        raise DecisionReceiptError("Invalid date")
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise DecisionReceiptError("Invalid date")
    except ValueError:
        raise DecisionReceiptError("Invalid date") from None
    return value


def _moment(value):
    if not isinstance(value, str):
        raise DecisionReceiptError("Invalid timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise DecisionReceiptError("Invalid timestamp") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DecisionReceiptError("Unzoned timestamp")
    return parsed


def _now(now):
    now = datetime.now(timezone.utc) if now is None else now
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise DecisionReceiptError("Invalid server clock")
    return now.astimezone(timezone.utc).replace(microsecond=0)


def _key(secret):
    if type(secret) is not str or len(secret) < 32:
        raise DecisionReceiptError("Signing key unavailable")
    return hmac.new(secret.encode(), b"ARC-RACE/owner-decision-capture/v1",
                    hashlib.sha256).digest()


def _sign(snapshot, secret):
    raw = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":"), allow_nan=False).encode()
    return hmac.new(_key(secret), raw, hashlib.sha256).hexdigest()


def _formation(first, second, third, points):
    parts = (first, second, third)
    if (not all(type(a) is list and 1 <= len(a) <= 18 for a in parts)
            or not 1 <= len(first) <= 3
            or not len(first) <= len(second) <= len(third)
            or any(type(n) is not int or not 1 <= n <= 18
                   for a in parts for n in a)
            or any(len(set(a)) != len(a) for a in parts)
            or not (set(first) <= set(second) <= set(third))
            or type(points) is not int or not 1 <= points <= 48):
        raise DecisionReceiptError("Invalid formation")
    combos = {(a, b, c) for a in first for b in second for c in third
              if len({a, b, c}) == 3}
    if len(combos) != points:
        raise DecisionReceiptError("Point count mismatch")
    return points


def issue_decision_captures(forecast, secret, day, *, now=None):
    day = _day(day)
    now = _now(now)
    if (type(forecast) is not dict or forecast.get("date") != day
            or forecast.get("sourceKind") != "owner-private-authored-preday"
            or forecast.get("predictionReady") is not False
            or forecast.get("officialJraVerified") is not False
            or forecast.get("purchased") is not False):
        raise DecisionReceiptError("Untrusted private reference")
    races = forecast.get("races")
    if type(races) is not list or not 1 <= len(races) <= MAX_RACES:
        raise DecisionReceiptError("Invalid race count")
    if not now.date() <= date.fromisoformat(day) <= now.date() + timedelta(days=7):
        # Normalize to Japanese civil day for before-race time comparison.
        if not (now.astimezone(JST).date()
                <= date.fromisoformat(day)
                <= now.astimezone(JST).date() + timedelta(days=7)):
            raise DecisionReceiptError("Day is not upcoming")
    seen, captures, started = set(), [], 0
    for race in races:
        if (not isinstance(race, dict) or race.get("track") not in TRACKS
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12):
            raise DecisionReceiptError("Invalid race identity")
        coord = race["track"], race["race"]
        if coord in seen:
            raise DecisionReceiptError("Duplicated race")
        seen.add(coord)
        hhmm = race.get("time")
        if (not isinstance(hhmm, str)
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", hhmm)):
            raise DecisionReceiptError("Invalid start time")
        off = datetime.fromisoformat(day + "T" + hhmm + ":00+09:00")
        if now >= off.astimezone(timezone.utc):
            started += 1
            continue
        status = race.get("status")
        if status not in ("買い候補", "見送り"):
            raise DecisionReceiptError("Invalid decision")
        first, second, third = race.get("first"), race.get("second"), race.get("third")
        points = race.get("points")
        _formation(first, second, third, points)
        snapshot = {
            "date": day, "track": race["track"], "race": race["race"],
            "decision": status,
            "lockedAt": now.isoformat(timespec="seconds"),
            "scheduledOffAt": off.isoformat(timespec="seconds"),
            "first": list(first), "second": list(second),
            "third": list(third), "points": points,
            "sourceKind": "owner-private-prestart-reference",
            "actualPurchase": False,
            "officialScheduleVerified": False,
            "formalPredictionVerified": False,
        }
        captures.append({"snapshot": snapshot,
                         "signature": _sign(snapshot, secret)})
    return {
        "schema": SCHEMA, "version": VERSION,
        "date": day, "captures": captures,
        "capturedRaces": len(captures), "skippedStartedRaces": started,
        "signedServerTime": now.isoformat(timespec="seconds"),
        "officialScheduleVerified": False, "resultsVerified": False,
        "actualPurchase": False,
    }


def verify_decision_captures(captures, secret, day):
    day = _day(day)
    if type(captures) is not list or not 1 <= len(captures) <= MAX_RACES:
        raise DecisionReceiptError("Invalid receipt count")
    result, seen = [], set()
    for item in captures:
        if (type(item) is not dict
                or set(item) != {"snapshot", "signature"}
                or type(item["snapshot"]) is not dict
                or set(item["snapshot"]) != FIELDS
                or type(item["signature"]) is not str
                or not re.fullmatch("[a-f0-9]{64}", item["signature"])):
            raise DecisionReceiptError("Invalid signed record")
        s = item["snapshot"]
        if not hmac.compare_digest(item["signature"], _sign(s, secret)):
            raise DecisionReceiptError("Signed record modified")
        track, number = s["track"], s["race"]
        if (s["date"] != day or track not in TRACKS
                or type(number) is not int or not 1 <= number <= 12
                or (track, number) in seen):
            raise DecisionReceiptError("Invalid or duplicate race")
        seen.add((track, number))
        if (s["decision"] not in ("買い候補", "見送り")
                or s["sourceKind"] != "owner-private-prestart-reference"
                or s["actualPurchase"] is not False
                or s["officialScheduleVerified"] is not False
                or s["formalPredictionVerified"] is not False):
            raise DecisionReceiptError("Unsafe signed claims")
        locked, off = _moment(s["lockedAt"]), _moment(s["scheduledOffAt"])
        if (locked >= off
                or off.astimezone(JST).date().isoformat() != day
                or (locked.astimezone(JST).date()
                    > date.fromisoformat(day))):
            raise DecisionReceiptError("Not a before-off capture")
        _formation(s["first"], s["second"], s["third"], s["points"])
        result.append({k: (list(v) if type(v) is list else v)
                       for k, v in s.items()})
    return {
        "schema": SCHEMA, "date": day, "verified": True,
        "captures": result, "captureCount": len(result),
        "officialScheduleVerified": False,
        "officialResultsVerified": False,
        "actualPurchase": False,
    }
