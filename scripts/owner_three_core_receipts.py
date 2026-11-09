"""HMAC first-observation receipts for the uncalibrated 70-point core study.

Only private, opt-in JRDB /history may issue these *prestart* attestations.
They are NOT 10-factor grades, official schedule verification, model
calibration, bets, purchases, ROI or a result source. Nothing is persisted here.
"""
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta, timezone

from evaluation_policy import POINTS
from jrdb_coverage import CoverageError
from owner_rebound_receipts import _timestamp, _day

VERSION = "owner-three-core-receipt-1"
RESEARCH_VERSION = "owner-three-core-research-1"
DOMAIN = b"keiba-nine/owner-three-core-research-attestation/v1"
MAX_RACES = 36
KEYS = ("training", "course_distance", "pace")
WEIGHTS = {"training": 30, "course_distance": 20, "pace": 20}
GRADES = frozenset(("S", "A", "B", "C"))
TRACKS = frozenset(("札幌", "函館", "福島", "新潟", "東京",
                    "中山", "中京", "京都", "阪神", "小倉"))
JST = timezone(timedelta(hours=9))
FIELDS = frozenset(("version", "date", "track", "race", "sourceKind",
                    "capturedAt", "scheduledOffAt", "raceRunnerCount",
                    "observedRunnerCount", "horses", "researchOnly",
                    "officialJraVerified", "sourceHypothesesUncalibrated",
                    "actualPurchase", "predictionReady"))


class CoreReceiptError(ValueError):
    """Safe message only: never disclose JRDB raw source rows."""


def _key(secret):
    if not isinstance(secret, str) or len(secret) < 32:
        raise CoreReceiptError("Private signing credential unavailable")
    return hmac.new(secret.encode("utf-8"), DOMAIN, hashlib.sha256).digest()


