"""Synthetic single-page JRA prestart candidate: no live fetch or JRDB charges."""
import sys
import unittest
from unittest.mock import patch
from urllib.parse import urlencode
from datetime import date
from email.message import Message
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jra_prestart_card_candidate import (
    MAX_BYTES, JraPrestartCardError, parse_prestart_card_candidate,
    probe_prestart_card, validate_racecard_url,
)

DAY = "2026-11-14"
MOBILE = ("https://sp.jra.jp/JRADB/accessD.html?"
          "CNAME=sw01ddd0108202605030120261114%2F91")
DESKTOP = ("https://www.jra.go.jp/JRADB/accessD.html?"
           "CNAME=pw01dde0105202605030820261114%2FDF")
MOBILE_HTML = """<!doctype html><html lang="ja"><title>JRA</title><body>
<h1>開催・レース選択</h1>
<p>2026年11月14日（土曜） 5回京都3日</p><h2>1レース</h2>
<p>発走時刻：10時00分</p><h3>2歳未勝利</h3>
<p>コース： 1,400メートル （ダート・右）</p>
<div>枠 馬番 馬名 オッズ 馬体重</div>
<script>発走時刻：21時00分 コース：2,000メートル（芝）</script>
</body></html>"""
DESKTOP_HTML = """<!doctype html><html><body>
<h1>出馬表</h1><p>2026年11月14日（土曜） 5回東京3日
発走時刻：13時45分 8レース</p>
<h2>秋陽ジャンプステークス</h2>
<p>コース：3,110メートル（障害）</p>
</body></html>"""


class StubResponse:
    def __init__(self, body, url=MOBILE, content_type="text/html; charset=utf-8"):
        self.raw = body.encode("utf-8")
        self.url = url
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.read_sizes = []

    def geturl(self):
        return self.url

    def read(self, n):
        self.read_sizes.append(n)
        return self.raw[:n]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class StubOpener:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        return self.response


