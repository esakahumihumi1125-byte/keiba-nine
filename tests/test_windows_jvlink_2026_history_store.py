"""Fake COM only; no real JV-Link, credentials or licensed records."""
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from windows_jvlink_2026_history_store import (
    save_archive, DATABASE, FROMTIME, MIN_FREE, JvLocalCheckError,
)
from test_windows_jvlink_day_history_preview import FakeJv, sources
from test_jvdata_ra_se_candidate import replace


class HistoryArchiveTests(unittest.TestCase):
    def test_one_normal_read_distinct_revisions_no_overwrite(self):
        current = sources()["RACE"]
        revised = replace(current[0], 2, 3, "7")
        other = replace(current[0], 11, 15, "2025")
        jv = FakeJv({"RACE": [*current, current[0], revised, other]})
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            counts = save_archive(jv, folder, free_bytes=lambda: MIN_FREE)
            self.assertEqual(counts, {"RA": 2, "SE": 4})
            self.assertEqual(jv.opens[0][:3], ("RACE", FROMTIME, 1))
            self.assertEqual(jv.closes, 1)
            with sqlite3.connect(folder / DATABASE) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM records").fetchone()[0], 6)
                self.assertEqual(dict(conn.execute("SELECT key,value FROM manifest"))["coverage_verified"], "no")
            conn.close()
            with self.assertRaisesRegex(JvLocalCheckError, "HISTORY_EXISTS"):
                save_archive(jv, folder, free_bytes=lambda: MIN_FREE)
            self.assertEqual(len(jv.opens), 1)

    def test_incomplete_stream_no_archive_and_no_retry(self):
        for rows, options in ((sources()["RACE"], {"max_steps": 1}),
                              ([sources()["RACE"][0]], {}),
                              ([b"RA7bad"], {})):
            with tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                jv = FakeJv({"RACE": rows})
                with self.assertRaises(JvLocalCheckError):
                    save_archive(jv, folder, free_bytes=lambda: MIN_FREE, **options)
                self.assertEqual(list(folder.iterdir()), [])
                self.assertEqual(jv.closes, 1)
                self.assertEqual(len(jv.opens), 1)

    def test_disk_guard_before_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            jv = FakeJv(sources())
            with self.assertRaisesRegex(JvLocalCheckError, "HISTORY_DISK_SPACE_LOW"):
                save_archive(jv, Path(tmp), free_bytes=lambda: MIN_FREE-1)
            self.assertEqual(jv.opens, [])


if __name__ == "__main__":
    unittest.main()
