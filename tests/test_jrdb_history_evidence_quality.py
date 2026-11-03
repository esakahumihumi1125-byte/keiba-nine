"""Synthetic-only coverage tests; never require a provider connection."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_going_history import build_going_history_observations
from jrdb_history_evidence_quality import summarize_history_evidence_quality
from test_jrdb_going_history import sample_going


def sample():
    p, e, z, history, going, current = sample_going()
    return build_going_history_observations(
        p, e, z, history, going, current, "20261101"
    )


class HistoricalEvidenceQualityTests(unittest.TestCase):
    def test_course_and_known_going_samples_are_headcounts_not_grades(self):
        result = summarize_history_evidence_quality(sample())
        by_track = {row["track"]: row for row in result["races"]}
        tokyo = by_track["東京"]
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["datedPastRuns"], 3)
        self.assertEqual(tokyo["linkedPastRuns"], 3)
        self.assertEqual(tokyo["unlinkedPastRuns"], 0)
        self.assertEqual(tokyo["runnersWithRecordedPast"], 2)
        self.assertEqual(tokyo["runnersWithMissingPast"], 0)
        self.assertEqual(tokyo["courseComparableSamples"],
                         {"none": 1, "oneOrTwo": 1, "threePlus": 0})
        self.assertEqual(tokyo["knownGoingComparableSamples"],
                         {"none": 1, "oneOrTwo": 1, "threePlus": 0})
        self.assertEqual(tokyo["materialStatus"], "番組履歴は照合")
        kyoto = by_track["京都"]
        self.assertEqual(kyoto["runnersNoRecordedPast"], 1)
        self.assertEqual(kyoto["materialStatus"], "該当記録なし")
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["suitabilityAssessed"])
        self.assertFalse(result["predictionConfidenceAssessed"])

    def test_missed_programmes_and_missing_going_do_not_boost_coverage(self):
        a = sample()
        a[0]["byNumber"]["01"]["linkedPastProgrammes"] = 1
        a[0]["byNumber"]["01"]["missingPastProgrammes"] = 1
        a[0]["byNumber"]["01"]["sameSurfaceRuns"] = 1
        a[0]["byNumber"]["01"]["sameSurfaceNearDistanceRuns"] = 1
        a[0]["byNumber"]["01"]["sameSurfaceKnownGoingRuns"] = 0
        a[0]["byNumber"]["01"]["sameSurfaceUnknownGoingRuns"] = 1
        a[0]["byNumber"]["01"]["knownGoingComparableRuns"] = 0
        a[0]["byNumber"]["01"]["unknownGoingComparableRuns"] = 1
        a[0]["byNumber"]["01"]["heavyComparableRuns"] = 0
        a[0]["byNumber"]["01"]["poorComparableRuns"] = 0
        a[0]["byNumber"]["01"]["heavyTopThreeRuns"] = 0
        a[0]["byNumber"]["01"]["poorTopThreeRuns"] = 0
        a[0]["byNumber"]["01"]["sameCurrentGoingComparableRuns"] = 0
        report = summarize_history_evidence_quality(a)
        tokyo = next(x for x in report["races"] if x["track"] == "東京")
        self.assertEqual(tokyo["runnersWithMissingPast"], 1)
        self.assertEqual(tokyo["materialStatus"], "未照合あり")
        self.assertEqual(tokyo["unlinkedPastRuns"], 1)
        self.assertEqual(tokyo["knownGoingComparableSamples"]["none"], 2)

    def test_three_or_more_comparisons_are_not_rank_s_or_a(self):
        a = sample()
        h = a[0]["byNumber"]["01"]
        h.update(datedRuns=3, linkedPastProgrammes=3, missingPastProgrammes=0,
                 sameSurfaceRuns=3, sameSurfaceNearDistanceRuns=3,
                 sameSurfaceKnownGoingRuns=3, sameSurfaceUnknownGoingRuns=0,
                 knownGoingComparableRuns=3, unknownGoingComparableRuns=0,
                 sameCurrentGoingComparableRuns=2,
                 heavyComparableRuns=2, poorComparableRuns=1,
                 heavyTopThreeRuns=1, poorTopThreeRuns=0)
        result = summarize_history_evidence_quality(a)
        tokyo = next(x for x in result["races"] if x["track"] == "東京")
        self.assertEqual(tokyo["courseComparableSamples"]["threePlus"], 1)
        self.assertEqual(tokyo["knownGoingComparableSamples"]["threePlus"], 1)
        for forbidden in ("grade", "S", "winProbability", "horse_number", "racekey"):
            self.assertNotIn('"' + forbidden + '"', repr(result))
        self.assertFalse(tokyo["suitabilityAssessed"])

    def test_five_run_max_and_inconsistent_counts_rejected(self):
        for field, value in (("datedRuns", 6),
                             ("linkedPastProgrammes", 4),
                             ("knownGoingComparableRuns", 4),
                             ("sameSurfaceRuns", 4),
                             ("poorTopThreeRuns", 9),
                             ("missingPastProgrammes", -1),
                             ("knownGoingComparableRuns", True)):
            x = sample()
            x[0]["byNumber"]["01"][field] = value
            with self.subTest(field=field), self.assertRaises(CoverageError):
                summarize_history_evidence_quality(x)

    def test_invalid_current_going_or_duplicate_race_rejected(self):
        x = sample()
        x[0]["currentGoingRecorded"] = "true"
        with self.assertRaises(CoverageError):
            summarize_history_evidence_quality(x)
        x = sample()
        x.append(copy.deepcopy(x[0]))
        with self.assertRaises(CoverageError):
            summarize_history_evidence_quality(x)

    def test_no_horse_identifiers_or_paid_content_leave_summary(self):
        x = sample()
        output = summarize_history_evidence_quality(x)
        for secret in ("horse_id", "horse_number", "byNumber",
                       "racekey", "05264a01", "PRIVATE-HORSE",
                       "LICENSED-PAST", "PAID-SECRET"):
            self.assertNotIn(secret, repr(output))

    def test_input_is_not_modified(self):
        x = sample()
        before = copy.deepcopy(x)
        summarize_history_evidence_quality(x)
        self.assertEqual(x, before)


if __name__ == "__main__":
    unittest.main()
