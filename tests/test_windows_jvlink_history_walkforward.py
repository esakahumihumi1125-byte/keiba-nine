import sqlite3
import tempfile
import unittest
from unittest.mock import patch
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

    def test_partial_coverage_preserves_unknowns_and_strict_chronology(self):
        records = [
            ("202601010501", ("20260102", "05", "芝", 1400,
                             [("a",1),("b",2),("c",3),("d",4)]), None),
            ("202601020501", ("20260103", "05", "芝", 1500,
                             [("a",1),("e",2),("f",3),("g",4)]), None),
            ("202601040501", ("20260105", "05", "芝", 1600,
                             [("a",1),("h",2),("i",3),("j",4)]), None),
            ("202601060501", ("20260107", "05", "ダート", 1600,
                             [("a",1),("k",2),("l",3),("m",4)]), None),
            ("202601080601", ("20260109", "06", "芝", 1600,
                             [("a",1),("n",2),("o",3),("p",4)]), None),
            ("202601100501", ("20260111", "05", "芝", 2000,
                             [("a",1),("q",2),("r",3),("s",4)]), None),
        ]
        with patch("windows_jvlink_history_walkforward.completed_races",
                   return_value=iter(records)):
            report = evaluate(None, as_of_day="20261126")
        self.assertEqual(report["evaluatedRaces"], 0)
        partial = report["partialCoverage"]
        self.assertEqual(partial["evaluatedRaces"], 1)
        self.assertEqual(partial["fieldRunners"], 4)
        self.assertEqual(partial["observedRunners"], 1)
        self.assertEqual(partial["unknownRunners"], 3)
        self.assertFalse(partial["missingEvidenceGraded"])
        self.assertLess(partial["modelBrier"], partial["uniformBrier"])
        self.assertLess(partial["observedModelBrier"], partial["observedUniformBrier"])

    def test_late_revisions_and_abnormal_groups_never_train(self):
        first = result("20260104","20260105")
        conflict = replace(first[-1],334,336,"01")
        r = self.run_rows(first+[conflict]+result("20260111","20260112"))
        self.assertEqual(r["evaluatedRaces"],0)
        self.assertIsNone(r["modelBrier"])
        self.assertFalse(r["formalTenFactorReady"])


if __name__ == "__main__":
    unittest.main()
