"""Read-only, fail-closed comparison of the two owner 10-factor policies.

Only accepts an INTERNAL independently checked prestart snapshot, passed
through owner_full_ten_factor's existing provenance, roster and time gate.
No direct HTTP entrypoint, raw JRDB payload, network access, prediction
publishing, ticket generation by this module, or archived-record mutation.

The original research-6 ranking is not rewritten. This candidate preserves
the owner's relative 105-weight preferences by scoring over 315 third-points.
"""
from decimal import Decimal, ROUND_HALF_UP

from evaluation_policy import OWNER_FORMAL_POLICY_VERSION, POINTS
from owner_full_ten_factor import full_ten_factor_preview
from owner_requested_weight_reconciliation import (
    REQUESTED_WEIGHTS, RAW_TOTAL, VERSION as REQUESTED_VERSION,
)

VERSION = "owner-ten-factor-policy-comparison-1"
SCORE_DENOMINATOR = 3 * RAW_TOTAL
ELIGIBLE_RESEARCH_STATUSES = frozenset((
    "review_only", "research_only", "ambiguous_score_cutoff"
))
assert SCORE_DENOMINATOR == 315 and len(REQUESTED_WEIGHTS) == 10


def _blocked(reason):
    """Never infer a candidate rank from incomplete or unverified materials."""
    return {
        "version": VERSION,
        "requestedPolicyVersion": REQUESTED_VERSION,
        "baselinePolicyVersion": OWNER_FORMAL_POLICY_VERSION,
        "status": "held",
        "reasonCode": reason,
        "researchOnly": True,
        "candidateRankReady": False,
        "publishable": False,
        "bettingReady": False,
        "autoPurchase": False,
        "runners": [],
        "changedPairwiseOrderCount": 0,
        "candidateTickets": [],
    }


def _score(raw):
    return float(
        (Decimal(100 * raw) / Decimal(SCORE_DENOMINATOR)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )


def _sign(value):
    return (value > 0) - (value < 0)


def compare_verified_policies(snapshot, *, now):
    """Compare ordinal ranks only; never return tickets or make a win pick.

    Caller must construct and provenance-verify snapshot server-side. In
    particular, no HTTP user-supplied verification flags can authorize it.
    This helper is currently a synthetic/internal research tool, not linked
    to the live two-factor JRDB prediction or its sealed receipts.
    """
    base = full_ten_factor_preview(snapshot, now=now)
    if (base.get("overallReady") is not True
            or base.get("independentJraVerified") is not True
            or base.get("status") not in ELIGIBLE_RESEARCH_STATUSES
            or snapshot.get("assessmentValidated") is not True
            or snapshot.get("predictionValidated") is not True):
        # Use only fixed codes from the already validated strict gate.
        return _blocked(base.get("status", "source_not_ready"))

    source = base["ranking"]
    if not 4 <= len(source) <= 18:
        return _blocked("runner_count_invalid")
    items = []
    for horse in source:
        grades = horse["grades"]
        if set(grades) != set(REQUESTED_WEIGHTS) or any(
            grade not in POINTS for grade in grades.values()
        ):
            return _blocked("incomplete_factor_grades")
        raw = sum(
            REQUESTED_WEIGHTS[key] * POINTS[grades[key]]
            for key in REQUESTED_WEIGHTS
        )
        items.append({
            "number": horse["number"], "baselineRank": horse["rank"],
            "baselineThirdPoints": horse["weightedPoints"],
            "candidateThirdPoints": raw,
            "candidateScore100": _score(raw),
        })

    items.sort(key=lambda row: (-row["candidateThirdPoints"], row["number"]))
    for position, item in enumerate(items):
        item["candidateRank"] = (
            items[position - 1]["candidateRank"]
            if position and item["candidateThirdPoints"] ==
            items[position - 1]["candidateThirdPoints"]
            else position + 1
        )
        item["rankDelta"] = item["baselineRank"] - item["candidateRank"]

    # Comparisons are based on exact integers, never 2dp display values.
    # Pairs that are tied in either policy are not counted as reversals.
    reversals = 0
    for i, left in enumerate(items):
        for right in items[i + 1:]:
            old_order = _sign(left["baselineThirdPoints"] -
                              right["baselineThirdPoints"])
            new_order = _sign(left["candidateThirdPoints"] -
                              right["candidateThirdPoints"])
            reversals += int(old_order * new_order < 0)
    return {
        "version": VERSION,
        "requestedPolicyVersion": REQUESTED_VERSION,
        "baselinePolicyVersion": OWNER_FORMAL_POLICY_VERSION,
        "status": "read_only_policy_comparison",
        "scoreFormula": "100*weighted_grade_thirds/315",
        "sourceGateStatus": base["status"],
        "researchOnly": True,
        "candidateRankReady": True,
        "publishable": False,
        "bettingReady": False,
        "autoPurchase": False,
        "runners": items,
        "changedPairwiseOrderCount": reversals,
        "candidateTickets": [],
    }
