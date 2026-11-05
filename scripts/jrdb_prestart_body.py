"""Private-only prestart /tpd data presence audit (not a body condition grade).

The beta endpoint includes horse weight, paddock and odds. Odds and provider
indices are deliberately ignored by this source-presence check, and no
horse-level values, identities, paid data or timestamps escape the response.
The source includes potentially unavailable/null rows; 0 kg is not a measured
body weight. A provider-reported weight is not independently JRA-verified.
"""
import re
from jrdb_coverage import CoverageError, audit_race_coverage
from jrdb_evidence_readiness import _valid_date

VERSION = "private-prestart-body-1"
HORSE_ID = re.compile(r"[0-9a-z]{12}\Z", re.ASCII)
NO = re.compile(r"(0[1-9]|1[0-8])\Z", re.ASCII)
KEY = re.compile(r"[0-9a-f]{8}\Z", re.ASCII)


def _present(value):
    return isinstance(value, str) and bool(value.strip())


def audit_prestart_body(programme, entries, prestart, racedate):
    """Join 0..2160 /tpd rows to /tky using stable horse id or horse number."""
    if not _valid_date(racedate):
        raise CoverageError("Invalid prestart date")
    base = audit_race_coverage(programme, entries, racedate)
    if not isinstance(prestart, list) or len(prestart) > 2160 or any(
            not isinstance(row, dict) for row in prestart):
        raise CoverageError("Invalid prestart collection")

    by_key = {row["racekey"]: {} for row in programme}
    by_id = {}
    for entry in entries:
        key, num, hid = entry["racekey"], entry["horse_number"], entry.get("horse_id")
        by_key[key][num] = (key, num)
        if hid not in (None, ""):
            if not isinstance(hid, str) or not HORSE_ID.fullmatch(hid):
                raise CoverageError("Invalid entry horse id")
            pair = (key, hid)
            if pair in by_id:
                raise CoverageError("Ambiguous entry horse id")
            by_id[pair] = (key, num)
    observed = set()
    counters = {key: dict(bodyWeight=0, weightChange=0, paddock=0,
                          reportedBodyState=0, reportedWithdrawn=0)
                for key in by_key}
    for record in prestart:
        key, date = record.get("racekey"), record.get("racedate")
        if (not isinstance(key, str) or not KEY.fullmatch(key)
                or key not in by_key or date != racedate):
            raise CoverageError("Prestart row belongs to another race/date")
        num, hid = record.get("horse_number"), record.get("horse_id")
        if num not in (None, "") and (
                not isinstance(num, str) or not NO.fullmatch(num)):
            raise CoverageError("Invalid prestart horse number")
        if hid not in (None, "") and (
                not isinstance(hid, str) or not HORSE_ID.fullmatch(hid)):
            raise CoverageError("Invalid prestart horse id")
        number_pair = by_key[key].get(num) if num not in (None, "") else None
        horse_pair = by_id.get((key, hid)) if hid not in (None, "") else None
        if (number_pair and horse_pair and number_pair != horse_pair):
            raise CoverageError("Prestart horse identity conflict")
        identity = number_pair or horse_pair
        if identity is None or identity in observed:
            raise CoverageError("Unknown or duplicate prestart entrant")
        observed.add(identity)
        weight = record.get("horse_weight")
        change = record.get("weight_cycling")
        if weight is not None and (type(weight) is not int or not 0 <= weight <= 1000):
            raise CoverageError("Invalid reported body weight")
        if change is not None and (type(change) is not int or not -100 <= change <= 100):
            raise CoverageError("Invalid reported body-weight change")
        for field in ("this_horse_body_state", "paddock_index"):
            value = record.get(field)
            if value is not None and (not isinstance(value, (str, int, float))
                                      or len(str(value)) > 100):
                raise CoverageError("Invalid private observation shape")
        flag = record.get("withdrawn_flag")
        if flag not in (None, "", "0", "1"):
            raise CoverageError("Invalid provider withdrawal flag")
        c = counters[key]
        if weight is not None and weight > 0:
            c["bodyWeight"] += 1
        if change is not None and weight is not None and weight > 0:
            c["weightChange"] += 1
        if _present(str(record.get("paddock_index") or "")):
            c["paddock"] += 1
        if _present(record.get("this_horse_body_state")):
            c["reportedBodyState"] += 1
        if flag == "1":
            c["reportedWithdrawn"] += 1
    by_coord = {(p["track"], p["race"]): p["racekey"] for p in programme}
    if len(by_coord) != len(programme):
        raise CoverageError("Duplicate programme coordinate")
    output = []
    for row in base["races"]:
        key = by_coord[row["track"], row["race"]]
        c = counters[key]
        n = row["observedEntries"]
        reported = sum(ident[0] == key for ident in observed)
        if reported > n:
            raise CoverageError("Prestart count exceeds roster")
        output.append({
            "track": row["track"], "race": row["race"],
            "registered": n, "prestartRowsMatched": reported,
            "prestartRowsMissing": n - reported,
            "bodyWeightRecords": c["bodyWeight"],
            "weightChangeRecords": c["weightChange"],
            "paddockRecords": c["paddock"],
            "bodyStateCodeRecords": c["reportedBodyState"],
            "providerWithdrawnReports": c["reportedWithdrawn"],
            "sourceDataUpdatedAtVerified": False,
            "officialBodyWeightVerified": False,
            "bodyConditionGraded": False,
            "realPredictionReady": False, "ticketReady": False,
        })
    output.sort(key=lambda row: (row["track"], row["race"]))
    return {
        "version": VERSION, "date": racedate, "raceCount": len(output),
        "races": output,
        "summary": {
            "matchedRows": len(observed),
            "weightRecords": sum(row["bodyWeightRecords"] for row in output),
            "paddockRecords": sum(row["paddockRecords"] for row in output),
            "missingRows": sum(row["prestartRowsMissing"] for row in output),
        },
        "sourceRequestsRequired": ["tra", "tky", "tpd"],
        "rawHorseRecordsIncluded": False, "oddsUsed": False,
        "officialBodyWeightVerified": False, "bodyConditionGraded": False,
        "realPredictionReady": False, "purchaseReady": False,
        "note": (
            "当日JRDB直前情報の資料件数のみ。馬体重・前走増減・パドック指数・"
            "馬体コードの有無を登録馬と照合。オッズや指数値は予想に使用しない。"
            "0kgやnullは測定値として数えない。提供元の情報はJRA公式の馬体重確定を意味しない。"
            "S/A/B/C・3連単・投票・実購入記録は作成しません。"
        ),
    }
