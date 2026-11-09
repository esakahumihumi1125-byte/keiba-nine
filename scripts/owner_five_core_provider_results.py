"""Compare sealed five-factor (85-weight) observations with provisional JRDB podiums.

This is an opt-in, read-only *research* comparison, never official JRA truth,
model accuracy, profitability, prediction output or purchase history.
The caller verifies each server HMAC before passing snapshots here.
"""
import re
from datetime import datetime, timezone

from jrdb_program_preview import TRACKS
from owner_five_core_receipts import _validate, KEYS, FiveCoreReceiptError
from owner_rebound_receipts import _day, _timestamp

VERSION = "owner-five-core-provider-observation-1"
MAX_ROWS = 2160
BANDS = ("S", "A", "B", "C")


def compare_five_core_provider_results(snapshots, rows, day, *,
                                       now=None, source_read_count=1):
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    if (type(source_read_count) is not int or source_read_count not in (0, 1)
            or not isinstance(snapshots, list) or not 1 <= len(snapshots) <= 36
            or not isinstance(rows, list) or len(rows) > MAX_ROWS
            or (source_read_count == 0 and rows)):
        raise FiveCoreReceiptError("Invalid provisional study collection")

    frozen, order = {}, []
    for snapshot in snapshots:
        key = _validate(snapshot)
        if key[0] != day or key in frozen:
            raise FiveCoreReceiptError("Invalid sealed 85-weight identity")
        frozen[key] = snapshot
        order.append(key)

    # Validate every provider row, including an unrelated race, before
    # associating any podium with a frozen historical observation.
    by_race = {}
    for row in rows:
        if not isinstance(row, dict):
            raise FiveCoreReceiptError("Unrecognized provider result")
        racekey = row.get("racekey")
        horse = row.get("horse_number")
        finish = row.get("order_of_finish")
        if (not isinstance(racekey, str)
                or not re.fullmatch(r"[0-9a-f]{8}", racekey)
                or racekey[:2] not in TRACKS
                or racekey[2:4] != day[2:4]
                or not racekey[6:].isdigit()
                or not 1 <= int(racekey[6:]) <= 12
                or row.get("racedate") != day
                or not isinstance(horse, str)
                or not re.fullmatch(r"(?:0[1-9]|1[0-8])", horse)
                or finish is not None and not isinstance(finish, str)):
            raise FiveCoreReceiptError("Provider race identity mismatch")
        coord = (TRACKS[racekey[:2]], int(racekey[6:]))
        group = by_race.setdefault(coord, {
            "racekeys": set(), "numbers": set(), "places": {},
            "rowCount": 0, "invalid": False,
        })
        group["racekeys"].add(racekey)
        group["rowCount"] += 1
        n = int(horse)
        if n in group["numbers"] or group["rowCount"] > 18:
            group["invalid"] = True
        group["numbers"].add(n)
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

    out, winner_count, eligible_count = [], 0, 0
    band_counts = {k: {b: 0 for b in BANDS} for k in KEYS}
    exposure_counts = {k: {b: 0 for b in BANDS} for k in KEYS}
    for key in order:
        original = frozen[key]
        group = by_race.get(key[1:])
        good = (
            now >= _timestamp(original["scheduledOffAt"])
            and group is not None and not group["invalid"]
            and len(group["racekeys"]) == 1
            and 3 <= group["rowCount"] <= original["raceRunnerCount"]
            and set(group["places"]) == {1, 2, 3}
            and len(set(group["places"].values())) == 3
        )
        podium = [group["places"][place] for place in (1, 2, 3)] if good else None
        frozen_horses = {h["number"]: h for h in original["horses"]}
        # Denominator from signed *prestart* runners, not only the winner.
        # A provisional podium is needed to include a race; unresolved
        # provider races do not count as failures or as exposures.
        if good:
            eligible_count += len(frozen_horses)
            for horse in frozen_horses.values():
                for factor in KEYS:
                    exposure_counts[factor][horse["bands"][factor]] += 1
        winner = frozen_horses.get(podium[0]) if good else None
        if winner is not None:
            winner_count += 1
            for factor in KEYS:
                band_counts[factor][winner["bands"][factor]] += 1
        out.append({
            "track": key[1], "race": key[2],
            "providerStatus": "podium_observed" if good else "pending",
            "observedPodiumNumbers": podium,
            "scoredRunnerCount": len(frozen_horses),
            "studiedWinnerObserved": bool(winner) if good else None,
            "winnerStudyScore85": (
                round(winner["rawThirdPoints"] / 3, 2) if winner else None
            ),
            "winnerStudyBands": (
                dict(winner["bands"]) if winner else None
            ),
            "officialVerified": False,
            "predictionHitVerified": None,
        })
    observed = sum(r["providerStatus"] == "podium_observed" for r in out)
    return {
        "version": VERSION, "date": day,
        "sourceKind": "jrdb-tse-unverified-five-core-observation",
        "providerSourceReadCount": source_read_count,
        "raceCount": len(out), "races": out,
        "observedRaceCount": observed,
        "observedStudiedWinnerCount": winner_count,
        "observedStudiedRunnerCount": eligible_count,
        "winnerBandCounts": band_counts,
        "observedResearchBandExposureCounts": exposure_counts,
        "verifiedRaceCount": 0, "confirmedHitCount": None,
        "officialJraVerified": False,
        "jraIndependentConfirmation": False,
        "officialFeedConnected": False,
        "outcomeCalibrationReady": False,
        "modelAccuracyPercent": None,
        "bettingReady": False, "actualPurchase": False,
        "payoutVerified": False, "roiPercent": None,
        "historicalBandsNotCalibrated": True,
        "sourceIncompleteCouldChange": True,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": (
            "発走前署名済み未検証85点とJRDB暫定着順を参考比較。"
            "S/A/B/Cごとに発走前の研究対象頭数と暫定勝ち馬の頭数を分ける。"
            "公式照合・時系列検証がないため勝率や精度・回収率には算入しません。"
        ),
    }
