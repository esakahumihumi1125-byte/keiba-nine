"""Local-only JRA-VAN matched-history 3連単 *research* trial.

This is an exploratory ordering rule, NOT a validated 10-factor model.
It makes ZERO provider/network/file calls and must not be connected to Render
or the production trifecta builder. Only already-sanitized owner-PC reports.
No odds, popularity, names, registration IDs, or paid raw rows leave the PC.
"""
from datetime import datetime
from html import escape
from itertools import product

from jrdb_coverage import CoverageError
from owner_jvdata_horse_history_coverage import JST
from owner_jvdata_offline_evidence import summarize_one_race

VERSION = "arc-race-jvlink-offline-trifecta-research-1"
DISTANCE_TOLERANCE_METERS = 200
MAX_POINTS = 48


def _clock(value):
    if value is None:
        value = datetime.now(JST)
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CoverageError("Timezone-aware local clock required")
    return value.astimezone(JST)


def _hold(evidence, reason, *, comparable=None):
    return {
        "version": VERSION, "date": evidence["date"],
        "track": evidence["track"], "race": evidence["race"],
        "status": "hold", "holdReason": reason,
        "runnerCount": evidence["runnerCount"],
        "comparableRunners": comparable or 0,
        "researchOrder": [], "first": [], "second": [], "third": [],
        "tickets": [], "points": 0, "referenceYenAt100": 0,
        "estimatedWinProbability": None, "officialJraVerified": False,
        "formalTenFactorReady": False, "predictionValidated": False,
        "sourceCompletenessVerified": False, "bettingReady": False,
        "purchased": False, "privateOwnerOnly": True, "researchOnly": True,
        "newProviderCalls": 0,
    }


def build_local_trifecta_study(report, *, as_of=None):
    """Order comparable past-course observations only when EVERY runner qualifies.

    Conditions: a complete numbered prestart candidate, valid owner-local
    snapshot clock, matched historical RA7, one comparable prior finish AND
    one observed final-corner position per runner. Missing values HOLD the
    entire race; a missing run never proves a new horse or weak performance.
    Equal keys across a formation boundary HOLD, never break by horse number.
    The model deliberately does not infer today's going, withdrawals or
    training, and is NOT eligible for production betting or a 100pt grade.
    """
    evidence = summarize_one_race(report)
    race = report["races"][0]
    before = _clock(as_of)
    surface = race.get("surfaceCandidate")
    distance = race.get("distanceMetersCandidate")
    post = race.get("postTimeCandidate")
    captured = report.get("capturedAtLocalJst")
    if (race.get("status") != "historical_observations_not_graded"
            or surface not in ("芝", "ダート")
            or type(distance) is not int or not 400 <= distance <= 10000
            or type(post) is not str or len(post) != 5
            or post[2] != ":"
            or not (post[:2] + post[3:]).isdigit()
            or int(post[:2]) > 23 or int(post[3:]) > 59):
        return _hold(evidence, "current_course_or_prestart_not_verified")
    try:
        off = datetime.strptime(evidence["date"] + post, "%Y%m%d%H:%M").replace(tzinfo=JST)
        snapshot = _clock(datetime.fromisoformat(captured))
    except (ValueError, TypeError):
        return _hold(evidence, "local_prestart_clock_missing")
    if (snapshot.date().strftime("%Y%m%d") != evidence["date"]
            or snapshot >= off or before < snapshot or before >= off):
        return _hold(evidence, "not_before_scheduled_off")

    support = []
    for horse in race["byNumber"]:
        number = horse["number"]
        matched = [
            run for run in horse["recentObservedRuns"]
            if run.get("historicalRaceContextMatched") is True
            and run.get("surface") == surface
            and type(run.get("distanceMeters")) is int
            and abs(run["distanceMeters"] - distance) <= DISTANCE_TOLERANCE_METERS
            and type(run.get("finishPosition")) is int
            and 1 <= run["finishPosition"] <= 18
            and isinstance(run.get("cornerPositions"), list)
            and len(run["cornerPositions"]) == 4
            and type(run["cornerPositions"][-1]) is int
            and 1 <= run["cornerPositions"][-1] <= 18
            and run.get("hasAbnormalCode") is False
        ]
        if not matched:
            # Collect coverage only, no zero/last-place invented for this horse.
            continue
        best = min(run["finishPosition"] for run in matched)
        gains = [run["cornerPositions"][-1] - run["finishPosition"]
                 for run in matched]
        # Observable past comparable results, NOT predicted performance.
        # Recent outcome is the last tie-break, not the primary signal.
        key = (best, -max(gains), matched[0]["finishPosition"])
        support.append({
            "number": number, "observedComparableRuns": len(matched),
            "bestPastComparableFinish": best,
            "bestPastStretchPositionGain": max(gains),
            "recentPastComparableFinish": matched[0]["finishPosition"],
            "_key": key,
        })
    if len(support) != evidence["runnerCount"]:
        return _hold(evidence, "incomplete_comparable_prior_runs",
                     comparable=len(support))

    support.sort(key=lambda item: (*item["_key"], item["number"]))
    field = len(support)
    first_n, second_n, third_n = ((2, 5, 7) if field >= 7 else
                                  (1, 3, min(5, field)))
    for boundary in (first_n, second_n, third_n):
        if boundary < field and support[boundary - 1]["_key"] == support[boundary]["_key"]:
            return _hold(evidence, "ambiguous_formation_boundary",
                         comparable=field)

    rank = [horse["number"] for horse in support]
    first, second, third = (rank[:first_n], rank[:second_n], rank[:third_n])
    tickets = [
        [a, b, c] for a, b, c in product(first, second, third)
        if len({a, b, c}) == 3
    ]
    if not tickets or len(tickets) > MAX_POINTS:
        raise CoverageError("Invalid local exploratory ticket count")
    return {
        "version": VERSION, "date": evidence["date"],
        "track": evidence["track"], "race": evidence["race"],
        "surfaceCandidate": surface, "distanceMetersCandidate": distance,
        "postTimeCandidate": post,
        "status": "local_history_research_only", "holdReason": None,
        "runnerCount": field, "comparableRunners": field,
        "researchOrder": rank, "first": first, "second": second, "third": third,
        "tickets": tickets, "points": len(tickets),
        "referenceYenAt100": len(tickets) * 100,
        "historicalObservationBasis": [
            {k: v for k, v in horse.items() if k != "_key"}
            for horse in support
        ],
        "estimatedWinProbability": None, "officialJraVerified": False,
        "formalTenFactorReady": False, "predictionValidated": False,
        "sourceCompletenessVerified": False, "bettingReady": False,
        "purchased": False, "privateOwnerOnly": True, "researchOnly": True,
        "newProviderCalls": 0,
    }


