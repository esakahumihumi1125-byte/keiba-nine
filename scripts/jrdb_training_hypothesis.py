"""Private JRDB /tcy workout-index research hints.

The /tcy fields oikirisisu and siagarisisu are provider numeric indexes;
the public JRDB field guide says higher is better, with 60 as a reference.
The experimental S/A/B/C thresholds below are KEIBA NINE hypotheses, NOT
provider grades, trained probabilities, confirmed fitness, or betting advice.
Never publish the resulting hints or return horse-level provider records.
"""
import math
from collections import defaultdict
from jrdb_coverage import audit_race_coverage, CoverageError
from jrdb_evidence_readiness import audit_evidence_coverage, HORSE_ID, NUMBER

VERSION = "training-hypothesis-1"
THRESHOLDS = ((75, "S"), (60, "A"), (45, "B"), (0, "C"))
GRADE_LABELS = ("S", "A", "B", "C", "未評価")


def _index(value):
    if value is None or value == "":
        return None
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 200:
        raise CoverageError("Workout index format is invalid")
    return float(value)


def _grade(oikiri, finish):
    # Conservative hypothesis: both a workout AND a finishing-condition
    # index must exist, and the weaker of the two limits the grade.
    if oikiri is None or finish is None:
        return "未評価"
    lower = min(oikiri, finish)
    return next(grade for boundary, grade in THRESHOLDS if lower >= boundary)


def build_training_hints(programme, entries, training, requested_date):
    """Return an INTERNAL number-level candidate grade, with no published data.

    Requires an unambiguous horse-id or horse-number join. Audit first, then
    reject mismatches and duplicate rows rather than picking a "best" value.
    """
    # This checks programme/roster, dates, racekeys and identity consistency.
    audit_evidence_coverage(programme, entries, training, [], requested_date)
    roster = defaultdict(dict)
    identities = {}
    valid_keys = {r["racekey"] for r in programme}
    for entry in entries:
        key, number, hid = entry["racekey"], entry["horse_number"], entry.get("horse_id")
        roster[key][number] = entry
        if hid:
            identities[(key, hid)] = number

    matched = {}
    for row in training:
        key, num, hid = row["racekey"], row.get("horse_number"), row.get("horse_id")
        if key not in valid_keys:
            raise CoverageError("Unexpected training race")
        via_number = num if isinstance(num, str) and NUMBER.fullmatch(num) and num in roster[key] else None
        via_id = identities.get((key, hid)) if isinstance(hid, str) and HORSE_ID.fullmatch(hid) else None
        if via_number and via_id and via_number != via_id:
            raise CoverageError("Training identity mismatch")
        if not (via_number or via_id):
            # No usable identity: cannot attach this value to any runner.
            continue
        number = via_id or via_number
        race_number = (key, number)
        if race_number in matched:
            raise CoverageError("Duplicate workout analysis for same runner")
        matched[race_number] = _grade(_index(row.get("oikirisisu")), _index(row.get("siagarisisu")))

    by_race = []
    for race in programme:
        key = race["racekey"]
        grades = {}
        for number in sorted(roster[key]):
            grades[number] = matched.get((key, number), "未評価")
        by_race.append({
            "racekey": key, "track": race["track"], "race": race["race"],
            "gradesByNumber": grades, "researchOnly": True,
            "predictionReady": False
        })
    return by_race


def summarize_training_hints(hints):
    """Redact identifiers and indexes: only safe per-race aggregate counts."""
    if not isinstance(hints, list) or len(hints) > 120:
        raise ValueError("Invalid training hints")
    out = []
    seen = set()
    for row in hints:
        if not isinstance(row, dict) or not isinstance(row.get("gradesByNumber"), dict):
            raise ValueError("Invalid internal training race")
        key = (row.get("track"), row.get("race"))
        if key in seen:
            raise ValueError("Duplicate training race")
        seen.add(key)
        counts = {grade: 0 for grade in GRADE_LABELS}
        for grade in row["gradesByNumber"].values():
            if grade not in counts:
                raise ValueError("Invalid training grade")
            counts[grade] += 1
        out.append({
            "track": row["track"], "race": row["race"],
            "gradeCounts": counts, "graded": sum(counts[g] for g in GRADE_LABELS[:4]),
            "missing": counts["未評価"], "researchOnly": True, "predictionReady": False
        })
    return {
        "version": VERSION, "races": out, "predictionReady": False,
        "policy": ("追切指数・仕上指数の両方がある場合だけ、暫定の独自閾値で判定。"
                   "S>=75、A>=60、B>=45、C<45。これらはJRDB公式の"
                   "評価ランクでも予測勝率でもなく、調教一項目の研究仮説です。"
                   "他の評価項目・取消・当日馬場が未確認のため買い目は作りません。")
    }
