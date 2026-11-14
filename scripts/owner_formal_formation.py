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

    Prefer two first-place horses when that boundary can be chosen without
    splitting a real equality. Try three only when two cannot be selected,
    then a single clear leader as a last resort. For small fields the natural
    ticket count can be lower than thirty. A 41..48 point formation is a
    fallback, not an invitation to increase an already good 30..40 ticket.
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

    for first in (2, 3, 1):
        if not complete(first):
            continue
        candidates = []
        for second in range(first + 1, min(count, 8) + 1):
            if not complete(second):
                continue
            for third in range(max(3, second), min(count, 12) + 1):
                if not complete(third):
                    continue
                # These candidate groups are nested: first ⊂ second ⊆ third.
                # Every horse may occupy only one finishing position,
                # yielding this exact de-duplicated ticket cardinality.
                points = first * (second - 1) * (third - 2)
                if 1 <= points <= MAX_POINTS:
                    candidates.append((points, first, second, third))
        if candidates:
            best = max(candidates, key=lambda row: (
                PREFERRED_LOW <= row[0] <= PREFERRED_HIGH,
                row[0], row[3], -row[2]
            ))
            return best[1:]
    return None
