"""One historical JRDB day's pre-race-ish /dky training index vs /dse finish.

Exploratory retrospective SOURCE check only, NOT a validated backtest:
archived /dky values have not been proved immutable pre-off snapshots,
the index is NOT today's /tcy or /tch measure, and /dse is not an
independent JRA confirmation. This function never trains, imputes,
decides a horse ticket, or uses odds. No licensed horse-level data
leaves the authenticated private server.
"""
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS

VERSION = "owner-historical-training-index-check-1"
KEY = re.compile(r"[0-9a-f]{8}\Z", re.ASCII)
NUMBER = re.compile(r"(0[1-9]|1[0-8])\Z", re.ASCII)
HORSE_ID = re.compile(r"[0-9a-z]{12}\Z", re.ASCII)
INDEX = re.compile(r"[+-]?(?:\d{1,3})(?:\.\d{1,2})?\Z", re.ASCII)
FINISH = re.compile(r"(?:0?[1-9]|1[0-8])\Z", re.ASCII)
MAX_HORSES = 2160
MAX_RACES = 120


def _racekey(value, day):
    if (type(value) is not str or not KEY.fullmatch(value)
            or value[:2] not in TRACKS or value[2:4] != day[2:4]
            or not value[6:].isdigit() or not 1 <= int(value[6:]) <= 12):
        raise CoverageError("Invalid historical training race identity")
    return TRACKS[value[:2]], int(value[6:])


def _horse(row, day):
    if not isinstance(row, dict) or row.get("racedate") != day:
        raise CoverageError("Historical training source date mismatch")
    coord = _racekey(row.get("racekey"), day)
    number = row.get("horse_number")
    horse_id = row.get("horse_id")
    if type(number) is not str or not NUMBER.fullmatch(number):
        raise CoverageError("Historical training horse number invalid")
    if horse_id not in (None, "") and (
            type(horse_id) is not str or not HORSE_ID.fullmatch(horse_id)):
        raise CoverageError("Historical training horse ID invalid")
    return coord, row["racekey"], int(number), horse_id


def _training(value):
    if value in (None, ""):
        return None
    if type(value) not in (str, int, float) or isinstance(value, bool):
        raise CoverageError("Historical training index type invalid")
    raw = str(value)
    if not INDEX.fullmatch(raw):
        raise CoverageError("Historical training index invalid")
    try:
        index = Decimal(raw)
    except InvalidOperation:
        raise CoverageError("Historical training index invalid") from None
    if not index.is_finite() or not Decimal("-200") <= index <= Decimal("200"):
        raise CoverageError("Historical training index out of range")
    return index


def _finish(value):
    if value in (None, ""):
        return None
    if type(value) is not str:
        raise CoverageError("Historical finishing order type invalid")
    if FINISH.fullmatch(value):
        return int(value)
    # null or nonnumeric completion (nonstarter, lost rider,
    # disqualification) is NOT a loss, nor a graded result.
    if len(value) > 24 or any(ord(ch) < 32 for ch in value):
        raise CoverageError("Historical finishing status malformed")
    return None


