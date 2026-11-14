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
from jrdb_owner_day_research import REVIEW_STAGES
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from jrdb_owner_runner_research import VALUES
from evaluation_policy import FACTORS, POLICY_VERSION

# Experimental TWO-FACTOR priority, never a completed 100-point rating.
# S=3, A=2, B=1, C=0 and 30:3 weights reflect owner's chosen policy.
# Other eight factors MUST NOT be assigned default grades.
PROVISIONAL_WEIGHTED_MAX = 3 * (FACTORS["training"] + FACTORS["recent"])
assert FACTORS["training"] == 30 and FACTORS["recent"] == 3
assert PROVISIONAL_WEIGHTED_MAX == 99

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
# Fixed codes for the fail-closed, whole-day contract. These map only
# literal errors authored in this module; never include raw JRDB data.
DAY_DRAFT_ISSUES = {
    "Invalid draft request": "bad_request_contract",
    "Timezone-aware timestamp required": "server_clock",
    "Research snapshot mismatch": "research_header",
    "Invalid research slot": "research_slot",
    "Invalid or duplicate research slot": "research_slot_duplicate",
    "Invalid programme slot": "programme_slot",
    "Programme and research slots differ": "race_set_mismatch",
    "Unverified research must be null": "unverified_research",
    "Invalid research programme slot": "race_programme_identity",
    "Day research identity mismatch": "race_research_identity",
    "Unexpected auto formation size": "formation_size",
}

# Fixed-only operator buckets. The server log may report aggregate *counts*,
# never a race ID, horse ID, provider value, credential or source exception.
# Other/future internal hold codes are collapsed to "other".
HOLD_LOG_CODES = (
    "after_provisional_off", "provider_withdrawal", "missing_research",
    "missing_factors", "invalid_two_factor",
    "ambiguous_equal_grade_boundary", "runner_count_mismatch",
    "too_few_runners", "missing_post_time", "unconfirmed_runner_count",
    "archived_earlier_draft",
)


def compact_hold_diagnostics(report):
    """Private log-safe aggregate for already-produced owner draft reports.

    Never accept or log arbitrary source text as a reason. A malformed
    report yields a fixed placeholder rather than breaking a signed forecast.
    """
    if not isinstance(report, dict):
        return "invalid"
    reasons, total = report.get("holdReasons"), report.get("holdCount")
    if (not isinstance(reasons, dict) or type(total) is not int
            or not 0 <= total <= MAX_RACES
            or any(type(count) is not int or count < 0 or count > MAX_RACES
                   for count in reasons.values())
            or sum(reasons.values()) != total):
        return "invalid"
    known = [(key, reasons.get(key, 0)) for key in HOLD_LOG_CODES
             if reasons.get(key, 0)]
    other = total - sum(count for _, count in known)
    if other:
        known.append(("other", other))
    return ",".join(f"{key}:{count}" for key, count in known) if known else "none"


def compact_factor_shortage_diagnostics(report):
    """Log-safe training/recent availability counts from the SAME 4 reads.

    Only aggregate runner counts from prestart missing-factor holds. No
    horse numbers, provider values or source text, and no additional reads.
    A malformed report becomes a fixed error marker, never a log leak.
    """
    if (not isinstance(report, dict)
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > MAX_RACES):
        return "invalid"
    affected = training_missing = recent_missing = both_missing = 0
    for race in report["races"]:
        if not isinstance(race, dict):
            return "invalid"
        if race.get("status") != "hold" or race.get("reason") != "missing_factors":
            continue
        runners = race.get("runners")
        if (not isinstance(runners, list) or len(runners) > 18):
            return "invalid"
        for horse in runners:
            if (not isinstance(horse, dict)
                    or horse.get("training") not in (*GRADES, "未評価")
                    or horse.get("recent") not in (*GRADES, "未評価")):
                return "invalid"
            t = horse["training"] == "未評価"
            r = horse["recent"] == "未評価"
            if t or r:
                affected += 1
                training_missing += int(t)
                recent_missing += int(r)
                both_missing += int(t and r)
    if not affected:
        return "none"
    return ("horses:%d,training:%d,recent:%d,both:%d" %
            (affected, training_missing, recent_missing, both_missing))


# Fixed, anonymized reasons are safe for developer logs. Never include race,
# horse, source row, timestamp or provider error text in this diagnostic.
MISSING_LOG_CODES = (
    "no_linked_recent_record", "no_usable_history",
    "only_one_usable_run", "insufficient_scored_runs",
    "recent_unassessed", "no_linked_training_record",
    "missing_training_indices", "training_unassessed",
)


