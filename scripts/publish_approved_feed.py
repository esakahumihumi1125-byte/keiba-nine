#!/usr/bin/env python3
"""Publish explicitly approved, original public forecasts; never fetch JRDB here."""
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
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise ValueError("Schema 1 public feed required")
    source = payload.get("source")
    if (not isinstance(source, dict) or source.get("publicReleaseApproved") is not True
            or not source.get("name") or not source.get("rightsNote")):
        raise ValueError("Explicit public publication approval and attribution required")
    target = payload.get("date")
    try:
        date = datetime.strptime(target, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid race date") from exc
    today = now.astimezone(JST).date()
    if date not in (today, today + timedelta(days=1)):
        raise ValueError("Only today's or tomorrow's race feed may be published")
    generated = stamp(payload.get("generatedAt"))
    if generated > now + timedelta(minutes=5) or generated < now - timedelta(hours=36):
        raise ValueError("Generated timestamp is stale or in the future")
    rows = payload.get("forecasts")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 120:
        raise ValueError("Feed must have 1-120 races")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.get("recordType") != "live":
            raise ValueError("Synthetic/test data cannot be published as live")
        if row.get("date") != target or row.get("track") not in TRACKS:
            raise ValueError("Race date or track mismatch")
        race = row.get("race")
        if type(race) is not int or not 1 <= race <= 12:
            raise ValueError("Invalid race number")
        key = (row["track"], race)
        if key in seen:
            raise ValueError("Duplicate race")
        seen.add(key)
        off = row.get("off")
        try:
            post = datetime.strptime(f"{target}T{off}", "%Y-%m-%dT%H:%M").replace(tzinfo=JST)
        except (TypeError, ValueError) as exc:
            raise ValueError("Valid local post time is required") from exc
        if row.get("status") not in ("draft", "final", "skip"):
            raise ValueError("Invalid status")
        ranking = numbers(row.get("ranking", []))
        first, second, third = (numbers(row.get(k, [])) for k in ("first", "second", "third"))
        tri = triple_count(first, second, third)
        trio = trio_count(row)
        if tri > 48 or trio > 120:
            raise ValueError("Bet exceeds allowed point count")
        if row.get("triPoints", tri) != tri or row.get("trioPoints", trio) != trio:
            raise ValueError("Declared bet count differs from actual combinations")
        if row["status"] == "final":
            if post <= now.astimezone(JST):
                raise ValueError("New final predictions cannot be published after post time")
            if not tri and not trio:
                raise ValueError("Final prediction must contain a valid bet")
            evidence = row.get("evidence", {})
            card = row.get("raceCard", {})
            if (not isinstance(evidence, dict) or
                    not isinstance(evidence.get("references"), list) or
                    not evidence["references"] or
                    not isinstance(card, dict) or card.get("complete") is not True or
                    not isinstance(card.get("runners"), list)):
                raise ValueError("Final prediction requires checked references and complete race card")
            runners = card["runners"]
            if not 1 <= len(runners) <= 18:
                raise ValueError("Invalid complete race card")
            ids = [h.get("number") for h in runners if isinstance(h, dict)]
            if len(ids) != len(runners):
                raise ValueError("Invalid runner record")
            numbers(ids)
            if not all(isinstance(h.get("name"), str) and h["name"].strip() for h in runners):
                raise ValueError("Runner names are required")
            if not set(ranking + first + second + third).issubset(ids):
                raise ValueError("Ranked or selected horse missing from complete race card")
    return payload


def preserve_started(payload, existing, now):
    if not isinstance(existing, dict) or existing.get("date") != payload["date"]:
        return payload
    old_rows = {(r["track"], r["race"]): r for r in existing.get("forecasts", [])
                if isinstance(r, dict) and "track" in r and "race" in r}
    newer = {(r["track"], r["race"]): r for r in payload["forecasts"]}
    for key, old in old_rows.items():
        try:
            post = datetime.strptime(payload["date"] + "T" + old["off"],
                                     "%Y-%m-%dT%H:%M").replace(tzinfo=JST)
        except (KeyError, ValueError):
            raise ValueError("Existing feed has invalid post time")
        if post <= now.astimezone(JST):
            if key in newer and newer[key] != old:
                raise ValueError("A started race's published prediction must not change")
            newer[key] = old
    payload["forecasts"] = sorted(newer.values(),
                                  key=lambda r: (r["off"], r["track"], r["race"]))
    if len(payload["forecasts"]) > 120:
        raise ValueError("Too many races after preserving earlier predictions")
    return payload


def publish(payload, existing, now):
    if now.tzinfo is None:
        raise ValueError("now must have timezone")
    # Keep previously published, already-started rows out of the new-feed validation.
    incoming = dict(payload)
    rows = []
    for row in payload.get("forecasts", []):
        if not isinstance(row, dict):
            raise ValueError("Invalid race")
        rows.append(dict(row))
    incoming["forecasts"] = rows
    old_rows = {}
    if isinstance(existing, dict) and existing.get("date") == incoming.get("date"):
        old_rows = {(r.get("track"), r.get("race")): r
                    for r in existing.get("forecasts", []) if isinstance(r, dict)}
    for row in rows:
        old = old_rows.get((row.get("track"), row.get("race")))
        if old == row and row.get("status") == "final":
            # Previously committed final picks retain their original pre-start validation.
            row["status"] = "draft" if False else "final"
    # Validate incoming races; final predictions for started races are only allowed if unchanged.
    for row in rows:
        if row.get("status") == "final" and old_rows.get((row.get("track"), row.get("race"))) == row:
            row["_alreadyPublishedFinal"] = True
    for row in rows:
        if row.pop("_alreadyPublishedFinal", False) and row.get("status") == "final":
            # Validate unchanged past finals against their original launch time.
            row["_preserved"] = True
    # The caller should omit started races in the incoming feed; they are restored below.
    rows_to_check = [r for r in rows if not r.pop("_preserved", False)]
    incoming["forecasts"] = rows_to_check
    if not rows_to_check:
        raise ValueError("At least one future race is required in the source feed")
    validate(incoming, now)
    incoming["forecasts"] = rows
    incoming = preserve_started(incoming, existing, now)
    if existing and existing.get("date") == incoming["date"]:
        if (existing.get("forecasts") == incoming["forecasts"] and
                existing.get("source") == incoming.get("source")):
            return None
    return incoming


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
