"""Configuration-only tests; no network, paid services, or real credentials."""
import os
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

CONFIG = Path(__file__).resolve().parents[1] / "deploy" / "gunicorn.conf.py"

class DeployConfigTests(unittest.TestCase):
    def test_local_http_exception_is_rejected(self):
        with patch.dict(os.environ, {"KEIBA_ALLOW_LOCAL_HTTP": "1"}):
            with self.assertRaises(RuntimeError):
                runpy.run_path(str(CONFIG))

    def test_backend_and_proxy_trust_are_local_only(self):
        with patch.dict(os.environ, {"KEIBA_ALLOW_LOCAL_HTTP": "0"}):
            cfg = runpy.run_path(str(CONFIG))
        self.assertEqual(cfg["bind"], "127.0.0.1:8765")
        self.assertEqual(cfg["forwarded_allow_ips"], "127.0.0.1,::1")
        self.assertEqual(cfg["secure_scheme_headers"], {"X-FORWARDED-PROTO": "https"})
        self.assertIsNone(cfg["accesslog"])
        self.assertFalse(cfg["capture_output"])
        self.assertTrue((Path(cfg["chdir"]) / "private_service.py").is_file())
        self.assertEqual(cfg["wsgi_app"], "private_service:create_app()")

if __name__ == "__main__":
    unittest.main()
