"""Owner-only 36R orchestration for *future* independently verified ten-factor input.

This is deliberately NOT connected to JRDB, JRA, HTTP, scheduled jobs or the
existing two-factor ticket service. Each race is assessed separately; one
malformed or late internal snapshot must not invent tickets or destroy other
races' research results. This consumes no paid data and changes no receipts.
"""
import re
from datetime import date, timedelta, timezone

from jrdb_coverage import CoverageError
from evaluation_policy import OWNER_FORMAL_FACTORS as FACTORS
from jrdb_program_preview import TRACKS
from owner_full_ten_factor import full_ten_factor_preview, _clock, _empty
from owner_formal_assessment_input import validate_formal_assessment_snapshot

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


def full_ten_day_research(day, race_snapshots, *, now, expected_coordinates=None):
    """Fail closed per race, with a strict unambiguous venue/R index.

    The result is PRIVATE RESEARCH. Flags inside a passed snapshot do not
    independently authenticate JRA and never authorize any real purchases.
    This helper must not be exposed as an HTTP endpoint that accepts client
    supplied assessments or official-verification flags.
    An optional independently supplied schedule coordinate list keeps absent
    snapshots visible. It is an inventory check, NOT proof of official origin.
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

    expected = None
    if expected_coordinates is not None:
        if (not isinstance(expected_coordinates, list)
                or len(expected_coordinates) > MAX_RACES):
            raise CoverageError("Invalid expected schedule")
        expected = set()
        for item in expected_coordinates:
            if (not isinstance(item, dict) or set(item) != {"track", "race"}
                    or type(item.get("track")) is not str
                    or item["track"] not in TRACK_NAMES
                    or type(item.get("race")) is not int
                    or not 1 <= item["race"] <= 12):
                raise CoverageError("Invalid expected schedule coordinate")
            coord = item["track"], item["race"]
            if coord in expected:
                raise CoverageError("Duplicate expected schedule coordinate")
            expected.add(coord)
        if not seen <= expected:
            raise CoverageError("Snapshot outside expected schedule")
    output = []
    for row in race_snapshots:
        assessment = row["snapshot"]
        try:
            assessment = validate_formal_assessment_snapshot(
                assessment, expected_track=row["track"],
                expected_race=row["race"], day=day,
            )
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
    missing = expected - seen if expected is not None else set()
    for track, race in sorted(missing):
        output.append({
            "track": track, "race": race,
            "status": "missing_internal_snapshot",
            "fullTenResearchRankReady": False,
            "reviewOnlyTicketCount": 0,
            "unassessedHorseCount": 0,
            "preview": _empty("missing_internal_snapshot"),
            "researchOnly": True, "bettingReady": False,
            "purchaseReady": False, "autoPurchase": False,
        })
    # Count only runners that actually reached the scorer in its prestart
    # window. A missing/invalid/expired snapshot has no reliable denominator,
    # and must not be counted as either an assessed horse or a poor score.
    factor_coverage = {
        key: {"weight": weight, "traceableRunnerCount": 0,
              "unassessedRunnerCount": 0, "affectedRaceCount": 0,
              "missingReasonCounts": {}}
        for key, weight in FACTORS.items()
    }
    checked_runners, checked_races = 0, 0
    for row in output:
        preview = row["preview"]
        readiness = preview["factorReadinessByNumber"]
        missing_by_number = preview["missingReasonCodesByNumber"]
        if not readiness:
            continue
        checked_races += 1
        checked_runners += len(readiness)
        affected = set()
        for number in readiness:
            reasons = missing_by_number.get(number, {})
            for key, coverage in factor_coverage.items():
                if key not in reasons:
                    coverage["traceableRunnerCount"] += 1
                    continue
                coverage["unassessedRunnerCount"] += 1
                code = reasons[key]
                totals = coverage["missingReasonCounts"]
                totals[code] = totals.get(code, 0) + 1
                affected.add(key)
        for key in affected:
            factor_coverage[key]["affectedRaceCount"] += 1
    priority = sorted(
        (key for key, item in factor_coverage.items()
         if item["unassessedRunnerCount"]),
        key=lambda key: (-FACTORS[key] * factor_coverage[key]["unassessedRunnerCount"],
                         -FACTORS[key], key),
    )
    ready = sum(r["fullTenResearchRankReady"] for r in output)
    tickets = sum(r["reviewOnlyTicketCount"] > 0 for r in output)
    return {
        "version": VERSION, "date": day, "raceCount": len(output),
        "races": output, "fullTenResearchRankRaces": ready,
        "expectedScheduleProvided": expected is not None,
        "expectedRaceCount": len(expected) if expected is not None else None,
        "receivedSnapshotRaceCount": len(seen),
        "missingSnapshotRaceCount": len(missing) if expected is not None else None,
        "scheduleSnapshotCoverageComplete": seen == expected if expected is not None else None,
        "factorEvidenceCoverage": {
            "checkedRaceCount": checked_races,
            "uncheckedRaceCount": len(output) - checked_races,
            "checkedRunnerCount": checked_runners,
            "byFactor": factor_coverage,
            "missingEvidencePriority": priority,
            "coverageIsNotAbilityScore": True,
        },
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
