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
            self.row_stack.append({"table": self.tables[-1], "cells": [], "spans": []})
        elif (tag in ("th", "td") and self.tables and self.row_stack
              and self.row_stack[-1]["table"] == self.tables[-1]):
            attributes = dict(attrs)
            self.cell_stack.append({"row": self.row_stack[-1],
                                    "tag": tag, "parts": [], "length": 0,
                                    "rowspan": attributes.get("rowspan", "1"),
                                    "colspan": attributes.get("colspan", "1")})

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
            cell["row"]["spans"].append((cell["rowspan"], cell["colspan"]))
        elif tag == "tr" and self.row_stack:
            row = self.row_stack.pop()
            if len(self.rows) < MAX_ROWS:
                self.rows.append(row)
        elif tag == "table" and self.tables:
            self.tables.pop()


def _effective_horse_rows(html):
    """Resolve only explicit frame-column rowspans in one current horse table.

    JRA may display a frame cell once for two or three horses. Restore the
    column position, never a horse number or a missing/cancelled identity.
    Other spans in the identity columns, incomplete carries and ambiguous
    headers fail closed instead of shifting a name into the number column.
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
        if (3 <= len(cells) <= 12
                and all(tag == "th" for tag, _ in cells[:3])
                and cells[0][1].replace(" ", "") in ("枠", "枠番")
                and cells[1][1].replace(" ", "") == "馬番"
                and cells[2][1].replace(" ", "").startswith("馬名")):
            targets.add(row["table"])
    if len(targets) != 1:
        return None
    target = next(iter(targets))
    carry, carry_width, rows = 0, 0, []
    for row in reader.rows:
        if row["table"] != target:
            continue
        cells, spans = row["cells"], row["spans"]
        if cells and cells[0][0] == "th":
            if carry:
                return None
            continue
        if len(cells) != len(spans):
            return None
        if carry:
            # The frame column is occupied by the previous explicit rowspan.
            # We need two actual identity cells: horse number and name.
            if (len(cells) != carry_width or len(cells) < 2
                    or spans[:2] != [("1", "1"), ("1", "1")]):
                return None
            cells = [("td", "")] + cells
            carry -= 1
        else:
            if len(cells) < 3 or spans[0] not in (
                    ("1", "1"), ("2", "1"), ("3", "1")):
                return None
            if spans[1:3] != [("1", "1"), ("1", "1")]:
                return None
            carry = int(spans[0][0]) - 1
            carry_width = len(cells) - 1
        if (not 3 <= len(cells) <= 12
                or any(tag != "td" for tag, _ in cells[:3])
                or not cells[2][1] or len(cells[2][1]) > MAX_CELL_CHARS):
            return None
        rows.append(cells)
        if len(rows) > 18:
            return None
    return rows if not carry else None


def racecard_cancellation_cue(html):
    """True only for an explicit supported cancellation, otherwise unknown."""
    rows = _effective_horse_rows(html)
    if rows is None:
        return None
    for cells in rows:
        if re.sub(r"\s+", "", cells[1][1]) in SCRATCH_MARKERS:
            return True
    return None


def racecard_number_candidates(html):
    """Read visible candidates only, never certify completeness or scratches."""
    rows = _effective_horse_rows(html)
    if rows is None:
        return None
    numbers = set()
    for cells in rows:
        value = re.sub(r"\s+", "", cells[1][1])
        if not re.fullmatch(r"(?:0?[1-9]|1[0-8])", value, re.ASCII):
            # Includes 取消/除外: the original number cannot be recovered.
            return None
        number = int(value)
        if number in numbers:
            return None
        numbers.add(number)
    return sorted(numbers) if 2 <= len(numbers) <= 18 else None
