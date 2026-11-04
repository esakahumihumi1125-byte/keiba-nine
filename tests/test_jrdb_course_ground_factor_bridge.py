"""Offline synthetic tests for private course/going evidence factor bridge."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_training_hypothesis import build_training_hints
from jrdb_recent_hypothesis import build_recent_hints
from jrdb_private_factor_bridge import build_private_factor_matrix
from jrdb_going_history import build_going_history_observations
from jrdb_course_ground_factor_bridge import (
    enrich_course_ground_matrix, summarize_course_ground_matrix, VERSION,
)
from test_jrdb_going_history import sample_going


def prepare():
    p, e, previous, past, old, today = sample_going()
    train = build_training_hints(p, e, [], "20261101")
    recent = build_recent_hints(p, e, previous, "20261101")
    base = build_private_factor_matrix(train, recent)
    history = build_going_history_observations(
        p, e, previous, past, old, today, "20261101"
    )
    return base, history


class CourseGroundFactorBridgeTests(unittest.TestCase):
    def test_observed_course_and_going_fill_two_slots_but_no_grade(self):
        base, history = prepare()
        enriched = enrich_course_ground_matrix(base, history, history_complete=True)
        runner = enriched[0]["byNumber"]["01"]
        self.assertEqual(runner["course_distance"]["grade"], "未評価")
        self.assertEqual(runner["course_distance"]["comparableRuns"], 2)
        self.assertEqual(runner["ground"]["knownComparableRuns"], 2)
        self.assertEqual(runner["ground"]["wetComparableRuns"], 2)
        self.assertEqual(runner["ground"]["matchingCurrentGoingRuns"], 1)
        self.assertEqual(runner["ground"]["grade"], "未評価")
        self.assertTrue(runner["ground"]["historyLookupComplete"])
        self.assertEqual(runner["pace"]["grade"], "未評価")
        for k in ("pedigree", "draw_weight", "jockey_stable",
                  "rotation", "body_condition"):
            self.assertEqual(runner[k], {"grade": "未評価", "basis": "not_mapped"})
        self.assertFalse(enriched[0]["predictionReady"])
        self.assertFalse(enriched[0]["bettingReady"])

    def test_only_aggregate_history_reaches_owner_status(self):
        base, history = prepare()
        data = summarize_course_ground_matrix(
            enrich_course_ground_matrix(base, history, history_complete=True)
        )
        self.assertEqual(data["version"], VERSION)
        self.assertEqual(data["raceCount"], 2)
        tokyo, kyoto = data["races"]
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["runnersWithComparableCourse"], 1)
        self.assertEqual(tokyo["runnersWithKnownGoingComparable"], 1)
        self.assertEqual(tokyo["runnersWithWetComparable"], 1)
        self.assertEqual(tokyo["runnersMatchingCurrentGoing"], 1)
        self.assertEqual(tokyo["runnersWithIncompleteHistory"], 0)
        self.assertEqual(tokyo["unmappedFactorCount"], 5)
        self.assertEqual(kyoto["runnerCount"], 1)
        self.assertEqual(kyoto["runnersWithCurrentGoingUnknown"], 1)
        self.assertFalse(tokyo["suitabilityAssessed"])
        self.assertFalse(tokyo["predictionReady"])
        self.assertFalse(data["bettingReady"])
        for secret in ("racekey", "byNumber", "horse_number", "horse_id",
                       "PRIVATE-HORSE", "PAID-SECRET", "LICENSED-PAST",
                       "05264a01", "01"):
            self.assertNotIn(secret, repr(data))

    def test_missing_current_going_stays_unknown(self):
        p, e, prev, history, old, _ = sample_going()
        base, _ = prepare()
        observed = build_going_history_observations(
            p, e, prev, history, old, [], "20261101"
        )
        enriched = enrich_course_ground_matrix(base, observed, history_complete=True)
        first = enriched[0]["byNumber"]["01"]["ground"]
        self.assertFalse(first["currentGoingRecorded"])
        self.assertEqual(first["matchingCurrentGoingRuns"], 0)
        self.assertEqual(first["grade"], "未評価")

    def test_missing_historical_conditions_is_not_bad_aptitude(self):
        p, e, prev, history, _, today = sample_going()
        base, _ = prepare()
        observed = build_going_history_observations(
            p, e, prev, history, [], today, "20261101"
        )
        enriched = enrich_course_ground_matrix(base, observed, history_complete=False)
        first = enriched[0]["byNumber"]["01"]
        self.assertEqual(first["course_distance"]["comparableRuns"], 2)
        self.assertEqual(first["ground"]["knownComparableRuns"], 0)
        self.assertEqual(first["ground"]["unknownComparableRuns"], 2)
        self.assertFalse(first["ground"]["historyLookupComplete"])
        report = summarize_course_ground_matrix(enriched)["races"][0]
        self.assertEqual(report["runnersWithKnownGoingComparable"], 0)
        self.assertEqual(report["unknownComparableGoingRuns"], 2)
        self.assertEqual(report["runnersWithIncompleteHistory"], 2)

    def test_mismatched_horse_and_race_rejected(self):
        for change in ("horse", "race", "missing_race", "duplicate"):
            base, history = prepare()
            if change == "horse":
                history[0]["byNumber"]["03"] = history[0]["byNumber"].pop("02")
            elif change == "race":
                history[0]["track"] = "函館"
            elif change == "missing_race":
                history.pop()
            else:
                history.append(copy.deepcopy(history[0]))
            with self.subTest(change=change), self.assertRaises(CoverageError):
                enrich_course_ground_matrix(base, history, history_complete=True)

    def test_invalid_history_counts_fail_closed(self):
        for field, value in (("datedRuns", 6),
                             ("knownGoingComparableRuns", 3),
                             ("missingPastProgrammes", -1),
                             ("heavyComparableRuns", 3),
                             ("sameCurrentGoingComparableRuns", 3),
                             ("unknownGoingComparableRuns", True)):
            base, history = prepare()
            history[0]["byNumber"]["01"][field] = value
            with self.subTest(field=field), self.assertRaises(CoverageError):
                enrich_course_ground_matrix(base, history, history_complete=True)

    def test_grading_ground_or_course_fails_closed(self):
        base, history = prepare()
        matrix = enrich_course_ground_matrix(base, history, history_complete=True)
        for factor in ("ground", "course_distance", "pace"):
            corrupted = copy.deepcopy(matrix)
            corrupted[0]["byNumber"]["01"][factor]["grade"] = "S"
            with self.subTest(factor=factor), self.assertRaises(CoverageError):
                summarize_course_ground_matrix(corrupted)

    def test_can_never_claim_authorized_official_or_betting_status(self):
        base, history = prepare()
        matrix = enrich_course_ground_matrix(base, history, history_complete=True)
        for name in ("independentJraVerified", "predictionReady", "bettingReady"):
            bad = copy.deepcopy(matrix)
            bad[0][name] = True
            with self.subTest(name=name), self.assertRaises(CoverageError):
                summarize_course_ground_matrix(bad)
        for flag in (True, "true", 1, None):
            if flag is True:
                continue
            with self.subTest(flag=flag), self.assertRaises(CoverageError):
                enrich_course_ground_matrix(base, history, history_complete=flag)

    def test_does_not_mutate_paid_rows_or_existing_factor_matrix(self):
        base, observed = prepare()
        originals = copy.deepcopy((base, observed))
        summary = summarize_course_ground_matrix(
            enrich_course_ground_matrix(base, observed, history_complete=True)
        )
        self.assertEqual((base, observed), originals)
        self.assertNotIn("byNumber", repr(summary))
        self.assertEqual(base[0]["byNumber"]["01"]["ground"],
                         {"grade": "未評価", "basis": "not_mapped"})


if __name__ == "__main__":
    unittest.main()
