"""No-live-data checks for optional Render owner preview deployment."""
import os
import runpy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "deploy" / "render-gunicorn.py"
MANIFEST = ROOT / "render.yaml"
REQUIREMENTS = ROOT / "deploy" / "render-requirements.txt"
WORKFLOW = ROOT / ".github" / "workflows" / "private-service-check.yml"


class RenderPreviewSafetyTests(unittest.TestCase):
    def env(self, **changed):
        base = {
            "RENDER": "true",
            "RENDER_SERVICE_TYPE": "web",
            "KEIBA_RENDER_PREVIEW_ONLY": "1",
            "KEIBA_ALLOW_LOCAL_HTTP": "0",
            "JRDB_PRIVATE_ENABLED": "0",
            "KEIBA_HISTORY_ENABLED": "0",
            "KEIBA_MANUAL_REFERENCE_ENABLED": "0",
            "PORT": "10000",
        }
        base.update(changed)
        return base

    def test_expected_secure_render_preview_settings(self):
        with patch.dict(os.environ, self.env(), clear=True):
            setting = runpy.run_path(str(CONFIG))
        self.assertEqual(setting["bind"], "0.0.0.0:10000")
        self.assertEqual(setting["workers"], 1)
        self.assertIsNone(setting["accesslog"])
        self.assertEqual(setting["forwarded_allow_ips"], "*")
        self.assertEqual(setting["secure_scheme_headers"],
                         {"X-FORWARDED-PROTO": "https"})
        self.assertEqual(setting["wsgi_app"], "private_service:create_app()")
        self.assertEqual(Path(setting["chdir"]).name, "scripts")

    def test_production_or_paid_configuration_fails_closed(self):
        values = [
            {"RENDER": "false"},
            {"RENDER_SERVICE_TYPE": "static"},
            {"KEIBA_RENDER_PREVIEW_ONLY": "0"},
            {"KEIBA_ALLOW_LOCAL_HTTP": "1"},
            {"JRDB_PRIVATE_ENABLED": "1"},
            {"KEIBA_HISTORY_ENABLED": "1"},
            {"KEIBA_MANUAL_REFERENCE_ENABLED": "1"},
            {"JRDB_API_KEY": "FAKE-DO-NOT-LOG"},
            {"JRDB_AUTH_KEY": "FAKE-DO-NOT-LOG"},
            {"PORT": "800"},
            {"PORT": "65536"},
            {"PORT": "invalid"},
        ]
        for setting in values:
            with self.subTest(setting=list(setting)):
                with patch.dict(os.environ, self.env(**setting), clear=True):
                    with self.assertRaises(RuntimeError) as error:
                        runpy.run_path(str(CONFIG))
                self.assertNotIn("FAKE-DO-NOT-LOG", str(error.exception))

    def test_manifest_never_publishes_secrets_or_enables_paid_data(self):
        content = MANIFEST.read_text(encoding="utf-8")
        self.assertIn('plan: free', content)
        self.assertIn('runtime: python', content)
        self.assertIn('autoDeployTrigger: "commit"', content)
        self.assertIn('notification delivery still depends on Render GitHub App', content)
        self.assertIn('gunicorn --config deploy/render-gunicorn.py', content)
        self.assertIn('key: KEIBA_OWNER_PASSWORD\n        generateValue: true', content)
        self.assertIn('key: JRDB_PRIVATE_ENABLED\n        value: "0"', content)
        self.assertIn('key: KEIBA_HISTORY_ENABLED\n        value: "0"', content)
        self.assertIn('key: KEIBA_MANUAL_REFERENCE_ENABLED\n        value: "0"', content)
        self.assertIn('key: GUNICORN_CMD_ARGS\n        value: ""', content)
        for forbidden in ("JRDB_API_KEY", "JRDB_AUTH_KEY",
                          "KEIBA_OWNER_PASSWORD\n        value:",
                          "KEIBA_OWNER_PASSWORD\n        sync: false",
                          "KEIBA_ALLOW_LOCAL_HTTP\n        value: \"1\""):
            self.assertNotIn(forbidden, content)

    def test_main_ci_is_not_path_filtered(self):
        # Run checks independently for each main update, even if the live Render
        # service currently uses On Commit rather than CI-gated deploys.
        workflow = WORKFLOW.read_text(encoding="utf-8")
        triggers = workflow.split("permissions:", 1)[0]
        self.assertIn("  push:\n    branches: [main]", triggers)
        self.assertIn("  pull_request:\n    branches: [main]", triggers)
        self.assertIn("  workflow_dispatch:", triggers)
        self.assertNotIn("    paths:", triggers)
        self.assertNotIn("    paths-ignore:", triggers)

    def test_only_pinned_single_wsgi_requirement(self):
        packages = REQUIREMENTS.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(packages, ["gunicorn==26.2.0"])


if __name__ == "__main__":
    unittest.main()
