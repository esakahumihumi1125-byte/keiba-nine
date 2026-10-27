"""Same-host HTTPS reverse proxy only. Run from repository root."""
import os
from pathlib import Path

if os.environ.get("KEIBA_ALLOW_LOCAL_HTTP") == "1":
    raise RuntimeError("Local HTTP exception must be disabled for deployment")

chdir = str(Path(__file__).resolve().parents[1] / "scripts")
bind = "127.0.0.1:8765"
workers = 2
timeout = 45
graceful_timeout = 45
accesslog = None
errorlog = "-"
loglevel = "warning"
capture_output = False
# Only a local TLS proxy may set the scheme. Never trust arbitrary public peers.
forwarded_allow_ips = "127.0.0.1,::1"
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
wsgi_app = "private_service:create_app()"
