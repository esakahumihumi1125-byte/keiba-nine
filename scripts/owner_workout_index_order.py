"""Owner-private live JRDB workout INDEX order within the existing S/A/B/C.

This does NOT turn the numeric /tcy indexes into an invented 30-point grade.
It only compares the WEAKER of oikirisisu/siagarisisu for runners in the
SAME provisional band. No index values, names, IDs or race keys are returned.
No provider calls, purchases, receipts, ROI changes or official claims.
All findings are suppressed at/after the programme's provisional off time.
"""
from datetime import datetime, timezone, timedelta
import re

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import NUMBER, HORSE_ID
from jrdb_training_hypothesis import build_training_hints, _index, _grade

VERSION = "owner-workout-index-order-1"
JST = timezone(timedelta(hours=9))
BANDS = ("S", "A", "B", "C")
POST = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")


def unavailable(day, race_count=0):
    return {
        "version": VERSION, "date": day, "raceCount": race_count,
        "studiedRaceCount": 0, "races": [],
        "researchOnly": True, "privateOwnerOnly": True,
        "scoreReady": False, "officialJraVerified": False,
        "predictionReady": False, "bettingReady": False,
        "ticketsIssued": 0, "newProviderRequests": 0,
        "changesExistingReceipts": False, "rawIndexesIncluded": False,
        "sourcePublicationTimeVerified": False,
    }


def workout_index_order(programme, entries, training, report, day, *, now):
    """Join original already-fetched /tra,/tky,/tcy only, per race, fail closed.

    This is an index comparison, not a race rank, win signal, or trained point
    converter. The raw source might lack authenticated publication timestamps.
    A source race with mismatches is skipped and cannot affect another race.
    """
    if (not isinstance(report, dict)
            or report.get("version") != "jrdb-owner-auto-draft-1"
            or report.get("date") != day
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("officialJraVerified") is not False
            or report.get("overallPredictionReady") is not False
            or not isinstance(report.get("races"), list)
            or not isinstance(programme, list) or len(programme) > 120
            or report.get("raceCount") != len(report["races"])
            or report["raceCount"] != len(programme)
            or not isinstance(entries, list) or len(entries) > 50000
            or not isinstance(training, list) or len(training) > 50000
            or not isinstance(now, datetime) or now.tzinfo is None
            or now.utcoffset() is None
            or not isinstance(day, str) or not re.fullmatch(r"20\d{6}", day)):
        raise CoverageError("Invalid workout order study input")
    current = now.astimezone(JST)
    result = unavailable(day, len(programme))
    by_coord = {}
    for row in report["races"]:
        coord = (row.get("track"), row.get("race"))
        if coord in by_coord:
            raise CoverageError("Duplicate source race")
        by_coord[coord] = row
    if len(by_coord) != len(programme):
        raise CoverageError("Wrong source roster size")
    entry_groups, workout_groups = {}, {}
    known_keys = {row.get("racekey") for row in programme}
    for source, groups in ((entries, entry_groups), (training, workout_groups)):
        for row in source:
            if not isinstance(row, dict):
                raise CoverageError("Invalid source row")
            key = row.get("racekey")
            if isinstance(key, str) and key in known_keys:
                groups.setdefault(key, []).append(row)

    for race in programme:
        key = race.get("racekey")
        coord = race.get("track"), race.get("race")
        draft = by_coord.get(coord)
        post = race.get("post_time")
        if (draft is None or draft.get("status") not in ("hold", "provisional_draft")
                or draft.get("reason") in (
                    "after_provisional_off", "provider_withdrawal",
                    "archived_earlier_draft", "invalid_two_factor",
                    "missing_research", "runner_count_mismatch")
                or not isinstance(post, str) or not POST.fullmatch(post)
                or draft.get("postTime") != post
                or not isinstance(key, str) or len(key) != 8):
            continue
        try:
            off = datetime.fromisoformat(
                f"{day[:4]}-{day[4:6]}-{day[6:]}T{post}:00+09:00"
            )
        except ValueError:
            continue
        if current >= off:
            continue
        roster = draft.get("runners")
        if not isinstance(roster, list) or not 2 <= len(roster) <= 18:
            continue
        one_entries = entry_groups.get(key, [])
        one_training = workout_groups.get(key, [])
        try:
            hints = build_training_hints(
                [race], one_entries, one_training, day)[0]["gradesByNumber"]
            exact = {}
            by_id = {}
            for entry in one_entries:
                num, horse_id = entry.get("horse_number"), entry.get("horse_id")
                if not isinstance(num, str) or not NUMBER.fullmatch(num) or num in exact:
                    raise CoverageError("Invalid entry number")
                exact[num] = True
                if isinstance(horse_id, str) and HORSE_ID.fullmatch(horse_id):
                    if horse_id in by_id:
                        raise CoverageError("Duplicate entry identifier")
                    by_id[horse_id] = num
            minimum = {}
            for item in one_training:
                num, hid = item.get("horse_number"), item.get("horse_id")
                direct = num if isinstance(num, str) and num in exact else None
                linked = by_id.get(hid) if isinstance(hid, str) else None
                if direct and linked and direct != linked:
                    raise CoverageError("Workout runner identity conflict")
                number = linked or direct
                if number is None:
                    continue
                if number in minimum:
                    raise CoverageError("Repeated workout runner")
                left = _index(item.get("oikirisisu"))
                right = _index(item.get("siagarisisu"))
                if left is not None and right is not None:
                    minimum[number] = min(left, right)
            expected = {f"{horse['number']:02d}": horse for horse in roster
                        if isinstance(horse, dict)
                        and type(horse.get("number")) is int
                        and 1 <= horse["number"] <= 18}
            if (len(expected) != len(roster)
                    or len(expected) != len(one_entries)
                    or set(expected) != set(exact)):
                continue
            if (set(hints) != set(expected) or set(minimum) != set(expected)):
                continue
            for number, horse in expected.items():
                if (hints[number] not in BANDS
                        or horse.get("training") != hints[number]
                        or _grade(minimum[number], minimum[number]) != hints[number]):
                    raise CoverageError("Training index grade mismatch")
            out, separated, equal = [], 0, 0
            for band in BANDS:
                peers = [(int(num), minimum[num]) for num in expected
                         if hints[num] == band]
                peers.sort(key=lambda x: (-x[1], x[0]))
                last, rank = None, None
                for pos, (number, value) in enumerate(peers, 1):
                    if last != value:
                        rank = pos
                    out.append({"number": number, "trainingBand": band,
                                "withinBandRank": rank})
                    last = value
                for i, (number, value) in enumerate(peers):
                    for other_number, other in peers[i+1:]:
                        if value == other:
                            equal += 1
                        else:
                            separated += 1
            if not out or len(out) != len(roster):
                continue
            result["races"].append({
                "track": coord[0], "race": coord[1], "runnerCount": len(out),
                "runners": out, "differentIndexPairsWithinBand": separated,
                "exactTiePairsWithinBand": equal,
                "rankingScope": "workout_index_within_band_only",
            })
        except (CoverageError, ValueError, TypeError, KeyError, IndexError):
            continue
    result["studiedRaceCount"] = len(result["races"])
    return result
