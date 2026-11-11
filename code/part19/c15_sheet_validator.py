#!/usr/bin/env python3
"""Validate the chapter 19.15 cheat sheet: every row needs a source id that resolves.

A sheet is Markdown. Every table row (a line starting with a pipe, other than the header
and the separator) must end with a source cell holding one or more handbook chapter ids
such as 20.3 or 19.5, separated by commas. An id resolves when the handbook has a chapter
file for it: docs/part-NN-*/MM-*.md for the id NN.MM.

A row may also carry anchors in a trailing HTML comment:

    | fact text | 20.12 | <!--a: 147,456 B per token || 0.36864 GB-->

Each anchor must appear in the cited chapter, after lower-casing and removing backticks,
asterisks and repeated white space. With several ids the anchor may appear in any of them.
An anchor proves that the figure is in the chapter, not that the chapter is right.

Usage: c15_sheet_validator.py [SHEET] [--docs DIR] [--no-anchors]
Exit status 1 when any problem is found.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
from dataclasses import dataclass, field

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SHEET = os.path.join(HERE, "c15_interview_cheat_sheet.md")
DEFAULT_DOCS = os.path.join(HERE, "..", "..", "docs")

ID_RE = re.compile(r"^\d{1,2}\.\d{1,2}$")
ANCHOR_RE = re.compile(r"<!--\s*a:(.*?)-->", re.S)
SEPARATOR_RE = re.compile(r"^\|\s*:?-{2,}")
BANNED_WORDS = ("unverified", "not verified", "todo", "tbd")


@dataclass
class Row:
    line_no: int
    section: str
    cells: list[str]
    source_cell: str
    anchors: list[str]

    @property
    def text(self) -> str:
        return " | ".join(self.cells[:-1])

    @property
    def ids(self) -> list[str]:
        return [p.strip() for p in self.source_cell.split(",") if p.strip()]


@dataclass
class Report:
    rows: int = 0
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def normalise(text: str) -> str:
    text = text.lower().replace("`", "").replace("*", "")
    return re.sub(r"\s+", " ", text)


def parse_sheet(text: str) -> list[Row]:
    """Return the data rows of every table, with the section heading above them."""
    rows: list[Row] = []
    section = ""
    header_seen = False
    for no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if line.startswith("#"):
            section = line.lstrip("#").strip()
            header_seen = False
            continue
        if not line.startswith("|"):
            header_seen = False
            continue
        anchors: list[str] = []
        m = ANCHOR_RE.search(line)
        if m:
            anchors = [a.strip() for a in m.group(1).split("||") if a.strip()]
            line = ANCHOR_RE.sub("", line).strip()
        if SEPARATOR_RE.match(line):
            continue
        if not header_seen:
            header_seen = True  # first line of a table is its header
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip("|"))]
        rows.append(Row(no, section, cells, cells[-1] if cells else "", anchors))
    return rows


_cache: dict[tuple[str, str], str | None] = {}


def chapter_path(chapter_id: str, docs_dir: str) -> str | None:
    """Map an id like 20.3 to docs/part-20-*/03-*.md, or None."""
    if not ID_RE.match(chapter_id):
        return None
    part, num = chapter_id.split(".")
    hits = sorted(glob.glob(os.path.join(docs_dir, f"part-{int(part):02d}-*", f"{int(num):02d}-*.md")))
    return hits[0] if hits else None


def chapter_text(chapter_id: str, docs_dir: str) -> str | None:
    key = (chapter_id, docs_dir)
    if key not in _cache:
        path = chapter_path(chapter_id, docs_dir)
        _cache[key] = normalise(open(path, encoding="utf-8").read()) if path else None
    return _cache[key]


def validate(text: str, docs_dir: str = DEFAULT_DOCS, check_anchors: bool = True) -> Report:
    rep = Report()
    rows = parse_sheet(text)
    rep.rows = len(rows)
    if not rows:
        rep.problems.append("no table rows found")
    for row in rows:
        where = f"line {row.line_no} [{row.section}]"
        low = row.text.lower()
        for word in BANNED_WORDS:
            if word in low:
                rep.problems.append(f"{where}: row contains '{word}'")
        if not row.ids:
            rep.problems.append(f"{where}: no source id")
            continue
        for cid in row.ids:
            if not ID_RE.match(cid):
                rep.problems.append(f"{where}: '{cid}' is not a chapter id")
            elif chapter_path(cid, docs_dir) is None:
                rep.problems.append(f"{where}: source id {cid} does not resolve to a chapter")
        resolvable = [cid for cid in row.ids if chapter_path(cid, docs_dir)]
        if check_anchors and resolvable:
            for anchor in row.anchors:
                needle = normalise(anchor)
                if not any(needle in (chapter_text(c, docs_dir) or "") for c in resolvable):
                    rep.problems.append(f"{where}: anchor '{anchor}' not found in {','.join(resolvable)}")
    return rep


def strip_anchors(text: str) -> str:
    """The sheet as the chapter shows it: no anchor comments."""
    return "\n".join(ANCHOR_RE.sub("", ln).rstrip() for ln in text.splitlines())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("sheet", nargs="?", default=DEFAULT_SHEET)
    ap.add_argument("--docs", default=DEFAULT_DOCS)
    ap.add_argument("--no-anchors", action="store_true")
    a = ap.parse_args()
    rep = validate(open(a.sheet, encoding="utf-8").read(), a.docs, not a.no_anchors)
    for p in rep.problems:
        print("PROBLEM", p)
    print(f"{rep.rows} rows, {len(rep.problems)} problems")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
