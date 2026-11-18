"""Static safety tests for the standalone owner Windows preflight launcher."""
from pathlib import Path
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


class OwnerWindowsPreflightTests(unittest.TestCase):
    def test_checks_prerequisites_without_network_or_data_access(self):
        command = (SCRIPTS / "windows_arc_race_preflight.cmd").read_text(
            encoding="utf-8")
        self.assertIn("py -3-64", command)
        self.assertIn("import win32com.client", command)
        self.assertIn("windows_check_jvlink.ps1", command)
        self.assertIn("PYTHON64_CHECK=OK", command)
        self.assertIn("PYWIN32_CHECK=OK", command)
        self.assertIn("ARC_RACE_PC_READY=YES", command)
        self.assertIn("ARC_RACE_PC_READY=NO", command)
        self.assertIn("pause", command)
        self.assertIn("-NoProfile", command)
        for unsafe in ("JVOpen(", "JVGets(", "JVRead(", "JVSetUIProperties",
                       "curl ", "wget ", "Invoke-WebRequest",
                       "Invoke-RestMethod", "pip install",
                       "git push", "gh auth", "Start-Process"):
            self.assertNotIn(unsafe, command)

    def test_existing_com_probe_does_not_download_or_echo_credentials(self):
        script = (SCRIPTS / "windows_check_jvlink.ps1").read_text(
            encoding="utf-8")
        self.assertIn("JVInit('UNKNOWN')", script)
        self.assertIn("JVDTLab.JVLink", script)
        self.assertIn("ReleaseComObject", script)
        self.assertNotIn("JVOpen(", script)
        self.assertNotIn("JVGets(", script)
        self.assertNotIn("Get-ItemProperty", script)


if __name__ == "__main__":
    unittest.main()
