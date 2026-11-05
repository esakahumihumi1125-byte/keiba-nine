"""Read-only, owner-only 72-race synthetic research review.

Demonstrates a frozen chronological split and missed-winner diagnostics.
The fixtures and outcomes are invented in year 2099. No JRDB data, JRA
results, API fetch, mutable state, costs, or user ticket records are accessed.
"""
from copy import deepcopy
from datetime import datetime, timedelta
from html import escape

from research_batch_demo import DEMO_VENUES, demo_race
from research_planner import plan_race
from research_winner_diagnostics import audit_synthetic_winners

VERSION = "synthetic-validation-review-1"
DAYS = ("2099-01-01", "2099-01-02")
SPLIT = "2099-01-02T00:00:00+09:00"
RACES_PER_DAY = 36
TOTAL_RACES = 72


def _fixture(date, venue, number):
    """Move only synthetic timestamps from day one to day two."""
    if date not in DAYS:
        raise ValueError("Synthetic date only")
    race = demo_race(venue, number)
    if date == DAYS[0]:
        return race
    race = deepcopy(race)
    race["raceId"] = race["raceId"].replace("20990101", "20990102")
    race["date"] = DAYS[1]
    race["asOf"] = race["asOf"].replace(DAYS[0], DAYS[1])
    race["offAt"] = race["offAt"].replace(DAYS[0], DAYS[1])
    for horse in race["horses"]:
        for assessment in horse["assessments"].values():
            for evidence in assessment["evidence"]:
                evidence["availableAt"] = evidence["availableAt"].replace(DAYS[0], DAYS[1])
    return race


def _invented_outcome(race):
    """The result is *never* added to the prediction input."""
    date, number = race["date"], race["race"]
    off = datetime.fromisoformat(race["offAt"])
    available = (off + timedelta(minutes=6)).isoformat()
    if number == 7:
        return None
    if number == 11:
        return {"recordType": "test", "status": "cancelled", "availableAt": available}
    # Hand-picked synthetic hits/misses test both bankroll accounting and
    # low-ranked winners. These probabilities/yen are NOT real or calibrated.
    plan = plan_race(race)
    if plan["researchDecision"] == "simulate" and (
            (date == DAYS[0] and number % 2 == 0)
            or (date == DAYS[1] and number % 3 == 0)):
        finish = list(plan["tri"][0])
    else:
        finish = [8, 7, 6]
    return {
        "recordType": "test", "status": "final", "availableAt": available,
        "finish": finish, "trifectaPayout": 8400 + 300 * number,
    }


def build_validation_review():
    """Pure offline fixture; chronological split happens before settlement."""
    races = [_fixture(day, venue, number) for day in DAYS
             for venue in DEMO_VENUES for number in range(1, 13)]
    ids = [race["raceId"] for race in races]
    if len(races) != TOTAL_RACES or len(set(ids)) != TOTAL_RACES:
        raise ValueError("Synthetic research races are not unique")
    outcomes = {race["raceId"]: result for race in races
                if (result := _invented_outcome(race)) is not None}
    report = audit_synthetic_winners(
        races, outcomes, SPLIT, min_validation_races=20
    )
    if (report["recordType"] != "test" or report["basis"] != "synthetic_only"
            or any(report.get(k) is not False for k in (
                "calibrated", "approvedForLive",
                "approvedForPublication", "approvedForBetting"))
            or not report["validationSampleMeetsMinimum"]
            or report["development"]["finalRaces"] != 30
            or report["validation"]["finalRaces"] != 30):
        raise ValueError("Cannot classify synthetic evidence as live performance")
    # Additional invariant: this is a test of the report contract, NOT an
    # external immutable evidence timestamp or experimental model approval.
    return {
        "version": VERSION,
        "recordType": "test",
        "basis": "synthetic_only",
        "splitAt": SPLIT,
        "fixtureRaces": len(races),
        "fictitiousSettledRaces": report["summary"]["finalRaces"],
        "development": report["development"],
        "validation": report["validation"],
        "validationDetails": [
            {
                "raceId": row["raceId"], "winnerNumber": row["winnerNumber"],
                "winnerRank": row["winnerRank"],
                "winnerInWinReview": row["winnerInWinReview"],
                "winnerInTicketFirst": row["winnerInTicketFirst"],
                "trifectaHit": row["trifectaHit"],
                "researchDecision": row["researchDecision"],
                "predictionHash": row["predictionHash"][:12],
            }
            for row in report["rows"] if row["partition"] == "validation"
        ],
        "officialResultsUsed": False,
        "fittedWinProbability": False,
        "realPredictionReady": False, "publishable": False,
        "purchaseReady": False,
    }


