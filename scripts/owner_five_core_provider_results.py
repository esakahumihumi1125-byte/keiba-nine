"""Compare sealed five-factor (85-weight) observations with provisional JRDB podiums.

This is an opt-in, read-only *research* comparison, never official JRA truth,
model accuracy, profitability, prediction output or purchase history.
The caller verifies each server HMAC before passing snapshots here.
"""
import re
from datetime import datetime, timezone

from jrdb_program_preview import TRACKS
from evaluation_policy import OWNER_FORMAL_FACTORS, POINTS
from owner_five_core_receipts import _validate, KEYS, FiveCoreReceiptError
from owner_rebound_receipts import _day, _timestamp

VERSION = "owner-five-core-provider-observation-1"
MAX_ROWS = 2160
BANDS = ("S", "A", "B", "C")
# Compare fixed current weights on identical frozen hypotheses, not a new
# score assigned to a horse. Legacy signed 85-point records remain intact.
CURRENT_WEIGHTS = {k: OWNER_FORMAL_FACTORS[k] for k in KEYS}
COMPARISON_MODELS = {
    "training_only": ("training",),
    "current_five": KEYS,
    **{"without_" + k: tuple(x for x in KEYS if x != k) for k in KEYS},
}
assert sum(CURRENT_WEIGHTS.values()) == 79


def _pair_counts(horses, finish_by_number):
    result = {}
    for label, factors in COMPARISON_MODELS.items():
        scores = {n: sum(CURRENT_WEIGHTS[k] * POINTS[h["bands"][k]]
                         for k in factors) for n, h in horses.items()}
        counts = {"concordant": 0, "discordant": 0, "tied": 0}
        numbers = sorted(horses)
        for i, left in enumerate(numbers):
            for right in numbers[i+1:]:
                diff = scores[left] - scores[right]
                finish_diff = finish_by_number[left] - finish_by_number[right]
                if not diff:
                    counts["tied"] += 1
                elif diff * finish_diff < 0:
                    counts["concordant"] += 1
                else:
                    counts["discordant"] += 1
        result[label] = counts
    return result


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
            "rowCount": 0, "invalid": False, "fullPlaces": {},
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
                group["fullPlaces"][n] = place
                if place in (1, 2, 3):
                    if place in group["places"]:
                        group["invalid"] = True
                    group["places"][place] = n

    out, winner_count, eligible_count = [], 0, 0
    paired_races, paired_runners, pair_total = 0, 0, 0
    paired_counts = {k: dict.fromkeys(("concordant", "discordant", "tied"), 0)
                     for k in COMPARISON_MODELS}
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
        # An incomplete signed roster or provisional result never enters a
        # paired comparison. All models use exactly the same full race.
        n = original["raceRunnerCount"]
        paired = (good and len(frozen_horses) == n
                  and group["rowCount"] == n
                  and set(group["fullPlaces"]) == set(frozen_horses)
                  and set(group["fullPlaces"].values()) == set(range(1, n+1)))
        if paired:
            paired_races += 1
            paired_runners += n
            pair_total += n * (n-1) // 2
            for model, counts in _pair_counts(frozen_horses, group["fullPlaces"]).items():
                for label, count in counts.items():
                    paired_counts[model][label] += count
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
        "pairedFactorResearch": {
            "version": "owner-fixed-factor-pair-comparison-1",
            "raceCount": paired_races, "runnerCount": paired_runners,
            "pairCount": pair_total,
            "weights": dict(CURRENT_WEIGHTS),
            "models": paired_counts,
            "sameFullRaceSample": True,
            "tiesKeptSeparate": True,
            "officialJraVerified": False,
            "modelCalibrated": False,
            "changesExistingReceipts": False,
            "newProviderRequests": 0,
        },
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
