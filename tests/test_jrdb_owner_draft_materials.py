"""Synthetic-only private redacted six-category material observations."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from jrdb_owner_draft_materials import (
    observe_owner_draft_materials, observe_owner_draft_materials_isolated,
    unavailable,
)
from jrdb_coverage import CoverageError
from test_jrdb_day_materials_progress import fixture
from jrdb_program_preview import normalize_program_rows


class OwnerDraftMaterialTests(unittest.TestCase):
    def samples(self):
        raw, entries, training, recent, _ = fixture()
        return normalize_program_rows(raw, "20261101"), entries, training, recent

    def test_redacted_source_presence_without_new_factor_grades(self):
        data=self.samples()
        original=copy.deepcopy(data)
        report=observe_owner_draft_materials(*data,"20261101")
        self.assertEqual(report["status"],"observed")
        self.assertEqual(report["observedFactorSlots"],8)
        self.assertEqual(report["gradedNewFactors"],0)
        self.assertFalse(report["officialJraVerified"])
        self.assertEqual(len(report["races"]),2)
        tokyo=next(row for row in report["races"] if row["track"]=="東京")
        self.assertEqual(tokyo["runnerCount"],2)
        self.assertEqual(tokyo["counts"]["pedigree"],1)
        self.assertEqual(tokyo["counts"]["drawWeight"],1)
        self.assertEqual(tokyo["counts"]["personnel"],1)
        self.assertEqual(tokyo["counts"]["body"],1)
        self.assertEqual(data,original)
        for sensitive in ("racekey","horse_id","horse_number",
                          "PRIVATE-SIRE","PRIVATE-JOCKEY","oikirisisu"):
            self.assertNotIn(sensitive,repr(report))

    def test_one_broken_race_keeps_other_ungraded_source_counts(self):
        p,e,t,z=self.samples()
        healthy_diagnostic={}
        normal=observe_owner_draft_materials_isolated(
            p,e,t,z,"20261101",diagnostics=healthy_diagnostic)
        self.assertEqual(normal["status"],"observed")
        self.assertEqual(healthy_diagnostic,{
            "wholeDayCode":"ok","fallbackUsed":False,
            "candidateRaces":2,"verifiedRaces":2,"rejectedRaces":0
        })
        self.assertEqual(len(normal["races"]),2)
        bad=copy.deepcopy(e)
        bad.append(copy.deepcopy(bad[0]))
        pristine=copy.deepcopy((p,bad,t,z))
        self.assertRaises(CoverageError,observe_owner_draft_materials,
                          p,bad,t,z,"20261101")
        failed_diagnostic={}
        partial=observe_owner_draft_materials_isolated(
            p,bad,t,z,"20261101",diagnostics=failed_diagnostic)
        self.assertEqual((p,bad,t,z),pristine)
        self.assertEqual(failed_diagnostic,{
            "wholeDayCode":"source_coverage","fallbackUsed":True,
            "candidateRaces":2,"verifiedRaces":1,"rejectedRaces":1
        })
        self.assertEqual(partial["status"],"partial")
        self.assertEqual(len(partial["races"]),1)
        self.assertNotEqual(partial["races"][0]["track"],p[0]["track"])
        self.assertEqual(partial["observedFactorSlots"],8)
        self.assertEqual(partial["gradedNewFactors"],0)
        self.assertFalse(partial["officialJraVerified"])
        self.assertEqual(set(partial["races"][0]["counts"]),{
            "pedigree","drawWeight","rotation",
            "personnel","body","pastCorner"})
        for private in ("horse_id","racekey","PRIVATE-SIRE",
                        "PRIVATE-JOCKEY","oikirisisu"):
            self.assertNotIn(private,repr(partial))

    def test_fallback_keeps_valid_other_race_with_unrelated_bad_keys(self):
        p,e,t,z = self.samples()
        damaged = copy.deepcopy(e)
        damaged.append(copy.deepcopy(damaged[0]))
        # Paid source rows that cannot be associated with an exact known
        # race key must not be guessed into a healthy separate race.
        damaged.append({"racekey": ["unhashable"], "horse_id":"PRIVATE"})
        unrelated = {"racekey":"20991231", "horse_id":"PRIVATE"}
        untouched = copy.deepcopy((p,damaged,t,z))
        report = observe_owner_draft_materials_isolated(
            p,damaged,t+[unrelated],z+[unrelated],"20261101")
        self.assertEqual((p,damaged,t,z),untouched)
        self.assertEqual(report["status"],"partial")
        self.assertEqual(len(report["races"]),1)
        self.assertEqual(report["races"][0]["track"],p[1]["track"])
        self.assertNotIn("PRIVATE",repr(report))
        self.assertFalse(report["officialJraVerified"])
        self.assertEqual(report["gradedNewFactors"],0)

    def test_duplicate_provider_race_keys_not_reused_by_isolation(self):
        p,e,t,z = self.samples()
        altered = copy.deepcopy(p)
        altered[1]["racekey"] = altered[0]["racekey"]
        # A slot with a duplicate provider identity must never reuse
        # another race's material if whole-day verification failed.
        report = observe_owner_draft_materials_isolated(
            altered,e,t,z,"20261101")
        self.assertEqual(report,unavailable())

    def test_no_valid_optional_race_never_invents_zero_materials(self):
        p,e,t,z=self.samples()
        broken=copy.deepcopy(e)
        for row in broken:
            row["horse_number"]="INVALID"
        diagnostic={}
        partial=observe_owner_draft_materials_isolated(
            p,broken,t,z,"20261101",diagnostics=diagnostic)
        self.assertEqual(partial,unavailable())
        self.assertEqual(diagnostic["wholeDayCode"],"source_coverage")
        self.assertEqual(diagnostic["verifiedRaces"],0)
        self.assertEqual(diagnostic["rejectedRaces"],2)

    def test_conflicting_roster_fails_without_graded_fallback(self):
        p,e,t,z=self.samples()
        bad=copy.deepcopy(e)
        bad.append(copy.deepcopy(bad[0]))
        with self.assertRaises(CoverageError):
            observe_owner_draft_materials(p,bad,t,z,"20261101")
        empty=unavailable()
        self.assertEqual(empty["races"],[])
        self.assertEqual(empty["gradedNewFactors"],0)
        self.assertFalse(empty["officialJraVerified"])

if __name__=="__main__":
    unittest.main()
