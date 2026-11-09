"""Owner-only race-day body-condition 1-point evidence gate (not a grade).

Consumes the *already redacted* joined /tra+/tky+/tpd report. Raw kilograms,
weight changes, odds, paddock indices, horse identities and market data never
enter this function. A recorded weight + change is a SOURCE PAIR, NOT proof
of fitness. The 1-point factor remains ungraded until official independent
verification and out-of-time conditional evaluation exist.
"""
from evaluation_policy import FACTORS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_prestart_body import VERSION as PRESTART_VERSION
from jrdb_program_preview import TRACKS

VERSION = "owner-body-one-evidence-preflight-1"
FACTOR = "body_condition"
FIELDS = frozenset(("number", "prestartRowMatched", "bodyWeightRecorded",
                    "weightChangeRecorded", "jraOfficialWeightVerified",
                    "bodyConditionGrade", "bodyConditionScore1", "bettingReady"))
BASE_GAPS = ("independent_jra_weight_not_verified",
             "body_condition_effect_not_calibrated",
             "temporal_holdout_not_validated")
assert FACTORS[FACTOR] == 1


def body_one_evidence_preflight(source):
    if (not isinstance(source, dict) or source.get("version") != PRESTART_VERSION
            or not isinstance(source.get("date"), str)
            or not isinstance(source.get("races"), list)
            or not 0 <= len(source["races"]) <= 120
            or type(source.get("raceCount")) is not int
            or source["raceCount"] != len(source["races"])
            or source.get("rawHorseRecordsIncluded") is not False
            or source.get("oddsUsed") is not False
            or source.get("officialBodyWeightVerified") is not False
            or source.get("bodyConditionGraded") is not False
            or source.get("realPredictionReady") is not False
            or source.get("purchaseReady") is not False
            or source.get("sourceRequestsRequired") != ["tra", "tky", "tpd"]
            or not isinstance(source.get("summary"), dict)
            or set(source["summary"]) != {
                "matchedRows", "weightRecords", "paddockRecords", "missingRows"}):
        raise CoverageError("Unverified body-one source report")

    output, seen, sums = [], set(), dict.fromkeys(source["summary"], 0)
    for race in source["races"]:
        if (not isinstance(race, dict) or race.get("track") not in TRACKS.values()
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or (race["track"], race["race"]) in seen
                or not isinstance(race.get("runners"), list)
                or type(race.get("registered")) is not int
                or not 0 <= race["registered"] <= 18
                or len(race["runners"]) != race["registered"]
                or any(race.get(k) is not False for k in (
                    "sourceDataUpdatedAtVerified", "officialBodyWeightVerified",
                    "bodyConditionGraded", "realPredictionReady", "ticketReady"))):
            raise CoverageError("Invalid body-one race")
        seen.add((race["track"], race["race"]))
        count_names = ("prestartRowsMatched", "prestartRowsMissing",
                       "bodyWeightRecords", "weightChangeRecords",
                       "paddockRecords", "bodyStateCodeRecords",
                       "providerWithdrawnReports")
        if (any(type(race.get(k)) is not int or not 0 <= race[k] <= race["registered"]
                for k in count_names)
                or race["registered"] != race["prestartRowsMatched"] + race["prestartRowsMissing"]
                or race["weightChangeRecords"] > race["bodyWeightRecords"]
                or any(race[k] > race["prestartRowsMatched"] for k in (
                    "bodyWeightRecords", "weightChangeRecords", "paddockRecords",
                    "bodyStateCodeRecords", "providerWithdrawnReports"))):
            raise CoverageError("Invalid body-one source totals")
        counters = dict(matched=0, weight=0, change=0)
        numbers, horses = set(), []
        for h in race["runners"]:
            if (not isinstance(h, dict) or set(h) != FIELDS
                    or type(h.get("number")) is not int
                    or not 1 <= h["number"] <= 18 or h["number"] in numbers
                    or any(type(h.get(k)) is not bool for k in (
                        "prestartRowMatched", "bodyWeightRecorded", "weightChangeRecorded"))
                    or h["jraOfficialWeightVerified"] is not False
                    or h["bodyConditionGrade"] != "未評価"
                    or h["bodyConditionScore1"] is not None
                    or h["bettingReady"] is not False
                    or (h["bodyWeightRecorded"] and not h["prestartRowMatched"])
                    or (h["weightChangeRecorded"] and not h["bodyWeightRecorded"])):
                raise CoverageError("Invalid body-one runner")
            numbers.add(h["number"])
            counters["matched"] += int(h["prestartRowMatched"])
            counters["weight"] += int(h["bodyWeightRecorded"])
            counters["change"] += int(h["weightChangeRecorded"])
            gaps = []
            if not h["prestartRowMatched"]:
                gaps.append("prestart_runner_row_unavailable")
            if not h["bodyWeightRecorded"]:
                gaps.append("body_weight_measurement_missing")
            if not h["weightChangeRecorded"]:
                gaps.append("previous_weight_comparison_missing")
            gaps.extend(BASE_GAPS)
            horses.append({
                "number": h["number"],
                "sourcePairPresent": h["bodyWeightRecorded"] and h["weightChangeRecorded"],
                "missingEvidence": gaps,
                "grade": "未評価", "score1": None,
                "officialVerified": False, "effectValidated": False,
                "temporalValidationComplete": False, "bettingReady": False,
            })
        if (counters["matched"] != race["prestartRowsMatched"]
                or counters["weight"] != race["bodyWeightRecords"]
                or counters["change"] != race["weightChangeRecords"]):
            raise CoverageError("Body-one runner counts differ")
        for src, target in (("prestartRowsMatched", "matchedRows"),
                            ("bodyWeightRecords", "weightRecords"),
                            ("paddockRecords", "paddockRecords"),
                            ("prestartRowsMissing", "missingRows")):
            sums[target] += race[src]
        horses.sort(key=lambda x: x["number"])
        output.append({
            "track": race["track"], "race": race["race"],
            "runnerCount": race["registered"],
            "completeMeasuredPairs": counters["change"],
            "missingMeasuredPairs": race["registered"] - counters["change"],
            "verifiedGradeCount": 0,
            "horses": horses, "scoreReady": False,
        })
    if sums != source["summary"]:
        raise CoverageError("Body-one source summary disagrees")
    output.sort(key=lambda r: (r["track"], r["race"]))
    return {
        "version": VERSION, "date": source["date"],
        "policyVersion": POLICY_VERSION, "factor": FACTOR,
        "weight": FACTORS[FACTOR], "raceCount": len(output), "races": output,
        "verifiedGradeCount": 0, "officialJraVerified": False,
        "sourceTimestampVerified": False, "conditionEffectValidated": False,
        "outOfTimeValidated": False, "overallPredictionReady": False,
        "bettingReady": False, "autoPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "changesExistingTickets": False, "changesExistingReceipts": False,
        "note": ("馬体重と前走比の記録有無を同一馬番で確認。"
                 "1点の正式採点にはJRA公式値・発表時刻・"
                 "同条件での過去実績と時系列検証が必要。"
                 "記録ありは体調良好や馬券推奨を意味しない。"),
    }
