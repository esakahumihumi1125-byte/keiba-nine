"""Offline-only bounded history audit tests; no real JRDB credentials."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_history_pipeline import (
    plan_bounded_history, run_bounded_history_audit, HistoryFetchError
)
from test_jrdb_going_history import sample_going


def context():
    programme, entries, previous, past, going, current = sample_going()
    dra = Mock(side_effect=lambda key: [copy.deepcopy(x) for x in past
                                       if x["racekey"] == key])
    dka = Mock(side_effect=lambda key: [copy.deepcopy(x) for x in going
                                       if x["holdingkey"] == key[:6]])
    return programme, entries, previous, current, dra, dka


def run_case(bundle, **kwargs):
    programme, entries, previous, current, dra, dka = bundle
    return run_bounded_history_audit(
        programme, entries, previous, current, "20261101",
        fetch_dra=dra, fetch_dka=dka, **kwargs
    )


class BoundedHistoryTests(unittest.TestCase):
    def test_unique_racekeys_and_one_dka_per_holding(self):
        bundle = context()
        report = run_case(bundle)
        self.assertEqual(report["referencedPastRaces"], 3)
        self.assertEqual(report["selectedPastRaces"], 3)
        self.assertEqual(report["deferredPastRaces"], 0)
        self.assertEqual(report["draCalls"], 3)
        self.assertEqual(report["dkaCalls"], 2)
        self.assertEqual(bundle[4].call_count, 3)
        self.assertEqual(bundle[5].call_count, 2)
        self.assertEqual(report["goingSummary"]["races"][0]["heavyComparableRuns"], 1)
        self.assertEqual(report["goingSummary"]["races"][0]["poorComparableRuns"], 1)
        tokyo = next(x for x in report["evidenceQuality"]["races"]
                     if x["track"] == "東京")
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["courseComparableSamples"],
                         {"none": 1, "oneOrTwo": 1, "threePlus": 0})
        self.assertEqual(tokyo["knownGoingComparableSamples"]["oneOrTwo"], 1)
        self.assertEqual(tokyo["materialStatus"], "番組履歴は照合")
        self.assertFalse(report["evidenceQuality"]["predictionConfidenceAssessed"])
        self.assertFalse(report["predictionReady"])
        self.assertFalse(report["goingSuitabilityAssessed"])

    def test_limit_one_defers_remaining_and_does_not_infer_failure(self):
        bundle = context()
        report = run_case(bundle, limit=1)
        self.assertEqual(report["selectedPastRaces"], 1)
        self.assertEqual(report["deferredPastRaces"], 2)
        self.assertEqual(report["draCalls"], 1)
        self.assertLessEqual(report["dkaCalls"], 1)
        self.assertFalse(report["historyComplete"])
        quality = next(x for x in report["evidenceQuality"]["races"]
                       if x["track"] == "東京")
        self.assertEqual(quality["runnersWithMissingPast"], 1)
        self.assertEqual(quality["materialStatus"], "未照合あり")
        self.assertEqual(report["goingSummary"]["races"][0]["knownComparableRuns"], 0)
        self.assertFalse(report["predictionReady"])

    def test_deduplicated_plan_newest_races_first(self):
        bundle = context()
        p, e, z, _, _, _ = bundle
        result = plan_bounded_history(p, e, z, "20261101")
        self.assertEqual(result["referencedCount"], 3)
        self.assertEqual(result["selectedCount"], 3)
        self.assertEqual(result["privateSelected"][-1][1], "20260920")
        self.assertEqual({x[0] for x in result["privateSelected"]},
                         {"05264a01", "05264a02", "05264903"})

    def test_missing_dra_remains_unavailable_without_dka_call(self):
        bundle = context()
        bundle[4].side_effect = lambda _: []
        output = run_case(bundle)
        self.assertEqual(output["draCalls"], 3)
        self.assertEqual(output["dkaCalls"], 0)
        self.assertEqual(output["unavailablePastProgrammes"], 3)
        self.assertEqual(output["goingSummary"]["races"][0]["knownComparableRuns"], 0)
        self.assertFalse(output["historyComplete"])

    def test_missing_dka_is_unknown(self):
        bundle = context()
        bundle[5].side_effect = lambda _: []
        output = run_case(bundle)
        self.assertEqual(output["goingSummary"]["races"][0]["knownComparableRuns"], 0)
        self.assertEqual(output["goingSummary"]["races"][0]["unknownComparableRuns"], 2)
        self.assertFalse(output["predictionReady"])
        self.assertEqual(output["unavailablePastConditions"], 2)
        self.assertFalse(output["historyComplete"])

    def test_no_past_keys_never_calls_private_provider(self):
        bundle = context()
        p, e, z, curr, _, _ = bundle
        for row in z:
            for i in range(1, 6):
                row.pop(f"race_back_{i}_racekey", None)
        output = run_case(bundle)
        self.assertEqual(output["selectedPastRaces"], 0)
        self.assertEqual(output["draCalls"], 0)
        self.assertEqual(output["dkaCalls"], 0)
        self.assertEqual(output["unkeyedPreviousRuns"], 3)
        self.assertFalse(output["historyComplete"])

    def test_limit_hard_cap_twelve_even_with_many_distinct_races(self):
        bundle = context()
        p, e, z, *_ = bundle
        # Three identified runners, five different past races per runner.
        template = [
            ("05264a", 1), ("052649", 1), ("08264a", 1)
        ]
        z.clear()
        for idx, (prefix, start) in enumerate(template):
            runner = e[idx]
            row = {
                "racekey": runner["racekey"],
                "racedate": "20261101",
                "horse_number": runner["horse_number"],
                "horse_id": runner["horse_id"],
            }
            for past_no in range(1, 6):
                row[f"race_back_{past_no}_racedate"] = "20261004"
                row[f"race_back_{past_no}_racekey"] = prefix + f"{start + past_no - 1:02d}"
            z.append(row)
        plan = plan_bounded_history(p, e, z, "20261101", limit=12)
        self.assertEqual(plan["referencedCount"], 15)
        self.assertEqual(plan["selectedCount"], 12)
        self.assertEqual(plan["deferredCount"], 3)
        self.assertEqual(plan["maxDraCalls"], 12)
        self.assertEqual(plan["maxDkaCalls"], 12)

    def test_invalid_current_going_prevents_all_historical_calls(self):
        bundle = context()
        bundle[3][0]["racedate"] = "20261102"
        with self.assertRaises(HistoryFetchError):
            run_case(bundle)
        bundle[4].assert_not_called()
        bundle[5].assert_not_called()

    def test_unsupported_limits_rejected_before_network(self):
        for limit in (0, 13, 2.0, "12", True, -1):
            bundle = context()
            with self.subTest(limit=limit), self.assertRaises(HistoryFetchError):
                run_case(bundle, limit=limit)
            bundle[4].assert_not_called()
            bundle[5].assert_not_called()

    def test_unmatched_date_key_rejected_without_network(self):
        bundle = context()
        bundle[2][0]["race_back_2_racedate"] = "20261104"
        with self.assertRaises(CoverageError):
            run_case(bundle)
        bundle[4].assert_not_called()

    def test_conflicting_prior_race_date_is_rejected(self):
        bundle = context()
        bundle[2][0]["race_back_2_racekey"] = "05264a01"
        with self.assertRaises(CoverageError):
            run_case(bundle)
        bundle[4].assert_not_called()

    def test_wrong_dra_identity_aborts_without_dka(self):
        bundle = context()
        bundle[4].side_effect = lambda _: [{
            "racekey": "0526aa01", "racedate": "20261004",
            "track_type": "1", "distance": "1600", "turn_cd": "2"
        }]
        with self.assertRaises(HistoryFetchError):
            run_case(bundle)
        bundle[5].assert_not_called()

    def test_wrong_dka_date_aborts(self):
        bundle = context()
        bundle[5].side_effect = lambda _: [{
            "holdingkey": "05264a", "racedate": "20261005",
            "turf_condition_cd": "03"
        }]
        with self.assertRaises(HistoryFetchError):
            run_case(bundle)

    def test_duplicate_rows_from_provider_are_not_silently_merged(self):
        for source in (4, 5):
            bundle = context()
            if source == 4:
                valid = {"racekey": "05264a02", "racedate": "20261004"}
            else:
                valid = {"holdingkey": "05264a", "racedate": "20261004"}
            bundle[source].side_effect = lambda _: [valid, valid]
            with self.subTest(source=source), self.assertRaises(HistoryFetchError):
                run_case(bundle)

    def test_internal_errors_do_not_copy_provider_secrets(self):
        for source in (4, 5):
            bundle = context()
            bundle[source].side_effect = RuntimeError("API_KEY=PRIVATE_SECRET_AND_RESULTS")
            with self.subTest(source=source), self.assertRaises(HistoryFetchError) as cm:
                run_case(bundle)
            self.assertNotIn("PRIVATE_SECRET", str(cm.exception))

    def test_return_never_contains_raw_racekeys_or_horses(self):
        report = run_case(context())
        for secret in ("racekey", "byNumber", "horse_id", "horse_number",
                       "05264a01", "PRIVATE-HORSE", "PAID-SECRET"):
            self.assertNotIn(secret, repr(report))

    def test_source_inputs_unchanged(self):
        bundle = context()
        originals = copy.deepcopy(bundle[:4])
        run_case(bundle)
        self.assertEqual(originals, bundle[:4])


if __name__ == "__main__":
    unittest.main()
