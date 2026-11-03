"""Private assessment preflight: map source-presence counts to evaluation work.

Takes only the already-aggregated JRDB evidence audit. Never reads raw horse
records, assigns grades, guesses winners, places bets, or publishes data.
"""
from evaluation_policy import FACTORS, CORE

VERSION = "assessment-preflight-1"
FACTOR_LABELS = {
    "training": "調教", "recent": "近走", "course_distance": "コース・距離",
    "pace": "展開・脚質", "ground": "馬場", "pedigree": "血統",
    "draw_weight": "枠・斤量", "jockey_stable": "騎手・厩舎",
    "rotation": "ローテ", "body_condition": "馬体"
}
SOURCE_FIELDS = {"training": "trainingRecords", "recent": "pastRunRecords"}


def _checked_count(value, name):
    if type(value) is not int or not 0 <= value <= 2160:
        raise ValueError("Invalid aggregate " + name)
    return value


def audit_assessment_preflight(audit):
    """Return source-count status per factor; all grades stay unassessed.

    A source-count match is *not* confirmation of scratches, a workout's
    quality, a first-time starter's history or the reliability of a source.
    """
    if not isinstance(audit, dict) or not isinstance(audit.get("races"), list):
        raise ValueError("Expected verified aggregate audit")
    if len(audit["races"]) > 120:
        raise ValueError("Too many races")
    if set(FACTOR_LABELS) != set(FACTORS):
        raise ValueError("Evaluation factor contract changed")
    seen = set()
    races = []
    for race in audit["races"]:
        if not isinstance(race, dict):
            raise ValueError("Invalid aggregate race")
        track, race_no = race.get("track"), race.get("race")
        if not isinstance(track, str) or track not in (
            "札幌", "函館", "福島", "新潟", "東京", "中山",
            "中京", "京都", "阪神", "小倉"):
            raise ValueError("Invalid aggregate track")
        if type(race_no) is not int or not 1 <= race_no <= 12:
            raise ValueError("Invalid aggregate race number")
        identity = (track, race_no)
        if identity in seen:
            raise ValueError("Duplicate aggregate race")
        seen.add(identity)
        observed = _checked_count(race.get("observedEntries"), "observed entries")
        declared = race.get("expectedRunners")
        if declared is not None:
            _checked_count(declared, "declared entries")
            if declared > 18:
                raise ValueError("Expected entries over 18")
        if observed > 18:
            raise ValueError("Observed entries over 18")
        source_status = {}
        pending = []
        for factor in FACTORS:
            if factor in SOURCE_FIELDS:
                count = _checked_count(race.get(SOURCE_FIELDS[factor]), factor)
                if count > observed:
                    raise ValueError("Source evidence exceeds entry count")
                if not observed or not count:
                    state = "unknown_or_not_applicable"
                elif count < observed:
                    state = "partial_source_records"
                else:
                    state = "source_record_count_matches"
            else:
                state = "not_mapped_from_provider"
            source_status[factor] = {
                "label": FACTOR_LABELS[factor], "sourceStatus": state,
                "grade": "未評価", "assessmentComplete": False,
                "requiredForCore": factor in CORE,
            }
            pending.append(factor)
        races.append({
            "track": track, "race": race_no,
            "observedEntries": observed, "expectedRunners": declared,
            "factors": source_status, "pendingAssessments": pending,
            "gradedCount": 0, "readyForPrediction": False,
        })
    return {
        "version": VERSION, "policyVersion": "research-1",
        "raceCount": len(races), "factorCount": len(FACTORS),
        "gradedFactors": 0, "readyForPrediction": 0,
        "coreFactors": sorted(CORE), "races": races,
        "note": ("集計済みの資料件数だけを調査した予想前の確認です。"
                 "資料件数一致でも真偽・取消・馬場・適性・評価は未確認。"
                 "新馬の近走欠如は正常な場合があります。"
                 "S/A/B/C、勝率、買い目は自動生成していません。"),
    }
