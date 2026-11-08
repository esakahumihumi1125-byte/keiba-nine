"""Server-only JRDB reader. Never connect this module to the public feed.

No disk writes, logging, automatic retries, or public HTTP endpoints.
Callers must provide a private, authenticated execution/storage environment.
"""
import datetime
import json
import os
import urllib.error
import urllib.parse
import urllib.request


class JRDBError(RuntimeError):
    """Safe error without response bodies, data, or credential-bearing URLs."""


# Only provider-published HTTPS origins may receive member credentials.
# The existing dev origin stays default until JRDB issues a beta account.
ALLOWED_API_BASES = frozenset({
    "https://dev.api.bigtime.world/v1",
    "https://api.bigtime.world/v1",
})


def approved_api_base(raw):
    """Pure check for owner diagnostics; returns no secrets or provider data."""
    return isinstance(raw, str) and (
        raw.strip() or "https://dev.api.bigtime.world/v1"
    ) in ALLOWED_API_BASES


def _api_base_url():
    raw = os.environ.get("JRDB_API_BASE_URL", "")
    if not approved_api_base(raw):
        raise JRDBError("Unapproved JRDB API endpoint configuration")
    return raw.strip() or "https://dev.api.bigtime.world/v1"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch_endpoint(endpoint, parameters):
    """Private memory-only source retrieval for one strict allowlisted request.

    JRDB_PRIVATE_ENABLED is not owner authentication; HTTPS + owner gating is mandatory.
    Historical requests must specify exactly one existing race key, never a
    date range or an unconstrained search.
    """
    if endpoint not in ('tra', 'tky', 'tcy', 'tze', 'tka', 'tpd', 'tse', 'dra', 'dka'):
        raise JRDBError('Unsupported JRDB endpoint')
    if os.environ.get("JRDB_PRIVATE_ENABLED") != "1":
        raise JRDBError("Private JRDB integration is disabled")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        raise JRDBError("JRDB retrieval is disabled in GitHub Actions")
    if not isinstance(parameters, dict):
        raise JRDBError("Invalid JRDB request parameters")
    if endpoint in ('dra', 'dka'):
        racekey = parameters.get("racekey")
        if (set(parameters) != {"racekey"} or not isinstance(racekey, str)
                or len(racekey) != 8 or any(ch not in "0123456789abcdef" for ch in racekey)):
            raise JRDBError("Expected one lowercase eight-character JRDB race key")
    else:
        racedate = parameters.get("racedate")
        if (set(parameters) != {"racedate"} or not isinstance(racedate, str)
                or len(racedate) != 8 or not racedate.isascii() or not racedate.isdigit()):
            raise JRDBError("Expected a YYYYMMDD date")
        try:
            datetime.datetime.strptime(racedate, "%Y%m%d")
        except ValueError:
            raise JRDBError("Invalid calendar date") from None
    # Check endpoint before reading credentials or constructing the request.
    api_base = _api_base_url()
    api_key = os.environ.get("JRDB_API_KEY", "").strip()
    auth_key = os.environ.get("JRDB_AUTH_KEY", "").strip()
    if not api_key or not auth_key:
        raise JRDBError("JRDB credentials are not configured")
    if (any(ord(c) < 33 or ord(c) > 126 for c in auth_key)
            or any(ord(c) < 33 or ord(c) > 126 for c in api_key)):
        raise JRDBError("Invalid credential format")
    url = api_base + "/" + endpoint + "?" + urllib.parse.urlencode({"api_key": api_key})
    request = urllib.request.Request(url, data=json.dumps(parameters).encode(),
        headers={"Content-Type": "application/json", "x-user-key": auth_key}, method="POST")
    try:
        with urllib.request.build_opener(_NoRedirect()).open(request, timeout=30) as response:
            raw = response.read(10_000_001)
        if len(raw) > 10_000_000:
            raise JRDBError("JRDB response exceeds size limit")
        payload = json.loads(raw)
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise JRDBError("JRDB request failed (HTTP %s)" % status) from None
    except (OSError, ValueError, urllib.error.URLError):
        raise JRDBError("JRDB request or response failed") from None
    if not isinstance(payload, dict):
        raise JRDBError("JRDB returned an unsuccessful response")
    result = payload.get("result")
    # Published beta docs currently disagree: the generic contract shows
    # result.status="success", while the /tra endpoint shows integer 200.
    # Support exactly these known success forms, plus the older explicitly
    # successful top-level fixture; never accept an absent success indicator.
    status = result.get("status") if isinstance(result, dict) else None
    top_success = payload.get("success")
    if (not isinstance(result, dict) or payload.get("error") is not None or
            top_success not in (None, True) or
            not (status == "success" or
                 (type(status) is int and status == 200) or
                 (status is None and top_success is True))):
        raise JRDBError("JRDB returned an unsuccessful response")
    # The generic docs echo request.racedate; the endpoint example nests it
    # inside request.parameters. Both must match what was actually sent.
    echoed = payload.get("request")
    if echoed is not None:
        if not isinstance(echoed, dict):
            raise JRDBError("JRDB returned a different race request")
        received = echoed.get("parameters", echoed)
        if (not isinstance(received, dict) or
                any(received.get(key) != value
                    for key, value in parameters.items())):
            raise JRDBError("JRDB returned a different race request")
    uri = result.get("endpoint_uri")
    if uri is not None and uri != "/v1/" + endpoint:
        raise JRDBError("JRDB returned a different endpoint")
    rows = result.get("data")
    if (not isinstance(rows, list) or len(rows) > 50000
            or not all(isinstance(row, dict) for row in rows)):
        raise JRDBError("Unexpected JRDB response format")
    n = result.get("result_count")
    if n is not None and (type(n) is not int or n != len(rows)):
        raise JRDBError("JRDB response count mismatch")
    return rows



