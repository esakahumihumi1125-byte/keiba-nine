"""Owner-only 5-factor/79-weight prestart formation drafts from existing history.

A separate research preview; NEVER a verified 10-factor or betting forecast.
Uses one already-fetched, already-checked bounded history snapshot with *zero*
additional paid reads. Missing grades, equal-score cutoff ties, absent/off
schedule, and stale/history-only races HOLD with no tickets. Does not save or
re-sign any existing 70/82/85-point receipts or place purchases.
"""
from datetime import datetime, timezone, timedelta
import re

from evaluation_policy import (
    POINTS, OWNER_FORMAL_FACTORS as FACTORS,
    OWNER_FORMAL_POLICY_VERSION as POLICY,
)
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import (normalize_program_rows, ProgrammeFormatError,
                                  TRACKS, RACE_KEY)
from jrdb_owner_auto_draft import _safe_formation_sizes
from owner_new_weight_five_research import (
    VERSION as SOURCE_VERSION, KEYS, WEIGHTS,
)

VERSION = "owner-research6-fivecore-drafts-1"
STAKE = 100
JST = timezone(timedelta(hours=9))
UNKNOWN = "未評価"
assert sum(WEIGHTS.values()) == 79
assert sum(FACTORS.values()) == 100
assert set(KEYS) == set(WEIGHTS)


def _check_report(report):
    if (not isinstance(report, dict)
            or report.get("version") != SOURCE_VERSION
            or report.get("policyVersion") != POLICY
            or report.get("sourcePolicyVersion") != "research-5"
            or report.get("factorWeights") != WEIGHTS
            or report.get("observedWeightTotal") != 79
            or report.get("factorGradesVerified") != 0
            or report.get("formalScoreReady") is not False
            or report.get("overallPredictionReady") is not False
            or report.get("officialJraVerified") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("historicalBandsNotCalibrated") is not True
            or report.get("resultVerified") is not False
            or report.get("extraProviderCalls") != 0
            or not isinstance(report.get("races"), list)
            or len(report["races"]) > 120
            or report.get("raceCount") != len(report["races"])):
        raise CoverageError("Untrusted five-factor research contract")
    index = {}
    for race in report["races"]:
        if (not isinstance(race, dict)
                or not isinstance(race.get("track"), str)
                or type(race.get("race")) is not int
                or not 1 <= race["race"] <= 12
                or (race["track"], race["race"]) in index
                or race.get("researchOnly") is not True
                or race.get("formalGradeReady") is not False
                or race.get("trifectaReady") is not False
                or race.get("comparisonIsFormalRank") is not False
                or not isinstance(race.get("horses"), list)
                or len(race["horses"]) > 18
                or race.get("runnerCount") != len(race["horses"])):
            raise CoverageError("Five-factor race mismatch")
        index[race["track"], race["race"]] = race
    return index


