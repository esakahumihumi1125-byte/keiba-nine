"""JRA PDF link discovery uses one whitelisted official HTML index, never PDF data."""
import io
import sys
import unittest
from datetime import date
from email.message import Message
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jra_official_pdf_discovery import (
    INDEX_URL, JRAIndexError, discover_official_pdf_links, parse_official_pdf_links
)
from private_service import create_app
from test_private_service import SETTINGS, call

OFFICIAL_LIKE_HTML = """<!doctype html><html lang='ja'>
<h3>11月7日（土曜）</h3><ul>
<li><a href='/keiba/rpdf/2026/some-tokyo-card.pdf'>5回 東京競馬場1日（PDF：2.1MB）</a></li>
<li><a href='https://jra.jp/keiba/rpdf/2026/some-kyoto-card.pdf'>5回 京都競馬場1日（PDF：2.0MB）</a></li>
<li><a href='/keiba/rpdf/2026/some-fukushima-card.pdf'>3回 福島競馬場1日（PDF：2.0MB）</a></li>
<li><a href='/keiba/rpdf/2026/racing-programme.pdf'>カラーページ（PDF：2.1MB）</a></li></ul>
<h3>11月8日（日曜）</h3><ul>
<li><a href='/keiba/rpdf/2026/sunday-tokyo.pdf'>5回 東京競馬場2日（PDF：2.0MB）</a></li></ul>
</html>"""


class StubResponse:
    def __init__(self, body, url=INDEX_URL, ctype="text/html; charset=utf-8"):
        self.content = body.encode()
        self.url = url
        self.headers = Message()
        self.headers["Content-Type"] = ctype
        self.read_sizes = []
    def geturl(self):
        return self.url
    def read(self, size):
        self.read_sizes.append(size)
        return self.content[:size]
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, trace):
        return False


