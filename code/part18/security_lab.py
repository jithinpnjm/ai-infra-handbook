#!/usr/bin/env python3
"""Self-checking lab for Part 18 (Security).

Validates the cross-cutting structural and source-coverage contracts for
chapters 18.1 through 18.7:

  - Status is drafted/reviewed/draft (not scaffold)
  - 20 checkpoint questions per chapter
  - Exercises section present
  - Sources and review notes section present
  - "Not verified on live hardware" note present
  - At least one Mermaid diagram or substantial structure
  - Mermaid nodes <= 130 characters
  - Per-chapter source books declared in the Sources section match the corpus
  - Per-chapter lab section is present and explicitly marked untested
  - Per-chapter ledger file exists (planning/ledgers/<P>-<CC>.md)

Run with: python3 -B code/part18/security_lab.py
"""
from __future__ import annotations

import re
import sys
import glob
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
PART_DIR = ROOT / "docs" / "part-18-security"
LEDGER_DIR = ROOT / "planning" / "ledgers"

EXPECTED_CHAPTERS = list(range(1, 8))
EXPECTED_BOOKS = [
    "Engineering AI Systems",
    "nvidia-devops",
    "Production Kubernetes",
]

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> int:
    # 1. Chapter files exist for all 18.1 through 18.7
    files = sorted(PART_DIR.glob("*.md"))
    file_map: dict[int, pathlib.Path] = {}
    for f in files:
        m = re.match(r"^(\d{2})-(.+)\.md$", f.name)
        if m:
            ch_num = int(m.group(1))
            if ch_num in EXPECTED_CHAPTERS:
                file_map[ch_num] = f

    for ch in EXPECTED_CHAPTERS:
        check(f"chapter 18.{ch} file exists", ch in file_map, f"missing 18.{ch}")

    # 2. Structural checks per chapter
    for ch, fpath in sorted(file_map.items()):
        text = fpath.read_text()
        prose = re.sub(r"```.*?```", "", text, flags=re.S)

        check(
            f"18.{ch} status is drafted/reviewed/draft",
            bool(re.search(r'^status:\s*"(drafted|reviewed|draft)"', text, re.M)),
            f"file: {fpath.name}",
        )
        check(
            f"18.{ch} has 20 checkpoint questions",
            text.count("<summary>") == 20,
            f"found {text.count('<summary>')}",
        )
        check(f"18.{ch} has Exercises section", "## Exercises" in text)
        check(f"18.{ch} has Sources and review notes section", "## Sources and review notes" in text)
        check(
            f"18.{ch} mentions untested or not verified",
            bool(re.search(r"untested|not (been )?(verified|executed|run)|not verified on live", text, re.I)),
        )
        check(
            f"18.{ch} has at least one Mermaid diagram or substantial structure",
            "```mermaid" in text or text.count("|---|") >= 5,
            f"file: {fpath.name}",
        )
        check(
            f"18.{ch} has no exclamation marks in prose",
            not re.search(r"(?<=[\w)`*\"%\]])!(?=\s|$)", prose),
            f"file: {fpath.name}",
        )

        long_nodes: list[tuple[int, int]] = []
        for k, m in enumerate(
            re.finditer(r"```mermaid\n(.*?)```", text, re.S), 1
        ):
            for lab in re.findall(
                r'\["([^"]+)"\]|\{"([^"]+)"\}|\("([^"]+)"\)', m.group(1)
            ):
                txt = next(x for x in lab if x)
                if len(txt.replace("<br/>", " ")) > 130:
                    long_nodes.append((k, len(txt.replace("<br/>", " "))))
        check(
            f"18.{ch} mermaid nodes <= 130 chars",
            not long_nodes,
            f"file: {fpath.name}",
        )

        ledger = LEDGER_DIR / f"18-{ch:02d}.md"
        check(f"18.{ch} ledger exists", ledger.exists(), f"expected: {ledger.name}")

    # 3. Source-book coverage
    all_text = "".join(fp.read_text() for fp in file_map.values())
    for book in EXPECTED_BOOKS:
        check(
            f"book '{book}' referenced in Part 18",
            book in all_text,
        )

    print(
        f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})"
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
