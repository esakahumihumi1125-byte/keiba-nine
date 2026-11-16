"""Read-only, opt-in JRA advance programme (NOT an official final racecard).

One bounded GET to a constructed, allowlisted JRA calendar page. The page
explicitly says announced schedules can change, including time, distance,
race number and cancellation. It NEVER certifies actual starters, scratches,
current going, official off, betting or results. No JRDB reads or storage.
"""
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit
import re

VERSION = "owner-jra-advance-programme-reference-1"
JST = timezone(timedelta(hours=9))
VENUES = frozenset(("札幌", "函館", "福島", "新潟", "東京", "中山",
                    "中京", "京都", "阪神", "小倉"))
VENUE_LABEL = re.compile(
    r"(?:[1-9]|1[0-2])回\s*(札幌|函館|福島|新潟|東京|中山|"
    r"中京|京都|阪神|小倉)\s*(?:[1-9]|1[0-2])日"
)
RACE_ROW = re.compile(
    r"(?<![0-9])([1-9]|1[0-2])\s*レース\s*(.*?)"
    r"(?<![0-9])([01]?[0-9]|2[0-3])\s*時\s*([0-5][0-9])\s*分",
    re.DOTALL
)
COURSE = re.compile(
    r"([1-9][0-9,]{2,5})\s*[（(]\s*(芝(?:・外)?|ダ|ダート)\s*[）)]"
)
MAX_HTML_BYTES = 750000
MAX_TEXT = 250000


