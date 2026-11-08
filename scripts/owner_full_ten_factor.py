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

VERSION = "owner-full-ten-factor-gate-1"
UNASSESSED = "未評価"
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


def _empty(status, *, missing=None, evidence=None):
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "status": status, "researchOnly": True, "publishable": False,
        "bettingReady": False, "autoPurchase": False, "overallReady": False,
        "ranking": [], "missingByNumber": missing or {},
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
    numbers, ranking, missing = set(), [], {}
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
        "independentJraVerified": all(valid_official.values()),
    }
    # Source-based ties cannot be broken by horse number merely to fill slots.
    sizes = _safe_formation_sizes([
        {"weightedResearchPoints": h["weightedPoints"]} for h in ranking
    ])
    if sizes is None:
        response["status"] = "ambiguous_score_cutoff"
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
    return response
