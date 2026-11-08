"""Server-attested owner-only *research watch*, sealed before provisional off.

The receipt shows when this server froze a small candidate set, NOT that
JRA schedules, runners or outcomes were independently verified. There is no
ticket purchase, official-result feed or retrospective rewriting here.
Only authenticated owner-triggered /history requests may issue receipts.
"""
from datetime import datetime, timezone, timedelta, date
import hashlib
import hmac
import json
import re

VERSION = "owner-rebound-watch-receipt-1"
DOMAIN = b"keiba-nine/owner-rebound-watch/v1"
JST = timezone(timedelta(hours=9))
MAX_RACES = 36
ALLOWED_STATES = frozenset((
    "cross_source_review", "overlapping_history_only", "need_more_evidence"
))


class WatchReceiptError(ValueError):
    pass


def _timestamp(value):
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise WatchReceiptError("Invalid server time") from None
    if (not isinstance(value, datetime) or value.tzinfo is None
            or value.utcoffset() is None):
        raise WatchReceiptError("Timezone-aware server time required")
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _day(value):
    if not isinstance(value, str) or not re.fullmatch(r"20\d{6}", value):
        raise WatchReceiptError("Invalid selected day")
    try:
        if date.fromisoformat(value[:4]+"-"+value[4:6]+"-"+value[6:]).strftime("%Y%m%d") != value:
            raise ValueError()
    except ValueError:
        raise WatchReceiptError("Invalid selected day") from None
    return value


def _key(secret):
    if not isinstance(secret, str) or len(secret) < 32:
        raise WatchReceiptError("Server signing key missing")
    return hmac.new(secret.encode("utf8"), DOMAIN, hashlib.sha256).digest()


def _seal(snapshot, secret):
    raw = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode("utf8")
    return hmac.new(_key(secret), raw, hashlib.sha256).hexdigest()


def _validate_watch(snapshot):
    allowed = {"version","date","track","race","sourceKind",
               "capturedAt","scheduledOffAt","watch",
               "researchOnly","officialJraVerified","actualPurchase",
               "winnerPickReady","captureAuditVerified"}
    if (not isinstance(snapshot, dict) or set(snapshot) != allowed
            or snapshot["version"] != VERSION
            or snapshot["sourceKind"] != "server-prestart-research-watch"
            or any(snapshot.get(k) is not False for k in (
                "officialJraVerified","actualPurchase","winnerPickReady",
                "captureAuditVerified"))
            or snapshot.get("researchOnly") is not True):
        raise WatchReceiptError("Invalid watch snapshot")
    day = _day(snapshot["date"])
    if (not isinstance(snapshot["track"], str)
            or snapshot["track"] not in (
                "札幌","函館","福島","新潟","東京","中山","中京",
                "京都","阪神","小倉")
            or type(snapshot["race"]) is not int
            or not 1 <= snapshot["race"] <= 12
            or not isinstance(snapshot["watch"], list)
            or not 1 <= len(snapshot["watch"]) <= 18):
        raise WatchReceiptError("Invalid watch race")
    if (not isinstance(snapshot["capturedAt"], str)
            or not isinstance(snapshot["scheduledOffAt"], str)):
        raise WatchReceiptError("Invalid capture timestamp")
    captured, off = _timestamp(snapshot["capturedAt"]), _timestamp(snapshot["scheduledOffAt"])
    if captured >= off or off.astimezone(JST).date().strftime("%Y%m%d") != day:
        raise WatchReceiptError("Watch was not captured before provisional off")
    if (off - captured).total_seconds() > 60*60*24*7:
        raise WatchReceiptError("Capture too early for this provisional day")
    last = 0
    for row in snapshot["watch"]:
        if (not isinstance(row, dict)
                or set(row) != {"number","reviewState"}
                or type(row["number"]) is not int
                or not last < row["number"] <= 18
                or row["reviewState"] not in ALLOWED_STATES):
            raise WatchReceiptError("Invalid sorted watch entries")
        last = row["number"]
    return (day, snapshot["track"], snapshot["race"])