class AdvanceProgrammeError(ValueError):
    """Only fixed diagnostics; no remote HTML, provider data or URLs."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AdvanceProgrammeError("JRA advance programme redirected")


class _Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = []
        self.length = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skip.append(tag)
        elif not self.skip and tag in (
                "tr", "td", "th", "br", "p", "h1", "h2", "h3",
                "h4", "table", "div", "section"):
            self.parts.append(" ")

    def handle_data(self, data):
        if not self.skip:
            self.length += len(data)
            if self.length > MAX_TEXT:
                raise AdvanceProgrammeError("JRA advance programme too large")
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.skip:
            if tag == self.skip[-1]:
                self.skip.pop()
        elif tag in ("tr", "td", "th", "br", "p", "h1",
                     "h2", "h3", "h4", "table", "div", "section"):
            self.parts.append(" ")


def calendar_url(day):
    if type(day) is not str:
        raise AdvanceProgrammeError("Invalid JRA calendar date")
    try:
        value = date.fromisoformat(day)
    except ValueError:
        raise AdvanceProgrammeError("Invalid JRA calendar date") from None
    if value.isoformat() != day or not 2020 <= value.year <= 2035:
        raise AdvanceProgrammeError("Invalid JRA calendar date")
    return (f"https://www.jra.go.jp/keiba/calendar{value.year}/"
            f"{value.year}/{value:%m}/{value:%m%d}.html")


def parse_advance_programme(html, day):
    """Parse only a complete 12R-per-venue *announced* schedule.

    A partial, duplicated, contradictory or redesigned calendar FAILS shut.
    Race names and page contents are discarded; return schedule metadata only.
    """
    calendar_url(day)
    if type(html) is not str or not html or len(html) > MAX_HTML_BYTES:
        raise AdvanceProgrammeError("Invalid JRA advance programme page")
    p = _Visible()
    try:
        p.feed(html)
        p.close()
    except AdvanceProgrammeError:
        raise
    except Exception:
        raise AdvanceProgrammeError("JRA advance programme markup unsupported") from None
    visible = " ".join("".join(p.parts).split())
    value = date.fromisoformat(day)
    title = re.search(
        rf"{value.year}\s*年\s*{value.month}\s*月\s*{value.day}\s*日"
        r"[\s\S]{0,45}?競馬番組", visible
    )
    # This is NOT the latest entry list. Require the publisher's notice
    # about changes instead of silently treating a plain racecard as a calendar.
    if (not title or title.start() > 20000
            or "このページの情報は、事前に発表した" not in visible
            or "変更" not in visible):
        raise AdvanceProgrammeError("JRA advance programme identity missing")
    tail = visible[title.end():]
    sections = list(VENUE_LABEL.finditer(tail))
    if not 2 <= len(sections) <= 4:
        raise AdvanceProgrammeError("JRA scheduled venues incomplete")
    output, seen_venues = [], set()
    for i, section in enumerate(sections):
        track = section.group(1)
        if track not in VENUES or track in seen_venues:
            raise AdvanceProgrammeError("Duplicate JRA scheduled venue")
        seen_venues.add(track)
        block = tail[section.end():sections[i + 1].start() if
                     i + 1 < len(sections) else len(tail)]
        found = list(RACE_ROW.finditer(block))
        if len(found) != 12 or [
                int(m.group(1)) for m in found] != list(range(1, 13)):
            raise AdvanceProgrammeError("JRA scheduled race rows incomplete")
        for item in found:
            number = int(item.group(1))
            condition = item.group(2)
            if not 3 <= len(condition) <= 240:
                raise AdvanceProgrammeError("JRA scheduled conditions ambiguous")
            courses = {(int(dist.replace(",", "")), surface)
                       for dist, surface in COURSE.findall(condition)}
            if len(courses) != 1:
                raise AdvanceProgrammeError("JRA scheduled course ambiguous")
            distance, surface_code = next(iter(courses))
            if not 600 <= distance <= 5000:
                raise AdvanceProgrammeError("Unsupported JRA scheduled distance")
            # Calendar labels a steeplechase as "(芝)", but JRDB may use
            # 障害 as its race type. Do not fabricate a surface comparison.
            surface = (None if "障害" in condition else
                       "ダート" if surface_code in ("ダ", "ダート") else "芝")
            post = f"{int(item.group(3)):02d}:{int(item.group(4)):02d}"
            output.append({
                "track": track, "race": number, "postTime": post,
                "distanceM": distance, "surface": surface,
            })
    return {
        "version": VERSION, "date": day,
        "referenceKind": "advance_schedule_not_final_racecard",
        "raceCount": len(output), "venueCount": len(seen_venues),
        "races": output,
        "officialFinalCardVerified": False,
        "officialStartersVerified": False,
        "officialScratchesVerified": False,
        "officialGoingVerified": False,
        "officialPostTimeVerified": False,
        "predictionReady": False, "bettingReady": False,
        "newJrdbRequests": 0, "existingTicketsChanged": False,
        "existingReceiptsChanged": False,
        "note": ("JRA公表の事前競馬番組にある予定発走時刻・予定距離・"
                 "芝ダートのみ。変更や中止を含む最新の出馬表ではなく、"
                 "出走/取消/馬場/確定発走時刻の正式照合ではありません。"),
    }


def probe_advance_programme(day, *, today=None, fetch_html=None):
    """One opt-in calendar GET; no automatic retries, redirects or paid calls."""
    url = calendar_url(day)
    target = date.fromisoformat(day)
    now = today if today is not None else datetime.now(JST).date()
    if (type(now) is not date
            or not now - timedelta(days=60) <= target <= now + timedelta(days=45)):
        raise AdvanceProgrammeError("JRA calendar date outside review window")
    if fetch_html is not None:
        html = fetch_html(url)
    else:
        req = Request(url, headers={
            "Accept": "text/html",
            "User-Agent": "ARC-RACE-Owner/1.0 (opt-in advance schedule reference)",
        })
        try:
            with build_opener(_NoRedirect).open(req, timeout=8) as response:
                if response.geturl() != url:
                    raise AdvanceProgrammeError("JRA calendar redirected")
                if "text/html" not in response.headers.get("Content-Type", "").lower():
                    raise AdvanceProgrammeError("JRA calendar not HTML")
                raw = response.read(MAX_HTML_BYTES + 1)
                if len(raw) > MAX_HTML_BYTES:
                    raise AdvanceProgrammeError("JRA calendar too large")
                encoding = response.headers.get_content_charset() or "utf-8"
                if encoding.lower() not in (
                        "utf-8", "cp932", "shift_jis", "shift-jis"):
                    raise AdvanceProgrammeError("Unsupported JRA calendar encoding")
                html = raw.decode(encoding)
        except AdvanceProgrammeError:
            raise
        except Exception:
            raise AdvanceProgrammeError("JRA calendar could not be read") from None
    return parse_advance_programme(html, day)
