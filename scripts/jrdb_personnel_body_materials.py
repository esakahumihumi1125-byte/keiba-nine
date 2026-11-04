"""Private, observation-only /tky jockey, trainer and body-code coverage.

Only provider-documented record presence is inspected. Body conformation codes
are NOT race-day body weight, weight change, condition, paddock assessment,
or a fitness forecast. No live requests, records, storage or public feeds.
"""
from copy import deepcopy

from jrdb_coverage import CoverageError, audit_race_coverage
from jrdb_private_factor_bridge import VERSION as BASE_VERSION
from jrdb_entry_rotation_materials import (
    NO_DATA, summarize_entry_materials_matrix,
)

VERSION = "personnel-body-observations-1"
PERSONNEL = "jockey_stable"
BODY = "body_condition"


def _recorded(row, field):
    value = row.get(field)
    if value is None or value == "":
        return False
    if (not isinstance(value, str) or len(value) > 128
            or any(ord(ch) < 32 or ord(ch) == 127 for ch in value)):
        raise CoverageError("Invalid optional personnel/body format")
    return bool(value.strip())


def enrich_personnel_body_matrix(matrix, programme, entries, date):
    """Only fill previously unmapped slots, strictly matching the private roster."""
    summarize_entry_materials_matrix(matrix)  # fail closed before mutation
    audit_race_coverage(programme, entries, date)
    roster = {(r["racekey"], r["horse_number"]): r for r in entries}
    if len(roster) != len(entries):
        raise CoverageError("Duplicate entry in personnel observation")
    out = deepcopy(matrix)
    if sum(len(r["byNumber"]) for r in out) != len(roster):
        raise CoverageError("Personnel roster size mismatch")
    for race in out:
        key = race["racekey"]
        for number, slots in race["byNumber"].items():
            row = roster.get((key, number))
            if (row is None or slots[PERSONNEL] != NO_DATA
                    or slots[BODY] != NO_DATA):
                raise CoverageError("Unmatched or already assessed runner")
            slots[PERSONNEL] = {
                "grade": "未評価", "basis": "tky_personnel_presence",
                "jockeyNameRecorded": _recorded(row, "jockey_name"),
                "jockeyCodeRecorded": _recorded(row, "jockey_cd"),
                "trainerNameRecorded": _recorded(row, "trainer_name"),
                "trainerCodeRecorded": _recorded(row, "trainer_cd"),
            }
            slots[BODY] = {
                "grade": "未評価", "basis": "tky_conformation_codes_only",
                "bodyTypeRecorded": _recorded(row, "bodytype"),
                "integrationCodeRecorded": any(
                    _recorded(row, "horse_bodytype_integration_cd" + str(i))
                    for i in (1, 2, 3)),
            }
    return out


def summarize_personnel_body_matrix(matrix):
    """Aggregate counts only. No identities, names, codes, weights or grades."""
    if not isinstance(matrix, list) or len(matrix) > 120:
        raise CoverageError("Invalid personnel-body matrix")
    stripped = deepcopy(matrix)
    for race in stripped:
        if not isinstance(race, dict) or not isinstance(race.get("byNumber"), dict):
            raise CoverageError("Invalid personnel-body race")
        for slots in race["byNumber"].values():
            if not isinstance(slots, dict) or PERSONNEL not in slots or BODY not in slots:
                raise CoverageError("Missing personnel/body slots")
            slots[PERSONNEL] = dict(NO_DATA)
            slots[BODY] = dict(NO_DATA)
    base = summarize_entry_materials_matrix(stripped)
    result = []
    for race, baseline in zip(matrix, base["races"]):
        if (race.get("track"), race.get("race")) != (baseline["track"], baseline["race"]):
            raise CoverageError("Personnel-body race ordering mismatch")
        n = baseline["runnerCount"]
        counts = dict.fromkeys((
            "jockeyNameRecorded", "jockeyCodeRecorded",
            "trainerNameRecorded", "trainerCodeRecorded",
            "bothPersonnelNamesRecorded",
            "bodyTypeRecorded", "integrationCodeRecorded",
            "anyConformationRecorded",
        ), 0)
        for slots in race["byNumber"].values():
            p, body = slots[PERSONNEL], slots[BODY]
            if (not isinstance(p, dict) or not isinstance(body, dict)
                    or set(p) != {"grade", "basis", "jockeyNameRecorded",
                                  "jockeyCodeRecorded", "trainerNameRecorded",
                                  "trainerCodeRecorded"}
                    or set(body) != {"grade", "basis", "bodyTypeRecorded",
                                     "integrationCodeRecorded"}
                    or p["grade"] != "未評価" or body["grade"] != "未評価"
                    or p["basis"] != "tky_personnel_presence"
                    or body["basis"] != "tky_conformation_codes_only"
                    or any(type(p[k]) is not bool for k in (
                        "jockeyNameRecorded", "jockeyCodeRecorded",
                        "trainerNameRecorded", "trainerCodeRecorded"))
                    or any(type(body[k]) is not bool for k in (
                        "bodyTypeRecorded", "integrationCodeRecorded"))):
                raise CoverageError("Unverified personnel/body data cannot be graded")
            for key in ("jockeyNameRecorded", "jockeyCodeRecorded",
                        "trainerNameRecorded", "trainerCodeRecorded"):
                counts[key] += p[key]
            counts["bothPersonnelNamesRecorded"] += (
                p["jockeyNameRecorded"] and p["trainerNameRecorded"])
            counts["bodyTypeRecorded"] += body["bodyTypeRecorded"]
            counts["integrationCodeRecorded"] += body["integrationCodeRecorded"]
            counts["anyConformationRecorded"] += (
                body["bodyTypeRecorded"] or body["integrationCodeRecorded"])
        if any(type(v) is not int or v < 0 or v > n for v in counts.values()):
            raise CoverageError("Invalid personnel/body totals")
        result.append({
            "track": baseline["track"], "race": baseline["race"],
            "runnerCount": n, "recorded": counts,
            "observedFactorSlots": 8, "unmappedFactorCount": 2,
            "verifiedFactorCount": 0,
            "jockeyTrainerPerformanceAssessed": False,
            "bodyConditionAssessed": False,
            "raceDayBodyWeightFetched": False,
            "overallRankReady": False, "predictionReady": False,
            "bettingReady": False,
        })
    return {
        "version": VERSION, "raceCount": len(result), "races": result,
        "predictionReady": False, "bettingReady": False,
        "note": ("騎手・調教師名/コードおよび馬体形状コードの記録有無だけを"
                 "確認。騎手・厩舎の成績評価や当日の馬体重・増減・状態は未取得。"
                 "実馬総合評価・3連単には使用しません。"),
    }
