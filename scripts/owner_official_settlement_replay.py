"""Owner-only settlement replay of immutable prestart receipts.

A future *independent, server-only JRA source adapter* must authenticate the
original JRA page before it may sign an official settlement envelope. This
module validates the independent HMAC and settles multiple exact winning
combinations (including dead heats), refunds and cancelled races.

No public route accepts result rows. This module never fetches JRA, makes a
purchase, changes prestart snapshots, or provisions a persistent database.
An HMAC proves only which trusted signer signed the normalized payload,
not by itself that the signer read an authentic JRA page.
"""
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qs

from keiba_100yen_review import _identity, _time, _tickets, ReviewInputError
from owner_prestart_receipt import (
    _selected_day, verify_preview_receipts, ReceiptError
)

VERSION = "owner-official-settlement-replay-1"
SCHEMA = "owner-jra-result-attestation-v1"
STAKE = 100
MAX_RACES = 36
OFFICIAL_HOSTS = {"www.jra.go.jp", "jra.jp", "app.jra.jp"}
MAX_PAYOUT = 1_000_000_000


class SettlementReplayError(ValueError):
    """Never contain data from a provider, a receipt or signing key."""


def _canonical(obj):
    try:
        return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError):
        raise SettlementReplayError("Settlement is not JSON serializable") from None


def _key(secret):
    if (not isinstance(secret, str) or not 48 <= len(secret) <= 512
            or len(set(secret)) < 16):
        raise SettlementReplayError("Independent result signer unavailable")
    return hmac.new(secret.encode("utf-8"),
                    b"keiba-nine/independent-jra-results/v1",
                    hashlib.sha256).digest()


def _signature(payload, secret):
    return hmac.new(_key(secret), _canonical(payload), hashlib.sha256).hexdigest()


def sign_authenticated_source_record(payload, secret):
    """Internal helper for a future trusted JRA ingestion adapter.

    It MUST first check origin, page identity, final official payouts and
    source freshness independently. Never expose as a web endpoint or call
    with user-supplied or JRDB-provisional results.
    """
    _validate_payload(payload)
    return {"payload": payload, "signature": _signature(payload, secret)}


def _source_url(url, compact_day):
    if (not isinstance(url, str) or len(url) > 500
            or any(ord(c) < 32 for c in url)):
        raise SettlementReplayError("Official source URL missing")
    try:
        s = urlsplit(url)
        if (s.scheme != "https" or s.hostname not in OFFICIAL_HOSTS
                or s.username is not None or s.password is not None
                or s.port not in (None, 443)
                or s.path != "/JRADB/accessS.html" or s.fragment):
            raise ValueError()
        qs = parse_qs(s.query, keep_blank_values=True)
        cname = qs.get("CNAME")
        if set(qs) != {"CNAME"} or not cname or len(cname) != 1:
            raise ValueError()
        if (not cname[0].startswith(("pw01sde", "sw01sde"))
                or compact_day not in cname[0]
                or len(cname[0]) > 100):
            raise ValueError()
    except ValueError:
        raise SettlementReplayError("Unrecognized official results URL") from None


def _unique_tickets(value, mode, *, with_yen):
    if not isinstance(value, list) or len(value) > 48:
        raise SettlementReplayError("Invalid settlement combinations")
    out = {}
    for item in value:
        if (not isinstance(item, dict)
                or set(item) != ({"ticket", "payoutYen"} if with_yen
                                    else {"ticket"})):
            raise SettlementReplayError("Invalid settlement entry")
        try:
            normalized = _tickets([item["ticket"]], mode)
        except (ReviewInputError, KeyError, TypeError):
            raise SettlementReplayError("Invalid settlement ticket") from None
        if len(normalized) != 1 or normalized[0] in out:
            raise SettlementReplayError("Duplicate settlement ticket")
        yen = item.get("payoutYen")
        if with_yen and (type(yen) is not int or not 100 <= yen <= MAX_PAYOUT):
            raise SettlementReplayError("Unrecognized payout amount")
        out[normalized[0]] = yen if with_yen else STAKE
    return out


def _validate_payload(p):
    if not isinstance(p, dict) or set(p) != {
        "schema", "date", "track", "race", "sourceUrl",
        "sourceCollectedAt", "finalizedAt", "status",
        "trifectaPayouts", "trioPayouts",
        "trifectaRefunds", "trioRefunds",
        "sourceVerificationMethod"}:
        raise SettlementReplayError("Unknown result payload schema")
    if p["schema"] != SCHEMA:
        raise SettlementReplayError("Result schema mismatch")
    try:
        day, _, _ = _identity(p)
        collected = _time(p["sourceCollectedAt"])
        finalized = _time(p["finalizedAt"])
        if (collected < finalized
                or finalized.astimezone(timezone.utc).date() <
                    datetime.fromisoformat(day).date()
                or p["sourceVerificationMethod"] !=
                    "server_authenticated_jra_page"
                or p["status"] not in ("settled", "cancelled")):
            raise ValueError()
    except (ReviewInputError, ValueError, KeyError, TypeError):
        raise SettlementReplayError("Unconfirmed official result timeline") from None
    _source_url(p["sourceUrl"], day.replace("-", ""))
    trip = _unique_tickets(p["trifectaPayouts"], "trifecta", with_yen=True)
    trio = _unique_tickets(p["trioPayouts"], "trio", with_yen=True)
    refund_trip = _unique_tickets(p["trifectaRefunds"], "trifecta", with_yen=False)
    refund_trio = _unique_tickets(p["trioRefunds"], "trio", with_yen=False)
    if (set(trip) & set(refund_trip) or set(trio) & set(refund_trio)
            or (p["status"] == "cancelled" and (trip or trio))
            or (p["status"] == "settled" and not trip and not trio
                and not refund_trip and not refund_trio)):
        raise SettlementReplayError("Inconsistent official settlement data")
    return collected, finalized, trip, trio, refund_trip, refund_trio


