"""Private offline diagnostic for historical evidence sufficiency, NOT horse skill.

Return only race-level headcounts and coarse data gaps. The labels describe
how many comparable past runs are documented, NOT prediction confidence,
course suitability, win probability, or financial returns.
"""
from jrdb_coverage import CoverageError
from jrdb_program_preview import TRACKS

VERSION = "history-evidence-coverage-1"
SAMPLE_BUCKETS = ("none", "oneOrTwo", "threePlus")
REQUIRED = (
    "datedRuns", "linkedPastProgrammes", "missingPastProgrammes",
    "sameSurfaceRuns", "sameSurfaceNearDistanceRuns",
    "sameSurfaceKnownGoingRuns", "sameSurfaceUnknownGoingRuns",
    "knownGoingComparableRuns", "unknownGoingComparableRuns",
    "sameCurrentGoingComparableRuns", "heavyComparableRuns",
    "poorComparableRuns", "heavyTopThreeRuns", "poorTopThreeRuns",
)


def _sample_group(count):
    if count == 0:
        return "none"
    return "oneOrTwo" if count < 3 else "threePlus"


def _check_counts(stats, current_going):
    if (not isinstance(stats, dict) or
            any(type(stats.get(field)) is not int or stats[field] < 0
                for field in REQUIRED)):
        raise CoverageError("Invalid historical evidence counts")
    if (stats["datedRuns"] > 5 or
            stats["linkedPastProgrammes"] + stats["missingPastProgrammes"]
            != stats["datedRuns"] or
            stats["sameSurfaceRuns"] > stats["linkedPastProgrammes"] or
            stats["sameSurfaceNearDistanceRuns"] > stats["sameSurfaceRuns"] or
            stats["sameSurfaceKnownGoingRuns"] +
            stats["sameSurfaceUnknownGoingRuns"] != stats["sameSurfaceRuns"] or
            stats["knownGoingComparableRuns"] +
            stats["unknownGoingComparableRuns"] != stats["sameSurfaceNearDistanceRuns"] or
            stats["heavyComparableRuns"] + stats["poorComparableRuns"] >
            stats["knownGoingComparableRuns"] or
            stats["heavyTopThreeRuns"] > stats["heavyComparableRuns"] or
            stats["poorTopThreeRuns"] > stats["poorComparableRuns"] or
            stats["sameCurrentGoingComparableRuns"] >
            stats["knownGoingComparableRuns"] or
            (not current_going and stats["sameCurrentGoingComparableRuns"])):
        raise CoverageError("Contradictory historical evidence counts")


def summarize_history_evidence_quality(races):
    """Aggregate only headcounts; horse numbers and paid rows never leave here.

    'threePlus' is a configurable-looking but FIXED research sample bucket,
    not a calibrated adequacy threshold. No suitability labels are produced.
    """
    if not isinstance(races, list) or len(races) > 120:
        raise CoverageError("Invalid historical evidence collection")
    seen, output = set(), []
    for race in races:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise CoverageError("Invalid historical race")
        name, number = race.get("track"), race.get("race")
        if (name not in TRACKS.values() or type(number) is not int or
                not 1 <= number <= 12 or
                (name, number) in seen or
                type(race.get("currentGoingRecorded")) is not bool or
                len(race["byNumber"]) > 18):
            raise CoverageError("Invalid or duplicate race")
        seen.add((name, number))
        course = dict.fromkeys(SAMPLE_BUCKETS, 0)
        going = dict.fromkeys(SAMPLE_BUCKETS, 0)
        dated_horses = 0
        linked_horses = 0
        unlinked_horses = 0
        unlinked_runs = 0
        dated_runs = 0
        linked_runs = 0
        for stats in race["byNumber"].values():
            _check_counts(stats, race["currentGoingRecorded"])
            dated = stats["datedRuns"]
            dated_runs += dated
            linked_runs += stats["linkedPastProgrammes"]
            unlinked_runs += stats["missingPastProgrammes"]
            dated_horses += dated > 0
            linked_horses += stats["linkedPastProgrammes"] > 0
            unlinked_horses += stats["missingPastProgrammes"] > 0
            course[_sample_group(stats["sameSurfaceNearDistanceRuns"])] += 1
            going[_sample_group(stats["knownGoingComparableRuns"])] += 1
        n = len(race["byNumber"])
        if dated_runs == 0:
            status = "該当記録なし"
        elif unlinked_runs:
            status = "未照合あり"
        else:
            status = "番組履歴は照合"
        output.append({
            "track": name, "race": number, "runnerCount": n,
            "runnersNoRecordedPast": n - dated_horses,
            "runnersWithRecordedPast": dated_horses,
            "runnersWithLinkedPast": linked_horses,
            "runnersWithMissingPast": unlinked_horses,
            "datedPastRuns": dated_runs, "linkedPastRuns": linked_runs,
            "unlinkedPastRuns": unlinked_runs,
            "courseComparableSamples": course,
            "knownGoingComparableSamples": going,
            "currentGoingRecorded": race["currentGoingRecorded"],
            "materialStatus": status,
            "predictionConfidenceAssessed": False,
            "suitabilityAssessed": False,
            "predictionReady": False,
        })
    return {
        "version": VERSION, "raceCount": len(output), "races": output,
        "predictionConfidenceAssessed": False, "suitabilityAssessed": False,
        "predictionReady": False,
        "note": ("比較履歴0／1～2／3走以上の頭数と未照合を整理した資料充足度。"
                 "3走は便宜上の区分で、統計的な信頼度・得意不得意・勝率・回収率"
                 "や実戦予想ではありません。データ不足は不明として扱います。"),
    }
