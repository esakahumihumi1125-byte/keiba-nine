"""36R acceptance through the REAL owner pipeline with JRDB beta-shaped rows.

No JRDB/JRA network, paid API calls, keys or results. Source field layouts
mirror the provider's documented /tra, /tky, /tcy and /tze contracts.
Most importantly /tcy and /tze may have horse_number=null: they MUST join
by the exact same horse_id and racekey, not silently remove every runner.

The earlier 36R synthetic test patched owner_day_research itself; this test
deliberately does NOT patch normalizers, evidence/grade joins or the builder.
Synthetic points are NOT proof of usable real JRDB or formal ten-factor grades.
"""
import json
import sys
import unittest
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import SETTINGS, call
from owner_prestart_receipt import verify_preview_receipts
from jrdb_owner_auto_draft import JST
from jrdb_private import JRDBError

DAY = "20990101"
SECRET = SETTINGS["KEIBA_OWNER_PASSWORD"]
VENUES = ("05", "08", "03")
# 30/3 scoring: S/S, S/A, A/S, A/A, B/B, B/C, C/C.
TRAIN = (80, 80, 65, 65, 50, 50, 30)
PAST_IDM = (75, 60, 75, 60, 45, 30, 30)


def provider_shaped_day(*, incomplete_recent=False, corrupt_horse_id=False):
    """Build all 36R with only documented field names and beta-like types."""
    programme, entries, training, recent = [], [], [], []
    for venue in VENUES:
        for race in range(1, 13):
            racekey = f"{venue}9901{race:02d}"
            programme.append({
                "racekey": racekey, "racedate": DAY, "post_time": "1500",
                "racecourse_cd": venue, "track_type": "1", "turn_cd": "2",
                "distance": "1600", "headcount": 7,
                "race_name": "合成テストレース",
            })
            for index in range(7):
                horse_number = f"{index + 1:02d}"
                horse_id = f"{int(venue):02d}{race:02d}{index+1:08d}"
                entry = {
                    "racekey": racekey, "racedate": DAY,
                    "horse_number": horse_number, "horse_id": horse_id,
                    "withdrawn_flag": "0",
                    "foottype_cd": str(index % 4 + 1),
                    "jockey_index": str(index + 1),
                    "stable_index": str((index + 1) * 2),
                    "distance_aptitude_cd1": "5",
                    "mudder_cd": "2",
                    "weight_to_carry": "56.0",
                }
                entries.append(entry)
                training.append({
                    "racedate": DAY, "racekey": racekey,
                    "horse_number": None, "horse_id": horse_id,
                    "oikirisisu": TRAIN[index],
                    "siagarisisu": TRAIN[index],
                    "exercise_amount_eval": "B",
                })
                recent.append({
                    "racedate": DAY, "racekey": racekey,
                    "horse_number": None, "horse_id": horse_id,
                    "race_back_1_racedate": "20981220",
                    "race_back_1_order_of_finish": 4,
                    "race_back_1_idm": str(PAST_IDM[index]),
                    "race_back_1_later3f_time": 356,
                    "race_back_1_corner4_order": 3,
                    "race_back_2_racedate": "20981201",
                    "race_back_2_order_of_finish": 5,
                    "race_back_2_idm": str(PAST_IDM[index]),
                    "race_back_2_later3f_time": 363,
                    "race_back_2_corner4_order": 5,
                })
    if incomplete_recent:
        # One runner is a legitimate debutant/unknown; hold only that 1R.
        entry = recent[0]
        for run in (1, 2):
            for name in ("racedate", "order_of_finish", "idm",
                         "later3f_time", "corner4_order"):
                entry.pop(f"race_back_{run}_{name}", None)
    if corrupt_horse_id:
        # An otherwise correct /tcy row cannot be attached by a null number
        # when its horse_id differs from /tky. Quarantine that R.
        training[0]["horse_id"] = "aaaaaaaaaaaa"
    return programme, entries, training, recent


def run_private_pipeline(fixture, *, tka_error=None):
    p, e, t, z = fixture
    config = {
        **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
        "KEIBA_RENDER_PREVIEW_ONLY": "0",
        "JRDB_PRIVATE_ENABLED": "1", "JRDB_API_KEY": "TEST-ONLY",
        "JRDB_AUTH_KEY": "TEST-ONLY",
        "JRDB_API_BASE_URL": "https://api.bigtime.world/v1",
    }
    stamped = "2099-01-01T09:00:00+09:00"
    with (patch("private_service.fetch_race_program",
                return_value=p) as tra,
          patch("private_service.fetch_horse_entries",
                return_value=e) as tky,
          patch("private_service.fetch_training_analysis",
                return_value=t) as tcy,
          patch("private_service.fetch_recent_runs",
                return_value=z) as tze,
          patch("private_service.fetch_venue_conditions",
                return_value=[], side_effect=tka_error) as tka,
          patch("private_service._now_in_jst",
                return_value=stamped)):
        response = call(create_app(config), "/api/jrdb/owner-auto-draft",
                        QUERY_STRING="date=" + DAY)
        counts = [f.call_count for f in (tra, tky, tcy, tze, tka)]
    return response, counts