def _fetch_day(endpoint, racedate):
    """Private current-week reader; historic endpoints cannot use this."""
    if endpoint not in ('tra', 'tky', 'tcy', 'tze', 'tka', 'tpd', 'tse'):
        raise JRDBError("Unsupported current-day endpoint")
    return _fetch_endpoint(endpoint, {"racedate": racedate})


def fetch_historical_race_program(racekey):
    """One private historical /dra race programme by exact racekey, no range."""
    return _fetch_endpoint('dra', {"racekey": racekey})


def fetch_historical_venue_conditions(racekey):
    """One private historical /dka venue snapshot by exact racekey, no range."""
    return _fetch_endpoint('dka', {'racekey': racekey})


def fetch_race_program(racedate):
    """Private-only programme rows (/tra)."""
    return _fetch_day("tra", racedate)


def fetch_horse_entries(racedate):
    """Private-only horse entry rows (/tky). Do not expose raw records to browsers."""
    return _fetch_day("tky", racedate)

def fetch_training_analysis(racedate):
    """Private-only per-race training indicators (/tcy), no public output."""
    return _fetch_day("tcy", racedate)


def fetch_recent_runs(racedate):
    """Private-only last-five-race rows (/tze), no public output."""
    return _fetch_day("tze", racedate)


def fetch_venue_conditions(racedate):
    """Private-only current meeting/going records (/tka). No public output."""
    return _fetch_day('tka', racedate)


def fetch_prestart_body(racedate):
    """Private-only `/tpd` snapshot; only invoke on owner prestart request.

    Contract: the client deliberately does not fetch or use odds for ranking.
    The caller must redact all body-weight and paddock fields before response.
    """
    return _fetch_day('tpd', racedate)


def fetch_finished_race_results(racedate):
    """Explicit owner-requested current-week /tse results, never official JRA verification.

    The caller MUST redact raw licensed provider rows and label comparisons
    unverified by JRA. No background polling or historical date range.
    """
    return _fetch_day("tse", racedate)
