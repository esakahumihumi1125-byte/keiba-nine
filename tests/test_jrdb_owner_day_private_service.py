"""Owner-only day research HTTP and mobile UI guards. No JRDB network."""
import json
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import call, AUTH, SETTINGS
from test_jrdb_training_hypothesis import setup as workouts
from test_jrdb_recent_hypothesis import fixture as past_races


class DayResearchHTTPTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            **SETTINGS, "JRDB_PRIVATE_ENABLED": "1",
            "KEIBA_RENDER_PRIVATE_ONLY": "1",
            "KEIBA_RENDER_PREVIEW_ONLY": "0",
            "JRDB_API_KEY": "synthetic-app",
            "JRDB_AUTH_KEY": "synthetic-key",
        }
        self.app = create_app(self.settings)

    def fetched(self):
        p, e, t = workouts()
        _, _, z = past_races()
        with ExitStack() as stack:
            for name, value in (
                ("fetch_race_program", p),
                ("fetch_horse_entries", e),
                ("fetch_training_analysis", t),
                ("fetch_recent_runs", z),
            ):
                stack.enter_context(patch("private_service." + name, return_value=value))
            return call(self.app, "/api/jrdb/day-runner-research",
                        QUERY_STRING="date=20261101", auth=AUTH)

    def test_one_click_fetches_four_sources_and_returns_two_factor_research(self):
        reply = self.fetched()
        self.assertEqual(reply["status"], "200 OK")
        body = json.loads(reply["body"])
        self.assertEqual(body["raceCount"], 2)
        self.assertEqual(body["researchAvailableCount"], 2)
        self.assertEqual(body["sourceReadCount"], 4)
        self.assertFalse(body["predictionReady"])
        self.assertFalse(body["bettingReady"])
        for private in ("synthetic-app", "synthetic-key", "horse_id",
                        "racekey", "idm", "oikirisisu", "horse_name"):
            self.assertNotIn(private, reply["body"].decode())

    def test_owner_login_and_extra_header_required(self):
        for change in ({"auth": ""}, {"HTTP_X_KEIBA_REQUEST": ""},
                       {"HTTP_SEC_FETCH_SITE": "cross-site"}):
            with self.subTest(change=change):
                reply = call(
                    self.app, "/api/jrdb/day-runner-research",
                    QUERY_STRING="date=20261101",
                    **change
                )
                self.assertIn(reply["status"].split()[0], ("401", "403"))

    def test_general_preview_never_serves_private_day_research(self):
        preview = create_app(SETTINGS)
        self.assertEqual(
            call(preview, "/owner-jrdb-day-research")["status"], "404 Not Found")
        self.assertNotIn(
            '/owner-jrdb-day-research',
            call(preview, "/")["body"].decode()
        )
        login = call(self.app, "/login", auth="")["body"].decode()
        self.assertIn("keiba-nine-owner-jrdb", login)
        self.assertNotIn("keiba-nine-owner-preview", login)

    def test_mobile_page_and_private_menu_are_available(self):
        page = call(self.app, "/owner-jrdb-day-research")
        js = call(self.app, "/owner-jrdb-day-research.js")
        css = call(self.app, "/owner-jrdb-day-research.css")
        self.assertEqual(page["status"], "200 OK")
        self.assertEqual(js["status"], "200 OK")
        self.assertEqual(css["status"], "200 OK")
        self.assertIn("この日の全Rをまとめて分析", page["body"].decode())
        self.assertIn("/api/jrdb/day-runner-research", js["body"].decode())
        self.assertIn('id="venueFilters"', page["body"].decode())
        self.assertIn('id="venueStats"', page["body"].decode())
        self.assertIn("aria-pressed", js["body"].decode())
        self.assertIn("byVenue.keys()", js["body"].decode())
        self.assertIn("showVenue('')", js["body"].decode())
        self.assertIn("本人専用", call(self.app, "/")["body"].decode())
        self.assertNotIn("innerHTML", js["body"].decode())
        self.assertNotIn("JRDB_API_KEY", js["body"].decode())


if __name__ == "__main__":
    unittest.main()
