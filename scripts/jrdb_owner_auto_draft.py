"""Owner-only automatic *provisional* picks from existing JRDB 2-factor research.

Four data-source reads happen in the authenticated caller, not here. This
module NEVER calls JRDB, claims official JRA confirmation, predicts win
probabilities, publishes paid indices, saves wagers or starts purchases.

Only unambiguous, complete, future provisional racecards get a mechanically
generated 3連単 formation for owner review. Missing factors and cutoff ties
hold the race rather than choosing by horse number. This is a research draft,
NOT a validated 10-factor or real betting recommendation.
"""
from datetime import datetime, timezone, timedelta
import re

from owner_factor_diagnostics import TRAINING, RECENT
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from jrdb_owner_runner_research import VALUES

VERSION = "jrdb-owner-auto-draft-1"
SOURCE_VERSION = "jrdb-owner-day-research-1"
RUNNER_VERSION = "jrdb-owner-runner-research-1"
JST = timezone(timedelta(hours=9))
GRADES = frozenset(VALUES)
OBSERVED = frozenset(("frontObserved", "backObserved",
                      "mixedObserved", "insufficient"))
MAX_RACES = 120
STAKE = 100
# Only trusted, constant error messages originating in _normalize_runners.
# Never send provider values or exception strings to the client or logs.
RUNNER_ISSUES = {
    "Bad two-factor research contract": "contract",
    "Invalid research runner": "runner_shape",
    "Factor completeness mismatch": "completeness",
    "Invalid research order": "rank_order",
    "Unassessed runner must not be ranked": "incomplete_rank",
    "Invalid missing-factor reasons": "missing_reasons",
    "Complete runner count mismatch": "summary_count",
}


def _grade(score):
    if score >= 8:
        return "S"
    if score >= 6:
        return "A"
    if score >= 4:
        return "B"
    return "C"


def _normalize_runners(research):
    runners = research.get("runners")
    if (research.get("version") != RUNNER_VERSION
            or research.get("researchOnly") is not True
            or research.get("privateOwnerOnly") is not True
            or any(research.get(k) is not False for k in (
                "officialJraVerified", "overallRankReady",
                "predictionReady", "bettingReady"))
            or not isinstance(runners, list)
            or not 0 <= len(runners) <= 18
            or research.get("runnerCount") != len(runners)):
        raise CoverageError("Bad two-factor research contract")
    numbers = set()
    normalized = []
    for r in runners:
        if (not isinstance(r, dict) or type(r.get("number")) is not int
                or not 1 <= r["number"] <= 18
                or r["number"] in numbers
                or r.get("training") not in (*GRADES, "未評価")
                or r.get("recent") not in (*GRADES, "未評価")
                or r.get("pastFourthCorner") not in OBSERVED):
            raise CoverageError("Invalid research runner")
        numbers.add(r["number"])
        trained = r["training"] in GRADES
        recent = r["recent"] in GRADES
        count = int(trained) + int(recent)
        if r.get("completeFactors") != count:
            raise CoverageError("Factor completeness mismatch")
        if count == 2:
            score = VALUES[r["training"]] + VALUES[r["recent"]]
            if type(r.get("researchOrder")) is not int or r["researchOrder"] < 1:
                raise CoverageError("Invalid research order")
        else:
            score = None
            if r.get("researchOrder") is not None:
                raise CoverageError("Unassessed runner must not be ranked")
        reasons = r.get("missingReasons", [])
        if not isinstance(reasons, list) or any(
                not isinstance(v, str) or v not in TRAINING | RECENT | {"training_unassessed", "recent_unassessed"}
                for v in reasons):
            raise CoverageError("Invalid missing-factor reasons")
        normalized.append({
            "missingReasons": reasons,
            "number": r["number"], "training": r["training"],
            "recent": r["recent"], "twoFactorGrade": _grade(score) if score is not None else "未評価",
            "pastFourthCorner": r["pastFourthCorner"], "twoFactorPoints": score,
        })
    normalized.sort(key=lambda x: (x["twoFactorPoints"] is None,
                                   -(x["twoFactorPoints"] or 0), x["number"]))
    if research.get("completeTwoFactorCount") != sum(
            x["twoFactorPoints"] is not None for x in normalized):
        raise CoverageError("Complete runner count mismatch")
    previous, rank = None, 0
    for index, horse in enumerate(normalized, 1):
        score = horse["twoFactorPoints"]
        if score is None:
            horse["comparisonRank"] = None
        else:
            if score != previous:
                rank = index
            horse["comparisonRank"] = rank
            previous = score
    return normalized


