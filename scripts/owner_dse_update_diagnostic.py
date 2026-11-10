"""Owner-only /dse updated_at *format* diagnostic from already fetched rows.

"updated_at" is a LAST MODIFICATION marker, NOT the initial publication time.
The provider's documented sample is date-only despite a datetime field
description. Never infer availability from a race date, a missing timezone,
the fetch time, or an updated_at value, even when before capture.

Call only in an already authenticated, explicitly requested private historic
study. This pure function makes no provider calls, writes, logs, grades or
predictions and never serializes horse IDs, timestamps or licensed source rows.
"""
import re
from datetime import datetime

VERSION = "owner-dse-update-diagnostic-1"
MAX_BATCHES = 3
MAX_ROWS_PER_BATCH = 18
DATE_ONLY = re.compile(r"(?:20[0-9]{6}|20[0-9]{2}-[0-9]{2}-[0-9]{2})\Z")


def _classification(raw, capture):
    if raw is None or raw == "":
        return "missing"
    if type(raw) is not str or len(raw) > 45:
        return "ambiguous"
    if DATE_ONLY.fullmatch(raw):
        return "dateOnly"
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            return "ambiguous"
        return "updateBeforeCapture" if stamp < capture else "updateAtOrAfterCapture"
    except (ValueError, TypeError, OverflowError):
        return "ambiguous"


def audit_dse_update_fields(fetched_batches, *, captured_at):
    """Assess /dse update markers without claiming result-publication proof.

    Input batches must be exactly those already returned by bounded /dse
    calls during an explicitly requested past-staff study. No new API reads.
    """
    if (not isinstance(captured_at, datetime) or captured_at.tzinfo is None
            or captured_at.utcoffset() is None):
        raise ValueError("Owner server snapshot must be timezone-aware")
    if (type(fetched_batches) is not list or len(fetched_batches) > MAX_BATCHES):
        raise ValueError("Invalid bounded result batch count")
    counts = {k: 0 for k in (
        "missing", "dateOnly", "ambiguous", "updateBeforeCapture",
        "updateAtOrAfterCapture",
    )}
    invalid_batches = 0
    observed_rows = 0
    for batch in fetched_batches:
        if (type(batch) is not list
                or not 3 <= len(batch) <= MAX_ROWS_PER_BATCH
                or any(type(row) is not dict for row in batch)):
            invalid_batches += 1
            continue
        observed_rows += len(batch)
        for row in batch:
            counts[_classification(row.get("updated_at"), captured_at)] += 1
    return {
        "version": VERSION,
        "source": "already_fetched_private_dse_updated_at",
        "observedResponseCount": len(fetched_batches),
        "invalidResponseCount": invalid_batches,
        "observedResultRowCount": observed_rows,
        "missingUpdateCount": counts["missing"],
        "dateOnlyCount": counts["dateOnly"],
        "ambiguousUpdateCount": counts["ambiguous"],
        "timestampBeforeCaptureCount": counts["updateBeforeCapture"],
        "timestampAtOrAfterCaptureCount": counts["updateAtOrAfterCapture"],
        "timestampOrderingChecked": True,
        "initialPublicationTimeVerified": False,
        "sourceTimestampAuthenticityVerified": False,
        "historicalResultPublicationTimesVerified": False,
        "independentJraVerified": False,
        "formalTenFactorsReady": False,
        "bettingReady": False,
        "researchOnly": True,
        "privateOwnerOnly": True,
        "extraProviderCalls": 0,
        "changesExistingTickets": False,
        "changesExistingReceipts": False,
        "changesExistingRoi": False,
        "note": "結果更新日時の形式だけを集計。更新日時は初回結果公表日時ではなく、正式採点には利用しません。",
    }
