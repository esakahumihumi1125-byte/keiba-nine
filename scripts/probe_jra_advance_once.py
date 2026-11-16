"""Explicit one-time JRA public schedule live check, without paid sources.

This command is not imported by the owner app and never logs HTML or
provider credentials. Use only for intentional one-GET diagnostics.
"""
from datetime import date
from jra_advance_programme_reference import probe_advance_programme


def main():
    # Genuine JRA calendar data for 2026-11-15 (36 scheduled races).
    # This is planned information, never final starters or betting proof.
    r = probe_advance_programme(
        "2026-11-15", today=date(2026, 11, 16))
    by = {(row["track"], row["race"]): row for row in r["races"]}
    assert r["raceCount"] == 36 and r["venueCount"] == 3
    assert by["東京", 1] == {
        "track": "東京", "race": 1, "postTime": "09:45",
        "distanceM": 1400, "surface": "ダート"}
    assert by["京都", 11] == {
        "track": "京都", "race": 11, "postTime": "15:40",
        "distanceM": 2200, "surface": "芝"}
    assert by["福島", 4] == {
        "track": "福島", "race": 4, "postTime": "11:05",
        "distanceM": 2750, "surface": None}
    assert all(r[k] is False for k in (
        "officialFinalCardVerified", "officialStartersVerified",
        "officialScratchesVerified", "officialGoingVerified",
        "officialPostTimeVerified", "predictionReady", "bettingReady"))
    print("JRA public advance schedule live check: 36 planned slots,"
          " 3 expected venue/race/course examples; no betting proof")


if __name__ == "__main__":
    main()
