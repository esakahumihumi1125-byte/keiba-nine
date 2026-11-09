"""Private full-ten-factor ranking gate for independently checked prestart inputs.

Does not fetch or authenticate JRDB/JRA, grade raw provider fields, or publish
predictions. The caller must validate evidence provenance and official checks
server-side; never pass client-asserted verification flags into this helper.
Incomplete, late, tied-boundary, or unverified evidence yields zero tickets.
"""
from datetime import datetime

from evaluation_policy import FACTORS, POINTS, POLICY_VERSION, SCORE_THRESHOLDS, supported, timestamp
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import _safe_formation_sizes
from keiba_trifecta_builder import REQUIRED_EVIDENCE, build_trifecta
from owner_upset_alternative import build_upset_alternative, _hold as hold_upset

VERSION = "owner-full-ten-factor-gate-1"
RECHECK_VERSION = "owner-full-ten-winner-recheck-1"
UNASSESSED = "未評価"
# Two different source families, not just two correlated labels, are needed
# before a lower-ranked horse can be put on the explicit winner review list.
RECHECK_FACTORS = ("training", "course_distance", "pace")
OFFICIAL = ("jra_starters_verified", "jra_scratches_verified",
            "jra_going_verified", "jra_posttime_verified")
assert len(FACTORS) == 10 and sum(FACTORS.values()) == 100


def _clock(value):
    dt = timestamp(value) if isinstance(value, str) else value
    if not isinstance(dt, datetime) or dt.tzinfo is None or dt.utcoffset() is None:
        raise CoverageError("Timezone-aware server clock required")
    return dt


def _grade(weighted):
    # Compare integers, not the rounded display score.
    if 100 * weighted >= 300 * SCORE_THRESHOLDS["S"]:
        return "S"
    if 100 * weighted >= 300 * SCORE_THRESHOLDS["A"]:
        return "A"
    if 100 * weighted >= 300 * SCORE_THRESHOLDS["B"]:
        return "B"
    return "C"


def _empty_recheck():
    return {
        "version": RECHECK_VERSION,
        "lowerRankCandidates": [], "recentLossCandidates": [],
        "changesTrifecta": False, "addsFirstPlaceAutomatically": False,
        "researchOnly": True, "requiresIndependentPrestartSources": True,
    }


def _has_independent_pair(support):
    """Require 2 factor families backed by non-overlapping source IDs."""
    keys = tuple(support)
    return any(
        support[a].isdisjoint(support[b])
        for i, a in enumerate(keys) for b in keys[i + 1:]
    )


def _empty(status, *, missing=None, evidence=None):
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "status": status, "researchOnly": True, "publishable": False,
        "bettingReady": False, "autoPurchase": False, "overallReady": False,
        "ranking": [], "missingByNumber": missing or {},
        "winnerRecheck": _empty_recheck(),
        "upsetAlternative": hold_upset("full_ten_not_ready"),
        "trifecta": build_trifecta([1, 2, 3, 4], evidence=evidence),
    }


