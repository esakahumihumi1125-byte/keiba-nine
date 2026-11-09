"""Synthetic body-condition 1-point source-gate tests, no genuine paid rows."""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from jrdb_prestart_body import audit_prestart_body
from owner_body_one_evidence_preflight import body_one_evidence_preflight
from test_jrdb_prestart_body import fixture
from test_private_single_readiness_endpoint import source
from test_private_service import SETTINGS, call
from private_service import create_app


def snapshot():
    p, e, tpd = fixture()
    return audit_prestart_body(p, e, tpd, "20261101")


class BodyOneResearchTests(unittest.TestCase):
    def test_valid_prestart_pairs_never_become_fitness_points(self):
        start = snapshot()
        original = copy.deepcopy(start)
        report = body_one_evidence_preflight(start)
        self.assertEqual(start, original)
        self.assertEqual(report["factor"], "body_condition")
        self.assertEqual(report["weight"], 1)
        self.assertEqual(report["raceCount"], 2)
        self.assertEqual(report["verifiedGradeCount"], 0)
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["conditionEffectValidated"])
        self.assertFalse(report["outOfTimeValidated"])
        self.assertFalse(report["overallPredictionReady"])
        self.assertFalse(report["bettingReady"])
        tokyo = next(r for r in report["races"] if r["track"] == "東京")
        kyoto = next(r for r in report["races"] if r["track"] == "京都")
        self.assertEqual(tokyo["completeMeasuredPairs"], 1)
        self.assertEqual(tokyo["missingMeasuredPairs"], 1)
        self.assertEqual(kyoto["completeMeasuredPairs"], 0)
        self.assertEqual(kyoto["missingMeasuredPairs"], 1)
        self.assertTrue(tokyo["horses"][0]["sourcePairPresent"])
        self.assertFalse(tokyo["horses"][1]["sourcePairPresent"])
        self.assertIn("body_weight_measurement_missing",
                      tokyo["horses"][1]["missingEvidence"])
        self.assertIn("prestart_runner_row_unavailable",
                      kyoto["horses"][0]["missingEvidence"])
        for race in report["races"]:
            self.assertEqual(len(race["horses"]), race["runnerCount"])
            self.assertEqual(sum(x["sourcePairPresent"] for x in race["horses"]),
                             race["completeMeasuredPairs"])
            for horse in race["horses"]:
                self.assertEqual(horse["grade"], "未評価")
                self.assertIsNone(horse["score1"])
                self.assertFalse(horse["officialVerified"])
                self.assertFalse(horse["effectValidated"])
                self.assertFalse(horse["temporalValidationComplete"])
                self.assertIn("independent_jra_weight_not_verified",
                              horse["missingEvidence"])
        redacted = repr(report)
        for private in ("2328aaa95a05", "horse_id", "horse_weight",
                        "weight_cycling", "win_odds", "SECRET_ODDS", "9999",
                        "480", "'paddock_index'"):
            self.assertNotIn(private, redacted)

    def test_count_conflicts_and_fake_official_grade_fail_closed(self):
        base = snapshot()
        cases = (
            lambda x: x.update(officialBodyWeightVerified=True),
            lambda x: x["races"][0]["runners"][0].update(bodyConditionScore1=1),
            lambda x: x["races"][0]["runners"][0].update(bodyConditionGrade="S"),
            lambda x: x["races"][0]["runners"][0].update(
                weightChangeRecorded=False),
            lambda x: x["races"][0]["runners"][1].update(
                bodyWeightRecorded=True),
            lambda x: x["races"][0].update(weightChangeRecords=2),
            lambda x: x["races"][0].update(prestartRowsMatched=1),
            lambda x: x["races"][1].update(track="東京", race=1),
            lambda x: x["summary"].update(missingRows=9),
        )
        for edit in cases:
            with self.subTest(edit=str(edit)):
                forged = copy.deepcopy(base)
                edit(forged)
                with self.assertRaises(CoverageError):
                    body_one_evidence_preflight(forged)

    def test_private_prestart_adds_only_same_request_redacted_readiness(self):
        raw, entries, _, _, _ = source()
        _, _, prestart = fixture()
        app = create_app({**SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
                          "KEIBA_PRESTART_BODY_ENABLED": "1",
                          "JRDB_API_KEY": "test-nonsecret",
                          "JRDB_AUTH_KEY": "test-nonsecret"})
        with (patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:40:00+09:00"),
              patch("private_service.fetch_race_program",
                    return_value=raw) as programme,
              patch("private_service.fetch_horse_entries",
                    return_value=entries) as horses,
              patch("private_service.fetch_prestart_body",
                    return_value=prestart) as body):
            res = call(app, "/api/jrdb/prestart-body",
                       QUERY_STRING="date=20261101")
        self.assertEqual(res["status"], "200 OK")
        payload = json.loads(res["body"])
        self.assertEqual(payload["bodyOneEvidencePreflight"]["raceCount"], 2)
        self.assertEqual(payload["bodyOneEvidencePreflight"]["weight"], 1)
        for fetch in (programme, horses, body):
            fetch.assert_called_once_with("20261101")
        self.assertNotIn("2328aaa95a05", res["body"].decode())
        self.assertNotIn("SECRET_ODDS", res["body"].decode())


if __name__ == "__main__":
    unittest.main()
