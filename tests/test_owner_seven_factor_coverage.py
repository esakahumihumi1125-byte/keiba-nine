"""Read-only 7-factor score COVERAGE tests; no real JRDB/JRA data."""
from copy import deepcopy
from datetime import datetime
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_seven_factor_coverage import seven_factor_research_coverage


WEIGHTS = {"course_distance": 17, "ground": 12, "pace": 17,
           "jockey_stable": 10, "rotation": 1}
ORDER = ("course_distance", "ground", "pace", "jockey_stable", "rotation")


def example():
    horses = [
        (1, "S", "A", 30, 2),
        (2, "A", "C", 20, 0),
        (3, "B", "B", 10, 1),
        (4, "C", "S", 0, 3),
    ]
    draft = {
        "track": "東京", "race": 1, "postTime": "12:00",
        "status": "provisional_draft",
        "runners": [{"number": n, "training": training, "recent": recent}
                    for n, training, recent, _, _ in horses],
    }
    ten = {
        "track": "東京", "race": 1, "runnerCount": 4,
        "horses": [
            {"number": n, "provisionalScoreReady": True,
             "provisionalPoints33": a + b,
             "provisionalBreakdown": {"training": a, "recent": b},
             "grades": {"training": training, "recent": recent}}
            for n, training, recent, a, b in horses
        ],
    }
    weights = {"course_distance": 85, "ground": None, "pace": 75,
               "jockey_stable": 50, "rotation": 80}
    extras = [
        {"number": n, "factors": {
            key: {
                "score": score,
                "points": (round(score * WEIGHTS[key] / 100, 4)
                           if score is not None else None),
                "weight": WEIGHTS[key],
                "grade": ("未評価" if score is None else
                          "S" if score >= 85 else "A" if score >= 70 else
                          "B" if score >= 55 else "C"),
            }
            for key, score in weights.items()
        }} for n in range(1, 5)
    ]
    held = {"track": "京都", "race": 2, "postTime": "13:00",
            "status": "hold", "runners": []}
    extra_held = {"track": "京都", "race": 2, "postTime": "13:00",
                  "status": "held", "reason": "after_start", "horses": []}
    return {
        "version": "jrdb-owner-auto-draft-1",
        "date": "20990101", "researchOnly": True, "privateOwnerOnly": True,
        "overallPredictionReady": False, "officialJraVerified": False,
        "bettingReady": False, "autoPurchase": False,
        "races": [draft, held],
        "tenFactorPreview": {
            "version": "owner-ten-factor-contract-1",
            "policyVersion": "research-6",
            "overallPredictionReady": False, "fullPredictionRaceCount": 0,
            "races": [ten, {"track": "京都", "race": 2, "runnerCount": 0,
                            "horses": []}],
        },
        "automaticFactorScores": {
            "version": "owner-automatic-factor-scores-3",
            "policyVersion": "research-6", "date": "20990101",
            "modelCalibrated": False, "officialJraVerified": False,
            "overallPredictionReady": False, "newProviderRequests": 0,
            "races": [
                {"track": "東京", "race": 1, "postTime": "12:00",
                 "status": "scored", "reason": None, "horses": extras},
                extra_held,
            ],
        },
    }


