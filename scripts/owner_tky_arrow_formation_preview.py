"""Unsigned arrow-first formation examples for owner-private held JRDB races.

This is a qualitative /tky expert-arrow observation, NOT a scored /tcy
workout, full-ten model, JRA validation or a purchasing recommendation.
The caller passes the already-fetched, same-request prestart study and held
2-factor report. Never issue receipts, persist, read paid endpoints or alter
the existing draft. Missing arrows never become a weak/last-place runner.
"""
from datetime import datetime
import re

from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import JST, VERSION as DRAFT_VERSION
from owner_tky_training_index_study import VERSION as STUDY_VERSION

VERSION = "owner-tky-arrow-formation-preview-1"
DAY = re.compile(r"20\d{6}\Z", re.ASCII)
POST = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z", re.ASCII)
LEVEL = {
    "デキ抜群": 1, "上昇": 2, "平行線": 3,
    "やや下降": 4, "デキ落ち": 5,
}
MAX_POINTS = 48


def _candidate(item, original):
    """Do not rank unless *every* original entrant has expert-arrow data.

    When every index is known, use its observed order ONLY within a
    common expert-arrow tier. Partial indexes are ignored entirely, so
    missing data never arbitrarily creates a bottom-ranked horse.
    """
    n = original.get("horseCount")
    horses = original.get("runners")
    if (type(n) is not int or not 4 <= n <= 18
            or not isinstance(horses, list) or len(horses) != n
            or item.get("rosterCount") != n
            or item.get("arrowObservedCount") != n
            or item.get("arrowUnobservedCount") != 0
            or type(item.get("observedCount")) is not int
            or not 0 <= item["observedCount"] <= n
            or item.get("unassessedCount") != n-item["observedCount"]
            or item.get("rankingScope") != "tky_arrow_first_index_descriptive_only"):
        return None
    roster = []
    for h in horses:
        number = h.get("number") if isinstance(h, dict) else None
        if (type(number) is not int or not 1 <= number <= 18
                or h.get("training") not in ("S", "A", "B", "C", "未評価")):
            return None
        roster.append(number)
    if len(set(roster)) != n or not any(
            h.get("training") == "未評価" for h in horses):
        return None
    if (not isinstance(item.get("arrows"), list)
            or len(item["arrows"]) != n
            or not isinstance(item.get("runners"), list)
            or len(item["runners"]) != item["observedCount"]):
        return None
    arrow_levels, previous = {}, (0, 0)
    for row in item["arrows"]:
        if (not isinstance(row, dict)
                or set(row) != {"number", "condition"}
                or type(row["number"]) is not int
                or row["number"] not in roster
                or row["number"] in arrow_levels
                or row["condition"] not in LEVEL):
            return None
        pair = (LEVEL[row["condition"]], row["number"])
        if pair <= previous:
            return None
        previous = pair
        arrow_levels[row["number"]] = pair[0]
    if set(arrow_levels) != set(roster):
        return None
    indexes = {}
    last_rank = 0
    for row in item["runners"]:
        if (not isinstance(row, dict)
                or set(row) != {"number", "observedRank"}
                or type(row["number"]) is not int
                or row["number"] not in roster
                or row["number"] in indexes
                or type(row["observedRank"]) is not int
                or not 1 <= row["observedRank"] <= item["observedCount"]
                or row["observedRank"] < last_rank):
            return None
        last_rank = row["observedRank"]
        indexes[row["number"]] = row["observedRank"]
    # A missing observed index can never become a numeric tiebreaker.
    complete_index = len(indexes) == n
    levels = {
        number: (arrow_levels[number], indexes[number])
        if complete_index else (arrow_levels[number],)
        for number in roster
    }
    ordered = sorted(roster, key=lambda x: (*levels[x], x))

    def boundary(size):
        return size == n or levels[ordered[size-1]] < levels[ordered[size]]

    for first in (2, 3, 1):
        if not boundary(first):
            continue
        valid = []
        for second in range(first+1, min(8, n)+1):
            if not boundary(second):
                continue
            for third in range(max(3, second), min(12, n)+1):
                if not boundary(third):
                    continue
                points = first*(second-1)*(third-2)
                if 1 <= points <= MAX_POINTS:
                    valid.append((points, first, second, third))
        if valid:
            selected = max(valid, key=lambda x: (
                30 <= x[0] <= 40, x[0], x[3], -x[2]
            ))
            points, a, b, c = selected
            return {
                "track": original["track"], "race": original["race"],
                "status": "unsigned_arrow_first_research",
                "first": ordered[:a], "second": ordered[:b],
                "third": ordered[:c], "points": points,
                "rosterCount": n, "arrowObservedCount": n,
                "indexObservedCount": len(indexes),
                "rankingScope": (
                    "arrow_then_index_rank" if complete_index else "arrow_only"
                ),
                "partialIndexIgnored": not complete_index,
                "tiedSourceTiersNotSplit": True,
                "researchOnly": True, "officialJraVerified": False,
                "formalScoreReady": False, "predictionReady": False,
                "bettingReady": False, "receiptIssued": False,
                "actualPurchase": False,
            }
    return None


