"""Separate, signed, immutable 79-weight 3連単 *research draft* receipts.

Only the authenticated private history handler can issue, using the exact
in-process original 5-factor/79-weight data and provisional JRDB schedule.
No user-submitted tickets can be signed. This is not a real purchase, a
JRA-verified prediction, or the formal full-ten model. Signature verification
is offline and does not upgrade a draft to official betting/ROI.
"""
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone

from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import _safe_formation_sizes
from owner_research6_five_drafts import (
    build_research6_five_drafts, _check_horses, _check_report,
    VERSION as DRAFT_VERSION,
)
from owner_rebound_receipts import _day, _timestamp
from owner_three_core_receipts import TRACKS

VERSION = "owner-research6-draft-receipt-1"
DOMAIN = b"keiba-nine/owner-research6-79-draft-prestart/v1"
SOURCE = "prestart-unverified-research6-79-draft"
MAX_RACES = 36
MAX_TICKETS = 40
MAX_AGE_SECONDS = 7 * 86400
FIELDS = frozenset((
    "version", "date", "track", "race", "sourceKind",
    "capturedAt", "scheduledOffAt", "policyVersion", "researchWeight",
    "remainingUnassessedWeight", "runnerCount", "first", "second",
    "third", "tickets", "points", "amountYen", "researchOnly",
    "officialJraVerified", "predictionReady", "actualPurchase",
))


class DraftReceiptError(ValueError):
    """Safe error with no licensed JRDB, timestamp or signing secret."""


def _key(secret):
    if not isinstance(secret, str) or len(secret) < 32:
        raise DraftReceiptError("Owner draft signing credential unavailable")
    return hmac.new(secret.encode(), DOMAIN, hashlib.sha256).digest()


def _sign(snapshot, secret):
    try:
        data = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, OverflowError):
        raise DraftReceiptError("Unrecognized draft receipt") from None
    return hmac.new(_key(secret), data, hashlib.sha256).hexdigest()


def _numbers(values, max_count):
    return (isinstance(values, list) and 1 <= len(values) <= max_count
            and all(type(n) is int and 1 <= n <= 18 for n in values)
            and len(set(values)) == len(values))


def _validate(snapshot):
    if (not isinstance(snapshot, dict) or set(snapshot) != FIELDS
            or snapshot["version"] != VERSION
            or snapshot["sourceKind"] != SOURCE
            or snapshot["policyVersion"] != "research-6"
            or snapshot["researchWeight"] != 79
            or snapshot["remainingUnassessedWeight"] != 21
            or snapshot["researchOnly"] is not True
            or snapshot["officialJraVerified"] is not False
            or snapshot["predictionReady"] is not False
            or snapshot["actualPurchase"] is not False):
        raise DraftReceiptError("Invalid research-6 draft receipt")
    day = _day(snapshot["date"])
    if (snapshot["track"] not in TRACKS
            or type(snapshot["race"]) is not int
            or not 1 <= snapshot["race"] <= 12
            or type(snapshot["runnerCount"]) is not int
            or not 4 <= snapshot["runnerCount"] <= 18):
        raise DraftReceiptError("Research-6 draft coordinate invalid")
    captured, off = _timestamp(snapshot["capturedAt"]), _timestamp(
        snapshot["scheduledOffAt"])
    if (captured >= off or not 0 < (off-captured).total_seconds() <= MAX_AGE_SECONDS
            or off.astimezone(__import__("datetime").timezone(
                __import__("datetime").timedelta(hours=9))).strftime("%Y%m%d") != day):
        raise DraftReceiptError("Research-6 draft was not locked before off")
    first, second, third = (snapshot["first"], snapshot["second"],
                            snapshot["third"])
    if (not _numbers(first, 3) or len(first) not in (2, 3)
            or not _numbers(second, 5) or len(second) <= len(first)
            or not _numbers(third, 9) or len(third) < len(second)
            or len(third) > snapshot["runnerCount"]
            or first != second[:len(first)] or second != third[:len(second)]
            or not isinstance(snapshot["tickets"], list)
            or len(snapshot["tickets"]) > MAX_TICKETS):
        raise DraftReceiptError("Invalid five-factor research formation")
    generated = [[a, b, c] for a in first for b in second for c in third
                 if a != b and a != c and b != c]
    if (not 1 <= len(generated) <= MAX_TICKETS
            or snapshot["tickets"] != generated
            or type(snapshot["points"]) is not int
            or snapshot["points"] != len(generated)
            or type(snapshot["amountYen"]) is not int
            or snapshot["amountYen"] != len(generated) * 100):
        raise DraftReceiptError("Research-6 signed tickets do not match formation")
    return day, snapshot["track"], snapshot["race"]