def full_ten_factor_preview(snapshot, *, now):
    """Compute a private research ranking and conditionally gated 3連単 draft.

    Expected input is a verified *internal* assessment snapshot, not an HTTP
    request or provider payload. Both each S/A/B/C and each official approval
    must have been independently checked by the upstream private service.
    """
    if not isinstance(snapshot, dict) or snapshot.get("mode") != "owner_verified_prestart_v1":
        raise CoverageError("Invalid full-factor input")
    as_of, off = timestamp(snapshot.get("asOf")), timestamp(snapshot.get("offAt"))
    current = _clock(now)
    if not as_of < off:
        raise CoverageError("Prediction timestamp is not before the race")
    # Never recalculate a horse ranking after its expected off-time.
    if current >= off or current < as_of:
        return _empty("outside_prestart_window")

    horses = snapshot.get("horses")
    if not isinstance(horses, list) or not 4 <= len(horses) <= 18:
        raise CoverageError("Expected 4-18 independently checked starters")
    official = snapshot.get("independentJra")
    if not isinstance(official, dict):
        official = {}
    valid_official = {k: official.get(k) is True for k in OFFICIAL}
    numbers, ranking, missing, support_by_number = set(), [], {}, {}
    for horse in horses:
        if not isinstance(horse, dict):
            raise CoverageError("Invalid runner assessment")
        n = horse.get("number")
        if type(n) is not int or not 1 <= n <= 18 or n in numbers:
            raise CoverageError("Invalid or duplicate runner number")
        numbers.add(n)
        a = horse.get("assessments")
        if not isinstance(a, dict) or set(a) - set(FACTORS):
            raise CoverageError("Invalid factor names")
        weighted, absent, grades = 0, [], {}
        for key, weight in FACTORS.items():
            item = a.get(key)
            if item is not None and (
                not isinstance(item, dict) or item.get("grade") not in (*POINTS, UNASSESSED)
            ):
                raise CoverageError("Invalid factor grade")
            if not item or item["grade"] == UNASSESSED or not supported(item, as_of):
                absent.append(key)
                grades[key] = UNASSESSED
                continue
            grades[key] = item["grade"]
            weighted += POINTS[item["grade"]] * weight
        if absent:
            missing[n] = absent

        # These flags do NOT create a win pick. They only make a horse
        # eligible for a separate, explicitly reviewed lower-rank hypothesis.
        # Never copy provider references or free-form reasons to the client.
        concerns = horse.get("blockingConcerns", [])
        if not isinstance(concerns, list) or len(concerns) > 12:
            raise CoverageError("Malformed race blocking concerns")
        source_ids = {}
        if not concerns:
            for factor in RECHECK_FACTORS:
                item = a.get(factor)
                if (grades[factor] in ("S", "A")
                        and item is not None
                        and item.get("winSupport") is True):
                    source_ids[factor] = frozenset(
                        e["sourceId"].strip() for e in item["evidence"]
                    )
        support_by_number[n] = {
            "sources": source_ids, "blocked": bool(concerns),
        }
        ranking.append({
            "number": n, "grades": grades, "weightedPoints": weighted,
        })

    # Do not extrapolate or sort partial 2-factor material into a full ranking.
    if missing:
        return _empty("missing_evidence", missing=missing)

    ranking.sort(key=lambda h: (-h["weightedPoints"], h["number"]))
    for pos, horse in enumerate(ranking):
        horse["score100"] = round(horse["weightedPoints"] / 3, 2)
        horse["overallGrade"] = _grade(horse["weightedPoints"])
        horse["rank"] = (ranking[pos - 1]["rank"]
                         if pos and ranking[pos - 1]["weightedPoints"] == horse["weightedPoints"]
                         else pos + 1)

    approval = (snapshot.get("assessmentValidated") is True
                and snapshot.get("predictionValidated") is True)

    recheck = _empty_recheck()
    # An unsupported or stale assessment never contributes, because the
    # full ranking is blocked above when any one factor is unassessed.
    if snapshot.get("assessmentValidated") is True:
        for horse in ranking:
            details = support_by_number[horse["number"]]
            sources = details["sources"]
            if details["blocked"] or not _has_independent_pair(sources):
                continue
            candidate = {
                "number": horse["number"], "rank": horse["rank"],
                "supportFactors": [k for k in RECHECK_FACTORS if k in sources],
                "overallGrade": horse["overallGrade"],
                "decision": "manual_recheck_only",
            }
            if 4 <= horse["rank"] <= 6:
                recheck["lowerRankCandidates"].append(candidate)
            if horse["grades"]["recent"] in ("B", "C"):
                recheck["recentLossCandidates"].append(candidate.copy())
    evidence = {k: valid_official[k] for k in OFFICIAL}
    evidence.update({
        "ten_factor_assessments_verified": snapshot.get("assessmentValidated") is True,
        "prediction_validated": approval,
        "before_off_time": True,
    })
    # Keep the official check and ranking even when generation is blocked.
    response = {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "status": "research_only", "researchOnly": True,
        "publishable": False, "bettingReady": False,
        "autoPurchase": False, "overallReady": True,
        "ranking": ranking, "missingByNumber": {},
        "winnerRecheck": recheck,
        "independentJraVerified": all(valid_official.values()),
    }
    # Source-based ties cannot be broken by horse number merely to fill slots.
    sizes = _safe_formation_sizes([
        {"weightedResearchPoints": h["weightedPoints"]} for h in ranking
    ])
    if sizes is None:
        response["status"] = "ambiguous_score_cutoff"
        response["upsetAlternative"] = hold_upset("ambiguous_score_cutoff")
        response["trifecta"] = build_trifecta(
            [h["number"] for h in ranking], evidence=None)
        return response
    first_size, second_size, third_size = sizes
    response["trifecta"] = build_trifecta(
        [h["number"] for h in ranking], evidence=evidence,
        first=[h["number"] for h in ranking[:first_size]],
        second=[h["number"] for h in ranking[:second_size]],
        third=[h["number"] for h in ranking[:third_size]],
    )
    if response["trifecta"]["status"] == "review_only":
        response["status"] = "review_only"
    # An independently supported lower-ranked winner is an ALTERNATIVE
    # hypothesis only; never edit/replace the sealed primary formation.
    # Fail closed if 4 JRA checks, 10 grades or prestart review are absent.
    response["upsetAlternative"] = build_upset_alternative(
        ranking, recheck, evidence, response["trifecta"],
    )
    return response
