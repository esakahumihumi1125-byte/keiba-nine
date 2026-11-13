"""Read-only five-factor 79-weight view under the owner's research-6 weights.

Takes the already validated legacy research-5 85-weight same-race snapshot.
Never changes the signed historical 70/82/85 receipts or imports results.
A new projection is NOT a trained five-factor forecast, full 100-point grade,
rank, probability, official JRA check, or betting recommendation.
"""
from evaluation_policy import (
    FACTORS as LEGACY, POLICY_VERSION as LEGACY_POLICY,
    OWNER_FORMAL_FACTORS as UPDATED, OWNER_FORMAL_POLICY_VERSION as POLICY,
    POINTS,
)
from jrdb_coverage import CoverageError
from owner_five_core_research import VERSION as LEGACY_VERSION

VERSION = "owner-new-weight-five-research-1"
KEYS = ("training", "course_distance", "pace", "ground", "recent")
LEGACY_WEIGHTS = {key: LEGACY[key] for key in KEYS}
WEIGHTS = {key: UPDATED[key] for key in KEYS}
assert sum(LEGACY_WEIGHTS.values()) == 85
assert WEIGHTS == {
    "training": 30, "course_distance": 17, "pace": 17,
    "ground": 12, "recent": 3
} and sum(WEIGHTS.values()) == 79

UNKNOWN = "未評価"


def _groups(horses):
    scored, unscored = {}, []
    for horse in horses:
        if horse["rawThirdPoints"] is None:
            unscored.append(horse["number"])
        else:
            scored.setdefault(horse["rawThirdPoints"], []).append(horse["number"])
    return ([{"rawThirdPoints": raw, "numbers": sorted(nums)}
             for raw, nums in sorted(scored.items(), reverse=True)],
            sorted(unscored))