def _check_horses(race):
    output, missing_by, seen = [], dict.fromkeys(KEYS, 0), set()
    if (not isinstance(race.get("missingByFactor"), dict)
            or set(race["missingByFactor"]) != set(KEYS)
            or not isinstance(race.get("comparisonGroups"), list)
            or not isinstance(race.get("unassessedNumbers"), list)):
        raise CoverageError("Invalid five-factor research metadata")
    for h in race["horses"]:
        if (not isinstance(h, dict)
                or type(h.get("number")) is not int
                or not 1 <= h["number"] <= 18 or h["number"] in seen
                or not isinstance(h.get("bands"), dict)
                or set(h["bands"]) != set(KEYS)
                or not isinstance(h.get("missing"), list)
                or h.get("formalScore100") is not None
                or h.get("formalGrade") != UNKNOWN
                or h.get("formalRank") is not None
                or h.get("scoreIsCalibrated") is not False
                or h.get("bettingReady") is not False):
            raise CoverageError("Invalid five-factor runner")
        seen.add(h["number"])
        bands = h["bands"]
        if any(v not in (*POINTS, UNKNOWN) for v in bands.values()):
            raise CoverageError("Unknown five-factor research band")
        missing = [k for k in KEYS if bands[k] == UNKNOWN]
        for key in missing:
            missing_by[key] += 1
        raw = (None if missing else sum(
            WEIGHTS[k] * POINTS[bands[k]] for k in KEYS))
        if (h["missing"] != missing
                or h.get("observedFactorCount") != 5 - len(missing)
                or h.get("rawThirdPoints") != raw
                or h.get("evidenceScore79") != (
                    None if raw is None else round(raw / 3, 2))):
            raise CoverageError("Five-factor runner score mismatch")
        output.append({
            "number": h["number"], "weightedResearchPoints": raw,
            "research79": None if raw is None else round(raw / 3, 2),
        })
    observed = [h for h in output if h["weightedResearchPoints"] is not None]
    groups = {}
    for h in observed:
        groups.setdefault(h["weightedResearchPoints"], []).append(h["number"])
    expected = [
        {"rawThirdPoints": k, "numbers": sorted(groups[k])}
        for k in sorted(groups, reverse=True)
    ]
    unknown = sorted(h["number"] for h in output
                     if h["weightedResearchPoints"] is None)
    if (race["missingByFactor"] != missing_by
            or race["comparisonGroups"] != expected
            or race["unassessedNumbers"] != unknown
            or race.get("completeObserved") != len(observed)):
        raise CoverageError("Five-factor cohort summary mismatch")
    return sorted(output, key=lambda h: (
        h["weightedResearchPoints"] is None,
        -(h["weightedResearchPoints"] or 0), h["number"]
    ))


