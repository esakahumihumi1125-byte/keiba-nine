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
