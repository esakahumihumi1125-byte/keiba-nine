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
from jrdb_training_hypothesis import build_training_hints, summarize_training_hints
from jrdb_recent_hypothesis import build_recent_hints, summarize_recent_hints
from jrdb_dual_factor_readiness import summarize_dual_factor_readiness
from jrdb_private_factor_bridge import build_private_factor_matrix, summarize_factor_materials
from jrdb_entry_rotation_materials import (
    enrich_entry_materials_matrix, summarize_entry_materials_matrix,
)
from jrdb_personnel_body_materials import (
    enrich_personnel_body_matrix, summarize_personnel_body_matrix,
)

VERSION = "selected-race-readiness-5"


def _only(rows, track, race):
    matches = [r for r in rows if r.get("track") == track and r.get("race") == race]
    if len(matches) != 1:
        raise CoverageError("Selected race missing or ambiguous")
    return matches[0]


def _scope_selected_race(programme, entries, training, previous, holding,
                         track, race):
    """Restrict a single-race check to its own provider keys in private memory.

    All source lists remain unmodified, ambiguous selected races still fail.
    Other races on the day cannot corrupt the selected-race evidence report.
    This is NOT a confirmed starter list or an official JRA verification.
    """
    if not isinstance(programme, list):
        raise CoverageError("Invalid programme collection")
    matches = [r for r in programme if isinstance(r, dict)
               and r.get("track") == track and r.get("race") == race]
    if len(matches) != 1:
        raise CoverageError("Selected race missing or ambiguous")
    selected = matches[0]
    key = selected.get("racekey")
    if not isinstance(key, str) or len(key) != 8:
        raise CoverageError("Selected race has no valid key")
    collections = (entries, training, previous, holding)
    if not all(isinstance(rows, list) for rows in collections):
        raise CoverageError("Invalid selected-race source collection")
    if not all(isinstance(row, dict) for rows in collections for row in rows):
        raise CoverageError("Malformed selected-race source row")
    # Rows with no race key are never treated as verified target evidence.
    scope = lambda rows: [row for row in rows if row.get("racekey") == key]
    track_prefix = key[:2]
    venues = [row for row in holding
              if isinstance(row.get("holdingkey"), str)
              and row["holdingkey"].startswith(track_prefix)]
    return [selected], scope(entries), scope(training), scope(previous), venues


