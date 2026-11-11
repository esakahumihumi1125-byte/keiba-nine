"""Owner-requested 2026-11-09 weights: exact 105-to-100 arithmetic review.

The ten numbers last requested total 105, not 100. This research-only
candidate preserves *all* relative preferences by applying 100/105 AFTER
summing evidence-backed grades. The deployed research-6 100-point policy,
sealed historic snapshots and published rankings are NEVER altered here.

No JRDB/JRA reads, credential handling, horse names, ticket generation or
official scores. The only supported input mode is an explicit synthetic test.
"""
from decimal import Decimal, ROUND_HALF_UP
from evaluation_policy import OWNER_FORMAL_FACTORS, OWNER_FORMAL_POLICY_VERSION, POINTS

VERSION = "owner-requested-weight-review-1"
REQUESTED_WEIGHTS = {
    "training": 30,
    "recent": 3,
    "course_distance": 17,
    "pace": 17,
    "ground": 15,
    "pedigree": 6,
    "draw_weight": 5,
    "jockey_stable": 10,
    "rotation": 1,
    "body_condition": 1,
}
RAW_TOTAL = sum(REQUESTED_WEIGHTS.values())
SCORE_MAX = 100
GRADE_MAX = 3
assert len(REQUESTED_WEIGHTS) == 10 and RAW_TOTAL == 105
assert set(REQUESTED_WEIGHTS) == set(OWNER_FORMAL_FACTORS)
assert sum(OWNER_FORMAL_FACTORS.values()) == 100


def requested_policy_review():
    """Exact, immutable-in-spirit values, with no hypothetical grades."""
    return {
        "version": VERSION,
        "status": "candidate_not_active",
        "rawRequestedWeightTotal": RAW_TOTAL,
        "normalizedScoreMax": SCORE_MAX,
        "normalization": "exact_ratio_100_over_105",
        "requestedWeights": dict(REQUESTED_WEIGHTS),
        "normalizedShares": {
            key: {"numerator": weight * SCORE_MAX, "denominator": RAW_TOTAL}
            for key, weight in REQUESTED_WEIGHTS.items()
        },
        "existingResearchPolicyVersion": OWNER_FORMAL_POLICY_VERSION,
        "existingResearchWeights": dict(OWNER_FORMAL_FACTORS),
        "requiresAllTenValidatedEvidence": True,
        "independentJraVerified": False,
        "officialPredictionReady": False,
        "bettingReady": False,
        "publishable": False,
    }


def synthetic_score_preview(record):
    """Arithmetic-only demo; cannot accept race data or assign official rank.

    A missing/unassessed factor blocks score output; never fill it with C.
    Numerator is exact integer third-points, so factor rounding cannot change
    a ranking even if this formula is later reviewed for trusted evidence.
    """
    if (type(record) is not dict
            or set(record) != {"recordType", "grades"}
            or record["recordType"] != "synthetic_test"
            or type(record["grades"]) is not dict):
        raise ValueError("Only synthetic ten-factor grade reviews are accepted")
    grades = record["grades"]
    if set(grades) - set(REQUESTED_WEIGHTS):
        raise ValueError("Unknown factors")
    if any(type(v) is not str or v not in (*POINTS, "未評価")
           for v in grades.values()):
        raise ValueError("Invalid synthetic grade")
    missing = [factor for factor in REQUESTED_WEIGHTS
               if grades.get(factor) not in POINTS]
    response = {
        "version": VERSION, "status": "missing_synthetic_factors" if missing
        else "synthetic_arithmetic_only",
        "missingFactors": missing,
        "score100": None,
        "rawThirdPoints": None,
        "maximumRawThirdPoints": GRADE_MAX * RAW_TOTAL,
        "normalizationNumerator": SCORE_MAX,
        "normalizationDenominator": GRADE_MAX * RAW_TOTAL,
        "researchOnly": True,
        "officialPredictionReady": False,
        "publishable": False,
        "bettingReady": False,
        "autoPurchase": False,
        "trifecta": None,
    }
    if missing:
        return response
    weighted_thirds = sum(REQUESTED_WEIGHTS[k] * POINTS[grades[k]]
                          for k in REQUESTED_WEIGHTS)
    response["rawThirdPoints"] = weighted_thirds
    response["score100"] = float(
        (Decimal(SCORE_MAX * weighted_thirds)
         / Decimal(GRADE_MAX * RAW_TOTAL)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
    return response
