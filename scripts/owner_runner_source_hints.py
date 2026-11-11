"""Private, same-read per-runner source availability for the 10-factor roadmap.

No extra JRDB calls, provider values, names, weights, pedigree strings,
dates, grades, points or ticket changes. A YES means only that the requested
input columns exist in a validated source row, never fitness or ability.
Only a prestart draft's already-visible runner numbers may be returned; held
or late races never regain a roster through this supplementary audit.
"""
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_private_factor_bridge import build_private_factor_matrix
from jrdb_entry_rotation_materials import enrich_entry_materials_matrix
from jrdb_personnel_body_materials import enrich_personnel_body_matrix

VERSION = "owner-runner-source-hints-1"
FIELDS = ("pedigree", "draw_weight", "jockey_stable", "rotation", "past_corner")
MAX_RACES = 120


def _unavailable(race):
    return {
        "track": race["track"], "race": race["race"],
        "status": "unavailable", "runners": [],
    }


def observe_owner_runner_sources(programme, entries, training, recent, day, report):
    """Keep fields from four *already fetched* sources isolated by race.

    The main private source adapter has already validated and joined draft
    racers. We re-evaluate only their exact racing source rows in memory.
    An optional malformed source affects that race only. All output values
    are fixed booleans, counts and horse numbers already present in the
    signed provisional draft. No official JRA comparison is inferred.
    """
    if (not isinstance(report, dict)
            or report.get("version") != "jrdb-owner-auto-draft-1"
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("overallPredictionReady") is not False
            or report.get("officialJraVerified") is not False
            or report.get("bettingReady") is not False
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > MAX_RACES
            or not isinstance(programme, list)
            or not isinstance(entries, list)
            or not isinstance(training, list)
            or not isinstance(recent, list)
            or len(programme) != len(report["races"])
            or len(programme) > MAX_RACES
            or len(entries) > 50000
            or len(training) > 50000
            or len(recent) > 50000
            or not all(isinstance(row, dict) for rows in
                       (programme, entries, training, recent) for row in rows)):
        raise CoverageError("Invalid private source evidence input")
    p_by_coord = {}
    key_set = set()
    for row in programme:
        key, coord = row.get("racekey"), (row.get("track"), row.get("race"))
        if (type(key) is not str or not key
                or coord in p_by_coord or key in key_set):
            raise CoverageError("Duplicate or invalid source programme")
        p_by_coord[coord] = row
        key_set.add(key)
    # One index for the whole day, instead of scanning every paid row for
    # every scheduled race. Orphan rows are NEVER assigned by horse name.
    grouped = []
    for rows in (entries, training, recent):
        index = {}
        for row in rows:
            key = row.get("racekey")
            if type(key) is str and key in key_set:
                index.setdefault(key, []).append(row)
        grouped.append(index)
    seen, outcome = set(), []
    for race in report["races"]:
        if (not isinstance(race, dict)
                or type(race.get("track")) is not str
                or type(race.get("race")) is not int
                or (race["track"], race["race"]) not in p_by_coord
                or (race["track"], race["race"]) in seen
                or race.get("status") not in ("hold", "provisional_draft")
                or not isinstance(race.get("runners"), list)):
            raise CoverageError("Invalid private draft source coordinate")
        coord = race["track"], race["race"]
        seen.add(coord)
        if race["status"] != "provisional_draft":
            outcome.append({
                "track": coord[0], "race": coord[1],
                "status": "held", "runners": [],
            })
            continue
        p = p_by_coord[coord]
        key = p["racekey"]
        one_e, one_t, one_r = (g.get(key, []) for g in grouped)
        try:
            tr = build_training_hints([p], one_e, one_t, day)
            prev = build_recent_hints([p], one_e, one_r, day)
            matrix = build_private_factor_matrix(tr, prev)
            matrix = enrich_entry_materials_matrix(
                matrix, [p], one_e, one_r, day)
            matrix = enrich_personnel_body_matrix(
                matrix, [p], one_e, day)
            source = matrix[0]["byNumber"]
            visible = {str(row["number"]).zfill(2) for row in race["runners"]}
            if (not 1 <= len(visible) <= 18
                    or len(visible) != len(race["runners"])
                    or set(source) != visible):
                raise CoverageError("Different private source runner roster")
            observations = []
            for n in sorted(visible):
                slots = source[n]
                a, b, c, pace = (slots["pedigree"], slots["draw_weight"],
                                 slots["jockey_stable"], slots["pace"])
                interval = slots["rotation"]["intervalBucket"]
                if (a["grade"] != "未評価" or b["grade"] != "未評価"
                        or c["grade"] != "未評価"
                        or pace["grade"] != "未評価"
                        or interval not in (
                            "under14Days", "days14to55", "days56plus", "unknown"
                        )):
                    raise CoverageError("A source-only material was graded")
                flags = {
                    "pedigree": (a["sireRecorded"]
                                 and a["maternalSireRecorded"]),
                    "draw_weight": (b["bracketRecorded"]
                                    and b["assignedWeightRecorded"]),
                    "jockey_stable": (c["jockeyNameRecorded"]
                                      and c["trainerNameRecorded"]),
                    "rotation": interval != "unknown",
                    "past_corner": (pace["positionObservation"]
                                      != "insufficient"),
                }
                if any(type(flag) is not bool for flag in flags.values()):
                    raise CoverageError("Malformed source-presence flag")
                observations.append({
                    "number": int(n), "observed": flags,
                    "verifiedFactorCount": 0,
                })
            outcome.append({
                "track": coord[0], "race": coord[1],
                "status": "observed", "runners": observations,
            })
        except (CoverageError, ValueError, TypeError, KeyError, IndexError):
            outcome.append(_unavailable(race))
    if len(seen) != len(p_by_coord):
        raise CoverageError("Incomplete private source race list")
    return {
        "version": VERSION, "races": outcome, "raceCount": len(outcome),
        "observedRaceCount": sum(r["status"] == "observed" for r in outcome),
        "unavailableRaceCount": sum(
            r["status"] == "unavailable" for r in outcome),
        "factorFields": list(FIELDS),
        "verifiedNewFactorCount": 0, "officialJraVerified": False,
        "overallPredictionReady": False, "bettingReady": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "newProviderRequests": 0, "rawSourceRowsIncluded": False,
        "note": ("追加10項目の資料有無だけを馬番別に確認。"
                 "過去4角は展開予想ではなく、馬体形状は当日馬体重ではない。"
                 "正式S/A/B/Cと総合点・買い目は作成しません。"),
    }
