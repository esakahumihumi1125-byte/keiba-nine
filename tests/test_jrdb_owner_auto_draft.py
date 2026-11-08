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
from jrdb_owner_auto_draft import build_owner_auto_drafts, VERSION
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
        pairs = [("S","S"),("S","A"),("A","S"),
                 ("A","B"),("B","B"),("B","C"),("C","C")]
        race = generate(programme(7),research(pairs))["races"][0]
        self.assertEqual(race["status"],"provisional_draft")
        self.assertEqual(race["first"],[1,2,3])
        self.assertEqual(race["points"],36)
        self.assertEqual(race["runners"][1]["comparisonRank"],2)
        self.assertEqual(race["runners"][2]["comparisonRank"],2)
        # Rank 5/6 tie: keep those equal-score runners together in third.
        pairs = [("S","S"),("S","A"),("A","A"),
                 ("A","B"),("B","B"),("C","A"),("C","C")]
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

    def test_missing_factor_or_time_holds_no_tickets(self):
        pairs = PAIRS[:-1]+[("未評価","C")]
        missing = generate(programme(7),research(pairs))["races"][0]
        self.assertEqual(missing["reason"],"missing_factors")
        self.assertEqual(missing["tickets"],[])
        no_time = generate(programme(time=None),research())["races"][0]
        self.assertEqual(no_time["reason"],"missing_post_time")
        self.assertEqual(no_time["points"],0)

    def test_already_started_or_historical_race_does_not_create_bets(self):
        for now in (datetime(2099,1,1,12,0,tzinfo=JST),
                    datetime(2099,1,2,8,0,tzinfo=JST)):
            r = generate(now=now)["races"][0]
            self.assertEqual(r["reason"],"after_provisional_off")
            self.assertEqual(r["tickets"],[])

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
        signed=seal_auto_research_drafts(
            result, SETTINGS["KEIBA_OWNER_PASSWORD"],
            now=datetime(2099,1,1,9,0,tzinfo=JST))
        self.assertEqual(len(signed), 1)
        self.assertEqual(signed[0]["snapshot"]["track"], "東京")

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

    def test_mobile_page_and_auto_route_are_private(self):
        root=call(self.app,"/")["body"].decode()
        self.assertIn('href="/owner-auto-forecast"',root)
        for route in ("/owner-auto-forecast","/owner-auto-forecast.js",
                      "/owner-auto-forecast.css"):
            self.assertEqual(call(self.app,route)["status"],"200 OK")
            self.assertIn(call(self.app,route,auth="")["status"].split()[0],("303","401"))
            self.assertEqual(call(create_app(SETTINGS),route)["status"],"404 Not Found")
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
                    return_value=datetime(2099,1,1,9,0,tzinfo=JST))):
            out=call(self.app,"/api/jrdb/owner-auto-draft",
                     QUERY_STRING="date="+DAY)
        self.assertEqual(out["status"],"200 OK")
        body=json.loads(out["body"])
        self.assertEqual(body["draftCount"],1)
        self.assertEqual(body["races"][0]["points"],40)
        self.assertEqual(body["sourceReadCount"],4)
        self.assertTrue(body["serverStamped"])
        self.assertFalse(body["captureAuditVerified"])
        self.assertEqual(body["researchReceiptCount"],1)
        self.assertEqual(len(body["researchReceipts"][0]["snapshot"]["trifectaTickets"]),40)
        for stub in (a,b,c,d,e):
            self.assertEqual(stub.call_count,1)
        for forbidden in ("horse_name","racekey","horse_id",
                          "synthetic-api","synthetic-auth","oikirisisu","idm"):
            self.assertNotIn(forbidden,out["body"].decode())

    def test_no_jrdb_calls_without_auth_or_in_preview_or_without_keys(self):
        for env in ({"auth":""},{"HTTP_X_KEIBA_REQUEST":""},
                    {"HTTP_SEC_FETCH_SITE":"cross-site"}):
            with self.subTest(env=env), patch("private_service.fetch_race_program") as call_source:
                response=call(self.app,"/api/jrdb/owner-auto-draft",
                              QUERY_STRING="date="+DAY,**env)
                self.assertIn(response["status"].split()[0],("401","403"))
                call_source.assert_not_called()
        for cfg in (SETTINGS,{**self.config,"JRDB_PRIVATE_ENABLED":"0"}):
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
                            return_value=datetime(2099, 1, 1, 9, 0, tzinfo=JST)),
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
