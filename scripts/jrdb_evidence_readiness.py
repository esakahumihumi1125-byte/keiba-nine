"""Private-only checks for pre-race training and recent-run data availability.

Never returns JRDB horse-level fields, names, timestamps, scores or any actual
prediction. Missing records are NOT fabricated, including first-time starters.
This module cannot decide whether a horse is fit, fast, or suitable.
"""
from datetime import datetime
import re

from jrdb_coverage import CoverageError, audit_race_coverage

KEY = re.compile(r"[0-9a-f]{8}\Z", re.ASCII)
NUMBER = re.compile(r"(0[1-9]|1[0-8])\Z", re.ASCII)
HORSE_ID = re.compile(r"[0-9a-z]{12}\Z", re.ASCII)
DATE = re.compile(r"[0-9]{8}\Z", re.ASCII)

# These are indicators of an actual source record, not ranking scores.
TRAINING_FIELDS = (
    "oikirisisu", "siagarisisu", "exercise_amount_eval", "exercise_eval",
)
LAST_WEEK_FIELDS = ("oikirisisu_lastweek", "oikiri_course_lastweek")


def _present(value):
    return value is not None and value != "" and value != " "


def _check_collection(rows, label):
    if not isinstance(rows, list) or len(rows) > 2160:
        raise CoverageError("Invalid " + label + " collection")
    if not all(isinstance(row, dict) for row in rows):
        raise CoverageError("Invalid " + label + " row")


def _valid_date(text):
    if not isinstance(text, str) or not DATE.fullmatch(text):
        return False
    try:
        datetime.strptime(text, "%Y%m%d")
    except ValueError:
        return False
    return True


def audit_evidence_coverage(programme, entries, training, previous, requested_date):
    """Summarize counts only, never make or validate predictions.

    Training may have null horse_number. Matching by an unambiguous tky horse_id
    is supported, but every training/previous record must match this race/date.
    """
    base = audit_race_coverage(programme, entries, requested_date)
    _check_collection(entries, "entry")
    _check_collection(training, "training")
    _check_collection(previous, "previous")

    by_number = {}
    by_id = {}
    for entry in entries:
        key, num, hid = entry["racekey"], entry["horse_number"], entry.get("horse_id")
        identity = (key, num)
        by_number[identity] = identity
        if hid is not None and hid != "":
            if not isinstance(hid, str) or not HORSE_ID.fullmatch(hid):
                raise CoverageError("Invalid horse ID in entry")
            index = (key, hid)
            if index in by_id:
                raise CoverageError("Duplicate horse ID within race")
            by_id[index] = identity

    training_seen, week_seen, prior_seen = set(), set(), set()
    all_keys = {item["racekey"] for item in programme}
    for label, collection in (("training", training), ("previous", previous)):
        for row in collection:
            key, date = row.get("racekey"), row.get("racedate")
            if (not isinstance(key, str) or not KEY.fullmatch(key)
                    or key not in all_keys or date != requested_date):
                raise CoverageError("Unrelated " + label + " row")
            num, hid = row.get("horse_number"), row.get("horse_id")
            identity_number = by_number.get((key, num)) if isinstance(num, str) and NUMBER.fullmatch(num) else None
            identity_id = by_id.get((key, hid)) if isinstance(hid, str) and HORSE_ID.fullmatch(hid) else None
            if isinstance(hid, str) and hid and not HORSE_ID.fullmatch(hid):
                raise CoverageError("Malformed horse ID")
            if isinstance(num, str) and num and not NUMBER.fullmatch(num):
                raise CoverageError("Malformed horse number")
            if hid and identity_id is None:
                raise CoverageError("Unmatched horse ID")
            if identity_id and identity_number and identity_id != identity_number:
                raise CoverageError("Horse ID and horse number disagree")
            identity = identity_id or identity_number
            if identity is None:
                # No evidence is counted if its horse identity cannot be verified.
                continue
            if label == "training":
                if any(_present(row.get(field)) for field in TRAINING_FIELDS):
                    training_seen.add(identity)
                if any(_present(row.get(field)) for field in LAST_WEEK_FIELDS):
                    week_seen.add(identity)
            else:
                # Previous-race evidence must actually predate the target race.
                dates = [row.get("race_back_" + str(i) + "_racedate") for i in range(1, 6)]
                for past_date in dates:
                    if _present(past_date):
                        if not _valid_date(past_date) or past_date >= requested_date:
                            raise CoverageError("Previous run date is invalid")
                if any(_present(d) for d in dates):
                    prior_seen.add(identity)

    for race in base["races"]:
        key = next((row["racekey"] for row in programme
                    if row["track"] == race["track"] and row["race"] == race["race"]), None)
        if key is None:
            raise CoverageError("Programme has no matching race key")
        race["trainingRecords"] = sum(k == key for k, _ in training_seen)
        race["lastWeekRecords"] = sum(k == key for k, _ in week_seen)
        race["pastRunRecords"] = sum(k == key for k, _ in prior_seen)
        # A verified entry identity can lack an evidence record, but the absence
        # is not proof that a workout was missed or a first-time starter ran before.
        observed = race["observedEntries"]
        race["trainingUnaccounted"] = max(0, observed - race["trainingRecords"])
        race["lastWeekUnaccounted"] = max(0, observed - race["lastWeekRecords"])
        race["pastRunUnaccounted"] = max(0, observed - race["pastRunRecords"])
        gaps = []
        if race["status"] != "件数一致（取消等未照合）":
            gaps.append("出走馬登録数を要確認")
        if race["trainingUnaccounted"]:
            gaps.append("調教記録なし・未対応 " + str(race["trainingUnaccounted"]) + "頭分")
        if race["lastWeekUnaccounted"]:
            gaps.append("1週前調教記録なし・未対応 " + str(race["lastWeekUnaccounted"]) + "頭分")
        if race["pastRunUnaccounted"]:
            gaps.append("近走記録なし・該当なし " + str(race["pastRunUnaccounted"]) + "頭分")
        race["evidenceGaps"] = gaps
        race["rosterVerified"] = False
        race["workoutsVerified"] = False
        race["predictionsReady"] = False
        race["evidenceStatus"] = ("資料に不足・未対応あり（評価未実施）" if gaps
                                  else "資料件数のみ一致（内容評価未実施）")
    base["gapRaceCount"] = sum(bool(race["evidenceGaps"]) for race in base["races"])
    base["unaccountedTotals"] = {
        "training": sum(r["trainingUnaccounted"] for r in base["races"]),
        "lastWeek": sum(r["lastWeekUnaccounted"] for r in base["races"]),
        "pastRuns": sum(r["pastRunUnaccounted"] for r in base["races"]),
    }
    base["note"] = ("出走馬・調教・1週前調教・近走の資料件数だけを照合。"
                    "記録がない馬には新馬・未提供・未照合が含まれ、欠損の原因は不明。"
                    "取消、資料の真偽、血統、馬場、展開、予想は未評価。"
                    "実馬名・馬ID・元データや買い目はこの診断結果に含まれない。")
    return base
