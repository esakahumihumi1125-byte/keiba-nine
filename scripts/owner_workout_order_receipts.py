"""HMAC-sealed PRESTART, owner-only S/A/B/C within-band workout order.

Source is the private same-request /tcy comparison, never a user form.
No numeric JRDB index or horse identity goes into the snapshot. This does
not create a scoring formula, official result, purchase or bet receipt.
"""
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta, timezone

from jrdb_coverage import CoverageError
from owner_workout_index_order import VERSION as ORDER_VERSION

VERSION = "owner-workout-order-lock-1"
DOMAIN = b"keiba-nine/owner-workout-index-research-lock/v1"
BANDS = ("S", "A", "B", "C")
TRACKS = frozenset(("札幌", "函館", "福島", "新潟", "東京",
                    "中山", "中京", "京都", "阪神", "小倉"))
JST = timezone(timedelta(hours=9))
MAX_RACES = 36
MAX_AGE = timedelta(days=7)
SNAP_FIELDS = frozenset((
    "version", "date", "track", "race", "sourceKind",
    "capturedAt", "scheduledOffAt", "raceRunnerCount", "horses",
    "researchOnly", "officialJraVerified", "modelCalibrated",
    "predictionReady", "actualPurchase",
))


class WorkoutLockError(ValueError):
    pass


def _day(day):
    if not isinstance(day, str) or not re.fullmatch(r"20\d{6}", day):
        raise WorkoutLockError("Invalid study day")
    try:
        datetime.strptime(day, "%Y%m%d")
    except ValueError:
        raise WorkoutLockError("Invalid calendar day") from None
    return day


def _clock(when):
    if not isinstance(when, datetime) or when.tzinfo is None or when.utcoffset() is None:
        raise WorkoutLockError("Timezone-aware server time required")
    return when.astimezone(timezone.utc)


def _secret(secret):
    if not isinstance(secret, str) or len(secret) < 16:
        raise WorkoutLockError("Signing key unavailable")
    return hmac.new(secret.encode("utf-8"), DOMAIN, hashlib.sha256).digest()


def _sign(snapshot, secret):
    data = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                      allow_nan=False, separators=(",", ":")).encode("utf-8")
    return hmac.new(_secret(secret), data, hashlib.sha256).hexdigest()


def _validate(snapshot):
    if (not isinstance(snapshot, dict) or set(snapshot) != SNAP_FIELDS
            or snapshot["version"] != VERSION
            or snapshot["sourceKind"] != "prestart-workout-index-order"
            or snapshot["researchOnly"] is not True
            or snapshot["officialJraVerified"] is not False
            or snapshot["modelCalibrated"] is not False
            or snapshot["predictionReady"] is not False
            or snapshot["actualPurchase"] is not False):
        raise WorkoutLockError("Unexpected workout lock mode")
    day = _day(snapshot["date"])
    track, race = snapshot["track"], snapshot["race"]
    if (track not in TRACKS or type(race) is not int or not 1 <= race <= 12
            or type(snapshot["raceRunnerCount"]) is not int
            or not 2 <= snapshot["raceRunnerCount"] <= 18
            or not isinstance(snapshot["horses"], list)
            or len(snapshot["horses"]) != snapshot["raceRunnerCount"]):
        raise WorkoutLockError("Invalid workout lock roster")
    try:
        captured = datetime.fromisoformat(snapshot["capturedAt"].replace("Z", "+00:00"))
        off = datetime.fromisoformat(snapshot["scheduledOffAt"].replace("Z", "+00:00"))
        captured, off = _clock(captured), _clock(off)
    except (ValueError, TypeError, AttributeError):
        raise WorkoutLockError("Invalid recorded time") from None
    if (not captured < off or off - captured > MAX_AGE
            or off.astimezone(JST).strftime("%Y%m%d") != day):
        raise WorkoutLockError("Workout lock must precede race start")
    numbers = set()
    bands = {b: [] for b in BANDS}
    last = 0
    for item in snapshot["horses"]:
        if (not isinstance(item, dict)
                or set(item) != {"number", "trainingBand", "withinBandRank"}
                or type(item["number"]) is not int
                or not last < item["number"] <= 18
                or item["trainingBand"] not in BANDS
                or type(item["withinBandRank"]) is not int
                or not 1 <= item["withinBandRank"] <= 18):
            raise WorkoutLockError("Invalid workout band entry")
        numbers.add(item["number"])
        bands[item["trainingBand"]].append(item["withinBandRank"])
        last = item["number"]
    if len(numbers) != snapshot["raceRunnerCount"]:
        raise WorkoutLockError("Duplicate workout runners")
    for ranks in bands.values():
        if not ranks:
            continue
        unique = sorted(set(ranks))
        # Competition ranks: 1,1,3 are valid; invented gaps are not.
        if unique[0] != 1 or any(next_rank != sum(r <= rank for r in ranks) + 1
                                 for rank, next_rank in zip(unique, unique[1:])):
            raise WorkoutLockError("Workout rank gap inconsistent")
    return day, track, race