def render_validation_html(report):
    """Only an explicitly synthetic, unapproved test report can be displayed."""
    if (not isinstance(report, dict)
            or report.get("version") != VERSION
            or report.get("recordType") != "test"
            or report.get("basis") != "synthetic_only"
            or any(report.get(key) is not False for key in (
                "officialResultsUsed", "fittedWinProbability",
                "realPredictionReady", "publishable", "purchaseReady"))
            or report.get("fixtureRaces") != TOTAL_RACES
            or not isinstance(report.get("validationDetails"), list)
            or len(report["validationDetails"]) != 30):
        raise ValueError("Only the synthetic demo can be shown")

    def e(value):
        return escape(str(value), quote=True)

    def panel(key, label):
        s = report[key]
        return (
            '<section class="venue" style="border:0"><h2>%s</h2>'
            '<p>架空の確定結果：%s R／1着が総合3位以内：%s R／'
            '1着候補に含めた：%s R／3連単的中：%s R</p>'
            '<p>見直し候補：総合4位以下で勝利 %s R、勝ち切り検討に入れたのに'
            '1着馬券に含めず %s R。</p>'
            '<p>架空購入額 %s円・架空払戻額 %s円・架空回収率 %s</p></section>'
        ) % (
            e(label), e(s["finalRaces"]), e(s["winnerRankTop3"]),
            e(s["winnerInTicketFirst"]), e(s["trifectaHit"]),
            e(s["winnerRankBelow3"]), e(s["reviewedButUnticketed"]),
            e(format(s["syntheticStake"], ",")),
            e(format(s["syntheticReturned"], ",")),
            e("計算対象なし" if s["syntheticRoi"] is None
              else "%.1f%%" % s["syntheticRoi"]),
        )
    lines = []
    for item in report["validationDetails"]:
        concern = (
            "1着候補から漏れ" if not item["winnerInTicketFirst"]
            else "買い目の1着候補には含む"
        )
        if item["winnerRank"] is None:
            rank = "未評価"
        else:
            rank = str(item["winnerRank"]) + "位"
        lines.append(
            '<details class="race"><summary><strong>%s</strong>'
            '<span class="status">%s</span></summary><div class="detail">'
            '<p>架空勝ち馬：%s番／総合%s</p>'
            '<p>%s／架空3連単%s</p><p>予想入力指紋：%s…</p>'
            '</div></details>' % (
                e(item["raceId"]), e(concern),
                e(item["winnerNumber"]), e(rank), e(concern),
                "的中" if item["trifectaHit"] else "不的中",
                e(item["predictionHash"]),
            )
        )
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>競馬ナイン｜1着候補の振り返り（架空検証）</title>'
        '<link rel="stylesheet" href="/research-batch-demo.css"></head><body><main>'
        '<header><a href="/">← 本人用ホームへ</a><h1>🏇 1着候補の振り返り（架空）</h1>'
        '<p class="warning">2099年の架空72R・架空払戻を使った研究用テスト。'
        '実際の競馬成績・的中率・回収率・予想精度を示しません。'
        '実馬やJRDBデータは未使用、馬券や実戦記録には反映しません。</p>'
        '<p>初日36Rを開発用、翌日36Rを検証用として先に分け、'
        '結果を見てから予想を書き換えない仕組みをテストしています。'
        '架空の結果確定は各日30R（他は取消または結果待ち）。</p></header>'
        '%s%s'
        '<details class="venue"><summary>架空の検証結果30Rを確認</summary>%s</details>'
        '<footer>サンプル数を満たしたことは実戦の採用承認ではありません。'
        '勝率モデル・外部の取得時刻証明・JRA公式照合は未完成です。</footer>'
        '</main></body></html>'
    ) % (panel("development", "開発用（架空）"),
         panel("validation", "検証用（架空）"), "".join(lines))
    )
