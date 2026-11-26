import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from windows_jvlink_history_workflow import acquire_missing, inspect
from windows_jvlink_2026_history_store import DATABASE, MIN_FREE, save_archive
from windows_jvlink_workout_store import save_workouts
from windows_jvlink_weekly_read import JvLocalCheckError
from test_windows_jvlink_day_history_preview import FakeJv, sources
from test_windows_jvlink_workout_store import row


class WorkflowTests(unittest.TestCase):
    def test_completed_sources_are_not_read_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            jv=FakeJv({"RACE":sources()["RACE"],"SLOP":[row("SLOP")],"WOOD":[row("WOOD")]})
            calls=[]
            def factory():
                calls.append(True)
                return jv
            with patch("windows_jvlink_history_workflow.save_archive",side_effect=lambda j,f:save_archive(j,f,free_bytes=lambda:MIN_FREE)), \
                 patch("windows_jvlink_history_workflow.save_workouts",side_effect=lambda j,f,s:save_workouts(j,f,s,free_bytes=lambda:MIN_FREE)):
                result=acquire_missing(folder,factory,emit=lambda _:None)
                self.assertEqual(list(result),["RACE","SLOP","WOOD"])
                self.assertEqual(result["RACE"],{"RA":1,"SE":4})
                self.assertEqual(result["WOOD"],{"records":1})
                self.assertEqual([x[0] for x in jv.opens],["RACE","SLOP","WOOD"])
                self.assertEqual(jv.closes,3)
                self.assertEqual(acquire_missing(folder,factory,emit=lambda _:None),result)
                self.assertEqual(len(calls),3)

    def test_failure_stops_later_reads_and_preserves_first_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            jv=FakeJv({"RACE":sources()["RACE"],"SLOP":[b"HC1bad"],"WOOD":[row("WOOD")]})
            with patch("windows_jvlink_history_workflow.save_archive",side_effect=lambda j,f:save_archive(j,f,free_bytes=lambda:MIN_FREE)), \
                 patch("windows_jvlink_history_workflow.save_workouts",side_effect=lambda j,f,s:save_workouts(j,f,s,free_bytes=lambda:MIN_FREE)):
                with self.assertRaises(JvLocalCheckError):
                    acquire_missing(folder,lambda:jv,emit=lambda _:None)
                self.assertEqual([x[0] for x in jv.opens],["RACE","SLOP"])
                self.assertEqual(inspect(folder),{"RACE":{"RA":1,"SE":4},"SLOP":None,"WOOD":None})
                second=FakeJv({"SLOP":[row("SLOP")],"WOOD":[row("WOOD")]})
                acquire_missing(folder,lambda:second,emit=lambda _:None)
                self.assertEqual([x[0] for x in second.opens],["SLOP","WOOD"])

    def test_invalid_archive_blocks_all_provider_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            (folder/DATABASE).write_bytes(b"not sqlite")
            calls=[]
            with self.assertRaises(JvLocalCheckError):
                acquire_missing(folder,lambda:calls.append(True),emit=lambda _:None)
            self.assertEqual(calls,[])
            self.assertEqual((folder/DATABASE).read_bytes(),b"not sqlite")


if __name__=="__main__":
    unittest.main()
