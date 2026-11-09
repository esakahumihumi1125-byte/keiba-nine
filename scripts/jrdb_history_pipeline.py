"""Offline-first bounded owner-only historical evidence preparation.

This module has NO JRDB imports or network configuration. Explicit injected
callables are the only way to retrieve histories. Never use it in GitHub Pages,
public actions, public feeds or any unauthenticated route. Licensed source rows
remain local to the caller; only redacted race totals are returned.

The research output is not a real-data suitability grade or wager.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import (
    audit_evidence_coverage, HORSE_ID, NUMBER, KEY, _valid_date
)
from jrdb_ten_factor_materials import combine_ten_factor_materials
from jrdb_program_preview import normalize_program_rows, ProgrammeFormatError, TRACKS
from jrdb_going_history import (
    build_going_history_observations, summarize_going_history_observations
)
from jrdb_history_evidence_quality import summarize_history_evidence_quality
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_private_factor_bridge import build_private_factor_matrix
from jrdb_course_ground_factor_bridge import (
    enrich_course_ground_matrix, summarize_course_ground_matrix,
    summarize_owner_runner_course_going,
)
from jrdb_entry_rotation_materials import enrich_entry_materials_matrix
from jrdb_personnel_body_materials import enrich_personnel_body_matrix
from jrdb_complete_factor_materials import combine_ten_factor_observations
from jrdb_real_assessment_preflight import audit_real_evaluation_preflight
from jrdb_experimental_condition_grades import hypothesis_from_owner_history
from jrdb_experimental_pace_scenarios import hypothesize_owner_pace
from jrdb_experimental_rebound_review import build_rebound_context_review
from jrdb_five_factor_hypotheses import combine_five_factor_hypotheses
from jrdb_ten_factor_source_inventory import ten_factor_source_inventory
from owner_three_core_research import three_core_research
from owner_four_core_research import four_core_research
from owner_five_core_research import five_core_research
from owner_new_weight_five_research import new_weight_five_research
from owner_remaining21_source_gaps import remaining21_source_gaps
from owner_research6_uncertainty import research6_uncertainty_intervals
from owner_research6_five_drafts import build_research6_five_drafts
from owner_pedigree_evidence_preflight import pedigree_evidence_preflight
from owner_support_six_preflight import support_six_preflight

VERSION = "bounded-history-1"
MAX_LOOKUPS_PER_RUN = 12
DEFAULT_LOOKUPS_PER_RUN = 8


class HistoryFetchError(ValueError):
    """Safe generic error: no keys, credentials or source response bodies."""


def _verify_limit(value):
    if type(value) is not int or not 1 <= value <= MAX_LOOKUPS_PER_RUN:
        raise HistoryFetchError("History budget must be between 1 and 12")
    return value


def plan_bounded_history(programme, entries, previous, requested_date,
                         limit=DEFAULT_LOOKUPS_PER_RUN):
    """Private plan: newest referenced racekeys first, one per unique past race.

    No date-range queries, no lookups by arbitrary input, no implicit retries.
    This plan contains private racekeys and MUST NOT be sent to browsers/logs.
    """
    _verify_limit(limit)
    audit_evidence_coverage(programme, entries, [], previous, requested_date)
    by_number = {(r["racekey"], r["horse_number"]) for r in entries}
    by_id = {(r["racekey"], r["horse_id"]): r["horse_number"]
             for r in entries if r.get("horse_id")}
    current_keys = {r["racekey"] for r in programme}
    referenced = {}
    unkeyed = 0
    for row in previous:
        current = row["racekey"]
        number = row.get("horse_number")
        hid = row.get("horse_id")
        matched_number = (isinstance(number, str) and NUMBER.fullmatch(number)
                          and (current, number) in by_number)
        matched_id = (isinstance(hid, str) and HORSE_ID.fullmatch(hid)
                      and (current, hid) in by_id)
        if not (matched_number or matched_id):
            continue  # Anonymous source rows are not a basis for paid lookups.
        for i in range(1, 6):
            prefix = f"race_back_{i}_"
            date, racekey = row.get(prefix + "racedate"), row.get(prefix + "racekey")
            if not date and not racekey:
                continue
            if not _valid_date(date) or date >= requested_date:
                raise CoverageError("Previous race date invalid")
            if racekey is None or racekey == "":
                unkeyed += 1
                continue  # Historical key unavailable; do not guess.
            if (not isinstance(racekey, str) or not KEY.fullmatch(racekey)
                    or racekey[:2] not in TRACKS
                    or not racekey[6:].isdigit()
                    or not 1 <= int(racekey[6:]) <= 12
                    or racekey in current_keys):
                raise CoverageError("Invalid historical racekey")
            if racekey in referenced and referenced[racekey] != date:
                raise CoverageError("Conflicting dates for historical racekey")
            referenced[racekey] = date
    ordered = sorted(referenced.items(), key=lambda item: (item[1], item[0]), reverse=True)
    return {
        "privateSelected": tuple(ordered[:limit]),
        "referencedCount": len(ordered),
        "unkeyedPreviousRuns": unkeyed,
        "selectedCount": min(len(ordered), limit),
        "deferredCount": max(0, len(ordered) - limit),
        "maxDraCalls": min(len(ordered), limit),
        "maxDkaCalls": min(len(ordered), limit),
        "historyComplete": len(ordered) <= limit and unkeyed == 0,
        "version": VERSION,
    }


def _one_programme(rows, key, date):
    if not isinstance(rows, list) or len(rows) > 1:
        raise HistoryFetchError("Historical programme response has unexpected shape")
    if not rows:
        return None
    if (not isinstance(rows[0], dict) or rows[0].get("racekey") != key
            or rows[0].get("racedate") != date):
        raise HistoryFetchError("Historical programme identifier mismatch")
    try:
        normalize_program_rows(rows, date)
    except ProgrammeFormatError:
        raise HistoryFetchError("Historical programme validation failed") from None
    return rows[0]


def _one_going(rows, key, date):
    if not isinstance(rows, list) or len(rows) > 1:
        raise HistoryFetchError("Historical going response has unexpected shape")
    if not rows:
        return None
    if (not isinstance(rows[0], dict) or rows[0].get("holdingkey") != key[:6]
            or rows[0].get("racedate") != date):
        raise HistoryFetchError("Historical going identifier mismatch")
    return rows[0]


def run_bounded_history_audit(programme, entries, previous,
                              current_conditions, requested_date,
                              *, fetch_dra, fetch_dka,
                              limit=DEFAULT_LOOKUPS_PER_RUN,
                              training=None):
    """Explicit, bounded private lookup with redacted response only.

    The caller supplies owner-approved *private* fetch functions after securing
    its server and credentials. This module is never a scheduled job.
    On any malformed/provider-error response, discard all partial output.
    A missing row remains unknown and is never used as a negative signal.
    """
    if not callable(fetch_dra) or not callable(fetch_dka):
        raise HistoryFetchError("Private source functions are required")
    plan = plan_bounded_history(programme, entries, previous, requested_date, limit)
    # Current-day training evidence is an optional private input. Validate its
    # horse/date identity BEFORE any paid historical requests.
    try:
        sources = audit_evidence_coverage(
            programme, entries, [] if training is None else training,
            previous, requested_date
        )
    except (CoverageError, ValueError, TypeError, KeyError):
        raise HistoryFetchError("Current evidence validation failed") from None
    # Reject malformed current conditions before any billable historical request.
    try:
        build_going_history_observations(
            programme, entries, previous, [], [], current_conditions, requested_date
        )
    except (CoverageError, ValueError, TypeError, KeyError):
        raise HistoryFetchError("Current evidence validation failed") from None
    historical, conditions = [], []
    seen_holdings = set()
    dra_calls = dka_calls = missing = missing_going = 0
    for key, date in plan["privateSelected"]:
        try:
            dra_calls += 1
            past = _one_programme(fetch_dra(key), key, date)
        except HistoryFetchError:
            raise
        except Exception:
            raise HistoryFetchError("Private historical programme lookup failed") from None
        if past is None:
            missing += 1
            continue
        historical.append(past)
        holding = key[:6], date
        if holding in seen_holdings:
            continue
        seen_holdings.add(holding)
        try:
            dka_calls += 1
            old_going = _one_going(fetch_dka(key), key, date)
        except HistoryFetchError:
            raise
        except Exception:
            raise HistoryFetchError("Private historical going lookup failed") from None
        if old_going is not None:
            conditions.append(old_going)
        else:
            missing_going += 1
    # Both auditors recheck all source-identity joins. Provider rows never
    # escape the scope of this function as a published response.
    try:
        observations = build_going_history_observations(
            programme, entries, previous, historical, conditions,
            current_conditions, requested_date
        )
        safe_summary = summarize_going_history_observations(observations)
        quality_summary = summarize_history_evidence_quality(observations)
        is_history_complete = (
            plan["historyComplete"] and missing == 0 and missing_going == 0
        )
        materials = combine_ten_factor_materials(
            sources, quality_summary,
            bounded_history_complete=is_history_complete
        )
        private_matrix = build_private_factor_matrix(
            build_training_hints(
                programme, entries, [] if training is None else training,
                requested_date,
            ),
            build_recent_hints(programme, entries, previous, requested_date),
        )
        pace_scenarios = hypothesize_owner_pace(private_matrix)
        course_matrix = enrich_course_ground_matrix(
            private_matrix, observations, history_complete=is_history_complete
        )
        history_factor_summary = summarize_course_ground_matrix(course_matrix)
        runner_history = summarize_owner_runner_course_going(
            course_matrix, observations
        )
        historical_bands = hypothesis_from_owner_history(runner_history)
        five_factor_view = combine_five_factor_hypotheses(
            private_matrix, historical_bands, pace_scenarios
        )
        rebound_review = build_rebound_context_review(
            private_matrix, runner_history, historical_bands, pace_scenarios
        )
        entry_matrix = enrich_entry_materials_matrix(
            private_matrix, programme, entries, previous, requested_date
        )
        personnel_matrix = enrich_personnel_body_matrix(
            entry_matrix, programme, entries, requested_date
        )
        ten_source_inventory = ten_factor_source_inventory(
            five_factor_view, personnel_matrix
        )
        three_core_view = three_core_research(
            five_factor_view, ten_source_inventory
        )
        four_core_view = four_core_research(
            five_factor_view, ten_source_inventory, three_core_view
        )
        five_core_view = five_core_research(
            five_factor_view, ten_source_inventory,
            three_core_view, four_core_view
        )
        new_weight_five_view = new_weight_five_research(five_core_view)
        new_weight_remaining = remaining21_source_gaps(
            new_weight_five_view, ten_source_inventory
        )
        new_weight_sensitivity = research6_uncertainty_intervals(
            new_weight_five_view, new_weight_remaining
        )
        five_research_drafts = build_research6_five_drafts(
            programme, new_weight_five_view, requested_date
        )
        pedigree_preflight = pedigree_evidence_preflight(ten_source_inventory)
        support_six = support_six_preflight(ten_source_inventory)
        all_factor_materials = combine_ten_factor_observations(
            course_matrix, personnel_matrix
        )
        readiness_preflight = audit_real_evaluation_preflight(
            all_factor_materials, quality_summary,
            history_complete=is_history_complete,
        )
        if (readiness_preflight["raceCount"] != materials["raceCount"]
                or readiness_preflight["realGradeReady"] is not False
                or readiness_preflight["realPredictionReady"] is not False
                or readiness_preflight["purchaseReady"] is not False
                or history_factor_summary["raceCount"] != materials["raceCount"]
                or history_factor_summary["raceCount"] != quality_summary["raceCount"]
                or all_factor_materials["raceCount"] != materials["raceCount"]
                or all_factor_materials["predictionReady"] is not False
                or all_factor_materials["bettingReady"] is not False
                or any(
                    not any(
                        combined["track"] == history["track"]
                        and combined["race"] == history["race"]
                        and combined["runnerCount"] == history["runnerCount"]
                        and combined["runnersWithComparableCourse"]
                            == history["runnersWithComparableCourse"]
                        and combined["runnersWithKnownGoingComparable"]
                            == history["runnersWithKnownGoingComparable"]
                        for history in history_factor_summary["races"]
                    )
                    for combined in all_factor_materials["races"]
                )
                or any(
                    not any(
                        row["track"] == grade["track"]
                        and row["race"] == grade["race"]
                        and row["runnerCount"] == grade["runnerCount"]
                        and row["runnersWithComparableCourse"]
                            == grade["courseComparableSamples"]["oneOrTwo"]
                            + grade["courseComparableSamples"]["threePlus"]
                        and row["runnersWithKnownGoingComparable"]
                            == grade["knownGoingComparableSamples"]["oneOrTwo"]
                            + grade["knownGoingComparableSamples"]["threePlus"]
                        for grade in quality_summary["races"]
                    )
                    for row in history_factor_summary["races"]
                )):
            raise HistoryFetchError("Historical factor summaries disagree")
    except (CoverageError, ValueError, KeyError, TypeError):
        raise HistoryFetchError("Private historical evidence validation failed") from None
    return {
        "version": VERSION,
        "date": requested_date,
        "referencedPastRaces": plan["referencedCount"],
        "unkeyedPreviousRuns": plan["unkeyedPreviousRuns"],
        "selectedPastRaces": plan["selectedCount"],
        "deferredPastRaces": plan["deferredCount"],
        "unavailablePastProgrammes": missing,
        "unavailablePastConditions": missing_going,
        "draCalls": dra_calls,
        "dkaCalls": dka_calls,
        "maxTotalCalls": 2 * limit,
        "historyComplete": is_history_complete,
        "goingSummary": safe_summary,
        "evidenceQuality": quality_summary,
        "tenFactorMaterials": materials,
        "privateHistoryFactors": history_factor_summary,
        "ownerRunnerHistory": runner_history,
        "historicalEvidenceBands": historical_bands,
        "paceScenarioHypotheses": pace_scenarios,
        "fiveFactorHypotheses": five_factor_view,
        "tenFactorSourceInventory": ten_source_inventory,
        "threeCoreResearch": three_core_view,
        "fourCoreResearch": four_core_view,
        "fiveCoreResearch": five_core_view,
        "newWeightFiveResearch": new_weight_five_view,
        "remaining21SourceGaps": new_weight_remaining,
        "research6Uncertainty": new_weight_sensitivity,
        "research6FiveDrafts": five_research_drafts,
        "pedigreeEvidencePreflight": pedigree_preflight,
        "supportSixPreflight": support_six,
        "reboundContextReview": rebound_review,
        "allTenFactorSources": all_factor_materials,
        "realAssessmentPreflight": readiness_preflight,
        "predictionReady": False,
        "goingSuitabilityAssessed": False,
        "note": ("本人専用の過去資料照合。取得上限内で参照できた履歴の集計のみ。"
                 "残りの過去走・未提供馬場は不明。10項目の資料枠を"
                 "結合しても適性S/A/Bや馬券は作成していません。"),
    }
