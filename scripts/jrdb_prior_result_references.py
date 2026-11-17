"""Read-only /tky previous-result reference count, shared by diagnosis and research.

A resultkey is only a source reference, never an authenticated completed race.
Published JRDB /tky examples also use paired 8-digit race-key placeholders.
Invalid or missing fields return None (unknown), NOT zero previous starts.
No network, licensed row leakage, prediction or persistence.
"""
import re

from jrdb_evidence_readiness import _valid_date

_RESULT_KEY = re.compile(r"[0-9]{16}\Z", re.ASCII)
_RACE_KEY = re.compile(r"[0-9]{8}\Z", re.ASCII)


def prior_result_reference_count(entry, day):
    """Count distinct dated references from all FIVE published /tky slots."""
    if not isinstance(entry, dict) or not _valid_date(day):
        return None
    fields = ["lastrace_resultkey" + str(i) for i in range(1, 6)]
    if not all(key in entry for key in fields):
        return None
    seen = set()
    for i, field in enumerate(fields, 1):
        value = entry[field]
        if value in (None, "", "0000000000000000", "00000000"):
            continue
        if type(value) is not str:
            return None
        if _RACE_KEY.fullmatch(value):
            if entry.get("lastrace_racekey" + str(i)) != value:
                return None
            continue
        if not _RESULT_KEY.fullmatch(value) or value in seen:
            return None
        past = value[-8:]
        if not _valid_date(past) or past >= day:
            return None
        seen.add(value)
    return len(seen)
