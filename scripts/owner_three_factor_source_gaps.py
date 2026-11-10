"""Owner-only, read-only source-gap audit for research-6 course/pace/going.

Joins already-redacted per-runner course/going observations to the existing
past-fourth-corner scenario, by exact venue / race / runner number. No raw
provider rows, history IDs, network calls, grading, picks or persistence.
Source presence is NOT aptitude, a calibrated score or official JRA proof.
"""
from evaluation_policy import OWNER_FORMAL_FACTORS
from jrdb_coverage import CoverageError
from jrdb_course_ground_factor_bridge import (
    VERSION as COURSE_VERSION,
)
from jrdb_experimental_pace_scenarios import VERSION as PACE_VERSION

VERSION = "owner-research6-three-factor-source-gaps-1"
WEIGHTS = {k: OWNER_FORMAL_FACTORS[k]
           for k in ("course_distance", "pace", "ground")}
assert WEIGHTS == {"course_distance": 17, "pace": 17, "ground": 12}
STYLES = {"frontObserved", "backObserved", "mixedObserved", "insufficient"}
BANDS = {"S", "A", "B", "未評価"}


def _count(v, upper=18):
    if type(v) is not int or not 0 <= v <= upper:
        raise CoverageError("Invalid source observation count")
    return v


def _unique_races(data, version):
    if (not isinstance(data, dict) or data.get("version") != version
            or data.get("researchOnly") is not True
            or data.get("privateOwnerOnly") is not True
            or data.get("officialJraVerified") is not False
            or data.get("bettingReady") is not False
            or not isinstance(data.get("races"), list)
            or not 0 <= len(data["races"]) <= 120
            or data.get("raceCount") != len(data["races"])):
        raise CoverageError("Invalid owner three-factor source report")
    seen = {}
    for race in data["races"]:
        if (not isinstance(race, dict)
                or not isinstance(race.get("track"), str) or not race["track"]
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or not isinstance(race.get("runners"), list)
                or not 0 <= len(race["runners"]) <= 18
                or race.get("runnerCount") != len(race["runners"])
                or race.get("gradeReady") is not False):
            raise CoverageError("Invalid three-factor race header")
        coordinate = race["track"], race["race"]
        if coordinate in seen:
            raise CoverageError("Duplicate three-factor race")
        seen[coordinate] = race
    return seen


def _course_going(horse):
    counts = ("comparableRuns", "comparableTopThreeRuns", "knownGoingRuns",
              "matchingCurrentGoingRuns", "matchingCurrentGoingTopThreeRuns",
              "wetGoingRuns", "wetTopThreeRuns", "missingPastProgrammes")
    if (not isinstance(horse, dict)
            or type(horse.get("number")) is not int
            or not 1 <= horse["number"] <= 18
            or any(_count(horse.get(k), 5) < 0 for k in counts)
            or type(horse.get("historyLookupComplete")) is not bool
            or type(horse.get("currentGoingRecorded")) is not bool):
        raise CoverageError("Invalid course/going runner")
    c = horse
    if (c["comparableTopThreeRuns"] > c["comparableRuns"]
            or c["knownGoingRuns"] > c["comparableRuns"]
            or c["matchingCurrentGoingRuns"] > c["knownGoingRuns"]
            or c["matchingCurrentGoingTopThreeRuns"] > c["matchingCurrentGoingRuns"]
            or c["wetGoingRuns"] > c["knownGoingRuns"]
            or c["wetTopThreeRuns"] > c["wetGoingRuns"]
            or (not c["currentGoingRecorded"]
                and c["matchingCurrentGoingRuns"] != 0)):
        raise CoverageError("Contradictory course/going observations")
    return c


def _pace_runner(horse):
    if (not isinstance(horse, dict)
            or type(horse.get("number")) is not int
            or not 1 <= horse["number"] <= 18
            or horse.get("pastFourthCorner") not in STYLES
            or horse.get("scenarioFitBand") not in BANDS
            or not isinstance(horse.get("reason"), str)
            or not horse["reason"]):
        raise CoverageError("Invalid pace observation")
    if ((horse["pastFourthCorner"] == "insufficient")
            != (horse["scenarioFitBand"] == "未評価"
                and horse["reason"] == "insufficient_position_coverage")):
        # Other unassessed reasons (e.g. no observed front candidate) are
        # permitted only for an observed style, never for 'insufficient'.
        if horse["pastFourthCorner"] == "insufficient":
            raise CoverageError("Unknown past position promoted to pace")
    return horse


