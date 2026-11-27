import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from windows_arc_race_validate_history import validate_local, summary_lines


class CombinedValidationTests(unittest.TestCase):
    def test_both_evaluators_share_readonly_race_connection(self):
        connections = [MagicMock() for _ in range(3)]
        with patch("windows_arc_race_validate_history._open", side_effect=connections) as op, \
             patch("windows_arc_race_validate_history.course_evaluate", return_value={"course":1}) as c, \
             patch("windows_arc_race_validate_history.workout_evaluate", return_value={"workout":2}) as w:
            result = validate_local(Path.cwd(), as_of_day="20261128")
        self.assertEqual(result, {"course":{"course":1},"workout":{"workout":2}})
        self.assertEqual(op.call_count,3)
        c.assert_called_once_with(connections[0],as_of_day="20261128")
        w.assert_called_once_with(connections[0],{"SLOP":connections[1],"WOOD":connections[2]},as_of_day="20261128")
        for conn in connections:
            conn.close.assert_called_once()

    def test_summary_contains_only_aggregate_fields(self):
        period = {"comparablePairs":2,"totalPairs":6,"directionalAgreementPercent":50.0,
                  "tied":0,"indexedRunners":3,"totalRunners":4,"private":"SECRET"}
        result = {
            "course":{"evaluatedRaces":1,"partialCoverage":{
                "evaluatedRaces":4,"observedRunners":10,"fieldRunners":20,
                "modelBrier":0.2,"uniformBrier":0.22,
                "observedModelBrier":0.18,"observedUniformBrier":0.22}},
            "workout":{"bySpec":{},"compositeStudy":dict.fromkeys(("earlier","holdout"),period),
                       "runnerIndexStudy":dict.fromkeys(("earlier","holdout"),period)},
        }
        lines = list(summary_lines(result))
        self.assertIn("COURSE_PARTIAL_COVERAGE=10/20",lines)
        self.assertIn("RUNNER_HOLDOUT_COVERAGE=3/4",lines)
        self.assertIn("NEW_PROVIDER_REQUESTS=0",lines)
        self.assertIn("FORMAL_TEN_FACTOR_READY=NO",lines)
        self.assertNotIn("SECRET",repr(lines))


if __name__ == "__main__":
    unittest.main()
