"""Saturday owner HTTP acceptance from synthetic raw /tra/tky/tcy/tze rows.

Unlike a mocked research report, this verifies real in-repo normalization,
horse identity joins, two-factor analysis, signed drafts and source passports
for a complete 3-venue day. No JRDB network or billable source is contacted.
"""
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import SETTINGS, call
from owner_prestart_receipt import verify_preview_receipts

DAY = "20990101"
SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]
VENUES = ("05", "08", "03")
TRAINING = (82, 78, 68, 63, 52, 48, 30)
RECENT = (85, 62, 60, 45, 42, 25, 20)


def raw_day(*, mixed=False):
    programmes, entries, training, previous = [], [], [], []
    for venue in VENUES:
        for race in range(1, 13):
            key = venue + "99aa" + f"{race:02d}"
            programmes.append({
                "racekey": key, "racedate": DAY,
                "post_time": "0859" if mixed and venue == "05" and race == 1
                             else "1500",
                "track_type": "1", "distance": "2000",
                "turn_cd": "2", "headcount": 7,
            })
            for i, (workout, recent) in enumerate(zip(TRAINING, RECENT), 1):
                hid = f"{int(venue)*1000 + race*20 + i:012x}"
                n = f"{i:02d}"
                entries.append({
                    "racekey": key, "racedate": DAY,
                    "horse_number": n, "horse_id": hid,
                    "horse_name": "PRIVATE-TEST-HORSE-" + hid,
                })
                training.append({
                    "racekey": key, "racedate": DAY,
                    "horse_number": n, "horse_id": hid,
                    "oikirisisu": workout, "siagarisisu": workout,
                    "oikirisisu_lastweek": workout,
                    "private_metric": "PRIVATE-WORKOUT-" + hid,
                })
                previous.append({
                    "racekey": key, "racedate": DAY,
                    "horse_number": n, "horse_id": hid,
                    "race_back_1_racedate": "20981215",
                    "race_back_1_order_of_finish": 1,
                    "race_back_1_idm": recent,
                    "race_back_1_corner4_order": 2,
                    "race_back_2_racedate": "20981115",
                    "race_back_2_order_of_finish": 2,
                    "race_back_2_idm": recent,
                    "race_back_2_corner4_order": 3,
                    "horse_name": "PRIVATE-PAST-" + hid,
                })
    if mixed:
        # One corrupted /tcy source row impacts only its own race. The
        # source-wide optional material count is allowed to be unavailable.
        bad = next(t for t in training if t["racekey"] == "0599aa02")
        training.append(copy.deepcopy(bad))
    return programmes, entries, training, previous


def owner_app():
    return create_app({
        **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
        "KEIBA_RENDER_PREVIEW_ONLY": "0",
        "JRDB_PRIVATE_ENABLED": "1",
        "JRDB_API_KEY": "raw-synthetic-key",
        "JRDB_AUTH_KEY": "raw-synthetic-auth",
    })


def run_request(data):
    programme, entries, training, previous = data
    with (
        patch("private_service.fetch_race_program", return_value=programme) as tra,
        patch("private_service.fetch_horse_entries", return_value=entries) as tky,
        patch("private_service.fetch_training_analysis", return_value=training) as tcy,
        patch("private_service.fetch_recent_runs", return_value=previous) as tze,
        patch("private_service.fetch_venue_conditions", return_value=[]) as tka,
        patch("private_service._now_in_jst",
              return_value="2099-01-01T09:00:00+09:00"),
    ):
        reply = call(owner_app(), "/api/jrdb/owner-auto-draft",
                     QUERY_STRING="date=" + DAY)
    for adapter in (tra, tky, tcy, tze, tka):
        adapter.assert_called_once_with(DAY)
    return reply


