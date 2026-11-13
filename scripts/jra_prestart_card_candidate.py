"""Owner-only, read-only JRA prestart racecard metadata *candidate*.

Fetch one explicitly supplied HTTPS JRA racecard URL. Parse just the dated race
header, scheduled off and course. The fetched HTML is NOT an authenticated
official feed, cannot certify scratches/going, and never changes predictions,
receipts, purchases or provider-derived scoring. No JRDB calls.
"""
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
import re
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

VERSION = "owner-jra-prestart-card-candidate-1"
HOSTS = frozenset(("www.jra.go.jp", "sp.jra.jp"))
VENUES = frozenset(("札幌", "函館", "福島", "新潟", "東京", "中山",
                    "中京", "京都", "阪神", "小倉"))
MAX_BYTES = 480_000
MAX_VISIBLE = 130_000
JST = timezone(timedelta(hours=9))
CNAME = re.compile(r"[A-Za-z0-9/_-]{16,90}\Z", re.ASCII)
# Both JRA official templates must be handled. The desktop format uses
# 「発走時刻：13時45分」 and 「コース：1,400メートル（芝・左）」;
# the mobile template uses 「発走13:45」 and 「コース 1400m 芝・左」.
TIME = re.compile(r"発走時刻\s*[：:]\s*([01]?\d|2[0-3])時([0-5]\d)分")
MOBILE_TIME = re.compile(r"発走\s*([01]?\d|2[0-3]):([0-5]\d)(?!\d)")
COURSE = re.compile(
    r"コース\s*[：:]\s*([1-9][0-9,]{2,5})\s*メートル\s*"
    r"[（(]\s*(芝|ダート|障害)(?:[・/][^）)]{1,18})?[）)]"
)
MOBILE_COURSE = re.compile(
    r"コース\s*([1-9][0-9]{2,4})\s*[mｍ]\s*(芝|ダート|障害)(?![一-龯])"
)
RACE_ICON_ALT = re.compile(r"(?:[1-9]|1[0-2])\s*(?:レース|R)\Z")


class JraPrestartCardError(ValueError):
    """Stable diagnostic message only; no remote URL or HTML in exceptions."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise JraPrestartCardError("Official racecard redirected")


class _Visible(HTMLParser):
    """Bounded visible text, never script or HTML attributes."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skipped = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skipped.append(tag)
        elif not self.skipped and tag == "img":
            # Desktop race number is sometimes an image alt such as
            # "8レース"; accept ONLY this very narrow marker, never
            # arbitrary HTML attributes, horse names or tracking data.
            alt = dict(attrs).get("alt")
            if isinstance(alt, str) and RACE_ICON_ALT.fullmatch(alt.strip()):
                self.parts.append(" " + alt.strip() + " ")
        elif not self.skipped and tag in ("br", "tr", "td", "th", "li",
                                          "h1", "h2", "h3", "h4", "p"):
            self.parts.append("\n")

    def handle_data(self, value):
        if not self.skipped:
            self.parts.append(value)

    def handle_endtag(self, tag):
        if self.skipped:
            if tag == self.skipped[-1]:
                self.skipped.pop()
        elif tag in ("br", "tr", "td", "th", "li", "h1", "h2", "h3", "h4", "p"):
            self.parts.append("\n")


def validate_racecard_url(url, requested_date, track, race):
    """Exact host/path, one query field, embedded date and clean identity."""
    if type(requested_date) is not str:
        raise JraPrestartCardError("Invalid requested day")
    try:
        day = date.fromisoformat(requested_date)
    except (TypeError, ValueError):
        raise JraPrestartCardError("Invalid requested day") from None
    if (day.isoformat() != requested_date or type(track) is not str
            or track not in VENUES or type(race) is not int
            or not 1 <= race <= 12 or not isinstance(url, str)
            or not 50 <= len(url) <= 250):
        raise JraPrestartCardError("Invalid official race identity")
    try:
        u = urlsplit(url)
        query = parse_qs(u.query, keep_blank_values=True)
        host, port, username, password = u.hostname, u.port, u.username, u.password
    except ValueError:
        raise JraPrestartCardError("Invalid official racecard URL") from None
    if (u.scheme != "https" or host not in HOSTS
            or port not in (None, 443) or username or password
            or u.path != "/JRADB/accessD.html" or u.fragment
            or set(query) != {"CNAME"} or len(query["CNAME"]) != 1
            or not CNAME.fullmatch(query["CNAME"][0])
            or requested_date.replace("-", "") not in query["CNAME"][0]):
        raise JraPrestartCardError("Not an allowlisted dated JRA racecard")
    return day


