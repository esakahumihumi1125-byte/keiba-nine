"""One selected race: private, provisional TWO-factor comparison only.

This is an uncalibrated training/recent research preview from permitted JRDB
materials, never a validated overall prediction, JRA racecard verification,
3連単 proposal, public feed or automatic purchase. No calls or persistence here.
"""
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints

VERSION = "owner-single-race-two-factor-trial-1"
VALUES = {"S": 4, "A": 3, "B": 2, "C": 1}
NOT_ASSESSED = "未評価"


def _select(rows, track, race, label):
    matches = [row for row in rows if row.get("track") == track
               and row.get("race") == race]
    if len(matches) != 1:
        raise CoverageError("Missing or ambiguous " + label + " race")
    return matches[0]


def build_one_race_trial(programme, entries, training, recent, date, track, race, *, hints=None):
    """Produce an ephemeral private candidate comparison, never a wager.

    Uses the existing identity-audited provider hypotheses unchanged. Runners
    missing either factor are unranked; no missing grades are imputed.
    """
    if (not _valid_date(date) or track not in TRACKS.values()
            or type(race) is not int or not 1 <= race <= 12):
        raise CoverageError("Invalid selected race coordinates")
    programme_row = _select(programme, track, race, "programme")
    if hints is None:
        training_rows = build_training_hints(programme, entries, training, date)
        recent_rows = build_recent_hints(programme, entries, recent, date)
    else:
        # Only the authenticated in-process day batch may reuse the same
        # fully audited, date-bound snapshot. Never treat this as verified JRA.
        if not isinstance(hints, tuple) or len(hints) != 2:
            raise CoverageError("Invalid shared factor snapshot")
        training_rows, recent_rows = hints
    a = _select(training_rows, track, race, "workout")
    b = _select(recent_rows, track, race, "history")
    if (a.get("racekey") != b.get("racekey")
            or a["racekey"] != programme_row.get("racekey")
            or a.get("predictionReady") is not False
            or b.get("predictionReady") is not False):
        raise CoverageError("Source race identities do not match")
    first = a.get("gradesByNumber")
    second = b.get("byNumber")
    if not isinstance(first, dict) or not isinstance(second, dict):
        raise CoverageError("Invalid runner factor lists")
    if set(first) != set(second) or not 1 <= len(first) <= 18:
        raise CoverageError("Runner factor lists do not agree")
    declared = programme_row.get("headcount")
    if declared is not None and declared != len(first):
        raise CoverageError("Provisional runner counts disagree")
    comparisons = []
    for number in first:
        if (not isinstance(number, str) or len(number) != 2
                or not number.isascii() or not number.isdigit()
                or not 1 <= int(number) <= 18):
            raise CoverageError("Invalid runner number")
        workout = first[number]
        history = second[number]
        form = history.get("grade") if isinstance(history, dict) else None
        if workout not in (*VALUES, NOT_ASSESSED) or form not in (*VALUES, NOT_ASSESSED):
            raise CoverageError("Unexpected provisional grade")
        points = VALUES[workout] + VALUES[form] if workout in VALUES and form in VALUES else None
        comparisons.append({
            "horseNumber": int(number),
            "trainingGrade": workout,
            "recentGrade": form,
            "twoFactorPoints": points,
            "provisionalOnly": True,
        })
    comparisons.sort(key=lambda item: (
        item["twoFactorPoints"] is None,
        -item["twoFactorPoints"] if item["twoFactorPoints"] is not None else 0,
        item["horseNumber"],
    ))
    last = None
    rank = 0
    for index, item in enumerate(comparisons, start=1):
        score = item["twoFactorPoints"]
        if score is None:
            item["comparisonRank"] = None
        else:
            if score != last:
                rank = index
            item["comparisonRank"] = rank
            last = score
    complete = sum(row["twoFactorPoints"] is not None for row in comparisons)
    return {
        "version": VERSION,
        "date": date,
        "track": track,
        "race": race,
        "runnersObserved": len(comparisons),
        "twoFactorComparable": complete,
        "ungraded": len(comparisons) - complete,
        "comparedFactors": ["調教（暫定）", "近走（暫定）"],
        "unverifiedFactors": 8,
        "researchOnly": True,
        "officialJraVerified": False,
        "overallRankReady": False,
        "predictionReady": False,
        "bettingReady": False,
        "autoTicketReady": False,
        "runners": comparisons,
        "warning": ("JRDB元資料の2項目だけで自動計算した研究用の比較順です。"
                    "調教・近走の独自閾値は未検証、残り8項目とJRA公式の出走確定・"
                    "取消・馬場を独立確認していません。総合評価S/A/B/C、"
                    "勝ち馬の予測、3連単買い目の自動作成はできません。"),
    }
