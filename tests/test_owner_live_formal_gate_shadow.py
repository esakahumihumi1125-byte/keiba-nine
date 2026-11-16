"""Synthetic production-day formal-gate shadow, zero licensed requests."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import build_owner_auto_drafts
from owner_ten_factor_contract import ten_factor_contract
from owner_live_formal_gate_shadow import live_formal_gate_shadow, VERSION
from test_jrdb_owner_auto_draft import programme, research, DAY, JST, generate

NOW = datetime(2099, 1, 1, 9, tzinfo=JST)
LATE = datetime(2099, 1, 1, 12, 30, tzinfo=JST)


def production_shaped(*, now=NOW, pairs=None):
    snapshot = build_owner_auto_drafts(
        programme(), research(pairs), DAY, now=now)
    snapshot["tenFactorPreview"] = ten_factor_contract(snapshot)
    return snapshot


class LiveFormalShadowTests(unittest.TestCase):
    def test_real_research_grades_do_not_promote_to_formal_tickets(self):
        report = production_shaped()
        self.assertEqual(report["races"][0]["status"], "provisional_draft")
        self.assertEqual(report["races"][0]["points"], 40)
        self.assertIn("S", [h["training"] for h in report["races"][0]["runners"]])
        before = copy.deepcopy(report)
        out = live_formal_gate_shadow(report, DAY, now=NOW)
        self.assertEqual(report, before)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual((out["raceCount"], out["prestartFormalGateRuns"],
                          out["blockedMissingEvidenceRaces"]), (1, 1, 1))
        self.assertEqual(out["races"], [{
            "track": "東京", "race": 1,
            "status": "blocked_missing_verified_evidence",
            "formalScoreReady": False, "officialJraVerified": False,
            "bettingReady": False,
        }])
        self.assertEqual(out["verifiedFormalFactorCount"], 0)
        self.assertEqual(out["verifiedTotalScoreCount"], 0)
        self.assertEqual(out["formalTrifectaCount"], 0)
        self.assertEqual(out["ticketsIssued"], 0)
        self.assertEqual(out["newProviderRequests"], 0)
        self.assertFalse(out["officialJraVerified"])
        self.assertFalse(out["overallPredictionReady"])
        self.assertFalse(out["bettingReady"])
        self.assertFalse(out["changesExistingDrafts"])
        self.assertFalse(out["changesExistingReceipts"])
        for secret in ("racekey", "idm", "jockey_index", "weightedResearchPoints"):
            self.assertNotIn(secret, repr(out))

    def test_held_partial_history_is_not_imputed_or_ticketed(self):
        report = production_shaped(
            pairs=[("S", "未評価")] * 6 + [("S", "A")])
        self.assertEqual(report["races"][0]["status"], "hold")
        self.assertEqual(report["races"][0]["reason"], "missing_factors")
        before = copy.deepcopy(report)
        out = live_formal_gate_shadow(report, DAY, now=NOW)
        self.assertEqual(report, before)
        self.assertEqual(out["prestartFormalGateRuns"], 1)
        self.assertEqual(out["blockedMissingEvidenceRaces"], 1)
        self.assertEqual(out["formalTrifectaCount"], 0)
        self.assertEqual(out["verifiedFormalFactorCount"], 0)

    def test_off_time_never_recreates_full_ten_horse_ranks(self):
        report = production_shaped(now=LATE)
        before = copy.deepcopy(report)
        out = live_formal_gate_shadow(report, DAY, now=LATE)
        self.assertEqual(report, before)
        self.assertEqual(out["prestartFormalGateRuns"], 0)
        self.assertEqual(out["pastOffRaces"], 1)
        self.assertEqual(out["races"][0]["status"], "past_off_no_retroactive_gate")
        self.assertEqual(out["formalTrifectaCount"], 0)

    def test_foreign_or_missing_runner_is_isolated_without_missing_grades(self):
        for corrupt in ("wrong_number", "fake_formal_grade", "missing_race_time"):
            report = production_shaped()
            if corrupt == "wrong_number":
                report["tenFactorPreview"]["races"][0]["horses"][0]["number"] = 18
            elif corrupt == "fake_formal_grade":
                report["tenFactorPreview"]["races"][0]["horses"][0][
                    "grades"]["pedigree"] = "S"
            else:
                report["races"][0]["postTime"] = "not-a-time"
            out = live_formal_gate_shadow(report, DAY, now=NOW)
            self.assertEqual(out["prestartFormalGateRuns"], 0)
            self.assertEqual(out["rosterOrTimeUnavailableRaces"], 1)
            self.assertEqual(out["formalTrifectaCount"], 0)

    def test_36_race_full_day_protects_ten_grade_and_hmac_history(self):
        report = production_shaped()
        rows = []
        for track in ("東京", "京都", "福島"):
            for n in range(1, 13):
                row = copy.deepcopy(report["races"][0])
                row["track"], row["race"] = track, n
                rows.append(row)
        report["races"] = rows
        report["raceCount"] = len(rows)
        report["tenFactorPreview"] = ten_factor_contract(report)
        original = copy.deepcopy(report)
        out = live_formal_gate_shadow(report, DAY, now=NOW)
        self.assertEqual(report, original)
        self.assertEqual(out["raceCount"], 36)
        self.assertEqual(out["prestartFormalGateRuns"], 36)
        self.assertEqual(out["blockedMissingEvidenceRaces"], 36)
        self.assertEqual(out["formalTrifectaCount"], 0)
        self.assertEqual(len({(x["track"], x["race"]) for x in out["races"]}), 36)
        self.assertEqual(sum(not x["formalScoreReady"]
                             for x in out["races"]), 36)

    def test_wrong_date_or_promoted_input_fails_closed(self):
        for mutation in (
            lambda x: x.update(date="20990102"),
            lambda x: x.update(officialJraVerified=True),
            lambda x: x["tenFactorPreview"].update(fullPredictionRaceCount=1),
            lambda x: x["tenFactorPreview"]["races"].append(
                copy.deepcopy(x["tenFactorPreview"]["races"][0])),
            lambda x: x.update(raceCount=2),
        ):
            report = production_shaped()
            mutation(report)
            with self.assertRaises(CoverageError):
                live_formal_gate_shadow(report, DAY, now=NOW)


if __name__ == "__main__":
    unittest.main()
