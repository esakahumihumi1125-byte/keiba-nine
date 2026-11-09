"""Strict time-cut, owner-private cohort evidence for support factors (3+10+1).

This is an OFFLINE, descriptive study. The present JRDB bounded-history bridge
does not supply the complete comparable result population required here.
No paid calls, raw data output, formal S/A/B/C, live predictions or purchases.

Even statistically adequate historical groups are not calibrated causal
effects: jockey/horse quality, draw/pace, class and other confounders remain.
"""
import math
import re
from datetime import timedelta
from statistics import median

from evaluation_policy import (OWNER_FORMAL_FACTORS as FACTORS,
    OWNER_FORMAL_POLICY_VERSION as POLICY_VERSION)
from owner_pedigree_cohort_study import (
    JST, ID, TRACKS, SURFACES, GOINGS, _date, _time, _distance_band,
    PedigreeCohortError
)

VERSION = "owner-support-six-timecut-cohort-1"
KEYS = ("draw_weight", "jockey_stable", "rotation")
WEIGHTS = {k: FACTORS[k] for k in KEYS}
assert WEIGHTS == {"draw_weight": 3, "jockey_stable": 10, "rotation": 1}
TARGET_FIELDS = frozenset((
    "raceDate", "track", "race", "capturedAt", "scheduledOffAt",
    "surface", "distanceM", "going", "classCode", "runners"
))
HISTORY_FIELDS = frozenset((
    "raceDate", "track", "race", "scheduledOffAt", "resultAvailableAt",
    "surface", "distanceM", "going", "classCode", "runners"
))
TARGET_HORSE = frozenset((
    "number", "frame", "carriedKg", "jockeyRef", "trainerRef", "lastRunDate"
))
HISTORIC_HORSE = TARGET_HORSE | {"horseRef", "finish"}
MAX_RACES = 2500
MIN_RACES = 10
MIN_RUNNERS = 30
MIN_HORSES = 20
UNKNOWN = "未評価"
CLASS = re.compile(r"[A-Za-z0-9_-]{2,24}\Z")


class SupportCohortError(ValueError):
    """Safe to return without identifying private horse, rider or stable."""


def _date_checked(value):
    try:
        return _date(value)
    except (PedigreeCohortError, TypeError, ValueError) as exc:
        raise SupportCohortError("Invalid race or run date") from exc


def _time_checked(value):
    try:
        return _time(value)
    except (PedigreeCohortError, TypeError, ValueError) as exc:
        raise SupportCohortError("Invalid race timestamp") from exc


def _race(r, fields):
    if not isinstance(r, dict) or set(r) != fields:
        raise SupportCohortError("Unexpected race data")
    day = _date_checked(r["raceDate"])
    if (r["track"] not in TRACKS or type(r["race"]) is not int
            or not 1 <= r["race"] <= 12 or r["surface"] not in SURFACES
            or r["going"] not in GOINGS or type(r["distanceM"]) is not int
            or not 800 <= r["distanceM"] <= 4000
            or not isinstance(r["classCode"], str)
            or not CLASS.fullmatch(r["classCode"])
            or not isinstance(r["runners"], list)
            or not 3 <= len(r["runners"]) <= 18):
        raise SupportCohortError("Invalid race context")
    off = _time_checked(r["scheduledOffAt"])
    if off.astimezone(JST).date() != day:
        raise SupportCohortError("Race date differs from scheduled start")
    return day, off


def _weight(value):
    if (type(value) not in (int, float) or not math.isfinite(value)
            or not 44 <= value <= 66 or 2 * value != int(2 * value)):
        raise SupportCohortError("Invalid carried weight")
    return float(value)


def _check_horses(r, day, *, historical):
    nums, horse_ids, places = set(), set(), set()
    for h in r["runners"]:
        if (not isinstance(h, dict)
                or set(h) != (HISTORIC_HORSE if historical else TARGET_HORSE)
                or type(h["number"]) is not int
                or not 1 <= h["number"] <= 18 or h["number"] in nums
                or type(h["frame"]) is not int or not 1 <= h["frame"] <= 8
                or not all(isinstance(h[k], str) and ID.fullmatch(h[k])
                           for k in ("jockeyRef", "trainerRef"))):
            raise SupportCohortError("Invalid starter")
        nums.add(h["number"])
        _weight(h["carriedKg"])
        last = h["lastRunDate"]
        if last is not None:
            d = _date_checked(last)
            if d >= day or (day - d).days > 730:
                raise SupportCohortError("Invalid past-run interval")
        if historical:
            if (not isinstance(h["horseRef"], str)
                    or not ID.fullmatch(h["horseRef"])
                    or h["horseRef"] in horse_ids
                    or type(h["finish"]) is not int
                    or not 1 <= h["finish"] <= len(r["runners"])
                    or h["finish"] in places):
                raise SupportCohortError("Incomplete or conflicting finish order")
            horse_ids.add(h["horseRef"])
            places.add(h["finish"])
    if historical and places != set(range(1, len(r["runners"]) + 1)):
        raise SupportCohortError("Incomplete past placing sequence")


def _frame_band(frame):
    return "inside" if frame <= 2 else "middle" if frame <= 6 else "outside"


def _weight_band(kg, center):
    return "lighter" if kg < center - 1 else "heavier" if kg > center + 1 else "close"


def _rotation_band(day, last):
    if last is None:
        return None
    days = (day - _date_checked(last)).days
    return "under14Days" if days < 14 else "days14to55" if days <= 55 else "days56plus"


def _field_band(n):
    return "small" if n <= 8 else "medium" if n <= 14 else "large"


def _group():
    return {"count": 0, "wins": 0, "top3": 0, "races": set(), "horses": set()}