def issue_research6_draft_receipts(history, programme, secret, day, now=None):
    """Sign only prestart, complete, recomputable *server-made* research drafts."""
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    if (not isinstance(history, dict) or history.get("date") != day
            or history.get("predictionReady") is not False
            or not isinstance(history.get("research6FiveDrafts"), dict)
            or not isinstance(history.get("newWeightFiveResearch"), dict)):
        raise DraftReceiptError("No trusted research-6 historical snapshot")
    original = history["research6FiveDrafts"]
    try:
        recalculated = build_research6_five_drafts(
            programme, history["newWeightFiveResearch"], day, now=now)
    except (CoverageError, ValueError, KeyError, TypeError):
        raise DraftReceiptError("Research-6 draft cannot be reconstructed") from None
    for key in ("version", "policyVersion", "date", "raceCount", "unitYen",
                "factorWeights", "remainingUnassessedWeight",
                "researchFactorWeight", "officialJraVerified",
                "researchOnly", "privateOwnerOnly", "overallPredictionReady",
                "bettingReady", "autoPurchase", "actualPurchase"):
        if original.get(key) != recalculated.get(key):
            raise DraftReceiptError("Research-6 draft source mismatch")
    if (not isinstance(original.get("races"), list)
            or len(original["races"]) != len(recalculated["races"])
            or len(original["races"]) > MAX_RACES):
        raise DraftReceiptError("Research-6 draft roster mismatch")
    captures, expired, seen = [], 0, set()
    for before, current in zip(original["races"], recalculated["races"]):
        if (not isinstance(before, dict)
                or (before.get("track"), before.get("race")) !=
                    (current["track"], current["race"])
                or (current["track"], current["race"]) in seen):
            raise DraftReceiptError("Research-6 draft race identity mismatch")
        coord = current["track"], current["race"]
        seen.add(coord)
        # A proposal generated milliseconds before off is NOT eligible for
        # post-off capture. Do not reconstruct a historical pick.
        if (before.get("status") == "five_factor_research_draft"
                and current["reason"] == "past_provisional_off"):
            expired += 1
            continue
        if before != current:
            raise DraftReceiptError("Research-6 draft payload changed after scoring")
        if current["status"] != "five_factor_research_draft":
            continue
        off = datetime.fromisoformat(
            f"{day[:4]}-{day[4:6]}-{day[6:]}T{current['postTime']}:00+09:00")
        if now >= off.astimezone(timezone.utc):
            expired += 1
            continue
        snapshot = {
            "version": VERSION, "date": day,
            "track": current["track"], "race": current["race"],
            "sourceKind": SOURCE,
            "capturedAt": now.isoformat(),
            "scheduledOffAt": off.isoformat(),
            "policyVersion": "research-6", "researchWeight": 79,
            "remainingUnassessedWeight": 21,
            "runnerCount": current["runnerCount"],
            "first": list(current["first"]),
            "second": list(current["second"]),
            "third": list(current["third"]),
            "tickets": [list(row) for row in current["tickets"]],
            "points": current["points"], "amountYen": current["amountYen"],
            "researchOnly": True, "officialJraVerified": False,
            "predictionReady": False, "actualPurchase": False,
        }
        _validate(snapshot)
        captures.append({"snapshot": snapshot, "signature": _sign(snapshot, secret)})
    return {
        "version": VERSION, "date": day,
        "receiptCount": len(captures), "receipts": captures,
        "expiredBeforeSigning": expired,
        "serverSigned": True, "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "jraScheduleVerified": False,
        "predictionReady": False, "bettingReady": False,
        "actualPurchase": False, "changesExistingReceipts": False,
        "changesExistingRoi": False,
    }


def verify_research6_draft_receipts(receipts, secret, day):
    """Verify signed first-write ticket snapshots without JRA/JRDB requests."""
    _day(day)
    if not isinstance(receipts, list) or len(receipts) > MAX_RACES:
        raise DraftReceiptError("Invalid research-6 receipt batch")
    seen, snapshots = set(), []
    for row in receipts:
        if (not isinstance(row, dict)
                or set(row) != {"snapshot", "signature"}
                or not isinstance(row["signature"], str)
                or not re.fullmatch(r"[a-f0-9]{64}", row["signature"])):
            raise DraftReceiptError("Invalid signed research-6 receipt shape")
        coord = _validate(row["snapshot"])
        if (coord[0] != day or coord in seen
                or not hmac.compare_digest(
                    row["signature"], _sign(row["snapshot"], secret))):
            raise DraftReceiptError("Research-6 receipt signature mismatch")
        seen.add(coord)
        snapshots.append(row["snapshot"])
    return snapshots
