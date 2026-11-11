"""Owner-only 36R orchestration for *future* independently verified ten-factor input.

This is deliberately NOT connected to JRDB, JRA, HTTP, scheduled jobs or the
existing two-factor ticket service. Each race is assessed separately; one
malformed or late internal snapshot must not invent tickets or destroy other
races' research results. This consumes no paid data and changes no receipts.
"""
import re
from datetime import date, timedelta, timezone

from evaluation_policy import timestamp
from jrdb_coverage import CoverageError
from jrdb_program_preview import TRACKS
from owner_full_ten_factor import full_ten_factor_preview, _clock, _empty

VERSION = "owner-full-ten-day-gate-1"
JST = timezone(timedelta(hours=9))
TRACK_NAMES = frozenset(TRACKS.values())
MAX_RACES = 36


def _day(value):
    if type(value) is not str or re.fullmatch(r"20[0-9]{6}", value) is None:
        raise CoverageError("Invalid day assessment date")
    try:
        parsed = date(int(value[:4]), int(value[4:6]), int(value[6:]))
    except ValueError:
        raise CoverageError("Invalid day assessment date") from None
    if parsed.strftime("%Y%m%d") != value:
        raise CoverageError("Invalid day assessment date")
    return value


def full_ten_day_research(day, race_snapshots, *, now):
    """Fail closed per race, with a strict unambiguous venue/R index.

    The result is PRIVATE RESEARCH. Flags inside a passed snapshot do not
    independently authenticate JRA and never authorize any real purchases.
    This helper must not be exposed as an HTTP endpoint that accepts client
    supplied assessments or official-verification flags.
    """
    _day(day)
    _clock(now)
    if not isinstance(race_snapshots, list) or len(race_snapshots) > MAX_RACES:
        raise CoverageError("Invalid full-ten day race list")
    seen = set()
    for row in race_snapshots:
        if (not isinstance(row, dict)
                or set(row) != {"track", "race", "snapshot"}
                or type(row.get("track")) is not str
                or row["track"] not in TRACK_NAMES
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12):
            raise CoverageError("Invalid full-ten day coordinate")
        coord = row["track"], row["race"]
        if coord in seen:
            raise CoverageError("Duplicate full-ten day coordinate")
        seen.add(coord)

    output = []
    for row in race_snapshots:
        assessment = row["snapshot"]
        try:
            if not isinstance(assessment, dict):
                raise CoverageError("Missing internal full-ten snapshot")
            # Every snapshot must target this day's expected off, even when
            # the pre-race evidence was collected on an earlier day.
            off = timestamp(assessment.get("offAt"))
            if off.astimezone(JST).strftime("%Y%m%d") != day:
                raise CoverageError("Full-ten snapshot belongs to another day")
            preview = full_ten_factor_preview(assessment, now=now)
        except (CoverageError, ValueError, TypeError, KeyError, OverflowError):
            preview = _empty("invalid_internal_snapshot")
        points = preview["trifecta"]["points"]
        if (type(points) is not int or not 0 <= points <= 48
                or not isinstance(preview.get("ranking"), list)
                or (points > 0 and preview["trifecta"]["status"] != "review_only")):
            # A broken internal engine contract is not a betting signal.
            preview = _empty("invalid_internal_snapshot")
            points = 0
        output.append({
            "track": row["track"], "race": row["race"],
            "status": preview["status"],
            "fullTenResearchRankReady": preview["overallReady"],
            "reviewOnlyTicketCount": points,
            "unassessedHorseCount": len(preview["missingByNumber"]),
            "preview": preview,
            "researchOnly": True, "bettingReady": False,
            "purchaseReady": False, "autoPurchase": False,
        })
    ready = sum(r["fullTenResearchRankReady"] for r in output)
    tickets = sum(r["reviewOnlyTicketCount"] > 0 for r in output)
    return {
        "version": VERSION, "date": day, "raceCount": len(output),
        "races": output, "fullTenResearchRankRaces": ready,
        "researchFormationRaces": tickets,
        "heldOrIncompleteRaces": len(output) - tickets,
        "invalidInternalSnapshotRaces": sum(
            r["status"] == "invalid_internal_snapshot" for r in output),
        "unassessedRaceCount": sum(
            r["status"] == "missing_evidence" for r in output),
        "newProviderRequests": 0, "paidSourceRowsIncluded": False,
        "liveJrdbConnectedHere": False, "independentJraFeedConnected": False,
        "officialJraVerified": False, "productionPredictionReady": False,
        "changesFrozenReceipts": False, "actualPurchase": False,
        "autoPurchase": False, "researchOnly": True, "privateOwnerOnly": True,
        "note": (
            "10項目が別系統で事前確認された場合だけ使う内部研究ゲート。"
            "実JRDB・JRAデータの接続、正式予想の配信、投票・公式結果照合は未完成。"
        ),
    }
