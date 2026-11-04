"""Owner-only private aggregate comparison of workout and past-form readiness.

Horse-number joins exist only in this module's memory. The return value has
no horse number, horse ID, raw index, previous result, or buy recommendation.
"""
from jrdb_coverage import CoverageError

VERSION = "dual-factor-readiness-2"
KNOWN = {"S", "A", "B", "C", "未評価"}
GRADE_LEVEL = {"S": 4, "A": 3, "B": 2, "C": 1}
HIGH = {"S", "A"}


def summarize_dual_factor_readiness(training_hints, recent_hints):
    if (not isinstance(training_hints, list) or not isinstance(recent_hints, list)
            or len(training_hints) > 120 or len(recent_hints) > 120):
        raise CoverageError("Invalid factor readiness input")
    if len(training_hints) != len(recent_hints):
        raise CoverageError("Inconsistent number of races")
    recent_map = {}
    for race in recent_hints:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise CoverageError("Invalid recent factor row")
        key = race.get("racekey")
        if not isinstance(key, str) or key in recent_map:
            raise CoverageError("Duplicate or invalid recent factor race")
        recent_map[key] = race
    result = []
    seen = set()
    for race in training_hints:
        if not isinstance(race, dict) or not isinstance(race.get("gradesByNumber"), dict):
            raise CoverageError("Invalid training factor row")
        key = race.get("racekey")
        if not isinstance(key, str) or key in seen:
            raise CoverageError("Duplicate or invalid training factor race")
        seen.add(key)
        other = recent_map.get(key)
        if other is None or (race.get("track"), race.get("race")) != (
                other.get("track"), other.get("race")):
            raise CoverageError("Factors refer to different races")
        train = race["gradesByNumber"]
        past = other["byNumber"]
        if set(train) != set(past):
            raise CoverageError("Factors refer to different runner lists")
        counts = {"both": 0, "trainingOnly": 0, "recentOnly": 0, "neither": 0}
        comparison = {
            "sameGrade": 0, "trainingHigher": 0, "recentHigher": 0,
            "largeDisagreement": 0, "bothHigh": 0,
        }
        for num in train:
            grade_a = train[num]
            past_stat = past[num]
            if grade_a not in KNOWN or not isinstance(past_stat, dict):
                raise CoverageError("Invalid factor grade")
            grade_b = past_stat.get("grade")
            if grade_b not in KNOWN:
                raise CoverageError("Invalid recent factor grade")
            a, b = grade_a != "未評価", grade_b != "未評価"
            name = ("both" if a and b else
                    "trainingOnly" if a else
                    "recentOnly" if b else "neither")
            counts[name] += 1
            if a and b:
                diff = GRADE_LEVEL[grade_a] - GRADE_LEVEL[grade_b]
                if diff == 0:
                    comparison["sameGrade"] += 1
                elif diff > 0:
                    comparison["trainingHigher"] += 1
                else:
                    comparison["recentHigher"] += 1
                if abs(diff) >= 2:
                    comparison["largeDisagreement"] += 1
                if grade_a in HIGH and grade_b in HIGH:
                    comparison["bothHigh"] += 1
        if (sum(counts.values()) != len(train)
                or (comparison["sameGrade"] + comparison["trainingHigher"]
                    + comparison["recentHigher"] != counts["both"])
                or comparison["largeDisagreement"] > counts["both"]
                or comparison["bothHigh"] > counts["both"]):
            raise CoverageError("Inconsistent paired factor counts")
        result.append({
            "track": race["track"], "race": race["race"],
            "runnerCount": len(train), **counts, **comparison,
            "remainingFactors": 8,
            "coreFactorsStillUnverified": True, "predictionReady": False
        })
    return {
        "version": VERSION, "races": result, "predictionReady": False,
        "note": ("調教・近走の独立した暫定評価が両方ある頭数と"
                 "評価方向の食い違いを数える。差2段階以上は再検討対象。"
                 "指数から付けたランクの妥当性は未検証であり、"
                 "馬場・距離・展開・取消と残り8項目は未確認。"
                 "総合評価・予想・買い目ではありません。")
    }
