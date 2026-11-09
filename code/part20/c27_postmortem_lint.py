#!/usr/bin/env python3
"""Lint a markdown post-mortem against the structure and action-item rules.

Rules (each finding has a code):
  S1 a required section is missing
  M1 owner, status or incident date line is missing
  I1 the Impact section has no number
  A1 no action items table, or it lacks required columns
  A2 an action has no single named owner
  A3 an action has no ISO due date
  A4 an action starts with a vague verb
  A5 an action has no measurable end state
  A6 an action has an unknown type
  A7 there is no item of type prevent
  B1 blame language found
Usage: python3 c27_postmortem_lint.py postmortem.md   (exit 1 on any error)
"""
import re
import sys

REQUIRED_SECTIONS = [
    "summary",
    "impact",
    "detection",
    "timeline",
    "root cause and trigger",
    "what went well",
    "what went poorly",
    "where we got lucky",
    "action items",
]
ACTION_COLUMNS = ["action", "type", "owner", "due", "measure"]
ACTION_TYPES = {"prevent", "detect", "mitigate"}
VAGUE_STARTS = (
    "improve", "investigate", "look into", "consider", "review", "be more",
    "make better", "monitor better", "ensure", "try to", "think about",
)
NOT_AN_OWNER = {"", "tbd", "team", "everyone", "sre", "sre team", "all", "none", "?"}
BLAME_PHRASES = (
    "human error", "careless", "carelessness", "negligen", "was at fault",
    "fault of", "should have known", "forgot to", "failed to notice",
    "incompetent", "sloppy",
)
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HEADING = re.compile(r"^#{2,3}\s+(.*?)\s*$")


class Finding:
    def __init__(self, level, code, message):
        self.level = level
        self.code = code
        self.message = message

    def __str__(self):
        return f"{self.level} {self.code} {self.message}"


def split_sections(text):
    """Return {lower-case heading: body text}. Level 2 and 3 headings count."""
    sections, current, body = {}, None, []
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            if current is not None:
                sections[current] = "\n".join(body)
            current, body = m.group(1).strip().lower(), []
        elif current is not None:
            body.append(line)
    if current is not None:
        sections[current] = "\n".join(body)
    return sections


def parse_table(body):
    """Return (header list, list of row dicts) for the first table in body."""
    rows = [l.strip() for l in body.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return [], []
    cells = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    header = [h.lower() for h in cells(rows[0])]
    out = []
    for line in rows[1:]:
        values = cells(line)
        if all(set(v) <= set("-: ") for v in values):
            continue
        out.append(dict(zip(header, values)))
    return header, out


def check_actions(body):
    findings = []
    header, rows = parse_table(body)
    missing = [c for c in ACTION_COLUMNS if c not in header]
    if not rows or missing:
        why = f"missing columns {missing}" if rows else "no table rows"
        return [Finding("error", "A1", f"action items table: {why}")]
    kinds = set()
    for n, row in enumerate(rows, start=1):
        label = f"action {n}"
        action = row["action"].lower()
        owner = row["owner"].strip().lower()
        if owner in NOT_AN_OWNER or " and " in owner or "," in owner or "/" in owner:
            findings.append(Finding("error", "A2", f"{label}: owner must be one named person"))
        if not DATE.match(row["due"]):
            findings.append(Finding("error", "A3", f"{label}: due must be YYYY-MM-DD"))
        if action.startswith(VAGUE_STARTS):
            findings.append(Finding("error", "A4", f"{label}: vague verb at the start"))
        measure = row["measure"]
        if not re.search(r"\d", measure) and "zero" not in measure.lower():
            findings.append(Finding("error", "A5", f"{label}: measure needs a number or zero"))
        kind = row["type"].strip().lower()
        if kind not in ACTION_TYPES:
            findings.append(Finding("error", "A6", f"{label}: type must be one of {sorted(ACTION_TYPES)}"))
        kinds.add(kind)
    if "prevent" not in kinds:
        findings.append(Finding("error", "A7", "no action of type prevent"))
    return findings


def lint(text):
    findings = []
    sections = split_sections(text)
    for name in REQUIRED_SECTIONS:
        if name not in sections:
            findings.append(Finding("error", "S1", f"missing section: {name}"))
    for field in ("owner", "status", "incident date"):
        if not re.search(rf"^\s*[-*]?\s*\**{field}\**\s*:\s*\S", text, re.I | re.M):
            findings.append(Finding("error", "M1", f"missing metadata line: {field}"))
    if "impact" in sections and not re.search(r"\d", sections["impact"]):
        findings.append(Finding("error", "I1", "impact has no number"))
    if "action items" in sections:
        findings.extend(check_actions(sections["action items"]))
    lowered = text.lower()
    for phrase in BLAME_PHRASES:
        if phrase in lowered:
            findings.append(Finding("error", "B1", f"blame language: {phrase!r}"))
    return findings


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        findings = lint(handle.read())
    for f in findings:
        print(f)
    print(f"{len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
