"""KEIBA NINE: deterministic 100-yen 3連単 formation with hard safety gates.

This module performs NO API calls, purchases, file writes, or prediction.
It must only be fed a trusted, already-validated race ranking and independent
JRA final checks from the private server. Experimental JRDB two-factor hints
CANNOT satisfy the evidence requirements. A missing flag returns NO tickets.
"""
from itertools import product

VERSION = "keiba-trifecta-builder-1"
STAKE_YEN = 100
MAX_POINTS = 48
REQUIRED_EVIDENCE = (
    "jra_starters_verified",
    "jra_scratches_verified",
    "jra_going_verified",
    "jra_posttime_verified",
    "ten_factor_assessments_verified",
    "prediction_validated",
    "before_off_time",
)


class FormationError(ValueError):
    """Malformed input, duplicate runner or too many requested tickets."""


def _numbers(raw, name, *, maximum=18):
    if not isinstance(raw, (list, tuple)) or not 1 <= len(raw) <= maximum:
        raise FormationError("Invalid " + name + " candidates")
    if any(type(n) is not int or not 1 <= n <= 18 for n in raw):
        raise FormationError("Horse numbers must be integers from 1 to 18")
    if len(set(raw)) != len(raw):
        raise FormationError("Duplicate horse in " + name)
    return tuple(raw)


def _blocked(missing):
    return {
        "version": VERSION, "status": "not_ready",
        "blockingEvidence": list(missing),
        "first": [], "second": [], "third": [], "individual": [],
        "tickets": [], "points": 0, "stakePerPointYen": STAKE_YEN,
        "totalStakeYen": 0, "maxPoints": MAX_POINTS,
        "bettingReady": False,
        "note": ("JRA公式と全項目評価が未検証のため、"
                 "実馬の買い目を自動で作成しません。"),
    }


def build_trifecta(ordered_numbers, *, evidence=None,
                   first=None, second=None, third=None,
                   extra_tickets=()):
    """Create unique formation tickets ONLY with complete, trusted evidence.

    Defaults are 2 × 5 × 7 candidate lists (40 *actual* combinations with
    seven or more distinct horses), max 48 points, one ticket 100 yen.
    For small fields fewer points are normal: no padding just to reach 40.
    'first' may hold 1 (strong single), 2 (normal), or 3 (complex) horses.
    Extra tickets for researched upsets must be explicitly chosen upstream.
    """
    ranked = _numbers(ordered_numbers, "ordered runners")
    if not isinstance(evidence, dict):
        missing = REQUIRED_EVIDENCE
    else:
        missing = tuple(key for key in REQUIRED_EVIDENCE
                        if evidence.get(key) is not True)
    if missing:
        return _blocked(missing)

    # NO arbitrary 'verified' boolean is accepted: every required independent
    # server-owned evidence flag is required as a literal bool True.
    firsts = _numbers(first if first is not None else ranked[:2],
                      "first-place", maximum=3)
    seconds = _numbers(second if second is not None else ranked[:5],
                       "second-place")
    thirds = _numbers(third if third is not None else ranked[:7],
                      "third-place")
    available = set(ranked)
    if not (set(firsts) <= available and set(seconds) <= available
            and set(thirds) <= available):
        raise FormationError("Candidate outside verified runner list")
    if not isinstance(extra_tickets, (list, tuple)) or len(extra_tickets) > MAX_POINTS:
        raise FormationError("Invalid individual-ticket collection")

    result, seen = [], set()
    for a, b, c in product(firsts, seconds, thirds):
        if len({a, b, c}) == 3 and (a, b, c) not in seen:
            result.append((a, b, c))
            seen.add((a, b, c))
    added = []
    for pick in extra_tickets:
        if (not isinstance(pick, (list, tuple)) or len(pick) != 3
                or any(type(n) is not int or n not in available for n in pick)
                or len(set(pick)) != 3):
            raise FormationError("Invalid individual trifecta ticket")
        ticket = tuple(pick)
        if ticket not in seen:
            result.append(ticket)
            added.append(ticket)
            seen.add(ticket)
    if len(result) > MAX_POINTS:
        raise FormationError("Trifecta count exceeds 48; revise formation")

    return {
        "version": VERSION, "status": "review_only",
        "blockingEvidence": [],
        "first": list(firsts), "second": list(seconds),
        "third": list(thirds),
        "individual": [list(t) for t in added],
        "tickets": [list(t) for t in result],
        "points": len(result),
        "stakePerPointYen": STAKE_YEN,
        "totalStakeYen": len(result) * STAKE_YEN,
        "maxPoints": MAX_POINTS,
        "bettingReady": False,  # review is still mandatory; never auto-purchase
        "note": ("候補から3連単を重複除外して計算した研究用下書き。"
                 "1点100円・上限48点。発走前の本人確認と購入操作が必要。"
                 "人気・オッズで順位を自動変更しません。"),
    }
