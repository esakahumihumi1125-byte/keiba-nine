"""Owner-only ten-factor research inventory from already joined JRDB observations.

All source rows stay inside the authenticated server. Five provisional bands
from the research overlay remain separate from the ungraded source-presence
states for bloodline, draw/weight, personnel, rest interval and race-day body
weight. These are NOT ten predictive grades, a winner selection or a bet.
"""
from evaluation_policy import FACTORS, POLICY_VERSION
from jrdb_coverage import CoverageError
from jrdb_entry_rotation_materials import BUCKETS
from jrdb_five_factor_hypotheses import (
    VERSION as FIVE_VERSION, FACTORS_IN_VIEW, GRADE,
)
from jrdb_personnel_body_materials import summarize_personnel_body_matrix

VERSION = "owner-ten-factor-source-inventory-1"
REMAINING = ("pedigree", "draw_weight", "jockey_stable",
             "rotation", "body_condition")
assert set(FACTORS_IN_VIEW) | set(REMAINING) == set(FACTORS)
assert set(FACTORS_IN_VIEW).isdisjoint(REMAINING)


def _indexed(rows, name):
    if not isinstance(rows, list) or len(rows) > 120:
        raise CoverageError("Invalid " + name + " race list")
    indexed = {}
    for race in rows:
        if (not isinstance(race, dict)
                or not isinstance(race.get("track"), str)
                or not race["track"]
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12):
            raise CoverageError("Invalid " + name + " race identity")
        key = race["track"], race["race"]
        if key in indexed:
            raise CoverageError("Duplicated " + name + " race")
        indexed[key] = race
    return indexed


def _state(flags):
    if any(type(x) is not bool for x in flags):
        raise CoverageError("Invalid source-presence flags")
    return "complete_fields_observed" if all(flags) else (
        "partial_fields_observed" if any(flags) else "no_fields_observed"
    )


