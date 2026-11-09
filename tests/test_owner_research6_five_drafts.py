"""Synthetic only: no JRDB/JRA requests, no result-based ticket hindsight."""
import copy
import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jrdb_coverage import CoverageError
from evaluation_policy import POINTS
from owner_new_weight_five_research import KEYS, WEIGHTS
from owner_research6_five_drafts import build_research6_five_drafts, VERSION

JST = timezone(timedelta(hours=9))
DAY = "20990101"
BANDS = [
    ("S", "S"), ("S", "A"), ("A", "S"), ("A", "A"),
    ("B", "S"), ("B", "A"), ("C", "S"),
]


def materials(bands=None):
    bands = BANDS if bands is None else bands
    horses = []
    for n, (training, recent) in enumerate(bands, 1):
        grades = {
            "training": training, "course_distance": "S", "pace": "S",
            "ground": "S", "recent": recent,
        }
        missing = [k for k in KEYS if grades[k] == "未評価"]
        raw = None if missing else sum(
            WEIGHTS[k] * POINTS[grades[k]] for k in KEYS)
        horses.append({
            "number": n, "bands": grades,
            "missing": missing,
            "observedFactorCount": 5 - len(missing),
            "rawThirdPoints": raw,
            "evidenceScore79": None if raw is None else round(raw / 3, 2),
            "formalScore100": None, "formalGrade": "未評価",
            "formalRank": None, "scoreIsCalibrated": False,
            "bettingReady": False,
        })
    groups = {}
    for h in horses:
        if h["rawThirdPoints"] is not None:
            groups.setdefault(h["rawThirdPoints"], []).append(h["number"])
    race = {
        "track": "東京", "race": 1, "runnerCount": len(horses),
        "horses": horses,
        "completeObserved": sum(h["rawThirdPoints"] is not None for h in horses),
        "missingByFactor": {
            k: sum(h["bands"][k] == "未評価" for h in horses) for k in KEYS
        },
        "comparisonGroups": [
            {"rawThirdPoints": score, "numbers": sorted(groups[score])}
            for score in sorted(groups, reverse=True)
        ],
        "unassessedNumbers": sorted(
            h["number"] for h in horses if h["rawThirdPoints"] is None),
        "comparisonIsFormalRank": False,
        "researchOnly": True, "formalGradeReady": False,
        "trifectaReady": False,
    }
    study = {
        "version": "owner-new-weight-five-research-1",
        "policyVersion": "research-6", "sourcePolicyVersion": "research-5",
        "factorWeights": dict(WEIGHTS), "observedWeightTotal": 79,
        "factorGradesVerified": 0, "formalScoreReady": False,
        "overallPredictionReady": False, "officialJraVerified": False,
        "bettingReady": False, "autoPurchase": False,
        "researchOnly": True, "privateOwnerOnly": True,
        "historicalBandsNotCalibrated": True,
        "resultVerified": False, "extraProviderCalls": 0,
        "raceCount": 1, "races": [race],
    }
    programme = [{
        "racedate": DAY, "racekey": "0526ff01",
        "racecourse_cd": "05", "post_time": "1200",
        "headcount": len(horses),
    }]
    return programme, study


def calculate(p=None, s=None, now=None):
    if p is None or s is None:
        p, s = materials()
    if now is None:
        now = datetime(2099, 1, 1, 9, 0, tzinfo=JST)
    return build_research6_five_drafts(p, s, DAY, now=now)


