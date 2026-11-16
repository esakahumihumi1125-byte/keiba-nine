"""Keep healthy JRDB optional-factor research when one race has bad evidence.

The primary two-factor draft already gates data per race. This adapter applies
the same isolation to the optional /tky-/tze research scores without changing
the strict underlying scoring rules. An untrusted or malformed race gets NO
factor scores and can never acquire unsigned comparable tickets from here.

All source reads occur upstream. No paid rows, indices, raw exceptions, new
bets, formal 100-point scores or official JRA verification are introduced.
"""
from datetime import datetime

from evaluation_policy import OWNER_FORMAL_FACTORS, OWNER_FORMAL_POLICY_VERSION
from jrdb_coverage import CoverageError, KEY
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from owner_automatic_factor_scores import (
    automatic_factor_scores, VERSION, FACTORS,
)

MAX_RACES = 120
MAX_ROWS = 50000


def isolated_automatic_factor_scores(programme, entries, recent, day, *,
                                     now, race_context=None):
    """Compute each race independently; preserve verified source identities.

    An unknown race key in any paid dataset remains a global integrity error.
    A malformed known race is quarantined, never silently dropped or counted
    as assessed. The next good race retains its normal factor calculations.
    """
    if (not _valid_date(day)
            or not isinstance(now, datetime)
            or now.tzinfo is None or now.utcoffset() is None
            or not isinstance(programme, list) or len(programme) > MAX_RACES
            or any(not isinstance(row, dict) for row in programme)):
        raise CoverageError("Invalid isolated factor input")
    keys, coords = set(), set()
    for race in programme:
        key = race.get("racekey")
        coord = (race.get("track"), race.get("race"))
        if (type(key) is not str or not KEY.fullmatch(key)
                or key in keys or race.get("racedate") != day
                or coord in coords or coord[0] not in TRACKS.values()
                or type(coord[1]) is not int or not 1 <= coord[1] <= 12):
            raise CoverageError("Invalid isolated programme identity")
        keys.add(key)
        coords.add(coord)

    grouped = []
    for collection in (entries, recent):
        if (not isinstance(collection, list) or len(collection) > MAX_ROWS
                or any(not isinstance(row, dict) for row in collection)):
            raise CoverageError("Invalid isolated source collection")
        by_race = {key: [] for key in keys}
        for row in collection:
            key = row.get("racekey")
            # Do not guess which race a foreign or malformed record belongs to.
            if type(key) is not str or key not in keys:
                raise CoverageError("Unmatched source race identity")
            by_race[key].append(row)
        grouped.append(by_race)
    entry_rows, recent_rows = grouped

    races = []
    for row in programme:
        key = row["racekey"]
        try:
            scoped = automatic_factor_scores(
                [row], entry_rows[key], recent_rows[key], day,
                now=now, race_context=race_context,
            )
            if (scoped.get("version") != VERSION or
                    scoped.get("date") != day or
                    scoped.get("modelCalibrated") is not False or
                    scoped.get("officialJraVerified") is not False or
                    scoped.get("overallPredictionReady") is not False or
                    scoped.get("newProviderRequests") != 0 or
                    len(scoped.get("races", [])) != 1 or
                    scoped["races"][0].get("track") != row["track"] or
                    scoped["races"][0].get("race") != row["race"]):
                raise CoverageError("Invalid scoped score output")
            races.append(scoped["races"][0])
        except (CoverageError, ValueError, TypeError, KeyError):
            # No horse list or private data from the rejected race; keep
            # this race HELD and let independent races continue.
            races.append({
                "track": row["track"], "race": row["race"],
                "postTime": row.get("post_time"),
                "status": "held", "reason": "source_validation_failed",
                "horses": [],
            })

    return {
        "version": VERSION, "policyVersion": OWNER_FORMAL_POLICY_VERSION,
        "date": day, "capturedAt": now.isoformat(), "races": races,
        "factorKeys": list(FACTORS),
        "maximumPoints": sum(OWNER_FORMAL_FACTORS[k] for k in FACTORS),
        "modelCalibrated": False, "officialJraVerified": False,
        "overallPredictionReady": False, "newProviderRequests": 0,
        "isolatedHeldRaces": sum(
            x["reason"] == "source_validation_failed" for x in races),
    }


