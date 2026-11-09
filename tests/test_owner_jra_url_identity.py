"""Check official published CNAME identity (venue, meeting, race, date).

No network calls; real JRA URL shapes from public race pages are used only as
test strings. No raw JRA body, horse identity, ticket or private key is stored.
"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from owner_official_settlement_replay import (
    _source_url, SettlementReplayError, sign_authenticated_source_record
)
from test_owner_official_settlement_replay import RESULT_SECRET, payload

KYOTO_8 = ("https://www.jra.go.jp/JRADB/accessS.html?"
           "CNAME=pw01sde0108202605020820261108%2FA0")
KYOTO_9 = ("https://www.jra.go.jp/JRADB/accessS.html?"
           "CNAME=pw01sde1008202605020920261108%2F34")
TOKYO_8 = ("https://www.jra.go.jp/JRADB/accessS.html?"
           "CNAME=pw01sde1005202605020820261108%2FA1")
MOBILE_KYOTO_8 = ("https://sp.jra.jp/JRADB/accessS.html?"
                  "CNAME=sw01sde1008202605020820261108%2F0C")


class OfficialRaceUrlIdentityTests(unittest.TestCase):
    def test_actual_published_jra_link_shapes_have_exact_identity(self):
        for url, day, track, race in (
            (KYOTO_8, "20261108", "京都", 8),
            (KYOTO_9, "20261108", "京都", 9),
            (TOKYO_8, "20261108", "東京", 8),
            (MOBILE_KYOTO_8, "20261108", "京都", 8),
        ):
            with self.subTest(track=track, race=race, url=url):
                _source_url(url, day, track, race)

    def test_same_day_different_course_or_race_is_rejected(self):
        for url, expected_track, expected_race in (
            (TOKYO_8, "京都", 8),
            (KYOTO_8, "東京", 8),
            (KYOTO_8, "京都", 9),
            (KYOTO_9, "京都", 8),
            (MOBILE_KYOTO_8, "京都", 11),
        ):
            with self.subTest(url=url, track=expected_track,
                              race=expected_race), self.assertRaises(SettlementReplayError):
                _source_url(url, "20261108", expected_track, expected_race)

    def test_fake_filename_params_and_embedded_date_fail(self):
        for bad in (
            KYOTO_8.replace("20261108", "20261109"),
            KYOTO_8.replace("20260502", "20250502"),
            KYOTO_8.replace("01082026", "01992026"),
            KYOTO_8.replace("050208", "050209"),
            KYOTO_8.replace("CNAME=", "xCNAME="),
            KYOTO_8.replace("A0", "zz"),
            KYOTO_8 + "&race=08",
            KYOTO_8.replace("www.jra.go.jp", "www.jra.go.jp.attacker.test"),
            KYOTO_8.replace("https:", "http:"),
            KYOTO_8.replace("/JRADB/accessS.html", "/JRADB/accessD.html"),
        ):
            with self.subTest(url=bad), self.assertRaises(SettlementReplayError):
                _source_url(bad, "20261108", "京都", 8)

    def test_future_result_signer_cannot_sign_different_course_page(self):
        # Even if an internal caller asserts that it checked the JRA page,
        # one exact race cannot be signed against another race's source URL.
        original = payload()
        original["sourceUrl"] = KYOTO_8
        with self.assertRaises(SettlementReplayError):
            sign_authenticated_source_record(original, RESULT_SECRET)
        as_other = copy.deepcopy(original)
        as_other["date"] = "2026-11-08"
        as_other["track"] = "京都"
        as_other["race"] = 8
        as_other["finalizedAt"] = "2026-11-08T15:30:00+09:00"
        as_other["sourceCollectedAt"] = "2026-11-08T15:40:00+09:00"
        result = sign_authenticated_source_record(as_other, RESULT_SECRET)
        self.assertEqual(set(result), {"payload", "signature"})
        self.assertNotIn("officialJraVerified", result)


if __name__ == "__main__":
    unittest.main()
