"""Deterministic 1/2/3-place sizes for an ALL-TEN verified score order.

Only the private formal 10-factor gate may use these sizes after its own
independent JRA and prestart checks. No provider reads, probabilities,
automatic purchases, receipts, odds or retrospective rankings occur here.

The legacy two-factor 40-point builder and its signed receipts are untouched.
"""
from jrdb_coverage import CoverageError

MAX_POINTS = 48
PREFERRED_LOW, PREFERRED_HIGH = 30, 40
MIN_RUNNERS, MAX_RUNNERS = 4, 18


def formal_formation_sizes(ranked):
    """Choose whole tied-score groups, prefer 30..40, never exceed 48.

    Normally prefer two first-place horses when that boundary can be
    chosen without splitting a real equality. A single demonstrably clear
    S-grade leader (at least a 10-point lead and an A-or-lower runner-up)
    may instead take a whole-tier 30..40-point formation rather than an
    otherwise necessary 41..48-point two-winner fallback. Three first-place
    horses are considered only when two cannot be selected. This is a fixed
    RESEARCH heuristic, not a calibrated reliability claim or proof of a
    safe single-winner bet. For small fields fewer than thirty is normal.
    Returns (first, second, third) group sizes or None if ambiguous.

    This has NO authority to grade horses or approve betting. The caller must
    independently verify all evidence, starters, scratches and off-time.
    """
    if not isinstance(ranked, list) or not MIN_RUNNERS <= len(ranked) <= MAX_RUNNERS:
        raise CoverageError("Invalid formal ranking length")
    scores = []
    for row in ranked:
        value = row.get("weightedPoints") if isinstance(row, dict) else None
        if type(value) is not int or not 0 <= value <= 300:
            raise CoverageError("Invalid formal weighted score")
        scores.append(value)
    if any(a < b for a, b in zip(scores, scores[1:])):
        raise CoverageError("Formal scores must be in descending order")

    count = len(scores)

    def complete(size):
        return size <= count and (
            size == count or scores[size - 1] > scores[size]
        )

    winners = {}
    for first in (2, 3, 1):
        if not complete(first):
            continue
        candidates = []
        # Any second cutoff >=9 already exceeds 48 with the smallest
        # permissible first tier: 1 * (9-1) * (9-2) == 56.
        # The THIRD tier is different: with 1S / 3A / 6B / 4C, retaining
        # the entire C band gives 1 * (4-1) * (14-2) == 36. An artificial
        # 12-runner ceiling would discard that valid 30-40 point option.
        # Examine through ALL 18 starters without splitting any equality.
        for second in range(first + 1, min(count, 8) + 1):
            if not complete(second):
                continue
            for third in range(max(3, second), count + 1):
                if not complete(third):
                    continue
                # These candidate groups are nested: first ⊂ second ⊆ third.
                # Every horse may occupy only one finishing position,
                # yielding this exact de-duplicated ticket cardinality.
                points = first * (second - 1) * (third - 2)
                if 1 <= points <= MAX_POINTS:
                    candidates.append((points, first, second, third))
        if candidates:
            winners[first] = max(candidates, key=lambda row: (
                PREFERRED_LOW <= row[0] <= PREFERRED_HIGH,
                row[0], row[3], -row[2]
            ))
    two = winners.get(2)
    one = winners.get(1)
    # Default two winners remain preferred. The clear-leader exception is
    # deliberately strict: exact unrounded /3 integer scores, a complete
    # top-1 boundary, S (>=85/100), A-or-below runner-up, and >=10/100
    # lead. Otherwise turning a 48pt/two-winner research reference into a
    # 36pt/single-winner reference would conceal material first-place risk.
    strong_single = (
        one is not None and two is not None
        and scores[0] >= 255 and scores[1] < 255
        and scores[0] - scores[1] >= 30
        and PREFERRED_LOW <= one[0] <= PREFERRED_HIGH
        and not PREFERRED_LOW <= two[0] <= PREFERRED_HIGH
    )
    if strong_single:
        return one[1:]
    for first in (2, 3, 1):
        if first in winners:
            return winners[first][1:]
    return None
