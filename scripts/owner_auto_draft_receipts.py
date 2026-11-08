"""Server-signed, transient receipts for private auto-generated research drafts.

This only seals already-generated in-process JRDB two-factor candidate tickets.
No arbitrary client tickets or horse metrics are accepted. No JRA truth,
official race time, purchase, payout, or archived persistence is claimed.
"""
from datetime import datetime, timezone, timedelta
import re

from owner_prestart_receipt import (
    _server_time, _selected_day, _sign, ReceiptError, MAX_RECEIPTS,
)
from keiba_100yen_review import _identity, _tickets, ReviewInputError

JST = timezone(timedelta(hours=9))
AUTO_VERSION = "jrdb-owner-auto-draft-1"
TRACKS = frozenset(("札幌", "函館", "福島", "新潟", "東京",
                   "中山", "中京", "京都", "阪神", "小倉"))


def seal_auto_research_drafts(report, password, now=None):
    """Return first-party research receipts for eligible future drafts.

    When run by the private WSGI service, report MUST come from its own
    just-computed provider research snapshot, never a browser request.
    """
    now = _server_time(now)
    if (not isinstance(report, dict)
            or report.get("version") != AUTO_VERSION
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("officialJraVerified") is not False
            or report.get("overallPredictionReady") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False
            or report.get("sourceReadCount") != 4
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > 120
            or report.get("raceCount") != len(report["races"])):
        raise ReceiptError("Untrusted automatic research report")
    day = report.get("date")
    if not isinstance(day, str) or len(day) != 8 or not day.isascii() or not day.isdigit():
        raise ReceiptError("Invalid research date")
    hyphenated = f"{day[:4]}-{day[4:6]}-{day[6:]}"
    _selected_day(hyphenated)
    receipts = []
    seen = set()
    for row in report["races"]:
        if not isinstance(row, dict):
            raise ReceiptError("Invalid auto-draft race")
        try:
            key = _identity({"date": hyphenated, "track": row.get("track"),
                             "race": row.get("race")})
        except ReviewInputError:
            raise ReceiptError("Invalid race identity") from None
        if key in seen:
            raise ReceiptError("Duplicate auto-draft identity")
        seen.add(key)
        if (row.get("researchOnly") is not True
                or row.get("officialJraVerified") is not False
                or row.get("overallPredictionReady") is not False
                or row.get("bettingReady") is not False
                or row.get("autoPurchase") is not False):
            raise ReceiptError("Non-research race cannot be signed")
        if row.get("status") == "hold":
            if row.get("points") != 0 or row.get("tickets") != []:
                raise ReceiptError("Held race has nonempty tickets")
            continue
        if row.get("status") != "provisional_draft":
            raise ReceiptError("Unknown research status")
        text = row.get("postTime")
        if not isinstance(text, str) or not re.fullmatch(
                r"(?:[01]\d|2[0-3]):[0-5]\d", text):
            raise ReceiptError("Missing provisional off time")
        off = datetime.fromisoformat(hyphenated + "T" + text + ":00+09:00")
        # Double-check server clock, even though the builder already did.
        if now >= off.astimezone(timezone.utc):
            continue
        first, second, third = row.get("first"), row.get("second"), row.get("third")
        if (not all(isinstance(x, list) for x in (first, second, third))
                or len(first) not in (2, 3)
                or not len(first) < len(second) <= 5
                or not len(second) <= len(third) <= 9):
            raise ReceiptError("Invalid automatic formation")
        expected = sorted({(x, y, z) for x in first for y in second for z in third
                           if x != y and x != z and y != z})
        try:
            actual = _tickets(row.get("tickets"), "trifecta")
        except ReviewInputError:
            raise ReceiptError("Invalid automatic ticket") from None
        if (not expected or len(expected) > 40
                or actual != tuple(expected)
                or row.get("points") != len(expected)
                or row.get("amountYen") != len(expected) * 100):
            raise ReceiptError("Auto-generated tickets do not match formation")
        snapshot = {
            "date": hyphenated, "track": key[1], "race": key[2],
            "sourceKind": "prestart-locked", "actualPurchase": False,
            "lockedAt": now.isoformat(timespec="seconds"),
            "scheduledOffAt": off.isoformat(timespec="seconds"),
            "trifectaTickets": [list(x) for x in expected],
            "trioTickets": [],
            "scheduleVerified": False, "predictionVerified": False,
        }
        receipts.append({"snapshot": snapshot, "signature": _sign(snapshot, password)})
    if len(receipts) > MAX_RECEIPTS:
        raise ReceiptError("More races than private daily research limit")
    return receipts
