"""Fail-closed podium-to-payout consistency check for a single JRA result page.

Only reconciles visible result rows with the *already parsed* 3連単/3連複
candidate amounts. This is not authentication, finality, refund verification,
a prediction or a settlement; it never calls JRA or modifies owner data.

Supports JRA's explicit first-, second- and third-place dead-heat rules
without guessing payouts: expected exact 3連単/3連複 combinations must match
the page's displayed payout rows. Unsafe or incomplete patterns stay pending.
"""
import re
from itertools import permutations

VERSION = "owner-jra-podium-payout-check-1"
NUMBER = re.compile(r"(?:[1-9]|1[0-8])\Z")
MAX_RUNNERS = 18


class PodiumConsistencyError(ValueError):
    """No page fragments, horse names or private data in exception details."""


def _cell(text):
    if not isinstance(text, str) or len(text) > 600:
        raise PodiumConsistencyError("Invalid result table cell")
    return re.sub(r"\s+", "", text)


def podium_payout_consistency(rows, trifecta, trio):
    """Ensure exact winning combinations agree with the visible result table.

    A matching, unambiguous podium and all combinations are necessary but
    insufficient for official verified settlement. Refunds, special pays and
    changed HTML are held, including unexplained/unsupported tie patterns.
    """
    if (not isinstance(rows, list) or len(rows) > 1000
            or not isinstance(trifecta, list) or not isinstance(trio, list)):
        raise PodiumConsistencyError("Invalid result table data")
    headers = []
    for i, row in enumerate(rows):
        if not isinstance(row, list) or len(row) > 32:
            raise PodiumConsistencyError("Unexpected result row")
        cells = [_cell(c) for c in row]
        if "着順" in cells and "馬番" in cells:
            headers.append((i, cells.index("着順"), cells.index("馬番")))
    if len(headers) != 1:
        raise PodiumConsistencyError("Unique finishing table not found")

    index, placing_idx, number_idx = headers[0]
    places = {1: [], 2: [], 3: []}
    seen, started = set(), False
    for row in rows[index + 1:]:
        if len(row) <= max(placing_idx, number_idx):
            if started:
                break
            raise PodiumConsistencyError("Incomplete finishing table")
        placing, horse = _cell(row[placing_idx]), _cell(row[number_idx])
        if not NUMBER.fullmatch(placing) or not NUMBER.fullmatch(horse):
            if started:
                break
            raise PodiumConsistencyError("Unrecognized finishing row")
        started = True
        place, number = int(placing), int(horse)
        if place > 3:
            break
        if number in seen or len(seen) >= MAX_RUNNERS:
            raise PodiumConsistencyError("Duplicate result horse")
        seen.add(number)
        places[place].append(number)

    first, second, third = places[1], places[2], places[3]
    # JRA's rule: a tie at place N occupies the subsequent finishing
    # positions until every tied horse has been considered (FAQ 1_12).
    # Only the first three effective positions determine trifecta payouts.
    # The displayed rank numbers MUST skip the slots consumed by ties.
    if len(first) == 1 and len(second) == 1 and 1 <= len(third) <= 6:
        # 1st A, 2nd B, tied 3rd C/D => A-B-C / A-B-D; NEVER C-D.
        three = {(first[0], second[0], n) for n in third}
        shape = "third_place_dead_heat" if len(third) > 1 else "single_third_place"
    elif len(first) in (2, 3) and not second and (
            (len(first) == 2 and 1 <= len(third) <= 6) or
            (len(first) == 3 and not third)):
        # Tied 1st A/B, official next finishing place is 3rd C:
        # A-B-C and B-A-C. Three-way first ties yield 3! permutations.
        three = (set(permutations(first, 3)) if len(first) == 3
                 else {(a, b, c) for a, b in permutations(first, 2)
                       for c in third})
        shape = "first_place_dead_heat"
    elif len(first) == 1 and 2 <= len(second) <= 4 and not third:
        # 1st A, tied 2nd B/C: A-B-C and A-C-B; do not import 4th.
        three = {(first[0], a, b) for a, b in permutations(second, 2)}
        shape = "second_place_dead_heat"
    else:
        raise PodiumConsistencyError("Unsupported or incomplete podium")
    # Avoid a combinatorial payout explosion and refuse ambiguous layouts.
    if not 1 <= len(three) <= 18:
        raise PodiumConsistencyError("Unsupported number of winning combinations")
    combination = {tuple(sorted(row)) for row in three}
    try:
        paid_three = [tuple(row["ticket"]) for row in trifecta]
        paid_trio = [tuple(row["ticket"]) for row in trio]
    except (TypeError, KeyError, ValueError):
        raise PodiumConsistencyError("Payout candidate format mismatch") from None
    if (len(paid_three) != len(three) or set(paid_three) != three
            or len(paid_trio) != len(combination)
            or set(paid_trio) != combination):
        raise PodiumConsistencyError("Payout tickets disagree with result table")

    return {
        "version": VERSION,
        "podiumShape": shape,
        "matchingTrifectaCount": len(three),
        "matchingTrioCount": len(combination),
        "payoutMatchesDisplayedPodium": True,
        "officialJraVerified": False,
        "officialFinalityVerified": False,
        "refundsVerified": False,
        "settlementReady": False,
    }
