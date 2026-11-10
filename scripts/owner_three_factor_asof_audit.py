"""Owner-private, offline AS-OF audit for three research-6 factor source slots.

The existing bounded JRDB /dra and /dka route does NOT supply verified
publication times. This module accepts a separate, trusted caller's candidate
past observations. It checks the chronology of timestamps as provided, but
DOES NOT authenticate them or certify official provenance. Never construct
resultAvailableAt from a race date or fetch time.

This is a source-readiness study, not a trained factor rubric, prediction,
ranking, betting signal, official JRA confirmation or additional provider read.
Private horse references, historical dates/times and historical identifiers
never appear in the result. No network, credentials, writes or logs.
"""
from datetime import date, datetime, timedelta, timezone
import re

from jrdb_coverage import CoverageError
from jrdb_course_history import DISTANCE_WINDOW_METRES
from evaluation_policy import OWNER_FORMAL_FACTORS

VERSION = "owner-three-factor-asof-study-1"
JST = timezone(timedelta(hours=9))
TRACKS = frozenset(("札幌", "函館", "福島", "新潟", "東京", "中山",
                    "中京", "京都", "阪神", "小倉"))
SURFACES = frozenset(("芝", "ダート"))
GOINGS = frozenset(("良", "稍重", "重", "不良"))
PRIVATE_ID = re.compile(r"[A-Za-z0-9_-]{5,64}\Z", re.ASCII)
DAY = re.compile(r"20\d{2}-\d{2}-\d{2}\Z", re.ASCII)
MAX_OBSERVATIONS_PER_HORSE = 5
MAX_OBSERVATIONS = 18 * MAX_OBSERVATIONS_PER_HORSE
SAMPLE_MINIMUM = 3
WEIGHTS = {k: OWNER_FORMAL_FACTORS[k] for k in
           ("course_distance", "pace", "ground")}
assert WEIGHTS == {"course_distance": 17, "pace": 17, "ground": 12}
TARGET_KEYS = frozenset((
    "raceDate", "track", "race", "capturedAt", "scheduledOffAt",
    "surface", "distanceM", "going", "runners",
))
TARGET_HORSE_KEYS = frozenset(("number", "horseRef"))
PAST_KEYS = frozenset((
    "horseRef", "raceDate", "track", "race", "scheduledOffAt",
    "resultAvailableAt", "surface", "distanceM", "going",
    "fieldSize", "fourthCorner",
))


def _date(value):
    if type(value) is not str or not DAY.fullmatch(value):
        raise CoverageError("Invalid AS-OF race date")
    try:
        day = date.fromisoformat(value)
        if day.isoformat() == value:
            return day
    except ValueError:
        pass
    raise CoverageError("Invalid AS-OF calendar date")


def _timestamp(value):
    if type(value) is not str or not 10 <= len(value) <= 40:
        raise CoverageError("Missing or invalid AS-OF timestamp")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is not None and dt.utcoffset() is not None:
            return dt
    except ValueError:
        pass
    raise CoverageError("Timezone-aware AS-OF timestamp required")


def _race_fields(row, *, target):
    if type(row) is not dict or set(row) != (TARGET_KEYS if target else PAST_KEYS):
        raise CoverageError("Unexpected AS-OF source fields")
    day = _date(row["raceDate"])
    if (type(row["track"]) is not str or row["track"] not in TRACKS
            or type(row["race"]) is not int or not 1 <= row["race"] <= 12
            or type(row["surface"]) is not str
            or row["surface"] not in SURFACES
            or type(row["distanceM"]) is not int
            or not 800 <= row["distanceM"] <= 4000
            or (row["going"] is not None
                and (type(row["going"]) is not str
                     or row["going"] not in GOINGS))):
        raise CoverageError("Invalid AS-OF track or conditions")
    off = _timestamp(row["scheduledOffAt"])
    if off.astimezone(JST).date() != day:
        raise CoverageError("AS-OF date/time mismatch")
    return day, off


