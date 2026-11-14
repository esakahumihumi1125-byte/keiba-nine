"""Synthetic, no-provider-call /tcy delivery breakdown and redaction tests."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_training_source_delivery import observe_training_source_delivery as inspect
from jrdb_coverage import CoverageError
from test_jrdb_training_hypothesis import setup

DAY="20261101"


def source():
    p,e,t=setup()
    return p,e,t,[]


def check(data,reads=4):
    return inspect(*data,DAY,source_read_count=reads)


class OwnerTrainingDeliveryTests(unittest.TestCase):
    def test_all_core_tcy_rows_cover_identity_and_two_indexes(self):
        inputs=source()
        original=copy.deepcopy(inputs)
        info=check(inputs)
        self.assertEqual(inputs,original)
        self.assertEqual(info["status"],"training_index_rows_present")
        self.assertEqual(info["raceCount"],2)
        self.assertEqual(info["entryRowsReturned"],3)
        self.assertEqual(info["entriesMatchedDayProgramme"],3)
        self.assertEqual(info["trainingRowsReturned"],3)
        self.assertEqual(info["trainingRowsKnownRace"],3)
        self.assertEqual(info["trainingRowsCurrentRaceDate"],3)
        self.assertEqual(info["trainingLinkedRunners"],3)
        self.assertEqual(info["trainingRunnersWithBothIndices"],3)
        self.assertEqual(info["trainingRacesWithBothIndices"],2)
        self.assertEqual(info["trainingIdentityConflicts"],0)
        self.assertEqual(info["trainingDuplicateRunnerRows"],0)
        self.assertEqual(info["newProviderRequests"],0)
        self.assertFalse(info["officialJraVerified"])
        self.assertFalse(info["predictionReady"])
        for private in ("horse_id","horse_number","racekey","oikirisisu",
                        "siagarisisu","NONPUBLIC","2328aaa95a05"):
            self.assertNotIn(private,repr(info))

    def test_zero_rows_is_not_35_real_losses(self):
        p,e,t,z=source()
        result=check((p,e,[],z))
        self.assertEqual(result["status"],"training_empty_response")
        self.assertEqual(result["entriesMatchedDayProgramme"],3)
        self.assertEqual(result["trainingRowsReturned"],0)
        self.assertEqual(result["trainingLinkedRunners"],0)
        self.assertEqual(result["trainingRunnersWithBothIndices"],0)
        self.assertFalse(result["scoreReady"])

    def test_foreign_race_and_wrong_day_are_distinct(self):
        p,e,t,z=source()
        wrong=[dict(t[0],racekey="99999999",private_metric="SECRET")]
        result=check((p,e,wrong,z))
        self.assertEqual(result["status"],"training_no_current_race")
        self.assertEqual(result["trainingRowsKnownRace"],0)
        self.assertNotIn("SECRET",repr(result))
        wrong=[dict(t[0],racedate="20261102")]
        result=check((p,e,wrong,z))
        self.assertEqual(result["status"],"training_current_race_date_mismatch")
        self.assertEqual(result["trainingRowsCurrentRaceDate"],0)

    def test_linked_but_missing_numeric_indexes_is_not_a_grade(self):
        p,e,t,z=source()
        rows=copy.deepcopy(t)
        rows[0]["siagarisisu"]=None
        result=check((p,e,rows,z))
        self.assertEqual(result["status"],"training_partial_index_coverage")
        self.assertEqual(result["trainingLinkedRunners"],3)
        self.assertEqual(result["trainingRunnersWithBothIndices"],2)
        rows=copy.deepcopy(t)
        for item in rows:item["siagarisisu"]=None
        result=check((p,e,rows,z))
        self.assertEqual(result["status"],"training_indices_missing")
        self.assertEqual(result["trainingRunnersWithBothIndices"],0)

    def test_identity_mismatch_and_duplicate_fail_readiness_not_source_call(self):
        p,e,t,z=source()
        rows=copy.deepcopy(t)
        rows[0]["horse_id"]="2328aaa95a99"
        result=check((p,e,rows,z))
        self.assertEqual(result["status"],"training_identity_conflict")
        self.assertEqual(result["trainingIdentityConflicts"],1)
        self.assertEqual(result["trainingRunnersWithBothIndices"],2)
        rows=copy.deepcopy(t);rows.append(copy.deepcopy(rows[0]))
        result=check((p,e,rows,z))
        self.assertEqual(result["status"],"training_identity_conflict")
        self.assertEqual(result["trainingDuplicateRunnerRows"],1)
        self.assertEqual(result["trainingRunnersWithBothIndices"],2)

    def test_unknown_runner_only_is_not_reclassified_as_empty(self):
        p,e,t,z=source()
        row=copy.deepcopy(t[0])
        row.update(horse_number=None,horse_id=None)
        result=check((p,e,[row],z))
        self.assertEqual(result["status"],"training_no_runner_match")
        self.assertEqual(result["trainingRowsCurrentRaceDate"],1)
        self.assertEqual(result["trainingLinkedRunners"],0)

    def test_no_programme_is_one_read_not_fabricated_data(self):
        result=inspect([],[],[],[],"20261102",source_read_count=1)
        self.assertEqual(result["status"],"programme_not_returned")
        self.assertEqual(result["sourceReadCount"],1)
        self.assertEqual(result["raceCount"],0)
        with self.assertRaises(CoverageError):
            inspect([],[],[],[],"20261102",source_read_count=4)
        # Four empty collections with count 4 are still an invalid
        # upstream call shape in the protected integration, though the
        # pure aggregator only explains its empty programme.
    
    def test_malformed_input_rejected(self):
        p,e,t,z=source()
        for bad in ("20260230","2026-11-01"):
            with self.assertRaises(CoverageError):
                inspect(p,e,t,z,bad,source_read_count=4)
        with self.assertRaises(CoverageError):
            inspect(p,e,t,z,DAY,source_read_count=1)
        with self.assertRaises(CoverageError):
            inspect(p,e,[42],z,DAY,source_read_count=4)


if __name__=="__main__":
    unittest.main()
