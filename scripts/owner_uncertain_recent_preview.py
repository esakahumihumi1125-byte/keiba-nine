"""Owner-private research formations resilient to *missing recent form*.

The formal 10-factor policy weights workout/recent 30:3. A missing recent
S/A/B/C grade spans 0..9 ordinal research units, not an assumed zero or C.
If candidate first/second/third *membership* is invariant for EVERY possible
assignment of those missing ordinal values, we may show an UNSIGNED,
ungraded, read-only formation preview. It is never an auto-draft, purchase,
official JRA verification, or ROI item. No licensed source values, horse
identities, odds, network access or persistence.

Unlike the normal two-factor drafts this preview cannot create any signed
ticket; it exists exclusively to explain why a particular partial ordering
is or is not safely distinguishable with sparse β data.
"""
from datetime import datetime, timedelta, timezone
import re

from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION
from evaluation_policy import OWNER_FORMAL_FACTORS as FACTORS

VERSION = "owner-uncertain-recent-preview-1"
JST = timezone(timedelta(hours=9))
OFF = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z", re.ASCII)
DAY = re.compile(r"20\d{6}\Z", re.ASCII)
GRADES = {"S": 3, "A": 2, "B": 1, "C": 0}
MAX_RACES = 120

assert FACTORS["training"] == 30 and FACTORS["recent"] == 3


def _cutoff_proven(ranked, size):
    """Return true only if the entire upper group ALWAYS outranks lower."""
    if size == len(ranked):
        return True
    if size < 1 or size > len(ranked):
        return False
    return (min(x["floor"] for x in ranked[:size])
            > max(x["ceiling"] for x in ranked[size:]))


def _formation(race):
    horses = race.get("runners")
    if (not isinstance(horses, list)
            or not 4 <= len(horses) <= 18
            or race.get("horseCount") != len(horses)):
        return None
    seen, ranked = set(), []
    absent_recent = 0
    for h in horses:
        if (not isinstance(h, dict) or type(h.get("number")) is not int
                or not 1 <= h["number"] <= 18 or h["number"] in seen
                or h.get("training") not in GRADES
                or h.get("recent") not in (*GRADES, "未評価")):
            # Missing TRAINING is too influential for bounded fallback.
            return None
        seen.add(h["number"])
        t, r = GRADES[h["training"]], h["recent"]
        absent_recent += int(r == "未評価")
        # The unknown 3-point factor contributes a possible 0/3/6/9,
        # NEVER a fabricated grade or earned ability score.
        floor = FACTORS["training"] * t
        ceiling = floor + 3 * FACTORS["recent"]
        if r != "未評価":
            floor += FACTORS["recent"] * GRADES[r]
            ceiling = floor
        ranked.append({"number": h["number"], "floor": floor,
                       "ceiling": ceiling})
    if not absent_recent:
        return None
    ranked.sort(key=lambda h: (-h["floor"], -h["ceiling"], h["number"]))
    count = len(ranked)
    options = []
    for first in (2, 3):
        if not _cutoff_proven(ranked, first):
            continue
        for second in range(first + 1, min(count, 5) + 1):
            if not _cutoff_proven(ranked, second):
                continue
            for third in range(second, min(count, 9) + 1):
                if not _cutoff_proven(ranked, third):
                    continue
                n = first * (second - 1) * (third - 2)
                if 12 <= n <= 40:
                    options.append((first, second, third, n))
    if not options:
        return None
    # Prefer a 30-40 point researcher preview, then the usual two first
    # horses; never split a tied or overlapping interval to reach 40.
    options.sort(key=lambda x: (x[3] >= 30, x[0] == 2, x[3]), reverse=True)
    a, b, c, points = options[0]
    return {
        "track": race["track"], "race": race["race"],
        "status": "bounded_recent_uncertainty_only",
        "first": [h["number"] for h in ranked[:a]],
        "second": [h["number"] for h in ranked[:b]],
        "third": [h["number"] for h in ranked[:c]],
        "points": points, "missingRecentCount": absent_recent,
        "assessedTrainingCount": count,
        "eachCutoffProvenForAllRecentGrades": True,
        "officialJraVerified": False, "formalScoreReady": False,
        "predictionReady": False, "bettingReady": False,
        "receiptIssued": False, "actualPurchase": False,
    }


def preview_missing_recent_holds(report, day, *, now):
    """Called AFTER the final server prestart gate on an internal draft."""
    if (not isinstance(report, dict) or report.get("version") != DRAFT_VERSION
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or any(report.get(k) is not False for k in (
                "officialJraVerified", "overallPredictionReady",
                "bettingReady", "autoPurchase"))
            or type(day) is not str or not DAY.fullmatch(day)
            or report.get("date") != day
            or not isinstance(now, datetime) or now.tzinfo is None
            or now.utcoffset() is None
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > MAX_RACES
            or report.get("raceCount") != len(report["races"])):
        raise CoverageError("Invalid uncertain-recent preview contract")
    now = now.astimezone(JST)
    rows, seen, reviewed = [], set(), 0
    for race in report["races"]:
        if (not isinstance(race, dict)
                or type(race.get("track")) is not str
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or (race["track"], race["race"]) in seen
                or race.get("status") not in ("hold", "provisional_draft")):
            raise CoverageError("Invalid source race in preview")
        coord = race["track"], race["race"]
        seen.add(coord)
        if (race["status"] != "hold"
                or race.get("reason") != "missing_factors"):
            continue
        off_text = race.get("postTime")
        if not isinstance(off_text, str) or not OFF.fullmatch(off_text):
            continue
        off = datetime.strptime(day + off_text, "%Y%m%d%H:%M").replace(tzinfo=JST)
        if now >= off:
            continue
        reviewed += 1
        candidate = _formation(race)
        if candidate:
            rows.append(candidate)
    return {
        "version": VERSION, "date": day,
        "raceCount": len(report["races"]),
        "reviewedPrestartMissingFactorRaces": reviewed,
        "safeResearchPreviewCount": len(rows), "races": rows,
        "researchOnly": True, "privateOwnerOnly": True,
        "independentJraVerified": False,
        "officialJraVerified": False, "formalTenFactorReady": False,
        "predictionReady": False, "bettingReady": False,
        "changesExistingDrafts": False, "changesExistingReceipts": False,
        "newProviderRequests": 0, "ticketsIssued": 0,
        "note": ("不足した近走3点をC・0点に決めつけず、全ての可能性でも"
                 "1/2/3着候補の区切りが変わらない場合だけ表示する署名なし研究例。"
                 "正式100点、JRA公式照合、購入可能な3連単ではない。"),
    }
