"""Offline-first bounded owner-only historical evidence preparation.

This module has NO JRDB imports or network configuration. Explicit injected
callables are the only way to retrieve histories. Never use it in GitHub Pages,
public actions, public feeds or any unauthenticated route. Licensed source rows
remain local to the caller; only redacted race totals are returned.

The research output is not a real-data suitability grade or wager.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import (
    audit_evidence_coverage, HORSE_ID, NUMBER, KEY, _valid_date
)
from jrdb_program_preview import normalize_program_rows, ProgrammeFormatError
from jrdb_going_history import (
    build_going_history_observations, summarize_going_history_observations
)

VERSION = "bounded-history-1"
MAX_LOOKUPS_PER_RUN = 12
DEFAULT_LOOKUPS_PER_RUN = 8


class HistoryFetchError(ValueError):
    """Safe generic error: no keys, credentials or source response bodies."""


def _verify_limit(value):
    if type(value) is not int or not 1 <= value <= MAX_LOOKUPS_PER_RUN:
        raise HistoryFetchError("History budget must be between 1 and 12")
    return value


def plan_bounded_history(programme, entries, previous, requested_date,
                         limit=DEFAULT_LOOKUPS_PER_RUN):
    """Private plan: newest referenced racekeys first, one per unique past race.

    No date-range queries, no lookups by arbitrary input, no implicit retries.
    This plan contains private racekeys and MUST NOT be sent to browsers/logs.
    """
    _verify_limit(limit)
    audit_evidence_coverage(programme, entries, [], previous, requested_date)
    by_number = {(r["racekey"], r["horse_number"]) for r in entries}
    by_id = {(r["racekey"], r["horse_id"]): r["horse_number"]
             for r in entries if r.get("horse_id")}
    current_keys = {r["racekey"] for r in programme}
    referenced = {}
    for row in previous:
        current = row["racekey"]
        number = row.get("horse_number")
        hid = row.get("horse_id")
        matched_number = (isinstance(number, str) and NUMBER.fullmatch(number)
                          and (current, number) in by_number)
        matched_id = (isinstance(hid, str) and HORSE_ID.fullmatch(hid)
                      and (current, hid) in by_id)
        if not (matched_number or matched_id):
            continue  # Anonymous source rows are not a basis for paid lookups.
        for i in range(1, 6):
            prefix = f"race_back_{i}_"
            date, racekey = row.get(prefix + "racedate"), row.get(prefix + "racekey")
            if not date and not racekey:
                continue
            if not _valid_date(date) or date >= requested_date:
                raise CoverageError("Previous race date invalid")
            if racekey is None or racekey == "":
                continue  # Historical key unavailable; do not guess.
            if (not isinstance(racekey, str) or not KEY.fullmatch(racekey)
                    or racekey in current_keys):
                raise CoverageError("Invalid historical racekey")
            if racekey in referenced and referenced[racekey] != date:
                raise CoverageError("Conflicting dates for historical racekey")
            referenced[racekey] = date
    ordered = sorted(referenced.items(), key=lambda item: (item[1], item[0]), reverse=True)
    return {
        "privateSelected": tuple(ordered[:limit]),
        "referencedCount": len(ordered),
        "selectedCount": min(len(ordered), limit),
        "deferredCount": max(0, len(ordered) - limit),
        "maxDraCalls": min(len(ordered), limit),
        "maxDkaCalls": min(len(ordered), limit),
        "historyComplete": len(ordered) <= limit,
        "version": VERSION,
    }


def _one_programme(rows, key, date):
    if not isinstance(rows, list) or len(rows) > 1:
        raise HistoryFetchError("Historical programme response has unexpected shape")
    if not rows:
        return None
    if (not isinstance(rows[0], dict) or rows[0].get("racekey") != key
            or rows[0].get("racedate") != date):
        raise HistoryFetchError("Historical programme identifier mismatch")
    try:
        normalize_program_rows(rows, date)
    except ProgrammeFormatError:
        raise HistoryFetchError("Historical programme validation failed") from None
    return rows[0]


def _one_going(rows, key, date):
    if not isinstance(rows, list) or len(rows) > 1:
        raise HistoryFetchError("Historical going response has unexpected shape")
    if not rows:
        return None
    if (not isinstance(rows[0], dict) or rows[0].get("holdingkey") != key[:6]
            or rows[0].get("racedate") != date):
        raise HistoryFetchError("Historical going identifier mismatch")
    return rows[0]


def run_bounded_history_audit(programme, entries, previous,
                              current_conditions, requested_date,
                              *, fetch_dra, fetch_dka,
                              limit=DEFAULT_LOOKUPS_PER_RUN):
    """Explicit, bounded private lookup with redacted response only.

    The caller supplies owner-approved *private* fetch functions after securing
    its server and credentials. This module is never a scheduled job.
    On any malformed/provider-error response, discard all partial output.
    A missing row remains unknown and is never used as a negative signal.
    """
    if not callable(fetch_dra) or not callable(fetch_dka):
        raise HistoryFetchError("Private source functions are required")
    plan = plan_bounded_history(programme, entries, previous, requested_date, limit)
    historical, conditions = [], []
    seen_holdings = set()
    dra_calls = dka_calls = missing = 0
    for key, date in plan["privateSelected"]:
        try:
            dra_calls += 1
            past = _one_programme(fetch_dra(key), key, date)
        except HistoryFetchError:
            raise
        except Exception:
            raise HistoryFetchError("Private historical programme lookup failed") from None
        if past is None:
            missing += 1
            continue
        historical.append(past)
        holding = key[:6], date
        if holding in seen_holdings:
            continue
        seen_holdings.add(holding)
        try:
            dka_calls += 1
            old_going = _one_going(fetch_dka(key), key, date)
        except HistoryFetchError:
            raise
        except Exception:
            raise HistoryFetchError("Private historical going lookup failed") from None
        if old_going is not None:
            conditions.append(old_going)
    # Both auditors recheck all source-identity joins. Provider rows never
    # escape the scope of this function as a published response.
    try:
        observations = build_going_history_observations(
            programme, entries, previous, historical, conditions,
            current_conditions, requested_date
        )
        safe_summary = summarize_going_history_observations(observations)
    except (CoverageError, ValueError, KeyError, TypeError):
        raise HistoryFetchError("Private historical evidence validation failed") from None
    return {
        "version": VERSION,
        "referencedPastRaces": plan["referencedCount"],
        "selectedPastRaces": plan["selectedCount"],
        "deferredPastRaces": plan["deferredCount"],
        "unavailablePastProgrammes": missing,
        "draCalls": dra_calls,
        "dkaCalls": dka_calls,
        "maxTotalCalls": 2 * limit,
        "historyComplete": plan["historyComplete"] and missing == 0,
        "goingSummary": safe_summary,
        "predictionReady": False,
        "goingSuitabilityAssessed": False,
        "note": ("本人専用の過去資料照合。取得上限内で参照できた履歴の集計のみ。"
                 "残りの過去走・未提供馬場は不明。適性S/A/Bや馬券は作成していません。"),
    }
