"""Private, per-race signed FIRST postrace provisional pair observations.

A completed JRDB comparison is not JRA verification, not a calibrated
numeric training score, and not a purchase. This module signs ONLY
redacted per-race aggregate counts tied to an earlier authenticated
prestart HMAC. No raw licensed /tcy or /tse row, horse number, name or
racekey is retained. The browser stores its first signed observation
per race, never overwrites history, and may verify signatures later
without an additional provider request.
"""
import hashlib
import hmac
import json
import re
from datetime import datetime, timezone

from owner_workout_order_receipts import (
    WorkoutLockError, _validate as validate_prestart, _clock, _day,
    _sign as sign_prestart, BANDS, TRACKS,
)
from owner_workout_order_provider_pairs import VERSION as PAIR_VERSION

VERSION = "owner-workout-pair-observation-receipt-1"
DOMAIN = b"keiba-nine/owner-workout-postrace-pairs/v1"
COUNTS = ("concordant", "discordant", "equalIndexExcluded")
MAX_RACES = 36
MAX_DAYS = 360
FIELDS = frozenset((
    "version", "date", "track", "race", "sourceKind",
    "observedAt", "scheduledOffAt", "prestartSignature", "runnerCount",
    "pairCounts", "researchOnly", "officialJraVerified",
    "resultSourceComplete", "sourcePublicationVerified",
    "modelCalibrated", "predictionReady", "actualPurchase",
))


def _key(secret):
    if not isinstance(secret, str) or len(secret) < 16:
        raise WorkoutLockError("Signing secret unavailable")
    return hmac.new(secret.encode(), DOMAIN, hashlib.sha256).digest()


def _sign(snapshot, secret):
    data = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                      allow_nan=False, separators=(",", ":")).encode()
    return hmac.new(_key(secret), data, hashlib.sha256).hexdigest()


def _bounds(counts, horses):
    """Validate all pair denominators and exact equal-index ties."""
    if not isinstance(counts, dict) or set(counts) != set(BANDS):
        raise WorkoutLockError("Wrong workout observation bands")
    normalized = {}
    for band in BANDS:
        row = counts[band]
        if not isinstance(row, dict) or set(row) != set(COUNTS):
            raise WorkoutLockError("Wrong workout pair columns")
        if any(type(row[k]) is not int or not 0 <= row[k] <= 153 for k in COUNTS):
            raise WorkoutLockError("Invalid observed pair count")
        peers = [h for h in horses if h["trainingBand"] == band]
        all_pairs = len(peers) * (len(peers)-1) // 2
        equal_pairs = sum(
            peers[i]["withinBandRank"] == peers[j]["withinBandRank"]
            for i in range(len(peers)) for j in range(i+1,len(peers)))
        if (sum(row.values()) != all_pairs
                or row["equalIndexExcluded"] != equal_pairs):
            raise WorkoutLockError("Pair totals disagree with frozen ranking")
        normalized[band] = dict(row)
    return normalized


def _validate(snapshot, prestart):
    validate_prestart(prestart)
    if (not isinstance(snapshot, dict) or set(snapshot) != FIELDS
            or snapshot.get("version") != VERSION
            or snapshot.get("sourceKind") != "jrdb-tse-provisional-workout-pairs"
            or snapshot.get("researchOnly") is not True
            or snapshot.get("officialJraVerified") is not False
            or snapshot.get("resultSourceComplete") is not True
            or snapshot.get("sourcePublicationVerified") is not False
            or snapshot.get("modelCalibrated") is not False
            or snapshot.get("predictionReady") is not False
            or snapshot.get("actualPurchase") is not False):
        raise WorkoutLockError("Postrace snapshot mode mismatch")
    if (snapshot["date"] != prestart["date"]
            or snapshot["track"] != prestart["track"]
            or snapshot["race"] != prestart["race"]
            or snapshot["scheduledOffAt"] != prestart["scheduledOffAt"]
            or type(snapshot["runnerCount"]) is not int
            or snapshot["runnerCount"] != prestart["raceRunnerCount"]
            or not isinstance(snapshot["prestartSignature"], str)
            or not re.fullmatch(r"[a-f0-9]{64}", snapshot["prestartSignature"])):
        raise WorkoutLockError("Postrace observation not joined to frozen race")
    try:
        at = _clock(datetime.fromisoformat(snapshot["observedAt"].replace("Z","+00:00")))
        off = _clock(datetime.fromisoformat(snapshot["scheduledOffAt"].replace("Z","+00:00")))
    except (ValueError, TypeError, AttributeError):
        raise WorkoutLockError("Invalid observation clock") from None
    if at < off:
        raise WorkoutLockError("Result captured before race off")
    _bounds(snapshot["pairCounts"], prestart["horses"])
    return snapshot["date"], snapshot["track"], snapshot["race"]


