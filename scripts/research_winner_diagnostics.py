"""Offline synthetic-only winner-review diagnostics, never a live predictor.

Uses research_backtest to freeze predictions before reading outcomes. Reports
missed first-place candidates separately from simulated trifecta misses.
"""
from evaluation_policy import timestamp
from research_backtest import backtest

VERSION = "synthetic-winner-review-1"
GRADES = ("S", "A", "B", "C", "未評価")


def _finish(race, result):
    if result is None:
        return None
    if not isinstance(result, dict) or result.get("recordType") != "test":
        raise ValueError("Only synthetic results are accepted")
    if timestamp(result.get("availableAt")) < timestamp(race["offAt"]):
        raise ValueError("Post-race result timestamp is required")
    if result.get("status") == "cancelled":
        return None
    if (result.get("status") != "final" or result.get("deadHeat")
            or result.get("excludedNumbers")):
        raise ValueError("Unsupported synthetic result status")
    finish = result.get("finish")
    numbers = {h["number"] for h in race["horses"]}
    if (not isinstance(finish, list) or len(finish) != 3
            or any(type(n) is not int or n not in numbers for n in finish)
            or len(set(finish)) != 3):
        raise ValueError("Invalid declared three-horse finish")
    payout = result.get("trifectaPayout")
    if type(payout) is not int or payout < 0:
        raise ValueError("Invalid 100-yen synthetic payout")
    return finish


def _summary(rows, baseline):
    ranked = [r for r in rows if r["winnerRank"] is not None]
    return {
        "finalRaces": len(rows),
        "winnerRanked": len(ranked),
        "winnerUnranked": len(rows) - len(ranked),
        "winnerRank1": sum(r["winnerRank"] == 1 for r in ranked),
        "winnerRankTop3": sum(r["winnerRank"] <= 3 for r in ranked),
        "winnerRankBelow3": sum(r["winnerRank"] > 3 for r in ranked),
        "winnerInWinReview": sum(r["winnerInWinReview"] for r in rows),
        "winnerInTicketFirst": sum(r["winnerInTicketFirst"] for r in rows),
        "reviewedButUnticketed": sum(r["reviewedButUnticketed"] for r in rows),
        "trifectaHit": sum(r["trifectaHit"] for r in rows),
        "winnerGrades": {g: sum(r["winnerGrade"] == g for r in rows) for g in GRADES},
        "syntheticStake": baseline["stake"],
        "syntheticReturned": baseline["returned"],
        "syntheticRoi": baseline["roi"],
    }


def audit_synthetic_winners(races, outcomes, split_at, *, min_validation_races=20):
    """Fixed policy and chronological split, with no threshold optimization."""
    if type(min_validation_races) is not int or not 1 <= min_validation_races <= 10000:
        raise ValueError("Invalid minimum validation sample")
    report = backtest(races, outcomes, split_at)
    by_id = {r["raceId"]: r for r in races}
    rows = []
    for entry in report["rows"]:
        finish = _finish(by_id[entry["raceId"]], outcomes.get(entry["raceId"]))
        if finish is None:
            continue
        plan = entry["plan"]
        winner = next(h for h in plan["evaluation"]["horses"]
                      if h["number"] == finish[0])
        candidate = finish[0] in plan["evaluation"]["winCandidatesToReview"]
        ticket_first = finish[0] in plan["first"]
        rows.append({
            "raceId": entry["raceId"], "partition": entry["partition"],
            "winnerNumber": finish[0], "winnerGrade": winner["overall"],
            "winnerRank": winner["rank"], "winnerInWinReview": candidate,
            "winnerInTicketFirst": ticket_first,
            "reviewedButUnticketed": candidate and not ticket_first,
            "trifectaHit": finish in plan["tri"],
            "researchDecision": plan["researchDecision"],
            "predictionHash": entry["predictionHash"],
        })
    development = [r for r in rows if r["partition"] == "development"]
    validation = [r for r in rows if r["partition"] == "validation"]
    return {
        "version": VERSION, "recordType": "test", "basis": "synthetic_only",
        "minValidationRaces": min_validation_races,
        "validationSampleMeetsMinimum": len(validation) >= min_validation_races,
        "calibrated": False, "approvedForLive": False,
        "approvedForPublication": False, "approvedForBetting": False,
        "rows": rows,
        "development": _summary(development, report["development"]),
        "validation": _summary(validation, report["validation"]),
        "summary": _summary(rows, report["summary"]),
        "note": ("架空データで総合上位3位外の勝ち馬と、勝ち切り再検討に"
                 "入れたのに1着候補券へ入れなかった馬を区別。"
                 "実際の的中率や本番評価の妥当性は示しません。"),
    }
