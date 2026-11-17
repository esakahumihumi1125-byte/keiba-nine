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
        self.assertTrue(report["podiumChecked"])
        self.assertTrue(report["payoutMatchesDisplayedPodium"])
        self.assertEqual(report["podiumShape"], "third_place_dead_heat")
        self.assertEqual(report["matchingTrifectaCount"], 2)
        self.assertEqual(report["matchingTrioCount"], 2)
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

    @staticmethod
    def _podium_with_payouts(placings, trifectas, trios):
        """Synthetic page, NOT a real JRA settlement or authentic source."""
        html = source()
        start = html.index("<tr><td>1</td><td>7</td></tr>")
        end = html.index("</table>\n<h2>払戻金</h2>", start)
        ranking = "".join(
            f"<tr><td>{place}</td><td>{number}</td></tr>"
            for place, number in placings)
        html = html[:start] + ranking + html[end:]
        start = html.index("<tr><th>3連複</th>")
        end = html.index("</table><h2>勝馬の紹介</h2>", start)
        def payout(kind, combos):
            return "".join(
                f"<tr><th>{kind}</th><td>{'-'.join(map(str, numbers))}</td>"
                f"<td>{(4000 + 1110*i):,}円</td><td>{i+1}番人気</td></tr>"
                for i, numbers in enumerate(combos))
        html = (html[:start] + payout("3連複", trios) +
                payout("3連単", trifectas) + html[end:])
        return html

    def test_first_place_dead_heat_two_horses_exact_trifecta_orders(self):
        # JRA official rule: 1st A/B tie, next reported placing is 3rd C.
        html = self._podium_with_payouts(
            [(1, 7), (1, 8), (3, 2)],
            [(7, 8, 2), (8, 7, 2)], [(2, 7, 8)])
        report = parse_public_result_candidate(
            html, URL, DAY, "京都", 8)
        self.assertEqual(report["podiumShape"], "first_place_dead_heat")
        self.assertEqual(report["matchingTrifectaCount"], 2)
        self.assertEqual(report["matchingTrioCount"], 1)
        self.assertTrue(report["payoutMatchesDisplayedPodium"])
        self.assertFalse(report["settlementReady"])
        self.assertFalse(report["officialJraVerified"])
        self.assertIsNone(report["officialRoiPercent"])

    def test_second_place_dead_heat_ignores_subsequent_fourth_horse(self):
        html = self._podium_with_payouts(
            [(1, 7), (2, 8), (2, 2), (4, 5)],
            [(7, 8, 2), (7, 2, 8)], [(2, 7, 8)])
        report = parse_public_result_candidate(
            html, URL, DAY, "京都", 8)
        self.assertEqual(report["podiumShape"], "second_place_dead_heat")
        self.assertEqual(report["matchingTrifectaCount"], 2)
        self.assertEqual(report["matchingTrioCount"], 1)
        self.assertFalse(report["finalityVerified"])
        self.assertFalse(report["refundsVerified"])

    def test_three_horse_first_tie_all_six_permutations(self):
        from itertools import permutations
        expected = sorted(permutations((7, 8, 2)))
        html = self._podium_with_payouts(
            [(1, 7), (1, 8), (1, 2), (4, 5)],
            expected, [(2, 7, 8)])
        report = parse_public_result_candidate(
            html, URL, DAY, "京都", 8)
        self.assertEqual(report["podiumShape"], "first_place_dead_heat")
        self.assertEqual(report["matchingTrifectaCount"], 6)
        self.assertEqual(report["matchingTrioCount"], 1)
        self.assertFalse(report["settlementReady"])

    def test_three_horse_second_tie_all_six_permutations(self):
        from itertools import permutations
        expected = [(7, a, b) for a, b in permutations((8, 2, 5), 2)]
        trios = sorted({tuple(sorted(combo)) for combo in expected})
        html = self._podium_with_payouts(
            [(1, 7), (2, 8), (2, 2), (2, 5), (5, 12)],
            expected, trios)
        report = parse_public_result_candidate(
            html, URL, DAY, "京都", 8)
        self.assertEqual(report["podiumShape"], "second_place_dead_heat")
        self.assertEqual(report["matchingTrifectaCount"], 6)
        self.assertEqual(report["matchingTrioCount"], 3)
        self.assertFalse(report["officialJraVerified"])

    def test_tied_winner_errors_never_inflate_pending_return(self):
        legitimate = self._podium_with_payouts(
            [(1, 7), (1, 8), (3, 2)],
            [(7, 8, 2), (8, 7, 2)], [(2, 7, 8)])
        cases = [
            legitimate.replace("8-7-2", "7-2-8"),
            legitimate.replace("8-7-2", "7-8-2"),
            legitimate.replace("8-7-2", "8-7-5"),
            legitimate.replace("<tr><td>3</td><td>2</td></tr>",
                               "<tr><td>2</td><td>2</td></tr>"),
            legitimate.replace("<tr><td>3</td><td>2</td></tr>", ""),
            legitimate.replace("2-7-8", "2-7-5"),
        ]
        for index, bad in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(JraPublicProbeError):
                parse_public_result_candidate(bad, URL, DAY, "京都", 8)

    def test_regular_podium_one_third_and_exact_one_payout(self):
        html = (source()
                .replace("<tr><td>3</td><td>5</td></tr>", "")
                .replace("<tr><th>3連複</th><td>5-7-8</td><td>5,510円</td><td>24番人気</td></tr>", "")
                .replace("<tr><th>3連単</th><td>7-8-5</td><td>48,920円</td><td>158番人気</td></tr>", ""))
        report = parse_public_result_candidate(html, URL, DAY, "京都", 8)
        self.assertEqual(report["podiumShape"], "single_third_place")
        self.assertEqual(report["matchingTrifectaCount"], 1)
        self.assertEqual(report["matchingTrioCount"], 1)
        self.assertFalse(report["officialJraVerified"])

    def test_results_and_payouts_must_be_exactly_the_same_horses(self):
        cases = [
            source().replace("<tr><td>3</td><td>5</td></tr>",
                             "<tr><td>4</td><td>5</td></tr>"),
            source().replace("<tr><td>3</td><td>5</td></tr>",
                             "<tr><td>3</td><td>2</td></tr>"),
            source().replace("<tr><td>2</td><td>8</td></tr>",
                             "<tr><td>1</td><td>8</td></tr>"),
            source().replace("<tr><td>1</td><td>7</td></tr>",
                             "<tr><td>1</td><td>9</td></tr>"),
            source().replace("7-8-5", "7-5-8"),
            source().replace("5-7-8", "2-5-8"),
            source().replace("<tr><td>3</td><td>5</td></tr>", ""),
            source().replace("<tr><th>着順</th><th>馬番</th></tr>", ""),
            source().replace("<tr><th>着順</th><th>馬番</th></tr>",
                             "<tr><th>着順</th><th>馬番</th></tr>"
                             "<tr><th>着順</th><th>馬番</th></tr>"),
        ]
        for n, html in enumerate(cases):
            with self.subTest(case=n), self.assertRaises(JraPublicProbeError):
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

    def test_same_jst_day_result_candidate_is_available_after_the_race(self):
        # A Saturday evening review must not wait until Sunday simply
        # because the JRA result page belongs to today's race.
        # This mock never makes a network call to JRA.
        import jra_official_result_probe as mod
        original_datetime = mod.datetime
        class SameDayClock:
            @staticmethod
            def now(tz):
                return datetime(2026, 11, 8, 9, 30, tzinfo=timezone.utc)

        class OnePageOpener:
            calls = 0
            def open(self, request, timeout):
                self.calls += 1
                self.url = request.full_url
                self.timeout = timeout
                return MockResponse(source())

        opener = OnePageOpener()
        mod.datetime = SameDayClock
        try:
            report = probe_official_result_page(
                URL, DAY, "京都", 8, opener=opener)
        finally:
            mod.datetime = original_datetime
        self.assertEqual(opener.calls, 1)
        self.assertEqual((opener.url, opener.timeout), (URL, 7))
        self.assertEqual(report["sourceReadCount"], 1)
        self.assertFalse(report["officialJraVerified"])
        self.assertFalse(report["finalityVerified"])
        self.assertFalse(report["settlementReady"])
        self.assertIsNone(report["officialRoiPercent"])

    def test_future_jst_date_cannot_trigger_a_page_read(self):
        # Same official-formatted URL, but the server is still on
        # the previous calendar day: reject before touching the opener.
        import jra_official_result_probe as mod
        original_datetime = mod.datetime
        class PreviousDayClock:
            @staticmethod
            def now(tz):
                return datetime(2026, 11, 7, 10, 0, tzinfo=timezone.utc)

        opener = Mock()
        mod.datetime = PreviousDayClock
        try:
            with self.assertRaises(JraPublicProbeError):
                probe_official_result_page(
                    URL, DAY, "京都", 8, opener=opener)
        finally:
            mod.datetime = original_datetime
        opener.open.assert_not_called()

    def test_future_or_stale_cannot_probe(self):
        for date in ("2026-11-14", "2020-11-08"):
            with self.assertRaises(JraPublicProbeError):
                probe_official_result_page(URL, date, "京都", 8, opener=Mock())


if __name__ == "__main__":
    unittest.main()
