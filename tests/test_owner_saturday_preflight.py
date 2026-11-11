"""Saturday preflight is an offline configuration PRESENCE check, not JRDB."""
import unittest
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_saturday_preflight import owner_saturday_config_preflight

NOW = datetime(2026, 11, 11, 9, 43, tzinfo=timezone(timedelta(hours=9)))
SETTINGS = {
    "KEIBA_RENDER_PRIVATE_ONLY": "1",
    "JRDB_PRIVATE_ENABLED": "1",
    "JRDB_API_KEY": "SYNTHETIC_ONLY_NO_REAL_KEY",
    "JRDB_AUTH_KEY": "SYNTHETIC_ONLY_NO_REAL_AUTH",
    "JRDB_API_BASE_URL": "",
}


class SaturdayConfigPreflightTests(unittest.TestCase):
    def test_2026_november_14_is_weekend_but_real_jrdb_not_verified(self):
        report = owner_saturday_config_preflight(
            SETTINGS, "20261114", server_now=NOW)
        self.assertEqual(report["date"], "20261114")
        self.assertEqual(report["serverDate"], "20261111")
        self.assertEqual(report["serverTimeJst"], "09:43")
        self.assertTrue(report["selectedDateIsWeekend"])
        self.assertFalse(report["selectedDateAlreadyPast"])
        self.assertTrue(report["configurationReady"])
        self.assertTrue(report["privateServiceConfigured"])
        self.assertEqual(report["sourceCallsMade"], 0)
        for k in ("serverClockIndependentlyVerified",
                  "providerConnectionVerified", "liveRaceFeedVerified",
                  "officialJraVerified", "formalTenFactorsReady",
                  "archivePersistenceVerified", "bettingReady",
                  "existingReceiptsChanged", "existingRoiChanged"):
            self.assertFalse(report[k], k)
        for secret in ("SYNTHETIC_ONLY_NO_REAL_KEY", "SYNTHETIC_ONLY_NO_REAL_AUTH",
                       "dev.api.bigtime.world"):
            self.assertNotIn(secret, str(report))

    def test_missing_secrets_or_unsafe_host_fail_configuration_only(self):
        for kind in ("key", "auth", "host", "private", "preview"):
            config = dict(SETTINGS)
            if kind == "key":
                config.pop("JRDB_API_KEY")
            elif kind == "auth":
                config["JRDB_AUTH_KEY"] = ""
            elif kind == "host":
                config["JRDB_API_BASE_URL"] = "https://untrusted.example"
            elif kind == "private":
                config["KEIBA_RENDER_PRIVATE_ONLY"] = "0"
            else:
                config["KEIBA_RENDER_PREVIEW_ONLY"] = "1"
            with self.subTest(kind=kind):
                report = owner_saturday_config_preflight(
                    config, "20261114", server_now=NOW)
                self.assertFalse(report["configurationReady"])
                self.assertFalse(report["providerConnectionVerified"])
                self.assertFalse(report["liveRaceFeedVerified"])

    def test_past_day_and_nonweekend_are_not_assumed_no_racing(self):
        report = owner_saturday_config_preflight(
            SETTINGS, "20261110", server_now=NOW)
        self.assertTrue(report["selectedDateAlreadyPast"])
        self.assertFalse(report["selectedDateIsWeekend"])
        self.assertTrue(report["configurationReady"])
        # A non-weekend is not a statement that there are no JRA races.
        self.assertNotIn("no races", str(report).lower())

    def test_timezones_are_normalized_to_japan(self):
        now_utc = datetime(2026, 11, 11, 0, 43,
                           tzinfo=timezone.utc)
        a = owner_saturday_config_preflight(
            SETTINGS, "20261114", server_now=NOW)
        b = owner_saturday_config_preflight(
            SETTINGS, "20261114", server_now=now_utc)
        self.assertEqual(a, b)

    def test_invalid_dates_and_naive_clock_rejected(self):
        for day in ("202611", "20261301", "20260230", "2099-01-01",
                    "../secrets", None, []):
            with self.subTest(day=str(day)), self.assertRaises(ValueError):
                owner_saturday_config_preflight(SETTINGS, day, server_now=NOW)
        with self.assertRaises(ValueError):
            owner_saturday_config_preflight(
                SETTINGS, "20261114", server_now=datetime(2026, 11, 11))
        with self.assertRaises(ValueError):
            owner_saturday_config_preflight(
                SETTINGS, "20261114", server_now="2026-11-11T09:43:00+09:00")


if __name__ == "__main__":
    unittest.main()