class StubOpener:
    def __init__(self, response):
        self.response = response
        self.calls = []
    def open(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        return self.response


class OfficialPdfDiscoveryTests(unittest.TestCase):
    def test_only_racecard_pdf_links_for_exact_day(self):
        out = parse_official_pdf_links(OFFICIAL_LIKE_HTML, "2026-11-07")
        self.assertEqual([v["track"] for v in out], ["福島", "東京", "京都"])
        self.assertTrue(all(v["url"].startswith(("https://jra.jp/keiba/rpdf/",
                                                    "https://www.jra.go.jp/keiba/rpdf/"))
                            for v in out))
        self.assertEqual(len(parse_official_pdf_links(OFFICIAL_LIKE_HTML, "2026-11-08")), 1)
        self.assertEqual(parse_official_pdf_links(OFFICIAL_LIKE_HTML, "2026-11-06"), [])

    def test_url_host_path_query_validation_and_duplicates(self):
        for path in (
            "https://thirdparty.test/keiba/rpdf/2026/evil.pdf",
            "https://jra.jp.evil.test/keiba/rpdf/evil.pdf",
            "http://jra.jp/keiba/rpdf/2026/evil.pdf",
            "javascript:alert(1)",
            "//private.local/keiba/rpdf/evil.pdf",
            "https://jra.jp/keiba/rpdf/2026/evil.pdf?download=true",
            "https://jra.jp/not-official/evil.pdf",
            "https://jra.jp/keiba/rpdf/2026/evil.html",
        ):
            changed = OFFICIAL_LIKE_HTML.replace(
                "/keiba/rpdf/2026/some-tokyo-card.pdf", path)
            with self.subTest(path=path):
                self.assertEqual(len(parse_official_pdf_links(changed, "2026-11-07")), 2)
        invalid = OFFICIAL_LIKE_HTML.replace(
            "<h3>11月8日（日曜）</h3>", "<h3>11月7日（土曜）</h3>")
        with self.assertRaisesRegex(JRAIndexError, "Duplicate course"):
            parse_official_pdf_links(invalid, "2026-11-07")

    def test_only_one_official_index_request_and_never_pdf_download(self):
        response = StubResponse(OFFICIAL_LIKE_HTML)
        opener = StubOpener(response)
        out = discover_official_pdf_links("2026-11-07",
                                        now=date(2026, 11, 5), opener=opener)
        self.assertEqual(opener.calls, [(INDEX_URL, 7)])
        self.assertEqual(response.read_sizes, [900001])
        self.assertEqual(out["date"], "2026-11-07")
        self.assertEqual(len(out["links"]), 3)
        for flag in ("pdfContentsRead", "officialRunnerNumbersVerified",
                     "entryChangeVerified", "predictionReady", "bettingReady"):
            self.assertIs(out[flag], False)

    def test_fail_closed_for_dates_content_type_and_redirects(self):
        opener = StubOpener(StubResponse(OFFICIAL_LIKE_HTML))
        for day in ("2026-09-01", "2026-12-02", "2026-11-31", "20261107"):
            with self.subTest(day=day), self.assertRaises(JRAIndexError):
                discover_official_pdf_links(day, now=date(2026, 11, 5), opener=opener)
        self.assertEqual(opener.calls, [])
        for response in (
            StubResponse(OFFICIAL_LIKE_HTML, url="https://wrong.test/keiba/rpdf/"),
            StubResponse(OFFICIAL_LIKE_HTML, url="https://jra.jp/keiba/rpdf/other.html"),
            StubResponse(OFFICIAL_LIKE_HTML, ctype="application/pdf"),
        ):
            with self.assertRaises(JRAIndexError):
                discover_official_pdf_links("2026-11-07",
                                            now=date(2026, 11, 5),
                                            opener=StubOpener(response))

    def test_server_endpoint_is_owner_only_and_does_not_call_jrdb(self):
        app = create_app(SETTINGS)
        with patch("private_service.discover_official_pdf_links") as discover, \
             patch("private_service.fetch_race_program") as paid:
            discover.return_value = discover_official_pdf_links(
                "2026-11-07", now=date(2026, 11, 5),
                opener=StubOpener(StubResponse(OFFICIAL_LIKE_HTML)))
            result = call(app, "/api/jra/official-pdf-links",
                          QUERY_STRING="date=2026-11-07")
            self.assertEqual(result["status"], "200 OK")
            self.assertIn(b'"officialRunnerNumbersVerified": false', result["body"])
            discover.assert_called_once_with("2026-11-07")
            paid.assert_not_called()
            unauth = call(app, "/api/jra/official-pdf-links",
                          QUERY_STRING="date=2026-11-07", auth="")
            self.assertEqual(unauth["status"], "401 Unauthorized")
            self.assertEqual(discover.call_count, 1)
            forbidden = call(app, "/api/jra/official-pdf-links",
                             QUERY_STRING="date=2026-11-07",
                             HTTP_X_KEIBA_REQUEST="")
            self.assertEqual(forbidden["status"], "403 Forbidden")
        for bad in ("", "date=2026-11-07&date=2026-11-08", "date=2026-11-07&url=evil"):
            result = call(app, "/api/jra/official-pdf-links", QUERY_STRING=bad)
            self.assertEqual(result["status"], "400 Bad Request")

    def test_owner_page_assets_are_guarded(self):
        app = create_app(SETTINGS)
        for path in ("/jra-official-pdf.js", "/jrdb-mail-local"):
            output = call(app, path)
            self.assertEqual(output["status"], "200 OK")
            denied = call(app, path, auth="")
            self.assertEqual(denied["status"],
                             "303 See Other" if path=="/jrdb-mail-local"
                             else "401 Unauthorized")
        body = call(app, "/jrdb-mail-local")["body"]
        self.assertIn(b'id="officialPdfSection"', body)
        self.assertIn(b'/jra-official-pdf.js', body)
        self.assertIn(b'id="manualNumberSection"', body)
        self.assertIn("text/javascript",
                      call(app, "/jra-official-pdf.js")["headers"]["Content-Type"])


if __name__ == "__main__":
    unittest.main()
