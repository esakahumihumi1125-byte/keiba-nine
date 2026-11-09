"""Owner-private, offline pedigree 6-weight cohort evidence with a strict time cut.

The source is a trusted caller's *separate* historical full-race dataset. The
current bounded JRDB history lookup does not provide this population. This
module never fetches it, authenticates its provenance, creates a prediction,
grades a horse, stores data or returns confidential lineage identifiers.

Rates below are descriptive historical frequencies, NOT win probabilities or
out-of-time-validated bloodline skill. An official-source verifier and a
separate future holdout are required before any formal grade can be enabled.
"""
import re
from datetime import date, datetime, timedelta, timezone

VERSION = "owner-pedigree-timecut-cohort-1"
JST = timezone(timedelta(hours=9))
TRACKS = frozenset(("札幌", "函館", "福島", "新潟", "東京", "中山",
                    "中京", "京都", "阪神", "小倉"))
SURFACES = frozenset(("芝", "ダート"))
GOINGS = frozenset(("良", "稍重", "重", "不良"))
ID = re.compile(r"[A-Za-z0-9_-]{5,64}\Z")
MIN_RACES = 10
MIN_RUNNERS = 30
MIN_DISTINCT_HORSES = 20
MAX_HISTORY_RACES = 2500
UNASSESSED = "未評価"
PAST_FIELDS = frozenset((
    "raceDate", "track", "race", "scheduledOffAt", "resultAvailableAt",
    "surface", "distanceM", "going", "runners"
))
TARGET_FIELDS = frozenset((
    "raceDate", "track", "race", "capturedAt", "scheduledOffAt",
    "surface", "distanceM", "going", "runners"
))
PAST_HORSE_FIELDS = frozenset((
    "number", "horseRef", "sireRef", "damsireRef", "finish"
))
TARGET_HORSE_FIELDS = frozenset(("number", "sireRef", "damsireRef"))


class PedigreeCohortError(ValueError):
    """Generic error: do not return identifiers or raw licensed rows."""


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", value):
        raise PedigreeCohortError("Invalid date")
    try:
        if date.fromisoformat(value).isoformat() == value:
            return date.fromisoformat(value)
    except ValueError:
        pass
    raise PedigreeCohortError("Invalid calendar date")


def _time(value):
    if not isinstance(value, str) or len(value) > 40:
        raise PedigreeCohortError("Invalid timestamp")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is not None and stamp.utcoffset() is not None:
            return stamp
    except ValueError:
        pass
    raise PedigreeCohortError("Timezone-aware timestamp required")


def _context(race, expected_keys):
    if not isinstance(race, dict) or set(race) != expected_keys:
        raise PedigreeCohortError("Unexpected race fields")
    d = _date(race["raceDate"])
    if (race["track"] not in TRACKS or type(race["race"]) is not int
            or not 1 <= race["race"] <= 12
            or race["surface"] not in SURFACES
            or race["going"] not in GOINGS
            or type(race["distanceM"]) is not int
            or not 800 <= race["distanceM"] <= 4000
            or not isinstance(race["runners"], list)
            or not 3 <= len(race["runners"]) <= 18):
        raise PedigreeCohortError("Invalid race context")
    off = _time(race["scheduledOffAt"])
    if off.astimezone(JST).date() != d:
        raise PedigreeCohortError("Race date and start timestamp differ")
    return d, off


def _validate_runners(race, *, historic):
    seen_num, seen_horses, places = set(), set(), set()
    for horse in race["runners"]:
        if (not isinstance(horse, dict) or set(horse) !=
                (PAST_HORSE_FIELDS if historic else TARGET_HORSE_FIELDS)
                or type(horse["number"]) is not int
                or not 1 <= horse["number"] <= 18
                or horse["number"] in seen_num
                or not all(isinstance(horse[k], str) and ID.fullmatch(horse[k])
                           for k in ("sireRef", "damsireRef"))):
            raise PedigreeCohortError("Invalid runner identity")
        seen_num.add(horse["number"])
        if historic:
            if (not isinstance(horse["horseRef"], str)
                    or not ID.fullmatch(horse["horseRef"])
                    or horse["horseRef"] in seen_horses
                    or type(horse["finish"]) is not int
                    or not 1 <= horse["finish"] <= len(race["runners"])
                    or horse["finish"] in places):
                raise PedigreeCohortError("Incomplete or ambiguous finished race")
            seen_horses.add(horse["horseRef"])
            places.add(horse["finish"])
    if historic and places != set(range(1, len(race["runners"]) + 1)):
        raise PedigreeCohortError("Non-unique finishing positions")


def _distance_band(meters):
    if meters <= 1400:
        return "short"
    if meters <= 2000:
        return "middle"
    if meters <= 2600:
        return "long"
    return "extended"


def _empty_group():
    return {"observedRunners": 0, "observedWins": 0, "observedTop3": 0,
            "distinctHistoricalRaces": 0, "distinctHorses": 0,
            "minimumCoverageMet": False, "observedWinRatePercent": None,
            "observedTop3RatePercent": None, "grade": UNASSESSED,
            "score8": None}


