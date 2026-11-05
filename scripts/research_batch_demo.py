"""Bounded, synthetic-only all-races research preview for the owner.

This module neither fetches JRDB/JRA data nor calls AI or writes any storage.
All entrants, evidence and race IDs are intentionally fictional (year 2099).
The research planner is still *unvalidated* and cannot issue real predictions.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone
from html import escape

from evaluation_policy import FACTORS
from research_planner import plan_race

DEMO_DATE = "2099-01-01"
DEMO_VENUES = ("架空A競馬場", "架空B競馬場", "架空C競馬場")
MAX_RACES = len(DEMO_VENUES) * 12
JST = timezone(timedelta(hours=9))
VERSION = "synthetic-batch-1"


def demo_race(venue, number):
    """Produce one clearly fictitious 8-runner fixture, with distinct outcomes."""
    if venue not in DEMO_VENUES or type(number) is not int or not 1 <= number <= 12:
        raise ValueError("Invalid synthetic fixture coordinate")
    place = DEMO_VENUES.index(venue) + 1
    off = datetime(2099, 1, 1, 10, 0, tzinfo=JST) + timedelta(minutes=30 * (number - 1))
    behavior = number % 4
    horses = []
    for horse_number in range(1, 9):
        grade = ("S" if horse_number <= 2 else "A" if horse_number <= 4 else "B")
        assessments = {}
        for factor in FACTORS:
            winner = (
                behavior in (2, 0) and horse_number <= 2
                or behavior == 3 and horse_number <= 4
            )
            assessments[factor] = {
                "grade": grade,
                "winSupport": winner and factor in ("training", "pace"),
                "reason": "架空の10項目研究テスト。実馬の根拠ではありません。",
                "evidence": [{
                    "sourceId": "synthetic",
                    "reference": "fixture-%s-%02d-%02d-%s" % (
                        place, number, horse_number, factor),
                    "availableAt": "2099-01-01T08:00:00+09:00",
                }],
            }
        if behavior == 0 and horse_number == 8:
            # Missing core evidence must hold the WHOLE race.
            del assessments["recent"]
        horses.append({"number": horse_number, "assessments": assessments})
    return {
        "raceId": "synthetic-20990101-%d-%02d" % (place, number),
        "recordType": "test",
        "date": DEMO_DATE,
        "track": venue,
        "race": number,
        "asOf": "2099-01-01T09:00:00+09:00",
        "offAt": off.isoformat(),
        "horses": horses,
    }


def _canonical_race_set(races):
    if not isinstance(races, list) or not 1 <= len(races) <= MAX_RACES:
        raise ValueError("Expected a bounded, nonempty synthetic race list")
    keys = set()
    for race in races:
        if not isinstance(race, dict) or race.get("recordType") != "test":
            raise ValueError("Only synthetic test races may be analyzed")
        if race.get("date") != DEMO_DATE or race.get("track") not in DEMO_VENUES:
            raise ValueError("The batch preview accepts synthetic venues only")
        number = race.get("race")
        if type(number) is not int or not 1 <= number <= 12:
            raise ValueError("Invalid synthetic race number")
        key = (race["track"], number)
        if key in keys:
            raise ValueError("Duplicate race in synthetic batch")
        keys.add(key)


def build_demo_batch(races=None):
    """Return an immutable-in-practice plan snapshot, no writes or provider IO."""
    if races is None:
        races = [demo_race(venue, number) for venue in DEMO_VENUES
                 for number in range(1, 13)]
    _canonical_race_set(races)
    rows = []
    for race in sorted(races, key=lambda r: (DEMO_VENUES.index(r["track"]), r["race"])):
        plan = plan_race(race)
        decision = plan["researchDecision"]
        if decision not in ("simulate", "hold", "skip") or plan["recordType"] != "test":
            raise ValueError("Unexpected synthetic research decision")
        tri = [tuple(t) for t in plan["tri"]]
        points = plan["points"]
        if (points != len(tri) or points > 40 or len(set(tri)) != points
                or plan["stake"] != points * 100
                or plan["publishable"] is not False
                or plan["validated"] is not False
                or plan["status"] != "draft"
                or (decision != "simulate" and points != 0)):
            raise ValueError("Research output violates synthetic-only safety contract")
        sorted_horses = plan["evaluation"]["horses"]
        if len(sorted_horses) != len(race["horses"]):
            raise ValueError("Ranking lost runners")
        ranks = [{"number": horse["number"], "overall": horse["overall"],
                  "rank": horse["rank"]} for horse in sorted_horses]
        choices = {
            "first": sorted({t[0] for t in tri}),
            "second": sorted({t[1] for t in tri}),
            "third": sorted({t[2] for t in tri}),
        }
        rows.append({
            "raceId": race["raceId"],
            "track": race["track"], "race": race["race"],
            "recordType": "test", "decision": decision,
            "reason": plan["reason"], "ranks": ranks,
            "choices": choices, "tickets": tri, "points": points,
            "stake": points * 100,
            "snapshotSha256": plan["snapshotGate"]["snapshotSha256"],
            "publishable": False,
        })
    counts = Counter(row["decision"] for row in rows)
    return {
        "version": VERSION, "recordType": "test", "sample": True,
        "date": DEMO_DATE, "raceCount": len(rows),
        "venues": list(DEMO_VENUES),
        "summary": {
            "simulate": counts["simulate"], "hold": counts["hold"],
            "skip": counts["skip"],
            "sampleStake": sum(r["stake"] for r in rows),
        },
        "rows": rows, "publishable": False,
        "livePredictionEnabled": False, "purchaseEnabled": False,
    }


CSS = """
*{box-sizing:border-box}html{color-scheme:dark}body{margin:0;background:#09172b;color:#edf4ff;font:15px/1.6 system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding:18px 14px 40px}
a{color:#e9c570}header{padding:14px 4px}h1{font-size:25px;margin:12px 0}
h2{font-size:20px;margin:5px 0 10px}.lead{color:#c6d6e8}
.warning{background:#382e24;border:1px solid #977949;border-radius:12px;color:#ffe4ad;padding:12px}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:18px 0}
.metric{background:#18314e;padding:12px;border-radius:12px;text-align:center}
.metric strong{display:block;font-size:26px;color:#e7c274}
.venue{margin:15px 0;border:1px solid #395475;border-radius:15px;background:#142a46;overflow:hidden}
.venue>summary{cursor:pointer;font-size:18px;font-weight:800;padding:15px}
.race{margin:9px 12px;padding:0 12px;background:#0c2038;border:1px solid #3b5470;border-radius:10px}
.race summary{cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 0}
.race strong{font-size:16px}.status{font-weight:700;font-size:12px;color:#b6d8ff}
.status.simulate{color:#f0cd73}.status.skip{color:#a8bccc}
.detail{padding:0 0 14px;color:#cad8e8}.detail p{margin:8px 0}
.rank{display:flex;flex-wrap:wrap;gap:6px;margin:7px 0 12px}
.rank span{border:1px solid #46617e;border-radius:8px;padding:6px 8px;font-weight:700}
.rank .S{color:#ecc86f}.rank .A{color:#ff696e}.rank .B{color:#a9d2ff}.rank .C{color:#d0d7e2}
pre{background:#10233b;border-radius:9px;padding:12px;overflow-x:auto;white-space:pre-wrap;overflow-wrap:anywhere}
footer{color:#b3c6d8;font-size:12px;margin:24px 0}
@media(max-width:380px){.metrics{gap:5px}.metric{padding:9px 3px}.metric strong{font-size:22px}}
"""


def render_batch_html(report):
    """Escape all dynamic text; no JS, local storage, or external requests."""
    if report.get("recordType") != "test" or report.get("publishable") is not False:
        raise ValueError("Only a synthetic report may be rendered")
    e = lambda x: escape(str(x), quote=True)
    summary = report["summary"]
    blocks = []
    for i, venue in enumerate(DEMO_VENUES):
        matches = [row for row in report["rows"] if row["track"] == venue]
        inner = []
        for row in matches:
            status = {"simulate": "参考買い目", "hold": "保留", "skip": "見送り"}[row["decision"]]
            ranked = "".join(
                '<span class="%s">%s位・%s番 %s</span>' % (
                    e(h["overall"]), e(h["rank"] or "—"), e(h["number"]), e(h["overall"]))
                for h in row["ranks"])
            choices = row["choices"]
            ticket_lines = "\n".join("-".join(map(str, t)) for t in row["tickets"])
            if not ticket_lines:
                ticket_lines = "買い目なし（保留・見送り）"
            inner.append(
                '<details class="race"><summary><strong>%dR</strong><span class="status %s">%s・%d点</span></summary>'
                '<div class="detail"><p>%s</p><div class="rank">%s</div>'
                '<p>1着：%s ／ 2着：%s ／ 3着：%s</p>'
                '<p>架空参考金額：%s円（1点100円）</p><details><summary>組み合わせ一覧</summary>'
                '<pre>%s</pre></details><p>根拠の検査指紋：%s…</p></div></details>' %
                (row["race"], e(row["decision"]), status, row["points"],
                 e(row["reason"]), ranked,
                 e(",".join(map(str, choices["first"])) or "—"),
                 e(",".join(map(str, choices["second"])) or "—"),
                 e(",".join(map(str, choices["third"])) or "—"),
                 e(format(row["stake"], ",")), e(ticket_lines),
                 e(row["snapshotSha256"][:12]))
            )
        blocks.append('<details class="venue"%s><summary>%s｜%dR</summary>%s</details>' %
                      (" open" if i == 0 else "", e(venue), len(matches), "".join(inner)))
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>競馬ナイン｜全R一括テスト（架空）</title>'
        '<link rel="stylesheet" href="/research-batch-demo.css"></head><body><main>'
        '<header><a href="/">← 本人用ホームへ</a><h1>🏇 全R一括テスト｜架空データ</h1>'
        '<p class="lead">架空の3競馬場×12R＝36Rを一度に処理する動作確認。</p>'
        '<p class="warning">2099年の架空開催・架空の8頭・架空の根拠だけを使用。'
        '実レース予想ではありません。AIの実データ分析・JRDBの取得・投票・購入・保存・公開は一切行いません。</p></header>'
        '<section class="metrics">'
        '<div class="metric">参考買い目<strong>%d R</strong></div>'
        '<div class="metric">保留<strong>%d R</strong></div>'
        '<div class="metric">見送り<strong>%d R</strong></div>'
        '</section><p class="lead">合計%dRを検査。参考買い目は最大40点まで。'
        '候補不足・資料欠損があれば無理に買い目を出しません。</p>'
        '%s<footer>本人認証後だけ表示。これはアルゴリズムのテストであり、'
        '予想精度や回収率を示すものではありません。</footer></main></body></html>'
    ) % (
        summary["simulate"], summary["hold"], summary["skip"],
        report["raceCount"], "".join(blocks)
    )
