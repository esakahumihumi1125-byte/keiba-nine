"""Tests for the private five-factor hypothesis overlay (synthetic only)."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_five_factor_hypotheses import combine_five_factor_hypotheses
from test_jrdb_experimental_rebound_review import fixtures


class FiveFactorHypothesisTests(unittest.TestCase):
    def test_five_factor_overlay_stays_unverified_and_preserves_source(self):
        matrix, _, history, pace = fixtures()
        originals = copy.deepcopy((matrix, history, pace))
        report = combine_five_factor_hypotheses(matrix, history, pace)
        self.assertEqual((matrix, history, pace), originals)
        self.assertEqual(report["version"], "owner-five-factor-hypotheses-1")
        self.assertEqual(report["policyVersion"], "research-5")
        self.assertEqual(report["raceCount"], 2)
        self.assertEqual({f["key"]: f["weight"] for f in report["factors"]}, {
            "training":30,"recent":3,"course_distance":20,"pace":20,"ground":12,
        })
        self.assertEqual(sum(f["weight"] for f in report["factors"]), 85)
        self.assertTrue(report["hypothesisBandsNotVerifiedGrades"])
        self.assertEqual(report["verifiedFactorCount"], 0)
        self.assertFalse(report["overallPredictionReady"])
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["bettingReady"])
        tokyo = next(r for r in report["races"] if r["track"] == "東京")
        self.assertEqual(tokyo["runnerCount"], 5)
        one = next(h for h in tokyo["runners"] if h["number"] == 1)
        self.assertEqual(one["bands"], {
            "training": "S", "recent": "C",
            "course_distance": "S", "pace": "S", "ground": "S",
        })
        self.assertIsNone(one["overallScore"])
        self.assertIsNone(one["overallRank"])
        self.assertEqual(one["actualGradesVerified"], 0)
        kyoto = next(r for r in report["races"] if r["track"] == "京都")
        self.assertTrue(all(h["bands"]["ground"] == "未評価" for h in kyoto["runners"]))
        for secret in ("racekey", "horse_id", "byNumber", "paid_index", "trifectaTickets"):
            self.assertNotIn(secret, repr(report))

    def test_mismatched_race_or_runner_fails_closed(self):
        def rejected(change):
            matrix, _, historical, pace = fixtures()
            change(matrix, historical, pace)
            with self.assertRaises(CoverageError):
                combine_five_factor_hypotheses(matrix, historical, pace)
        rejected(lambda a,b,c: b["races"][0].update(track="阪神"))
        rejected(lambda a,b,c: c["races"][0]["runners"][0].update(number=18))
        rejected(lambda a,b,c: b["races"][0]["runners"][0].update(number=18))
        rejected(lambda a,b,c: a[0]["byNumber"]["01"]["ground"].update(grade="S"))
        rejected(lambda a,b,c: b.update(bettingReady=True))
        rejected(lambda a,b,c: c.update(officialJraVerified=True))

    def test_coverage_counts_are_observation_not_computed_prediction(self):
        matrix, _, historical, pace = fixtures()
        report = combine_five_factor_hypotheses(matrix, historical, pace)
        tokyo = next(r for r in report["races"] if r["track"] == "東京")
        for factor in ("training","recent","course_distance","pace","ground"):
            self.assertLessEqual(tokyo["bandsPresentByFactor"][factor], tokyo["runnerCount"])
        self.assertEqual(tokyo["verifiedFactorCount"],0)
        self.assertFalse(tokyo["overallReady"])
        self.assertFalse(tokyo["bettingReady"])


if __name__ == "__main__":
    unittest.main()
