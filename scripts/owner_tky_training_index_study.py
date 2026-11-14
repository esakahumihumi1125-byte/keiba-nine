"""Read-only prestart alternative JRDB /tky *training_index* ordering.

JRDB's /tky '調教指数' (information/analyst index) is distinct from
/tcy '追切指数' & '仕上指数'. Never infer /tcy grades, 30-point scores,
win chances or betting picks from this separate index. The private caller
has already fetched /tky; no API calls, raw values or horse identities
other than programme horse numbers are returned.
"""
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime

from jrdb_coverage import CoverageError, audit_race_coverage
from jrdb_evidence_readiness import _valid_date, HORSE_ID
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION, JST

VERSION = "owner-tky-training-index-study-1"
DECIMAL = re.compile(r"-?\d{1,4}(?:\.\d{1,3})?\Z")
POST = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")
MAX_RACES = 120


def _index(value):
    if value is None or value == "":
        return None
    if type(value) in (int, float):
        if not -1000 <= value <= 1000:
            return None
        value = str(value)
    if type(value) is not str or not DECIMAL.fullmatch(value):
        return None
    try:
        n = Decimal(value)
    except InvalidOperation:
        return None
    return n if n.is_finite() and -1000 <= n <= 1000 else None


def tky_training_index_study(programme, entries, report, day, *, now):
    """Private, rank observed runners only; missing indices are NOT last."""
    if (not _valid_date(day) or not isinstance(programme, list)
            or len(programme) > MAX_RACES or not isinstance(entries, list)
            or not isinstance(report, dict)
            or report.get("version") != DRAFT_VERSION
            or report.get("date") != day
            or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or report.get("officialJraVerified") is not False
            or report.get("overallPredictionReady") is not False
            or report.get("bettingReady") is not False
            or report.get("raceCount") != len(programme)
            or not isinstance(report.get("races"), list)
            or len(report["races"]) != len(programme)
            or not isinstance(now, datetime)
            or now.tzinfo is None or now.utcoffset() is None):
        raise CoverageError("Invalid tky training index study input")
    # No source writes and no silent entry creation from a sparse response.
    audit_race_coverage(programme, entries, day)
    groups = {r["racekey"]: [] for r in programme}
    for row in entries:
        groups[row["racekey"]].append(row)
    observed_report = {}
    for race in report["races"]:
        coord = race.get("track"),race.get("race")
        if coord in observed_report:
            raise CoverageError("Duplicate research race")
        observed_report[coord] = race
    if len(observed_report) != len(programme):
        raise CoverageError("Incomplete research race set")
    study = []
    current = now.astimezone(JST)
    for race in programme:
        coord = race["track"], race["race"]
        base = observed_report.get(coord)
        if base is None:
            raise CoverageError("Research race identity mismatch")
        if (base.get("status") != "hold"
                or base.get("reason") != "missing_factors"
                or base.get("postTime") != race.get("post_time")
                or base.get("horseCount") != race.get("headcount")):
            continue
        post = race.get("post_time")
        if type(post) is not str or not POST.fullmatch(post):
            continue
        try:
            off = datetime.strptime(day+post,"%Y%m%d%H:%M").replace(tzinfo=JST)
        except ValueError:
            continue
        if current >= off:
            continue
        raw = groups[race["racekey"]]
        original = base.get("runners")
        if (not isinstance(original, list)
                or not 4 <= len(original) <= 18
                or len(original) != len(raw)
                or race.get("headcount") != len(raw)
                or not any(h.get("training") == "未評価" for h in original)):
            continue
        numbers = [h.get("number") for h in original]
        if (any(type(n) is not int or not 1 <= n <= 18 for n in numbers)
                or len(set(numbers)) != len(numbers)
                or {int(x["horse_number"]) for x in raw} != set(numbers)
                or any(x.get("withdrawn_flag") not in ("0", "", None) for x in raw)):
            continue
        ids = [x.get("horse_id") for x in raw if x.get("horse_id") not in (None,"")]
        if (any(type(hid) is not str or not HORSE_ID.fullmatch(hid) for hid in ids)
                or len(set(ids)) != len(ids)):
            continue
        available = []
        for item in raw:
            metric = _index(item.get("training_index"))
            if metric is not None:
                available.append((int(item["horse_number"]),metric))
        if len(available) < 2:
            continue
        available.sort(key=lambda x: (-x[1],x[0]))
        ranked,previous,rank = [],None,None
        for place,(number,value) in enumerate(available,1):
            if value != previous:
                rank=place
            ranked.append({"number":number,"observedRank":rank})
            previous=value
        study.append({
            "track":coord[0],"race":coord[1],
            "rosterCount":len(raw),"observedCount":len(ranked),
            "unassessedCount":len(raw)-len(ranked),
            "rankingScope":"observed_tky_training_index_only",
            "runners":ranked,
        })
    return {
        "version":VERSION,"date":day,"raceCount":len(programme),
        "studiedRaceCount":len(study),"races":study,
        "sourceMetric":"tky_training_index",
        "trainingSourceDistinctFromTcy":True,
        "researchOnly":True,"privateOwnerOnly":True,
        "officialJraVerified":False,"modelCalibrated":False,
        "training30Ready":False,"predictionReady":False,
        "bettingReady":False,"ticketsIssued":0,
        "newProviderRequests":0,"changesExistingDrafts":False,
        "changesExistingReceipts":False,"rawIndicesIncluded":False,
        "note":("出走馬データに含まれる別系統の調教指数の観測馬だけを"
                "指数順で表示。追切指数/仕上指数と同一視せず、"
                "欠測馬を最下位扱いしない。正式な調教30点、"
                "総合順位、3連単、JRA公式照合には使用しません。"),
    }