def new_weight_five_research(legacy):
    """Cross-validate legacy score arithmetic and derive *new* 79 research.

    A missing band remains unknown. Scores never imply formal 100-point grade.
    No network, persistence, source-row or identifier output.
    """
    if (not isinstance(legacy, dict)
            or legacy.get("version") != LEGACY_VERSION
            or legacy.get("policyVersion") != LEGACY_POLICY
            or legacy.get("factorWeights") != LEGACY_WEIGHTS
            or legacy.get("observedWeightTotal") != 85
            or legacy.get("factorGradesVerified") != 0
            or legacy.get("overallPredictionReady") is not False
            or legacy.get("formalScoreReady") is not False
            or legacy.get("officialJraVerified") is not False
            or legacy.get("bettingReady") is not False
            or legacy.get("autoPurchase") is not False
            or legacy.get("changesExistingTickets") is not False
            or legacy.get("changesExistingCoreReceipts") is not False
            or legacy.get("historicalBandsNotCalibrated") is not True
            or legacy.get("recentResultRankNotPrediction") is not True
            or legacy.get("researchOnly") is not True
            or legacy.get("privateOwnerOnly") is not True
            or not isinstance(legacy.get("races"), list)
            or not 0 <= len(legacy["races"]) <= 120
            or legacy.get("raceCount") != len(legacy["races"])):
        raise CoverageError("Legacy five-factor snapshot failed validation")
    seen_races, output = set(), []
    for race in legacy["races"]:
        if (not isinstance(race, dict)
                or not isinstance(race.get("track"), str) or not race["track"]
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or (race["track"], race["race"]) in seen_races
                or race.get("researchOnly") is not True
                or race.get("formalGradeReady") is not False
                or race.get("trifectaReady") is not False
                or race.get("comparisonIsFormalRank") is not False
                or not isinstance(race.get("horses"), list)
                or not 0 <= len(race["horses"]) <= 18
                or race.get("runnerCount") != len(race["horses"])
                or not isinstance(race.get("missingByFactor"), dict)
                or set(race["missingByFactor"]) != set(KEYS)
                or not isinstance(race.get("comparisonGroups"), list)
                or not isinstance(race.get("unassessedNumbers"), list)):
            raise CoverageError("Legacy five-factor race malformed")
        seen_races.add((race["track"], race["race"]))
        missing_counts = dict.fromkeys(KEYS, 0)
        old_horses, new_horses, numbers = [], [], set()
        for horse in race["horses"]:
            if (not isinstance(horse, dict)
                    or type(horse.get("number")) is not int
                    or not 1 <= horse["number"] <= 18
                    or horse["number"] in numbers
                    or not isinstance(horse.get("bands"), dict)
                    or set(horse["bands"]) != set(KEYS)
                    or not isinstance(horse.get("missing"), list)
                    or horse.get("formalScore100") is not None
                    or horse.get("formalGrade") != UNKNOWN
                    or horse.get("formalRank") is not None
                    or horse.get("scoreIsCalibrated") is not False
                    or horse.get("bettingReady") is not False):
                raise CoverageError("Legacy five-factor horse malformed")
            numbers.add(horse["number"])
            bands = horse["bands"]
            if any(b not in (*POINTS, UNKNOWN) for b in bands.values()):
                raise CoverageError("Unrecognized five-factor band")
            missing = [key for key in KEYS if bands[key] == UNKNOWN]
            for key in missing:
                missing_counts[key] += 1
            old_raw = None if missing else sum(
                LEGACY_WEIGHTS[key] * POINTS[bands[key]] for key in KEYS)
            new_raw = None if missing else sum(
                WEIGHTS[key] * POINTS[bands[key]] for key in KEYS)
            if (horse["missing"] != missing
                    or horse.get("observedFactorCount") != len(KEYS) - len(missing)
                    or horse.get("rawThirdPoints") != old_raw
                    or horse.get("evidenceScore85") != (
                        None if old_raw is None else round(old_raw / 3, 2))):
                raise CoverageError("Legacy 85-weight score mismatch")
            old_horses.append({"number": horse["number"], "rawThirdPoints": old_raw})
            # A *separate* 17+17 research subtotal can exist even if the
            # other three uncalibrated historical bands are missing. This
            # is arithmetic on descriptive bands, NOT a suitability grade.
            course_pace = ("course_distance", "pace")
            course_pace_raw = (None if any(bands[k] == UNKNOWN for k in course_pace)
                else sum(WEIGHTS[k] * POINTS[bands[k]] for k in course_pace))
            # The current-going historical band is a separate descriptive
            # study, never an assessment of the verified JRA race-day ground.
            going_raw = (None if bands["ground"] == UNKNOWN else
                         WEIGHTS["ground"] * POINTS[bands["ground"]])
            new_horses.append({
                "number": horse["number"], "bands": dict(bands),
                "missing": missing, "observedFactorCount": len(KEYS) - len(missing),
                "rawThirdPoints": new_raw,
                "evidenceScore79": (
                    None if new_raw is None else round(new_raw / 3, 2)),
                "coursePaceEvidenceRawThirdPoints": course_pace_raw,
                "coursePaceEvidenceScore34": (
                    None if course_pace_raw is None
                    else round(course_pace_raw / 3, 2)),
                "coursePaceEvidenceNotFormalGrade": True,
                "goingEvidenceRawThirdPoints": going_raw,
                "goingEvidenceScore12": (
                    None if going_raw is None else round(going_raw / 3, 2)),
                "goingEvidenceNotFormalGrade": True,
                "formalScore100": None, "formalGrade": UNKNOWN,
                "formalRank": None, "scoreIsCalibrated": False,
                "bettingReady": False,
            })
        old_groups, old_unassessed = _groups(old_horses)
        if (race["comparisonGroups"] != old_groups
                or race["unassessedNumbers"] != old_unassessed
                or race.get("completeObserved") != len(old_horses) - len(old_unassessed)
                or race["missingByFactor"] != missing_counts):
            raise CoverageError("Legacy five-factor groups mismatch")
        new_groups, unknown = _groups(new_horses)
        output.append({
            "track": race["track"], "race": race["race"],
            "runnerCount": len(new_horses), "horses": new_horses,
            "completeObserved": len(new_horses) - len(unknown),
            "missingByFactor": missing_counts,
            "comparisonGroups": new_groups, "unassessedNumbers": unknown,
            "comparisonIsFormalRank": False, "researchOnly": True,
            "formalGradeReady": False, "trifectaReady": False,
        })
    return {
        "version": VERSION, "policyVersion": POLICY,
        "sourcePolicyVersion": LEGACY_POLICY,
        "raceCount": len(output), "races": output,
        "factorWeights": dict(WEIGHTS), "observedWeightTotal": 79,
        "factorGradesVerified": 0, "overallPredictionReady": False,
        "formalScoreReady": False, "officialJraVerified": False,
        "bettingReady": False, "autoPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "historicalBandsNotCalibrated": True,
        "coursePaceEvidenceNotFormalGrade": True,
        "coursePaceEvidenceWeight": 34,
        "goingEvidenceNotFormalGrade": True,
        "goingEvidenceWeight": 12,
        "resultVerified": False, "changesExistingTickets": False,
        "changesExistingCoreReceipts": False,
        "changesExistingFiveReceipts": False,
        "extraProviderCalls": 0,
        "note": ("新配点の先頭5項目79点を、旧配点85点と同じ"
                 "未検証の発走前資料帯から再比較。正式100点ではなく"
                 "80/100等へ換算しない。旧署名、馬券、収支は変更しない。"),
    }
