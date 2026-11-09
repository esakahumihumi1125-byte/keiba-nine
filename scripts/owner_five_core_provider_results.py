"""Read-only JRDB /tse reference comparison with prestart-sealed 85-weight study.

An observed podium from the licensed provider is not independent JRA truth,
a calibrated model hit, a settled 3連単, a wager, or a payout. The owner has
explicitly requested this study after the race; no background provider calls
or storage mutations are performed here. Only verified HMAC snapshots enter.
"""
import re
from datetime import datetime, timezone

from jrdb_program_preview import TRACKS
from owner_five_core_receipts import (
    _validate, KEYS, BANDS, FiveCoreReceiptError
)
from owner_rebound_receipts import _day, _timestamp

VERSION = "owner-five-core-provider-observation-1"
MAX_ROWS = 2160
PODIUM = "podium_observed"
PENDING = "pending"


def compare_five_core_provider_results(snapshots, rows, day, *,
                                       now=None, source_read_count=1):
    """Compare immutable 85-weight bands with provider provisional 1st-3rd."""
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    if (type(source_read_count) is not int or source_read_count not in (0, 1)
            or not isinstance(snapshots, list) or not 1 <= len(snapshots) <= 36
            or not isinstance(rows, list) or len(rows) > MAX_ROWS
            or (source_read_count == 0 and rows)):
        raise FiveCoreReceiptError("Invalid 85-point provider comparison")

    indexed, order = {}, []
    for snap in snapshots:
        coord = _validate(snap)
        if coord[0] != day or coord in indexed:
            raise FiveCoreReceiptError("Unverified or duplicate 85-point race")
        indexed[coord] = snap
        order.append(coord)

    grouped = {}
    for row in rows:
        if not isinstance(row, dict):
            raise FiveCoreReceiptError("Malformed provider result")
        key, horse, finish = (row.get("racekey"), row.get("horse_number"),
                              row.get("order_of_finish"))
        if (not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{8}", key)
                or key[:2] not in TRACKS or key[2:4] != day[2:4]
                or not key[6:].isdigit() or not 1 <= int(key[6:]) <= 12
                or row.get("racedate") != day
                or not isinstance(horse, str)
                or not re.fullmatch(r"(?:0[1-9]|1[0-8])", horse)
                or finish is not None and not isinstance(finish, str)):
            raise FiveCoreReceiptError("Provider date, race or runner mismatch")
        coord = TRACKS[key[:2]], int(key[6:])
        item = grouped.setdefault(coord, {
            "keys": set(), "horses": set(), "podium": {},
            "invalid": False, "rowCount": 0,
        })
        item["keys"].add(key)
        number = int(horse)
        item["rowCount"] += 1
        if number in item["horses"] or item["rowCount"] > 18:
            item["invalid"] = True
        item["horses"].add(number)
        if finish not in (None, ""):
            if (not re.fullmatch(r"0?[1-9]|1[0-8]", finish)
                    or row.get("trouble_classification") not in (None, "", "0")):
                item["invalid"] = True
            else:
                place = int(finish)
                if place in (1, 2, 3):
                    if place in item["podium"]:
                        item["invalid"] = True
                    item["podium"][place] = number

    buckets = {factor: {grade: 0 for grade in ("S", "A", "B", "C")}
               for factor in KEYS}
    races, observed, studied, group_first = [], 0, 0, 0
    for coord in order:
        snap = indexed[coord]
        group = grouped.get(coord[1:])
        good = (now >= _timestamp(snap["scheduledOffAt"])
                and snap["raceRunnerCount"] >= 3 and group is not None
                and not group["invalid"] and len(group["keys"]) == 1
                and 3 <= group["rowCount"] <= snap["raceRunnerCount"]
                and set(group["podium"]) == {1, 2, 3}
                and len(set(group["podium"].values())) == 3)
        result = {
            "track": coord[1], "race": coord[2],
            "providerStatus": PODIUM if good else PENDING,
            "observedPodiumNumbers": None, "scoredRunnerCount": len(snap["horses"]),
            "studiedWinnerObserved": None, "winnerStudyScore85": None,
            "winnerStudyBands": None, "winnerStudyGroup": None,
            "winnerInTopStudyGroup": None,
            "studyGroupNotFormalRank": True,
            "officialVerified": False, "predictionHitVerified": None,
        }
        if not good:
            races.append(result)
            continue
        observed += 1
        podium = [group["podium"][place] for place in (1, 2, 3)]
        result["observedPodiumNumbers"] = podium
        by_number = {horse["number"]: horse for horse in snap["horses"]}
        winner = by_number.get(podium[0])
        result["studiedWinnerObserved"] = winner is not None
        if winner is not None:
            studied += 1
            distinct_scores = sorted(
                {horse["rawThirdPoints"] for horse in snap["horses"]},
                reverse=True
            )
            # Tied horses share the same group, including top group.
            tier = distinct_scores.index(winner["rawThirdPoints"]) + 1
            result["winnerStudyGroup"] = tier
            result["winnerInTopStudyGroup"] = tier == 1
            group_first += tier == 1
            result["winnerStudyScore85"] = round(winner["rawThirdPoints"] / 3, 2)
            result["winnerStudyBands"] = dict(winner["bands"])
            for factor in KEYS:
                buckets[factor][winner["bands"][factor]] += 1
        races.append(result)
    return {
        "version": VERSION, "date": day, "raceCount": len(races),
        "races": races, "sourceKind": "jrdb-tse-unverified-podium-observation",
        "providerSourceReadCount": source_read_count,
        "observedRaceCount": observed,
        "observedStudiedWinnerCount": studied,
        "observedTopGroupWinnerCount": group_first,
        "winnerBandCounts": buckets,
        "verifiedRaceCount": 0, "confirmedHitCount": None,
        "officialJraVerified": False, "jraIndependentConfirmation": False,
        "officialFeedConnected": False, "outcomeCalibrationReady": False,
        "modelAccuracyPercent": None, "bettingReady": False,
        "actualPurchase": False, "payoutVerified": False, "roiPercent": None,
        "historicalBandsNotCalibrated": True,
        "sourceIncompleteCouldChange": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": ("発走前に固定した調教・コース距離・展開・馬場・近走の"
                 "研究85点とJRDB暫定1〜3着の参考比較。"
                 "S/A/B/Cの正式検証、JRA公式照合、勝率・的中・払戻・"
                 "回収率の集計には算入しない。"),
    }
