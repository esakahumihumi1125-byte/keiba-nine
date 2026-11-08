"""Owner-only 4-factor rebound research review (not a winner prediction).

This joins high provisional training + low recent form with independent
experimental course/going history and positional pace scenarios. Past course
and going podiums can describe the SAME historical runs; they do not count
as independent proof of a win. Repeated runs, finishing positions, or low
recent grades never automatically remove a horse from first-place review.

No odds, predictions, tickets, purchases, external fetch or mutable state.
Only pre-JRA-verification observations cross the private owner boundary.
"""
from jrdb_coverage import CoverageError
from jrdb_private_factor_bridge import summarize_factor_materials
from jrdb_experimental_pace_scenarios import hypothesize_owner_pace
from jrdb_experimental_condition_grades import hypothesis_from_owner_history
from evaluation_policy import FACTORS, POLICY_VERSION

VERSION = "owner-rebound-context-review-1"
CONTEXT_FACTORS = ("course_distance", "pace", "ground")
GOOD_BANDS = frozenset(("S", "A"))
assert (FACTORS["training"], FACTORS["recent"],
        FACTORS["course_distance"], FACTORS["pace"], FACTORS["ground"]) == (
        30, 3, 20, 20, 12
)

def _coords(rows, source_name):
    found = {}
    for row in rows:
        coord = row["track"], row["race"]
        if coord in found:
            raise CoverageError("Duplicate private " + source_name + " race")
        found[coord] = row
    return found

def build_rebound_context_review(factor_matrix, owner_runner_history,
                                 condition_bands, pace_scenarios):
    """Fail closed on any cross-race/number mismatch or fabricated evidence."""
    # These three validators enforce safe provider joins, ungraded inputs and
    # consistency with the original audited position/history counts.
    factor_status = summarize_factor_materials(factor_matrix)
    if (hypothesis_from_owner_history(owner_runner_history) != condition_bands
            or hypothesize_owner_pace(factor_matrix) != pace_scenarios):
        raise CoverageError("Research factor hypotheses do not match source")
    matrix = _coords(factor_matrix, "factor")
    history = _coords(owner_runner_history["races"], "history")
    bands = _coords(condition_bands["races"], "band")
    scenarios = _coords(pace_scenarios["races"], "pace")
    keys = set(matrix)
    if (keys != set(history) or keys != set(bands) or keys != set(scenarios)
            or factor_status["raceCount"] != len(keys)):
        raise CoverageError("Rebound research race sets do not match")
    output, total_watch, multi_source = [], 0, 0
    for key in sorted(keys):
        snapshot = matrix[key]["byNumber"]
        historical = history[key]["runners"]
        c = bands[key]["runners"]
        p = scenarios[key]["runners"]
        normalize = lambda num: int(num)
        nums = {normalize(x) for x in snapshot}
        if (nums != {h["number"] for h in historical}
                or nums != {h["number"] for h in c}
                or nums != {h["number"] for h in p}
                or len(nums) != len(snapshot)
                or len(historical) != len(nums)
                or len(c) != len(nums) or len(p) != len(nums)):
            raise CoverageError("Rebound research runner sets do not match")
        c_by = {h["number"]: h for h in c}
        p_by = {h["number"]: h for h in p}
        row_watch = []
        for text_number, slots in snapshot.items():
            number = int(text_number)
            training = slots["training"]["grade"]
            recent = slots["recent"]["grade"]
            if training not in ("S", "A") or recent not in ("B", "C"):
                continue  # Not excluded from real predictions, only not watched.
            context = {
                "course_distance": c_by[number]["courseEvidenceBand"],
                "pace": p_by[number]["scenarioFitBand"],
                "ground": c_by[number]["goingEvidenceBand"],
            }
            signals = [name for name in CONTEXT_FACTORS
                       if context[name] in GOOD_BANDS]
            unknown = [name for name in CONTEXT_FACTORS
                       if context[name] == "未評価"]
            # Pace positions are separate from course+going placing history.
            # Course + going alone may count the SAME historic finishes twice.
            cross_source = ("pace" in signals
                            and ("course_distance" in signals
                                 or "ground" in signals))
            history_overlap_only = (
                not cross_source
                and "course_distance" in signals and "ground" in signals
            )
            state = (
                "cross_source_review" if cross_source
                else "overlapping_history_only" if history_overlap_only
                else "need_more_evidence"
            )
            row_watch.append({
                "number": number, "trainingProvisional": training,
                "recentProvisional": recent,
                "courseEvidenceBand": context["course_distance"],
                "paceScenarioBand": context["pace"],
                "goingEvidenceBand": context["ground"],
                "supportingContextFactors": signals,
                "unassessedContextFactors": unknown,
                "contextSignalCount": len(signals),
                "reviewState": state,
                "evidenceOnly": True,
                "winPickReady": False,
            })
        row_watch.sort(key=lambda x: x["number"])
        multi_source += sum(x["reviewState"] == "cross_source_review"
                            for x in row_watch)
        total_watch += len(row_watch)
        output.append({
            "track": key[0], "race": key[1],
            "runnerCount": len(nums), "watchCount": len(row_watch),
            "watch": row_watch, "winPickReady": False,
            "gradedTenFactors": 0,
        })
    return {
        "version": VERSION, "policyVersion": POLICY_VERSION,
        "raceCount": len(output), "watchCount": total_watch,
        "crossSourceReviewCount": multi_source, "races": output,
        "factorWeights": {
            name: FACTORS[name] for name in (
                "training", "recent", *CONTEXT_FACTORS
            )
        },
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "overallScoreReady": False,
        "winPickReady": False, "bettingReady": False,
        "autoPurchase": False, "modifiesFrozenPicks": False,
        "contextRequiresPaceAndHistory": True,
        "historyOnlySignalsMayOverlap": True,
        "note": (
            "調教が良いのに近走の評価が低い馬を、今回のコース、"
            "馬場、位置取りの研究仮説で再審査。コースと馬場の好走実績は"
            "同じ過去走に基づく可能性があるため別根拠とは断定しない。"
            "出走取消、正式な馬場・展開・JRAの最終照合、"
            "予想精度の検証が未完了。1着候補や買い目へ自動追加しない。"
        ),
    }
