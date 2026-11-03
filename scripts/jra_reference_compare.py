"""Private, deterministic comparison of an independently supplied race snapshot.

No JRA scraping or API access is implemented. A supplied snapshot can be a
manual transcription or a FUTURE authorized adapter: its origin is NOT
authenticated merely because it carries the word JRA. For that reason this
module never declares JRA official final verification, race readiness, grades
or bet readiness. Neither paid JRDB horse rows nor independent horse-level
records appear in the returned race-level summary.
"""
import re

from jrdb_race_day_gates import audit_race_day_checks
from jrdb_race_context import audit_race_context
from jrdb_coverage import CoverageError
from jrdb_program_preview import TRACKS

VERSION = "independent-reference-compare-1"
HORSE_NO = re.compile(r"(0[1-9]|1[0-8])\Z", re.ASCII)
JOCKEY_CODE = re.compile(r"[0-9A-Za-z]{1,12}\Z", re.ASCII)
ALLOWED_GOING = {"良", "稍重", "重", "不良"}
SURFACES = {"芝", "ダート", "障害"}
SOURCES = {"operator_transcription", "future_authorized_adapter"}
WITHDRAWN = {"active": "0", "withdrawn": "1", "unknown": None}
STATUS = ("missing_reference", "differences_found",
          "insufficient_comparable_fields", "no_differences_in_available_fields")


class ReferenceCompareError(ValueError):
    """Synthetic-safe validation failure without user/provider source text."""


def _valid_post(value):
    if value is None:
        return None
    if (not isinstance(value, str) or len(value) != 5 or value[2] != ":"
            or not value[:2].isascii() or not value[:2].isdigit()
            or not value[3:].isascii() or not value[3:].isdigit()
            or int(value[:2]) > 23 or int(value[3:]) > 59):
        raise ReferenceCompareError("Invalid independent post time")
    return value


def _valid_going(value):
    if value is None:
        return None
    if type(value) is not str or value not in ALLOWED_GOING:
        raise ReferenceCompareError("Invalid independent going")
    return value


def _valid_jockey(value):
    if value is None:
        return None
    if not isinstance(value, str) or not JOCKEY_CODE.fullmatch(value):
        raise ReferenceCompareError("Invalid jockey identifier")
    return value


def _reference_rows(snapshot, requested_date, expected_keys):
    if snapshot is None:
        return None
    if (not isinstance(snapshot, dict)
            or snapshot.get("date") != requested_date
            or snapshot.get("source") not in SOURCES
            or not isinstance(snapshot.get("races"), list)
            or len(snapshot["races"]) > 120
            or set(snapshot) != {"date", "source", "races"}):
        raise ReferenceCompareError("Invalid independent snapshot")
    result = {}
    for row in snapshot["races"]:
        if not isinstance(row, dict) or set(row) != {
            "track", "race", "completeRoster", "postTime",
            "going", "surface", "entries"
        }:
            raise ReferenceCompareError("Invalid independent race row")
        track, race = row["track"], row["race"]
        if (track not in TRACKS.values() or type(race) is not int
                or not 1 <= race <= 12 or (track, race) not in expected_keys
                or (track, race) in result
                or type(row["completeRoster"]) is not bool):
            raise ReferenceCompareError("Invalid independent race identity")
        _valid_post(row["postTime"])
        _valid_going(row["going"])
        surface = row["surface"]
        if surface is not None and (type(surface) is not str or surface not in SURFACES):
            raise ReferenceCompareError("Invalid independent race surface")
        entries = row["entries"]
        if not isinstance(entries, list) or len(entries) > 18:
            raise ReferenceCompareError("Invalid independent entry list")
        names = set()
        parsed = {}
        for starter in entries:
            if not isinstance(starter, dict) or set(starter) != {
                "horseNumber", "status", "jockeyCode"
            }:
                raise ReferenceCompareError("Invalid independent horse row")
            number = starter["horseNumber"]
            status = starter["status"]
            if (not isinstance(number, str) or not HORSE_NO.fullmatch(number)
                    or number in names or
                    not isinstance(status, str) or status not in WITHDRAWN):
                raise ReferenceCompareError("Duplicate or invalid horse status")
            names.add(number)
            parsed[number] = {
                "status": WITHDRAWN[status],
                "jockey": _valid_jockey(starter["jockeyCode"]),
            }
        result[track, race] = (row, parsed)
    return result


