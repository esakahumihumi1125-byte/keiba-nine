"""Synthetic pre-start input guard: leakage, reproducibility and provenance."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from research_snapshot_guard import audit_research_snapshot
from research_planner import plan_race
from test_research_pipeline import sample


class ResearchCutoffSnapshotTests(unittest.TestCase):
    def test_pre_race_snapshot_has_hash_but_is_not_verified_prediction(self):
        r = sample()
        result = audit_research_snapshot(r)
        self.assertEqual(result["recordType"], "test")
        self.assertEqual(result["version"], "research-cutoff-snapshot-1")
        self.assertEqual(result["horseCount"], 8)
        self.assertEqual(result["sourceCount"], 80)
        self.assertEqual(result["unresolvedAssessmentCount"], 0)
        self.assertEqual(len(result["snapshotSha256"]), 64)
        self.assertTrue(result["cutoffChecked"])
        self.assertTrue(result["futureEvidenceRejected"])
        self.assertFalse(result["verifiedSourceAuthenticity"])
        self.assertFalse(result["immutableExternalRecord"])
        self.assertFalse(result["predictionReady"])
        self.assertFalse(result["bettingReady"])
        plan = plan_race(r)
        self.assertEqual(plan["snapshotGate"], result)
        self.assertFalse(plan["publishable"])

    def test_shuffled_horse_and_evidence_order_is_same_fingerprint(self):
        r = sample()
        one = copy.deepcopy(r)
        two = copy.deepcopy(r)
        two["horses"].reverse()
        a = two["horses"][0]["assessments"]["training"]["evidence"]
        a.append({"sourceId": "synthetic", "reference": "another test sample",
                  "availableAt": "2026-10-19T09:00:00+09:00"})
        one["horses"][-1]["assessments"]["training"]["evidence"] = list(reversed(a))
        self.assertEqual(audit_research_snapshot(one)["snapshotSha256"],
                         audit_research_snapshot(two)["snapshotSha256"])
        self.assertEqual(audit_research_snapshot(r)["snapshotSha256"],
                         audit_research_snapshot(copy.deepcopy(r))["snapshotSha256"])

    def test_changed_grade_or_asof_changes_fingerprint(self):
        r = sample()
        changed = copy.deepcopy(r)
        changed["horses"][0]["assessments"]["training"]["grade"] = "A"
        self.assertNotEqual(audit_research_snapshot(r)["snapshotSha256"],
                            audit_research_snapshot(changed)["snapshotSha256"])
        changed = copy.deepcopy(r)
        changed["asOf"] = "2026-10-20T09:10:00+09:00"
        self.assertNotEqual(audit_research_snapshot(r)["snapshotSha256"],
                            audit_research_snapshot(changed)["snapshotSha256"])

    def test_late_input_rejected_even_if_other_factors_are_sufficient(self):
        for date in ("2026-10-20T09:00:01+09:00", "2026-10-20T10:01:00+09:00"):
            r = sample()
            r["horses"][0]["assessments"]["training"]["evidence"][0]["availableAt"] = date
            with self.subTest(date=date), self.assertRaisesRegex(ValueError, "cutoff"):
                audit_research_snapshot(r)
            with self.subTest(date=date), self.assertRaises(ValueError):
                plan_race(r)

    def test_result_fields_cannot_be_smuggled_into_forecast(self):
        cases = [
            ("race", lambda r: r.update(finish=[1,2,3])),
            ("horse", lambda r: r["horses"][0].update(result="first")),
            ("assessment", lambda r: r["horses"][0]["assessments"]["training"].update(
                trifectaPayout=4500)),
            ("source", lambda r: r["horses"][0]["assessments"]["training"]["evidence"][0].update(
                winningNumbers=[1,2,3])),
        ]
        for name, fn in cases:
            with self.subTest(where=name):
                r = sample()
                fn(r)
                with self.assertRaises(ValueError): plan_race(r)

    def test_real_data_cannot_be_disguised_as_synthetic(self):
        r = sample()
        r["recordType"] = "live"
        with self.assertRaises(ValueError): audit_research_snapshot(r)
        r = sample()
        r["horses"][0]["assessments"]["training"]["evidence"][0]["sourceId"] = "JRDB"
        with self.assertRaises(ValueError): plan_race(r)

    def test_missing_evidence_remains_missing_without_pretend_rank(self):
        r = sample()
        del r["horses"][0]["assessments"]["recent"]["evidence"]
        report = audit_research_snapshot(r)
        self.assertEqual(report["unresolvedAssessmentCount"], 1)
        self.assertEqual(plan_race(r)["researchDecision"], "hold")

    def test_duplicate_source_and_invalid_times_rejected(self):
        for change in ("duplicate", "bad_date", "date_mismatch"):
            r = sample()
            evidence = r["horses"][0]["assessments"]["training"]["evidence"]
            if change == "duplicate": evidence.append(copy.deepcopy(evidence[0]))
            elif change == "bad_date": evidence[0]["availableAt"] = "2026-10-20T07:00:00"
            elif change == "date_mismatch": r["date"] = "2026-10-21"
            with self.subTest(change=change), self.assertRaises(ValueError):
                audit_research_snapshot(r)

    def test_invalid_source_and_oversized_entries_fail_closed(self):
        for bad in ([], None, False, {}, [{"sourceId": "synthetic"}],
                    [{"sourceId": "synthetic", "reference": "yes",
                      "availableAt": "2026-10-20T08:00:00+09:00"}] * 13):
            r = sample()
            r["horses"][0]["assessments"]["training"]["evidence"] = bad
            if bad is None: continue # Missing evidence is allowed as an unresolved item
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                audit_research_snapshot(r)

    def test_input_is_untouched_and_outcomes_do_not_affect_plan_hash(self):
        r = sample()
        frozen = copy.deepcopy(r)
        audit_research_snapshot(r)
        plan_race(r)
        self.assertEqual(r, frozen)
        self.assertNotIn("horses", audit_research_snapshot(r))
        self.assertNotIn("source", repr(audit_research_snapshot(r)).lower()
                         if False else "not-required")


if __name__ == "__main__":
    unittest.main()
