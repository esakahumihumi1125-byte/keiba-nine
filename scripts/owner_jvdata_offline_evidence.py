"""Offline ARC RACE evidence readiness from an existing PRIVATE per-race report.

No JV-Link, JRDB, HTTP, Render, GitHub, account access or odds. Input is
the already sanitized JSON left on the owner's PC by the RACE+RCVN probe.
It must never convert history observations into scores/grades or bets.
"""
from datetime import datetime
from html import escape
from pathlib import Path
import re

from evaluation_policy import OWNER_FORMAL_FACTORS
from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS

VERSION = "arc-race-offline-factor-evidence-1"
SOURCE_VERSION = "owner-jvdata-local-day-history-bridge-1"
MAX_RUNNERS = 18
MAX_RECENT = 5
MAX_OBSERVED = 5000
NUMERIC_KEYS = ("finishPosition", "last3fTenths", "historicalRunningStyleCode")
FACTORS_JP = {
    "training": "調教", "recent": "近走", "course_distance": "コース・距離",
    "pace": "展開・脚質", "ground": "馬場", "pedigree": "血統",
    "draw_weight": "枠・斤量", "jockey_stable": "騎手・厩舎",
    "rotation": "ローテ", "body_condition": "馬体重",
}
assert set(OWNER_FORMAL_FACTORS) == set(FACTORS_JP)


def _int_in(value, low, high):
    return type(value) is int and low <= value <= high


def summarize_runner(horse, *, target_day=None):
    """Never infer quality from positions, missing history, or running style.

    A saved prior result must predate the race being studied. This blocks
    future/same-day results from silently becoming pre-off evidence.
    """
    if target_day is not None and (type(target_day) is not str
                                   or not _valid_date(target_day)):
        raise CoverageError("Invalid target race date")
    if not isinstance(horse, dict):
        raise CoverageError("Invalid private runner summary")
    number, count, recent = (
        horse.get("number"), horse.get("observedRecordCount"),
        horse.get("recentObservedRuns"),
    )
    if (not _int_in(number, 1, MAX_RUNNERS)
            or not _int_in(count, 0, MAX_OBSERVED)
            or not isinstance(recent, list)
            or len(recent) > MAX_RECENT or len(recent) > count
            or horse.get("graded") is not False
            or horse.get("missingHistoryUnproven") is not True):
        raise CoverageError("Invalid private history collection")

    finishes, corners, styles, last3f, dates = [], [], [], [], []
    historical_course_rows = historical_going_rows = 0
    field_relative_runs = []
    for run in recent:
        if not isinstance(run, dict) or not isinstance(run.get("date"), str):
            raise CoverageError("Invalid private prior run")
        day = run["date"]
        if not _valid_date(day):
            raise CoverageError("Invalid private prior date")
        if target_day is not None and day >= target_day:
            raise CoverageError("Historical race is not before target date")
        if day in dates:
            raise CoverageError("Duplicate private prior race date")
        dates.append(day)
        finish, closing, style = [run.get(k) for k in NUMERIC_KEYS]
        if finish is not None and not _int_in(finish, 1, 18):
            raise CoverageError("Invalid private finish position")
        if closing is not None and not _int_in(closing, 1, 998):
            raise CoverageError("Invalid private closing time")
        if style is not None and not _int_in(style, 1, 4):
            raise CoverageError("Invalid private historical style")
        raw_corners = run.get("cornerPositions")
        if not isinstance(raw_corners, list) or len(raw_corners) != 4:
            raise CoverageError("Invalid private corner data")
        if any(x is not None and not _int_in(x, 1, 18)
               for x in raw_corners):
            raise CoverageError("Invalid private corner value")
        # RA7 describes the PAST race, not the target race. Only count
        # a genuine, explicitly joined course; never infer current course
        # or current going from a past performance.
        ra_joined = run.get("historicalRaceContextMatched") is True
        past_surface = run.get("surface")
        past_distance = run.get("distanceMeters")
        past_going = run.get("going")
        if (ra_joined and past_surface in ("芝", "ダート")
                and _int_in(past_distance, 400, 10000)):
            historical_course_rows += 1
            if past_going in ("良", "稍重", "重", "不良"):
                historical_going_rows += 1
        starters = run.get("historicalStarterCount")
        finishers = run.get("historicalFinishersCount")
        # Old files lack these optional fields. Do not invent denominators.
        # The proportion beaten is descriptive, not an ability score.
        relative = None
        if (ra_joined and _int_in(starters, 2, 18)
                and _int_in(finishers, 1, starters)
                and _int_in(finish, 1, finishers)
                and run.get("hasAbnormalCode") is False
                and all(x is None or x <= starters for x in raw_corners)):
            relative = {
                "starters": starters, "finishers": finishers,
                "finishPosition": finish,
                "finisherPositionPercentile": (
                    round(100 * (finishers - finish) / (finishers - 1), 2)
                    if finishers >= 2 else None
                ),
                "finalCornerToFinishGainPerFieldPercent": (
                    round(100 * (raw_corners[-1] - finish) / (starters - 1), 2)
                    if raw_corners[-1] is not None and finishers == starters else None
                ),
            }
        field_relative_runs.append(relative)
        finishes.append(finish)
        corners.append(raw_corners)
        styles.append(style)
        last3f.append(closing)
    if dates != sorted(dates, reverse=True):
        raise CoverageError("Non-chronological private observations")
    recent_evidence = any(x is not None for x in finishes)
    pace_evidence = any(x is not None for x in styles + last3f) or any(
        x is not None for row in corners for x in row
    )
    factors = {
        name: {
            "label": FACTORS_JP[name],
            "weight": weight,
            "status": ("observed_not_scored"
                       if (name == "recent" and recent_evidence)
                       or (name == "pace" and pace_evidence)
                       else "past_context_only"
                       if (name == "course_distance" and historical_course_rows)
                       or (name == "ground" and historical_going_rows)
                       else "unverified"),
            "score": None,
            "grade": None,
        }
        for name, weight in OWNER_FORMAL_FACTORS.items()
    }
    return {
        "number": number,
        "historicalRowsObserved": count,
        "visiblePriorRuns": len(recent),
        "observedFinishes": finishes,
        "fieldRelativeHistoricalObservations": field_relative_runs,
        "observedLast3fTenths": last3f,
        "observedCornerPositions": corners,
        "observedStyleCodes": styles,
        "historicalCourseContextRowsObserved": historical_course_rows,
        "historicalGoingContextRowsObserved": historical_going_rows,
        "factorEvidence": factors,
        "factorsWithObservations": [
            name for name in OWNER_FORMAL_FACTORS
            if factors[name]["status"] == "observed_not_scored"
        ],
        "totalScore": None,
        "overallGrade": None,
        "eligibleForPrediction": False,
        "historyComplete": False,
        "missingHistoryUnproven": True,
    }


