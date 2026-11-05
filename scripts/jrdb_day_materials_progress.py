"""Eight-slot source-material audit for the private full-day owner view.

Works only with the five already fetched current-day JRDB lists, with no
additional API/network, historical guesses, real horse ranking or predictions.
The two historical course/going slots remain explicitly unobserved until a
separate, bounded, licensed historical lookup and suitability evaluation.
Only strict bounded aggregate counters leave the private process.
"""
from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_private_factor_bridge import (
    build_private_factor_matrix, summarize_factor_materials,
)
from jrdb_entry_rotation_materials import (
    enrich_entry_materials_matrix, summarize_entry_materials_matrix,
)
from jrdb_personnel_body_materials import (
    enrich_personnel_body_matrix, summarize_personnel_body_matrix,
)

VERSION = "private-eight-materials-1"
MAX_RACES = 120
MAPPED = ("training", "recent", "pace", "pedigree",
          "draw_weight", "rotation", "jockey_stable", "body_condition")
UNMAPPED = ("course_distance", "ground")


def _index(summary, count, *, name):
    if (not isinstance(summary, dict) or summary.get("predictionReady") is not False
            or not isinstance(summary.get("races"), list)
            or len(summary["races"]) != count
            or summary.get("raceCount") != count):
        raise CoverageError("Invalid " + name + " material summary")
    out = {}
    for row in summary["races"]:
        if not isinstance(row, dict):
            raise CoverageError("Invalid observation race row")
        coord = row.get("track"), row.get("race")
        if (coord in out or row.get("predictionReady") is not False
                or row.get("bettingReady") is not False):
            raise CoverageError("Duplicate or promoted observation race")
        out[coord] = row
    return out


def _count(value, n):
    if type(value) is not int or not 0 <= value <= n:
        raise CoverageError("Source material count out of bounds")
    return value


