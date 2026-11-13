"""Synthetic only: derive an exact JRA URL without inventing CNAME checksums."""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jra_card_link_resolver import (
    HOME, VERSION, JraLinkResolutionError, resolve_racecard_link,
)
from test_private_service import SETTINGS, call
from private_service import create_app

DAY = "2026-11-14"
SEED = ("https://own.jra.jp/JRADB/accessD.html?"
        "CNAME=pw01dde0108202605031120261114%2F1C")
TARGET1 = ("https://app.jra.jp/JRADB/accessD.html?"
           "CNAME=sw01dde0108202605030120261114%2F57")
TARGET12 = ("https://app.jra.jp/JRADB/accessD.html?"
            "CNAME=sw01dde0108202605031220261114%2F5E")
HOME_HTML = f"""<html><body><h1>今週の開催・注目レース</h1>
  <p>11月14日土曜</p>
  <a href="{SEED}">京都11R 15時45分発走予定 デイリー杯2歳S</a>
  <p>11月15日日曜</p><a href="https://other.test/evil">京都11R 偽物</a>
  </body></html>"""
SEED_HTML = f"""<html><body><h1>出馬表</h1>
 <p>2026年11月14日（土曜）5回京都3日</p>
 <p>発走時刻：15時45分 <img alt="11レース"></p>
 <p>コース：1,600メートル（芝・右 外）</p>
 <a href="{TARGET1}">1R</a>
 <a href="{TARGET12}">12R</a>
 </body></html>"""


def stub(pages):
    calls = []

    def get(url):
        calls.append(url)
        if url not in pages:
            raise AssertionError("Unexpected JRA GET " + url)
        return pages[url]
    return get, calls


class JraCardLinkTests(unittest.TestCase):
    def test_discover_one_honest_card_link_from_current_meeting(self):
        get, calls = stub({HOME: HOME_HTML, SEED: SEED_HTML})
        data = resolve_racecard_link(
            DAY, "京都", 1, today=date(2026, 11, 14), fetch_html=get)
        self.assertEqual(calls, [HOME, SEED])
        self.assertEqual(data["version"], VERSION)
        self.assertEqual(data["officialRacecardUrl"], TARGET1)
        self.assertEqual((data["date"], data["track"], data["race"]),
                         (DAY, "京都", 1))
        self.assertTrue(data["officialLinkFound"])
        for name in ("officialLinkTargetVerified", "officialRacecardContentsVerified",
                     "officialStartersVerified", "officialScratchesVerified",
                     "officialGoingVerified", "officialPostTimeVerified",
                     "formalTenFactorReady", "bettingReady",
                     "existingReceiptsChanged", "existingTicketsChanged"):
            self.assertIs(data[name], False)
        self.assertEqual(data["newJrdbRequests"], 0)

    def test_homepage_featured_11r_requires_just_one_public_get(self):
        get, calls = stub({HOME: HOME_HTML})
        data = resolve_racecard_link(
            DAY, "京都", 11, today=date(2026, 11, 14), fetch_html=get)
        self.assertEqual(calls, [HOME])
        self.assertEqual(data["officialRacecardUrl"], SEED)

    def test_fail_closed_wrong_venue_date_race_or_ambiguous_urls(self):
        for text in (
            SEED_HTML.replace(TARGET1, TARGET12),
            SEED_HTML.replace(TARGET1, TARGET1.replace("0108", "0105", 1)),
            SEED_HTML.replace(TARGET1, TARGET1.replace("20261114", "20261115")),
            SEED_HTML.replace(TARGET1, TARGET1.replace("app.jra.jp", "evil.test")),
            SEED_HTML.replace('href="' + TARGET1 + '"',
                              'href="https://app.jra.jp.evil.test/' + TARGET1 + '"'),
            SEED_HTML.replace('<a href="' + TARGET1 + '">1R</a>', ''),
            SEED_HTML.replace('<a href="' + TARGET1 + '">1R</a>',
                              '<a href="' + TARGET1 + '">2R</a>'),
        ):
            with self.subTest(sample=text[:100]):
                get, _ = stub({HOME: HOME_HTML, SEED: text})
                with self.assertRaises(JraLinkResolutionError):
                    resolve_racecard_link(
                        DAY, "京都", 1, today=date(2026, 11, 14), fetch_html=get)
        for bad_day in ("2026-11-13", "2026-11-15", "2026-11-31", "20261114"):
            with self.subTest(day=bad_day):
                get, calls = stub({HOME: HOME_HTML, SEED: SEED_HTML})
                with self.assertRaises(JraLinkResolutionError):
                    resolve_racecard_link(
                        bad_day, "京都", 1, today=date(2026, 11, 14), fetch_html=get)

    def test_duplicate_homepage_race_card_anchors_require_one_unique_url(self):
        other = SEED.replace("%2F1C", "%2F77")
        home = HOME_HTML.replace(
            "</body>", f'<a href="{other}">京都11R 別のURL</a></body>')
        get, calls = stub({HOME: home})
        with self.assertRaises(JraLinkResolutionError):
            resolve_racecard_link(
                DAY, "京都", 1, today=date(2026, 11, 14), fetch_html=get)
        self.assertEqual(calls, [HOME])

    def test_owner_route_permissions_shape_and_zero_paid_requests(self):
        payload = resolve_racecard_link(
            DAY, "京都", 1, today=date(2026, 11, 14),
            fetch_html=stub({HOME: HOME_HTML, SEED: SEED_HTML})[0])
        app = create_app(SETTINGS)
        query = urlencode({"date": DAY, "track": "京都", "race": "1"})
        with patch("private_service.resolve_racecard_link",
                   return_value=payload) as resolve, \
             patch("private_service.fetch_race_program") as provider:
            resp = call(app, "/api/jra/selected-race-card-link",
                        QUERY_STRING=query)
            self.assertEqual(resp["status"], "200 OK")
            self.assertIn(b'"officialLinkFound": true', resp["body"])
            self.assertIn(b'"newJrdbRequests": 0', resp["body"])
            resolve.assert_called_once_with(DAY, "京都", 1)
            unauth = call(app, "/api/jra/selected-race-card-link",
                          QUERY_STRING=query, auth="")
            self.assertEqual(unauth["status"], "401 Unauthorized")
            for invalid in ("", query + "&track=東京", query + "&unsafe=1",
                            urlencode({"date": DAY, "track": "京都", "race": "01"})):
                with self.subTest(invalid=invalid):
                    response = call(app, "/api/jra/selected-race-card-link",
                                    QUERY_STRING=invalid)
                    self.assertEqual(response["status"], "400 Bad Request")
            provider.assert_not_called()
            self.assertEqual(resolve.call_count, 1)


if __name__ == "__main__":
    unittest.main()
