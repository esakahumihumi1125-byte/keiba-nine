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
            if index in by_id and by_id[index] != identity:
                raise CoverageError("Ambiguous horse ID within race")
            by_id[index] = identity

    training_seen, week_seen, prior_seen = set(), set(), set()
    all_keys = {item["racekey"] for item in programme}
    for label, collection in (("training", training), ("previous", previous)):
        record_seen = set()
        for row in collection:
            key, date = row.get("racekey"), row.get("racedate")
            if (not isinstance(key, str) or not KEY.fullmatch(key)
                    or key not in all_keys or date != requested_date):
                raise CoverageError("Unrelated " + label + " row")
            num, hid = row.get("horse_number"), row.get("horse_id")
            identity_number = by_number.get((key, num)) if isinstance(num, str) and NUMBER.fullmatch(num) else None
            identity_id = by_id.get((key, hid)) if isinstance(hid, str) and HORSE_ID.fullmatch(hid) else None
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
            record_seen.add(identity)

    for race in base["races"]:
        key = next((row["racekey"] for row in programme
                    if row["track"] == race["track"] and row["race"] == race["race"]), None)
        if key is None:
            raise CoverageError("Programme has no matching race key")
        race["trainingRecords"] = sum(k == key for k, _ in training_seen)
        race["lastWeekRecords"] = sum(k == key for k, _ in week_seen)
        race["pastRunRecords"] = sum(k == key for k, _ in prior_seen)
        race["rosterVerified"] = False
        race["workoutsVerified"] = False
        race["predictionsReady"] = False
        race["evidenceStatus"] = "資料件数のみ確認（評価未実施）"
    base["note"] = ("出走馬・調教・1週前調教・近走の資料件数だけを照合。"
                    "取消、資料の真偽、血統、馬場、展開、予想は未評価。"
                    "新馬など近走がない馬も補完しない。")
    return base
