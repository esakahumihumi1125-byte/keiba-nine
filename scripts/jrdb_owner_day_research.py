"""Private all-day JRDB two-factor research from FOUR user-triggered reads.

No API calls or persistence here. The caller fetches one date's /tra /tky
/tcy /tze once each, then this module scopes every race independently.
Research-only derived SABC / horse numbers are returned to the AUTHENTICATED
owner browser; no raw paid metrics or identities leave the server.
No JRA confirmation, overall ranks, bets, automatic purchases or background
provider polling occur.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_owner_runner_research import owner_runner_research
from jrdb_program_preview import TRACKS

VERSION = "jrdb-owner-day-research-1"
MAX_RACES = 120
MAX_SOURCE_ROWS = 50000


def owner_day_research(programme, entries, training, previous, date):
    if not _valid_date(date):
        raise CoverageError("Invalid day research date")
    if (not isinstance(programme, list) or not 0 <= len(programme) <= MAX_RACES
            or not all(isinstance(row, dict) for row in programme)):
        raise CoverageError("Invalid all-day programme")
    for name, collection in (("entries", entries), ("training", training),
                             ("recent", previous)):
        if (not isinstance(collection, list) or len(collection) > MAX_SOURCE_ROWS
                or not all(isinstance(row, dict) for row in collection)):
            raise CoverageError("Invalid all-day " + name + " collection")
    ids, names = set(), set()
    for row in programme:
        key, track, race = (row.get("racekey"), row.get("track"), row.get("race"))
        if (not isinstance(key, str) or len(key) != 8 or key in ids
                or row.get("racedate") != date
                or track not in TRACKS.values() or type(race) is not int
                or not 1 <= race <= 12 or (track, race) in names):
            raise CoverageError("Inconsistent all-day race identifiers")
        ids.add(key)
        names.add((track, race))

    # Do not mix records from a different day/race into a selected slot.
    # Unrelated source anomalies remain flagged at their own race rather than
    # affecting an otherwise valid one. No rows are guessed into a race.
    rows = []
    for programme_row in programme:
        key = programme_row["racekey"]
        track, number = programme_row["track"], programme_row["race"]
        try:
            one_entry = [r for r in entries if r.get("racekey") == key]
            one_training = [r for r in training if r.get("racekey") == key]
            one_recent = [r for r in previous if r.get("racekey") == key]
            t = build_training_hints([programme_row], one_entry, one_training, date)
            p = build_recent_hints([programme_row], one_entry, one_recent, date)
            result = owner_runner_research(t, p, track, number)
            status = "research_only"
            item = {
                "track": track, "race": number,
                "status": status,
                "research": result,
            }
        except (CoverageError, ValueError, TypeError, KeyError):
            # Do not return paid rows, field values, private record keys,
            # failing horse IDs, or source exception messages.
            item = {
                "track": track, "race": number,
                "status": "needs_review",
                "research": None,
            }
        rows.append(item)
    return {
        "version": VERSION,
        "date": date,
        "races": rows,
        "raceCount": len(rows),
        "researchAvailableCount": sum(x["status"] == "research_only" for x in rows),
        "needsReviewCount": sum(x["status"] == "needs_review" for x in rows),
        "researchOnly": True,
        "privateOwnerOnly": True,
        "officialJraVerified": False,
        "overallRankReady": False,
        "predictionReady": False,
        "bettingReady": False,
        "sourceReadCount": 4,
        "note": ("本人の操作時に開催日分の番組・出走馬・調教・近走を各1回だけ読み、"
                 "馬番別の未検証2項目を研究用に表示する。"
                 "レースごとに別々に整合性を確認し、不一致は要確認。"
                 "JRA公式の取消・馬場・発走時刻と残り8項目は未評価。"
                 "総合順位・3連単・WIN5・自動購入は作らない。"),
    }
