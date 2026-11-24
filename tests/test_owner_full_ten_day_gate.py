"""Offline 36R full-ten research gate: no JRDB/JRA calls or real bets."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from owner_full_ten_day_gate import full_ten_day_research, VERSION
from test_owner_full_ten_factor import fixture, horse, NOW, OFF

DATE = "20990101"
VENUES = ("東京", "京都", "福島")


def batch():
    rows = [
        {"track": track, "race": race, "snapshot": fixture()}
        for track in VENUES for race in range(1, 13)
    ]
    for row in rows:
        row["snapshot"]["track"] = row["track"]
        row["snapshot"]["race"] = row["race"]
    return rows


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

    def test_factor_coverage_counts_missing_evidence_without_fake_runner_denominator(self):
        rows = batch()[:3]
        rows[0]["snapshot"]["horses"][0]["assessments"]["training"]["grade"] = "C"
        del rows[0]["snapshot"]["horses"][1]["assessments"]["training"]
        del rows[0]["snapshot"]["horses"][2]["assessments"]["training"]
        rows[1]["snapshot"]["horses"][0]["assessments"]["pace"]["evidence"][0][
            "availableAt"] = "2099-01-01T09:01:00+09:00"
        rows[2]["snapshot"]["offAt"] = "2099-01-02T10:00:00+09:00"
        expected = [{"track": row["track"], "race": row["race"]} for row in rows]
        expected.append({"track": "東京", "race": 4})
        report = full_ten_day_research(DATE, rows, now=NOW,
                                       expected_coordinates=expected)
        coverage = report["factorEvidenceCoverage"]
        self.assertEqual(coverage["checkedRaceCount"], 2)
        self.assertEqual(coverage["uncheckedRaceCount"], 2)
        self.assertEqual(coverage["checkedRunnerCount"], 16)
        self.assertTrue(coverage["coverageIsNotAbilityScore"])
        self.assertEqual(coverage["byFactor"]["training"], {
            "weight": 30, "traceableRunnerCount": 14,
            "unassessedRunnerCount": 2, "affectedRaceCount": 1,
            "missingReasonCounts": {"factor_unassessed": 2},
        })
        self.assertEqual(coverage["byFactor"]["pace"], {
            "weight": 17, "traceableRunnerCount": 15,
            "unassessedRunnerCount": 1, "affectedRaceCount": 1,
            "missingReasonCounts": {"evidence_after_prediction_cutoff": 1},
        })
        self.assertEqual(coverage["byFactor"]["recent"]["traceableRunnerCount"], 16)
        self.assertEqual(coverage["missingEvidencePriority"], ["training", "pace"])
        expired = full_ten_day_research(DATE, rows, now=OFF)["factorEvidenceCoverage"]
        self.assertEqual(expired["checkedRunnerCount"], 0)
        self.assertEqual(expired["uncheckedRaceCount"], 3)
        self.assertEqual(expired["missingEvidencePriority"], [])
        self.assertTrue(all(item["traceableRunnerCount"] == 0 and
                            item["unassessedRunnerCount"] == 0
                            for item in expired["byFactor"].values()))

    def test_expected_schedule_keeps_missing_races_visible(self):
        rows = batch()
        expected = [{"track": r["track"], "race": r["race"]} for r in rows]
        report = full_ten_day_research(DATE, rows[:-2], now=NOW,
                                       expected_coordinates=expected)
        self.assertEqual(report["expectedRaceCount"], 36)
        self.assertEqual(report["receivedSnapshotRaceCount"], 34)
        self.assertEqual(report["missingSnapshotRaceCount"], 2)
        self.assertEqual(report["raceCount"], 36)
        self.assertEqual(report["heldOrIncompleteRaces"], 2)
        self.assertEqual(report["researchFormationRaces"], 34)
        self.assertFalse(report["scheduleSnapshotCoverageComplete"])
        missing = [r for r in report["races"]
                   if r["status"] == "missing_internal_snapshot"]
        self.assertEqual({(r["track"], r["race"]) for r in missing},
                         {("福島", 11), ("福島", 12)})
        self.assertTrue(all(r["reviewOnlyTicketCount"] == 0
                            and r["preview"]["ranking"] == []
                            and r["preview"]["trifecta"]["tickets"] == []
                            for r in missing))
        full = full_ten_day_research(DATE, rows, now=NOW,
                                     expected_coordinates=expected)
        self.assertTrue(full["scheduleSnapshotCoverageComplete"])
        self.assertFalse(full["officialJraVerified"])

    def test_expected_schedule_rejects_duplicate_foreign_and_bad_coordinates(self):
        rows = batch()[:1]
        coord = {"track": "東京", "race": 1}
        for expected in ([], [coord, coord],
                         [{"track": "京都", "race": 1}],
                         [{"track": "東京", "race": True}],
                         [{"track": "東京", "race": 13}],
                         [{"track": "東京", "race": 1, "raw": "secret"}]):
            with self.subTest(expected=expected), self.assertRaises(CoverageError):
                full_ten_day_research(DATE, rows, now=NOW,
                                      expected_coordinates=expected)
        empty = full_ten_day_research(DATE, [], now=NOW,
                                      expected_coordinates=[coord])
        self.assertEqual(empty["missingSnapshotRaceCount"], 1)
        self.assertFalse(empty["scheduleSnapshotCoverageComplete"])
        unchecked = full_ten_day_research(DATE, rows, now=NOW)
        self.assertIsNone(unchecked["scheduleSnapshotCoverageComplete"])
        self.assertIsNone(unchecked["missingSnapshotRaceCount"])

    def test_one_full_eighteen_runner_tie_can_coexist_with_35_unchanged_races(self):
        rows = batch()
        single = rows[0]["snapshot"]
        single["horses"] = (
            [horse(1)] +
            [horse(n, {"training": "A"}) for n in range(2, 5)] +
            [horse(n, {"training": "B"}) for n in range(5, 19)]
        )
        single["independentJra"]["confirmedStarterNumbers"] = list(range(1, 19))
        untouched = copy.deepcopy(rows)
        report = full_ten_day_research(DATE, rows, now=NOW)
        self.assertEqual(rows, untouched)
        self.assertEqual(report["researchFormationRaces"], 36)
        self.assertEqual(report["races"][0]["reviewOnlyTicketCount"], 48)
        self.assertEqual(len({tuple(t) for t in report["races"][0]["preview"]
                              ["trifecta"]["tickets"]}), 48)
        self.assertTrue(all(r["reviewOnlyTicketCount"] == 40
                            for r in report["races"][1:]))
        self.assertFalse(report["productionPredictionReady"])
        self.assertFalse(report["independentJraFeedConnected"])
        # Once the scheduled race has started, no retroactive 48-point
        # preview or any other forecast gets created.
        expired = full_ten_day_research(DATE, rows, now=OFF)
        self.assertEqual(expired["researchFormationRaces"], 0)
        self.assertTrue(all(r["reviewOnlyTicketCount"] == 0
                            for r in expired["races"]))

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

    def test_foreign_race_snapshots_never_become_another_races_prediction(self):
        # Two legitimate-looking independent 10-factor assessments cannot
        # be swapped between a different R/venue or silently reused.
        rows = batch()
        rows[0]["snapshot"], rows[1]["snapshot"] = (
            rows[1]["snapshot"], rows[0]["snapshot"])
        rows[2]["snapshot"].pop("track")
        original = copy.deepcopy(rows)
        report = full_ten_day_research(DATE, rows, now=NOW)
        self.assertEqual(rows, original)
        self.assertEqual(report["researchFormationRaces"], 33)
        self.assertEqual(report["invalidInternalSnapshotRaces"], 3)
        for row in report["races"][:3]:
            self.assertEqual(row["status"], "invalid_internal_snapshot")
            self.assertEqual(row["preview"]["ranking"], [])
            self.assertEqual(row["reviewOnlyTicketCount"], 0)
        self.assertEqual(report["races"][3]["reviewOnlyTicketCount"], 40)
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

    def test_one_incomplete_jra_starter_roster_holds_only_its_race(self):
        rows = batch()
        rows[3]["snapshot"]["independentJra"][
            "confirmedStarterNumbers"] = [1, 2, 3, 4, 5, 6, 7]
        report = full_ten_day_research(DATE, rows, now=NOW)
        self.assertEqual(report["researchFormationRaces"], 35)
        self.assertEqual(report["heldOrIncompleteRaces"], 1)
        self.assertEqual(report["races"][3]["status"], "unverified_starter_roster")
        self.assertEqual(report["races"][3]["reviewOnlyTicketCount"], 0)
        self.assertEqual(report["races"][4]["reviewOnlyTicketCount"], 40)
        self.assertFalse(report["officialJraVerified"])

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
