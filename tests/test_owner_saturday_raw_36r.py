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


def run_request(data, *, clocks=None):
    programme, entries, training, previous = data
    clock_patch = (patch("private_service._now_in_jst", side_effect=clocks)
                   if clocks is not None else
                   patch("private_service._now_in_jst",
                         return_value="2099-01-01T09:00:00+09:00"))
    with (
        patch("private_service.fetch_race_program", return_value=programme) as tra,
        patch("private_service.fetch_horse_entries", return_value=entries) as tky,
        patch("private_service.fetch_training_analysis", return_value=training) as tcy,
        patch("private_service.fetch_recent_runs", return_value=previous) as tze,
        patch("private_service.fetch_venue_conditions", return_value=[]) as tka,
        clock_patch as clock,
    ):
        reply = call(owner_app(), "/api/jrdb/owner-auto-draft",
                     QUERY_STRING="date=" + DAY)
    for adapter in (tra, tky, tcy, tze, tka):
        adapter.assert_called_once_with(DAY)
    clock.assert_called()
    if clocks is not None:
        assert clock.call_count == 2
    return reply


def raw_specific_saturday_2026_11_14():
    """An entirely synthetic current-calendar feed; no real JRDB request.

    The provider racekey's year component and every source row's date
    must agree, not just the HTTP query date.
    """
    programme, entries, training, previous = copy.deepcopy(raw_day())
    for rows in (programme, entries, training, previous):
        for row in rows:
            assert row["racedate"] == DAY
            row["racedate"] = "20261114"
            row["racekey"] = row["racekey"].replace("99aa", "26aa")
    for row in previous:
        row["race_back_1_racedate"] = "20261015"
        row["race_back_2_racedate"] = "20260915"
    return programme, entries, training, previous


def run_november_14_synthetic(data, *, clocks):
    """Full authenticated HTTP path with four/five mocked provider reads."""
    date = "20261114"
    programme, entries, training, previous = data
    with (
        patch("private_service.fetch_race_program", return_value=programme) as tra,
        patch("private_service.fetch_horse_entries", return_value=entries) as tky,
        patch("private_service.fetch_training_analysis", return_value=training) as tcy,
        patch("private_service.fetch_recent_runs", return_value=previous) as tze,
        patch("private_service.fetch_venue_conditions", return_value=[]) as tka,
        patch("private_service._now_in_jst", side_effect=clocks) as clock,
    ):
        reply = call(owner_app(), "/api/jrdb/owner-auto-draft",
                     QUERY_STRING="date=" + date)
    for adapter in (tra, tky, tcy, tze, tka):
        adapter.assert_called_once_with(date)
    assert clock.call_count == 2
    return reply


