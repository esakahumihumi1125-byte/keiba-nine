"""Owner-only runner material endpoint and iPhone UI tests (no real JRDB)."""
import json
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import call, SETTINGS, AUTH
from test_jrdb_selected_race_readiness import records, NOW


class RunnerResearchPrivateUITests(unittest.TestCase):
    def run_selected(self, private=True, auth=True):
        config = {
            **SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
            "JRDB_API_KEY": "synthetic-app", "JRDB_AUTH_KEY": "synthetic-user",
            "KEIBA_RENDER_PRIVATE_ONLY": "1" if private else "0",
            "KEIBA_RENDER_PREVIEW_ONLY": "0",
        }
        app = create_app(config)
        p, e, t, z, h = records()
        with ExitStack() as stack:
            mocks = {
                "fetch_race_program": p,
                "fetch_horse_entries": e,
                "fetch_training_analysis": t,
                "fetch_recent_runs": z,
                "fetch_venue_conditions": h,
            }
            for name, content in mocks.items():
                stack.enter_context(patch("private_service." + name,
                                          return_value=content))
            stack.enter_context(patch("private_service._now_in_jst",
                                      return_value=NOW))
            return call(app, "/api/jrdb/selected-readiness",
                        auth=AUTH if auth else "",
                        QUERY_STRING="date=20261101&track=東京&race=1")

    def test_authenticated_private_render_receives_derived_runner_material(self):
        reply = self.run_selected(private=True)
        self.assertEqual(reply["status"], "200 OK")
        doc = json.loads(reply["body"])
        detail = doc["runnerResearch"]
        self.assertTrue(detail["privateOwnerOnly"])
        self.assertEqual(detail["runnerCount"], doc["observedEntries"])
        self.assertFalse(detail["overallRankReady"])
        self.assertFalse(detail["predictionReady"])
        self.assertFalse(detail["bettingReady"])
        self.assertIn("no-store", reply["headers"]["Cache-Control"])
        for secret in ("synthetic-user", "synthetic-app",
                       "horse_id", "racekey", "idm", "oikirisisu"):
            self.assertNotIn(secret, reply["body"].decode())

    def test_nonprivate_configuration_stays_aggregate_only(self):
        reply = self.run_selected(private=False)
        self.assertEqual(reply["status"], "200 OK")
        self.assertNotIn("runnerResearch", json.loads(reply["body"]))

    def test_unauthenticated_request_cannot_read_runner_material(self):
        reply = self.run_selected(private=True, auth=False)
        self.assertTrue(reply["status"].startswith("401"))
        self.assertNotIn("runnerResearch", reply["body"].decode())

    def test_mobile_screen_has_draft_panel_not_betting_confirmation(self):
        app = create_app(SETTINGS)
        html = call(app, "/")["body"].decode()
        js = call(app, "/app.js")["body"].decode()
        css = call(app, "/app.css")["body"].decode()
        self.assertIn('id="ownerRunnerResearch"', html)
        self.assertIn('showOwnerRunnerResearch(data.runnerResearch,selected)', js)
        self.assertIn('target.replaceChildren()', js)
        self.assertIn('総合ランク・勝率・馬券の買い目ではありません', js)
        self.assertIn('.grade-S', css)
        self.assertIn('.grade-A', css)
        self.assertNotIn("innerHTML", js)


if __name__ == "__main__":
    unittest.main()