def ten_factor_source_inventory(five, personnel_matrix):
    """Check all runner identities and report ungraded ten-factor source states.

    Only run from the private same-snapshot JRDB history coordinator. The
    returned research band is not the actual factor grade. Horse number is
    only attached after roster equivalence is checked (01 vs 1 normalized).
    """
    summary = summarize_personnel_body_matrix(personnel_matrix)
    if (not isinstance(five, dict)
            or five.get("version") != FIVE_VERSION
            or five.get("policyVersion") != POLICY_VERSION
            or five.get("researchOnly") is not True
            or five.get("privateOwnerOnly") is not True
            or five.get("officialJraVerified") is not False
            or five.get("overallPredictionReady") is not False
            or five.get("verifiedFactorCount") != 0
            or five.get("bettingReady") is not False
            or five.get("autoPurchase") is not False
            or five.get("hypothesisBandsNotVerifiedGrades") is not True
            or five.get("materialCoverageDoesNotMeanPrediction") is not True
            or not isinstance(five.get("races"), list)
            or five.get("raceCount") != len(five["races"])
            or summary.get("predictionReady") is not False
            or summary.get("bettingReady") is not False
            or summary.get("raceCount") != len(personnel_matrix)):
        raise CoverageError("Invalid ten-factor inventory sources")
    factors = five.get("factors")
    if (not isinstance(factors, list)
            or len(factors) != len(FACTORS_IN_VIEW)
            or any(not isinstance(f, dict) or f.get("key") != key
                   or f.get("weight") != FACTORS[key]
                   for f, key in zip(factors, FACTORS_IN_VIEW))):
        raise CoverageError("Unexpected provisional factor policy")

    f_map = _indexed(five["races"], "five-factor")
    p_map = _indexed(personnel_matrix, "personnel")
    if set(f_map) != set(p_map):
        raise CoverageError("Ten-factor source race sets differ")
    output = []
    for key in sorted(f_map):
        research, source = f_map[key], p_map[key]
        rows, internal = research.get("runners"), source.get("byNumber")
        if (not isinstance(rows, list) or not isinstance(internal, dict)
                or len(rows) != len(internal)
                or len(rows) != research.get("runnerCount")
                or not 0 <= len(rows) <= 18
                or research.get("verifiedFactorCount") != 0
                or research.get("overallReady") is not False
                or research.get("bettingReady") is not False
                or any(type(k) is not str or len(k) != 2
                       or not k.isascii() or not k.isdigit()
                       or not 1 <= int(k) <= 18 for k in internal)):
            raise CoverageError("Invalid source runner roster")
        source_numbers = {int(k) for k in internal}
        if len(source_numbers) != len(internal):
            raise CoverageError("Repeated runner number")
        counted = dict.fromkeys(REMAINING, 0)
        horses, seen = [], set()
        for horse in rows:
            number = horse.get("number") if isinstance(horse, dict) else None
            if (type(number) is not int or number not in source_numbers
                    or number in seen
                    or horse.get("actualGradesVerified") != 0
                    or horse.get("overallScore") is not None
                    or horse.get("overallRank") is not None
                    or not isinstance(horse.get("bands"), dict)
                    or set(horse["bands"]) != set(FACTORS_IN_VIEW)
                    or any(x not in GRADE for x in horse["bands"].values())):
                raise CoverageError("Unverified five-factor research runner")
            seen.add(number)
            slots = internal[f"{number:02d}"]
            if (not isinstance(slots, dict)
                    or set(slots) != set(FACTORS)
                    or slots["training"].get("grade") != horse["bands"]["training"]
                    or slots["recent"].get("grade") != horse["bands"]["recent"]
                    or any(slots[k].get("grade") != "未評価" for k in
                           (*REMAINING, "course_distance", "pace", "ground"))):
                raise CoverageError("Two-factor research or source grades differ")
            pedigree = slots["pedigree"]
            draw = slots["draw_weight"]
            personnel = slots["jockey_stable"]
            rotation = slots["rotation"]
            body = slots["body_condition"]
            # summarize_personnel_body_matrix above checks the exact type,
            # key set, grade and basis for each of these source fields.
            p_state = _state((pedigree["sireRecorded"],
                              pedigree["maternalSireRecorded"]))
            d_state = _state((draw["bracketRecorded"],
                              draw["assignedWeightRecorded"]))
            j_state = _state((personnel["jockeyNameRecorded"],
                              personnel["trainerNameRecorded"]))
            interval = rotation["intervalBucket"]
            if interval not in BUCKETS:
                raise CoverageError("Invalid historic rest interval")
            b_flag = (body["bodyTypeRecorded"] or
                      body["integrationCodeRecorded"])
            if type(b_flag) is not bool:
                raise CoverageError("Invalid conformation indicator")
            status = {
                "pedigree": p_state,
                "draw_weight": d_state,
                "jockey_stable": j_state,
                "rotation": interval,
                # Body conformation codes are NEVER a substitute for the
                # actual race-day bodyweight or its change.
                "body_condition": "race_day_bodyweight_unavailable",
            }
            observed = {
                "pedigree": p_state == "complete_fields_observed",
                "draw_weight": d_state == "complete_fields_observed",
                "jockey_stable": j_state == "complete_fields_observed",
                "rotation": interval != "unknown",
                "body_condition": False,
            }
            for k in REMAINING:
                counted[k] += int(observed[k])
            horses.append({
                "number": number,
                "provisionalBands": {k: horse["bands"][k]
                                     for k in FACTORS_IN_VIEW},
                "sourceStates": status,
                "bodyShapeCodePresent": b_flag,
                "verifiedGrades": 0,
                "overallScore": None,
                "overallRank": None,
            })
        if seen != source_numbers:
            raise CoverageError("Ten-factor runner roster mismatch")
        horses.sort(key=lambda row: row["number"])
        output.append({
            "track": key[0], "race": key[1],
            "runnerCount": len(horses), "runners": horses,
            "remainingFieldCoverage": counted,
            "verifiedGrades": 0, "overallReady": False,
            "independentJraVerified": False,
            "bettingReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": len(output), "races": output,
        "factorWeights": dict(FACTORS),
        "factorCount": 10, "totalWeight": sum(FACTORS.values()),
        "independentJraVerified": False,
        "overallPredictionReady": False, "verifiedGrades": 0,
        "researchOnly": True, "privateOwnerOnly": True,
        "bettingReady": False, "autoPurchase": False,
        "note": ("調教・近走は暫定ランク、コース距離・展開・馬場は"
                 "過去資料の研究用目安。血統・枠斤量・騎手厩舎・"
                 "ローテは資料有無、馬体重は当日の値が未取得。"
                 "資料有無だけでは能力のS/A/B/Cは付けられません。"
                 "JRA公式照合と10項目の採点・予想は未完成。"),
    }