def three_factor_source_gaps(course_history, pace_scenarios):
    """Check source coverage only; missing samples never receive zero/C scores."""
    hist = _unique_races(course_history, "owner-runner-course-going-observation-2")
    pace = _unique_races(pace_scenarios, PACE_VERSION)
    if (course_history.get("gradeReady") is not False
            or course_history.get("predictionReady") is not False
            or pace_scenarios.get("factorWeight") != 20
            or pace_scenarios.get("bandNotVerifiedFactorGrade") is not True
            or pace_scenarios.get("winnerPickReady") is not False
            or pace_scenarios.get("overallScoreReady") is not False
            or set(hist) != set(pace)):
        raise CoverageError("Unmatched or promoted three-factor source data")
    result = []
    for coord in sorted(hist):
        h, p = hist[coord], pace[coord]
        if (h["runnerCount"] != p["runnerCount"]
                or h.get("courseSuitabilityAssessed") is not False
                or h.get("goingSuitabilityAssessed") is not False
                or h.get("paceForecastReady") is not False
                or p.get("paceForecastReady") is not False
                or p.get("bettingReady") is not False
                or type(p.get("coverageAdequate")) is not bool):
            raise CoverageError("Course and pace race flags disagree")
        hrows, prows = {}, {}
        for horse in h["runners"]:
            horse = _course_going(horse)
            if horse["number"] in hrows:
                raise CoverageError("Repeated historical horse")
            hrows[horse["number"]] = horse
        for horse in p["runners"]:
            horse = _pace_runner(horse)
            if horse["number"] in prows:
                raise CoverageError("Repeated pace horse")
            prows[horse["number"]] = horse
        if set(hrows) != set(prows):
            raise CoverageError("Horse identities differ between source reports")
        past_count = sum(row["pastFourthCorner"] != "insufficient"
                         for row in prows.values())
        expected_coverage = (len(prows) >= 3 and past_count >= 3
                             and past_count * 5 >= len(prows) * 3)
        if p["coverageAdequate"] != expected_coverage:
            raise CoverageError("Pace coverage flag disagrees with runners")
        totals = {
            "courseComparableObserved": 0,
            "courseHistoryComplete": 0,
            "currentGoingRecorded": 0,
            "sameGoingObserved": 0,
            "pacePositionObserved": past_count,
            "paceScenarioObserved": 0,
            "allThreeSourcesObserved": 0,
        }
        gaps = {
            "noCourseComparableRuns": 0,
            "courseHistoryIncomplete": 0,
            "currentGoingUnknown": 0,
            "noSameGoingRuns": 0,
            "paceScenarioUnassessed": 0,
        }
        for n, c in hrows.items():
            s = prows[n]
            course = c["comparableRuns"] > 0
            same_going = (c["currentGoingRecorded"] and
                          c["matchingCurrentGoingRuns"] > 0)
            pace_observed = (p["coverageAdequate"] and
                             s["scenarioFitBand"] != "未評価")
            totals["courseComparableObserved"] += int(course)
            totals["courseHistoryComplete"] += int(c["historyLookupComplete"])
            totals["currentGoingRecorded"] += int(c["currentGoingRecorded"])
            totals["sameGoingObserved"] += int(same_going)
            totals["paceScenarioObserved"] += int(pace_observed)
            totals["allThreeSourcesObserved"] += int(
                course and c["historyLookupComplete"] and same_going
                and pace_observed
            )
            gaps["noCourseComparableRuns"] += int(not course)
            gaps["courseHistoryIncomplete"] += int(not c["historyLookupComplete"])
            gaps["currentGoingUnknown"] += int(not c["currentGoingRecorded"])
            gaps["noSameGoingRuns"] += int(
                c["currentGoingRecorded"] and not same_going
            )
            gaps["paceScenarioUnassessed"] += int(not pace_observed)
        result.append({
            "track": coord[0], "race": coord[1],
            "runnerCount": len(hrows), "observed": totals,
            "gaps": gaps,
            "allThreeAreResearchOnly": True,
            "formalGradesVerified": 0, "bettingReady": False,
        })
    return {
        "version": VERSION,
        "policyVersion": "research-6",
        "factorWeights": WEIGHTS, "weightTotal": sum(WEIGHTS.values()),
        "raceCount": len(result), "races": result,
        "extraProviderCalls": 0, "researchOnly": True,
        "privateOwnerOnly": True, "officialJraVerified": False,
        "courseSuitabilityAssessed": False, "paceForecastReady": False,
        "goingSuitabilityAssessed": False, "formalGradesVerified": 0,
        "overallPredictionReady": False, "bettingReady": False,
        "changesExistingTickets": False,
        "note": "コース17・展開17・馬場12点の元資料不足のみ照合。正式採点と公式JRA確認は未実施。",
    }
