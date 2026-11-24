"""The owner mobile forecast page uses a compact four-step layout."""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML, JS, CSS

class SimpleForecastScreenTest(unittest.TestCase):
    def test_primary_flow(self):
        cues = [
            "<h2>1. 予想を見る</h2>",
            "<h2>2. 予想を見る・競馬場を選ぶ</h2>",
            "<h2>3. 公式情報・取得状況・詳しい分析</h2>",
            "<h2>4. 発走前に固定した買い目</h2>",
            "<summary>追加分析・詳しい設定（必要なときだけ）</summary>",
        ]
        offsets = [HTML.index(x) for x in cues]
        self.assertEqual(offsets, sorted(offsets))
        self.assertIn('href="#autoVenues"', HTML)
        self.assertIn('href="#fixedHistorySection"', HTML)
        self.assertLess(HTML.index('id="autoRaces"'),
                        HTML.index('id="autoDayDiagnostics"'))
        self.assertLess(HTML.index('id="autoRaces"'),
                        HTML.index('id="autoFiveQuickSection"'))
        self.assertIn('id="autoAdvancedResearch"', HTML)
        self.assertIn('href="#forecastRacesSection">予想一覧をすぐ見る', HTML)

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
        self.assertEqual(HTML.count('id="autoHoldBreakdown"'), 1)
        self.assertIn("function holdBreakdownSummary(data)", JS)
        self.assertIn("発走時刻経過は資料不足ではありません", JS)
        self.assertIn("JRDBのAPI照会", HTML)
        self.assertIn("正式10項目", HTML)

    def test_primary_mobile_navigation_and_racecards_before_research(self):
        # Three anchor links stay on this page: they MUST NOT trigger a
        # JRDB/API call, edit an existing receipt or open purchase pages.
        for label, anchor in [
            ("予想を取得", "autoDailyStart"),
            ("レース一覧", "forecastRacesSection"),
            ("結果・記録", "fixedHistorySection"),
        ]:
            self.assertIn('href="#' + anchor + '">' + label + '</a>', HTML)
            self.assertEqual(HTML.count('id="' + anchor + '"'), 1)
        self.assertEqual(HTML.count('class="arc-main-tabs"'), 1)
        self.assertIn('class="owner-weekend-actions"', HTML)
        self.assertIn('id="autoEasyPulse"', HTML)
        self.assertIn('id="autoRaceQuickSummary"', HTML)
        self.assertIn('id="autoDayDiagnostics"', HTML)
        self.assertIn('id="autoResearchTools"', HTML)
        self.assertIn('<summary>詳しい分析・調教資料を見る（任意）</summary>', HTML)
        self.assertLess(HTML.index('id="autoVenues"'),
                        HTML.index('id="autoResearchTools"'))
        self.assertLess(HTML.index('id="autoRaces"'),
                        HTML.index('id="autoResearchTools"'))
        self.assertLess(HTML.index('id="autoRaces"'),
                        HTML.index('id="autoTkyTrainingPanel"'))
        self.assertLess(HTML.index('id="autoRaces"'),
                        HTML.index('id="autoUncertainRecentPanel"'))
        self.assertLess(HTML.index('id="autoRaces"'),
                        HTML.index('id="autoHoldPanel"'))
        self.assertIn("safeDraftCount+'R｜見送り '+data.holdCount+'R'", JS)
        self.assertIn("JRDB2項目方式｜", JS)
        self.assertIn('id="autoQualityLink" href="/owner-100yen-review"', HTML)
        self.assertIn(" $('autoQualityLink').href=target;", JS)
        self.assertIn("grid-template-columns:repeat(4,minmax(0,1fr))", CSS)
        # Tapping the link opens the existing read-only review page.
        # No new JRDB result request, local storage mutation or signed
        # forecast update is made by the navigation itself.
        nav=HTML.split('<nav class="arc-main-tabs"',1)[1].split('</nav>',1)[0]
        self.assertEqual(nav.count('id="autoQualityLink"'),1)
        self.assertNotIn('onclick=',nav)
        self.assertIn("highlightSelectedWeekend()", JS)
        # No new provider endpoint, polling, purchase control or access
        # to paid API keys is introduced by simplified navigation.
        self.assertNotIn('onclick=', HTML.split(
            '<nav class="arc-main-tabs"', 1)[1].split('</nav>', 1)[0])

    def test_default_closed_diagnostics_preserve_existing_ids(self):
        for id_ in (
            "autoResearchTools", "autoDayDiagnostics", "autoHoldPanel",
            "autoTkyTrainingPanel", "autoTkyArrowFormationPanel",
            "autoUncertainRecentPanel", "autoEvidenceGapPanel",
            "autoReceiptVerify", "autoHistory", "autoTenStatus",
        ):
            self.assertEqual(HTML.count('id="' + id_ + '"'), 1)
        self.assertNotIn('id="autoResearchTools" open', HTML)
        self.assertNotIn('id="autoDayDiagnostics" open', HTML)
        self.assertLess(HTML.index('id="autoEasyPulse"'),
                        HTML.index('id="autoMorningStatus"'))
        self.assertLess(HTML.index('id="autoEasyPulse"'),
                        HTML.index('id="autoVenues"'))

    def test_official_jra_link_is_visible_without_opening_advanced_panels(self):
        link = ('<a id="autoOfficialQuickLink" '
                'href="https://www.jra.go.jp/keiba/" '
                'target="_blank" rel="noopener noreferrer">')
        self.assertEqual(HTML.count('id="autoOfficialQuickLink"'), 1)
        self.assertIn(link, HTML)
        self.assertLess(HTML.index(link), HTML.index("<summary>取得・資料の詳しい状態</summary>"))
        self.assertIn("手動確認・自動照合0R", HTML)
        self.assertNotIn('onclick=', link)

if __name__ == "__main__":
    unittest.main()
