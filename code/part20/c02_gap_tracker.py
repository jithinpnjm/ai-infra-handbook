#!/usr/bin/env python3
"""Rank study order from the filled self-assessment table in chapter 20.2.

Reads a markdown file, finds the first table whose header has the columns
"Skill", "Posting lines", "Confidence" and "Chapter to study", and prints the
skills in study order. Priority = (5 - confidence) * number of posting lines.
Standard library only.

Usage: python3 c02_gap_tracker.py assessment.md
"""
import re
import sys
from dataclasses import dataclass

SEPARATOR = re.compile(r"^:?-{3,}:?$")
BLANKS = {"", "?", "-", "_", "n/a", "tbd"}


@dataclass
class Row:
    skill: str
    confidence: "int | None"
    lines: int
    evidence: str
    chapter: str

    @property
    def priority(self):
        return 0 if self.confidence is None else (5 - self.confidence) * self.lines


def split_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def count_lines(cell):
    """'R3, Q1, R8' -> 3. A bare number such as '3' is used as the count. Empty -> 1."""
    cell = cell.strip()
    if re.fullmatch(r"\d+", cell):
        return max(1, int(cell))
    items = [x for x in re.split(r"[,;]", cell) if x.strip()]
    return max(1, len(items))


def parse_confidence(cell, skill):
    cell = cell.strip()
    if cell.lower() in BLANKS:
        return None
    if not re.fullmatch(r"[1-5]", cell):
        raise ValueError(f"confidence for {skill!r} must be 1 to 5, got {cell!r}")
    return int(cell)


def parse_table(text):
    """Return a list of Row from the first matching table. Raise ValueError if none."""
    rows, cols = [], None
    for raw in text.splitlines():
        if not raw.strip().startswith("|"):
            if cols and rows:
                break
            continue
        cells = split_row(raw)
        if all(SEPARATOR.match(c) for c in cells if c):
            continue
        lowered = [c.lower() for c in cells]
        if cols is None:
            if "skill" in lowered and any(c.startswith("confidence") for c in lowered):
                cols = {
                    "skill": lowered.index("skill"),
                    "lines": next((i for i, c in enumerate(lowered) if c.startswith("posting")), None),
                    "conf": next(i for i, c in enumerate(lowered) if c.startswith("confidence")),
                    "evidence": next((i for i, c in enumerate(lowered) if c.startswith("evidence")), None),
                    "chapter": next((i for i, c in enumerate(lowered) if c.startswith("chapter")), None),
                }
            continue
        def cell(key):
            i = cols[key]
            return cells[i] if i is not None and i < len(cells) else ""
        skill = cell("skill")
        if not skill:
            continue
        rows.append(Row(skill, parse_confidence(cell("conf"), skill),
                        count_lines(cell("lines")), cell("evidence"), cell("chapter")))
    if cols is None:
        raise ValueError("no table with Skill and Confidence columns found")
    return rows


def study_order(rows):
    """Rated rows, highest priority first. Ties: lower confidence, then skill name."""
    rated = [r for r in rows if r.confidence is not None]
    return sorted(rated, key=lambda r: (-r.priority, r.confidence, r.skill.lower()))


def warnings(rows):
    out = []
    for r in rows:
        if r.confidence is None:
            out.append(f"not rated: {r.skill}")
        elif r.confidence >= 4 and not r.evidence.strip():
            out.append(f"confidence {r.confidence} without evidence: {r.skill}")
    return out


def render(rows):
    lines = []
    for n, r in enumerate(study_order(rows), 1):
        study = r.chapter or "(no chapter given)"
        lines.append(f"{n:>2}. {r.skill} | priority {r.priority} "
                     f"(5-{r.confidence})x{r.lines} | study: {study}")
    lines += [f"warning: {w}" for w in warnings(rows)]
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        text = f.read()
    try:
        rows = parse_table(text)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(render(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