def compare_independent_race_snapshot(programme, entries, conditions,
                                      requested_date, independent_snapshot=None):
    """Check structured independent reference against validated JRDB day rows.

    A missing snapshot is the ordinary safe state. Differences are reported
    ONLY as aggregate per-race counts. For an incomplete official-style
    transcription, absent horse rows mean UNKNOWN, not cancellation.
    """
    source = audit_race_day_checks(programme, entries, conditions, requested_date)
    context = audit_race_context(programme, conditions, requested_date)
    prog = {(r["track"], r["race"]): r for r in programme}
    ctx = {(r["track"], r["race"]): r for r in context["races"]}
    ref = _reference_rows(independent_snapshot, requested_date, set(prog))
    by_number = {r["racekey"]: {} for r in programme}
    for runner in entries:
        # All identities and duplicate horse numbers already validated above.
        flag = runner.get("withdrawn_flag")
        if flag not in (None, "", "0", "1"):
            raise ReferenceCompareError("Unsupported source withdrawal status")
        jockey = _valid_jockey(runner.get("jockey_code"))
        by_number[runner["racekey"]][runner["horse_number"]] = {
            "status": flag if flag in ("0", "1") else None,
            "jockey": jockey,
        }
    reports = []
    for race in source["races"]:
        key = (race["track"], race["race"])
        program = prog[key]
        comparison = None if ref is None else ref.get(key)
        diffs = {
            "withdrawal": 0, "jockey": 0, "postTime": 0,
            "going": 0, "surface": 0, "roster": 0
        }
        compared = dict.fromkeys(diffs, 0)
        unknown = 0
        missing = comparison is None
        if not missing:
            reference, ref_horses = comparison
            rows = by_number[program["racekey"]]
            def field(name, left, right):
                nonlocal unknown
                if left is None or right is None or left == "未確認":
                    unknown += 1
                else:
                    compared[name] += 1
                    if left != right:
                        diffs[name] += 1
            field("postTime", program.get("post_time"), reference["postTime"])
            field("going", ctx[key]["going"], reference["going"])
            field("surface", program.get("surface"), reference["surface"])
            for number, source_runner in rows.items():
                row = ref_horses.get(number)
                if row is None:
                    if reference["completeRoster"]:
                        compared["roster"] += 1
                        diffs["roster"] += 1
                    else:
                        unknown += 1
                    continue
                field("withdrawal", source_runner["status"], row["status"])
                if source_runner["status"] == "0" and row["status"] == "0":
                    field("jockey", source_runner["jockey"], row["jockey"])
            for number in ref_horses:
                if number not in rows:
                    compared["roster"] += 1
                    diffs["roster"] += 1
            if reference["completeRoster"] and not ref_horses:
                # No runners is not a proof of cancellations, irrespective of
                # the provider's counted headcount.
                unknown += 1
        total_diff = sum(diffs.values())
        total_comparisons = sum(compared.values())
        state = ("missing_reference" if missing else
                 "differences_found" if total_diff else
                 "insufficient_comparable_fields" if not total_comparisons else
                 "no_differences_in_available_fields")
        reports.append({
            "track": race["track"], "race": race["race"],
            "independentReferenceProvided": not missing,
            "comparisonStatus": state,
            "differenceCount": total_diff,
            "differenceCategories": diffs,
            "comparableFields": total_comparisons,
            "unknownComparisons": unknown,
            "independentSnapshotAuthenticated": False,
            "officialJraFinalVerification": False,
            "officialStarterListVerified": False,
            "officialGoingVerified": False,
            "officialPostTimeVerified": False,
            "predictionReady": False, "bettingReady": False,
        })
    return {
        "version": VERSION,
        "raceCount": len(reports),
        "racesCompared": sum(x["independentReferenceProvided"] for x in reports),
        "racesWithDifferences": sum(x["differenceCount"] > 0 for x in reports),
        "racesMissingReference": sum(not x["independentReferenceProvided"] for x in reports),
        "officialJraFinalVerification": False,
        "predictionReady": False, "bettingReady": False,
        "races": reports,
        "note": ("独立資料の入力形式と出走馬・取消・騎手コード・馬場・"
                 "発走予定時刻の差異をレース単位で集計する研究用処理。"
                 "入力の出所を認証していないため、差分0件でも"
                 "JRA公式確認済み・予想可能・馬券購入可能とは判定しません。"
                 "公式データの取得・入力接続はまだ未実装です。"),
    }
