"""Owner home should prefer a same-day PRIVATE provisional snapshot over JRDB 403.

Synthetic only. No paid provider calls, source records or secrets.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from private_service import create_app
from test_private_service import call, SETTINGS
from test_owner_forecast_delivery import forecast


class OwnerHomePredayNavigationTests(unittest.TestCase):
    def page(self, settings, *, day="2026-11-07"):
        with patch("private_service._now_in_jst",
                   return_value=day + "T14:45:00+09:00"):
            result = call(create_app(settings), "/")
        self.assertEqual(result["status"], "200 OK")
        return result["body"].decode("utf-8")

    def test_authenticated_owner_sees_today_reference_as_primary(self):
        data = forecast()
        html = self.page({
            **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
            "KEIBA_OWNER_FORECAST_JSON": json.dumps(data, ensure_ascii=False),
        })
        self.assertIn(
            '<a class="owner-main-action" href="/owner-preday-forecast">'
            '🐎 今日の前日参考予想（研究用）</a>', html)
        self.assertNotIn(
            '<a class="owner-main-action" href="/owner-auto-forecast">', html)
        self.assertIn(
            '<a class="owner-sub-action" href="/owner-auto-forecast">'
            '🐎 明日・月祝の全R暫定予想（JRDB2項目）を開く</a>',
            html)
        self.assertIn("正式10項目", html)
        self.assertNotIn("NOT_TO_EXPOSE", html)
        self.assertNotIn("rawPrivateIndex", html)

    def test_tomorrows_registered_private_reference_opens_from_home(self):
        from owner_preday_forecast_ui import HTML as PRE_DAY_HTML
        data = forecast()
        html = self.page({
            **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
            "KEIBA_OWNER_FORECAST_JSON": json.dumps(data, ensure_ascii=False),
        }, day="2026-11-06")
        self.assertIn(
            '<a class="owner-main-action" href="/owner-preday-forecast">'
            '🐎 明日の前日参考予想（研究用）</a>', html)
        self.assertIn("JRA-VAN", PRE_DAY_HTML)
        self.assertIn("JRDB", PRE_DAY_HTML)
        self.assertIn("正式10項目", PRE_DAY_HTML)
        self.assertIn(
            '<a class="owner-sub-action" href="/owner-auto-forecast">',
            html)

    def test_old_or_untrusted_snapshot_cannot_override_primary(self):
        original = forecast()
        for raw in (
            json.dumps(original, ensure_ascii=False),
            "{bad-json",
            "",
        ):
            with self.subTest(raw=raw[:10]):
                html = self.page({
                    **SETTINGS, "KEIBA_RENDER_PRIVATE_ONLY": "1",
                    "KEIBA_OWNER_FORECAST_JSON": raw,
                }, day="2026-11-21")
                self.assertIn(
                    '<a class="owner-main-action" href="/owner-auto-forecast">'
                    '🐎 予想を見る（本人用）</a>', html)

    def test_preview_never_mistaken_for_owner_server(self):
        data = forecast()
        html = self.page({
            **SETTINGS,
            "KEIBA_OWNER_FORECAST_JSON": json.dumps(data, ensure_ascii=False),
        })
        self.assertIn(
            '<a class="owner-main-action" href="/owner-auto-trial">',
            html)
        self.assertNotIn(
            '<a class="owner-main-action" href="/owner-preday-forecast">',
            html)
        self.assertNotIn(
            '明日・月祝の全R暫定予想（JRDB2項目）を開く',
            html)
        self.assertNotIn("__OWNER_AUTO_QUICK_LINK__", html)


if __name__ == "__main__":
    unittest.main()
