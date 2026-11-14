"""Unsigned, no-network 48-point formation salvage for HELD exact-score ties.

This considers only races with all ORIGINAL provisional two-factor scores
available, but whose old <=40-point generator withheld a candidate due to
unsplittable same-score group boundaries. It does NOT manufacture a precise
score, use an unknown recent grade, issue tickets, amend signed bets or
re-evaluate a race after the JRDB provisional off time.
"""
import re
from datetime import datetime, timedelta, timezone

from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION

VERSION = "owner-held-tie-48-preview-1"
JST = timezone(timedelta(hours=9))
DAY = re.compile(r"20\d{6}\Z")
TIME = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")


def _cutoff(runners, n):
    return 1 <= n <= len(runners) and (
        n == len(runners) or
        runners[n-1]["weightedResearchPoints"] >
        runners[n]["weightedResearchPoints"]
    )


def _candidate(race):
    horses = race.get("runners")
    if (not isinstance(horses, list) or not 4 <= len(horses) <= 18
            or race.get("horseCount") != len(horses)):
        return None
    seen, ranked = set(), []
    for h in horses:
        if (not isinstance(h, dict) or type(h.get("number")) is not int
                or not 1 <= h["number"] <= 18 or h["number"] in seen
                or h.get("training") not in ("S", "A", "B", "C")
                or h.get("recent") not in ("S", "A", "B", "C")
                or type(h.get("weightedResearchPoints")) is not int):
            return None
        seen.add(h["number"])
        # The score is solely the existing, complete 30:3 research ordinal.
        t, r = ("C", "B", "A", "S").index(h["training"]), (
            "C", "B", "A", "S").index(h["recent"])
        expected = 30*t+3*r
        if h["weightedResearchPoints"] != expected:
            return None
        ranked.append({"number":h["number"], "weightedResearchPoints":expected})
    ranked.sort(key=lambda x:(-x["weightedResearchPoints"],x["number"]))
    options=[]
    for first in (1,2,3):
        if not _cutoff(ranked,first):continue
        for second in range(first+1,min(6,len(ranked))+1):
            if not _cutoff(ranked,second):continue
            for third in range(max(3,second),min(12,len(ranked))+1):
                if not _cutoff(ranked,third):continue
                points=first*(second-1)*(third-2)
                if 12<=points<=48:
                    options.append((first,second,third,points))
    if not options:return None
    # Prefer the user's usual 30-40 points; allow 41-48 only for
    # previously held races, never modify ordinary prestart drafts.
    options.sort(key=lambda x:(
        30<=x[3]<=40, 41<=x[3]<=48,
        x[0]==2, x[0]==1, x[3]),reverse=True)
    first,second,third,points=options[0]
    return {
        "track":race["track"],"race":race["race"],
        "status":"unsplit_complete_two_factor_hold",
        "first":[h["number"] for h in ranked[:first]],
        "second":[h["number"] for h in ranked[:second]],
        "third":[h["number"] for h in ranked[:third]],
        "points":points,"completeRunnerCount":len(ranked),
        "allTiedScoreBoundariesUnsplit":True,
        "researchOnly":True,"officialJraVerified":False,
        "formalScoreReady":False,"predictionReady":False,
        "bettingReady":False,"receiptIssued":False,
        "actualPurchase":False,
    }


def preview_held_ties_48(report, day, *, now):
    if (not isinstance(report,dict) or report.get("version")!=DRAFT_VERSION
            or report.get("date")!=day or report.get("researchOnly") is not True
            or report.get("privateOwnerOnly") is not True
            or any(report.get(k) is not False for k in
                ("officialJraVerified","overallPredictionReady",
                 "bettingReady","autoPurchase"))
            or not isinstance(day,str) or not DAY.fullmatch(day)
            or not isinstance(now,datetime) or now.tzinfo is None
            or now.utcoffset() is None
            or not isinstance(report.get("races"),list)
            or report.get("raceCount")!=len(report["races"])
            or len(report["races"])>120):
        raise CoverageError("Invalid held-tie preview input")
    current=now.astimezone(JST)
    rows,seen,reviewed=[],set(),0
    for race in report["races"]:
        if (not isinstance(race,dict) or type(race.get("race")) is not int
                or not 1<=race["race"]<=12 or not isinstance(race.get("track"),str)
                or (race["track"],race["race"]) in seen
                or race.get("status") not in ("hold","provisional_draft")):
            raise CoverageError("Invalid source race for held tie preview")
        coord=race["track"],race["race"]
        seen.add(coord)
        if (race["status"]!="hold"
                or race.get("reason")!="ambiguous_equal_grade_boundary"):
            continue
        post=race.get("postTime")
        if not isinstance(post,str) or not TIME.fullmatch(post):continue
        try:
            off=datetime.strptime(day+post,"%Y%m%d%H:%M").replace(tzinfo=JST)
        except ValueError:
            continue
        if current>=off:continue
        reviewed+=1
        candidate=_candidate(race)
        if candidate:rows.append(candidate)
    return {
        "version":VERSION,"date":day,"raceCount":len(report["races"]),
        "reviewedPrestartTieHolds":reviewed,
        "unsignedReferenceCount":len(rows),"races":rows,
        "researchOnly":True,"privateOwnerOnly":True,
        "officialJraVerified":False,"formalTenFactorReady":False,
        "predictionReady":False,"bettingReady":False,
        "changesExistingDrafts":False,"changesExistingReceipts":False,
        "newProviderRequests":0,"ticketsIssued":0,
        "note":("従来40点で見送りとなった同点群の境界を"
                "恣意的に切らず、最大48通りまでに収まるときだけ"
                "署名なしの参考候補を提示。独立JRA照合・正式10項目"
                "得点・購入案や検証済み勝率ではありません。"),
    }
