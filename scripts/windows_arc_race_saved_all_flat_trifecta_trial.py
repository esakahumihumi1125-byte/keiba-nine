"""Local all-flat JRA-VAN study -> research-only trifecta holds/previews.

Consumes ONLY an existing sanitized all-flat-races JSON on the owner's PC.
No JV-Link, JRDB, HTTP, Render, GitHub, automatic bets, new history reads,
source identifiers or paid credentials. Never changes prior one-race files.
"""
import argparse
from collections import Counter
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import re
import sys
import tempfile

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_program_preview import TRACKS
from owner_jvdata_horse_history_coverage import JST
from owner_jvdata_offline_trifecta_trial import (
    build_local_trifecta_study, VERSION as STUDY_VERSION,
)
from windows_jvlink_weekly_read import JvLocalCheckError

VERSION = "arc-race-jvlink-all-flat-trifecta-study-1"
FILE = re.compile(r"jvdata-all-flat-races-(20[0-9]{6})[.]json\Z")
MAX_BYTES = 8_000_000
NO_REVERIFY = (
    "officialStarterListVerified", "officialScratchStateVerified",
    "officialGoingVerified", "formalTenFactorReady",
    "productionPredictionReady", "bettingReady", "autoPurchase",
    "historyCompletenessVerified", "captureTimeIndependentlyVerified",
)


def build_day_studies(report, *, as_of):
    """Reuse the existing per-R fail-closed matcher without modifying it."""
    if (not isinstance(as_of, datetime) or as_of.tzinfo is None
            or as_of.utcoffset() is None
            or not isinstance(report, dict)
            or report.get("version") != "owner-jvdata-local-day-history-bridge-1"
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or any(report.get(k) is not False for k in NO_REVERIFY)
            or type(report.get("date")) is not str
            or not _valid_date(report["date"])
            or type(report.get("raceCount")) is not int
            or not 1 <= report["raceCount"] <= 36
            or not isinstance(report.get("races"), list)
            or report["raceCount"] != len(report["races"])):
        raise CoverageError("Invalid all-flat research contract")
    # Use one common local instant; no retroactive results are used to rank.
    timestamp = as_of.astimezone(JST)
    seen, results = set(), []
    for row in report["races"]:
        if (not isinstance(row, dict)
                or row.get("track") not in TRACKS.values()
                or type(row.get("race")) is not int
                or not 1 <= row["race"] <= 12
                or row.get("graded") is not False
                or row.get("bettingReady") is not False):
            raise CoverageError("Invalid all-flat race")
        coordinate = row["track"], row["race"]
        if coordinate in seen:
            raise CoverageError("Duplicate all-flat race")
        seen.add(coordinate)
        one = dict(report)
        one["raceCount"] = 1
        one["races"] = [row]
        study = build_local_trifecta_study(one, as_of=timestamp)
        if (study.get("version") != STUDY_VERSION
                or study.get("track") != row["track"]
                or study.get("race") != row["race"]
                or study.get("date") != report["date"]
                or study.get("researchOnly") is not True
                or study.get("privateOwnerOnly") is not True
                or study.get("officialJraVerified") is not False
                or study.get("formalTenFactorReady") is not False
                or study.get("bettingReady") is not False
                or study.get("purchased") is not False
                or study.get("newProviderCalls") != 0
                or type(study.get("points")) is not int
                or not 0 <= study["points"] <= 48
                or (study["points"] == 0 and study["status"] != "hold")
                or (study["points"] > 0
                    and study["status"] != "local_history_research_only")):
            raise CoverageError("All-flat study returned invalid status")
        results.append(study)
    results.sort(key=lambda r: (r["track"], r["race"]))
    reasons = dict(sorted(Counter(
        row["holdReason"] for row in results if row["status"] == "hold"
    ).items()))
    drafts = sum(row["status"] == "local_history_research_only"
                 for row in results)
    return {
        "version": VERSION, "date": report["date"],
        "asOfJst": timestamp.isoformat(timespec="seconds"),
        "raceCount": len(results), "studyCount": drafts,
        "holdCount": len(results) - drafts, "holdReasons": reasons,
        "races": results, "newProviderCalls": 0, "ticketsIssued": 0,
        "signedReceiptsIssued": 0, "realPurchases": 0,
        "changesExistingRecords": False,
        "officialJraVerified": False, "formalTenFactorReady": False,
        "predictionValidated": False, "bettingReady": False,
        "privateOwnerOnly": True, "researchOnly": True,
        "note": ("すでにPCへ保存したJRA-VAN部分履歴だけを全R一括研究。"
                 "直近過去の同じ芝ダ・距離差200m以内の全頭比較が"
                 "発走前に成立したRのみ3連単の未購入参考を提示。"
                 "不一致・観測不足・発走済みは0点。実戦収支には含めない。"),
    }


