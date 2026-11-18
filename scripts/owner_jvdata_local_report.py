"""Static, owner-local summary of JV-Link prestart RA/SE CANDIDATES.

No network/JS/external assets. Only same-day race metadata, never licensed raw
records, horse names, horse IDs, provider keys, odds or secrets. Output remains
in the user's private Windows local app-data directory, not in ARC RACE public
pages or the Render server.
"""
from datetime import datetime
from html import escape
from jrdb_coverage import CoverageError
from jrdb_program_preview import TRACKS

VERSION = "owner-jvlink-local-html-summary-1"
WEEK_VERSION = "owner-jvlink-weekly-local-candidates-1"
CARD_VERSION = "owner-jvdata-ra-se-racecard-candidate-1"
TIME_RE = __import__("re").compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]\Z")
DAY_RE = __import__("re").compile(r"20[0-9]{6}\Z")
VENUES = frozenset(TRACKS.values())
MAX_RACES = 36


def render_weekly_candidate_summary(report):
    """Validate the exact safe candidate shape and render an OFFLINE status page.

    A roster match is only a research candidate. Official JRA finality,
    scratches, going, last-minute change and formal score remain unverified.
    """
    if (type(report) is not dict or report.get("version") != WEEK_VERSION
            or type(report.get("date")) is not str
            or not DAY_RE.fullmatch(report["date"])
            or not isinstance(report.get("races"), list)
            or type(report.get("raceCount")) is not int
            or report["raceCount"] != len(report["races"])
            or not 1 <= report["raceCount"] <= MAX_RACES
            or report.get("source") != "private_jvlink_weekly_ra_se_candidate"
            or report.get("privateOwnerOnly") is not True
            or report.get("researchOnly") is not True
            or report.get("providerDataRawIncluded") is not False
            or report.get("independentJraVerified") is not False
            or report.get("officialScratchesVerified") is not False
            or report.get("officialGoingVerified") is not False
            or report.get("officialFinalPostTimeVerified") is not False
            or report.get("productionPredictionReady") is not False
            or report.get("bettingReady") is not False
            or report.get("autoPurchase") is not False):
        raise CoverageError("Invalid unverified private report")
    try:
        day = datetime.strptime(report["date"], "%Y%m%d").strftime("%Y年%m月%d日")
    except ValueError:
        raise CoverageError("Invalid candidate day") from None

    races, seen = {}, set()
    for row in report["races"]:
        if (type(row) is not dict
                or row.get("version") != CARD_VERSION
                or row.get("date") != report["date"]
                or type(row.get("track")) is not str
                or row["track"] not in VENUES
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12
                or (row["track"], row["race"]) in seen
                or type(row.get("postTimeCandidate")) is not str
                or not TIME_RE.fullmatch(row["postTimeCandidate"])
                or type(row.get("registeredRunnerCount")) is not int
                or not 4 <= row["registeredRunnerCount"] <= 18
                or type(row.get("horseNumbersCandidate")) is not list
                or row.get("registeredRunnerCount") != len(row["horseNumbersCandidate"])
                or any(type(n) is not int or not 1 <= n <= 18
                       for n in row["horseNumbersCandidate"])
                or len(set(row["horseNumbersCandidate"])) != len(row["horseNumbersCandidate"])
                or row.get("privateInputOnly") is not True
                or row.get("sourceDataUseRightsVerified") is not False
                or row.get("sourceRecordCategory") != "numbered_racecard_not_final_changes"
                or row.get("independentlyAuthenticated") is not False
                or row.get("prestartDeliveryTimeVerified") is not False
                or row.get("finalStarterListVerified") is not False
                or row.get("scratchStatusVerified") is not False
                or row.get("latestGoingVerified") is not False
                or row.get("officialFinalPostTimeVerified") is not False
                or row.get("formalTenFactorReady") is not False
                or row.get("bettingReady") is not False):
            raise CoverageError("Invalid one-race private candidate")
        coord = (row["track"], row["race"])
        seen.add(coord)
        races.setdefault(row["track"], []).append(row)
    if not races:
        raise CoverageError("No private candidate races")

    groups = []
    for track in sorted(races):
        entries = sorted(races[track], key=lambda x: x["race"])
        count = len(entries)
        full = {r["race"] for r in entries} == set(range(1, 13))
        cards = []
        for r in entries:
            # No horse names, registration numbers, private source values,
            # raw records, grades, odds or anything beyond schedule metadata.
            cards.append(
                '<div class="race"><b>' + str(r["race"]) + 'R</b>'
                '<span>' + escape(r["postTimeCandidate"]) + ' 発走予定</span>'
                '<span>' + str(r["registeredRunnerCount"]) + '頭候補</span></div>')
        groups.append(
            '<section><h2>' + escape(track) + '</h2><p>'
            + str(count) + ' / 12R ｜ '
            + ('12R確認（当初出馬表候補のみ）' if full else '未取得のRあり')
            + '</p><div class="races">' + ''.join(cards) + '</div></section>')
    styles = (
        'body{background:#0d192b;color:#edf4ff;font:16px system-ui,sans-serif;'
        'margin:auto;max-width:900px;padding:22px;line-height:1.6}'
        'h1{font-size:25px;margin-bottom:5px}h2{font-size:21px;margin-bottom:2px}'
        'section{background:#17283d;border:1px solid #34506e;border-radius:13px;'
        'padding:14px 18px;margin:16px 0}section p{color:#bdd2e7;margin-top:0}'
        '.races{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));'
        'gap:8px}.race{background:#234464;border-radius:8px;padding:10px}'
        '.race b{display:block;font-size:19px}.race span{display:block;font-size:13px}'
        '.notice{border-left:4px solid #68b9f8;padding:11px 13px;background:#16324b}'
        '.muted{font-size:14px;color:#adc5dc}'
    )
    return (
        '<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" '
        'content="default-src &apos;none&apos;; style-src &apos;unsafe-inline&apos;">'
        '<title>ARC RACE｜出馬表候補・内部確認</title>'
        '<style>' + styles + '</style></head><body>'
        '<h1>ARC RACE｜JRA-VAN出馬表候補</h1>'
        '<p>' + escape(day) + ' ｜観測 ' + str(len(races))
        + '場 / ' + str(report["raceCount"]) + 'R</p>'
        '<p class="notice"><b>まだJRA公式最終確認ではありません。</b>'
        '馬番・発走予定の候補のみ。取消、直前の馬場・時刻変更、'
        '開催場全体の網羅性、正式10項目採点、馬券は未確認です。</p>'
        + ''.join(groups)
        + '<p class="muted">PC内だけで作られた読み取り結果です。'
        '実データのダウンロード成功と、正式予想の完成は別です。</p>'
        '</body></html>'
    )
