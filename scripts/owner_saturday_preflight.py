"""Owner-authenticated, zero-provider-call preflight for private Saturday use.

Reports configuration PRESENCE only, not successful JRDB authorization,
real race feeds, official JRA agreement, the Render revision, or forecasts.
Do not expose raw configuration, credentials, provider URLs, paid rows,
horse IDs, ticket data, purchase history, or forecasts. No side effects.
"""
from datetime import date, datetime, timedelta, timezone

from jrdb_private import approved_api_base
from jrdb_evidence_readiness import _valid_date

VERSION = "owner-saturday-config-preflight-1"
JST = timezone(timedelta(hours=9))


def owner_saturday_config_preflight(settings, day, *, server_now):
    if (not isinstance(settings, dict)
            or type(day) is not str or not _valid_date(day)):
        raise ValueError("Invalid owner preflight request")
    if (not isinstance(server_now, datetime)
            or server_now.tzinfo is None or server_now.utcoffset() is None):
        raise ValueError("Timezone-aware server clock required")
    now = server_now.astimezone(JST)
    selected = date(int(day[:4]), int(day[4:6]), int(day[6:8]))
    private_mode = (
        settings.get("KEIBA_RENDER_PRIVATE_ONLY") == "1"
        and settings.get("KEIBA_RENDER_PREVIEW_ONLY") != "1"
        and settings.get("JRDB_PRIVATE_ENABLED") == "1"
        and settings.get("GITHUB_ACTIONS") != "true"
    )
    secrets_present = all(
        isinstance(settings.get(key), str) and bool(settings.get(key))
        for key in ("JRDB_API_KEY", "JRDB_AUTH_KEY")
    )
    approved_host = approved_api_base(settings.get("JRDB_API_BASE_URL", ""))
    configured = private_mode and secrets_present and approved_host
    return {
        "version": VERSION,
        "date": day,
        "serverDate": now.strftime("%Y%m%d"),
        "serverTimeJst": now.strftime("%H:%M"),
        "serverTimeZone": "Asia/Tokyo",
        "privateServiceConfigured": bool(private_mode),
        "jrdbCredentialsPresent": bool(secrets_present),
        "approvedProviderHostConfigured": bool(approved_host),
        "configurationReady": bool(configured),
        "selectedDateAlreadyPast": selected < now.date(),
        "selectedDateIsWeekend": selected.weekday() in (5, 6),
        "serverClockIndependentlyVerified": False,
        "providerConnectionVerified": False,
        "liveRaceFeedVerified": False,
        "officialJraVerified": False,
        "formalTenFactorsReady": False,
        "archivePersistenceVerified": False,
        "sourceCallsMade": 0,
        "researchOnly": True,
        "privateOwnerOnly": True,
        "bettingReady": False,
        "existingReceiptsChanged": False,
        "existingRoiChanged": False,
        "note": "設定有無だけの無料事前診断。JRDBの接続・当日配信・JRA公式・10項目採点は未確認。",
    }
