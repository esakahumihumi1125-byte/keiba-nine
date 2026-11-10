"""Synthetic-only tests for private, provisional two-factor automatic picks."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, call as mock_call

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import build_owner_auto_drafts, compact_hold_diagnostics, VERSION
from owner_auto_draft_receipts import seal_auto_research_drafts
from owner_prestart_receipt import verify_preview_receipts, ReceiptError
from keiba_100yen_review import review_100yen
from private_service import create_app
from test_private_service import call, SETTINGS
from test_jrdb_training_hypothesis import setup as workout_fixture
from test_jrdb_recent_hypothesis import fixture as recent_fixture

JST = timezone(timedelta(hours=9))
DAY = "20990101"
PAIRS = [("S", "S"), ("S", "A"), ("A", "A"),
         ("A", "B"), ("B", "B"), ("B", "C"), ("C", "C")]


def programme(headcount=7, time="12:00"):
    return [{
        "racedate": DAY, "racekey": "0526ff01",
        "track": "東京", "race": 1, "post_time": time,
        "headcount": headcount,
    }]


def research(pairs=None):
    pairs = PAIRS if pairs is None else pairs
    ranks = []
    for number, (training, recent) in enumerate(pairs, 1):
        points = {"S": 4, "A": 3, "B": 2, "C": 1}
        total = (points[training] + points[recent]
                 if training in points and recent in points else None)
        ranks.append({
            "number": number, "training": training, "recent": recent,
            "pastFourthCorner": "insufficient",
            "completeFactors": int(training in points) + int(recent in points),
            "researchOrder": number if total is not None else None,
        })
    return {
        "version": "jrdb-owner-day-research-1",
        "date": DAY, "raceCount": 1,
        "researchOnly": True, "privateOwnerOnly": True,
        "sourceReadCount": 4,
        "officialJraVerified": False,
        "overallRankReady": False, "predictionReady": False, "bettingReady": False,
        "races": [{
            "track": "東京", "race": 1, "status": "research_only",
            "research": {
                "version": "jrdb-owner-runner-research-1",
                "track": "東京", "race": 1,
                "researchOnly": True, "privateOwnerOnly": True,
                "officialJraVerified": False, "overallRankReady": False,
                "predictionReady": False, "bettingReady": False,
                "runners": ranks, "runnerCount": len(ranks),
                "completeTwoFactorCount": sum(x["completeFactors"] == 2
                                              for x in ranks)
            }
        }],
    }


def generate(p=None, r=None, now=None):
    p = programme() if p is None else p
    r = research() if r is None else r
    now = datetime(2099, 1, 1, 9, 0, tzinfo=JST) if now is None else now
    return build_owner_auto_drafts(p, r, DAY, now=now)


class AutoDraftTests(unittest.TestCase):
    def test_seven_full_distinct_horses_produces_40_tickets(self):
        p, r = programme(), research()
        p0, r0 = copy.deepcopy(p), copy.deepcopy(r)
        out = generate(p, r)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(out["raceCount"], 1)
        self.assertEqual((out["draftCount"], out["holdCount"]), (1, 0))
        self.assertEqual(out["holdReasons"], {})
        self.assertFalse(out["officialJraVerified"])
        self.assertFalse(out["overallPredictionReady"])
        self.assertFalse(out["bettingReady"])
        self.assertFalse(out["autoPurchase"])
        race = out["races"][0]
        self.assertEqual(race["status"], "provisional_draft")
        self.assertEqual((race["first"], race["second"], race["third"]),
                         ([1,2], [1,2,3,4,5], [1,2,3,4,5,6,7]))
        self.assertEqual(race["points"], 40)
        self.assertEqual(race["amountYen"], 4000)
        self.assertEqual(out["weightedResearchOrder"],"training30_recent3")
        self.assertEqual(out["weightedResearchMax"],99)
        self.assertEqual([h["weightedResearchPoints"] for h in race["runners"]],
                         [99,96,66,63,33,30,0])
        self.assertEqual(len({tuple(x) for x in race["tickets"]}), 40)
        self.assertTrue(all(len(set(x)) == 3 for x in race["tickets"]))
        self.assertEqual([x["twoFactorGrade"] for x in race["runners"]],
                         ["S", "A", "A", "B", "B", "C", "C"])
        self.assertEqual(p, p0)
        self.assertEqual(r, r0)
        for forbidden in ("racekey", "horse_id", "horse_name", "idm",
                          "oikirisisu", "JRDB_API_KEY", "training_hints"):
            self.assertNotIn(forbidden, repr(out))

    def test_six_full_horses_produce_32_and_five_produce_24(self):
        for size, expected in ((6, 32), (5, 24), (4, 12)):
            with self.subTest(size=size):
                pairs = PAIRS[:size]
                out = generate(programme(size), research(pairs))
                race = out["races"][0]
                self.assertEqual(race["status"], "provisional_draft")
                self.assertEqual(race["points"], expected)

    def test_equal_grade_cutoffs_expand_safely_or_hold(self):
        # Rank 2/3 tie: expand first to three rather than pick by horse number.
        pairs = [("S","S"),("S","A"),("S","A"),
                 ("A","B"),("B","B"),("B","C"),("C","C")]
        race = generate(programme(7),research(pairs))["races"][0]
        self.assertEqual(race["status"],"provisional_draft")
        self.assertEqual(race["first"],[1,2,3])
        self.assertEqual(race["points"],36)
        self.assertEqual(race["runners"][1]["comparisonRank"],2)
        self.assertEqual(race["runners"][2]["comparisonRank"],2)
        # Rank 5/6 tie: keep those equal-score runners together in third.
        pairs = [("S","S"),("S","A"),("A","A"),
                 ("A","B"),("B","B"),("B","B"),("C","C")]
        race = generate(programme(7),research(pairs))["races"][0]
        self.assertEqual(race["status"],"provisional_draft")
        self.assertEqual(race["second"],[1,2,3,4])
        self.assertEqual(race["third"],[1,2,3,4,5,6,7])
        self.assertEqual(race["points"],30)
        # All runners tied: any first boundary is arbitrary, so hold.
        pairs = [("A","A")]*7
        race = generate(programme(7),research(pairs))["races"][0]
        self.assertEqual(race["status"],"hold")
        self.assertEqual(race["reason"],"ambiguous_equal_grade_boundary")
        self.assertEqual(race["tickets"],[])

    def test_training_overrides_bad_recent_form_in_provisional_ranking(self):
        # A horse with training S / recent C must outrank training A /
        # recent S, while no overall 10-factor grade is claimed.
        pairs=[("S","S"),("A","S"),("S","C"),
               ("A","A"),("B","B"),("B","C"),("C","C")]
        row=generate(programme(7),research(pairs))["races"][0]
        self.assertEqual(row["status"],"provisional_draft")
        self.assertEqual([h["number"] for h in row["runners"][:3]], [1,3,2])
        self.assertEqual(row["first"],[1,3])
        self.assertEqual(row["runners"][1]["training"],"S")
        self.assertEqual(row["runners"][1]["recent"],"C")
        self.assertEqual(row["runners"][1]["weightedResearchPoints"],90)
        self.assertEqual(row["runners"][2]["weightedResearchPoints"],69)
        self.assertFalse(row["overallPredictionReady"])

    def test_missing_factor_or_time_holds_no_tickets(self):
        pairs = PAIRS[:-1]+[("未評価","C")]
        missing = generate(programme(7),research(pairs))["races"][0]
        self.assertEqual(missing["reason"],"missing_factors")
        self.assertEqual(missing["tickets"],[])
        past_with_missing=generate(
            programme(7), research(pairs),
            now=datetime(2099,1,1,12,30,tzinfo=JST))
        self.assertEqual(past_with_missing["races"][0]["reason"],
                         "after_provisional_off")
        self.assertEqual(past_with_missing["holdReasons"],
                         {"after_provisional_off":1})
        no_time = generate(programme(time=None),research())["races"][0]
        self.assertEqual(no_time["reason"],"missing_post_time")
        self.assertEqual(no_time["points"],0)

    def test_missing_or_zero_programme_runner_count_cannot_create_tickets(self):
        for missing in (None, 0, True, "7", -1, 19):
            with self.subTest(headcount=repr(missing)):
                p=programme()
                p[0]["headcount"]=missing
                result=generate(p=p)
                self.assertEqual((result["draftCount"],result["holdCount"]),(0,1))
                self.assertEqual(result["holdReasons"],
                                 {"unconfirmed_runner_count":1})
                held=result["races"][0]
                self.assertEqual(held["reason"],"unconfirmed_runner_count")
                self.assertEqual(held["runners"],[])
                self.assertEqual(held["tickets"],[])
                self.assertEqual(held["points"],0)
                self.assertEqual(held["amountYen"],0)
                self.assertEqual(seal_auto_research_drafts(
                    result,SETTINGS["KEIBA_OWNER_PASSWORD"],
                    now=datetime(2099,1,1,9,tzinfo=JST)),[])
        # A source-reported lower nonzero count remains a specific mismatch
        # rather than being silently assumed to be the actual full field.
        mismatched=generate(p=programme(headcount=6))
        self.assertEqual(mismatched["races"][0]["reason"],
                         "runner_count_mismatch")
        # Post-off cannot reconstruct grades and tickets, independent of
        # whether the source headcount was known before the start.
        p=programme(headcount=None)
        closed=generate(p=p,now=datetime(2099,1,1,12,30,tzinfo=JST))
        self.assertEqual(closed["races"][0]["reason"],"after_provisional_off")

    def test_already_started_or_historical_race_does_not_create_bets(self):
        for now in (datetime(2099,1,1,12,0,tzinfo=JST),
                    datetime(2099,1,2,8,0,tzinfo=JST)):
            r = generate(now=now)["races"][0]
            self.assertEqual(r["reason"],"after_provisional_off")
            self.assertEqual(r["tickets"],[])

    def test_post_off_http_research_never_displays_new_ranks(self):
        past = datetime(2099, 1, 1, 12, 30, tzinfo=JST)
        invalid = research()
        # A latest fetch may contain changed or malformed post-race data.
        # Neither future tickets nor retrospectively computed rankings are
        # published in an after-off research request.
        invalid["races"][0]["research"]["runners"][0]["number"] = 2
        report = generate(r=invalid, now=past)
        race = report["races"][0]
        self.assertEqual(race["reason"], "after_provisional_off")
        self.assertEqual(race["status"], "hold")
        self.assertEqual(race["runners"], [])
        self.assertEqual(race["tickets"], [])
        self.assertEqual(report["holdReasons"], {"after_provisional_off": 1})
        self.assertEqual(report["draftCount"], 0)
        self.assertEqual(
            seal_auto_research_drafts(report, SETTINGS["KEIBA_OWNER_PASSWORD"],
                                      now=past), [])

    def test_private_review_stage_is_only_for_prestart_missing_research(self):
        src = research()
        src["races"][0].update(status="needs_review",
                               research=None, reviewStage="training")
        row = generate(r=src)["races"][0]
        self.assertEqual(row["status"], "hold")
        self.assertEqual(row["reason"], "missing_research")
        self.assertEqual(row["reviewStage"], "training")
        self.assertEqual(row["points"], 0)
        self.assertEqual(row["tickets"], [])
        self.assertNotIn("reviewStage", generate(
            r=src, now=datetime(2099, 1, 1, 13, tzinfo=JST)
        )["races"][0])
        older = copy.deepcopy(src)
        del older["races"][0]["reviewStage"]
        self.assertNotIn("reviewStage", generate(r=older)["races"][0])
        for bad in ("horse_name: PRIVATE", "training extra", [], None, "raw"):
            broken = copy.deepcopy(src)
            broken["races"][0]["reviewStage"] = bad
            if bad is None:
                # Legacy omission is accepted, an explicit None also carries
                # no failure-stage diagnostics.
                self.assertNotIn("reviewStage", generate(r=broken)["races"][0])
                continue
            with self.subTest(stage=repr(bad)), self.assertRaises(CoverageError):
                generate(r=broken)
        unsafe = research()
        unsafe["races"][0]["reviewStage"] = "training"
        with self.assertRaises(CoverageError):
            generate(r=unsafe)

    def test_reported_withdrawal_is_held_with_no_fresh_tickets(self):
        src = research()
        src["races"][0].update(
            status="needs_review", research=None,
            reviewStage="entries", reviewKind="provider_withdrawal")
        result = generate(r=src)
        held = result["races"][0]
        self.assertEqual(result["draftCount"],0)
        self.assertEqual(result["holdReasons"],{"provider_withdrawal":1})
        self.assertEqual(held["reason"],"provider_withdrawal")
        self.assertEqual(held["runners"],[])
        self.assertEqual(held["tickets"],[])
        self.assertEqual(held["points"],0)
        self.assertNotIn("reviewKind",repr(held))
        self.assertNotIn("reviewStage",held)
        self.assertEqual(seal_auto_research_drafts(
            result,SETTINGS["KEIBA_OWNER_PASSWORD"],
            now=datetime(2099,1,1,9,tzinfo=JST)),[])
        late=generate(r=src,now=datetime(2099,1,1,12,30,tzinfo=JST))
        self.assertEqual(late["races"][0]["reason"],"after_provisional_off")
        self.assertNotIn("reviewKind",repr(late))
        for kind,stage in (
            ("provider_withdrawal","training"),
            ("invalid","entries"),("provider_withdrawal",None)):
            with self.subTest(kind=kind,stage=stage):
                bad=copy.deepcopy(src)
                bad["races"][0]["reviewKind"]=kind
                bad["races"][0]["reviewStage"]=stage
                with self.assertRaises(CoverageError):
                    generate(r=bad)
        bad=research()
        bad["races"][0]["reviewKind"]="provider_withdrawal"
        with self.assertRaises(CoverageError):
            generate(r=bad)

    def test_signed_auto_drafts_are_prestart_only_and_pending_in_roi(self):
        now=datetime(2099,1,1,9,0,tzinfo=JST)
        result=generate(now=now)
        signed=seal_auto_research_drafts(
            result,SETTINGS["KEIBA_OWNER_PASSWORD"],now=now)
        self.assertEqual(len(signed),1)
        snapshot=signed[0]["snapshot"]
        self.assertEqual(snapshot["date"],"2099-01-01")
        self.assertEqual(snapshot["race"],1)
        self.assertEqual(len(snapshot["trifectaTickets"]),40)
        self.assertFalse(snapshot["actualPurchase"])
        self.assertFalse(snapshot["scheduleVerified"])
        self.assertFalse(snapshot["predictionVerified"])
        preds=verify_preview_receipts(
            signed,SETTINGS["KEIBA_OWNER_PASSWORD"],"2099-01-01")
        review=review_100yen(preds,[])
        self.assertEqual(review["pendingRaces"],1)
        self.assertEqual(review["pendingStakeYen"],4000)
        self.assertEqual(review["reviewedRaces"],0)
        self.assertIsNone(review["roiPercent"])
        self.assertEqual(seal_auto_research_drafts(
            result,SETTINGS["KEIBA_OWNER_PASSWORD"],
            now=datetime(2099,1,1,12,0,tzinfo=JST)),[])
        corrupted=copy.deepcopy(result)
        corrupted["races"][0]["tickets"][0][0]=17
        with self.assertRaises(ReceiptError):
            seal_auto_research_drafts(
                corrupted,SETTINGS["KEIBA_OWNER_PASSWORD"],now=now)

    def test_bad_dates_wrong_race_and_untrusted_status_are_rejected(self):
        with self.assertRaises(CoverageError):
            generate(now=datetime(2099,1,1,9,0))
        r=research()
        r["officialJraVerified"]=True
        with self.assertRaises(CoverageError):
            generate(r=r)
        r=research()
        r["races"][0]["research"]["runners"][0]["number"]=2
        held=generate(r=r)["races"][0]
        self.assertEqual(held["reason"], "invalid_two_factor")
        self.assertEqual(held["validationIssue"], "runner_shape")
        self.assertEqual(held["runners"], [])
        self.assertEqual(held["tickets"], [])
        r=research()
        r["races"][0]["race"]=2
        with self.assertRaises(CoverageError):
            generate(r=r)
        with self.assertRaises(CoverageError):
            generate(p=programme()+programme())

    def test_one_invalid_race_holds_without_blocking_another_race(self):
        p=programme()
        second=copy.deepcopy(p[0])
        second.update(track="京都", race=2, racekey="0826ff02")
        p.append(second)
        report=research()
        invalid=copy.deepcopy(report["races"][0])
        invalid.update(track="京都", race=2)
        invalid["research"].update(track="京都", race=2)
        invalid["research"]["runners"][0]["completeFactors"]=0
        report["races"].append(invalid)
        report["raceCount"]=2
        result=generate(p=p, r=report)
        self.assertEqual((result["draftCount"], result["holdCount"]), (1, 1))
        self.assertEqual(result["races"][0]["points"], 40)
        self.assertEqual(result["races"][1]["reason"], "invalid_two_factor")
        self.assertEqual(result["races"][1]["validationIssue"], "completeness")
        self.assertEqual(result["races"][1]["runners"], [])
        self.assertEqual(result["races"][1]["tickets"], [])
        self.assertEqual(result["holdReasons"], {"invalid_two_factor":1})
        signed=seal_auto_research_drafts(
            result, SETTINGS["KEIBA_OWNER_PASSWORD"],
            now=datetime(2099,1,1,9,0,tzinfo=JST))
        self.assertEqual(len(signed), 1)
        self.assertEqual(signed[0]["snapshot"]["track"], "東京")

    def test_redacted_operator_hold_summary_counts_only_fixed_categories(self):
        base=generate()
        self.assertEqual(compact_hold_diagnostics(base),"none")
        after=generate(now=datetime(2099,1,1,12,30,tzinfo=JST))
        self.assertEqual(compact_hold_diagnostics(after),
                         "after_provisional_off:1")
        reported=copy.deepcopy(base)
        reported["holdCount"]=4
        reported["holdReasons"]={
            "provider_withdrawal":1,
            "missing_factors":2,
            "UNTRUSTED_PAID_HORSE_ID":1,
        }
        self.assertEqual(compact_hold_diagnostics(reported),
                         "provider_withdrawal:1,missing_factors:2,other:1")
        self.assertNotIn("UNTRUSTED",compact_hold_diagnostics(reported))
        invalid=copy.deepcopy(reported)
        invalid["holdReasons"]["missing_factors"]="PRIVATE_LICENSED_TEXT"
        self.assertEqual(compact_hold_diagnostics(invalid),"invalid")
        invalid["holdReasons"]={"provider_withdrawal":4}
        invalid["holdCount"]=1
        self.assertEqual(compact_hold_diagnostics(invalid),"invalid")
        self.assertEqual(compact_hold_diagnostics({"holdReasons":{}}),
                         "invalid")

    def test_needs_review_only_holds(self):
        r=research()
        r["races"][0]["status"]="needs_review"
        r["races"][0]["research"]=None
        out=generate(r=r)
        self.assertEqual(out["holdCount"],1)
        self.assertEqual(out["races"][0]["reason"],"missing_research")


class AutoDraftHTTPTests(unittest.TestCase):
    def setUp(self):
        self.config={
            **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY":"1",
            "KEIBA_RENDER_PREVIEW_ONLY":"0", "JRDB_PRIVATE_ENABLED":"1",
            "JRDB_API_KEY":"synthetic-api","JRDB_AUTH_KEY":"synthetic-auth"
        }
        self.app=create_app(self.config)
        self.venue_patch = patch("private_service.fetch_venue_conditions",
                                 return_value=[])
        self.mock_venue = self.venue_patch.start()
        self.addCleanup(self.venue_patch.stop)

    def test_mobile_page_and_auto_route_are_private(self):
        root=call(self.app,"/")["body"].decode()
        self.assertIn('href="/owner-auto-forecast"',root)
        for route in ("/owner-auto-forecast","/owner-auto-forecast.js",
                      "/owner-auto-forecast.css"):
            self.assertEqual(call(self.app,route)["status"],"200 OK")
            self.assertIn(call(self.app,route,auth="")["status"].split()[0],("303","401"))
            self.assertEqual(call(create_app(SETTINGS),route)["status"],"404 Not Found")
        page = call(self.app, "/owner-auto-forecast")["body"].decode()
        self.assertIn("正式100点の計算方法・安全確認", page)
        self.assertIn("調教A＝20/30点", page)
        self.assertIn("近走C＝0/3点", page)
        self.assertIn("合計87点のS", page)
        self.assertIn("正式採点には昇格していません", page)
        self.assertIn("正式3連単を作りません", page)
        js=call(self.app,"/owner-auto-forecast.js")["body"].decode()
        self.assertIn("/api/jrdb/owner-auto-draft",js)
        self.assertNotIn("innerHTML",js)
        self.assertIn("RECEIPTS_KEY",js)
        self.assertIn("saveAutoReceipts",js)
        self.assertNotIn("keiba-nine-owner-real-purchases-v1",js)
        self.assertNotIn("JRDB_API_KEY",js)

    def test_four_reads_and_generated_tickets_with_mocked_derived_research(self):
        p=programme()
        with (patch("private_service.fetch_race_program",return_value=[{"unused":"synthetic"}]) as a,
              patch("private_service.normalize_program_rows",return_value=p),
              patch("private_service.fetch_horse_entries",return_value=[]) as b,
              patch("private_service.fetch_training_analysis",return_value=[]) as c,
              patch("private_service.fetch_recent_runs",return_value=[]) as d,
              patch("private_service.owner_day_research",return_value=research()) as e,
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00+09:00")):
            out=call(self.app,"/api/jrdb/owner-auto-draft",
                     QUERY_STRING="date="+DAY)
        self.assertEqual(out["status"],"200 OK")
        body=json.loads(out["body"])
        self.assertEqual(body["draftCount"],1)
        self.assertEqual(body["races"][0]["points"],40)
        self.assertEqual(body["sourceReadCount"],4)
        self.assertEqual(body["raceContext"]["version"],"race-context-1")
        self.assertEqual(body["raceContext"]["conditionProviderReadCount"],1)
        self.assertEqual(body["raceContext"]["conditionProviderFetchStatus"],"received")
        self.assertEqual(body["raceContext"]["races"][0]["going"],"未確認")
        self.assertFalse(body["raceContext"]["raceConditionsVerified"])
        self.mock_venue.assert_called_once_with(DAY)
        preview=body["tenFactorPreview"]
        self.assertEqual(preview["factorCount"],10)
        self.assertEqual(preview["totalWeight"],100)
        self.assertEqual(preview["gradeThresholds"],{"S":85,"A":70,"B":55})
        self.assertEqual(preview["fullPredictionRaceCount"],0)
        self.assertFalse(preview["overallPredictionReady"])
        self.assertEqual(preview["races"][0]["horses"][0]["grades"]["training"],"S")
        self.assertEqual(preview["races"][0]["horses"][0]["grades"]["recent"],"S")
        self.assertEqual(preview["races"][0]["horses"][0]["grades"]["pace"],"未評価")
        self.assertEqual(preview["races"][0]["horses"][0]["overallGrade"],"未評価")
        self.assertEqual(preview["races"][0]["horses"][0]["verifiedFactorCount"],0)
        self.assertTrue(body["serverStamped"])
        self.assertFalse(body["captureAuditVerified"])
        self.assertEqual(body["researchReceiptCount"],1)
        self.assertEqual(len(body["researchReceipts"][0]["snapshot"]["trifectaTickets"]),40)
        for stub in (a,b,c,d,e):
            self.assertEqual(stub.call_count,1)
        for forbidden in ("horse_name","racekey","horse_id",
                          "synthetic-api","synthetic-auth","oikirisisu","idm"):
            self.assertNotIn(forbidden,out["body"].decode())

    def test_realistic_four_source_reads_include_redacted_materials(self):
        from test_jrdb_day_materials_progress import fixture
        from jrdb_program_preview import normalize_program_rows
        raw, entries, training, recent, _conditions = fixture()
        app = create_app(self.config)
        with (patch("private_service.fetch_race_program", return_value=raw) as a,
              patch("private_service.fetch_horse_entries", return_value=entries) as b,
              patch("private_service.fetch_training_analysis", return_value=training) as c,
              patch("private_service.fetch_recent_runs", return_value=recent) as d,
              patch("private_service._now_in_jst",
                    return_value="2026-11-01T09:00:00+09:00")):
            result = call(app,"/api/jrdb/owner-auto-draft",
                          QUERY_STRING="date=20261101")
        self.assertEqual(result["status"],"200 OK")
        body = json.loads(result["body"])
        materials = body["sourceMaterials"]
        self.assertEqual(materials["status"],"observed")
        self.assertEqual(materials["observedFactorSlots"],8)
        self.assertEqual(materials["gradedNewFactors"],0)
        self.assertEqual(materials["races"][0]["runnerCount"],1 if
                         materials["races"][0]["track"]=="京都" else 2)
        self.assertEqual(body["sourceReadCount"],4)
        self.assertEqual(body["tenFactorPreview"]["factorCount"],10)
        self.assertEqual(body["tenFactorPreview"]["fullPredictionRaceCount"],0)
        source_passport = body["sourcePassport"]
        self.assertEqual(source_passport["version"],"owner-day-source-passport-1")
        self.assertEqual(source_passport["raceCount"],body["raceCount"])
        self.assertTrue(source_passport["sourceAuditAvailable"])
        self.assertEqual(source_passport["newProviderRequests"],0)
        self.assertEqual(source_passport["gradedFactors"],0)
        self.assertFalse(source_passport["independentJraVerified"])
        self.assertFalse(source_passport["purchaseReady"])
        self.assertEqual(source_passport["observedMaterialRaces"],body["raceCount"])
        self.assertTrue(all(x["verifiedFactorCount"]==0
                            and not x["completeTenFactorReady"]
                            for x in source_passport["races"]))
        self.assertEqual(body["raceContext"]["conditionProviderFetchStatus"],"received")
        self.assertFalse(body["officialJraVerified"])
        for forbidden in ("racekey","horse_id","PRIVATE-SIRE",
                          "PRIVATE-JOCKEY","PRIVATE-MATERNAL"):
            self.assertNotIn(forbidden,result["body"].decode())
        for mock in (a,b,c,d):
            mock.assert_called_once_with("20261101")

    def test_missing_optional_materials_does_not_fail_forecast(self):
        with (patch("private_service.fetch_race_program",return_value=[]),
              patch("private_service.normalize_program_rows",
                    return_value=programme()),
              patch("private_service.fetch_horse_entries",return_value=[]),
              patch("private_service.fetch_training_analysis",return_value=[]),
              patch("private_service.fetch_recent_runs",return_value=[]),
              patch("private_service.owner_day_research",return_value=research()),
              patch("private_service.observe_owner_draft_materials",
                    side_effect=CoverageError("synthetic-unsafe-provider-value")),
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00+09:00")):
            result=call(self.app,"/api/jrdb/owner-auto-draft",
                        QUERY_STRING="date="+DAY)
        self.assertEqual(result["status"],"200 OK")
        body=json.loads(result["body"])
        self.assertEqual(body["draftCount"],1)
        self.assertEqual(body["sourceMaterials"]["status"],"unavailable")
        self.assertEqual(body["sourceMaterials"]["gradedNewFactors"],0)
        self.assertEqual(body["sourceMaterials"]["races"],[])
        self.assertEqual(body["sourcePassport"]["newProviderRequests"],0)
        self.assertEqual(body["sourcePassport"]["gradedFactors"],0)
        self.assertTrue(body["sourcePassport"]["sourceAuditAvailable"])
        self.assertIsNone(
            body["sourcePassport"]["races"][0]["additionalFieldCounts"])
        self.assertEqual(body["tenFactorPreview"]["factorCount"],10)
        self.assertEqual(body["tenFactorPreview"]["fullPredictionRaceCount"],0)

    def test_optional_current_conditions_attach_to_each_race_without_grades(self):
        p=programme()
        p[0].update(surface="芝",distance_m=2000,turn="左")
        # The five-source response is owner-private and the venue condition
        # is NOT independent JRA verification or horse suitability.
        self.mock_venue.return_value=[{
            "holdingkey":"0526ff","racedate":DAY,
            "turf_condition_cd":"3","dirt_condition_cd":"1",
            "updated_at":"2099-01-01T08:30:00+09:00",
            "horse_name":"REDACT-ME"
        }]
        with (patch("private_service.fetch_race_program",return_value=[]),
              patch("private_service.normalize_program_rows",return_value=p),
              patch("private_service.fetch_horse_entries",return_value=[]),
              patch("private_service.fetch_training_analysis",return_value=[]),
              patch("private_service.fetch_recent_runs",return_value=[]),
              patch("private_service.owner_day_research",return_value=research()),
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00+09:00")):
            result=call(self.app,"/api/jrdb/owner-auto-draft",
                        QUERY_STRING="date="+DAY)
        self.assertEqual(result["status"],"200 OK")
        body=json.loads(result["body"])
        ctx=body["raceContext"]
        self.assertEqual(ctx["conditionProviderFetchStatus"],"received")
        row=ctx["races"][0]
        self.assertEqual((row["surface"],row["distance_m"],row["turn"],row["going"]),
                         ("芝",2000,"左","重"))
        self.assertFalse(row["horseCourseSuitabilityAssessed"])
        self.assertFalse(row["horseGoingSuitabilityAssessed"])
        self.assertFalse(ctx["raceConditionsVerified"])
        self.assertFalse(body["overallPredictionReady"])
        self.assertEqual(body["tenFactorPreview"]["fullPredictionRaceCount"],0)
        self.assertNotIn("REDACT-ME",result["body"].decode())

    def test_optional_condition_api_failure_preserves_signed_research_receipt(self):
        from jrdb_private import JRDBError
        self.mock_venue.side_effect=JRDBError("SECRET-PAID-RESPONSE")
        with (patch("private_service.fetch_race_program",return_value=[]),
              patch("private_service.normalize_program_rows",return_value=programme()),
              patch("private_service.fetch_horse_entries",return_value=[]),
              patch("private_service.fetch_training_analysis",return_value=[]),
              patch("private_service.fetch_recent_runs",return_value=[]),
              patch("private_service.owner_day_research",return_value=research()),
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00+09:00")):
            result=call(self.app,"/api/jrdb/owner-auto-draft",
                        QUERY_STRING="date="+DAY)
        self.assertEqual(result["status"],"200 OK")
        body=json.loads(result["body"])
        self.assertEqual(body["researchReceiptCount"],1)
        self.assertEqual(body["draftCount"],1)
        self.assertEqual(body["raceContext"]["conditionProviderFetchStatus"],"unavailable")
        self.assertEqual(body["raceContext"]["conditionProviderReadCount"],1)
        self.assertEqual(body["raceContext"]["races"][0]["going"],"未確認")
        self.assertNotIn("SECRET-PAID-RESPONSE",result["body"].decode())

    def test_optional_server_archive_first_write_wins(self):
        from owner_receipt_archive import FLAG, SIGNING_KEY, DSN_KEY
        secret = "synthetic-independent-signing-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        config = {**self.config, FLAG:"1", SIGNING_KEY:secret,
                  DSN_KEY:"postgresql://fake_owner:fake_password@db.invalid/keiba"}
        app = create_app(config)
        original = {}
        def fake_save(settings, signing_key, day, received):
            self.assertEqual(signing_key, secret)
            for item in received:
                s = item["snapshot"]
                original.setdefault((day,s["track"],s["race"]), copy.deepcopy(item))
            return list(original.values())
        first_report = generate()
        changed = copy.deepcopy(first_report)
        row = changed["races"][0]
        row["first"] = [3,4]
        row["second"] = [3,4,5,6,7]
        row["third"] = [1,2,3,4,5,6,7]
        row["tickets"] = [[a,b,c] for a in row["first"]
                          for b in row["second"] for c in row["third"]
                          if len({a,b,c}) == 3]
        row["points"] = len(row["tickets"])
        row["amountYen"] = 100 * row["points"]
        self.assertEqual(row["points"], 40)
        with (patch("private_service.fetch_race_program", return_value=[]),
              patch("private_service.normalize_program_rows", return_value=programme()),
              patch("private_service.fetch_horse_entries", return_value=[]),
              patch("private_service.fetch_training_analysis", return_value=[]),
              patch("private_service.fetch_recent_runs", return_value=[]),
              patch("private_service.owner_day_research", return_value=research()),
              patch("private_service.build_owner_auto_drafts",
                    side_effect=[first_report,changed]),
              patch("private_service.save_first_and_read", side_effect=fake_save),
              patch("private_service._now_in_jst", side_effect=[
                  "2099-01-01T09:00:00+09:00", "2099-01-01T09:00:00+09:00",
                  "2099-01-01T09:30:00+09:00", "2099-01-01T09:30:00+09:00"])):
            early = call(app, "/api/jrdb/owner-auto-draft", QUERY_STRING="date="+DAY)
            later = call(app, "/api/jrdb/owner-auto-draft", QUERY_STRING="date="+DAY)
        self.assertEqual(early["status"], "200 OK")
        self.assertEqual(later["status"], "200 OK")
        e, l = json.loads(early["body"]), json.loads(later["body"])
        self.assertTrue(e["archiveEnabled"])
        self.assertEqual(e["archiveRecordCount"], 1)
        self.assertEqual(e["archiveConflictCount"], 0)
        self.assertEqual(len(e["researchReceipts"]), 1)
        self.assertEqual(l["archiveRecordCount"], 1)
        self.assertEqual(l["archiveConflictCount"], 1)
        self.assertEqual(l["researchReceipts"], [])
        self.assertEqual((l["draftCount"], l["holdCount"]), (0,1))
        self.assertEqual(l["holdReasons"], {"archived_earlier_draft":1})
        self.assertEqual(l["races"][0]["reason"], "archived_earlier_draft")
        self.assertEqual(l["races"][0]["status"], "hold")
        self.assertEqual(l["races"][0]["tickets"], [])
        self.assertEqual(l["races"][0]["points"], 0)
        self.assertEqual(l["races"][0]["runners"], [])
        self.assertEqual(len(original), 1)
        self.assertEqual(e["researchReceipts"][0], list(original.values())[0])

    def test_archive_changed_provisional_off_time_is_also_a_conflict(self):
        from owner_receipt_archive import FLAG, SIGNING_KEY, DSN_KEY
        secret = "synthetic-independent-signing-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        app = create_app({**self.config, FLAG: "1", SIGNING_KEY: secret,
                          DSN_KEY: "postgresql://fake_owner:fake_password@db.invalid/keiba"})
        first = generate()
        changed = copy.deepcopy(first)
        changed["races"][0]["postTime"] = "13:00"
        saved = {}
        def fake_save(settings, signing_key, day, received):
            for item in received:
                snapshot = item["snapshot"]
                saved.setdefault((day, snapshot["track"], snapshot["race"]),
                                 copy.deepcopy(item))
            return list(saved.values())
        with (patch("private_service.fetch_race_program", return_value=[]),
              patch("private_service.normalize_program_rows", return_value=programme()),
              patch("private_service.fetch_horse_entries", return_value=[]),
              patch("private_service.fetch_training_analysis", return_value=[]),
              patch("private_service.fetch_recent_runs", return_value=[]),
              patch("private_service.owner_day_research", return_value=research()),
              patch("private_service.build_owner_auto_drafts", side_effect=[first,changed]),
              patch("private_service.save_first_and_read", side_effect=fake_save),
              patch("private_service._now_in_jst", side_effect=[
                  "2099-01-01T09:00:00+09:00", "2099-01-01T09:00:00+09:00",
                  "2099-01-01T09:10:00+09:00", "2099-01-01T09:10:00+09:00"])):
            a = call(app, "/api/jrdb/owner-auto-draft", QUERY_STRING="date="+DAY)
            b = call(app, "/api/jrdb/owner-auto-draft", QUERY_STRING="date="+DAY)
        self.assertEqual(a["status"], "200 OK")
        self.assertEqual(b["status"], "200 OK")
        result = json.loads(b["body"])
        self.assertEqual(result["archiveConflictCount"], 1)
        self.assertEqual(result["races"][0]["status"], "hold")
        self.assertEqual(result["holdReasons"], {"archived_earlier_draft": 1})
        self.assertEqual(result["researchReceipts"], [])

    def test_optional_archive_failure_stops_without_new_receipts(self):
        from owner_receipt_archive import FLAG, SIGNING_KEY, DSN_KEY, ArchiveUnavailable
        secret = "synthetic-independent-signing-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        config = {**self.config, FLAG:"1", SIGNING_KEY:secret,
                  DSN_KEY:"postgresql://fake_owner:fake_password@db.invalid/keiba"}
        with (patch("private_service.fetch_race_program", return_value=[]),
              patch("private_service.normalize_program_rows", return_value=programme()),
              patch("private_service.fetch_horse_entries", return_value=[]),
              patch("private_service.fetch_training_analysis", return_value=[]),
              patch("private_service.fetch_recent_runs", return_value=[]),
              patch("private_service.owner_day_research", return_value=research()),
              patch("private_service.save_first_and_read",
                    side_effect=ArchiveUnavailable("private-connection-details")),
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00+09:00")):
            res = call(create_app(config), "/api/jrdb/owner-auto-draft",
                       QUERY_STRING="date="+DAY)
        self.assertEqual(res["status"], "502 Bad Gateway")
        body=json.loads(res["body"])
        self.assertEqual(body["failureStage"], "receipt_archiving")
        self.assertEqual(body["failureKind"], "receipt_guard")
        self.assertNotIn("private-connection-details",res["body"].decode())
        self.assertNotIn("researchReceipts",res["body"].decode())

    def test_iso_clock_does_not_create_post_start_tickets(self):
        # Production _now_in_jst returns ISO text, not datetime.
        for clock, expected in (
            ("2099-01-01T09:00:00+09:00", "provisional_draft"),
            ("2099-01-01T12:00:00+09:00", "hold"),
        ):
            with self.subTest(clock=clock):
                with (patch("private_service.fetch_race_program", return_value=[]),
                      patch("private_service.normalize_program_rows", return_value=programme()),
                      patch("private_service.fetch_horse_entries", return_value=[]),
                      patch("private_service.fetch_training_analysis", return_value=[]),
                      patch("private_service.fetch_recent_runs", return_value=[]),
                      patch("private_service.owner_day_research", return_value=research()),
                      patch("private_service._now_in_jst", return_value=clock)):
                    out = call(self.app, "/api/jrdb/owner-auto-draft",
                               QUERY_STRING="date="+DAY)
                self.assertEqual(out["status"], "200 OK")
                data = json.loads(out["body"])
                self.assertEqual(data["races"][0]["status"], expected)
                self.assertEqual(data["researchReceiptCount"],
                                 int(expected == "provisional_draft"))
                if expected == "hold":
                    self.assertEqual(data["races"][0]["reason"],
                                     "after_provisional_off")
                    self.assertEqual(data["researchReceipts"], [])

    def test_naive_clock_never_gets_signed(self):
        with (patch("private_service.fetch_race_program", return_value=[]),
              patch("private_service.normalize_program_rows", return_value=programme()),
              patch("private_service.fetch_horse_entries", return_value=[]),
              patch("private_service.fetch_training_analysis", return_value=[]),
              patch("private_service.fetch_recent_runs", return_value=[]),
              patch("private_service.owner_day_research", return_value=research()),
              patch("private_service._now_in_jst",
                    return_value="2099-01-01T09:00:00")):
            out = call(self.app, "/api/jrdb/owner-auto-draft",
                       QUERY_STRING="date="+DAY)
        self.assertEqual(out["status"], "502 Bad Gateway")
        body=json.loads(out["body"])
        self.assertEqual(body["failureDetail"], "server_clock")
        self.assertNotIn("researchReceipts", body)

    def test_no_jrdb_calls_without_auth_or_in_preview_or_without_keys(self):
        for env in ({"auth":""},{"HTTP_X_KEIBA_REQUEST":""},
                    {"HTTP_SEC_FETCH_SITE":"cross-site"}):
            with self.subTest(env=env), patch("private_service.fetch_race_program") as call_source:
                response=call(self.app,"/api/jrdb/owner-auto-draft",
                              QUERY_STRING="date="+DAY,**env)
                self.assertIn(response["status"].split()[0],("401","403"))
                call_source.assert_not_called()
        for cfg in (SETTINGS, {**self.config,"JRDB_PRIVATE_ENABLED":"0"},
                    {**self.config,"JRDB_API_BASE_URL":"https://malicious.invalid/v1"}):
            with patch("private_service.fetch_race_program") as source:
                response=call(create_app(cfg),"/api/jrdb/owner-auto-draft",
                              QUERY_STRING="date="+DAY)
                self.assertEqual(response["status"],"503 Service Unavailable")
                source.assert_not_called()
        for query in ("","date=20260230","date=20261108&date=20261109",
                      "date=../etc","date=20261108&race=1"):
            with patch("private_service.fetch_race_program") as source:
                response=call(self.app,"/api/jrdb/owner-auto-draft",QUERY_STRING=query)
                self.assertEqual(response["status"],"400 Bad Request")
                source.assert_not_called()

    def test_failure_stage_is_safe_and_does_not_expose_provider_data(self):
        from jrdb_private import JRDBError
        cases = (
            ('fetch_training_analysis', JRDBError('private-training-value'),
             'training', 'provider'),
            ('owner_day_research', CoverageError('private-horse-id'),
             'day_research', 'source_validation'),
            ('seal_auto_research_drafts', ReceiptError('private-signer-value'),
             'receipt_signing', 'receipt_guard'),
        )
        for method, err, stage, kind in cases:
            with self.subTest(stage=stage):
                with (patch('private_service.fetch_race_program', return_value=[]),
                      patch('private_service.normalize_program_rows', return_value=programme()),
                      patch('private_service.fetch_horse_entries', return_value=[]),
                      patch('private_service.fetch_training_analysis', return_value=[]),
                      patch('private_service.fetch_recent_runs', return_value=[]),
                      patch('private_service.owner_day_research', return_value=research()),
                      patch('private_service._now_in_jst',
                            return_value="2099-01-01T09:00:00+09:00"),
                      patch('private_service.' + method, side_effect=err)):
                    out = call(self.app, '/api/jrdb/owner-auto-draft',
                               QUERY_STRING='date=' + DAY)
                self.assertEqual(out['status'], '502 Bad Gateway')
                body = json.loads(out['body'])
                self.assertEqual(body['failureStage'], stage)
                self.assertEqual(body['failureKind'], kind)
                for private in ('private-training-value', 'private-horse-id',
                                'private-signer-value', 'horse_id', 'racekey'):
                    self.assertNotIn(private, out['body'].decode())

    def test_jrdb_http_status_categories_guide_recovery_without_leaking(self):
        from jrdb_private import JRDBError
        cases = (
            ("401", "provider_auth", "entries"),
            ("403", "provider_entitlement", "training"),
            ("429", "provider_rate_limit", "recent"),
            ("500", "provider", "programme"),
        )
        for status, expected, stage in cases:
            with self.subTest(status=status, stage=stage):
                method = {
                    "programme": "fetch_race_program",
                    "entries": "fetch_horse_entries",
                    "training": "fetch_training_analysis",
                    "recent": "fetch_recent_runs",
                }[stage]
                with (
                    patch('private_service.fetch_race_program', return_value=[]),
                    patch('private_service.normalize_program_rows',
                          return_value=programme()),
                    patch('private_service.fetch_horse_entries', return_value=[]),
                    patch('private_service.fetch_training_analysis', return_value=[]),
                    patch('private_service.fetch_recent_runs', return_value=[]),
                    patch('private_service.' + method,
                          side_effect=JRDBError('JRDB request failed (HTTP ' +
                                                status + ')')),
                    patch('private_service.logging.warning') as logger,
                ):
                    response = call(self.app, '/api/jrdb/owner-auto-draft',
                                    QUERY_STRING='date=' + DAY)
                self.assertEqual(response['status'], '502 Bad Gateway')
                result = json.loads(response['body'])
                self.assertEqual(result['failureStage'], stage)
                self.assertEqual(result['failureKind'], expected)
                self.assertIsNone(result['failureDetail'])
                self.assertNotIn('researchReceipts', result)
                self.assertNotIn('trifectaTickets', result)
                self.assertNotIn('api_key', response['body'].decode())
                self.assertNotIn('x-user-key', response['body'].decode())
                self.assertEqual(logger.call_count, 1)
                self.assertEqual(
                    logger.call_args.args[0],
                    'KEIBA_AUTO_DRAFT_FAILURE stage=%s kind=%s detail=%s',
                )
                self.assertEqual(logger.call_args.args[1:], (stage, expected, 'none'))

    def test_whole_day_draft_failure_reports_only_fixed_reason(self):
        from jrdb_owner_auto_draft import DAY_DRAFT_ISSUES
        self.assertEqual(DAY_DRAFT_ISSUES["Research snapshot mismatch"],
                         "research_header")
        for raw_message, expected in (
            ("Research snapshot mismatch", "research_header"),
            ("Programme and research slots differ", "race_set_mismatch"),
            ("sensitive-unknown-provider-field", "other"),
        ):
            with self.subTest(expected=expected):
                with (patch("private_service.fetch_race_program", return_value=[]),
                      patch("private_service.normalize_program_rows", return_value=programme()),
                      patch("private_service.fetch_horse_entries", return_value=[]),
                      patch("private_service.fetch_training_analysis", return_value=[]),
                      patch("private_service.fetch_recent_runs", return_value=[]),
                      patch("private_service.owner_day_research", return_value=research()),
                      patch("private_service.build_owner_auto_drafts",
                            side_effect=CoverageError(raw_message))):
                    out = call(self.app, "/api/jrdb/owner-auto-draft",
                               QUERY_STRING="date="+DAY)
                self.assertEqual(out["status"], "502 Bad Gateway")
                body=json.loads(out["body"])
                self.assertEqual(body["failureStage"], "draft_generation")
                self.assertEqual(body["failureKind"], "source_validation")
                self.assertEqual(body["failureDetail"], expected)
                self.assertNotIn(raw_message, out["body"].decode())

    def test_provider_failure_never_leaks_source_data_or_makes_tickets(self):
        from jrdb_private import JRDBError
        with patch("private_service.fetch_race_program",
                   side_effect=JRDBError("secret-horse-X")):
            out=call(self.app,"/api/jrdb/owner-auto-draft",
                     QUERY_STRING="date="+DAY)
        self.assertEqual(out["status"],"502 Bad Gateway")
        self.assertNotIn("secret-horse-X",out["body"].decode())
        self.assertNotIn("tickets",out["body"].decode())


if __name__=="__main__":
    unittest.main()
