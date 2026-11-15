"""Immutable private prestart RECORD of an unsigned 79-point sparse research example.

Signing is evidence that a server-generated *research reference* existed
before the provisional JRDB off time. It does NOT upgrade any grade, turn
an unsigned example into a betting recommendation, certify JRA entries,
claim a real purchase or create official/virtual ROI.
Only trusted in-process /history evidence can be signed. User-supplied
candidate tickets are never accepted for signing.
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone, timedelta

from jrdb_coverage import CoverageError
from owner_rebound_receipts import _day, _timestamp
from owner_three_core_receipts import TRACKS
from owner_research6_five_drafts import _normal_programme
from owner_sparse_five_preview import preview_sparse_five_holds, JST

VERSION = "owner-sparse-five-reference-receipt-1"
SOURCE = "prestart-sparse-recent-79-research-record"
DOMAIN = b"keiba-nine/owner-sparse-five-prestart-reference/v1"
MAX_RACES = 36
MAX_TICKETS = 40
MAX_AGE_SECONDS = 7 * 86400
FIELDS = {
    "version", "date", "track", "race", "sourceKind",
    "capturedAt", "scheduledOffAt", "policyVersion",
    "runnerCount", "missingRecentCount", "first", "second", "third",
    "tickets", "points", "amountYen", "researchOnly",
    "scoreCalibrated", "officialJraVerified", "predictionReady",
    "bettingReady", "actualPurchase"
}


class SparseReferenceReceiptError(ValueError):
    """Safe public error: no paid data, credentials or horse identifiers."""


def _key(secret):
    if not isinstance(secret, str) or len(secret) < 32:
        raise SparseReferenceReceiptError("Owner signing secret unavailable")
    return hmac.new(secret.encode(), DOMAIN, hashlib.sha256).digest()


def _sign(snapshot, secret):
    try:
        canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, OverflowError):
        raise SparseReferenceReceiptError("Invalid prestart research record") from None
    return hmac.new(_key(secret), canonical, hashlib.sha256).hexdigest()


def _validate(snapshot):
    if (not isinstance(snapshot, dict) or set(snapshot) != FIELDS
            or snapshot["version"] != VERSION
            or snapshot["sourceKind"] != SOURCE
            or snapshot["policyVersion"] != "research-6"
            or snapshot["researchOnly"] is not True
            or snapshot["scoreCalibrated"] is not False
            or snapshot["officialJraVerified"] is not False
            or snapshot["predictionReady"] is not False
            or snapshot["bettingReady"] is not False
            or snapshot["actualPurchase"] is not False):
        raise SparseReferenceReceiptError("Invalid sparse reference record")
    try:
        day = _day(snapshot["date"])
        captured = _timestamp(snapshot["capturedAt"])
        off = _timestamp(snapshot["scheduledOffAt"])
    except (ValueError, TypeError, KeyError):
        raise SparseReferenceReceiptError("Invalid sparse reference time") from None
    if (snapshot["track"] not in TRACKS
            or type(snapshot["race"]) is not int
            or not 1 <= snapshot["race"] <= 12
            or type(snapshot["runnerCount"]) is not int
            or not 4 <= snapshot["runnerCount"] <= 18
            or type(snapshot["missingRecentCount"]) is not int
            or not 1 <= snapshot["missingRecentCount"] <= snapshot["runnerCount"]
            or captured >= off
            or not 0 < (off - captured).total_seconds() <= MAX_AGE_SECONDS
            or off.astimezone(JST).strftime("%Y%m%d") != day):
        raise SparseReferenceReceiptError("Invalid prestart identity or order")
    arrays = [snapshot["first"], snapshot["second"], snapshot["third"]]
    for arr in arrays:
        if (not isinstance(arr, list) or not arr
                or any(type(n) is not int or not 1 <= n <= 18 for n in arr)
                or len(set(arr)) != len(arr)):
            raise SparseReferenceReceiptError("Invalid research candidate numbers")
    a, b, c = map(len, arrays)
    if (not 1 <= a <= 3 or not a < b <= 5 or not b <= c <= 9
            or c > snapshot["runnerCount"]
            or arrays[1][:a] != arrays[0]
            or arrays[2][:b] != arrays[1]):
        raise SparseReferenceReceiptError("Unstable research membership")
    tickets = [[x, y, z] for x in arrays[0] for y in arrays[1]
               for z in arrays[2] if len({x, y, z}) == 3]
    if (not 12 <= len(tickets) <= MAX_TICKETS
            or not isinstance(snapshot["tickets"], list)
            or snapshot["tickets"] != tickets
            or type(snapshot["points"]) is not int
            or snapshot["points"] != len(tickets)
            or type(snapshot["amountYen"]) is not int
            or snapshot["amountYen"] != len(tickets) * 100):
        raise SparseReferenceReceiptError("Invalid research combinations")
    return day, snapshot["track"], snapshot["race"]


def issue_sparse_reference_receipts(history, programme, secret, day, *, now=None):
    """Issue only recomputed before-off math-stable references from /history."""
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    if (not isinstance(history, dict) or history.get("date") != day
            or history.get("predictionReady") is not False
            or not isinstance(history.get("newWeightFiveResearch"), dict)
            or not isinstance(history.get("research6FiveDrafts"), dict)
            or not isinstance(history.get("sparseFiveRecentReferences"), dict)):
        raise SparseReferenceReceiptError("Trusted research snapshot unavailable")
    original = history["sparseFiveRecentReferences"]
    if (original.get("researchOnly") is not True
            or original.get("officialJraVerified") is not False
            or original.get("predictionReady") is not False
            or original.get("bettingReady") is not False
            or original.get("ticketsIssued") != 0
            or original.get("date") != day
            or not isinstance(original.get("races"), list)):
        raise SparseReferenceReceiptError("Untrusted sparse references")
    try:
        current = preview_sparse_five_holds(
            programme, history["newWeightFiveResearch"],
            history["research6FiveDrafts"], day, now=now)
        schedule = _normal_programme(programme, day)
    except (CoverageError, ValueError, TypeError, KeyError):
        raise SparseReferenceReceiptError("Sparse research cannot be reconstructed") from None
    original_by = {}
    for row in original["races"]:
        if not isinstance(row, dict):
            raise SparseReferenceReceiptError("Malformed sparse reference")
        coord = row.get("track"), row.get("race")
        if coord in original_by:
            raise SparseReferenceReceiptError("Duplicate sparse reference")
        original_by[coord] = row
    current_by = {(r["track"], r["race"]): r for r in current["races"]}
    programme_by = {(r["track"], r["race"]): r for r in schedule}
    source_by = {(r["track"], r["race"]): r
                 for r in history["newWeightFiveResearch"]["races"]}
    if (len(original_by) > MAX_RACES
            or len(programme_by) != len(schedule)
            or len(source_by) != len(schedule)):
        raise SparseReferenceReceiptError("Invalid reference race set")
    signed, expired = [], 0
    for coord, old in original_by.items():
        program, source = programme_by.get(coord), source_by.get(coord)
        if program is None or source is None:
            raise SparseReferenceReceiptError("Unknown sparse race")
        post = program["post_time"]
        if not isinstance(post, str):
            raise SparseReferenceReceiptError("Unscheduled sparse race")
        off = datetime.strptime(day + post, "%Y%m%d%H:%M").replace(tzinfo=JST)
        if now >= off:
            expired += 1
            continue
        if old != current_by.get(coord):
            raise SparseReferenceReceiptError("Reference changed before signature")
        numbers = (old["first"], old["second"], old["third"])
        tickets = [[a, b, c] for a in numbers[0] for b in numbers[1]
                   for c in numbers[2] if len({a, b, c}) == 3]
        snapshot = {
            "version": VERSION, "date": day,
            "track": coord[0], "race": coord[1],
            "sourceKind": SOURCE, "capturedAt": now.isoformat(),
            "scheduledOffAt": off.isoformat(), "policyVersion": "research-6",
            "runnerCount": source["runnerCount"],
            "missingRecentCount": old["missingRecentCount"],
            "first": list(numbers[0]), "second": list(numbers[1]),
            "third": list(numbers[2]), "tickets": tickets,
            "points": old["points"], "amountYen": old["points"] * 100,
            "researchOnly": True, "scoreCalibrated": False,
            "officialJraVerified": False, "predictionReady": False,
            "bettingReady": False, "actualPurchase": False,
        }
        _validate(snapshot)
        signed.append({"snapshot": snapshot, "signature": _sign(snapshot, secret)})
    return {
        "version": VERSION, "date": day, "serverSigned": True,
        "receiptCount": len(signed), "receipts": signed,
        "expiredBeforeSigning": expired,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "predictionReady": False,
        "bettingReady": False, "actualPurchase": False,
        "changesExistingReceipts": False, "changesExistingRoi": False,
    }


def verify_sparse_reference_receipts(receipts, secret, day):
    """Cryptographic verification; zero provider reads, no result claims."""
    _day(day)
    if not isinstance(receipts, list) or len(receipts) > MAX_RACES:
        raise SparseReferenceReceiptError("Invalid sparse reference batch")
    seen, snapshots = set(), []
    for row in receipts:
        if (not isinstance(row, dict) or set(row) != {"signature", "snapshot"}
                or not isinstance(row["signature"], str)
                or len(row["signature"]) != 64
                or any(c not in "0123456789abcdef" for c in row["signature"])):
            raise SparseReferenceReceiptError("Invalid research signature")
        coord = _validate(row["snapshot"])
        if coord[0] != day or coord in seen or not hmac.compare_digest(
                row["signature"], _sign(row["snapshot"], secret)):
            raise SparseReferenceReceiptError("Research reference signature mismatch")
        seen.add(coord)
        snapshots.append(row["snapshot"])
    return snapshots
