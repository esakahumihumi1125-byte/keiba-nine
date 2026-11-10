"""Offline 36R Saturday acceptance smoke: no network, credentials or paid reads.

Covers all 3x12 race slots, per-race safe holds, capped formations,
server-signed first prestart snapshots and after-off refusal. Synthetic only.
"""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_owner_auto_draft import build_owner_auto_drafts, JST
from owner_auto_draft_receipts import seal_auto_research_drafts
from owner_prestart_receipt import verify_preview_receipts
from test_jrdb_owner_auto_draft import programme, research
from test_private_service import SETTINGS
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
        self.assertIn("12種類の記録をバックアップ", AUTO_HTML)
        self.assertNotIn("10種類の記録をバックアップ", AUTO_HTML)
        self.assertNotIn("11種類の端末記録", AUTO_HTML)
        self.assertIn("新配点79点", AUTO_HTML)
        self.assertIn("旧85点", AUTO_HTML)
        self.assertIn("12種類の記録を1つのJSON", BACKUP_HTML)

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

    def test_after_off_never_reconstructs_historical_tickets(self):
        p, study = synthetic_day()
        report = build_owner_auto_drafts(p, study, DAY, now=AFTER)
        self.assertEqual((report["draftCount"], report["holdCount"]), (0, 36))
        self.assertEqual(report["holdReasons"], {"after_provisional_off": 36})
        self.assertTrue(all(not r["runners"] and not r["tickets"] for r in report["races"]))
        self.assertEqual(seal_auto_research_drafts(report, SECRET, now=AFTER), [])


if __name__ == "__main__":
    unittest.main()
