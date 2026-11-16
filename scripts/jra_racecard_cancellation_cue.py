"""Conservative warning-only marker from the current JRA racecard horse table.

This is not a trusted complete starters/scratches feed. It returns True only
when a table explicitly headed 枠 / 馬番 / 馬名 contains a horse row whose
馬番 cell reads 取消 or 除外. None means NOT PROVEN, never 'no scratches'.
No horse names, source HTML, licensed data, wagers or standings are returned.
The caller validates URL/date/venue/race *before* invoking this parser.
"""
from html.parser import HTMLParser
import re

MAX_ROWS = 1200
MAX_CELL_CHARS = 1500
SCRATCH_MARKERS = frozenset(("取消", "除外"))


class _HorseTableCells(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.table_id = 0
        self.tables = []
        self.rows = []
        self.row_stack = []
        self.cell_stack = []
        self.skips = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "svg"):
            self.skips.append(tag)
            return
        if self.skips:
            return
        if tag == "table":
            self.table_id += 1
            self.tables.append(self.table_id)
        elif tag == "tr" and self.tables:
            self.row_stack.append({"table": self.tables[-1], "cells": []})
        elif (tag in ("th", "td") and self.tables and self.row_stack
              and self.row_stack[-1]["table"] == self.tables[-1]):
            self.cell_stack.append({"row": self.row_stack[-1],
                                    "tag": tag, "parts": [], "length": 0})

    def handle_data(self, data):
        if self.skips or not self.cell_stack:
            return
        cell = self.cell_stack[-1]
        room = MAX_CELL_CHARS - cell["length"]
        if room > 0:
            fragment = data[:room]
            cell["parts"].append(fragment)
            cell["length"] += len(fragment)

    def handle_endtag(self, tag):
        if self.skips:
            if tag == self.skips[-1]:
                self.skips.pop()
            return
        if tag in ("th", "td") and self.cell_stack and self.cell_stack[-1]["tag"] == tag:
            cell = self.cell_stack.pop()
            cell["row"]["cells"].append(
                (tag, " ".join("".join(cell["parts"]).split())))
        elif tag == "tr" and self.row_stack:
            row = self.row_stack.pop()
            if len(self.rows) < MAX_ROWS:
                self.rows.append(row)
        elif tag == "table" and self.tables:
            self.tables.pop()


def racecard_cancellation_cue(html):
    """Return True when a supported horse table shows an explicit cancellation.

    None means missing/unsupported/ambiguous, NEVER a negative official status.
    Ignore any '取消' in navigation, past starts, history or unrelated tables.
    """
    if type(html) is not str or not html or len(html) > 480000:
        return None
    reader = _HorseTableCells()
    try:
        reader.feed(html)
        reader.close()
    except Exception:
        return None
    # Recognize only a narrow racecard table header, not results/history
    # tables that may independently contain 取消 for past performances.
    horse_tables = set()
    for row in reader.rows:
        cells = row["cells"]
        if (not cells or len(cells) > 12
                or not any(tag == "th" for tag, _ in cells)):
            continue
        header = " ".join(text for _, text in cells)
        if (len(header) < 450 and "枠" in header
                and "馬番" in header and "馬名" in header):
            horse_tables.add(row["table"])
    if len(horse_tables) != 1:
        return None
    target = next(iter(horse_tables))
    for row in reader.rows:
        if row["table"] != target:
            continue
        cells = row["cells"]
        if (len(cells) < 3 or len(cells) > 10
                or cells[0][0] != "td" or cells[1][0] != "td"
                or cells[2][0] != "td"):
            continue
        # JRA places 取消 in the 馬番 cell rather than its original number.
        # We MUST NOT infer a scratched horse number from surrounding rows.
        number_cell = re.sub(r"\s+", "", cells[1][1])
        if (number_cell in SCRATCH_MARKERS
                and cells[2][1] and len(cells[2][1]) <= MAX_CELL_CHARS):
            return True
    return None


def racecard_number_candidates(html):
    """Read only visible horse-number *candidates* from one narrow racecard table.

    Do not claim a complete field or absence of withdrawals: page contents may
    be cached or partial. Invalid, ambiguous or scratched rows return None.
    Names, raw HTML and other JRA table data never leave this function.
    """
    if type(html) is not str or not html or len(html) > 480000:
        return None
    reader = _HorseTableCells()
    try:
        reader.feed(html)
        reader.close()
    except Exception:
        return None
    targets = set()
    for row in reader.rows:
        cells = row["cells"]
        if (len(cells) >= 3 and len(cells) <= 12
                and all(tag == "th" for tag, _ in cells[:3])
                and cells[0][1].replace(" ", "") in ("枠", "枠番")
                and cells[1][1].replace(" ", "") == "馬番"
                and cells[2][1].replace(" ", "").startswith("馬名")):
            targets.add(row["table"])
    if len(targets) != 1:
        return None
    table = next(iter(targets))
    numbers = set()
    for row in reader.rows:
        if row["table"] != table:
            continue
        cells = row["cells"]
        if cells and cells[0][0] == "th":
            continue
        if (not 3 <= len(cells) <= 12
                or any(tag != "td" for tag, _ in cells[:3])
                or not cells[2][1] or len(cells[2][1]) > MAX_CELL_CHARS):
            return None
        value = re.sub(r"\s+", "", cells[1][1])
        if not re.fullmatch(r"(?:0?[1-9]|1[0-8])", value, re.ASCII):
            # Includes 取消/除外: the original number cannot be recovered.
            return None
        number = int(value)
        if number in numbers:
            return None
        numbers.add(number)
    return sorted(numbers) if 2 <= len(numbers) <= 18 else None