def study_three_factor_asof(target, historical):
    """Count timestamp-eligible past observations for an existing target race.

    Only a trusted private adapter may pass candidate history. Published time
    is data, not a certificate: provenance, independent official verification,
    holdout and factor scoring all remain FALSE, even if samples pass.
    """
    target_day, target_off = _race_fields(target, target=True)
    capture = _timestamp(target["capturedAt"])
    if not timedelta(0) < target_off - capture <= timedelta(days=7):
        raise CoverageError("Target must be captured before race off")
    roster = target["runners"]
    if type(roster) is not list or not 2 <= len(roster) <= 18:
        raise CoverageError("Invalid target field size")
    by_ref = {}
    seen_numbers = set()
    for horse in roster:
        if (type(horse) is not dict or set(horse) != TARGET_HORSE_KEYS
                or type(horse["number"]) is not int
                or not 1 <= horse["number"] <= 18
                or horse["number"] in seen_numbers
                or type(horse["horseRef"]) is not str
                or not PRIVATE_ID.fullmatch(horse["horseRef"])
                or horse["horseRef"] in by_ref):
            raise CoverageError("Invalid or repeated target runner")
        seen_numbers.add(horse["number"])
        by_ref[horse["horseRef"]] = horse["number"]
    if type(historical) is not list or len(historical) > MAX_OBSERVATIONS:
        raise CoverageError("AS-OF historical list exceeds private budget")
    # Keep internal history keyed by private horse IDs and historical race IDs.
    # Never expose this set or underlying records beyond the function.
    per_horse = {ref: {
        "historicalRowsProvided": 0,
        "publicationTimestampMissing": 0,
        "excludedAtOrAfterCapture": 0,
        "excludedSameDayOrFuture": 0,
        "timestampEligibleRuns": 0,
        "comparableCourseRuns": 0,
        "matchingCurrentGoingRuns": 0,
        "pastFourthCornerObserved": 0,
    } for ref in by_ref}
    seen_horse_date = set()
    race_contexts = {}
    for record in historical:
        day, old_off = _race_fields(record, target=False)
        horse_ref = record["horseRef"]
        if type(horse_ref) is not str or horse_ref not in by_ref:
            raise CoverageError("Historical observation outside target roster")
        if (type(record["fieldSize"]) is not int
                or not 2 <= record["fieldSize"] <= 18
                or (record["fourthCorner"] is not None
                    and (type(record["fourthCorner"]) is not int
                         or not 1 <= record["fourthCorner"] <= record["fieldSize"]))):
            raise CoverageError("Invalid fourth-corner observation")
        published = (None if record["resultAvailableAt"] is None else
                     _timestamp(record["resultAvailableAt"]))
        if published is not None and published <= old_off:
            raise CoverageError("AS-OF result timestamp before race")
        history_race = (day, record["track"], record["race"])
        context = (old_off, published, record["surface"], record["distanceM"],
                   record["going"], record["fieldSize"])
        if history_race in race_contexts and race_contexts[history_race] != context:
            raise CoverageError("Conflicting historical race context")
        race_contexts[history_race] = context
        identity = (horse_ref, day)
        if identity in seen_horse_date:
            raise CoverageError("One horse cannot have two races on one date")
        seen_horse_date.add(identity)
        counts = per_horse[horse_ref]
        counts["historicalRowsProvided"] += 1
        if counts["historicalRowsProvided"] > MAX_OBSERVATIONS_PER_HORSE:
            raise CoverageError("More than five historical runs for one horse")
        # Same-day or future source data are conservatively unavailable, even
        # if a race earlier on the target day had already finished.
        if day >= target_day:
            counts["excludedSameDayOrFuture"] += 1
            continue
        if published is None:
            counts["publicationTimestampMissing"] += 1
            continue
        # Compare timezone-aware instants, not lexical strings or local dates.
        if published >= capture:
            counts["excludedAtOrAfterCapture"] += 1
            continue
        counts["timestampEligibleRuns"] += 1
        if record["fourthCorner"] is not None:
            counts["pastFourthCornerObserved"] += 1
        comparable = (record["track"] == target["track"]
                      and record["surface"] == target["surface"]
                      and abs(record["distanceM"] - target["distanceM"])
                      <= DISTANCE_WINDOW_METRES)
        if comparable:
            counts["comparableCourseRuns"] += 1
            if (target["going"] is not None
                    and record["going"] == target["going"]):
                counts["matchingCurrentGoingRuns"] += 1
    rows = []
    totals = {k: 0 for k in (
        "historicalRowsProvided", "publicationTimestampMissing",
        "excludedAtOrAfterCapture", "excludedSameDayOrFuture",
        "timestampEligibleRuns", "comparableCourseRuns",
        "matchingCurrentGoingRuns", "pastFourthCornerObserved",
        "courseMinimumStudySamples", "goingMinimumStudySamples",
        "pacePositionObserved", "allThreeMinimumStudySamples",
    )}
    for ref, number in sorted(by_ref.items(), key=lambda x: x[1]):
        counts = per_horse[ref]
        for k in ("historicalRowsProvided", "publicationTimestampMissing",
                  "excludedAtOrAfterCapture", "excludedSameDayOrFuture",
                  "timestampEligibleRuns", "comparableCourseRuns",
                  "matchingCurrentGoingRuns", "pastFourthCornerObserved"):
            totals[k] += counts[k]
        gates = {
            "course_distance": counts["comparableCourseRuns"] >= SAMPLE_MINIMUM,
            "pace": counts["pastFourthCornerObserved"] >= 1,
            "ground": (target["going"] is not None
                       and counts["matchingCurrentGoingRuns"] >= SAMPLE_MINIMUM),
        }
        for key, summary in (
                ("course_distance", "courseMinimumStudySamples"),
                ("pace", "pacePositionObserved"),
                ("ground", "goingMinimumStudySamples")):
            totals[summary] += int(gates[key])
        totals["allThreeMinimumStudySamples"] += int(all(gates.values()))
        reasons = []
        if counts["publicationTimestampMissing"]:
            reasons.append("result_publication_unknown")
        if counts["excludedAtOrAfterCapture"] or counts["excludedSameDayOrFuture"]:
            reasons.append("future_information_quarantined")
        if not gates["course_distance"]:
            reasons.append("course_eligible_sample_below_three")
        if not gates["pace"]:
            reasons.append("past_fourth_corner_unavailable")
        if not gates["ground"]:
            reasons.append("going_eligible_sample_below_three")
        rows.append({
            "number": number, "counts": dict(counts),
            "minimumStudySamples": gates,
            "allThreeMinimumStudySamples": all(gates.values()),
            "gaps": reasons, "formalGradesVerified": 0,
            "score46": None, "winnerPickReady": False,
        })
    return {
        "version": VERSION, "policyVersion": "research-6",
        "track": target["track"], "race": target["race"],
        "runnerCount": len(roster), "runners": rows, "summary": totals,
        "factorWeights": WEIGHTS, "weightTotal": 46,
        "minimumComparableRuns": SAMPLE_MINIMUM,
        "maxPastRunsPerHorse": MAX_OBSERVATIONS_PER_HORSE,
        "timestampOrderingChecked": True,
        "publicationTimestampAuthenticityVerified": False,
        "historicalResultPublicationTimesVerified": False,
        "independentSourceFamiliesVerified": False,
        "officialJraVerified": False,
        "independentTimeCutVerified": False,
        "conditionMatchedHoldoutValidated": False,
        "factorRubricsCalibrated": False,
        "formalGradesVerified": 0, "overallPredictionReady": False,
        "bettingReady": False, "researchOnly": True,
        "privateOwnerOnly": True, "extraProviderCalls": 0,
        "changesExistingTickets": False, "changesExistingRoi": False,
        "note": "公表日時の入力値を時系列照合した研究資料のみ。時刻の独立認証・正式採点は未実施。",
    }
