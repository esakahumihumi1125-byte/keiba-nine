import sqlite3
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from windows_jvlink_2026_history_store import save_archive, DATABASE, MIN_FREE
from windows_jvlink_history_walkforward import evaluate
from test_windows_jvlink_day_history_preview import FakeJv
from test_owner_jvdata_horse_history_preview import old_ra, sample
from test_jvdata_ra_se_candidate import replace


def result(day, created, race="01", bad=False):
    ra = old_ra(day=day, created=created, race=race)
    for a,b in ((881,883),(883,885),(885,887)):
        ra = replace(ra,a,b,"04")
    se = [replace(sample(n,day=day,race=race,finish=f"{n:02d}"),
                  3,11,created) for n in range(1,5)]
    return [ra,*se[:-1]] if bad else [ra,*se]


class WalkforwardTests(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            jv = FakeJv({"RACE":rows})
            save_archive(jv,path,free_bytes=lambda:MIN_FREE)
            conn = sqlite3.connect(path/DATABASE)
            try:
                report = evaluate(conn,as_of_day="20261126")
            finally:
                conn.close()
            return report

    def test_same_day_creation_is_excluded_and_prior_history_used_later(self):
        rows = (result("20260104","20260105")
                + result("20260105","20260106")
                + result("20260111","20260112")
                + result("20260118","20260119",bad=True))
        r = self.run_rows(rows)
        self.assertEqual(r["evaluatedRaces"],1)
        self.assertEqual(r["evaluatedRunners"],4)
        self.assertEqual(r["skippedRaces"]["prior_course_history_incomplete"],2)
        self.assertEqual(r["skippedRaces"]["missing_or_conflicting_final_rows"],1)
        self.assertLess(r["modelBrier"],r["uniformBrier"])
        self.assertFalse(r["prestartAvailabilityVerified"])
        self.assertFalse(r["modelSaved"])
        self.assertEqual(r["newProviderRequests"],0)

    def test_late_revisions_and_abnormal_groups_never_train(self):
        first = result("20260104","20260105")
        conflict = replace(first[-1],334,336,"01")
        r = self.run_rows(first+[conflict]+result("20260111","20260112"))
        self.assertEqual(r["evaluatedRaces"],0)
        self.assertIsNone(r["modelBrier"])
        self.assertFalse(r["formalTenFactorReady"])


if __name__ == "__main__":
    unittest.main()
