"""Private post-off comparison of verified research6 tickets, not settlement.

Only call with HMAC-verified 79-weight snapshots. Keep the legacy signed
two-factor record namespace separate. No network, persistence or purchases.
"""
from collections import defaultdict
import re

from jrdb_program_preview import TRACKS
from owner_prestart_tse_review import compare_prestart_tickets, ProvisionalResultError

VERSION = "owner-research6-result-review-1"


def _normalize_verified(snapshots, day):
    if not isinstance(snapshots, list) or not 1 <= len(snapshots) <= 36:
        raise ProvisionalResultError("Missing verified research6 drafts")
    if not isinstance(day, str) or not re.fullmatch(r"20[0-9]{6}", day):
        raise ProvisionalResultError("Invalid selected date")
    iso = day[:4] + "-" + day[4:6] + "-" + day[6:]
    normalized, sizes = [], {}
    for s in snapshots:
        if (not isinstance(s, dict)
                or s.get("sourceKind") != "prestart-unverified-research6-79-draft"
                or s.get("date") != day or s.get("researchWeight") != 79
                or s.get("officialJraVerified") is not False
                or s.get("actualPurchase") is not False):
            raise ProvisionalResultError("Unexpected verified research6 mode")
        coord = s["track"], s["race"]
        if coord in sizes:
            raise ProvisionalResultError("Duplicate research6 race")
        sizes[coord] = s["runnerCount"]
        normalized.append({
            "date": iso, "track": s["track"], "race": s["race"],
            "sourceKind": "prestart-locked", "actualPurchase": False,
            "lockedAt": s["capturedAt"], "scheduledOffAt": s["scheduledOffAt"],
            "trifectaTickets": s["tickets"], "trioTickets": [],
        })
    return iso, normalized, sizes


def compare_research6_payoffs(snapshots, rows, day, *, now, source_read_count=1):
    """Reference-only hypothetical accounting in the separate 79-point mode."""
    from owner_prestart_thj_review import compare_verified_prestart_thj
    iso, normalized, _ = _normalize_verified(snapshots, day)
    report = compare_verified_prestart_thj(
        normalized, rows, iso, now=now, provider_read_count=source_read_count)
    report.update(version="owner-research6-payoff-review-1",
                  researchWeight=79, serverSigned=True,
                  source="research6-79-jrdb-thj-reference",
                  changesExistingRoi=False)
    return report


def compare_research6_results(snapshots, rows, day, *, now, source_read_count=1):
    if not isinstance(rows, list) or len(rows) > 2160:
        raise ProvisionalResultError("Invalid result rows")
    iso, normalized, sizes = _normalize_verified(snapshots, day)
    # First validate the entire provider response with the shared parser.
    compare_prestart_tickets(normalized, rows, iso, now=now,
                             source_read_count=source_read_count)
    groups = defaultdict(list)
    for row in rows:
        key = row["racekey"]
        groups[TRACKS[key[:2]], int(key[6:])].append(row)
    complete = []
    selected = {(s["track"], s["race"]): {f"{n:02d}" for n in s["third"]}
                for s in snapshots}
    for coord, size in sizes.items():
        group = groups.get(coord, [])
        if len(group) != size:
            continue
        numbers, places = set(), set()
        for row in group:
            finish = row.get("order_of_finish")
            if (not isinstance(finish, str)
                    or not re.fullmatch(r"0?[1-9]|1[0-8]", finish)
                    or row.get("trouble_classification") not in (None, "", "0")):
                break
            numbers.add(row["horse_number"])
            places.add(int(finish))
        else:
            if (len(numbers) == size and places == set(range(1, size + 1))
                    and selected[coord] <= numbers):
                complete.extend(group)
    report = compare_prestart_tickets(normalized, complete, iso, now=now,
                                      source_read_count=source_read_count)
    report.update(version=VERSION, researchWeight=79,
                  sourceKind="research6-79-signed-jrdb-provisional",
                  fullFinishOrderRequired=True, serverSigned=True,
                  changesExistingRoi=False,
                  note="署名付き79点研究下書きのJRDB暫定比較。全頭数・全着順が揃わない場合は保留。公式結果・払戻・回収率・購入とは別です。")
    return report
