"""Experimental race-relative pace scenarios from *past* fourth-corner positions.

Never estimate actual race pace, win probability or grade horses for betting.
Requires independently checked private factor matrix; emits horse numbers and
small categorical hypotheses ONLY for authenticated owner history diagnostics.
No provider access or licensed raw data export.
"""
from jrdb_coverage import CoverageError
from jrdb_private_factor_bridge import POSITION_LABELS, summarize_factor_materials
from evaluation_policy import FACTORS

VERSION = "owner-pace-scenario-hypothesis-1"
STYLES = frozenset(POSITION_LABELS)
assert FACTORS["pace"] == 20

def _band(label, pressure, enough):
    # No scenario can be assigned when most running styles are unknown.
    if not enough or label == "insufficient":
        return "未評価", "insufficient_position_coverage"
    if pressure == "single_front_observed":
        if label == "frontObserved":
            return "S", "possible_single_front_advantage"
        return "B", "low_observed_front_pressure"
    if pressure == "two_front_observed":
        if label == "frontObserved":
            return "A", "two_front_candidates"
        return "B", "uncertain_chase_scenario"
    if pressure == "multiple_front_observed":
        if label == "backObserved":
            return "A", "possible_late_run_if_pressured"
        if label == "frontObserved":
            return "B", "multiple_front_candidates"
        return "B", "mixed_position_under_pressure"
    return "未評価", "no_observed_front_candidate"

def hypothesize_owner_pace(matrix):
    """Separate unvalidated S/A/B/unknown SCENARIO FIT, never factor grades."""
    # This validator enforces ten-factor completeness and refuses an attempted
    # grade promotion on the pace or unmapped factors.
    expected = summarize_factor_materials(matrix)
    result = []
    for source, aggregate in zip(matrix, expected["races"]):
        runners = source["byNumber"]
        styles = {int(number): row["pace"]["positionObservation"]
                  for number, row in runners.items()}
        if any(x not in STYLES for x in styles.values()):
            raise CoverageError("Invalid prior-position style")
        n = len(styles)
        front = sum(x == "frontObserved" for x in styles.values())
        back = sum(x == "backObserved" for x in styles.values())
        mixed = sum(x == "mixedObserved" for x in styles.values())
        unobserved = n - front - back - mixed
        counts = aggregate["pastFourthCorner"]
        if any(counts[k] != sum(s == k for s in styles.values())
               for k in POSITION_LABELS):
            raise CoverageError("Pace observation aggregates disagree")
        # At least 60% of field AND at least three horses must have
        # >=2 observed fourth-corner records; otherwise no race inference.
        enough = n >= 3 and (n-unobserved) >= 3 and (n-unobserved)*5 >= 3*n
        pressure = ("coverage_insufficient" if not enough else
                    "no_front_observed" if front == 0 else
                    "single_front_observed" if front == 1 else
                    "two_front_observed" if front == 2 else
                    "multiple_front_observed")
        hypotheses = []
        for number, label in sorted(styles.items()):
            band, reason = _band(label, pressure, enough)
            hypotheses.append({
                "number": number, "pastFourthCorner": label,
                "scenarioFitBand": band, "reason": reason,
            })
        result.append({
            "track": source["track"], "race": source["race"],
            "runnerCount": n,
            "frontObserved": front, "backObserved": back,
            "mixedObserved": mixed, "insufficient": unobserved,
            "coverageAdequate": enough, "pacePressureScenario": pressure,
            "runners": hypotheses, "paceForecastReady": False,
            "gradeReady": False, "bettingReady": False
        })
    return {
        "version": VERSION, "raceCount": len(result), "races": result,
        "factorWeight": FACTORS["pace"],
        "minObservedFieldShare": "3/5", "minObservedRunners": 3,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "scenarioNotActualPace": True,
        "bandNotVerifiedFactorGrade": True,
        "overallScoreReady": False, "winnerPickReady": False,
        "bettingReady": False,
        "note": ("過去4角の位置から仮説を作るだけ。実際のペースや能力ではない。"
                 "先行候補が多くても勝ち切り候補から除外しない。"
                 "10項目の点数・実馬券・固定予想へ反映しない。"),
    }