def issue_workout_pair_observations(review, prestart, secret, *, now):
    """Sign ONLY complete rows from already checked provider comparison.

    This consumes zero provider calls and performs no persistence. The
    prestart argument must be the HMAC-verified snapshots from the private
    owner result route, never a browser-provided unverified payload.
    """
    now = _clock(now)
    if (not isinstance(prestart, list) or not 1 <= len(prestart) <= MAX_RACES
            or not isinstance(review, dict)
            or review.get("version") != PAIR_VERSION
            or review.get("sourceKind") != "jrdb-tse-provisional-workout-order-pair-review"
            or review.get("sourceReadCount") not in (0,1)
            or review.get("researchOnly") is not True
            or review.get("privateOwnerOnly") is not True
            or review.get("officialJraVerified") is not False
            or review.get("accuracyVerified") is not False
            or review.get("calibrationReady") is not False
            or review.get("newScoringRubric") is not False
            or review.get("actualPurchase") is not False
            or not isinstance(review.get("races"), list)
            or len(review["races"]) != len(prestart)
            or review.get("raceCount") != len(prestart)):
        raise WorkoutLockError("Untrusted workout result review")
    day = _day(review["date"])
    entries = {}
    for snap in prestart:
        identity = validate_prestart(snap)
        if identity[0] != day or identity[1:] in entries:
            raise WorkoutLockError("Duplicate or mismatched signed research")
        entries[identity[1:]] = snap
    seen, result = set(), []
    totals = {b: {k: 0 for k in COUNTS} for b in BANDS}
    completed = 0
    for row in review["races"]:
        coord = row.get("track"), row.get("race")
        snap = entries.get(coord)
        if (coord in seen or snap is None
                or row.get("officialJraVerified") is not False
                or row.get("predictionVerified") is not False
                or row.get("providerStatus") not in (
                    "pending", "complete_provisional_order")):
            raise WorkoutLockError("Result race mismatch")
        seen.add(coord)
        if row["providerStatus"] == "pending":
            if row.get("comparedRunnerCount") != 0 or row.get("pairCounts") is not None:
                raise WorkoutLockError("Pending result carries observed pairs")
            continue
        completed += 1
        if (review["sourceReadCount"] != 1
                or row.get("comparedRunnerCount") != snap["raceRunnerCount"]):
            raise WorkoutLockError("Complete result without one provider read")
        counts = _bounds(row.get("pairCounts"), snap["horses"])
        for band in BANDS:
            for key in COUNTS:
                totals[band][key] += counts[band][key]
        record = {
            "version": VERSION, "date": day,
            "track": coord[0], "race": coord[1],
            "sourceKind": "jrdb-tse-provisional-workout-pairs",
            "observedAt": now.isoformat(timespec="seconds"),
            "scheduledOffAt": snap["scheduledOffAt"],
            "prestartSignature": sign_prestart(snap, secret),
            "runnerCount": snap["raceRunnerCount"],
            "pairCounts": counts,
            "researchOnly": True, "officialJraVerified": False,
            "resultSourceComplete": True,
            "sourcePublicationVerified": False,
            "modelCalibrated": False, "predictionReady": False,
            "actualPurchase": False,
        }
        _validate(record, snap)
        result.append({"snapshot": record, "signature": _sign(record, secret)})
    if (seen != set(entries) or completed != review.get("studiedRaceCount")
            or totals != review.get("observedPairsByTrainingBand")):
        raise WorkoutLockError("Provider pair aggregates do not match their races")
    return result


def verify_workout_pair_observations(receipts, prestart, secret, day):
    """Read-only verification of prior observations, no JRDB data fetch."""
    _day(day)
    if (not isinstance(receipts, list) or not 1 <= len(receipts) <= MAX_DAYS
            or not isinstance(prestart, list)
            or not 1 <= len(prestart) <= MAX_DAYS):
        raise WorkoutLockError("Invalid saved observation collection")
    originals = {}
    for snap in prestart:
        identity = validate_prestart(snap)
        if identity[0] != day or identity[1:] in originals:
            raise WorkoutLockError("Invalid saved prestart roster")
        originals[identity[1:]] = snap
    used, output = set(), []
    for row in receipts:
        if not isinstance(row, dict) or set(row) != {"snapshot","signature"}:
            raise WorkoutLockError("Invalid saved comparison receipt")
        snap, signature = row["snapshot"], row["signature"]
        if not isinstance(snap, dict):
            raise WorkoutLockError("Invalid stored observation shape")
        coord = snap.get("track"), snap.get("race")
        original = originals.get(coord)
        if (coord in used or original is None
                or _validate(snap, original)[0] != day
                or snap["prestartSignature"] != sign_prestart(original,secret)
                or not isinstance(signature,str)
                or not re.fullmatch(r"[a-f0-9]{64}",signature)
                or not hmac.compare_digest(signature,_sign(snap,secret))):
            raise WorkoutLockError("Invalid saved pair observation signature")
        used.add(coord)
        output.append(snap)
    return output
