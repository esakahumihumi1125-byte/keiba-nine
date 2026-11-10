"""Offline, out-of-time pedigree six-point RESEARCH preflight.

Requires a separately sourced, complete full-field result history that is not
yet available from the bounded JRDB lookup. No network, paid calls, storing of
horse identities, official JRA claims, betting advice or grades. The held-out
results never update the training cohort.
"""
from collections import defaultdict
from datetime import timedelta

from evaluation_policy import OWNER_FORMAL_FACTORS, OWNER_FORMAL_POLICY_VERSION
from owner_pedigree_cohort_study import (
    TARGET_FIELDS, PAST_FIELDS, MAX_HISTORY_RACES, MIN_RACES, MIN_RUNNERS,
    MIN_DISTINCT_HORSES, PedigreeCohortError,
    _context, _validate_runners, _time, _distance_band,
)

VERSION = "owner-pedigree-walkforward-private-1"
MIN_TRAIN_RACES = 10
MIN_HOLDOUT_RACES = 5
MIN_HOLDOUT_RUNNERS = 20
PRIOR_STRENGTH = 12
assert OWNER_FORMAL_FACTORS["pedigree"] == 6


def _matches(record, target, distance_band):
    return (
        record["track"] == target["track"]
        and record["surface"] == target["surface"]
        and record["going"] == target["going"]
        and _distance_band(record["distanceM"]) == distance_band
    )


def _groups(past):
    """Counts from pre-published training races ONLY, within one held cutoff."""
    sire, damsire, used_horses = {}, {}, set()
    for day, record in past:
        key = (day, record["track"], record["race"])
        for h in record["runners"]:
            used_horses.add(h["horseRef"])
            for source, group in (("sireRef", sire), ("damsireRef", damsire)):
                g = group.setdefault(h[source], [0, 0, set(), set()])
                g[0] += 1
                g[1] += int(h["finish"] <= 3)
                g[2].add(key)
                g[3].add(h["horseRef"])
    return sire, damsire, used_horses


def _qualified(group):
    return (group is not None
            and group[0] >= MIN_RUNNERS
            and len(group[2]) >= MIN_RACES
            and len(group[3]) >= MIN_DISTINCT_HORSES)


