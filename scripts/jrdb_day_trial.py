"""Private one-day JRDB research comparison (max 36 R, 4 provider calls).

Builds ALL selected day races from one date-bound, identity-audited snapshot.
No JRA official validation, outcome forecasts, S/A/B/C overall ratings, bets,
writes, scheduler, logs, external calls, or public publishing.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_one_race_trial import build_one_race_trial, VERSION as ONE_R_VERSION

VERSION = "owner-day-two-factor-trial-1"


def build_day_trial(programme, entries, training, recent, date):
    """Use one consistent provider snapshot, refuse duplicate/ambiguous races.

    The caller fetches /tra, /tky, /tcy, /tze ONCE each and must be a private,
    authenticated, explicit user action. No provider data is persisted.
    """
    if not _valid_date(date):
        raise CoverageError("Invalid selected day")
    if not isinstance(programme, list) or len(programme) > 36:
        raise CoverageError("Invalid number of races on selected day")
    keys, coords = set(), set()
    for row in programme:
        if not isinstance(row, dict):
            raise CoverageError("Invalid programme row")
        key, course, race = (row.get("racekey"), row.get("track"),
                             row.get("race"))
        if (not isinstance(key, str) or len(key) != 8
                or course not in TRACKS.values()
                or type(race) is not int or not 1 <= race <= 12
                or row.get("racedate") != date or key in keys
                or (course, race) in coords):
            raise CoverageError("Ambiguous day race schedule")
        keys.add(key)
        coords.add((course, race))
    if not programme:
        if entries or training or recent:
            raise CoverageError("Source data exists without scheduled races")
        return {
            "version": VERSION, "date": date, "raceCount": 0,
            "runnerCount": 0, "twoFactorComparable": 0, "ungraded": 0,
            "researchOnly": True, "officialJraVerified": False,
            "overallRankReady": False, "predictionReady": False,
            "bettingReady": False, "autoTicketReady": False,
            "races": [],
            "warning": "番組データに対象レースがありません。実開催なしとは断定できません。",
        }
    if len({row["track"] for row in programme}) > 3:
        raise CoverageError("Unexpected number of simultaneous racecourses")
    # Perform the costly joins once, not per R. These existing builders audit
    # source dates, race/horse identity and duplicate provider observations.
    train = build_training_hints(programme, entries, training, date)
    past = build_recent_hints(programme, entries, recent, date)
    if (len(train) != len(programme) or len(past) != len(programme)
            or {row.get("racekey") for row in train} != keys
            or {row.get("racekey") for row in past} != keys):
        raise CoverageError("Incomplete shared research snapshot")
    results = []
    for row in programme:
        r = build_one_race_trial(programme, entries, training, recent, date,
                                 row["track"], row["race"], hints=(train, past))
        if (r["version"] != ONE_R_VERSION or r["predictionReady"] is not False
                or r["bettingReady"] is not False or r["autoTicketReady"] is not False):
            raise CoverageError("Non-research result in shared day snapshot")
        results.append(r)
    observed = sum(r["runnersObserved"] for r in results)
    compared = sum(r["twoFactorComparable"] for r in results)
    missing = sum(r["ungraded"] for r in results)
    if compared + missing != observed or observed > 36 * 18:
        raise CoverageError("Day runner coverage mismatch")
    return {
        "version": VERSION, "date": date, "raceCount": len(results),
        "runnerCount": observed, "twoFactorComparable": compared,
        "ungraded": missing, "researchOnly": True,
        "officialJraVerified": False, "overallRankReady": False,
        "predictionReady": False, "bettingReady": False,
        "autoTicketReady": False, "races": results,
        "warning": ("当日の各Rを調教・近走の暫定2項目のみで比較。"
                    "元データは本人専用・未検証。JRA公式出走確定・取消・馬場未照合、"
                    "残り8項目未評価。実戦予想・買い目は未作成です。"),
    }
