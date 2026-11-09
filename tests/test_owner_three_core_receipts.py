"""Uncalibrated 70-point study receipts: pre-off and tamper-evident only."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_three_core_receipts import (
    issue_three_core_receipts, verify_three_core_receipts, CoreReceiptError
)
from test_owner_rebound_receipts import sample as rebound_sample
from test_private_service import SETTINGS, call
from private_service import create_app

DAY = "20990412"
SECRET = "synthetic-extra-long-private-owner-secret-v1"
WEIGHTS = {"training": 30, "course_distance": 20, "pace": 20}


def horse(number, bands=None):
    bands = bands or {"training": "S", "course_distance": "A", "pace": "B"}
    weights = {"S": 3, "A": 2, "B": 1, "C": 0}
    raw = (None if "未評価" in bands.values() else
           sum(weights[v] * WEIGHTS[k] for k, v in bands.items()))
    return {
        "number": number, "bands": bands,
        "observedCoreCount": sum(v != "未評価" for v in bands.values()),
        "missing": [k for k, v in bands.items() if v == "未評価"],
        "rawThirdPoints": raw,
        "evidenceScore70": None if raw is None else round(raw / 3, 2),
        "scoreIsCalibrated": False,
        "formalScore100": None, "formalGrade": "未評価",
        "formalRank": None, "bettingReady": False,
    }


def source():
    history, programme, now = rebound_sample()
    races = [
        {"track": "東京", "race": 1, "runnerCount": 3,
         "formalGradeReady": False, "trifectaReady": False,
         "horses": [
             horse(1), horse(2, {"training": "C", "course_distance": "S", "pace": "S"}),
             horse(3, {"training": "未評価", "course_distance": "S", "pace": "S"}),
         ]},
        {"track": "京都", "race": 2, "runnerCount": 2,
         "formalGradeReady": False, "trifectaReady": False,
         "horses": [horse(4), horse(7)]},
    ]
    history["threeCoreResearch"] = {
        "version": "owner-three-core-research-1",
        "coreWeightTotal": 70, "coreFactorWeights": WEIGHTS,
        "factorGradesVerified": 0,
        "formalScoreReady": False, "overallPredictionReady": False,
        "officialJraVerified": False,
        "historicalBandsNotCalibrated": True,
        "bettingReady": False, "autoPurchase": False,
        "changesExistingTickets": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "raceCount": 2, "races": races,
    }
    return history, programme, now


class ThreeCoreReceiptTests(unittest.TestCase):
    def test_prestart_lock_only_complete_horses_from_same_programme(self):
        history, programme, now = source()
        before = copy.deepcopy((history, programme))
        out = issue_three_core_receipts(history, programme, SECRET, DAY, now)
        self.assertEqual(out["receiptCount"], 2)
        self.assertEqual(out["postOffOrMissingTimeRaces"], 0)
        self.assertFalse(out["officialResultsVerified"])
        self.assertFalse(out["calibrationReady"])
        self.assertFalse(out["bettingReady"])
        self.assertFalse(out["actualPurchase"])
        snaps = verify_three_core_receipts(out["receipts"], SECRET, DAY)
        self.assertEqual([r["track"] for r in snaps], ["東京", "京都"])
        self.assertEqual(snaps[0]["raceRunnerCount"], 3)
        self.assertEqual(snaps[0]["observedRunnerCount"], 2)
        self.assertEqual([h["number"] for h in snaps[0]["horses"]], [1, 2])
        self.assertEqual(snaps[0]["horses"][0]["rawThirdPoints"], 170)
        self.assertEqual(snaps[0]["horses"][1]["rawThirdPoints"], 120)
        self.assertEqual(before, (history, programme))
        for term in ("racekey", "horse_id", "sireRecorded",
                     "paid_index", "trifectaTickets", "result", "winner",
                     "PRIVATE_HORSE"):
            self.assertNotIn(term, repr(out))

    def test_no_after_start_or_ambiguous_or_missing_provisional_post(self):
        history, programme, _ = source()
        at_kyoto_off = datetime(2099, 4, 12, 1, 0, tzinfo=timezone.utc)
        out = issue_three_core_receipts(
            history, programme, SECRET, DAY, at_kyoto_off)
        self.assertEqual(out["receiptCount"], 1)
        self.assertEqual(out["postOffOrMissingTimeRaces"], 1)
        self.assertEqual(out["receipts"][0]["snapshot"]["track"], "東京")
        after = datetime(2099, 4, 12, 2, 1, tzinfo=timezone.utc)
        none = issue_three_core_receipts(history, programme, SECRET, DAY, after)
        self.assertEqual(none["receiptCount"], 0)
        self.assertEqual(none["postOffOrMissingTimeRaces"], 2)
        programme[0]["post_time"] = None
        one = issue_three_core_receipts(history, programme, SECRET, DAY, source()[2])
        self.assertEqual(one["receiptCount"], 1)
        programme.append(copy.deepcopy(programme[0]))
        with self.assertRaises(CoreReceiptError):
            issue_three_core_receipts(history, programme, SECRET, DAY, source()[2])

    def test_any_tamper_blocks_signature_and_source_promotion(self):
        history, programme, now = source()
        signed = issue_three_core_receipts(
            history, programme, SECRET, DAY, now)["receipts"]
        originals = copy.deepcopy(signed)
        changes = (
            lambda x: x[0]["snapshot"]["horses"][0].update(rawThirdPoints=210),
            lambda x: x[0]["snapshot"]["horses"][0]["bands"].update(training="C"),
            lambda x: x[0]["snapshot"].update(capturedAt="2099-04-12T02:00:00+00:00"),
            lambda x: x[0]["snapshot"].update(officialJraVerified=True),
            lambda x: x[0]["snapshot"].update(predictionReady=True),
            lambda x: x[0]["snapshot"].update(actualPurchase=True),
            lambda x: x[0]["snapshot"].update(sourceKind="official-result"),
            lambda x: x[0].update(signature="f"*64),
        )
        for mutate in changes:
            value = copy.deepcopy(signed)
            mutate(value)
            with self.subTest(mutate=repr(mutate)), self.assertRaises(CoreReceiptError):
                verify_three_core_receipts(value, SECRET, DAY)
        with self.assertRaises(CoreReceiptError):
            verify_three_core_receipts(originals, "different-long-secret-value-12345", DAY)
        with self.assertRaises(CoreReceiptError):
            verify_three_core_receipts(originals + originals[:1], SECRET, DAY)
        with self.assertRaises(CoreReceiptError):
            verify_three_core_receipts(originals, SECRET, "20990413")
        history["threeCoreResearch"]["bettingReady"] = True
        with self.assertRaises(CoreReceiptError):
            issue_three_core_receipts(history, programme, SECRET, DAY, now)

    def test_private_verification_does_not_fetch_paid_data_or_results(self):
        history, programme, now = source()
        signed = issue_three_core_receipts(
            history, programme, SETTINGS["KEIBA_OWNER_PASSWORD"], DAY, now)
        cfg = {**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
               "KEIBA_RENDER_PREVIEW_ONLY": "0"}
        app = create_app(cfg)
        with (patch("private_service.fetch_finished_race_results") as results,
              patch("private_service.fetch_race_program") as program):
            r = call(app, "/api/owner-three-core-verify", method="POST",
                     data={"date": DAY, "receipts": signed["receipts"]})
            results.assert_not_called()
            program.assert_not_called()
        self.assertEqual(r["status"], "200 OK")
        body = json.loads(r["body"])
        self.assertEqual(body["recordCount"], 2)
        for flag in ("officialJraVerified", "calibrationReady",
                     "resultComparisonReady", "bettingReady", "autoPurchase",
                     "actualPurchase"):
            self.assertFalse(body[flag])
        self.assertTrue(body["serverSigned"])
        self.assertNotIn("horses", body)
        self.assertEqual(call(app, "/api/owner-three-core-verify",
                              method="POST", auth="",
                              data={"date": DAY, "receipts": signed["receipts"]})["status"],
                         "401 Unauthorized")
        self.assertEqual(call(app, "/api/owner-three-core-verify",
                              method="POST",
                              data={"date": DAY, "receipts": signed["receipts"],
                                    "results": [{"winner": 4}]})["status"],
                         "400 Bad Request")
        bad = copy.deepcopy(signed["receipts"])
        bad[0]["snapshot"]["horses"][0]["rawThirdPoints"] = 210
        self.assertEqual(call(app, "/api/owner-three-core-verify",
                              method="POST",
                              data={"date": DAY, "receipts": bad})["status"],
                         "400 Bad Request")
        public = create_app(SETTINGS)
        self.assertEqual(call(public, "/api/owner-three-core-verify",
                              method="POST", data={"date": DAY, "receipts": []})["status"],
                         "404 Not Found")

    def test_opt_in_history_attests_three_core_without_replacing_watch(self):
        history, programme, _ = source()
        cfg = {**SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
               "KEIBA_RENDER_PREVIEW_ONLY": "0",
               "JRDB_PRIVATE_ENABLED": "1", "KEIBA_HISTORY_ENABLED": "1",
               "JRDB_API_KEY": "synthetic-private-key",
               "JRDB_AUTH_KEY": "synthetic-auth-key"}
        app = create_app(cfg)
        with (patch("private_service.fetch_race_program", return_value=[]),
              patch("private_service.normalize_program_rows", return_value=programme),
              patch("private_service.fetch_horse_entries", return_value=[]),
              patch("private_service.fetch_recent_runs", return_value=[]),
              patch("private_service.fetch_training_analysis", return_value=[]),
              patch("private_service.fetch_venue_conditions", return_value=[]),
              patch("private_service.run_bounded_history_audit", return_value=history),
              patch("private_service._now_in_jst",
                    return_value="2099-04-12T09:30:00+09:00")):
            response = call(app, "/api/jrdb/history", method="POST",
                            data={"date": DAY, "limit": 8})
        self.assertEqual(response["status"], "200 OK")
        body = json.loads(response["body"])
        self.assertEqual(body["coreCapture"]["receiptCount"], 2)
        self.assertEqual(body["watchCapture"]["receiptCount"], 2)
        self.assertFalse(body["coreCapture"]["calibrationReady"])
        self.assertEqual(verify_three_core_receipts(
            body["coreCapture"]["receipts"],
            SETTINGS["KEIBA_OWNER_PASSWORD"], DAY),
            [x["snapshot"] for x in body["coreCapture"]["receipts"]])


if __name__ == "__main__":
    unittest.main()
