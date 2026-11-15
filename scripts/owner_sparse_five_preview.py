"""Unsigned five-factor research references despite an ungraded recent run.

Do not reinterpret absent JRDB recent evidence as C/zero or as a calibrated
grade. Given four fully observed hypothetical factors, find 1st/2nd/3rd
membership boundaries that remain invariant for *every possible* missing
three-point recent grade. Display only as an ephemeral owner-only research
example, never sign, save, price as a wager, or create retrospective picks.
"""
from datetime import datetime
from jrdb_coverage import CoverageError
from evaluation_policy import POINTS
from owner_new_weight_five_research import KEYS, WEIGHTS
from owner_research6_five_drafts import (
    _check_report, _check_horses, _normal_programme, JST, STAKE,
)
from jrdb_evidence_readiness import _valid_date

VERSION = "owner-sparse-five-79-reference-1"
RECENT = "recent"
MAX_TICKETS = 40
MAX_RACES = 120
assert WEIGHTS[RECENT] == 3 and sum(WEIGHTS.values()) == 79


def _cutoff_proven(ranked, size):
    return (size == len(ranked) or
            min(x["floor"] for x in ranked[:size])
            > max(x["ceiling"] for x in ranked[size:]))


def _candidate(race):
    """Only one or more MISSING RECENT grades; every other band present."""
    runners = _check_horses(race)  # strict source arithmetic + cohort check
    n = len(runners)
    if not 4 <= n <= 18:
        return None, "too_few_runners"
    ranked, missing_recent = [], 0
    for h in race["horses"]:
        bands = h["bands"]
        # Every observed four-factor grade must agree with the original
        # independently computed 34-point course/pace and 12-point going
        # subtotals. A partial five-factor score alone is null and cannot
        # detect alteration of a known band. Fail closed on that gap.
        pair = ("course_distance", "pace")
        pair_raw = (None if any(bands[k] == "未評価" for k in pair)
                    else sum(WEIGHTS[k] * POINTS[bands[k]] for k in pair))
        going_raw = (None if bands["ground"] == "未評価"
                     else WEIGHTS["ground"] * POINTS[bands["ground"]])
        if (h.get("coursePaceEvidenceRawThirdPoints") != pair_raw
                or h.get("coursePaceEvidenceScore34") != (
                    None if pair_raw is None else round(pair_raw / 3, 2))
                or h.get("coursePaceEvidenceNotFormalGrade") is not True
                or h.get("goingEvidenceRawThirdPoints") != going_raw
                or h.get("goingEvidenceScore12") != (
                    None if going_raw is None else round(going_raw / 3, 2))
                or h.get("goingEvidenceNotFormalGrade") is not True):
            raise CoverageError("Sparse observed bands differ from original subtotals")
        missing = [key for key in KEYS if bands[key] == "未評価"]
        if any(key != RECENT for key in missing):
            return None, "other_factors_missing"
        missing_recent += bool(missing)
        floor = sum(WEIGHTS[key] * POINTS[bands[key]]
                    for key in KEYS if key not in missing)
        ceiling = floor + sum(WEIGHTS[key] * 3 for key in missing)
        ranked.append({"number": h["number"], "floor": floor, "ceiling": ceiling})
    if not missing_recent:
        return None, "no_missing_recent"
    ranked.sort(key=lambda h: (-h["floor"], -h["ceiling"], h["number"]))
    options = []
    for a in (1, 2, 3):
        if not _cutoff_proven(ranked, a):
            continue
        for b in range(a + 1, min(n, 5) + 1):
            if not _cutoff_proven(ranked, b):
                continue
            for c in range(b, min(n, 9) + 1):
                if not _cutoff_proven(ranked, c):
                    continue
                count = a * (b - 1) * (c - 2)
                if 12 <= count <= MAX_TICKETS:
                    options.append((a, b, c, count))
    if not options:
        return None, "unstable_boundary"
    options.sort(key=lambda x: (
        30 <= x[3] <= 40, x[0] == 2,
        -abs(x[3] - 36), x[3]), reverse=True)
    a, b, c, count = options[0]
    first = [h["number"] for h in ranked[:a]]
    second = [h["number"] for h in ranked[:b]]
    third = [h["number"] for h in ranked[:c]]
    tickets = [[i, j, k] for i in first for j in second for k in third
               if i != j and j != k and i != k]
    if len(tickets) != count or len({tuple(x) for x in tickets}) != count:
        raise CoverageError("Unstable sparse reference arithmetic")
    return {
        "track": race["track"], "race": race["race"],
        "status": "bounded_missing_recent_reference",
        "first": first, "second": second, "third": third,
        "points": count, "missingRecentCount": missing_recent,
        "eachCutoffProvenForEveryRecentGrade": True,
        "receiptIssued": False, "predictionReady": False,
        "officialJraVerified": False, "bettingReady": False,
        "actualPurchase": False,
    }, None


