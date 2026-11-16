"""Cross-check already-fetched /tky past-result references against /tze coverage.

This is a source DIAGNOSTIC, not permission to award a 近走 grade. It does
not fetch additional licensed rows, reveal result keys/horse IDs, repair
unobserved runs, alter any signed formation or claim a horse is a debutant.

The new /tky evidence is especially useful when the /tze beta source has
one scored run or no usable history. A referenced race is only a *hint*:
an observed reference greater than the visible /tze dated runs suggests a
feed/association gap worth investigating, NOT proof that JRDB is wrong.
"""
import re
from collections import Counter

from jrdb_coverage import CoverageError
from jrdb_evidence_readiness import _valid_date
from jrdb_owner_auto_draft import VERSION as DRAFT_VERSION

VERSION = "owner-recent-crossfeed-diagnostics-1"
REF = re.compile(r"[0-9]{16}\Z", re.ASCII)
NO = re.compile(r"0[1-9]|1[0-8]", re.ASCII)
MAX_RACES = 120
CODES = (
    "more_prior_references_than_tze_runs",
    "no_prior_reference_visible",
    "only_one_dated_run_visible",
    "multiple_unscored_runs_visible",
    "reference_or_tze_coverage_unknown",
)


def _reference_count(entry):
    """Count distinct valid /tky prior result IDs, or return None if unknown.

    Missing *columns* and malformed identifiers are not the same as a
    genuinely absent earlier race. Never use horse names or result payloads.
    """
    fields = ["lastrace_resultkey" + str(i) for i in range(1, 6)]
    if not all(k in entry for k in fields):
        return None
    seen = set()
    for key in fields:
        value = entry[key]
        if value in (None, "", "0000000000000000"):
            continue
        if type(value) is not str or not REF.fullmatch(value) or value in seen:
            return None
        seen.add(value)
    return len(seen)


