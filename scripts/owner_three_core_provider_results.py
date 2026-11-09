"""Read-only JRDB /tse podium observations against sealed prestart 70-point study.

A provider's preliminary placing is NOT an independent JRA official result.
Only server-verified, previously signed snapshots may reach this module.
No model fitting, win prediction, ranking, accuracy/ROI or saved record writes.
"""
from datetime import datetime, timezone
import re

from owner_three_core_receipts import (
    _validate_snapshot, CoreReceiptError, KEYS, GRADES
)
from owner_rebound_receipts import _day, _timestamp
from jrdb_program_preview import TRACKS

VERSION = "owner-three-core-provider-observation-1"
MAX_ROWS = 2160
COUNT = {k: 0 for k in ("S", "A", "B", "C")}


def compare_three_core_provider_results(snapshots, rows, day, *,
                                        now=None, source_read_count=1):
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    if (type(source_read_count) is not int or source_read_count not in (0, 1)
            or not isinstance(snapshots, list) or not snapshots
            or len(snapshots) > 36 or not isinstance(rows, list)
            or len(rows) > MAX_ROWS or (source_read_count == 0 and rows)):
        raise CoreReceiptError("Invalid preliminary result collection")
    saved, first_order = {}, []
    for snap in snapshots:
        key = _validate_snapshot(snap)
        if key[0] != day or key in saved:
            raise CoreReceiptError("Invalid sealed study identity")
        saved[key] = snap
        first_order.append(key)

    # Validate all provider rows, including unrelated races. Contradictory
    # rows inside a race *never* produce a podium observation.
    by_slot = {}
    for row in rows:
        if not isinstance(row, dict):
            raise CoreReceiptError("Unrecognized provider result record")
        racekey = row.get("racekey")
        horse = row.get("horse_number")
        finish = row.get("order_of_finish")
        if (not isinstance(racekey, str)
                or not re.fullmatch(r"[0-9a-f]{8}", racekey)
                or row.get("racedate") != day
                or racekey[2:4] != day[2:4]
                or racekey[:2] not in TRACKS
                or not racekey[6:].isdigit()
                or not 1 <= int(racekey[6:]) <= 12
                or not isinstance(horse, str)
                or not re.fullmatch(r"(?:0[1-9]|1[0-8])", horse)
                or finish is not None and not isinstance(finish, str)):
            raise CoreReceiptError("Provider race or horse identity mismatch")
        slot = (TRACKS[racekey[:2]], int(racekey[6:]))
        if slot not in by_slot:
            by_slot[slot] = {
                "keys": set(), "horses": set(), "places": {},
                "invalid": False, "rowCount": 0,
            }
        group = by_slot[slot]
        group["keys"].add(racekey)
        n = int(horse)
        group["rowCount"] += 1
        if n in group["horses"] or group["rowCount"] > 18:
            group["invalid"] = True
        group["horses"].add(n)
        # 0, void, unsupported special finishing marks or trouble flags
        # must prevent using the entire race, not be treated as a miss.
        if finish not in (None, ""):
            if (not re.fullmatch(r"0?[1-9]|1[0-8]", finish)
                    or row.get("trouble_classification") not in (None, "", "0")):
                group["invalid"] = True
            else:
                place = int(finish)
                if place in (1, 2, 3):
                    if place in group["places"]:
                        group["invalid"] = True
                    group["places"][place] = n

    output, scored_winners = [], 0
    winner_bands = {k: dict(COUNT) for k in KEYS}
    for key in first_order:
        snap = saved[key]
        slot = key[1:]
        group = by_slot.get(slot)
        started = now >= _timestamp(snap["scheduledOffAt"])
        good = (started and snap["raceRunnerCount"] >= 3
                and group is not None
                and not group["invalid"] and len(group["keys"]) == 1
                and 3 <= group["rowCount"] <= snap["raceRunnerCount"]
                and set(group["places"]) == {1, 2, 3}
                and len(set(group["places"].values())) == 3)
        podium = [group["places"][i] for i in (1, 2, 3)] if good else None
        studied = {h["number"]: h for h in snap["horses"]}
        winner = studied.get(podium[0]) if good else None
        if winner:
            scored_winners += 1
            for k in KEYS:
                winner_bands[k][winner["bands"][k]] += 1
        output.append({
            "track": key[1], "race": key[2],
            "providerStatus": "podium_observed" if good else "pending",
            "observedPodiumNumbers": podium,
            "scoredRunnerCount": len(studied),
            "winnerStudyScore70": (
                round(winner["rawThirdPoints"] / 3, 2) if winner else None),
            "winnerStudyBands": (
                {k: winner["bands"][k] for k in KEYS} if winner else None),
            "studiedWinnerObserved": (bool(winner) if good else None),
            "officialVerified": False, "predictionHitVerified": None,
        })
    observed = sum(x["providerStatus"] == "podium_observed" for x in output)
    return {
        "version": VERSION, "date": day,
        "sourceKind": "jrdb-tse-unverified-podium-observation",
        "providerSourceReadCount": source_read_count,
        "raceCount": len(output), "races": output,
        "observedRaceCount": observed,
        "observedStudiedWinnerCount": scored_winners,
        "winnerBandCounts": winner_bands,
        "verifiedRaceCount": 0, "confirmedHitCount": None,
        "officialJraVerified": False,
        "jraIndependentConfirmation": False,
        "officialFeedConnected": False,
        "outcomeCalibrationReady": False,
        "modelAccuracyPercent": None,
        "bettingReady": False,
        "actualPurchase": False,
        "payoutVerified": False,
        "roiPercent": None,
        "historicalBandsNotCalibrated": True,
        "sourceIncompleteCouldChange": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": ("発走前に固定した未検証70点研究値とJRDB成績の"
                 "暫定1〜3着観測を比較。JRA公式の独立照合が未完了のため"
                 "予測的中率、モデル精度、3連単回収率に算入しません。"),
    }