def render_local_trifecta_html(result):
    """No JavaScript, web links, external resources, or unescaped source text."""
    if (not isinstance(result, dict) or result.get("version") != VERSION
            or result.get("privateOwnerOnly") is not True
            or result.get("researchOnly") is not True
            or result.get("bettingReady") is not False
            or result.get("formalTenFactorReady") is not False
            or result.get("officialJraVerified") is not False):
        raise CoverageError("Invalid local-only trifecta research result")
    e = lambda value: escape(str(value), quote=True)
    parts = [
        "<!doctype html><html lang='ja'><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>ARC RACE｜PC内・過去走だけの3連単研究</title>",
        "<style>body{font:16px/1.6 system-ui,sans-serif;max-width:760px;"
        "margin:auto;padding:18px;background:#092039;color:#edf4ff}"
        "section{border:1px solid #52718d;border-radius:14px;padding:15px;"
        "margin:14px 0;background:#18354f}strong{color:#f1d088}"
        ".warning{border-color:#e0af6b}.muted{color:#b9c8d7}"
        "li{padding:3px 0}code{color:#f6d78c}</style>",
        "<h1>ARC RACE｜過去走限定・3連単研究</h1>",
        "<section class='warning'><strong>正式予想・購入用ではありません。</strong>"
        "調教30点など正式10項目の評価、JRAの最終出走馬・取消・"
        "馬場・時刻、元データの配信時刻、過去履歴の網羅性は未確認。"
        "過去走の比較ルールは予測精度未検証です。"
        "人気・オッズは使わず、外部通信・自動購入はありません。</section>",
        "<h2>" + e(result["date"]) + " " + e(result["track"])
        + " " + e(result["race"]) + "R</h2>",
    ]
    if result["status"] == "hold":
        parts.append(
            "<section><strong>見送り・研究候補を確定できません。</strong>"
            "<p>理由：" + e(result["holdReason"]) + "</p>"
            "<p>条件に合う過去走のある馬："
            + e(result["comparableRunners"]) + " / "
            + e(result["runnerCount"]) + "頭</p>"
            "<p>3連単は0点。データ欠損を弱い馬とは扱いません。</p></section>"
        )
    elif result["status"] == "local_history_research_only":
        parts.extend([
            "<section><p>今回のコース候補：" + e(result["surfaceCandidate"])
            + e(result["distanceMetersCandidate"]) + "m（当日変更未照合）</p>",
            "<p>過去に同じ芝ダート・距離差200m以内の記録がある全馬を比較。"
            "着順→最終コーナーからの着順改善→近い過去の結果、という"
            "実験的な並び順。調教・展開予測・能力S/A/Bではありません。</p>",
            "<p>参考順：<strong>" + e("・".join(
                str(n) for n in result["researchOrder"])) + "</strong></p>",
            "<p>1着候補：<strong>" + e("・".join(
                str(n) for n in result["first"])) + "</strong></p>",
            "<p>2着候補：<strong>" + e("・".join(
                str(n) for n in result["second"])) + "</strong></p>",
            "<p>3着候補：<strong>" + e("・".join(
                str(n) for n in result["third"])) + "</strong></p>",
            "<p>重複除外：<strong>" + e(result["points"]) + "点</strong>"
            "（1点100円で " + e(result["referenceYenAt100"])
            + "円相当の机上計算。購入・投資記録ではありません）</p></section>",
        ])
    else:
        raise CoverageError("Unsupported research result status")
    parts.append("<p class='muted'>この画面とJSONは本人のPC内限定。"
                 "本番アプリへ自動送信せず、既存の固定記録も更新しません。</p></html>")
    return "".join(parts)