def render_day_html(result):
    if (not isinstance(result, dict) or result.get("version") != VERSION
            or result.get("researchOnly") is not True
            or result.get("privateOwnerOnly") is not True
            or result.get("formalTenFactorReady") is not False
            or result.get("officialJraVerified") is not False
            or result.get("bettingReady") is not False):
        raise CoverageError("Bad all-flat local research output")
    e = lambda x: escape(str(x), quote=True)
    rows = [
        "<!doctype html><html lang='ja'><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>ARC RACE 全場研究用3連単（PC内のみ）</title>",
        "<style>body{font:15px/1.6 system-ui,sans-serif;max-width:850px;"
        "margin:auto;padding:18px;background:#10253c;color:#edf4ff}"
        "details{background:#193650;border:1px solid #4b6a87;border-radius:12px;"
        "padding:12px;margin:9px 0}summary{cursor:pointer;font-weight:700}"
        "strong{color:#f7d78b}.muted{color:#bdd0e2}</style>",
        "<h1>ARC RACE｜全場・過去走限定の3連単研究</h1>",
        "<p>追加のJRA-VAN / JRDB照会 0回。"
        "JRA最終出走・取消・馬場・時刻、調教、正式10項目100点は未照合。"
        "発走済みRには後付けの買い目を作りません。"
        "過去走比較は予測精度未検証。実購入・保存済み馬券・収支は不変。</p>",
        "<p>対象 " + e(result["raceCount"]) + "R／研究例 "
        + e(result["studyCount"]) + "R／見送り "
        + e(result["holdCount"]) + "R</p>",
    ]
    for row in result["races"]:
        label = (e(row["track"]) + " " + e(row["race"]) + "R")
        if row["status"] == "hold":
            rows.append("<details><summary>" + label
                        + "｜見送り・研究用0点</summary><p>理由："
                        + e(row["holdReason"]) + "</p><p>比較可能 "
                        + e(row["comparableRunners"]) + "/"
                        + e(row["runnerCount"]) + "頭。"
                        "欠損馬を低評価とみなしません。</p></details>")
        else:
            rows.append("<details><summary>" + label
                        + "｜過去走研究用" + e(row["points"])
                        + "点（未購入）</summary><p>1着：<strong>"
                        + e("・".join(map(str, row["first"])))
                        + "</strong>　2着：<strong>"
                        + e("・".join(map(str, row["second"])))
                        + "</strong>　3着：<strong>"
                        + e("・".join(map(str, row["third"])))
                        + "</strong></p><p class='muted'>正式10項目予想ではなく"
                        "過去走のみの仮説。購入・実収支の記録はしません。</p></details>")
    rows.append("</html>")
    return "".join(rows)


def local_path(day=None, *, appdata=None):
    day = day or datetime.now(JST).strftime("%Y%m%d")
    if type(day) is not str or not _valid_date(day):
        raise JvLocalCheckError("ALL_FLAT_DATE_INVALID")
    folder = Path(appdata or os.environ.get("LOCALAPPDATA") or "")
    if not folder.is_absolute():
        raise JvLocalCheckError("ALL_FLAT_LOCALAPPDATA_UNAVAILABLE")
    return folder / "ARC-RACE-private" / ("jvdata-all-flat-races-" + day + ".json")


def save_local_day_trial(source, *, as_of=None):
    if (not isinstance(source, Path) or not FILE.fullmatch(source.name)
            or source.is_symlink() or not source.is_file()
            or not 0 < source.stat().st_size <= MAX_BYTES):
        raise JvLocalCheckError("ALL_FLAT_SOURCE_INVALID")
    try:
        data = json.loads(source.read_text("utf-8"))
        if data.get("date") != FILE.fullmatch(source.name).group(1):
            raise CoverageError("Day file mismatch")
        research = build_day_studies(
            data, as_of=as_of if as_of is not None else datetime.now(JST),
        )
        content_json = json.dumps(research, ensure_ascii=False, indent=2)
        content_html = render_day_html(research)
    except (OSError, UnicodeError, ValueError, TypeError, CoverageError, KeyError):
        raise JvLocalCheckError("ALL_FLAT_SOURCE_INVALID") from None
    base = source.stem + "-trifecta-study"
    targets = (source.with_name(base + ".json"), source.with_name(base + ".html"))
    if any(p.exists() or p.is_symlink() for p in targets):
        raise JvLocalCheckError("ALL_FLAT_ALREADY_SAVED")
    staged, linked = [], []
    try:
        for content in (content_json, content_html):
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", prefix=".arc-race-all-study-",
                suffix=".tmp", dir=source.parent, delete=False,
            ) as output:
                pending = Path(output.name)
                staged.append(pending)
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
        for temp, target in zip(staged, targets):
            os.link(temp, target)
            linked.append(target)
    except FileExistsError:
        for target in linked:
            target.unlink(missing_ok=True)
        raise JvLocalCheckError("ALL_FLAT_ALREADY_SAVED") from None
    except OSError:
        for target in linked:
            target.unlink(missing_ok=True)
        raise JvLocalCheckError("ALL_FLAT_SAVE_FAILED") from None
    finally:
        for temp in staged:
            temp.unlink(missing_ok=True)
    return targets[1], research


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="ARC RACE: offline all-flat historical 3連単 study"
    )
    parser.add_argument("--date", default=None, help="YYYYMMDD (defaults to JST today)")
    args = parser.parse_args(argv)
    try:
        target, result = save_local_day_trial(local_path(args.date))
        print("ARC_RACE_ALL_FLAT_STUDY=SUCCESS_RESEARCH_ONLY")
        print("RACES=" + str(result["raceCount"]))
        print("RESEARCH_ONLY=" + str(result["studyCount"]))
        print("HOLD=" + str(result["holdCount"]))
        print("NEW_PROVIDER_REQUESTS=0")
        print("OFFICIAL_JRA_VERIFIED=NO")
        print("FORMAL_TEN_FACTOR_GRADED=NO")
        print("BETTING_READY=NO")
        if hasattr(os, "startfile"):
            try:
                os.startfile(str(target))
            except OSError:
                print("LOCAL_HTML_OPEN=MANUAL")
        return 0
    except JvLocalCheckError as error:
        print("ARC_RACE_ALL_FLAT_STUDY=" + str(error))
        print("NEW_PROVIDER_REQUESTS=0")
        return 1


if __name__ == "__main__":
    sys.exit(main())
