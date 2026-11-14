"""Owner-only, non-publishable horse-number research from JRDB beta factors.

Inputs are already validated and scoped to a single race. No original paid
values, horse names, identifiers, sources or credentials are returned.
Two experimental factor grades ARE NOT an overall grade, a win probability,
a betting selection, or a final official JRA start list.
"""
from owner_factor_diagnostics import missing_reasons
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import NUMBER
from jrdb_dual_factor_readiness import KNOWN
from jrdb_program_preview import TRACKS

VERSION = "jrdb-owner-runner-research-1"
VALUES = {"S": 4, "A": 3, "B": 2, "C": 1}
POSITION = {"frontObserved", "backObserved", "mixedObserved", "insufficient"}


def _recent_position(stats):
    observed, front = stats.get("fourthObserved"), stats.get("frontAtFourth")
    if (type(observed) is not int or type(front) is not int
            or not 0 <= front <= observed <= 3):
        raise CoverageError("Invalid past fourth-corner observation")
    if observed < 2:
        return "insufficient"
    if front >= 2:
        return "frontObserved"
    if front == 0:
        return "backObserved"
    return "mixedObserved"


def _recent_observations(past):
    """Redacted completed-history counts; never ungraded into a grade.

    The beta /tze feed can offer one real, finish-observed start but not
    the two completed scored starts required for a RECENT S/A/B/C.
    Return only bounded COUNTS for owner research: no raw IDM, placing,
    race dates, horse IDs, or private source fields.
    Older/mocked partial contracts without these counts remain supported.
    """
    names = ("datedRuns", "completedRuns", "topThree",
             "fourthObserved", "late3fObserved")
    if not any(name in past for name in names):
        return None
    if not all(name in past for name in names):
        raise CoverageError("Incomplete past-run observation counts")
    dated, completed, top3, fourth, late = (past[name] for name in names)
    if (any(type(x) is not int for x in
            (dated, completed, top3, fourth, late))
            or not 0 <= dated <= 5
            or not 0 <= completed <= dated
            or not 0 <= top3 <= min(3, completed)
            or not 0 <= fourth <= min(3, dated)
            or not 0 <= late <= min(3, dated)):
        raise CoverageError("Invalid past-run observation counts")
    return {
        "datedRuns": dated,
        "completedRuns": completed,
        "topThreeObserved": top3,
        "fourthCornerObserved": fourth,
        "late3fObserved": late,
    }


def owner_runner_research(training_hints, recent_hints, track, race):
    """An owner-only, partial two-factor ordering: not a final prediction."""
    if (track not in TRACKS.values() or type(race) is not int
            or not 1 <= race <= 12
            or not isinstance(training_hints, list)
            or not isinstance(recent_hints, list)
            or len(training_hints) != 1 or len(recent_hints) != 1):
        raise CoverageError("Expected exactly one selected race")
    t, p = training_hints[0], recent_hints[0]
    if (not isinstance(t, dict) or not isinstance(p, dict)
            or (t.get("track"), t.get("race")) != (track, race)
            or (p.get("track"), p.get("race")) != (track, race)
            or t.get("racekey") != p.get("racekey")
            or t.get("predictionReady") is not False
            or p.get("predictionReady") is not False):
        raise CoverageError("Selected research source mismatch")
    training, recent = t.get("gradesByNumber"), p.get("byNumber")
    if (not isinstance(training, dict) or not isinstance(recent, dict)
            or set(training) != set(recent) or not 0 <= len(training) <= 18):
        raise CoverageError("Research runner lists disagree")
    result = []
    for number in training:
        if not isinstance(number, str) or not NUMBER.fullmatch(number):
            raise CoverageError("Unexpected runner number")
        a, past = training[number], recent[number]
        if a not in KNOWN or not isinstance(past, dict):
            raise CoverageError("Unexpected workout research row")
        b = past.get("grade")
        if b not in KNOWN:
            raise CoverageError("Unexpected past-form research grade")
        position = _recent_position(past)
        recent_counts = _recent_observations(past)
        completeness = int(a != "未評価") + int(b != "未評価")
        # No ranking with missing factors. The sort uses BOTH present grades
        # only, with no normalization or imaginary replacement for missing data.
        subtotal = VALUES[a] + VALUES[b] if completeness == 2 else None
        result.append({
            "number": int(number), "training": a, "recent": b,
            "missingReasons": missing_reasons(a, b,
                t.get("assessmentStatusByNumber", {}).get(number), past.get("assessmentStatus")),
            "pastFourthCorner": position,
            "recentObserved": recent_counts,
            "completeFactors": completeness,
            "researchOrder": None,
            "_partialScore": subtotal,
        })
    result.sort(key=lambda row: (
        row["_partialScore"] is None,
        -(row["_partialScore"] or 0),
        row["number"]
    ))
    rank, previous = 0, None
    for idx, row in enumerate(result, 1):
        score = row.pop("_partialScore")
        if score is not None:
            if score != previous:
                rank = idx
            row["researchOrder"] = rank
            previous = score
    return {
        "version": VERSION,
        "track": track, "race": race,
        "runners": result,
        "runnerCount": len(result),
        "completeTwoFactorCount": sum(r["completeFactors"] == 2 for r in result),
        "rankBasis": "unvalidated_training_recent_only",
        "researchOnly": True,
        "privateOwnerOnly": True,
        "officialJraVerified": False,
        "overallRankReady": False,
        "predictionReady": False,
        "bettingReady": False,
        "note": ("調教指数と近走資料の独立した暫定S/A/B/Cを馬番別に表示。"
                 "両方に評価がある馬だけ仮並びを付けるが、能力順位や勝率ではない。"
                 "調教時計・近走数値などのJRDB元データは表示しない。"
                 "コース距離・馬場・血統・展開・取消を含めた総合評価、"
                 "JRA公式照合、3連単は未実施。"),
    }
