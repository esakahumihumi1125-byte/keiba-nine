"""Fail-closed, credential-free GitHub/Render release comparison."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_revision_diagnostic import (
    _public_head, inspect_owner_revision, GITHUB_MAIN
)


class RevisionDiagnosticTests(unittest.TestCase):
    def test_matching_and_stale_commits(self):
        head = "a" * 40
        with patch("owner_revision_diagnostic._public_head") as network:
            current = inspect_owner_revision("A" * 12, head)
            self.assertEqual(current["status"], "current")
            self.assertEqual(current["renderCommit"], "a" * 12)
            self.assertEqual(current["githubMainCommit"], "a" * 12)
            stale = inspect_owner_revision("b" * 12, head)
            self.assertEqual(stale["status"], "behind")
            self.assertEqual(stale["githubMainCommit"], "a" * 12)
            self.assertFalse(stale["autoDeployed"])
            self.assertFalse(stale["predictionReady"])
            network.assert_not_called()

    def test_unknown_never_means_current(self):
        for render, latest in (
            ("not-reported", "a" * 40),
            ("a" * 11, "a" * 40),
            ("a" * 12, "invalid sha"),
            ("a" * 12, ""),
            (None, ""),
        ):
            with self.subTest(render=render, latest=latest):
                self.assertEqual(inspect_owner_revision(render, latest)["status"], "unknown")

    def test_github_public_read_has_fixed_destination_and_size_limit(self):
        class Reply:
            status = 200
            def __init__(self, contents):
                self.contents = contents
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, limit):
                self.limit = limit
                return self.contents[:limit]
        class Opener:
            def __init__(self, reply):
                self.reply = reply
            def open(self, req, timeout):
                self.request = req
                self.timeout = timeout
                return self.reply
        opener = Opener(Reply(json.dumps({"sha": "c" * 40}).encode()))
        with patch("owner_revision_diagnostic.urllib.request.build_opener", return_value=opener):
            self.assertEqual(_public_head(), "c" * 40)
        self.assertEqual(opener.request.full_url, GITHUB_MAIN)
        self.assertEqual(opener.request.get_method(), "GET")
        self.assertEqual(opener.timeout, 4)
        self.assertEqual(opener.reply.limit, 4097)
        for value in [b"not JSON", b'{"sha": "abc"}', b"x" * 4097]:
            with patch("owner_revision_diagnostic.urllib.request.build_opener",
                       return_value=Opener(Reply(value))):
                self.assertIsNone(_public_head())
        with patch("owner_revision_diagnostic.urllib.request.build_opener",
                   side_effect=TimeoutError("synthetic offline")):
            self.assertIsNone(_public_head())


if __name__ == "__main__":
    unittest.main()
