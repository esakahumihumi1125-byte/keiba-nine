"""HMAC-sealed, privacy-preserving per-day owner jockey/stable study sessions.

A signed session proves only what the private server observed during an
explicit /history run. It does NOT prove JRA authenticity, result publication
times, independent historic race identities, performance quality or a
prediction. Only NON-IDENTIFYING summary counters are signed.
"""
from datetime import datetime, timezone
import hashlib
import hmac
import json
import re

from owner_rebound_receipts import _day, _timestamp

VERSION = "owner-staff-study-receipt-1"
SOURCE = "private-server-three-race-aggregate-unverified"
DOMAIN = b"keiba-nine/owner-staff-study-summary/v1"
MAX_DAYS = 120

COUNTS = frozenset((
    "requestedRaceLimit", "selectedPastRaceCount", "providerReadCount",
    "providerReadBudget", "completedJoinRaceCount",
    "heldOrIncompleteRaceCount", "totalJoinedRunnerObservations",
    "distinctJockeyCount", "distinctTrainerCount", "distinctPairCount",
    "pairsSeenInTwoOrMoreRaces", "pairRunnerObservations",
    "observedFirstPlaceCount", "observedTopThreeCount",
))
FLAGS_FALSE = frozenset((
    "pastResultPublicationVerified", "independentJraVerified",
    "fullTenFactorReady", "jockeyTrainerPerformanceAssessed",
    "holdoutValidated", "predictionReady", "bettingReady", "autoPurchase",
    "actualPurchase", "changesExistingReceipts", "changesExistingTickets",
    "changesExistingRoi",
))
FLAGS_TRUE = frozenset((
    "researchOnly", "privateOwnerOnly",
    "additionalPaidReadsOnlyOnExplicitOptIn",
))
SUMMARY_FIELDS = COUNTS | FLAGS_FALSE | FLAGS_TRUE | {
    "version", "sourceFamily", "providerUnavailable",
    "formalTenPointGrade", "formalTenPointScore",
}
SNAPSHOT_FIELDS = frozenset((
    "version", "date", "capturedAt", "sourceKind", "summary",
    "researchOnly", "officialJraVerified", "actualPurchase",
    "independentHistoricRaceDedupVerified", "formalTenPointReady",
))


class StaffStudyReceiptError(ValueError):
    """Never show provider payloads, keys or HMAC secret in exception text."""


def _validate_summary(summary):
    if (not isinstance(summary, dict) or set(summary) != SUMMARY_FIELDS
            or summary["version"] != "owner-past-staff-batch-1"
            or summary["sourceFamily"] != "private_dky_dse_bounded_races"
            or summary["formalTenPointGrade"] != "未評価"
            or summary["formalTenPointScore"] is not None
            or type(summary["providerUnavailable"]) is not bool
            or any(summary.get(key) is not False for key in FLAGS_FALSE)
            or any(summary.get(key) is not True for key in FLAGS_TRUE)
            or any(type(summary.get(key)) is not int
                   or summary[key] < 0 for key in COUNTS)):
        raise StaffStudyReceiptError("Invalid ungraded staff study summary")
    selected = summary["selectedPastRaceCount"]
    complete = summary["completedJoinRaceCount"]
    held = summary["heldOrIncompleteRaceCount"]
    reads = summary["providerReadCount"]
    observed = summary["totalJoinedRunnerObservations"]
    if (summary["requestedRaceLimit"] != 3
            or summary["providerReadBudget"] != 6
            or not 1 <= selected <= 3
            or not 1 <= reads <= 6
            or reads > 2 * selected
            or complete + held != selected
            or summary["pairRunnerObservations"] != observed
            or not 3 * complete <= observed <= 18 * complete
            or summary["observedFirstPlaceCount"] != complete
            or summary["observedTopThreeCount"] != 3 * complete
            or any(summary[k] > observed for k in (
                "distinctJockeyCount", "distinctTrainerCount",
                "distinctPairCount"))
            or summary["pairsSeenInTwoOrMoreRaces"] >
                    summary["distinctPairCount"]
            or (complete == 0 and any(summary[k] != 0 for k in (
                "distinctJockeyCount", "distinctTrainerCount",
                "distinctPairCount", "pairsSeenInTwoOrMoreRaces")))
            or (complete > 0 and any(summary[k] == 0 for k in (
                "distinctJockeyCount", "distinctTrainerCount",
                "distinctPairCount")))
            or (not summary["providerUnavailable"] and reads != 2 * selected)
            or (summary["providerUnavailable"] and held == 0)):
        raise StaffStudyReceiptError("Staff study counters inconsistent")
    return summary