def replay_attested_settlements(receipts, receipt_secret, day,
                                 attestations, result_secret, *, now=None):
    """Reconcile HMAC-locked selections only with independently signed inputs.

    Use no outcomes for any race without a validated attestation. This is
    deliberately separate from the default, still-unconnected JRA results
    feed and cannot be invoked with browser-supplied results.
    """
    _selected_day(day)
    now = datetime.now(timezone.utc) if now is None else now
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise SettlementReplayError("Trusted server clock unavailable")
    if (not isinstance(receipts, list) or not 0 <= len(receipts) <= MAX_RACES
            or not isinstance(attestations, list)
            or len(attestations) > MAX_RACES):
        raise SettlementReplayError("Invalid settlement batch")
    try:
        predictions = verify_preview_receipts(receipts, receipt_secret, day)
    except (ReceiptError, ReviewInputError, TypeError, ValueError):
        raise SettlementReplayError("Prestart receipts are invalid") from None
    signed = {}
    for attestation in attestations:
        if (not isinstance(attestation, dict)
                or set(attestation) != {"payload", "signature"}
                or not isinstance(attestation["signature"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", attestation["signature"])):
            raise SettlementReplayError("Unsigned result record")
        payload = attestation["payload"]
        if not hmac.compare_digest(attestation["signature"],
                                   _signature(payload, result_secret)):
            raise SettlementReplayError("Result signature mismatch")
        collected, finalized, trip, trio, refunds_trip, refunds_trio = (
            _validate_payload(payload))
        race = _identity(payload)
        if race[0] != day or race in signed or collected > now or finalized > now:
            raise SettlementReplayError("Result day, replay time or identity mismatch")
        signed[race] = (payload, collected, finalized,
                        trip, trio, refunds_trip, refunds_trio)

    out, done, pending, gross, received, refunded = [], 0, 0, 0, 0, 0
    first_hits, trifecta_hits, trio_hits = 0, 0, 0
    for p in predictions:
        race = _identity(p)
        try:
            three = _tickets(p["trifectaTickets"], "trifecta")
            trio = _tickets(p["trioTickets"], "trio")
            off, locked = _time(p["scheduledOffAt"]), _time(p["lockedAt"])
        except (ReviewInputError, TypeError, KeyError):
            raise SettlementReplayError("Frozen ticket list invalid") from None
        stake = STAKE * (len(three) + len(trio))
        verified = signed.get(race)
        if verified is None:
            pending += 1
            out.append({"track": race[1], "race": race[2],
                        "status": "pending", "ticketCount": len(three)+len(trio),
                        "grossStakeYen": None, "returnedYen": None,
                        "trifectaHit": None, "trioHit": None,
                        "refundedTicketCount": None})
            continue
        payload, collected, finalized, tr_payout, tri_payout, tr_ref, tri_ref = verified
        if finalized <= off or collected <= off or locked >= off:
            raise SettlementReplayError("Result chronology conflicts with locked forecast")
        if payload["status"] == "cancelled":
            tr_ref = dict.fromkeys(three, STAKE)
            tri_ref = dict.fromkeys(trio, STAKE)
        three_hits = [t for t in three if t in tr_payout]
        trio_hits = [t for t in trio if t in tri_payout]
        refunds = sum(t in tr_ref for t in three) + sum(t in tri_ref for t in trio)
        returned = (sum(tr_payout[t] for t in three_hits)
                    + sum(tri_payout[t] for t in trio_hits)
                    + refunds * STAKE)
        done += 1
        gross += stake
        received += returned
        refunded += refunds
        trifecta_hits += bool(three_hits)
        first_hits += bool(three_hits)  # exact winning ticket implies correct first
        trio_hits += bool(trio_hits)
        out.append({
            "track": race[1], "race": race[2],
            "status": "attested_replay",
            "ticketCount": len(three) + len(trio),
            "grossStakeYen": stake, "returnedYen": returned,
            "trifectaHit": bool(three_hits), "trioHit": bool(trio_hits),
            "refundedTicketCount": refunds,
        })
    if set(signed) - {_identity(p) for p in predictions}:
        raise SettlementReplayError("Official result was not linked to frozen tickets")
    return {
        "version": VERSION, "date": day, "races": out,
        "raceCount": len(out), "attestedReplayRaces": done,
        "pendingRaces": pending, "unitYen": STAKE,
        "grossStakeYen": gross, "returnedYen": received,
        "netYen": received - gross,
        "refundedTicketCount": refunded,
        "trifectaHitRaces": trifecta_hits,
        "trioHitRaces": trio_hits,
        # Replay figures are isolated until the real JRA adapter is proven
        # at runtime. HMAC alone is NOT JRA authentication.
        "replayRoiPercent": round(100 * received / gross, 1) if gross else None,
        "officialRoiPercent": None, "officialJraVerified": False,
        "independentJraFeedConnected": False,
        "sourceRecordsIndependentlyValidatedHere": False,
        "sourceAttestationsAuthenticated": done > 0,
        "newPurchase": False, "actualPurchase": False,
        "changesExistingReceipts": False,
        "changesExistingTicketRecords": False,
        "changesExistingOfficialRoi": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": (
            "別系統で署名された公式結果形式データの研究用再計算。"
            "3着同着による複数3連単払戻や返還を個別に処理する。"
            "現環境ではJRA原本を取得・認証する接続が未完成。"
            "署名だけを理由に公式回収率には算入しません。"
        ),
    }
