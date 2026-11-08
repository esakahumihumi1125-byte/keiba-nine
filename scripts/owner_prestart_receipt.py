"""Private owner-only server-attested, tamper-evident prestart ticket receipts.

Receipts prove the private service signed these exact forecast picks at a
particular server timestamp. They DO NOT independently verify JRA off-times,
official runners, purchases, payouts, or full audit completeness.
Stateless: browser retains receipts; no signing key or licensed records are sent.
"""
import hashlib
import hmac
import json
import re
from datetime import date, datetime, timezone, timedelta

from keiba_100yen_review import ReviewInputError, _identity, _time, _tickets

SCHEMA = "keiba-nine-owner-server-receipt-v1"
JST = timezone(timedelta(hours=9))
MAX_RECEIPTS = 36
RECORD_FIELDS = frozenset((
    "date", "track", "race", "sourceKind", "actualPurchase",
    "lockedAt", "scheduledOffAt", "trifectaTickets", "trioTickets",
    "scheduleVerified", "predictionVerified",
))


class ReceiptError(ValueError):
    pass


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _key(password):
    if not isinstance(password, str) or len(password) < 32:
        raise ReceiptError("Owner credential unavailable")
    return hmac.new(password.encode("utf-8"),
                    b"keiba-nine/prestart-review-receipt/v1",
                    hashlib.sha256).digest()


def _sign(snapshot, password):
    return hmac.new(_key(password), _canonical(snapshot),
                    hashlib.sha256).hexdigest()


def _selected_day(day):
    if not isinstance(day, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", day):
        raise ReceiptError("Invalid racing date")
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ReceiptError("Invalid racing date")
    except ValueError:
        raise ReceiptError("Invalid racing date") from None
    return day


def _server_time(now):
    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ReceiptError("Server timestamp unavailable")
    return now.astimezone(timezone.utc).replace(microsecond=0)


def issue_preview_receipts(forecast, password, day, now=None):
    """Sign eligible full formations from the validated owner editorial forecast.

    This is an authenticated user-triggered preview, NOT a trusted JRA pre-race
    capture. The forecast's scheduled time remains independently unverified.
    """
    day = _selected_day(day)
    now = _server_time(now)
    if not isinstance(forecast, dict) or forecast.get("date") != day:
        raise ReceiptError("Selected day differs from server forecast")
    if forecast.get("sourceKind") != "owner-private-authored-preday":
        raise ReceiptError("Invalid editorial forecast origin")
    if (forecast.get("predictionReady") is not False
            or forecast.get("officialJraVerified") is not False
            or forecast.get("purchased") is not False):
        raise ReceiptError("Unsupported production status")
    races = forecast.get("races")
    if not isinstance(races, list) or len(races) > MAX_RECEIPTS:
        raise ReceiptError("Invalid race count")
    receipts = []
    seen = set()
    past = 0
    skipped = 0
    for race in races:
        if not isinstance(race, dict):
            raise ReceiptError("Invalid race")
        try:
            track = race["track"]
            number = race["race"]
            key = _identity({"date": day, "track": track, "race": number})
            if key in seen:
                raise ReceiptError("Duplicate race")
            seen.add(key)
            time = race["time"]
            if not isinstance(time, str) or not re.fullmatch(
                    r"(?:[01]\d|2[0-3]):[0-5]\d", time):
                raise ReceiptError("Invalid editorial off time")
            off = datetime.fromisoformat(day + "T" + time + ":00+09:00")
            # No after-off signing, even using the unverified editorial schedule.
            if now >= off.astimezone(timezone.utc):
                past += 1
                continue
            if race["status"] != "買い候補":
                skipped += 1
                continue
            first, second, third = (
                race["first"], race["second"], race["third"])
            if (not all(isinstance(a, list) for a in (first, second, third))
                    or not all(1 <= len(a) <= 18 for a in (first, second, third))):
                raise ReceiptError("Missing formation")
            tickets = sorted({(a, b, c) for a in first for b in second for c in third
                              if a != b and a != c and b != c})
            valid_tickets = _tickets([list(x) for x in tickets], "trifecta")
            if (not valid_tickets or len(valid_tickets) > 48
                    or len(valid_tickets) != race["points"]):
                raise ReceiptError("Formation does not match forecast")
        except (KeyError, TypeError, ReviewInputError) as exc:
            raise ReceiptError("Invalid forecast race") from exc
        snapshot = {
            "date": day, "track": track, "race": number,
            "sourceKind": "prestart-locked", "actualPurchase": False,
            "lockedAt": now.isoformat(timespec="seconds"),
            "scheduledOffAt": off.isoformat(timespec="seconds"),
            "trifectaTickets": [list(x) for x in valid_tickets],
            "trioTickets": [],
            "scheduleVerified": False, "predictionVerified": False,
        }
        receipts.append({"snapshot": snapshot, "signature": _sign(snapshot, password)})
    return {
        "schema": SCHEMA, "receipts": receipts, "issuedRaces": len(receipts),
        "skippedStartedRaces": past, "skippedNotBuyRaces": skipped,
        "captureServerTime": now.isoformat(timespec="seconds"),
        "officialScheduleVerified": False, "officialResultsConnected": False,
        "actualPurchase": False,
    }


def verify_preview_receipts(receipts, password, day):
    """Reject any changed receipt, even when only one horse number changes.

    No independent off-time assertion is made: signed server timestamp only.
    """
    _selected_day(day)
    if not isinstance(receipts, list) or len(receipts) > MAX_RECEIPTS:
        raise ReceiptError("Invalid receipt count")
    predictions = []
    seen = set()
    for receipt in receipts:
        if (not isinstance(receipt, dict)
                or set(receipt) != {"snapshot", "signature"}):
            raise ReceiptError("Invalid receipt shape")
        snapshot, signature = receipt["snapshot"], receipt["signature"]
        if (not isinstance(snapshot, dict)
                or set(snapshot) != RECORD_FIELDS
                or snapshot.get("date") != day
                or snapshot.get("scheduleVerified") is not False
                or snapshot.get("predictionVerified") is not False
                or not isinstance(signature, str)
                or not re.fullmatch(r"[0-9a-f]{64}", signature)
                or not hmac.compare_digest(_sign(snapshot, password), signature)):
            raise ReceiptError("Receipt signature is invalid")
        try:
            key = _identity(snapshot)
            if key in seen:
                raise ReceiptError("Duplicate receipt")
            seen.add(key)
            locked = _time(snapshot["lockedAt"])
            off = _time(snapshot["scheduledOffAt"])
            if (locked >= off or snapshot.get("sourceKind") != "prestart-locked"
                    or snapshot.get("actualPurchase") is not False):
                raise ReceiptError("Invalid receipt timestamp")
            triple = _tickets(snapshot["trifectaTickets"], "trifecta")
            trio = _tickets(snapshot["trioTickets"], "trio")
            if not triple and not trio:
                raise ReceiptError("Empty receipt")
        except (ReviewInputError, KeyError, TypeError) as exc:
            raise ReceiptError("Invalid receipt content") from exc
        predictions.append({key: value for key, value in snapshot.items()
                            if key not in ("scheduleVerified", "predictionVerified")})
    return predictions
