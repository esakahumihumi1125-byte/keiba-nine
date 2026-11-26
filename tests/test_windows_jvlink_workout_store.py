import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from windows_jvlink_workout_store import save_workouts, workout_record, SPECS, MIN_FREE, JvLocalCheckError
from test_windows_jvlink_day_history_preview import FakeJv


def row(spec, category=b"1", day=b"20261120"):
    kind,length=SPECS[spec]
    return kind+category+b"20261121"+b"0"+day+b"0715"+b"1000000001"+b"0"*(length-36)+b"\r\n"


class WorkoutArchiveTests(unittest.TestCase):
    def test_both_specs_keep_deletions_and_distinct_revisions(self):
        for spec in SPECS:
            with self.subTest(spec=spec), tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)
                r=row(spec)
                jv=FakeJv({spec:[r,r,row(spec,b"0"),row(spec,day=b"20251120")]})
                self.assertEqual(save_workouts(jv,folder,spec,free_bytes=lambda:MIN_FREE),2)
                self.assertEqual(jv.opens[0][:3],(spec,"20260101000000",1))
                self.assertEqual(jv.closes,1)
                conn=sqlite3.connect(folder/("jvdata-2026-"+spec.lower()+".sqlite3"))
                try:
                    self.assertEqual(set(conn.execute("SELECT category FROM records")),{("0",),("1",)})
                    self.assertEqual(dict(conn.execute("SELECT key,value FROM manifest"))["coverage_verified"],"no")
                finally:
                    conn.close()
                with self.assertRaisesRegex(JvLocalCheckError,"WORKOUT_EXISTS"):
                    save_workouts(jv,folder,spec,free_bytes=lambda:MIN_FREE)
                self.assertEqual(len(jv.opens),1)

    def test_invalid_record_and_incomplete_stream_are_not_saved(self):
        for data,kwargs in (([b"HC1bad"],{}),([row("SLOP")],{"max_steps":1}),
                            ([row("SLOP",day=b"20261131")],{})):
            with tempfile.TemporaryDirectory() as tmp:
                folder=Path(tmp)
                jv=FakeJv({"SLOP":data})
                with self.assertRaises(JvLocalCheckError):
                    save_workouts(jv,folder,"SLOP",free_bytes=lambda:MIN_FREE,**kwargs)
                self.assertEqual(list(folder.iterdir()),[])
                self.assertEqual(jv.closes,1)

    def test_disk_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            jv=FakeJv({"WOOD":[row("WOOD")]})
            with self.assertRaisesRegex(JvLocalCheckError,"WORKOUT_DISK_SPACE_LOW"):
                save_workouts(jv,Path(tmp),"WOOD",free_bytes=lambda:MIN_FREE-1)
            self.assertEqual(jv.opens,[])


if __name__=="__main__":
    unittest.main()