def _summarize(group):
    if not group:
        return _empty_group()
    n = group["count"]
    ok = (n >= MIN_RUNNERS and len(group["races"]) >= MIN_RACES
          and len(group["horses"]) >= MIN_DISTINCT_HORSES)
    return {
        "observedRunners": n, "observedWins": group["wins"],
        "observedTop3": group["top3"],
        "distinctHistoricalRaces": len(group["races"]),
        "distinctHorses": len(group["horses"]),
        "minimumCoverageMet": ok,
        # Even enough historic exposure is not prospective calibration.
        "observedWinRatePercent": round(100 * group["wins"] / n, 2) if ok else None,
        "observedTop3RatePercent": round(100 * group["top3"] / n, 2) if ok else None,
        "grade": UNASSESSED, "score8": None,
    }


def _add(groups, key, race_key, horse):
    group = groups.setdefault(key, {
        "count": 0, "wins": 0, "top3": 0, "races": set(), "horses": set()
    })
    group["count"] += 1
    group["wins"] += horse["finish"] == 1
    group["top3"] += horse["finish"] <= 3
    group["races"].add(race_key)
    group["horses"].add(horse["horseRef"])


def study_pedigree_cohorts(target, historic_races):
    """Compare complete earlier results by track/surface/distance band/going.

    Strictly excludes same-day racing, result publication at or after capture,
    and later dates. This only prepares evidence for a FUTURE separate holdout.
    Results are anonymous aggregates; sire/damsire IDs never leave this call.
    """
    target_day, off = _context(target, TARGET_FIELDS)
    _validate_runners(target, historic=False)
    capture = _time(target["capturedAt"])
    if not timedelta(0) < off - capture <= timedelta(days=7):
        raise PedigreeCohortError("Not a prestart target snapshot")
    if not isinstance(historic_races, list) or len(historic_races) > MAX_HISTORY_RACES:
        raise PedigreeCohortError("Invalid historical cohort size")
    seen, eligible, later, other_conditions = set(), 0, 0, 0
    sire_groups, dam_groups = {}, {}
    baseline = {"count": 0, "wins": 0, "top3": 0,
                "races": set(), "horses": set()}
    target_band = _distance_band(target["distanceM"])
    for race in historic_races:
        day, raced_off = _context(race, PAST_FIELDS)
        _validate_runners(race, historic=True)
        race_key = (day, race["track"], race["race"])
        if race_key in seen or race_key == (
                target_day, target["track"], target["race"]):
            raise PedigreeCohortError("Duplicate or target historical race")
        seen.add(race_key)
        available = _time(race["resultAvailableAt"])
        if available <= raced_off:
            raise PedigreeCohortError("Result existed before race start")
        if day >= target_day or available >= capture:
            later += 1
            continue
        eligible += 1
        if (race["track"] != target["track"]
                or race["surface"] != target["surface"]
                or race["going"] != target["going"]
                or _distance_band(race["distanceM"]) != target_band):
            other_conditions += 1
            continue
        for horse in race["runners"]:
            baseline["count"] += 1
            baseline["wins"] += horse["finish"] == 1
            baseline["top3"] += horse["finish"] <= 3
            baseline["races"].add(race_key)
            baseline["horses"].add(horse["horseRef"])
            _add(sire_groups, horse["sireRef"], race_key, horse)
            _add(dam_groups, horse["damsireRef"], race_key, horse)
    rows = []
    for horse in sorted(target["runners"], key=lambda x: x["number"]):
        rows.append({
            "number": horse["number"],
            "sireHistory": _summarize(sire_groups.get(horse["sireRef"])),
            "damsireHistory": _summarize(dam_groups.get(horse["damsireRef"])),
            "outOfTimeValidated": False,
            "grade": UNASSESSED, "score8": None,
        })
    return {
        "version": VERSION, "factor": "pedigree", "weight": 6,
        "date": target["raceDate"], "track": target["track"], "race": target["race"],
        "runnerCount": len(rows), "horses": rows,
        "providedHistoricalRaces": len(historic_races),
        "historicalRacesAvailableBeforeCapture": eligible,
        "excludedLaterOrUnpublishedRaces": later,
        "otherConditionRaces": other_conditions,
        "conditionMatchedBaseline": _summarize(baseline),
        "minimumGroupRaces": MIN_RACES,
        "minimumGroupRunners": MIN_RUNNERS,
        "minimumDistinctHorses": MIN_DISTINCT_HORSES,
        "allPastResultsHaveIndependentProvenance": False,
        "independentJraOfficialVerification": False,
        "prospectiveHoldoutValidated": False,
        "formalPedigreeGradesVerified": 0,
        "overallPredictionReady": False,
        "bettingReady": False, "autoPurchase": False,
        "actualPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "sourceReadCount": 0, "changesExistingReceipts": False,
        "changesExistingTickets": False,
        "note": (
            "血統の過去同条件の記録件数と観測頻度のみ。独立した"
            "JRA出典認証・未使用期間の予測検証をしていないため"
            "正式S/A/B/C・8点・勝率・買い目へ昇格させません。"
        ),
    }
