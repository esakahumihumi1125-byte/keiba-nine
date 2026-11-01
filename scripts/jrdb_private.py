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


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch_day(endpoint, racedate):
    """Return private source rows in memory for one strictly allowlisted endpoint.

    JRDB_PRIVATE_ENABLED is not owner authentication; HTTPS + owner gating is mandatory.
    """
    if endpoint not in ('tra', 'tky', 'tcy', 'tze'):
        raise JRDBError('Unsupported JRDB endpoint')
    if os.environ.get("JRDB_PRIVATE_ENABLED") != "1":
        raise JRDBError("Private JRDB integration is disabled")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        raise JRDBError("JRDB retrieval is disabled in GitHub Actions")
    if not isinstance(racedate, str) or len(racedate) != 8 or not racedate.isascii() or not racedate.isdigit():
        raise JRDBError("Expected a YYYYMMDD date")
    try:
        datetime.datetime.strptime(racedate, "%Y%m%d")
    except ValueError:
        raise JRDBError("Invalid calendar date") from None
    api_key = os.environ.get("JRDB_API_KEY", "").strip()
    auth_key = os.environ.get("JRDB_AUTH_KEY", "").strip()
    if not api_key or not auth_key:
        raise JRDBError("JRDB credentials are not configured")
    if any(ord(c) < 32 or ord(c) > 126 for c in auth_key):
        raise JRDBError("Invalid credential format")
    url = "https://dev.api.bigtime.world/v1/" + endpoint + "?" + urllib.parse.urlencode({"api_key": api_key})
    request = urllib.request.Request(url, data=json.dumps({"racedate": racedate}).encode(),
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
    if not isinstance(payload, dict) or payload.get("success") is False:
        raise JRDBError("JRDB returned an unsuccessful response")
    result = payload.get("result")
    rows = result.get("data") if isinstance(result, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise JRDBError("Unexpected JRDB response format")
    return rows


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
