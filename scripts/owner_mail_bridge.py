"""Read only an owner's minimally summarized Gmail prestart notes from Apps Script.

The private preview never receives raw paid emails, proprietary rankings,
odds, provider metrics, or the Apps Script shared secret in an HTTP response.
Transport only runs when explicitly configured; it changes no forecasts or bets.
"""
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from owner_live_notes import parse_live_notes, LiveNoteError

BRIDGE_SCHEMA = "keiba-nine-mail-bridge-v1"
BRIDGE_URL = "KEIBA_MAIL_BRIDGE_URL"
BRIDGE_TOKEN = "KEIBA_MAIL_BRIDGE_TOKEN"
TRACKS = ("東京", "京都", "福島")
_ALLOWED_URL = re.compile(r"https://script\.google\.com/macros/s/[A-Za-z0-9_-]{20,}/exec")
_TIME = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")
_DATE = re.compile(r"20\d{2}-\d{2}-\d{2}")


class BridgeUnavailable(Exception):
    pass


def bridge_enabled(settings):
    url, token = settings.get(BRIDGE_URL, ""), settings.get(BRIDGE_TOKEN, "")
    return (isinstance(url, str) and _ALLOWED_URL.fullmatch(url) is not None
            and isinstance(token, str) and 32 <= len(token) <= 256
            and re.fullmatch("[A-Za-z0-9_-]+", token) is not None)


def _minute(value):
    h, m = map(int, value.split(":"))
    return h * 60 + m


def validate_bridge_feed(feed, expected_date, race_times):
    """Reject records for the wrong race, date, or late-arriving mail.

    race_times is exclusively derived from the owner-authenticated pre-day
    forecast. A scripted email must not invent additional races/start times.
    """
    if not isinstance(feed, dict) or feed.get("schema") != BRIDGE_SCHEMA:
        raise BridgeUnavailable("Invalid bridge reply")
    if (feed.get("date") != expected_date or not isinstance(expected_date, str)
            or not _DATE.fullmatch(expected_date)):
        raise BridgeUnavailable("The remote day does not match")
    entries = feed.get("races")
    if not isinstance(entries, list) or len(entries) > 36:
        raise BridgeUnavailable("Invalid bridge race count")
    checked = []
    seen = set()
    for r in entries:
        if not isinstance(r, dict):
            raise BridgeUnavailable("Invalid record")
        track, race = r.get("track"), r.get("race")
        if (track not in TRACKS or type(race) is not int or not 1 <= race <= 12
                or (track, race) in seen):
            raise BridgeUnavailable("Invalid race reference")
        seen.add((track, race))
        start, observed = r.get("time"), r.get("observedAt")
        if (not isinstance(start, str) or not _TIME.fullmatch(start)
                or not isinstance(observed, str) or not _TIME.fullmatch(observed)
                or race_times.get((track, race)) != start
                or not 0 <= _minute(observed) <= _minute(start) - 2):
            raise BridgeUnavailable("Wrong start or after-start mail")
        going = r.get("ground")
        if going not in ("良", "稍重", "重", "不良", "未確認"):
            raise BridgeUnavailable("Invalid going")
        picks = r.get("paddock")
        if (not isinstance(picks, list) or not 1 <= len(picks) <= 5
                or any(type(n) is not int or not 1 <= n <= 18 for n in picks)
                or len(set(picks)) != len(picks)):
            raise BridgeUnavailable("Invalid top numbers")
        note = ("Gmailの発走前メールから要点のみ抽出。予想・馬券は変更しません。"
                "JRA公式の取消・馬場・発走時刻との最終照合が必要。")
        checked.append({"track": track, "race": race, "time": start,
                        "observedAt": observed, "ground": going,
                        "paddock": picks, "note": note})
    if not checked:
        return None
    payload = {"schema": "keiba-nine-owner-live-notes-v1",
               "date": expected_date, "races": checked}
    try:
        return parse_live_notes(json.dumps(payload, ensure_ascii=False))
    except LiveNoteError as exc:
        raise BridgeUnavailable("Rejected remote brief") from exc


def fetch_mail_brief(settings, expected_date, race_times, opener=urlopen):
    """Make a short server-only POST. The browser never receives the token."""
    if not bridge_enabled(settings):
        return None
    url = settings[BRIDGE_URL]
    token = settings[BRIDGE_TOKEN]
    request = Request(
        url,
        data=json.dumps({"action": "read", "token": token,
                         "date": expected_date}).encode("utf-8"),
        headers={"Content-Type": "text/plain; charset=utf-8",
                 "Accept": "application/json"},
        method="POST",
    )
    try:
        with opener(request, timeout=5) as response:
            raw = response.read(12001)
        if len(raw) > 12000:
            raise BridgeUnavailable("Remote payload too large")
        doc = json.loads(raw.decode("utf-8"))
        return validate_bridge_feed(doc, expected_date, race_times)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError,
            UnicodeError) as exc:
        raise BridgeUnavailable("Remote source unavailable") from exc


def load_owner_live_notes(settings, *, today=None, opener=urlopen):
    """Merge today-only manual and remote briefs, latest prestart mail wins."""
    today = today or datetime.now(ZoneInfo("Asia/Tokyo")).date().isoformat()
    configured = bridge_enabled(settings)
    current = None
    raw = settings.get("KEIBA_OWNER_LIVE_NOTES_JSON", "")
    if raw:
        try:
            parsed = parse_live_notes(raw)
        except LiveNoteError as exc:
            raise BridgeUnavailable("Stored notes invalid") from exc
        if parsed["date"] == today or not configured:
            current = parsed
    status = "未設定"
    if configured:
        try:
            from owner_forecast_delivery import (decode_plain_owner_snapshot,
                                                 decode_forecast, ENV_KEY)
            raw_plain = settings.get("KEIBA_OWNER_FORECAST_JSON", "")
            raw_packed = settings.get(ENV_KEY, "")
            forecast = (decode_plain_owner_snapshot(raw_plain) if raw_plain
                        else decode_forecast(raw_packed) if raw_packed else None)
            if not forecast or forecast["date"] != today:
                raise BridgeUnavailable("No matching race calendar")
            times = {(r["track"], r["race"]): r["time"] for r in forecast["races"]}
            remote = fetch_mail_brief(settings, today, times, opener=opener)
            if remote:
                merged = {(r["track"], r["race"]): r for r in (
                    current["races"] if current else [])}
                for race in remote["races"]:
                    key = race["track"], race["race"]
                    if key not in merged or race["observedAt"] >= merged[key]["observedAt"]:
                        merged[key] = race
                current = parse_live_notes(json.dumps({
                    "schema": "keiba-nine-owner-live-notes-v1", "date": today,
                    "races": list(merged.values())}, ensure_ascii=False))
            status = "接続済み"
        except (BridgeUnavailable, ValueError):
            status = "要確認"
    return current, {"configured": configured, "status": status,
                     "autoChangesToPicks": False}
