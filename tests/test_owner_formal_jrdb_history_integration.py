"""Private history integration regression: formal JRDB intake never creates bets."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from test_jrdb_history_pipeline import context, run_case
from owner_formal_jrdb_day_bridge import VERSION


class FormalJrdbHistoryIntegrationTests(unittest.TestCase):
    def test_existing_history_route_supplies_redacted_formal_material_audit(self):
        sources = context()
        output = run_case(sources)
        audit = output["formalJrdbInputAudit"]
        self.assertEqual(audit["version"], VERSION)
        self.assertTrue(audit["sourceMaterialOnly"])
        self.assertEqual(audit["formalVerifiedFactorCount"], 0)
        self.assertFalse(audit["independentJraConnected"])
        self.assertFalse(audit["productionPredictionReady"])
        self.assertFalse(audit["actualPurchase"])
        self.assertFalse(audit["autoPurchase"])
        self.assertEqual(audit["extraPaidRequests"], 0)
        self.assertEqual(output["draCalls"], 3)
        self.assertEqual(output["dkaCalls"], 2)
        self.assertEqual(sources[4].call_count, 3)
        self.assertEqual(sources[5].call_count, 2)
        self.assertTrue(all(
            row["status"] in ("missing_evidence", "invalid_internal_snapshot",
                              "outside_prestart_window")
            for row in audit["races"]
        ))
        self.assertTrue(all(row["reviewOnlyTicketCount"] == 0
                            for row in audit["races"]))
        for private in ("racekey", "byNumber", "horse_id", "horse_number",
                        "05264b01", "05264a01", "PAID-SECRET",
                        "experimental_workout_index"):
            self.assertNotIn(private, repr(audit))
        self.assertFalse(output["predictionReady"])


if __name__ == "__main__":
    unittest.main()
