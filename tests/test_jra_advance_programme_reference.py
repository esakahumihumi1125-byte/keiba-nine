"""Synthetic-only JRA advance schedule; never certify current racecard/going."""
import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jra_advance_programme_reference import (
    VERSION, calendar_url, parse_advance_programme,
    probe_advance_programme, AdvanceProgrammeError,
)
from private_service import create_app
from test_private_service import SETTINGS, call

DAY = "2026-11-15"
URL = "https://www.jra.go.jp/keiba/calendar2026/2026/11/1115.html"
VENUES = ("東京", "京都", "福島")
NOTICE = (
    "このページの情報は、事前に発表した春季・夏季・秋季の各競馬番組の"
    "内容（予定）です。変更が発生する場合があります。"
)


def sample():
    chunks = [
        "<h1>2026年11月15日（日曜）　競馬番組</h1>",
        "<p>" + NOTICE + "</p>",
    ]
    for track in VENUES:
        chunks.append(f"<h3>5回{track}4日</h3><table>")
        chunks.append("<tr><th>レース番号</th><th>レース名・条件</th><th>発走時刻</th></tr>")
        for race in range(1, 13):
            # Three documented 2026-11-15 JRA facts (the other 33 rows
            # are SYNTHETIC and must not be presented as live results).
            if track == "東京" and race == 1:
                course, off = "2歳未勝利 1,400（ダ）", "9時45分"
            elif track == "京都" and race == 11:
                course, off = "3歳以上オープン 2,200（芝・外）", "15時40分"
            elif track == "福島" and race == 4:
                course, off = "障害3歳以上未勝利 2,750（芝）", "11時05分"
            else:
                course = ("2歳未勝利 1,400（ダ）" if race == 1
                          else "3歳以上3勝クラス 1,800（芝・外）")
                off = f"{9 + race // 5}時{(race * 5) % 60:02d}分"
            chunks.append(
                f"<tr><td>{race}レース</td><td>{course}</td>"
                f"<td>{off}</td></tr>"
            )
        chunks.append("</table>")
    return "<html><body><script>bad 5回中山1日</script>" + "".join(chunks) + "</body></html>"


class AdvanceProgrammeTests(unittest.TestCase):
    def test_complete_three_venue_36_scheduled_races_without_runners(self):
        report = parse_advance_programme(sample(), DAY)
        self.assertEqual(report["version"], VERSION)
        self.assertEqual(report["referenceKind"],
                         "advance_schedule_not_final_racecard")
        self.assertEqual(report["raceCount"], 36)
        self.assertEqual(report["venueCount"], 3)
        self.assertEqual(len(report["races"]), 36)
        self.assertEqual(report["races"][0], {
            "track": "東京", "race": 1, "postTime": "09:45",
            "distanceM": 1400, "surface": "ダート",
        })
        self.assertEqual(report["races"][3]["surface"], "芝")
        self.assertIsNone(report["races"][27]["surface"])  # 福島4R障害
        self.assertEqual(report["races"][22], {
            "track": "京都", "race": 11, "postTime": "15:40",
            "distanceM": 2200, "surface": "芝"})
        self.assertEqual(report["races"][27]["postTime"], "11:05")
        for flag in (
            "officialFinalCardVerified", "officialStartersVerified",
            "officialScratchesVerified", "officialGoingVerified",
            "officialPostTimeVerified", "predictionReady", "bettingReady",
            "existingTicketsChanged", "existingReceiptsChanged",
        ):
            self.assertIs(report[flag], False)
        self.assertEqual(report["newJrdbRequests"], 0)
        for secret in ("horse_id", "racekey", "馬名", "馬主", "単勝"):
            self.assertNotIn(secret, repr(report))

    def test_dated_exact_url_and_one_public_get_only(self):
        calls = []
        def get(url):
            calls.append(url)
            self.assertEqual(url, URL)
            return sample()
        report = probe_advance_programme(
            DAY, today=date(2026, 11, 16), fetch_html=get)
        self.assertEqual(report["raceCount"], 36)
        self.assertEqual(calls, [URL])
        self.assertEqual(calendar_url(DAY), URL)
        self.assertEqual(calendar_url("2026-12-05"),
                         "https://www.jra.go.jp/keiba/calendar2026/2026/12/1205.html")

    def test_partial_duplicate_wrong_date_or_spoofed_html_fail_closed(self):
        original = sample()
        for altered in (
            original.replace("2026年11月15日", "2026年11月14日", 1),
            original.replace(NOTICE, ""),
            original.replace("<h3>5回福島4日</h3>", "<h3>5回東京4日</h3>"),
            original.replace("<td>12レース</td>", "<td>11レース</td>", 1),
            original.replace("1,400（ダ）", "1,400（不明）", 1),
            original.replace("9時45分", "無時刻", 1),
            original.replace("<td>1レース</td>", "<td>取消</td>", 1),
            original + "<h3>5回阪神4日</h3><table></table>",
        ):
            with self.subTest(sample=altered[:150]):
                with self.assertRaises(AdvanceProgrammeError):
                    parse_advance_programme(altered, DAY)
        for value in ("20261115", "2026-02-29", "2026-13-01",
                      "2026-11-15?date=bad", "2019-11-15"):
            with self.assertRaises(AdvanceProgrammeError):
                calendar_url(value)

    def test_future_or_out_of_window_does_not_fetch(self):
        called = []
        for day in ("2026-09-01", "2027-01-10"):
            with self.subTest(day=day):
                with self.assertRaises(AdvanceProgrammeError):
                    probe_advance_programme(
                        day, today=date(2026, 11, 16),
                        fetch_html=lambda url: called.append(url))
        self.assertEqual(called, [])

    def test_owner_route_uses_manual_free_reference_only(self):
        report = parse_advance_programme(sample(), DAY)
        app = create_app(SETTINGS)
        with patch("private_service.probe_advance_programme",
                   return_value=report) as getter, \
             patch("private_service.fetch_race_program") as paid:
            resp = call(app, "/api/jra/advance-programme",
                        QUERY_STRING="date=" + DAY)
            self.assertEqual(resp["status"], "200 OK")
            self.assertIn(b'"referenceKind": "advance_schedule_not_final_racecard"',
                          resp["body"])
            self.assertIn(b'"newJrdbRequests": 0', resp["body"])
            getter.assert_called_once_with(DAY)
            for params in ("", "date=bad", "date=" + DAY + "&date=" + DAY,
                           "date=" + DAY + "&track=東京"):
                response = call(app, "/api/jra/advance-programme",
                                QUERY_STRING=params)
                self.assertEqual(response["status"], "400 Bad Request")
            denied = call(app, "/api/jra/advance-programme",
                          QUERY_STRING="date=" + DAY, auth="")
            self.assertEqual(denied["status"], "401 Unauthorized")
            paid.assert_not_called()


if __name__ == "__main__":
    unittest.main()
