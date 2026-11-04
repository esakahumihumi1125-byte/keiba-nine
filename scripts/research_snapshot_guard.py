"""Synthetic-only evidence cutoff and reproducibility check.

This is a RESEARCH input audit, not evidence of a source's authenticity,
license, ability, bookmaker odds, or betting readiness. No IO/network.
Only a synthetic pre-race snapshot can be fingerprinted here; never accept
private JRDB rows or live-race data.
"""
import hashlib
import json
from datetime import datetime
from evaluation_policy import timestamp, FACTORS

VERSION = "research-cutoff-snapshot-1"
MAX_ITEMS = 900
FORBIDDEN_RESULT_FIELDS = frozenset({
    "outcome", "outcomes", "result", "results", "finish",
    "trifectaPayout", "payout", "returned", "settlement",
    "actualResult", "officialResult", "winningNumbers",
})


def _valid_source(value, cutoff):
    if not isinstance(value, dict):
        raise ValueError("Evidence source is not an object")
    if set(value) & FORBIDDEN_RESULT_FIELDS:
        raise ValueError("Result material cannot be a pre-race source")
    source_id, reference = value.get("sourceId"), value.get("reference")
    if not isinstance(source_id, str) or not source_id.strip() or len(source_id) > 128:
        raise ValueError("Evidence sourceId is missing")
    if source_id != "synthetic":
        raise ValueError("Only synthetic evidence is permitted in research sandbox")
    if not isinstance(reference, str) or not reference.strip() or len(reference) > 256:
        raise ValueError("Evidence reference is missing")
    when = timestamp(value.get("availableAt"))
    if when > cutoff:
        raise ValueError("Evidence was not available by the prediction cutoff")
    # Extra unknown data is never included in the audit hash or exported.
    return {
        "sourceId": source_id,
        "reference": reference,
        "availableAtUtc": when.isoformat(),
    }


def _audit_item(item, cutoff):
    if not isinstance(item, dict):
        raise ValueError("Invalid assessment")
    if set(item) & FORBIDDEN_RESULT_FIELDS:
        raise ValueError("Assessment contains post-race results")
    grade = item.get("grade")
    if grade is not None and grade not in ("S", "A", "B", "C", "未評価"):
        raise ValueError("Unknown assessment grade")
    reason = item.get("reason")
    if reason is not None and (not isinstance(reason, str) or len(reason) > 1500):
        raise ValueError("Invalid assessment reason")
    evidence = item.get("evidence")
    if evidence is None:
        return {"grade": grade, "reason": reason, "evidence": []}, 1
    if not isinstance(evidence, list) or len(evidence) > 12:
        raise ValueError("Invalid evidence collection")
    sources = [_valid_source(v, cutoff) for v in evidence]
    keys = [(s["sourceId"], s["reference"], s["availableAtUtc"]) for s in sources]
    if len(set(keys)) != len(keys):
        raise ValueError("Repeated evidence in one assessment")
    # Sorting makes the fingerprint independent of source insertion order.
    sources.sort(key=lambda s: (s["sourceId"], s["reference"], s["availableAtUtc"]))
    unverified = int(not sources or not reason or not reason.strip())
    return {"grade": grade, "reason": reason, "evidence": sources,
            "winSupport": item.get("winSupport") is True}, unverified


def audit_research_snapshot(race):
    """Reject future/result data before planning; create deterministic test hash.

    Hash only the canonical pre-race input, never results. A hash alone does
    NOT prove the input was recorded before post time (no external timestamp
    service or immutable log is connected).
    """
    if not isinstance(race, dict) or race.get("recordType") != "test":
        raise ValueError("Only synthetic test races are supported")
    if set(race) & FORBIDDEN_RESULT_FIELDS:
        raise ValueError("Race outcome fields cannot be part of prediction input")
    as_of, off_at = timestamp(race.get("asOf")), timestamp(race.get("offAt"))
    if as_of >= off_at:
        raise ValueError("Prediction cutoff must precede race start")
    horses = race.get("horses")
    if not isinstance(horses, list) or not 2 <= len(horses) <= 18:
        raise ValueError("Expected 2-18 horses")
    numbers = [h.get("number") if isinstance(h, dict) else None for h in horses]
    if (any(type(n) is not int or not 1 <= n <= 18 for n in numbers)
            or len(set(numbers)) != len(numbers)):
        raise ValueError("Horse numbers must be distinct integers")
    stamp = race.get("date")
    if stamp is not None:
        if not isinstance(stamp, str):
            raise ValueError("Invalid race date")
        try:
            target = datetime.strptime(stamp, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid race date") from None
        from zoneinfo import ZoneInfo
        if off_at.astimezone(ZoneInfo("Asia/Tokyo")).date() != target:
            raise ValueError("Race date differs from scheduled start")
    ordered = []
    source_count = missing_count = 0
    for horse in sorted(horses, key=lambda h: h["number"]):
        if set(horse) & FORBIDDEN_RESULT_FIELDS:
            raise ValueError("Horse outcome fields cannot be used as prior evidence")
        assessments = horse.get("assessments", {})
        if not isinstance(assessments, dict) or set(assessments) - set(FACTORS):
            raise ValueError("Unknown assessment factor")
        graded = {}
        for name in sorted(FACTORS):
            if name not in assessments:
                missing_count += 1
                continue
            item, missing = _audit_item(assessments[name], as_of)
            graded[name] = item
            missing_count += missing
            source_count += len(item["evidence"])
        concerns = horse.get("blockingConcerns", [])
        if not isinstance(concerns, list) or len(concerns) > 25:
            raise ValueError("Invalid concern collection")
        normalized_concerns = []
        for concern in concerns:
            item, missing = _audit_item(concern, as_of)
            normalized_concerns.append(item)
            missing_count += missing
            source_count += len(item["evidence"])
        normalized_concerns.sort(key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True))
        ordered.append({"number": horse["number"], "assessments": graded,
                        "blockingConcerns": normalized_concerns})
    if source_count > MAX_ITEMS:
        raise ValueError("Too many evidence sources")
    canonical = {
        "version": VERSION,
        "recordType": "test",
        "raceId": race.get("raceId"),
        "date": stamp,
        "track": race.get("track"),
        "race": race.get("race"),
        "asOfUtc": as_of.isoformat(),
        "offAtUtc": off_at.isoformat(),
        "horses": ordered,
    }
    digest = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":"),
                   ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return {
        "version": VERSION,
        "recordType": "test",
        "snapshotSha256": digest,
        "horseCount": len(horses),
        "sourceCount": source_count,
        "unresolvedAssessmentCount": missing_count,
        "cutoffChecked": True,
        "futureEvidenceRejected": True,
        "verifiedSourceAuthenticity": False,
        "immutableExternalRecord": False,
        "predictionReady": False,
        "bettingReady": False,
        "note": ("架空研究の根拠時刻は予想締切以前。照合用ハッシュを発行。"
                 "入力日時は自己申告で、独立した取得日時証明・実馬予想ではありません。"),
    }
