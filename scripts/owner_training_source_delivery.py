"""Private aggregate explanation of JRDB /tcy source delivery versus scoring.

A successful HTTP fetch does NOT mean training rows are present, matched to
today's race, matched to a runner, or complete for both exercise indexes.
This counters misleading 35R+ 'hold' situations without assigning fake
grades or adding provider calls. Returns counts and fixed enum ONLY.
"""
from collections import defaultdict
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date, NUMBER, HORSE_ID
from jrdb_training_hypothesis import _index

VERSION = "owner-training-source-delivery-1"
LIMIT = 50000
STATES = frozenset((
    "programme_not_returned", "training_not_queried", "training_empty_response",
    "training_no_current_race", "training_current_race_date_mismatch",
    "training_no_runner_match", "training_indices_missing",
    "training_identity_conflict", "training_partial_index_coverage",
    "training_index_rows_present",
))


def observe_training_source_delivery(programme, entries, training, recent, day,
                                     *, source_read_count):
    """Explain SAME read, no IO, no source values/horse numbers in result."""
    if (not _valid_date(day) or type(source_read_count) is not int
            or source_read_count not in (1, 4)):
        raise CoverageError("Invalid source delivery day/read count")
    for name, group in (("programme", programme), ("entry", entries),
                        ("training", training), ("recent", recent)):
        if (not isinstance(group, list) or len(group) > (120 if name == "programme" else LIMIT)
                or any(not isinstance(r, dict) for r in group)):
            raise CoverageError("Invalid source delivery collection")
    if source_read_count == 1 and (programme or entries or training or recent):
        raise CoverageError("Programme-only source call with supplemental rows")
    if not programme and (entries or training or recent):
        raise CoverageError("Missing source programme")
    known = {}
    for row in programme:
        key = row.get("racekey")
        coord = row.get("track"), row.get("race")
        if (not isinstance(key, str) or len(key) != 8 or key in known
                or row.get("racedate") != day):
            raise CoverageError("Invalid day race key")
        known[key] = coord
    valid_entries, by_id = {}, {}
    for entry in entries:
        key, num, hid = (entry.get("racekey"), entry.get("horse_number"),
                         entry.get("horse_id"))
        if key not in known or entry.get("racedate") != day:
            continue
        if not isinstance(num, str) or not NUMBER.fullmatch(num):
            raise CoverageError("Invalid current entry number")
        identity = (key, num)
        if identity in valid_entries:
            raise CoverageError("Duplicate entry")
        valid_entries[identity] = True
        if hid not in (None, ""):
            if not isinstance(hid, str) or not HORSE_ID.fullmatch(hid):
                raise CoverageError("Invalid entry horse identity")
            if (key, hid) in by_id:
                raise CoverageError("Duplicate entry horse identity")
            by_id[key, hid] = identity

    training_known_race = 0
    training_current_date = 0
    joined = set()
    matching_rows = defaultdict(int)
    clean_indices = set()
    mismatched = 0
    training_races_with_rows = set()
    training_races_with_indices = set()
    for row in training:
        key = row.get("racekey")
        if not isinstance(key, str) or key not in known:
            continue
        training_known_race += 1
        if row.get("racedate") != day:
            continue
        training_current_date += 1
        training_races_with_rows.add(key)
        num, hid = row.get("horse_number"), row.get("horse_id")
        num_id = (key, num) if (isinstance(num, str)
                                and NUMBER.fullmatch(num)
                                and (key, num) in valid_entries) else None
        horse_id = by_id.get((key, hid)) if isinstance(hid, str) else None
        # The independent research validator would reject unknown nonempty
        # IDs. Never use a horse-number fallback to disguise an ID conflict.
        if (isinstance(hid, str) and hid and horse_id is None
                or num_id is not None and horse_id is not None and num_id != horse_id):
            mismatched += 1
            continue
        identity = horse_id or num_id
        if identity is None:
            continue
        joined.add(identity)
        matching_rows[identity] += 1
        try:
            both = (_index(row.get("oikirisisu")) is not None
                    and _index(row.get("siagarisisu")) is not None)
        except CoverageError:
            both = False
        if both:
            clean_indices.add(identity)
    duplicates = sum(max(0, n-1) for n in matching_rows.values())
    complete = {x for x in clean_indices if matching_rows[x] == 1}
    training_races_with_indices = {key for key, _ in complete}
    recent_known = sum(
        type(row.get("racekey")) is str
        and row["racekey"] in known and row.get("racedate") == day
        for row in recent
    )
    if source_read_count == 1:
        status = "training_not_queried"
    elif not training:
        status = "training_empty_response"
    elif not training_known_race:
        status = "training_no_current_race"
    elif not training_current_date:
        status = "training_current_race_date_mismatch"
    elif mismatched or duplicates:
        status = "training_identity_conflict"
    elif not joined:
        status = "training_no_runner_match"
    elif not complete:
        status = "training_indices_missing"
    elif len(complete) < len(valid_entries):
        status = "training_partial_index_coverage"
    else:
        status = "training_index_rows_present"
    if not programme:
        status = "programme_not_returned"
    if status not in STATES:
        raise CoverageError("Invalid source delivery state")
    return {
        "version": VERSION, "date": day,
        "raceCount": len(programme),
        "sourceReadCount": source_read_count,
        "entryRowsReturned": len(entries),
        "entriesMatchedDayProgramme": len(valid_entries),
        "trainingRowsReturned": len(training),
        "trainingRowsKnownRace": training_known_race,
        "trainingRowsCurrentRaceDate": training_current_date,
        "trainingRacesWithRows": len(training_races_with_rows),
        "trainingLinkedRunners": len(joined),
        "trainingRunnersWithBothIndices": len(complete),
        "trainingRacesWithBothIndices": len(training_races_with_indices),
        "trainingIdentityConflicts": mismatched,
        "trainingDuplicateRunnerRows": duplicates,
        "recentRowsReturned": len(recent),
        "recentRowsCurrentRaceDate": recent_known,
        "status": status,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "scoreReady": False,
        "predictionReady": False, "bettingReady": False,
        "newProviderRequests": 0, "retainedLicensedRows": False,
        "changesExistingDrafts": False,
        "changesExistingReceipts": False,
        "note": ("HTTP取得成功と馬別指数の利用可否は別。行がない原因は"
                 "公開時刻、提供状況、API応答、照合条件などがあり、"
                 "この診断だけでは特定不可。指数や個人識別子は返さない。"),
    }
