"""Research-only JRDB /tcy workout index hypotheses with synthetic inputs."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_training_hypothesis import (
    build_training_hints, summarize_training_hints, VERSION
)
from jrdb_coverage import CoverageError
from test_jrdb_evidence_readiness import sample


def setup():
    p, e, t, z = sample()
    t[0]["oikirisisu"] = 80
    t[0]["siagarisisu"] = 78
    t[1]["oikirisisu"] = 60
    t[1]["siagarisisu"] = 62
    t.append({"racekey": "08264b01", "racedate": "20261101",
              "horse_number": "01", "horse_id": "2328aaa95a07",
              "oikirisisu": 48, "siagarisisu": 45})
    return p, e, t


class TrainingHypothesisTests(unittest.TestCase):
    def audit(self, inputs=None):
        p, e, t = inputs if inputs is not None else setup()
        return build_training_hints(p, e, t, "20261101")

    def test_private_hints_grade_only_when_both_indexes_exist(self):
        a, b = self.audit()
        self.assertEqual(a["gradesByNumber"], {"01": "S", "02": "A"})
        self.assertEqual(b["gradesByNumber"], {"01": "B"})
        self.assertFalse(a["predictionReady"])

    def test_thresholds_are_explicitly_hypothetical(self):
        p, e, t = setup()
        t[0].update(oikirisisu=40, siagarisisu=90)
        self.assertEqual(self.audit((p, e, t))[0]["gradesByNumber"]["01"], "C")
        t[0].update(oikirisisu=60, siagarisisu=60)
        self.assertEqual(self.audit((p, e, t))[0]["gradesByNumber"]["01"], "A")
        t[0].update(oikirisisu=75, siagarisisu=75)
        self.assertEqual(self.audit((p, e, t))[0]["gradesByNumber"]["01"], "S")

    def test_missing_index_is_never_imputed(self):
        p, e, t = setup()
        t[0]["siagarisisu"] = None
        self.assertEqual(self.audit((p, e, t))[0]["gradesByNumber"]["01"], "未評価")
        t.pop()
        self.assertEqual(self.audit((p, e, t))[1]["gradesByNumber"], {"01": "未評価"})

    def test_only_aggregate_counts_are_exposed(self):
        hints = self.audit()
        redacted = summarize_training_hints(hints)
        self.assertEqual(redacted["version"], VERSION)
        self.assertEqual(redacted["races"][0]["gradeCounts"]["S"], 1)
        self.assertEqual(redacted["races"][0]["gradeCounts"]["A"], 1)
        self.assertEqual(redacted["races"][1]["gradeCounts"]["B"], 1)
        self.assertFalse(redacted["predictionReady"])
        self.assertNotIn("2328aaa95a05", repr(redacted))
        self.assertNotIn("racekey", repr(redacted))
        self.assertNotIn("oikirisisu", repr(redacted))

    def test_wrong_identity_is_rejected(self):
        p, e, t = setup()
        t[0]["horse_number"] = "02"
        with self.assertRaises(CoverageError):
            self.audit((p, e, t))

    def test_duplicate_workout_rows_fail_closed(self):
        p, e, t = setup()
        t.append(copy.deepcopy(t[0]))
        with self.assertRaises(CoverageError):
            self.audit((p, e, t))

    def test_bad_numbers_fail_closed(self):
        for value in ("80", True, float("inf"), float("nan"), -1, 201, [], {}):
            with self.subTest(value=value):
                p, e, t = setup()
                t[0]["oikirisisu"] = value
                with self.assertRaises(CoverageError):
                    self.audit((p, e, t))

    def test_nonmatching_date_and_unknown_horse_are_rejected(self):
        p, e, t = setup()
        t[0]["racedate"] = "20261102"
        with self.assertRaises(CoverageError):
            self.audit((p, e, t))
        p, e, t = setup()
        t[0]["horse_id"] = "2328aaa95a99"
        with self.assertRaises(CoverageError):
            self.audit((p, e, t))

    def test_input_immutable(self):
        data = setup()
        before = copy.deepcopy(data)
        self.audit(data)
        self.assertEqual(data, before)

    def test_source_absence_does_not_auto_select_winners(self):
        p, e, t = setup()
        t.clear()
        summary = summarize_training_hints(self.audit((p, e, t)))
        self.assertTrue(all(row["graded"] == 0 for row in summary["races"]))
        self.assertTrue(all(row["missing"] > 0 for row in summary["races"]))
        self.assertFalse(summary["predictionReady"])


if __name__ == "__main__":
    unittest.main()
