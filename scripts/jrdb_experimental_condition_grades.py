"""Research-only hypotheses for course/going evidence strength.

Input is already redacted, owner-private 0..5 per-runner observations. The
historical conditional placing rate is NOT a calibrated suitability grade,
probability, real race prediction, or authority to add a betting ticket.
Missing /dra or /dka rows, incomplete history, and debutants are UNASSESSED.
No provider calls, odds, names, keys, credentials, results or persistence.
"""
from jrdb_coverage import CoverageError
from evaluation_policy import FACTORS

VERSION = "owner-condition-evidence-hypothesis-1"
SOURCE_VERSION = "owner-runner-course-going-observation-2"
MIN_SAMPLE = 3
BANDS = ("S", "A", "B", "C", "未評価")
assert FACTORS["course_distance"] == 20 and FACTORS["ground"] == 12

def _points(value):
    if type(value) is not int or not 0 <= value <= 5:
        raise CoverageError("Invalid private historical sample")
    return value

def _rank(samples, top_three, complete):
    """A transparent, unvalidated 3-to-5 run descriptive heuristic."""
    if not complete:
        return "未評価", "incomplete_history"
    if samples < MIN_SAMPLE:
        return "未評価", "sample_below_three"
    # The C band is descriptive of five historical non-podium finishes,
    # NOT a prohibition on rebound wins. None of these bands alter tickets.
    if samples == 5 and top_three == 0:
        return "C", "observed_five_without_top_three"
    if top_three >= 2 and 3 * top_three >= 2 * samples:
        return "S", "observed_two_thirds_top_three"
    if top_three >= 1 and 3 * top_three >= samples:
        return "A", "observed_one_third_top_three"
    return "B", "observed_limited_top_three"

def hypothesis_from_owner_history(report):
    """Validate complete redacted source and return separate experimental bands.

    The existing factor matrix (all ten verified? no), signed drafts, 100-point
    grades and historical source counts are NEVER changed.
    """
    if (not isinstance(report, dict)
            or report.get("version") != SOURCE_VERSION
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or any(report.get(k) is not False for k in (
                "officialJraVerified", "gradeReady", "predictionReady",
                "bettingReady"))
            or type(report.get("raceCount")) is not int
            or not isinstance(report.get("races"), list)
            or report["raceCount"] != len(report["races"])
            or report["raceCount"] > 120):
        raise CoverageError("Invalid condition research source")
    seen_races = set()
    races = []
    for race in report["races"]:
        if (not isinstance(race, dict)
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or not isinstance(race.get("track"), str)
                or not race["track"]
                or race.get("gradeReady") is not False
                or race.get("courseSuitabilityAssessed") is not False
                or race.get("goingSuitabilityAssessed") is not False
                or race.get("paceForecastReady") is not False
                or type(race.get("runnerCount")) is not int
                or not 0 <= race["runnerCount"] <= 18
                or not isinstance(race.get("runners"), list)
                or race["runnerCount"] != len(race["runners"])):
            raise CoverageError("Invalid condition research race")
        key = race["track"], race["race"]
        if key in seen_races:
            raise CoverageError("Duplicate condition research race")
        seen_races.add(key)
        horses = []
        seen_numbers = set()
        for raw in race["runners"]:
            if (not isinstance(raw, dict)
                    or type(raw.get("number")) is not int
                    or not 1 <= raw["number"] <= 18
                    or raw["number"] in seen_numbers
                    or type(raw.get("historyLookupComplete")) is not bool
                    or type(raw.get("currentGoingRecorded")) is not bool):
                raise CoverageError("Invalid condition runner identity")
            seen_numbers.add(raw["number"])
            counts = {name: _points(raw.get(name)) for name in (
                "comparableRuns", "comparableTopThreeRuns",
                "knownGoingRuns", "matchingCurrentGoingRuns",
                "matchingCurrentGoingTopThreeRuns", "wetGoingRuns",
                "wetTopThreeRuns", "missingPastProgrammes"
            )}
            c, t = counts["comparableRuns"], counts["comparableTopThreeRuns"]
            k, m = counts["knownGoingRuns"], counts["matchingCurrentGoingRuns"]
            mt = counts["matchingCurrentGoingTopThreeRuns"]
            wet, wt = counts["wetGoingRuns"], counts["wetTopThreeRuns"]
            if (t > c or k > c or m > k or mt > m or wet > k
                    or wt > wet
                    or (not raw["currentGoingRecorded"] and (m or mt))
                    or (raw["historyLookupComplete"]
                        and counts["missingPastProgrammes"])):
                raise CoverageError("Contradictory condition research counts")
            course, course_reason = _rank(
                c, t, raw["historyLookupComplete"]
            )
            if not raw["currentGoingRecorded"]:
                going, going_reason = "未評価", "current_going_unknown"
            elif not raw["historyLookupComplete"] or k != c:
                going, going_reason = "未評価", "incomplete_history"
            else:
                going, going_reason = _rank(m, mt, True)
            horses.append({
                "number": raw["number"],
                "courseEvidenceBand": course,
                "courseReason": course_reason,
                "goingEvidenceBand": going,
                "goingReason": going_reason,
            })
        races.append({
            "track": key[0], "race": key[1],
            "runnerCount": len(horses), "runners": horses,
            "overallScoreReady": False, "winnerPickReady": False,
        })
    return {
        "version": VERSION, "sourceVersion": SOURCE_VERSION,
        "raceCount": len(races), "races": races,
        "minComparableSamples": MIN_SAMPLE,
        "courseDistanceWeight": FACTORS["course_distance"],
        "goingWeight": FACTORS["ground"],
        "evidenceBandsNotSuitability": True,
        "negativeBandNeverExcludesRebound": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallScoreReady": False,
        "winnerPickReady": False, "bettingReady": False,
        "note": ("過去3〜5走の同条件3着内実績を使う検証前の説明用指標。"
                 "過去着順で今回の勝ち切り能力は断定しない。"
                 "サンプル不足は未評価。総合評価・3連単・購入には反映しない。"),
    }