class SaturdayRawDayTests(unittest.TestCase):
    def test_november_14_real_calendar_date_prestart_and_final_gate(self):
        """Saturday 2026-11-14: source join and immutable HMAC cutoff.

        Data is deliberately synthetic: successful assertions must not be
        mistaken for JRDB weekly delivery, actual race venues or JRA proof.
        """
        raw = raw_specific_saturday_2026_11_14()
        snapshot = copy.deepcopy(raw)
        prior = run_november_14_synthetic(raw, clocks=[
            "2026-11-14T09:00:00+09:00",
            "2026-11-14T09:01:00+09:00",
        ])
        self.assertEqual(prior["status"], "200 OK", prior["body"][:250])
        data = json.loads(prior["body"])
        self.assertEqual(data["date"], "20261114")
        self.assertEqual((data["raceCount"], data["draftCount"],
                          data["holdCount"]), (36, 36, 0))
        self.assertEqual(data["researchReceiptCount"], 36)
        self.assertEqual(data["sourceReadCount"], 4)
        self.assertEqual(len(verify_preview_receipts(
            data["researchReceipts"], SECRET, "2026-11-14")), 36)
        for r in data["researchReceipts"]:
            self.assertEqual(r["snapshot"]["date"], "2026-11-14")
            self.assertEqual(r["snapshot"]["scheduledOffAt"],
                             "2026-11-14T15:00:00+09:00")
            self.assertFalse(r["snapshot"]["actualPurchase"])
        self.assertEqual(raw, snapshot,
                         "provider rows must not be rewritten after parsing")
        for marker in ("PRIVATE-TEST-HORSE", "horse_id", "raw-synthetic",
                       "20261015", "racekey", "API_KEY"):
            self.assertNotIn(marker, prior["body"].decode())
        self.assertFalse(data["officialJraVerified"])
        self.assertFalse(data["overallPredictionReady"])

        # The same day, but now after all provisional start times:
        # retrieving a historical source never creates post-hoc tickets.
        after = run_november_14_synthetic(raw, clocks=[
            "2026-11-14T15:01:00+09:00",
            "2026-11-14T15:01:01+09:00",
        ])
        self.assertEqual(after["status"], "200 OK", after["body"][:250])
        late = json.loads(after["body"])
        self.assertEqual((late["raceCount"], late["draftCount"],
                          late["holdCount"]), (36, 0, 36))
        self.assertEqual(late["holdReasons"], {"after_provisional_off": 36})
        self.assertEqual(late["researchReceiptCount"], 0)
        self.assertEqual(late["researchReceipts"], [])
        self.assertTrue(all(not row["tickets"] and not row["runners"]
                            for row in late["races"]))
        self.assertFalse(late["bettingReady"])

        # Even if the provider finishes exactly as the clock crosses
        # the temporary start, the final server gate refuses new records.
        crosses_off = run_november_14_synthetic(raw, clocks=[
            "2026-11-14T14:59:59+09:00",
            "2026-11-14T15:00:01+09:00",
        ])
        self.assertEqual(crosses_off["status"], "200 OK",
                         crosses_off["body"][:250])
        crossed = json.loads(crosses_off["body"])
        self.assertEqual((crossed["draftCount"], crossed["holdCount"]),
                         (0, 36))
        self.assertEqual(crossed["researchReceiptCount"], 0)
        self.assertEqual(crossed["researchReceipts"], [])
        self.assertFalse(crossed["officialJraVerified"])

    def test_per_runner_remaining_factor_field_presence_from_same_reads(self):
        # Horse-level availability, not skill or S/A/B/C. The fixture
        # carries historical dates and past-corner fields, but intentionally
        # lacks sire/draw/personnel fields. No extra paid fetch is allowed.
        reply = run_request(raw_day())
        self.assertEqual(reply["status"], "200 OK")
        report = json.loads(reply["body"])
        evidence = report["runnerSourceEvidence"]
        self.assertEqual(evidence["version"], "owner-runner-source-hints-1")
        self.assertEqual(evidence["raceCount"], 36)
        self.assertEqual(evidence["observedRaceCount"], 36)
        self.assertEqual(evidence["unavailableRaceCount"], 0)
        self.assertEqual(evidence["newProviderRequests"], 0)
        self.assertEqual(evidence["verifiedNewFactorCount"], 0)
        self.assertFalse(evidence["overallPredictionReady"])
        self.assertFalse(evidence["officialJraVerified"])
        self.assertFalse(evidence["rawSourceRowsIncluded"])
        self.assertEqual(evidence["factorFields"], [
            "pedigree", "draw_weight", "jockey_stable",
            "rotation", "past_corner"])
        self.assertTrue(all(row["status"] == "observed"
                            and len(row["runners"]) == 7
                            for row in evidence["races"]))
        first = evidence["races"][0]["runners"][0]
        self.assertEqual(first, {
            "number": 1,
            "observed": {
                "pedigree": False, "draw_weight": False,
                "jockey_stable": False, "rotation": True,
                "past_corner": True,
            },
            "verifiedFactorCount": 0,
        })
        for private in ("PRIVATE-TEST-HORSE", "PRIVATE-WORKOUT",
                        "PRIVATE-PAST", "horse_id", "racekey",
                        "race_back_1_idm", "sire_name", "trainer_name"):
            self.assertNotIn(private, reply["body"].decode())
        self.assertEqual(report["researchReceiptCount"], 36)

    def test_poststart_runner_fields_cannot_recreate_held_rosters(self):
        raw = raw_specific_saturday_2026_11_14()
        late = run_november_14_synthetic(raw, clocks=[
            "2026-11-14T15:01:00+09:00",
            "2026-11-14T15:01:01+09:00",
        ])
        self.assertEqual(late["status"], "200 OK")
        data = json.loads(late["body"])
        hints = data["runnerSourceEvidence"]
        self.assertEqual(hints["raceCount"], 36)
        self.assertEqual(hints["observedRaceCount"], 0)
        self.assertTrue(all(r["status"] == "held"
                            and r["runners"] == [] for r in hints["races"]))
        self.assertEqual(data["researchReceiptCount"], 0)

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
        source_events = [s.split("KEIBA_AUTO_DRAFT_SOURCE ", 1)[1]
                         for s in captured.output if "KEIBA_AUTO_DRAFT_SOURCE " in s]
        expected_events = [
            f"stage={stage} state={state}"
            for stage in ("programme", "entries", "training", "recent",
                          "optional_going")
            for state in ("begin", "returned")
        ]
        self.assertEqual(source_events, expected_events)
        # The new stage trace is only fixed allowlisted words, never paid
        # data, requested day, URL, race keys, horse IDs or owner secrets.
        for event in source_events:
            self.assertLess(len(event), 70)
            for forbidden in (
                    DAY, "PRIVATE", "raw-synthetic", "http", "api_key",
                    "horse_id", "racekey", "tickets", "trifecta",
                    "0526", "x-user-key"):
                self.assertNotIn(forbidden, event)

    def test_optional_context_finishes_after_one_off_no_new_late_ticket(self):
        programme, entries, training, previous = raw_day()
        # One race starts while the optional fifth /tka is being processed.
        # Initial research/HMAC capture still occurred BEFORE its start.
        target = next(r for r in programme if r["racekey"] == "0599aa02")
        target["post_time"] = "1000"
        times = ["2099-01-01T09:59:00+09:00",
                 "2099-01-01T10:01:00+09:00"]
        with self.assertLogs(level="WARNING") as logs:
            response = run_request(
                (programme, entries, training, previous), clocks=times)
        self.assertEqual(response["status"], "200 OK", response["body"][:200])
        report = json.loads(response["body"])
        self.assertEqual((report["raceCount"], report["draftCount"],
                          report["holdCount"]), (36, 35, 1))
        self.assertEqual(report["holdReasons"], {"after_provisional_off": 1})
        self.assertEqual(report["researchReceiptCount"], 35)
        self.assertEqual(len(verify_preview_receipts(
            report["researchReceipts"], SECRET, "2099-01-01")), 35)
        self.assertTrue(report["sourcePassport"]["sourceAuditAvailable"])
        self.assertEqual(report["sourcePassport"]["raceCount"], 36)
        held = [x for x in report["races"] if x["status"] == "hold"]
        self.assertEqual([(r["track"], r["race"]) for r in held],
                         [("東京", 2)])
        self.assertEqual(held[0]["reason"], "after_provisional_off")
        self.assertFalse(held[0]["tickets"])
        self.assertFalse(held[0]["runners"])
        self.assertEqual(held[0]["points"], 0)
        self.assertEqual(held[0]["amountYen"], 0)
        one = next(x for x in report["tenFactorPreview"]["races"]
                   if x["track"] == "東京" and x["race"] == 2)
        self.assertEqual(one["runnerCount"], 0)
        self.assertEqual(one["horses"], [])
        successes = [x for x in logs.output
                     if "KEIBA_AUTO_DRAFT_PIPELINE" in x]
        self.assertEqual(len(successes), 1)
        self.assertIn("expired_on_return=1", successes[0])
        self.assertIn("hold_causes=after_provisional_off:1", successes[0])
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["overallPredictionReady"])
        self.assertNotIn("PRIVATE-", response["body"].decode())

    def test_invalid_final_clock_never_returns_new_signed_tickets(self):
        with self.assertLogs(level="WARNING") as captured:
            response=run_request(
                raw_day(),clocks=[
                    "2099-01-01T09:00:00+09:00",
                    "2099-01-01T09:00:00",  # Naive, no timezone.
                ])
        self.assertEqual(response["status"],"502 Bad Gateway")
        body=json.loads(response["body"])
        self.assertEqual(body["failureStage"],"final_prestart_gate")
        self.assertEqual(body["failureKind"],"source_validation")
        self.assertNotIn("researchReceipts",body)
        self.assertNotIn("tickets",body)
        self.assertTrue(any(
            "stage=final_prestart_gate" in line
            for line in captured.output))
        self.assertFalse(any(
            "KEIBA_AUTO_DRAFT_PIPELINE status=complete" in line
            for line in captured.output))

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
                       "2099-01-01","withdrawn_flag"):
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

    def test_one_undisclosed_programme_headcount_holds_only_that_race(self):
        programme,entries,training,previous=raw_day()
        # Actual normalization converts a missing /tra count to None.
        # Seven observed /tky entries are not proof of the declared field.
        target=next(row for row in programme if row["racekey"]=="0599aa02")
        target.pop("headcount")
        reply=run_request((programme,entries,training,previous))
        self.assertEqual(reply["status"],"200 OK",reply["body"][:300])
        data=json.loads(reply["body"])
        self.assertEqual((data["raceCount"],data["draftCount"],data["holdCount"]),
                         (36,35,1))
        self.assertEqual(data["holdReasons"],{"unconfirmed_runner_count":1})
        self.assertEqual(data["researchReceiptCount"],35)
        held=[row for row in data["races"] if row["status"]=="hold"]
        self.assertEqual([(row["track"],row["race"]) for row in held],
                         [("東京",2)])
        self.assertEqual(held[0]["reason"],"unconfirmed_runner_count")
        self.assertEqual(held[0]["tickets"],[])
        self.assertEqual(held[0]["runners"],[])
        self.assertEqual(held[0]["points"],0)
        self.assertEqual(len(verify_preview_receipts(
            data["researchReceipts"],SECRET,"2099-01-01")),35)
        self.assertEqual(data["sourceMaterials"]["status"],"partial")
        self.assertEqual(len(data["sourceMaterials"]["races"]),35)
        self.assertEqual(data["sourcePassport"]["observedMaterialRaces"],35)
        missing=next(x for x in data["sourcePassport"]["races"]
                     if x["track"]=="東京" and x["race"]==2)
        self.assertFalse(missing["sourceMaterialsObserved"])
        self.assertIsNone(missing["additionalFieldCounts"])
        healthy=next(x for x in data["sourcePassport"]["races"]
                     if x["track"]=="東京" and x["race"]==3)
        self.assertTrue(healthy["sourceMaterialsObserved"])
        self.assertEqual(healthy["additionalFieldCounts"]["pedigree"],0)
        self.assertFalse(data["officialJraVerified"])
        self.assertFalse(data["bettingReady"])
        self.assertNotIn("PRIVATE-TEST-HORSE",reply["body"].decode())

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
        self.assertEqual(result["sourceMaterials"]["status"], "partial")
        self.assertEqual(len(result["sourceMaterials"]["races"]),35)
        self.assertTrue(result["sourcePassport"]["sourceAuditAvailable"])
        self.assertEqual(result["sourcePassport"]["observedMaterialRaces"],35)
        unobserved=next(x for x in result["sourcePassport"]["races"]
                        if x["track"]=="東京" and x["race"]==2)
        self.assertFalse(unobserved["sourceMaterialsObserved"])
        self.assertIsNone(unobserved["additionalFieldCounts"])
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
