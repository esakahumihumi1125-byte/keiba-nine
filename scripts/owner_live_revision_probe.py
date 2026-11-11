"""Read-only GitHub Actions probe of public code SHA on the private Render host.

This probe makes only GET requests to a fixed, public revision endpoint;
it never logs in, queries JRDB, reads private races, or transmits credentials.
A matching code SHA does NOT prove private provider data, prediction, or JRA.
"""
import json
import os
import re
import sys
import time
from urllib import error, request

URL = "https://keiba-nine-owner-jrdb.onrender.com/live-revision"
VERSION = "owner-live-revision-1"
FIELDS = frozenset((
    "version", "renderCommit", "revisionOnly", "jrdbConnectionVerified",
    "forecastExecutionVerified", "ownerDataIncluded",
))


def verify_live_revision(expected_sha, *, fetch=None, sleep=None, tries=12):
    """Return (verified, reason); never return remote response content."""
    if type(expected_sha) is not str or not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("Expected GitHub commit must be a 40-character SHA")
    if type(tries) is not int or not 1 <= tries <= 16:
        raise ValueError("Invalid bounded probe tries")
    opener = request.urlopen if fetch is None else fetch
    sleeper = time.sleep if sleep is None else sleep
    reason = "unreachable"
    for i in range(tries):
        try:
            req = request.Request(URL, headers={
                "Accept": "application/json",
                "Cache-Control": "no-cache",
                "User-Agent": "keiba-nine-safe-live-revision-check",
            }, method="GET")
            with opener(req, timeout=12) as response:
                if response.status != 200:
                    reason = "bad_http_status"
                else:
                    raw = response.read(1025)
                    if len(raw) > 1024:
                        reason = "invalid_contract"
                    else:
                        obj = json.loads(raw)
                        if (type(obj) is not dict or set(obj) != FIELDS
                                or obj.get("version") != VERSION
                                or obj.get("revisionOnly") is not True
                                or obj.get("jrdbConnectionVerified") is not False
                                or obj.get("forecastExecutionVerified") is not False
                                or obj.get("ownerDataIncluded") is not False
                                or not isinstance(obj.get("renderCommit"), str)
                                or not re.fullmatch(
                                    r"(?:[0-9a-f]{12}|not-reported)",
                                    obj["renderCommit"])):
                            reason = "invalid_contract"
                        elif obj["renderCommit"] == expected_sha[:12]:
                            return True, "sha_verified"
                        else:
                            reason = "live_sha_mismatch"
        except (error.HTTPError, error.URLError, TimeoutError,
                ConnectionError, OSError):
            reason = "unreachable"
        except (ValueError, TypeError, UnicodeError):
            reason = "invalid_contract"
        if i + 1 < tries:
            sleeper(12)
    return False, reason


def main():
    expected_sha = os.environ.get("EXPECTED_SHA", "")
    try:
        ok, reason = verify_live_revision(expected_sha)
    except ValueError:
        print("Live Render code: EXPECTED_SHA invalid")
        return 2
    if ok:
        print("Live Render code: VERIFIED - SHA matches GitHub main")
        print("JRDB data, official JRA, and real forecast: NOT VERIFIED")
        return 0
    print("Live Render code: NOT VERIFIED (" + reason + ")")
    print("JRDB data, official JRA, and real forecast: NOT VERIFIED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
