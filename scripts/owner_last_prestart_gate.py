"""Final server-clock gate just before returning private owner research drafts.

This is a SECOND time check, not a replacement for the original single
captured timestamp used for ranking and HMAC signing. The optional /tka read,
source diagnostics or server serialization can complete after a race's JRDB
provisional off time. That late race must not be newly presented as a
prestart draft. No JRDB calls, archive writes, official JRA claims or wagers.
"""
from datetime import datetime, timezone, timedelta
import re

from jrdb_coverage import CoverageError

JST = timezone(timedelta(hours=9))
OFF_TEXT = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z", re.ASCII)



def _signed_triplets(value):
    """Match frozen tickets to the draft without assuming the same list order."""
    if (not isinstance(value, list) or not 1 <= len(value) <= 40):
        raise CoverageError("Final prestart ticket list mismatch")
    triples = set()
    for item in value:
        if (not isinstance(item, list) or len(item) != 3
                or any(type(number) is not int or not 1 <= number <= 18
                       for number in item)
                or len(set(item)) != 3):
            raise CoverageError("Final prestart ticket mismatch")
        key = tuple(item)
        if key in triples:
            raise CoverageError("Duplicate final prestart ticket")
        triples.add(key)
    return triples


def _signed_clock(value):
    if not isinstance(value, str):
        raise CoverageError("Final prestart timestamp missing")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise CoverageError("Final prestart timestamp invalid") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CoverageError("Final prestart timestamp lacks timezone")
    return parsed.astimezone(JST)


def _verify_delivery_alignment(report, current_time):
    """Reject swapped, stale, duplicated or unrelated receipts BEFORE redaction.

    This is a structural identity check; HMAC signing happens earlier and the
    iPhone verifies signatures independently. Do not read provider or JRA.
    """
    day = report["date"]
    try:
        date_iso = datetime.strptime(day, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        raise CoverageError("Final prestart day invalid") from None
    draft_rows = {}
    all_keys = set()
    for row in report["races"]:
        if (not isinstance(row, dict) or not isinstance(row.get("track"), str)
                or not row["track"] or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12
                or row.get("status") not in ("hold", "provisional_draft")):
            raise CoverageError("Final prestart race structure invalid")
        key = (row["track"], row["race"])
        if key in all_keys:
            raise CoverageError("Final prestart duplicate race")
        all_keys.add(key)
        if row["status"] == "hold":
            if row.get("tickets") != [] or row.get("points") != 0:
                raise CoverageError("Final prestart held ticket mismatch")
            continue
        text = row.get("postTime")
        if not isinstance(text, str) or not OFF_TEXT.fullmatch(text):
            raise CoverageError("Final prestart off time mismatch")
        off = datetime.strptime(day + text, "%Y%m%d%H:%M").replace(tzinfo=JST)
        triplets = _signed_triplets(row.get("tickets"))
        if (row.get("points") != len(triplets)
                or row.get("amountYen") != len(triplets) * 100):
            raise CoverageError("Final prestart draft amount mismatch")
        draft_rows[key] = (off, triplets)

    receipts = {}
    for receipt in report["researchReceipts"]:
        if (not isinstance(receipt, dict)
                or not isinstance(receipt.get("snapshot"), dict)
                or not isinstance(receipt.get("signature"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", receipt["signature"],
                                    re.ASCII)):
            raise CoverageError("Final prestart receipt structure invalid")
        snap = receipt["snapshot"]
        key = (snap.get("track"), snap.get("race"))
        if (key not in draft_rows or key in receipts
                or snap.get("date") != date_iso
                or snap.get("sourceKind") != "prestart-locked"
                or snap.get("actualPurchase") is not False
                or snap.get("scheduleVerified") is not False
                or snap.get("predictionVerified") is not False):
            raise CoverageError("Final prestart receipt identity mismatch")
        off, triplets = draft_rows[key]
        if (_signed_clock(snap.get("scheduledOffAt")) != off
                or _signed_clock(snap.get("lockedAt")) >= off
                or _signed_clock(snap.get("lockedAt")) > current_time
                or _signed_triplets(snap.get("trifectaTickets")) != triplets
                or snap.get("trioTickets") != []):
            raise CoverageError("Final prestart receipt does not match draft")
        receipts[key] = receipt
    if set(draft_rows) != set(receipts):
        raise CoverageError("Final prestart missing or extra receipt")


def expire_undelivered_drafts(report, current_time):
    """Mutate only this unreturned private report; preserve persisted receipts.

    The first valid signed record may already be stored in opt-in Postgres.
    Its immutable history is NEVER deleted here. Only the response's fresh
    formations and its outgoing receipt list are withheld for newly late races.
    """
    if (not isinstance(current_time, datetime)
            or current_time.tzinfo is None
            or current_time.utcoffset() is None):
        raise CoverageError("Final prestart server clock is unavailable")
    current_time = current_time.astimezone(JST)
    if (not isinstance(report, dict) or not isinstance(report.get("races"), list)
            or not isinstance(report.get("researchReceipts"), list)
            or not isinstance(report.get("date"), str)
            or not re.fullmatch(r"[0-9]{8}", report["date"], re.ASCII)):
        raise CoverageError("Final prestart report contract mismatch")
    races = report["races"]
    receipt_rows = report["researchReceipts"]
    if (report.get("draftCount") != sum(
            r.get("status") == "provisional_draft" for r in races)
            or report.get("researchReceiptCount") != len(receipt_rows)
            or len(receipt_rows) != report["draftCount"]):
        raise CoverageError("Final prestart receipt count mismatch")

    # Validate the complete prestart receipt/race bijection even if no
    # race has expired yet. Counts alone cannot detect a swapped receipt.
    _verify_delivery_alignment(report, current_time)

    expired = set()
    for row in races:
        if row.get("status") != "provisional_draft":
            continue
        text = row.get("postTime")
        if not isinstance(text, str) or not OFF_TEXT.fullmatch(text):
            raise CoverageError("Final prestart off time mismatch")
        off_time = datetime.strptime(
            report["date"] + text, "%Y%m%d%H:%M").replace(tzinfo=JST)
        if current_time >= off_time:
            expired.add((row["track"], row["race"]))
    if not expired:
        return 0

    retained = []
    for receipt in receipt_rows:
        if not isinstance(receipt, dict) or not isinstance(
                receipt.get("snapshot"), dict):
            raise CoverageError("Final prestart receipt mismatch")
        snap = receipt["snapshot"]
        if (snap.get("track"), snap.get("race")) not in expired:
            retained.append(receipt)
    for row in races:
        if (row["track"], row["race"]) in expired:
            row.update({
                "status": "hold", "reason": "after_provisional_off",
                "runners": [], "first": [], "second": [], "third": [],
                "tickets": [], "points": 0, "amountYen": 0,
            })
    report["researchReceipts"] = retained
    report["researchReceiptCount"] = len(retained)
    report["draftCount"] = sum(r["status"] == "provisional_draft" for r in races)
    report["holdCount"] = sum(r["status"] == "hold" for r in races)
    reasons = {}
    for row in races:
        if row["status"] == "hold":
            reason = row["reason"]
            reasons[reason] = reasons.get(reason, 0) + 1
    report["holdReasons"] = reasons
    if report["researchReceiptCount"] != report["draftCount"]:
        raise CoverageError("Final prestart filtered receipt mismatch")
    return len(expired)