def compact_missing_reason_diagnostics(report):
    """Count WHY missing factors held races, from already loaded data.

    This cannot distinguish a JRDB beta publication gap from a truly
    inapplicable record. It is a no-cost debugging summary, not new evidence
    or permission to fabricate missing grades.
    """
    if (not isinstance(report, dict)
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > MAX_RACES):
        return "invalid"
    tally = dict.fromkeys(MISSING_LOG_CODES, 0)
    count = 0
    for race in report["races"]:
        if not isinstance(race, dict):
            return "invalid"
        if race.get("status") != "hold" or race.get("reason") != "missing_factors":
            continue
        rows = race.get("runners")
        if not isinstance(rows, list) or len(rows) > 18:
            return "invalid"
        for horse in rows:
            if (not isinstance(horse, dict)
                    or horse.get("training") not in (*GRADES, "未評価")
                    or horse.get("recent") not in (*GRADES, "未評価")
                    or not isinstance(horse.get("missingReasons"), list)
                    or len(horse["missingReasons"]) > 4):
                return "invalid"
            reasons = horse["missingReasons"]
            if any(type(label) is not str or label not in MISSING_LOG_CODES
                   for label in reasons):
                return "invalid"
            for factor, candidates, fallback in (
                ("recent", MISSING_LOG_CODES[:4], "recent_unassessed"),
                ("training", MISSING_LOG_CODES[5:7], "training_unassessed"),
            ):
                if horse[factor] != "未評価":
                    continue
                found = [label for label in candidates if label in reasons]
                label = found[0] if len(found) == 1 else fallback
                tally[label] += 1
                count += 1
    if not count:
        return "none"
    return ",".join(f"{code}:{tally[code]}" for code in MISSING_LOG_CODES
                    if tally[code])


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


