"""Architecture decision record generator for chapter 19.10.

Turns a small JSON decision into a numbered markdown ADR. The generator
refuses one-sided records: at least two options, every option with at least
one con, a decision that names one of the options, and a revisit trigger.
This is the author's recommended practice, not a vendor standard.

    python3 c10_adr.py c10_adr_input_larkfield.json [adr_dir]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

STATUSES = ("proposed", "accepted", "superseded", "rejected")


def validate(d: dict) -> None:
    for key in ("title", "status", "date", "context", "options", "decision", "consequences", "revisit_when"):
        if not d.get(key):
            raise ValueError(f"missing or empty field: {key}")
    if d["status"] not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    if len(d["options"]) < 2:
        raise ValueError("an ADR needs at least two options")
    names = [o["name"] for o in d["options"]]
    if len(names) != len(set(names)):
        raise ValueError("duplicate option name")
    for o in d["options"]:
        if not o.get("cons"):
            raise ValueError(f"option {o['name']!r} has no cons; every option has a cost")
        if not o.get("pros"):
            raise ValueError(f"option {o['name']!r} has no pros; remove it or say why it was considered")
    if d["decision"] not in names:
        raise ValueError(f"decision {d['decision']!r} is not one of the options")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d["date"]):
        raise ValueError("date must be YYYY-MM-DD")


def next_number(adr_dir: Path) -> int:
    nums = [int(m.group(1)) for p in adr_dir.glob("*.md") if (m := re.match(r"(\d{4})-", p.name))]
    return max(nums, default=0) + 1


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:60]


def render(d: dict, number: int) -> str:
    validate(d)
    out = [f"# ADR {number:04d}: {d['title']}", "", f"Status: {d['status']}", f"Date: {d['date']}", "",
           "## Context", "", d["context"], ""]
    if d.get("drivers"):
        out += ["## Decision drivers", ""] + [f"- {x}" for x in d["drivers"]] + [""]
    out += ["## Options considered", ""]
    for o in d["options"]:
        mark = " (chosen)" if o["name"] == d["decision"] else ""
        out += [f"### {o['name']}{mark}", "", "Pros:"] + [f"- {p}" for p in o["pros"]]
        out += ["", "Cons:"] + [f"- {c}" for c in o["cons"]] + [""]
    out += ["## Decision", "", f"We will use: {d['decision']}.", "", "## Consequences", ""]
    out += [f"- {c}" for c in d["consequences"]] + ["", "## Revisit when", ""]
    out += [f"- {r}" for r in d["revisit_when"]] + [""]
    return "\n".join(out)


def write(d: dict, adr_dir: Path) -> Path:
    adr_dir.mkdir(parents=True, exist_ok=True)
    n = next_number(adr_dir)
    path = adr_dir / f"{n:04d}-{slug(d['title'])}.md"
    path.write_text(render(d, n))
    return path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: c10_adr.py decision.json [adr_dir]", file=sys.stderr)
        return 2
    d = {k: v for k, v in json.loads(Path(argv[1]).read_text()).items() if not k.startswith("_")}
    try:
        if len(argv) > 2:
            print(write(d, Path(argv[2])))
        else:
            print(render(d, 1))
    except ValueError as exc:
        print(f"invalid ADR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
