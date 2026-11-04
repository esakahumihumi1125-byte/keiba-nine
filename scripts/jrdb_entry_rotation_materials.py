"""Private observation-only tky/tze inputs for pedigree, draw, weight, rotation.

Uses documented /tky bracket_number, weight_to_carry, sire_name,
mare_sire_name and /tze race_back_N_racedate. No scores, favorite-based
ranking, aptitude claims, paid API calls, storage or public feed.
The horse-number matrix is private; only bounded per-race totals leave it.
"""
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re

from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import (
    HORSE_ID, NUMBER, _valid_date, audit_evidence_coverage,
)
from jrdb_private_factor_bridge import summarize_factor_materials

VERSION = "entry-pedigree-draw-rotation-materials-1"
NO_DATA = {"grade": "未評価", "basis": "not_mapped"}
SLOTS = ("pedigree", "draw_weight", "rotation")
BUCKETS = ("under14Days", "days14to55", "days56plus", "unknown")
WEIGHT = re.compile(r"(?:[3-7][0-9]|80)(?:\.[0-9])?\Z", re.ASCII)


def _text(raw, *, field):
    if raw is None or raw == "":
        return False
    if (not isinstance(raw, str) or len(raw) > 128 or not raw.strip()
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in raw)):
        raise CoverageError("Invalid optional " + field)
    return True


def _bracket(value):
    if value is None or value == "":
        return False
    if type(value) is not str or value not in tuple(str(i) for i in range(1, 9)):
        raise CoverageError("Invalid provider bracket number")
    return True


def _weight(value):
    if value is None or value == "":
        return False
    if type(value) is bool or type(value) not in (str, int, float):
        raise CoverageError("Invalid provider assigned weight")
    value = str(value)
    if not WEIGHT.fullmatch(value):
        raise CoverageError("Invalid provider assigned weight")
    try:
        dec = Decimal(value)
    except InvalidOperation:
        raise CoverageError("Invalid provider assigned weight") from None
    if not Decimal("30") <= dec <= Decimal("80"):
        raise CoverageError("Invalid provider assigned weight")
    return True


def _rotation(last, date):
    """No date => unknown, not a debut/long-layoff classification."""
    if last is None or last == "":
        return None
    if not _valid_date(last) or last >= date:
        raise CoverageError("Invalid most recent race date")
    interval = (datetime.strptime(date, "%Y%m%d").date()
                - datetime.strptime(last, "%Y%m%d").date()).days
    if interval <= 0:
        raise CoverageError("Previous run must predate programme")
    if interval < 14:
        return "under14Days"
    if interval < 56:
        return "days14to55"
    return "days56plus"


def _previous_index(entries, previous):
    roster, ids, matched = {}, {}, {}
    for row in entries:
        key, number, horse_id = row["racekey"], row["horse_number"], row.get("horse_id")
        roster[key, number] = True
        if horse_id:
            if not isinstance(horse_id, str) or not HORSE_ID.fullmatch(horse_id):
                raise CoverageError("Invalid horse identity")
            if (key, horse_id) in ids:
                raise CoverageError("Duplicate horse ID")
            ids[key, horse_id] = number
    for row in previous:
        key, num, horse_id = row["racekey"], row.get("horse_number"), row.get("horse_id")
        direct = num if isinstance(num, str) and NUMBER.fullmatch(num) and (key, num) in roster else None
        via_id = ids.get((key, horse_id)) if isinstance(horse_id, str) and HORSE_ID.fullmatch(horse_id) else None
        if direct and via_id and direct != via_id:
            raise CoverageError("Previous runner identity conflict")
        number = via_id or direct
        if number is None:
            continue
        if (key, number) in matched:
            raise CoverageError("Duplicate previous runner")
        matched[key, number] = row
    return matched


def enrich_entry_materials_matrix(matrix, programme, entries, previous, date):
    """Attach only observed record-presence and last-race date interval."""
    if not _valid_date(date):
        raise CoverageError("Invalid race date")
    summarize_factor_materials(matrix)  # fail closed before enriching
    audit_evidence_coverage(programme, entries, [], previous, date)
    index = _previous_index(entries, previous)
    # Do not depend on source row ordering or emit a private entry in summary.
    roster = {}
    for row in entries:
        id_ = (row["racekey"], row["horse_number"])
        if id_ in roster:
            raise CoverageError("Duplicate entry")
        roster[id_] = row
    if len(roster) != sum(len(x["byNumber"]) for x in matrix):
        raise CoverageError("Entry and private factor roster counts differ")
    enriched = deepcopy(matrix)
    for race in enriched:
        key = race["racekey"]
        for number, slots in race["byNumber"].items():
            entry = roster.get((key, number))
            if entry is None or any(slots[factor] != NO_DATA for factor in SLOTS):
                raise CoverageError("Entry and factor roster identities differ")
            sire = _text(entry.get("sire_name"), field="sire name")
            maternal_sire = _text(entry.get("mare_sire_name"), field="maternal grandsire")
            bracket = _bracket(entry.get("bracket_number"))
            assigned_weight = _weight(entry.get("weight_to_carry"))
            past = index.get((key, number))
            latest = past.get("race_back_1_racedate") if past else None
            interval_bucket = _rotation(latest, date)
            slots["pedigree"] = {
                "grade": "未評価", "basis": "documented_parentage_presence",
                "sireRecorded": sire, "maternalSireRecorded": maternal_sire,
            }
            slots["draw_weight"] = {
                "grade": "未評価", "basis": "documented_draw_weight_presence",
                "bracketRecorded": bracket, "assignedWeightRecorded": assigned_weight,
            }
            slots["rotation"] = {
                "grade": "未評価", "basis": "latest_past_run_date_interval",
                "intervalBucket": interval_bucket or "unknown",
            }
    return enriched


