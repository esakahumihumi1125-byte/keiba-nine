"""Strict, stateless one-factor operator observation intake for private preview.

Only owner-selected enumerations are accepted. No paid data, free-text,
betting, grades, real-source authentication, storage or provider calls.
Acknowledgement never means independent JRA verification.
"""
from datetime import datetime
from evaluation_policy import FACTORS, timestamp
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS

VERSION = "operator-factor-intake-1"
TRACK_NAMES = frozenset(TRACKS.values())
SOURCES = frozenset({"jra_page_viewed_by_operator", "operator_observation", "none"})
FACTORS_SET = frozenset(FACTORS)
NUMBERS = frozenset(f"{n:02d}" for n in range(1, 19))
ALLOWED = frozenset({
    "recordType", "date", "track", "race", "horseNumber",
    "factor", "state", "source",
})


def validate_operator_factor_note(payload, received_at):
    """Return only owner-facing acknowledgement, never an assessment result."""
    if not isinstance(payload, dict) or set(payload) != ALLOWED:
        raise ValueError("Expected one enumerated observation")
    date = payload["date"]
    if not _valid_date(date):
        raise ValueError("Invalid date")
    if (payload["recordType"] != "operator_factor_note"
            or type(payload["track"]) is not str or payload["track"] not in TRACK_NAMES
            or type(payload["race"]) is not int or not 1 <= payload["race"] <= 12
            or type(payload["horseNumber"]) is not str
            or payload["horseNumber"] not in NUMBERS
            or type(payload["factor"]) is not str
            or payload["factor"] not in FACTORS_SET
            or type(payload["state"]) is not str
            or payload["state"] not in ("noted", "unknown")
            or type(payload["source"]) is not str
            or payload["source"] not in SOURCES):
        raise ValueError("Invalid operator note selection")
    if ((payload["state"] == "noted" and payload["source"] == "none")
            or (payload["state"] == "unknown" and payload["source"] != "none")):
        raise ValueError("Unknown observations must not claim a source")
    checked = timestamp(received_at)
    if checked > datetime.now(checked.tzinfo).replace(microsecond=999999):
        raise ValueError("Receipt timestamp cannot be in the future")
    # Server receipt is not evidence publication time, official validation, or
    # proof of a note being made before the race started.
    return {
        "version": VERSION, "recordType": "operator_factor_note",
        "track": payload["track"], "race": payload["race"], "date": date,
        "factor": payload["factor"], "state": payload["state"],
        "sourceKind": payload["source"],
        "receivedAt": checked.isoformat(),
        "submittedByOperator": True,
        "saved": False, "sourceAuthenticated": False,
        "verifiedBeforePostTime": False,
        "jraOfficialFinalVerification": False,
        "grade": "未評価", "gradedFactorCount": 0,
        "predictionReady": False, "bettingReady": False,
        "note": ("本人の選択入力を形式確認したのみ。記録保存はしません。"
                 "JRA公式の独立検証やS/A/B/C評価、実戦予想は未実施。"),
    }
