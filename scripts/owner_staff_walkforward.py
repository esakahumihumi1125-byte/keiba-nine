"""Owner-only OFFLINE walk-forward diagnostic for jockey x trainer pairs.

The source is independently supplied, fully validated synthetic/provenance
candidate data, never fetched here. A fixed earlier-training / later-holdout
split prevents the tested race from appearing in its own reference sample.
Even a favorable holdout comparison is NOT evidence of JRA authentication,
causality, a calibrated ten-point score or actual betting performance.
Return anonymous aggregate counters only. Never serialize private identities.
"""
from collections import defaultdict
from datetime import timedelta
import math

from evaluation_policy import OWNER_FORMAL_POLICY_VERSION as POLICY_VERSION
from owner_support_six_cohort_study import (
    TARGET_FIELDS, HISTORY_FIELDS, MAX_RACES, SupportCohortError,
    _race, _check_horses, _time_checked, _distance_band, _field_band,
)

VERSION = "owner-staff-walkforward-private-1"
MIN_TRAIN_RACES = 10
MIN_PAIR_RACES = 8
MIN_PAIR_OBSERVATIONS = 15
MIN_EVALUATION_RACES = 5
MIN_EVALUATION_RUNNERS = 20
SMOOTHING_STRENGTH = 12


def _comparable(record, target, field_band, distance_band):
    return (
        record["track"] == target["track"]
        and record["surface"] == target["surface"]
        and record["going"] == target["going"]
        and record["classCode"] == target["classCode"]
        and _distance_band(record["distanceM"]) == distance_band
        and _field_band(len(record["runners"])) == field_band
    )


def staff_pair_walkforward_preflight(target, history):
    """Strictly past-observable, fixed-split pair-vs-naive diagnostic.

    For each held-out race, only *older* training races whose claimed result
    availability precedes its start can be used. No holdout race updates the
    training dictionary, and no matching pair may borrow another pair's starts.
    The result publication timestamps have NOT been independently verified.
    """
    day, off = _race(target, TARGET_FIELDS)
    _check_horses(target, day, historical=False)
    capture = _time_checked(target["capturedAt"])
    if not timedelta(0) < off - capture <= timedelta(days=7):
        raise SupportCohortError("Target was not locked before start")
    if not isinstance(history, list) or len(history) > MAX_RACES:
        raise SupportCohortError("Invalid historical sample size")

    historical = []
    seen = set()
    future = mismatched = 0
    band = _field_band(len(target["runners"]))
    distance = _distance_band(target["distanceM"])
    for record in history:
        race_day, race_off = _race(record, HISTORY_FIELDS)
        _check_horses(record, race_day, historical=True)
        key = (race_day, record["track"], record["race"])
        if key in seen or key == (day, target["track"], target["race"]):
            raise SupportCohortError("Duplicate or target historical race")
        seen.add(key)
        available = _time_checked(record["resultAvailableAt"])
        if available <= race_off:
            raise SupportCohortError("Invalid historical result clock")
        if race_day >= day or available >= capture:
            future += 1
            continue
        if not _comparable(record, target, band, distance):
            mismatched += 1
            continue
        historical.append((race_day, race_off, available, record))

    historical.sort(key=lambda item: (item[0], item[1], item[3]["race"]))
    distinct_days = sorted({x[0] for x in historical})
    # Splitting by day means no same-day result can leak across train and test.
    cutoff = distinct_days[(len(distinct_days) * 7) // 10] if len(distinct_days) >= 2 else None
    train = [x for x in historical if cutoff is not None and x[0] < cutoff]
    holdout = [x for x in historical if cutoff is not None and x[0] >= cutoff]

    baseline_error = pair_error = 0.0
    compared = 0
    compared_races = set()
    skipped_no_pair = 0
    # Keep the training cohort FIXED throughout validation.
    if len(train) >= MIN_TRAIN_RACES:
        for held_day, held_off, _, held in holdout:
            by_pair = defaultdict(lambda: [0, 0, set()])
            for prior_day, prior_off, prior_available, prior in train:
                # Do not infer publish time from the date or from a joined result.
                if not prior_day < held_day or not prior_available < held_off:
                    continue
                identity = (prior_day, prior["track"], prior["race"])
                for horse in prior["runners"]:
                    group = by_pair[(horse["jockeyRef"], horse["trainerRef"])]
                    group[0] += 1
                    group[1] += int(horse["finish"] <= 3)
                    group[2].add(identity)

            naive = 3 / len(held["runners"])
            for horse in held["runners"]:
                obs, top3, race_ids = by_pair.get(
                    (horse["jockeyRef"], horse["trainerRef"]), (0, 0, set()))
                if obs < MIN_PAIR_OBSERVATIONS or len(race_ids) < MIN_PAIR_RACES:
                    skipped_no_pair += 1
                    continue
                estimate = (top3 + SMOOTHING_STRENGTH * naive) / (
                    obs + SMOOTHING_STRENGTH)
                label = int(horse["finish"] <= 3)
                baseline_error += (naive - label) ** 2
                pair_error += (estimate - label) ** 2
                compared += 1
                compared_races.add((held_day, held["track"], held["race"]))

    # Never present an undersized or unverified pseudo-metric as skill.
    enough = (
        len(train) >= MIN_TRAIN_RACES
        and len(compared_races) >= MIN_EVALUATION_RACES
        and compared >= MIN_EVALUATION_RUNNERS
    )
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "providedHistoricalRaces": len(history),
        "eligibleConditionMatchedRaces": len(historical),
        "futureOrUnpublishedRacesExcluded": future,
        "otherConditionRacesExcluded": mismatched,
        "trainingRaceCount": len(train),
        "holdoutRaceCount": len(holdout),
        "holdoutPairComparisonRaces": len(compared_races),
        "holdoutPairComparisonRunners": compared,
        "holdoutWithoutQualifiedPairRunners": skipped_no_pair,
        "minimumTrainingRaces": MIN_TRAIN_RACES,
        "minimumPairHistoricalRaces": MIN_PAIR_RACES,
        "minimumPairHistoricalStarts": MIN_PAIR_OBSERVATIONS,
        "minimumHoldoutRaces": MIN_EVALUATION_RACES,
        "minimumHoldoutComparisonRunners": MIN_EVALUATION_RUNNERS,
        "descriptiveComparisonCoverageMet": enough,
        "pairTopThreeBrier": round(pair_error / compared, 6) if enough else None,
        "naiveTopThreeBrier": round(baseline_error / compared, 6) if enough else None,
        "claimedResultPublicationTimesIndependentlyVerified": False,
        "independentJraVerified": False,
        "causalPairEffectVerified": False,
        "outOfTimePerformanceOfficiallyValidated": False,
        "formalTenPointGrade": "未評価",
        "formalTenPointScore": None,
        "predictionReady": False, "bettingReady": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "sourceReadCount": 0, "autoPurchase": False,
        "changesExistingReceipts": False, "changesExistingTickets": False,
        "changesExistingRoi": False,
        "note": (
            "騎手×厩舎ペアの過去結果を古い学習期間と未使用期間に分離。"
            "未使用期間の実際の着順を過去側へ混ぜない。"
            "結果公表時刻の独立証明・JRA照合・条件差や馬質の補正は未完成。"
            "比較誤差が小さくても騎手厩舎10点や正式S/A/B/Cに変換しません。"
        ),
    }
