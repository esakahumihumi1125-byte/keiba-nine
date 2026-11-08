"""Offline-only hypothetical pace pressure and fail-closed checks."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_private_factor_bridge import build_private_factor_matrix
from jrdb_experimental_pace_scenarios import hypothesize_owner_pace
from test_jrdb_private_factor_bridge import inputs

def matrix_with(styles):
    m=build_private_factor_matrix(*inputs())
    r=m[0]
    template=copy.deepcopy(r["byNumber"]["01"])
    r["byNumber"]={}
    for i,style in enumerate(styles,1):
        slot=copy.deepcopy(template)
        slot["pace"]["positionObservation"]=style
        r["byNumber"][f"{i:02d}"]=slot
    return m

class OwnerPaceHypothesisTests(unittest.TestCase):
    def test_single_front_and_rebound_candidate_are_hypotheses_not_bets(self):
        m=matrix_with(["frontObserved","backObserved","backObserved",
                       "mixedObserved","insufficient"])
        orig=copy.deepcopy(m)
        result=hypothesize_owner_pace(m)
        self.assertEqual(m,orig)
        self.assertEqual(result["factorWeight"],20)
        self.assertFalse(result["winnerPickReady"])
        self.assertFalse(result["bettingReady"])
        self.assertTrue(result["scenarioNotActualPace"])
        first=result["races"][0]
        self.assertEqual(first["pacePressureScenario"],"single_front_observed")
        self.assertEqual(first["frontObserved"],1)
        self.assertTrue(first["coverageAdequate"])
        self.assertEqual(first["runners"][0]["scenarioFitBand"],"S")
        self.assertEqual(first["runners"][0]["reason"],"possible_single_front_advantage")
        self.assertEqual(first["runners"][1]["scenarioFitBand"],"B")
        self.assertEqual(first["runners"][4]["scenarioFitBand"],"未評価")
        self.assertFalse(first["paceForecastReady"])
        for forbidden in ("racekey","horse_id","byNumber","PAID-SECRET","horse_name"):
            self.assertNotIn(forbidden,repr(result))

    def test_multiple_fronts_are_a_scenario_not_race_outcome(self):
        m=matrix_with(["frontObserved","frontObserved","frontObserved",
                       "backObserved","backObserved"])
        r=hypothesize_owner_pace(m)["races"][0]
        self.assertEqual(r["pacePressureScenario"],"multiple_front_observed")
        self.assertEqual([h["scenarioFitBand"] for h in r["runners"]],
                         ["B","B","B","A","A"])
        self.assertFalse(r["gradeReady"])

    def test_unknown_styles_force_all_unassessed(self):
        m=matrix_with(["frontObserved","frontObserved","insufficient",
                       "insufficient","insufficient"])
        r=hypothesize_owner_pace(m)["races"][0]
        self.assertEqual(r["pacePressureScenario"],"coverage_insufficient")
        self.assertFalse(r["coverageAdequate"])
        self.assertEqual({h["scenarioFitBand"] for h in r["runners"]},{"未評価"})
        m=matrix_with(["backObserved","backObserved","mixedObserved"])
        r=hypothesize_owner_pace(m)["races"][0]
        self.assertEqual(r["pacePressureScenario"],"no_front_observed")
        self.assertEqual({h["scenarioFitBand"] for h in r["runners"]},{"未評価"})

    def test_tampering_with_positions_or_factor_grades_is_rejected(self):
        m=matrix_with(["frontObserved","backObserved","mixedObserved"])
        m[0]["byNumber"]["01"]["pace"]["positionObservation"]="winner"
        with self.assertRaises(CoverageError):
            hypothesize_owner_pace(m)
        m=matrix_with(["frontObserved","backObserved","mixedObserved"])
        m[0]["byNumber"]["01"]["pace"]["grade"]="S"
        with self.assertRaises(CoverageError):
            hypothesize_owner_pace(m)
        m=matrix_with(["frontObserved","backObserved","mixedObserved"])
        m[0]["byNumber"]["01"]["course_distance"]["grade"]="S"
        with self.assertRaises(CoverageError):
            hypothesize_owner_pace(m)
        m=matrix_with(["frontObserved","backObserved","mixedObserved"])
        del m[0]["byNumber"]["01"]["pedigree"]
        with self.assertRaises(CoverageError):
            hypothesize_owner_pace(m)

if __name__ == "__main__":
    unittest.main()
