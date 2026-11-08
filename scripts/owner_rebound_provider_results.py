"""Private JRDB /tse preliminary outcome cross-check against sealed watch records.

JRDB is a separate provider, NOT an independent official JRA result source.
No odds, horse names, winner IDs, proprietary raw rows or race keys escape.
No result updates any saved watches, tickets, ROI, or actual purchase state.
"""
from datetime import datetime, timezone
import re

from owner_rebound_receipts import _validate_watch, _day, _timestamp, WatchReceiptError
from jrdb_program_preview import TRACKS

VERSION = "owner-rebound-provider-check-1"
MAX_SOURCE_ROWS = 2160


def summarize_provider_watch_results(watches, rows, day, now=None,
                                     source_read_count=1):
    """One day /tse, all original watches remain immutable; never official."""
    _day(day)
    now = _timestamp(datetime.now(timezone.utc) if now is None else now)
    if (source_read_count not in (0,1) or type(source_read_count) is not int
            or not isinstance(watches,list) or len(watches)>36 or
            not isinstance(rows,list) or len(rows)>MAX_SOURCE_ROWS
            or (source_read_count==0 and rows)):
        raise WatchReceiptError("Invalid postrace source collection")
    by_coord, by_watch = {}, {}
    for snap in watches:
        key=_validate_watch(snap)
        if key[0] != day or key in by_watch:
            raise WatchReceiptError("Watch date or identity mismatch")
        by_watch[key]=snap
    # Collapse by race slot, not by horse ID. Contradictions and partial
    # races never become official or go into denominator of settled ROI.
    for entry in rows:
        if not isinstance(entry,dict):
            raise WatchReceiptError("Invalid postrace source row")
        racekey,racedate=entry.get("racekey"),entry.get("racedate")
        number,finish=entry.get("horse_number"),entry.get("order_of_finish")
        if (not isinstance(racekey,str)
                or not re.fullmatch(r"[0-9a-f]{8}",racekey)
                or racedate != day or racekey[2:4] != day[2:4]
                or racekey[:2] not in TRACKS
                or not racekey[6:].isdigit()
                or not 1 <= int(racekey[6:]) <= 12
                or not isinstance(number,str)
                or not re.fullmatch(r"(?:0[1-9]|1[0-8])",number)):
            raise WatchReceiptError("Postrace source identity mismatch")
        track,race=TRACKS[racekey[:2]],int(racekey[6:])
        slot=(track,race)
        if slot not in by_coord:
            by_coord[slot]={"keys":set(),"numbers":set(),"first":[],
                            "podiumCounts":{1:0,2:0,3:0},
                            "duplicate":False,"rows":0}
        target=by_coord[slot]
        target["keys"].add(racekey)
        n=int(number)
        if n in target["numbers"]:
            target["duplicate"]=True
        target["numbers"].add(n)
        target["rows"]+=1
        if finish is not None and not isinstance(finish,str):
            raise WatchReceiptError("Unexpected postrace finish type")
        if finish is not None and finish != "":
            if not re.fullmatch(r"0?[1-9]|1[0-8]",finish):
                # Some nonstandard/special outcome markers remain unknown.
                # Do not infer a winner or declare a miss from them.
                target["duplicate"]=True
            else:
                place=int(finish)
                trouble=entry.get("trouble_classification")
                if trouble not in (None,"","0"):
                    target["duplicate"]=True
                if place in (1,2,3):
                    target["podiumCounts"][place]+=1
                if place==1:
                    target["first"].append(n)
        if target["rows"]>18:
            target["duplicate"]=True
    races=[]
    for key,snap in by_watch.items():
        slot=key[1:]
        fetched=by_coord.get(slot)
        started=now>=_timestamp(snap["scheduledOffAt"])
        # A single winning row is not even a stable 1st-place *observation*:
        # require distinct 1st/2nd/3rd rows, otherwise treat as pending.
        # This still is NOT independent official JRA verification.
        ok=(started and fetched is not None and not fetched["duplicate"]
            and len(fetched["keys"])==1 and len(fetched["first"])==1
            and fetched["podiumCounts"]=={1:1,2:1,3:1})
        winner=fetched["first"][0] if ok else None
        watched={h["number"]:h["reviewState"] for h in snap["watch"]}
        observed=winner in watched if ok else None
        races.append({
            "track":key[1],"race":key[2],
            "watchCount":len(snap["watch"]),
            "providerStatus":"first_place_observed" if ok else "pending",
            "observedFirstNumber":winner,
            "observedFirstInWatch":observed,
            "observedFirstInPriorityWatch":(
                watched.get(winner)=="cross_source_review"
                if observed else False if ok else None),
            "officialVerified":False,
            "confirmedWatchHit":None,
            "confirmedPredictionHit":None,
        })
    noted=[r for r in races if r["providerStatus"]=="first_place_observed"]
    return {
        "version":VERSION,"date":day,
        "sourceKind":"jrdb-tse-provider-observation",
        "providerSourceReadCount":source_read_count,
        "raceCount":len(races),"races":races,
        "observedRaceCount":len(noted),
        "observedFirstInWatchCount":sum(r["observedFirstInWatch"] is True for r in noted),
        "observedFirstInPriorityCount":sum(
            r["observedFirstInPriorityWatch"] is True for r in noted),
        "verifiedRaceCount":0,"verifiedWatchHitCount":None,
        "officialJraVerified":False,"jraIndependentConfirmation":False,
        "officialFeedConnected":False,
        "outcomeCalibrationReady":False,"bettingReady":False,
        "actualPurchase":False,"payoutVerified":False,"roiPercent":None,
        "sourceIncompleteCouldChange":True,
        "researchOnly":True,"privateOwnerOnly":True,
        "note":("JRDBの成績情報で1着候補を照合した暫定値。"
                "独立したJRA公式着順照合が完了するまで"
                "的中・不的中、回収率、モデル精度には算入しません。"),
    }