def compare_one_historical_training_day(training_rows, finish_rows, day):
    """Validate and join <=36 races; return aggregated ranking diagnostics."""
    if not _valid_date(day):
        raise CoverageError("Historical training day malformed")
    for name, group in (("training", training_rows), ("result", finish_rows)):
        if (not isinstance(group, list) or len(group) > MAX_HORSES
                or any(not isinstance(r, dict) for r in group)):
            raise CoverageError("Historical " + name + " collection invalid")
    by_race, keys, slots, ids = {}, {}, set(), set()
    for row in training_rows:
        coord, key, number, horse_id = _horse(row, day)
        slot = key, number
        if slot in slots:
            raise CoverageError("Historical training runner duplicated")
        slots.add(slot)
        if horse_id:
            identity = key, horse_id
            if identity in ids:
                raise CoverageError("Historical training horse ID duplicated")
            ids.add(identity)
        if coord in keys and keys[coord] != key:
            raise CoverageError("Ambiguous historical race slot")
        keys[coord] = key
        data = by_race.setdefault(coord, {})
        data[number] = {"horse_id": horse_id,
                        "training": _training(row.get("training_index")),
                        "finish": None, "found_result_row": False}
        if len(data) > 18 or len(by_race) > MAX_RACES:
            raise CoverageError("Historical training race over size")
    result_slots = set()
    for row in finish_rows:
        coord, key, number, result_hid = _horse(row, day)
        if coord not in by_race or keys.get(coord) != key:
            raise CoverageError("Result race not present in earlier data")
        slot = key, number
        if slot in result_slots:
            raise CoverageError("Duplicate historical result runner")
        result_slots.add(slot)
        original = by_race[coord].get(number)
        if original is None:
            raise CoverageError("Result horse not in pre-race entry")
        prior = original["horse_id"]
        if prior and result_hid and prior != result_hid:
            raise CoverageError("Result joins a different horse")
        original["found_result_row"] = True
        original["finish"] = _finish(row.get("order_of_finish"))
    totals = Counter()
    reason_counts = Counter()
    races = []
    for track, race in sorted(by_race):
        runners = list(by_race[track, race].values())
        n = len(runners)
        have_index = sum(x["training"] is not None for x in runners)
        have_result_row = sum(x["found_result_row"] for x in runners)
        have_finish = sum(x["finish"] is not None for x in runners)
        pair_count = sum(x["finish"] is not None and
                         x["training"] is not None for x in runners)
        totals.update(dict(
            registered=n, trainingIndexRecorded=have_index,
            resultRowsMatched=have_result_row, numericFinishRecorded=have_finish,
            runnersWithBoth=pair_count))
        # A partial roster never enters the index-performance denominator.
        # Avoid treating withdrawn/missing finish as beaten horses.
        reason = None
        if n < 4:
            reason = "too_few_runners"
        elif have_index != n:
            reason = "training_index_missing"
        elif have_finish != n:
            reason = "race_result_incomplete"
        elif sum(x["finish"] == 1 for x in runners) != 1:
            reason = "single_winner_unconfirmed"
        max_index = max((x["training"] for x in runners
                         if x["training"] is not None), default=None)
        if reason is None and sum(x["training"] == max_index
                                  for x in runners) != 1:
            reason = "top_training_index_tied"
        eligible = reason is None
        hit = None
        concordant = discordant = 0
        if eligible:
            best = next(x for x in runners if x["training"] == max_index)
            hit = best["finish"] == 1
            for i, left in enumerate(runners):
                for right in runners[i + 1:]:
                    # Exclude ambiguous historical index ties and dead heats.
                    score_diff = left["training"] - right["training"]
                    finish_diff = left["finish"] - right["finish"]
                    if not score_diff or not finish_diff:
                        continue
                    if (score_diff > 0 and finish_diff < 0 or
                            score_diff < 0 and finish_diff > 0):
                        concordant += 1
                    else:
                        discordant += 1
            totals["eligibleRaces"] += 1
            totals["uniqueIndexTopWon"] += bool(hit)
            totals["indexFinishConcordantPairs"] += concordant
            totals["indexFinishDiscordantPairs"] += discordant
        else:
            reason_counts[reason] += 1
        races.append({
            "track": track, "race": race,
            "registered": n, "trainingIndexRecorded": have_index,
            "resultRowsMatched": have_result_row,
            "numericFinishRecorded": have_finish,
            "runnersWithBoth": pair_count,
            "retrospectiveComparisonEligible": eligible,
            "ineligibleReason": reason,
            "topIndexWinnerObserved": hit,
            "concordantPairs": concordant,
            "discordantPairs": discordant,
            "officialJraVerified": False,
            "prestartFeatureSnapshotVerified": False,
            "outOfTimeValidated": False, "bettingReady": False,
        })
    for k in ("registered", "trainingIndexRecorded", "resultRowsMatched",
              "numericFinishRecorded", "runnersWithBoth", "eligibleRaces",
              "uniqueIndexTopWon", "indexFinishConcordantPairs",
              "indexFinishDiscordantPairs"):
        totals.setdefault(k, 0)
    # Validate historical dates via rows and strictly prohibit any
    # look-ahead claims; no per-horse index/finish/IDs ever leave memory.
    return {
        "version": VERSION, "date": day, "raceCount": len(races),
        "races": races, "summary": dict(totals),
        "ineligibleReasons": dict(reason_counts),
        "sourceRequestsRequired": ["dky", "dse"],
        "researchOnly": True, "privateOwnerOnly": True,
        "rawProviderRowsIncluded": False,
        "horseNumbersIncluded": False, "oddsUsed": False,
        "trainingSource": "dky_training_index_not_tcy_tch",
        "providerResultSource": "jrdb_dse_not_independent_jra",
        "prestartFeatureSnapshotVerified": False,
        "independentJraVerified": False, "outOfTimeValidated": False,
        "calibrationReady": False, "formalTrainingScore30Ready": False,
        "overallPredictionReady": False, "bettingReady": False,
        "actualPurchase": False, "changesExistingTickets": False,
        "changesExistingReceipts": False, "changesExistingRoi": False,
        "additionalProviderReadsAfterTwo": 0,
        "note": (
            "過去dky調教指数とdse着順の同日比較。指数最高の馬の1着件数"
            "およびレース内順位の整合性だけを参考集計。"
            "dkyの発走前スナップショット真正性、出走取消、"
            "同じtcy/tch指数か、時系列外部検証、JRA公式結果は未検証。"
            "正式調教30点・的中判定・回収率・買い目には反映しない。"
        ),
    }
