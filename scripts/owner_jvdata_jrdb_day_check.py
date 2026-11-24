"""Owner-private, OFFLINE one-day cross-provider candidate comparison.

This is the next integration seam after a user-authorized Windows JV-Link read
and the existing authenticated JRDB day read. It performs no API calls or
uploads. Never call it from an unauthenticated public page or publish raw
provider records. A matching roster is NOT official JRA starters, scratches,
going, or final post-time verification.
"""
from collections import Counter
from datetime import datetime, timedelta, timezone

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jvdata_ra_se_candidate import (
    VERSION as CARD_VERSION, compare_jvdata_candidate_to_jrdb,
)
from windows_jvlink_weekly_read import VERSION as WEEK_VERSION

VERSION = "owner-jvdata-jrdb-day-candidate-crosscheck-1"
MAX_RACES = 36
JST = timezone(timedelta(hours=9))
VENUES = frozenset(("札幌", "函館", "福島", "新潟", "東京",
                    "中山", "中京", "京都", "阪神", "小倉"))


def _coordinate(value):
    if not isinstance(value, dict):
        raise CoverageError("Invalid one-day race row")
    track, race = value.get("track"), value.get("race")
    if (type(track) is not str or track not in VENUES
            or type(race) is not int or not 1 <= race <= 12):
        raise CoverageError("Invalid one-day race coordinate")
    return track, race


