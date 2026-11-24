"""Regression contract: free JRA advance comparison after a successful owner day read.

This deliberately does not contact JRA or JRDB. It checks that the automatic
request is gated behind validated report + signed-receipt handling, can diagnose a zero-race response and cannot run
for a stale iPhone date, and keeps JRA *advance* information
separate from final official verification.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "scripts" / "owner_auto_forecast_ui.py").read_text(encoding="utf-8")


class AutoFreeJraProgrammeContractTests(unittest.TestCase):
    def test_after_successful_owner_read_only(self):
        start = SOURCE.index("$('autoRun').onclick=async()=>{")
        end = SOURCE.index(" }catch(error){if(seq===request){", start)
        block = SOURCE[start:end]
        checks = (
            "validate(body,day);",
            "localStatus=saveAutoReceipts(body,day);",
            "const displayed=render(body,day);",
            "latestDisplayedReport=body;latestDisplayedDay=day;",
            "if(seq===request&&day===$('autoDay').value.replaceAll('-','')){",
            "const jraCalendarYear=Number(day.slice(0,4));",
            "if(jraCalendarYear>=2020&&jraCalendarYear<=2035)",
            "void $('autoAdvanceCompare').onclick();",
        )
        positions = [block.index(value) for value in checks]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(block.count("void $('autoAdvanceCompare').onclick();"), 1)

    def test_zero_received_races_are_not_a_verified_empty_schedule(self):
        start = SOURCE.index("const jraCalendarYear=Number(day.slice(0,4));")
        end = SOURCE.index("void $('autoAdvanceCompare').onclick();", start)
        self.assertNotIn("body.raceCount", SOURCE[start:end])
        start = SOURCE.index("$('autoAdvanceCompare').onclick=async()=>{")
        end = SOURCE.index("// Optional, JRA-only HTML index lookup.", start)
        block = SOURCE[start:end]
        self.assertIn("if(!original){", block)
        self.assertIn("unknown+=3;missingSlots++;", block)
        self.assertIn("JRA事前番組 '+p.raceCount+'R／JRDB受信 '+source.raceCount", block)
        self.assertIn("取得できず未確認", block)

    def test_only_public_schedule_no_paid_refresh(self):
        start = SOURCE.index("$('autoAdvanceCompare').onclick=async()=>{")
        end = SOURCE.index("// Optional, JRA-only HTML index lookup.", start)
        block = SOURCE[start:end]
        self.assertIn("'/api/jra/advance-programme?date='", block)
        self.assertNotIn("'/api/jrdb/", block)
        self.assertIn("newJrdbRequests!==0", block)
        self.assertIn("p.officialFinalCardVerified!==false", block)
        self.assertIn("p.officialStartersVerified!==false", block)
        self.assertIn("p.officialScratchesVerified!==false", block)
        self.assertIn("p.officialGoingVerified!==false", block)
        self.assertIn("p.officialPostTimeVerified!==false", block)

    def test_status_and_errors_stay_unverified(self):
        self.assertIn('id="autoAdvanceHeadline"', SOURCE)
        self.assertIn("JRA事前競馬番組の参考比較：差異 ", SOURCE)
        self.assertIn("取得できず未確認。研究用予想・固定記録はそのままです。", SOURCE)
        self.assertIn("正式な最終照合ではありません。", SOURCE)
        self.assertIn("JRDBへの追加有料通信0回", SOURCE)


if __name__ == "__main__":
    unittest.main()
