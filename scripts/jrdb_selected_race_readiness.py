"""Owner-only selected-race evidence status assembled from a single source snapshot.

Use only normalized programme data and provider rows held in private memory.
Exports bounded aggregate counts, NEVER horse identities, private race keys,
source metrics, raw timestamps, scores, predictions, or betting instructions.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import audit_evidence_coverage, _valid_date
from jrdb_race_day_gates import audit_race_day_checks
from jrdb_prestart_freshness import audit_prestart_freshness
from jrdb_program_preview import TRACKS
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_dual_factor_readiness import summarize_dual_factor_readiness
from jrdb_private_factor_bridge import build_private_factor_matrix, summarize_factor_materials

VERSION = "selected-race-readiness-3"


def _only(rows, track, race):
    matches = [r for r in rows if r.get("track") == track and r.get("race") == race]
    if len(matches) != 1:
        raise CoverageError("Selected race missing or ambiguous")
    return matches[0]


def selected_race_readiness(
    programme, entries, training, previous, holding, date, track, race, checked_at
):
    """Return ONLY selected-race aggregates and permanent non-ready flags.

    A record-count match cannot validate source rights, official JRA conditions,
    runner identity completeness, workout quality or a horse's relative ability.
    """
    if not _valid_date(date) or track not in TRACKS.values() or type(race) is not int or not 1 <= race <= 12:
        raise CoverageError("Invalid selected race coordinates")
    evidence = audit_evidence_coverage(programme, entries, training, previous, date)
    day = audit_race_day_checks(programme, entries, holding, date)
    freshness = audit_prestart_freshness(programme, holding, date, checked_at)
    training_hints = build_training_hints(programme, entries, training, date)
    recent_hints = build_recent_hints(programme, entries, previous, date)
    paired = summarize_dual_factor_readiness(training_hints, recent_hints)
    factors = summarize_factor_materials(
        build_private_factor_matrix(training_hints, recent_hints)
    )
    if (evidence["raceCount"] != day["raceCount"]
            or evidence["raceCount"] != freshness["raceCount"]
            or evidence["raceCount"] != len(paired["races"])
            or evidence["raceCount"] != factors["raceCount"]
            or paired["predictionReady"] is not False
            or factors["predictionReady"] is not False
            or factors["bettingReady"] is not False):
        raise CoverageError("Cross-source race count mismatch")
    a = _only(evidence["races"], track, race)
    b = _only(day["races"], track, race)
    c = _only(freshness["races"], track, race)
    d = _only(paired["races"], track, race)
    e = _only(factors["races"], track, race)
    n = a["observedEntries"]
    if (type(n) is not int or not 0 <= n <= 18
            or d["runnerCount"] != n or d["predictionReady"] is not False
            or d["coreFactorsStillUnverified"] is not True
            or d["remainingFactors"] != 8
            or e["runnerCount"] != n
            or e["verifiedFactorCount"] != 0
            or e["unmappedFactorCount"] != 7
            or e["paceForecastAvailable"] is not False
            or e["overallRankReady"] is not False
            or e["predictionReady"] is not False
            or e["bettingReady"] is not False
            or e["mappedFactors"] != ["training", "recent"]
            or e["observationOnlyFactors"] != ["pace"]
            or b["observedEntries"] != n
            or a["rosterVerified"] is not False
            or a["predictionsReady"] is not False
            or b["predictionReady"] is not False
            or b["bettingReady"] is not False
            or b["officialScratchesVerified"] is not False
            or b["officialGoingVerified"] is not False
            or c["jraOfficialDataFetched"] is not False
            or c["jraScratchesVerified"] is not False
            or c["jraGoingVerified"] is not False
            or c["jraPostTimeVerified"] is not False):
        raise CoverageError("Unverified race state is inconsistent")

    count_keys = (
        "trainingUnaccounted", "lastWeekUnaccounted", "pastRunUnaccounted",
    )
    if any(type(a[k]) is not int or not 0 <= a[k] <= n for k in count_keys):
        raise CoverageError("Evidence counts exceed runner count")
    for key in ("providerWithdrawnCount", "withdrawalFlagUnknownCount"):
        if type(b[key]) is not int or not 0 <= b[key] <= n:
            raise CoverageError("Invalid provider withdrawal aggregate")
    if b["providerWithdrawnCount"] + b["withdrawalFlagUnknownCount"] > n:
        raise CoverageError("Provider withdrawal totals exceed entries")
    counts = (
        "both", "trainingOnly", "recentOnly", "neither",
        "sameGrade", "trainingHigher", "recentHigher",
        "largeDisagreement", "bothHigh",
    )
    if any(type(d[name]) is not int or not 0 <= d[name] <= n for name in counts):
        raise CoverageError("Invalid research factor comparison counts")
    if (sum(d[name] for name in ("both", "trainingOnly", "recentOnly", "neither")) != n
            or d["sameGrade"] + d["trainingHigher"] + d["recentHigher"] != d["both"]
            or d["largeDisagreement"] > d["both"]
            or d["bothHigh"] > d["both"]):
        raise CoverageError("Inconsistent paired research coverage")
    position = e["pastFourthCorner"]
    if (not isinstance(position, dict)
            or set(position) != {
                "frontObserved", "backObserved", "mixedObserved", "insufficient",
            }
            or any(type(value) is not int or not 0 <= value <= n
                   for value in position.values())
            or sum(position.values()) != n):
        raise CoverageError("Historical position coverage is inconsistent")
    if (e["provisionalGradeCounts"].get("trainingProvisional")
            != d["both"] + d["trainingOnly"]
            or e["provisionalGradeCounts"].get("recentProvisional")
            != d["both"] + d["recentOnly"]):
        raise CoverageError("Factor-grade inputs differ between research summaries")
    if c["prestartWindow"] not in (
        "post_time_unknown", "other_date", "post_time_passed",
        "within_two_hours", "more_than_two_hours",
    ):
        raise CoverageError("Unknown prestart window")
    if c["sourceGoingAgeStatus"] not in (
        "no_going_report", "no_update_timestamp", "timestamp_in_future",
        "recent_reported", "old_or_other_date_reported",
    ):
        raise CoverageError("Unknown reported source timestamp status")
    going = b["sourceGoing"]
    if going not in ("良", "稍重", "重", "不良", "未確認"):
        raise CoverageError("Invalid summarized going")
    return {
        "version": VERSION,
        "date": date, "track": track, "race": race,
        "observedEntries": n,
        "expectedRunners": a["expectedRunners"],
        "entryCountMatchesSource": b["providerEntryCountMatches"] is True,
        "trainingUnaccounted": a["trainingUnaccounted"],
        "lastWeekUnaccounted": a["lastWeekUnaccounted"],
        "pastRunUnaccounted": a["pastRunUnaccounted"],
        "providerWithdrawnCount": b["providerWithdrawnCount"],
        "withdrawalFlagUnknownCount": b["withdrawalFlagUnknownCount"],
        "sourceGoing": going,
        "sourceGoingAgeStatus": c["sourceGoingAgeStatus"],
        "prestartWindow": c["prestartWindow"],
        "factorResearch": {
            "bothGraded": d["both"],
            "trainingOnly": d["trainingOnly"],
            "recentOnly": d["recentOnly"],
            "neither": d["neither"],
            "sameGrade": d["sameGrade"],
            "trainingHigher": d["trainingHigher"],
            "recentHigher": d["recentHigher"],
            "largeDisagreement": d["largeDisagreement"],
            "bothHigh": d["bothHigh"],
            "remainingFactors": 8,
            "experimental": True,
            "predictionReady": False,
        },
        "factorMaterials": {
            "pastFourthCorner": position,
            "trainingProvisional": e["provisionalGradeCounts"]["trainingProvisional"],
            "recentProvisional": e["provisionalGradeCounts"]["recentProvisional"],
            "observedFactors": 3,
            "verifiedFactorCount": 0,
            "unmappedFactors": 7,
            "paceForecastAvailable": False,
            "overallRankReady": False,
            "predictionReady": False,
        },
        "sourceSnapshotNotOfficial": True,
        "independentJraConnected": False,
        "officialJraFinalVerification": False,
        "gradedFactors": 0,
        "predictionReady": False,
        "bettingReady": False,
        "note": (
            "提供元の件数・取消報告・馬場の資料状態と調教・近走の"
            "暫定評価が一致・不一致の頭数を1R分まとめました。"
            "過去4角位置も展開材料として集計するが脚質・ペースは未予測。"
            "調教と近走の閾値は未検証で、残り8項目も未評価。"
            "JRA公式の出走馬・取消・馬場・発走時刻は独立照合していません。"
            "10項目の総合評価や3連単・馬券購入には利用できません。"
        ),
    }