def issue_workout_locks(report, secret, now):
    """Sign only complete original prestart observations from same report."""
    now = _clock(now)
    if (not isinstance(report, dict)
            or report.get("version") != "jrdb-owner-auto-draft-1"
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("officialJraVerified") is not False
            or report.get("overallPredictionReady") is not False
            or not isinstance(report.get("races"), list)
            or report.get("raceCount") != len(report["races"])
            or report["raceCount"] > 120
            or not isinstance(report.get("workoutIndexOrder"), dict)):
        raise WorkoutLockError("Untrusted original workout order")
    day = _day(report["date"])
    study = report["workoutIndexOrder"]
    if (study.get("version") != ORDER_VERSION
            or study.get("date") != day
            or study.get("raceCount") != report["raceCount"]
            or study.get("researchOnly") is not True
            or study.get("privateOwnerOnly") is not True
            or study.get("predictionReady") is not False
            or study.get("bettingReady") is not False
            or study.get("rawIndexesIncluded") is not False
            or not isinstance(study.get("races"), list)
            or study.get("studiedRaceCount") != len(study["races"])):
        raise WorkoutLockError("Study contract mismatch")
    by_coord = {}
    for race in report["races"]:
        coord = (race.get("track"), race.get("race"))
        if coord in by_coord:
            raise WorkoutLockError("Duplicate draft race")
        by_coord[coord] = race
    seen, receipts = set(), []
    for row in study["races"]:
        coord = row.get("track"), row.get("race")
        old = by_coord.get(coord)
        if (coord in seen or old is None
                or old.get("status") not in ("hold", "provisional_draft")
                or old.get("reason") in ("after_provisional_off", "provider_withdrawal",
                                          "archived_earlier_draft", "missing_research")
                or not isinstance(row.get("runners"), list)
                or type(row.get("runnerCount")) is not int
                or len(row["runners"]) != row["runnerCount"]
                or not isinstance(old.get("runners"), list)
                or len(old["runners"]) != row["runnerCount"]):
            raise WorkoutLockError("Study does not match guarded draft")
        seen.add(coord)
        post = old.get("postTime")
        if not isinstance(post, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", post):
            continue
        off = datetime.fromisoformat(
            day[:4] + "-" + day[4:6] + "-" + day[6:] + "T" + post + ":00+09:00"
        ).astimezone(timezone.utc)
        if now >= off:
            continue
        names = {h["number"]: h["training"] for h in old["runners"]}
        if (len(names) != row["runnerCount"] or
                len(set(names)) != row["runnerCount"] or
                any(names.get(h.get("number")) != h.get("trainingBand")
                    for h in row["runners"])):
            raise WorkoutLockError("Band mismatch against original draft")
        snap = {
            "version": VERSION, "date": day,
            "track": coord[0], "race": coord[1],
            "sourceKind": "prestart-workout-index-order",
            "capturedAt": now.isoformat(timespec="seconds"),
            "scheduledOffAt": off.isoformat(timespec="seconds"),
            "raceRunnerCount": row["runnerCount"],
            "horses": sorted(
                [{"number": h["number"], "trainingBand": h["trainingBand"],
                  "withinBandRank": h["withinBandRank"]}
                 for h in row["runners"]], key=lambda h: h["number"]),
            "researchOnly": True, "officialJraVerified": False,
            "modelCalibrated": False, "predictionReady": False,
            "actualPurchase": False,
        }
        _validate(snap)
        receipts.append({"snapshot": snap, "signature": _sign(snap, secret)})
    if len(receipts) > MAX_RACES:
        raise WorkoutLockError("Too many workout order locks")
    return receipts


def verify_workout_locks(receipts, secret, day):
    _day(day)
    if not isinstance(receipts, list) or not 1 <= len(receipts) <= MAX_RACES:
        raise WorkoutLockError("Invalid workout receipt batch")
    seen, frozen = set(), []
    for item in receipts:
        if not isinstance(item, dict) or set(item) != {"snapshot", "signature"}:
            raise WorkoutLockError("Unexpected workout receipt row")
        snapshot = item["snapshot"]
        identity = _validate(snapshot)
        signature = item["signature"]
        if (identity[0] != day or identity in seen
                or not isinstance(signature, str)
                or not re.fullmatch(r"[a-f0-9]{64}", signature)
                or not hmac.compare_digest(signature, _sign(snapshot, secret))):
            raise WorkoutLockError("Invalid workout receipt signature")
        seen.add(identity)
        frozen.append(snapshot)
    return frozen
