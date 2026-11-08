"""Synthetic startup checks for the separate JRDB owner service; no network."""
import os
import runpy
import unittest
from pathlib import Path
from unittest.mock import patch

CONFIG = str(Path(__file__).resolve().parents[1] / "deploy" / "render-owner-private.py")
BASE = {
    "RENDER": "true",
    "RENDER_SERVICE_TYPE": "web",
    "KEIBA_RENDER_PRIVATE_ONLY": "1",
    "KEIBA_RENDER_PREVIEW_ONLY": "0",
    "KEIBA_ALLOW_LOCAL_HTTP": "0",
    "JRDB_PRIVATE_ENABLED": "0",
    "KEIBA_OWNER_USERNAME": "owner",
    "KEIBA_OWNER_PASSWORD": "synthetic-Pass-Only-For-Unit-Tests-123abcXYZ@!",
}


class RenderOwnerPrivateTests(unittest.TestCase):
    def run_config(self, changes=None):
        env = dict(BASE)
        env.update(changes or {})
        with patch.dict(os.environ, env, clear=True):
            return runpy.run_path(CONFIG)

    def test_disabled_stage_is_valid_and_has_no_jrdb_keys(self):
        values = self.run_config()
        self.assertEqual(values["wsgi_app"], "private_service:create_app()")
        self.assertIsNone(values["accesslog"])
        self.assertIn("X-FORWARDED-PROTO", values["secure_scheme_headers"])

    def test_profile_rejects_preview_and_insecure_or_unscoped_setup(self):
        cases = [
            {"KEIBA_RENDER_PRIVATE_ONLY": "0"},
            {"KEIBA_RENDER_PREVIEW_ONLY": "1"},
            {"KEIBA_ALLOW_LOCAL_HTTP": "1"},
            {"GITHUB_ACTIONS": "true"},
            {"KEIBA_HISTORY_ENABLED": "1"},
            {"KEIBA_MANUAL_REFERENCE_ENABLED": "1"},
            {"KEIBA_OWNER_PASSWORD": ""},
            {"PORT": "bad"},
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(RuntimeError):
                self.run_config(changes)

    def test_live_requires_both_secrets_and_expected_provider_host(self):
        good = {"JRDB_PRIVATE_ENABLED": "1",
                "JRDB_API_KEY": "synthetic-app",
                "JRDB_AUTH_KEY": "synthetic-user",
                "JRDB_API_BASE_URL": "https://api.bigtime.world/v1"}
        for key in ("JRDB_API_KEY", "JRDB_AUTH_KEY", "JRDB_API_BASE_URL"):
            bad = dict(good)
            bad.pop(key)
            with self.subTest(missing=key), self.assertRaises(RuntimeError):
                self.run_config(bad)
        self.run_config(good)

    def test_invalid_live_flag_rejected(self):
        with self.assertRaises(RuntimeError):
            self.run_config({"JRDB_PRIVATE_ENABLED": "true"})


if __name__ == "__main__":
    unittest.main()
