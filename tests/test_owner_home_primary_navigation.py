"""Private iPhone home navigation stays simple and environment-aware.

Synthetic WSGI tests only; no provider calls or authentication changes.
"""
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import SETTINGS, call

WIN5_URL = ("https://esakahumihumi1125-byte.github.io/keiba-nine/"
            "keiba-nine-beta51-feed-record.html#win5")


class OwnerPrimaryNavigationTests(unittest.TestCase):
    def page(self, private):
        settings = {**SETTINGS,
                    "KEIBA_RENDER_PRIVATE_ONLY": "1" if private else "0",
                    "KEIBA_RENDER_PREVIEW_ONLY": "0" if private else "1"}
        return call(create_app(settings), "/")["body"].decode("utf-8")

    def main_nav(self, page):
        matches = re.findall(
            r'<nav class="owner-home-four"[^>]*>(.*?)</nav>', page, re.S)
        self.assertEqual(len(matches), 1)
        return re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                          matches[0], re.S)

    def test_private_main_nav_is_four_real_destinations(self):
        page = self.page(True)
        links = self.main_nav(page)
        self.assertEqual([href for href, _ in links], [
            "/owner-auto-forecast", "/owner-100yen-review",
            "/my-tickets", WIN5_URL
        ])
        self.assertIn("結果・100円仮想収支", links[1][1])
        self.assertIn("正式10項目とJRA公式照合は未完成", page)
        self.assertIn("JRA公式の結果照合が未完成", page)
        self.assertIn('rel="noopener noreferrer">🏆 WIN5', page)
        self.assertIn("<details class=\"owner-home-extra\">", page)
        self.assertIn("端末内12種類の記録をバックアップ・復元", page)

    def test_preview_never_links_to_private_only_results_or_auto_draft(self):
        page = self.page(False)
        self.assertEqual([href for href, _ in self.main_nav(page)], [
            "/owner-auto-trial", "/owner-daily-review", "/my-tickets", WIN5_URL
        ])
        self.assertNotIn('href="/owner-100yen-review"', page)
        self.assertNotIn('href="/owner-auto-forecast"', page)
        self.assertIn("補助機能・過去の研究画面を開く", page)
        self.assertIn('href="/owner-backup"', page)

    def test_old_investigation_tools_remain_available_but_collapsed(self):
        page = self.page(True)
        self.assertIn("<summary>旧メニュー・詳しい設定を見る</summary>", page)
        self.assertIn('id="ownerManualSection"', page)
        self.assertIn('id="operatorFactorPanel"', page)
        self.assertIn("Safariとデータが別になることがあります", page)


if __name__ == "__main__":
    unittest.main()