def summarize_entry_materials_matrix(matrix):
    """One race per row, no horse numbers, names, pedigree or weights."""
    if not isinstance(matrix, list) or len(matrix) > 120:
        raise CoverageError("Invalid private entry-material matrix")
    stripped = deepcopy(matrix)
    for race in stripped:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise CoverageError("Invalid entry material race")
        for slots in race["byNumber"].values():
            if not isinstance(slots, dict) or any(k not in slots for k in SLOTS):
                raise CoverageError("Missing entry factor slots")
            for name in SLOTS:
                slots[name] = dict(NO_DATA)
    baseline = summarize_factor_materials(stripped)
    base_map = {(r["track"], r["race"]): r for r in baseline["races"]}
    output = []
    for race in matrix:
        coord = race["track"], race["race"]
        base = base_map[coord]
        n = base["runnerCount"]
        totals = dict.fromkeys((
            "sireRecorded", "maternalSireRecorded", "bothPedigreeRecorded",
            "bracketRecorded", "weightRecorded", "drawAndWeightRecorded",
        ), 0)
        interval_counts = dict.fromkeys(BUCKETS, 0)
        for number, slots in race["byNumber"].items():
            if not isinstance(number, str) or not NUMBER.fullmatch(number):
                raise CoverageError("Invalid internal runner key")
            a, b, c = (slots.get(factor) for factor in SLOTS)
            if (not isinstance(a, dict) or not isinstance(b, dict)
                    or not isinstance(c, dict)
                    or set(a) != {"grade", "basis", "sireRecorded", "maternalSireRecorded"}
                    or set(b) != {"grade", "basis", "bracketRecorded", "assignedWeightRecorded"}
                    or set(c) != {"grade", "basis", "intervalBucket"}
                    or a["grade"] != "未評価" or b["grade"] != "未評価"
                    or c["grade"] != "未評価"
                    or a["basis"] != "documented_parentage_presence"
                    or b["basis"] != "documented_draw_weight_presence"
                    or c["basis"] != "latest_past_run_date_interval"
                    or any(type(v) is not bool for v in (
                        a["sireRecorded"], a["maternalSireRecorded"],
                        b["bracketRecorded"], b["assignedWeightRecorded"]))
                    or c["intervalBucket"] not in BUCKETS):
                raise CoverageError("Only documented ungraded entry observations are allowed")
            totals["sireRecorded"] += a["sireRecorded"]
            totals["maternalSireRecorded"] += a["maternalSireRecorded"]
            totals["bothPedigreeRecorded"] += a["sireRecorded"] and a["maternalSireRecorded"]
            totals["bracketRecorded"] += b["bracketRecorded"]
            totals["weightRecorded"] += b["assignedWeightRecorded"]
            totals["drawAndWeightRecorded"] += b["bracketRecorded"] and b["assignedWeightRecorded"]
            interval_counts[c["intervalBucket"]] += 1
        if sum(interval_counts.values()) != n or any(x > n for x in totals.values()):
            raise CoverageError("Entry observation totals mismatch")
        output.append({
            "track": coord[0], "race": coord[1], "runnerCount": n,
            "entryObservations": totals, "rotationIntervals": interval_counts,
            "observedFactorSlots": 6,
            "unmappedFactorCount": 4, "verifiedFactorCount": 0,
            "pedigreeAptitudeAssessed": False,
            "drawWeightEffectAssessed": False,
            "rotationEffectAssessed": False,
            "overallRankReady": False, "predictionReady": False,
            "bettingReady": False,
        })
    return {
        "version": VERSION, "raceCount": len(output), "races": output,
        "predictionReady": False, "bettingReady": False,
        "note": ("枠・斤量・父と母父の資料有無、前走日付からの間隔を"
                 "10項目の未評価スロットへ接続。血統適性・枠の有利不利・"
                 "斤量差の影響・休養明けの良否は未検証。"
                 "実馬ランク・買い目は生成しません。"),
    }
