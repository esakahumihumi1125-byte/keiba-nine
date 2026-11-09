"""Read-only JRA official results page *candidate extraction* for owner use.

No feed authorization assumed. Parsing visible JRA HTML is NOT an official
settlement attestation; this importer never calls the independent result signer,
updates ROI, returns raw pages or makes betting decisions. A future vetted
source adapter must prove finality, refunds, special payouts and consent first.

One explicit safe public HTTPS request only; no bulk scraping or redirects
to arbitrary hosts. Unexpected layouts/ambiguity fail CLOSED.
"""
import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlsplit

from keiba_100yen_review import _date, ReviewInputError, VENUES
from jra_result_podium_guard import podium_payout_consistency, PodiumConsistencyError
from owner_official_settlement_replay import (
    _source_url, SettlementReplayError
)

VERSION = "owner-jra-public-result-probe-1"
MAX_BYTES = 600_000
MAX_TEXT = 140_000
LABELS = ("単勝", "複勝", "枠連", "ワイド", "馬連", "馬単", "3連複", "3連単")
JST = timezone(timedelta(hours=9))
TICKET = re.compile(r"(?<!\d)(\d{1,2})[-‐‑–—－→](\d{1,2})[-‐‑–—－→](\d{1,2})(?!\d)")
YEN = re.compile(r"(?<!\d)(\d{1,3}(?:,\d{3})+|\d{2,9})\s*円")


class JraPublicProbeError(ValueError):
    """Safe diagnostic: no source body, URL or race identifiers included."""


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise JraPublicProbeError("Unexpected official page redirect")


