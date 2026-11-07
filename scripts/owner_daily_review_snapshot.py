"""Strict validation of private, provisional retrospective statistics.

Never treat these figures as JRA-certified or as real purchases.
Never copy personal review details into the public repository.
"""
import json
import re
from datetime import date

ENV_KEY = "KEIBA_OWNER_DAILY_REVIEW_JSON"
SCHEMA = "keiba-nine-private-review-v1"
VENUES = ("東京", "京都", "福島")


class ReviewError(ValueError):
    pass


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _safe_text(value, max_length):
    return (isinstance(value, str) and 1 <= len(value) <= max_length
            and not any(ch in value for ch in "<>\r\n")
            and "http" not in value.lower())


def decode_review(value):
    if not isinstance(value, str) or len(value) > 12000:
        raise ReviewError("Invalid review size")
    try:
        raw = json.loads(value)
    except (ValueError, TypeError) as exc:
        raise ReviewError("Invalid review JSON") from exc
    if (not isinstance(raw, dict) or raw.get("schema") != SCHEMA or
            raw.get("sourceKind") != "owner-retrospective-provisional" or
            raw.get("actualPurchase") is not False or
            raw.get("jraAllVerified") is not False or
            raw.get("complete") is not False):
        raise ReviewError("Unsupported claim or schema")
    day = raw.get("date")
    if not isinstance(day, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", day):
        raise ReviewError("Invalid date")
    try:
        if date.fromisoformat(day).isoformat() != day:
            raise ReviewError("Invalid date")
    except ValueError as exc:
        raise ReviewError("Invalid date") from exc
    count = raw.get("racesReviewed")
    if not _integer(count, 1, 35) or raw.get("unit") != 100 or raw.get("pointsPerRace") != 30:
        raise ReviewError("Invalid retrospective unit")
    venue_rows = raw.get("venues")
    if not isinstance(venue_rows, list) or len(venue_rows) != 3:
        raise ReviewError("Invalid venue collection")
    seen, venues = set(), []
    for row in venue_rows:
        if not isinstance(row, dict):
            raise ReviewError("Invalid venue")
        name = row.get("name")
        n, first, hit, second, payout = (row.get(k) for k in
            ("racesReviewed", "firstCandidateHits", "trifectaHits", "secondCandidateHits", "payout"))
        if name not in VENUES or name in seen or not _integer(n, 1, 12) or not _integer(first, 0, n) or not _integer(hit, 0, n) or not _integer(second, 0, n) or not _integer(payout, 0, 10**8):
            raise ReviewError("Invalid venue figures")
        seen.add(name)
        venues.append({"name":name, "racesReviewed":n, "firstCandidateHits":first,
                       "secondCandidateHits":second,"trifectaHits":hit, "payout":payout})
    if seen != set(VENUES) or sum(r["racesReviewed"] for r in venues) != count:
        raise ReviewError("Venue count mismatch")
    hits = raw.get("hits")
    if not isinstance(hits, list) or len(hits) != sum(v["trifectaHits"] for v in venues):
        raise ReviewError("Hit count mismatch")
    safe_hits, identifiers = [], set()
    for row in hits:
        if not isinstance(row, dict) or row.get("track") not in VENUES or not _integer(row.get("race"), 1, 12):
            raise ReviewError("Invalid hit identity")
        track, race = row["track"], row["race"]
        nums, payout = row.get("combination"), row.get("payout")
        if ((track, race) in identifiers or not isinstance(nums, list) or
                len(nums) != 3 or any(not _integer(n, 1, 18) for n in nums) or
                len(set(nums)) != 3 or not _integer(payout, 0, 10**8)):
            raise ReviewError("Invalid payout row")
        identifiers.add((track, race))
        safe_hits.append({"track":track, "race":race, "combination":nums[:],
                          "payout":payout})
    for v in venues:
        corresponding = [h for h in safe_hits if h["track"] == v["name"]]
        if len(corresponding) != v["trifectaHits"] or sum(x["payout"] for x in corresponding) != v["payout"]:
            raise ReviewError("Payout mismatch")
    strong = raw.get("strong")
    if (not isinstance(strong, dict) or not _integer(strong.get("races"), 1, count) or
        not _integer(strong.get("hits"), 0, strong["races"]) or
        not _integer(strong.get("payout"), 0, sum(v["payout"] for v in venues))):
        raise ReviewError("Invalid high-confidence retrospective")
    findings = raw.get("findings")
    if not isinstance(findings, list) or not 2 <= len(findings) <= 6 or any(not _safe_text(x, 180) for x in findings):
        raise ReviewError("Invalid lessons")
    if not _safe_text(raw.get("scopeNote"), 240):
        raise ReviewError("Invalid coverage note")
    return {"date":day, "racesReviewed":count, "unit":100, "pointsPerRace":30,
            "venues":venues, "hits":safe_hits, "strong":dict(strong),
            "findings":findings[:], "scopeNote":raw["scopeNote"],
            "sourceKind":"owner-retrospective-provisional",
            "actualPurchase":False, "jraAllVerified":False, "complete":False}
