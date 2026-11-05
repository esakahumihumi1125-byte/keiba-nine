"""One-read-per-source, full-day *readiness* coordinator for private JRDB.

The caller fetches each of /tra /tky /tcy /tze /tka exactly once per day.
This pure function joins only redacted aggregates and NEVER scores horses,
creates a real bet, returns horse identities or persists licensed data.

It deliberately does not accept browser-supplied "verified" flags: until an
independent JRA source and a validated real evaluator exist, every race holds.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import audit_evidence_coverage, _valid_date
from jrdb_race_day_gates import audit_race_day_checks

VERSION = "private-day-pipeline-1"
SOURCE_NAMES = ("tra", "tky", "tcy", "tze", "tka")


def inspect_day(programme, entries, training, recent, conditions, racedate):
    """Return an owner-only source-readiness report for 0..120 real races.

    The five inputs must already be fetched by a private authenticated server
    and belong to one date. All error handling is fail-closed in the caller.
    """
    if not _valid_date(racedate):
        raise CoverageError("Invalid calendar date")
    evidence = audit_evidence_coverage(
        programme, entries, training, recent, racedate
    )
    race_day = audit_race_day_checks(
        programme, entries, conditions, racedate
    )
    if (evidence.get("raceCount") != race_day.get("raceCount")
            or evidence["raceCount"] > 120):
        raise CoverageError("Race count mismatch in day-wide snapshots")

    source_races = {}
    for row in race_day["races"]:
        if not isinstance(row, dict):
            raise CoverageError("Invalid race-day audit row")
        coord = (row.get("track"), row.get("race"))
        if coord in source_races:
            raise CoverageError("Ambiguous race-day coordinate")
        source_races[coord] = row
    if len(source_races) != evidence["raceCount"]:
        raise CoverageError("Race-day audits do not match")

    summary = {
        "matchedEntryCountRaces": 0,
        "missingTrainingRecords": 0,
        "missingLastWeekRecords": 0,
        "missingRecentRecords": 0,
        "sourceGoingRecordedRaces": 0,
        "providerWithdrawalRaces": 0,
        "independentOfficialChecks": 0,
        "realPredictions": 0,
    }
    rows = []
    for evidence_row in evidence["races"]:
        key = (evidence_row["track"], evidence_row["race"])
        source = source_races.pop(key, None)
        if source is None:
            raise CoverageError("Missing race-day status")
        n = evidence_row["observedEntries"]
        if (type(n) is not int or n < 0 or n > 18
                or source["observedEntries"] != n):
            raise CoverageError("Entry count differs between source checks")
        for field in ("trainingUnaccounted", "lastWeekUnaccounted",
                      "pastRunUnaccounted"):
            count = evidence_row[field]
            if type(count) is not int or not 0 <= count <= n:
                raise CoverageError("Invalid evidence gap count")
        if (source.get("finalRaceReady") is not False
                or source.get("predictionReady") is not False
                or source.get("bettingReady") is not False
                or source.get("officialStarterListVerified") is not False
                or source.get("officialGoingVerified") is not False
                or evidence_row.get("predictionsReady") is not False):
            raise CoverageError("Unverified source promoted to real prediction")
        matches = source["providerEntryCountMatches"]
        going = source["sourceGoingRecorded"]
        withdrawal = source["providerWithdrawnCount"] > 0
        if any(type(v) is not bool for v in (matches, going, withdrawal)):
            raise CoverageError("Invalid source status")
        summary["matchedEntryCountRaces"] += int(matches)
        summary["sourceGoingRecordedRaces"] += int(going)
        summary["providerWithdrawalRaces"] += int(withdrawal)
        summary["missingTrainingRecords"] += evidence_row["trainingUnaccounted"]
        summary["missingLastWeekRecords"] += evidence_row["lastWeekUnaccounted"]
        summary["missingRecentRecords"] += evidence_row["pastRunUnaccounted"]
        rows.append({
            "track": key[0], "race": key[1],
            "postTimeFromProvider": evidence_row.get("post_time"),
            "registered": n,
            "expected": evidence_row["expectedRunners"],
            "entryCountMatches": matches,
            "trainingUnaccounted": evidence_row["trainingUnaccounted"],
            "lastWeekUnaccounted": evidence_row["lastWeekUnaccounted"],
            "recentUnaccounted": evidence_row["pastRunUnaccounted"],
            "providerWithdrawalPresent": withdrawal,
            "providerWithdrawalFlagsUnknown":
                source["withdrawalFlagUnknownCount"] > 0,
            "sourceGoingRecorded": going,
            "independentJraVerified": False,
            "gradedFactors": 0,
            "realPredictionReady": False,
            "ticketReady": False,
            "blockers": [
                "独立したJRA公式の取消・馬場・発走時刻の照合待ち",
                "10項目の実データ評価・検証待ち",
                "本人専用の実戦予想生成・記録連携待ち",
            ],
        })
    if source_races:
        raise CoverageError("Extra unpaired race-day snapshots")
    rows.sort(key=lambda r: (r["postTimeFromProvider"] or "99:99",
                             r["track"], r["race"]))
    return {
        "version": VERSION,
        "date": racedate,
        "raceCount": len(rows),
        "sourceRequestsRequired": list(SOURCE_NAMES),
        "sourceRequestCount": len(SOURCE_NAMES),
        "summary": summary,
        "races": rows,
        "realPredictionReady": False,
        "purchaseReady": False,
        "rawHorseRecordsIncluded": False,
        "note": (
            "1開催日の番組・出走登録・調教・1週前・近走・馬場の資料件数を"
            "5種類のJRDB取得から一括照合。登録頭数の一致は公式の出走確定ではありません。"
            "実馬の総合S/A/B/C・3連単・購入記録は作成せず、個別有料資料も返しません。"
        ),
    }
