"""Private one-day orchestration for existing JRDB *ungraded* factor material.

Accept only the same-day, already normalized /tra programme and already
matched server-private two-factor matrix. No provider/HTTP calls are made.
This deliberately does not turn provisional grades, guesses, or client
verification flags into a formal 100-point score or a purchasable ticket.

Use only inside an authenticated server process. Licensed raw runner rows
must not be logged, persisted, or included in browser responses.
"""
import re
from datetime import datetime, timedelta, timezone

from evaluation_policy import timestamp
from jrdb_coverage import CoverageError
from jrdb_program_preview import TRACKS, RACE_KEY
from owner_full_ten_day_gate import full_ten_day_research, _day, _clock
from owner_formal_jrdb_source_bridge import build_ungraded_formal_race_input

VERSION = "owner-formal-jrdb-day-bridge-1"
JST = timezone(timedelta(hours=9))
OFF = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z")
MAX_RACES = 36


def _coordinate(row):
    if not isinstance(row, dict):
        raise CoverageError("Invalid private day row")
    key, track, race = row.get("racekey"), row.get("track"), row.get("race")
    if (type(key) is not str or RACE_KEY.fullmatch(key) is None
            or key[:2] not in TRACKS
            or track != TRACKS[key[:2]]
            or type(race) is not int
            or not 1 <= race <= 12
            or key[6:] != f"{race:02d}"):
        raise CoverageError("Private day race identity mismatch")
    return track, race, key


def audit_ungraded_formal_jrdb_day(day, programme, private_matrix, *,
                                   as_of, now):
    """Audit all matching JRDB material races through the guarded formal gate.

    A missing/incomplete source or a missing post time puts ONLY that race
    on hold. Conflicting day/track/race collections and duplicated identities
    reject the entire batch, rather than attaching a horse to another race.
    The output is fixed-form, nonidentifying diagnostics and no private data.
    """
    _day(day)
    current = _clock(now)
    try:
        captured = timestamp(as_of)
    except (TypeError, ValueError, OverflowError):
        raise CoverageError("Invalid private snapshot capture time") from None
    if current < captured:
        raise CoverageError("Private source capture cannot be in the future")
    if (not isinstance(programme, list) or len(programme) > MAX_RACES
            or not isinstance(private_matrix, list)
            or len(private_matrix) > MAX_RACES):
        raise CoverageError("Invalid private day source count")

    schedule, seen_keys = {}, set()
    for row in programme:
        track, race, key = _coordinate(row)
        coord = track, race
        if (coord in schedule or key in seen_keys
                or row.get("racedate") != day
                or row.get("programmeOnly") is not True
                or row.get("horsesVerified") is not False
                or row.get("predictionStatus") != "未作成"):
            raise CoverageError("Invalid normalized JRDB programme")
        schedule[coord] = row
        seen_keys.add(key)

    materials = {}
    for source in private_matrix:
        track, race, key = _coordinate(source)
        coord = track, race
        if (coord in materials or coord not in schedule
                or key != schedule[coord]["racekey"]):
            raise CoverageError("Unmatched or duplicate private factor source")
        materials[coord] = source

    rows, source_holds = [], {}
    for (track, race), program in sorted(schedule.items()):
        source = materials.get((track, race))
        off = program.get("post_time")
        count = program.get("headcount")
        snapshot, hold = None, "none"
        # Report only fixed diagnostic codes. Do not expose JRDB source rows,
        # race keys, paid identifiers, provider errors or individual grades.
        if source is None:
            hold = "source_missing"
        elif type(count) is not int or not 4 <= count <= 18:
            hold = "programme_headcount_unknown"
        elif (not isinstance(source.get("byNumber"), dict)
              or len(source["byNumber"]) != count):
            hold = "roster_count_mismatch"
        elif type(off) is not str or OFF.fullmatch(off) is None:
            hold = "post_time_unknown"
        else:
            off_dt = datetime.strptime(day + off.replace(":", ""),
                                       "%Y%m%d%H%M").replace(tzinfo=JST)
            if captured >= off_dt:
                hold = "source_captured_after_post_time"
            else:
                try:
                    row = build_ungraded_formal_race_input(
                        source, day=day, as_of=as_of,
                        off_at=off_dt.isoformat(),
                    )
                    snapshot = row["snapshot"]
                except (CoverageError, TypeError, ValueError, OverflowError):
                    hold = "source_contract_invalid"
        source_holds[(track, race)] = hold
        rows.append({"track": track, "race": race, "snapshot": snapshot})

    audit = full_ten_day_research(day, rows, now=now)
    # The guard must never become a graded prediction just because a provider
    # supplied 10 named fields or a provisional S/A/B/C research band.
    if audit["researchFormationRaces"] != 0 or audit["fullTenResearchRankRaces"] != 0:
        raise CoverageError("Unverified material unexpectedly produced ranking")
    return {
        "version": VERSION,
        "date": day,
        "sourceRaceCount": len(materials),
        "scheduledRaceCount": len(schedule),
        "heldSourceRaces": sum(r["status"] == "invalid_internal_snapshot"
                               for r in audit["races"]),
        "sourceHoldReasonCounts": {
            reason: sum(value == reason for value in source_holds.values())
            for reason in sorted(set(source_holds.values()) - {"none"})
        },
        "races": [{
            "track": row["track"], "race": row["race"],
            "status": row["status"],
            "sourceHoldReason": source_holds[(row["track"], row["race"])],
            "unassessedHorseCount": row["unassessedHorseCount"],
            "reviewOnlyTicketCount": 0,
            "researchOnly": True, "bettingReady": False,
        } for row in audit["races"]],
        "sourceMaterialOnly": True,
        "formalVerifiedFactorCount": 0,
        "independentJraConnected": False,
        "liveProviderFetchPerformedHere": False,
        "extraPaidRequests": 0,
        "productionPredictionReady": False,
        "actualPurchase": False,
        "autoPurchase": False,
        "note": "JRDB同日資料を正式ゲートへ未評価として内部突合。正式採点・JRA公式確認・馬券は未実装。",
    }
