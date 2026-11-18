"""Synthetic input-boundary tests for the private formal ten-factor gate."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_formal_assessment_input import validate_formal_assessment_snapshot
from owner_full_ten_day_gate import full_ten_day_research
from test_owner_full_ten_factor import fixture, NOW

DAY = "20990101"


def snapshot():
    source = fixture()
    source.update({"track": "東京", "race": 1})
    return source


def validate(source):
    return validate_formal_assessment_snapshot(
        source, expected_track="東京", expected_race=1, day=DAY,
    )


class FormalAssessmentInputTests(unittest.TestCase):
    def test_valid_synthetic_snapshot_is_copied_and_scores_with_existing_gate(self):
        source = snapshot()
        original = copy.deepcopy(source)
        checked = validate(source)
        self.assertEqual(checked, original)
        self.assertIsNot(checked, source)
        self.assertIsNot(checked["horses"], source["horses"])
        self.assertEqual(source, original)

        result = full_ten_day_research(
            DAY, [{"track": "東京", "race": 1, "snapshot": checked}],
            now=NOW,
        )
        self.assertEqual(result["fullTenResearchRankRaces"], 1)
        self.assertEqual(result["researchFormationRaces"], 1)
        self.assertEqual(result["races"][0]["reviewOnlyTicketCount"], 40)
        self.assertFalse(result["productionPredictionReady"])
        self.assertNotIn("sourceId", repr(result))
        self.assertNotIn("reference", repr(result))

    def test_unassessed_factor_stays_unassessed_and_cannot_create_tickets(self):
        source = snapshot()
        source["horses"][0]["assessments"]["body_condition"] = {
            "grade": "未評価",
        }
        checked = validate(source)
        result = full_ten_day_research(
            DAY, [{"track": "東京", "race": 1, "snapshot": checked}],
            now=NOW,
        )
        self.assertEqual(result["races"][0]["status"], "missing_evidence")
        self.assertEqual(result["races"][0]["reviewOnlyTicketCount"], 0)
        self.assertEqual(result["researchFormationRaces"], 0)

    def test_rejects_malformed_or_unbound_synthetic_inputs(self):
        mutations = (
            lambda x: x.update(private_horse_name="raw provider data"),
            lambda x: x.update(track="京都"),
            lambda x: x.update(race=True),
            lambda x: x["horses"][1].update(number=x["horses"][0]["number"]),
            lambda x: x["horses"][0]["assessments"].update(odds={"grade": "S"}),
            lambda x: x["horses"][0]["assessments"]["training"].update(grade="D"),
            lambda x: x["horses"][0]["assessments"]["training"]["evidence"][0].update(
                rawProviderRow={"secret": "not allowed"}),
            lambda x: x["horses"][0]["assessments"]["training"].update(
                reason=" "),
            lambda x: x["independentJra"].update(jra_scratches_verified="true"),
            lambda x: x.update(assessmentValidated=1),
            lambda x: x.update(offAt="2099-01-02T10:00:00+09:00"),
        )
        for mutate in mutations:
            source = snapshot()
            mutate(source)
            with self.subTest(mutation=mutate), self.assertRaises(CoverageError):
                validate(source)

    def test_late_evidence_is_left_for_existing_scorer_to_hold(self):
        source = snapshot()
        source["horses"][0]["assessments"]["training"]["evidence"][0][
            "availableAt"
        ] = "2099-01-01T09:01:00+09:00"
        checked = validate(source)
        result = full_ten_day_research(
            DAY, [{"track": "東京", "race": 1, "snapshot": checked}],
            now=NOW,
        )
        self.assertEqual(result["races"][0]["status"], "missing_evidence")
        self.assertEqual(result["races"][0]["reviewOnlyTicketCount"], 0)


if __name__ == "__main__":
    unittest.main()
