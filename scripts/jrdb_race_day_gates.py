"""Owner-only race-day SOURCE-status checks, never official JRA confirmation.

Use normalized /tra, /tky and /tka records in memory. JRDB /tky's
withdrawn_flag is a provider-reported signal, NOT an independently verified
starter list. No horse numbers, identities, flags or raw provider rows are
returned; do not treat any result as authority to buy a ticket.
"""
from jrdb_coverage import audit_race_coverage, CoverageError
from jrdb_race_context import audit_race_context, RaceContextError

VERSION = "race-day-source-gates-1"


def audit_race_day_checks(programme, entries, current_conditions, requested_date):
    """Bounded redacted race-level status with explicit official-review blockers."""
    coverage = audit_race_coverage(programme, entries, requested_date)
    context = audit_race_context(programme, current_conditions, requested_date)
    program_by_key = {(r["track"], r["race"]): r for r in programme}
    if len(program_by_key) != len(programme):
        raise CoverageError("Ambiguous programme races")
    context_by_key = {(r["track"], r["race"]): r for r in context["races"]}
    if set(program_by_key) != set(context_by_key):
        raise CoverageError("Course context does not match programme")
    counters = {r["racekey"]: {"active": 0, "withdrawn": 0, "unknown": 0}
                for r in programme}
    for row in entries:
        # audit_race_coverage already verified race/date/number and duplicates.
        value = row.get("withdrawn_flag")
        bucket = counters[row["racekey"]]
        if value is None or value == "":
            bucket["unknown"] += 1
        elif type(value) is not str or value not in ("0", "1"):
            # Never map unfamiliar provider flags into "not withdrawn".
            raise CoverageError("Unsupported withdrawal code")
        elif value == "1":
            bucket["withdrawn"] += 1
        else:
            bucket["active"] += 1
    result = []
    for race in coverage["races"]:
        name, number = race["track"], race["race"]
        current = program_by_key[name, number]
        status = context_by_key[name, number]
        total = race["observedEntries"]
        flags = counters[current["racekey"]]
        if total != sum(flags.values()):
            raise CoverageError("Withdrawal indicators do not match entries")
        declared = race["expectedRunners"]
        blocks = ["JRA公式の出走取消・除外・発走時刻と馬場を最終照合"]
        if declared is None or declared != total:
            blocks.append("番組と登録馬の頭数を再照合")
        if flags["unknown"]:
            blocks.append("提供元の取消フラグに未確認あり")
        if flags["withdrawn"]:
            blocks.append("提供元で取消報告あり・JRA公式と再照合")
        if not status["goingAvailable"]:
            blocks.append("当日の芝・ダート馬場を確認")
        if not status["conditionUpdateRecorded"]:
            blocks.append("馬場情報の更新日時が未確認")
        if not race.get("post_time"):
            blocks.append("発走時刻の存在を確認")
        result.append({
            "track": name, "race": number,
            "observedEntries": total,
            "expectedRunners": declared,
            "providerNonWithdrawnCount": flags["active"],
            "providerWithdrawnCount": flags["withdrawn"],
            "withdrawalFlagUnknownCount": flags["unknown"],
            "withdrawalFlagCoverageComplete": flags["unknown"] == 0 and total > 0,
            "providerEntryCountMatches": declared is not None and declared == total,
            "sourcePostTimeRecorded": bool(race.get("post_time")),
            "sourceGoingRecorded": status["goingAvailable"],
            "sourceGoingUpdateTimeRecorded": status["conditionUpdateRecorded"],
            "sourceGoing": status["going"],
            "officialStarterListVerified": False,
            "officialScratchesVerified": False,
            "officialGoingVerified": False,
            "officialPostTimeVerified": False,
            "finalRaceReady": False,
            "predictionReady": False,
            "bettingReady": False,
            "blockingChecks": blocks,
        })
    return {
        "version": VERSION, "raceCount": len(result),
        "racesWithProviderWithdrawal": sum(r["providerWithdrawnCount"] > 0
                                           for r in result),
        "racesWithUnknownFlags": sum(r["withdrawalFlagUnknownCount"] > 0
                                     for r in result),
        "racesWithSourceGoing": sum(r["sourceGoingRecorded"] for r in result),
        "racesWithOfficialFinalCheck": 0,
        "predictionReady": False,
        "bettingReady": False,
        "races": result,
        "note": ("JRDBの出走取消フラグ・頭数・芝ダート馬場・発走時刻の"
                 "資料確認。提供元の0は公式確定を意味しません。"
                 "JRA公式の取消・馬場・発走時刻、更新時刻の最新性、"
                 "除外・競走中止等の最終確認は未実施。"
                 "馬券の買い目・実戦予想は生成しません。"),
    }
