"""Synthetic HTML and mock HTTP: no real JRA requests or licensed data."""
import copy
import sys
import unittest
from datetime import datetime, timezone
from email.message import Message
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jra_official_result_probe import (
    JraPublicProbeError, parse_public_result_candidate, probe_official_result_page
)

DAY = "2026-11-08"
URL = ("https://www.jra.go.jp/JRADB/accessS.html?"
       "CNAME=pw01sde0108202605020820261108%2FA0")


def source():
    return """<!doctype html><html lang="ja"><head><title>レース結果</title>
<style>3連単 9-8-7 999999円</style></head><body>
<nav><p>レース結果／払戻金</p></nav>
<header><h1>レース結果</h1>
<div>2026年11月8日（日曜） 5回京都2日 8レース</div></header>
<main><h2>レース結果</h2><table><tr><th>着順</th><th>馬番</th></tr>
<tr><td>1</td><td>7</td></tr><tr><td>2</td><td>8</td></tr>
<tr><td>3</td><td>2</td></tr><tr><td>3</td><td>5</td></tr></table>
<h2>払戻金</h2>
<table><tr><th>単勝</th><td>7</td><td>2,980円</td></tr>
<tr><th>3連複</th><td>2-7-8</td><td>2,320円</td><td>13番人気</td></tr>
<tr><th>3連複</th><td>5-7-8</td><td>5,510円</td><td>24番人気</td></tr>
<tr><th>3連単</th><td>7-8-2</td><td>26,050円</td><td>109番人気</td></tr>
<tr><th>3連単</th><td>7-8-5</td><td>48,920円</td><td>158番人気</td></tr>
</table><h2>勝馬の紹介</h2><p>ここから別見出し</p>
</main></body></html>"""


class MockResponse:
    def __init__(self, content, url=URL, content_type="text/html; charset=utf-8"):
        self.content = content.encode("utf-8")
        self.url = url
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return None

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.content[:limit]


class PublicResultProbeTests(unittest.TestCase):
    def test_public_official_shape_has_multiple_winners_but_is_unverified(self):
        src = source()
        report = parse_public_result_candidate(src, URL, DAY, "京都", 8)
        self.assertEqual(report["trifectaCandidates"], [
            {"ticket": [7, 8, 2], "payoutYen": 26050},
            {"ticket": [7, 8, 5], "payoutYen": 48920},
        ])
        self.assertEqual(report["trioCandidates"], [
            {"ticket": [2, 7, 8], "payoutYen": 2320},
            {"ticket": [5, 7, 8], "payoutYen": 5510}
        ])
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["sourceAuthenticityAttested"])
        self.assertFalse(report["finalityVerified"])
        self.assertFalse(report["refundsVerified"])
        self.assertFalse(report["settlementReady"])
        self.assertIsNone(report["officialRoiPercent"])
        self.assertEqual(report["sourceReadCount"], 0)
        for marker in ("API_KEY", "horseName", "password", "<html",
                       "3連単 9-8-7"):
            self.assertNotIn(marker, repr(report))
        self.assertEqual(src, source())

    def test_discrepancy_changed_page_and_refunds_fail_closed(self):
        cases = [
            source().replace("8レース", "9レース"),
            source().replace("5回京都2日", "5回東京2日"),
            source().replace("2026年11月8日", "2026年11月7日"),
            source().replace("26,050円", ""),
            source().replace("7-8-2", "7-8-5"),
            source().replace("7-8-2", "7-7-2"),
            source().replace("3連複", "馬連"),
            source().replace("<h2>払戻金</h2>", "<h2>払い戻し</h2>"),
            source().replace("<h2>勝馬の紹介</h2>", "<div>返還があります</div><h2>勝馬の紹介</h2>"),
            source().replace("26,050円", "10000000000円"),
            source().replace("26,050円", "26,050円と30,000円"),
        ]
        for n, html in enumerate(cases):
            with self.subTest(n=n), self.assertRaises(JraPublicProbeError):
                parse_public_result_candidate(html, URL, DAY, "京都", 8)

    def test_url_not_trusted_just_because_it_contains_jra_letters(self):
        bad_urls = [
            URL.replace("www.jra.go.jp", "www.jra.go.jp.evil.test"),
            URL.replace("https:", "http:"),
            URL.replace("/JRADB/accessS.html", "/another/path"),
            URL.replace("20261108", "20261109"),
            URL.replace("CNAME=", "OTHER="),
            URL.replace("www.jra.go.jp", "www.jra.go.jp:8080"),
            URL + "#frag",
        ]
        for u in bad_urls:
            with self.subTest(url=u), self.assertRaises(JraPublicProbeError):
                parse_public_result_candidate(source(), u, DAY, "京都", 8)

    def test_one_explicit_read_no_hidden_network_or_certification(self):
        class Opener:
            def __init__(self):
                self.calls = []
            def open(self, request, timeout):
                self.calls.append((request.full_url, timeout))
                return MockResponse(source())
        opener = Opener()
        # The live-probe date is always constrained to a recent past day. We
        # test this using a clock patch; never call a production host.
        import jra_official_result_probe as mod
        original_datetime = mod.datetime
        class FakeDateTime:
            @staticmethod
            def now(tz):
                return datetime(2026, 11, 10, 6, 0, tzinfo=timezone.utc)
        mod.datetime = FakeDateTime
        try:
            report = probe_official_result_page(URL, DAY, "京都", 8, opener=opener)
        finally:
            mod.datetime = original_datetime
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(opener.calls[0], (URL, 7))
        self.assertEqual(report["sourceReadCount"], 1)
        self.assertFalse(report["officialJraVerified"])
        self.assertIsNone(report["officialRoiPercent"])

    def test_unexpected_redirect_or_content_type_cannot_be_accepted(self):
        class Opener:
            def __init__(self, response):
                self.response = response
            def open(self, *_args, **_kwargs):
                return self.response
        import jra_official_result_probe as mod
        original_datetime = mod.datetime
        class FakeDateTime:
            @staticmethod
            def now(tz):
                return datetime(2026, 11, 10, 6, 0, tzinfo=timezone.utc)
        mod.datetime = FakeDateTime
        try:
            for response in (
                MockResponse(source(), URL.replace("www.jra.go.jp", "evil.test")),
                MockResponse(source(), URL, "application/json"),
                MockResponse("bad layout")
            ):
                with self.assertRaises(JraPublicProbeError):
                    probe_official_result_page(
                        URL, DAY, "京都", 8, opener=Opener(response))
        finally:
            mod.datetime = original_datetime

    def test_future_or_stale_cannot_probe(self):
        for date in ("2026-11-14", "2020-11-08"):
            with self.assertRaises(JraPublicProbeError):
                probe_official_result_page(URL, date, "京都", 8, opener=Mock())


if __name__ == "__main__":
    unittest.main()
