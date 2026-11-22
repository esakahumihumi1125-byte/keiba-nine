"""Server archive race coordinates are derived ONLY from verified receipts."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_archive_coordinate_summary import summarize_saved_races, VERSION
from owner_prestart_receipt import ReceiptError

DAY = "2026-11-23"


def row(track, race):
    return {
        "date": DAY, "track": track, "race": race,
        "sourceKind": "prestart-locked", "actualPurchase": False,
        "trifectaTickets": [[1, 2, 3]],
        "lockedAt": "2026-11-22T08:00:00+09:00",
        "scheduledOffAt": "2026-11-23T10:00:00+09:00",
    }


class ArchivedCoordinateSummaryTests(unittest.TestCase):
    def test_mixed_24r_saves_only_race_coordinates(self):
        verified = [row("東京", k) for k in range(1, 13)]
        verified += [row("福島", k) for k in range(1, 13)]
        actual = summarize_saved_races(verified[::-1], DAY)
        self.assertEqual(actual["version"], VERSION)
        self.assertEqual(actual["serverSavedRaceCount"], 24)
        self.assertEqual(len(actual["storedRaceCoordinates"]), 24)
        self.assertEqual(actual["storedVenueCounts"], [
            {"track": "福島", "raceCount": 12},
            {"track": "東京", "raceCount": 12},
        ])
        self.assertEqual(actual["newProviderRequests"], 0)
        self.assertIs(actual["changesExistingReceipts"], False)
        self.assertIs(actual["completeJraDayVerified"], False)
        self.assertNotIn("trifectaTickets", repr(actual))
        self.assertNotIn("lockedAt", repr(actual))
        self.assertNotIn("scheduledOffAt", repr(actual))

    def test_zero_is_not_full_card(self):
        actual = summarize_saved_races([], DAY)
        self.assertEqual(actual["storedRaceCoordinates"], [])
        self.assertEqual(actual["storedVenueCounts"], [])
        self.assertEqual(actual["serverSavedRaceCount"], 0)
        self.assertIs(actual["completeJraDayVerified"], False)

    def test_invalid_coordinate_or_flags_fails_closed(self):
        for mutation in (
            lambda rows: rows.append(row("東京", 1)),
            lambda rows: rows[0].update(track="不明"),
            lambda rows: rows[0].update(race=True),
            lambda rows: rows[0].update(race=13),
            lambda rows: rows[0].update(sourceKind="provisional"),
            lambda rows: rows[0].update(actualPurchase=True),
            lambda rows: rows[0].update(date="2026-11-22"),
            lambda rows: rows[0].update(race="1"),
        ):
            with self.subTest(mutation=mutation):
                rows = [row("東京", 1)]
                mutation(rows)
                with self.assertRaises(ReceiptError):
                    summarize_saved_races(rows, DAY)
        with self.assertRaises(ReceiptError):
            summarize_saved_races([row("東京", 1)] * 37, DAY)
        with self.assertRaises(ReceiptError):
            summarize_saved_races([row("東京", 1)], "2026-02-30")


if __name__ == "__main__":
    unittest.main()
