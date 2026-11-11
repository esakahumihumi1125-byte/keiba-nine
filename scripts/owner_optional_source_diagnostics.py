"""Tiny, non-sensitive diagnostics for optional owner JRDB source handling.

Return stable, coarse category strings ONLY. The caller may log these but
must never emit exception messages, race keys, horse identifiers, dates,
paid source content, provider response bodies, request URLs, or credentials.
No API calls, persistence, ranking, or receipt mutations.
"""
from jrdb_coverage import CoverageError
from jrdb_private import JRDBError
from jrdb_race_context import RaceContextError

CONTEXT_MESSAGES = {
    "Invalid condition timestamp": "condition_timestamp_format",
    "Invalid going code": "going_code",
    "Invalid holding key": "holding_key",
    "Venue/date mismatch": "venue_date_mismatch",
    "Duplicate venue condition": "duplicate_venue",
    "Invalid venue row": "venue_row_shape",
    "Invalid venue collection": "venue_collection_shape",
    "Invalid surface": "course_surface",
    "Invalid distance": "course_distance",
    "Invalid turn direction": "course_turn",
    "Duplicate race": "duplicate_race",
    "Invalid track or race": "race_coordinate",
    "Invalid programme race": "programme_race_shape",
    "Invalid programme": "programme_shape",
    "Invalid target date": "target_date",
    "Invalid calendar date": "target_date",
}


def safe_material_error_code(exc):
    """Only type-based, fixed codes; never the error string."""
    if type(exc) is CoverageError:
        return "source_coverage"
    if type(exc) is ValueError:
        return "source_value"
    if type(exc) is TypeError:
        return "source_type"
    if type(exc) is KeyError:
        return "source_missing_field"
    return "source_other"


def safe_context_error_code(exc):
    """Whitelist known context errors and provider HTTP categories."""
    if type(exc) is JRDBError:
        raw = str(exc)  # inspected in memory only; never serialized/logged
        if raw == "JRDB request failed (HTTP 401)":
            return "provider_auth"
        if raw == "JRDB request failed (HTTP 403)":
            return "provider_entitlement"
        if raw == "JRDB request failed (HTTP 429)":
            return "provider_rate_limit"
        return "provider_other"
    if type(exc) is RaceContextError:
        # Exact allowlisted match avoids logging unknown provider details.
        return CONTEXT_MESSAGES.get(str(exc), "context_schema_other")
    if type(exc) is KeyError:
        return "context_missing_field"
    if type(exc) is TypeError:
        return "context_type"
    if type(exc) is ValueError:
        return "context_value"
    return "context_other"