def preview_sparse_five_holds(programme, study, drafts, day, *, now):
    """Read-only, private reference from an ALREADY validated /history read.

    No more provider calls; only original incomplete five-factor holds may
    produce a reference. No reference is generated for an already started
    race, or where the official headcount/provisional clock is uncertain.
    """
    if (not _valid_date(day) or not isinstance(now, datetime)
            or now.tzinfo is None or now.utcoffset() is None):
        raise CoverageError("Invalid sparse research day or server clock")
    source = _check_report(study)
    normalized = _normal_programme(programme, day)
    if (not isinstance(drafts, dict)
            or drafts.get("version") != "owner-research6-fivecore-drafts-1"
            or drafts.get("date") != day
            or drafts.get("researchFactorWeight") != 79
            or drafts.get("overallPredictionReady") is not False
            or drafts.get("officialJraVerified") is not False
            or drafts.get("researchOnly") is not True
            or not isinstance(drafts.get("races"), list)
            or len(drafts["races"]) != len(normalized)
            or not 0 <= len(normalized) <= MAX_RACES
            or set(source) != {(r["track"], r["race"]) for r in normalized}):
        raise CoverageError("Sparse research source contract mismatch")
    drafts_by = {}
    for row in drafts["races"]:
        if not isinstance(row, dict):
            raise CoverageError("Invalid original research hold")
        coord = row.get("track"), row.get("race")
        if coord in drafts_by:
            raise CoverageError("Duplicate original research hold")
        drafts_by[coord] = row
    if set(drafts_by) != set(source):
        raise CoverageError("Source and draft race identities mismatch")
    reference, counts, candidates = [], {}, 0
    now = now.astimezone(JST)
    for program in normalized:
        coord = program["track"], program["race"]
        row, hold = source[coord], drafts_by[coord]
        if (hold.get("status") != "hold"
                or hold.get("reason") != "incomplete_five_factors"):
            continue
        if (hold.get("runnerCount") != row["runnerCount"]
                or hold.get("completeObserved") != row["completeObserved"]):
            raise CoverageError("Held race roster mismatched")
        time = program.get("post_time")
        if not isinstance(time, str):
            continue
        off = datetime.strptime(day + time, "%Y%m%d%H:%M").replace(tzinfo=JST)
        if now >= off or program.get("headcount") != row["runnerCount"]:
            continue
        candidates += 1
        item, reason = _candidate(row)
        if item is not None:
            reference.append(item)
        else:
            counts[reason] = counts.get(reason, 0) + 1
    return {
        "version": VERSION, "policyVersion": "research-6", "date": day,
        "raceCount": len(normalized),
        "reviewedPrestartMissingFactorRaces": candidates,
        "safeResearchPreviewCount": len(reference),
        "heldReasons": counts, "races": reference,
        "researchOnly": True, "privateOwnerOnly": True,
        "formalTenFactorReady": False, "officialJraVerified": False,
        "predictionReady": False, "bettingReady": False,
        "actualPurchase": False, "ticketsIssued": 0,
        "changesExistingReceipts": False, "changesExistingTickets": False,
        "changesExistingRoi": False, "newProviderRequests": 0,
        "note": ("近走の未評価3点を最悪〜最良の全候補として扱い、"
                 "どの割当でも区切りが変わらない場合だけ参考3連単例を表示。"
                 "署名なし、発走前のみ、正式10項目・JRA公式結果・実購入ではない。"),
    }
