"""HMAC-seal uncalibrated 85-weight observations BEFORE provisional race-off.

The complete five-factor research subset is recorded for later out-of-time
study, never promoted to formal S/A/B/C, betting, official results or ROI.
All input comes from the authenticated private /history coordinator. No JRDB
calls, network, browser-supplied values or persistent writes are made here.
"""
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone, timedelta

from evaluation_policy import FACTORS, POINTS, POLICY_VERSION
from jrdb_coverage import CoverageError
from owner_rebound_receipts import _day, _timestamp
from owner_three_core_receipts import TRACKS

VERSION = "owner-five-core-receipt-1"
RESEARCH_VERSION = "owner-five-core-research-1"
DOMAIN = b"keiba-nine/owner-five-core-study-prestart/v1"
KEYS = ("training", "course_distance", "pace", "ground", "recent")
WEIGHTS = {k: FACTORS[k] for k in KEYS}
BANDS = frozenset(POINTS)
MAX_RACES = 36
MAX_AGE = 7 * 24 * 3600
JST = timezone(timedelta(hours=9))
SNAP_FIELDS = frozenset((
    "version", "date", "track", "race", "sourceKind",
    "capturedAt", "scheduledOffAt", "raceRunnerCount",
    "observedRunnerCount", "horses", "researchOnly",
    "sourceHypothesesUncalibrated", "officialJraVerified",
    "predictionReady", "actualPurchase",
))
assert sum(WEIGHTS.values()) == 85 and WEIGHTS["recent"] == 3


class FiveCoreReceiptError(ValueError):
    """Safe public error without raw source rows or signing credentials."""


def _secret(secret):
    if not isinstance(secret, str) or len(secret) < 32:
        raise FiveCoreReceiptError("Owner signing secret unavailable")
    return hmac.new(secret.encode("utf-8"), DOMAIN, hashlib.sha256).digest()


def _sign(snapshot, secret):
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                     allow_nan=False, separators=(",", ":")).encode("utf-8")
    return hmac.new(_secret(secret), raw, hashlib.sha256).hexdigest()


def _validate(snapshot):
    if (not isinstance(snapshot, dict) or set(snapshot) != SNAP_FIELDS
            or snapshot.get("version") != VERSION
            or snapshot.get("sourceKind") != "prestart-uncalibrated-85-research"
            or snapshot.get("researchOnly") is not True
            or snapshot.get("sourceHypothesesUncalibrated") is not True
            or snapshot.get("officialJraVerified") is not False
            or snapshot.get("predictionReady") is not False
            or snapshot.get("actualPurchase") is not False):
        raise FiveCoreReceiptError("Invalid 85-weight research snapshot")
    day = _day(snapshot.get("date"))
    track, race = snapshot.get("track"), snapshot.get("race")
    if (track not in TRACKS or type(race) is not int or not 1 <= race <= 12
            or type(snapshot.get("raceRunnerCount")) is not int
            or not 1 <= snapshot["raceRunnerCount"] <= 18
            or type(snapshot.get("observedRunnerCount")) is not int
            or not 1 <= snapshot["observedRunnerCount"] <= snapshot["raceRunnerCount"]
            or not isinstance(snapshot.get("horses"), list)
            or len(snapshot["horses"]) != snapshot["observedRunnerCount"]):
        raise FiveCoreReceiptError("85-weight research roster mismatch")
    captured = _timestamp(snapshot.get("capturedAt"))
    off = _timestamp(snapshot.get("scheduledOffAt"))
    if (captured >= off or not 0 < (off-captured).total_seconds() <= MAX_AGE
            or off.astimezone(JST).strftime("%Y%m%d") != day):
        raise FiveCoreReceiptError("85-weight observation outside prestart window")
    last = 0
    for item in snapshot["horses"]:
        if (not isinstance(item, dict)
                or set(item) != {"number", "bands", "rawThirdPoints"}
                or type(item["number"]) is not int
                or not last < item["number"] <= 18
                or not isinstance(item["bands"], dict)
                or set(item["bands"]) != set(KEYS)
                or any(item["bands"][k] not in BANDS for k in KEYS)
                or type(item["rawThirdPoints"]) is not int
                or not 0 <= item["rawThirdPoints"] <= 255
                or item["rawThirdPoints"] != sum(
                    WEIGHTS[k] * POINTS[item["bands"][k]] for k in KEYS)):
            raise FiveCoreReceiptError("85-weight factor arithmetic mismatch")
        last = item["number"]
    return day, track, race


