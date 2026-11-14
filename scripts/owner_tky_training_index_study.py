"""Read-only prestart JRDB /tky *training_arrow* plus *training_index*.

The JRDB reference instructs analysts to PRIORITIZE the five-category
training arrow over the specialist training index when these conflict.
Never combine their rankings into a fabricated 30-point model or convert
to /tcy '追切指数' / '仕上指数' grades. Only owner-private observations,
horse numbers and public category labels leave this helper: no raw
paid numeric indexes, new provider reads, ticket issues or receipt edits.
"""
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime

from jrdb_coverage import CoverageError, audit_race_coverage
from jrdb_evidence_readiness import _valid_date, HORSE_ID
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION, JST

VERSION = "owner-tky-training-index-study-2"
# JRDB's official training-arrow code table (1=excellent, 5=declining).
# These are expert opinion categories, NOT calibrated winning probabilities.
ARROWS = {
    "1": "デキ抜群",
    "2": "上昇",
    "3": "平行線",
    "4": "やや下降",
    "5": "デキ落ち",
}
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
    """Compare two DISTINCT source observations, never impute missing rows.

    Show the training-arrow categories first. Numeric training_index rank is
    shown separately as descriptive research, NEVER as overriding an arrow.
    Horses missing either observation stay unobserved for THAT field.
    """
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
        arrow_observations = []
        for item in raw:
            number = int(item["horse_number"])
            metric = _index(item.get("training_index"))
            if metric is not None:
                available.append((number, metric))
            arrow = item.get("training_arrow")
            if type(arrow) is str and arrow in ARROWS:
                arrow_observations.append((number, arrow))
        # One numerical index alone cannot form an index comparison.
        if len(available) < 2:
            available = []
        # Two arrow codes alone CAN convey expert condition categories;
        # a sparse numeric index must never erase those observations.
        if len(available) < 2 and len(arrow_observations) < 2:
            continue
        available.sort(key=lambda x: (-x[1], x[0]))
        ranked, previous, rank = [], None, None
        for place, (number, value) in enumerate(available, 1):
            if value != previous:
                rank = place
            ranked.append({"number": number, "observedRank": rank})
            previous = value
        arrow_observations.sort(key=lambda x: (int(x[1]), x[0]))
        arrow_rows = [
            {"number": number, "condition": ARROWS[arrow]}
            for number, arrow in arrow_observations
        ]
        study.append({
            "track": coord[0], "race": coord[1],
            "rosterCount": len(raw), "observedCount": len(ranked),
            "unassessedCount": len(raw) - len(ranked),
            "arrowObservedCount": len(arrow_rows),
            "arrowUnobservedCount": len(raw) - len(arrow_rows),
            "rankingScope": "tky_arrow_first_index_descriptive_only",
            "runners": ranked, "arrows": arrow_rows,
        })
    return {
        "version":VERSION,"date":day,"raceCount":len(programme),
        "studiedRaceCount":len(study),"races":study,
        "sourceMetric":"tky_training_index_and_training_arrow",
        "trainingArrowPriority":True,
        "trainingSourceDistinctFromTcy":True,
        "researchOnly":True,"privateOwnerOnly":True,
        "officialJraVerified":False,"modelCalibrated":False,
        "training30Ready":False,"predictionReady":False,
        "bettingReady":False,"ticketsIssued":0,
        "newProviderRequests":0,"changesExistingDrafts":False,
        "changesExistingReceipts":False,"rawIndicesIncluded":False,
        "note":("JRDB公式の見方に従い調教矢印の5段階評価を先に表示し、"
                "別系統の調教指数は数値順の参考として独立表示。"
                "指数と矢印の評価が異なる場合は矢印を優先。"
                "欠測馬を最下位扱いせず、/tcy追切・仕上指数や"
                "正式調教30点・総合順位・3連単には使用しません。"),
    }
