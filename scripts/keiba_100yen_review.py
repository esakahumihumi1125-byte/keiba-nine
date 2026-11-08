"""Read-only 100-yen hypothetical P/L for frozen, pre-race ticket snapshots.

No source retrieval, auto purchase, edits, data persistence or JRA validation.
Only a separate trusted official-results connector may populate the verification
flag. Missing/unverified results are PENDING, never recorded as a loss.
"""
from datetime import datetime, date

VERSION = "keiba-100yen-review-1"
STAKE = 100
VENUES = {"札幌", "函館", "福島", "新潟", "東京",
          "中山", "中京", "京都", "阪神", "小倉"}


class ReviewInputError(ValueError):
    pass


def _time(s):
    if not isinstance(s, str) or not 16 <= len(s) <= 35:
        raise ReviewInputError("Expected timestamp with timezone")
    try:
        v = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        raise ReviewInputError("Invalid timestamp") from None
    if v.tzinfo is None or v.utcoffset() is None:
        raise ReviewInputError("Prediction timestamps must include timezone")
    return v


def _date(text):
    if not isinstance(text, str) or len(text) != 10:
        raise ReviewInputError("Expected ISO race date")
    try:
        d = date.fromisoformat(text)
    except ValueError:
        raise ReviewInputError("Invalid race date") from None
    if d.isoformat() != text:
        raise ReviewInputError("Invalid race date")
    return text


def _identity(row):
    if not isinstance(row, dict):
        raise ReviewInputError("Invalid race record")
    day, track, race = row.get("date"), row.get("track"), row.get("race")
    _date(day)
    if track not in VENUES or type(race) is not int or not 1 <= race <= 12:
        raise ReviewInputError("Invalid track or race")
    return (day, track, race)


def _tickets(raw, mode):
    if raw is None:
        return ()
    if not isinstance(raw, list) or len(raw) > 48:
        raise ReviewInputError("Too many tickets")
    unique = set()
    for entry in raw:
        if (not isinstance(entry, list) or len(entry) != 3
                or any(type(n) is not int or not 1 <= n <= 18 for n in entry)
                or len(set(entry)) != 3):
            raise ReviewInputError("Malformed " + mode + " ticket")
        ticket = tuple(entry)
        if mode == "trio":
            ticket = tuple(sorted(ticket))
        unique.add(ticket)
    return tuple(sorted(unique))


def _official(record):
    if record is None or record.get("officialVerified") is not True:
        return None
    final = record.get("finish")
    if (not isinstance(final, list) or len(final) != 3
            or any(type(n) is not int or not 1 <= n <= 18 for n in final)
            or len(set(final)) != 3):
        raise ReviewInputError("Official finishing order missing")
    trifecta, trio = record.get("trifectaPer100Yen"), record.get("trioPer100Yen")
    if (type(trifecta) is not int or not 0 <= trifecta <= 10**9
            or type(trio) is not int or not 0 <= trio <= 10**9):
        raise ReviewInputError("Official payouts are incomplete")
    return tuple(final), trifecta, trio