def parse_prestart_card_candidate(html, url, requested_date, track, race):
    """A candidate must unambiguously contain the matching dated race header.

    A visible status or entrant list alone is never proof of an independently
    authenticated JRA source, even though the URL is allowlisted.
    """
    validate_racecard_url(url, requested_date, track, race)
    if type(html) is not str or not html or len(html) > MAX_BYTES:
        raise JraPrestartCardError("Invalid JRA candidate page")
    p = _Visible()
    try:
        p.feed(html)
        p.close()
    except Exception:
        raise JraPrestartCardError("Unrecognized JRA racecard markup") from None
    visible = re.sub(r"\s+", " ", "".join(p.parts))
    if len(visible) > MAX_VISIBLE:
        raise JraPrestartCardError("JRA racecard content too large")
    y, m, d = (int(part) for part in requested_date.split("-"))
    # Header must bind YYYY-MM-DD, venue and race *before* the odds/past
    # results table; never infer race identity from site navigation alone.
    pattern = (rf"{y}\s*年\s*{m}\s*月\s*{d}\s*日"
               rf"[\s\S]{{0,100}}?{re.escape(track)}"
               rf"[\s\S]{{0,110}}?(?:\b0?{race}\s*レース|\b0?{race}\s*R\b)")
    marker = re.search(pattern, visible)
    if (not marker or marker.start() > 11000 or
            not any(label in visible[:12000]
                    for label in ("出馬表", "開催・レース選択"))):
        raise JraPrestartCardError("Dated JRA race header unavailable")
    # Limit time/course readings to the main race header, not past run rows.
    local = visible[max(0, marker.end()-130):marker.end()+650]
    times = {(int(h), int(mm)) for pattern in (TIME, MOBILE_TIME)
             for h, mm in pattern.findall(local)}
    courses = {(int(distance.replace(",", "")), surface)
               for pattern in (COURSE, MOBILE_COURSE)
               for distance, surface in pattern.findall(local)}
    if len(times) != 1 or len(courses) != 1:
        raise JraPrestartCardError("Ambiguous JRA start time or course")
    hour, minute = next(iter(times))
    distance, surface = next(iter(courses))
    if distance < 600 or distance > 5000:
        raise JraPrestartCardError("Unsupported official course distance")
    return {
        "version": VERSION, "date": requested_date, "track": track,
        "race": race, "postTimeCandidate": f"{hour:02d}:{minute:02d}",
        "courseSurfaceCandidate": surface, "distanceMCandidate": distance,
        "officialHostAllowlisted": True, "visibleRaceHeaderMatched": True,
        "pageContentsParsed": True, "independentSourceAuthenticated": False,
        "officialStartersVerified": False, "officialScratchesVerified": False,
        "officialGoingVerified": False, "officialPostTimeVerified": False,
        "formalTenFactorReady": False, "bettingReady": False,
        "changesExistingReceipts": False, "changesExistingTickets": False,
        "newJrdbProviderRequests": 0, "researchOnly": True,
        "note": ("JRA出馬表ページの発走時刻・コース候補のみ読取。"
                 "正式な出走・取消・馬場・時刻の4項目照合は未完了。"),
    }


def probe_prestart_card(url, requested_date, track, race, *,
                        now=None, opener=None):
    """One opt-in GET, no retries/redirects, no provider or secret read."""
    day = validate_racecard_url(url, requested_date, track, race)
    today = now if now is not None else datetime.now(JST).date()
    if type(today) is not date or not today - timedelta(days=1) <= day <= today + timedelta(days=7):
        raise JraPrestartCardError("Racecard day is outside prestart review window")
    request = Request(url, headers={
        "Accept": "text/html",
        "User-Agent": "ARC-RACE-Owner/1.0 (single public JRA racecard header review)",
    })
    client = opener or build_opener(_NoRedirect)
    try:
        with client.open(request, timeout=7) as response:
            if response.geturl() != url:
                raise JraPrestartCardError("JRA racecard target changed")
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                raise JraPrestartCardError("Unexpected JRA racecard content type")
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise JraPrestartCardError("JRA racecard over byte limit")
            encoding = response.headers.get_content_charset() or "utf-8"
            if encoding.lower() not in ("utf-8", "cp932", "shift_jis", "shift-jis"):
                raise JraPrestartCardError("Unsupported JRA page encoding")
            html = body.decode(encoding)
    except JraPrestartCardError:
        raise
    except Exception:
        # Never serialize remote exceptions, URLs or HTML to the owner UI.
        raise JraPrestartCardError("JRA racecard could not be read") from None
    return parse_prestart_card_candidate(
        html, url, requested_date, track, race)
