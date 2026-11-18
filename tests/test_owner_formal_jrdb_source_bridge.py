"""Synthetic contract tests: provisional JRDB rows cannot become formal grades."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from evaluation_policy import OWNER_FORMAL_FACTORS
from jrdb_coverage import CoverageError
from owner_formal_jrdb_source_bridge import build_ungraded_formal_race_input
from owner_full_ten_day_gate import full_ten_day_research

DAY = "20990101"
AS_OF = "2099-01-01T09:00:00+09:00"
NOW = "2099-01-01T09:15:00+09:00"
OFF = "2099-01-01T10:00:00+09:00"


def source():
    runners = {}
    for number in range(1, 5):
        slots = {
            key: {"grade": "未評価", "basis": "not_mapped"}
            for key in OWNER_FORMAL_FACTORS
        }
        slots["training"] = {
            "grade": "S", "basis": "experimental_workout_index",
        }
        slots["recent"] = {
            "grade": "A", "basis": "experimental_recent_idm",
        }
        slots["pace"] = {
            "grade": "未評価",
            "basis": "historical_fourth_corner_only",
            "positionObservation": "frontObserved",
        }
        runners[f"{number:02d}"] = slots
    return {
        "racekey": "05264b01", "track": "東京", "race": 1,
        "byNumber": runners,
        "researchOnly": True, "independentJraVerified": False,
        "predictionReady": False, "bettingReady": False,
    }


def bridge(data):
    return build_ungraded_formal_race_input(
        data, day=DAY, as_of=AS_OF, off_at=OFF,
    )


class FormalJrdbSourceBridgeTests(unittest.TestCase):
    def test_provisional_data_reaches_internal_gate_without_any_grades(self):
        private = source()
        original = copy.deepcopy(private)
        row = bridge(private)
        self.assertEqual(private, original)
        self.assertEqual(row["track"], "東京")
        self.assertEqual(row["race"], 1)
        snapshot = row["snapshot"]
        self.assertEqual([h["number"] for h in snapshot["horses"]], [1, 2, 3, 4])
        self.assertTrue(all(
            set(h["assessments"]) == set(OWNER_FORMAL_FACTORS)
            and all(value is None for value in h["assessments"].values())
            for h in snapshot["horses"]
        ))
        self.assertFalse(snapshot["assessmentValidated"])
        self.assertFalse(snapshot["predictionValidated"])
        self.assertTrue(all(value is False
                            for value in snapshot["independentJra"].values()))

        report = full_ten_day_research(DAY, [row], now=NOW)
        self.assertEqual(report["races"][0]["status"], "missing_evidence")
        self.assertEqual(report["researchFormationRaces"], 0)
        self.assertEqual(report["races"][0]["reviewOnlyTicketCount"], 0)
        self.assertEqual(report["races"][0]["preview"]["ranking"], [])
        self.assertFalse(report["productionPredictionReady"])
        for private_marker in ("05264b01", "experimental_workout_index",
                               "experimental_recent_idm", "frontObserved"):
            self.assertNotIn(private_marker, repr(row))
            self.assertNotIn(private_marker, repr(report))

    def test_rejects_source_claims_and_foreign_race_identity(self):
        changes = (
            lambda x: x.update(researchOnly=False),
            lambda x: x.update(predictionReady=True),
            lambda x: x.update(bettingReady=True),
            lambda x: x.update(independentJraVerified=True),
            lambda x: x.update(racekey="08264b01"),
            lambda x: x.update(race=2),
            lambda x: x.update(track="京都"),
            lambda x: x.update(private_horse_id="do-not-copy"),
            lambda x: x["byNumber"].update({"19": copy.deepcopy(x["byNumber"]["01"])}),
            lambda x: x["byNumber"].pop("04"),
            lambda x: x["byNumber"]["01"]["training"].update(grade="X"),
            lambda x: x["byNumber"]["01"]["training"].update(
                reason="unverified source narrative"),
            lambda x: x["byNumber"]["01"]["pace"].update(grade="S"),
            lambda x: x["byNumber"]["01"]["ground"].update(grade="A"),
            lambda x: x["byNumber"]["01"]["body_condition"].update(
                basis="conformation_as_weight"),
        )
        for change in changes:
            data = source()
            change(data)
            with self.subTest(change=change), self.assertRaises(CoverageError):
                bridge(data)

    def test_day_and_prestart_time_are_still_checked_by_formal_validator(self):
        private = source()
        for day, as_of, off_at in (
            ("2099-02-30", AS_OF, OFF),
            (DAY, "2099-01-01T11:00:00+09:00", OFF),
            (DAY, AS_OF, "2099-01-02T10:00:00+09:00"),
            (DAY, "2099-01-01T09:00:00", OFF),
        ):
            with self.subTest(day=day, as_of=as_of, off_at=off_at):
                with self.assertRaises(CoverageError):
                    build_ungraded_formal_race_input(
                        private, day=day, as_of=as_of, off_at=off_at,
                    )

    def test_cannot_inject_official_roster_or_factor_proof(self):
        data = source()
        data["byNumber"]["01"]["recent"]["grade"] = "C"
        row = bridge(data)
        self.assertNotIn("confirmedStarterNumbers", row["snapshot"]["independentJra"])
        self.assertIsNone(row["snapshot"]["horses"][0]["assessments"]["recent"])


if __name__ == "__main__":
    unittest.main()