def review_100yen(predictions, results):
    """Reconcile only strictly pre-race locked prediction snapshots.

    Anything unconfirmed is excluded from ROI denominator and returned as
    pending. Return values are purely hypothetical, not proof of purchasing.
    """
    if (not isinstance(predictions, list) or len(predictions) > 36
            or not isinstance(results, list) or len(results) > 36):
        raise ReviewInputError("Invalid number of race records")
    by_result = {}
    for row in results:
        key = _identity(row)
        if key in by_result:
            raise ReviewInputError("Duplicate official result")
        by_result[key] = row
    seen = set()
    rows = []
    for p in predictions:
        key = _identity(p)
        if key in seen:
            raise ReviewInputError("Duplicate frozen race snapshot")
        seen.add(key)
        if p.get("sourceKind") != "prestart-locked" or p.get("actualPurchase") is not False:
            raise ReviewInputError("Not a frozen hypothetical prediction")
        locked = _time(p.get("lockedAt"))
        off = _time(p.get("scheduledOffAt"))
        if locked >= off:
            raise ReviewInputError("Post-race or unverified prediction lock")
        triple = _tickets(p.get("trifectaTickets"), "trifecta")
        trio = _tickets(p.get("trioTickets"), "trio")
        if not triple and not trio:
            continue
        official = _official(by_result.get(key))
        if official is None:
            rows.append({
                "date": key[0], "track": key[1], "race": key[2],
                "status": "pending", "trifectaPoints": len(triple),
                "trioPoints": len(trio), "investedYen": None,
                "returnedYen": None, "hitTrifecta": None,
                "hitTrio": None, "firstCandidateHit": None,
            })
            continue
        finish, trifecta_payout, trio_payout = official
        three_hit = finish in triple
        trio_hit = tuple(sorted(finish)) in trio
        amount = (len(triple) + len(trio)) * STAKE
        returned = (trifecta_payout if three_hit else 0) + (
            trio_payout if trio_hit else 0)
        rows.append({
            "date": key[0], "track": key[1], "race": key[2],
            "status": "verified_result",
            "trifectaPoints": len(triple),
            "trioPoints": len(trio),
            "investedYen": amount,
            "returnedYen": returned,
            "hitTrifecta": three_hit,
            "hitTrio": trio_hit,
            "firstCandidateHit": finish[0] in {t[0] for t in triple}
                                  if triple else None,
        })
    done = [x for x in rows if x["status"] == "verified_result"]
    invested = sum(x["investedYen"] for x in done)
    paid = sum(x["returnedYen"] for x in done)
    # Keep unresolved stakes visible, but OUTSIDE the verified ROI denominator.
    pending_stake = sum(
        (x["trifectaPoints"] + x["trioPoints"]) * STAKE
        for x in rows if x["status"] == "pending")
    # Track-level breakdown makes the same frozen review useful for a full
    # racing day. Preserve the order in which the owner supplied race records.
    by_venue = []
    for track in dict.fromkeys(x["track"] for x in rows):
        races = [x for x in rows if x["track"] == track]
        verified = [x for x in races if x["status"] == "verified_result"]
        stake = sum(x["investedYen"] for x in verified)
        returned = sum(x["returnedYen"] for x in verified)
        candidates = [x for x in verified if x["firstCandidateHit"] is not None]
        by_venue.append({
            "track": track,
            "reviewedRaces": len(verified),
            "pendingRaces": len(races) - len(verified),
            "investedYen": stake,
            "returnedYen": returned,
            "profitYen": returned - stake,
            "roiPercent": round(returned / stake * 100, 1) if stake else None,
            "pendingStakeYen": sum(
                (x["trifectaPoints"] + x["trioPoints"]) * STAKE
                for x in races if x["status"] == "pending"),
            "trifectaHits": sum(x["hitTrifecta"] is True for x in verified),
            "trioHits": sum(x["hitTrio"] is True for x in verified),
            "firstCandidateHits": sum(
                x["firstCandidateHit"] is True for x in candidates),
            "firstCandidateEligibleRaces": len(candidates),
        })
    candidates = [x for x in done if x["firstCandidateHit"] is not None]
    return {
        "version": VERSION, "unitYen": STAKE,
        "races": rows, "reviewedRaces": len(done),
        "pendingRaces": len(rows) - len(done),
        "totalInvestedYen": invested, "totalReturnedYen": paid,
        "totalProfitYen": paid - invested,
        "roiPercent": round(paid / invested * 100, 1) if invested else None,
        "pendingStakeYen": pending_stake,
        "venueBreakdown": by_venue,
        "firstCandidateHits": sum(x["firstCandidateHit"] is True for x in candidates),
        "firstCandidateEligibleRaces": len(candidates),
        "trifectaHits": sum(x["hitTrifecta"] is True for x in done),
        "trioHits": sum(x["hitTrio"] is True for x in done),
        "actualPurchase": False,
        "note": ("レース前に固定された買い目を1点100円で仮購入した場合の集計。"
                 "JRA公式結果が未確認のレースは保留して収支に入れない。"
                 "実際の購入・払戻・課税記録とは別。"),
    }