def _seal(snapshot, secret):
    encoded = json.dumps(snapshot, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hmac.new(_key(secret), encoded, hashlib.sha256).hexdigest()


def _validate_snapshot(snapshot):
    if (not isinstance(snapshot, dict) or set(snapshot) != FIELDS
            or snapshot["version"] != VERSION
            or snapshot["sourceKind"] != "prestart-uncalibrated-70-research"
            or snapshot["researchOnly"] is not True
            or snapshot["officialJraVerified"] is not False
            or snapshot["sourceHypothesesUncalibrated"] is not True
            or snapshot["actualPurchase"] is not False
            or snapshot["predictionReady"] is not False):
        raise CoreReceiptError("Invalid research snapshot")
    day = _day(snapshot["date"])
    track, race = snapshot["track"], snapshot["race"]
    if (track not in TRACKS or type(race) is not int or not 1 <= race <= 12
            or type(snapshot["raceRunnerCount"]) is not int
            or not 1 <= snapshot["raceRunnerCount"] <= 18
            or type(snapshot["observedRunnerCount"]) is not int
            or not 1 <= snapshot["observedRunnerCount"] <= snapshot["raceRunnerCount"]
            or not isinstance(snapshot["horses"], list)
            or len(snapshot["horses"]) != snapshot["observedRunnerCount"]):
        raise CoreReceiptError("Invalid research race count")
    captured = _timestamp(snapshot["capturedAt"])
    off = _timestamp(snapshot["scheduledOffAt"])
    if (captured >= off or (off - captured).total_seconds() > 7*24*3600
            or off.astimezone(JST).date().strftime("%Y%m%d") != day):
        raise CoreReceiptError("Research was not captured before provisional off")
    last = 0
    for horse in snapshot["horses"]:
        if (not isinstance(horse, dict)
                or set(horse) != {"number", "bands", "rawThirdPoints"}
                or type(horse["number"]) is not int
                or not last < horse["number"] <= 18
                or type(horse["rawThirdPoints"]) is not int
                or not 0 <= horse["rawThirdPoints"] <= 210
                or not isinstance(horse["bands"], dict)
                or set(horse["bands"]) != set(KEYS)
                or any(horse["bands"][k] not in GRADES for k in KEYS)
                or horse["rawThirdPoints"] != sum(
                    POINTS[horse["bands"][k]] * WEIGHTS[k] for k in KEYS)):
            raise CoreReceiptError("Research study score inconsistency")
        last = horse["number"]
    return day, track, race


def issue_three_core_receipts(history, programme, secret, day, now=None):
    """Sign complete research-only rows before the provisional start time.

    An incomplete runner is omitted instead of given zero, a C, or a
    made-up 70-point comparison. Start-time checks use the server clock.
    """
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    if (not isinstance(history, dict) or history.get("date") != day
            or history.get("predictionReady") is not False):
        raise CoreReceiptError("Unverified research source")
    core = history.get("threeCoreResearch")
    if (not isinstance(core, dict)
            or core.get("version") != RESEARCH_VERSION
            or core.get("coreWeightTotal") != 70
            or core.get("coreFactorWeights") != WEIGHTS
            or core.get("factorGradesVerified") != 0
            or core.get("formalScoreReady") is not False
            or core.get("overallPredictionReady") is not False
            or core.get("officialJraVerified") is not False
            or core.get("historicalBandsNotCalibrated") is not True
            or core.get("bettingReady") is not False
            or core.get("autoPurchase") is not False
            or core.get("changesExistingTickets") is not False
            or core.get("researchOnly") is not True
            or core.get("privateOwnerOnly") is not True
            or not isinstance(core.get("races"), list)
            or core.get("raceCount") != len(core["races"])
            or len(core["races"]) > MAX_RACES
            or not isinstance(programme, list)
            or len(programme) != len(core["races"])):
        raise CoreReceiptError("Unsafe three-core source")
    by_programme = {}
    for row in programme:
        if (not isinstance(row, dict) or row.get("racedate") != day
                or row.get("track") not in TRACKS
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoreReceiptError("Invalid programme identity")
        key = row["track"], row["race"]
        if key in by_programme:
            raise CoreReceiptError("Duplicate programme race")
        by_programme[key] = row
    out, seen, skipped = [], set(), 0
    for race in core["races"]:
        if not isinstance(race, dict):
            raise CoreReceiptError("Invalid research race")
        key = race.get("track"), race.get("race")
        if key in seen or key not in by_programme:
            raise CoreReceiptError("Research programme mismatch")
        seen.add(key)
        horses = race.get("horses")
        if (not isinstance(horses, list) or len(horses) > 18
                or race.get("runnerCount") != len(horses)
                or type(race.get("runnerCount")) is not int
                or race.get("formalGradeReady") is not False
                or race.get("trifectaReady") is not False):
            raise CoreReceiptError("Invalid scored race")
        observed = []
        for row in horses:
            if (not isinstance(row, dict)
                    or type(row.get("number")) is not int
                    or row.get("formalScore100") is not None
                    or row.get("formalGrade") != "未評価"
                    or row.get("formalRank") is not None
                    or row.get("bettingReady") is not False):
                raise CoreReceiptError("Unsafe study horse")
            raw = row.get("rawThirdPoints")
            if raw is None:
                if row.get("evidenceScore70") is not None:
                    raise CoreReceiptError("Partial research score")
                continue
            observed.append({
                "number": row["number"],
                "bands": {k: row["bands"][k] for k in KEYS},
                "rawThirdPoints": raw,
            })
        if not observed:
            continue
        post = by_programme[key].get("post_time")
        if (not isinstance(post, str)
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", post)):
            skipped += 1
            continue
        off = datetime.fromisoformat(
            f"{day[:4]}-{day[4:6]}-{day[6:]}T{post}:00+09:00")
        if now >= off.astimezone(timezone.utc):
            skipped += 1
            continue
        snap = {
            "version": VERSION, "date": day,
            "track": key[0], "race": key[1],
            "sourceKind": "prestart-uncalibrated-70-research",
            "capturedAt": now.isoformat(),
            "scheduledOffAt": off.astimezone(timezone.utc).isoformat(),
            "raceRunnerCount": race["runnerCount"],
            "observedRunnerCount": len(observed),
            "horses": sorted(observed, key=lambda r: r["number"]),
            "researchOnly": True, "officialJraVerified": False,
            "sourceHypothesesUncalibrated": True,
            "actualPurchase": False, "predictionReady": False,
        }
        _validate_snapshot(snap)
        out.append({"snapshot": snap, "signature": _seal(snap, secret)})
    if seen != set(by_programme):
        raise CoreReceiptError("Unmatched research race")
    return {
        "version": VERSION, "date": day,
        "receiptCount": len(out), "receipts": out,
        "postOffOrMissingTimeRaces": skipped,
        "serverSigned": True, "jraScheduleVerified": False,
        "officialResultsVerified": False, "calibrationReady": False,
        "bettingReady": False, "actualPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
    }


def verify_three_core_receipts(receipts, secret, day):
    _day(day)
    if not isinstance(receipts, list) or len(receipts) > MAX_RACES:
        raise CoreReceiptError("Invalid research receipt list")
    seen, snapshots = set(), []
    for item in receipts:
        if not isinstance(item, dict) or set(item) != {"snapshot", "signature"}:
            raise CoreReceiptError("Invalid sealed research record")
        snap = item["snapshot"]
        key = _validate_snapshot(snap)
        if (key[0] != day or key in seen
                or not isinstance(item["signature"], str)
                or not re.fullmatch("[a-f0-9]{64}", item["signature"])
                or not hmac.compare_digest(
                    item["signature"], _seal(snap, secret))):
            raise CoreReceiptError("Unverified study receipt")
        seen.add(key)
        snapshots.append(snap)
    return snapshots