def preview_tky_arrow_formations(report, study, day, *, now):
    """One bounded preview from the existing no-extra-read /tky study."""
    if (type(day) is not str or not DAY.fullmatch(day)
            or not isinstance(now, datetime) or now.tzinfo is None
            or now.utcoffset() is None
            or not isinstance(report, dict)
            or report.get("version") != DRAFT_VERSION
            or report.get("date") != day
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or any(report.get(x) is not False for x in
                   ("officialJraVerified", "overallPredictionReady",
                    "bettingReady", "autoPurchase"))
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > 120
            or report.get("raceCount") != len(report["races"])
            or not isinstance(study, dict)
            or study.get("version") != STUDY_VERSION
            or study.get("date") != day
            or study.get("raceCount") != len(report["races"])
            or study.get("sourceMetric") != "tky_training_index_and_training_arrow"
            or study.get("trainingArrowPriority") is not True
            or study.get("trainingSourceDistinctFromTcy") is not True
            or any(study.get(x) is not False for x in
                   ("officialJraVerified", "modelCalibrated", "training30Ready",
                    "predictionReady", "bettingReady", "changesExistingDrafts",
                    "changesExistingReceipts", "rawIndicesIncluded"))
            or study.get("researchOnly") is not True
            or study.get("privateOwnerOnly") is not True
            or study.get("newProviderRequests") != 0
            or study.get("ticketsIssued") != 0
            or not isinstance(study.get("races"), list)
            or len(study["races"]) > len(report["races"])
            or study.get("studiedRaceCount") != len(study["races"])):
        raise CoverageError("Invalid expert arrow preview source")
    originals = {}
    for race in report["races"]:
        if (not isinstance(race, dict)
                or (race.get("track"), race.get("race")) in originals
                or type(race.get("track")) is not str
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12):
            raise CoverageError("Invalid draft race identity")
        originals[race["track"], race["race"]] = race
    seen, previews = set(), []
    current = now.astimezone(JST)
    for item in study["races"]:
        if (not isinstance(item, dict)
                or (item.get("track"), item.get("race")) in seen):
            raise CoverageError("Repeated expert arrow race")
        coord = item.get("track"), item.get("race")
        seen.add(coord)
        race = originals.get(coord)
        if (race is None or race.get("status") != "hold"
                or race.get("reason") != "missing_factors"):
            raise CoverageError("Expert arrow race not a held source race")
        post = race.get("postTime")
        if type(post) is not str or not POST.fullmatch(post):
            continue
        off = datetime.strptime(day+post,"%Y%m%d%H:%M").replace(tzinfo=JST)
        if current >= off:
            continue
        candidate = _candidate(item, race)
        if candidate:
            previews.append(candidate)
    return {
        "version": VERSION, "date": day, "raceCount": len(report["races"]),
        "reviewedPrestartStudies": len(study["races"]),
        "safeReferenceCount": len(previews), "races": previews,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "formalTenFactorReady": False,
        "predictionReady": False, "bettingReady": False,
        "newProviderRequests": 0, "ticketsIssued": 0,
        "changesExistingDrafts": False,
        "changesExistingReceipts": False,
        "note": ("JRDB調教矢印を優先する観測だけの参考組み合わせ。"
                 "全馬の矢印が必要。指数の一部欠測を下位扱いせず、"
                 "正式調教30点や総合10項目・JRA公式・購入案ではありません。"),
    }