class SevenFactorCoverageTests(unittest.TestCase):
    def test_partial_78_of_100_includes_33_and_four_scored_optional_factors(self):
        source = example()
        old = deepcopy(source)
        result = seven_factor_research_coverage(source)
        self.assertEqual(source, old, "no changes to signed source")
        self.assertEqual(result["partialRaceCount"], 1)
        self.assertEqual(result["maximumPossibleAssessedWeight"], 90)
        self.assertEqual(result["remainingUnmappedWeight"], 10)
        self.assertFalse(result["overallPredictionReady"])
        self.assertFalse(result["officialJraVerified"])
        self.assertFalse(result["bettingReady"])
        self.assertEqual(result["ticketsIssued"], 0)
        row = result["races"][0]
        self.assertEqual(row["status"], "partial")
        horse = row["horses"][0]
        self.assertEqual(horse["number"], 1)
        self.assertEqual(horse["researchSubtotal"], 65.0)
        self.assertEqual(horse["assessedWeight"], 78)
        self.assertEqual(horse["unassessedWeight"], 22)
        self.assertIn("ground", horse["unassessedFactors"])
        self.assertIsNone(horse["finalScore100"])
        self.assertEqual(horse["overallGrade"], "未評価")
        self.assertIsNone(horse["overallRank"])
        self.assertEqual(result["races"][1]["status"], "held")
        self.assertEqual(result["races"][1]["horses"], [])

    def test_prestart_held_missing_recent_gets_partial_observation_not_ticket(self):
        source = example()
        race = source["races"][0]
        race["status"] = "hold"
        race["reason"] = "missing_factors"
        race["runners"][0]["recent"] = "未評価"
        for i, entry in enumerate(source["tenFactorPreview"]["races"][0]["horses"]):
            entry["provisionalScoreReady"] = False
            entry["provisionalPoints33"] = None
            entry["provisionalBreakdown"] = {"training": None, "recent": None}
            if i == 0:
                entry["grades"]["recent"] = "未評価"
        unchanged = deepcopy(source)
        before_off = datetime.fromisoformat("2099-01-01T09:00:00+09:00")
        result = seven_factor_research_coverage(source, now=before_off)
        self.assertEqual(source, unchanged)
        self.assertEqual(result["partialRaceCount"], 0)
        self.assertEqual(result["heldPartialRaceCount"], 1)
        self.assertTrue(result["heldCoverageNeverRanksOrBets"])
        row = result["races"][0]
        self.assertEqual(row["status"], "partial_held")
        self.assertTrue(row["heldResearchNeverFormsTickets"])
        horse = row["horses"][0]
        self.assertEqual(horse["number"], 1)
        self.assertEqual(horse["researchSubtotal"], 63.0)
        self.assertEqual(horse["assessedWeight"], 75)
        self.assertEqual(horse["unassessedWeight"], 25)
        self.assertIn("recent", horse["unassessedFactors"])
        self.assertIsNone(horse["finalScore100"])
        self.assertIsNone(horse["overallRank"])
        self.assertEqual(result["ticketsIssued"], 0)
        self.assertFalse(result["officialJraVerified"])
        self.assertEqual(seven_factor_research_coverage(source)["heldPartialRaceCount"], 0)
        after_off = datetime.fromisoformat("2099-01-01T13:00:00+09:00")
        self.assertEqual(seven_factor_research_coverage(
            source, now=after_off)["heldPartialRaceCount"], 0)
        source["tenFactorPreview"]["races"][0]["horses"][0]["provisionalPoints33"] = 30
        self.assertEqual(seven_factor_research_coverage(
            source, now=before_off)["heldPartialRaceCount"], 0)

    def test_prestart_tie_hold_with_complete_grades_is_still_unranked(self):
        source = example()
        source["races"][0].update(status="hold", reason="ambiguous_equal_grade_boundary")
        for entry in source["tenFactorPreview"]["races"][0]["horses"]:
            entry["provisionalScoreReady"] = False
            entry["provisionalPoints33"] = None
            entry["provisionalBreakdown"] = {"training": None, "recent": None}
        result = seven_factor_research_coverage(
            source, now=datetime.fromisoformat("2099-01-01T09:00:00+09:00"))
        self.assertEqual(result["heldPartialRaceCount"], 1)
        self.assertEqual(result["races"][0]["horses"][0]["researchSubtotal"], 65.0)
        self.assertIsNone(result["races"][0]["horses"][0]["overallRank"])

    def test_all_optional_scores_means_maximum_90_not_formal_100(self):
        source = example()
        for item in source["automaticFactorScores"]["races"][0]["horses"]:
            item["factors"]["ground"] = {
                "score": 75, "points": 9.0, "weight": 12, "grade": "A"
            }
        output = seven_factor_research_coverage(source)
        for horse in output["races"][0]["horses"]:
            self.assertEqual(horse["assessedWeight"], 90)
            self.assertEqual(horse["unassessedWeight"], 10)
            self.assertEqual(horse["unassessedFactors"],
                             ["pedigree", "draw_weight", "body_condition"])
            self.assertIsNone(horse["finalScore100"])

    def test_mismatch_isolated_to_one_race_and_no_score_promotion(self):
        bad = example()
        bad["automaticFactorScores"]["races"][0]["horses"][0]["number"] = 8
        output = seven_factor_research_coverage(bad)
        self.assertEqual(output["partialRaceCount"], 0)
        self.assertEqual(output["races"][0]["status"], "held")
        self.assertEqual(output["races"][0]["horses"], [])
        self.assertEqual(output["races"][1]["status"], "held")

    def test_different_score_or_grade_never_sneaks_through(self):
        for edit in [
            lambda x: x["automaticFactorScores"]["races"][0]["horses"][0]["factors"]["pace"].update(points=17),
            lambda x: x["tenFactorPreview"]["races"][0]["horses"][0].update(provisionalPoints33=33),
            lambda x: x["automaticFactorScores"]["races"][0]["horses"][0]["factors"]["pace"].update(grade="S"),
            lambda x: x["races"][0]["runners"][1].update(number=1),
        ]:
            bad = example()
            edit(bad)
            output = seven_factor_research_coverage(bad)
            self.assertEqual(output["races"][0]["status"], "held")

    def test_remaining_three_points_fields_observed_are_not_scores(self):
        source = example()
        flags = ("pedigree", "draw_weight", "jockey_stable",
                 "rotation", "past_corner")
        source["runnerSourceEvidence"] = {
            "version": "owner-runner-source-hints-1",
            "researchOnly": True, "privateOwnerOnly": True,
            "officialJraVerified": False,
            "overallPredictionReady": False, "bettingReady": False,
            "verifiedNewFactorCount": 0, "newProviderRequests": 0,
            "rawSourceRowsIncluded": False, "factorFields": list(flags),
            "raceCount": 2, "races": [
                {"track": "東京", "race": 1, "status": "observed",
                 "runners": [
                     {"number": n, "verifiedFactorCount": 0,
                      "observed": {
                          "pedigree": n % 2 == 1,
                          "draw_weight": n != 1,
                          "jockey_stable": True, "rotation": True,
                          "past_corner": False,
                      }} for n in (4, 2, 1, 3)]},
                {"track": "京都", "race": 2, "status": "held", "runners": []},
            ]
        }
        original = deepcopy(source)
        result = seven_factor_research_coverage(source)
        self.assertEqual(original, source, "no input mutation")
        self.assertEqual(result["partialRaceCount"], 1)
        self.assertTrue(result["remainingFactorFieldsOnly"])
        self.assertFalse(result["racedayBodyWeightFromDayRead"])
        one, two = result["races"][0]["horses"][:2]
        self.assertEqual(one["remainingMaterialReadiness"], {
            "pedigree": "fields_observed",
            "draw_weight": "fields_missing",
            "body_condition": "raceday_bodyweight_not_available",
        })
        self.assertEqual(two["remainingMaterialReadiness"]["pedigree"],
                         "fields_missing")
        self.assertEqual(two["remainingMaterialReadiness"]["draw_weight"],
                         "fields_observed")
        self.assertTrue(one["remainingEvidenceIsNotScore"])
        self.assertEqual(one["assessedWeight"], 78)
        self.assertEqual(one["unassessedWeight"], 22)
        self.assertIsNone(one["finalScore100"])
        self.assertEqual(one["overallGrade"], "未評価")

    def test_bad_material_roster_is_unchecked_not_missing(self):
        source = example()
        source["runnerSourceEvidence"] = {
            "version": "owner-runner-source-hints-1",
            "researchOnly": True, "privateOwnerOnly": True,
            "officialJraVerified": False,
            "overallPredictionReady": False, "bettingReady": False,
            "verifiedNewFactorCount": 0, "newProviderRequests": 0,
            "rawSourceRowsIncluded": False,
            "factorFields": ["pedigree", "draw_weight", "jockey_stable",
                             "rotation", "past_corner"],
            "raceCount": 2, "races": [
                {"track": "東京", "race": 1, "status": "observed",
                 "runners": [{
                     "number": n, "verifiedFactorCount": 0,
                     "observed": {
                         "pedigree": True, "draw_weight": True,
                         "jockey_stable": True, "rotation": True,
                         "past_corner": True,
                     },
                 } for n in (1, 2, 3, 8)]},
                {"track": "京都", "race": 2, "status": "held", "runners": []},
            ],
        }
        result = seven_factor_research_coverage(source)
        self.assertEqual(result["partialRaceCount"], 1)
        for horse in result["races"][0]["horses"]:
            self.assertEqual(horse["remainingMaterialReadiness"]["pedigree"],
                             "not_checked")
            self.assertEqual(horse["remainingMaterialReadiness"]["draw_weight"],
                             "not_checked")
            self.assertEqual(horse["remainingMaterialReadiness"]["body_condition"],
                             "raceday_bodyweight_not_available")
            self.assertIsNone(horse["finalScore100"])

    def test_unavailable_material_is_not_false_no_data(self):
        source = example()
        result = seven_factor_research_coverage(source)
        first = result["races"][0]["horses"][0]
        self.assertEqual(first["remainingMaterialReadiness"], {
            "pedigree": "not_checked", "draw_weight": "not_checked",
            "body_condition": "raceday_bodyweight_not_available",
        })

    def test_whole_day_identity_or_status_mutation_is_rejected(self):
        for edit in [
            lambda x: x.update(officialJraVerified=True),
            lambda x: x["automaticFactorScores"].update(modelCalibrated=True),
            lambda x: x["tenFactorPreview"].update(fullPredictionRaceCount=1),
            lambda x: x["automaticFactorScores"]["races"].pop(),
        ]:
            bad = example()
            edit(bad)
            with self.assertRaises(CoverageError):
                seven_factor_research_coverage(bad)


if __name__ == "__main__":
    unittest.main()
