"""Offline 36R Saturday acceptance smoke: no network, credentials or paid reads.

Covers all 3x12 race slots, per-race safe holds, capped formations,
server-signed first prestart snapshots and after-off refusal. Synthetic only.
"""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_owner_auto_draft import build_owner_auto_drafts, JST
from owner_auto_draft_receipts import seal_auto_research_drafts
from owner_prestart_receipt import verify_preview_receipts
from test_jrdb_owner_auto_draft import programme, research
from test_private_service import SETTINGS, call
from private_service import create_app
from owner_auto_forecast_ui import HTML as AUTO_HTML
from owner_backup import HTML as BACKUP_HTML

DAY = "20990101"
SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]
VENUES = (("東京", "05"), ("京都", "08"), ("福島", "03"))
BEFORE = datetime(2099, 1, 1, 9, 0, tzinfo=JST)
AFTER = datetime(2099, 1, 1, 18, 0, tzinfo=JST)


def synthetic_day(*, mixed=False):
    p, rows = [], []
    for venue, code in VENUES:
        for number in range(1, 13):
            record = copy.deepcopy(programme()[0])
            record.update(
                track=venue, race=number,
                racekey=code + "99aa" + f"{number:02d}",
                post_time="15:00",
            )
            study = copy.deepcopy(research()["races"][0])
            study.update(track=venue, race=number)
            study["research"].update(track=venue, race=number)
            p.append(record)
            rows.append(study)
    if mixed:
        # After provisional off: no fresh order, ticket or signed receipt.
        p[0]["post_time"] = "08:59"
        # A single malformed race must hold while other 34 keep working.
        rows[1]["research"]["runners"][0]["completeFactors"] = 0
    source = research()
    source["raceCount"] = 36
    source["races"] = rows
    return p, source


