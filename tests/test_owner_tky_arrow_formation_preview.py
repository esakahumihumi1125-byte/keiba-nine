"""No-provider, no-wager tests for complete-roster expert-arrow previews."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_tky_training_index_study import tky_training_index_study
from owner_tky_arrow_formation_preview import preview_tky_arrow_formations
from test_owner_tky_training_index_study import fixture, DAY, NOW, LATE


def complete():
    programme, entries, report = fixture()
    # Seven actual source-shaped runner observations, but synthetic ONLY.
    programme[0]["headcount"] = 7
    raw = entries[0]
    entries[:] = []
    arrows = ("1", "1", "2", "2", "3", "3", "4")
    for i, arrow in enumerate(arrows, 1):
        row = dict(raw)
        row["horse_number"] = f"{i:02d}"
        row["horse_id"] = f"2328aaa95a{i:02d}"
        row["training_arrow"] = arrow
        row["training_index"] = str(20-i)
        entries.append(row)
    # Mirror the private-service draft's explicit no-auto-purchase flag.
    report["autoPurchase"] = False
    report["races"][0]["horseCount"] = 7
    report["races"][0]["runners"] = [
        {"number": i, "training": "未評価", "recent": "C"}
        for i in range(1, 8)
    ]
    study = tky_training_index_study(programme, entries, report, DAY, now=NOW)
    return programme, entries, report, study


class TkyArrowFormationPreviewTests(unittest.TestCase):
    def test_all_horses_observed_forty_distinct_reference_combinations(self):
        p,e,r,s = complete()
        original=copy.deepcopy((p,e,r,s))
        out=preview_tky_arrow_formations(r,s,DAY,now=NOW)
        self.assertEqual((p,e,r,s),original)
        self.assertEqual(out["safeReferenceCount"],1)
        self.assertEqual(out["reviewedPrestartStudies"],1)
        row=out["races"][0]
        self.assertEqual(row["first"],[1,2])
        self.assertEqual(row["second"],[1,2,3,4,5])
        self.assertEqual(row["third"],list(range(1,8)))
        self.assertEqual(row["points"],40)
        self.assertEqual(row["rankingScope"],"arrow_then_index_rank")
        self.assertFalse(row["partialIndexIgnored"])
        self.assertFalse(row["bettingReady"])
        self.assertFalse(row["receiptIssued"])
        self.assertFalse(row["officialJraVerified"])
        self.assertEqual(out["ticketsIssued"],0)
        self.assertEqual(out["newProviderRequests"],0)
        self.assertFalse(out["changesExistingDrafts"])
        for private in ("PAID-TEST-HORSE","horse_id","training_index","racekey"):
            self.assertNotIn(private,repr(out))

    def test_partial_indexes_do_not_assign_a_missing_horse_last_place(self):
        p,e,r,s=complete()
        e[6]["training_index"]=None
        s=tky_training_index_study(p,e,r,DAY,now=NOW)
        out=preview_tky_arrow_formations(r,s,DAY,now=NOW)
        self.assertEqual(out["safeReferenceCount"],1)
        row=out["races"][0]
        self.assertEqual(row["rankingScope"],"arrow_only")
        self.assertTrue(row["partialIndexIgnored"])
        for size in (len(row["first"]),len(row["second"]),len(row["third"])):
            self.assertLessEqual(size,7)
        self.assertLessEqual(row["points"],48)

    def test_missing_arrow_holds_entire_research_example(self):
        p,e,r,s=complete()
        e[6]["training_arrow"]=None
        s=tky_training_index_study(p,e,r,DAY,now=NOW)
        out=preview_tky_arrow_formations(r,s,DAY,now=NOW)
        self.assertEqual(out["safeReferenceCount"],0)
        self.assertEqual(out["races"],[])

    def test_same_arrow_and_same_index_never_splits_horse_numbers(self):
        p,e,r,s=complete()
        for row in e:
            row["training_arrow"]="3"
            row["training_index"]=None
        s=tky_training_index_study(p,e,r,DAY,now=NOW)
        out=preview_tky_arrow_formations(r,s,DAY,now=NOW)
        self.assertEqual(out["safeReferenceCount"],0)
        self.assertEqual(out["races"],[])

    def test_zero_after_start_even_if_earlier_snapshot_had_horses(self):
        _,_,r,s=complete()
        out=preview_tky_arrow_formations(r,s,DAY,now=LATE)
        self.assertEqual(out["safeReferenceCount"],0)
        self.assertEqual(out["races"],[])

    def test_stale_untrusted_or_mismatched_snapshot_fails_closed(self):
        _,_,r,s=complete()
        for field,value in (
            ("officialJraVerified",True),("modelCalibrated",True),
            ("training30Ready",True),("ticketsIssued",1),
        ):
            broken=copy.deepcopy(s)
            broken[field]=value
            with self.subTest(field=field),self.assertRaises(CoverageError):
                preview_tky_arrow_formations(r,broken,DAY,now=NOW)
        wrong=copy.deepcopy(r)
        wrong["races"][0]["status"]="provisional_draft"
        with self.assertRaises(CoverageError):
            preview_tky_arrow_formations(wrong,s,DAY,now=NOW)
        with self.assertRaises(CoverageError):
            preview_tky_arrow_formations(r,s,DAY,now=datetime(2099,1,1,9))


if __name__=="__main__":
    unittest.main()
