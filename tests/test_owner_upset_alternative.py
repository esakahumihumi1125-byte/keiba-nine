"""Synthetic only: 4-6th-ranked longshot winner alternative formation safety."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_full_ten_factor import full_ten_factor_preview
from test_owner_full_ten_factor import fixture, NOW, OFF


def add_independent_support(source, index, factors=("training", "course_distance")):
    for factor in factors:
        item = source["horses"][index]["assessments"][factor]
        item["winSupport"] = True
        item["evidence"][0]["sourceId"] = f"private-{factor}-{index}"
        item["evidence"][0]["sourceFamily"] = f"independent_{factor}"
        item["reason"] = f"Independent source for {factor}"


class UpsetAlternativeTests(unittest.TestCase):
    def test_rank_four_alt_is_40_real_unique_trifecta_points(self):
        source = fixture()
        add_independent_support(source, 3)
        pristine = copy.deepcopy(source)
        out = full_ten_factor_preview(source, now=NOW)
        alt, base = out["upsetAlternative"], out["trifecta"]
        self.assertEqual(source, pristine)
        self.assertEqual(base["first"], [1, 2])
        self.assertEqual(base["points"], 40)
        self.assertEqual(alt["status"], "review_only")
        self.assertEqual((alt["candidateNumber"], alt["candidateRank"]), (4, 4))
        self.assertEqual(alt["first"], [1, 4])
        self.assertEqual(alt["points"], 40)
        self.assertEqual(alt["totalStakeYen"], 4000)
        self.assertEqual(alt["newTicketsComparedWithPrimary"], 20)
        self.assertEqual(len({tuple(t) for t in alt["tickets"]}), 40)
        self.assertTrue(all(len(set(t)) == 3 for t in alt["tickets"]))
        self.assertFalse(alt["bettingReady"])
        self.assertFalse(alt["autoPurchase"])
        self.assertFalse(alt["automaticallySelected"])
        self.assertTrue(alt["primaryUnchanged"])
        self.assertTrue(alt["requiresOwnerReview"])
        # The alternate ticket list must NEVER flow into base saved receipts.
        self.assertEqual(base["first"], [1, 2])
        self.assertEqual(base["individual"], [])
        self.assertNotIn("private-training-3", str(alt))
        self.assertNotIn("Independent source for", str(alt))

    def test_rank_six_alt_is_bounded_30_to_40_without_fillers(self):
        source = fixture()
        add_independent_support(source, 5, ("course_distance", "pace"))
        out = full_ten_factor_preview(source, now=NOW)
        alt = out["upsetAlternative"]
        self.assertEqual(alt["candidateNumber"], 6)
        self.assertEqual(alt["candidateRank"], 6)
        self.assertEqual(alt["first"], [1, 6])
        self.assertTrue(30 <= alt["points"] <= 40)
        self.assertEqual(alt["points"], len(alt["tickets"]))
        self.assertEqual(alt["totalStakeYen"], alt["points"] * 100)
        self.assertTrue(any(t[0] == 6 for t in alt["tickets"]))
        self.assertEqual(out["trifecta"]["points"], 40)

    def test_multiple_longshot_candidates_require_human_review(self):
        source = fixture()
        add_independent_support(source, 3)
        add_independent_support(source, 4, ("course_distance", "pace"))
        out = full_ten_factor_preview(source, now=NOW)
        alt = out["upsetAlternative"]
        self.assertEqual(alt["status"], "held")
        self.assertEqual(alt["reason"], "multiple_supported_lower_rank_horses")
        self.assertEqual(alt["points"], 0)
        self.assertEqual(alt["tickets"], [])
        self.assertEqual(out["trifecta"]["points"], 40)

    def test_shared_upstream_source_does_not_enable_alt(self):
        source = fixture()
        add_independent_support(source, 3)
        for factor in ("training", "course_distance"):
            source["horses"][3]["assessments"][factor]["evidence"][0][
                "sourceId"] = "same-upstream-data"
        out = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(out["upsetAlternative"]["status"], "held")
        self.assertEqual(out["upsetAlternative"]["points"], 0)

    def test_official_and_assessment_checks_both_gate_alt(self):
        for kind in ("jra", "assessment", "prediction"):
            source = fixture()
            add_independent_support(source, 3)
            if kind == "jra":
                source["independentJra"]["jra_scratches_verified"] = False
            elif kind == "assessment":
                source["assessmentValidated"] = False
            else:
                source["predictionValidated"] = False
            with self.subTest(kind=kind):
                out = full_ten_factor_preview(source, now=NOW)
                self.assertEqual(out["upsetAlternative"]["status"], "held")
                self.assertEqual(out["upsetAlternative"]["points"], 0)

    def test_missing_and_late_sources_never_generate_alt(self):
        for kind in ("missing", "late", "postoff"):
            source = fixture()
            add_independent_support(source, 3)
            if kind == "missing":
                source["horses"][2]["assessments"].pop("pedigree")
            if kind == "late":
                source["horses"][3]["assessments"]["pace"]["evidence"][0][
                    "availableAt"] = "2099-01-01T09:15:00+09:00"
            with self.subTest(kind=kind):
                out = full_ten_factor_preview(
                    source, now=OFF if kind == "postoff" else NOW,
                )
                if kind == "late":
                    # "asOf" is 09:00 and the evidence arrived 09:15.
                    self.assertEqual(out["status"], "missing_evidence")
                self.assertEqual(out["upsetAlternative"]["status"], "held")
                self.assertEqual(out["upsetAlternative"]["points"], 0)

    def test_exact_top_rank_tie_never_uses_horse_number_to_pick_first(self):
        source = fixture()
        add_independent_support(source, 3)
        for item in source["horses"][1]["assessments"].values():
            item["grade"] = "S"
        out = full_ten_factor_preview(source, now=NOW)
        self.assertEqual(out["upsetAlternative"]["status"], "held")
        self.assertEqual(out["upsetAlternative"]["reason"], "top_rank_tied")


if __name__ == "__main__":
    unittest.main()
