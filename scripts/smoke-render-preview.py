"""Boot an ephemeral Render-style preview process with synthetic credentials.

No external network, actual Render account, JRDB request or paid API.
Run after installing deploy/render-requirements.txt.
"""
import base64
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _request(url, headers):
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, err.read()


def main():
    port = _port()
    env = dict(os.environ)
    env.update({
        "RENDER": "true",
        "RENDER_SERVICE_TYPE": "web",
        "KEIBA_RENDER_PREVIEW_ONLY": "1",
        "JRDB_PRIVATE_ENABLED": "0",
        "KEIBA_HISTORY_ENABLED": "0",
        "KEIBA_MANUAL_REFERENCE_ENABLED": "0",
        "KEIBA_ALLOW_LOCAL_HTTP": "0",
        "PORT": str(port),
        "KEIBA_OWNER_USERNAME": "owner",
        "KEIBA_OWNER_PASSWORD": "synthetic-RENDER-Preview-Only-NOT-REAL-xYz123!@#$%",
        "GUNICORN_CMD_ARGS": "",
    })
    for secret in ("JRDB_API_KEY", "JRDB_AUTH_KEY"):
        env.pop(secret, None)
    proc = subprocess.Popen(
        [sys.executable, "-m", "gunicorn", "--config", "deploy/render-gunicorn.py"],
        cwd=str(ROOT), env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        url = "http://127.0.0.1:%s/" % port
        for _ in range(35):
            if proc.poll() is not None:
                raise AssertionError("Gunicorn preview failed to boot")
            try:
                status, _ = _request(url, {})
                if status == 426:
                    break
            except (OSError, TimeoutError):
                time.sleep(0.15)
        else:
            raise AssertionError("Gunicorn preview startup timed out")
        status, _ = _request(url, {})
        assert status == 426, "HTTP without verified edge scheme must be refused"
        forwarded = {"X-Forwarded-Proto": "https"}
        status, _ = _request(url, forwarded)
        assert status == 401, "Unauthenticated HTTPS-forwarded visit must be denied"
        credentials = base64.b64encode(
            ("owner:" + env["KEIBA_OWNER_PASSWORD"]).encode()).decode()
        headers = {**forwarded, "Authorization": "Basic " + credentials}
        status, body = _request(url, headers)
        assert status == 200 and b"KEIBA NINE" in body, "Owner page should open"
        status, body = _request(url + "api/status", {
            **headers, "X-Keiba-Request": "private"
        })
        assert status == 200, "Owner-only status should respond"
        report = json.loads(body)
        assert report == {
            "jrdbConfigured": False, "historyConfigured": False,
            "manualComparisonConfigured": False, "livePredictionEnabled": False
        }, "Preview must not claim any paid/live data"
        status, _ = _request(url + "api/status", headers)
        assert status == 403, "API without explicit custom header must be rejected"
        print("Render preview smoke: HTTPS gate, owner auth, and paid-offline mode passed")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)


if __name__ == "__main__":
    main()
