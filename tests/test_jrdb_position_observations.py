"""Historical 4th-corner tendency counts from synthetic races only."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_position_observations import summarize_position_observations
from jrdb_coverage import CoverageError
from jrdb_recent_hypothesis import build_recent_hints
from test_jrdb_recent_hypothesis import fixture


def prepared():
    p, e, z = fixture()
    return build_recent_hints(p, e, z, "20261101")


class PositionObservationTests(unittest.TestCase):
    def test_private_only_positioning_counts(self):
        reports = summarize_position_observations(prepared())
        tokyo, kyoto = reports["races"]
        self.assertEqual(tokyo["runnerCount"], 2)
        self.assertEqual(tokyo["observations"]["frontObserved"], 1)
        self.assertEqual(tokyo["observations"]["insufficient"], 1)
        self.assertEqual(kyoto["observations"]["insufficient"], 1)
        self.assertFalse(reports["paceForecastAvailable"])
        self.assertFalse(reports["predictionReady"])

    def test_positioning_counts_only_when_two_races_verified(self):
        data = prepared()
        first = data[0]["byNumber"]["01"]
        first["fourthObserved"] = 1
        first["frontAtFourth"] = 1
        out = summarize_position_observations(data)["races"][0]["observations"]
        self.assertEqual(out["insufficient"], 2)
        self.assertEqual(out["frontObserved"], 0)

    def test_back_observations_not_proven_closing_style(self):
        data = prepared()
        first = data[0]["byNumber"]["01"]
        first["fourthObserved"] = 2
        first["frontAtFourth"] = 0
        out = summarize_position_observations(data)["races"][0]["observations"]
        self.assertEqual(out["backObserved"], 1)
        self.assertFalse(summarize_position_observations(data)["paceForecastAvailable"])

    def test_mixed_positions_not_assigned_to_front(self):
        data = prepared()
        first = data[0]["byNumber"]["01"]
        first["fourthObserved"] = 2
        first["frontAtFourth"] = 1
        out = summarize_position_observations(data)["races"][0]["observations"]
        self.assertEqual(out["mixedObserved"], 1)
        self.assertEqual(out["frontObserved"], 0)

    def test_malformed_observations_blocked(self):
        for n, front in ((4, 0), (2, 3), (-1, 0), (2, -1),
                         (True, 0), (2, 1.5), ("2", 1)):
            with self.subTest(n=n, front=front):
                data = prepared()
                data[0]["byNumber"]["01"]["fourthObserved"] = n
                data[0]["byNumber"]["01"]["frontAtFourth"] = front
                with self.assertRaises(CoverageError):
                    summarize_position_observations(data)

    def test_duplicate_race_rejected(self):
        data = prepared()
        data.append(copy.deepcopy(data[0]))
        with self.assertRaises(CoverageError):
            summarize_position_observations(data)

    def test_raw_private_information_absent(self):
        reports = summarize_position_observations(prepared())
        for field in ("horse_id", "horse_number", "racekey",
                      "SECRET-PAID-HORSE", "idm", "byNumber", "01"):
            self.assertNotIn(field, repr(reports))

    def test_source_unchanged(self):
        data = prepared()
        frozen = copy.deepcopy(data)
        summarize_position_observations(data)
        self.assertEqual(data, frozen)


if __name__ == "__main__":
    unittest.main()
