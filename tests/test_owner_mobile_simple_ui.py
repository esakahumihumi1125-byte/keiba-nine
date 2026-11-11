"""The owner mobile forecast page uses a compact four-step layout."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML

class SimpleForecastScreenTest(unittest.TestCase):
    def test_primary_flow(self):
        cues = [
            "<h2>1. 予想を見る</h2>",
            "<h2>2. 今日の予想状況</h2>",
            "<h2>3. 競馬場・レースを選ぶ</h2>",
            "<h2>4. 発走前に固定した買い目</h2>",
            "<summary>追加分析・詳しい設定（必要なときだけ）</summary>",
        ]
        offsets = [HTML.index(x) for x in cues]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn('href="#autoVenues"', HTML)
        self.assertIn('href="#fixedHistorySection"', HTML)

    def test_details_and_preserved_controls(self):
        for control in [
            "autoDay", "autoRun", "autoSaturdayQuick", "autoSaturday",
            "autoSunday", "autoPreflight", "autoConnectionCheck",
            "autoVenues", "autoRacePick", "autoRaces", "autoHistory",
            "autoHistoryAudit", "autoReceiptVerify", "autoOfficialPdf",
        ]:
            self.assertEqual(HTML.count('id="' + control + '"'), 1, control)
        ids = re.findall('id="([^"]+)"', HTML)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertLess(
            HTML.index("<summary>取得・資料の詳しい状態</summary>"),
            HTML.index('id="autoReadProof"'))
        self.assertLess(
            HTML.index("<summary>追加分析・詳しい設定（必要なときだけ）</summary>"),
            HTML.index('id="autoHistoryAudit"'))
        self.assertIn("JRDBのAPI照会", HTML)
        self.assertIn("正式10項目", HTML)

if __name__ == "__main__":
    unittest.main()
