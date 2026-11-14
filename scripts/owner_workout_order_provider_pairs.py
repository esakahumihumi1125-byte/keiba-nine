"""Read-only postrace concordance study for HMAC-VERIFIED prestart workout order.

Inputs are verified HMAC snapshots + caller-injected JRDB /tse rows, never
browser-supplied outcomes. Exact full-field provisional finish orders are
required. Only aggregate within-band INDEX-ORDER pairs are compared. No
individual JRDB index, horse, race key, finish or payout leaves this module.
A positive concordance is NOT a validated point rubric or win probability.
"""
import re
from datetime import datetime, timezone

from jrdb_program_preview import TRACKS
from owner_workout_order_receipts import (
    _validate, _clock, WorkoutLockError, BANDS, VERSION as LOCK_VERSION,
)

VERSION = "owner-workout-order-provider-pairs-1"
MAX_ROWS = 2160
MAX_RACES = 36


def compare_workout_order_with_provider(snapshots, rows, day, *,
                                        now, source_read_count=1):
    if (not isinstance(snapshots, list) or not 1 <= len(snapshots) <= MAX_RACES
            or not isinstance(rows, list) or len(rows) > MAX_ROWS
            or type(source_read_count) is not int
            or source_read_count not in (0, 1)
            or (source_read_count == 0 and rows)):
        raise WorkoutLockError("Invalid pair-study inputs")
    current = _clock(now)
    frozen, identities = [], set()
    for snap in snapshots:
        coord = _validate(snap)
        if coord[0] != day or coord in identities:
            raise WorkoutLockError("Invalid or duplicate prestart study race")
        identities.add(coord)
        frozen.append(snap)
    # Strictly check even unrelated provider data; never connect one
    # horse solely by its number without a verified course/day identity.
    provider = {}
    for raw in rows:
        if not isinstance(raw, dict):
            raise WorkoutLockError("Invalid provisional finish row")
        key = raw.get("racekey")
        racedate = raw.get("racedate")
        number = raw.get("horse_number")
        finish = raw.get("order_of_finish")
        if (not isinstance(key, str) or not re.fullmatch(r"[0-9a-f]{8}", key)
                or key[:2] not in TRACKS or key[2:4] != day[2:4]
                or not key[6:].isdigit() or not 1 <= int(key[6:]) <= 12
                or racedate != day or not isinstance(number, str)
                or not re.fullmatch(r"(?:0[1-9]|1[0-8])", number)
                or finish is not None and not isinstance(finish, str)):
            raise WorkoutLockError("Provisional result identity mismatch")
        coord = (TRACKS[key[:2]], int(key[6:]))
        race = provider.setdefault(coord, {
            "keys": set(), "places": {}, "numbers": set(), "complete": True,
        })
        n = int(number)
        race["keys"].add(key)
        if n in race["numbers"]:
            race["complete"] = False
        race["numbers"].add(n)
        trouble = raw.get("trouble_classification")
        if (not isinstance(finish, str)
                or not re.fullmatch(r"(?:0?[1-9]|1[0-8])", finish)
                or trouble not in (None, "", "0")):
            race["complete"] = False
            continue
        place = int(finish)
        if place in race["places"]:
            race["complete"] = False
        race["places"][place] = n

    summary = {grade: {"concordant": 0, "discordant": 0,
                       "equalIndexExcluded": 0} for grade in BANDS}
    output = []
    for snap in frozen:
        coord = snap["track"], snap["race"]
        group = provider.get(coord)
        off = datetime.fromisoformat(snap["scheduledOffAt"]).astimezone(timezone.utc)
        n = snap["raceRunnerCount"]
        good = (current >= off and group is not None and group["complete"]
                and len(group["keys"]) == 1 and len(group["numbers"]) == n
                and set(group["numbers"]) == {h["number"] for h in snap["horses"]}
                and set(group["places"]) == set(range(1, n + 1)))
        counts = {grade: {"concordant": 0, "discordant": 0,
                          "equalIndexExcluded": 0} for grade in BANDS}
        if good:
            finishes = {number: place for place, number in group["places"].items()}
            for grade in BANDS:
                peers = [h for h in snap["horses"] if h["trainingBand"] == grade]
                for index, left in enumerate(peers):
                    for right in peers[index + 1:]:
                        a, b = left["withinBandRank"], right["withinBandRank"]
                        if a == b:
                            counts[grade]["equalIndexExcluded"] += 1
                        elif ((a < b) == (finishes[left["number"]] < finishes[right["number"]])):
                            counts[grade]["concordant"] += 1
                        else:
                            counts[grade]["discordant"] += 1
            for grade in BANDS:
                for k in summary[grade]:
                    summary[grade][k] += counts[grade][k]
        output.append({
            "track": coord[0], "race": coord[1],
            "providerStatus": "complete_provisional_order" if good else "pending",
            "comparedRunnerCount": n if good else 0,
            "pairCounts": counts if good else None,
            "officialJraVerified": False,
            "predictionVerified": False,
        })
    return {
        "version": VERSION, "date": day,
        "sourceKind": "jrdb-tse-provisional-workout-order-pair-review",
        "sourceReadCount": source_read_count,
        "raceCount": len(output), "races": output,
        "studiedRaceCount": sum(
            x["providerStatus"] == "complete_provisional_order" for x in output),
        "observedPairsByTrainingBand": summary,
        "officialJraVerified": False, "accuracyVerified": False,
        "calibrationReady": False, "scoreReady": False,
        "newScoringRubric": False, "bettingReady": False,
        "predictionReady": False, "actualPurchase": False,
        "roiPercent": None, "payoutVerified": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "note": ("発走前に固定した調教指数の同ランク内順序とJRDB暫定着順の"
                 "一致・不一致ペア数を参考集計。元指数が同点の組は対象外。"
                 "資料欠落・取消等を含むレースは未集計。"
                 "JRA公式結果未照合で、精度・勝率・30点の採点基準ではありません。"),
    }
