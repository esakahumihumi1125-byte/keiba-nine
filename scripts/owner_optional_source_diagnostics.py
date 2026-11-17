"""Tiny, non-sensitive diagnostics for optional owner JRDB source handling.

Return stable, coarse category strings ONLY. The caller may log these but
must never emit exception messages, race keys, horse identifiers, dates,
paid source content, provider response bodies, request URLs, or credentials.
No API calls, persistence, ranking, or receipt mutations.
"""
from jrdb_coverage import CoverageError
from jrdb_private import JRDBError
from jrdb_race_context import RaceContextError

# Fixed categories may be logged or shown to the owner, but NEVER the
# provider exception string: it could contain paid source records or secrets.
# The current /tka log said provider_other for every failed read; distinguish
# exact published HTTP and local failure classes without another API call.
PROVIDER_MESSAGES = {
    "JRDB request failed (HTTP 400)": "provider_request_rejected",
    "JRDB request failed (HTTP 401)": "provider_auth",
    "JRDB request failed (HTTP 403)": "provider_entitlement",
    "JRDB request failed (HTTP 404)": "provider_endpoint_missing",
    "JRDB request failed (HTTP 408)": "provider_timeout",
    "JRDB request failed (HTTP 422)": "provider_request_rejected",
    "JRDB request failed (HTTP 429)": "provider_rate_limit",
    "JRDB request failed (HTTP 500)": "provider_server_error",
    "JRDB request failed (HTTP 502)": "provider_server_error",
    "JRDB request failed (HTTP 503)": "provider_server_error",
    "JRDB request failed (HTTP 504)": "provider_server_error",
    "JRDB request or response failed": "provider_transport_or_decode",
    "JRDB response exceeds size limit": "provider_response_too_large",
    "JRDB returned an unsuccessful response": "provider_response_contract",
    "Unexpected JRDB response format": "provider_response_contract",
    "JRDB response count mismatch": "provider_response_contract",
    "JRDB returned a different endpoint": "provider_response_contract",
    "JRDB returned a different race request": "provider_response_contract",
    "JRDB credentials are not configured": "provider_credentials_missing",
    "Invalid credential format": "provider_credentials_invalid",
    "Unapproved JRDB API endpoint configuration": "provider_base_unapproved",
    "Private JRDB integration is disabled": "provider_disabled",
    "JRDB retrieval is disabled in GitHub Actions": "provider_disabled",
}
CONTEXT_FAILURE_CODES = frozenset((
    *PROVIDER_MESSAGES.values(), "provider_other",
    *(
        "condition_timestamp_format", "going_code", "holding_key",
        "venue_date_mismatch", "duplicate_venue", "venue_row_shape",
        "venue_collection_shape", "course_surface", "course_distance",
        "course_turn", "duplicate_race", "race_coordinate",
        "programme_race_shape", "programme_shape", "target_date",
        "context_schema_other", "context_missing_field", "context_type",
        "context_value", "context_other",
    ),
))

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
        # Exact whitelist only. Unknown errors, including a provider body
        # appended to an otherwise familiar phrase, remain generic.
        return PROVIDER_MESSAGES.get(str(exc), "provider_other")
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
