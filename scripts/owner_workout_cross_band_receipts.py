"""Separate postrace HMAC evidence for *cross-band* workout rank pairs.

The prestart ranks must have been signed before the provisional race off.
This is not an extra JRDB fetch, official JRA outcome, a trained model,
or a purchase. No horse, index or licensed result row is in the record.
"""
import hashlib
import hmac
import json
from datetime import datetime
from owner_workout_order_receipts import (
    _clock, _validate as validate_prestart, _sign as sign_prestart,
    WorkoutLockError, BANDS,
)
from owner_workout_order_provider_pairs import VERSION as REVIEW_VERSION, CROSS_BAND_PAIRS

VERSION = "owner-workout-cross-band-observation-1"
DOMAIN = b"arc-race/owner-workout-cross-band-observation/v1"
MAX_RACES = 36
MAX_SAVED = 360
FIELDS = frozenset((
    "version", "date", "track", "race", "sourceKind", "observedAt",
    "scheduledOffAt", "prestartSignature", "runnerCount", "crossBandPairs",
    "researchOnly", "officialJraVerified", "resultSourceComplete",
    "sourcePublicationVerified", "modelCalibrated", "predictionReady",
    "actualPurchase",
))


def _digest(snapshot, secret):
    if not isinstance(secret, str) or len(secret) < 16:
        raise WorkoutLockError("Signing secret unavailable")
    payload = json.dumps(snapshot, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
    key = hmac.new(secret.encode(), DOMAIN, hashlib.sha256).digest()
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def _checked_counts(counts, horses):
    if not isinstance(counts, dict) or set(counts) != set(CROSS_BAND_PAIRS):
        raise WorkoutLockError("Cross-band grade labels mismatch")
    out = {}
    for key in CROSS_BAND_PAIRS:
        row = counts[key]
        if (not isinstance(row, dict)
                or set(row) != {"concordant", "discordant"}
                or any(type(row[k]) is not int or not 0 <= row[k] <= 324
                       for k in ("concordant", "discordant"))):
            raise WorkoutLockError("Invalid cross-band research counts")
        upper, lower = key.split(">")
        expected = (sum(h["trainingBand"] == upper for h in horses) *
                    sum(h["trainingBand"] == lower for h in horses))
        if row["concordant"] + row["discordant"] != expected:
            raise WorkoutLockError("Cross-band pair denominator mismatch")
        out[key] = dict(row)
    return out


def _validate(snapshot, prestart):
    before = validate_prestart(prestart)
    if (not isinstance(snapshot, dict) or set(snapshot) != FIELDS
            or snapshot["version"] != VERSION
            or snapshot["sourceKind"] != "jrdb-tse-cross-band-training-research"
            or snapshot["researchOnly"] is not True
            or snapshot["officialJraVerified"] is not False
            or snapshot["resultSourceComplete"] is not True
            or snapshot["sourcePublicationVerified"] is not False
            or snapshot["modelCalibrated"] is not False
            or snapshot["predictionReady"] is not False
            or snapshot["actualPurchase"] is not False
            or (snapshot["date"], snapshot["track"], snapshot["race"]) != before
            or snapshot["scheduledOffAt"] != prestart["scheduledOffAt"]
            or snapshot["runnerCount"] != prestart["raceRunnerCount"]
            or type(snapshot["prestartSignature"]) is not str
            or len(snapshot["prestartSignature"]) != 64):
        raise WorkoutLockError("Cross-band postrace identity mismatch")
    try:
        observed = _clock(datetime.fromisoformat(snapshot["observedAt"].replace("Z","+00:00")))
        off = _clock(datetime.fromisoformat(snapshot["scheduledOffAt"].replace("Z","+00:00")))
    except (ValueError, AttributeError, TypeError):
        raise WorkoutLockError("Invalid research clock") from None
    if observed < off:
        raise WorkoutLockError("Cross-band comparison is pre-off")
    _checked_counts(snapshot["crossBandPairs"], prestart["horses"])
    return before


def issue_cross_band_observations(review, original, secret, *, now):
    now = _clock(now)
    if (not isinstance(review, dict)
            or review.get("version") != REVIEW_VERSION
            or review.get("sourceReadCount") not in (0,1)
            or review.get("officialJraVerified") is not False
            or review.get("crossBandHypothesisOnly") is not True
            or review.get("crossBandResultsSigned") is not False
            or review.get("sourceReadsForCrossBand") != 0
            or review.get("calibrationReady") is not False
            or review.get("actualPurchase") is not False
            or review.get("researchOnly") is not True
            or not isinstance(review.get("races"), list)
            or not isinstance(original, list)
            or not 1 <= len(original) <= MAX_RACES
            or review.get("raceCount") != len(original)
            or len(review["races"]) != len(original)):
        raise WorkoutLockError("Cross-band review source invalid")
    day = review.get("date")
    known = {}
    for snap in original:
        identity = validate_prestart(snap)
        if identity[0] != day or identity[1:] in known:
            raise WorkoutLockError("Cross-band prestart identities invalid")
        known[identity[1:]] = snap
    seen, out, totals, completed = set(), [], {
        k: {"concordant":0,"discordant":0} for k in CROSS_BAND_PAIRS}, 0
    for row in review["races"]:
        coord = row.get("track"), row.get("race")
        snap = known.get(coord)
        if (coord in seen or snap is None
                or row.get("officialJraVerified") is not False
                or row.get("predictionVerified") is not False):
            raise WorkoutLockError("Cross-band result coordinate mismatch")
        seen.add(coord)
        if row.get("providerStatus") == "pending":
            if (row.get("comparedRunnerCount") != 0
                    or row.get("crossBandPairs") is not None
                    or row.get("pairCounts") is not None):
                raise WorkoutLockError("Pending result cannot carry pairs")
            continue
        if (row.get("providerStatus") != "complete_provisional_order"
                or review["sourceReadCount"] != 1
                or row.get("comparedRunnerCount") != snap["raceRunnerCount"]):
            raise WorkoutLockError("Cross-band result not complete")
        completed += 1
        counts = _checked_counts(row.get("crossBandPairs"), snap["horses"])
        for key in CROSS_BAND_PAIRS:
            for k in ("concordant","discordant"):
                totals[key][k] += counts[key][k]
        record = {
            "version":VERSION,"date":day,
            "track":coord[0],"race":coord[1],
            "sourceKind":"jrdb-tse-cross-band-training-research",
            "observedAt":now.isoformat(timespec="seconds"),
            "scheduledOffAt":snap["scheduledOffAt"],
            "prestartSignature":sign_prestart(snap,secret),
            "runnerCount":snap["raceRunnerCount"],"crossBandPairs":counts,
            "researchOnly":True,"officialJraVerified":False,
            "resultSourceComplete":True,"sourcePublicationVerified":False,
            "modelCalibrated":False,"predictionReady":False,
            "actualPurchase":False,
        }
        _validate(record,snap)
        out.append({"snapshot":record,"signature":_digest(record,secret)})
    if (seen != set(known) or completed != review.get("studiedRaceCount")
            or totals != review.get("observedCrossBandPairs")):
        raise WorkoutLockError("Cross-band study totals mismatch")
    return out


def verify_cross_band_observations(receipts, prestart, secret, day):
    if (not isinstance(receipts, list) or not 1 <= len(receipts) <= MAX_SAVED
            or not isinstance(prestart,list)
            or not 1 <= len(prestart) <= MAX_SAVED):
        raise WorkoutLockError("Invalid cross-band saved collection")
    known = {}
    for snap in prestart:
        identity = validate_prestart(snap)
        if identity[0] != day or identity[1:] in known:
            raise WorkoutLockError("Cross-band original race mismatch")
        known[identity[1:]] = snap
    out, seen = [], set()
    for item in receipts:
        if not isinstance(item,dict) or set(item) != {"snapshot","signature"}:
            raise WorkoutLockError("Invalid cross-band receipt")
        snap = item["snapshot"]
        if not isinstance(snap,dict):
            raise WorkoutLockError("Invalid cross-band stored snapshot")
        coord = (snap.get("track"), snap.get("race"))
        original = known.get(coord)
        if (coord in seen or original is None
                or _validate(snap,original)[0] != day
                or snap["prestartSignature"] != sign_prestart(original,secret)
                or type(item["signature"]) is not str
                or not hmac.compare_digest(item["signature"],
                                           _digest(snap,secret))):
            raise WorkoutLockError("Cross-band receipt signature mismatch")
        seen.add(coord)
        out.append(snap)
    return out