def _record(book, key, race_id, horse):
    if key is None:
        return
    group = book.setdefault(key, _group())
    group["count"] += 1
    group["wins"] += horse["finish"] == 1
    group["top3"] += horse["finish"] <= 3
    group["races"].add(race_id)
    group["horses"].add(horse["horseRef"])


def _summary(group):
    if not group:
        group = _group()
    n = group["count"]
    sufficient = (n >= MIN_RUNNERS and len(group["races"]) >= MIN_RACES
                  and len(group["horses"]) >= MIN_HORSES)
    return {
        "observedRunners": n,
        "observedWins": group["wins"],
        "observedTop3": group["top3"],
        "distinctHistoricalRaces": len(group["races"]),
        "distinctHorses": len(group["horses"]),
        "minimumCoverageMet": sufficient,
        "observedWinRatePercent": round(100 * group["wins"] / n, 2)
                                  if sufficient else None,
        "observedTop3RatePercent": round(100 * group["top3"] / n, 2)
                                  if sufficient else None,
        "verifiedConditionalEffect": False,
        "grade": UNKNOWN,
    }


def support_six_cohort_study(target, history):
    """Analyze distinct, complete pre-capture results for matching conditions.

    Outputs counts only, never rider/horse/stable IDs. All three factor scores
    stay unassessed even for large cohorts. No model fitting or predictions.
    """
    target_day, off = _race(target, TARGET_FIELDS)
    _check_horses(target, target_day, historical=False)
    capture = _time_checked(target["capturedAt"])
    if not timedelta(0) < off - capture <= timedelta(days=7):
        raise SupportCohortError("Target not locked before provisional start")
    if not isinstance(history, list) or len(history) > MAX_RACES:
        raise SupportCohortError("Historical population size invalid")
    roster_count = len(target["runners"])
    field_band = _field_band(roster_count)
    hist = {k: {} for k in (
        "frame", "weight", "jockey", "trainer", "rotation"
    )}
    base = {}
    seen, available, future, unmatched = set(), 0, 0, 0
    target_band = _distance_band(target["distanceM"])

    for r in history:
        past_day, past_off = _race(r, HISTORY_FIELDS)
        _check_horses(r, past_day, historical=True)
        identity = (past_day, r["track"], r["race"])
        if identity in seen or identity == (target_day, target["track"], target["race"]):
            raise SupportCohortError("Duplicate or target race used as history")
        seen.add(identity)
        available_at = _time_checked(r["resultAvailableAt"])
        if available_at <= past_off:
            raise SupportCohortError("Impossible historical result timestamp")
        if past_day >= target_day or available_at >= capture:
            future += 1
            continue
        available += 1
        # A class and field-size mismatch is not causally comparable.
        if (r["track"] != target["track"]
                or r["surface"] != target["surface"]
                or r["going"] != target["going"]
                or r["classCode"] != target["classCode"]
                or _distance_band(r["distanceM"]) != target_band
                or _field_band(len(r["runners"])) != field_band):
            unmatched += 1
            continue
        midpoint = median(_weight(h["carriedKg"]) for h in r["runners"])
        for h in r["runners"]:
            _record(base, "all", identity, h)
            _record(hist["frame"], _frame_band(h["frame"]), identity, h)
            _record(hist["weight"], _weight_band(h["carriedKg"], midpoint), identity, h)
            _record(hist["jockey"], h["jockeyRef"], identity, h)
            _record(hist["trainer"], h["trainerRef"], identity, h)
            _record(hist["rotation"], _rotation_band(past_day, h["lastRunDate"]),
                    identity, h)

    target_mid = median(_weight(h["carriedKg"]) for h in target["runners"])
    horses = []
    for h in sorted(target["runners"], key=lambda x: x["number"]):
        rotation = _rotation_band(target_day, h["lastRunDate"])
        summaries = {
            "frame": _summary(hist["frame"].get(_frame_band(h["frame"]))),
            "relativeWeight": _summary(hist["weight"].get(
                _weight_band(h["carriedKg"], target_mid))),
            "jockey": _summary(hist["jockey"].get(h["jockeyRef"])),
            "trainer": _summary(hist["trainer"].get(h["trainerRef"])),
            "rotation": _summary(hist["rotation"].get(rotation)),
        }
        horses.append({
            "number": h["number"], "cohortEvidence": summaries,
            "rotationSourceAvailable": rotation is not None,
            "grades": dict.fromkeys(KEYS, UNKNOWN),
            "scores": dict.fromkeys(KEYS, None),
            "independentSourcesVerified": False,
            "outOfTimeValidated": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "date": target["raceDate"], "track": target["track"],
        "race": target["race"], "runnerCount": roster_count,
        "factorWeights": dict(WEIGHTS), "weightTotal": 14,
        "racesProvided": len(history), "pastRacesEligible": available,
        "futureOrUnpublishedRacesExcluded": future,
        "otherConditionRacesExcluded": unmatched,
        "matchingBaseline": _summary(base.get("all")),
        "minimumGroupRaces": MIN_RACES, "minimumGroupRunners": MIN_RUNNERS,
        "minimumDistinctHorses": MIN_HORSES,
        "horses": horses, "verifiedFactorCount": 0,
        "verifiedOverallScore": None,
        "independentJraVerified": False,
        "holdoutValidationComplete": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "overallPredictionReady": False, "bettingReady": False,
        "autoPurchase": False, "actualPurchase": False,
        "sourceReadCount": 0, "changesExistingReceipts": False,
        "changesExistingTickets": False, "changesExistingRoi": False,
        "note": (
            "枠位置と相対斤量、騎手と厩舎、休養間隔の過去母数・"
            "着順を分けた研究用観測。独立JRA照合と時系列検証が"
            "未完成。枠斤量3・騎手厩舎10・ローテ1は正式未評価。"
        ),
    }
