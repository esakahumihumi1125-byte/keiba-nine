"""Static safety checks only. No Windows COM calls in CI."""
import re
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
PS1 = SCRIPTS / "windows_check_jvlink.ps1"
CMD = SCRIPTS / "windows_check_jvlink.cmd"


class WindowsJvLinkLocalCheckTests(unittest.TestCase):
    def test_local_check_does_not_request_or_export_race_data(self):
        contents = PS1.read_text(encoding="utf-8")
        self.assertIn("JVDTLab.JVLink", contents)
        self.assertIn("JVInit('UNKNOWN')", contents)
        self.assertIn("Is64BitProcess", contents)
        self.assertIn("ReleaseComObject", contents)
        for forbidden in (
            "JVOpen(", "JVRTOpen(", "JVRead(", "JVGets(", "JVSave(",
            "Invoke-WebRequest", "Invoke-RestMethod", "HttpClient",
            "WebRequest", "api_key", "x-user-key", "upload", "Start-Process",
        ):
            self.assertNotIn(forbidden, contents)
        self.assertNotIn("$_.Exception.Message", contents)
        self.assertNotIn("Get-ItemProperty", contents)
        self.assertIn("JVLINK_CHECK=INIT_OK", contents)
        self.assertIn("JVLINK_CHECK=COM_UNAVAILABLE", contents)

    def test_launcher_only_invokes_local_script(self):
        contents = CMD.read_text(encoding="utf-8")
        self.assertIn("windows_check_jvlink.ps1", contents)
        self.assertIn("-NoProfile", contents)
        self.assertIn("-File", contents)
        self.assertIn("pause", contents)
        self.assertNotIn("curl", contents.lower())
        self.assertNotIn("http:", contents.lower())
        self.assertNotIn("https:", contents.lower())
        self.assertNotIn("python", contents.lower())
        self.assertNotIn("git ", contents.lower())
        self.assertNotIn("JVOpen", contents)
        self.assertTrue(re.search(r"exit /b %CHECK_EXIT%", contents, re.I))


if __name__ == "__main__":
    unittest.main()
