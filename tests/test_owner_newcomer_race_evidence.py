"""Debut-race candidate handling: name is evidence of class, not horse debut.

Offline only: no JRDB/JRA network, credentials, purchases or ROI writes.
Covers the existing prestart 3連単 research pipeline, without promoting
unobserved recent form to C/0 or a formal 97/100 assessment.
"""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_owner_auto_draft import build_owner_auto_drafts, JST
from owner_uncertain_recent_preview import preview_missing_recent_holds
from test_jrdb_owner_auto_draft import programme, research, DAY
from test_owner_jrdb_docs_shaped_36r_acceptance import (
    provider_shaped_day, run_private_pipeline,
)
import json

PRESTART = datetime(2099, 1, 1, 9, tzinfo=JST)
PAIRS = [("S", "未評価")] * 2 + [("A", "未評価")] * 4 + [
    ("B", "未評価")
] * 4
ZERO = {
    "datedRuns": 0, "completedRuns": 0, "topThreeObserved": 0,
    "fourthCornerObserved": 0, "late3fObserved": 0,
}


def draft_for_name(name, *, one_past_run=False, missing_workout=False):
    p = programme(headcount=len(PAIRS))
    if name is not None:
        p[0]["race_name"] = name
    rec = research(PAIRS)
    for h in rec["races"][0]["research"]["runners"]:
        h["recentObserved"] = dict(ZERO)
    if one_past_run:
        rec["races"][0]["research"]["runners"][0]["recentObserved"] = {
            **ZERO, "datedRuns": 1, "completedRuns": 1
        }
    if missing_workout:
        h = rec["races"][0]["research"]["runners"][0]
        h["training"] = "未評価"
        h["completeFactors"] = 0
        h["researchOrder"] = None
    return build_owner_auto_drafts(p, rec, DAY, now=PRESTART)


class NewcomerProgrammeEvidenceTests(unittest.TestCase):
    def test_explicit_newcomer_and_zero_prior_observations_only_unsigned_reference(self):
        report = draft_for_name("2歳新馬")
        before = copy.deepcopy(report)
        self.assertEqual(report["draftCount"], 0)
        self.assertEqual(report["holdReasons"], {"missing_factors": 1})
        self.assertTrue(report["races"][0]["newcomerRaceCandidate"])
        reference = preview_missing_recent_holds(report, DAY, now=PRESTART)
        self.assertEqual(reference["safeResearchPreviewCount"], 1)
        row = reference["races"][0]
        self.assertTrue(row["newcomerRaceCandidate"])
        self.assertEqual(row["missingRecentCount"], 10)
        self.assertEqual(row["points"], 40)
        self.assertEqual(len(row["first"]), 2)
        self.assertTrue(row["eachCutoffProvenForAllRecentGrades"])
        self.assertFalse(row["officialJraVerified"])
        self.assertFalse(row["receiptIssued"])
        self.assertFalse(reference["formalTenFactorReady"])
        self.assertFalse(reference["predictionReady"])
        self.assertEqual(reference["ticketsIssued"], 0)
        self.assertEqual(report, before)

    def test_missing_history_in_unbeaten_or_maiden_is_not_newcomer_evidence(self):
        for name in ("2歳未勝利", None, "新馬記念", "3歳1勝クラス"):
            with self.subTest(name=name):
                report = draft_for_name(name)
                self.assertFalse(report["races"][0]["newcomerRaceCandidate"])
                reference = preview_missing_recent_holds(report, DAY, now=PRESTART)
                self.assertEqual(reference["safeResearchPreviewCount"], 1)
                self.assertFalse(reference["races"][0]["newcomerRaceCandidate"])

    def test_prior_observed_run_in_newcomer_race_cannot_be_called_zero_prior(self):
        report = draft_for_name("3歳新馬", one_past_run=True)
        self.assertTrue(report["races"][0]["newcomerRaceCandidate"])
        reference = preview_missing_recent_holds(report, DAY, now=PRESTART)
        self.assertEqual(reference["safeResearchPreviewCount"], 1)
        self.assertFalse(reference["races"][0]["newcomerRaceCandidate"])

    def test_explicit_debut_name_does_not_invent_missing_training(self):
        report = draft_for_name("メイクデビュー東京", missing_workout=True)
        self.assertTrue(report["races"][0]["newcomerRaceCandidate"])
        reference = preview_missing_recent_holds(report, DAY, now=PRESTART)
        self.assertEqual(reference["safeResearchPreviewCount"], 0)
        self.assertEqual(reference["ticketsIssued"], 0)

    def test_after_off_never_backfills_newcomer_reference(self):
        report = draft_for_name("2歳新馬")
        after = datetime(2099, 1, 1, 18, tzinfo=JST)
        result = preview_missing_recent_holds(report, DAY, now=after)
        self.assertEqual(result["safeResearchPreviewCount"], 0)

    def test_all_36r_real_pipeline_zero_prior_on_newcomer_only_one_held(self):
        p, e, t, z = provider_shaped_day()
        p[0]["race_name"] = "2歳新馬"
        key = p[0]["racekey"]
        for row in z:
            if row["racekey"] == key:
                for i in (1, 2):
                    for field in ("racedate", "order_of_finish", "idm",
                                  "later3f_time", "corner4_order"):
                        row.pop(f"race_back_{i}_{field}", None)
        original = copy.deepcopy((p, e, t, z))
        res, reads = run_private_pipeline((p, e, t, z))
        self.assertEqual(res["status"], "200 OK")
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        self.assertEqual((p, e, t, z), original)
        body = json.loads(res["body"])
        self.assertEqual((body["draftCount"], body["holdCount"]), (35, 1))
        hold = next(r for r in body["races"] if r["status"] == "hold")
        self.assertTrue(hold["newcomerRaceCandidate"])
        self.assertEqual(hold["reason"], "missing_factors")
        self.assertEqual(body["researchReceiptCount"], 35)
        preview = body["uncertainRecentResearch"]
        self.assertEqual(preview["safeResearchPreviewCount"], 1)
        candidate = preview["races"][0]
        self.assertTrue(candidate["newcomerRaceCandidate"])
        self.assertEqual(candidate["missingRecentCount"], 7)
        self.assertEqual(candidate["assessedTrainingCount"], 7)
        self.assertTrue(candidate["points"] <= 48)
        self.assertFalse(body["officialJraVerified"])
        self.assertFalse(body["overallPredictionReady"])
        self.assertFalse(body["bettingReady"])
        self.assertNotIn("horse_id", res["body"].decode())
        self.assertNotIn("racekey", res["body"].decode())


if __name__ == "__main__":
    unittest.main()