class OwnerFiveDraftTests(unittest.TestCase):
    def test_seven_complete_distinct_bands_generate_exact_40(self):
        p, s = materials()
        original = copy.deepcopy((p, s))
        out = calculate(p, s)
        self.assertEqual((p, s), original)
        self.assertEqual(out["version"], VERSION)
        self.assertEqual(out["policyVersion"], "research-6")
        self.assertEqual(out["researchFactorWeight"], 79)
        self.assertEqual(out["remainingUnassessedWeight"], 21)
        self.assertEqual((out["draftCount"], out["holdCount"]), (1, 0))
        r = out["races"][0]
        self.assertEqual(r["status"], "five_factor_research_draft")
        self.assertEqual((r["first"], r["second"], r["third"]),
                         ([1, 2], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5, 6, 7]))
        self.assertEqual(r["points"], 40)
        self.assertEqual(r["amountYen"], 4000)
        self.assertEqual(len(r["tickets"]), len({tuple(x) for x in r["tickets"]}))
        self.assertEqual(r["rankedResearch"][0]["research79"], 79.0)
        self.assertEqual(r["rankedResearch"][0]["comparisonRank"], 1)
        for flag in ("officialJraVerified", "overallPredictionReady",
                     "bettingReady", "autoPurchase", "actualPurchase",
                     "changesExistingReceipts", "changesExistingTickets",
                     "changesExistingRoi"):
            self.assertFalse(out[flag])
        self.assertEqual(out["extraProviderCalls"], 0)
        for text in ("racekey", "horse_id", "sire_name", "sourceId",
                     "password", "payout", "signedReceipt"):
            self.assertNotIn(text, repr(out))

    def test_old_research_scores_not_treated_as_formal_or_winners(self):
        p, s = materials()
        r = calculate(p, s)["races"][0]
        self.assertTrue(r["researchOnly"])
        self.assertFalse(r["officialJraVerified"])
        self.assertFalse(r["overallPredictionReady"])
        self.assertFalse(r["bettingReady"])
        self.assertTrue(all(x["research79"] <= 79 for x in r["rankedResearch"]))
        self.assertEqual(r["reason"], "unverified_five_factor_hypotheses")

    def test_missing_band_and_tied_cutoff_hold_without_guessing(self):
        p, s = materials([("S","S"),("S","A"),("未評価","S"),
                          ("A","A"),("B","S"),("B","A"),("C","S")])
        r = calculate(p, s)["races"][0]
        self.assertEqual(r["status"], "hold")
        self.assertEqual(r["reason"], "incomplete_five_factors")
        self.assertEqual((r["tickets"], r["rankedResearch"], r["points"]),
                         ([], [], 0))
        p, s = materials([("S","S")] * 7)
        r = calculate(p, s)["races"][0]
        self.assertEqual(r["status"], "hold")
        self.assertEqual(r["reason"], "tied_cutoff")
        self.assertEqual(r["tickets"], [])

    def test_non_future_races_never_reconstruct_research_tickets(self):
        p, s = materials()
        for now in (datetime(2099,1,1,12,0,tzinfo=JST),
                    datetime(2099,1,2,7,0,tzinfo=JST)):
            r = calculate(p, s, now)["races"][0]
            self.assertEqual(r["reason"], "past_provisional_off")
            self.assertEqual(r["tickets"], [])
            self.assertEqual(r["rankedResearch"], [])
        p[0]["post_time"] = None
        r = calculate(p, s)["races"][0]
        self.assertEqual(r["reason"], "missing_provisional_off")
        self.assertEqual(r["tickets"], [])

    def test_unverified_runner_count_never_yields_tickets(self):
        p, s = materials()
        p[0]["headcount"] = None
        r = calculate(p, s)["races"][0]
        self.assertEqual(r["reason"], "runner_count_unconfirmed")
        p[0]["headcount"] = 6
        r = calculate(p, s)["races"][0]
        self.assertEqual(r["reason"], "runner_count_unconfirmed")

    def test_forged_study_and_wrong_roster_rejected(self):
        cases = [
            lambda p,s: s.update(policyVersion="research-5"),
            lambda p,s: s["factorWeights"].update(pace=20),
            lambda p,s: s.update(officialJraVerified=True),
            lambda p,s: s["races"][0]["horses"][0].update(rawThirdPoints=100),
            lambda p,s: s["races"][0]["horses"][0].update(formalScore100=79),
            lambda p,s: s["races"][0]["horses"][0]["bands"].update(recent="B"),
            lambda p,s: s["races"][0]["horses"][0].update(number=21),
            lambda p,s: s["races"][0].update(comparisonGroups=[]),
            lambda p,s: s["races"][0].update(completeObserved=0),
            lambda p,s: s["races"][0].update(unassessedNumbers=[1]),
            lambda p,s: s["races"][0].update(runnerCount=99),
            lambda p,s: p[0].update(racekey="0926ff01"),
            lambda p,s: p[0].update(racedate="20990102"),
            lambda p,s: p[0].update(racecourse_cd="09"),
        ]
        for change in cases:
            p, s = materials()
            change(p, s)
            with self.subTest(change=repr(change)), self.assertRaises(CoverageError):
                calculate(p, s)


if __name__ == "__main__":
    unittest.main()
