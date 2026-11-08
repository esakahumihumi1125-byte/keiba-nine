"""Strict owner-only input for a future automatic, prestart snapshot feed.

This adapter never fetches JRA results, trusts a client flag, or persists data.
An operator-controlled environment entry cannot prove immutable pre-race capture;
that proof requires a separate trusted capture pipeline, still pending.
"""
import json
from datetime import date

SCHEMA = "keiba-nine-owner-frozen-preview-v1"
MAX_BYTES = 64000


class FrozenSnapshotError(ValueError):
    pass


def _date(value):
    if not isinstance(value, str) or len(value) != 10:
        raise FrozenSnapshotError("Date required")
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def decode_frozen_snapshots(raw, selected_date):
    """Return only tickets for a selected day from private JSON.

    This does NOT independently verify that the snapshot was truly locked
    before off; the read-only ROI engine checks the supplied timestamps, while
    a future capture-and-audit service must establish their provenance.
    """
    if not _date(selected_date):
        raise FrozenSnapshotError("Invalid selected date")
    if not isinstance(raw, str) or not 2 <= len(raw) <= MAX_BYTES:
        raise FrozenSnapshotError("Invalid owner snapshot payload length")
    try:
        obj = json.loads(raw)
    except (TypeError, ValueError):
        raise FrozenSnapshotError("Invalid JSON") from None
    if not isinstance(obj, dict) or set(obj) != {"schema", "snapshots"}:
        raise FrozenSnapshotError("Invalid owner snapshot schema")
    if obj["schema"] != SCHEMA:
        raise FrozenSnapshotError("Unsupported owner snapshot schema")
    snapshots = obj["snapshots"]
    if not isinstance(snapshots, list) or len(snapshots) > 36:
        raise FrozenSnapshotError("Too many race snapshots")
    allowed = {"date", "track", "race", "sourceKind", "actualPurchase",
               "lockedAt", "scheduledOffAt", "trifectaTickets", "trioTickets"}
    selected = []
    for p in snapshots:
        if not isinstance(p, dict) or set(p) != allowed:
            raise FrozenSnapshotError("Unsupported race fields")
        if not _date(p.get("date")):
            raise FrozenSnapshotError("Invalid race date")
        if p["date"] == selected_date:
            selected.append(p)
    return selected