def audit_day_candidate_matches(jv_week, jrdb_programme, jrdb_entries, day):
    """Compare all same-day matching source records, rejecting orphan data.

    Missing JV-data RA/SE for a JRDB race means an explicit HOLD. Different
    horse numbers, counts, and scheduled off-times are HOLDs too. Never
    declare JRA final status or manufacture missing competitors.
    """
    if (type(day) is not str or not _valid_date(day)
            or not isinstance(jv_week, dict)
            or jv_week.get("version") != WEEK_VERSION
            or jv_week.get("date") != day
            or jv_week.get("source") != "private_jvlink_weekly_ra_se_candidate"
            or jv_week.get("privateOwnerOnly") is not True
            or jv_week.get("researchOnly") is not True
            or jv_week.get("providerDataRawIncluded") is not False
            or jv_week.get("independentJraVerified") is not False
            or jv_week.get("officialScratchesVerified") is not False
            or jv_week.get("officialGoingVerified") is not False
            or jv_week.get("officialFinalPostTimeVerified") is not False
            or jv_week.get("productionPredictionReady") is not False
            or jv_week.get("bettingReady") is not False
            or jv_week.get("autoPurchase") is not False
            or jv_week.get("collectionTimeIndependentlyVerified") is not False
            or type(jv_week.get("allCandidatesBeforeScheduledOff")) is not bool
            or not isinstance(jv_week.get("races"), list)
            or type(jv_week.get("raceCount")) is not int
            or jv_week["raceCount"] != len(jv_week["races"])
            or len(jv_week["races"]) > MAX_RACES
            or not isinstance(jrdb_programme, list)
            or len(jrdb_programme) > MAX_RACES
            or not isinstance(jrdb_entries, list)
            or len(jrdb_entries) > 18 * MAX_RACES):
        raise CoverageError("Invalid private day comparison contract")

    # A local JSON file is editable: recompute all prestart flags from the
    # same local timestamp. This detects accidental mismatches, but does NOT
    # attest the PC clock or the JV-Link provider's original delivery time.
    try:
        captured = datetime.fromisoformat(jv_week["capturedAtLocalJst"])
        if captured.tzinfo is None or captured.utcoffset() is None:
            raise ValueError()
        captured = captured.astimezone(JST)
    except (KeyError, TypeError, ValueError, OverflowError):
        raise CoverageError("Missing local candidate capture time") from None
    cards, programme = {}, {}
    for card in jv_week["races"]:
        key = _coordinate(card)
        if (key in cards or card.get("date") != day
                or card.get("version") != CARD_VERSION
                or card.get("privateInputOnly") is not True
                or card.get("sourceDataUseRightsVerified") is not False
                or card.get("researchOnly") is not True
            or card.get("collectionTimeIndependentlyVerified") is not False
            or type(card.get("beforeScheduledOffAtLocalCapture")) is not bool):
            raise CoverageError("Duplicated or promoted JV-data candidate")
        try:
            off = datetime.strptime(day + card["postTimeCandidate"],
                                    "%Y%m%d%H:%M").replace(tzinfo=JST)
        except (KeyError, TypeError, ValueError):
            raise CoverageError("Invalid scheduled candidate time") from None
        if card["beforeScheduledOffAtLocalCapture"] != (captured < off):
            raise CoverageError("Inconsistent candidate collection timestamp")
        cards[key] = card

    if jv_week["allCandidatesBeforeScheduledOff"] != all(
        card["beforeScheduledOffAtLocalCapture"] for card in cards.values()
    ):
        raise CoverageError("Inconsistent whole-day candidate timing")
    for row in jrdb_programme:
        key = _coordinate(row)
        if (key in programme or row.get("racedate") != day
                or row.get("programmeOnly") is not True
                or row.get("horsesVerified") is not False
                or type(row.get("racekey")) is not str):
            raise CoverageError("Invalid private JRDB programme")
        programme[key] = row
    if set(cards) - set(programme):
        raise CoverageError("JRA-VAN data outside the matching JRDB day")

    keyed = {row["racekey"]: coord for coord, row in programme.items()}
    if len(keyed) != len(programme):
        raise CoverageError("Duplicate JRDB programme racekey")
    grouped = {coord: [] for coord in programme}
    for entry in jrdb_entries:
        if not isinstance(entry, dict) or entry.get("racekey") not in keyed:
            raise CoverageError("Unmatched JRDB entry for JV-data day")
        coord = keyed[entry["racekey"]]
        if entry.get("racedate") != day:
            raise CoverageError("Different-day JRDB entry")
        grouped[coord].append(entry)

    results = []
    for coord in sorted(programme):
        row, card = programme[coord], cards.get(coord)
        cross = None
        if card is None:
            status = "missing_jvdata_candidate"
            matched = False
        elif card["beforeScheduledOffAtLocalCapture"] is False:
            # A local diagnostic captured after scheduled off cannot be
            # used to reconstruct a supposedly prestart roster.
            status = "post_off_local_capture"
            matched = False
        else:
            cross = compare_jvdata_candidate_to_jrdb(
                card, row, grouped[coord],
            )
            status = cross["status"]
            matched = status == "candidate_matched_not_final"
        results.append({
            "track": coord[0], "race": coord[1],
            "status": status,
            "candidateMatched": matched,
            "entryCountCandidateMatch": cross["entryCountCandidateMatch"] if cross is not None else None,
            "jrdbEntryRowsMissingCandidate": cross["jrdbEntryRowsMissingCandidate"] if cross is not None else None,
            "possibleWithdrawnInJrdb": cross["possibleWithdrawnInJrdb"] if cross is not None else None,
            "officialJraVerified": False,
            "finalScratchesVerified": False,
            "productionPredictionReady": False,
        })

    counts = Counter(r["status"] for r in results)
    return {
        "version": VERSION, "date": day,
        "jrdbRaceCount": len(programme),
        "jvdataRaceCount": len(cards),
        "candidateMatchedRaces": counts["candidate_matched_not_final"],
        "missingJvdataRaces": counts["missing_jvdata_candidate"],
        "heldMismatchRaces": counts["hold_source_mismatch"],
        "missingJrdbEntryRaces": sum((r["jrdbEntryRowsMissingCandidate"] or 0) > 0 for r in results),
        "possibleJrdbWithdrawalRaces": sum(r["possibleWithdrawnInJrdb"] is True for r in results),
        "postOffCandidateRaces": counts["post_off_local_capture"],
        "allCandidatesMatched": len(programme) > 0 and (
            counts["candidate_matched_not_final"] == len(programme)
        ),
        "races": results,
        "finalJraStarterListVerified": False,
        "officialScratchesVerified": False,
        "officialGoingVerified": False,
        "officialFinalPostTimeVerified": False,
        "formalTenFactorReady": False,
        "productionPredictionReady": False,
        "bettingReady": False,
        "actualPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "newJraVanRead": False, "newJrdbPaidReads": 0,
        "note": "JRA-VANとJRDBの同日出馬表候補をR単位で比較。最終公式確認・採点・馬券は未実施。",
    }
