import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_evidence_readiness import audit_evidence_coverage, CoverageError
# Catch the exact exception exported by the audited module; distinct import paths
# (jrdb_coverage vs scripts.jrdb_coverage) otherwise create different classes.


def sample():
    programme = [
        {"racekey": "05264b01", "racedate": "20261101",
         "track": "東京", "race": 1, "headcount": 2, "post_time": "10:00"},
        {"racekey": "08264b01", "racedate": "20261101",
         "track": "京都", "race": 1, "headcount": 1, "post_time": "10:05"},
    ]
    entries = [
        {"racekey": "05264b01", "racedate": "20261101",
         "horse_number": "01", "horse_id": "2328aaa95a05",
         "horse_name": "NONPUBLIC"},
        {"racekey": "05264b01", "racedate": "20261101",
         "horse_number": "02", "horse_id": "2328aaa95a06",
         "horse_name": "NONPUBLIC2"},
        {"racekey": "08264b01", "racedate": "20261101",
         "horse_number": "01", "horse_id": "2328aaa95a07",
         "horse_name": "NONPUBLIC3"},
    ]
    training = [
        {"racekey": "05264b01", "racedate": "20261101",
         "horse_number": None, "horse_id": "2328aaa95a05",
         "oikirisisu": 52, "oikirisisu_lastweek": "41",
         "private_metric": "SECRET-NOT-FOR-API"},
        {"racekey": "05264b01", "racedate": "20261101",
         "horse_number": "02", "horse_id": "2328aaa95a06",
         "exercise_amount_eval": "B"},
    ]
    previous = [
        {"racekey": "05264b01", "racedate": "20261101",
         "horse_number": "01", "horse_id": "2328aaa95a05",
         "race_back_1_racedate": "20261004",
         "race_back_1_order_of_finish": 4},
    ]
    return programme, entries, training, previous


class EvidenceReadinessTests(unittest.TestCase):
    def audit(self, *args):
        return audit_evidence_coverage(*(args or sample()), "20261101")

    def test_coverage_error_identity_is_consistent(self):
        self.assertIs(CoverageError, audit_evidence_coverage.__globals__['CoverageError'])

    def test_evidence_counts_are_per_race(self):
        result = self.audit()
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["matchingEntryCounts"], 2)
        tokyo, kyoto = result["races"]
        self.assertEqual(tokyo["trainingRecords"], 2)
        self.assertEqual(tokyo["lastWeekRecords"], 1)
        self.assertEqual(tokyo["pastRunRecords"], 1)
        self.assertEqual(kyoto["trainingRecords"], 0)
        self.assertEqual(kyoto["lastWeekRecords"], 0)
        self.assertEqual(kyoto["pastRunRecords"], 0)
        self.assertEqual(result["predictionsReady"], 0)
        self.assertEqual(result["fullyVerifiedRaces"], 0)

    def test_no_private_horse_content_is_returned(self):
        text = repr(self.audit())
        for secret in ("NONPUBLIC", "SECRET-NOT-FOR-API", "2328aaa95a05"):
            self.assertNotIn(secret, text)

    def test_no_data_never_becomes_ready(self):
        p, e, t, z = sample()
        result = self.audit(p, e, [], [])
        self.assertEqual(result["predictionsReady"], 0)
        self.assertEqual(result["races"][0]["trainingRecords"], 0)

    def test_same_day_past_race_is_rejected(self):
        p, e, t, z = sample()
        z[0]["race_back_1_racedate"] = "20261101"
        with self.assertRaises(CoverageError):
            self.audit(p, e, t, z)

    def test_future_past_race_is_rejected(self):
        p, e, t, z = sample()
        z[0]["race_back_1_racedate"] = "20261201"
        with self.assertRaises(CoverageError):
            self.audit(p, e, t, z)

    def test_wrong_race_is_rejected(self):
        p, e, t, z = sample()
        t[0]["racekey"] = "09264b01"
        with self.assertRaises(CoverageError):
            self.audit(p, e, t, z)

    def test_unmatched_horse_id_is_rejected(self):
        p, e, t, z = sample()
        t[0]["horse_id"] = "2328aaa95a99"
        with self.assertRaises(CoverageError):
            self.audit(p, e, t, z)

    def test_inconsistent_id_and_number_is_rejected(self):
        p, e, t, z = sample()
        t[0]["horse_number"] = "02"
        with self.assertRaises(CoverageError):
            self.audit(p, e, t, z)

    def test_broken_id_is_rejected(self):
        p, e, t, z = sample()
        t[0]["horse_id"] = "garbage"
        with self.assertRaises(CoverageError):
            self.audit(p, e, t, z)

    def test_ambiguous_entry_id_is_rejected(self):
        p, e, t, z = sample()
        e[1]["horse_id"] = e[0]["horse_id"]
        with self.assertRaises(CoverageError):
            self.audit(p, e, t, z)


if __name__ == "__main__":
    unittest.main()
