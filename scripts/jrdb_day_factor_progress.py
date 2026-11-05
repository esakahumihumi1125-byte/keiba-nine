"""One-shot redacted research-factor progress for the owner day pipeline.

Uses the same already-fetched /tra,/tky,/tcy,/tze snapshots, not more JRDB calls.
Horse IDs, numbers, actual workout indices and historical finishes stay in
server memory. Provisional training/recent grade coverage is NOT a ten-factor
overall grade, a live prediction or a betting recommendation.
"""
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints, summarize_training_hints
from jrdb_recent_hypothesis import build_recent_hints, summarize_recent_hints
from jrdb_dual_factor_readiness import summarize_dual_factor_readiness

VERSION = "day-factor-progress-1"
GRADES = ("S", "A", "B", "C", "未評価")


def _index(rows, expected_version, date_races):
    if not isinstance(rows, list) or len(rows) != len(date_races):
        raise CoverageError("Factor rows and day roster disagree")
    out = {}
    for row in rows:
        if not isinstance(row, dict):
            raise CoverageError("Invalid factor row")
        key = (row.get("track"), row.get("race"))
        if key in out or key not in date_races:
            raise CoverageError("Unknown or repeated factor race")
        if row.get("predictionReady") is not False:
            raise CoverageError("Provisional factor was promoted to prediction")
        out[key] = row
    return out


def summarize_day_factor_progress(programme, entries, training, recent, racedate, day):
    """Return 0..120 race-level aggregate factor counts, never horse data."""
    if (not isinstance(day, dict)
            or day.get("version") != "private-day-pipeline-1"
            or day.get("date") != racedate
            or day.get("realPredictionReady") is not False
            or day.get("rawHorseRecordsIncluded") is not False
            or day.get("purchaseReady") is not False
            or not isinstance(day.get("races"), list)
            or day.get("raceCount") != len(day["races"])
            or len(day["races"]) > 120):
        raise CoverageError("Factor and source day snapshot do not agree")
    date_races = {}
    for row in day["races"]:
        if not isinstance(row, dict):
            raise CoverageError("Invalid source-day race")
        key = (row.get("track"), row.get("race"))
        if key in date_races or row.get("realPredictionReady") is not False:
            raise CoverageError("Repeated or promoted source-day race")
        date_races[key] = row

    training_hints = build_training_hints(programme, entries, training, racedate)
    recent_hints = build_recent_hints(programme, entries, recent, racedate)
    training_summary = summarize_training_hints(training_hints)
    recent_summary = summarize_recent_hints(recent_hints)
    paired_summary = summarize_dual_factor_readiness(training_hints, recent_hints)
    if (training_summary.get("predictionReady") is not False
            or recent_summary.get("predictionReady") is not False
            or paired_summary.get("predictionReady") is not False):
        raise CoverageError("Unverified factor was marked as ready")
    tr = _index(training_summary["races"], "training", date_races)
    re = _index(recent_summary["races"], "recent", date_races)
    pa = _index(paired_summary["races"], "paired", date_races)

    rows = []
    for key, source in sorted(date_races.items()):
        a, b, c = tr[key], re[key], pa[key]
        n = source.get("registered")
        if (type(n) is not int or not 0 <= n <= 18
                or c.get("runnerCount") != n or c.get("remainingFactors") != 8
                or c.get("coreFactorsStillUnverified") is not True
                or a.get("researchOnly") is not True
                or b.get("researchOnly") is not True):
            raise CoverageError("Factor population or state disagrees with source")
        grade_a, grade_b = a.get("gradeCounts"), b.get("gradeCounts")
        for grades in (grade_a, grade_b):
            if (not isinstance(grades, dict) or set(grades) != set(GRADES)
                    or any(type(v) is not int or v < 0 or v > n for v in grades.values())
                    or sum(grades.values()) != n):
                raise CoverageError("Invalid experimental factor counts")
        if (sum(c.get(k, -1) for k in ("both", "trainingOnly", "recentOnly", "neither")) != n
                or a.get("graded") != c["both"] + c["trainingOnly"]
                or b.get("graded") != c["both"] + c["recentOnly"]
                or c.get("largeDisagreement", -1) < 0
                or c["largeDisagreement"] > c["both"]):
            raise CoverageError("Paired factor counts contradict source totals")
        rows.append({
            "track": key[0], "race": key[1], "registered": n,
            "trainingExperimentalGraded": a["graded"],
            "recentExperimentalGraded": b["graded"],
            "bothExperimentalGraded": c["both"],
            "largeExperimentalDisagreement": c["largeDisagreement"],
            "trainingGradeCounts": {k: grade_a[k] for k in GRADES},
            "recentGradeCounts": {k: grade_b[k] for k in GRADES},
            "fullTenFactorsGraded": 0,
            "remainingFactorsUnassessed": 8,
            "officialRaceVerified": False,
            "realOverallGradeReady": False,
            "realPredictionReady": False,
            "ticketReady": False,
        })
    return {
        "version": VERSION, "date": racedate, "raceCount": len(rows),
        "summary": {
            "runnersWithTrainingProvisional": sum(r["trainingExperimentalGraded"] for r in rows),
            "runnersWithRecentProvisional": sum(r["recentExperimentalGraded"] for r in rows),
            "runnersWithBothProvisional": sum(r["bothExperimentalGraded"] for r in rows),
            "runnersWithLargeGradeDisagreement": sum(r["largeExperimentalDisagreement"] for r in rows),
            "actualOverallGrades": 0, "actualPredictions": 0,
        },
        "races": rows,
        "realOverallGradeReady": False, "realPredictionReady": False,
        "purchaseReady": False, "rawHorseRecordsIncluded": False,
        "note": ("調教指数と過去走IDMに対する未検証の独自閾値を、"
                 "同一出走馬で突き合わせた暫定研究カウント。"
                 "総合10項目、JRA公式照合、実レースの予想・3連単は未実施。"),
    }
