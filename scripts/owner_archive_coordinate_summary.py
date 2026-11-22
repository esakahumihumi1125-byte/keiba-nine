"""Redacted archive coverage from already HMAC-verified prestart receipts.

No source records, signatures, ticket numbers, credentials, purchase data or
paid requests. This only labels known server-saved, immutable research R coords;
it cannot certify that a full JRA day was forecast.
"""
from collections import Counter

from jrdb_program_preview import TRACKS
from owner_prestart_receipt import _selected_day, ReceiptError

VERSION = "owner-prestart-saved-coordinate-summary-1"
VENUES = frozenset(TRACKS.values())


def summarize_saved_races(verified, selected_day):
    """Accept ONLY the result of verify_preview_receipts, never raw client data."""
    _selected_day(selected_day)
    if not isinstance(verified, list) or len(verified) > 36:
        raise ReceiptError("Verified archive summary is invalid")
    coords = set()
    for snapshot in verified:
        if (not isinstance(snapshot, dict)
                or snapshot.get("date") != selected_day
                or snapshot.get("sourceKind") != "prestart-locked"
                or snapshot.get("actualPurchase") is not False
                or snapshot.get("track") not in VENUES
                or type(snapshot.get("race")) is not int
                or not 1 <= snapshot["race"] <= 12):
            raise ReceiptError("Verified archive summary identity invalid")
        key = snapshot["track"], snapshot["race"]
        if key in coords:
            raise ReceiptError("Repeated verified archive coordinate")
        coords.add(key)
    order = {track: i for i, track in enumerate(TRACKS.values())}
    sorted_races = sorted(coords, key=lambda x: (order[x[0]], x[1]))
    by_venue = Counter(track for track, _ in sorted_races)
    return {
        "version": VERSION,
        "storedRaceCoordinates": [
            {"track": track, "race": race} for track, race in sorted_races
        ],
        "storedVenueCounts": [
            {"track": track, "raceCount": by_venue[track]}
            for track in TRACKS.values() if by_venue[track]
        ],
        "serverSavedRaceCount": len(sorted_races),
        "completeJraDayVerified": False,
        "officialJraVerified": False,
        "newProviderRequests": 0,
        "changesExistingReceipts": False,
        "researchOnly": True,
    }
