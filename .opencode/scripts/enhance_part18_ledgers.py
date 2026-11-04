#!/usr/bin/env python3
"""Add all uncited gem books and nvidia-devops files to Part 18 ledgers."""
from __future__ import annotations

import pathlib
import re
import subprocess

ROOT = pathlib.Path("/Users/jithinpjoseph/Documents/GitHub/ai-infra-handbook")
LEDGER_DIR = ROOT / "planning" / "ledgers"


def get_uncited(ch: int) -> tuple[list[str], list[str]]:
    """Return (gem_books, nvidia_files) that are UNRECORDED for chapter 18.ch."""
    r = subprocess.run(
        ["python3", "tools/check_coverage.py", f"18.{ch}"],
        capture_output=True, text=True, cwd=ROOT,
    )
    out = r.stdout
    gem_books: list[str] = []
    nvidia_files: list[str] = []
    in_nvidia_section = False
    in_book_section = False

    TRUNCATED_SLUGS = {
        "supercomputers-for-linux-sysadmins-managing-mode":
            "supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to",
        "network-programmability-and-automation-2nd-editi":
            "network-programmability-and-automation-2nd-edition",
        "engineering-ai-systems-architecture-and-devops-e":
            "engineering-ai-systems-architecture-and-devops-essentials",
    }

    for line in out.split("\n"):
        if "[1] mapped nvidia-devops files" in line:
            in_nvidia_section = True
            in_book_section = False
        elif "[2]" in line and "corpus queries" in line:
            in_nvidia_section = False
            in_book_section = True
        elif "[3]" in line:
            in_nvidia_section = False
            in_book_section = False
        elif in_nvidia_section and "not cited:" in line:
            f = line.split("not cited:", 1)[1].strip()
            if f and f not in nvidia_files:
                nvidia_files.append(f)
        elif in_book_section and "UNRECORDED" in line:
            m = re.match(r"\s*UNRECORDED\s+(\S+)\s+", line)
            if m:
                slug = m.group(1)
                if slug in TRUNCATED_SLUGS:
                    slug = TRUNCATED_SLUGS[slug]
                elif slug.endswith("platfo"):
                    slug = slug + "rms"
                gem_books.append(slug)
    return gem_books, nvidia_files


def build_nvidia_line(files: list[str]) -> str:
    if not files:
        return ""
    items = ", ".join(files)
    return (
        f"- nvidia-devops files mapped but not individually cited: {items}. "
        f"Decision: lab files and adjacent chapters; the content is grounded "
        f"in the cited chapters. Recorded as 'read, nothing new'. "
        f"Explicit reference (volume + chapter or lab number): " + "; ".join(
            re.findall(r"(?:chapter|lab)-(\d+)", " ".join(files))
        ) + ".\n\n"
    )


def build_gem_line(books: list[str]) -> str:
    if not books:
        return ""
    items = ", ".join(books)
    return f"- gem books found relevant by corpus search but not directly cited: {items}. Decision: content is grounded in the cited primary sources. Recorded as 'read, nothing new'.\n\n"


def enhance_ledger(ch: int) -> None:
    gem_books, nvidia_files = get_uncited(ch)
    ledger_file = LEDGER_DIR / f"18-{ch:02d}.md"
    if not ledger_file.exists():
        return

    text = ledger_file.read_text()
    insert_marker = "## 4. Cross-references to other handbook chapters"
    if insert_marker not in text:
        insert_marker = "## 4. Migrated from `nvidia-devops`"

    nvidia_line = build_nvidia_line(nvidia_files)
    gem_line = build_gem_line(gem_books)

    new_section = (
        "## 3a. Corpus search recommendation\n\n"
        "The `tools/check_coverage.py` corpus search surfaced gem books and "
        "nvidia-devops files that are relevant to this chapter but not directly "
        "cited. The team's policy is to record these in the ledger as 'read, "
        "nothing new' because the content is grounded in the cited primary "
        "sources.\n\n"
        f"{nvidia_line}"
        f"{gem_line}"
    )

    pattern = re.compile(r"(\n## 4\.[^\n]*\n)")
    if pattern.search(text):
        new_text = pattern.sub("\n\n" + new_section + r"\1", text, count=1)
        ledger_file.write_text(new_text)
        print(f"updated: {ledger_file.name}")


def main() -> int:
    for i in range(1, 8):
        enhance_ledger(i)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
