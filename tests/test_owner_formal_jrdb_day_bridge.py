"""Synthetic same-day JRDB -> formal scorer bridge contract tests.

These never request provider data and never create verified predictions.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_coverage import CoverageError
from owner_formal_jrdb_day_bridge import audit_ungraded_formal_jrdb_day
from test_owner_formal_jrdb_source_bridge import source, DAY, AS_OF, NOW


def programme(key="05264b01", track="東京", race=1, *,
              post_time="10:00", headcount=4):
    return {
        "racekey": key, "racedate": DAY, "track": track, "race": race,
        "post_time": post_time, "headcount": headcount,
        "programmeOnly": True, "horsesVerified": False,
        "predictionStatus": "未作成",
    }


def two_races():
    a = source()
    b = copy.deepcopy(a)
    b["racekey"] = "08264b01"
    b["track"] = "京都"
    return ([programme(), programme("08264b01", "京都")], [a, b])


def audit(p, m, **overrides):
    kwargs = dict(as_of=AS_OF, now=NOW)
    kwargs.update(overrides)
    return audit_ungraded_formal_jrdb_day(DAY, p, m, **kwargs)


class FormalJrdbDayBridgeTests(unittest.TestCase):
    def test_same_day_private_jrdb_materials_remain_ungraded(self):
        p, m = two_races()
        original = copy.deepcopy((p, m))
        report = audit(p, m)
        self.assertEqual((p, m), original)
        self.assertEqual(report["scheduledRaceCount"], 2)
        self.assertEqual(report["sourceRaceCount"], 2)
        self.assertEqual(report["heldSourceRaces"], 0)
        self.assertEqual({(x["track"], x["race"]) for x in report["races"]},
                         {("東京", 1), ("京都", 1)})
        self.assertTrue(all(x["status"] == "missing_evidence"
                            for x in report["races"]))
        self.assertTrue(all(x["unassessedHorseCount"] == 4
                            for x in report["races"]))
        self.assertTrue(all(x["reviewOnlyTicketCount"] == 0
                            for x in report["races"]))
        self.assertFalse(report["productionPredictionReady"])
        self.assertEqual(report["formalVerifiedFactorCount"], 0)
        self.assertEqual(report["extraPaidRequests"], 0)
        for forbidden in ("05264b01", "08264b01", "experimental_workout_index",
                          "experimental_recent_idm", "frontObserved"):
            self.assertNotIn(forbidden, repr(report))

    def test_one_missing_source_holds_only_that_race(self):
        p, m = two_races()
        report = audit(p, [m[0]])
        self.assertEqual(report["sourceRaceCount"], 1)
        self.assertEqual(report["heldSourceRaces"], 1)
        by_track = {x["track"]: x for x in report["races"]}
        self.assertEqual(by_track["東京"]["status"], "missing_evidence")
        self.assertEqual(by_track["京都"]["status"], "invalid_internal_snapshot")

    def test_missing_posttime_and_count_conflict_hold_only_their_races(self):
        p, m = two_races()
        p[0]["headcount"] = 5
        p[1]["post_time"] = None
        report = audit(p, m)
        self.assertEqual(report["heldSourceRaces"], 2)
        self.assertTrue(all(x["status"] == "invalid_internal_snapshot"
                            for x in report["races"]))
        self.assertTrue(all(x["reviewOnlyTicketCount"] == 0
                            for x in report["races"]))

    def test_attempted_pace_or_official_grade_promotion_is_held(self):
        p, m = two_races()
        m[0]["byNumber"]["01"]["pace"]["grade"] = "S"
        report = audit(p, m)
        self.assertEqual(report["heldSourceRaces"], 1)
        by_track = {x["track"]: x for x in report["races"]}
        self.assertEqual(by_track["東京"]["status"], "invalid_internal_snapshot")
        self.assertEqual(by_track["京都"]["status"], "missing_evidence")

    def test_crossed_roster_and_date_are_rejected_before_gate(self):
        p, m = two_races()
        cases = [
            (lambda ps, ms: ms[0].update(racekey="08264b01")),
            (lambda ps, ms: ms[0].update(track="京都")),
            (lambda ps, ms: ps[0].update(racedate="20990102")),
            (lambda ps, ms: ps.append(copy.deepcopy(ps[0]))),
            (lambda ps, ms: ms.append(copy.deepcopy(ms[0]))),
            (lambda ps, ms: ms[0].update(race=2)),
            (lambda ps, ms: ps[0].update(horsesVerified=True)),
        ]
        for change in cases:
            programme_rows, material_rows = copy.deepcopy((p, m))
            change(programme_rows, material_rows)
            with self.subTest(change=change), self.assertRaises(CoverageError):
                audit(programme_rows, material_rows)

    def test_invalid_time_and_post_off_never_issue_tickets(self):
        p, m = two_races()
        for as_of, now in (
            ("2099-01-01T09:30:00+09:00", "2099-01-01T09:15:00+09:00"),
            ("2099-01-01T09:00:00", NOW),
        ):
            with self.subTest(as_of=as_of, now=now):
                with self.assertRaises(CoverageError):
                    audit(p, m, as_of=as_of, now=now)
        report = audit(p, m, now="2099-01-01T10:00:00+09:00")
        self.assertTrue(all(x["status"] == "outside_prestart_window"
                            for x in report["races"]))
        self.assertTrue(all(x["reviewOnlyTicketCount"] == 0
                            for x in report["races"]))


if __name__ == "__main__":
    unittest.main()
