"""Render-only authenticated PREVIEW. Never enable paid JRDB on this service.

Render terminates HTTPS at its edge and forwards X-Forwarded-Proto to this
process. Only Render's edge may reach the public container port. Never reuse
this config behind a general-purpose reverse proxy with direct client access.
"""
import os
from pathlib import Path

if os.environ.get("RENDER") != "true" or os.environ.get("RENDER_SERVICE_TYPE") != "web":
    raise RuntimeError("This config is for a Render web service only")
if os.environ.get("KEIBA_RENDER_PREVIEW_ONLY") != "1":
    raise RuntimeError("Render must run in explicitly opted-in preview-only mode")
if os.environ.get("KEIBA_ALLOW_LOCAL_HTTP") == "1":
    raise RuntimeError("Render preview cannot allow insecure HTTP")
if any(os.environ.get(key) == "1" for key in (
        "JRDB_PRIVATE_ENABLED", "KEIBA_HISTORY_ENABLED",
        "KEIBA_MANUAL_REFERENCE_ENABLED")):
    raise RuntimeError("No live/private provider integration in Render preview")
if any(os.environ.get(key) for key in ("JRDB_API_KEY", "JRDB_AUTH_KEY")):
    raise RuntimeError("Do not supply paid API credentials to Render preview")

raw_port = os.environ.get("PORT", "10000")
if not raw_port.isascii() or not raw_port.isdecimal() or not 1024 <= int(raw_port) <= 65535:
    raise RuntimeError("Invalid Render port")

chdir = str(Path(__file__).resolve().parents[1] / "scripts")
bind = "0.0.0.0:" + raw_port
workers = 1
timeout = 60
graceful_timeout = 20
accesslog = None
errorlog = "-"
loglevel = "warning"
capture_output = False
# Render itself sets FORWARDED_ALLOW_IPS="*" in Python services. That is
# safe here only because the container port is reached through Render's edge.
# Never use this setting on a directly internet-reachable Gunicorn process.
forwarded_allow_ips = "*"
secure_scheme_headers = {"X-FORWARDED-PROTO": "https"}
wsgi_app = "private_service:create_app()"
