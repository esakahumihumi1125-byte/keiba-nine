"""Offline 36R full-ten research gate: no JRDB/JRA calls or real bets."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_full_ten_day_gate import full_ten_day_research, VERSION
from test_owner_full_ten_factor import fixture, NOW, OFF

DATE = "20990101"
VENUES = ("東京", "京都", "福島")


def batch():
    return [
        {"track": track, "race": race, "snapshot": fixture()}
        for track in VENUES for race in range(1, 13)
    ]


class FullTenDayGateTests(unittest.TestCase):
    def test_synthetic_36r_gated_preview_remains_private_and_not_live(self):
        snapshots = batch()
        before = copy.deepcopy(snapshots)
        report = full_ten_day_research(DATE, snapshots, now=NOW)
        self.assertEqual(snapshots, before)
        self.assertEqual(report["version"], VERSION)
        self.assertEqual(report["date"], DATE)
        self.assertEqual(report["raceCount"], 36)
        self.assertEqual(report["fullTenResearchRankRaces"], 36)
        self.assertEqual(report["researchFormationRaces"], 36)
        self.assertEqual(report["heldOrIncompleteRaces"], 0)
        self.assertTrue(all(
            r["reviewOnlyTicketCount"] == 40
            and r["preview"]["trifecta"]["points"] == 40
            and r["status"] == "review_only"
            and r["researchOnly"] is True
            and r["bettingReady"] is False
            for r in report["races"]
        ))
        self.assertEqual(len({
            (r["track"], r["race"]) for r in report["races"]
        }), 36)
        for flag in ("liveJrdbConnectedHere", "independentJraFeedConnected",
                     "officialJraVerified", "productionPredictionReady",
                     "changesFrozenReceipts", "actualPurchase", "autoPurchase"):
            self.assertFalse(report[flag])
        self.assertEqual(report["newProviderRequests"], 0)
        self.assertFalse(report["paidSourceRowsIncluded"])

    def test_one_missing_factor_and_one_invalid_race_do_not_erase_other_34(self):
        snapshots = batch()
        snapshots[0]["snapshot"]["horses"][0]["assessments"]["pace"][
            "evidence"][0]["availableAt"] = "bad-timestamp"
        snapshots[1]["snapshot"]["offAt"] = "2099-01-02T10:00:00+09:00"
        untouched = copy.deepcopy(snapshots)
        report = full_ten_day_research(DATE, snapshots, now=NOW)
        self.assertEqual(snapshots, untouched)
        self.assertEqual(report["raceCount"], 36)
        self.assertEqual(report["researchFormationRaces"], 34)
        self.assertEqual(report["heldOrIncompleteRaces"], 2)
        self.assertEqual(report["unassessedRaceCount"], 1)
        self.assertEqual(report["invalidInternalSnapshotRaces"], 1)
        self.assertEqual(report["races"][0]["status"], "missing_evidence")
        self.assertEqual(report["races"][0]["reviewOnlyTicketCount"], 0)
        self.assertEqual(report["races"][0]["preview"][
            "missingReasonCodesByNumber"], {
                1: {"pace": "evidence_timestamp_invalid"}
            })
        self.assertEqual(report["races"][1]["status"], "invalid_internal_snapshot")
        self.assertEqual(report["races"][1]["preview"]["ranking"], [])
        self.assertEqual(report["races"][1]["preview"]["trifecta"]["tickets"], [])
        self.assertEqual(report["races"][2]["reviewOnlyTicketCount"], 40)
        self.assertFalse(report["officialJraVerified"])

    def test_at_race_off_none_of_the_36_gets_retroactive_tickets(self):
        report = full_ten_day_research(DATE, batch(), now=OFF)
        self.assertEqual(report["fullTenResearchRankRaces"], 0)
        self.assertEqual(report["researchFormationRaces"], 0)
        self.assertEqual(report["heldOrIncompleteRaces"], 36)
        self.assertTrue(all(
            r["status"] == "outside_prestart_window"
            and r["preview"]["trifecta"]["tickets"] == []
            for r in report["races"]
        ))

    def test_unverified_official_checks_never_create_review_tickets(self):
        rows = batch()[:1]
        rows[0]["snapshot"]["independentJra"]["jra_scratches_verified"] = False
        report = full_ten_day_research(DATE, rows, now=NOW)
        self.assertEqual(report["fullTenResearchRankRaces"], 1)
        self.assertEqual(report["researchFormationRaces"], 0)
        self.assertEqual(report["races"][0]["preview"]["trifecta"]["points"], 0)
        self.assertEqual(report["heldOrIncompleteRaces"], 1)

    def test_bad_day_duplicate_coordinates_or_extra_raw_keys_rejected(self):
        valid = batch()
        for day in ("20990230", "2099-01-01", "99990101", "00000000"):
            with self.subTest(day=day), self.assertRaises(CoverageError):
                full_ten_day_research(day, valid, now=NOW)
        for changed in (
            lambda x: x.append(copy.deepcopy(x[0])),
            lambda x: x[0].update(track=["東京"]),
            lambda x: x[0].update(race=True),
            lambda x: x[0].update(private_horse_name="DO_NOT_COPY"),
        ):
            sample = copy.deepcopy(valid)
            changed(sample)
            with self.assertRaises(CoverageError):
                full_ten_day_research(DATE, sample, now=NOW)
        with self.assertRaises(CoverageError):
            full_ten_day_research(DATE, valid + [copy.deepcopy(valid[0])],
                                  now=NOW)

    def test_no_raw_reasons_or_source_ids_in_readiness_batch(self):
        rows = batch()[:1]
        rows[0]["snapshot"]["horses"][0]["assessments"]["training"][
            "reason"] = "PRIVATE-WORKOUT-NARRATIVE"
        rows[0]["snapshot"]["horses"][0]["assessments"]["training"][
            "evidence"][0]["sourceId"] = "PRIVATE-PAID-SOURCE-ID"
        report = full_ten_day_research(DATE, rows, now=NOW)
        self.assertNotIn("PRIVATE-", repr(report))
        self.assertEqual(report["newProviderRequests"], 0)


if __name__ == "__main__":
    unittest.main()
