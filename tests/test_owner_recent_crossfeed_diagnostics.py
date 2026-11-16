"""Synthetic /tky vs /tze diagnostics; do not fetch paid JRDB data."""
import copy
import sys
import unittest
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_owner_auto_draft import build_owner_auto_drafts
from owner_recent_crossfeed_diagnostics import (
    recent_crossfeed_diagnostics, compact_recent_crossfeed_log, VERSION,
)
from test_jrdb_owner_auto_draft import programme, research, JST, DAY

NOW = datetime(2099, 1, 1, 9, tzinfo=JST)
KEY = "0526ff01"


def source_fixture():
    pairs = [("S", "未評価")] * 5 + [("S", "A"), ("A", "未評価")]
    # Complete training but insufficient recent for six of seven starters.
    source = programme(headcount=7)
    draft = build_owner_auto_drafts(source, research(pairs), DAY, now=NOW)
    assert draft["races"][0]["reason"] == "missing_factors"
    runs = {1: 0, 2: 0, 3: 1, 4: 2, 5: 0, 6: 3, 7: 1}
    for h in draft["races"][0]["runners"]:
        n = h["number"]
        h["recentObserved"] = {
            "datedRuns": runs[n], "completedRuns": runs[n],
            "topThreeObserved": 0, "fourthCornerObserved": 0,
            "late3fObserved": 0,
        }
    resultkeys = [
        ["2310715320251115", "2310715320251001"],
        [],
        ["2310715320251115"],
        ["2310715320251115", "2310715320251001"],
        None,
        ["2310715320251115"],
        ["2310715320251115", "2310715320251001", "2310715320250901"],
    ]
    entries = []
    for i, ids in enumerate(resultkeys, 1):
        e = {"racekey": KEY, "horse_number": f"{i:02d}",
             "horse_id": f"123456789{i:03d}"}
        if ids is not None:
            e.update({f"lastrace_resultkey{k}":
                      ids[k-1] if k <= len(ids) else None
                      for k in range(1, 6)})
        entries.append(e)
    return source, entries, draft


class CrossfeedTests(unittest.TestCase):
    def test_anonymized_held_classification_with_no_calls_or_scoring(self):
        p, entries, draft = source_fixture()
        untouched = copy.deepcopy((p, entries, draft))
        out = recent_crossfeed_diagnostics(p, entries, draft, DAY)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual((out["raceCount"], out["examinedHeldRaces"],
                          out["unassessedRecentCount"]), (1, 1, 6))
        self.assertEqual(out["reasonCounts"], {
            "more_prior_references_than_tze_runs": 2,
            "no_prior_reference_visible": 1,
            "only_one_dated_run_visible": 1,
            "multiple_unscored_runs_visible": 1,
            "reference_or_tze_coverage_unknown": 1,
        })
        self.assertEqual(out["races"][0]["unassessedRecentCount"], 6)
        self.assertFalse(out["officialJraVerified"])
        self.assertEqual(out["formalRecentGradesVerified"], 0)
        self.assertEqual(out["newProviderRequests"], 0)
        self.assertFalse(out["existingTicketsChanged"])
        self.assertEqual((p, entries, draft), untouched)
        self.assertNotIn(KEY, repr(out))
        self.assertNotIn("2310715320251115", repr(out))
        self.assertNotIn("123456789", repr(out))
        self.assertEqual(compact_recent_crossfeed_log(out),
                         "held_recent:6,possible_gap:2,no_prior_reference:1,"
                         "one_run:1,multiple_unscored:1,unknown:1")

    def test_reference_keys_are_only_hints_not_debut_or_grades(self):
        p, entries, draft = source_fixture()
        entries[0]["lastrace_resultkey1"] = "0000000000000000"
        entries[0]["lastrace_resultkey2"] = None
        out = recent_crossfeed_diagnostics(p, entries, draft, DAY)
        self.assertEqual(out["reasonCounts"]["no_prior_reference_visible"], 2)
        self.assertEqual(out["reasonCounts"]["more_prior_references_than_tze_runs"], 1)
        self.assertEqual(next(h for h in draft["races"][0]["runners"]
                              if h["number"] == 1)["recent"], "未評価")

    def test_unrecognized_or_duplicate_source_is_not_made_up(self):
        for variant in ("malformed_ref", "duplicate_ref", "missing_columns"):
            p, entries, draft = source_fixture()
            if variant == "malformed_ref":
                entries[0]["lastrace_resultkey1"] = "bogus"
            elif variant == "duplicate_ref":
                entries[0]["lastrace_resultkey2"] = entries[0]["lastrace_resultkey1"]
            else:
                entries[0].pop("lastrace_resultkey3")
            out = recent_crossfeed_diagnostics(p, entries, draft, DAY)
            self.assertEqual(out["reasonCounts"]["reference_or_tze_coverage_unknown"], 2)
            self.assertEqual(out["reasonCounts"]["more_prior_references_than_tze_runs"], 1)
        p, entries, draft = source_fixture()
        entries.append(copy.deepcopy(entries[0]))
        with self.assertRaises(CoverageError):
            recent_crossfeed_diagnostics(p, entries, draft, DAY)

    def test_after_start_or_not_missing_has_no_diagnostic_or_ticket_change(self):
        p, entries, draft = source_fixture()
        later = build_owner_auto_drafts(
            p, research([("S", "未評価")] * 7), DAY,
            now=datetime(2099, 1, 1, 12, 1, tzinfo=JST))
        self.assertEqual(later["races"][0]["reason"], "after_provisional_off")
        out = recent_crossfeed_diagnostics(p, entries, later, DAY)
        self.assertEqual(out["examinedHeldRaces"], 0)
        self.assertEqual(out["unassessedRecentCount"], 0)
        self.assertEqual(compact_recent_crossfeed_log({"data": "private"}), "unavailable")

    def test_malformed_source_cannot_promote_formal_verification(self):
        p, entries, draft = source_fixture()
        draft["officialJraVerified"] = True
        with self.assertRaises(CoverageError):
            recent_crossfeed_diagnostics(p, entries, draft, DAY)
        p, entries, draft = source_fixture()
        draft["races"][0]["track"] = "京都"
        with self.assertRaises(CoverageError):
            recent_crossfeed_diagnostics(p, entries, draft, DAY)


if __name__ == "__main__":
    unittest.main()