def reconcile_factor_rosters_with_drafts(factors, drafts):
    """Quarantine research scores not bound to the same prestart runner list.

    The five-factor /tky-/tze scorer independently excludes withdrawals,
    while the signed two-factor pipeline can hold a race or return a different
    runner set. An exact identity match is required before displaying these
    experimental points beside any horse. A mismatch invalidates ONLY the
    optional five-factor panel, never the primary signed draft or archive.
    No source reads, new tickets, formal grades, or official claims.
    """
    if (not isinstance(factors, dict) or factors.get("version") != VERSION
            or factors.get("overallPredictionReady") is not False
            or factors.get("officialJraVerified") is not False
            or factors.get("newProviderRequests") != 0
            or not isinstance(factors.get("races"), list)
            or not isinstance(drafts, dict)
            or drafts.get("researchOnly") is not True
            or drafts.get("officialJraVerified") is not False
            or not isinstance(drafts.get("races"), list)
            or len(factors["races"]) != len(drafts["races"])
            or len(factors["races"]) > MAX_RACES):
        raise CoverageError("Incompatible private research snapshots")

    current = {}
    for draft in drafts["races"]:
        if (not isinstance(draft, dict)
                or draft.get("track") not in TRACKS.values()
                or type(draft.get("race")) is not int
                or not 1 <= draft["race"] <= 12
                or draft.get("status") not in ("hold", "provisional_draft")
                or not isinstance(draft.get("runners"), list)
                or len(draft["runners"]) > 18):
            raise CoverageError("Invalid private research race")
        key = draft["track"], draft["race"]
        if key in current:
            raise CoverageError("Duplicate private research race")
        current[key] = draft

    updated = []
    seen = set()
    for item in factors["races"]:
        if not isinstance(item, dict):
            raise CoverageError("Invalid additional factor race")
        key = item.get("track"), item.get("race")
        if (key not in current or key in seen
                or item.get("status") not in ("held", "scored")
                or not isinstance(item.get("horses"), list)
                or len(item["horses"]) > 18):
            raise CoverageError("Additional factor identity mismatch")
        seen.add(key)
        draft = current[key]
        if item.get("postTime") != draft.get("postTime"):
            raise CoverageError("Additional factor schedule mismatch")
        if item["status"] != "scored":
            if item["horses"]:
                raise CoverageError("Held additional factors contain horses")
            updated.append(item)
            continue

        # Reject duplicate or malformed numbers as an integrity failure;
        # do not silently convert them to a set and claim all horses match.
        def numbers(rows, field):
            values = []
            for row in rows:
                if (not isinstance(row, dict) or type(row.get(field)) is not int
                        or not 1 <= row[field] <= 18):
                    raise CoverageError("Invalid research runner number")
                values.append(row[field])
            if len(set(values)) != len(values):
                raise CoverageError("Duplicate research runner number")
            return set(values)

        actual = numbers(item["horses"], "number")
        expected = numbers(draft["runners"], "number")
        if (len(actual) != len(expected) or actual != expected
                or len(actual) < 4):
            updated.append({
                "track": key[0], "race": key[1],
                "postTime": item.get("postTime"),
                "status": "held", "reason": "research_roster_mismatch",
                "horses": [],
            })
        else:
            updated.append(item)
    if seen != set(current):
        raise CoverageError("Missing additional factor race")
    return {
        **factors, "races": updated,
        "isolatedHeldRaces": sum(
            row["reason"] in ("source_validation_failed",
                              "research_roster_mismatch")
            for row in updated
        ),
    }
