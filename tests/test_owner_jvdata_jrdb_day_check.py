"""Synthetic offline whole-day JRA-VAN vs JRDB race-matching tests."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jvdata_ra_se_candidate import compare_jvdata_candidate_to_jrdb
from owner_jvdata_jrdb_day_check import audit_day_candidate_matches
from test_jvdata_ra_se_candidate import DAY, jrdb
from test_windows_jvlink_weekly_read import FakeJv, weekly_records
from windows_jvlink_weekly_read import collect_weekly_candidate_records


def data():
    week = collect_weekly_candidate_records(FakeJv(weekly_records()), DAY)
    programme, entries = jrdb()
    return week, [programme], entries


class JvDayCrosscheckTests(unittest.TestCase):
    def test_one_actual_coordinate_candidate_not_promoted_to_official(self):
        inputs = data()
        original = copy.deepcopy(inputs)
        report = audit_day_candidate_matches(*inputs, DAY)
        self.assertEqual(inputs, original)
        self.assertEqual(report["jrdbRaceCount"], 1)
        self.assertEqual(report["jvdataRaceCount"], 1)
        self.assertEqual(report["candidateMatchedRaces"], 1)
        self.assertTrue(report["allCandidatesMatched"])
        self.assertEqual(report["missingJvdataRaces"], 0)
        self.assertEqual(report["heldMismatchRaces"], 0)
        self.assertEqual(report["races"][0]["status"], "candidate_matched_not_final")
        for field in ("finalJraStarterListVerified",
                      "officialScratchesVerified", "officialGoingVerified",
                      "officialFinalPostTimeVerified", "formalTenFactorReady",
                      "productionPredictionReady", "bettingReady",
                      "actualPurchase"):
            self.assertFalse(report[field])
        self.assertEqual(report["newJrdbPaidReads"], 0)
        self.assertFalse(report["newJraVanRead"])
        for private in ("horse_id", "racekey", "1000000001",
                        "byNumber", "jockey_index", "private_field"):
            self.assertNotIn(private, json.dumps(report))

    def test_missing_jra_candidate_preserves_race_and_holds_it_only(self):
        week, programme, entries = data()
        missing = {**programme[0], "track": "京都", "race": 2,
                   "racekey": "08265502", "post_time": "10:35"}
        programme.append(missing)
        entries.extend({**r, "racekey": missing["racekey"]} for r in entries[:4])
        report = audit_day_candidate_matches(week, programme, entries, DAY)
        self.assertEqual(report["jrdbRaceCount"], 2)
        self.assertEqual(report["candidateMatchedRaces"], 1)
        self.assertEqual(report["missingJvdataRaces"], 1)
        self.assertFalse(report["allCandidatesMatched"])
        statuses = {(r["track"], r["race"]): r["status"]
                    for r in report["races"]}
        self.assertEqual(statuses[("東京", 1)], "candidate_matched_not_final")
        self.assertEqual(statuses[("京都", 2)], "missing_jvdata_candidate")

    def test_wrong_post_and_horse_set_hold_without_raising_race_grade(self):
        for field in ("post_time", "horse_number", "headcount"):
            week, programme, entries = data()
            if field == "horse_number":
                entries[0]["horse_number"] = "09"
            else:
                programme[0][field] = "10:05" if field == "post_time" else 5
            with self.subTest(field=field):
                report = audit_day_candidate_matches(week, programme, entries, DAY)
                self.assertEqual(report["heldMismatchRaces"], 1)
                self.assertEqual(report["races"][0]["status"], "hold_source_mismatch")
                self.assertFalse(report["productionPredictionReady"])

    def test_foreign_source_and_promoted_flags_rejected(self):
        cases = (
            lambda w, p, e: w.update(officialGoingVerified=True),
            lambda w, p, e: w["races"][0].update(bettingReady=True),
            lambda w, p, e: w["races"].append(copy.deepcopy(w["races"][0])),
            lambda w, p, e: p.append(copy.deepcopy(p[0])),
            lambda w, p, e: w.update(date="20261122"),
            lambda w, p, e: p[0].update(racedate="20261122"),
            lambda w, p, e: e[0].update(racekey="08265501"),
            lambda w, p, e: e[0].update(racedate="20261122"),
            lambda w, p, e: w["races"][0].update(race=2),
        )
        for change in cases:
            week, programme, entries = data()
            change(week, programme, entries)
            with self.subTest(change=change), self.assertRaises(CoverageError):
                audit_day_candidate_matches(week, programme, entries, DAY)

    def test_empty_day_cannot_claim_complete(self):
        week, programme, entries = data()
        week["races"] = []
        week["raceCount"] = 0
        report = audit_day_candidate_matches(week, programme, entries, DAY)
        self.assertEqual(report["candidateMatchedRaces"], 0)
        self.assertFalse(report["allCandidatesMatched"])
        self.assertEqual(report["missingJvdataRaces"], 1)


if __name__ == "__main__":
    unittest.main()