def _cutoff_tied(runners, size):
    return size < len(runners) and (
        runners[size - 1]["twoFactorPoints"]
        == runners[size]["twoFactorPoints"]
    )


def _safe_formation_sizes(runners):
    """Choose complete-score cutoffs, never number-based ties.

    A two-horse first slot is preferred even when fewer than 30 tickets
    exist. Three first horses are tried only when two cannot be selected
    without arbitrarily splitting an exact-score tie.
    This is mechanical hypothesis research, not an outcome predictor.
    """
    count = len(runners)
    options = {}
    for first_count in (2, 3):
        if first_count > count or _cutoff_tied(runners, first_count):
            continue
        candidates = []
        for second_count in range(first_count + 1, min(5, count) + 1):
            if _cutoff_tied(runners, second_count):
                continue
            for third_count in range(second_count, min(9, count) + 1):
                if _cutoff_tied(runners, third_count):
                    continue
                points = first_count * (second_count - 1) * (third_count - 2)
                if 1 <= points <= 40:
                    candidates.append((points, first_count, second_count, third_count))
        if candidates:
            options[first_count] = max(candidates)
    pair = options.get(2)
    triple = options.get(3)
    if pair:
        return pair[1:]
    # The usual two-horse first slot is impossible without arbitrarily
    # splitting an exact-score tie: then try three for a contested race.
    if triple:
        return triple[1:]
    return None


def _draft_for_race(row, research, day, now):
    if (not isinstance(row, dict) or row.get("racedate") != day
            or row.get("track") not in TRACKS.values()
            or type(row.get("race")) is not int
            or not 1 <= row["race"] <= 12):
        raise CoverageError("Invalid research programme slot")
    track, number = row["track"], row["race"]
    output = {
        "track": track, "race": number,
        "postTime": row.get("post_time"),
        "status": "hold", "reason": "missing_research",
        "runners": [], "first": [], "second": [], "third": [],
        "tickets": [], "points": 0, "amountYen": 0,
        "horseCount": row.get("headcount"),
        "researchOnly": True, "officialJraVerified": False,
        "overallPredictionReady": False, "bettingReady": False,
        "autoPurchase": False,
    }
    if research is None:
        return output
    if (not isinstance(research, dict)
            or research.get("track") != track
            or research.get("race") != number):
        raise CoverageError("Day research identity mismatch")
    try:
        runners = _normalize_runners(research)
    except CoverageError as exc:
        # A malformed horse-level research record must never create tickets
        # or prevent other, independent races from being inspected. The
        # cross-race and source identity checks above still fail closed.
        issue = RUNNER_ISSUES.get(str(exc))
        if issue is None:
            raise
        output["reason"] = "invalid_two_factor"
        output["validationIssue"] = issue
        return output
    output["runners"] = runners
    if (row.get("headcount") is not None
            and row["headcount"] != len(runners)):
        output["reason"] = "runner_count_mismatch"
        return output
    if len(runners) < 4:
        output["reason"] = "too_few_runners"
        return output
    if any(x["twoFactorPoints"] is None for x in runners):
        output["reason"] = "missing_factors"
        return output
    off_text = row.get("post_time")
    if not isinstance(off_text, str) or not re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d", off_text):
        output["reason"] = "missing_post_time"
        return output
    off = datetime.strptime(day + off_text, "%Y%m%d%H:%M").replace(tzinfo=JST)
    if now >= off:
        output["reason"] = "after_provisional_off"
        return output
    sizes = _safe_formation_sizes(runners)
    if sizes is None:
        output["reason"] = "ambiguous_equal_grade_boundary"
        return output
    a, b, c = sizes
    first = [x["number"] for x in runners[:a]]
    second = [x["number"] for x in runners[:b]]
    third = [x["number"] for x in runners[:c]]
    tickets = [[x, y, z] for x in first for y in second for z in third
               if x != y and x != z and y != z]
    if not 1 <= len(tickets) <= 40 or len({tuple(x) for x in tickets}) != len(tickets):
        raise CoverageError("Unexpected auto formation size")
    output.update({
        "status": "provisional_draft", "reason": "two_factor_only",
        "first": first, "second": second, "third": third,
        "tickets": tickets, "points": len(tickets),
        "amountYen": len(tickets) * STAKE,
    })
    return output


