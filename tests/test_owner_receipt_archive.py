"""No-live-credentials regression tests for opt-in owner receipt archiving."""
import copy
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_receipt_archive import (
    FLAG, DSN_KEY, SIGNING_KEY, INSERT, SELECT, ArchiveUnavailable, archive_config,
    save_first_and_read, read_day)
from owner_prestart_receipt import issue_preview_receipts
from test_owner_prestart_receipt import DAY, sample_race, forecast, setup, post
from private_service import create_app
from test_private_service import call, SETTINGS

ARCHIVE_CONFIG = {
    **setup(sample_race()),
    FLAG: "1",
    DSN_KEY: "postgresql://fake_owner:fake_password@db.invalid/keiba_private",
    SIGNING_KEY: "synthetic-independent-signing-secret-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ",
}


class MemoryPostgres:
    """Transactional fake with the FIRST INSERT winning and a DB clock gate."""
    def __init__(self, now=None):
        self.rows = {}
        self.now = now or datetime(2099, 4, 11, 11, tzinfo=timezone.utc)
        self.fail = False
        self.commands = []

    def connect(self, dsn):
        if "db.invalid" not in dsn:
            raise ValueError("unexpected test connection")
        return Transaction(self)


class Transaction:
    def __init__(self, database):
        self.db = database
        self.staged = dict(database.rows)
        self.last = []
    def __enter__(self):
        return self
    def __exit__(self, kind, value, traceback):
        if kind is None:
            self.db.rows = self.staged
        return False
    def cursor(self):
        return self
    def execute(self, sql, params):
        self.db.commands.append(sql)
        if self.db.fail:
            raise RuntimeError("Fake database outage. No secrets in error.")
        if sql == INSERT:
            day, track, race, encoded, off = params
            if self.db.now < datetime.fromisoformat(off):
                self.staged.setdefault((day, track, race), json.loads(encoded))
        elif sql == SELECT:
            day, = params
            self.last = [(copy.deepcopy(self.staged[k]),)
                         for k in sorted(self.staged) if k[0] == day]
        else:
            raise AssertionError("Unexpected archive query")
    def fetchall(self):
        return list(self.last)


