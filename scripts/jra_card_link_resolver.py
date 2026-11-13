"""Owner-only opt-in JRA racecard link resolver, never a score or verification.

One exact, fixed JRA homepage GET; then one seed racecard GET if and only if
a current meeting's anchor is discovered. Extract just the target racecard
URL from first-party links (not the horse table, data or odds). Never guess
checksum-bearing CNAMEs. No JRDB API, secrets, persistence, or auto-poll.
"""
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import Request, build_opener

from jra_prestart_card_candidate import (
    HOSTS, JST, MAX_BYTES, _NoRedirect, JraPrestartCardError,
    validate_racecard_url, parse_prestart_card_candidate,
)

VERSION = "owner-jra-race-link-resolver-1"
HOME = "https://www.jra.go.jp/"
VENUE_CODES = {
    "札幌": "01", "函館": "02", "福島": "03", "新潟": "04",
    "東京": "05", "中山": "06", "中京": "07", "京都": "08",
    "阪神": "09", "小倉": "10",
}


class JraLinkResolutionError(ValueError):
    """Only fixed public diagnostics, no remote HTML or source URLs."""


class _Anchors(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.href = None
        self.text = []
        self.suppressed = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.suppressed.append(tag)
        if tag == "a" and not self.suppressed and self.href is None:
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None and not self.suppressed:
            self.text.append(data[:200])

    def handle_endtag(self, tag):
        if self.suppressed:
            if tag == self.suppressed[-1]:
                self.suppressed.pop()
        elif tag == "a" and self.href is not None:
            label = " ".join(" ".join(self.text).split())[:150]
            if len(self.links) < 4000:
                self.links.append((label, self.href))
            self.href = None
            self.text = []


def _links(html):
    if not isinstance(html, str) or len(html) > 1_000_000:
        raise JraLinkResolutionError("JRA public index is too large")
    p = _Anchors()
    try:
        p.feed(html)
        p.close()
    except Exception:
        raise JraLinkResolutionError("JRA public index markup unsupported") from None
    return p.links


def _validated_card_link(href, origin, day, track, race):
    """Verify encoded day, venue and race: NEVER manufacture JRA CNAME CRC."""
    if not isinstance(href, str) or len(href) > 280:
        return None
    url = urljoin(origin, href)
    if len(url) > 250:
        return None
    try:
        validate_racecard_url(url, day, track, race)
        u = urlsplit(url)
        token = parse_qs(u.query, keep_blank_values=True)["CNAME"][0]
        code = VENUE_CODES[track]
        target_day = day.replace("-", "")
        # The 2026 mobile/desktop D/E racecard token has a race coordinate
        # and integrity suffix. Reject other formats instead of guessing.
        prefix = ("sw01dde01", "pw01dde01")
        if not token.startswith(prefix):
            return None
        stem = token[9:]
        # venue (2), meeting (8), race (2), date (8), slash, CRC(2)
        if (len(stem) != 23 or stem[:2] != code or
                stem[2:6] != day[:4] or
                not stem[6:10].isdigit() or
                stem[10:12] != f"{race:02d}" or
                stem[12:20] != target_day or
                stem[20] != "/" or
                len(stem[21:]) != 2 or
                any(char not in "0123456789ABCDEFabcdef"
                    for char in stem[21:])):
            return None
    except (JraPrestartCardError, ValueError, KeyError):
        return None
    return url


def _fetch_html(url, *, opener=None):
    u = urlsplit(url)
    if (u.scheme != "https" or u.hostname not in HOSTS or
            u.username or u.password or u.port not in (None, 443) or
            (url != HOME and u.path != "/JRADB/accessD.html")):
        raise JraLinkResolutionError("Unexpected official index target")
    client = opener or build_opener(_NoRedirect)
    req = Request(url, headers={
        "Accept": "text/html",
        "User-Agent": "ARC-RACE-Owner/1.0 (explicit public race link review)",
    })
    try:
        with client.open(req, timeout=8) as response:
            if response.geturl() != url:
                raise JraLinkResolutionError("JRA redirected")
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                raise JraLinkResolutionError("JRA index is not HTML")
            raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise JraLinkResolutionError("JRA public index too large")
            encoding = response.headers.get_content_charset() or "utf-8"
            if encoding.lower() not in ("utf-8", "shift_jis", "shift-jis", "cp932"):
                raise JraLinkResolutionError("JRA index encoding unsupported")
            return raw.decode(encoding)
    except JraLinkResolutionError:
        raise
    except Exception:
        raise JraLinkResolutionError("JRA public index unavailable") from None


def resolve_racecard_link(day, track, race, *, today=None, fetch_html=None):
    """Owner gesture: exactly two public JRA requests when successful.

    Does not fetch/grade the selected race, and does not authorize
    post-time picks or claim official JRA data verification.
    """
    if not isinstance(day, str) or track not in VENUE_CODES or type(race) is not int:
        raise JraLinkResolutionError("Invalid target race")
    now = today if today is not None else datetime.now(JST).date()
    try:
        requested = date.fromisoformat(day)
        if (type(now) is not date or requested.isoformat() != day or
                not 1 <= race <= 12 or
                not now - timedelta(days=1) <= requested <= now + timedelta(days=7)):
            raise ValueError()
    except (TypeError, ValueError):
        raise JraLinkResolutionError("Invalid target race") from None
    get = fetch_html or _fetch_html
    index = get(HOME)
    candidates = []
    # JRA links notable same-day races from its homepage. The label
    # provides the venue, while encoded CNAME provides its real coordinate.
    for label, href in _links(index):
        if not label.startswith(track + "11R"):
            continue
        candidate = _validated_card_link(href, HOME, day, track, 11)
        if candidate and candidate not in candidates:
            candidates.append(candidate)
    if len(candidates) != 1:
        raise JraLinkResolutionError("One dated JRA venue link not found")
    seed = candidates[0]
    if race == 11:
        target = seed
    else:
        page = get(seed)
        # Do NOT trust the linked seed alone: ensure its visible JRA header
        # actually names this requested day, track, race 11.
        try:
            parse_prestart_card_candidate(page, seed, day, track, 11)
        except JraPrestartCardError:
            raise JraLinkResolutionError("JRA seed racecard not identifiable") from None
        matches = []
        for label, href in _links(page):
            if label != f"{race}R":
                continue
            candidate = _validated_card_link(href, seed, day, track, race)
            if candidate and candidate not in matches:
                matches.append(candidate)
        if len(matches) != 1:
            raise JraLinkResolutionError("Target JRA race link not unambiguous")
        target = matches[0]
    return {
        "version": VERSION, "date": day, "track": track, "race": race,
        "officialRacecardUrl": target, "officialLinkFound": True,
        "officialLinkTargetVerified": False,
        "officialRacecardContentsVerified": False,
        "officialStartersVerified": False, "officialScratchesVerified": False,
        "officialGoingVerified": False, "officialPostTimeVerified": False,
        "formalTenFactorReady": False, "bettingReady": False,
        "researchOnly": True, "existingReceiptsChanged": False,
        "existingTicketsChanged": False, "newJrdbRequests": 0,
        "note": ("JRA公開出馬表への公式サイト内リンクだけを発見。"
                 "リンク先の発走時刻、出走・取消・馬場の独立照合は未実施。"),
    }
