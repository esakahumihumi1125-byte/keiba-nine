"""Discover official JRA per-course racecard PDF LINKS, not racecard contents.

The only network target is the fixed official index. This module neither
downloads PDFs nor claims their contents were parsed/verified, and is not
a provider API or an alternative to licensed feed agreements.
"""
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
from zoneinfo import ZoneInfo
import re

INDEX_URL = "https://www.jra.go.jp/keiba/rpdf/"
INDEX_HOSTS = {"www.jra.go.jp", "jra.jp"}
COURSES = ("札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉")
MAX_BYTES = 900_000
MAX_LINKS = 10


class JRAIndexError(ValueError):
    pass


def _safe_url(raw, base=INDEX_URL, pdf=False):
    if not isinstance(raw, str) or len(raw) > 350:
        raise JRAIndexError("invalid URL")
    url = urljoin(base, raw)
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname not in INDEX_HOSTS or p.port not in (None, 443)
            or p.username or p.password or p.query or p.fragment
            or not p.path.startswith("/keiba/rpdf/")
            or (pdf and not p.path.lower().endswith(".pdf"))):
        raise JRAIndexError("Non-official or ambiguous document link")
    return url


class _OfficialLinksHTML(HTMLParser):
    """Read the date headings + venue-labelled PDF anchors, no PDF contents."""
    def __init__(self, day):
        super().__init__(convert_charrefs=True)
        self.day = day
        self.current_date = None
        self.heading = False
        self.anchor_href = None
        self.parts = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3", "h4"):
            self.heading = tag
            self.parts = []
        elif tag == "a":
            self.anchor_href = dict(attrs).get("href")
            self.parts = []

    def handle_data(self, text):
        if self.heading or self.anchor_href is not None:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if self.heading == tag:
            title = re.sub(r"\s+", "", "".join(self.parts))
            m = re.match(r"^(\d{1,2})月(\d{1,2})日", title)
            self.current_date = ((int(m.group(1)), int(m.group(2))) if m else None)
            self.heading = False
            self.parts = []
        elif tag == "a" and self.anchor_href is not None:
            label = re.sub(r"\s+", "", "".join(self.parts))
            if self.current_date == (self.day.month, self.day.day):
                match = re.match(r"^\d+回(" + "|".join(COURSES) + r")競馬場\d+日.*PDF", label)
                if match:
                    try:
                        pdf_url = _safe_url(self.anchor_href, pdf=True)
                    except (JRAIndexError, ValueError):
                        pass
                    else:
                        self.links.append({"track": match.group(1), "url": pdf_url})
            self.anchor_href = None
            self.parts = []


def parse_official_pdf_links(html, requested_date):
    """Return 0-10 safe official PDF links for a yyyy-mm-dd date.

    This is *only* a dated link index discovery. No JRA runner validation.
    """
    try:
        day = date.fromisoformat(requested_date)
    except (ValueError, TypeError):
        raise JRAIndexError("Invalid day")
    if not isinstance(html, str) or not html or len(html) > MAX_BYTES:
        raise JRAIndexError("Invalid index content")
    parser = _OfficialLinksHTML(day)
    parser.feed(html)
    if len(parser.links) > MAX_LINKS:
        raise JRAIndexError("Ambiguous official list")
    seen = set()
    for item in parser.links:
        if item["track"] in seen:
            raise JRAIndexError("Duplicate course entry in official page")
        seen.add(item["track"])
    return sorted(parser.links, key=lambda v: COURSES.index(v["track"]))


class _AllowOfficialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _safe_url(newurl, pdf=False)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def discover_official_pdf_links(requested_date, now=None, opener=None):
    """One explicit GET to official HTML index; fail closed on network errors."""
    try:
        day = date.fromisoformat(requested_date)
    except (ValueError, TypeError):
        raise JRAIndexError("Date must be YYYY-MM-DD")
    if requested_date != day.isoformat():
        raise JRAIndexError("Invalid date format")
    today = now or datetime.now(ZoneInfo("Asia/Tokyo")).date()
    if not isinstance(today, date) or day < today - timedelta(days=56) or day > today + timedelta(days=14):
        raise JRAIndexError("Date outside the official listing range")
    req = Request(INDEX_URL, headers={
        "User-Agent": "KEIBA-NINE-Owner/1.0 (JRA PDF index link only; no PDF download)",
        "Accept": "text/html",
    })
    reader = opener or build_opener(_AllowOfficialRedirect)
    try:
        with reader.open(req, timeout=7) as resp:
            final_url = _safe_url(resp.geturl(), pdf=False)
            if final_url not in (INDEX_URL, INDEX_URL + "index.html"):
                raise JRAIndexError("Unexpected official page URL")
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                raise JRAIndexError("Not an HTML index")
            data = resp.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise JRAIndexError("Index page too large")
            encoding = resp.headers.get_content_charset() or "utf-8"
            try:
                html = data.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                raise JRAIndexError("Unsupported official page encoding")
    except JRAIndexError:
        raise
    except Exception as exc:
        raise JRAIndexError("Official index could not be reached") from exc
    links = parse_official_pdf_links(html, requested_date)
    return {
        "version": "jra-official-pdf-link-discovery-1",
        "date": requested_date,
        "indexUrl": INDEX_URL,
        "links": links,
        "linkFound": bool(links),
        "pdfContentsRead": False,
        "officialRunnerNumbersVerified": False,
        "entryChangeVerified": False,
        "predictionReady": False,
        "bettingReady": False,
    }