def _validate_snapshot(snapshot):
    if (not isinstance(snapshot, dict) or set(snapshot) != SNAPSHOT_FIELDS
            or snapshot.get("version") != VERSION
            or snapshot.get("sourceKind") != SOURCE
            or snapshot.get("researchOnly") is not True
            or snapshot.get("officialJraVerified") is not False
            or snapshot.get("actualPurchase") is not False
            or snapshot.get("formalTenPointReady") is not False
            or snapshot.get("independentHistoricRaceDedupVerified") is not False):
        raise StaffStudyReceiptError("Invalid private study receipt")
    try:
        day = _day(snapshot["date"])
        stamp = _timestamp(snapshot["capturedAt"])
        if not isinstance(snapshot["capturedAt"], str):
            raise ValueError()
        _validate_summary(snapshot["summary"])
    except (KeyError, ValueError, TypeError):
        raise StaffStudyReceiptError("Invalid study receipt structure") from None
    # Session timestamps are audit observation times, NOT pre-race lock times.
    if stamp.year < 2025:
        raise StaffStudyReceiptError("Invalid study observation clock")
    return day


def _sign(snapshot, secret):
    if not isinstance(secret, str) or not 32 <= len(secret) <= 1024:
        raise StaffStudyReceiptError("Owner study signing key unavailable")
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf-8")
    derived = hmac.new(secret.encode(), DOMAIN, hashlib.sha256).digest()
    return hmac.new(derived, raw, hashlib.sha256).hexdigest()


def issue_staff_study_receipt(summary, secret, day, *, now=None):
    """Issue ONLY after server completes explicit 3R study, not client POST."""
    try:
        day = _day(day)
        if not isinstance(summary, dict) or not isinstance(summary.get("note"), str):
            raise StaffStudyReceiptError("Unsigned source summary")
        protected = {key: value for key, value in summary.items()
                     if key != "note"}
        _validate_summary(protected)
        if set(summary) != SUMMARY_FIELDS | {"note"}:
            raise StaffStudyReceiptError("Unknown source fields")
        stamp = _timestamp(datetime.now(timezone.utc) if now is None else now)
        snapshot = {
            "version": VERSION, "date": day,
            "capturedAt": stamp.isoformat(),
            "sourceKind": SOURCE, "summary": protected,
            "researchOnly": True, "officialJraVerified": False,
            "actualPurchase": False, "formalTenPointReady": False,
            "independentHistoricRaceDedupVerified": False,
        }
        _validate_snapshot(snapshot)
        return {"snapshot": snapshot, "signature": _sign(snapshot, secret)}
    except (ValueError, TypeError, KeyError):
        raise StaffStudyReceiptError("Cannot sign private staff study") from None


def verify_staff_study_receipts(records, secret, day):
    """Read-only authentication of up to 120 dated, first-write aggregates."""
    try:
        _day(day)
        if (not isinstance(records, list) or len(records) > MAX_DAYS):
            raise StaffStudyReceiptError("Invalid study receipt count")
        seen, verified = set(), []
        for record in records:
            if (not isinstance(record, dict)
                    or set(record) != {"snapshot", "signature"}
                    or not isinstance(record["signature"], str)
                    or not re.fullmatch(r"[a-f0-9]{64}", record["signature"])):
                raise StaffStudyReceiptError("Invalid study receipt structure")
            snap = record["snapshot"]
            if (_validate_snapshot(snap) != day or
                    not hmac.compare_digest(
                        record["signature"], _sign(snap, secret))):
                raise StaffStudyReceiptError("Private study signature mismatch")
            if snap["date"] in seen:
                raise StaffStudyReceiptError("Repeated study date")
            seen.add(snap["date"])
            verified.append(snap)
        return verified
    except (StaffStudyReceiptError, ValueError, TypeError, KeyError):
        raise StaffStudyReceiptError("Private study signature verification failed") from None
