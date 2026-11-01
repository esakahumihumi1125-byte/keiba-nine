"""Validation tests: real-source publication must fail closed."""
import copy
import unittest
from datetime import datetime, timedelta, timezone

from scripts.publish_approved_feed import JST, publish, validate


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 7, 0, 0, tzinfo=timezone.utc)
        self.date = self.now.astimezone(JST).date().isoformat()
        self.card = {
            "date": self.date, "track": "京都", "race": 10,
            "source": "https://www.jra.go.jp/",
            "checkedAt": self.now.isoformat(), "complete": True,
            "runners": [
                {"number": n, "name": f"架空テスト馬{n}", "status": "active"}
                for n in range(1, 4)
            ]
        }
        self.final = {
            "date": self.date, "track": "京都", "race": 10, "off": "14:50",
            "recordType": "live", "status": "final", "confidence": "B",
            "intent": "参考", "ranking": [1, 2, 3],
            "first": [1], "second": [2], "third": [3],
            "triPoints": 1, "trioPoints": 0,
            "evidence": {"references": ["https://www.jra.go.jp/"]},
            "raceCard": self.card,
        }
        self.payload = {
            "schema": 1, "date": self.date,
            "generatedAt": self.now.isoformat(),
            "source": {"name": "Owner's original public forecasts",
                       "rightsNote": "Permission is explicitly recorded by owner",
                       "publicReleaseApproved": True,
                       "originalForecast": True},
            "forecasts": [self.final],
        }

    def test_future_final_valid(self):
        self.assertEqual(validate(copy.deepcopy(self.payload), self.now)["date"], self.date)
        self.assertEqual(len(publish(copy.deepcopy(self.payload), None, self.now)["forecasts"]), 1)

    def test_missing_public_permission_rejected(self):
        data = copy.deepcopy(self.payload)
        data["source"]["publicReleaseApproved"] = False
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_non_original_source_rejected(self):
        data = copy.deepcopy(self.payload)
        data["source"]["originalForecast"] = False
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_test_record_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["recordType"] = "test"
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_unchecked_final_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["raceCard"]["complete"] = False
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_scratched_horse_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["raceCard"]["runners"][0]["status"] = "scratched"
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_future_check_timestamp_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["raceCard"]["checkedAt"] = (
            self.now + timedelta(hours=2)).isoformat()
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_post_time_new_final_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["off"] = "08:50"
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_post_time_new_draft_rejected(self):
        data = copy.deepcopy(self.payload)
        row = data["forecasts"][0]
        row["status"], row["first"], row["second"], row["third"] = "draft", [], [], []
        row["triPoints"] = 0
        row["off"] = "08:50"
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_unverified_draft_with_bets_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["status"] = "draft"
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_point_count_mismatch_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["triPoints"] = 2
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_started_race_preserved(self):
        previous = copy.deepcopy(self.payload)
        previous["forecasts"][0]["off"] = "08:00"
        incoming = copy.deepcopy(self.payload)
        incoming["forecasts"][0]["race"] = 11
        incoming["forecasts"][0]["raceCard"]["race"] = 11
        updated = publish(incoming, previous, self.now)
        self.assertEqual({r["race"] for r in updated["forecasts"]}, {10, 11})
        self.assertEqual(next(r for r in updated["forecasts"] if r["race"] == 10),
                         previous["forecasts"][0])

    def test_started_race_cannot_be_rewritten(self):
        old = copy.deepcopy(self.payload)
        old["forecasts"][0]["off"] = "08:00"
        new = copy.deepcopy(old)
        new["forecasts"][0]["ranking"] = [2, 1, 3]
        with self.assertRaises(ValueError):
            publish(new, old, self.now)

    def test_unchanged_started_race_is_noop(self):
        old = copy.deepcopy(self.payload)
        old["forecasts"][0]["off"] = "08:00"
        self.assertIsNone(publish(copy.deepcopy(old), old, self.now))

    def test_noop_same_future_race(self):
        self.assertIsNone(publish(copy.deepcopy(self.payload), self.payload, self.now))

    def test_expired_source_rejected(self):
        data = copy.deepcopy(self.payload)
        data["generatedAt"] = (self.now - timedelta(days=3)).isoformat()
        with self.assertRaises(ValueError):
            publish(data, None, self.now)


if __name__ == "__main__":
    unittest.main()
