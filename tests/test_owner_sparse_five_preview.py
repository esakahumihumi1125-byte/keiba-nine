"""Synthetic no-network tests for mathematically bounded JRDB 79 research."""
import copy
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from test_owner_research6_five_drafts import materials, calculate, JST, DAY
from jrdb_coverage import CoverageError
from owner_sparse_five_preview import preview_sparse_five_holds, VERSION

NOW = datetime(2099, 1, 1, 9, 0, tzinfo=JST)
SPARSE = [
    ("S", "未評価"), ("S", "未評価"),
    ("A", "未評価"), ("A", "未評価"), ("A", "未評価"),
    ("B", "未評価"), ("B", "未評価"),
]


def add_original_subtotals(study):
    # The real new-weight research always includes separately computed
    # 34-point course/pace and 12-point going observations.
    from owner_new_weight_five_research import WEIGHTS
    from evaluation_policy import POINTS
    for race in study["races"]:
        for h in race["horses"]:
            bands = h["bands"]
            pair = ("course_distance", "pace")
            cp = (None if any(bands[k] == "未評価" for k in pair)
                  else sum(WEIGHTS[k] * POINTS[bands[k]] for k in pair))
            going = (None if bands["ground"] == "未評価"
                     else WEIGHTS["ground"] * POINTS[bands["ground"]])
            h.update(
                coursePaceEvidenceRawThirdPoints=cp,
                coursePaceEvidenceScore34=None if cp is None else round(cp / 3, 2),
                coursePaceEvidenceNotFormalGrade=True,
                goingEvidenceRawThirdPoints=going,
                goingEvidenceScore12=None if going is None else round(going / 3, 2),
                goingEvidenceNotFormalGrade=True,
            )
    return study


def run_sparse(bands=SPARSE, *, now=NOW):
    programme, study = materials(bands)
    add_original_subtotals(study)
    drafts = calculate(programme, study, now=now)
    return preview_sparse_five_holds(
        programme, study, drafts, DAY, now=now)


class SparseFiveReferenceTests(unittest.TestCase):
    def test_recover_stable_40_point_reference_when_all_recent_missing(self):
        p, s = materials(SPARSE)
        add_original_subtotals(s)
        drafts = calculate(p, s)
        self.assertEqual((drafts["draftCount"], drafts["holdCount"]), (0, 1))
        self.assertEqual(drafts["races"][0]["reason"], "incomplete_five_factors")
        before = copy.deepcopy((p, s, drafts))
        out = preview_sparse_five_holds(p, s, drafts, DAY, now=NOW)
        self.assertEqual((p, s, drafts), before, "never mutate original")
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(out["safeResearchPreviewCount"], 1)
        self.assertEqual(out["reviewedPrestartMissingFactorRaces"], 1)
        row = out["races"][0]
        self.assertEqual(row["status"], "bounded_missing_recent_reference")
        self.assertEqual(row["missingRecentCount"], 7)
        self.assertEqual(row["first"], [1, 2])
        self.assertEqual(row["second"], [1, 2, 3, 4, 5])
        self.assertEqual(row["third"], list(range(1, 8)))
        self.assertEqual(row["points"], 40)
        self.assertTrue(row["eachCutoffProvenForEveryRecentGrade"])
        for flag in ("receiptIssued", "predictionReady", "bettingReady",
                     "actualPurchase", "officialJraVerified"):
            self.assertFalse(row[flag])
        for flag in ("formalTenFactorReady", "predictionReady", "bettingReady",
                     "actualPurchase", "changesExistingReceipts",
                     "changesExistingTickets", "changesExistingRoi"):
            self.assertFalse(out[flag])
        self.assertEqual(out["ticketsIssued"], 0)
        self.assertEqual(out["newProviderRequests"], 0)
        for forbidden in ("horse_id", "racekey", "password", "signed", "odds",
                          "payout", "idms"):
            self.assertNotIn(forbidden, repr(out))

    def test_source_grade_C_does_not_replace_missing_grades(self):
        bands = [("S", "未評価"), ("S", "C"),
                 ("A", "未評価"), ("A", "A"), ("A", "B"),
                 ("B", "未評価"), ("B", "S")]
        out = run_sparse(bands)
        self.assertEqual(out["safeResearchPreviewCount"], 1)
        self.assertEqual(out["races"][0]["missingRecentCount"], 3)
        self.assertEqual(out["races"][0]["points"], 40)

    def test_other_missing_factors_and_identical_cutoffs_remain_held(self):
        mixed = list(SPARSE)
        mixed[2] = ("未評価", "未評価")
        out = run_sparse(mixed)
        self.assertEqual(out["safeResearchPreviewCount"], 0)
        self.assertEqual(out["heldReasons"], {"other_factors_missing": 1})
        identical = [("S", "未評価")] * 7
        out = run_sparse(identical)
        self.assertEqual(out["safeResearchPreviewCount"], 0)
        self.assertEqual(out["heldReasons"], {"unstable_boundary": 1})

    def test_large_field_tied_third_boundary_never_split_by_horse_number(self):
        large = [("S", "未評価")] + [("A", "未評価")] * 3 + [
            ("B", "未評価")] * 14
        out = run_sparse(large)
        self.assertEqual(out["safeResearchPreviewCount"], 0)
        self.assertEqual(out["heldReasons"], {"unstable_boundary": 1})

    def test_after_off_never_reconstructs_backdated_formations(self):
        after = datetime(2099, 1, 1, 12, 0, tzinfo=JST)
        out = run_sparse(now=after)
        self.assertEqual(out["reviewedPrestartMissingFactorRaces"], 0)
        self.assertEqual(out["safeResearchPreviewCount"], 0)
        self.assertEqual(out["races"], [])

    def test_only_existing_incomplete_signed_hold_is_scanned(self):
        p, s = materials(SPARSE)
        add_original_subtotals(s)
        drafts = calculate(p, s)
        forged = copy.deepcopy(drafts)
        forged["races"][0]["status"] = "five_factor_research_draft"
        out = preview_sparse_five_holds(p, s, forged, DAY, now=NOW)
        self.assertEqual(out["safeResearchPreviewCount"], 0)
        forged = copy.deepcopy(drafts)
        forged["races"][0]["completeObserved"] = 99
        with self.assertRaises(CoverageError):
            preview_sparse_five_holds(p, s, forged, DAY, now=NOW)
        forged = copy.deepcopy(drafts)
        forged["date"] = "20990102"
        with self.assertRaises(CoverageError):
            preview_sparse_five_holds(p, s, forged, DAY, now=NOW)

    def test_malformed_band_or_study_score_rejected(self):
        p, s = materials(SPARSE)
        add_original_subtotals(s)
        d = calculate(p, s)
        s["races"][0]["horses"][0]["bands"]["course_distance"] = "C"
        with self.assertRaises(CoverageError):
            preview_sparse_five_holds(p, s, d, DAY, now=NOW)


if __name__ == "__main__":
    unittest.main()
