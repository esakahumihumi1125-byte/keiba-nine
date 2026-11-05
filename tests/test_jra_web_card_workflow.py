"""JRA release timing and owner-local manual race coverage UI regression tests."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jra_web_card_workflow import HTML, JS, CSS
from private_service import create_app
from test_private_service import SETTINGS, call


class JRAWebCardWorkflowTests(unittest.TestCase):
    def test_owner_only_static_navigation(self):
        app = create_app(SETTINGS)
        with (patch("private_service.discover_official_pdf_links") as index,
              patch("private_service.fetch_race_program") as paid):
            page = call(app, "/jrdb-mail-local")
            script = call(app, "/jra-web-card.js")
            stylesheet = call(app, "/jrdb-mail-local.css")
        self.assertEqual(page["status"], "200 OK")
        self.assertEqual(script["status"], "200 OK")
        self.assertEqual(stylesheet["status"], "200 OK")
        self.assertIn("no-store", page["headers"]["Cache-Control"])
        self.assertIn("text/javascript", script["headers"]["Content-Type"])
        self.assertIn(b'id="jraPrestartSection"', page["body"])
        self.assertIn(b'id="jraRaceChecklist"', page["body"])
        self.assertIn(b'/jra-web-card.js', page["body"])
        self.assertIn(b'https://www.jra.go.jp/keiba/', page["body"])
        self.assertIn(b"jraRaceChecklist", script["body"])
        self.assertIn("grid-template-columns", stylesheet["body"].decode())
        index.assert_not_called()
        paid.assert_not_called()
        self.assertEqual(call(app, "/jra-web-card.js", auth="")["status"], "401 Unauthorized")
        self.assertEqual(call(app, "/jrdb-mail-local", auth="")["status"], "303 See Other")
        self.assertEqual(call(app, "/jra-web-card.js", method="POST")["status"], "404 Not Found")

    def test_local_progress_and_no_false_official_verification(self):
        self.assertIn("通常の馬番付き出馬表", JS)
        self.assertIn("前日", HTML)
        self.assertIn("発表目安", JS)
        self.assertIn("sourceMark", JS)
        self.assertIn("馬名差異あり", JS)
        self.assertIn("未入力", JS)
        self.assertIn("本人の手入力", HTML)
        self.assertIn("公式確認済みの件数ではない", JS)
        self.assertIn("https://www.jra.go.jp/keiba/", HTML)
        self.assertNotIn("fetch(", JS)
        self.assertNotIn("XMLHttpRequest", JS)
        self.assertNotIn("innerHTML", JS)
        self.assertNotIn("localStorage.setItem", JS)
        self.assertNotIn("JRDB_API_KEY", JS)
        self.assertNotIn("purchase", JS.lower())


if __name__ == "__main__":
    unittest.main()