class Saturday36RSmokeTests(unittest.TestCase):
    def test_saturday_iphone_copy_refers_to_current_backup_and_scores(self):
        self.assertIn("13種類の記録をバックアップ", AUTO_HTML)
        self.assertNotIn("10種類の記録をバックアップ", AUTO_HTML)
        self.assertNotIn("11種類の端末記録", AUTO_HTML)
        self.assertIn("新配点79点", AUTO_HTML)
        self.assertIn("旧85点", AUTO_HTML)
        self.assertIn("13種類の記録を1つのJSON", BACKUP_HTML)

    def test_full_day_generates_36_valid_bounded_receipts_before_off(self):
        p, study = synthetic_day()
        before = copy.deepcopy((p, study))
        result = build_owner_auto_drafts(p, study, DAY, now=BEFORE)
        self.assertEqual((p, study), before)
        self.assertEqual(result["raceCount"], 36)
        self.assertEqual((result["draftCount"], result["holdCount"]), (36, 0))
        self.assertEqual(len(result["races"]), 36)
        self.assertEqual(
            {(r["track"], r["race"]) for r in result["races"]},
            {(venue, i) for venue, _ in VENUES for i in range(1, 13)},
        )
        self.assertTrue(all(r["points"] == 40 for r in result["races"]))
        self.assertTrue(all(
            r["amountYen"] == r["points"] * 100
            and len({tuple(ticket) for ticket in r["tickets"]}) == r["points"]
            and r["researchOnly"] is True
            and r["bettingReady"] is False
            for r in result["races"]
        ))
        sealed = seal_auto_research_drafts(result, SECRET, now=BEFORE)
        self.assertEqual(len(sealed), 36)
        restored = verify_preview_receipts(sealed, SECRET, "2099-01-01")
        self.assertEqual(len(restored), 36)
        self.assertTrue(all(
            r["sourceKind"] == "prestart-locked"
            and r["actualPurchase"] is False
            and len(r["trifectaTickets"]) == 40
            for r in restored
        ))
        for forbidden in ("horse_id", "horse_name", "api_key", "racekey"):
            self.assertNotIn(forbidden, repr(sealed))

    def test_one_past_and_one_invalid_only_hold_their_own_race(self):
        p, study = synthetic_day(mixed=True)
        result = build_owner_auto_drafts(p, study, DAY, now=BEFORE)
        self.assertEqual((result["draftCount"], result["holdCount"]), (34, 2))
        self.assertEqual(
            result["holdReasons"],
            {"after_provisional_off": 1, "invalid_two_factor": 1},
        )
        first, second = result["races"][:2]
        self.assertEqual(first["reason"], "after_provisional_off")
        self.assertEqual(second["reason"], "invalid_two_factor")
        for r in (first, second):
            self.assertEqual(r["runners"], [])
            self.assertEqual(r["tickets"], [])
            self.assertEqual(r["points"], 0)
        sealed = seal_auto_research_drafts(result, SECRET, now=BEFORE)
        self.assertEqual(len(sealed), 34)
        self.assertNotIn(
            ("東京", 1),
            {(x["snapshot"]["track"], x["snapshot"]["race"]) for x in sealed},
        )
        self.assertNotIn(
            ("東京", 2),
            {(x["snapshot"]["track"], x["snapshot"]["race"]) for x in sealed},
        )

    def test_authenticated_http_end_to_end_36r_five_provider_reads(self):
        # Full private request pipeline, including signed receipts, the
        # ten-factor ungraded contract, and race/source count consistency.
        # All five external adapters are mocked; this never spends JRDB calls.
        p, source = synthetic_day()
        config = {
            **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
            "KEIBA_RENDER_PREVIEW_ONLY": "0", "JRDB_PRIVATE_ENABLED": "1",
            "JRDB_API_KEY": "synthetic-api", "JRDB_AUTH_KEY": "synthetic-auth",
        }
        with (patch("private_service.fetch_race_program", return_value=[]) as tra,
              patch("private_service.normalize_program_rows", return_value=p),
              patch("private_service.fetch_horse_entries", return_value=[]) as tky,
              patch("private_service.fetch_training_analysis", return_value=[]) as cyb,
              patch("private_service.fetch_recent_runs", return_value=[]) as tze,
              patch("private_service.owner_day_research", return_value=source),
              patch("private_service.fetch_venue_conditions", return_value=[]) as tka,
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00+09:00")):
            resp = call(create_app(config), "/api/jrdb/owner-auto-draft",
                        QUERY_STRING="date=" + DAY)
        self.assertEqual(resp["status"], "200 OK")
        body = json.loads(resp["body"])
        self.assertEqual((body["raceCount"], body["draftCount"], body["holdCount"]),
                         (36, 36, 0))
        self.assertEqual(body["researchReceiptCount"], 36)
        self.assertEqual(body["sourceReadCount"], 4)
        self.assertEqual(body["tenFactorPreview"]["raceCount"], 36)
        self.assertEqual(body["sourcePassport"]["raceCount"], 36)
        self.assertFalse(body["overallPredictionReady"])
        self.assertFalse(body["officialJraVerified"])
        self.assertFalse(body["bettingReady"])
        self.assertFalse(body["captureAuditVerified"])
        self.assertTrue(body["serverStamped"])
        self.assertEqual(
            len(verify_preview_receipts(body["researchReceipts"], SECRET,
                                        "2099-01-01")), 36)
        self.assertTrue(all(
            race["fullTenFactorCount"] == 0
            for race in body["tenFactorPreview"]["races"]))
        for api in (tra, tky, cyb, tze, tka):
            api.assert_called_once()
        self.assertNotIn("synthetic-api", resp["body"].decode())
        self.assertNotIn("synthetic-auth", resp["body"].decode())

    def test_http_mixed_36r_keeps_34_safe_drafts(self):
        p, source = synthetic_day(mixed=True)
        config = {
            **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
            "KEIBA_RENDER_PREVIEW_ONLY": "0", "JRDB_PRIVATE_ENABLED": "1",
            "JRDB_API_KEY": "synthetic-api", "JRDB_AUTH_KEY": "synthetic-auth",
        }
        with (patch("private_service.fetch_race_program", return_value=[]),
              patch("private_service.normalize_program_rows", return_value=p),
              patch("private_service.fetch_horse_entries", return_value=[]),
              patch("private_service.fetch_training_analysis", return_value=[]),
              patch("private_service.fetch_recent_runs", return_value=[]),
              patch("private_service.owner_day_research", return_value=source),
              patch("private_service.fetch_venue_conditions", return_value=[]),
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00+09:00")):
            resp = call(create_app(config), "/api/jrdb/owner-auto-draft",
                        QUERY_STRING="date=" + DAY)
        self.assertEqual(resp["status"], "200 OK")
        body = json.loads(resp["body"])
        self.assertEqual((body["raceCount"], body["draftCount"], body["holdCount"]),
                         (36, 34, 2))
        self.assertEqual(body["researchReceiptCount"], 34)
        self.assertEqual(body["holdReasons"],
                         {"after_provisional_off": 1, "invalid_two_factor": 1})
        self.assertTrue(all(
            not row["tickets"] and row["points"] == 0
            for row in body["races"] if row["status"] == "hold"))
        self.assertFalse(body["officialJraVerified"])
        self.assertFalse(body["bettingReady"])
        self.assertFalse(body["tenFactorPreview"]["overallPredictionReady"])

    def test_after_off_never_reconstructs_historical_tickets(self):
        p, study = synthetic_day()
        report = build_owner_auto_drafts(p, study, DAY, now=AFTER)
        self.assertEqual((report["draftCount"], report["holdCount"]), (0, 36))
        self.assertEqual(report["holdReasons"], {"after_provisional_off": 36})
        self.assertTrue(all(not r["runners"] and not r["tickets"] for r in report["races"]))
        self.assertEqual(seal_auto_research_drafts(report, SECRET, now=AFTER), [])


if __name__ == "__main__":
    unittest.main()
