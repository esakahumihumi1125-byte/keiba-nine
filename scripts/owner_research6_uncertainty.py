"""Research-6 sensitivity: show what *ungraded factors* could change.

This is arithmetic on uncalibrated S/A/B/C hypotheses, not a formal score,
probability, rank, verified source effect or recommendation. It uses the same
already-reviewed owner-private history snapshot. Missing observations are
intervals, NEVER C/zero outcomes. No network, storage, HMAC changes or bets.
"""
from evaluation_policy import (
    OWNER_FORMAL_FACTORS as FACTORS,
    OWNER_FORMAL_POLICY_VERSION as POLICY,
    POINTS,
)
from owner_new_weight_five_research import VERSION as FIVE_VERSION, KEYS as FIVE
from owner_remaining21_source_gaps import (
    VERSION as REMAINING_VERSION, KEYS as REMAINING,
)
from jrdb_coverage import CoverageError

VERSION = "owner-research6-uncertainty-intervals-1"
ALL = (*FIVE, *REMAINING)
assert len(ALL) == 10 and set(ALL) == set(FACTORS)
assert sum(FACTORS[k] for k in FIVE) == 79
assert sum(FACTORS[k] for k in REMAINING) == 21
UNKNOWN = "未評価"


def _index_races(payload):
    if (not isinstance(payload.get("races"), list)
            or len(payload["races"]) > 120
            or payload.get("raceCount") != len(payload["races"])):
        raise CoverageError("Sensitivity race list invalid")
    result = {}
    for race in payload["races"]:
        if (not isinstance(race, dict)
                or not isinstance(race.get("track"), str)
                or not race["track"]
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12):
            raise CoverageError("Sensitivity race identity invalid")
        ident = race["track"], race["race"]
        if ident in result:
            raise CoverageError("Duplicate sensitivity race")
        result[ident] = race
    return result


def _horse_index(race):
    rows = race.get("horses")
    if (not isinstance(rows, list) or len(rows) > 18
            or race.get("runnerCount") != len(rows)):
        raise CoverageError("Sensitivity horse count invalid")
    result = {}
    for h in rows:
        if (not isinstance(h, dict) or type(h.get("number")) is not int
                or not 1 <= h["number"] <= 18 or h["number"] in result):
            raise CoverageError("Invalid or repeated sensitivity horse")
        result[h["number"]] = h
    return result


