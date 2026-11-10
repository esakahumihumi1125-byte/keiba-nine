"""Bounded owner-only historic jockey/trainer source diagnostic, no real grading.

Exactly ONE validated previous race, /dky once + /dse once, when the
authenticated user explicitly opts in to two additional provider reads.
No extra queries to determine a sample. Historical names, horse IDs, keys,
rider/trainer identifiers and raw licensed data NEVER leave this module.
A sample cannot demonstrate trainer skill or JRA-certified results.
"""
from jrdb_history_pipeline import plan_bounded_history, HistoryFetchError
from owner_jrdb_past_staff_join import (
    join_jrdb_past_jockey_trainer, PastStaffJoinError,
)

VERSION = "owner-past-staff-sample-1"


def _report(status, *, queried=0, runners=0, riders=0,
            trainers=0, pairs=0, wins=0, top3=0):
    return {
        "version": VERSION, "status": status,
        "pastRacesSelected": 1 if queried else 0,
        "providerReadCount": queried,
        "runnerCount": runners, "distinctJockeyCount": riders,
        "distinctTrainerCount": trainers,
        "distinctPairCount": pairs,
        "observedFirstPlaceCount": wins, "observedTop3Count": top3,
        "sourceFamily": "private_dky_dse_past_race",
        "pastResultPublicationVerified": False,
        "independentJraVerified": False,
        "jockeyTrainerPerformanceAssessed": False,
        "holdoutValidated": False,
        "formalTenPointGrade": "未評価",
        "formalTenPointScore": None,
        "predictionReady": False, "bettingReady": False,
        "autoPurchase": False, "actualPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "changesExistingReceipts": False,
        "changesExistingTickets": False,
        "changesExistingRoi": False,
        "note": (
            "本人操作で既存の候補から過去1Rだけ追加の2 API照会。"
            "出走馬・着順・騎手厩舎IDの結合状態のみ集計。"
            "過去の確定時刻と独立JRA出典は未確認。"
            "母数が1Rのため騎手・厩舎10点の能力評価には使いません。"
        ),
    }


def inspect_one_past_staff_sample(programme, entries, previous, day, *,
                                  fetch_dky, fetch_dse, limit=8):
    """Explicit two-call sample with zero URL/ID/horse-name output.

    The programme/entries/previous records MUST come from the current private
    day /tra+/tky+/tze snapshot already fetched for history audit. Callers
    MUST not pass client-supplied histories or use this on page load.
    """
    if not callable(fetch_dky) or not callable(fetch_dse):
        raise HistoryFetchError("Private historic callbacks required")
    plan = plan_bounded_history(programme, entries, previous, day, limit)
    pairs = plan.get("privateSelected")
    if not isinstance(pairs, list):
        raise HistoryFetchError("Historical sample plan unavailable")
    if not pairs:
        return _report("no_referenced_past_race")
    key, past_date = pairs[0]
    # Fetch exactly two endpoints. No automatic retry, fallback date range,
    # or second race when records are missing or disqualified.
    try:
        dky = fetch_dky(key)
        dse = fetch_dse(key)
    except Exception:
        return _report("provider_unavailable", queried=2)
    try:
        merged = join_jrdb_past_jockey_trainer(
            dky, dse, racekey=key, racedate=past_date)
    except (PastStaffJoinError, TypeError, KeyError, ValueError):
        return _report("incomplete_or_ambiguous_historical_result", queried=2)
    records = merged["horseRows"]
    jockeys = {h["jockeyRef"] for h in records}
    trainers = {h["trainerRef"] for h in records}
    staff_pairs = {(h["jockeyRef"], h["trainerRef"]) for h in records}
    return _report(
        "joined_private_sample", queried=2,
        runners=len(records), riders=len(jockeys),
        trainers=len(trainers), pairs=len(staff_pairs),
        wins=sum(h["finish"] == 1 for h in records),
        top3=sum(h["finish"] <= 3 for h in records),
    )