def build_owner_auto_drafts(programme, research_report, day, *, now=None):
    """Private same-snapshot conversion; never trust a browser-provided report."""
    if not _valid_date(day) or not isinstance(programme, list) or len(programme) > MAX_RACES:
        raise CoverageError("Invalid draft request")
    if now is None:
        now = datetime.now(JST)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise CoverageError("Timezone-aware timestamp required")
    now = now.astimezone(JST)
    if (not isinstance(research_report, dict)
            or research_report.get("version") != SOURCE_VERSION
            or research_report.get("date") != day
            or research_report.get("researchOnly") is not True
            or research_report.get("privateOwnerOnly") is not True
            or any(research_report.get(k) is not False for k in (
                "officialJraVerified", "overallRankReady", "predictionReady", "bettingReady"))
            or research_report.get("sourceReadCount") != 4
            or not isinstance(research_report.get("races"), list)
            or len(research_report["races"]) != len(programme)):
        raise CoverageError("Research snapshot mismatch")
    by_coordinate = {}
    for race in research_report["races"]:
        if not isinstance(race, dict):
            raise CoverageError("Invalid research slot")
        key = (race.get("track"), race.get("race"))
        if key in by_coordinate or race.get("status") not in ("research_only", "needs_review"):
            raise CoverageError("Invalid or duplicate research slot")
        by_coordinate[key] = race
    out = []
    seen = set()
    for row in programme:
        if not isinstance(row, dict):
            raise CoverageError("Invalid programme slot")
        key = (row.get("track"), row.get("race"))
        if key in seen or key not in by_coordinate:
            raise CoverageError("Programme and research slots differ")
        seen.add(key)
        item = by_coordinate[key]
        if item["status"] == "needs_review" and item.get("research") is not None:
            raise CoverageError("Unverified research must be null")
        output = _draft_for_race(
            row, item.get("research") if item["status"] == "research_only" else None,
            day, now)
        out.append(output)
    return {
        "version": VERSION, "date": day, "raceCount": len(out),
        "draftCount": sum(x["status"] == "provisional_draft" for x in out),
        "holdCount": sum(x["status"] == "hold" for x in out),
        "races": out, "sourceReadCount": 4, "unitYen": STAKE,
        "comparedFactors": ["調教", "近走"], "unverifiedFactors": 8,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "bettingReady": False, "autoPurchase": False,
        "policy": ("実際のJRDB β資料から2項目の仮説的S/A/B/Cを自動計算した参考並び。"
                   "全頭に2項目が揃い、候補の同点境界が曖昧でなく、"
                   "1着基本2頭（境界の同点など必要時だけ3頭）で"
                   "JRDB記載の暫定発走時刻より前のレースだけに"
                   "3連単フォーメーションの研究用下書きを提示。"
                   "調教・近走以外の8項目やJRA公式取消・確定出走馬・馬場・"
                   "発走時刻は未照合。勝率・正式総合ランク・購入推奨ではない。"
                   "1点100円換算だが購入や正式記録への保存はしない。"),
    }
