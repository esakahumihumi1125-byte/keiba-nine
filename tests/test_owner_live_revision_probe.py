"""No-network checks of the public-code-only Render revision probe."""
import json
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_live_revision_probe import verify_live_revision, URL

SHA = "b" * 40


class Reply:
    def __init__(self, obj, status=200):
        self.status = status
        self.data = (json.dumps(obj).encode() if not isinstance(obj, bytes)
                     else obj)

    def read(self, limit):
        return self.data[:limit]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


def contract(commit):
    return {
        "version": "owner-live-revision-1",
        "renderCommit": commit,
        "revisionOnly": True,
        "jrdbConnectionVerified": False,
        "forecastExecutionVerified": False,
        "ownerDataIncluded": False,
    }


class LiveRevisionProbeTests(unittest.TestCase):
    def test_matching_real_build_sha_without_private_requests(self):
        seen = []
        def fetch(req, timeout):
            seen.append((req.full_url, req.get_method(), req.headers, timeout))
            return Reply(contract(SHA[:12]))
        self.assertEqual(verify_live_revision(SHA, fetch=fetch, tries=1),
                         (True, "sha_verified"))
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0][0], URL)
        self.assertEqual(seen[0][1], "GET")
        self.assertEqual(seen[0][3], 12)
        self.assertFalse(any("Authorization" in k or "Cookie" in k
                             for k in seen[0][2]))
        self.assertNotIn("/api/jrdb/", seen[0][0])
        self.assertTrue(URL.startswith("https://"))

    def test_older_build_retried_until_current_build(self):
        returns = iter([Reply(contract("a" * 12)),
                        Reply(contract("b" * 12))])
        sleeps = []
        good, why = verify_live_revision(
            SHA, fetch=lambda req, timeout: next(returns),
            sleep=sleeps.append, tries=2
        )
        self.assertEqual((good, why), (True, "sha_verified"))
        self.assertEqual(sleeps, [12])

    def test_no_sha_match_does_not_imply_deployed(self):
        self.assertEqual(verify_live_revision(
            SHA, fetch=lambda req, timeout: Reply(contract("a" * 12)),
            sleep=lambda x: None, tries=2),
            (False, "live_sha_mismatch"))

    def test_not_reported_or_wrong_contract_cannot_claim_live(self):
        for corrupt in (
            contract("not-reported"),
            {**contract(SHA[:12]), "forecastExecutionVerified": True},
            {**contract(SHA[:12]), "jrdbConnectionVerified": True},
            {**contract(SHA[:12]), "ownerDataIncluded": True},
            {**contract(SHA[:12]), "extraPrivateData": "forbidden"},
            {**contract(SHA[:12]), "revisionOnly": 1},
            {**contract(SHA[:12]), "renderCommit": ["b" * 12]},
        ):
            with self.subTest(corrupt=str(corrupt)[:100]):
                _, why = verify_live_revision(
                    SHA, fetch=lambda req, timeout: Reply(corrupt), tries=1
                )
                self.assertIn(why, ("invalid_contract", "live_sha_mismatch"))

    def test_network_failure_and_auth_redirect_do_not_verify(self):
        def bad(req, timeout):
            raise URLError("simulated offline")
        self.assertEqual(verify_live_revision(
            SHA, fetch=bad, sleep=lambda t: None, tries=2),
            (False, "unreachable"))
        self.assertEqual(verify_live_revision(
            SHA, fetch=lambda req, timeout: Reply(contract(SHA[:12]), status=302),
            tries=1),
            (False, "bad_http_status"))

    def test_response_size_and_bad_expected_sha_rejected(self):
        payload = b"{" + b"x" * 1400
        self.assertEqual(verify_live_revision(
            SHA, fetch=lambda req, timeout: Reply(payload), tries=1),
            (False, "invalid_contract"))
        for bad in ("", "not-a-sha", "b" * 12, ["b" * 40]):
            with self.assertRaises(ValueError):
                verify_live_revision(bad, tries=1)
        for tries in (0, 17, 1.2):
            with self.assertRaises(ValueError):
                verify_live_revision(SHA, tries=tries)


if __name__ == "__main__":
    unittest.main()
