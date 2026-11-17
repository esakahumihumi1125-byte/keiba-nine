"""Mobile-first owner flow: reach prevalidated race picks before optional analysis.

These tests check HTML structure only. No JRDB/JRA requests, no receipt
signature changes, no storage writes and no forecast re-ranking.
"""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from owner_auto_forecast_ui import HTML, CSS, JS


class _OwnerLayout(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.parents = {}
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in ("section", "details"):
            return
        attrs = dict(attrs)
        identity = attrs.get("id")
        if identity:
            if identity in self.parents:
                self.errors.append("duplicate structural id")
            self.parents[identity] = tuple(self.stack)
        self.stack.append((tag, identity))

    def handle_endtag(self, tag):
        if tag not in ("section", "details"):
            return
        if not self.stack or self.stack[-1][0] != tag:
            self.errors.append("misnested section or details")
            return
        self.stack.pop()


class MobileForecastFirstContract(unittest.TestCase):
    def test_owner_basic_flow_comes_before_diagnostics_and_costly_analysis(self):
        expected = (
            'id="autoDailyStart"', 'id="autoForecastJump"',
            'id="forecastRacesSection"',
            'id="autoReferenceQuickPanel"',
            'id="autoReferenceQuickRaces"',
            'id="autoDayDetailSection"', 'id="autoAdvancedResearch"',
            'id="autoFiveQuickSection"', 'id="fixedHistorySection"',
        )
        positions = [HTML.index(v) for v in expected]
        self.assertEqual(positions, sorted(positions))
        for token in expected:
            self.assertEqual(HTML.count(token), 1)
        self.assertIn('href="#forecastRacesSection">予想一覧をすぐ見る（追加のJRDB照会なし）', HTML)
        self.assertIn("<h2>1. 予想を見る</h2>", HTML)
        self.assertIn("<h2>2. 予想を見る・競馬場を選ぶ</h2>", HTML)
        self.assertIn("<h2>3. 公式情報・取得状況・詳しい分析</h2>", HTML)
        self.assertIn("<h2>4. 発走前に固定した買い目</h2>", HTML)
        self.assertIn("JRA公式出馬表を開いて出走・取消・発走時刻を確認", HTML)
        self.assertIn("正式10項目の予想とJRA公式照合は未完成", HTML)

    def test_major_hold_reasons_and_next_action_are_visible_immediately(self):
        # Daily data is read once; these text nodes are filled by the already
        # validated snapshot and must not be hidden in optional diagnostics.
        first = HTML.index('id="autoEasyPulse"')
        reasons = HTML.index('id="autoHoldBreakdown"')
        next_action = HTML.index('id="autoOperationalNext"')
        list_link = HTML.index('id="autoForecastJump"')
        self.assertLess(first, reasons)
        self.assertLess(reasons, next_action)
        self.assertLess(next_action, list_link)
        for token in ('id="autoHoldBreakdown"', 'id="autoOperationalNext"'):
            self.assertEqual(HTML.count(token), 1)
        self.assertIn("holdBreakdownSummary(data)", JS)
        self.assertIn("operationalNextStep(", JS)
        self.assertIn("JRA公式の出走・取消・馬場・発走時刻は未照合", JS)

    def test_advanced_provider_calls_are_inside_closed_opt_in_panel(self):
        start = HTML.index('<section class="daily-start" id="autoDailyStart">')
        stop = HTML.index('<section id="fixedHistorySection">')
        p = _OwnerLayout()
        p.feed(HTML[start:stop])
        p.close()
        self.assertFalse(p.errors, p.errors)
        self.assertFalse(p.stack, "primary and optional UI sections must close")
        parents = p.parents
        self.assertEqual(parents["forecastRacesSection"], ())
        self.assertEqual(parents["autoDayDetailSection"], ())
        self.assertIn(("section", "autoDayDetailSection"),
                      parents["autoAdvancedResearch"])
        self.assertIn(("details", "autoAdvancedResearch"),
                      parents["autoFiveQuickSection"])
        self.assertIn(("section", "autoDayDetailSection"),
                      parents["autoFiveQuickSection"])
        # Hidden by HTML details' default CLOSED state, not by inventing
        # new client permission or making any optional source call.
        opening = HTML[HTML.index('id="autoAdvancedResearch"')-9:
                       HTML.index('id="autoAdvancedResearch"')+45]
        self.assertNotIn(" open", opening)
        self.assertIn("id=\"autoFiveWeekendOptIn\"", HTML)
        self.assertIn("id=\"autoRun\"", HTML)
        self.assertIn("id=\"autoSaturdayQuick\"", HTML)
        self.assertIn("id=\"autoSundayQuick\"", HTML)

    def test_reordering_does_not_remove_race_or_archive_handlers(self):
        self.assertIn("function render(input,day)", JS)
        self.assertIn("validate(body,day)", JS)
        self.assertIn("saveAutoReceipts(body,day)", JS)
        self.assertIn("renderComparableFactorResearch(data,day)", JS)
        self.assertIn("function clearDraftShortcut()", JS)
        self.assertIn(".owner-forecast-cta{", CSS)
        self.assertIn(".owner-advanced-research>summary{", CSS)


if __name__ == "__main__":
    unittest.main()
