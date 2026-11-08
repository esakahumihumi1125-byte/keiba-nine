"""Synthetic-only /tze recent performance research regressions."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_recent_hypothesis import build_recent_hints, summarize_recent_hints
from jrdb_coverage import CoverageError
from test_jrdb_evidence_readiness import sample


def fixture():
    programme, entries, _, _ = sample()
    histories = [
        {"racekey": "05264b01", "racedate": "20261101",
         "horse_number": "01", "horse_id": "2328aaa95a05",
         "race_back_1_racedate": "20261025",
         "race_back_1_order_of_finish": 1, "race_back_1_idm": 78,
         "race_back_1_corner4_order": 2, "race_back_1_later3f_time": 34.5,
         "race_back_2_racedate": "20261011",
         "race_back_2_order_of_finish": 3, "race_back_2_idm": 70,
         "race_back_2_corner4_order": 5, "race_back_2_later3f_time": 35.8,
         "race_back_3_racedate": "20260920",
         "race_back_3_order_of_finish": 4, "race_back_3_idm": 69,
         "race_back_3_corner4_order": 4, "race_back_3_later3f_time": 35.4,
         "race_back_1_confirmed_win_odds": 999.0,
         "horse_name": "SECRET-PAID-HORSE"},
        {"racekey": "05264b01", "racedate": "20261101",
         "horse_number": "02", "horse_id": "2328aaa95a06",
         "race_back_1_racedate": "20261025",
         "race_back_1_order_of_finish": 2, "race_back_1_idm": "60.0",
         "race_back_2_racedate": "20261011",
         "race_back_2_order_of_finish": "4", "race_back_2_idm": 50,
         "race_back_1_confirmed_win_odds": 1.1},
    ]
    return programme, entries, histories


class RecentHypothesisTests(unittest.TestCase):
    def audit(self, p_e_z=None):
        p, e, z = p_e_z or fixture()
        return build_recent_hints(p, e, z, "20261101")

    def test_provisional_recent_form_grades(self):
        rows = self.audit()
        self.assertEqual(rows[0]["byNumber"]["01"]["grade"], "S")
        self.assertEqual(rows[0]["byNumber"]["02"]["grade"], "A")
        self.assertEqual(rows[1]["byNumber"]["01"]["grade"], "未評価")
        self.assertEqual(rows[0]["byNumber"]["01"]["topThree"], 2)
        self.assertEqual(rows[0]["byNumber"]["01"]["frontAtFourth"], 2)
        self.assertEqual(rows[0]["byNumber"]["01"]["late3fObserved"], 3)
        self.assertFalse(rows[0]["predictionReady"])

    def test_odds_do_not_influence_grade(self):
        first = self.audit()
        p, e, z = fixture()
        z[0]["race_back_1_confirmed_win_odds"] = 1.01
        z[1]["race_back_1_confirmed_win_odds"] = 999999
        self.assertEqual(first, self.audit((p, e, z)))

    def test_no_debutant_imputation(self):
        p, e, z = fixture()
        z[1].pop("race_back_2_racedate")
        z[1].pop("race_back_2_order_of_finish")
        z[1].pop("race_back_2_idm")
        self.assertEqual(self.audit((p, e, z))[0]["byNumber"]["02"]["grade"], "未評価")

    def test_two_complete_runs_required(self):
        p, e, z = fixture()
        z[0].pop("race_back_1_idm")
        z[0].pop("race_back_3_idm")
        self.assertEqual(self.audit((p, e, z))[0]["byNumber"]["01"]["grade"], "未評価")

    def test_missing_date_with_result_is_invalid(self):
        p, e, z = fixture()
        z[0].pop("race_back_2_racedate")
        with self.assertRaises(CoverageError):
            self.audit((p, e, z))

    def test_future_and_disordered_history_invalid(self):
        for value in ("20261101", "20261230", "20261030", "20260230"):
            with self.subTest(value=value):
                p, e, z = fixture()
                z[0]["race_back_2_racedate"] = value
                with self.assertRaises(CoverageError):
                    self.audit((p, e, z))

    def test_official_beta_tenths_seconds_are_decoded(self):
        p, e, z = fixture()
        z[0]["race_back_1_later3f_time"] = 360  # JRDB: 36.0s
        z[0]["race_back_2_later3f_time"] = "358"  # JRDB: 35.8s
        z[0]["race_back_3_later3f_time"] = 0  # no valid split
        from jrdb_recent_hypothesis import _extract
        values = _extract(z[0], "20261101")
        self.assertEqual(values[0]["later3f"], 36.0)
        self.assertEqual(values[1]["later3f"], 35.8)
        self.assertIsNone(values[2]["later3f"])
        row = self.audit((p, e, z))[0]["byNumber"]["01"]
        self.assertEqual(row["late3fObserved"], 2)
        self.assertEqual(row["grade"], "S")

    def test_zero_filled_beta_history_slots_do_not_create_fake_starts(self):
        p, e, z = fixture()
        z[0].update({
            "race_back_4_racedate": "20260920",  # duplicate stub
            "race_back_4_order_of_finish": 0,
            "race_back_4_idm": 0,
            "race_back_4_later3f_time": 0,
            "race_back_4_corner4_order": 0,
            "race_back_5_racedate": "20260920",
            "race_back_5_order_of_finish": 0,
            "race_back_5_idm": 0,
            "race_back_5_later3f_time": 0,
            "race_back_5_corner4_order": 0,
        })
        result = self.audit((p, e, z))[0]["byNumber"]["01"]
        self.assertEqual(result["datedRuns"], 3)
        self.assertEqual(result["completedRuns"], 3)
        self.assertEqual(result["topThree"], 2)
        self.assertEqual(result["grade"], "S")

    def test_zero_finishing_position_is_not_a_top_three_finish(self):
        p, e, z = fixture()
        z[0]["race_back_1_order_of_finish"] = 0
        z[0]["race_back_1_corner4_order"] = 0
        row = self.audit((p, e, z))[0]["byNumber"]["01"]
        self.assertEqual(row["completedRuns"], 2)
        self.assertEqual(row["topThree"], 1)
        self.assertEqual(row["frontAtFourth"], 1)

    def test_bad_numeric_values_rejected(self):
        for field, value in (
            ("race_back_1_idm", 400),
            ("race_back_1_idm", True),
            ("race_back_1_idm", "72x"),
            ("race_back_1_idm", float("inf")),
            ("race_back_1_later3f_time", -5),
            ("race_back_1_corner4_order", 3.4),
            ("race_back_1_order_of_finish", -1),
        ):
            with self.subTest(field=field, value=value):
                p, e, z = fixture()
                z[0][field] = value
                with self.assertRaises(CoverageError):
                    self.audit((p, e, z))

    def test_duplicated_source_row_invalid(self):
        p, e, z = fixture()
        z.append(copy.deepcopy(z[0]))
        with self.assertRaises(CoverageError):
            self.audit((p, e, z))

    def test_wrong_horse_id_rejected(self):
        p, e, z = fixture()
        z[0]["horse_id"] = "2328aaa95a99"
        with self.assertRaises(CoverageError):
            self.audit((p, e, z))

    def test_horse_number_vs_id_conflict_rejected(self):
        p, e, z = fixture()
        z[0]["horse_number"] = "02"
        with self.assertRaises(CoverageError):
            self.audit((p, e, z))

    def test_redacted_aggregate_has_no_raw_info(self):
        summary = summarize_recent_hints(self.audit())
        self.assertEqual(summary["races"][0]["gradeCounts"]["S"], 1)
        self.assertEqual(summary["races"][0]["gradeCounts"]["A"], 1)
        self.assertEqual(summary["races"][1]["gradeCounts"]["未評価"], 1)
        self.assertEqual(summary["races"][0]["frontAtFourthObservations"], 2)
        self.assertFalse(summary["predictionReady"])
        for excluded in ("2328aaa95a05", "SECRET-PAID-HORSE",
                         "999.0", "racekey", "byNumber", "idm"):
            self.assertNotIn(excluded, repr(summary))

    def test_invalid_aggregate_rejected(self):
        rows = self.audit()
        rows[0]["byNumber"]["01"]["grade"] = "Z"
        with self.assertRaises(ValueError):
            summarize_recent_hints(rows)

    def test_immutability(self):
        data = fixture()
        original = copy.deepcopy(data)
        self.audit(data)
        self.assertEqual(original, data)


if __name__ == "__main__":
    unittest.main()
