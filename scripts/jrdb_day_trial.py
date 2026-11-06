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
from jrdb_private_factor_bridge import build_private_factor_matrix, summarize_factor_materials
from jrdb_entry_rotation_materials import enrich_entry_materials_matrix, summarize_entry_materials_matrix
from jrdb_personnel_body_materials import enrich_personnel_body_matrix, summarize_personnel_body_matrix

VERSION = "owner-day-two-factor-trial-2"


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
    # Extend the SAME vetted /tra /tky /tcy /tze snapshot with objective
    # material-presence observations. This does NOT add rankings or API calls.
    matrix = build_private_factor_matrix(train, past)
    base = summarize_factor_materials(matrix)
    pedigree_matrix = enrich_entry_materials_matrix(
        matrix, programme, entries, recent, date
    )
    pedigree = summarize_entry_materials_matrix(pedigree_matrix)
    personnel = summarize_personnel_body_matrix(
        enrich_personnel_body_matrix(pedigree_matrix, programme, entries, date)
    )
    def _index(summary, label):
        if (summary.get("raceCount") != len(programme)
                or summary.get("predictionReady") is not False
                or summary.get("bettingReady") is not False):
            raise CoverageError("Unverified " + label + " material counts")
        indexed = {}
        for item in summary.get("races", []):
            coord = (item.get("track"), item.get("race"))
            if coord in indexed:
                raise CoverageError("Duplicate " + label + " material race")
            indexed[coord] = item
        if set(indexed) != coords:
            raise CoverageError("Missing " + label + " material race")
        return indexed
    base_by = _index(base, "form")
    pedigree_by = _index(pedigree, "entry")
    personnel_by = _index(personnel, "personnel")
    results = []
    for row in programme:
        r = build_one_race_trial(programme, entries, training, recent, date,
                                 row["track"], row["race"], hints=(train, past))
        if (r["version"] != ONE_R_VERSION or r["predictionReady"] is not False
                or r["bettingReady"] is not False or r["autoTicketReady"] is not False):
            raise CoverageError("Non-research result in shared day snapshot")
        coord = row["track"], row["race"]
        a, b, c = (base_by[coord], pedigree_by[coord], personnel_by[coord])
        n = r["runnersObserved"]
        if (any(x.get("runnerCount") != n for x in (a, b, c))
                or any(x.get("verifiedFactorCount") != 0 for x in (a, b, c))
                or any(x.get("overallRankReady") is not False for x in (a, b, c))
                or a.get("paceForecastAvailable") is not False
                or b.get("pedigreeAptitudeAssessed") is not False
                or b.get("drawWeightEffectAssessed") is not False
                or b.get("rotationEffectAssessed") is not False
                or c.get("jockeyTrainerPerformanceAssessed") is not False
                or c.get("bodyConditionAssessed") is not False):
            raise CoverageError("Material counts do not establish readiness")
        counts = {
            "training": a["provisionalGradeCounts"]["trainingProvisional"],
            "recent": a["provisionalGradeCounts"]["recentProvisional"],
            "pace": n - a["pastFourthCorner"]["insufficient"],
            "pedigree": b["entryObservations"]["bothPedigreeRecorded"],
            "draw_weight": b["entryObservations"]["drawAndWeightRecorded"],
            "rotation": n - b["rotationIntervals"]["unknown"],
            "jockey_stable": c["recorded"]["bothPersonnelNamesRecorded"],
            "body_condition": c["recorded"]["anyConformationRecorded"],
            "course_distance": 0,
            "ground": 0,
        }
        if (set(counts) != {
                "training", "recent", "pace", "pedigree",
                "draw_weight", "rotation", "jockey_stable",
                "body_condition", "course_distance", "ground"
            } or any(type(count) is not int or count < 0 or count > n
                     for count in counts.values())):
            raise CoverageError("Invalid ten-factor material coverage")
        r["factorCoverage"] = {
            "observedRunnerCount": n,
            "materialCountByFactor": counts,
            "experimentalFactors": ["training", "recent"],
            "observationOnlyFactors": [
                "pace", "pedigree", "draw_weight", "rotation",
                "jockey_stable", "body_condition"
            ],
            "uncheckedFactors": ["course_distance", "ground"],
            "verifiedAbilityFactors": 0,
            "notOverallGrades": True,
            "note": ("資料記録がある頭数のみ。血統適性・展開予測・"
                     "騎手評価・当日の馬体状態などの能力評価は未実施。"),
        }
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
                    "残り8項目未評価。資料の存在は能力の証明ではありません。"
                    "実戦予想・買い目は未作成です。"),
    }
