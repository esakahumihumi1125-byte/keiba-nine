"""Independent-evidence upset 3連単 RESEARCH alternative for future full ten-factor inputs.

Not connected to live JRDB, JRA or purchasing. Needs an already validated
private ten-factor ranking and independently approved JRA checks. Does not
change or overwrite the normal formation; never uses odds, popularity or
post-race results. Conflicting/tied lower-ranked winners are held for review.
"""
from keiba_trifecta_builder import (
    build_trifecta, REQUIRED_EVIDENCE, MAX_POINTS, STAKE_YEN,
)

VERSION = "owner-upset-alternative-1"
MAX_RESEARCH_POINTS = 40
MIN_PREFERRED_POINTS = 30


def _hold(reason):
    return {
        "version": VERSION, "status": "held", "reason": reason,
        "candidateNumber": None, "candidateRank": None,
        "first": [], "second": [], "third": [],
        "tickets": [], "points": 0,
        "newTicketsComparedWithPrimary": 0,
        "stakePerPointYen": STAKE_YEN, "totalStakeYen": 0,
        "primaryUnchanged": True, "automaticallySelected": False,
        "researchOnly": True, "requiresOwnerReview": True,
        "bettingReady": False, "autoPurchase": False,
    }


def build_upset_alternative(ranking, review, evidence, primary):
    """One alternative 1st-place formation, not an automatic replacement.

    Inputs must be from the existing private full_ten_factor_preview helper,
    *not* from browser requests. Exactly one independently justified rank 4-6
    candidate is required; unsupported popularity-based additions are refused.
    """
    if (not isinstance(evidence, dict)
            or any(evidence.get(k) is not True for k in REQUIRED_EVIDENCE)):
        return _hold("missing_independent_evidence")
    if (not isinstance(ranking, list) or len(ranking) < 6
            or not isinstance(review, dict)
            or review.get("changesTrifecta") is not False
            or review.get("addsFirstPlaceAutomatically") is not False
            or not isinstance(primary, dict)
            or primary.get("status") != "review_only"
            or not isinstance(primary.get("tickets"), list)
            or not isinstance(primary.get("first"), list)
            or len(primary["first"]) != 2):
        return _hold("primary_not_ready")
    candidates = review.get("lowerRankCandidates")
    if not isinstance(candidates, list):
        return _hold("invalid_recheck")
    if not candidates:
        return _hold("no_independently_supported_lower_rank_horse")
    if len(candidates) != 1:
        return _hold("multiple_supported_lower_rank_horses")

    candidate = candidates[0]
    if (not isinstance(candidate, dict)
            or type(candidate.get("number")) is not int
            or type(candidate.get("rank")) is not int
            or candidate.get("decision") != "manual_recheck_only"
            or not 4 <= candidate["rank"] <= 6
            or not isinstance(candidate.get("supportFactors"), list)
            or len(candidate["supportFactors"]) < 2):
        return _hold("invalid_recheck")
    numbers = [h.get("number") for h in ranking if isinstance(h, dict)]
    if (len(numbers) != len(ranking)
            or any(type(n) is not int or not 1 <= n <= 18 for n in numbers)
            or len(set(numbers)) != len(numbers)
            or any(type(h.get("rank")) is not int or
                   type(h.get("weightedPoints")) is not int for h in ranking)
            or any(ranking[i]["weightedPoints"] < ranking[i + 1]["weightedPoints"]
                   for i in range(len(ranking) - 1))):
        return _hold("invalid_ranking")
    index = numbers.index(candidate["number"]) if candidate["number"] in numbers else -1
    if (index < 0 or ranking[index]["rank"] != candidate["rank"]
            or sum(h["rank"] == candidate["rank"] for h in ranking) != 1
            or candidate["number"] in primary["first"]):
        return _hold("ambiguous_candidate")
    # One unique top-rated runner: never resolve an exact top tie by number.
    if ranking[0]["rank"] != 1 or ranking[1]["weightedPoints"] == ranking[0]["weightedPoints"]:
        return _hold("top_rank_tied")
    first = [numbers[0], candidate["number"]]
    available = set(numbers)
    if (any(type(t) is not list or len(t) != 3 or
            any(type(n) is not int or n not in available for n in t)
            or len(set(t)) != 3 for t in primary["tickets"])
            or len(set(map(tuple, primary["tickets"]))) != len(primary["tickets"])):
        return _hold("invalid_primary")

    # Prefer 30-40 unique tickets, and never split exact score ties at the
    # second/third cutoffs to force a target count. Smaller fields can yield
    # fewer points; the 48 hard maximum still applies to all cases.
    choices = []
    for second_size in range(3, min(5, len(ranking)) + 1):
        if (second_size < len(ranking) and
                ranking[second_size - 1]["weightedPoints"] ==
                ranking[second_size]["weightedPoints"]):
            continue
        for third_size in range(max(second_size, 3), min(9, len(ranking)) + 1):
            if (third_size <= index or
                    (third_size < len(ranking) and
                     ranking[third_size - 1]["weightedPoints"] ==
                     ranking[third_size]["weightedPoints"])):
                continue
            proposed = build_trifecta(
                numbers, evidence=evidence, first=first,
                second=numbers[:second_size], third=numbers[:third_size],
            )
            if (proposed["status"] != "review_only"
                    or not 1 <= proposed["points"] <= min(MAX_RESEARCH_POINTS, MAX_POINTS)):
                continue
            preferred = MIN_PREFERRED_POINTS <= proposed["points"] <= MAX_RESEARCH_POINTS
            # Keep the candidate's presence in the third slot so that this
            # is a formation change, not fabricated individual tickets.
            choices.append((preferred, proposed["points"],
                            -second_size, -third_size, proposed))
    if not choices:
        return _hold("no_safe_formation")
    best = max(choices, key=lambda p: p[:4])[-1]
    main = {tuple(t) for t in primary["tickets"]}
    extra_count = sum(tuple(t) not in main for t in best["tickets"])
    return {
        "version": VERSION, "status": "review_only",
        "reason": "independent_lower_rank_winner_hypothesis",
        "candidateNumber": candidate["number"],
        "candidateRank": candidate["rank"],
        "first": best["first"], "second": best["second"], "third": best["third"],
        "tickets": best["tickets"], "points": best["points"],
        "newTicketsComparedWithPrimary": extra_count,
        "stakePerPointYen": STAKE_YEN,
        "totalStakeYen": best["totalStakeYen"],
        "primaryUnchanged": True, "automaticallySelected": False,
        "researchOnly": True, "requiresOwnerReview": True,
        "bettingReady": False, "autoPurchase": False,
    }