def summarize_one_race(report):
    """Strict version/flags + data minimization for local evidence readiness.

    Unrecognised input fields are never copied into the output, including
    the provider's private record fields, file paths and any horse IDs.
    """
    if (not isinstance(report, dict)
            or report.get("version") != SOURCE_VERSION
            or report.get("privateOwnerOnly") is not True
            or report.get("researchOnly") is not True
            or report.get("formalTenFactorReady") is not False
            or report.get("productionPredictionReady") is not False
            or report.get("bettingReady") is not False
            or report.get("historyCompletenessVerified") is not False
            or report.get("officialStarterListVerified") is not False
            or type(report.get("date")) is not str
            or not _valid_date(report["date"])
            or type(report.get("raceCount")) is not int
            or report["raceCount"] != 1
            or not isinstance(report.get("races"), list)
            or len(report["races"]) != 1
            or not isinstance(report["races"][0], dict)):
        raise CoverageError("Not a private research-only one-race report")
    race = report["races"][0]
    if (race.get("track") not in TRACKS.values()
            or not _int_in(race.get("race"), 1, 12)
            or race.get("graded") is not False
            or race.get("bettingReady") is not False
            or race.get("historyComplete") is not False
            or not isinstance(race.get("byNumber"), list)
            or not 4 <= len(race["byNumber"]) <= MAX_RUNNERS):
        raise CoverageError("Invalid research race details")
    horses = [summarize_runner(row, target_day=report["date"])
              for row in race["byNumber"]]
    numbers = [horse["number"] for horse in horses]
    if sorted(numbers) != list(range(1, len(numbers) + 1)):
        raise CoverageError("Private runner numbering incomplete")
    observed = sum(bool(x["historicalRowsObserved"]) for x in horses)
    if not _int_in(race.get("observedHorseHistory"), 0, MAX_RUNNERS):
        raise CoverageError("Invalid private history coverage counter")
    if observed != race["observedHorseHistory"]:
        raise CoverageError("History coverage counter inconsistent")
    return {
        "version": VERSION,
        "date": report["date"],
        "track": race["track"], "race": race["race"],
        "runnerCount": len(horses),
        "runnersWithObservedHistory": observed,
        "runnersWithRecentFinishObservation": sum(
            "recent" in x["factorsWithObservations"] for x in horses),
        "runnersWithPaceObservation": sum(
            "pace" in x["factorsWithObservations"] for x in horses),
        "runnersWithPastCourseContext": sum(
            x["historicalCourseContextRowsObserved"] > 0 for x in horses),
        "runnersWithFieldRelativeObservations": sum(
            any(item is not None for item in h["fieldRelativeHistoricalObservations"])
            for h in horses),
        "runnersWithPastGoingContext": sum(
            x["historicalGoingContextRowsObserved"] > 0 for x in horses),
        "byNumber": horses,
        "factorNames": [FACTORS_JP[k] for k in OWNER_FORMAL_FACTORS],
        "tenFactorScoresReady": False,
        "formalForecastReady": False,
        "trifectaReady": False,
        "rankedByAbility": False,
        "officialStartersVerified": False,
        "sourceCompletenessVerified": False,
        "networkCalls": 0,
        "rawJvdataExported": False,
        "ownerPrivateOnly": True,
        "researchOnly": True,
        "note": (
            "過去走由来の近走・展開脚質の一部を資料として観測しただけ。"
            "過去走RA7が一致すれば当時の距離・馬場だけ観測する。"
            "今回の条件との比較、調教等の検証不足は未確認のまま。"
            "近走の着順や人気を根拠に加点せず、正式10項目採点・"
            "3連単予想・馬券購入には使わない。"
        ),
    }