class _Visible(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0
        self.in_cell = None
        self.row = None
        self.rows = []
        self.cell_start = None

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
            return
        if self.skip:
            return
        if tag in ("br", "hr"):
            self.parts.append("\n")
        if tag == "tr":
            self.row = []
        if tag in ("th", "td") and self.row is not None:
            self.cell_start = len(self.parts)
            self.in_cell = tag

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag in ("td", "th") and self.row is not None and self.in_cell == tag:
            value = "".join(self.parts[self.cell_start:]).strip()
            self.row.append(re.sub(r"[\t\r ]+", " ", value))
            self.in_cell = None
        if tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
        if tag in ("td", "th", "tr", "p", "li", "h1", "h2",
                   "h3", "h4", "section", "div"):
            self.parts.append("\n")

    @property
    def visible(self):
        return re.sub(r"\n{3,}", "\n\n", "".join(self.parts))


def _safe_identity(date, track, race, url):
    try:
        _date(date)
        if (track not in VENUES or type(race) is not int or
                not 1 <= race <= 12):
            raise ValueError()
        _source_url(url, date.replace("-", ""))
        parsed = urlsplit(url)
        if parsed.hostname not in ("www.jra.go.jp", "jra.jp", "app.jra.jp"):
            raise ValueError()
    except (ReviewInputError, SettlementReplayError, TypeError,
            ValueError, AttributeError):
        raise JraPublicProbeError("Invalid official result identity") from None
    return parsed


def _validate_ticket(kind, numbers):
    triple = tuple(int(i) for i in numbers)
    if any(not 1 <= i <= 18 for i in triple) or len(set(triple)) != 3:
        raise JraPublicProbeError("Invalid official ticket combination")
    return tuple(sorted(triple)) if kind == "3連複" else triple


def _extract_block(section, kind):
    marker = re.search(r"(?:^|\n)\s*(?:[*・]\s*)?"+re.escape(kind)+r"\s*(?=\n|$)", section)
    if marker is None:
        raise JraPublicProbeError("Required result payout heading unavailable")
    after = section[marker.end():]
    # Stop at the next type. A missing terminator for trifecta is
    # accepted only when the standard post-table caution text follows.
    terminator = re.search(
        r"(?:^|\n)\s*(?:[*・]\s*)?(?:"
        + "|".join(re.escape(k) for k in LABELS if k != kind)
        + r"|勝馬の紹介|競走中の出来事|勝馬投票に|JRAプラス10)"
        + r"\s*(?=\n|$)", after)
    if terminator:
        after = after[:terminator.start()]
    return after


def _payouts(section, kind):
    content = _extract_block(section, kind)
    if len(content) > 8000:
        raise JraPublicProbeError("Payout section too large")
    # Each official-style ticket line must be followed by its exact
    # 100-yen payout before the next ticket. Popularity values are ignored.
    matches = list(TICKET.finditer(content))
    if not 1 <= len(matches) <= 18:
        raise JraPublicProbeError("Payout combination count unavailable")
    out, seen = [], set()
    for i, match in enumerate(matches):
        bound = matches[i+1].start() if i+1 < len(matches) else len(content)
        until_next = content[match.end():bound]
        amounts = YEN.findall(until_next)
        if len(amounts) != 1:
            raise JraPublicProbeError("Ambiguous amount for ticket")
        ticket = _validate_ticket(kind, match.groups())
        if ticket in seen:
            raise JraPublicProbeError("Duplicate winning combination")
        seen.add(ticket)
        yen = int(amounts[0].replace(",", ""))
        if not 100 <= yen <= 1_000_000_000:
            raise JraPublicProbeError("Invalid official payout")
        out.append({"ticket": list(ticket), "payoutYen": yen})
    return out


def parse_public_result_candidate(html, url, date, track, race):
    """Extract candidate payouts from known JRA page; NEVER certify results.

    Parsing is limited to a clearly dated and track-labelled page containing
    both explicit 3連複 and 3連単 payout sections. Refunds, special payouts or
    changed layouts are deferred rather than incorrectly settled.
    """
    _safe_identity(date, track, race, url)
    if not isinstance(html, str) or not html or len(html) > MAX_BYTES:
        raise JraPublicProbeError("Invalid official HTML body")
    p = _Visible()
    try:
        p.feed(html)
        p.close()
    except Exception:
        raise JraPublicProbeError("Unrecognized official page structure") from None
    visible = p.visible
    if len(visible) > MAX_TEXT:
        raise JraPublicProbeError("Official visible page too large")
    y, m, d = [int(i) for i in date.split("-")]
    # Header is required near the results table (do not trust menu links).
    header = re.search(
        rf"{y}\s*年\s*{m}\s*月\s*{d}\s*日[\s\S]{{0,90}}?"
        rf"{re.escape(track)}[\s\S]{{0,50}}?"
        rf"(?:\b{race}\s*レース|\b{race}\s*R)",
        visible
    )
    if not header or "レース結果" not in visible[:header.end()]:
        raise JraPublicProbeError("Official race identity not found")
    # Navigation itself contains 払戻金. Only the payout heading after
    # the visible race results and their runner table is admissible.
    cut = visible.find("払戻金", header.end())
    if cut == -1 or "着順" not in visible[header.end():cut]:
        raise JraPublicProbeError("Official result table not identified")
    section = visible[cut+len("払戻金"):]
    if "返還" in section or "不成立" in section or "発売中止" in section:
        raise JraPublicProbeError("Refund/special settlement needs manual source review")
    trifecta = _payouts(section, "3連単")
    trio = _payouts(section, "3連複")
    try:
        podium = podium_payout_consistency(p.rows, trifecta, trio)
    except PodiumConsistencyError:
        raise JraPublicProbeError(
            "Finishing table and payouts could not be independently reconciled"
        ) from None
    return {
        "version": VERSION, "date": date, "track": track, "race": race,
        "trifectaCandidates": trifecta, "trioCandidates": trio,
        "payoutMatchesDisplayedPodium": podium["payoutMatchesDisplayedPodium"],
        "podiumShape": podium["podiumShape"],
        "matchingTrifectaCount": podium["matchingTrifectaCount"],
        "matchingTrioCount": podium["matchingTrioCount"],
        "sourceHostAllowlisted": True,
        "visibleRaceIdentityMatched": True,
        "payoutLayoutParsed": True, "podiumChecked": True,
        "officialJraVerified": False, "sourceAuthenticityAttested": False,
        "finalityVerified": False, "refundsVerified": False,
        "settlementReady": False, "officialRoiPercent": None,
        "actualPurchase": False, "researchOnly": True,
        "sourceReadCount": 0, "changesExistingReceipts": False,
        "changesExistingRoi": False,
        "note": "JRA公式形式の結果候補を読取。確定・返還・独立出典の認証前なので収支には算入しません。",
    }


def probe_official_result_page(url, date, track, race, *, opener=None):
    """One explicit owner-server read only, no retries/bulk or browser input.

    A source URL needs to be obtained separately from an authenticated JRA
    official result index. Do not synthesize links or call from public routes.
    """
    _safe_identity(date, track, race, url)
    try:
        from datetime import date as calendar
        race_day = calendar.fromisoformat(date)
        today = datetime.now(JST).date()
    except (ValueError, TypeError):
        raise JraPublicProbeError("Invalid result date") from None
    if not today - timedelta(days=365) <= race_day < today:
        raise JraPublicProbeError("Official result probing date out of range")
    request = Request(url, headers={
        "Accept": "text/html",
        "User-Agent": "KEIBA-NINE-Owner/1.0 (single official results page verification probe)"
    })
    client = opener or build_opener(_NoRedirect)
    try:
        with client.open(request, timeout=7) as response:
            if response.geturl() != url:
                raise JraPublicProbeError("Official URL changed in transit")
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type.lower():
                raise JraPublicProbeError("Unexpected official response type")
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise JraPublicProbeError("Official response over size limit")
            encoding = response.headers.get_content_charset() or "utf-8"
            if encoding.lower() not in ("utf-8", "shift_jis", "shift-jis", "cp932"):
                raise JraPublicProbeError("Unsupported official page encoding")
            html = data.decode(encoding)
    except JraPublicProbeError:
        raise
    except Exception:
        raise JraPublicProbeError("Official result page unavailable") from None
    result = parse_public_result_candidate(html, url, date, track, race)
    result["sourceReadCount"] = 1
    return result
