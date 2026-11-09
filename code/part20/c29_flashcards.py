# code/part20/c29_flashcards.py
"""Extract the drill questions of the Volume 20 chapters into a CSV.

Usage: python3 c29_flashcards.py DOCS_DIR OUT.csv [--answers] [--start 2026-11-09]

Three markdown shapes exist in the chapters, all inside "## Drill questions":
  A. <details><summary>3. Question?</summary> then the answer
  B. <details> and <summary>3. Question?</summary> on separate lines
  C. a numbered line "3. Question?" then <details><summary>Answer</summary>
Answers are left out unless --answers is given. Each card also gets a
Leitner box (1) and a first due date, so the CSV can seed a review tool.
"""
import argparse
import csv
import datetime as dt
import pathlib
import re

ID_RE = re.compile(r'^id:\s*"?c20-(\d+)"?\s*$', re.M)
SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>")
NUM_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
FIELDS = ["card_id", "chapter", "number", "question", "box", "due"]


def chapter_id(text):
    m = ID_RE.search(text)
    return f"20.{int(m.group(1))}" if m else None


def drill_section(text):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## Drill questions":
            start = i + 1
            break
    if start is None:
        return []
    out = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        out.append(line)
    return out


def parse_drills(text):
    """Return a list of (number, question, answer) from one chapter."""
    cards = []
    pending = None          # numbered line seen outside a details block
    in_details = False
    summary = None
    answer = []
    for line in drill_section(text):
        s = line.strip()
        if s.startswith("<details>"):
            in_details, answer = True, []
            summary = None
            rest = s[len("<details>"):]
            m = SUMMARY_RE.search(rest)
            if m:
                summary = m.group(1).strip()
            continue
        if in_details and summary is None:
            m = SUMMARY_RE.search(s)
            if m:
                summary = m.group(1).strip()
                continue
        if s.startswith("</details>"):
            if summary is not None:
                nm = NUM_RE.match(summary)
                if nm:
                    cards.append((int(nm.group(1)), nm.group(2), "\n".join(answer).strip()))
                elif summary.lower() == "answer" and pending:
                    cards.append((pending[0], pending[1], "\n".join(answer).strip()))
            in_details, summary, pending = False, None, None
            continue
        if in_details:
            answer.append(line)
            continue
        m = NUM_RE.match(line)
        if m:
            pending = (int(m.group(1)), m.group(2))
    return cards


def collect(docs_dir, with_answers=False, start=None):
    start = start or dt.date.today()
    rows = []
    for path in sorted(pathlib.Path(docs_dir).glob("[0-9][0-9]-*.md")):
        text = path.read_text(encoding="utf-8")
        cid = chapter_id(text)
        if not cid:
            continue
        for number, question, answer in parse_drills(text):
            row = {"card_id": f"{cid}-Q{number}", "chapter": cid, "number": number,
                   "question": question, "box": 1, "due": start.isoformat()}
            if with_answers:
                row["answer"] = " ".join(answer.split())
            rows.append(row)
    return rows


def write_csv(rows, out_path, with_answers=False):
    fields = FIELDS + (["answer"] if with_answers else [])
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("docs_dir")
    p.add_argument("out")
    p.add_argument("--answers", action="store_true")
    p.add_argument("--start", default=None)
    a = p.parse_args(argv)
    start = dt.date.fromisoformat(a.start) if a.start else None
    rows = collect(a.docs_dir, a.answers, start)
    write_csv(rows, a.out, a.answers)
    chapters = len({r["chapter"] for r in rows})
    print(f"{len(rows)} cards from {chapters} chapters -> {a.out}")


if __name__ == "__main__":
    main()