def research6_uncertainty_intervals(five_study, remaining_gaps):
    """Bound all 100 hypothetical points using validated research bands only.

    Unknown five-factor bands and all five uncalibrated support factors are
    independently allowed 0..their allotted weight. Even if JRDB personnel
    field *exists*, its performance grade remains unknown. The intervals can
    narrow only once real factor assessments are independently validated.
    """
    if (not isinstance(five_study, dict) or not isinstance(remaining_gaps, dict)
            or five_study.get("version") != FIVE_VERSION
            or five_study.get("policyVersion") != POLICY
            or five_study.get("observedWeightTotal") != 79
            or five_study.get("factorWeights") != {k: FACTORS[k] for k in FIVE}
            or five_study.get("factorGradesVerified") != 0
            or five_study.get("formalScoreReady") is not False
            or five_study.get("officialJraVerified") is not False
            or five_study.get("bettingReady") is not False
            or five_study.get("researchOnly") is not True
            or remaining_gaps.get("version") != REMAINING_VERSION
            or remaining_gaps.get("policyVersion") != POLICY
            or remaining_gaps.get("factorWeights") != {
                k: FACTORS[k] for k in REMAINING
            }
            or remaining_gaps.get("remainingWeight") != 21
            or remaining_gaps.get("initialResearchWeight") != 79
            or remaining_gaps.get("totalWeight") != 100
            or remaining_gaps.get("verifiedFactorCount") != 0
            or remaining_gaps.get("officialJraVerified") is not False
            or remaining_gaps.get("bettingReady") is not False
            or remaining_gaps.get("researchOnly") is not True
            or five_study.get("privateOwnerOnly") is not True
            or remaining_gaps.get("privateOwnerOnly") is not True):
        raise CoverageError("Sensitivity sources are not ungraded research")
    old, gaps = _index_races(five_study), _index_races(remaining_gaps)
    if set(old) != set(gaps):
        raise CoverageError("Sensitivity race set disagrees")

    out = []
    for coord in sorted(old):
        r, g = old[coord], gaps[coord]
        five_horses = _horse_index(r)
        gap_horses = _horse_index(g)
        if (set(five_horses) != set(gap_horses)
                or r.get("formalGradeReady") is not False
                or r.get("trifectaReady") is not False
                or r.get("comparisonIsFormalRank") is not False
                or g.get("gradeReady") is not False
                or g.get("trifectaReady") is not False):
            raise CoverageError("Sensitivity source race not eligible")
        horses = []
        for number in sorted(five_horses):
            h, support = five_horses[number], gap_horses[number]
            bands = h.get("bands")
            if (not isinstance(bands, dict) or set(bands) != set(FIVE)
                    or not isinstance(h.get("missing"), list)
                    or h.get("formalScore100") is not None
                    or h.get("formalGrade") != UNKNOWN
                    or h.get("scoreIsCalibrated") is not False
                    or h.get("bettingReady") is not False
                    or support.get("research79") != h.get("evidenceScore79")
                    or support.get("research79Observed") != (
                        h.get("rawThirdPoints") is not None
                    )
                    or support.get("verifiedFactorCount") != 0
                    or support.get("formalScore100") is not None
                    or support.get("formalGrade") != UNKNOWN
                    or support.get("bettingReady") is not False
                    or not isinstance(support.get("sourceFieldsPresent"), dict)
                    or set(support["sourceFieldsPresent"]) != set(REMAINING)):
                raise CoverageError("Sensitivity horse sources disagree")
            missing = [k for k in FIVE if bands[k] == UNKNOWN]
            if (h["missing"] != missing
                    or h.get("observedFactorCount") != len(FIVE) - len(missing)
                    or any(v not in (*POINTS, UNKNOWN) for v in bands.values())):
                raise CoverageError("Invalid five-factor research evidence")
            observed_raw = sum(
                FACTORS[k] * POINTS[bands[k]]
                for k in FIVE if k not in missing)
            full_raw = None if missing else observed_raw
            if (h.get("rawThirdPoints") != full_raw
                    or h.get("evidenceScore79") != (
                        None if full_raw is None else round(full_raw / 3, 2))):
                raise CoverageError("Sensitivity research score does not match bands")
            if (any(type(v) is not bool
                    for v in support["sourceFieldsPresent"].values())
                    or support["sourceFieldsPresent"]["body_condition"] is not False
                    or support.get("sourceFieldCoverageEquivalent21") != sum(
                        FACTORS[k] for k in REMAINING
                        if support["sourceFieldsPresent"][k])):
                raise CoverageError("Sensitivity source coverage inconsistent")
            unresolved = 21 + sum(FACTORS[k] for k in missing)
            lower, upper = observed_raw, observed_raw + 3 * unresolved
            if not 0 <= lower <= upper <= 300:
                raise CoverageError("Impossible research interval")
            horses.append({
                "number": number,
                "observedHypothesisFactors": 5 - len(missing),
                "unassessedFiveFactors": list(missing),
                "unassessedTotalWeight": unresolved,
                "jockeyStableStillUnassessedWeight": 10,
                "otherUnassessedWeight": unresolved - 10,
                "lowerResearchRawThirdPoints": lower,
                "upperResearchRawThirdPoints": upper,
                "lowerResearchBound": round(lower / 3, 2),
                "upperResearchBound": round(upper / 3, 2),
                "formalScore100": None,
                "formalGrade": UNKNOWN,
                "formalRank": None,
                "scoreIsCalibrated": False,
                "bettingReady": False,
            })
        for h in horses:
            # For this *fixed hypothesis* only, a higher lower-bound than a
            # competitor's maximum survives any missing-factor assignment.
            h["arithmeticallyAbove"] = [
                x["number"] for x in horses
                if x["number"] != h["number"]
                and h["lowerResearchRawThirdPoints"] >
                    x["upperResearchRawThirdPoints"]
            ]
            h["researchPossibleBestRank"] = 1 + sum(
                x["lowerResearchRawThirdPoints"] >
                    h["upperResearchRawThirdPoints"]
                for x in horses if x["number"] != h["number"]
            )
            h["researchPossibleWorstRank"] = 1 + sum(
                x["upperResearchRawThirdPoints"] >=
                    h["lowerResearchRawThirdPoints"]
                for x in horses if x["number"] != h["number"]
            )
        out.append({
            "track": coord[0], "race": coord[1],
            "runnerCount": len(horses), "horses": horses,
            "strictAdvantagePairCount": sum(len(h["arithmeticallyAbove"])
                                             for h in horses),
            "researchOnly": True, "formalRankReady": False,
            "trifectaReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY,
        "raceCount": len(out), "races": out,
        "factorWeights": dict(FACTORS),
        "observedFactorWeightCeiling": 79,
        "alwaysUnassessedWeight": 21,
        "jockeyStableUnassessedWeight": 10,
        "verifiedFactorCount": 0, "formalScoreReady": False,
        "officialJraVerified": False, "bettingReady": False,
        "autoPurchase": False, "researchOnly": True,
        "privateOwnerOnly": True, "extraProviderCalls": 0,
        "changesExistingReceipts": False, "changesExistingTickets": False,
        "changesExistingRoi": False,
        "note": ("新配点100点の仮説的な上下限。近走3点、騎手厩舎10点を"
                 "含む未評価項目は最低0〜最高満点の範囲だけを示します。"
                 "5項目も未検証なので、この数学的な上下限・順位は"
                 "能力評価、勝率、正式S/A/B/Cや馬券とは違います。"),
    }