class SaturdayRawDayTests(unittest.TestCase):
    def test_raw_36r_really_parses_analyzes_signs_and_redacts(self):
        raw = raw_day()
        frozen = copy.deepcopy(raw)
        reply = run_request(raw)
        self.assertEqual(reply["status"], "200 OK", reply["body"][:300])
        self.assertEqual(raw, frozen)
        result = json.loads(reply["body"])
        self.assertEqual((result["raceCount"], result["draftCount"],
                          result["holdCount"]), (36, 36, 0))
        self.assertEqual(result["researchReceiptCount"], 36)
        self.assertEqual(result["sourceReadCount"], 4)
        self.assertEqual(result["sourcePassport"]["raceCount"], 36)
        self.assertEqual(result["sourcePassport"]["observedMaterialRaces"], 36)
        self.assertEqual(result["tenFactorPreview"]["raceCount"], 36)
        self.assertFalse(result["overallPredictionReady"])
        self.assertFalse(result["officialJraVerified"])
        self.assertFalse(result["bettingReady"])
        self.assertTrue(all(
            item["points"] == 40
            and item["first"] == [1, 2]
            and item["second"] == [1, 2, 3, 4, 5]
            and item["third"] == [1, 2, 3, 4, 5, 6, 7]
            and len(set(map(tuple, item["tickets"]))) == 40
            for item in result["races"]))
        restored = verify_preview_receipts(
            result["researchReceipts"], SECRET, "2099-01-01")
        self.assertEqual(len(restored), 36)
        self.assertTrue(all(len(r["trifectaTickets"]) == 40 for r in restored))
        self.assertTrue(all(
            r["verifiedFactorCount"] == 0 and not r["completeTenFactorReady"]
            for r in result["sourcePassport"]["races"]))
        self.assertTrue(all(
            r["fullTenFactorCount"] == 0
            for r in result["tenFactorPreview"]["races"]))
        text = reply["body"].decode()
        for secret in ("raw-synthetic-key", "raw-synthetic-auth",
                       "PRIVATE-TEST-HORSE", "PRIVATE-WORKOUT", "PRIVATE-PAST",
                       "horse_id", "racekey", "oikirisisu",
                       "race_back_1_idm"):
            self.assertNotIn(secret, text)

    def test_completed_real_pipeline_writes_only_redacted_operator_status(self):
        # The old /tra connection probe is not proof of prestart HMAC sealing.
        # One new log line proves this complete authenticated HTTP path ran,
        # while disclosing no requested date, horse identity, source fields,
        # endpoints, API keys or generated ticket combinations.
        with self.assertLogs(level="WARNING") as captured:
            reply = run_request(raw_day())
        self.assertEqual(reply["status"], "200 OK")
        events = [line for line in captured.output
                  if "KEIBA_AUTO_DRAFT_PIPELINE" in line]
        self.assertEqual(len(events), 1)
        self.assertIn("status=complete", events[0])
        for field in ("programme=present", "drafts=36", "holds=0",
                      "receipts=36", "hold_causes=none",
                      "jra=unverified", "formal=ungraded"):
            self.assertIn(field, events[0])
        for forbidden in (
                DAY, "PRIVATE-", "racekey", "horse_id", "horse_name",
                "2099-01-01", "raw-synthetic", "api_key", "x-user-key",
                "tickets", "trifecta", "0526", "TRAINING", "JRDB_API"):
            self.assertNotIn(forbidden, events[0])
        self.assertNotIn("KEIBA_AUTO_DRAFT_FAILURE", " ".join(captured.output))

    def test_one_source_withdrawal_logs_fixed_hold_cause_no_horse_data(self):
        programme, entries, training, previous = raw_day()
        for row in entries:
            row["withdrawn_flag"] = "0"
        entries[0]["withdrawn_flag"] = "1"
        with self.assertLogs(level="WARNING") as captured:
            response=run_request((programme,entries,training,previous))
        self.assertEqual(response["status"],"200 OK",response["body"][:250])
        logs=[line for line in captured.output
              if "KEIBA_AUTO_DRAFT_PIPELINE" in line]
        self.assertEqual(len(logs),1)
        self.assertIn("drafts=35 holds=1 receipts=35",logs[0])
        self.assertIn("hold_causes=provider_withdrawal:1",logs[0])
        for secret in ("horse_id","horse_name","racekey","PRIVATE",
                       "raw-synthetic","x-user-key",DAY,
                       "2099-01-01","withdrawn_flag","01","02"):
            # Only check source-bearing strings, not ordinary digits
            # already present in aggregate counts.
            if secret in ("01","02"):
                continue
            self.assertNotIn(secret,logs[0])

    def test_provider_withdrawal_only_holds_one_of_thirty_six(self):
        programme, entries, training, previous = raw_day()
        for row in entries:
            # Explicitly clear all provider flags for this synthetic case.
            row["withdrawn_flag"] = "0"
        scratch = next(row for row in entries
                       if row["racekey"]=="0599aa02"
                       and row["horse_number"]=="03")
        scratch["withdrawn_flag"] = "1"
        response = run_request((programme,entries,training,previous))
        self.assertEqual(response["status"],"200 OK",response["body"][:350])
        report=json.loads(response["body"])
        self.assertEqual((report["raceCount"],report["draftCount"],
                          report["holdCount"]),(36,35,1))
        self.assertEqual(report["holdReasons"],{"provider_withdrawal":1})
        held=[x for x in report["races"] if x["status"]=="hold"]
        self.assertEqual([(x["track"],x["race"]) for x in held],[("東京",2)])
        self.assertEqual(held[0]["reason"],"provider_withdrawal")
        self.assertFalse(held[0]["tickets"])
        self.assertFalse(held[0]["runners"])
        self.assertEqual(report["researchReceiptCount"],35)
        self.assertEqual(len(verify_preview_receipts(
            report["researchReceipts"],SECRET,"2099-01-01")),35)
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["bettingReady"])
        # No horse identity or JRDB raw flag is disclosed.
        redacted=response["body"].decode()
        for private in ("withdrawn_flag","horse_name","horse_id",
                        "PRIVATE-TEST-HORSE","racekey"):
            self.assertNotIn(private,redacted)

    def test_single_missing_workout_holds_only_one_race(self):
        programme, entries, training, previous = raw_day()
        # A missing /tcy row is NOT a C grade or zero ability. The other
        # 35 original races must still be converted and sealed.
        training = [t for t in training
                    if not (t["racekey"] == "0599aa02"
                            and t["horse_number"] == "07")]
        reply = run_request((programme, entries, training, previous))
        self.assertEqual(reply["status"], "200 OK", reply["body"][:300])
        report = json.loads(reply["body"])
        self.assertEqual((report["raceCount"], report["draftCount"],
                          report["holdCount"]), (36, 35, 1))
        self.assertEqual(report["holdReasons"], {"missing_factors": 1})
        self.assertEqual(report["researchReceiptCount"], 35)
        held = [x for x in report["races"] if x["status"] == "hold"]
        self.assertEqual([(x["track"], x["race"]) for x in held],
                         [("東京", 2)])
        self.assertEqual(held[0]["points"], 0)
        self.assertTrue(all(len(x["tickets"]) == 40
                            for x in report["races"] if x["status"] == "provisional_draft"))
        self.assertEqual(len(verify_preview_receipts(
            report["researchReceipts"], SECRET, "2099-01-01")), 35)
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["bettingReady"])

    def test_one_off_and_one_bad_raw_workout_keep_other_34(self):
        reply = run_request(raw_day(mixed=True))
        self.assertEqual(reply["status"], "200 OK", reply["body"][:300])
        result = json.loads(reply["body"])
        self.assertEqual((result["raceCount"], result["draftCount"],
                          result["holdCount"]), (36, 34, 2))
        self.assertEqual(result["researchReceiptCount"], 34)
        self.assertEqual(result["holdReasons"], {
            "after_provisional_off": 1, "missing_research": 1
        })
        self.assertEqual(result["sourceMaterials"]["status"], "unavailable")
        self.assertTrue(result["sourcePassport"]["sourceAuditAvailable"])
        held = [r for r in result["races"] if r["status"] == "hold"]
        self.assertEqual({(r["track"], r["race"]) for r in held},
                         {("東京", 1), ("東京", 2)})
        self.assertTrue(all(not r["tickets"] and not r["runners"] for r in held))
        by_race = {(r["track"], r["race"]): r for r in held}
        self.assertNotIn("reviewStage", by_race[("東京", 1)])
        self.assertEqual(by_race[("東京", 2)]["reviewStage"], "training")
        self.assertEqual(len(verify_preview_receipts(
            result["researchReceipts"], SECRET, "2099-01-01")), 34)
        self.assertNotIn("PRIVATE-WORKOUT", reply["body"].decode())


if __name__ == "__main__":
    unittest.main()
