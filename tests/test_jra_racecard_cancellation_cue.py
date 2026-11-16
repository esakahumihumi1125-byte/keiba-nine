"""Synthetic JRA horse-table caution cues: no official status attestation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jra_racecard_cancellation_cue import (
    racecard_cancellation_cue, racecard_number_candidates,
)
from jra_prestart_card_candidate import parse_prestart_card_candidate
from test_jra_prestart_card_candidate import MOBILE, DAY

HEAD = """<!doctype html><html><body><h1>出馬表</h1>
<p>2026年11月14日（土曜）5回京都3日</p><h2>1R</h2>
<p>発走時刻：10時00分 コース：1,400メートル（ダート・右）</p>
<div>枠 馬番 馬名 / 単勝オッズ</div>"""
TABLE = """<table><tr><th>枠</th><th>馬番</th>
<th>馬名 / 単勝オッズ(人気)</th><th>性齢</th></tr>
<tr><td><img alt="枠1白"></td><td>1</td><td>架空の馬A</td><td>牡2</td></tr>
<tr><td><img alt="枠2黒"></td><td>取消</td>
<td>架空の馬B<span>取消</span></td><td>牝2</td></tr>
<tr><td><img alt="枠3赤"></td><td>3</td><td>架空の馬C</td><td>牡2</td></tr></table>"""


class CancellationCueTests(unittest.TestCase):
    def test_current_horse_number_cell_explicitly_cancelled(self):
        html = HEAD + TABLE + "</body></html>"
        self.assertIs(racecard_cancellation_cue(html), True)
        snapshot = parse_prestart_card_candidate(
            html, MOBILE, DAY, "京都", 1)
        self.assertIs(snapshot["cancellationCueCandidate"], True)
        self.assertIsNone(snapshot["horseNumbersCandidate"])
        self.assertIs(snapshot["officialScratchesVerified"], False)
        self.assertIs(snapshot["officialStartersVerified"], False)
        self.assertIs(snapshot["bettingReady"], False)
        self.assertEqual(snapshot["newJrdbProviderRequests"], 0)
        for private in ("架空の馬A", "架空の馬B", "架空の馬C",
                        "取消がなかった", "horse_number"):
            self.assertNotIn(private, repr(snapshot))

    def test_no_cue_does_not_mean_scratch_free(self):
        no_marker = TABLE.replace("<td>取消</td>", "<td>2</td>")
        self.assertIsNone(racecard_cancellation_cue(HEAD + no_marker))
        snapshot = parse_prestart_card_candidate(
            HEAD + no_marker, MOBILE, DAY, "京都", 1)
        self.assertIsNone(snapshot["cancellationCueCandidate"])
        self.assertEqual(snapshot["horseNumbersCandidate"], [1, 2, 3])
        self.assertFalse(snapshot["officialScratchesVerified"])

    def test_past_race_and_unrelated_table_cancellation_ignored(self):
        safe = TABLE.replace("<td>取消</td>", "<td>2</td>")
        irrelevant = """<table><tr><th>過去走</th><th>馬番</th><th>馬名</th></tr>
<tr><td>昨日</td><td>取消</td><td>古い結果</td></tr></table>"""
        self.assertIsNone(racecard_cancellation_cue(HEAD+safe+irrelevant))
        # Mentions of 取消 outside the current 馬番 cell are never a trigger.
        note = safe.replace("<td>架空の馬C</td>", "<td>架空の馬C 取消の噂</td>")
        self.assertIsNone(racecard_cancellation_cue(HEAD+note))

    def test_wrong_column_ambiguous_headers_or_scripts_are_ignored(self):
        wrong = TABLE.replace("<td>取消</td>", "<td>2</td>").replace(
            "<td>架空の馬B<span>取消</span></td>",
            "<td>取消</td>")
        self.assertIsNone(racecard_cancellation_cue(HEAD+wrong))
        self.assertIsNone(racecard_cancellation_cue(HEAD+TABLE+TABLE))
        self.assertIsNone(racecard_cancellation_cue(
            HEAD+'<script>'+TABLE+'</script>'))
        self.assertIsNone(racecard_cancellation_cue(None))
        self.assertIsNone(racecard_cancellation_cue('x'*480001))

    def test_unsupported_row_is_not_a_confirmation_of_no_scratch(self):
        # Some JRA layouts may differ: conservatively withhold instead
        # of reading a fake number or claiming official completeness.
        without_rows = """<table><tr><th>枠</th><th>馬番</th>
        <th>馬名</th></tr><tr><td>取消</td><td>unknown</td>
        <td>未確認</td></tr></table>"""
        self.assertIsNone(racecard_cancellation_cue(HEAD+without_rows))


    def test_number_candidates_are_strict_not_completeness_or_official_status(self):
        clean = HEAD + TABLE.replace("<td>取消</td>", "<td>2</td>")
        self.assertEqual(racecard_number_candidates(clean), [1, 2, 3])
        snap = parse_prestart_card_candidate(clean, MOBILE, DAY, "京都", 1)
        self.assertEqual(snap["horseNumbersCandidate"], [1, 2, 3])
        self.assertFalse(snap["officialStartersVerified"])
        self.assertFalse(snap["officialScratchesVerified"])
        self.assertFalse(snap["formalTenFactorReady"])
        self.assertFalse(snap["bettingReady"])
        self.assertNotIn("架空の馬", repr(snap))

        variants = (
            clean.replace("<td>2</td>", "<td>1</td>"),  # duplicates
            clean.replace("<td>2</td>", "<td>19</td>"),  # invalid range
            clean.replace("<td>2</td>", "<td>未定</td>"),
            clean.replace("<td>2</td>", "<td>除外</td>"),
            clean + clean[clean.index("<table>"):],  # two horse tables
            clean.replace("<td>架空の馬B<span>取消</span></td>",
                          "<td></td>"),  # missing horse-name cell
            HEAD + "<script>" + clean[clean.index("<table>"):] + "</script>",
            HEAD + "<table><tr><th>枠</th><th>馬番</th><th>馬名</th></tr></table>",
        )
        for html in variants:
            with self.subTest(html=html[:80]):
                self.assertIsNone(racecard_number_candidates(html))


if __name__ == "__main__":
    unittest.main()
