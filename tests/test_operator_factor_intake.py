"""Synthetic, stateless owner-operator note intake checks."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from operator_factor_intake import validate_operator_factor_note

NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")


def note():
    return {
        "recordType": "operator_factor_note", "date": "20261107",
        "track": "京都", "race": 1, "horseNumber": "01",
        "factor": "training", "state": "noted",
        "source": "jra_page_viewed_by_operator",
    }


class OperatorFactorIntakeTests(unittest.TestCase):
    def test_observation_not_assessment_or_publication(self):
        out = validate_operator_factor_note(note(), NOW)
        self.assertEqual(out["version"], "operator-factor-intake-1")
        self.assertEqual(out["grade"], "未評価")
        self.assertEqual(out["gradedFactorCount"], 0)
        self.assertTrue(out["submittedByOperator"])
        self.assertFalse(out["saved"])
        self.assertFalse(out["sourceAuthenticated"])
        self.assertFalse(out["verifiedBeforePostTime"])
        self.assertFalse(out["jraOfficialFinalVerification"])
        self.assertFalse(out["predictionReady"])
        self.assertFalse(out["bettingReady"])
        self.assertNotIn("horseNumber", out)

    def test_unknown_requires_no_claimed_source(self):
        data = note()
        data.update(state="unknown", source="none")
        out = validate_operator_factor_note(data, NOW)
        self.assertEqual(out["state"], "unknown")
        for invalid in (
            dict(state="unknown", source="operator_observation"),
            dict(state="noted", source="none"),
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_operator_factor_note({**data, **invalid}, NOW)

    def test_all_ten_factors_accepted_only_as_labels(self):
        from evaluation_policy import FACTORS
        for factor in FACTORS:
            report = validate_operator_factor_note({**note(), "factor": factor}, NOW)
            self.assertEqual(report["factor"], factor)
            self.assertEqual(report["grade"], "未評価")

    def test_bad_fields_rejected(self):
        invalid = [
            {"recordType": "live"},
            {"recordType": "test"},
            {"date": "20260230"},
            {"date": "2026-11-07"},
            {"track": "架空場"},
            {"race": 0}, {"race": True}, {"race": "1"},
            {"horseNumber": "00"}, {"horseNumber": "1"},
            {"horseNumber": "19"}, {"horseNumber": 1},
            {"factor": "odds"}, {"factor": "result"},
            {"state": "S"}, {"source": "paid_jrdb_api"},
            {"source": "none"}, {"extra": "horse_name"},
            {"assessment": {"grade": "S"}},
            {"horseNumber": "01\n"},
        ]
        for alteration in invalid:
            with self.subTest(alteration=alteration), self.assertRaises(ValueError):
                validate_operator_factor_note({**note(), **alteration}, NOW)
        with self.assertRaises(ValueError):
            validate_operator_factor_note(None, NOW)
        with self.assertRaises(ValueError):
            validate_operator_factor_note({k: v for k, v in note().items() if k != "state"}, NOW)

    def test_forged_future_receipt_rejected(self):
        with self.assertRaises(ValueError):
            validate_operator_factor_note(note(), "2099-01-01T12:00:00+09:00")

    def test_no_input_mutation(self):
        data = note()
        before = dict(data)
        validate_operator_factor_note(data, NOW)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
