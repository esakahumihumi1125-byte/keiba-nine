"""Fail-closed internal bridge from JRDB provisional materials to formal inputs.

This is a preparation boundary, NOT a grading adapter. The JRDB two-factor
training/recent bands and fourth-corner observations are unverified research;
none becomes a supported formal S/A/B/C grade. Only call from the authenticated
private server with a same-request matrix; never expose the matrix or this
function as a public endpoint. It performs no network access or paid reads.
"""
from evaluation_policy import OWNER_FORMAL_FACTORS
from jrdb_coverage import CoverageError
from jrdb_dual_factor_readiness import KNOWN
from jrdb_evidence_readiness import KEY, NUMBER
from jrdb_private_factor_bridge import POSITION_LABELS
from jrdb_program_preview import TRACKS
from owner_formal_assessment_input import validate_formal_assessment_snapshot

VERSION = "owner-formal-jrdb-source-bridge-1"
SOURCE_KEYS = frozenset((
    "racekey", "track", "race", "byNumber", "researchOnly",
    "independentJraVerified", "predictionReady", "bettingReady",
))
SOURCE_BASIS = {
    "training": "experimental_workout_index",
    "recent": "experimental_recent_idm",
}
UNMAPPED = {"grade": "未評価", "basis": "not_mapped"}
NO_OFFICIAL_PROOF = {
    "jra_starters_verified": False,
    "jra_scratches_verified": False,
    "jra_going_verified": False,
    "jra_posttime_verified": False,
}


def build_ungraded_formal_race_input(private_race, *, day, as_of, off_at):
    """Normalize a single *unverified* JRDB source matrix for the formal gate.

    All ten assessments are deliberately None, not guessed grades. The input
    only proves provisional record shape; the future separate source-licensed
    grading adapter must supply graded evidence and independently checked
    official JRA information before a usable research ranking can be made.

    `as_of`, `off_at` and `day` must be supplied by a trusted same-request
    server coordinator; a JRDB racekey alone does not verify calendar date or
    independently confirm the JRA post time. Nothing here sets approval flags.
    """
    if (not isinstance(private_race, dict)
            or set(private_race) != SOURCE_KEYS
            or private_race.get("researchOnly") is not True
            or private_race.get("independentJraVerified") is not False
            or private_race.get("predictionReady") is not False
            or private_race.get("bettingReady") is not False):
        raise CoverageError("Invalid unverified private source contract")
    key, track, race = (
        private_race.get("racekey"),
        private_race.get("track"),
        private_race.get("race"),
    )
    if (type(key) is not str or KEY.fullmatch(key) is None
            or key[:2] not in TRACKS
            or track != TRACKS[key[:2]]
            or type(race) is not int or not 1 <= race <= 12
            or int(key[6:]) != race):
        raise CoverageError("Private source race identity mismatch")

    rows = private_race.get("byNumber")
    if not isinstance(rows, dict) or not 4 <= len(rows) <= 18:
        raise CoverageError("Invalid source runner count")
    horses = []
    for number, slots in rows.items():
        if type(number) is not str or NUMBER.fullmatch(number) is None:
            raise CoverageError("Invalid source runner identity")
        if not isinstance(slots, dict) or set(slots) != set(OWNER_FORMAL_FACTORS):
            raise CoverageError("Invalid source factor roster")
        for factor, slot in slots.items():
            if factor in SOURCE_BASIS:
                if (not isinstance(slot, dict)
                        or set(slot) != {"grade", "basis"}
                        or slot["basis"] != SOURCE_BASIS[factor]
                        or slot["grade"] not in KNOWN):
                    raise CoverageError("Unverified provisional source changed")
            elif factor == "pace":
                if (not isinstance(slot, dict)
                        or set(slot) != {"grade", "basis", "positionObservation"}
                        or slot["grade"] != "未評価"
                        or slot["basis"] != "historical_fourth_corner_only"
                        or slot["positionObservation"] not in POSITION_LABELS):
                    raise CoverageError("Historical position cannot become pace grade")
            elif slot != UNMAPPED:
                raise CoverageError("Unverified factor cannot become a grade")
        horses.append({
            "number": int(number),
            "assessments": {factor: None for factor in OWNER_FORMAL_FACTORS},
        })

    snapshot = {
        "mode": "owner_verified_prestart_v1",
        "track": track, "race": race,
        "asOf": as_of, "offAt": off_at,
        "independentJra": dict(NO_OFFICIAL_PROOF),
        "assessmentValidated": False, "predictionValidated": False,
        "horses": sorted(horses, key=lambda horse: horse["number"]),
    }
    checked = validate_formal_assessment_snapshot(
        snapshot, expected_track=track, expected_race=race, day=day,
    )
    return {"track": track, "race": race, "snapshot": checked}