def pedigree_walkforward_preflight(target, history):
    """Compare strictly past sire/damsire evidence on later untouched races.

    Never transfer a race's results or a runner's own previous result to its
    holdout prediction. A fixed date-scoped 70/30 train/holdout split avoids
    tuning to the observed validation outcomes. Results are DESCRIPTIVE only.
    """
    day, off = _context(target, TARGET_FIELDS)
    _validate_runners(target, historic=False)
    capture = _time(target["capturedAt"])
    if not timedelta(0) < off - capture <= timedelta(days=7):
        raise PedigreeCohortError("Target was not captured before its start")
    if not isinstance(history, list) or len(history) > MAX_HISTORY_RACES:
        raise PedigreeCohortError("Invalid historical pedigree sample size")

    records, seen = [], set()
    future, other_conditions = 0, 0
    distance_band = _distance_band(target["distanceM"])
    for record in history:
        prior_day, prior_off = _context(record, PAST_FIELDS)
        _validate_runners(record, historic=True)
        key = (prior_day, record["track"], record["race"])
        if key in seen or key == (day, target["track"], target["race"]):
            raise PedigreeCohortError("Duplicate or target result")
        seen.add(key)
        available = _time(record["resultAvailableAt"])
        if available <= prior_off:
            raise PedigreeCohortError("Claimed result publication precedes off time")
        if prior_day >= day or available >= capture:
            future += 1
            continue
        if not _matches(record, target, distance_band):
            other_conditions += 1
            continue
        records.append((prior_day, prior_off, available, record))

    records.sort(key=lambda x: (x[0], x[1], x[3]["race"]))
    days = sorted({item[0] for item in records})
    split = days[len(days) * 7 // 10] if len(days) >= 2 else None
    train = [item for item in records if split is not None and item[0] < split]
    holdout = [item for item in records if split is not None and item[0] >= split]

    compared, compared_races, overlap, no_group = 0, set(), 0, 0
    sire_used = damsire_used = 0
    naive_error = pedigree_error = 0.0
    # Fixed train; an observed held-out finish NEVER changes its reference.
    if len(train) >= MIN_TRAIN_RACES:
        for held_day, held_off, _, race in holdout:
            earlier = [(d, r) for d, _, published, r in train
                       if d < held_day and published < held_off]
            by_sire, by_damsire, seen_horses = _groups(earlier)
            baseline = 3 / len(race["runners"])
            for horse in race["runners"]:
                # Do not smuggle previous finishes of the SAME horse into its
                # bloodline estimate; test generalization to unseen horses.
                if horse["horseRef"] in seen_horses:
                    overlap += 1
                    continue
                sire = by_sire.get(horse["sireRef"])
                damsire = by_damsire.get(horse["damsireRef"])
                if _qualified(sire):
                    group = sire
                    sire_used += 1
                elif _qualified(damsire):
                    group = damsire
                    damsire_used += 1
                else:
                    no_group += 1
                    continue
                smoothed = (group[1] + PRIOR_STRENGTH * baseline) / (
                    group[0] + PRIOR_STRENGTH)
                label = int(horse["finish"] <= 3)
                pedigree_error += (smoothed - label) ** 2
                naive_error += (baseline - label) ** 2
                compared += 1
                compared_races.add((held_day, race["track"], race["race"]))

    sufficient = (len(train) >= MIN_TRAIN_RACES
                  and len(compared_races) >= MIN_HOLDOUT_RACES
                  and compared >= MIN_HOLDOUT_RUNNERS)
    return {
        "version": VERSION,
        "policyVersion": OWNER_FORMAL_POLICY_VERSION,
        "factor": "pedigree", "weight": 6,
        "providedHistoricalRaces": len(history),
        "conditionMatchedHistoricalRaces": len(records),
        "futureOrUnpublishedExcluded": future,
        "differentConditionsExcluded": other_conditions,
        "trainingRaceCount": len(train),
        "holdoutRaceCount": len(holdout),
        "holdoutComparisonRaces": len(compared_races),
        "holdoutComparisonRunners": compared,
        "heldOutPreviouslySeenHorseRunnersExcluded": overlap,
        "holdoutNoQualifiedLineageRunners": no_group,
        "comparedBySire": sire_used,
        "comparedByDamsire": damsire_used,
        "minimumTrainingRaces": MIN_TRAIN_RACES,
        "minimumLineageHistoricalRaces": MIN_RACES,
        "minimumLineageStarts": MIN_RUNNERS,
        "minimumDistinctHistoricalHorses": MIN_DISTINCT_HORSES,
        "minimumHoldoutRaces": MIN_HOLDOUT_RACES,
        "minimumHoldoutRunners": MIN_HOLDOUT_RUNNERS,
        "descriptiveComparisonCoverageMet": sufficient,
        "pedigreeTopThreeBrier": (
            round(pedigree_error / compared, 6) if sufficient else None),
        "naiveTopThreeBrier": (
            round(naive_error / compared, 6) if sufficient else None),
        "claimedPublicationTimesIndependentlyVerified": False,
        "independentJraVerified": False,
        "horseQualityAndConfoundingAdjusted": False,
        "prospectiveResultCalibrationVerified": False,
        "formalPedigreeGrade": "未評価",
        "formalPedigreeScore6": None,
        "predictionReady": False, "bettingReady": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "providerReads": 0, "autoPurchase": False,
        "changesExistingReceipts": False,
        "changesExistingTickets": False,
        "changesExistingRoi": False,
        "note": (
            "血統ごとの過去実績を古い学習期間と未使用の後日検証に分離。"
            "同じ馬自身の成績・結果公開前データ・検証期間の結果を学習へ混ぜない。"
            "JRA独立確認と馬質補正は未実施。比較が良好でも血統6点・"
            "正式S/A/B/C・買い目・回収率へ昇格させません。"
        ),
    }
