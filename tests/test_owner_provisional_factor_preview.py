"""Synthetic tests: source-comparable 7-factor references NEVER replace drafts."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_comparable_factor_preview import preview_comparable_factor_holds
from owner_provisional_factor_preview import (
    preview_provisional_seven_factors, VERSION
)
from test_owner_comparable_factor_preview import fixture, DAY, NOW


def issued_fixture():
    draft, automatic = fixture()
    r = draft["races"][0]
    r.update(status="provisional_draft", reason=None,
             first=[1, 2], second=[1, 2, 3, 4, 5],
             third=list(range(1, 9)), points=40, amountYen=4000,
             tickets=[[1, 2, 3], [2, 1, 3]],
             researchReceipt="IMMUTABLE-FIRST-SIGNED-REFERENCE")
    for n, runner in enumerate(r["runners"], 1):
        runner["recent"] = ("S", "A", "B", "C")[((n-1)//2)]
    draft["draftCount"], draft["holdCount"] = 1, 0
    return draft, automatic


class ProvisionalSevenReferenceTests(unittest.TestCase):
    def test_issued_two_factor_40_preserved_when_another_reference_available(self):
        draft, auto = issued_fixture()
        untouched = copy.deepcopy((draft, auto))
        out = preview_provisional_seven_factors(draft, auto, DAY, now=NOW)
        self.assertEqual((draft, auto), untouched)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(out["raceCount"], 1)
        self.assertEqual(out["reviewedPrestartDraftRaces"], 1)
        self.assertEqual(out["unsignedReferenceCount"], 1)
        self.assertEqual(out["diagnostics"]["preview"], 1)
        row = out["races"][0]
        self.assertEqual(row["status"], "provisional_comparable_research_only")
        self.assertEqual(row["comparedWeight"], 78)  # training30/recent3/course17/pace17/staff10/rotation1
        self.assertEqual(row["excludedKeys"], ["ground"])
        self.assertEqual(row["comparedKeys"], [
            "training", "recent", "course_distance", "pace",
            "jockey_stable", "rotation"])
        self.assertTrue(12 <= row["points"] <= 48)
        self.assertTrue(row["tiesNeverSplit"])
        self.assertTrue(row["missingNeverImputed"])
        self.assertEqual(row["points"], len(row["first"]) *
                         (len(row["second"])-1) *
                         (len(row["third"])-2))
        self.assertFalse(row["receiptIssued"])
        self.assertFalse(row["bettingReady"])
        self.assertEqual(out["ticketsIssued"], 0)
        self.assertEqual(out["newProviderRequests"], 0)
        self.assertFalse(out["changesExistingDrafts"])
        self.assertFalse(out["changesExistingReceipts"])
        self.assertFalse(out["changesExistingRoi"])
        for secret in ("IMMUTABLE-FIRST-SIGNED-REFERENCE",
                       "racekey", "horse_id", "idm", "jockey_index"):
            self.assertNotIn(secret, repr(out))

    def test_missing_common_course_or_workout_holds_one_reference(self):
        for condition in ("missing_pace", "missing_training",
                          "unknown_points", "different_roster",
                          "no_common_weight"):
            draft, auto = issued_fixture()
            if condition == "missing_pace":
                f = auto["races"][0]["horses"][0]["factors"]["pace"]
                f.update(score=None, points=None, grade="未評価")
            if condition == "missing_training":
                draft["races"][0]["runners"][0]["training"] = "未評価"
            if condition == "unknown_points":
                auto["races"][0]["horses"][0]["factors"]["pace"]["points"] = float("nan")
            if condition == "different_roster":
                auto["races"][0]["horses"][0]["number"] = 17
            if condition == "no_common_weight":
                for horse in auto["races"][0]["horses"]:
                    for key in ("course_distance", "pace"):
                        horse["factors"][key].update(
                            score=None, points=None, grade="未評価")
            result = preview_provisional_seven_factors(draft, auto, DAY, now=NOW)
            self.assertEqual(result["unsignedReferenceCount"], 0, condition)
            self.assertEqual(result["ticketsIssued"], 0)

    def test_prestart_only_future_late_and_other_days_fully_blocked(self):
        d, a = issued_fixture()
        late = datetime.fromisoformat("2026-11-21T11:00:00+09:00")
        out = preview_provisional_seven_factors(d, a, DAY, now=late)
        self.assertEqual(out["unsignedReferenceCount"], 0)
        self.assertEqual(out["diagnostics"]["time_unavailable"], 1)
        # A previously held race must NOT be accidentally promoted to a
        # new provisional draft or a signed ticket.
        held, scores = fixture()
        held_before = copy.deepcopy((held, scores))
        out = preview_provisional_seven_factors(held, scores, DAY, now=NOW)
        self.assertEqual(out["reviewedPrestartDraftRaces"], 0)
        self.assertEqual(out["unsignedReferenceCount"], 0)
        original_hold = preview_comparable_factor_holds(held, scores, DAY, now=NOW)
        self.assertEqual(original_hold["unsignedReferenceCount"], 1)
        self.assertEqual((held, scores), held_before)

    def test_36_race_batch_only_compares_prestart_issued_races(self):
        d, a = issued_fixture()
        rows, optional = [], []
        for track in ("東京", "京都", "福島"):
            for number in range(1, 13):
                base = copy.deepcopy(d["races"][0])
                auto = copy.deepcopy(a["races"][0])
                base["track"], base["race"] = track, number
                auto["track"], auto["race"] = track, number
                rows.append(base)
                optional.append(auto)
        d["races"], a["races"] = rows, optional
        d["raceCount"], d["draftCount"], d["holdCount"] = 36, 36, 0
        # One held race is excluded from the alternative research output.
        d["races"][5]["status"] = "hold"
        d["races"][5]["reason"] = "missing_factors"
        d["draftCount"], d["holdCount"] = 35, 1
        before = copy.deepcopy((d, a))
        out = preview_provisional_seven_factors(d, a, DAY, now=NOW)
        self.assertEqual(out["raceCount"], 36)
        self.assertEqual(out["reviewedPrestartDraftRaces"], 35)
        self.assertEqual(out["unsignedReferenceCount"], 35)
        self.assertEqual(len({(x["track"], x["race"]) for x in out["races"]}), 35)
        self.assertEqual((d, a), before)

    def test_untrusted_source_rejected_without_altering_ticket(self):
        bad = [
            lambda d,a: d.update(date="20261122"),
            lambda d,a: d.update(officialJraVerified=True),
            lambda d,a: a.update(modelCalibrated=True),
            lambda d,a: a.update(newProviderRequests=1),
            lambda d,a: a["races"].append(copy.deepcopy(a["races"][0])),
            lambda d,a: a["races"][0].update(track="阪神"),
            lambda d,a: d.update(raceCount=2),
        ]
        for change in bad:
            d,a=issued_fixture()
            change(d,a)
            with self.assertRaises(CoverageError):
                preview_provisional_seven_factors(d,a,DAY,now=NOW)


if __name__ == "__main__":
    unittest.main()