def selected_race_readiness(
    programme, entries, training, previous, holding, date, track, race, checked_at,
    *, diagnostic=None
):
    """Return ONLY selected-race aggregates and permanent non-ready flags.

    A record-count match cannot validate source rights, official JRA conditions,
    runner identity completeness, workout quality or a horse's relative ability.
    """
    if not _valid_date(date) or track not in TRACKS.values() or type(race) is not int or not 1 <= race <= 12:
        raise CoverageError("Invalid selected race coordinates")
    if diagnostic is not None:
        diagnostic["stage"] = "source_selection"
    programme, entries, training, previous, holding = _scope_selected_race(
        programme, entries, training, previous, holding, track, race
    )
    if diagnostic is not None:
        diagnostic["stage"] = "evidence_and_entries"
    evidence = audit_evidence_coverage(programme, entries, training, previous, date)
    if diagnostic is not None:
        diagnostic["stage"] = "provider_day_status"
    day = audit_race_day_checks(programme, entries, holding, date)
    if diagnostic is not None:
        diagnostic["stage"] = "venue_freshness"
    freshness = audit_prestart_freshness(programme, holding, date, checked_at)
    if diagnostic is not None:
        diagnostic["stage"] = "training_coverage"
    training_hints = build_training_hints(programme, entries, training, date)
    if diagnostic is not None:
        diagnostic["stage"] = "recent_coverage"
    recent_hints = build_recent_hints(programme, entries, previous, date)
    if diagnostic is not None:
        diagnostic["stage"] = "factor_pairing"
    paired = summarize_dual_factor_readiness(training_hints, recent_hints)
    # These are separate, UNVALIDATED source-factor distributions, never
    # overall grades or per-horse records. Counts are owner-visible only.
    train_distribution = _only(
        summarize_training_hints(training_hints)["races"], track, race
    )["gradeCounts"]
    recent_distribution = _only(
        summarize_recent_hints(recent_hints)["races"], track, race
    )["gradeCounts"]
    if diagnostic is not None:
        diagnostic["stage"] = "factor_matrix"
    factor_matrix = build_private_factor_matrix(training_hints, recent_hints)
    if diagnostic is not None:
        diagnostic["stage"] = "factor_summary"
    factors = summarize_factor_materials(factor_matrix)
    if diagnostic is not None:
        diagnostic["stage"] = "entry_materials"
    entry_matrix = enrich_entry_materials_matrix(
        factor_matrix, programme, entries, previous, date
    )
    if diagnostic is not None:
        diagnostic["stage"] = "entry_summary"
    entry_materials = summarize_entry_materials_matrix(entry_matrix)
    if diagnostic is not None:
        diagnostic["stage"] = "personnel_materials"
    personnel_body = summarize_personnel_body_matrix(
        enrich_personnel_body_matrix(entry_matrix, programme, entries, date)
    )
    if diagnostic is not None:
        diagnostic["stage"] = "cross_source_validation"
    if (evidence["raceCount"] != day["raceCount"]
            or evidence["raceCount"] != freshness["raceCount"]
            or evidence["raceCount"] != len(paired["races"])
            or evidence["raceCount"] != factors["raceCount"]
            or evidence["raceCount"] != entry_materials["raceCount"]
            or evidence["raceCount"] != personnel_body["raceCount"]
            or personnel_body["predictionReady"] is not False
            or personnel_body["bettingReady"] is not False
            or entry_materials["predictionReady"] is not False
            or entry_materials["bettingReady"] is not False
            or paired["predictionReady"] is not False
            or factors["predictionReady"] is not False
            or factors["bettingReady"] is not False):
        raise CoverageError("Cross-source race count mismatch")
    a = _only(evidence["races"], track, race)
    b = _only(day["races"], track, race)
    c = _only(freshness["races"], track, race)
    d = _only(paired["races"], track, race)
    e = _only(factors["races"], track, race)
    f = _only(entry_materials["races"], track, race)
    g = _only(personnel_body["races"], track, race)
    n = a["observedEntries"]
    if (type(n) is not int or not 0 <= n <= 18
            or d["runnerCount"] != n or d["predictionReady"] is not False
            or d["coreFactorsStillUnverified"] is not True
            or d["remainingFactors"] != 8
            or e["runnerCount"] != n
            or f["runnerCount"] != n
            or g["runnerCount"] != n
            or g["observedFactorSlots"] != 8
            or g["unmappedFactorCount"] != 2
            or g["verifiedFactorCount"] != 0
            or g["jockeyTrainerPerformanceAssessed"] is not False
            or g["bodyConditionAssessed"] is not False
            or g["raceDayBodyWeightFetched"] is not False
            or g["overallRankReady"] is not False
            or g["predictionReady"] is not False
            or g["bettingReady"] is not False
            or f["observedFactorSlots"] != 6
            or f["unmappedFactorCount"] != 4
            or f["verifiedFactorCount"] != 0
            or f["pedigreeAptitudeAssessed"] is not False
            or f["drawWeightEffectAssessed"] is not False
            or f["rotationEffectAssessed"] is not False
            or f["overallRankReady"] is not False
            or f["predictionReady"] is not False
            or f["bettingReady"] is not False
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
    labels = {"S", "A", "B", "C", "未評価"}
    if (set(train_distribution) != labels or set(recent_distribution) != labels
            or any(type(x) is not int or not 0 <= x <= n
                   for x in (*train_distribution.values(), *recent_distribution.values()))
            or sum(train_distribution.values()) != n
            or sum(recent_distribution.values()) != n
            or n - train_distribution["未評価"] != d["both"] + d["trainingOnly"]
            or n - recent_distribution["未評価"] != d["both"] + d["recentOnly"]):
        raise CoverageError("Experimental factor grade distributions disagree")
    entry_counts = f["entryObservations"]
    interval_counts = f["rotationIntervals"]
    nkeys = ("sireRecorded", "maternalSireRecorded", "bothPedigreeRecorded",
             "bracketRecorded", "weightRecorded", "drawAndWeightRecorded")
    buckets = ("under14Days", "days14to55", "days56plus", "unknown")
    if (set(entry_counts) != set(nkeys) or set(interval_counts) != set(buckets)
            or any(type(entry_counts[k]) is not int or not 0 <= entry_counts[k] <= n
                   for k in nkeys)
            or any(type(interval_counts[k]) is not int
                   or not 0 <= interval_counts[k] <= n for k in buckets)
            or sum(interval_counts.values()) != n
            or entry_counts["bothPedigreeRecorded"]
               > min(entry_counts["sireRecorded"], entry_counts["maternalSireRecorded"])
            or entry_counts["drawAndWeightRecorded"]
               > min(entry_counts["bracketRecorded"], entry_counts["weightRecorded"])):
        raise CoverageError("Documented entry/rotation coverage is inconsistent")
    pc = g["recorded"]
    pc_keys = (
        "jockeyNameRecorded", "jockeyCodeRecorded", "trainerNameRecorded",
        "trainerCodeRecorded", "bothPersonnelNamesRecorded",
        "bodyTypeRecorded", "integrationCodeRecorded", "anyConformationRecorded",
    )
    if (not isinstance(pc, dict) or set(pc) != set(pc_keys)
            or any(type(pc[k]) is not int or not 0 <= pc[k] <= n for k in pc_keys)
            or pc["bothPersonnelNamesRecorded"] >
               min(pc["jockeyNameRecorded"], pc["trainerNameRecorded"])
            or pc["anyConformationRecorded"] <
               max(pc["bodyTypeRecorded"], pc["integrationCodeRecorded"])
            or pc["anyConformationRecorded"] >
               pc["bodyTypeRecorded"] + pc["integrationCodeRecorded"]):
        raise CoverageError("Personnel/body record presence counts are inconsistent")
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
        "experimentalGradeDistributions": {
            "training": dict(train_distribution),
            "recent": dict(recent_distribution),
            "experimental": True,
            "overallRankReady": False,
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
        "entryMaterials": {
            "entryObservations": entry_counts,
            "rotationIntervals": interval_counts,
            "observedFactorSlots": 6,
            "unmappedFactors": 4,
            "verifiedFactorCount": 0,
            "pedigreeAptitudeAssessed": False,
            "drawWeightEffectAssessed": False,
            "rotationEffectAssessed": False,
            "overallRankReady": False,
            "predictionReady": False,
        },
        "personnelBodyMaterials": {
            "recorded": pc,
            "observedFactorSlots": 8, "unmappedFactors": 2,
            "verifiedFactorCount": 0,
            "jockeyTrainerPerformanceAssessed": False,
            "bodyConditionAssessed": False,
            "raceDayBodyWeightFetched": False,
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
            "父・母父・枠・斤量・前走間隔に加えて騎手・厩舎・馬体形状の"
            "記録有無も接続（馬体重と当日の状態は未取得）。"
            "調教と近走の閾値は未検証で、残り8項目も未評価。"
            "JRA公式の出走馬・取消・馬場・発走時刻は独立照合していません。"
            "10項目の総合評価や3連単・馬券購入には利用できません。"
        ),
    }