class JraPrestartCardCandidateTests(unittest.TestCase):
    def test_mobile_header_only_no_formal_verification(self):
        result = parse_prestart_card_candidate(
            MOBILE_HTML, MOBILE, DAY, "京都", 1)
        self.assertEqual(result["postTimeCandidate"], "10:00")
        self.assertEqual(result["courseSurfaceCandidate"], "ダート")
        self.assertEqual(result["distanceMCandidate"], 1400)
        self.assertTrue(result["visibleRaceHeaderMatched"])
        for flag in ("independentSourceAuthenticated", "officialStartersVerified",
                     "officialScratchesVerified", "officialGoingVerified",
                     "officialPostTimeVerified", "formalTenFactorReady",
                     "bettingReady", "changesExistingReceipts",
                     "changesExistingTickets"):
            self.assertIs(result[flag], False)
        self.assertEqual(result["newJrdbProviderRequests"], 0)
        self.assertNotIn("オッズ", repr(result))

    def test_desktop_off_time_can_precede_race_number(self):
        result = parse_prestart_card_candidate(
            DESKTOP_HTML, DESKTOP, DAY, "東京", 8)
        self.assertEqual(result["postTimeCandidate"], "13:45")
        self.assertEqual(result["courseSurfaceCandidate"], "障害")
        self.assertEqual(result["distanceMCandidate"], 3110)

    def test_actual_mobile_style_off_time_and_metres(self):
        # Current JRA iPhone pages use "コース 1400m 芝・右 外 発走16:25",
        # rather than the long desktop labels. The marker must bind to this
        # race and never use navigation or last-run rows.
        mobile = """<!doctype html><html><body><h1>出馬表</h1>
        <p>11月14日(土曜) 東京 京都 福島</p>
        <h2>2026年11月14日(土曜) 5回京都3日</h2>
        <h3>1R 2歳未勝利</h3>
        <p>コース 1400m ダート・右 発走10:00</p>
        <p>前4走 2026年11月3日 芝1800 発走16:25</p>
        </body></html>"""
        result = parse_prestart_card_candidate(
            mobile, MOBILE, DAY, "京都", 1)
        self.assertEqual(result["postTimeCandidate"], "10:00")
        self.assertEqual(result["courseSurfaceCandidate"], "ダート")
        self.assertEqual(result["distanceMCandidate"], 1400)
        self.assertFalse(result["officialPostTimeVerified"])
        self.assertFalse(result["formalTenFactorReady"])

    def test_desktop_race_number_in_strict_alt_attribute_only(self):
        desktop = """<html><body><h1>出馬表</h1>
        2026年11月14日（土曜） 5回東京3日
        発走時刻：13時45分 <img alt="8レース" src="race.png">
        <h2>秋陽ジャンプステークス</h2>
        コース：3,110メートル（障害）
        <script>発走時刻：09時99分</script>
        </body></html>"""
        out = parse_prestart_card_candidate(
            desktop, DESKTOP, DAY, "東京", 8)
        self.assertEqual(out["postTimeCandidate"], "13:45")
        self.assertEqual(out["distanceMCandidate"], 3110)
        # Arbitrary alt attributes must not be allowed to forge a race.
        alt = desktop.replace('alt="8レース"', 'alt="8レース：外部の広告"')
        with self.assertRaises(JraPrestartCardError):
            parse_prestart_card_candidate(alt, DESKTOP, DAY, "東京", 8)

    def test_ambiguous_mobile_headers_are_rejected(self):
        original = """<html><body><h1>出馬表</h1>
        <p>2026年11月14日（土曜）5回京都3日</p><h2>1R</h2>
        <p>コース 1400m ダート・右 発走10:00</p>
        </body></html>"""
        for modified in (
            original.replace("</body>", "<p>発走10:10</p></body>"),
            original.replace("</body>", "<p>コース 1200m 芝・右</p></body>"),
            original.replace("発走10:00", "時刻不詳"),
        ):
            with self.subTest(modified=modified), self.assertRaises(JraPrestartCardError):
                parse_prestart_card_candidate(modified, MOBILE, DAY, "京都", 1)

    def test_identity_and_ssrf_hosts_fail_closed(self):
        for changed in (
            "http://sp.jra.jp/JRADB/accessD.html?CNAME=sw01ddd0108202605030120261114%2F91",
            MOBILE.replace("sp.jra.jp", "sp.jra.jp.evil.test"),
            MOBILE.replace("sp.jra.jp", "127.0.0.1"),
            MOBILE.replace("/JRADB/accessD.html", "/robots.txt"),
            MOBILE+"&other=1",
            MOBILE+"#fragment",
            MOBILE.replace("20261114", "20261115"),
            MOBILE.replace("%2F91", "%2F91%0D%0AHeader:1"),
            MOBILE.replace("sp.jra.jp", "user@sp.jra.jp"),
        ):
            with self.subTest(url=changed), self.assertRaises(JraPrestartCardError):
                validate_racecard_url(changed, DAY, "京都", 1)
        for bad_day in ("2026-11-13", "20261114", "2026-11-31"):
            with self.assertRaises(JraPrestartCardError):
                validate_racecard_url(MOBILE, bad_day, "京都", 1)
        with self.assertRaises(JraPrestartCardError):
            validate_racecard_url(MOBILE, DAY, "京都", True)

    def test_wrong_day_venue_race_or_ambiguous_time_hold(self):
        for day, track, race in ((DAY, "東京", 1), (DAY, "京都", 2)):
            with self.subTest(track=track, race=race):
                with self.assertRaises(JraPrestartCardError):
                    parse_prestart_card_candidate(MOBILE_HTML, MOBILE, day, track, race)
        duplicate = MOBILE_HTML.replace(
            "</body>", "<p>発走時刻：11時00分</p></body>")
        # Duplicates in the same header window are not arbitrary choices.
        with self.assertRaises(JraPrestartCardError):
            parse_prestart_card_candidate(duplicate, MOBILE, DAY, "京都", 1)
        missing = MOBILE_HTML.replace("コース： 1,400メートル", "競走距離： 1,400メートル")
        with self.assertRaises(JraPrestartCardError):
            parse_prestart_card_candidate(missing, MOBILE, DAY, "京都", 1)

    def test_one_exact_official_get_only_no_redirect_or_html_leak(self):
        response = StubResponse(MOBILE_HTML)
        opener = StubOpener(response)
        result = probe_prestart_card(
            MOBILE, DAY, "京都", 1, now=date(2026, 11, 14), opener=opener)
        self.assertEqual(opener.calls, [(MOBILE, 7)])
        self.assertEqual(response.read_sizes, [MAX_BYTES + 1])
        self.assertTrue(result["researchOnly"])
        for response in (
            StubResponse(MOBILE_HTML, url="https://other.test/JRADB/accessD.html"),
            StubResponse(MOBILE_HTML, content_type="application/json"),
            StubResponse("A" * (MAX_BYTES + 1)),
        ):
            with self.assertRaises(JraPrestartCardError):
                probe_prestart_card(MOBILE, DAY, "京都", 1,
                                    now=date(2026, 11, 14),
                                    opener=StubOpener(response))
        with self.assertRaises(JraPrestartCardError):
            probe_prestart_card(MOBILE, DAY, "京都", 1,
                                now=date(2026, 12, 1), opener=opener)
        self.assertEqual(len(opener.calls), 1)

    def test_owner_route_is_read_only_single_official_page(self):
        from private_service import create_app
        from test_private_service import SETTINGS, call
        app = create_app(SETTINGS)
        query = urlencode({"date": DAY, "track": "京都", "race": "1",
                           "url": MOBILE})
        candidate = parse_prestart_card_candidate(
            MOBILE_HTML, MOBILE, DAY, "京都", 1)
        with patch("private_service.probe_prestart_card",
                   return_value=candidate) as probe, \
             patch("private_service.fetch_race_program") as jrdb:
            result = call(app, "/api/jra/prestart-card-candidate",
                          QUERY_STRING=query)
            self.assertEqual(result["status"], "200 OK")
            self.assertIn(b'"officialStartersVerified": false', result["body"])
            self.assertIn(b'"postTimeCandidate": "10:00"', result["body"])
            probe.assert_called_once_with(MOBILE, DAY, "京都", 1)
            jrdb.assert_not_called()
            unauth = call(app, "/api/jra/prestart-card-candidate",
                          QUERY_STRING=query, auth="")
            self.assertEqual(unauth["status"], "401 Unauthorized")
            blocked = call(app, "/api/jra/prestart-card-candidate",
                           QUERY_STRING=query, HTTP_X_KEIBA_REQUEST="")
            self.assertEqual(blocked["status"], "403 Forbidden")
            self.assertEqual(probe.call_count, 1)
            for malformed in (
                "", "date=" + DAY,
                query + "&race=2",
                query + "&token=unsafe",
                urlencode({"date": DAY, "track": "京都", "race": "1",
                           "url": MOBILE.replace("sp.jra.jp", "evil.test")}),
                urlencode({"date": DAY, "track": "京都", "race": "01",
                           "url": MOBILE}),
            ):
                with self.subTest(query=malformed):
                    response = call(app, "/api/jra/prestart-card-candidate",
                                    QUERY_STRING=malformed)
                    self.assertEqual(response["status"], "400 Bad Request")
            self.assertEqual(probe.call_count, 1)
            jrdb.assert_not_called()

if __name__ == "__main__":
    unittest.main()
