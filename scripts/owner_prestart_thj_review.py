"""Owner-private /thj payoff reference against immutable signed prestart bets.

This is a *JRDB provider-observed* 100-yen research comparison. It is not an
independently JRA-certified result, a real purchase, or an actual bank payout.
Only the calling private WSGI service may retrieve licensed /thj rows, and
only AFTER verifying every server HMAC. No source rows, racekeys, popularity,
secrets or paid inputs are returned to the browser. Refunds and uncertain
payoff encoding MUST remain pending instead of producing false ROI figures.
"""
from datetime import date, datetime, timedelta, timezone
import re

from jrdb_coverage import CoverageError

JST = timezone(timedelta(hours=9))
VERSION = "owner-prestart-thj-100yen-reference-1"
VENUES = {
    "01": "札幌", "02": "函館", "03": "福島", "04": "新潟",
    "05": "東京", "06": "中山", "07": "中京", "08": "京都",
    "09": "阪神", "10": "小倉",
}
RACEKEY = re.compile(r"(?:0[1-9]|10)[0-9]{2}[0-9a-f]{2}(?:0[1-9]|1[0-2])\Z", re.ASCII)
DAY = re.compile(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)
COMPACT = re.compile(r"[0-9]{6}\Z", re.ASCII)
DASHED = re.compile(r"[0-9]{1,2}-[0-9]{1,2}-[0-9]{1,2}\Z", re.ASCII)


def _triple(value):
    """Accept only explicit three-number encodings; no silent fuzzy parsing."""
    if type(value) is not str:
        return None
    if COMPACT.fullmatch(value):
        numbers = [int(value[i:i + 2]) for i in (0, 2, 4)]
    elif DASHED.fullmatch(value):
        numbers = [int(part) for part in value.split("-")]
    else:
        return None
    return tuple(numbers) if (all(1 <= n <= 18 for n in numbers)
                              and len(set(numbers)) == 3) else None


def _stamp(value):
    if type(value) is not str:
        raise CoverageError("Invalid saved time")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise CoverageError("Invalid saved time") from None
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise CoverageError("Missing saved timezone")
    return stamp.astimezone(JST)


def compare_verified_prestart_thj(receipts, raw_payoffs, selected_day, *, now,
                                  provider_read_count=1):
    """Compute *provisional research* returns only for verified signed tickets.

    Receipts MUST first be passed through verify_preview_receipts (HMAC),
    never a user-supplied unsigned ticket list. Future races are pending;
    a nonempty /thj row alone is not proof of final settlement.
    """
    if (type(selected_day) is not str or not DAY.fullmatch(selected_day)
            or date.fromisoformat(selected_day).isoformat() != selected_day
            or not isinstance(now, datetime) or now.tzinfo is None
            or now.utcoffset() is None
            or type(provider_read_count) is not int
            or provider_read_count not in (0, 1)
            or not isinstance(receipts, list) or not 1 <= len(receipts) <= 36
            or not isinstance(raw_payoffs, list)
            or len(raw_payoffs) > 120
            or (provider_read_count == 0 and raw_payoffs)):
        raise CoverageError("Invalid payoff research request")
    current = now.astimezone(JST)
    compact_day = selected_day.replace("-", "")
    indices = {}
    for source in raw_payoffs:
        if not isinstance(source, dict):
            raise CoverageError("Bad payoff data")
        key = source.get("racekey")
        if (type(key) is not str or not RACEKEY.fullmatch(key)
                or source.get("racedate") != compact_day
                or key[2:4] != compact_day[2:4]):
            raise CoverageError("Payoff day or race identity mismatch")
        coord = (VENUES[key[:2]], int(key[-2:]))
        if coord in indices:
            raise CoverageError("Duplicate payoff race")
        indices[coord] = source

    seen, rows = set(), []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise CoverageError("Bad verified prestart snapshot")
        track, race = receipt.get("track"), receipt.get("race")
        coord = (track, race)
        if (track not in VENUES.values() or type(race) is not int
                or not 1 <= race <= 12 or coord in seen
                or receipt.get("date") != selected_day
                or receipt.get("sourceKind") != "prestart-locked"
                or receipt.get("actualPurchase") is not False
                or not isinstance(receipt.get("trifectaTickets"), list)
                or not 1 <= len(receipt["trifectaTickets"]) <= 48
                or receipt.get("trioTickets") != []):
            raise CoverageError("Invalid verified prestart race")
        seen.add(coord)
        locked = _stamp(receipt.get("lockedAt"))
        off = _stamp(receipt.get("scheduledOffAt"))
        if locked >= off or off.date() != date.fromisoformat(selected_day):
            raise CoverageError("Invalid prestart time order")
        tickets = set()
        for item in receipt["trifectaTickets"]:
            if (not isinstance(item, list) or len(item) != 3
                    or any(type(n) is not int or not 1 <= n <= 18 for n in item)
                    or len(set(item)) != 3
                    or tuple(item) in tickets):
                raise CoverageError("Invalid fixed triple")
            tickets.add(tuple(item))
        invested = 100 * len(tickets)
        state, returned, winning = "pending", None, 0
        provider = indices.get(coord) if current >= off else None
        if provider is not None:
            refunds = [provider.get("refund_number_" + str(i)) for i in range(1, 6)]
            if any(value not in (None, "", 0, "0") for value in refunds):
                state = "refund_review"
            else:
                hits = {}
                valid = True
                for i in range(1, 7):
                    raw = provider.get("trifecta_number_" + str(i))
                    payout = provider.get("trifecta_payoff_" + str(i))
                    if raw in (None, ""):
                        if payout not in (None, 0):
                            valid = False
                        continue
                    triple = _triple(raw)
                    if (triple is None or triple in hits or
                            type(payout) is not int or not 1 <= payout <= 100000000):
                        valid = False
                        break
                    hits[triple] = payout
                if not valid:
                    state = "format_review"
                elif hits:
                    state = "provider_observed"
                    returned = sum(hits.get(ticket, 0) for ticket in tickets)
                    winning = sum(ticket in hits for ticket in tickets)
        rows.append({
            "track": track, "race": race, "status": state,
            "trifectaPoints": len(tickets),
            "investedYen": invested if state == "provider_observed" else None,
            "returnedYen": returned, "providerMatchedTickets": winning
            if state == "provider_observed" else None,
            "officialJraVerified": False,
        })
    eligible = [r for r in rows if r["status"] == "provider_observed"]
    investment = sum(r["investedYen"] for r in eligible)
    payout = sum(r["returnedYen"] for r in eligible)
    pending_stake = sum(r["trifectaPoints"] * 100 for r in rows if r not in eligible)
    return {
        "version": VERSION, "date": selected_day, "unitYen": 100,
        "source": "jrdb_thj_provider_reference", "providerReadCount": provider_read_count,
        "raceCount": len(rows), "observedRaces": len(eligible),
        "pendingRaces": len(rows) - len(eligible), "pendingStakeYen": pending_stake,
        "reviewedInvestedYen": investment, "reviewedReturnedYen": payout,
        "reviewedProfitYen": payout - investment,
        "reviewedRoiPercent": round(payout * 100 / investment, 2) if investment else None,
        "providerMatchedRaces": sum(r["providerMatchedTickets"] > 0 for r in eligible),
        "races": rows,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "payoutOfficiallyVerified": False,
        "actualPurchase": False, "predictionReady": False,
        "changesExistingReceipts": False, "writesPersistentResults": False,
        "note": "JRDB払戻データとの100円仮想比較。JRA公式の独立照合・実購入は未確認。返還・欠損・不明形式は集計から除外。",
    }
