"""Explicit, bounded 3-race JRDB jockey/trainer cross-race evidence trial.

Consumes only the first up to three *validated* historical keys selected from
the same private /tra, /tky and /tze source already in the owner's history
audit. Fetch /dky and /dse once per key (at most SIX provider reads), and
never return racekeys, horses, jockey/trainer identifiers, names, raw result
records, private time cut or request URLs. No persistence, receipts, grading,
wagers, official results or additional retry/query if a sample is invalid.
"""
from collections import defaultdict

from jrdb_history_pipeline import plan_bounded_history, HistoryFetchError
from owner_jrdb_past_staff_join import (
    join_jrdb_past_jockey_trainer, PastStaffJoinError,
)

VERSION = "owner-past-staff-batch-1"
MAX_RACES = 3


def _summary(*, requested, selected, reads, complete, held, source_unavailable,
             unique_jockeys, unique_trainers, pairs, total_runners, wins, podium):
    return {
        "version": VERSION,
        "requestedRaceLimit": requested,
        "selectedPastRaceCount": selected,
        "providerReadCount": reads,
        "providerReadBudget": 2 * requested,
        "completedJoinRaceCount": complete,
        "heldOrIncompleteRaceCount": held,
        "providerUnavailable": source_unavailable,
        "totalJoinedRunnerObservations": total_runners,
        "distinctJockeyCount": len(unique_jockeys),
        "distinctTrainerCount": len(unique_trainers),
        "distinctPairCount": len(pairs),
        "pairsSeenInTwoOrMoreRaces": sum(len(v) >= 2 for v in pairs.values()),
        "pairRunnerObservations": sum(pairs.values(), []).__len__(),
        "observedFirstPlaceCount": wins,
        "observedTopThreeCount": podium,
        "sourceFamily": "private_dky_dse_bounded_races",
        "pastResultPublicationVerified": False,
        "independentJraVerified": False,
        "fullTenFactorReady": False,
        "jockeyTrainerPerformanceAssessed": False,
        "holdoutValidated": False,
        "formalTenPointGrade": "未評価",
        "formalTenPointScore": None,
        "predictionReady": False,
        "bettingReady": False,
        "autoPurchase": False,
        "actualPurchase": False,
        "researchOnly": True,
        "privateOwnerOnly": True,
        "changesExistingReceipts": False,
        "changesExistingTickets": False,
        "changesExistingRoi": False,
        "additionalPaidReadsOnlyOnExplicitOptIn": True,
        "note": (
            "本人が選んだ最大3件の過去レースを各2照会で研究用に結合。"
            "同一騎手×厩舎が複数レースに現れた件数だけを非識別集計。"
            "3Rは騎手厩舎10点を校正する母数ではありません。"
            "結果公表時刻・JRA公式照合・ホールドアウト未検証。"
            "研究値も保存済み買い目・回収率も変更しません。"
        ),
    }


def inspect_three_past_staff_samples(programme, entries, previous, day, *,
                                     fetch_dky, fetch_dse, limit=8):
    """At most three fixed historical keys, at most six calls, no fallback.

    The returned summary deliberately cannot be used to rate a specific
    rider or trainer: their identities are retained only in transient
    function-local sets, never serialized or stored.
    """
    if not callable(fetch_dky) or not callable(fetch_dse):
        raise HistoryFetchError("Private historical staff callback unavailable")
    plan = plan_bounded_history(programme, entries, previous, day, limit)
    keys = plan.get("privateSelected")
    if not isinstance(keys, (tuple, list)):
        raise HistoryFetchError("Invalid bounded private staff plan")
    selected = tuple(keys[:MAX_RACES])
    seen_jockeys, seen_trainers, pair_races = set(), set(), defaultdict(set)
    total = wins = podium = complete = held = reads = 0
    provider_unavailable = False
    for index, (key, past_day) in enumerate(selected):
        # Provider errors stop further chargeable requests. Invalid result
        # formats hold just that predetermined race, never search elsewhere.
        try:
            reads += 1
            dky = fetch_dky(key)
            reads += 1
            dse = fetch_dse(key)
        except Exception:
            provider_unavailable = True
            held += 1
            held += len(selected) - index - 1
            break
        try:
            joined = join_jrdb_past_jockey_trainer(
                dky, dse, racekey=key, racedate=past_day)
        except (PastStaffJoinError, ValueError, TypeError, KeyError):
            held += 1
            continue
        rows = joined["horseRows"]
        if (joined.get("officialJraVerified") is not False
                or joined.get("resultPublicationTimeVerified") is not False
                or joined.get("eligibleForTimeCutScoring") is not False):
            held += 1
            continue
        complete += 1
        total += len(rows)
        wins += sum(row["finish"] == 1 for row in rows)
        podium += sum(row["finish"] <= 3 for row in rows)
        for row in rows:
            staff = (row["jockeyRef"], row["trainerRef"])
            seen_jockeys.add(staff[0])
            seen_trainers.add(staff[1])
            pair_races[staff].add(key)
    return _summary(
        requested=MAX_RACES, selected=len(selected), reads=reads,
        complete=complete, held=held,
        source_unavailable=provider_unavailable,
        unique_jockeys=seen_jockeys, unique_trainers=seen_trainers,
        pairs=pair_races, total_runners=total, wins=wins, podium=podium,
    )