def _safe_recent_observations(raw):
    """Validate public count-only fields before returning owner draft JSON.

    This optional (backward-compatible) observation gives no ability score
    and may never affect the weighted two-factor sort or signed tickets.
    """
    if raw is None:
        return None
    fields = ("datedRuns", "completedRuns", "topThreeObserved",
              "fourthCornerObserved", "late3fObserved")
    if not isinstance(raw, dict) or set(raw) != set(fields):
        raise CoverageError("Invalid redacted recent evidence")
    dated, complete, top, corner, late = (raw[k] for k in fields)
    if (any(type(v) is not int for v in
            (dated, complete, top, corner, late))
            or not 0 <= dated <= 5
            or not 0 <= complete <= dated
            or not 0 <= top <= min(3, complete)
            or not 0 <= corner <= min(3, dated)
            or not 0 <= late <= min(3, dated)):
        raise CoverageError("Invalid redacted recent evidence")
    return dict(raw)


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
            # Retain old equally-weighted 2-factor tally ONLY as a
            # backward-compatible diagnostic, not as the order/ticket key.
            score = VALUES[r["training"]] + VALUES[r["recent"]]
            weighted = (
                (VALUES[r["training"]] - 1) * FACTORS["training"]
                + (VALUES[r["recent"]] - 1) * FACTORS["recent"]
            )
            if type(r.get("researchOrder")) is not int or r["researchOrder"] < 1:
                raise CoverageError("Invalid research order")
        else:
            score = None
            weighted = None
            if r.get("researchOrder") is not None:
                raise CoverageError("Unassessed runner must not be ranked")
        reasons = r.get("missingReasons", [])
        if not isinstance(reasons, list) or any(
                not isinstance(v, str) or v not in TRAINING | RECENT | {"training_unassessed", "recent_unassessed"}
                for v in reasons):
            raise CoverageError("Invalid missing-factor reasons")
        recent_observed = _safe_recent_observations(r.get("recentObserved"))
        normalized.append({
            "missingReasons": reasons,
            "number": r["number"], "training": r["training"],
            "recent": r["recent"], "twoFactorGrade": _grade(score) if score is not None else "未評価",
            "pastFourthCorner": r["pastFourthCorner"], "twoFactorPoints": score,
            "weightedResearchPoints": weighted,
            "recentObserved": recent_observed,
        })
    normalized.sort(key=lambda x: (x["weightedResearchPoints"] is None,
                                   -(x["weightedResearchPoints"] or 0),
                                   x["number"]))
    if research.get("completeTwoFactorCount") != sum(
            x["twoFactorPoints"] is not None for x in normalized):
        raise CoverageError("Complete runner count mismatch")
    previous, rank = None, 0
    for index, horse in enumerate(normalized, 1):
        score = horse["weightedResearchPoints"]
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
        runners[size - 1]["weightedResearchPoints"]
        == runners[size]["weightedResearchPoints"]
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
        if not candidates and first_count == 2 and count >= 6:
            # Safe exceptional rescue for an otherwise HELD race.
            # Example: ranks 3..6 have the SAME 2-factor score, so the
            # old second<=5 cutoff would arbitrarily exclude one runner.
            # Expanding second and third to SIX keeps every tied horse and
            # produces exactly 2*(6-1)*(6-2)=40 distinct tickets.
            # This branch is *only* considered when the existing <=5
            # formation produces no candidate; previously emitted tickets
            # are not reordered or replaced.
            second_count = 6
            if not _cutoff_tied(runners, second_count):
                third_count = 6
                points = first_count * (second_count - 1) * (third_count - 2)
                if points <= 40:
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
    # Time-gate BEFORE parsing today's research. After the provisional off
    # time, a new HTTP request must not generate or even display a ranking
    # that could be mistaken for a genuine pre-race assessment.
    off_text = row.get("post_time")
    if not isinstance(off_text, str) or not re.fullmatch(
            r"(?:[01]\d|2[0-3]):[0-5]\d", off_text):
        output["reason"] = "missing_post_time"
        return output
    off = datetime.strptime(day + off_text, "%Y%m%d%H:%M").replace(tzinfo=JST)
    if now >= off:
        output["reason"] = "after_provisional_off"
        return output
    if research is None:
        return output
    # The provider's declared roster must be present to cross-check /tky.
    # Never turn an absent or zero /tra count into an implicit all-starter
    # confirmation simply because some /tky horse numbers were observed.
    # Other independent races can continue without new paid source reads.
    if (type(row.get("headcount")) is not int
            or not 1 <= row["headcount"] <= 18):
        output["reason"] = "unconfirmed_runner_count"
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
            or research_report.get("sourceReadCount") not in (1, 4)
            or (research_report.get("sourceReadCount") == 1 and programme)
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
        if item["status"] == "needs_review":
            if item.get("research") is not None:
                raise CoverageError("Unverified research must be null")
            # Older research snapshots can lack the optional fixed code.
            stage = item.get("reviewStage")
            if stage is not None and (
                    not isinstance(stage, str) or stage not in REVIEW_STAGES):
                raise CoverageError("Invalid research review stage")
            kind = item.get("reviewKind")
            if kind is not None and (
                    kind != "provider_withdrawal" or stage != "entries"):
                raise CoverageError("Invalid provider withdrawal review")
        elif "reviewStage" in item or "reviewKind" in item:
            raise CoverageError("Unexpected review flags for complete research")
        output = _draft_for_race(
            row, item.get("research") if item["status"] == "research_only" else None,
            day, now)
        # Never disclose a post-off research stage, or turn a hold into a
        # ticket. This is a diagnostic label for a PRESTART held race only.
        if (output["reason"] == "missing_research"
                and item.get("reviewKind") == "provider_withdrawal"):
            output["reason"] = "provider_withdrawal"
        elif (output["reason"] == "missing_research"
              and item.get("reviewStage") in REVIEW_STAGES):
            output["reviewStage"] = item["reviewStage"]
        out.append(output)
    reasons = {}
    for race in out:
        if race["status"] == "hold":
            code = race["reason"]
            reasons[code] = reasons.get(code, 0) + 1
    return {
        "version": VERSION, "date": day, "raceCount": len(out),
        "draftCount": sum(x["status"] == "provisional_draft" for x in out),
        "holdCount": sum(x["status"] == "hold" for x in out),
        "holdReasons": reasons,
        "races": out, "sourceReadCount": research_report["sourceReadCount"],
        "unitYen": STAKE,
        "weightedResearchOrder": "training30_recent3",
        "weightedResearchMax": PROVISIONAL_WEIGHTED_MAX,
        "weightedResearchPolicy": POLICY_VERSION,
        "comparedFactors": ["調教", "近走"], "unverifiedFactors": 8,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallPredictionReady": False,
        "bettingReady": False, "autoPurchase": False,
        "policy": ("実際のJRDB β資料から2項目の仮説的S/A/B/Cを自動計算した参考並び。"
                   "全頭に2項目が揃い、候補の同点境界が曖昧でなく、"
                   "1着基本2頭（境界の同点など必要時だけ3頭）で"
                   "JRDB記載の暫定発走時刻より前のレースだけに"
                   "3連単フォーメーションの研究用下書きを提示。"
                   "2項目の仮順位では調教30：近走3の重みを適用し、"
                   "近走不振だけで調教好調馬を下位に落とさない。"
                   "調教・近走以外の8項目やJRA公式取消・確定出走馬・馬場・"
                   "発走時刻は未照合。勝率・正式総合ランク・購入推奨ではない。"
                   "1点100円換算だが購入や正式記録への保存はしない。"),
    }
