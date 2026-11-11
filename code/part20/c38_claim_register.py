#!/usr/bin/env python3
"""Claim register validator for chapter 20.38.

Every public claim about Token Factory inference must carry a source URL, a date and
an evidence tag. Vendor, third-party and report claims must also name the workload
they came from, because a marketing number without a workload is not a number.

Usage:  python3 c38_claim_register.py [register.json]
Exit code 0 when valid, 1 when any entry fails. Standard library only.
"""
import json
import os
import sys
from datetime import date

TAGS = {"official", "vendor", "filing", "source-code", "third-party", "report", "inference"}
WORKLOAD_TAGS = {"vendor", "third-party", "report"}
REQUIRED = ("id", "claim", "source_url", "date", "tag")
MAX_QUOTE_WORDS = 15
DEFAULT_REGISTER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "c38_claim_register.json")


def _blank(value):
    return not isinstance(value, str) or not value.strip()


def validate_entry(entry, as_of=None):
    """Return a list of problems for one entry. An empty list means the entry is valid."""
    as_of = as_of or date.today()
    if not isinstance(entry, dict):
        return ["entry is not an object"]
    ident = entry.get("id") or "<no id>"
    problems = []
    for key in REQUIRED:
        if _blank(entry.get(key)):
            problems.append(f"{ident}: missing {key}")
    url = entry.get("source_url")
    if not _blank(url) and not url.startswith("https://"):
        problems.append(f"{ident}: source_url must start with https://")
    when = entry.get("date")
    if not _blank(when):
        try:
            parsed = date.fromisoformat(when)
            if parsed > as_of:
                problems.append(f"{ident}: date {when} is in the future")
        except ValueError:
            problems.append(f"{ident}: date {when!r} is not YYYY-MM-DD")
    tag = entry.get("tag")
    if not _blank(tag) and tag not in TAGS:
        problems.append(f"{ident}: unknown tag {tag!r}")
    if tag in WORKLOAD_TAGS and _blank(entry.get("workload")):
        problems.append(f"{ident}: tag {tag} requires a workload")
    quote = entry.get("quote")
    if quote is not None and (not isinstance(quote, str)
                              or len(quote.split()) > MAX_QUOTE_WORDS):
        problems.append(f"{ident}: quote longer than {MAX_QUOTE_WORDS} words")
    return problems


def validate_register(data, as_of=None):
    """Validate a whole register (a dict with an 'entries' list). Returns all problems."""
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        return ["register must be an object with an 'entries' list"]
    if not data["entries"]:
        return ["register has no entries"]
    problems, seen = [], set()
    for entry in data["entries"]:
        problems.extend(validate_entry(entry, as_of))
        ident = entry.get("id") if isinstance(entry, dict) else None
        if ident:
            if ident in seen:
                problems.append(f"{ident}: duplicate id")
            seen.add(ident)
    return problems


def load_register(path=DEFAULT_REGISTER):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def count_by_tag(data):
    counts = {}
    for entry in data["entries"]:
        counts[entry["tag"]] = counts.get(entry["tag"], 0) + 1
    return counts


def main(argv):
    path = argv[1] if len(argv) > 1 else DEFAULT_REGISTER
    data = load_register(path)
    problems = validate_register(data)
    for line in problems:
        print("FAIL", line)
    print(f"{len(data.get('entries', []))} entries, {len(problems)} problems")
    if not problems:
        print("by tag:", dict(sorted(count_by_tag(data).items())))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
