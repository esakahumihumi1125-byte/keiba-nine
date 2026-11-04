"""Private in-memory bridge from provisional /tcy,/tze hints to ten factors.

No provider fetch, persistence, public output, official JRA verification or
betting decisions. Training/recent grades are experimental heuristics; past
fourth-corner position is ONLY an observation, never a pace grade.
The horse-number matrix must stay inside the authenticated private process.
Only summarize_factor_materials() may be sent to the owner-only HTTP client.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import KEY, NUMBER
from jrdb_program_preview import TRACKS
from evaluation_policy import FACTORS
from jrdb_dual_factor_readiness import KNOWN

VERSION = "private-factor-bridge-1"
POSITION_LABELS = ("frontObserved", "backObserved", "mixedObserved", "insufficient")
PROVISIONAL = frozenset(("training", "recent"))


def _race_index(rows, name):
    if not isinstance(rows, list) or len(rows) > 120:
        raise CoverageError("Invalid " + name + " factor races")
    out = {}
    for row in rows:
        if not isinstance(row, dict):
            raise CoverageError("Invalid factor race row")
        key = row.get("racekey")
        track, number = row.get("track"), row.get("race")
        if (not isinstance(key, str) or not KEY.fullmatch(key)
                or track not in TRACKS.values()
                or type(number) is not int or not 1 <= number <= 12
                or key in out or (track, number) in
                {(v["track"], v["race"]) for v in out.values()}
                or row.get("predictionReady") is not False):
            raise CoverageError("Invalid or duplicate factor race")
        out[key] = row
    return out


def _position(stats):
    if not isinstance(stats, dict):
        raise CoverageError("Invalid previous-run observation")
    n, front = stats.get("fourthObserved"), stats.get("frontAtFourth")
    if (type(n) is not int or type(front) is not int
            or not 0 <= front <= n <= 3):
        raise CoverageError("Invalid historical position counts")
    if n < 2:
        return "insufficient"
    if front >= 2:
        return "frontObserved"
    if front == 0:
        return "backObserved"
    return "mixedObserved"


def build_private_factor_matrix(training_hints, recent_hints):
    """Internal runner-number factor slots for later evaluation development.

    All other factors are explicitly ungraded; do NOT feed the provisional
    two-factor grades into a complete 10-factor overall ranking.
    """
    train = _race_index(training_hints, "training")
    past = _race_index(recent_hints, "recent")
    if set(train) != set(past):
        raise CoverageError("Training and recent-form race sets differ")
    result = []
    for key, row in train.items():
        other = past[key]
        if (row["track"], row["race"]) != (other["track"], other["race"]):
            raise CoverageError("Training and recent race identity differs")
        a, b = row.get("gradesByNumber"), other.get("byNumber")
        if not isinstance(a, dict) or not isinstance(b, dict) or set(a) != set(b):
            raise CoverageError("Factor runner lists disagree")
        if not 0 <= len(a) <= 18:
            raise CoverageError("Too many runners")
        runners = {}
        for number in sorted(a):
            if not isinstance(number, str) or not NUMBER.fullmatch(number):
                raise CoverageError("Invalid runner number")
            tgrade, recent = a[number], b[number]
            if tgrade not in KNOWN or not isinstance(recent, dict):
                raise CoverageError("Invalid training or recent grade")
            rgrade = recent.get("grade")
            if rgrade not in KNOWN:
                raise CoverageError("Invalid recent grade")
            position = _position(recent)
            slots = {factor: {"grade": "未評価", "basis": "not_mapped"}
                     for factor in FACTORS}
            slots["training"] = {"grade": tgrade, "basis": "experimental_workout_index"}
            slots["recent"] = {"grade": rgrade, "basis": "experimental_recent_idm"}
            slots["pace"] = {"grade": "未評価",
                             "basis": "historical_fourth_corner_only",
                             "positionObservation": position}
            runners[number] = slots
        result.append({"racekey": key, "track": row["track"], "race": row["race"],
                       "byNumber": runners, "researchOnly": True,
                       "independentJraVerified": False,
                       "predictionReady": False, "bettingReady": False})
    return result


def summarize_factor_materials(matrix):
    """Only per-race counters may cross the authenticated private boundary."""
    if not isinstance(matrix, list) or len(matrix) > 120:
        raise CoverageError("Invalid private factor matrix")
    seen = set()
    result = []
    for race in matrix:
        if (not isinstance(race, dict) or race.get("researchOnly") is not True
                or race.get("predictionReady") is not False
                or race.get("bettingReady") is not False
                or race.get("independentJraVerified") is not False
                or race.get("track") not in TRACKS.values()
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or not isinstance(race.get("byNumber"), dict)):
            raise CoverageError("Unverified factor data cannot be summarized")
        coord = (race["track"], race["race"])
        if coord in seen:
            raise CoverageError("Duplicate factor matrix race")
        seen.add(coord)
        rows = race["byNumber"]
        if len(rows) > 18:
            raise CoverageError("Too many runners")
        counts = {"trainingProvisional": 0, "recentProvisional": 0}
        observations = dict.fromkeys(POSITION_LABELS, 0)
        for number, slots in rows.items():
            if not isinstance(number, str) or not NUMBER.fullmatch(number):
                raise CoverageError("Invalid runner identity")
            if not isinstance(slots, dict) or set(slots) != set(FACTORS):
                raise CoverageError("Incomplete factor matrix")
            for factor, value in slots.items():
                if not isinstance(value, dict):
                    raise CoverageError("Malformed factor slot")
                if factor == "training":
                    if value.get("basis") != "experimental_workout_index" or value.get("grade") not in KNOWN:
                        raise CoverageError("Untrusted workout grade")
                    counts["trainingProvisional"] += value["grade"] != "未評価"
                elif factor == "recent":
                    if value.get("basis") != "experimental_recent_idm" or value.get("grade") not in KNOWN:
                        raise CoverageError("Untrusted past-form grade")
                    counts["recentProvisional"] += value["grade"] != "未評価"
                elif factor == "pace":
                    label = value.get("positionObservation")
                    if (value.get("basis") != "historical_fourth_corner_only"
                            or value.get("grade") != "未評価"
                            or label not in observations):
                        raise CoverageError("Historical position is not a pace grade")
                    observations[label] += 1
                elif value != {"grade": "未評価", "basis": "not_mapped"}:
                    raise CoverageError("Unmapped factor cannot be graded")
        n = len(rows)
        if sum(observations.values()) != n:
            raise CoverageError("Historical observation totals differ from runners")
        result.append({
            "track": coord[0], "race": coord[1], "runnerCount": n,
            "provisionalGradeCounts": counts,
            "pastFourthCorner": observations,
            "mappedFactors": ["training", "recent"],
            "observationOnlyFactors": ["pace"],
            "unmappedFactorCount": len(FACTORS) - 3,
            "verifiedFactorCount": 0,
            "paceForecastAvailable": False,
            "overallRankReady": False,
            "predictionReady": False, "bettingReady": False,
        })
    return {"version": VERSION, "raceCount": len(result), "races": result,
            "predictionReady": False, "bettingReady": False,
            "note": ("調教・近走の未検証ランクと過去4角位置の観測を10項目の"
                     "内部スロットに仮接続。残り7項目は未マップ、"
                     "展開・脚質を含めた8項目は未評価。"
                     "勝率・総合評価・買い目は作成しません。")}