def _normal_programme(programme, day):
    """Preserve HH:MM schedule from already-normalized /tra output.

    Service gives normalize_program_rows() output while offline tests and
    direct provider invocations may give raw 4-digit HHMM /tra fields.
    Running the original normalizer twice drops HH:MM to None, making every
    otherwise-valid research race appear to have no post time.
    """
    if not isinstance(programme, list) or len(programme) > 120:
        raise CoverageError("Invalid programme roster")
    normalized = [isinstance(row, dict) and (
        row.get("programmeOnly") is True
        or isinstance(row.get("post_time"), str) and
        bool(re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", row["post_time"])))
        for row in programme]
    if any(normalized):
        if not all(normalized):
            raise CoverageError("Mixed raw and normalized JRDB programme")
        observed, used = [], set()
        for row in programme:
            key = row.get("racekey")
            track, race = row.get("track"), row.get("race")
            if (not isinstance(key, str) or not RACE_KEY.fullmatch(key)
                    or key[:2] not in TRACKS
                    or track != TRACKS[key[:2]]
                    or type(race) is not int or not 1 <= race <= 12
                    or key[6:] != f"{race:02d}"
                    or row.get("racedate") != day
                    or (track, race) in used
                    or (row.get("headcount") is not None
                        and (type(row["headcount"]) is not int
                             or not 0 <= row["headcount"] <= 18))
                    or (row.get("post_time") is not None and
                        (not isinstance(row["post_time"], str)
                         or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",
                                             row["post_time"])))):
                raise CoverageError("Invalid normalized programme identity")
            used.add((track, race))
            observed.append(row)
        return observed
    try:
        return normalize_program_rows(programme, day)
    except (ProgrammeFormatError, TypeError):
        raise CoverageError("Invalid raw JRDB programme for research draft") from None


def build_research6_five_drafts(programme, study, day, *, now=None):
    """Build up to 40 *unverified* owner-research tickets per future race.

    An explicit prestart local clock is required for every non-hold output.
    This code never accepts browser-asserted official result/starter status.
    """
    if not _valid_date(day):
        raise CoverageError("Invalid research draft date")
    normalized = _normal_programme(programme, day)
    by_race = _check_report(study)
    if {(r["track"], r["race"]) for r in normalized} != set(by_race):
        raise CoverageError("Five-factor draft race set differs from schedule")
    if now is None:
        now = datetime.now(JST)
    if (not isinstance(now, datetime) or now.tzinfo is None
            or now.utcoffset() is None):
        raise CoverageError("Trusted timezone-aware clock required")
    now = now.astimezone(JST)
    output = []
    for program in normalized:
        coord = program["track"], program["race"]
        race = by_race[coord]
        slot = {
            "track": coord[0], "race": coord[1],
            "postTime": program["post_time"],
            "status": "hold", "reason": "incomplete_five_factors",
            "first": [], "second": [], "third": [], "tickets": [],
            "points": 0, "amountYen": 0,
            "completeObserved": race["completeObserved"],
            "runnerCount": race["runnerCount"],
            "rankedResearch": [],
            "researchOnly": True, "overallPredictionReady": False,
            "officialJraVerified": False, "bettingReady": False,
            "autoPurchase": False,
        }
        t = program["post_time"]
        if not isinstance(t, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", t):
            slot["reason"] = "missing_provisional_off"
            output.append(slot)
            continue
        off = datetime.strptime(day + t, "%Y%m%d%H:%M").replace(tzinfo=JST)
        if now >= off:
            slot["reason"] = "past_provisional_off"
            output.append(slot)
            continue
        if (program["headcount"] is None
                or program["headcount"] != race["runnerCount"]):
            slot["reason"] = "runner_count_unconfirmed"
            output.append(slot)
            continue
        runners = _check_horses(race)
        if len(runners) < 4:
            slot["reason"] = "too_few_runners"
            output.append(slot)
            continue
        if any(h["weightedResearchPoints"] is None for h in runners):
            slot["reason"] = "incomplete_five_factors"
            output.append(slot)
            continue
        sizes = _safe_formation_sizes(runners)
        if sizes is None:
            slot["reason"] = "tied_cutoff"
            output.append(slot)
            continue
        a, b, c = sizes
        first = [r["number"] for r in runners[:a]]
        second = [r["number"] for r in runners[:b]]
        third = [r["number"] for r in runners[:c]]
        tickets = [[x, y, z] for x in first for y in second for z in third
                   if x != y and x != z and y != z]
        if not (1 <= len(tickets) <= 40
                and len({tuple(t) for t in tickets}) == len(tickets)):
            raise CoverageError("Research formation deduplication failed")
        slot.update({
            "status": "five_factor_research_draft",
            "reason": "unverified_five_factor_hypotheses",
            "first": first, "second": second, "third": third,
            "tickets": tickets, "points": len(tickets),
            "amountYen": len(tickets) * STAKE,
            "rankedResearch": [
                {"number": h["number"], "research79": h["research79"],
                 "comparisonRank": (1 + sum(
                     x["weightedResearchPoints"] > h["weightedResearchPoints"]
                     for x in runners))}
                for h in runners
            ],
        })
        output.append(slot)
    reasons = {}
    for r in output:
        if r["status"] == "hold":
            reasons[r["reason"]] = reasons.get(r["reason"], 0) + 1
    return {
        "version": VERSION, "policyVersion": POLICY,
        "date": day, "raceCount": len(output),
        "draftCount": sum(r["status"] == "five_factor_research_draft"
                          for r in output),
        "holdCount": sum(r["status"] == "hold" for r in output),
        "holdReasons": reasons, "races": output,
        "unitYen": STAKE, "researchFactorWeight": 79,
        "factorWeights": dict(WEIGHTS), "remainingUnassessedWeight": 21,
        "officialJraVerified": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "overallPredictionReady": False, "bettingReady": False,
        "autoPurchase": False, "actualPurchase": False,
        "extraProviderCalls": 0,
        "changesExistingReceipts": False,
        "changesExistingTickets": False,
        "changesExistingRoi": False,
        "note": (
            "旧85点研究から同一資料の新配点79点で発走前だけ参考3連単下書きを作成。"
            "全頭5項目が揃う時のみ、同点境界を馬番で恣意的に分けない。"
            "残り21点とJRA公式出馬・取消・馬場・確定時刻、採点性能は未検証。"
            "保存済み旧署名と実購入・回収率は変更しません。"
        )
    }
