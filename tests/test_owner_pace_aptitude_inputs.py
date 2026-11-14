"""No-new-call, horse-anonymous /tky input-presence tests."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from owner_pace_aptitude_inputs import observe_pace_aptitude_input_counts, KEYS
from jrdb_coverage import CoverageError
from jrdb_program_preview import normalize_program_rows
from test_jrdb_day_materials_progress import fixture


class PaceAptitudeInputTests(unittest.TestCase):
    def sample(self):
        programme, entries, *_ = fixture()
        return normalize_program_rows(programme,"20261101"), entries

    def test_source_presence_not_a_graded_aptitude(self):
        programme, entries = self.sample()
        rows = copy.deepcopy(entries)
        first = rows[0]
        surface = programme[0]["surface"]
        source_field = "turf_tekisei_cd" if surface == "芝" else "dirt_tekisei_cd"
        first.update({
            "foottype_cd":"1", source_field:"2",
            "distance_aptitude_cd1":"3", "mudder_cd":"1",
            "ten_index":0, "pace_index":32.5,
            "agari_index":"-5.0", "ichi_index":18
        })
        pristine = copy.deepcopy((programme,rows))
        report = observe_pace_aptitude_input_counts(programme,rows,"20261101")
        self.assertEqual((programme,rows),pristine)
        target = next(r for r in report if r["track"]==programme[0]["track"])
        self.assertEqual(set(target["counts"]),set(KEYS))
        self.assertEqual(target["counts"],dict.fromkeys(KEYS,1))
        self.assertEqual(target["runnerCount"],2)
        for secret in ("racekey","horse_id","horse_number","32.5","-5.0",
                       "PRIVATE-SIRE","PRIVATE-JOCKEY"):
            self.assertNotIn(secret,repr(report))

    def test_other_surface_code_does_not_fake_current_surface(self):
        p,e=self.sample()
        rows=copy.deepcopy(e)
        surface=p[0]["surface"]
        wrong="dirt_tekisei_cd" if surface=="芝" else "turf_tekisei_cd"
        rows[0][wrong]="1"
        output=observe_pace_aptitude_input_counts(p,rows,"20261101")
        current=next(r for r in output if r["track"]==p[0]["track"])
        self.assertEqual(current["counts"]["surfaceAptitude"],0)

    def test_incomplete_and_odd_fields_do_not_assign_grades(self):
        p,e=self.sample()
        rows=copy.deepcopy(e)
        rows[0].update({
            "foottype_cd":"unknown","distance_aptitude_cd1":"  ",
            "mudder_cd":{},"ten_index":True,
            "pace_index":4,"agari_index":6,"ichi_index":2
        })
        report=observe_pace_aptitude_input_counts(p,rows,"20261101")
        current=next(r for r in report if r["track"]==p[0]["track"])
        self.assertEqual(current["counts"]["runningStyle"],0)
        self.assertEqual(current["counts"]["distanceAptitude"],0)
        self.assertEqual(current["counts"]["goingAptitude"],0)
        self.assertEqual(current["counts"]["paceIndices"],0)

    def test_duplicate_horse_or_unconfirmed_roster_fails_closed(self):
        p,e=self.sample()
        bad=copy.deepcopy(e);bad.append(copy.deepcopy(e[0]))
        with self.assertRaises(CoverageError):
            observe_pace_aptitude_input_counts(p,bad,"20261101")
        missing=copy.deepcopy(e);missing.pop(0)
        with self.assertRaises(CoverageError):
            observe_pace_aptitude_input_counts(p,missing,"20261101")


if __name__=="__main__":
    unittest.main()
