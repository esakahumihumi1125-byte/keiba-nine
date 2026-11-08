"""Render configuration for a separate, owner-authenticated JRDB beta service.

This is NOT the existing preview. Do not put paid keys on the preview service.
Startup never contacts JRDB. Keys must be supplied by the owner via Render's
private Environment settings, never GitHub, chat, or client-side JavaScript.
"""
import os
from pathlib import Path

if os.environ.get("RENDER") != "true" or os.environ.get("RENDER_SERVICE_TYPE") != "web":
    raise RuntimeError("This profile is for a Render web service only")
if os.environ.get("KEIBA_RENDER_PRIVATE_ONLY") != "1":
    raise RuntimeError("Explicit private-owner deployment mode is required")
if os.environ.get("KEIBA_RENDER_PREVIEW_ONLY") == "1":
    raise RuntimeError("JRDB private service must never run as a preview")
if os.environ.get("KEIBA_ALLOW_LOCAL_HTTP") == "1":
    raise RuntimeError("Owner JRDB service requires HTTPS")
if os.environ.get("GITHUB_ACTIONS") == "true":
    raise RuntimeError("Never run a private JRDB service in GitHub Actions")
if os.environ.get("KEIBA_HISTORY_ENABLED") == "1":
    raise RuntimeError("Historical JRDB access needs a separate security review")
if os.environ.get("KEIBA_MANUAL_REFERENCE_ENABLED") == "1":
    raise RuntimeError("Manual reference collection needs a separate review")

# Start in connection-disabled mode. Confirm owner login and HTTPS first.
# The owner can then add secrets and opt into a SINGLE manual connection test.
enabled = os.environ.get("JRDB_PRIVATE_ENABLED", "0")
if enabled not in ("0", "1"):
    raise RuntimeError("JRDB_PRIVATE_ENABLED must be exactly 0 or 1")
if enabled == "1":
    if not os.environ.get("JRDB_API_KEY") or not os.environ.get("JRDB_AUTH_KEY"):
        raise RuntimeError("JRDB credentials must be configured privately")
    if os.environ.get("JRDB_API_BASE_URL") != "https://api.bigtime.world/v1":
        raise RuntimeError("Unexpected JRDB API base URL")

password = os.environ.get("KEIBA_OWNER_PASSWORD", "")
if len(password) < 32 or len(set(password)) < 12:
    raise RuntimeError("Set a strong generated KEIBA_OWNER_PASSWORD in Render")

port = os.environ.get("PORT", "10000")
if not port.isascii() or not port.isdecimal() or not 1024 <= int(port) <= 65535:
    raise RuntimeError("Invalid Render service port")

chdir = str(Path(__file__).resolve().parents[1] / "scripts")
bind = "0.0.0.0:" + port
workers = 1
timeout = 60
graceful_timeout = 20
accesslog = None
errorlog = "-"
loglevel = "warning"
capture_output = False
# Render's edge owns ingress; never use this on a directly exposed gunicorn port.
forwarded_allow_ips = "*"
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
wsgi_app = "private_service:create_app()"
