"""Validate minimal authored, owner-only prestart notes.

No JRDB source body, paid per-horse metrics, odds, credentials, or
provider-authenticated assertions may be sent to the browser.
"""
import json
import re
from datetime import date

ENV_KEY = "KEIBA_OWNER_LIVE_NOTES_JSON"
SCHEMA = "keiba-nine-owner-live-notes-v1"
TRACKS = frozenset(("東京", "京都", "福島", "札幌", "函館",
                    "新潟", "中山", "中京", "阪神", "小倉"))
GOINGS = frozenset(("良", "稍重", "重", "不良", "未確認"))
class LiveNoteError(ValueError):
    pass


def parse_live_notes(value):
    if not isinstance(value, str) or len(value) > 5000:
        raise LiveNoteError("Live notes too large")
    try:
        data = json.loads(value)
    except (ValueError, TypeError) as exc:
        raise LiveNoteError("Invalid live note JSON") from exc
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise LiveNoteError("Invalid live note schema")
    raw_date = data.get("date")
    if not isinstance(raw_date, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", raw_date):
        raise LiveNoteError("Invalid live note date")
    try:
        if date.fromisoformat(raw_date).isoformat() != raw_date:
            raise LiveNoteError("Invalid date")
    except ValueError as exc:
        raise LiveNoteError("Invalid date") from exc
    races = data.get("races")
    if not isinstance(races, list) or not 1 <= len(races) <= 36:
        raise LiveNoteError("Invalid notes list")
    keys = set()
    out = []
    for r in races:
        if not isinstance(r, dict):
            raise LiveNoteError("Invalid note")
        track, race = r.get("track"), r.get("race")
        if track not in TRACKS or type(race) is not int or not 1 <= race <= 12:
            raise LiveNoteError("Invalid identity")
        if (track, race) in keys:
            raise LiveNoteError("Duplicate note")
        keys.add((track, race))
        stamp, start = r.get("observedAt"), r.get("time")
        if any(not isinstance(v, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", v)
               for v in (stamp, start)):
            raise LiveNoteError("Invalid clock")
        ground, picks = r.get("ground"), r.get("paddock")
        if ground not in GOINGS or not isinstance(picks, list) or not 1 <= len(picks) <= 5:
            raise LiveNoteError("Invalid observation")
        if (any(type(n) is not int or n < 1 or n > 18 for n in picks) or
                len(set(picks)) != len(picks)):
            raise LiveNoteError("Invalid horse numbers")
        note = r.get("note")
        if (not isinstance(note, str) or not 1 <= len(note) <= 140 or
                any(c in note for c in "<>\r\n") or "http" in note.lower()):
            raise LiveNoteError("Invalid authored summary")
        out.append({"track":track, "race":race, "time":start,
                    "observedAt":stamp, "ground":ground,
                    "paddock":picks[:], "note":note})
    out.sort(key=lambda r:(("東京","京都","福島","札幌","函館","新潟","中山","中京","阪神","小倉").index(r["track"]),r["race"]))
    return {"date":raw_date, "races":out, "sourceKind":"owner-edited-live-brief",
            "officialJraVerified":False, "predictionReady":False}
