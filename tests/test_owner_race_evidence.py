"""Synthetic owner-private race rationale checks."""
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_race_evidence import decode_evidence, EvidenceError, SCHEMA, ENV_KEY
from private_service import create_app
from test_private_service import SETTINGS, call

def fixture():
    tracks=("東京","京都","福島")
    rows=[{"track":t,"race":r,
           "lead":[{"number":2,"name":"架空の馬","reason":"前日の順位と脚質からの仮説。"}],
           "pace":"先行構成から展開を想定。","secondThird":"上位候補を再確認。",
           "singles":"フォーメーションを減らした比較案。",
           "risk":"当日の馬場・取消と調教・近走の全頭照合は未完了。",
           "verifiedFacts":[],
           "coverage":{"officialPastRuns":False,"publicTrainingChecked":False,
           "officialPedigreeChecked":False,"officialEntryCompared":False,
           "allHorseTrainingChecked":False,"dayOfScratchesAndTrackChecked":False}}
          for t in tracks for r in range(1,13)]
    return {"schema":SCHEMA,"sourceKind":"owner-editorial-limited-evidence",
            "date":"2026-11-08","races":rows}

class RaceEvidenceTests(unittest.TestCase):
    def test_owner_endpoint_returns_rationale_without_buying(self):
        app=create_app({**SETTINGS,ENV_KEY:json.dumps(fixture(),ensure_ascii=False)})
        self.assertEqual(call(app,"/api/owner-race-evidence",auth="")["status"],"401 Unauthorized")
        self.assertEqual(call(app,"/api/owner-race-evidence",
             HTTP_X_KEIBA_REQUEST="")["status"],"403 Forbidden")
        self.assertEqual(call(app,"/api/owner-race-evidence",method="POST")["status"],"404 Not Found")
        r=call(app,"/api/owner-race-evidence")
        self.assertEqual(r["status"],"200 OK")
        data=json.loads(r["body"])["evidence"]
        self.assertEqual(len(data["races"]),36)
        self.assertFalse(data["finalVerified"])
        self.assertFalse(data["predictionRevised"])
        self.assertIn("no-store",r["headers"]["Cache-Control"])

    def test_incomplete_and_uncertain_source_does_not_claim_final(self):
        data=fixture()
        for change in (
            lambda d:d["races"][0]["coverage"].update(dayOfScratchesAndTrackChecked=True),
            lambda d:d["races"][0]["coverage"].update(allHorseTrainingChecked=True),
            lambda d:d["races"][0].update(race=13),
            lambda d:d["races"].pop(),
            lambda d:d["races"][0].update(risk="<script>bad</script>")
        ):
            current=json.loads(json.dumps(data,ensure_ascii=False))
            change(current)
            with self.assertRaises(EvidenceError):
                decode_evidence(json.dumps(current,ensure_ascii=False))
        self.assertEqual(json.loads(call(create_app(SETTINGS),
          "/api/owner-race-evidence")["body"]),{"available":False,"evidence":None})
if __name__=="__main__":
    unittest.main()
