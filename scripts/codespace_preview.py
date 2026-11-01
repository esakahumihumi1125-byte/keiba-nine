"""Start a safe, synthetic-only private WSGI preview within GitHub Codespaces.

Run explicitly from the Codespaces terminal, not via GitHub Actions.
No JRDB credentials, paid data, model calls, writes or user-record changes.
"""
import os
import secrets
from wsgiref.simple_server import make_server, WSGIRequestHandler

from private_service import create_app

PORT = 8765


def build_preview_settings(environ=None):
    current = dict(os.environ if environ is None else environ)
    if current.get("CODESPACES") != "true" or current.get("GITHUB_ACTIONS") == "true":
        raise RuntimeError("GitHub Codespaces preview only (never GitHub Actions)")
    # Never enable JRDB while using a development-only HTTP loopback exception.
    current["JRDB_PRIVATE_ENABLED"] = "0"
    current["JRDB_API_KEY"] = ""
    current["JRDB_AUTH_KEY"] = ""
    current["KEIBA_ALLOW_LOCAL_HTTP"] = "1"
    current["KEIBA_OWNER_USERNAME"] = "owner"
    current["KEIBA_OWNER_PASSWORD"] = secrets.token_urlsafe(36)
    return current


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        # Never print authenticated request paths or HTTP authorization.
        pass


def main():
    settings = build_preview_settings()
    app = create_app(settings)
    print("KEIBA NINE private Codespaces PREVIEW (not a real JRDB connection).")
    print("Before opening port 8765, verify Ports > Port visibility = Private.")
    print("Login username: owner")
    print("One-time preview password: " + settings["KEIBA_OWNER_PASSWORD"])
    print("This password is shown only in your own Codespaces terminal.")
    print("Preview server: http://127.0.0.1:8765")
    print("No real JRDB data, AI predictions, or public site updates are enabled.", flush=True)
    with make_server("127.0.0.1", PORT, app, handler_class=QuietHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