def issue_five_core_receipts(history, programme, secret, day, now=None):
    """Sign available complete rows only; omit missing horses and started races."""
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    report = history.get("fiveCoreResearch") if isinstance(history, dict) else None
    if (not isinstance(history, dict) or history.get("date") != day
            or history.get("predictionReady") is not False
            or not isinstance(report, dict)
            or report.get("version") != RESEARCH_VERSION
            or report.get("policyVersion") != POLICY_VERSION
            or report.get("factorWeights") != WEIGHTS
            or report.get("observedWeightTotal") != 85
            or report.get("factorGradesVerified") != 0
            or report.get("overallPredictionReady") is not False
            or report.get("formalScoreReady") is not False
            or report.get("officialJraVerified") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False
            or report.get("changesExistingTickets") is not False
            or report.get("changesExistingCoreReceipts") is not False
            or report.get("historicalBandsNotCalibrated") is not True
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > MAX_RACES
            or report.get("raceCount") != len(report["races"])
            or not isinstance(programme, list)
            or len(programme) != len(report["races"])):
        raise FiveCoreReceiptError("Unverified 85-weight study input")
    programme_by_id = {}
    for p in programme:
        if (not isinstance(p, dict) or p.get("racedate") != day
                or p.get("track") not in TRACKS or
                type(p.get("race")) is not int or not 1 <= p["race"] <= 12):
            raise FiveCoreReceiptError("Invalid programme entry")
        key = p["track"], p["race"]
        if key in programme_by_id:
            raise FiveCoreReceiptError("Duplicate programme coordinate")
        programme_by_id[key] = p
    seen, receipts, expired = set(), [], 0
    for race in report["races"]:
        if not isinstance(race, dict):
            raise FiveCoreReceiptError("Invalid research race")
        coord = race.get("track"), race.get("race")
        if coord in seen or coord not in programme_by_id:
            raise FiveCoreReceiptError("85-weight race not on same programme")
        seen.add(coord)
        runners = race.get("horses")
        if (not isinstance(runners, list) or not 0 <= len(runners) <= 18
                or type(race.get("runnerCount")) is not int
                or race["runnerCount"] != len(runners)
                or race.get("formalGradeReady") is not False
                or race.get("trifectaReady") is not False
                or race.get("comparisonIsFormalRank") is not False
                or type(race.get("completeObserved")) is not int):
            raise FiveCoreReceiptError("Invalid five-factor research field")
        number_set, complete, saved = set(), 0, []
        for h in runners:
            if (not isinstance(h, dict) or type(h.get("number")) is not int
                    or not 1 <= h["number"] <= 18 or h["number"] in number_set
                    or h.get("formalScore100") is not None
                    or h.get("formalGrade") != "未評価"
                    or h.get("formalRank") is not None
                    or h.get("scoreIsCalibrated") is not False
                    or h.get("bettingReady") is not False
                    or not isinstance(h.get("bands"), dict)
                    or set(h["bands"]) != set(KEYS)):
                raise FiveCoreReceiptError("Promoted or duplicate research runner")
            number_set.add(h["number"])
            missing = [k for k in KEYS if h["bands"][k] == "未評価"]
            raw = h.get("rawThirdPoints")
            if missing:
                if (raw is not None or h.get("evidenceScore85") is not None
                        or h.get("missing") != missing):
                    raise FiveCoreReceiptError("Partial research treated as a score")
                continue
            expected = sum(WEIGHTS[k]*POINTS[h["bands"][k]] for k in KEYS)
            if (type(raw) is not int or raw != expected
                    or h.get("missing") != []
                    or h.get("evidenceScore85") != round(raw/3, 2)):
                raise FiveCoreReceiptError("85-weight scores inconsistent")
            complete += 1
            saved.append({
                "number": h["number"], "bands": {k:h["bands"][k] for k in KEYS},
                "rawThirdPoints": raw,
            })
        if complete != race["completeObserved"]:
            raise FiveCoreReceiptError("85-weight observed coverage inconsistency")
        if not saved:
            continue
        post = programme_by_id[coord].get("post_time")
        if (not isinstance(post, str)
                or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", post)):
            expired += 1
            continue
        off = datetime.fromisoformat(f"{day[:4]}-{day[4:6]}-{day[6:]}T{post}:00+09:00")
        if now >= off.astimezone(timezone.utc):
            expired += 1
            continue
        snap = {
            "version":VERSION,"date":day,"track":coord[0],"race":coord[1],
            "sourceKind":"prestart-uncalibrated-85-research",
            "capturedAt":now.isoformat(),"scheduledOffAt":off.astimezone(timezone.utc).isoformat(),
            "raceRunnerCount":race["runnerCount"],"observedRunnerCount":len(saved),
            "horses":sorted(saved,key=lambda h:h["number"]),
            "researchOnly":True,"sourceHypothesesUncalibrated":True,
            "officialJraVerified":False,"predictionReady":False,
            "actualPurchase":False,
        }
        _validate(snap)
        receipts.append({"snapshot":snap,"signature":_sign(snap,secret)})
    if seen != set(programme_by_id):
        raise FiveCoreReceiptError("History versus programme race set mismatch")
    return {
        "version":VERSION,"date":day,
        "receiptCount":len(receipts),"receipts":receipts,
        "postOffOrMissingTimeRaces":expired,"serverSigned":True,
        "jraScheduleVerified":False,"officialResultsVerified":False,
        "calibrationReady":False,"bettingReady":False,"actualPurchase":False,
        "researchOnly":True,"privateOwnerOnly":True,
    }


def verify_five_core_receipts(receipts, secret, day):
    _day(day)
    if not isinstance(receipts, list) or len(receipts)>MAX_RACES:
        raise FiveCoreReceiptError("Invalid receipt collection")
    seen, snapshots = set(), []
    for row in receipts:
        if (not isinstance(row,dict) or set(row)!={"snapshot","signature"}):
            raise FiveCoreReceiptError("Invalid receipt entry")
        snap=row["snapshot"]
        coord=_validate(snap)
        if (coord[0]!=day or coord in seen
                or not isinstance(row["signature"],str)
                or not re.fullmatch(r"[a-f0-9]{64}",row["signature"])
                or not hmac.compare_digest(row["signature"],_sign(snap,secret))):
            raise FiveCoreReceiptError("Signature mismatch or duplicate research")
        seen.add(coord)
        snapshots.append(snap)
    return snapshots
