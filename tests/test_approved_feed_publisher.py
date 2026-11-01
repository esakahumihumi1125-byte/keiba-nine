"""Fail-closed unit tests for an explicitly approved public forecast feed."""
import copy
import unittest
from datetime import datetime, timedelta, timezone

from scripts.publish_approved_feed import JST, publish, validate


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 7, 0, 0, tzinfo=timezone.utc)  # 09:00 JST
        self.date = self.now.astimezone(JST).date().isoformat()
        self.source = {"name": "Owner-authorized independent forecast",
                       "rightsNote": "Original predictions cleared for public release",
                       "publicReleaseApproved": True}
        self.final = {
            "date": self.date, "track": "京都", "race": 10, "off": "14:50",
            "recordType": "live", "status": "final", "confidence": "B",
            "intent": "参考", "ranking": [1, 2, 3],
            "first": [1], "second": [2], "third": [3],
            "triPoints": 1, "trioPoints": 0,
            "evidence": {"references": ["https://www.jra.go.jp/"]},
            "raceCard": {"complete": True, "runners": [
                {"number": 1, "name": "架空テスト馬A"},
                {"number": 2, "name": "架空テスト馬B"},
                {"number": 3, "name": "架空テスト馬C"}]},
        }
        self.payload = {"schema": 1, "date": self.date,
                        "generatedAt": self.now.isoformat(),
                        "source": self.source, "forecasts": [self.final]}

    def test_valid_complete_future_final(self):
        self.assertEqual(validate(copy.deepcopy(self.payload), self.now)["date"], self.date)

    def test_no_permission_no_publish(self):
        data = copy.deepcopy(self.payload)
        data["source"]["publicReleaseApproved"] = False
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_test_record_rejected(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["recordType"] = "test"
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_reject_unchecked_final(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["raceCard"]["complete"] = False
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_reject_post_time_final(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["off"] = "08:50"
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_reject_wrong_ticket_count(self):
        data = copy.deepcopy(self.payload)
        data["forecasts"][0]["triPoints"] = 2
        with self.assertRaises(ValueError):
            publish(data, None, self.now)

    def test_prior_started_race_immutable(self):
        previous = copy.deepcopy(self.payload)
        previous["forecasts"][0]["off"] = "08:00"
        incoming = copy.deepcopy(self.payload)
        incoming["forecasts"][0]["race"] = 11
        result = publish(incoming, previous, self.now)
        self.assertEqual(len(result["forecasts"]), 2)
        self.assertEqual(result["forecasts"][0]["race"], 10)

        changed = copy.deepcopy(incoming)
        changed["forecasts"].append(copy.deepcopy(previous["forecasts"][0]))
        changed["forecasts"][-1]["ranking"] = [2, 1, 3]
        with self.assertRaises(ValueError):
            publish(changed, previous, self.now)

    def test_noop_same_data(self):
        self.assertIsNone(publish(copy.deepcopy(self.payload), self.payload, self.now))

    def test_expired_source_rejected(self):
        data = copy.deepcopy(self.payload)
        data["generatedAt"] = (self.now - timedelta(days=3)).isoformat()
        with self.assertRaises(ValueError):
            publish(data, None, self.now)


if __name__ == "__main__":
    unittest.main()
