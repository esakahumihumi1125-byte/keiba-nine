"""Pure, synthetic 10-factor gate regression tests. No provider or bet calls."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluation_policy import FACTORS
from jrdb_coverage import CoverageError
from owner_full_ten_factor import full_ten_factor_preview

AS_OF = "2099-01-01T09:00:00+09:00"
NOW = "2099-01-01T09:15:00+09:00"
OFF = "2099-01-01T10:00:00+09:00"
OFFICIAL = {
    "jra_starters_verified": True,
    "jra_scratches_verified": True,
    "jra_going_verified": True,
    "jra_posttime_verified": True,
}
CHANGES = ({}, {"recent": "A"}, {"pedigree": "A"},
           {"ground": "A"}, {"course_distance": "A"},
           {"training": "A"}, {"training": "A", "ground": "A"},
           {"training": "A", "course_distance": "A"})


def horse(number, changes=None):
    grades = {key: "S" for key in FACTORS}
    grades.update(changes or {})
    return {
        "number": number,
        "assessments": {
            key: {
                "grade": grade, "reason": "Prestart independent evidence",
                "evidence": [{
                    "sourceId": "test-original", "reference": "fixture",
                    "availableAt": AS_OF,
                }],
            }
            for key, grade in grades.items()
        },
    }


def fixture():
    return {
        "mode": "owner_verified_prestart_v1",
        "asOf": AS_OF, "offAt": OFF,
        "independentJra": dict(OFFICIAL),
        "assessmentValidated": True, "predictionValidated": True,
        "horses": [horse(i + 1, change) for i, change in enumerate(CHANGES)],
    }


class FullTenFactorGateTests(unittest.TestCase):
    def test_full_evidenced_eight_horse_preview_40_unique_tickets(self):
        source = fixture()
        untouched = copy.deepcopy(source)
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, untouched)
        self.assertEqual(result["status"], "review_only")
        self.assertTrue(result["overallReady"])
        self.assertFalse(result["bettingReady"])
        self.assertFalse(result["publishable"])
        self.assertEqual([r["number"] for r in result["ranking"]], list(range(1, 9)))
        self.assertEqual(result["ranking"][0]["score100"], 100)
        self.assertEqual(result["ranking"][0]["overallGrade"], "S")
        self.assertEqual(result["trifecta"]["points"], 40)
        self.assertEqual(result["trifecta"]["totalStakeYen"], 4000)
        self.assertEqual(len(set(map(tuple, result["trifecta"]["tickets"]))), 40)
        self.assertTrue(all(len(set(t)) == 3 for t in result["trifecta"]["tickets"]))

    def test_exact_all_ten_factor_contributions_sum_to_100(self):
        """Every displayed item is evidence-backed; round only for display."""
        source = fixture()
        source["horses"][0]["assessments"]["recent"]["grade"] = "C"
        source["horses"][0]["assessments"]["training"]["grade"] = "A"
        untouched = copy.deepcopy(source)
        output = full_ten_factor_preview(source, now=NOW)
        first = next(r for r in output["ranking"] if r["number"] == 1)
        self.assertEqual(source, untouched)
        rows = first["factorContributions"]
        self.assertEqual(set(rows), set(FACTORS))
        self.assertEqual({k: v["weight"] for k, v in rows.items()}, FACTORS)
        self.assertEqual(rows["training"], {
            "grade": "A", "weight": 30, "earned100": 20.0, "rawThirdPoints": 60
        })
        self.assertEqual(rows["recent"], {
            "grade": "C", "weight": 3, "earned100": 0.0, "rawThirdPoints": 0
        })
        self.assertEqual(rows["course_distance"]["earned100"], 20.0)
        self.assertEqual(rows["pace"]["earned100"], 20.0)
        self.assertEqual(rows["ground"]["earned100"], 12.0)
        self.assertEqual(rows["pedigree"]["earned100"], 8.0)
        self.assertEqual(rows["draw_weight"]["earned100"], 3.0)
        self.assertEqual(rows["jockey_stable"]["earned100"], 2.0)
        self.assertEqual(rows["rotation"]["earned100"], 1.0)
        self.assertEqual(rows["body_condition"]["earned100"], 1.0)
        self.assertEqual(first["weightedPoints"], sum(
            row["rawThirdPoints"] for row in rows.values()
        ))
        self.assertEqual(first["score100"], 87.0)
        self.assertEqual(first["overallGrade"], "S")
        self.assertNotIn("sourceId", repr(first))
        self.assertNotIn("reference", repr(first))

    def test_low_recent_results_have_only_three_point_maximum_impact(self):
        baseline = fixture()
        worse = fixture()
        worse["horses"][0]["assessments"]["recent"]["grade"] = "C"
        a = full_ten_factor_preview(baseline, now=NOW)
        b = full_ten_factor_preview(worse, now=NOW)
        total = lambda result: next(
            h["score100"] for h in result["ranking"] if h["number"] == 1
        )
        self.assertEqual(total(a) - total(b), 3.0)
        self.assertEqual(total(b), 97.0)
        self.assertEqual(next(
            h["overallGrade"] for h in b["ranking"] if h["number"] == 1
        ), "S")

    def test_s_grade_uses_exact_integer_boundary_not_rounded_display(self):
        # 30+12+3 S->A loses 45 raw third-points: 85.00 / 100.
        at = fixture()
        for factor in ("training", "ground", "draw_weight"):
            at["horses"][0]["assessments"][factor]["grade"] = "A"
        at_result = full_ten_factor_preview(at, now=NOW)
        at_first = next(h for h in at_result["ranking"] if h["number"] == 1)
        self.assertEqual(at_first["weightedPoints"], 255)
        self.assertEqual(at_first["score100"], 85.0)
        self.assertEqual(at_first["overallGrade"], "S")
        # The additional 1-point rotation reduction makes 84.67, an A.
        below = copy.deepcopy(at)
        below["horses"][0]["assessments"]["rotation"]["grade"] = "A"
        below_result = full_ten_factor_preview(below, now=NOW)
        below_first = next(h for h in below_result["ranking"]
                           if h["number"] == 1)
        self.assertEqual(below_first["weightedPoints"], 254)
        self.assertEqual(below_first["score100"], 84.67)
        self.assertEqual(below_first["overallGrade"], "A")
        self.assertEqual(below_first["factorContributions"]["rotation"]["earned100"], 0.67)

    def test_no_partial_score_ledger_when_evidence_is_missing(self):
        source = fixture()
        del source["horses"][0]["assessments"]["body_condition"]
        report = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(report["status"], "missing_evidence")
        self.assertEqual(report["ranking"], [])
        self.assertEqual(report["trifecta"]["points"], 0)
        self.assertEqual(report["missingByNumber"], {1: ["body_condition"]})
        self.assertNotIn("factorContributions", repr(report))

    def test_missing_eighth_factor_never_normalizes_partial_grade(self):
        source = fixture()
        del source["horses"][0]["assessments"]["ground"]
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["status"], "missing_evidence")
        self.assertFalse(result["overallReady"])
        self.assertEqual(result["ranking"], [])
        self.assertEqual(result["missingByNumber"], {1: ["ground"]})
        self.assertEqual(result["trifecta"]["points"], 0)

    def test_source_available_after_prediction_cutoff_is_unassessed(self):
        source = fixture()
        source["horses"][1]["assessments"]["pace"]["evidence"][0]["availableAt"] = (
            "2099-01-01T09:10:00+09:00")
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["status"], "missing_evidence")
        self.assertEqual(result["missingByNumber"], {2: ["pace"]})

    def test_no_caller_supplied_approval_means_no_trifecta(self):
        for absent in ("predictionValidated", "assessmentValidated"):
            source = fixture()
            source[absent] = False
            result = full_ten_factor_preview(source, now=NOW)
            self.assertEqual(result["status"], "research_only")
            self.assertTrue(result["overallReady"])
            self.assertEqual(result["trifecta"]["points"], 0)
            self.assertEqual(result["trifecta"]["status"], "not_ready")
        source = fixture()
        source["independentJra"]["jra_scratches_verified"] = False
        result = full_ten_factor_preview(source, now=NOW)
        self.assertIn("jra_scratches_verified", result["trifecta"]["blockingEvidence"])
        self.assertEqual(result["trifecta"]["points"], 0)

    def test_cutoff_ties_never_split_using_horse_number(self):
        source = fixture()
        source["horses"] = [horse(i) for i in range(1, 9)]
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["status"], "ambiguous_score_cutoff")
        self.assertEqual(result["trifecta"]["points"], 0)
        self.assertEqual([h["rank"] for h in result["ranking"]], [1] * 8)

    def test_stale_or_poststart_snapshot_cannot_recalculate(self):
        for clock in (OFF, "2099-01-01T11:00:00+09:00",
                      "2099-01-01T08:59:00+09:00"):
            result = full_ten_factor_preview(fixture(), now=clock)
            self.assertEqual(result["status"], "outside_prestart_window")
            self.assertEqual(result["ranking"], [])
            self.assertEqual(result["trifecta"]["points"], 0)

    def test_rebound_horse_is_not_penalized_by_finishing_position(self):
        source = fixture()
        source["horses"][0]["assessments"]["recent"]["grade"] = "C"
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["ranking"][0]["number"], 2)
        self.assertEqual(result["ranking"][1]["number"], 3)
        self.assertEqual(result["ranking"][2]["number"], 1)
        self.assertEqual(result["ranking"][2]["score100"], 97)
        self.assertEqual(result["ranking"][2]["overallGrade"], "S")

    def test_rank_four_to_six_win_recheck_never_auto_adds_tickets(self):
        source = fixture()
        horse4 = source["horses"][3]
        for factor, origin in (("training", "independent-workout"),
                               ("course_distance", "independent-course")):
            item = horse4["assessments"][factor]
            item["winSupport"] = True
            item["evidence"][0]["sourceId"] = origin
        before = copy.deepcopy(source)
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(source, before)
        recheck = result["winnerRecheck"]
        self.assertEqual(recheck["version"], "owner-full-ten-winner-recheck-1")
        self.assertEqual(recheck["lowerRankCandidates"], [{
            "number": 4, "rank": 4,
            "supportFactors": ["training", "course_distance"],
            "overallGrade": "S", "decision": "manual_recheck_only",
        }])
        self.assertEqual(recheck["recentLossCandidates"], [])
        self.assertFalse(recheck["changesTrifecta"])
        self.assertFalse(recheck["addsFirstPlaceAutomatically"])
        self.assertEqual(result["trifecta"]["first"], [1, 2])
        self.assertEqual(result["trifecta"]["points"], 40)
        self.assertFalse(result["bettingReady"])

    def test_recent_loss_rebound_review_and_independence_gate(self):
        source = fixture()
        horse = source["horses"][3]
        horse["assessments"]["recent"]["grade"] = "C"
        for factor, origin in (("training", "workout-source"),
                               ("pace", "pace-source")):
            item = horse["assessments"][factor]
            item["winSupport"] = True
            item["evidence"][0]["sourceId"] = origin
        result = full_ten_factor_preview(source, now=NOW)
        r = result["winnerRecheck"]
        self.assertEqual([h["number"] for h in r["recentLossCandidates"]], [4])
        self.assertEqual([h["number"] for h in r["lowerRankCandidates"]], [4])
        # Merely repeating the same upstream observation as two factors
        # does not meet the independent-source review threshold.
        source["horses"][3]["assessments"]["pace"]["evidence"][0]["sourceId"] = (
            "workout-source")
        result = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(result["winnerRecheck"]["recentLossCandidates"], [])
        self.assertEqual(result["winnerRecheck"]["lowerRankCandidates"], [])

    def test_no_unverified_or_blocked_winner_review(self):
        source = fixture()
        horse = source["horses"][3]
        for factor, origin in (("training", "workout-4"),
                               ("pace", "pace-4")):
            horse["assessments"][factor]["winSupport"] = True
            horse["assessments"][factor]["evidence"][0]["sourceId"] = origin
        source["assessmentValidated"] = False
        report = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(report["winnerRecheck"]["lowerRankCandidates"], [])
        self.assertEqual(report["trifecta"]["points"], 0)
        source["assessmentValidated"] = True
        source["horses"][3]["blockingConcerns"] = [
            {"reason": "Official starter status uncertain"}]
        report = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(report["winnerRecheck"]["lowerRankCandidates"], [])
        source["horses"][3]["blockingConcerns"] = "unverified"
        with self.assertRaises(CoverageError):
            full_ten_factor_preview(source, now=NOW)

    def test_unresolved_entry_blocks_even_full_100_point_scores(self):
        """An unverified scratched runner is not a ticket despite 10 grades."""
        for n in (1, 4, 8):
            with self.subTest(horse=n):
                source = fixture()
                source["horses"][n - 1]["blockingConcerns"] = [{
                    "reason": "Starter confirmation not checked"
                }]
                before = copy.deepcopy(source)
                result = full_ten_factor_preview(source, now=NOW)
                self.assertEqual(source, before)
                self.assertTrue(result["overallReady"])
                self.assertEqual(result["status"], "unresolved_runner_blocker")
                self.assertEqual(result["blockedRunnerCount"], 1)
                self.assertFalse(result["bettingReady"])
                self.assertFalse(result["publishable"])
                self.assertEqual(len(result["ranking"]), 8)
                self.assertEqual(result["trifecta"]["points"], 0)
                self.assertEqual(result["trifecta"]["tickets"], [])
                self.assertFalse(result["winnerRecheck"]["changesTrifecta"])
                self.assertFalse(result["upsetAlternative"]["autoPurchase"])

    def test_prestart_official_flags_cannot_replace_independent_grades(self):
        # Even all four official checks do not justify turning missing
        # horse-by-horse evidence into S/A/B/C or a 3連単.
        source = fixture()
        for h in source["horses"]:
            del h["assessments"]["pedigree"]
        response = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(response["status"], "missing_evidence")
        self.assertEqual(response["ranking"], [])
        self.assertEqual(response["trifecta"]["points"], 0)
        self.assertEqual(len(response["missingByNumber"]), 8)

    def test_does_not_reconstruct_winner_review_after_start(self):
        source = fixture()
        source["horses"][3]["assessments"]["training"]["winSupport"] = True
        result = full_ten_factor_preview(source, now=OFF)
        self.assertEqual(result["winnerRecheck"]["recentLossCandidates"], [])
        self.assertEqual(result["winnerRecheck"]["lowerRankCandidates"], [])
        self.assertEqual(result["trifecta"]["points"], 0)

    def test_duplicate_numbers_and_unrecognized_factors_are_rejected(self):
        source = fixture()
        source["horses"][1]["number"] = 1
        with self.assertRaises(CoverageError):
            full_ten_factor_preview(source, now=NOW)
        source = fixture()
        source["horses"][0]["assessments"]["odds"] = {
            "grade": "S", "reason": "invalid"}
        with self.assertRaises(CoverageError):
            full_ten_factor_preview(source, now=NOW)


if __name__ == "__main__":
    unittest.main()