class JrdBDocsShapedThirtySixAcceptance(unittest.TestCase):
    def test_documented_null_horse_numbers_still_produce_36_signed_research_drafts(self):
        sources = provider_shaped_day()
        frozen = deepcopy(sources)
        response, reads = run_private_pipeline(sources)
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        self.assertEqual(sources, frozen)
        data = json.loads(response["body"])
        self.assertEqual(data["raceCount"], 36)
        self.assertEqual(data["sourceReadCount"], 4)
        self.assertEqual((data["draftCount"], data["holdCount"]), (36, 0))
        self.assertEqual(data["researchReceiptCount"], 36)
        self.assertTrue(all(row["points"] == 40 for row in data["races"]))
        self.assertTrue(all(len(row["tickets"]) == 40 for row in data["races"]))
        verified = verify_preview_receipts(data["researchReceipts"],
                                           SECRET, "2099-01-01")
        self.assertEqual(len(verified), 36)
        self.assertTrue(all(len(r["trifectaTickets"]) == 40 for r in verified))
        self.assertEqual(data["tenFactorPreview"]["fullPredictionRaceCount"], 0)
        self.assertFalse(data["overallPredictionReady"])
        self.assertFalse(data["officialJraVerified"])
        self.assertFalse(data["bettingReady"])
        for secret in ("horse_id", "horse_name", "racekey",
                       "TEST-ONLY", "oikirisisu", "race_back_1_idm"):
            self.assertNotIn(secret, response["body"].decode("utf-8"))

    def test_unscored_recent_runner_holds_its_race_not_other_35(self):
        response, reads = run_private_pipeline(
            provider_shaped_day(incomplete_recent=True))
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        data = json.loads(response["body"])
        self.assertEqual((data["draftCount"], data["holdCount"]), (35, 1))
        self.assertEqual(data["researchReceiptCount"], 35)
        self.assertEqual(data["holdReasons"], {"missing_factors": 1})
        self.assertTrue(any(r["status"] == "hold" and r["points"] == 0
                            for r in data["races"]))
        self.assertFalse(data["officialJraVerified"])

    def test_wrong_null_number_horse_id_cannot_borrow_another_grade(self):
        response, reads = run_private_pipeline(
            provider_shaped_day(corrupt_horse_id=True))
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        data = json.loads(response["body"])
        self.assertEqual((data["draftCount"], data["holdCount"]), (35, 1))
        self.assertEqual(data["researchReceiptCount"], 35)
        self.assertTrue(any(r["status"] == "hold" and r["points"] == 0
                            for r in data["races"]))
        self.assertFalse(data["overallPredictionReady"])


    def test_seven_one_run_horses_can_still_form_one_prestart_research_race(self):
        """A real /tze one-run observation is not equivalent to a missing feed.

        Earlier, any single-runner with only one scored history forced the
        entire race into hold; this must only affect the 3pt research band.
        """
        p, e, t, z = provider_shaped_day()
        racekey = p[0]["racekey"]
        for row in z:
            if row["racekey"] == racekey:
                for name in ("racedate", "order_of_finish", "idm",
                             "later3f_time", "corner4_order"):
                    row.pop("race_back_2_" + name, None)
        frozen = deepcopy((p, e, t, z))
        response, reads = run_private_pipeline((p, e, t, z))
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual((p, e, t, z), frozen)
        data = json.loads(response["body"])
        self.assertEqual((data["draftCount"], data["holdCount"]), (36, 0))
        self.assertEqual(data["researchReceiptCount"], 36)
        first = next(r for r in data["races"]
                     if r["track"] == p[0]["racekey"][:2].replace("05", "東京") and
                     r["race"] == 1)
        self.assertEqual(first["status"], "provisional_draft")
        self.assertEqual(first["points"], 40)
        self.assertTrue(all(h["recent"] in ("S", "A", "B", "C")
                            for h in first["runners"]))
        self.assertTrue(all(h["recentObserved"]["datedRuns"] == 1
                            and h["recentObserved"]["completedRuns"] == 1
                            for h in first["runners"]))
        self.assertFalse(data["overallPredictionReady"])
        self.assertFalse(data["officialJraVerified"])
        self.assertFalse(data["bettingReady"])
        self.assertNotIn("horse_id", response["body"].decode())
        self.assertNotIn("racekey", response["body"].decode())


    def test_tky_two_prior_results_quarantines_just_one_unsupported_one_run(self):
        """More /tky references than /tze observed runs blocks a 1-run grade."""
        p, e, t, z = provider_shaped_day()
        key = p[0]["racekey"]
        for row in z:
            if row["racekey"] == key:
                for name in ("racedate", "order_of_finish", "idm",
                             "later3f_time", "corner4_order"):
                    row.pop("race_back_2_" + name, None)
        # One horse has two independent historical references but /tze
        # now contains only one run. Others are genuine one-run profiles.
        e[0].update({
            "lastrace_resultkey1": "1234567820981220",
            "lastrace_resultkey2": "1234567820981201",
            "lastrace_resultkey3": None,
            "lastrace_resultkey4": None,
            "lastrace_resultkey5": None,
        })
        original = deepcopy((p, e, t, z))
        response, reads = run_private_pipeline((p, e, t, z))
        self.assertEqual(response["status"], "200 OK")
        self.assertEqual(reads, [1, 1, 1, 1, 1])
        self.assertEqual(original, (p, e, t, z))
        data = json.loads(response["body"])
        self.assertEqual((data["raceCount"], data["draftCount"],
                          data["holdCount"], data["researchReceiptCount"]),
                         (36, 35, 1, 35))
        hold = [r for r in data["races"] if r["status"] == "hold"]
        self.assertEqual(len(hold), 1)
        self.assertEqual(hold[0]["reason"], "missing_factors")
        self.assertEqual(hold[0]["points"], 0)
        suspect = [h for h in hold[0]["runners"] if h["number"] == 1]
        self.assertEqual(len(suspect), 1)
        self.assertEqual(suspect[0]["recent"], "未評価")
        self.assertEqual(suspect[0]["recentObserved"]["datedRuns"], 1)
        self.assertEqual(suspect[0]["recentObserved"]["completedRuns"], 1)
        self.assertFalse(data["overallPredictionReady"])
        self.assertFalse(data["officialJraVerified"])
        self.assertFalse(data["bettingReady"])
        for private in ("horse_id", "racekey", "1234567820981220",
                        "1234567820981201", "TEST-ONLY"):
            self.assertNotIn(private, response["body"].decode())

    def test_tka_failure_is_visible_but_never_blocks_four_core_drafts(self):
        """Provider HTTP category is safe: no body/IDs and no extra paid call."""
        sources = provider_shaped_day()
        frozen = deepcopy(sources)
        for error, expected in (
            ("JRDB request failed (HTTP 404)", "provider_endpoint_missing"),
            ("JRDB request failed (HTTP 503)", "provider_server_error"),
            ("JRDB returned an unsuccessful response", "provider_response_contract"),
        ):
            with self.subTest(expected=expected):
                response, counts = run_private_pipeline(
                    sources, tka_error=JRDBError(error))
                self.assertEqual(response["status"], "200 OK")
                self.assertEqual(counts, [1, 1, 1, 1, 1])
                obj = json.loads(response["body"])
                ctx = obj["raceContext"]
                self.assertEqual(ctx["conditionProviderReadCount"], 1)
                self.assertEqual(ctx["conditionProviderFetchStatus"], "unavailable")
                self.assertEqual(ctx["conditionProviderFailureCode"], expected)
                self.assertEqual((obj["draftCount"], obj["holdCount"]), (36, 0))
                self.assertEqual(obj["researchReceiptCount"], 36)
                self.assertFalse(obj["overallPredictionReady"])
                self.assertFalse(obj["officialJraVerified"])
                self.assertFalse(obj["bettingReady"])
                for private in ("horse_id", "racekey", "TEST-ONLY", "api_key"):
                    self.assertNotIn(private, response["body"].decode())
        self.assertEqual(sources, frozen)

    def test_empty_tka_data_is_received_not_official_going(self):
        response, counts = run_private_pipeline(provider_shaped_day())
        self.assertEqual(counts, [1, 1, 1, 1, 1])
        self.assertEqual(response["status"], "200 OK")
        obj = json.loads(response["body"])
        ctx = obj["raceContext"]
        self.assertEqual(ctx["conditionProviderFailureCode"], "none")
        self.assertEqual(ctx["conditionProviderFetchStatus"], "received")
        self.assertEqual(ctx["goingAvailableCount"], 0)
        self.assertFalse(ctx["raceConditionsVerified"])