def summarize_day_materials(programme, entries, training, recent, racedate, day):
    """Return runner-count-only material observations for an entire day."""
    if (not isinstance(day, dict) or day.get("version") != "private-day-pipeline-1"
            or day.get("date") != racedate
            or day.get("realPredictionReady") is not False
            or day.get("purchaseReady") is not False
            or day.get("rawHorseRecordsIncluded") is not False
            or not isinstance(day.get("races"), list)
            or type(day.get("raceCount")) is not int
            or not 0 <= day["raceCount"] <= MAX_RACES
            or len(day["races"]) != day["raceCount"]):
        raise CoverageError("Invalid unverified day coverage snapshot")
    keys = {}
    for row in day["races"]:
        if (not isinstance(row, dict) or row.get("realPredictionReady") is not False
                or row.get("ticketReady") is not False):
            raise CoverageError("Unsafe day race")
        key = row.get("track"), row.get("race")
        if key in keys:
            raise CoverageError("Duplicate day race")
        keys[key] = row

    train = build_training_hints(programme, entries, training, racedate)
    past = build_recent_hints(programme, entries, recent, racedate)
    base = build_private_factor_matrix(train, past)
    base_counts = summarize_factor_materials(base)
    extended = enrich_entry_materials_matrix(base, programme, entries, recent, racedate)
    entry_counts = summarize_entry_materials_matrix(extended)
    full = enrich_personnel_body_matrix(extended, programme, entries, racedate)
    body_counts = summarize_personnel_body_matrix(full)
    a = _index(base_counts, len(keys), name="base")
    b = _index(entry_counts, len(keys), name="entry")
    c = _index(body_counts, len(keys), name="personnel")
    if set(a) != set(keys) or set(b) != set(keys) or set(c) != set(keys):
        raise CoverageError("Different race sets across factor material summaries")
    out = []
    for coord in sorted(keys):
        day_row, base_row, entry_row, body_row = keys[coord], a[coord], b[coord], c[coord]
        n = day_row.get("registered")
        if (type(n) is not int or not 0 <= n <= 18
                or any(x.get("runnerCount") != n for x in (base_row, entry_row, body_row))
                or base_row.get("unmappedFactorCount") != 7
                or entry_row.get("unmappedFactorCount") != 4
                or body_row.get("unmappedFactorCount") != 2
                or body_row.get("observedFactorSlots") != 8
                or body_row.get("verifiedFactorCount") != 0
                or body_row.get("overallRankReady") is not False
                or body_row.get("jockeyTrainerPerformanceAssessed") is not False
                or body_row.get("bodyConditionAssessed") is not False
                or body_row.get("raceDayBodyWeightFetched") is not False):
            raise CoverageError("Unsafe or incomplete eight-slot observations")
        observations = entry_row.get("entryObservations")
        rotation = entry_row.get("rotationIntervals")
        personnel = body_row.get("recorded")
        position = base_row.get("pastFourthCorner")
        workout = base_row.get("provisionalGradeCounts")
        if (not isinstance(observations, dict) or not isinstance(rotation, dict)
                or not isinstance(personnel, dict) or not isinstance(position, dict)
                or not isinstance(workout, dict)):
            raise CoverageError("Missing material aggregate categories")
        # Bounded fixed counters only; no provider text or IDs pass through.
        result_counts = {
            "pedigreeParentsRecorded": _count(observations.get("bothPedigreeRecorded"), n),
            "drawAndAssignedWeightRecorded": _count(observations.get("drawAndWeightRecorded"), n),
            "lastRaceDateRecorded": n - _count(rotation.get("unknown"), n),
            "jockeyTrainerNamesRecorded": _count(personnel.get("bothPersonnelNamesRecorded"), n),
            "conformationCodeRecorded": _count(personnel.get("anyConformationRecorded"), n),
            "pastCornerObservedForPaceResearch": (
                n - _count(position.get("insufficient"), n)),
            "trainingProvisional": _count(workout.get("trainingProvisional"), n),
            "recentProvisional": _count(workout.get("recentProvisional"), n),
        }
        if (sum(_count(rotation.get(k), n) for k in (
                "unknown", "under14Days", "days14to55", "days56plus")) != n
                or sum(_count(position.get(k), n) for k in (
                    "insufficient", "frontObserved", "backObserved", "mixedObserved")) != n):
            raise CoverageError("Observation category totals contradict roster")
        out.append({
            "track": coord[0], "race": coord[1], "registered": n,
            "observedSourceSlots": len(MAPPED),
            "unmappedHistorySlots": len(UNMAPPED),
            "unverifiedFactorGrades": len(FACTORS),
            "provisionalFactorsOnly": 2,
            "counts": result_counts,
            "officialJraVerified": False,
            "overallRankReady": False,
            "realPredictionReady": False,
            "ticketReady": False,
        })
    return {
        "version": VERSION, "date": racedate, "raceCount": len(out),
        "mappedSourceSlots": list(MAPPED),
        "unmappedHistorySlots": list(UNMAPPED),
        "summary": {
            "totalRegistered": sum(r["registered"] for r in out),
            "pedigreePresent": sum(r["counts"]["pedigreeParentsRecorded"] for r in out),
            "drawAndWeightPresent": sum(r["counts"]["drawAndAssignedWeightRecorded"] for r in out),
            "rotationDatesPresent": sum(r["counts"]["lastRaceDateRecorded"] for r in out),
            "personnelPresent": sum(r["counts"]["jockeyTrainerNamesRecorded"] for r in out),
            "conformationPresent": sum(r["counts"]["conformationCodeRecorded"] for r in out),
            "cornerResearchPresent": sum(r["counts"]["pastCornerObservedForPaceResearch"] for r in out),
        },
        "races": out,
        "verifiedOverallFactors": 0,
        "realPredictionReady": False,
        "purchaseReady": False,
        "rawHorseRecordsIncluded": False,
        "note": (
            "既存の当日5種類の資料を再利用し、10項目のうち8枠の材料有無だけ集計。"
            "調教・近走の暫定基準は検証前で、展開・血統適性・斤量影響・騎手実績・"
            "馬体状態など残り6枠の能力評価も未実施。"
            "距離/コース・馬場適性の2枠は過去資料が未接続。"
            "JRA公式照合・実馬総合評価・3連単・購入は行いません。"
        )
    }
