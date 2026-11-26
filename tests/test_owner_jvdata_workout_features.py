import sqlite3
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_jvdata_workout_features import parse_observation, observations_before
from windows_jvlink_workout_store import workout_record
from windows_jvlink_weekly_read import JvLocalCheckError
from test_windows_jvlink_workout_store import row


def example(spec, day=b"20261120", created=b"20261121"):
    raw=bytearray(row(spec,day=day))
    raw[3:11]=created
    offset=34 if spec=="SLOP" else 79
    raw[offset:offset+24]=b"052013003901400250130120"
    return bytes(raw)


class WorkoutFeatureTests(unittest.TestCase):
    def test_both_types_and_missing_wood_intervals(self):
        for spec in ("SLOP","WOOD"):
            with self.subTest(spec=spec):
                obs=parse_observation(example(spec),spec)
                self.assertEqual(obs["totalTenths"][4],520)
                self.assertEqual(obs["lastFurlongTenths"],120)
                self.assertEqual(obs["lastFurlongGainTenths"],10)
                if spec=="WOOD":
                    self.assertIsNone(obs["totalTenths"][10])
        raw=example("SLOP")
        self.assertIsNone(parse_observation(raw[:2]+b"0"+raw[3:],"SLOP"))
        with self.assertRaises(JvLocalCheckError):
            parse_observation(raw[:34]+b"0600"+raw[38:],"SLOP")

    def test_revision_cutoff_and_deletion(self):
        conn=sqlite3.connect(":memory:")
        try:
            conn.execute("CREATE TABLE manifest(key,value)")
            conn.executemany("INSERT INTO manifest VALUES(?,?)",[
                ("schema","arc-race-workout-1"),("dataspec","SLOP"),
                ("stream_completed","yes")])
            conn.execute("CREATE TABLE records(digest,workout_day,workout_key,created_day,category,raw)")
            old=example("SLOP")
            late=example("SLOP",created=b"20261128")
            delete=old[:2]+b"0"+b"20261125"+old[11:]
            for raw in (old,late,delete):
                conn.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",workout_record(raw,"SLOP"))
            horse={"1000000001"}
            first=observations_before(conn,"SLOP","20261125",horse)
            self.assertEqual(len(first["byPrivateHorseId"]["1000000001"]),1)
            second=observations_before(conn,"SLOP","20261126",horse)
            self.assertEqual(second["byPrivateHorseId"]["1000000001"],[])
            self.assertFalse(first["formalTrainingGradeReady"])
        finally:
            conn.close()


if __name__=="__main__":
    unittest.main()