def render_evidence_html(result):
    """Static, readable per-horse HTML. No script, links, remote assets."""
    if (not isinstance(result, dict)
            or result.get("version") != VERSION
            or result.get("ownerPrivateOnly") is not True
            or result.get("researchOnly") is not True
            or result.get("formalForecastReady") is not False
            or result.get("trifectaReady") is not False
            or result.get("tenFactorScoresReady") is not False):
        raise CoverageError("Not an offline research-only evidence report")
    def e(value):
        return escape(str(value), quote=True)
    lines = [
        "<!doctype html><html lang='ja'><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>ARC RACE｜資料確認（PC内）</title>",
        "<style>body{font-family:system-ui,sans-serif;max-width:900px;",
        "margin:auto;padding:20px;background:#f5f7fb;color:#152237}",
        "section{background:white;padding:16px;margin:10px 0;",
        "border-radius:12px}table{border-collapse:collapse;width:100%}",
        "td,th{border-bottom:1px solid #dbe2ec;padding:8px;text-align:left}",
        ".muted{color:#49566a}.warn{padding:14px;border:1px solid #c3a763}",
        "details{margin:8px 0}summary{cursor:pointer;font-weight:700}",
        "</style><h1>ARC RACE｜10項目の資料確認（未採点）</h1>",
        "<p class='warn'>⚠ これは予想ではありません。正式採点、"
        "3連単の買い目、JRAの最終出走・取消・馬場・発走時刻は未確認。</p>",
        "<h2>" + e(result["date"]) + " "
        + e(result["track"]) + " " + e(result["race"]) + "R</h2>",
        "<p>出走馬番 " + e(result["runnerCount"])
        + "頭／過去走記録を観測 " + e(result["runnersWithObservedHistory"])
        + "頭／近走着順の観測 "
        + e(result["runnersWithRecentFinishObservation"])
        + "頭／脚質・展開関連記録の観測 "
        + e(result["runnersWithPaceObservation"])
        + "頭／過去レースのコース条件あり "
        + e(result["runnersWithPastCourseContext"])
        + "頭（今回の適性は未評価）</p>",
        "<p class='muted'>馬番順。優劣順でも人気順でもありません。"
        "過去走の記録が見つからなくても新馬とは断定しません。</p>",
    ]
    for horse in result["byNumber"]:
        recent = horse["factorEvidence"]["recent"]["status"]
        pace = horse["factorEvidence"]["pace"]["status"]
        observed = lambda s: ("資料あり・未採点" if s == "observed_not_scored"
                              else "過去の条件のみ・今回の適性は未評価"
                              if s == "past_context_only" else "未確認")
        finishes = "、".join(
            "不明" if x is None else str(x) + "着"
            for x in horse["observedFinishes"]
        ) or "観測なし"
        three_f = "、".join(
            "不明" if x is None else f"{x / 10:.1f}秒"
            for x in horse["observedLast3fTenths"]
        ) or "観測なし"
        relative = "、".join(
            "不明" if item is None else
            f'{item["finishPosition"]}着/{item["starters"]}頭出走・{item["finishers"]}頭入線'
            for item in horse.get("fieldRelativeHistoricalObservations", [])
        ) or "観測なし"
        lines.append(
            "<section><details><summary>" + e(horse["number"])
            + "番｜過去走 " + e(horse["historicalRowsObserved"])
            + "件｜近走 " + observed(recent)
            + "｜展開・脚質 " + observed(pace)
            + "</summary><p>過去コース条件の観測 "
            + e(horse["historicalCourseContextRowsObserved"])
            + "走／過去の馬場条件の観測 "
            + e(horse["historicalGoingContextRowsObserved"])
            + "走（いずれも今回の適性評価ではない）</p>"
            + "<p>観測した着順：" + e(finishes)
            + "</p><p>上がり3F候補：" + e(three_f)
            + "</p><p>過去走の出走・入線頭数：" + e(relative)
            + "（着順の比較資料・能力点ではない）</p><table><tr><th>10項目</th><th>状態</th></tr>"
        )
        for item in horse["factorEvidence"].values():
            lines.append(
                "<tr><td>" + e(item["label"]) + "</td><td>"
                + observed(item["status"]) + "</td></tr>"
            )
        lines.append("</table></details></section>")
    lines.append(
        "<p class='muted'>調教・今回のコース適性・今回の馬場適性・血統・枠斤量・騎手厩舎・"
        "ローテ・馬体重は別資料が必要。"
        "過去走の観測件数は強さや勝率を表しません。</p></html>"
    )
    return "".join(lines)