def recent_crossfeed_diagnostics(programme, entries, drafts, day):
    """Source-bound, aggregate only, for ALREADY HELD missing-recent horses.

    This is called after the existing 4-read, prestart, roster/time-guarded
    draft logic. It never changes provisional/held status, horse scores, or
    signed receipts. Only fixed counts and venue/R coordinates escape.
    """
    if (not _valid_date(day) or not isinstance(programme, list)
            or len(programme) > MAX_RACES or not isinstance(entries, list)
            or len(entries) > 2160 or not isinstance(drafts, dict)
            or drafts.get("version") != DRAFT_VERSION
            or drafts.get("date") != day
            or drafts.get("researchOnly") is not True
            or drafts.get("privateOwnerOnly") is not True
            or drafts.get("officialJraVerified") is not False
            or drafts.get("overallPredictionReady") is not False
            or drafts.get("bettingReady") is not False
            or not isinstance(drafts.get("races"), list)
            or drafts.get("raceCount") != len(drafts["races"])
            or len(drafts["races"]) != len(programme)):
        raise CoverageError("Invalid crossfeed source contract")
    races = {}
    for p in programme:
        if (not isinstance(p, dict) or p.get("racedate") != day
                or type(p.get("track")) is not str
                or type(p.get("race")) is not int
                or not 1 <= p["race"] <= 12
                or type(p.get("racekey")) is not str
                or len(p["racekey"]) != 8):
            raise CoverageError("Invalid crossfeed programme")
        coord = (p["track"], p["race"])
        if coord in races:
            raise CoverageError("Repeated crossfeed programme")
        races[coord] = p
    by_entry = {}
    for e in entries:
        if not isinstance(e, dict):
            raise CoverageError("Invalid crossfeed entry")
        key, number = e.get("racekey"), e.get("horse_number")
        if (type(key) is not str or not any(p["racekey"] == key for p in programme)
                or type(number) is not str or not NO.fullmatch(number)):
            # An unrecognizable roster cannot support a source-gap claim.
            raise CoverageError("Crossfeed entry race/number mismatch")
        coord = key, number
        if coord in by_entry:
            raise CoverageError("Duplicate crossfeed entry")
        by_entry[coord] = e

    rows, seen, total = [], set(), Counter({code: 0 for code in CODES})
    examined = 0
    for race in drafts["races"]:
        if not isinstance(race, dict):
            raise CoverageError("Invalid crossfeed draft race")
        coord = race.get("track"), race.get("race")
        if coord not in races or coord in seen:
            raise CoverageError("Crossfeed race identity mismatch")
        seen.add(coord)
        if race.get("status") != "hold" or race.get("reason") != "missing_factors":
            continue
        head = races[coord]
        horses = race.get("runners")
        if (not isinstance(horses, list) or not 4 <= len(horses) <= 18
                or race.get("horseCount") != len(horses)):
            continue
        # An unrecognized roster counts as 'not checked', never evidence of
        # absent past runs. Isolation is per race: others remain available.
        counts = Counter({code: 0 for code in CODES})
        if ({h.get("number") for h in horses if isinstance(h, dict)}
                != {int(number) for (key, number) in by_entry
                    if key == head["racekey"]}):
            continue
        for h in horses:
            if (not isinstance(h, dict) or type(h.get("number")) is not int
                    or h.get("recent") not in ("S", "A", "B", "C", "未評価")):
                raise CoverageError("Invalid crossfeed runner")
            if h["recent"] != "未評価":
                continue
            source = by_entry[(head["racekey"], f"{h['number']:02d}")]
            refs = _reference_count(source)
            seen_runs = h.get("recentObserved")
            dated = (seen_runs.get("datedRuns")
                     if isinstance(seen_runs, dict) else None)
            if (type(dated) is not int or not 0 <= dated <= 5
                    or refs is None):
                code = "reference_or_tze_coverage_unknown"
            elif refs > dated:
                code = "more_prior_references_than_tze_runs"
            elif dated == 0 and refs == 0:
                code = "no_prior_reference_visible"
            elif dated == 1:
                code = "only_one_dated_run_visible"
            elif dated >= 2:
                code = "multiple_unscored_runs_visible"
            else:
                code = "reference_or_tze_coverage_unknown"
            counts[code] += 1
        if sum(counts.values()) == 0:
            continue
        examined += 1
        total.update(counts)
        rows.append({
            "track": coord[0], "race": coord[1],
            "unassessedRecentCount": sum(counts.values()),
            "reasonCounts": dict(counts),
        })
    if seen != set(races):
        raise CoverageError("Crossfeed day race set differs")
    return {
        "version": VERSION, "date": day, "raceCount": len(programme),
        "examinedHeldRaces": examined,
        "unassessedRecentCount": sum(total.values()),
        "reasonCounts": dict(total), "races": rows,
        "researchOnly": True, "privateOwnerOnly": True,
        "officialJraVerified": False, "formalRecentGradesVerified": 0,
        "newProviderRequests": 0, "existingTicketsChanged": False,
        "existingReceiptsChanged": False,
        "note": ("tkyに過去の参照があってtzeの観測走数より多い馬を"
                 "配信/結合の要調査候補として件数化。"
                 "参照のない馬も新馬とは断定せず、近走3点は未評価のまま。"),
    }


def compact_recent_crossfeed_log(report):
    """Safe allowlisted numbers only; no source text or horse identifiers."""
    if (not isinstance(report, dict) or report.get("version") != VERSION
            or report.get("researchOnly") is not True
            or report.get("officialJraVerified") is not False
            or type(report.get("unassessedRecentCount")) is not int
            or not isinstance(report.get("reasonCounts"), dict)
            or set(report["reasonCounts"]) != set(CODES)
            or any(type(n) is not int or not 0 <= n <= 2160
                   for n in report["reasonCounts"].values())
            or sum(report["reasonCounts"].values()) != report["unassessedRecentCount"]):
        return "unavailable"
    c = report["reasonCounts"]
    return ("held_recent:%d,possible_gap:%d,no_prior_reference:%d,"
            "one_run:%d,multiple_unscored:%d,unknown:%d" %
            (report["unassessedRecentCount"],
             c["more_prior_references_than_tze_runs"],
             c["no_prior_reference_visible"],
             c["only_one_dated_run_visible"],
             c["multiple_unscored_runs_visible"],
             c["reference_or_tze_coverage_unknown"]))
