"""Offline guard for independent preview/JRDB deployment hooks.

The workflow must never leak deploy URLs, deploy an older main SHA, run
against an untrusted PR, or allow preview failure to block JRDB deployment.
This does not check Render/GitHub secret values or assert a live deployment.
"""
import re
import unittest
from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[1] / ".github"
            / "workflows" / "owner-render-after-checks.yml")


class OwnerRenderDeployFallbackTests(unittest.TestCase):
    def test_preview_and_jrdb_are_separate_jobs(self):
        raw = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("    workflows: [\"Private service checks\"]", raw)
        self.assertIn("    types: [completed]", raw)
        self.assertIn("    branches: [main]", raw)
        self.assertIn("  contents: read", raw)
        self.assertIn("  deploy-preview:", raw)
        self.assertIn("  deploy-jrdb:", raw)
        preview = raw.split("  deploy-preview:\n", 1)[1].split(
            "  deploy-jrdb:\n", 1)[0]
        owner = raw.split("  deploy-jrdb:\n", 1)[1]
        self.assertNotIn("RENDER_JRDB_DEPLOY_HOOK_URL", preview)
        self.assertNotIn("RENDER_DEPLOY_HOOK_URL", owner)
        self.assertIn(
            "'https://api.render.com/deploy/srv-dbo1m515efls73cl39s0?key='*",
            owner,
        )
        self.assertIn("case \"$RENDER_JRDB_DEPLOY_HOOK_URL\" in", owner)
        self.assertIn("BLOCKED (wrong hook destination)", owner)
        for part, secret in (
            (preview, "RENDER_DEPLOY_HOOK_URL"),
            (owner, "RENDER_JRDB_DEPLOY_HOOK_URL"),
        ):
            self.assertIn("github.event.workflow_run.conclusion == 'success'", part)
            self.assertIn("github.event.workflow_run.event == 'push'", part)
            self.assertIn("github.event.workflow_run.head_branch == 'main'", part)
            self.assertIn(
                "github.event.workflow_run.head_repository.full_name == github.repository",
                part,
            )
            self.assertIn("PASSED_SHA: ${{ github.event.workflow_run.head_sha }}", part)
            self.assertIn("LATEST=$(gh api", part)
            self.assertIn('if [[ "$LATEST" != "$PASSED_SHA" ]]; then', part)
            self.assertIn('if [[ -z "${' + secret + ':-}" ]]; then', part)
            self.assertIn("curl --fail --silent --show-error", part)
            self.assertIn("--output /dev/null", part)
            self.assertIn('"$' + secret + '"', part)
            self.assertNotIn("set -x", part)
            self.assertNotIn("echo ${" + secret, part)
            self.assertNotIn("git push", part)
            self.assertNotIn("workflow_dispatch", part)

    def test_no_provider_data_or_credentials_are_embedded(self):
        raw = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("JRDB_API_KEY", raw)
        self.assertNotIn("JRDB_AUTH_KEY", raw)
        self.assertNotIn("KEIBA_OWNER_PASSWORD", raw)
        self.assertEqual(len(re.findall(r"^  deploy-(?:preview|jrdb):$", raw,
                                        re.MULTILINE)), 2)


if __name__ == "__main__":
    unittest.main()
