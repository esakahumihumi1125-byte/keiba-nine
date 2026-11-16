"""Unsigned 7-factor research alternatives for EXISTING prestart 2-factor drafts.

Reuses the exact comparable source rules that previously applied only to
missing-factor/tied HELD races. A normal signed 2-factor research draft is
never amended, rescored or replaced: the response contains an optional
ungraded 1/2/3-place comparison, not new tickets, validated 100-point form,
official JRA authorization, a bet, a receipt or an ROI observation.

Only the already fetched JRDB /tra /tky /tcy /tze (and optional /tka)
and their same-roster research slots are examined. No new licensed reads.
"""
from datetime import datetime, timedelta, timezone
import re

from jrdb_coverage import CoverageError
from evaluation_policy import OWNER_FORMAL_FACTORS as WEIGHTS
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION
from owner_automatic_factor_scores import VERSION as AUTO_VERSION
from owner_comparable_factor_preview import (
    _candidate, DIAGNOSTIC_KEYS, AUTO_FACTORS,
    MIN_COMPARABLE_WEIGHT
)

VERSION = "owner-provisional-seven-factor-reference-1"
JST = timezone(timedelta(hours=9))
DAY = re.compile(r"20\d{6}\Z", re.ASCII)
MAX_RACES = 120


def preview_provisional_seven_factors(drafts, automatic, day, *, now):
    """Only already-provisional prestart races; no source or score promotion."""
    if (not isinstance(now, datetime) or now.tzinfo is None
            or now.utcoffset() is None or not isinstance(day, str)
            or not DAY.fullmatch(day) or not isinstance(drafts, dict)
            or not isinstance(automatic, dict)
            or drafts.get("version") != DRAFT_VERSION
            or automatic.get("version") != AUTO_VERSION
            or drafts.get("date") != day or automatic.get("date") != day
            or drafts.get("researchOnly") is not True
            or drafts.get("privateOwnerOnly") is not True
            or any(drafts.get(k) is not False for k in (
                "officialJraVerified", "overallPredictionReady",
                "bettingReady", "autoPurchase"))
            or automatic.get("officialJraVerified") is not False
            or automatic.get("overallPredictionReady") is not False
            or automatic.get("modelCalibrated") is not False
            or automatic.get("newProviderRequests") != 0
            or automatic.get("maximumPoints") !=
                sum(WEIGHTS[k] for k in AUTO_FACTORS)
            or automatic.get("factorKeys") != [
                "pace", "jockey_stable", "rotation", "course_distance", "ground"]
            or not isinstance(drafts.get("races"), list)
            or not isinstance(automatic.get("races"), list)
            or not isinstance(drafts.get("raceCount"), int)
            or drafts["raceCount"] != len(drafts["races"])
            or len(drafts["races"]) != len(automatic["races"])
            or len(drafts["races"]) > MAX_RACES):
        raise CoverageError("Unverified provisional comparable source")
    by_race = {}
    for row in drafts["races"]:
        if (not isinstance(row, dict)
                or type(row.get("track")) is not str
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoverageError("Unrecognized provisional research coordinate")
        coordinate = row["track"], row["race"]
        if coordinate in by_race:
            raise CoverageError("Duplicated provisional research race")
        by_race[coordinate] = row
    # Never generate another formation if an automatic score source appears
    # for a different, duplicated or orphan race; the whole optional
    # comparison is withheld without affecting existing signed receipts.
    seen = set()
    summaries = []
    diagnostics = {key: 0 for key in DIAGNOSTIC_KEYS}
    reviewed = 0
    jst = now.astimezone(JST)
    for row in automatic["races"]:
        if not isinstance(row, dict):
            raise CoverageError("Malformed provisional factor race")
        coordinate = row.get("track"), row.get("race")
        if coordinate in seen or coordinate not in by_race:
            raise CoverageError("Unmatched provisional factor race")
        seen.add(coordinate)
        original = by_race[coordinate]
        if original.get("status") != "provisional_draft":
            continue
        reviewed += 1
        candidate, reason = _candidate(
            original, row, day, jst, allow_provisional=True)
        if reason not in diagnostics:
            raise CoverageError("Unknown provisional comparison status")
        diagnostics[reason] += 1
        if candidate is not None:
            summaries.append(candidate)
    if seen != set(by_race) or sum(diagnostics.values()) != reviewed:
        raise CoverageError("Incomplete provisional factor join")
    return {
        "version": VERSION, "date": day, "raceCount": len(by_race),
        "reviewedPrestartDraftRaces": reviewed,
        "unsignedReferenceCount": len(summaries),
        "minimumComparableWeight": MIN_COMPARABLE_WEIGHT,
        "diagnostics": diagnostics, "races": summaries,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "formalTenFactorReady": False,
        "predictionReady": False, "bettingReady": False,
        "ticketsIssued": 0, "newProviderRequests": 0,
        "changesExistingDrafts": False, "changesExistingReceipts": False,
        "changesExistingRoi": False,
        "note": (
            "すでに研究用2項目の買い目が出たRでも、全馬に共通の追加"
            "項目だけで1/2/3着候補を再比較する署名なしの別案。"
            "正式10項目・JRA最終照合・購入・固定買い目は変更しない。"
        ),
    }
