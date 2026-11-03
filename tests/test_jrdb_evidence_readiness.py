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

    def test_missing_evidence_summary_is_per_race_and_contains_no_horse_ids(self):
        result = self.audit()
        tokyo, kyoto = result["races"]
        self.assertEqual(tokyo["trainingUnaccounted"], 0)
        self.assertEqual(tokyo["lastWeekUnaccounted"], 1)
        self.assertEqual(tokyo["pastRunUnaccounted"], 1)
        self.assertEqual(kyoto["trainingUnaccounted"], 1)
        self.assertEqual(kyoto["lastWeekUnaccounted"], 1)
        self.assertEqual(kyoto["pastRunUnaccounted"], 1)
        self.assertEqual(result["unaccountedTotals"],
                         {"training": 1, "lastWeek": 2, "pastRuns": 2})
        self.assertEqual(result["gapRaceCount"], 2)
        self.assertTrue(any("1週前調教" in item for item in tokyo["evidenceGaps"]))
        self.assertTrue(any("近走記録" in item for item in kyoto["evidenceGaps"]))
        self.assertNotIn("2328aaa95a05", repr(result))
        self.assertNotIn("NONPUBLIC", repr(result))

    def test_complete_evidence_counts_never_claim_actual_forecast(self):
        p, e, t, z = sample()
        t.append({"racekey": "05264b01", "racedate": "20261101",
                  "horse_number": "02", "horse_id": "2328aaa95a06",
                  "oikirisisu_lastweek": 35})
        t.append({"racekey": "08264b01", "racedate": "20261101",
                  "horse_number": "01", "horse_id": "2328aaa95a07",
                  "oikirisisu": 42, "oikirisisu_lastweek": 39})
        z.extend([
            {"racekey": "05264b01", "racedate": "20261101",
             "horse_number": "02", "horse_id": "2328aaa95a06",
             "race_back_1_racedate": "20261004"},
            {"racekey": "08264b01", "racedate": "20261101",
             "horse_number": "01", "horse_id": "2328aaa95a07",
             "race_back_1_racedate": "20261004"},
        ])
        result = self.audit(p, e, t, z)
        self.assertEqual(result["gapRaceCount"], 0)
        self.assertEqual(result["unaccountedTotals"],
                         {"training": 0, "lastWeek": 0, "pastRuns": 0})
        self.assertTrue(all(not r["evidenceGaps"] for r in result["races"]))
        self.assertTrue(all(r["predictionsReady"] is False for r in result["races"]))
        self.assertTrue(all(r["rosterVerified"] is False for r in result["races"]))
        self.assertEqual(result["predictionsReady"], 0)

    def test_no_evidence_reports_unaccounted_but_not_fabricated_past_runs(self):
        p, e, _, _ = sample()
        result = self.audit(p, e, [], [])
        self.assertEqual(result["gapRaceCount"], 2)
        self.assertEqual(result["unaccountedTotals"]["training"], 3)
        self.assertEqual(result["unaccountedTotals"]["lastWeek"], 3)
        self.assertEqual(result["unaccountedTotals"]["pastRuns"], 3)
        self.assertFalse(any(r["predictionsReady"] for r in result["races"]))

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
