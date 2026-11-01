#!/usr/bin/env python3
"""Publish original, authorized public predictions; no race scraping or paid AI."""
import argparse
import ipaddress
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

JST = timezone(timedelta(hours=9))
TRACKS = set("札幌 函館 福島 新潟 東京 中山 中京 京都 阪神 小倉".split())
MAX_BYTES = 500000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Source redirects are not allowed")


def read_source(url):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
            parsed.password or parsed.port not in (None, 443)):
        raise ValueError("An HTTPS source URL without credentials is required")
    host = parsed.hostname.lower().rstrip(".")
    try:
        ipaddress.ip_address(host)
        raise ValueError("IP-address source URLs are not allowed")
    except ValueError as ex:
        if str(ex) == "IP-address source URLs are not allowed":
            raise
    if host in ("localhost", "localhost.localdomain") or "." not in host:
        raise ValueError("A public DNS hostname is required")
    request = Request(url, headers={"User-Agent": "KEIBA-NINE-public-feed/1"})
    with build_opener(NoRedirect()).open(request, timeout=15) as response:
        if response.status != 200:
            raise ValueError("Source did not return HTTP 200")
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError("Source feed is too large")
    return json.loads(raw.decode("utf-8"))


def stamp(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp missing")
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("A timezone-aware timestamp is required")
    return d.astimezone(timezone.utc)


def numbers(value):
    if not isinstance(value, list):
        raise ValueError("Horse numbers must be arrays")
    if any(type(n) is not int or not 1 <= n <= 18 for n in value):
        raise ValueError("Invalid horse number")
    if len(set(value)) != len(value):
        raise ValueError("Duplicate horse number")
    return value


def triple_count(a, b, c):
    return sum(x != y and y != z and x != z for x in a for y in b for z in c)


def trio_count(row):
    mode = row.get("trioMode", "ボックス")
    pool = numbers(row.get("trioPool", []))
    axis = numbers(row.get("trioAxis", []))
    columns = row.get("trioFormation", [[], [], []])
    if not isinstance(columns, list) or len(columns) != 3:
        raise ValueError("Invalid trio formation")
    columns = [numbers(x) for x in columns]
    bets = set()
    def add(a, b, c):
        if len({a, b, c}) == 3:
            bets.add(tuple(sorted((a, b, c))))
    if mode == "ボックス":
        for a in pool:
            for b in pool:
                for c in pool:
                    add(a, b, c)
    elif mode == "1頭軸流し" and len(axis) == 1:
        for b in pool:
            for c in pool:
                add(axis[0], b, c)
    elif mode == "2頭軸流し" and len(axis) == 2:
        for c in pool:
            add(axis[0], axis[1], c)
    elif mode == "フォーメーション":
        for a in columns[0]:
            for b in columns[1]:
                for c in columns[2]:
                    add(a, b, c)
    else:
        raise ValueError("Invalid trio mode or axis")
    return len(bets)


def validate(payload, now):
    """Validate new future race forecasts against the app's existing schema."""
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise ValueError("Expected public feed schema 1")
    source = payload.get("source")
    if (not isinstance(source, dict) or source.get("publicReleaseApproved") is not True or
            source.get("originalForecast") is not True or
            not isinstance(source.get("name"), str) or not source["name"].strip() or
            not isinstance(source.get("rightsNote"), str) or not source["rightsNote"].strip()):
        raise ValueError("Explicit approval for original public forecasts required")
    target = payload.get("date")
    try:
        target_date = datetime.strptime(target, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid race date") from exc
    today = now.astimezone(JST).date()
    if target_date not in (today, today + timedelta(days=1)):
        raise ValueError("Only today/tomorrow may be published")
    generated = stamp(payload.get("generatedAt"))
    if generated > now + timedelta(minutes=5) or generated < now - timedelta(hours=36):
        raise ValueError("Stale or future generation timestamp")
    if payload.get("sample") or payload.get("testOnly"):
        raise ValueError("Sample/test feed cannot be published as live")
    rows = payload.get("forecasts")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 120:
        raise ValueError("Expected 1-120 race forecasts")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("recordType") != "live" or row.get("sample"):
            raise ValueError("Live, non-synthetic forecasts only")
        if row.get("date") != target or row.get("track") not in TRACKS:
            raise ValueError("Race date/track mismatch")
        race = row.get("race")
        if type(race) is not int or not 1 <= race <= 12:
            raise ValueError("Race number must be 1-12")
        key = (row["track"], race)
        if key in seen:
            raise ValueError("Duplicate race")
        seen.add(key)
        post = post_time(target, row)
        if post <= now.astimezone(JST):
            raise ValueError("Cannot first publish or change a race after post time")
        if row.get("status") not in ("draft", "final", "skip"):
            raise ValueError("Invalid forecast status")
        if row.get("confidence", "C") not in ("S", "A", "B", "C"):
            raise ValueError("Invalid confidence")
        if row.get("intent", "参考") not in ("購入推奨", "参考", "見送り"):
            raise ValueError("Invalid intent")
        a, b, c, ranking = [numbers(row.get(k, [])) for k in
                             ("first", "second", "third", "ranking")]
        tri, trio = triple_count(a, b, c), trio_count(row)
        if tri > 48 or trio > 120:
            raise ValueError("Bet point cap exceeded")
        if row.get("triPoints", tri) != tri or row.get("trioPoints", trio) != trio:
            raise ValueError("Declared ticket points mismatch")
        if row["status"] == "skip" and row.get("intent", "見送り") != "見送り":
            raise ValueError("Skipped races must use a skip intent")
        if row["status"] != "final" and (tri or trio):
            raise ValueError("Drafts and skips must not contain bet formations")
        if row["status"] == "final":
            if tri + trio == 0:
                raise ValueError("Final forecast must contain a valid ticket")
            card, evidence = row.get("raceCard"), row.get("evidence")
            if (not isinstance(card, dict) or card.get("complete") is not True or
                    card.get("date") != target or card.get("track") != row["track"] or
                    card.get("race") != race or not isinstance(card.get("source"), str) or
                    not card["source"] or not isinstance(card.get("runners"), list) or
                    not isinstance(evidence, dict) or
                    not isinstance(evidence.get("references"), list) or
                    not evidence["references"]):
                raise ValueError("Final forecast requires a complete, cited race card")
            runners = card["runners"]
            if not 1 <= len(runners) <= 18:
                raise ValueError("Invalid runner count")
            ids = numbers([h.get("number") if isinstance(h, dict) else None for h in runners])
            if any(not isinstance(h.get("name"), str) or not h["name"].strip() or
                   h.get("status") not in ("active", "scratched", "excluded") for h in runners):
                raise ValueError("Each runner needs name and status")
            active = {h["number"] for h in runners if h["status"] == "active"}
            if not set(ranking + a + b + c).issubset(active):
                raise ValueError("Ranked or bet horse scratched/not in race card")
            checked = stamp(card.get("checkedAt"))
            if checked > now + timedelta(minutes=5):
                raise ValueError("Race card verification timestamp is in the future")
    return payload


def post_time(date, row):
    try:
        return datetime.strptime(f"{date}T{row['off']}", "%Y-%m-%dT%H:%M").replace(tzinfo=JST)
    except (TypeError, ValueError, KeyError) as exc:
        raise ValueError("Valid local post time HH:MM required") from exc


def publish(payload, existing, now):
    """Merge authorized future rows while preserving ALL previously started races."""
    if now.tzinfo is None or not isinstance(payload, dict):
        raise ValueError("Timezone-aware now and source object required")
    target = payload.get("date")
    incoming = payload.get("forecasts")
    if not isinstance(incoming, list) or not incoming:
        raise ValueError("Source has no forecast rows")
    old = {}
    if isinstance(existing, dict) and existing.get("date") == target:
        for row in existing.get("forecasts", []):
            if not isinstance(row, dict) or "track" not in row or "race" not in row:
                raise ValueError("Invalid existing public forecast")
            key = (row["track"], row["race"])
            if key in old:
                raise ValueError("Existing feed contains duplicate races")
            old[key] = row
    fresh, seen = [], set()
    for row in incoming:
        if not isinstance(row, dict):
            raise ValueError("Invalid incoming race")
        key = (row.get("track"), row.get("race"))
        if key in seen:
            raise ValueError("Duplicate incoming race")
        seen.add(key)
        original = old.get(key)
        if original and post_time(target, original) <= now.astimezone(JST):
            if row != original:
                raise ValueError("Started race cannot be altered")
            continue
        fresh.append(row)
    # Always validate source rights and metadata, even if every race is unchanged.
    check = dict(payload)
    check["forecasts"] = fresh if fresh else [dict(incoming[0])]
    if fresh:
        validate(check, now)
    else:
        if not old or any(old.get((r.get("track"), r.get("race"))) != r for r in incoming):
            raise ValueError("No future races to publish")
        # Validate source metadata using an unchanged started row without attempting
        # a post-time validation; all unchanged rows already exist in Git history.
        check["forecasts"] = []
        future_old = next((r for r in incoming if post_time(target, r) > now.astimezone(JST)), None)
        if future_old:
            validate({**check, "forecasts": [future_old]}, now)
        else:
            if (not isinstance(payload.get("source"), dict) or
                    payload["source"].get("publicReleaseApproved") is not True or
                    payload["source"].get("originalForecast") is not True):
                raise ValueError("Public approval missing")
            return None
    merged = dict(old)
    for row in fresh:
        merged[(row["track"], row["race"])] = row
    if not 1 <= len(merged) <= 120:
        raise ValueError("Merged feed race count invalid")
    updated = dict(payload)
    updated["forecasts"] = sorted(merged.values(),
                                  key=lambda r: (r["off"], r["track"], r["race"]))
    if (isinstance(existing, dict) and existing.get("date") == target and
            existing.get("forecasts") == updated["forecasts"] and
            existing.get("source") == updated.get("source")):
        return None
    return updated


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-url", default=os.environ.get("KEIBA_NINE_PUBLIC_FEED_URL"))
    parser.add_argument("--output", default="keiba-nine-auto-feed.json")
    args = parser.parse_args()
    if not args.source_url:
        raise SystemExit("No approved public forecast source configured")
    now = datetime.now(timezone.utc)
    payload = read_source(args.source_url)
    path = Path(args.output)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    updated = publish(payload, existing, now)
    if updated is None:
        print("Forecasts unchanged; nothing to publish")
    else:
        path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
        print(f"Approved forecast feed prepared: {len(updated['forecasts'])} races")


if __name__ == "__main__":
    main()
