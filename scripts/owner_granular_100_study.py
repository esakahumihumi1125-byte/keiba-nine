"""Owner research-only *granular* 100-point arithmetic, synthetic inputs ONLY.

This prototype intentionally cannot grade JRDB beta source rows. Raw provider
codes, prestart publication times, calibrated grade rubrics, and independent
JRA checks do not yet have a trusted scoring adapter. An arbitrary score must
not be promoted to a real-world horse ranking, ticket, or performance record.

Centi-points are integers to preserve exact boundaries and equal-score ties.
The legacy research-5 / research-6 signed records remain immutable.
"""
from evaluation_policy import (
    OWNER_FORMAL_FACTORS as WEIGHTS,
    OWNER_FORMAL_POLICY_VERSION, SCORE_THRESHOLDS,
    timestamp, supported,
)
from jrdb_coverage import CoverageError

VERSION = "owner-granular-100-synthetic-study-1"
MODE = "synthetic-granular-v1"
UNASSESSED = "未評価"
BANDS = ("S", "A", "B", "C")


def factor_grade(points_centi, weight):
    """Describe fractional earned points; NOT a model-derived ability grade.

    Display bands: S >= 90%, A >= 22/30 (~73.33%), B >= 50%.
    For training 30: S 27-30, A 22-<27, B 15-<22, C <15.
    This preserves fine differences within S and between factor scores.
    """
    if type(points_centi) is not int or type(weight) is not int or weight <= 0:
        raise CoverageError("Invalid granular factor points")
    maximum = weight * 100
    if not 0 <= points_centi <= maximum:
        raise CoverageError("Granular factor points exceed weight")
    if 10 * points_centi >= 9 * maximum:
        return "S"
    if 30 * points_centi >= 22 * maximum:
        return "A"
    if 2 * points_centi >= maximum:
        return "B"
    return "C"


def _overall(points_centi):
    # Total score is 0..10000 centi-points; never compare rounded floats.
    return next((grade for grade in ("S", "A", "B")
                 if points_centi >= SCORE_THRESHOLDS[grade] * 100), "C")


def research_granular_100(snapshot):
    """Synthetic-only dry run of the future full-factor scoring math.

    No source lookups, serialization, ticket construction or browser writes.
    Per-horse details (including secret source identifiers) are not returned
    unless all ten separately supported factor inputs exist before the cutoff.
    Unsupported and incomplete races receive NO ranked horse list.
    """
    if (not isinstance(snapshot, dict)
            or snapshot.get("mode") != MODE
            or snapshot.get("recordType") != "test"):
        raise CoverageError("Granular research accepts synthetic data only")
    try:
        as_of = timestamp(snapshot.get("asOf"))
        off = timestamp(snapshot.get("offAt"))
    except (ValueError, TypeError, OverflowError):
        raise CoverageError("Invalid study time") from None
    if as_of >= off:
        raise CoverageError("Research cutoff must precede off time")
    horses = snapshot.get("horses")
    if not isinstance(horses, list) or not 2 <= len(horses) <= 18:
        raise CoverageError("Invalid synthetic runner roster")
    seen = set()
    rows, missing = [], {}
    for horse in horses:
        number = horse.get("number") if isinstance(horse, dict) else None
        if type(number) is not int or not 1 <= number <= 18 or number in seen:
            raise CoverageError("Duplicate or invalid horse number")
        seen.add(number)
        assessments = horse.get("assessments", {})
        if not isinstance(assessments, dict) or set(assessments) - set(WEIGHTS):
            raise CoverageError("Invalid granular factor names")
        contributions, withheld = {}, []
        for factor, weight in WEIGHTS.items():
            item = assessments.get(factor)
            if item is None:
                withheld.append(factor)
                continue
            if not isinstance(item, dict):
                raise CoverageError("Invalid granular assessment")
            points = item.get("pointsCenti")
            if type(points) is not int or not 0 <= points <= weight * 100:
                raise CoverageError("Granular points invalid or out of bounds")
            grade = factor_grade(points, weight)
            if "grade" in item and item["grade"] != grade:
                raise CoverageError("Supplied grade contradicts earned points")
            try:
                traceable = supported(item, as_of)
            except (ValueError, TypeError, OverflowError, AttributeError):
                traceable = False
            if not traceable:
                withheld.append(factor)
                continue
            contributions[factor] = {
                "pointsCenti": points, "grade": grade, "weight": weight,
            }
        if withheld:
            missing[number] = withheld
        rows.append({"number": number, "contributions": contributions})

    # Avoid turning a partially observed set into an apparently precise order.
    if missing:
        return {
            "version": VERSION, "policyVersion": OWNER_FORMAL_POLICY_VERSION,
            "status": "missing_evidence", "syntheticOnly": True,
            "scoreReady": False, "missingByNumber": missing,
            "ranking": [], "formalPrediction": False, "bettingReady": False,
            "tickets": [], "purchases": [], "newProviderCalls": 0,
            "changesExistingReceipts": False, "changesExistingRoi": False,
        }
    ranked = []
    for row in rows:
        total = sum(part["pointsCenti"] for part in row["contributions"].values())
        if sum(part["weight"] for part in row["contributions"].values()) != 100:
            raise CoverageError("Incomplete granular scoring weights")
        ranked.append({
            "number": row["number"],
            "pointsCenti": total,
            "score100": total / 100,
            "overallGrade": _overall(total),
            "factorGrades": {
                key: value["grade"] for key, value in row["contributions"].items()
            },
            "factorPointsCenti": {
                key: value["pointsCenti"] for key, value in row["contributions"].items()
            },
        })
    ranked.sort(key=lambda h: (-h["pointsCenti"], h["number"]))
    last, rank = None, None
    for index, row in enumerate(ranked, 1):
        if row["pointsCenti"] != last:
            rank = index
        row["rank"] = rank
        last = row["pointsCenti"]
    return {
        "version": VERSION, "policyVersion": OWNER_FORMAL_POLICY_VERSION,
        "status": "synthetic_study", "syntheticOnly": True, "scoreReady": True,
        "missingByNumber": {}, "ranking": ranked,
        "factorCount": len(WEIGHTS), "totalWeight": sum(WEIGHTS.values()),
        "formalPrediction": False, "bettingReady": False,
        "tickets": [], "purchases": [], "newProviderCalls": 0,
        "changesExistingReceipts": False, "changesExistingRoi": False,
        "note": ("S/A/B/Cは閲覧用の帯、順位比較は根拠付きの0.01点単位。"
                 "本版は架空データ検証のみで実馬評価・馬券作成に未接続。"),
    }
