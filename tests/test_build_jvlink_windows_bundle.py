"""Ensure the Windows ZIP contains only explicitly reviewed source files."""
from pathlib import Path
import tempfile
import unittest
import zipfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_jvlink_windows_bundle import FILES, README, build


class WindowsBundleTests(unittest.TestCase):
    def test_only_whitelisted_scripts_and_readme_are_packaged(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "local.zip"
            self.assertEqual(build(file), file)
            with zipfile.ZipFile(file) as package:
                names = package.namelist()
                self.assertEqual(
                    set(names),
                    {"ARC-RACE-JV-Link/README.txt"}
                    | {"ARC-RACE-JV-Link/" + path for path in FILES},
                )
                self.assertEqual(len(names), len(set(names)))
                for name in names:
                    self.assertTrue(name.startswith("ARC-RACE-JV-Link/"))
                    self.assertFalse(name.startswith("/"))
                    self.assertNotIn("..", name)
                    self.assertNotIn(".env", name)
                    self.assertNotIn("__pycache__", name)
                    self.assertNotIn(".git/", name)
                guide = package.read("ARC-RACE-JV-Link/README.txt").decode("utf-8-sig")
                self.assertIn("windows_arc_race_preflight.cmd", guide)
                self.assertIn("windows_jvlink_weekly_read.cmd", guide)
                self.assertIn("windows_jvlink_horse_data_probe.cmd", guide)
                self.assertIn("ARC_RACE_RCVN_CHECK", guide)
                self.assertIn("windows_jvlink_day_history_preview.cmd", guide)
                self.assertIn("windows_arc_race_saved_trifecta_trial.cmd", guide)
                self.assertIn("LOCAL_TRIFECTA", guide)
                self.assertIn("ARC_RACE_DAY_HISTORY", guide)
                self.assertIn("YES", guide)
                self.assertIn("未完成", guide)
                self.assertNotIn("RENDER_DEPLOY_HOOK_URL", guide)
                self.assertNotIn("JRDB_API_KEY", guide)
                self.assertNotIn("JRA_VAN_LICENSE", guide)

    def test_runner_has_dependencies_without_external_urls(self):
        self.assertIn("scripts/jvdata_ra_se_candidate.py", FILES)
        self.assertIn("scripts/jrdb_program_preview.py", FILES)
        self.assertIn("scripts/jrdb_evidence_readiness.py", FILES)
        self.assertIn("scripts/owner_jvdata_local_report.py", FILES)
        self.assertIn("scripts/windows_check_jvlink.ps1", FILES)
        self.assertIn("scripts/windows_jvlink_horse_data_probe.cmd", FILES)
        self.assertIn("scripts/windows_jvlink_horse_data_probe.py", FILES)
        self.assertIn("scripts/windows_jvlink_day_history_preview.cmd", FILES)
        self.assertIn("scripts/windows_jvlink_day_history_preview.py", FILES)
        self.assertIn("scripts/windows_arc_race_saved_trifecta_trial.cmd", FILES)
        self.assertIn("scripts/windows_arc_race_saved_trifecta_trial.py", FILES)
        self.assertIn("scripts/owner_jvdata_offline_trifecta_trial.py", FILES)
        self.assertIn("scripts/owner_jvdata_day_history_bridge.py", FILES)
        self.assertIn("scripts/owner_jvdata_horse_history_coverage.py", FILES)
        self.assertIn("scripts/owner_jvdata_horse_history_preview.py", FILES)
        self.assertTrue(all(path.startswith(("scripts/", "docs/")) for path in FILES))


if __name__ == "__main__":
    unittest.main()
