"""Parse one private JRA-VAN JV-Data RA/SE prestart racecard candidate.

The fixed byte offsets come from JV-Data specification 4.9.0.1 (RA=1272,
SE=555, including CRLF). This module is strictly offline: no JV-Link COM,
network, files, database, credentials, or public HTTP output. The caller must
have independently obtained licensed source records and checked entitlement.

Only data category 2 (numbered racecard) is accepted. Category 1 lacks final
horse numbers; categories 3..7 can be POST-RACE results and are never allowed
to create prestart evidence. The latest AV/WE/TC/WH realtime updates are NOT
part of RA/SE, so a match here never verifies the final JRA starter list,
scratches, going, off-time, a wager, or a formal factor grade.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import NUMBER, _valid_date
from jrdb_program_preview import TRACKS

VERSION = "owner-jvdata-ra-se-racecard-candidate-1"
RA_LENGTH = 1272
SE_LENGTH = 555
# 2009 track-code categories, flat turf/dirt only. Unknown/obstacle HOLD.
JRA_VENUES = frozenset(TRACKS)
TURF_TRACK_CODES = frozenset(f"{n:02d}" for n in range(10, 23))
DIRT_TRACK_CODES = frozenset(f"{n:02d}" for n in (23, 24, 25, 26, 29))
# 1-based JV-Data positions converted to 0-based Python byte slices.
COMMON = {
    "created": (3, 11),
    "year": (11, 15),
    "month_day": (15, 19),
    "venue": (19, 21),
    "meeting": (21, 23),
    "meeting_day": (23, 25),
    "race": (25, 27),
}


def _fixed(source, kind, expected_length):
    if (type(source) is not bytes or len(source) != expected_length
            or source[:2] != kind or source[2:3] != b"2"
            or source[-2:] != b"\r\n"):
        raise CoverageError("Unsupported JV-Data prestart record")
    return source


def _ascii(source, left, right):
    try:
        value = source[left:right].decode("ascii")
    except UnicodeDecodeError:
        raise CoverageError("Malformed JV-Data race identity") from None
    if not value.isascii() or not value.isdigit():
        raise CoverageError("Malformed JV-Data race identity")
    return value


def _identity(record, day):
    fields = {key: _ascii(record, *pos) for key, pos in COMMON.items()}
    if (not _valid_date(fields["created"])
            or fields["created"] > day
            or fields["year"] + fields["month_day"] != day
            or fields["venue"] not in JRA_VENUES
            or not 1 <= int(fields["meeting"]) <= 12
            or not 1 <= int(fields["meeting_day"]) <= 12
            or not 1 <= int(fields["race"]) <= 12):
        raise CoverageError("JV-Data race/date identity mismatch")
    return tuple(fields[key] for key in (
        "year", "month_day", "venue", "meeting", "meeting_day", "race"
    ))


def parse_jvdata_prestart_racecard(ra_record, se_records, day):
    """Parse one RA + every SE in the same race, no guesswork or paid output.

    The returned horse-number set remains owner-private and only a *candidate*
    for cross-provider comparison. No claim that the record has been
    authenticated, finalized, updated with scratches or obtained in time.
    """
    if type(day) is not str or not _valid_date(day):
        raise CoverageError("Invalid target JV-Data date")
    ra = _fixed(ra_record, b"RA", RA_LENGTH)
    key = _identity(ra, day)
    post = _ascii(ra, 873, 877)
    hour, minute = int(post[:2]), int(post[2:])
    if hour > 23 or minute > 59:
        raise CoverageError("Invalid JV-Data scheduled off time")
    registered = int(_ascii(ra, 881, 883))
    if not 4 <= registered <= 18:
        raise CoverageError("Unsupported JV-Data registered runner count")
    if (not isinstance(se_records, (list, tuple))
            or len(se_records) != registered):
        raise CoverageError("Incomplete JV-Data prestart horse list")

    # Same RA byte offsets in numbered racecards and historical RA results.
    # This is a scheduled course CANDIDATE, not a final JRA confirmation.
    distance_text = ra[697:701].decode("ascii", errors="replace")
    track_code = ra[705:707].decode("ascii", errors="replace")
    distance = (int(distance_text) if distance_text.isdigit()
                and 400 <= int(distance_text) <= 10000 else None)
    surface = ("芝" if track_code in TURF_TRACK_CODES else
               "ダート" if track_code in DIRT_TRACK_CODES else None)
    numbers, pedigree_ids = set(), set()
    for raw in se_records:
        se = _fixed(raw, b"SE", SE_LENGTH)
        if _identity(se, day) != key:
            raise CoverageError("Foreign JV-Data race horse")
        number = _ascii(se, 28, 30)
        frame = _ascii(se, 27, 28)
        horse_id = _ascii(se, 30, 40)
        if (not NUMBER.fullmatch(number)
                or not 1 <= int(frame) <= 8
                or horse_id == "0000000000"
                or number in numbers or horse_id in pedigree_ids):
            raise CoverageError("Duplicate or unnumbered JV-Data starter")
        numbers.add(number)
        pedigree_ids.add(horse_id)

    if len(numbers) != registered:
        raise CoverageError("JV-Data roster count differs from RA")
    return {
        "version": VERSION,
        "date": day, "track": TRACKS[key[2]], "race": int(key[5]),
        "postTimeCandidate": f"{hour:02d}:{minute:02d}",
        "distanceMetersCandidate": distance,
        "surfaceCandidate": surface,
        "registeredRunnerCount": registered,
        "horseNumbersCandidate": sorted(int(n) for n in numbers),
        "sourceRecordCategory": "numbered_racecard_not_final_changes",
        "privateInputOnly": True,
        "sourceDataUseRightsVerified": False,
        "independentlyAuthenticated": False,
        "prestartDeliveryTimeVerified": False,
        "finalStarterListVerified": False,
        "scratchStatusVerified": False,
        "latestGoingVerified": False,
        "officialFinalPostTimeVerified": False,
        "formalTenFactorReady": False,
        "bettingReady": False,
        "newProviderRequests": 0,
        "researchOnly": True,
        "note": "JRA-VAN RA/SEの馬番付き出馬表候補のみ。AV/WE/TC等の直前変更・真正性は未確認。",
    }


def compare_jvdata_candidate_to_jrdb(jv, jrdb_programme, jrdb_entries):
    """Cross-check raw-source race identities without granting official status.

    `jrdb_programme` must be an ALREADY normalized one-race /tra dict.
    `jrdb_entries` are validated per-horse /tky dicts for that same race.
    A mismatch means HOLD, not a weaker horse or permission to pick runners.
    """
    if (not isinstance(jv, dict) or jv.get("version") != VERSION
            or jv.get("privateInputOnly") is not True
            or jv.get("sourceDataUseRightsVerified") is not False
            or jv.get("researchOnly") is not True
            or any(jv.get(key) is not False for key in (
                "independentlyAuthenticated", "prestartDeliveryTimeVerified",
                "finalStarterListVerified", "scratchStatusVerified",
                "latestGoingVerified", "officialFinalPostTimeVerified",
                "formalTenFactorReady", "bettingReady"
            ))
            or not isinstance(jrdb_programme, dict)
            or jrdb_programme.get("programmeOnly") is not True
            or jrdb_programme.get("horsesVerified") is not False
            or jrdb_programme.get("racedate") != jv.get("date")
            or jrdb_programme.get("track") != jv.get("track")
            or jrdb_programme.get("race") != jv.get("race")
            or not isinstance(jrdb_entries, list)
            or not 4 <= len(jrdb_entries) <= 18):
        raise CoverageError("Invalid two-provider race comparison")
    expected_key = jrdb_programme.get("racekey")
    if type(expected_key) is not str:
        raise CoverageError("Missing JRDB programme key")
    numbers, withdrawn = set(), set()
    for entry in jrdb_entries:
        if (not isinstance(entry, dict)
                or entry.get("racekey") != expected_key
                or entry.get("racedate") != jv["date"]
                or type(entry.get("horse_number")) is not str
                or not NUMBER.fullmatch(entry["horse_number"])
                or entry["horse_number"] in numbers
                or entry.get("withdrawn_flag") not in ("0", "1")):
            raise CoverageError("Invalid JRDB entry for candidate comparison")
        numbers.add(entry["horse_number"])
        if entry["withdrawn_flag"] == "1":
            withdrawn.add(entry["horse_number"])

    candidate = jv.get("horseNumbersCandidate")
    if (not isinstance(candidate, list)
            or len(candidate) != jv.get("registeredRunnerCount")
            or len(candidate) > 18 or len(candidate) < 4
            or any(type(n) is not int or n < 1 or n > 18 for n in candidate)
            or len(set(candidate)) != len(candidate)):
        raise CoverageError("Invalid JV-Data candidate runner set")
    matching_numbers = {f"{number:02d}" for number in candidate} == numbers
    matching_post = (type(jrdb_programme.get("post_time")) is str
                     and jrdb_programme["post_time"] == jv.get("postTimeCandidate"))
    matching_count = jrdb_programme.get("headcount") == len(candidate)
    matched = matching_numbers and matching_post and matching_count
    return {
        "version": "owner-jvdata-jrdb-crosscheck-1",
        "track": jv["track"], "race": jv["race"],
        "status": "candidate_matched_not_final" if matched else "hold_source_mismatch",
        "raceAndNumbersCandidateMatch": bool(matching_numbers),
        "scheduledPostCandidateMatch": bool(matching_post),
        "registeredCountCandidateMatch": bool(matching_count),
        "withdrawalStatusUnresolved": True,
        "possibleWithdrawnInJrdb": len(withdrawn) > 0,
        "independentOfficialJraVerified": False,
        "currentStartersVerified": False,
        "currentScratchesVerified": False,
        "currentGoingVerified": False,
        "finalPostTimeVerified": False,
        "productionPredictionReady": False,
        "bettingReady": False,
        "actualPurchase": False,
        "newJrdbProviderRequests": 0,
        "privateOwnerOnly": True, "researchOnly": True,
        "note": "同日同場同Rの馬番と当初発走予定だけ比較。直前変更確認・最終公式証明ではない。",
    }
