"""Join private full-day source coverage with trusted-clock timing gates.

Pure, bounded, redacted per-race *manual review queue*. This does not fetch JRA
or JRDB and never produces ranked entrants, confirmed odds or betting tickets.
An update timestamp of a provider snapshot never certifies JRA final status.
"""
from jrdb_coverage import CoverageError

VERSION = "private-day-review-1"
WINDOWS = frozenset({"post_time_unknown", "other_date", "post_time_passed",
                     "within_two_hours", "more_than_two_hours"})
GOING_AGE = frozenset({"no_going_report", "no_update_timestamp",
                       "timestamp_in_future", "recent_reported",
                       "old_or_other_date_reported"})


def build_day_review_queue(day, freshness):
    """Validate the same race set before returning per-race timing notes."""
    if (not isinstance(day, dict)
            or day.get("version") != "private-day-pipeline-1"
            or day.get("realPredictionReady") is not False
            or day.get("purchaseReady") is not False
            or day.get("rawHorseRecordsIncluded") is not False
            or not isinstance(day.get("races"), list)
            or type(day.get("raceCount")) is not int
            or len(day["races"]) != day["raceCount"]
            or not 0 <= day["raceCount"] <= 120
            or not isinstance(freshness, dict)
            or freshness.get("version") != "prestart-freshness-1"
            or freshness.get("predictionReady") is not False
            or freshness.get("bettingReady") is not False
            or not isinstance(freshness.get("races"), list)
            or type(freshness.get("raceCount")) is not int
            or freshness["raceCount"] != day["raceCount"]):
        raise CoverageError("Incompatible unverified day review sources")
    snapshots = {}
    for item in freshness["races"]:
        if not isinstance(item, dict):
            raise CoverageError("Invalid timing row")
        key = (item.get("track"), item.get("race"))
        if (key in snapshots or item.get("prestartWindow") not in WINDOWS
                or item.get("sourceGoingAgeStatus") not in GOING_AGE
                or type(item.get("candidateForManualJraReview")) is not bool
                or item.get("officiallyVerified") is True
                or item.get("finalRaceReady") is not False
                or item.get("predictionReady") is not False
                or item.get("bettingReady") is not False):
            raise CoverageError("Invalid prestart review state")
        minutes = item.get("minutesUntilListedPost")
        if minutes is not None and (type(minutes) is not int or
                                    not -100000 <= minutes <= 100000):
            raise CoverageError("Invalid minutes-to-post")
        snapshots[key] = item

    rows = []
    for row in day["races"]:
        if not isinstance(row, dict):
            raise CoverageError("Invalid private source row")
        key = (row.get("track"), row.get("race"))
        snap = snapshots.pop(key, None)
        if (snap is None or row.get("realPredictionReady") is not False
                or row.get("ticketReady") is not False
                or row.get("independentJraVerified") is not False):
            raise CoverageError("Race sources changed during day review")
        if snap.get("listedPostTime") != row.get("postTimeFromProvider"):
            raise CoverageError("Programme post times differ")
        if snap["sourceGoingAgeStatus"] == "recent_reported" and not row.get("sourceGoingRecorded"):
            raise CoverageError("Going age disagrees with source presence")
        if (snap["candidateForManualJraReview"] !=
                (snap["prestartWindow"] == "within_two_hours"
                 and snap["sourceGoingAgeStatus"] == "recent_reported")):
            raise CoverageError("Incorrect prestart candidate classification")
        window = snap["prestartWindow"]
        if window == "post_time_passed":
            priority = "post_time_passed"
        elif window == "within_two_hours":
            priority = "urgent_manual_check"
        else:
            priority = "not_near_start"
        blocks = list(row["blockers"])
        if not row["entryCountMatches"]:
            blocks.append("提供元の登録頭数が未確認・不一致")
        if row["providerWithdrawalPresent"]:
            blocks.append("提供元に出走取消報告あり・公式再確認")
        if row["providerWithdrawalFlagsUnknown"]:
            blocks.append("出走取消フラグが未確認")
        if any(row[k] for k in ("trainingUnaccounted", "lastWeekUnaccounted",
                                "recentUnaccounted")):
            blocks.append("調教・近走に未対応の資料あり（新馬の近走なしは別途判断）")
        if not row["sourceGoingRecorded"]:
            blocks.append("提供元の当日馬場を確認")
        if snap["sourceGoingAgeStatus"] in ("no_update_timestamp", "timestamp_in_future",
                                             "old_or_other_date_reported"):
            blocks.append("馬場資料の更新日時を再確認")
        if window == "post_time_passed":
            blocks.append("発走時刻経過・馬券対象外")
        elif window == "post_time_unknown":
            blocks.append("発走予定時刻が未取得")
        rows.append({
            "track": row["track"], "race": row["race"],
            "postTimeFromProvider": row["postTimeFromProvider"],
            "prestartWindow": window,
            "minutesUntilListedPost": snap["minutesUntilListedPost"],
            "sourceGoingAgeStatus": snap["sourceGoingAgeStatus"],
            "reviewPriority": priority,
            "candidateForManualJraReview": snap["candidateForManualJraReview"],
            "blockers": blocks,
            "independentJraVerified": False, "realPredictionReady": False,
            "ticketReady": False,
        })
    if snapshots:
        raise CoverageError("Different race sets between source and timing")
    order = {"urgent_manual_check": 0, "not_near_start": 1, "post_time_passed": 2}
    rows.sort(key=lambda r: (order[r["reviewPriority"]],
                             r["minutesUntilListedPost"] if r["minutesUntilListedPost"] is not None
                             else 100000, r["track"], r["race"]))
    return {
        "version": VERSION,
        "date": day["date"],
        "raceCount": len(rows),
        "checkedAtJapan": freshness.get("checkedAtJapan"),
        "racesWithinTwoHours": sum(r["prestartWindow"] == "within_two_hours" for r in rows),
        "racesNeedingManualPriorityCheck": sum(
            r["reviewPriority"] == "urgent_manual_check" for r in rows),
        "racesPassedPost": sum(r["reviewPriority"] == "post_time_passed" for r in rows),
        "racesWithRecentSourceGoing": sum(
            r["sourceGoingAgeStatus"] == "recent_reported" for r in rows),
        "races": rows,
        "officialFinalVerified": False,
        "realPredictionReady": False, "purchaseReady": False,
        "note": ("提供元の発走時刻・馬場更新日だけで人が優先チェックする対象を整理。"
                 "公式JRA照合・勝率評価・3連単・投票の実装ではありません。"),
    }
