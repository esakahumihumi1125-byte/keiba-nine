"""Owner-only coverage audit; never returns JRDB horse records or model predictions.

Combines validated /tra programme preview with /tky horse identifiers.
Counts matching records only. It cannot prove scratches, source completeness,
runner eligibility, workout coverage, or the validity of a final prediction.
"""
import re

KEY = re.compile(r"[0-9a-f]{8}\Z", re.ASCII)
DATE = re.compile(r"[0-9]{8}\Z", re.ASCII)
NUMBER = re.compile(r"(0[1-9]|1[0-8])\Z", re.ASCII)


class CoverageError(ValueError):
    """Unexpected schema or inconsistent provider records."""


def audit_race_coverage(programme, entries, requested_date):
    if not isinstance(requested_date, str) or not DATE.fullmatch(requested_date):
        raise CoverageError("Invalid date")
    if not isinstance(programme, list) or len(programme) > 120:
        raise CoverageError("Invalid programme")
    if not isinstance(entries, list) or len(entries) > 2160:
        raise CoverageError("Invalid horse entries")
    expected = {}
    for race in programme:
        if not isinstance(race, dict) or race.get("racedate") != requested_date:
            raise CoverageError("Mismatched programme")
        key = race.get("racekey")
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in expected:
            raise CoverageError("Invalid or duplicate programme race")
        if race.get("track") is None or type(race.get("race")) is not int:
            raise CoverageError("Programme has not been normalized")
        expected[key] = race
    horses = {key: set() for key in expected}
    for raw in entries:
        if not isinstance(raw, dict):
            raise CoverageError("Invalid horse entry")
        key = raw.get("racekey")
        date = raw.get("racedate")
        number = raw.get("horse_number")
        if (not isinstance(key, str) or not KEY.fullmatch(key) or
                key not in horses or date != requested_date):
            raise CoverageError("Horse entry belongs to another race or date")
        if not isinstance(number, str) or not NUMBER.fullmatch(number):
            raise CoverageError("Invalid horse number")
        if number in horses[key]:
            raise CoverageError("Duplicate horse entry")
        horses[key].add(number)
    details = []
    for key, race in expected.items():
        actual = len(horses[key])
        declared = race.get("headcount")
        if type(declared) is not int or not 0 <= declared <= 18:
            declared = None
        if declared is None or declared == 0:
            status = "頭数未確認"
        elif actual == declared:
            status = "件数一致（取消等未照合）"
        elif actual < declared:
            status = "出走馬データ不足"
        else:
            status = "出走馬データ過多"
        details.append({
            "date": requested_date,
            "track": race["track"],
            "race": race["race"],
            "post_time": race.get("post_time"),
            "expectedRunners": declared,
            "observedEntries": actual,
            "status": status,
            "rosterVerified": False,
            "workoutsVerified": False,
            "predictionsReady": False,
        })
    details.sort(key=lambda x: (x["post_time"] or "99:99", x["track"], x["race"]))
    return {
        "date": requested_date,
        "raceCount": len(details),
        "matchingEntryCounts": sum(row["status"] == "件数一致（取消等未照合）" for row in details),
        "fullyVerifiedRaces": 0,
        "predictionsReady": 0,
        "note": "番組と出走馬データの件数を照合しただけです。取消・調教・近走・血統・当日馬場は未検証。",
        "races": details,
    }
