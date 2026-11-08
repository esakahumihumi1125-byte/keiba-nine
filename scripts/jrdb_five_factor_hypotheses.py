"""Research-only 5-factor hypothesis overlay for authenticated JRDB history audits.

Combines two experimental factor bands with course/going evidence descriptions
and past-position pace scenarios, all from one internally matched private
snapshot. No new provider reads, 100-point scoring, ticket changes, or JRA
official verification. Only derived bands and horse numbers leave the server.
"""
from evaluation_policy import FACTORS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_private_factor_bridge import summarize_factor_materials
from jrdb_experimental_condition_grades import VERSION as HISTORY_VERSION
from jrdb_experimental_pace_scenarios import VERSION as PACE_VERSION

VERSION = "owner-five-factor-hypotheses-1"
GRADE = frozenset(("S", "A", "B", "C", "未評価"))
FACTORS_IN_VIEW = ("training", "recent", "course_distance", "pace", "ground")
assert len(FACTORS_IN_VIEW) == 5


def _index(rows, kind):
    if not isinstance(rows, list) or len(rows) > 120:
        raise CoverageError("Invalid " + kind + " race list")
    result = {}
    for row in rows:
        if (not isinstance(row, dict)
                or not isinstance(row.get("track"), str)
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoverageError("Invalid " + kind + " race coordinate")
        coord = row["track"], row["race"]
        if coord in result:
            raise CoverageError("Duplicate " + kind + " race")
        result[coord] = row
    return result


def _horse_index(rows, kind):
    if not isinstance(rows, list) or len(rows) > 18:
        raise CoverageError("Invalid " + kind + " runner list")
    out = {}
    for row in rows:
        if not isinstance(row, dict) or type(row.get("number")) is not int:
            raise CoverageError("Invalid " + kind + " runner")
        n = row["number"]
        if not 1 <= n <= 18 or n in out:
            raise CoverageError("Duplicate " + kind + " runner")
        out[n] = row
    return out


def combine_five_factor_hypotheses(private_matrix, history, pace):
    """Merge already validated, same-roster findings without promoting grades."""
    baseline = summarize_factor_materials(private_matrix)
    if (not isinstance(history, dict)
            or history.get("version") != HISTORY_VERSION
            or history.get("researchOnly") is not True
            or history.get("privateOwnerOnly") is not True
            or history.get("officialJraVerified") is not False
            or history.get("overallScoreReady") is not False
            or history.get("bettingReady") is not False
            or history.get("evidenceBandsNotSuitability") is not True
            or not isinstance(history.get("races"), list)
            or history.get("raceCount") != len(history["races"])
            or not isinstance(pace, dict)
            or pace.get("version") != PACE_VERSION
            or pace.get("researchOnly") is not True
            or pace.get("privateOwnerOnly") is not True
            or pace.get("officialJraVerified") is not False
            or pace.get("bandNotVerifiedFactorGrade") is not True
            or pace.get("bettingReady") is not False
            or pace.get("overallScoreReady") is not False
            or not isinstance(pace.get("races"), list)
            or pace.get("raceCount") != len(pace["races"])
            or baseline.get("predictionReady") is not False
            or baseline.get("bettingReady") is not False):
        raise CoverageError("Invalid five-factor research sources")
    bases = _index(private_matrix, "private")
    historical = _index(history["races"], "history")
    scenarios = _index(pace["races"], "pace")
    if (not set(bases) == set(historical) == set(scenarios)
            or len(bases) != baseline["raceCount"]):
        raise CoverageError("Five-factor source races differ")

    races = []
    for coord in sorted(bases):
        base, past, scenario = bases[coord], historical[coord], scenarios[coord]
        if (past.get("overallScoreReady") is not False
                or past.get("winnerPickReady") is not False
                or scenario.get("gradeReady") is not False
                or scenario.get("paceForecastReady") is not False
                or scenario.get("bettingReady") is not False
                or base.get("independentJraVerified") is not False
                or base.get("predictionReady") is not False
                or base.get("bettingReady") is not False):
            raise CoverageError("Unverified factor source promoted to prediction")
        private = base["byNumber"]
        history_by_num = _horse_index(past.get("runners"), "history")
        pace_by_num = _horse_index(scenario.get("runners"), "pace")
        ids = {int(x) for x in private}
        if (ids != set(history_by_num) or ids != set(pace_by_num)
                or len(ids) != past.get("runnerCount")
                or len(ids) != scenario.get("runnerCount")):
            raise CoverageError("Five-factor runner rosters differ")
        horses, coverage = [], dict.fromkeys(FACTORS_IN_VIEW, 0)
        for number in sorted(ids):
            # The validated private matrix uses numeric strings for runner ids.
            t = private[str(number)]
            h, p = history_by_num[number], pace_by_num[number]
            training, recent = t["training"]["grade"], t["recent"]["grade"]
            course, going = h.get("courseEvidenceBand"), h.get("goingEvidenceBand")
            scenario_band = p.get("scenarioFitBand")
            if (any(x not in GRADE for x in (training, recent, course, going, scenario_band))
                    or t["course_distance"]["grade"] != "未評価"
                    or t["ground"]["grade"] != "未評価"
                    or t["pace"]["grade"] != "未評価"
                    or not isinstance(p.get("reason"), str)
                    or not isinstance(h.get("courseReason"), str)
                    or not isinstance(h.get("goingReason"), str)):
                raise CoverageError("Unverified grades cannot enter five-factor report")
            bands = {
                "training": training,
                "recent": recent,
                "course_distance": course,
                "pace": scenario_band,
                "ground": going,
            }
            for key, band in bands.items():
                coverage[key] += int(band != "未評価")
            horses.append({
                "number": number,
                "bands": bands,
                "explanations": {
                    "course_distance": h["courseReason"],
                    "pace": p["reason"],
                    "ground": h["goingReason"],
                },
                "actualGradesVerified": 0,
                "overallScore": None,
                "overallRank": None,
            })
        races.append({
            "track": coord[0], "race": coord[1],
            "runnerCount": len(horses), "runners": horses,
            "bandsPresentByFactor": coverage,
            "verifiedFactorCount": 0,
            "overallReady": False, "bettingReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": len(races), "races": races,
        "factors": [{"key": k, "weight": FACTORS[k]} for k in FACTORS_IN_VIEW],
        "hypothesisBandsNotVerifiedGrades": True,
        "materialCoverageDoesNotMeanPrediction": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "verifiedFactorCount": 0, "bettingReady": False,
        "autoPurchase": False,
        "note": ("調教・近走の暫定ランク、過去同条件の好走実績、"
                 "過去4角から見た展開仮説を馬番ごとに同時表示。"
                 "距離・馬場の過去好走は今回の適性保証ではなく、"
                 "展開は実際の先行争いを予測したものではありません。"
                 "10項目の実戦評価・順位・買い目へは反映しません。"),
    }