class OwnerArchiveTests(unittest.TestCase):
    def setUp(self):
        self.db = MemoryPostgres()
        self.password = ARCHIVE_CONFIG[SIGNING_KEY]
        self.receipts = issue_preview_receipts(
            forecast(sample_race()), self.password, DAY,
            now=datetime(2099,4,11,10,tzinfo=timezone.utc))["receipts"]

    def test_archive_requires_private_opt_in_and_persistent_url(self):
        for config in (
            {**ARCHIVE_CONFIG, FLAG: "0"},
            {**ARCHIVE_CONFIG, "KEIBA_RENDER_PRIVATE_ONLY":"0"},
            {**ARCHIVE_CONFIG, "KEIBA_RENDER_PREVIEW_ONLY":"1"},
            {**ARCHIVE_CONFIG, "GITHUB_ACTIONS":"true"},
            {**ARCHIVE_CONFIG, DSN_KEY:""},
            {**ARCHIVE_CONFIG, SIGNING_KEY:""},
            {**ARCHIVE_CONFIG, SIGNING_KEY:"too-weak"},
            {**ARCHIVE_CONFIG, DSN_KEY:"file:///tmp/archive.db"},
            {**ARCHIVE_CONFIG, DSN_KEY:"postgresql://fake_owner/db"},
        ):
            with self.subTest(config=list(config.keys())):
                with self.assertRaises(ArchiveUnavailable):
                    archive_config(config)
        self.assertEqual(archive_config(ARCHIVE_CONFIG), ARCHIVE_CONFIG[DSN_KEY])
        # A login password rotation does not rotate the durable archive key.
        changed_login = {**ARCHIVE_CONFIG,
                         "KEIBA_OWNER_PASSWORD": "rotated-owner-login-0123456789-ABCDEFGHIJKLMNOPQRSTUVWXYZ"}
        self.assertEqual(archive_config(changed_login), ARCHIVE_CONFIG[DSN_KEY])

    def test_first_saved_ticket_is_never_replaced_by_later_forecast(self):
        saved = save_first_and_read(
            ARCHIVE_CONFIG,self.password,DAY,self.receipts,connect=self.db.connect)
        self.assertEqual(saved, self.receipts)
        newer = issue_preview_receipts(
            forecast(sample_race()),self.password,DAY,
            now=datetime(2099,4,11,10,30,tzinfo=timezone.utc))["receipts"]
        self.assertNotEqual(newer[0]["signature"], self.receipts[0]["signature"])
        got = save_first_and_read(
            ARCHIVE_CONFIG,self.password,DAY,newer,connect=self.db.connect)
        self.assertEqual(got,self.receipts)
        self.assertEqual(read_day(
            ARCHIVE_CONFIG,self.password,DAY,connect=self.db.connect), self.receipts)
        self.assertEqual(len(self.db.rows),1)
        self.assertTrue(all("UPDATE" not in q and "DELETE" not in q
                            for q in self.db.commands))
        self.assertIn("ON CONFLICT", INSERT)
        self.assertIn("clock_timestamp()", INSERT)

    def test_after_race_archive_cannot_insert_even_with_signed_older_receipt(self):
        self.db.now=datetime(2099,4,12,2,tzinfo=timezone.utc)
        with self.assertRaises(ArchiveUnavailable):
            save_first_and_read(ARCHIVE_CONFIG,self.password,DAY,
                                self.receipts,connect=self.db.connect)
        self.assertEqual(self.db.rows,{})
        self.assertEqual(read_day(
            ARCHIVE_CONFIG,self.password,DAY,connect=self.db.connect),[])

    def test_database_failure_does_not_claim_saved_or_mutate_previous_races(self):
        save_first_and_read(
            ARCHIVE_CONFIG,self.password,DAY,self.receipts,connect=self.db.connect)
        original=copy.deepcopy(self.db.rows)
        self.db.fail=True
        with self.assertRaises(ArchiveUnavailable):
            save_first_and_read(
                ARCHIVE_CONFIG,self.password,DAY,self.receipts,
                connect=self.db.connect)
        self.assertEqual(self.db.rows,original)

    def test_database_tampering_or_owner_password_change_fails_closed(self):
        save_first_and_read(
            ARCHIVE_CONFIG,self.password,DAY,self.receipts,connect=self.db.connect)
        self.db.rows[(DAY,"東京",1)]["snapshot"]["trifectaTickets"][0][0]=17
        with self.assertRaises(ArchiveUnavailable):
            read_day(ARCHIVE_CONFIG,self.password,DAY,connect=self.db.connect)
        self.db.rows.clear()
        save_first_and_read(
            ARCHIVE_CONFIG,self.password,DAY,self.receipts,connect=self.db.connect)
        with self.assertRaises(ArchiveUnavailable):
            read_day(ARCHIVE_CONFIG, "replacement-owner-password-12345678", DAY,
                     connect=self.db.connect)

    def test_archive_http_round_trip_and_summary_does_not_leak_receipts(self):
        app=create_app(ARCHIVE_CONFIG)
        def save(s, password, day, receipts):
            return save_first_and_read(s,password,day,receipts,connect=self.db.connect)
        def load(s,password,day):
            return read_day(s,password,day,connect=self.db.connect)
        with (patch("private_service.save_first_and_read",side_effect=save),
              patch("private_service.read_archived_day",side_effect=load)):
            issued=post(app,"/api/owner-freeze-preday",{"date":DAY})
            self.assertEqual(issued["status"],"200 OK")
            payload=json.loads(issued["body"])
            self.assertTrue(payload["archiveEnabled"])
            self.assertEqual(payload["archiveRecordCount"],1)
            result=call(app,"/api/owner-100yen-archived",QUERY_STRING="date="+DAY)
            self.assertEqual(result["status"],"200 OK")
            view=json.loads(result["body"])
            self.assertTrue(view["archiveEnabled"])
            self.assertTrue(view["available"])
            self.assertEqual(view["review"]["pendingRaces"],1)
            self.assertEqual(view["review"]["reviewedRaces"],0)
            self.assertIsNone(view["review"]["roiPercent"])
            self.assertNotIn("signature",result["body"].decode())
            self.assertNotIn("lockedAt",result["body"].decode())
            self.assertNotIn("fake_password",result["body"].decode())
            self.assertEqual(call(
                app,"/api/owner-100yen-archived",
                QUERY_STRING="date="+DAY,auth="")["status"],"401 Unauthorized")
            self.assertEqual(call(
                app,"/api/owner-100yen-archived",
                QUERY_STRING="date="+DAY,HTTP_X_KEIBA_REQUEST="")["status"],
                "403 Forbidden")
            self.assertEqual(call(
                app,"/api/owner-100yen-archived",
                QUERY_STRING="date=2099-02-31")["status"],"400 Bad Request")

    def test_archive_disabled_is_safe_and_does_not_require_db(self):
        app=create_app(setup(sample_race()))
        result=call(app,"/api/owner-100yen-archived",QUERY_STRING="date="+DAY)
        self.assertEqual(result["status"],"200 OK")
        self.assertFalse(json.loads(result["body"])["archiveEnabled"])
        issued=post(app,"/api/owner-freeze-preday",{"date":DAY})
        self.assertEqual(issued["status"],"200 OK")
        self.assertFalse(json.loads(issued["body"])["archiveEnabled"])


if __name__ == "__main__":
    unittest.main()
