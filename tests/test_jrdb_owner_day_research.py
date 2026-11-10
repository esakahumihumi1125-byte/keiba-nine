"""Four-read one-day owner research tests using synthetic beta-shaped data."""
import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_owner_day_research import owner_day_research
from test_jrdb_training_hypothesis import setup as workout_fixture
from test_jrdb_recent_hypothesis import fixture as recent_fixture


def sample():
    programme, entries, workouts = workout_fixture()
    _, _, recent = recent_fixture()
    return programme, entries, workouts, recent, "20261101"


class OwnerDayResearchTests(unittest.TestCase):
    def test_two_races_stay_private_research_only(self):
        inputs = sample()
        frozen = copy.deepcopy(inputs)
        data = owner_day_research(*inputs)
        self.assertEqual(data["raceCount"], 2)
        self.assertEqual(data["researchAvailableCount"], 2)
        self.assertEqual(data["needsReviewCount"], 0)
        self.assertEqual(data["sourceReadCount"], 4)
        self.assertTrue(data["privateOwnerOnly"])
        self.assertFalse(data["overallRankReady"])
        self.assertFalse(data["predictionReady"])
        self.assertFalse(data["bettingReady"])
        tokyo, kyoto = data["races"]
        self.assertEqual((tokyo["track"], tokyo["race"]), ("東京", 1))
        self.assertEqual(tokyo["research"]["runnerCount"], 2)
        self.assertEqual(tokyo["research"]["completeTwoFactorCount"], 2)
        self.assertEqual(kyoto["research"]["runnerCount"], 1)
        self.assertEqual(kyoto["research"]["completeTwoFactorCount"], 0)
        self.assertIsNone(kyoto["research"]["runners"][0]["researchOrder"])
        for secret in ("horse_id", "racekey", "byNumber", "oikirisisu",
                       "siagarisisu", "idm", "horse_name", "private_metric"):
            self.assertNotIn(secret, repr(data))
        self.assertEqual(inputs, frozen)

    def test_unrelated_race_failure_does_not_spoil_other_race(self):
        p, e, t, z, date = sample()
        e[-1]["racedate"] = "20261102"  # only Kyoto is inconsistent
        result = owner_day_research(p, e, t, z, date)
        self.assertEqual(result["raceCount"], 2)
        self.assertEqual(result["researchAvailableCount"], 1)
        self.assertEqual(result["needsReviewCount"], 1)
        self.assertEqual(result["races"][0]["status"], "research_only")
        self.assertEqual(result["races"][1]["status"], "needs_review")
        self.assertIsNone(result["races"][1]["research"])
        self.assertEqual(result["races"][1]["reviewStage"], "entries")
        self.assertFalse(result["predictionReady"])

    def test_private_fixed_stage_codes_isolate_a_bad_source(self):
        for stage in ("entries", "training", "recent", "runner_join"):
            with self.subTest(stage=stage):
                p, e, t, z, date = sample()
                if stage == "entries":
                    e[-1]["racedate"] = "20261102"
                if stage == "training":
                    # A bad training grade in Kyoto; no source strings leak.
                    t[-1]["oikirisisu"] = "PRIVATE-RAW-WORKOUT"
                if stage == "recent":
                    z.append(copy.deepcopy(z[0]))
                if stage == "runner_join":
                    import jrdb_owner_day_research as module
                    original = module.owner_runner_research

                    def join(*args):
                        if args[2:] == ("京都", 1):
                            raise CoverageError("PRIVATE-RAW-ERROR-DO-NOT-LEAK")
                        return original(*args)

                if stage == "runner_join":
                    with patch("jrdb_owner_day_research.owner_runner_research",
                               side_effect=join):
                        report = owner_day_research(p, e, t, z, date)
                else:
                    report = owner_day_research(p, e, t, z, date)
                failed = [row for row in report["races"]
                          if row["status"] == "needs_review"]
                self.assertEqual(len(failed), 1)
                # Duplicate recent for Tokyo is a Tokyo-only failure.
                self.assertEqual(failed[0]["track"],
                                 "東京" if stage == "recent" else "京都")
                self.assertEqual(failed[0]["reviewStage"], stage)
                self.assertIsNone(failed[0]["research"])
                self.assertEqual(report["researchAvailableCount"], 1)
                self.assertNotIn("PRIVATE-RAW", repr(report))
                self.assertNotIn("racekey", repr(report))
                self.assertNotIn("horse_id", repr(report))

    def test_empty_non_racing_date_is_not_misidentified_as_failure(self):
        result = owner_day_research([], [], [], [], "20261102")
        self.assertEqual(result["raceCount"], 0)
        self.assertEqual(result["researchAvailableCount"], 0)
        self.assertEqual(result["races"], [])
        self.assertFalse(result["bettingReady"])

    def test_bad_date_and_ambiguous_programme_rejected(self):
        for bad_date in ("20260230", "2026-11-01", "20261100"):
            with self.subTest(bad_date=bad_date), self.assertRaises(CoverageError):
                p,e,t,z,_ = sample()
                owner_day_research(p,e,t,z,bad_date)
        p,e,t,z,day = sample()
        p.append(copy.deepcopy(p[0]))
        with self.assertRaises(CoverageError):
            owner_day_research(p,e,t,z,day)

    def test_source_row_types_rejected(self):
        p,e,t,z,day = sample()
        e.append("not an entry")
        with self.assertRaises(CoverageError):
            owner_day_research(p,e,t,z,day)


if __name__ == "__main__":
    unittest.main()
