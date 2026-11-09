"""Private, offline /dky × /dse historic starter join for a future 10-point study.

A vetted historical caller must obtain these records under valid JRDB terms.
Do NOT expose the return value via an HTTP route: it intentionally includes
licensed horse/rider/trainer identifiers. This function does no fetching,
logging, persistence or scoring. It cannot attest original result finality or
publication time: those MUST be verified separately before a time-cut study.
Incomplete/withdrawn/duplicate/dead-heat results fail closed.
"""
import re
from datetime import date

VERSION = "owner-past-jockey-trainer-join-1"
TRACK_CODES = frozenset(f"{n:02d}" for n in range(1, 11))
RACEKEY = re.compile(r"[0-9]{4}[0-9a-f]{2}(?:0[1-9]|1[0-2])\Z")
HORSE_ID = re.compile(r"[A-Za-z0-9]{12}\Z")
RESULTKEY = re.compile(r"[0-9]{16}\Z")
NUMBER = re.compile(r"(?:0[1-9]|1[0-8])\Z")
STAFF_CODE = re.compile(r"[0-9]{5}\Z")
DAY = re.compile(r"20[0-9]{6}\Z")
MAX_STARTERS = 18


class PastStaffJoinError(ValueError):
    """Never report private provider rows or IDs in exception text."""


def _day(value):
    if not isinstance(value, str) or not DAY.fullmatch(value):
        raise PastStaffJoinError("Invalid historic date")
    try:
        d = date.fromisoformat(f"{value[:4]}-{value[4:6]}-{value[6:8]}")
        if d.strftime("%Y%m%d") == value:
            return d
    except ValueError:
        pass
    raise PastStaffJoinError("Invalid historic date")


def _identity(row, racekey, day):
    if (not isinstance(row, dict)
            or row.get("racekey") != racekey
            or row.get("racedate") != day
            or not isinstance(row.get("horse_number"), str)
            or not NUMBER.fullmatch(row["horse_number"])
            or not isinstance(row.get("horse_id"), str)
            or not HORSE_ID.fullmatch(row["horse_id"])
            or not isinstance(row.get("resultkey"), str)
            or not RESULTKEY.fullmatch(row["resultkey"])
            or not row["resultkey"].endswith(day)):
        raise PastStaffJoinError("Historic horse identity not aligned")
    return int(row["horse_number"])


def _indexed(rows, racekey, day):
    if not isinstance(rows, list) or not 3 <= len(rows) <= MAX_STARTERS:
        raise PastStaffJoinError("Historic result population incomplete")
    index, horses, results = {}, set(), set()
    for row in rows:
        number = _identity(row, racekey, day)
        if number in index or row["horse_id"] in horses or row["resultkey"] in results:
            raise PastStaffJoinError("Duplicate historic runner")
        index[number] = row
        horses.add(row["horse_id"])
        results.add(row["resultkey"])
    return index


def _weight(value):
    try:
        kg = float(value)
    except (TypeError, ValueError, OverflowError):
        raise PastStaffJoinError("Invalid historic carried weight") from None
    if (isinstance(value, bool) or not 44 <= kg <= 66
            or 2 * kg != int(2 * kg)):
        raise PastStaffJoinError("Invalid historic carried weight")
    return kg


def _position(value):
    if isinstance(value, bool) or type(value) not in (int, str):
        raise PastStaffJoinError("Missing or ambiguous historic placing")
    if isinstance(value, str) and not re.fullmatch(r"(?:0?[1-9]|1[0-8])", value):
        raise PastStaffJoinError("Missing or ambiguous historic placing")
    number = int(value)
    if not 1 <= number <= 18:
        raise PastStaffJoinError("Missing or ambiguous historic placing")
    return number


def join_jrdb_past_jockey_trainer(dky_rows, dse_rows, *, racekey, racedate):
    """Strict per-race /dky prestart identity joined with /dse postrace placing.

    Returned object contains PRIVATE provider IDs and may ONLY flow into
    internal, time-cut controlled aggregate code; never serialize to clients.

    The join itself is not proof the historical result was already published
    before a later prediction capture. That must be established by a separate
    trusted result publication timestamp and independent source review.
    """
    if (not isinstance(racekey, str) or not RACEKEY.fullmatch(racekey)
            or racekey[:2] not in TRACK_CODES):
        raise PastStaffJoinError("Invalid past race key")
    _day(racedate)
    if racekey[2:4] != racedate[2:4]:
        raise PastStaffJoinError("Race key year differs from racing date")
    starters = _indexed(dky_rows, racekey, racedate)
    results = _indexed(dse_rows, racekey, racedate)
    if set(starters) != set(results):
        raise PastStaffJoinError("Past entrants and placing rows disagree")
    out, places = [], set()
    for number in sorted(starters):
        starter, result = starters[number], results[number]
        if (starter["horse_id"] != result["horse_id"]
                or starter["resultkey"] != result["resultkey"]
                or starter.get("withdrawn_flag") not in (None, "", "0", 0)
                or result.get("trouble_classification") not in (None, "", "0", 0)):
            raise PastStaffJoinError("Past starter/result provenance mismatch")
        frame = starter.get("bracket_number")
        if (type(frame) not in (int, str)
                or not str(frame).isdigit()
                or not 1 <= int(frame) <= 8
                or not isinstance(starter.get("jockey_cd"), str)
                or not STAFF_CODE.fullmatch(starter["jockey_cd"])
                or not isinstance(starter.get("trainer_cd"), str)
                or not STAFF_CODE.fullmatch(starter["trainer_cd"])):
            raise PastStaffJoinError("Missing historic rider/trainer identity")
        finish = _position(result.get("order_of_finish"))
        if finish > len(starters) or finish in places:
            raise PastStaffJoinError("Dead heat or impossible historic finish")
        places.add(finish)
        out.append({
            "number": number, "horseRef": starter["horse_id"],
            "frame": int(frame), "carriedKg": _weight(starter.get("weight_to_carry")),
            "jockeyRef": starter["jockey_cd"],
            "trainerRef": starter["trainer_cd"],
            "finish": finish,
        })
    if places != set(range(1, len(starters) + 1)):
        raise PastStaffJoinError("Historic finish order incomplete")
    return {
        "version": VERSION, "raceDate": racedate,
        "racekey": racekey, "horseRows": out,
        "completeStarterResultJoin": True,
        "includesPrivateProviderIdentifiers": True,
        "officialJraVerified": False,
        "resultPublicationTimeVerified": False,
        "eligibleForTimeCutScoring": False,
        "formalJockeyStableGrade": None,
        "sourceReadCount": 0,
    }
