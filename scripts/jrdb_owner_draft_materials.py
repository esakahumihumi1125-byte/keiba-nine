"""Private, non-predictive source-material coverage for owner auto drafts.

Use already fetched /tra /tky /tcy /tze only. Never return horse names, scores,
paid source rows, race keys, official result claims or newly graded factors.
"""
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_private_factor_bridge import build_private_factor_matrix, summarize_factor_materials
from jrdb_entry_rotation_materials import enrich_entry_materials_matrix, summarize_entry_materials_matrix
from jrdb_personnel_body_materials import enrich_personnel_body_matrix, summarize_personnel_body_matrix

VERSION = "owner-draft-material-coverage-1"
FIELDS = ("pedigree", "drawWeight", "rotation", "personnel", "body", "pastCorner")


def unavailable():
    return {"version": VERSION, "status": "unavailable",
            "observedFactorSlots": 0, "gradedNewFactors": 0,
            "officialJraVerified": False, "races": []}


def observe_owner_draft_materials(programme, entries, training, recent, day):
    workouts = build_training_hints(programme, entries, training, day)
    past = build_recent_hints(programme, entries, recent, day)
    base = build_private_factor_matrix(workouts, past)
    base_summary = summarize_factor_materials(base)
    enriched = enrich_entry_materials_matrix(
        base, programme, entries, recent, day)
    entry_summary = summarize_entry_materials_matrix(enriched)
    personnel_matrix = enrich_personnel_body_matrix(
        enriched, programme, entries, day)
    personnel_summary = summarize_personnel_body_matrix(personnel_matrix)
    reports = (base_summary, entry_summary, personnel_summary)
    if any(r.get("predictionReady") is not False or
           r.get("bettingReady") is not False for r in reports):
        raise CoverageError("Source observations promoted to prediction")

    indexed = []
    for report in reports:
        if report.get("raceCount") != len(programme):
            raise CoverageError("Source material race count mismatch")
        rows = {}
        for item in report["races"]:
            coord = (item["track"], item["race"])
            if coord in rows:
                raise CoverageError("Duplicated source material coordinate")
            rows[coord] = item
        indexed.append(rows)
    keys = {(item["track"], item["race"]) for item in programme}
    if len(keys) != len(programme) or any(set(m) != keys for m in indexed):
        raise CoverageError("Source material races disagree")
    output = []
    programme_by_coord = {
        (row["track"], row["race"]): row for row in programme
    }
    for key in sorted(keys):
        a, b, c = (m[key] for m in indexed)
        count = a["runnerCount"]
        declared = programme_by_coord[key].get("headcount")
        if (type(count) is not int or not 0 <= count <= 18
                or type(declared) is not int or declared != count
                or b["runnerCount"] != count or c["runnerCount"] != count
                or any(x["verifiedFactorCount"] != 0 for x in (a, b, c))):
            raise CoverageError("Source material counts contradict roster")
        entry = b["entryObservations"]
        people = c["recorded"]
        observed = {
            "pedigree": entry["bothPedigreeRecorded"],
            "drawWeight": entry["drawAndWeightRecorded"],
            "rotation": count - b["rotationIntervals"]["unknown"],
            "personnel": people["bothPersonnelNamesRecorded"],
            "body": people["anyConformationRecorded"],
            "pastCorner": count - a["pastFourthCorner"]["insufficient"],
        }
        if any(type(value) is not int or not 0 <= value <= count
               for value in observed.values()):
            raise CoverageError("Invalid source material counters")
        output.append({"track": key[0], "race": key[1],
                       "runnerCount": count, "counts": observed})
    return {"version": VERSION, "status": "observed",
            "observedFactorSlots": 8, "gradedNewFactors": 0,
            "officialJraVerified": False, "races": output}


def observe_owner_draft_materials_isolated(programme, entries, training, recent, day):
    """Keep independent races' optional 8-factor *source coverage* visible.

    First use the original strict whole-day evaluator. If any race's source
    material is malformed, retry in-memory with exactly one programme race
    and its four already-fetched source lists. This does NOT issue provider
    requests, repair bad paid records, assign grades, or rank horses.
    A failed race is simply absent from 'partial' observations, never 0/0.
    """
    try:
        return observe_owner_draft_materials(
            programme, entries, training, recent, day)
    except (CoverageError, ValueError, TypeError, KeyError):
        pass
    if (not isinstance(programme, list) or len(programme) > 120
            or not all(isinstance(p, dict) for p in programme)):
        return unavailable()
    sources = (entries, training, recent)
    if any(not isinstance(source, list) or len(source) > 50000
           or not all(isinstance(item, dict) for item in source)
           for source in sources):
        return unavailable()
    coords = set()
    observed = []
    for race in programme:
        coord = (race.get("track"), race.get("race"))
        if coord in coords:
            return unavailable()
        coords.add(coord)
        key = race.get("racekey")
        if not isinstance(key, str):
            continue
        one = ([item for item in source if item.get("racekey") == key]
               for source in sources)
        one_entries, one_training, one_recent = one
        try:
            result = observe_owner_draft_materials(
                [race], one_entries, one_training, one_recent, day)
            if (result.get("status") != "observed"
                    or result.get("races") is None
                    or len(result["races"]) != 1
                    or (result["races"][0].get("track"),
                        result["races"][0].get("race")) != coord):
                continue
            observed.append(result["races"][0])
        except (CoverageError, ValueError, TypeError, KeyError):
            continue
    if not observed:
        return unavailable()
    if len(observed) == len(programme):
        # Even if the whole-day aggregator rejects unrelated/orphan rows,
        # never call the partial fallback 'all observed'. The global source
        # shape was not validated, so preserve the diagnostic distinction.
        status = "partial"
    else:
        status = "partial"
    return {
        "version": VERSION, "status": status,
        "observedFactorSlots": 8, "gradedNewFactors": 0,
        "officialJraVerified": False, "races": observed,
    }
