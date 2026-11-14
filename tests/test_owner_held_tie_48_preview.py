"""No guessed tie-breaks: unsigned rescue of formerly held score groups."""
import copy
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import build_owner_auto_drafts
from owner_held_tie_48_preview import preview_held_ties_48,VERSION
from test_jrdb_owner_auto_draft import programme,research,JST,DAY
PRESTART=datetime(2099,1,1,9,tzinfo=JST)

def build(pairs,now=PRESTART):
    return build_owner_auto_drafts(
        programme(headcount=len(pairs)),research(pairs),DAY,now=now)


class HeldTie48Tests(unittest.TestCase):
    def test_solo_clear_leader_preserves_all_four_ambiguous_second_runners(self):
        # The usual first-2/3 formation cannot be selected without
        # splitting four tied A horses. One S is alone ahead of them.
        scores=[("S","C")]+[("A","C")]*4+[("B","C")]*5
        report=build(scores)
        self.assertEqual(report["draftCount"],0)
        self.assertEqual(report["races"][0]["reason"],"ambiguous_equal_grade_boundary")
        before=copy.deepcopy(report)
        out=preview_held_ties_48(report,DAY,now=PRESTART)
        self.assertEqual(out["version"],VERSION)
        self.assertEqual(out["reviewedPrestartTieHolds"],1)
        self.assertEqual(out["unsignedReferenceCount"],1)
        r=out["races"][0]
        self.assertEqual(r["first"],[1])
        self.assertEqual(r["second"],[1,2,3,4,5])
        self.assertEqual(r["third"],list(range(1,11)))
        self.assertEqual(r["points"],32)
        self.assertTrue(r["allTiedScoreBoundariesUnsplit"])
        self.assertFalse(r["receiptIssued"])
        self.assertFalse(r["bettingReady"])
        self.assertEqual(out["ticketsIssued"],0)
        self.assertEqual(out["newProviderRequests"],0)
        self.assertEqual(before,report)

    def test_highly_ambiguous_first_tier_remains_held(self):
        scores=[("S","C")]*4+[("A","C")]*6
        report=build(scores)
        self.assertEqual(report["races"][0]["reason"],"ambiguous_equal_grade_boundary")
        out=preview_held_ties_48(report,DAY,now=PRESTART)
        self.assertEqual(out["unsignedReferenceCount"],0)
        self.assertEqual(out["races"],[])

    def test_unknown_recent_cannot_be_imputed(self):
        scores=[("S","未評価")]+[("A","C")]*4+[("B","C")]*5
        report=build(scores)
        self.assertEqual(report["races"][0]["reason"],"missing_factors")
        out=preview_held_ties_48(report,DAY,now=PRESTART)
        self.assertEqual(out["unsignedReferenceCount"],0)

    def test_does_not_change_existing_complete_draft(self):
        report=build([("S","S"),("S","A"),("A","A"),
                      ("A","B"),("B","B"),("B","C"),("C","C")])
        self.assertEqual(report["draftCount"],1)
        out=preview_held_ties_48(report,DAY,now=PRESTART)
        self.assertEqual(out["unsignedReferenceCount"],0)

    def test_after_start_never_constructs_new_candidates(self):
        scores=[("S","C")]+[("A","C")]*4+[("B","C")]*5
        pre=build(scores)
        later=datetime(2099,1,1,12,1,tzinfo=JST)
        self.assertEqual(preview_held_ties_48(pre,DAY,now=later)["races"],[])
        post=build(scores,now=later)
        self.assertEqual(post["races"][0]["reason"],"after_provisional_off")
        self.assertEqual(preview_held_ties_48(post,DAY,now=later)["races"],[])

    def test_reject_untrusted_input_without_altering_original(self):
        scores=[("S","C")]+[("A","C")]*4+[("B","C")]*5
        report=build(scores)
        broken=copy.deepcopy(report)
        broken["officialJraVerified"]=True
        with self.assertRaises(CoverageError):
            preview_held_ties_48(broken,DAY,now=PRESTART)
        with self.assertRaises(CoverageError):
            preview_held_ties_48(report,DAY,now=datetime(2099,1,1,9))
        tampered=copy.deepcopy(report)
        tampered["races"][0]["runners"][0]["weightedResearchPoints"]=42
        self.assertEqual(preview_held_ties_48(tampered,DAY,now=PRESTART)["races"],[])


if __name__=="__main__":
    unittest.main()
