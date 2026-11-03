"""Synthetic private materials report checks; no JRDB/API/real races."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_evidence_readiness import audit_evidence_coverage
from jrdb_going_history import build_going_history_observations
from jrdb_history_evidence_quality import summarize_history_evidence_quality
from jrdb_ten_factor_materials import combine_ten_factor_materials
from test_jrdb_going_history import sample_going
from test_jrdb_evidence_readiness import sample


def materials():
    p, e, prev, past, old_going, now = sample_going()
    _, _, training, _ = sample()
    evidence = audit_evidence_coverage(p, e, training, prev, "20261101")
    observations = build_going_history_observations(
        p, e, prev, past, old_going, now, "20261101"
    )
    return evidence, summarize_history_evidence_quality(observations)


class TenFactorMaterialsTests(unittest.TestCase):
    def test_coarse_observation_counts_not_grades(self):
        evidence, history = materials()
        result = combine_ten_factor_materials(
            evidence, history, bounded_history_complete=True
        )
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["factorCount"], 10)
        tokyo = next(r for r in result["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["observedFactorCount"], 4)
        self.assertEqual(tokyo["factors"]["training"]["observedRunnerCount"], 2)
        self.assertEqual(tokyo["factors"]["recent"]["observedRunnerCount"], 2)
        self.assertEqual(tokyo["factors"]["course_distance"]["observedRunnerCount"], 1)
        self.assertEqual(tokyo["factors"]["ground"]["observedRunnerCount"], 1)
        self.assertEqual(tokyo["factors"]["training"]["sourceStatus"],
                         "observed_record_count_matches")
        self.assertEqual(tokyo["factors"]["ground"]["sourceStatus"],
                         "partial_observed_records")
        self.assertFalse(tokyo["bettingReady"])
        self.assertFalse(tokyo["predictionReady"])
        self.assertEqual(tokyo["gradedFactors"], 0)
        self.assertTrue(all(x["grade"] == "未評価"
                            and x["assessmentComplete"] is False
                            for x in tokyo["factors"].values()))
        self.assertEqual(sum(v["sourceStatus"] == "not_mapped_from_provider"
                             for v in tokyo["factors"].values()), 6)

    def test_unknown_race_conditions_and_no_past_are_not_negative_grades(self):
        evidence, history = materials()
        result = combine_ten_factor_materials(
            evidence, history, bounded_history_complete=True
        )
        kyoto = next(r for r in result["races"] if r["track"] == "京都")
        self.assertEqual(kyoto["observedFactorCount"], 0)
        self.assertEqual(kyoto["factors"]["ground"]["sourceStatus"],
                         "current_going_unverified")
        self.assertEqual(kyoto["factors"]["course_distance"]["sourceStatus"],
                         "no_comparable_records_observed")
        self.assertFalse(kyoto["scratchesVerified"])
        self.assertFalse(kyoto["predictionConfidenceAssessed"])

    def test_partial_bounded_history_never_reports_full_coverage(self):
        evidence, history = materials()
        report = combine_ten_factor_materials(
            evidence, history, bounded_history_complete=False
        )
        tokyo = next(r for r in report["races"] if r["track"] == "東京")
        self.assertTrue(tokyo["pastLookupIncomplete"])
        self.assertEqual(tokyo["factors"]["course_distance"]["sourceStatus"],
                         "historical_lookup_incomplete")
        self.assertEqual(tokyo["factors"]["ground"]["sourceStatus"],
                         "historical_lookup_incomplete")
        self.assertFalse(tokyo["bettingReady"])
        self.assertEqual(tokyo["factors"]["course_distance"]["observedRunnerCount"], 1)

    def test_unlinked_past_runs_flag_incompleteness(self):
        evidence, history = materials()
        history["races"][0]["unlinkedPastRuns"] = 1
        report = combine_ten_factor_materials(
            evidence, history, bounded_history_complete=True
        )
        tokyo = next(r for r in report["races"] if r["track"] == "東京")
        self.assertTrue(tokyo["pastLookupIncomplete"])

    def test_mismatched_race_roster_and_duplicate_rejected(self):
        for modify in ("missing", "extra", "runner", "track", "duplicate"):
            evidence, history = materials()
            if modify == "missing":
                history["races"].pop()
                history["raceCount"] -= 1
            elif modify == "extra":
                history["races"].append(copy.deepcopy(history["races"][0]))
                history["raceCount"] += 1
            elif modify == "runner":
                history["races"][0]["runnerCount"] = 18
            elif modify == "track":
                history["races"][0]["track"] = "函館"
            else:
                history["races"][1]["track"] = history["races"][0]["track"]
                history["races"][1]["race"] = history["races"][0]["race"]
            with self.subTest(modify=modify), self.assertRaises(ValueError):
                combine_ten_factor_materials(
                    evidence, history, bounded_history_complete=True
                )

    def test_invalid_sample_buckets_or_disallowed_status_rejected(self):
        for field, value in (("none", -1), ("oneOrTwo", True), ("threePlus", 99)):
            evidence, history = materials()
            history["races"][0]["courseComparableSamples"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                combine_ten_factor_materials(
                    evidence, history, bounded_history_complete=True
                )
        evidence, history = materials()
        history["races"][0]["predictionReady"] = True
        with self.assertRaises(ValueError):
            combine_ten_factor_materials(
                evidence, history, bounded_history_complete=True
            )

    def test_output_has_no_horse_records_or_private_keys(self):
        evidence, history = materials()
        evidence["races"][0]["extraSecret"] = "PRIVATE-JRDB-HORSE"
        history["races"][0]["extraSecret"] = "LICENSED-KEY"
        result = combine_ten_factor_materials(
            evidence, history, bounded_history_complete=True
        )
        for secret in ("PRIVATE-JRDB-HORSE", "LICENSED-KEY", "horse_number",
                       "horse_id", "racekey", "05264a01", "byNumber"):
            self.assertNotIn(secret, repr(result))

    def test_inputs_unchanged(self):
        evidence, history = materials()
        source = copy.deepcopy((evidence, history))
        combine_ten_factor_materials(
            evidence, history, bounded_history_complete=False
        )
        self.assertEqual((evidence, history), source)


if __name__ == "__main__":
    unittest.main()
