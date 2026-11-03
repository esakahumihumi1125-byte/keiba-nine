"""Synthetic source-status tests with no official JRA or JRDB connections."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from jrdb_race_context import RaceContextError
from jrdb_race_day_gates import audit_race_day_checks
from test_jrdb_evidence_readiness import sample


def fixture():
    p, entries, _, _ = sample()
    entries = copy.deepcopy(entries)
    entries[0]["withdrawn_flag"] = "0"
    entries[1]["withdrawn_flag"] = "1"
    entries[2]["withdrawn_flag"] = None
    entries[0]["horse_name"] = "LICENSED-HORSE-PRIVATE"
    conditions = [{"holdingkey": "05264b", "racedate": "20261101",
                   "turf_condition_cd": "03", "dirt_condition_cd": "01",
                   "updated_at": "2026-11-01T00:30:00Z",
                   "private_notes": "LICENSED-GOING-PRIVATE"}]
    # Race 1 is turf and course metadata may be absent; going is still a
    # source report. The race's official final condition is unknown.
    p[0]["surface"] = "芝"
    p[0]["distance_m"] = 1600
    p[0]["turn"] = "左"
    p[1]["surface"] = "ダート"
    p[1]["distance_m"] = 1800
    p[1]["turn"] = "右"
    return p, entries, conditions


class RaceDayGateTests(unittest.TestCase):
    def test_withdrawn_flag_counts_never_claim_official_verification(self):
        data = fixture()
        out = audit_race_day_checks(*data, "20261101")
        tokyo = next(x for x in out["races"] if x["track"] == "東京")
        kyoto = next(x for x in out["races"] if x["track"] == "京都")
        self.assertEqual((tokyo["providerNonWithdrawnCount"],
                          tokyo["providerWithdrawnCount"],
                          tokyo["withdrawalFlagUnknownCount"]), (1, 1, 0))
        self.assertTrue(tokyo["withdrawalFlagCoverageComplete"])
        self.assertTrue(tokyo["providerEntryCountMatches"])
        self.assertTrue(tokyo["sourceGoingRecorded"])
        self.assertTrue(tokyo["sourceGoingUpdateTimeRecorded"])
        self.assertFalse(tokyo["officialScratchesVerified"])
        self.assertFalse(tokyo["officialGoingVerified"])
        self.assertFalse(tokyo["finalRaceReady"])
        self.assertFalse(tokyo["predictionReady"])
        self.assertFalse(tokyo["bettingReady"])
        self.assertEqual(kyoto["withdrawalFlagUnknownCount"], 1)
        self.assertFalse(kyoto["withdrawalFlagCoverageComplete"])
        self.assertFalse(kyoto["sourceGoingRecorded"])
        self.assertEqual(out["racesWithProviderWithdrawal"], 1)
        self.assertEqual(out["racesWithUnknownFlags"], 1)
        self.assertEqual(out["racesWithOfficialFinalCheck"], 0)

    def test_all_zero_flags_still_do_not_prove_starters(self):
        p, entries, conditions = fixture()
        for row in entries:
            row["withdrawn_flag"] = "0"
        report = audit_race_day_checks(p, entries, conditions, "20261101")
        self.assertEqual(report["racesWithProviderWithdrawal"], 0)
        self.assertEqual(report["racesWithUnknownFlags"], 0)
        self.assertTrue(all(r["blockingChecks"] for r in report["races"]))
        self.assertTrue(all(not r["officialStarterListVerified"]
                            for r in report["races"]))

    def test_absent_flags_are_unknown_not_zero(self):
        p, entries, conditions = fixture()
        for row in entries:
            row.pop("withdrawn_flag", None)
        report = audit_race_day_checks(p, entries, conditions, "20261101")
        self.assertEqual(report["racesWithUnknownFlags"], 2)
        self.assertTrue(all(r["providerNonWithdrawnCount"] == 0
                            for r in report["races"]))
        self.assertFalse(report["bettingReady"])

    def test_invalid_flag_types_fail_closed(self):
        for flag in ("2", "01", 1, True, False, "withdrawn", " 0"):
            p, entries, conditions = fixture()
            entries[0]["withdrawn_flag"] = flag
            with self.subTest(flag=flag), self.assertRaises(CoverageError):
                audit_race_day_checks(p, entries, conditions, "20261101")

    def test_wrong_race_or_date_rejected(self):
        for field, value in (("racedate", "20261102"),
                             ("racekey", "05264b12"),
                             ("horse_number", "20")):
            p, entries, conditions = fixture()
            entries[0][field] = value
            with self.subTest(field=field), self.assertRaises(CoverageError):
                audit_race_day_checks(p, entries, conditions, "20261101")

    def test_duplicate_horse_rejected(self):
        p, entries, conditions = fixture()
        entries.append(copy.deepcopy(entries[0]))
        with self.assertRaises(CoverageError):
            audit_race_day_checks(p, entries, conditions, "20261101")

    def test_missing_or_invalid_going_stays_unverified(self):
        p, entries, _ = fixture()
        report = audit_race_day_checks(p, entries, [], "20261101")
        self.assertTrue(all(not r["sourceGoingRecorded"] for r in report["races"]))
        p, entries, conditions = fixture()
        conditions[0]["turf_condition_cd"] = "99"
        with self.assertRaises(RaceContextError):
            audit_race_day_checks(p, entries, conditions, "20261101")

    def test_unverified_roster_count_is_a_blocker(self):
        p, entries, conditions = fixture()
        p[0]["headcount"] = 3
        result = audit_race_day_checks(p, entries, conditions, "20261101")
        tokyo = next(x for x in result["races"] if x["track"] == "東京")
        self.assertFalse(tokyo["providerEntryCountMatches"])
        self.assertTrue(any("頭数" in x for x in tokyo["blockingChecks"]))

    def test_no_identity_or_secrets_in_response(self):
        report = audit_race_day_checks(*fixture(), "20261101")
        for secret in ("horse_name", "horse_number", "horse_id", "racekey",
                       "2328aaa95a05", "LICENSED-HORSE-PRIVATE",
                       "LICENSED-GOING-PRIVATE"):
            self.assertNotIn(secret, repr(report))

    def test_no_mutation(self):
        inp = fixture()
        before = copy.deepcopy(inp)
        audit_race_day_checks(*inp, "20261101")
        self.assertEqual(inp, before)


if __name__ == "__main__":
    unittest.main()
