"""Private owner research notes; no licensed raw rows or provider secrets.

Stores authored brief reasons, explicit evidence coverage, and pending checks.
The API only returns validated presentation fields to its authenticated owner.
"""
import json
import re
from datetime import date

ENV_KEY = "KEIBA_OWNER_RACE_EVIDENCE_JSON"
SCHEMA = "keiba-nine-private-evidence-v1"
VENUES = ("東京", "京都", "福島")
FLAGS = ("officialPastRuns", "publicTrainingChecked", "officialPedigreeChecked",
         "officialEntryCompared", "allHorseTrainingChecked",
         "dayOfScratchesAndTrackChecked")


class EvidenceError(ValueError):
    pass


def _text(value, max_len):
    return (isinstance(value, str) and 1 <= len(value) <= max_len
            and not any(c in value for c in "<>\r\n")
            and not re.search(r"https?://", value, re.IGNORECASE))


def _safe_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"20\d{2}-\d\d-\d\d", value):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def decode_evidence(raw):
    if not isinstance(raw, str) or not 1 <= len(raw) <= 60000:
        raise EvidenceError("Invalid evidence size")
    try:
        doc = json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise EvidenceError("Invalid JSON") from exc
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not _safe_date(doc.get("date")):
        raise EvidenceError("Invalid schema or date")
    source = doc.get("sourceKind")
    if source != "owner-editorial-limited-evidence":
        raise EvidenceError("Invalid evidence source")
    races = doc.get("races")
    if not isinstance(races, list) or len(races) != 36:
        raise EvidenceError("Invalid race count")
    seen = set()
    vetted = []
    for item in races:
        if not isinstance(item, dict):
            raise EvidenceError("Invalid entry")
        track, race = item.get("track"), item.get("race")
        if (track not in VENUES or type(race) is not int or not 1 <= race <= 12
                or (track, race) in seen):
            raise EvidenceError("Invalid race key")
        seen.add((track, race))
        lead = item.get("lead")
        if not isinstance(lead, list) or not 1 <= len(lead) <= 3:
            raise EvidenceError("Invalid lead comments")
        selected = set()
        for x in lead:
            if (not isinstance(x, dict)
                    or type(x.get("number")) is not int
                    or not 1 <= x["number"] <= 18
                    or x["number"] in selected
                    or not _text(x.get("name"), 40)
                    or not _text(x.get("reason"), 160)):
                raise EvidenceError("Invalid horse note")
            selected.add(x["number"])
        for key, limit in (("pace", 180), ("secondThird", 220),
                           ("singles", 220), ("risk", 260)):
            if not _text(item.get(key), limit):
                raise EvidenceError("Missing or invalid basis")
        extra = item.get("verifiedFacts", [])
        if (not isinstance(extra, list) or len(extra) > 5
                or any(not _text(x, 230) for x in extra)):
            raise EvidenceError("Invalid external findings")
        status = item.get("coverage")
        if not isinstance(status, dict) or any(type(status.get(k)) is not bool for k in FLAGS):
            raise EvidenceError("Invalid coverage flags")
        if status["dayOfScratchesAndTrackChecked"] or status["allHorseTrainingChecked"]:
            raise EvidenceError("Cannot claim full prestart or training coverage")
        vetted.append({"track": track, "race": race,
                       "lead": [{"number": x["number"], "name": x["name"],
                                 "reason": x["reason"]} for x in lead],
                       **{k: item[k] for k in ("pace", "secondThird", "singles", "risk")},
                       "verifiedFacts": extra[:],
                       "coverage": {k: status[k] for k in FLAGS}})
    if len(seen) != 36:
        raise EvidenceError("Missing venue race")
    vetted.sort(key=lambda x: (VENUES.index(x["track"]), x["race"]))
    return {"schema": SCHEMA, "date": doc["date"], "races": vetted,
            "sourceKind": source, "finalVerified": False,
            "predictionRevised": False}