def issue_rebound_watch_receipts(history, programme, secret, day, now=None):
    """Sign at most 36 non-empty, prestart owner-only watch snapshots.

    This is a second research capture, independent of signed 3連単 receipts.
    Not a self-validated statement of official schedule / result.
    """
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    review = history.get("reboundContextReview") if isinstance(history, dict) else None
    if (history.get("date") != day or history.get("predictionReady") is not False
            or not isinstance(review, dict)
            or review.get("version") != "owner-rebound-context-review-1"
            or review.get("researchOnly") is not True
            or any(review.get(k) is not False for k in (
                "officialJraVerified","overallScoreReady","winPickReady",
                "bettingReady","autoPurchase","modifiesFrozenPicks"))
            or not isinstance(review.get("races"), list)
            or type(review.get("raceCount")) is not int
            or len(review["races"]) != review["raceCount"]
            or len(review["races"]) > MAX_RACES
            or not isinstance(programme, list)
            or len(programme) != len(review["races"])):
        raise WatchReceiptError("Invalid private historical review")
    by_programme = {}
    for r in programme:
        if (not isinstance(r, dict) or r.get("racedate") != day
                or type(r.get("race")) is not int
                or not isinstance(r.get("track"), str)):
            raise WatchReceiptError("Invalid programme source")
        k=(r["track"],r["race"])
        if k in by_programme:
            raise WatchReceiptError("Ambiguous programme")
        by_programme[k]=r
    output,seen,skipped = [],set(),0
    for r in review["races"]:
        if not isinstance(r, dict):
            raise WatchReceiptError("Invalid review row")
        key=(r.get("track"),r.get("race"))
        if key in seen or key not in by_programme or r.get("winPickReady") is not False:
            raise WatchReceiptError("Review does not match programme")
        seen.add(key)
        raw=r.get("watch")
        if (not isinstance(raw,list) or type(r.get("watchCount")) is not int
                or len(raw) != r["watchCount"]):
            raise WatchReceiptError("Invalid watch count")
        if not raw:
            continue
        post=by_programme[key].get("post_time")
        if not isinstance(post,str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",post):
            skipped+=1
            continue
        off=datetime.fromisoformat(
            f"{day[:4]}-{day[4:6]}-{day[6:]}T{post}:00+09:00")
        if now >= off.astimezone(timezone.utc):
            skipped+=1
            continue
        # Validate everything before signing any receipt; no trace of paid
        # JRDB rows, horse names, reasons, IDs or race keys is persisted.
        watch = sorted(({"number":x["number"],"reviewState":x["reviewState"]}
                        for x in raw),key=lambda x:x["number"])
        snapshot = {
            "version":VERSION,"date":day,"track":key[0],"race":key[1],
            "sourceKind":"server-prestart-research-watch",
            "capturedAt":now.isoformat(),
            "scheduledOffAt":off.astimezone(timezone.utc).isoformat(),
            "watch":watch,"researchOnly":True,
            "officialJraVerified":False,"actualPurchase":False,
            "winnerPickReady":False,"captureAuditVerified":False,
        }
        _validate_watch(snapshot)
        output.append({"snapshot":snapshot,"signature":_seal(snapshot,secret)})
    if seen != set(by_programme):
        raise WatchReceiptError("Incomplete review schedule")
    return {"version":VERSION,"date":day,"receipts":output,
            "receiptCount":len(output),
            "postOffOrMissingTimeRaces":skipped,
            "serverSigned":True,"officialFeedConnected":False,
            "jraScheduleVerified":False,"officialResultsVerified":False,
            "actualPurchase":False,"purchaseReady":False}


def verify_rebound_watch_receipts(receipts, secret, day):
    """Server-side verification ONLY; never trust local storage as authority."""
    _day(day)
    if (not isinstance(receipts,list) or len(receipts)>MAX_RACES):
        raise WatchReceiptError("Invalid receipt collection")
    seen,checked=set(),[]
    for record in receipts:
        if not isinstance(record,dict) or set(record)!={"snapshot","signature"}:
            raise WatchReceiptError("Invalid signed record")
        snapshot=record["snapshot"]
        identity=_validate_watch(snapshot)
        if snapshot["date"]!=day or identity in seen:
            raise WatchReceiptError("Duplicate or different-day watch")
        signature=record["signature"]
        if (not isinstance(signature,str) or not re.fullmatch("[0-9a-f]{64}",signature)
                or not hmac.compare_digest(signature,_seal(snapshot,secret))):
            raise WatchReceiptError("Unverified watch signature")
        seen.add(identity)
        checked.append(snapshot)
    return checked


def compare_watched_winners(verified_watch, official_results):
    """Pure future adapter; only the SERVER may supply independently sourced results.

    No active production route supplies official_results. Missing, ambiguous,
    abandoned or refunded races must not count as wins or losses.
    """
    if (not isinstance(verified_watch,list) or not isinstance(official_results,list)
            or len(verified_watch)>MAX_RACES or len(official_results)>MAX_RACES):
        raise WatchReceiptError("Invalid result comparison inputs")
    watches={}
    for snap in verified_watch:
        k=_validate_watch(snap)
        if k in watches:raise WatchReceiptError("Duplicate watch")
        watches[k]=snap
    outcomes={}
    for result in official_results:
        if not isinstance(result,dict):
            raise WatchReceiptError("Untrusted result row")
        key=(result.get("date"),result.get("track"),result.get("race"))
        if key in outcomes or key not in watches:
            raise WatchReceiptError("Results do not match frozen watches")
        outcomes[key]=result
    rows=[]
    for key,watch in watches.items():
        result=outcomes.get(key)
        confirmed=(isinstance(result,dict)
                   and result.get("officialVerified") is True
                   and result.get("sourceKind")=="independent-official-result"
                   and result.get("deadHeat") is False
                   and result.get("refundRequired") is False
                   and result.get("raceAbandoned") is False
                   and type(result.get("winner")) is int
                   and 1<=result["winner"]<=18)
        winner = result["winner"] if confirmed else None
        watch_map={r["number"]:r["reviewState"] for r in watch["watch"]}
        included=winner in watch_map if confirmed else None
        rows.append({
            "date":key[0],"track":key[1],"race":key[2],
            "status":"verified_result" if confirmed else "pending",
            "watchCount":len(watch_map),
            "winnerWasWatched":included,
            "winnerWasCrossSourceReview":(
                watch_map.get(winner)=="cross_source_review"
                if included else False if confirmed else None),
        })
    done=[r for r in rows if r["status"]=="verified_result"]
    return {
        "version":"owner-rebound-outcome-diagnostic-1",
        "races":rows,"reviewedRaces":len(done),
        "pendingRaces":len(rows)-len(done),
        "winnersInWatch":sum(r["winnerWasWatched"] is True for r in done),
        "winnersInCrossSource":sum(
            r["winnerWasCrossSourceReview"] is True for r in done),
        "researchOnly":True,"actualPurchase":False,
        "officialFeedConnected":False,"outcomeCalibrationReady":False,
        "note":"JRA公式結果の独立取得が接続されるまで成績は保留。",
    }
