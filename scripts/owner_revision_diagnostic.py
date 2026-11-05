"""Owner-only, explicitly requested Render-vs-GitHub revision check.

Only the public GitHub repository's HEAD commit is read. No credentials, user
browsing state, paid JRDB records or betting data leave the private service.
Unknown results fail closed: this cannot deploy or update any service.
"""
import json
import re
import urllib.error
import urllib.request

GITHUB_MAIN = "https://api.github.com/repos/esakahumihumi1125-byte/keiba-nine/commits/main"
VERSION = "owner-revision-diagnostic-1"
SHA = re.compile(r"[0-9a-fA-F]{40}\Z")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _public_head():
    req = urllib.request.Request(
        GITHUB_MAIN, headers={
            "User-Agent": "keiba-nine-owner-revision-check",
            "Accept": "application/vnd.github+json",
        }, method="GET",
    )
    try:
        with urllib.request.build_opener(_NoRedirect()).open(req, timeout=4) as response:
            if response.status != 200:
                return None
            raw = response.read(4097)
            if len(raw) > 4096:
                return None
        obj = json.loads(raw)
        value = obj.get("sha") if isinstance(obj, dict) else None
        return value.lower() if isinstance(value, str) and SHA.fullmatch(value) else None
    except (OSError, ValueError, urllib.error.URLError):
        return None


def inspect_owner_revision(render_commit, latest_commit=None):
    """Return a small non-sensitive owner-facing diagnostic; never auto-deploy."""
    current = render_commit[:12].lower() if (
        isinstance(render_commit, str)
        and re.fullmatch(r"[0-9a-fA-F]{12}", render_commit)
    ) else None
    head = latest_commit if latest_commit is not None else _public_head()
    latest = head[:12].lower() if isinstance(head, str) and SHA.fullmatch(head) else None
    if current is None or latest is None:
        status = "unknown"
        note = "版を照合できません。Render/GitHubの接続状態と配信履歴を確認してください。"
    elif current == latest:
        status = "current"
        note = "Renderの配信コミットは、確認時点のGitHub mainと一致しています。"
    else:
        status = "behind"
        note = "GitHub mainに新しいコードがありますが、Renderは別のコミットを配信中です。自動デプロイの接続設定を確認してください。"
    return {
        "version": VERSION, "status": status,
        "renderCommit": current or "not-reported",
        "githubMainCommit": latest or "unavailable",
        "checkedOnDemand": True,
        "autoDeployed": False,
        "predictionReady": False,
        "note": note,
    }
