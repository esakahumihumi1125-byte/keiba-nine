"""Owner-only PRELIMINARY JRDB placing comparison for server-signed trifecta tickets.

Only the authenticated server-verified prestart receipt is trusted as the
original selection. A JRDB /tse placing is NOT a JRA official result, purchase,
settled ticket or payout; a partial/ambiguous placing stays PENDING.
The client cannot supply a placing, win flag, odds, or payout. This module is
pure: no API calls, persistence, result manipulation or future predictions.
"""
import re
from datetime import datetime, timezone

from keiba_100yen_review import _identity, _time, _tickets, ReviewInputError
from jrdb_program_preview import TRACKS

VERSION = "owner-prestart-tse-comparison-1"
MAX_ROWS = 2160
MISSING = "pending"
OBSERVED = "provider_podium_observed"


class ProvisionalResultError(ValueError):
    pass


def compare_prestart_tickets(predictions, rows, day, *, now=None,
                             source_read_count=1):
    """Return redacted coverage observations for signed prestart selections."""
    if (not isinstance(day, str)
            or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", day)):
        raise ProvisionalResultError("Invalid selected date")
    try:
        from datetime import date
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError()
    except ValueError:
        raise ProvisionalResultError("Invalid selected date") from None
    now = datetime.now(timezone.utc) if now is None else now
    if (not isinstance(now, datetime) or now.tzinfo is None or
            now.utcoffset() is None):
        raise ProvisionalResultError("Trusted clock missing")
    if (type(source_read_count) is not int or source_read_count not in (0, 1)
            or not isinstance(predictions, list)
            or not 1 <= len(predictions) <= 36
            or not isinstance(rows, list) or len(rows) > MAX_ROWS
            or (source_read_count == 0 and rows)):
        raise ProvisionalResultError("Invalid source count")

    before = {}
    ordered = []
    for entry in predictions:
        try:
            identity = _identity(entry)
            if (identity[0] != day or identity in before
                    or entry.get("sourceKind") != "prestart-locked"
                    or entry.get("actualPurchase") is not False):
                raise ProvisionalResultError("Untrusted prestart identity")
            signed_at = _time(entry["lockedAt"])
            scheduled = _time(entry["scheduledOffAt"])
            if signed_at >= scheduled:
                raise ProvisionalResultError("Prestart timeline invalid")
            triple = set(_tickets(entry["trifectaTickets"], "trifecta"))
            trio = _tickets(entry["trioTickets"], "trio")
            if not triple or trio:
                raise ProvisionalResultError("Unexpected signed ticket mode")
            before[identity] = (entry, triple, scheduled)
            ordered.append(identity)
        except (ReviewInputError, KeyError, TypeError) as exc:
            raise ProvisionalResultError("Invalid verified ticket") from exc

    compact = day.replace("-", "")
    # Never take result information supplied by the browser. Every row was
    # fetched server-side and must belong to the selected JRDB date.
    groups = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ProvisionalResultError("Invalid JRDB result row")
        key = row.get("racekey")
        number = row.get("horse_number")
        finish = row.get("order_of_finish")
        if (not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{8}", key)
                or key[:2] not in TRACKS
                or key[2:4] != compact[2:4]
                or not key[6:].isdigit() or not 1 <= int(key[6:]) <= 12
                or row.get("racedate") != compact
                or not isinstance(number, str)
                or not re.fullmatch(r"(?:0[1-9]|1[0-8])", number)
                or finish is not None and not isinstance(finish, str)):
            raise ProvisionalResultError("JRDB result key mismatch")
        coordinate = (TRACKS[key[:2]], int(key[6:]))
        target = groups.setdefault(coordinate, {
            "keys": set(), "numbers": set(), "podium": {},
            "invalid": False, "count": 0,
        })
        target["keys"].add(key)
        horse = int(number)
        target["count"] += 1
        if horse in target["numbers"] or target["count"] > 18:
            target["invalid"] = True
        target["numbers"].add(horse)
        if finish not in (None, ""):
            if (not re.fullmatch(r"0?[1-9]|1[0-8]", finish)
                    or row.get("trouble_classification") not in (None, "", "0")):
                target["invalid"] = True
            else:
                place = int(finish)
                if place in (1, 2, 3):
                    if place in target["podium"]:
                        target["invalid"] = True
                    target["podium"][place] = horse

    report = []
    for identity in ordered:
        entry, tickets, scheduled = before[identity]
        track, race = identity[1:]
        group = groups.get((track, race))
        good = (now >= scheduled and group is not None
                and not group["invalid"] and len(group["keys"]) == 1
                and 3 <= group["count"] <= 18
                and set(group["podium"]) == {1, 2, 3}
                and len(set(group["podium"].values())) == 3)
        if not good:
            report.append({
                "track": track, "race": race, "providerStatus": MISSING,
                "trifectaPoints": len(tickets),
                "firstCandidateObserved": None, "secondCandidateObserved": None,
                "thirdCandidateObserved": None,
                "exactCombinationObserved": None, "firstMissType": None,
                "officialVerified": False,
            })
            continue
        finish = tuple(group["podium"][i] for i in (1, 2, 3))
        first = {t[0] for t in tickets}
        second = {t[1] for t in tickets}
        third = {t[2] for t in tickets}
        seen_first = finish[0] in first
        reason = ("first_candidate" if seen_first else
                  "wrong_slot" if finish[0] in second or finish[0] in third
                  else "not_selected")
        report.append({
            "track": track, "race": race, "providerStatus": OBSERVED,
            "trifectaPoints": len(tickets),
            "firstCandidateObserved": seen_first,
            "secondCandidateObserved": finish[1] in second,
            "thirdCandidateObserved": finish[2] in third,
            "exactCombinationObserved": finish in tickets,
            "firstMissType": reason,
            "officialVerified": False,
        })
    observed = [x for x in report if x["providerStatus"] == OBSERVED]
    return {
        "version": VERSION, "date": day, "raceCount": len(report),
        "observedRaceCount": len(observed),
        "pendingRaceCount": len(report) - len(observed),
        "provisionalExactCombinationCount": sum(
            x["exactCombinationObserved"] is True for x in observed),
        "provisionalFirstCandidateCount": sum(
            x["firstCandidateObserved"] is True for x in observed),
        "providerReadCount": source_read_count, "races": report,
        "researchOnly": True, "privateOwnerOnly": True,
        "sourceKind": "jrdb-tse-provisional-podium",
        "officialJraVerified": False, "independentJraVerified": False,
        "payoutVerified": False, "roiPercent": None,
        "officialHitCount": None, "realPredictionReady": False,
        "actualPurchase": False, "bettingReady": False,
        "changesExistingReceipts": False,
        "note": ("JRDB /tseで3着までの暫定着順がそろう場合のみ、"
                 "固定済み3連単との参考比較を表示。"
                 "独立したJRA公式結果・返還・同着・確定払戻は未照合。"
                 "公式的中率、100円仮想収支、実購入収支には一切算入しない。"),
    }
