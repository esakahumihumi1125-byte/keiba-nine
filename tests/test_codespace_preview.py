"""Codespaces preview tests; they do not start a server or print a password."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from codespace_preview import build_preview_settings
from private_service import create_app


class CodespacesPreviewTests(unittest.TestCase):
    def test_private_port_config_and_no_automatic_live_start(self):
        cfg = json.loads((ROOT / ".devcontainer" / "devcontainer.json")
                         .read_text(encoding="utf-8"))
        self.assertEqual(cfg["portsAttributes"]["8765"]["visibility"], "private")
        self.assertIn(8765, cfg["forwardPorts"])
        self.assertEqual(cfg["containerEnv"]["JRDB_PRIVATE_ENABLED"], "0")
        self.assertNotIn("JRDB_API_KEY", json.dumps(cfg))
        self.assertNotIn("JRDB_AUTH_KEY", json.dumps(cfg))
        self.assertNotIn("KEIBA_OWNER_PASSWORD", json.dumps(cfg))
        self.assertIn("unittest", cfg["postCreateCommand"])
        self.assertNotIn("codespace_preview.py", cfg["postCreateCommand"])

    def test_never_allowed_in_actions(self):
        with self.assertRaises(RuntimeError):
            build_preview_settings({"CODESPACES": "true",
                                    "GITHUB_ACTIONS": "true"})
        with self.assertRaises(RuntimeError):
            build_preview_settings({"CODESPACES": "false"})

    def test_disabled_live_api_even_if_environment_contains_keys(self):
        env = {"CODESPACES": "true", "JRDB_PRIVATE_ENABLED": "1",
               "JRDB_API_KEY": "PRIVATE-APP-KEY",
               "JRDB_AUTH_KEY": "PRIVATE-AUTH-KEY",
               "KEIBA_OWNER_PASSWORD": "NOT-THIS-OLD-PASSWORD"}
        settings = build_preview_settings(env)
        self.assertEqual(settings["JRDB_PRIVATE_ENABLED"], "0")
        self.assertEqual(settings["JRDB_API_KEY"], "")
        self.assertEqual(settings["JRDB_AUTH_KEY"], "")
        self.assertEqual(settings["KEIBA_ALLOW_LOCAL_HTTP"], "1")
        self.assertEqual(settings["KEIBA_OWNER_USERNAME"], "owner")
        self.assertNotEqual(settings["KEIBA_OWNER_PASSWORD"], env["KEIBA_OWNER_PASSWORD"])
        self.assertGreaterEqual(len(settings["KEIBA_OWNER_PASSWORD"]), 32)
        create_app(settings)

    def test_each_preview_has_unique_owner_password(self):
        env = {"CODESPACES": "true"}
        a, b = build_preview_settings(env), build_preview_settings(env)
        self.assertNotEqual(a["KEIBA_OWNER_PASSWORD"], b["KEIBA_OWNER_PASSWORD"])


if __name__ == "__main__":
    unittest.main()
