"""Synthetic, credential-free regression for publication-time AS-OF evidence."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_three_factor_asof_audit import (
    VERSION, study_three_factor_asof
)


def target():
    return {
        "raceDate": "2026-11-14", "track": "京都", "race": 1,
        "capturedAt": "2026-11-13T20:00:00+09:00",
        "scheduledOffAt": "2026-11-14T10:00:00+09:00",
        "surface": "芝", "distanceM": 1600, "going": "良",
        "runners": [{"number": 1, "horseRef": "HORSE_A_private"},
                    {"number": 6, "horseRef": "HORSE_B_private"}],
    }


def past(day, *, horse="HORSE_A_private", race=3, track="京都",
         surface="芝", dist=1600, going="良", fourth=2,
         published=None, field_size=12):
    off = f"{day}T12:30:00+09:00"
    if published is None:
        published = f"{day}T14:00:00+09:00"
    return {
        "horseRef": horse, "raceDate": day, "track": track, "race": race,
        "scheduledOffAt": off, "resultAvailableAt": published,
        "surface": surface, "distanceM": dist, "going": going,
        "fieldSize": field_size, "fourthCorner": fourth,
    }


class ThreeFactorAsOfAuditTests(unittest.TestCase):
    def test_prior_publication_samples_only_research_never_grades(self):
        history = [past(day) for day in (
            "2026-10-10", "2026-10-17", "2026-10-24"
        )]
        original = copy.deepcopy((target(), history))
        out = study_three_factor_asof(target(), history)
        self.assertEqual((target(), history), original)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(out["weightTotal"], 46)
        self.assertEqual(out["factorWeights"], {
            "course_distance": 17, "pace": 17, "ground": 12
        })
        self.assertEqual(out["runnerCount"], 2)
        self.assertEqual(out["summary"]["timestampEligibleRuns"], 3)
        self.assertEqual(out["summary"]["allThreeMinimumStudySamples"], 1)
        runner = out["runners"][0]
        self.assertEqual(runner["number"], 1)
        self.assertEqual(runner["counts"]["comparableCourseRuns"], 3)
        self.assertEqual(runner["counts"]["matchingCurrentGoingRuns"], 3)
        self.assertTrue(runner["allThreeMinimumStudySamples"])
        self.assertEqual(out["runners"][1]["number"], 6)
        self.assertFalse(out["runners"][1]["allThreeMinimumStudySamples"])
        for name in ("publicationTimestampAuthenticityVerified",
                     "historicalResultPublicationTimesVerified",
                     "independentTimeCutVerified",
                     "independentSourceFamiliesVerified",
                     "officialJraVerified", "conditionMatchedHoldoutValidated",
                     "factorRubricsCalibrated", "overallPredictionReady",
                     "bettingReady", "changesExistingTickets",
                     "changesExistingRoi"):
            self.assertFalse(out[name], name)
        self.assertEqual(out["formalGradesVerified"], 0)
        self.assertIsNone(runner["score46"])
        self.assertFalse(runner["winnerPickReady"])
        for secret in ("HORSE_A_private", "HORSE_B_private",
                       "2026-10-10", "2026-11-13T20:00",
                       "resultAvailableAt", "scheduledOffAt", "horseRef"):
            self.assertNotIn(secret, repr(out))

    def test_delayed_and_unknown_result_are_not_proof(self):
        history = [
            past("2026-10-10"),
            past("2026-10-17", published=None),
            past("2026-10-24", published="2026-11-13T20:00:00+09:00"),
            past("2026-10-31", published="2026-11-13T21:00:00+09:00"),
        ]
        # Explicitly null indicates that the original publication time
        # is unknown; don't synthesize one from the race date.
        history[1]["resultAvailableAt"] = None
        out = study_three_factor_asof(target(), history)
        c = out["runners"][0]["counts"]
        self.assertEqual(c["historicalRowsProvided"], 4)
        self.assertEqual(c["timestampEligibleRuns"], 1)
        self.assertEqual(c["publicationTimestampMissing"], 1)
        self.assertEqual(c["excludedAtOrAfterCapture"], 2)
        self.assertEqual(c["comparableCourseRuns"], 1)
        self.assertFalse(out["runners"][0]["allThreeMinimumStudySamples"])
        self.assertIn("result_publication_unknown", out["runners"][0]["gaps"])
        self.assertIn("future_information_quarantined", out["runners"][0]["gaps"])

    def test_different_offset_same_instant_never_leaks(self):
        history = [past("2026-10-24",
                        published="2026-11-13T11:00:00Z")]
        out = study_three_factor_asof(target(), history)
        self.assertEqual(out["summary"]["timestampEligibleRuns"], 0)
        history[0]["resultAvailableAt"] = "2026-11-13T10:59:59Z"
        out = study_three_factor_asof(target(), history)
        self.assertEqual(out["summary"]["timestampEligibleRuns"], 1)

    def test_same_day_and_future_are_conservatively_excluded(self):
        history = [
            past("2026-11-14", published="2026-11-14T14:00:00+09:00"),
            past("2026-11-15", published="2026-11-15T14:00:00+09:00"),
        ]
        out = study_three_factor_asof(target(), history)
        self.assertEqual(out["summary"]["timestampEligibleRuns"], 0)
        self.assertEqual(out["summary"]["excludedSameDayOrFuture"], 2)

    def test_only_exact_course_and_going_bands_count(self):
        history = [
            past("2026-10-10", dist=1800),  # exact +/- 200 allowed
            past("2026-10-17", dist=1801),  # outside comparable window
            past("2026-10-24", going="稍重"),
            past("2026-10-31", track="東京"),
        ]
        out = study_three_factor_asof(target(), history)
        c = out["runners"][0]["counts"]
        self.assertEqual(c["timestampEligibleRuns"], 4)
        self.assertEqual(c["comparableCourseRuns"], 2)
        self.assertEqual(c["matchingCurrentGoingRuns"], 1)
        self.assertEqual(c["pastFourthCornerObserved"], 4)
        self.assertFalse(out["runners"][0]["minimumStudySamples"]["ground"])
        self.assertFalse(out["runners"][0]["allThreeMinimumStudySamples"])

    def test_one_horse_cannot_race_twice_same_day_or_six_times(self):
        a = past("2026-10-10")
        b = past("2026-10-10", race=4)
        with self.assertRaises(CoverageError):
            study_three_factor_asof(target(), [a, b])
        records = [past(f"2026-10-{i:02d}") for i in range(10, 16)]
        with self.assertRaises(CoverageError):
            study_three_factor_asof(target(), records)

    def test_conflicting_context_for_one_old_race_rejected(self):
        a = past("2026-10-10", horse="HORSE_A_private")
        b = past("2026-10-10", horse="HORSE_B_private", dist=1800)
        with self.assertRaises(CoverageError):
            study_three_factor_asof(target(), [a, b])

    def test_malformed_dates_or_times_never_promoted(self):
        for mutation in (
            lambda r: r.update(resultAvailableAt="2026-10-10T10:00:00+09:00"),
            lambda r: r.update(resultAvailableAt="2026-10-10T14:00:00"),
            lambda r: r.update(scheduledOffAt="2026-10-09T12:30:00+09:00"),
            lambda r: r.update(raceDate="2026-02-30"),
            lambda r: r.update(fourthCorner=19),
            lambda r: r.update(fourthCorner=True),
            lambda r: r.update(horseRef="UNKNOWN_HORSE"),
            lambda r: r.update(privateKey="secret"),
        ):
            row = past("2026-10-10")
            mutation(row)
            with self.subTest(row=str(row)[:70]), self.assertRaises(CoverageError):
                study_three_factor_asof(target(), [row])

    def test_target_snapshot_or_roster_tampering_rejected(self):
        for mutation in (
            lambda t: t.update(capturedAt="2026-11-14T10:00:00+09:00"),
            lambda t: t.update(capturedAt="2026-11-01T10:00:00+09:00"),
            lambda t: t.update(capturedAt="2026-11-13T20:00:00"),
            lambda t: t["runners"][1].update(number=1),
            lambda t: t["runners"][1].update(horseRef="HORSE_A_private"),
            lambda t: t.update(raceDate="2026-11-15"),
            lambda t: t.update(untrustedOfficialVerified=True),
        ):
            item = target()
            mutation(item)
            with self.assertRaises(CoverageError):
                study_three_factor_asof(item, [])

    def test_missing_current_going_is_not_bad_ground_grade(self):
        item = target()
        item["going"] = None
        out = study_three_factor_asof(item, [
            past("2026-10-10"), past("2026-10-17"), past("2026-10-24")
        ])
        horse = out["runners"][0]
        self.assertTrue(horse["minimumStudySamples"]["course_distance"])
        self.assertFalse(horse["minimumStudySamples"]["ground"])
        self.assertIn("going_eligible_sample_below_three", horse["gaps"])
        self.assertEqual(out["formalGradesVerified"], 0)


if __name__ == "__main__":
    unittest.main()
