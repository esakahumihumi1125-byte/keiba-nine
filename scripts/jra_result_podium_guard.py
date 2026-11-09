"""Fail-closed podium-to-payout consistency check for a single JRA result page.

Only reconciles visible result rows with the *already parsed* 3連単/3連複
candidate amounts. This is not authentication, finality, refund verification,
a prediction or a settlement; it never calls JRA or modifies owner data.

Initially handles exactly one 1st, one 2nd and one or more tied 3rd horses.
Other tie patterns are explicitly pending instead of guessed.
"""
import re

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
    insufficient for official verified settlement. In particular first- and
    second-place dead heats, refunds, special pays and changed HTML are held.
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

    if (len(places[1]) != 1 or len(places[2]) != 1
            or not 1 <= len(places[3]) <= 6
            or len(seen) != 2 + len(places[3])):
        raise PodiumConsistencyError("Unsupported or incomplete podium")

    winner, second = places[1][0], places[2][0]
    three = {(winner, second, third) for third in places[3]}
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
        "podiumShape": ("third_place_dead_heat" if len(places[3]) > 1
                        else "single_third_place"),
        "matchingTrifectaCount": len(three),
        "matchingTrioCount": len(combination),
        "payoutMatchesDisplayedPodium": True,
        "officialJraVerified": False,
        "officialFinalityVerified": False,
        "refundsVerified": False,
        "settlementReady": False,
    }
