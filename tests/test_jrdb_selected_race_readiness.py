"""Synthetic-only tests for selected-race single-source readiness response."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from jrdb_selected_race_readiness import selected_race_readiness
from jrdb_coverage import CoverageError
from test_jrdb_evidence_readiness import sample
from test_jrdb_race_day_gates import fixture

NOW = "2026-11-01T09:30:00+09:00"


def records():
    programme, entries, holding = fixture()
    _, _, training, past = sample()
    return programme, entries, training, past, holding


class SelectedRaceReadinessTests(unittest.TestCase):
    def check(self, *values, track="東京", race=1, day="20261101", now=NOW):
        return selected_race_readiness(*(values or records()), day, track, race, now)

    def test_only_one_race_aggregates_and_never_forecasts(self):
        result = self.check()
        self.assertEqual((result["track"], result["race"]), ("東京", 1))
        self.assertEqual(result["observedEntries"], 2)
        self.assertEqual(result["trainingUnaccounted"], 0)
        self.assertEqual(result["lastWeekUnaccounted"], 1)
        self.assertEqual(result["pastRunUnaccounted"], 1)
        self.assertEqual(result["providerWithdrawnCount"], 1)
        self.assertEqual(result["withdrawalFlagUnknownCount"], 0)
        self.assertEqual(result["sourceGoing"], "重")
        self.assertEqual(result["prestartWindow"], "within_two_hours")
        self.assertTrue(result["sourceSnapshotNotOfficial"])
        self.assertFalse(result["independentJraConnected"])
        self.assertFalse(result["officialJraFinalVerification"])
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["bettingReady"])
        provisional = result["experimentalGradeDistributions"]
        self.assertTrue(provisional["experimental"])
        self.assertFalse(provisional["overallRankReady"])
        self.assertFalse(provisional["predictionReady"])
        for key in ("training", "recent"):
            grades = provisional[key]
            self.assertEqual(set(grades), {"S", "A", "B", "C", "未評価"})
            self.assertEqual(sum(grades.values()), result["observedEntries"])
            self.assertTrue(all(type(v) is int and v >= 0
                                for v in grades.values()))
        self.assertEqual(
            result["observedEntries"] - provisional["training"]["未評価"],
            result["factorResearch"]["bothGraded"] + result["factorResearch"]["trainingOnly"])
        self.assertEqual(
            result["observedEntries"] - provisional["recent"]["未評価"],
            result["factorResearch"]["bothGraded"] + result["factorResearch"]["recentOnly"])
        self.assertNotIn("byNumber", repr(provisional))
        self.assertNotIn("racekey", repr(provisional))
        self.assertNotIn("horse_id", repr(provisional))
        self.assertEqual(result["gradedFactors"], 0)
        self.assertEqual(result["version"], "selected-race-readiness-5")
        entry = result["entryMaterials"]
        self.assertEqual(entry["observedFactorSlots"], 6)
        self.assertEqual(entry["unmappedFactors"], 4)
        self.assertEqual(entry["verifiedFactorCount"], 0)
        self.assertFalse(entry["pedigreeAptitudeAssessed"])
        self.assertFalse(entry["drawWeightEffectAssessed"])
        self.assertFalse(entry["rotationEffectAssessed"])
        self.assertEqual(sum(entry["rotationIntervals"].values()), 2)
        self.assertEqual(entry["rotationIntervals"]["under14Days"], 0)
        self.assertEqual(entry["rotationIntervals"]["days14to55"], 1)
        self.assertEqual(entry["rotationIntervals"]["unknown"], 1)
        self.assertEqual(entry["entryObservations"]["bothPedigreeRecorded"], 0)
        personnel = result["personnelBodyMaterials"]
        self.assertEqual(personnel["observedFactorSlots"], 8)
        self.assertEqual(personnel["unmappedFactors"], 2)
        self.assertEqual(personnel["recorded"]["jockeyNameRecorded"], 0)
        self.assertEqual(personnel["recorded"]["anyConformationRecorded"], 0)
        self.assertFalse(personnel["bodyConditionAssessed"])
        self.assertFalse(personnel["raceDayBodyWeightFetched"])
        self.assertFalse(personnel["predictionReady"])
        pair = result["factorResearch"]
        bridge = result["factorMaterials"]
        self.assertEqual(bridge["unmappedFactors"], 7)
        self.assertEqual(bridge["observedFactors"], 3)
        self.assertFalse(bridge["paceForecastAvailable"])
        self.assertFalse(bridge["overallRankReady"])
        self.assertFalse(bridge["predictionReady"])
        self.assertEqual(sum(bridge["pastFourthCorner"].values()), 2)
        self.assertEqual(bridge["trainingProvisional"],
                         pair["bothGraded"] + pair["trainingOnly"])
        self.assertEqual(bridge["recentProvisional"],
                         pair["bothGraded"] + pair["recentOnly"])
        self.assertEqual(pair["bothGraded"] + pair["trainingOnly"] +
                         pair["recentOnly"] + pair["neither"], 2)
        self.assertTrue(pair["experimental"])
        self.assertEqual(pair["remainingFactors"], 8)
        self.assertFalse(pair["predictionReady"])
        self.assertNotIn("races", result, "response should contain just the selected race")

    def test_jockey_and_body_presence_is_redacted(self):
        p, e, t, z, h = records()
        e[0].update(jockey_name="PRIVATE-JOCKEY",
                    jockey_cd="00123", trainer_name="PRIVATE-TRAINER",
                    trainer_cd="00456", bodytype="222222")
        result = self.check(p, e, t, z, h)
        counts = result["personnelBodyMaterials"]["recorded"]
        self.assertEqual(counts["bothPersonnelNamesRecorded"], 1)
        self.assertEqual(counts["anyConformationRecorded"], 1)
        self.assertFalse(result["personnelBodyMaterials"]["bodyConditionAssessed"])
        self.assertFalse(result["predictionReady"])
        for secret in ("PRIVATE-JOCKEY", "PRIVATE-TRAINER", "222222", "00123"):
            self.assertNotIn(secret, repr(result))

    def test_second_race_is_isolated_and_uncertainty_remains(self):
        result = self.check(track="京都")
        self.assertEqual(result["observedEntries"], 1)
        self.assertEqual(result["trainingUnaccounted"], 1)
        self.assertEqual(result["lastWeekUnaccounted"], 1)
        self.assertEqual(result["pastRunUnaccounted"], 1)
        self.assertEqual(result["sourceGoing"], "未確認")
        self.assertEqual(result["withdrawalFlagUnknownCount"], 1)
        self.assertFalse(result["entryCountMatchesSource"] is False)
        self.assertFalse(result["bettingReady"])

    def test_does_not_leak_paid_records_or_unselected_races(self):
        text = repr(self.check())
        for token in ("racekey", "horse_id", "horse_number",
                      "NONPUBLIC", "LICENSED-HORSE-PRIVATE",
                      "LICENSED-GOING-PRIVATE", "SECRET-NOT-FOR-API",
                      "2328aaa95a05", "08264b01", "oikirisisu"):
            self.assertNotIn(token, text)

    def test_unknown_race_or_invalid_requested_coordinates_fail(self):
        for args in [
            {"track":"阪神"}, {"track":"TOKYO"}, {"race":0}, {"race":13},
            {"race":"1"}, {"race":True}, {"day":"20261132"},
            {"day":"2026-11-01"}, {"day":"20261102"},
        ]:
            with self.subTest(args=args), self.assertRaises(CoverageError):
                self.check(**args)
        with self.assertRaises(CoverageError):
            self.check(track="京都", race=2)

    def test_unrelated_race_anomalies_do_not_fail_selected_race(self):
        p, e, t, z, h = records()
        # The response is for Tokyo 1R only; unrelated Kyoto records must not
        # be joined to it, even if another race's beta rows need repair.
        e[2]["racedate"] = "20261102"
        e[2]["withdrawn_flag"] = "UNSUPPORTED"
        t.append({"racekey": "08264b01", "racedate": "20261101",
                  "horse_id": "not-a-verified-id"})
        z.append({"racekey": "08264b01", "racedate": "20261101",
                  "race_back_1_racedate": "20990101"})
        h.append({"holdingkey": "08264b", "racedate": "20261101",
                  "turf_condition_cd": "unknown"})
        report = self.check(p, e, t, z, h)
        self.assertEqual((report["track"], report["race"]), ("東京", 1))
        self.assertEqual(report["observedEntries"], 2)
        self.assertFalse(report["predictionReady"])
        self.assertFalse(report["officialJraFinalVerification"])

    def test_selected_race_mismatches_remain_blocking(self):
        p, e, t, z, h = records()
        e[0]["withdrawn_flag"] = "UNSUPPORTED"
        with self.assertRaises(CoverageError):
            self.check(p, e, t, z, h)

    def test_source_mismatch_fails_closed(self):
        p, e, t, z, h = records()
        e[0]["racedate"] = "20261102"
        with self.assertRaises(CoverageError):
            self.check(p, e, t, z, h)

    def test_bad_provider_status_fails_closed(self):
        p, e, t, z, h = records()
        e[0]["withdrawn_flag"] = "YES"
        with self.assertRaises(CoverageError):
            self.check(p, e, t, z, h)

    def test_blank_condition_preserves_unverified_race(self):
        p, e, t, z, _ = records()
        result = self.check(p, e, t, z, [])
        self.assertEqual(result["sourceGoing"], "未確認")
        self.assertEqual(result["sourceGoingAgeStatus"], "no_going_report")
        self.assertFalse(result["officialJraFinalVerification"])

    def test_source_inputs_are_not_mutated(self):
        inputs=records()
        frozen=copy.deepcopy(inputs)
        self.check(*inputs)
        self.assertEqual(inputs, frozen)


if __name__ == "__main__":
    unittest.main()
